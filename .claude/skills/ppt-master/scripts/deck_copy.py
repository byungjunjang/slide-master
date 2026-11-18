#!/usr/bin/env python3
"""
PPT Master - Deck Copy Tool (outline review + guarded copy polish)

Three read/write helpers around the visible text of `svg_output/*.svg`:

- `outline` prints each page's title and lead (the largest lines in the top
  part of the page) so the main agent can review the deck's message flow in
  one short list: two pages making the same point, a missing link between
  neighbours, an order problem.
- `extract` writes every visible text line per page to a JSON file — the input
  for a copy-polish pass.
- `apply` replaces lines from an edits file, but only when the new text keeps
  the same numbers, number+unit pairs and Latin words (names, acronyms) as the
  old text, and only when the old text is exactly one text node on that page.
  Everything else is rejected and listed. Results go to
  `<project>/analysis/copy_polish.json`.

Usage:
    python3 scripts/deck_copy.py outline <project_path>
    python3 scripts/deck_copy.py extract <project_path> -o <copy.json>
    python3 scripts/deck_copy.py apply <project_path> <edits.json>

Edits file: a JSON list of {"page": "07", "old": "<exact line>", "new": "<line>"}.

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from consistency_check import _local, _page_no, _text_lines, page_files  # noqa: E402

OUTLINE_TOP = 0.40          # title / lead live in the top 40% of the canvas
OUTLINE_LINES = 2           # title + one lead line per page
_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)")
_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
_UNIT_RE = re.compile(r"\d+(?:[.,]\d+)*\s*(%p|%|pp|bp|조|억|만|천|원|배|x|×|명|개|건|년|월|일|분기|대)")
_LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9&+\-]*")


def _font_size(el: ET.Element) -> float:
    sizes = []
    for node in el.iter():
        raw = node.get("font-size") or ""
        style = node.get("style") or ""
        m = _SIZE_RE.search(raw) or re.search(r"font-size:\s*(\d+(?:\.\d+)?)", style)
        if m:
            sizes.append(float(m.group(1)))
    return max(sizes) if sizes else 0.0


def _first_y(el: ET.Element) -> float | None:
    for node in el.iter():
        raw = node.get("y")
        if raw:
            m = _SIZE_RE.search(raw)
            if m:
                return float(m.group(1))
    return None


def page_outline(svg_path: Path) -> list[str]:
    """Largest distinct lines with 4+ letters in the top part of the page, biggest first."""
    root = ET.parse(str(svg_path)).getroot()
    height = float((root.get("viewBox") or "0 0 1280 720").split()[3])
    picks: list[tuple[float, float, str]] = []
    for el in root.iter():
        if _local(el.tag) != "text":
            continue
        y = _first_y(el)
        text = " ".join(" ".join(el.itertext()).split())  # runs and lines joined by a space
        if y is None or y > OUTLINE_TOP * height or sum(ch.isalpha() for ch in text) < 4:
            continue  # hero numbers ('47.2 vs 43.6', '+33%') are not page messages
        picks.append((-_font_size(el), y, text))
    lines: list[str] = []
    for _neg_size, _y, text in sorted(picks):
        if text not in lines:
            lines.append(text)
        if len(lines) == OUTLINE_LINES:
            break
    return lines


def cmd_outline(project: Path) -> int:
    for f in page_files(project):
        print(f"P{_page_no(f)}: " + "  |  ".join(page_outline(f)))
    return 0


def cmd_extract(project: Path, out: Path) -> int:
    pages = {_page_no(f): {"file": f.name, "lines": _text_lines(f)} for f in page_files(project)}
    out.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {sum(len(p['lines']) for p in pages.values())} lines from {len(pages)} pages to {out}")
    return 0


def _protected(text: str) -> tuple[Counter, Counter, Counter]:
    return (Counter(_NUMBER_RE.findall(text)),
            Counter(u.replace(" ", "") for u in _UNIT_RE.findall(text)),
            Counter(_LATIN_RE.findall(text)))


def _reject_reason(old: str, new: str) -> str | None:
    labels = ("numbers", "number+unit pairs", "Latin words")
    for label, before, after in zip(labels, _protected(old), _protected(new)):
        if before != after:
            return f"changes {label}: {sorted(before.elements())} -> {sorted(after.elements())}"
    return None


def cmd_apply(project: Path, edits_path: Path) -> int:
    edits = json.loads(edits_path.read_text(encoding="utf-8-sig"))
    files = {_page_no(f): f for f in page_files(project)}
    applied, rejected = [], []
    for edit in edits:
        page = str(edit.get("page", "")).zfill(2)
        old, new = str(edit.get("old", "")), str(edit.get("new", ""))
        reason = None if page in files else f"no page {page}"
        reason = reason or _reject_reason(old, new)
        if reason is None:
            raw = files[page].read_bytes().decode("utf-8")  # bytes: keep line endings as they are
            needle = ">" + escape(old) + "<"
            hits = raw.count(needle)
            if hits != 1:
                reason = ("old text is not one exact text node on the page "
                          f"(found {hits}); edit by hand if it spans styled runs")
            else:
                files[page].write_bytes(raw.replace(needle, ">" + escape(new) + "<").encode("utf-8"))
        (rejected if reason else applied).append({**edit, "page": page, **({"reason": reason} if reason else {})})
    report = project / "analysis" / "copy_polish.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({"applied": applied, "rejected": rejected}, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for item in rejected:
        print(f"[REJECTED] P{item['page']}: {item['old']!r} — {item['reason']}")
    changed = sorted({item["page"] for item in applied})
    print(f"\nCopy polish: {len(applied)} applied, {len(rejected)} rejected; report {report}")
    if changed:
        print("Re-check the changed pages: svg_quality_checker.py <project> --pages " + ",".join(changed))
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Outline review and guarded copy polish for svg_output/.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_outline = sub.add_parser("outline", help="print each page's title and lead")
    p_outline.add_argument("project")
    p_extract = sub.add_parser("extract", help="write every visible text line per page to JSON")
    p_extract.add_argument("project")
    p_extract.add_argument("-o", "--output", required=True)
    p_apply = sub.add_parser("apply", help="apply copy edits that keep numbers, units and Latin words")
    p_apply.add_argument("project")
    p_apply.add_argument("edits")
    args = parser.parse_args(argv)
    project = Path(args.project)
    if not (project / "svg_output").is_dir():
        print(f"[ERROR] no svg_output/ under {project}", file=sys.stderr)
        return 1
    if args.command == "outline":
        return cmd_outline(project)
    if args.command == "extract":
        return cmd_extract(project, Path(args.output))
    return cmd_apply(project, Path(args.edits))


if __name__ == "__main__":
    raise SystemExit(main())
