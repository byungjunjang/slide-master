#!/usr/bin/env python3
"""
PPT Master - Number Ledger

Keeps every number a deck shows traceable to the design_spec.md §XI Number
Ledger, and lists the source gaps the web gap-fill can close. See
references/strategist.md §6.3 for the ledger contract and the tag words.

- `gaps <source.md> ...` lists gap candidates with line numbers: a table cell
  or prose line marked '—' / '-' / 'N/A' / '미수집' / '미확인' / '비공개' /
  '확인 필요', an empty cell in a numeric column (one side of a comparison has
  the value, the other does not), and a quarter missing from a table's quarter
  run (1Q25, 2Q25, 4Q25 → 3Q25). The Strategist judges each candidate and
  writes the real count to recommendations.json `web_gapfill`.
- `check <project_path>` reads the ledger and the visible text of
  `svg_output/*.svg` and warns on (a) numbers not in the ledger, (b) 계산 /
  전망 / 가정 / 웹 values on a page that shows no tag word for that type,
  (c) malformed ledger rows (unknown type, no source, 웹 row without a URL)
  and rows that hold only exempt values, and (d) internal file references on
  a page ('analysis/fin_model.json', 'fin_model: pnl[2031].ebit') — a source
  line names a source a reader can look up.
  Exempt: years, dates, page numbers and page references ('14쪽'), axis ticks
  and list markers (3+ bare numbers in one column or row stepping evenly),
  period / ordinal / structure counters ('2분기', '1위', '3단계'),
  identifiers ('HBM4', '4Q25', 'Phase 1'), and a per-unit base ('1조 원당').

A ledger value matches by number, not by unit: '47.2조 원' in the ledger
covers a '47.2' chart label. Warnings only — both commands exit 0 (1 on
unreadable input).

Usage:
    python3 scripts/number_ledger.py gaps <source.md> [<source.md> ...]
    python3 scripts/number_ledger.py check <project_path>

Examples:
    python3 scripts/number_ledger.py gaps projects/demo/sources/report.md
    python3 scripts/number_ledger.py check projects/demo

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from consistency_check import (  # noqa: E402
    _floats,
    _local,
    _page_no,
    _text_lines,
    page_files,
)

# Ledger type → words accepted in the `type` column; for a tagged type the
# same words are the tags a page must show (Korean deck / English deck).
TYPE_WORDS = {
    "원문": ("원문", "source"),
    "계산": ("계산", "calc"),
    "전망": ("전망", "forecast"),
    "가정": ("가정", "assumption"),
    "웹": ("웹", "web"),
}
TAGGED_TYPES = ("계산", "전망", "가정", "웹")

_NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_ARTIFACT_RE = re.compile(  # analysis/fin_model.json, sources/report.md, fin_model: pnl[…]
    r"(?<![\w.])(?:analysis|sources|svg_output|notes|images|exports)[/\\]"
    r"|(?<=\w)\.(?:json|md|csv|xlsx|py)(?![A-Za-z0-9])"
    r"|(?<![\w.])fin_(?:model|assumptions)(?![A-Za-z0-9])")
_DATE_RE = re.compile(  # 2026-07-15 / 2025.09 / 2025/5 / 2월 15일
    r"(?<![\d.,])(?:19|20)\d\d[.\-/](?:0?[1-9]|1[0-2])"
    r"(?:[.\-/](?:0?[1-9]|[12]\d|3[01]))?(?!\d)"
    r"|(?<!\d)\d{1,2}\s?월\s?\d{1,2}\s?일")
_YEAR_RANGE_RE = re.compile(r"(?:19|20)\d\d\s?[–~∼-]\s?$")   # the '29' of 2028–29
_WORD_PREFIX_RE = re.compile(r"(?<![A-Za-z])(?!vs\b)[A-Za-z]{2,}\.?\s$")  # Phase 1
_LETTER_UNIT_RE = re.compile(r"(?:x|pp|bp)(?![A-Za-z])")     # 3.4x, 25pp
_COUNTER_RE = re.compile(  # period / ordinal / structure counters and page refs
    r"\s?(?:분기|반기|년차|월|위|차|번째|단계|단|세대|종|유형|가지|쪽|페이지)")
_PER_UNIT_RE = re.compile(r"\s?(?:조|억|만|천)?\s?(?:원|명|인|대|개|주|건)?\s?당")
_CHAIN_SEP_RE = re.compile(r"\s?[·~∼–\-/]\s?")  # 1~12월, 1·2·3년차, Gate 1·2
_UNIT_CHARS = set("%배x조억만천원")
_PAGE_NO_RE = re.compile(r"(?:p\.?\s?|page\s)?0*(\d{1,3})(?:\s?/\s?\d{1,3})?", re.IGNORECASE)
_BARE_RE = re.compile(r"[+\-−]?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?(?:%|조|억|만|원|배|x)?")
_LEDGER_HEADING_RE = re.compile(r"^##\s+XI\.", re.MULTILINE)
_PAGE_REF_RE = re.compile(r"P?(\d{1,3})(?:\s?[–~-]\s?P?(\d{1,3}))?", re.IGNORECASE)
_GAP_WORD_RE = re.compile(r"미수집|미확인|미공개|비공개|확인\s?필요|\bN/A\b", re.IGNORECASE)
_DASHES = "—–―-−"
_NUMERIC_CELL_RE = re.compile(r"^[~약±+\-−≈△▲▼]*\s?\d")
_QUARTER_RE = re.compile(
    r"([1-4])Q'?(\d{2}(?:\d{2})?)"               # 1Q25 / 1Q2025
    r"|Q([1-4])\s?'?(\d{2}(?:\d{2})?)"           # Q1 25 / Q1'25
    r"|(\d{4})\s?(?:년\s?)?([1-4])(?:Q|분기)")    # 2025 1Q / 2025년 1분기


@dataclass
class Number:
    raw: str
    value: float
    exempt: str = ""   # why the number needs no ledger row ('' = it needs one)


@dataclass
class LedgerRow:
    id: str
    shown: str
    type: str          # canonical type, or the raw cell when unknown
    source: str
    pages: set[int] = field(default_factory=set)
    values: set[float] = field(default_factory=set)
    cells: int = 5


def _key(value: float) -> float:
    return round(abs(value), 4)


def _clip(text: str, limit: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


# ---- numbers ----------------------------------------------------------------

def _exempt_reason(raw: str, value: float, before: str, after: str) -> str:
    if re.search(r"[A-Za-z]$", before) or (
            re.match(r"[A-Za-z]", after) and not _LETTER_UNIT_RE.match(after)):
        return "identifier"
    if "," not in raw and "." not in raw:
        if len(raw) == 4 and 1900 <= value <= 2100:
            return "year"
        if len(raw) == 2 and _YEAR_RANGE_RE.search(before):
            return "year"
        if value <= 20 and _WORD_PREFIX_RE.search(before) and after[:1] not in _UNIT_CHARS:
            return "identifier"
        if value == 1 and _PER_UNIT_RE.match(after):
            return "per-unit base"
    if _COUNTER_RE.match(after):
        return "counter"
    return ""


def numbers(text: str) -> list[Number]:
    """Numbers in one visible line, each with its exemption reason ('' = needs a row)."""
    text = _DATE_RE.sub(" ", _URL_RE.sub(" ", text))
    found: list[tuple[Number, int, int]] = []
    for m in _NUM_RE.finditer(text):
        before, after = text[:m.start()], text[m.end():]
        if before[-1:] in (".", ",") and before[-2:-1].isdigit():
            continue  # tail of a dotted run such as 1.2.3
        value = float(m.group().replace(",", ""))
        found.append((Number(m.group(), value, _exempt_reason(m.group(), value, before, after)),
                      m.start(), m.end()))
    # A chain ('1~12월', '1·2·3년차', 'Gate 1·2') shares its last counter and
    # its first identifier with every member.
    i = 0
    while i < len(found):
        j = i
        while j + 1 < len(found) and _CHAIN_SEP_RE.fullmatch(text[found[j][2]:found[j + 1][1]]):
            j += 1
        chain = [num for num, _, _ in found[i:j + 1]]
        shared = chain[-1].exempt if chain[-1].exempt == "counter" else (
            chain[0].exempt if chain[0].exempt == "identifier" else "")
        if len(chain) > 1 and shared:
            for num in chain:
                num.exempt = num.exempt or shared
        i = j + 1
    return [num for num, _, _ in found]


# ---- ledger -----------------------------------------------------------------

def _canonical_type(cell: str) -> str:
    word = (cell.split() or [""])[0].lower()
    for canonical, words in TYPE_WORDS.items():
        if word in words:
            return canonical
    return cell


def _page_set(cell: str) -> set[int]:
    pages: set[int] = set()
    for m in _PAGE_REF_RE.finditer(cell):
        first = int(m.group(1))
        last = int(m.group(2)) if m.group(2) else first
        pages.update(range(first, last + 1))
    return pages


def parse_ledger(design_spec: str) -> Optional[list[LedgerRow]]:
    """§XI Number Ledger rows, or None when the spec has no §XI section."""
    m = _LEDGER_HEADING_RE.search(design_spec)
    if not m:
        return None
    section = design_spec[m.end():]
    nxt = re.search(r"^##\s", section, re.MULTILINE)
    if nxt:
        section = section[:nxt.start()]
    rows: list[LedgerRow] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0].lower() == "id" or all(set(c) <= set("-: ") for c in cells):
            continue
        count = len(cells)
        cells += [""] * (5 - count)
        rows.append(LedgerRow(
            id=cells[0] or "?", shown=cells[1], type=_canonical_type(cells[2]),
            source=cells[3], pages=_page_set(cells[4]), cells=count,
            values={_key(n.value) for n in numbers(cells[1]) if not n.exempt}))
    return rows


def ledger_problems(rows: list[LedgerRow]) -> list[str]:
    """Row defects that break traceability: shape, type, source, 웹 URL."""
    problems = []
    for row in rows:
        if row.cells != 5:
            problems.append(f"{row.id}: {row.cells} cells — expected "
                            f"id | shown as | type | formula or source/URL | pages")
        if row.type not in TYPE_WORDS:
            problems.append(f"{row.id}: type '{row.type}' is not one of "
                            f"{' / '.join(TYPE_WORDS)}")
        if not row.source:
            problems.append(f"{row.id}: no formula or source")
        elif row.type == "웹" and not _URL_RE.search(row.source):
            problems.append(f"{row.id}: a 웹 row needs the URL it came from")
    return problems


def ledger_notes(rows: list[LedgerRow]) -> list[str]:
    """Rows that hold only exempt values: harmless, but no page number needs them."""
    return [f"{row.id}: 'shown as' holds no number that needs a row ('{_clip(row.shown, 30)}') "
            f"— years, counters and identifiers are exempt; drop the row or write the shown value"
            for row in rows if not row.values]


# ---- page text --------------------------------------------------------------

def _anchor(el: ET.Element) -> Optional[list[float]]:
    for node in [el, *el]:
        pos = _floats(node, "x", "y")
        if pos:
            return pos
    return None


def _even_steps(values: list[float]) -> bool:
    steps = [b - a for a, b in zip(values, values[1:])]
    return bool(steps) and steps[0] != 0 and all(
        abs(s - steps[0]) <= 1e-6 * max(1.0, abs(steps[0])) for s in steps)


def _tick_lines(svg_path: Path) -> Counter:
    """Texts of axis ticks / list markers: 3+ bare-number labels sharing one x
    (or one y) whose values step evenly in position order."""
    labels = []
    root = ET.parse(str(svg_path)).getroot()
    for el in root.iter():
        if _local(el.tag) != "text":
            continue
        raw = "".join(el.itertext()).strip()
        m = _BARE_RE.fullmatch(raw)
        pos = _anchor(el) if m else None
        if pos:
            labels.append((pos, el.get("font-size") or "", raw,
                           float(m.group(1).replace(",", "")), id(el)))
    ticks: dict[int, str] = {}
    for axis in (0, 1):   # 0: shared x (a column), 1: shared y (a row)
        runs: dict[tuple, list] = {}
        for lab in labels:
            runs.setdefault((round(lab[0][axis]), lab[1]), []).append(lab)
        for run in runs.values():
            run.sort(key=lambda lab: lab[0][1 - axis])
            if len(run) >= 3 and _even_steps([lab[3] for lab in run]):
                ticks.update((lab[4], lab[2]) for lab in run)
    return Counter(ticks.values())


def page_lines(svg_path: Path, page: int) -> list[str]:
    """Visible text lines minus tick / marker labels and the page number."""
    ticks = _tick_lines(svg_path)
    lines = []
    for line in _text_lines(svg_path):
        if ticks[line] > 0:
            ticks[line] -= 1
            continue
        m = _PAGE_NO_RE.fullmatch(line)
        if m and int(m.group(1)) == page:
            continue
        lines.append(line)
    return lines


# ---- commands ---------------------------------------------------------------

def check(project: Path) -> int:
    spec = project / "design_spec.md"
    if not spec.is_file():
        print(f"[ERROR] no design_spec.md under {project}", file=sys.stderr)
        return 1
    rows = parse_ledger(spec.read_text(encoding="utf-8", errors="replace"))
    warnings = 0
    if rows is None:
        print("[WARNING] design_spec.md has no §XI Number Ledger — "
              "every number below counts as unledgered")
        warnings += 1
        rows = []
    problems = ledger_problems(rows) + ledger_notes(rows)
    for problem in problems:
        print(f"[WARNING] ledger {problem}")
    by_value: dict[float, list[LedgerRow]] = {}
    for row in rows:
        for value in row.values:
            by_value.setdefault(value, []).append(row)

    files = page_files(project) if (project / "svg_output").is_dir() else []
    if not files:
        print("[WARNING] no svg_output/*.svg — checked the ledger rows only")
    texts: dict[int, tuple[str, str]] = {}      # page → (file name, joined text)
    shown_on: dict[str, set[int]] = {}          # tagged row id → pages showing it
    checked = unledgered = internal = 0
    for f in files:
        page = int(_page_no(f)) if _page_no(f).isdigit() else 0
        lines = page_lines(f, page)
        texts[page] = (f.name, "\n".join(lines).lower())
        reported: set[float] = set()
        for line in lines:
            ref = _ARTIFACT_RE.search(_URL_RE.sub(" ", line))
            if ref:
                print(f"[WARNING] {f.name}: internal file reference '{ref.group()}' — name the "
                      f"source in words (strategist.md §6.3) — \"{_clip(line)}\"")
                internal += 1
            for num in numbers(line):
                if num.exempt:
                    continue
                checked += 1
                matched = by_value.get(_key(num.value), [])
                if not matched and _key(num.value) not in reported:
                    reported.add(_key(num.value))
                    print(f"[WARNING] {f.name}: '{num.raw}' not in the ledger — \"{_clip(line)}\"")
                    unledgered += 1
                elif matched and all(r.type in TAGGED_TYPES for r in matched):
                    for row in matched:
                        shown_on.setdefault(row.id, set()).add(page)

    untagged = 0
    for row in rows:
        if row.type not in TAGGED_TYPES:
            continue
        for page in sorted((shown_on.get(row.id, set()) | row.pages) & texts.keys()):
            name, text = texts[page]
            if not any(word in text for word in TYPE_WORDS[row.type]):
                print(f"[WARNING] {name}: {row.id} '{_clip(row.shown, 30)}' is {row.type} "
                      f"but the page shows no '{row.type}' tag")
                untagged += 1
    warnings += len(problems) + unledgered + untagged + internal
    print(f"\nLedger: {len(files)} pages, {len(rows)} rows, {checked} numbers checked — "
          f"{unledgered} not in the ledger, {untagged} missing tags, "
          f"{internal} internal file references, "
          f"{len(problems)} row problems ({warnings} warnings)")
    return 0


def _md_tables(lines: list[str]) -> list[list[tuple[int, list[str]]]]:
    """Markdown tables as [(line index, cells)], header row first."""
    tables: list[list[tuple[int, list[str]]]] = []
    current: list[tuple[int, list[str]]] = []
    for i, line in enumerate(lines + [""]):
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-: ") and "-" in c for c in cells):
                current.append((i, cells))
        elif current:
            tables.append(current)
            current = []
    return tables


def _is_gap_cell(cell: str) -> bool:
    dash_led = cell != "" and cell[0] in _DASHES and (len(cell) == 1 or cell[1] == " ")
    return dash_led or bool(_GAP_WORD_RE.search(cell))


def _quarter_index(label: str) -> Optional[int]:
    m = _QUARTER_RE.fullmatch(label.strip())
    if not m:
        return None
    g = m.groups()
    q, year = (g[0], g[1]) if g[0] else (g[2], g[3]) if g[2] else (g[5], g[4])
    year = int(year) + (2000 if len(year) == 2 else 0)
    return year * 4 + int(q) - 1


def _quarter_holes(labels: list[str]) -> list[str]:
    have = {q for q in map(_quarter_index, labels) if q is not None}
    if len(have) < 2:
        return []
    return [f"{i % 4 + 1}Q{i // 4 % 100:02d}"
            for i in range(min(have), max(have)) if i not in have]


def find_gaps(text: str) -> list[tuple[int, str]]:
    """(1-based line, description) for every gap candidate in a source file."""
    lines = text.splitlines()
    gaps: list[tuple[int, str]] = []
    in_table: set[int] = set()
    for table in _md_tables(lines):
        header = table[0][1]
        body = table[1:]
        in_table.update(i for i, _ in table)
        numeric = set()
        for j in range(1, len(header)):
            filled = [cells[j] for _, cells in body
                      if j < len(cells) and cells[j] and not _is_gap_cell(cells[j])]
            if filled and 2 * sum(bool(_NUMERIC_CELL_RE.match(c)) for c in filled) >= len(filled):
                numeric.add(j)
        for i, cells in body:
            for j, cell in enumerate(cells[1:], start=1):
                name = header[j] if j < len(header) else f"column {j + 1}"
                if _is_gap_cell(cell):
                    gaps.append((i + 1, f"{cells[0]} / {name}: {_clip(cell, 40)}"))
                elif not cell and j in numeric:
                    gaps.append((i + 1, f"{cells[0]} / {name}: empty"))
        for labels, kind in (([cells[0] for _, cells in body], "rows"), (header[1:], "columns")):
            holes = _quarter_holes(labels)
            if holes:
                present = ", ".join(x for x in labels if _quarter_index(x) is not None)
                gaps.append((table[0][0] + 1, f"table {kind} skip {', '.join(holes)} "
                                              f"(has {present})"))
    for i, line in enumerate(lines):
        if i not in in_table and _GAP_WORD_RE.search(line):
            gaps.append((i + 1, _clip(line.strip().lstrip("-*> ").strip())))
    return sorted(gaps)


def gaps(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"[ERROR] cannot read {path}: {exc}", file=sys.stderr)
            return 1
        for line_no, desc in find_gaps(text):
            print(f"[GAP] {path.name}:{line_no} {desc}")
            total += 1
    print(f"\nGaps: {total} candidates in {len(paths)} file(s) — judge each, then put "
          f"the real count in recommendations.json web_gapfill")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Number ledger check and source gap listing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_gaps = sub.add_parser("gaps", help="list gap candidates in source Markdown files")
    p_gaps.add_argument("sources", nargs="+", type=Path, help="source .md files")
    p_check = sub.add_parser("check", help="match svg_output numbers against design_spec.md §XI")
    p_check.add_argument("project", type=Path, help="project path with design_spec.md")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    if args.command == "gaps":
        return gaps(args.sources)
    return check(args.project)


if __name__ == "__main__":
    raise SystemExit(main())
