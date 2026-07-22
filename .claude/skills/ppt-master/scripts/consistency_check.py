#!/usr/bin/env python3
"""
PPT Master - Cross-Page Consistency Checker

Compares every generated page against an anchor-derived vocabulary seed:
horizontal chrome-line y positions, spec_lock palette membership, font-size
set, and left text margin. Read-only diagnostic for the bundle fan-out
workflow (see workflows/parallel-execute.md); sequential decks are the
calibration ground truth.

Usage:
    python3 scripts/consistency_check.py <project_path> [--seed FILE]
    python3 scripts/consistency_check.py <project_path> --emit-seed --anchors 01,03,12

Examples:
    python3 scripts/consistency_check.py projects/demo --emit-seed --anchors 01,05,12
    python3 scripts/consistency_check.py projects/demo

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

CHROME_MIN_SPAN = 0.60      # horizontal line counts as chrome at >= 60% canvas width
CHROME_Y_TOL = 2.0          # px tolerance vs seed chrome y
CHROME_NEAR = 24.0          # lines farther than this from any seed chrome y are page content, not chrome
CHROME_TOP_FRAC = 0.20      # chrome lives in the page frame bands: top 20% ...
CHROME_BOTTOM_FRAC = 0.85   # ... and bottom 15% of the canvas; mid-zone lines are content
MARGIN_TOL = 8.0            # px tolerance vs seed left margin
THIN_RECT_MAX_H = 3.0       # rect this thin is a hairline
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _floats(el: ET.Element, *names: str) -> list[float] | None:
    out = []
    for n in names:
        raw = el.get(n)
        if raw is None:
            return None
        m = _NUM_RE.match(raw.strip())
        if not m:
            return None
        out.append(float(m.group()))
    return out


def parse_page(svg_path: Path) -> dict:
    """Extract chrome lines, text metrics, colors, and font sizes from one page."""
    root = ET.parse(str(svg_path)).getroot()
    vb = (root.get("viewBox") or "0 0 1280 720").split()
    width, height = float(vb[2]), float(vb[3])
    chrome_ys: list[float] = []
    text_xs: list[float] = []
    colors: set[str] = set()
    font_sizes: set[float] = set()

    def walk(el: ET.Element, transformed: bool) -> None:
        tag = _local(el.tag)
        t = transformed or el.get("transform") is not None
        for attr in ("fill", "stroke", "stop-color"):
            val = (el.get(attr) or "").strip()
            if val and _HEX_RE.match(val):
                colors.add(val.upper())
        fs = el.get("font-size")
        if fs and _NUM_RE.match(fs.strip()):
            font_sizes.add(float(_NUM_RE.match(fs.strip()).group()))
        if not t:
            if tag == "line":
                got = _floats(el, "x1", "y1", "x2", "y2")
                if got and abs(got[1] - got[3]) <= 0.5 and abs(got[2] - got[0]) >= CHROME_MIN_SPAN * width:
                    y = (got[1] + got[3]) / 2
                    if y <= CHROME_TOP_FRAC * height or y >= CHROME_BOTTOM_FRAC * height:
                        chrome_ys.append(y)
            elif tag == "rect":
                got = _floats(el, "x", "y", "width", "height")
                if got and got[3] <= THIN_RECT_MAX_H and got[2] >= CHROME_MIN_SPAN * width:
                    y = got[1] + got[3] / 2
                    if y <= CHROME_TOP_FRAC * height or y >= CHROME_BOTTOM_FRAC * height:
                        chrome_ys.append(y)
            elif tag == "text":
                anchor = el.get("text-anchor") or "start"
                got = _floats(el, "x", "y")
                if got and anchor == "start":
                    text_xs.append(got[0])
        for child in el:
            walk(child, t)

    walk(root, False)
    return {
        "canvas": {"w": width, "h": height},
        "chrome_ys": sorted(chrome_ys),
        "left_margin": min(text_xs) if text_xs else None,
        "colors": sorted(colors),
        "font_sizes": sorted(font_sizes),
    }


def load_lock_values(project: Path) -> tuple[set[str], set[float]]:
    """Read palette hexes and typography sizes from spec_lock.md."""
    lock = project / "spec_lock.md"
    palette: set[str] = set()
    sizes: set[float] = set()
    if not lock.is_file():
        return palette, sizes
    section = ""
    for line in lock.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        m = re.match(r"-\s*[^:]+:\s*(.+)$", line.strip())
        if not m:
            continue
        value = m.group(1).strip()
        if section == "colors":
            for hx in re.findall(r"#[0-9A-Fa-f]{6}", value):
                palette.add(hx.upper())
        elif section == "typography":
            m2 = re.fullmatch(r"(\d+(?:\.\d+)?)", value)
            if m2:
                sizes.add(float(m2.group(1)))
    return palette, sizes


def page_files(project: Path) -> list[Path]:
    return sorted((project / "svg_output").glob("*.svg"))


def _page_no(path: Path) -> str:
    m = re.match(r"(\d+)", path.stem)
    return m.group(1).zfill(2) if m else path.stem


def cluster_recurring(per_page_ys: list[list[float]], tol: float) -> list[float]:
    """Merge near-equal y values into cluster means; keep clusters seen on
    a majority of pages (a one-page line is content, not chrome)."""
    tagged = sorted((y, i) for i, ys in enumerate(per_page_ys) for y in ys)
    groups: list[list[tuple[float, int]]] = []
    for item in tagged:
        if groups and item[0] - groups[-1][-1][0] <= tol:
            groups[-1].append(item)
        else:
            groups.append([item])
    min_pages = max(2, (len(per_page_ys) + 1) // 2) if len(per_page_ys) > 1 else 1
    kept = [g for g in groups if len({i for _, i in g}) >= min_pages]
    return [sum(y for y, _ in g) / len(g) for g in kept]


def emit_seed(project: Path, anchor_nos: list[str]) -> int:
    files = [f for f in page_files(project) if _page_no(f) in anchor_nos]
    if not files:
        print(f"[ERROR] no anchor pages matched {anchor_nos} in {project / 'svg_output'}", file=sys.stderr)
        return 1
    chrome_per_page: list[list[float]] = []
    margins: list[float] = []
    fsizes: set[float] = set()
    for f in files:
        page = parse_page(f)
        chrome_per_page.append(page["chrome_ys"])
        if page["left_margin"] is not None:
            margins.append(page["left_margin"])
        fsizes.update(page["font_sizes"])
    palette, lock_sizes = load_lock_values(project)
    first = parse_page(files[0])
    seed = {
        "canvas": first["canvas"],
        "chrome_lines_y": cluster_recurring(chrome_per_page, CHROME_Y_TOL),
        "left_margin": min(margins) if margins else None,
        "font_sizes": sorted(fsizes | lock_sizes),
        "palette": sorted(palette),
        "anchors": [f.name for f in files],
    }
    out = project / "anchor_vocab.json"
    out.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Seed written: {out} ({len(files)} anchor pages)", file=sys.stderr)
    return 0


def check(project: Path, seed_path: Path) -> int:
    if not seed_path.is_file():
        print(f"[ERROR] seed not found: {seed_path} (run --emit-seed first)", file=sys.stderr)
        return 1
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    palette = set(seed.get("palette") or [])
    seed_sizes = set(seed.get("font_sizes") or [])
    seed_chrome = seed.get("chrome_lines_y") or []
    left = seed.get("left_margin")
    anchor_names = set(seed.get("anchors") or [])
    errors = warnings = 0
    for f in page_files(project):
        page = parse_page(f)
        is_anchor = f.name in anchor_names
        if not is_anchor:
            for y in page["chrome_ys"]:
                nearest = min((abs(y - s) for s in seed_chrome), default=None)
                if nearest is not None and CHROME_Y_TOL < nearest <= CHROME_NEAR:
                    print(f"[ERROR] {f.name}: chrome line y={y:g} deviates {nearest:.1f}px from anchor chrome")
                    errors += 1
        if palette:
            for c in page["colors"]:
                if c not in palette:
                    print(f"[ERROR] {f.name}: off-palette color {c}")
                    errors += 1
        for s in page["font_sizes"]:
            if seed_sizes and s not in seed_sizes:
                print(f"[WARNING] {f.name}: font-size {s:g} outside anchor/lock set")
                warnings += 1
        if left is not None and page["left_margin"] is not None and not is_anchor:
            if abs(page["left_margin"] - left) > MARGIN_TOL:
                print(f"[WARNING] {f.name}: left margin {page['left_margin']:g} vs anchor {left:g}")
                warnings += 1
    total = len(page_files(project))
    print(f"\nConsistency: {total} pages, {errors} errors, {warnings} warnings")
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-page consistency check against an anchor vocabulary seed.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project", help="project path containing svg_output/ and spec_lock.md")
    parser.add_argument("--emit-seed", action="store_true", help="derive anchor_vocab.json from anchor pages")
    parser.add_argument("--anchors", default="", help="comma-separated page numbers (e.g. 01,03,12); required with --emit-seed")
    parser.add_argument("--seed", default="", help="seed file path (default <project>/anchor_vocab.json)")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    project = Path(args.project)
    if not (project / "svg_output").is_dir():
        print(f"[ERROR] no svg_output/ under {project}", file=sys.stderr)
        return 1
    if args.emit_seed:
        nos = [n.strip().zfill(2) for n in args.anchors.split(",") if n.strip()]
        if not nos:
            print("[ERROR] --emit-seed requires --anchors 01,02,...", file=sys.stderr)
            return 1
        return emit_seed(project, nos)
    seed_path = Path(args.seed) if args.seed else project / "anchor_vocab.json"
    return check(project, seed_path)


if __name__ == "__main__":
    raise SystemExit(main())
