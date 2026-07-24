#!/usr/bin/env python3
"""
PPT Master - Planning Artifact Validator

Machine gate for the Strategist's planning artifacts. Run right after
`design_spec.md` + `spec_lock.md` are written (SKILL.md Step 4) and fix every
reported error before generation starts — a planning defect discovered after
20 generated pages costs a whole-deck rewrite.

Checks:
    - design_spec.md §IX parses; every content page carries a Core message
      (cover / chapter / closing pages exempt); P01 carries a Cover impact
    - design_spec.md §VII template names exist in charts_index.json and each
      Summary-quote is verbatim (the anti-fabrication audit from
      templates/design_spec_reference.md §VII)
    - spec_lock.md completeness: canvas / mode / visual_style / colors /
      typography sections; page_rhythm covers exactly the §IX pages with
      anchor|dense|breathing values
    - spec_lock.md pptx_structure route rules: flat forbids
      pptx_masters/pptx_layouts/page_layouts; structured requires all three
      with exactly one row per page
    - spec_lock.md page_charts ⊆ charts_index and consistent with §VII

Usage:
    python3 scripts/validate_spec.py <project_path> [--strict]

Examples:
    python3 scripts/validate_spec.py projects/20260714_ai_agent_adoption

Dependencies:
    None (only uses standard library)

See templates/design_spec_reference.md and references/strategist.md §6.2 for
the authored contracts these checks enforce.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

CHARTS_INDEX = _SCRIPTS_DIR.parent / "templates" / "charts" / "charts_index.json"
RHYTHM_VALUES = {"anchor", "dense", "breathing"}
STRUCTURED_SECTIONS = ("pptx_masters", "pptx_layouts", "page_layouts")
SLIDE_HEADING_RE = re.compile(r"^####\s+Slide\s+(\d+)", re.MULTILINE)
SECTION_RE = re.compile(r"^##\s+([A-Za-z_]+)\s*$", re.MULTILINE)
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
# Pages that legitimately carry no Core message line
EXEMPT_TITLE_RE = re.compile(
    r"chapter|章|agenda|目录|목차|divider|section|part\b|cover|closing|ending"
    r"|q\s*&\s*a|qna|thanks",
    re.IGNORECASE,
)


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_slides(design_spec: str) -> list[dict]:
    """Extract §IX slide blocks: number, heading line, and rationale fields."""
    m = re.search(r"^##\s+IX\.", design_spec, re.MULTILINE)
    if not m:
        return []
    section = design_spec[m.start():]
    nxt = re.search(r"^##\s+[^#]", section[3:], re.MULTILINE)
    if nxt:
        section = section[: nxt.start() + 3]
    slides = []
    matches = list(SLIDE_HEADING_RE.finditer(section))
    for i, sm in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        block = section[sm.start():end]
        heading = block.splitlines()[0]
        slides.append({
            "number": int(sm.group(1)),
            "heading": heading,
            "core": "**Core message**" in block,
            "cover_impact": "**Cover impact**" in block,
            "closing_impact": "**Closing impact**" in block,
        })
    return slides


def parse_vii_rows(design_spec: str) -> list[dict]:
    """Extract §VII table rows: page, template, quote."""
    m = re.search(r"^##\s+VII\.", design_spec, re.MULTILINE)
    if not m:
        return []
    section = design_spec[m.start():]
    nxt = re.search(r"^##\s+[^#]", section[3:], re.MULTILINE)
    if nxt:
        section = section[: nxt.start() + 3]
    rows = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or set(cells[0]) <= {"-", " "}:
            continue
        page, template, quote = cells[0], cells[1], cells[3]
        if page.lower() in {"page", ""}:
            continue
        rows.append({"page": page, "template": template, "quote": quote})
    return rows


def parse_spec_lock(spec_lock: str) -> dict[str, dict[str, str]]:
    """Parse `## section` blocks of `- key: value` lines."""
    sections: dict[str, dict[str, str]] = {}
    current: Optional[str] = None
    for line in spec_lock.splitlines():
        hm = re.match(r"^##\s+([A-Za-z_]+)\s*$", line)
        if hm:
            current = hm.group(1)
            sections[current] = {}
            continue
        if current is None:
            continue
        im = re.match(r"^-\s+([^:]+):\s*(.*)$", line)
        if im:
            sections[current][im.group(1).strip()] = im.group(2).strip()
    return sections


def load_charts_index() -> dict[str, str]:
    try:
        data = json.loads(CHARTS_INDEX.read_text(encoding="utf-8"))
        return {name: entry.get("summary", "")
                for name, entry in data.get("charts", {}).items()}
    except (OSError, json.JSONDecodeError) as e:
        print(f"  ! WARN charts_index.json unreadable ({e}) — "
              f"§VII / page_charts checks skipped", file=sys.stderr)
        return {}


def check_slides(slides: list[dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not slides:
        return ["design_spec.md has no parseable §IX Content Outline "
                "(#### Slide NN blocks) — the Executor has no content contract"], []
    first = slides[0]
    if not first["cover_impact"]:
        warnings.append(
            "P01 has no `Cover impact` line — mandatory on main-pipeline routes "
            "(strategist.md §6.2); acceptable only on beautify / template-fill "
            "preservation paths")
    for s in slides[1:]:
        if s["core"] or s["closing_impact"]:
            continue
        if EXEMPT_TITLE_RE.search(s["heading"]):
            continue
        errors.append(
            f"Slide {s['number']:02d} has no `Core message` line "
            f"(heading: {_norm_ws(s['heading'])[:60]}) — every content page "
            f"needs its one assertion sentence, or merge/cut the page")
    return errors, warnings


def check_vii(rows: list[dict], charts: dict[str, str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not charts:
        return errors, warnings
    for row in rows:
        name_clean = row["template"].strip("`()").strip()
        if not name_clean or name_clean in {"—", "-"} or \
                "no-template-match" in name_clean:
            continue
        if name_clean not in charts:
            errors.append(
                f"§VII {row['page']}: template `{name_clean}` not found in "
                f"charts_index.json — misspelled or invented")
            continue
        quote = _norm_ws(row["quote"]).strip('"“”')
        expected = _norm_ws(charts[name_clean]).strip('"')
        if quote and quote != expected:
            errors.append(
                f"§VII {row['page']}: Summary-quote for `{name_clean}` is not "
                f"verbatim from charts_index.json — paraphrasing breaks the audit")
        elif not quote:
            warnings.append(f"§VII {row['page']}: empty Summary-quote for "
                            f"`{name_clean}`")
    return errors, warnings


def check_spec_lock(sections: dict[str, dict[str, str]], page_count: int,
                    charts: dict[str, str],
                    vii_rows: list[dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    expected_pages = {f"P{n:02d}" for n in range(1, page_count + 1)}

    for name in ("canvas", "mode", "visual_style", "colors", "typography",
                 "page_rhythm", "pptx_structure"):
        if name not in sections:
            errors.append(f"spec_lock.md missing `## {name}` section")
    if errors:
        return errors, warnings

    if not sections["canvas"].get("viewBox"):
        errors.append("spec_lock.md canvas has no `viewBox`")
    if not sections["mode"].get("mode"):
        errors.append("spec_lock.md mode has no `mode` value")
    if not sections["visual_style"].get("visual_style"):
        errors.append("spec_lock.md visual_style has no `visual_style` value")

    colors = sections["colors"]
    if len(colors) < 6:
        errors.append(f"spec_lock.md colors has only {len(colors)} entries — "
                      f"the full neutral set must be locked before generation")
    for role, value in colors.items():
        if not HEX_RE.match(value):
            warnings.append(f"spec_lock.md colors `{role}: {value}` is not a "
                            f"#RRGGBB hex value")

    typo = sections["typography"]
    if not typo.get("font_family"):
        errors.append("spec_lock.md typography has no `font_family`")
    if not typo.get("body"):
        errors.append("spec_lock.md typography has no `body` size")

    rhythm = sections["page_rhythm"]
    if page_count and set(rhythm) != expected_pages:
        missing = sorted(expected_pages - set(rhythm))
        extra = sorted(set(rhythm) - expected_pages)
        detail = (f"missing {', '.join(missing)}" if missing else "") + \
                 ("; " if missing and extra else "") + \
                 (f"extra {', '.join(extra)}" if extra else "")
        errors.append(f"spec_lock.md page_rhythm does not cover exactly the "
                      f"{page_count} §IX pages — {detail}")
    for page, value in rhythm.items():
        if value not in RHYTHM_VALUES:
            errors.append(f"spec_lock.md page_rhythm `{page}: {value}` is not "
                          f"one of anchor / dense / breathing")

    structure_mode = sections["pptx_structure"].get("mode", "")
    if structure_mode not in {"flat", "structured"}:
        errors.append(f"spec_lock.md pptx_structure mode `{structure_mode}` is "
                      f"not flat / structured (legacy values must be migrated)")
    elif structure_mode == "flat":
        present = [s for s in STRUCTURED_SECTIONS if s in sections]
        if present:
            errors.append(f"spec_lock.md is `mode: flat` but carries structured "
                          f"sections: {', '.join(present)} — flat routes omit them")
    else:
        for name in STRUCTURED_SECTIONS:
            if name not in sections:
                errors.append(f"spec_lock.md is `mode: structured` but missing "
                              f"`## {name}`")
        for name in ("pptx_layouts", "page_layouts"):
            rows = sections.get(name, {})
            if rows and page_count and set(rows) != expected_pages:
                errors.append(f"spec_lock.md {name} rows do not match the "
                              f"{page_count} §IX pages exactly (one row per page)")

    page_charts = sections.get("page_charts", {})
    vii_by_page = {r["page"]: r["template"].strip("`") for r in vii_rows}
    for page, chart in page_charts.items():
        if page_count and page not in expected_pages:
            errors.append(f"spec_lock.md page_charts `{page}` is outside the "
                          f"§IX page range")
        if charts and chart not in charts:
            errors.append(f"spec_lock.md page_charts `{page}: {chart}` not found "
                          f"in charts_index.json — Executor would look for a "
                          f"non-existent reference")
        if vii_by_page and page in vii_by_page and vii_by_page[page] != chart:
            warnings.append(f"page_charts `{page}: {chart}` disagrees with §VII "
                            f"(`{vii_by_page[page]}`)")
    for page, template in vii_by_page.items():
        if template in charts and page not in page_charts:
            warnings.append(f"§VII lists catalog template `{template}` for "
                            f"{page} but spec_lock.md page_charts has no "
                            f"`{page}` row — add the row, or mark the page "
                            f"`no-template-match` in §VII")
    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate design_spec.md + spec_lock.md before generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project", help="path to projects/<project_name>")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(args.project)
    design_path = project / "design_spec.md"
    lock_path = project / "spec_lock.md"
    if not design_path.exists() or not lock_path.exists():
        print(f"Error: {project} has no design_spec.md / spec_lock.md",
              file=sys.stderr)
        return 2

    design_spec = design_path.read_text(encoding="utf-8", errors="replace")
    spec_lock = lock_path.read_text(encoding="utf-8", errors="replace")
    charts = load_charts_index()

    slides = parse_slides(design_spec)
    vii_rows = parse_vii_rows(design_spec)
    sections = parse_spec_lock(spec_lock)

    errors, warnings = check_slides(slides)
    e2, w2 = check_vii(vii_rows, charts)
    e3, w3 = check_spec_lock(sections, len(slides), charts, vii_rows)
    errors += e2 + e3
    warnings += w2 + w3

    for w in warnings:
        print(f"  ! WARN {w}", file=sys.stderr)
    if args.strict:
        errors += warnings
    if errors:
        print(f"[validate_spec] FAIL ({len(errors)} error(s)):", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        return 1
    print(f"[validate_spec] PASS — {len(slides)} pages, "
          f"{len(vii_rows)} §VII rows checked")
    # Record the pass so verify_deck.py can skip an unchanged re-run
    # (mtime comparison against design_spec.md / spec_lock.md).
    try:
        (project / ".spec_pass.json").write_text(
            json.dumps({
                "passed_at": datetime.now(timezone.utc).isoformat(),
                "pages": len(slides),
            }),
            encoding="utf-8",
        )
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
