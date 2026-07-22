# lite-P v2 묶음 팬아웃 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Step 6 페이지 저작을 연속 2–3장 묶음 서브에이전트 팬아웃으로 병렬화하는 옵트인 워크플로 + 기계 일관성 게이트를 구현하고, 콜드 3런 A/B로 판정한다.

**Architecture:** 독립 진단 스크립트 `consistency_check.py`(앵커 어휘 시드 생성 + 전 페이지 대조)를 먼저 만들고 기존 순차 벤치 덱으로 캘리브레이션 → `workflows/parallel-execute.md`를 v2로 전면 개정(묶음 배정·시드 주입·기계 게이트) + SKILL.md 규칙 6/7 좁은 예외 + 레지스트리 등록 → 콜드 GP 서브에이전트 3런(seq-24p는 main 체크아웃, fan-24p/fan-12p는 이 워크트리) 직렬 실행 → 스펙 §7 기입·판정.

**Tech Stack:** Python 표준 라이브러리(xml.etree), 기존 ppt-master 스크립트 관례 (`docs/rules/code-style.md`), 프롬프트 문서 관례 (`docs/rules/prompt-style.md`).

**Spec:** [`docs/superpowers/specs/2026-07-22-lite-p-v2-fanout-design.md`](../specs/2026-07-22-lite-p-v2-fanout-design.md)

## Global Constraints

- 저장소는 자동 테스트를 싣지 않는다 — `tests/`·`test_*.py`·pytest 금지, 검증은 실물 코퍼스 스모크(`code-style.md` §11).
- Python: shebang + 모듈 독스트링(Usage/Examples/Dependencies), `configure_utf8_stdio()`, `main(argv) -> int`, `raise SystemExit(main())`, UTF-8/LF, stderr에 진행 로그·stdout에 1차 출력.
- 프롬프트 파일: 명령형, 표 우선, `**Hard rule**:`/`**Trigger**:` 라벨, why는 `> Note` 1줄 (`prompt-style.md`).
- workflows/·references/ 마크다운은 영어(디렉터리 형제 언어 일치).
- 품질 원천 무변경: 지오메트리 게이트, 규칙 9 손저작(서브에이전트 내부 포함), verify-charts, Pretendard 락.
- 벤치 교훈: 벤치 중인 체크아웃에 머지·파일 변경 금지, `result.json` 쓰지 않기, 웜 수치 무효(콜드 서브에이전트만), n=1 % 주장 금지.
- 로컬 main 푸시 금지(사용자 확인 대기). 커밋 말미 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- 작업 체크아웃: `C:\Users\byung\WorkOS\AI Work\slide-master\.claude\worktrees\lite-p-v2` (브랜치 `lite-p-v2`). 메인 체크아웃은 seq-24p 대조군 실행 전용.

---

### Task 1: `consistency_check.py` — 앵커 어휘 시드 + 크로스 페이지 일관성 검사

**Files:**
- Create: `.claude/skills/ppt-master/scripts/consistency_check.py`

**Interfaces:**
- Produces (Task 2·4·5·6이 의존):
  - `python3 scripts/consistency_check.py <project_path> --emit-seed --anchors 01,03,07,12` → `<project_path>/anchor_vocab.json` 생성, exit 0
  - `python3 scripts/consistency_check.py <project_path>` → `[ERROR]`/`[WARNING]` 라인 + 요약, error>0이면 exit 1
  - `anchor_vocab.json` 스키마: `{canvas: {w,h}, chrome_lines_y: [float], left_margin: float, font_sizes: [float], palette: [..], anchors: [..]}`

- [ ] **Step 1: 스크립트 작성** — 아래 코드 그대로 생성 (추출 로직 하나가 시드/검증 양쪽 담당):

```python
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
MARGIN_TOL = 8.0            # px tolerance vs seed left margin
THIN_RECT_MAX_H = 3.0       # rect this thin is a hairline
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _floats(el, *names) -> list[float] | None:
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

    def walk(el, transformed: bool) -> None:
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
                    chrome_ys.append((got[1] + got[3]) / 2)
            elif tag == "rect":
                got = _floats(el, "x", "y", "width", "height")
                if got and got[3] <= THIN_RECT_MAX_H and got[2] >= CHROME_MIN_SPAN * width:
                    chrome_ys.append(got[1] + got[3] / 2)
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
        m = re.match(r"-\s*[\w#·\s]+:\s*(.+)$", line.strip())
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


def cluster(values: list[float], tol: float) -> list[float]:
    """Merge near-equal values into cluster means."""
    out: list[list[float]] = []
    for v in sorted(values):
        if out and v - out[-1][-1] <= tol:
            out[-1].append(v)
        else:
            out.append([v])
    return [sum(c) / len(c) for c in out]


def emit_seed(project: Path, anchor_nos: list[str]) -> int:
    files = [f for f in page_files(project) if _page_no(f) in anchor_nos]
    if not files:
        print(f"[ERROR] no anchor pages matched {anchor_nos} in {project / 'svg_output'}", file=sys.stderr)
        return 1
    chrome, margins, fsizes = [], [], set()
    for f in files:
        page = parse_page(f)
        chrome.extend(page["chrome_ys"])
        if page["left_margin"] is not None:
            margins.append(page["left_margin"])
        fsizes.update(page["font_sizes"])
    palette, lock_sizes = load_lock_values(project)
    first = parse_page(files[0])
    seed = {
        "canvas": first["canvas"],
        "chrome_lines_y": cluster(chrome, CHROME_Y_TOL),
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
        for y in page["chrome_ys"]:
            nearest = min((abs(y - s) for s in seed_chrome), default=None)
            if nearest is not None and nearest > CHROME_Y_TOL:
                print(f"[ERROR] {f.name}: chrome line y={y:g} deviates {nearest:.1f}px from anchor chrome {seed_chrome}")
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
        if left is not None and page["left_margin"] is not None and f.name not in anchor_names:
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
```

- [ ] **Step 2: 순차 정답지 스모크 (캘리브레이션 루프)** — 순차 덱은 일관성 정답지: 아래 두 코퍼스에서 seed→check가 **0 error**가 될 때까지 추출 규칙/허용 오차만 조정(검사 축 삭제 금지). 경고는 건별로 눈으로 보고 합리성 판단.

```bash
cd "C:/Users/byung/WorkOS/AI Work/slide-master/.claude/worktrees/lite-p-v2"
P=../pipeline-lite/projects/20260721_bench_semis_roundA
python .claude/skills/ppt-master/scripts/consistency_check.py "$P" --emit-seed --anchors 01,03,07,12
python .claude/skills/ppt-master/scripts/consistency_check.py "$P"
P=../pipeline-lite/projects/20260721_bench_semis_coldA
python .claude/skills/ppt-master/scripts/consistency_check.py "$P" --emit-seed --anchors 01,04,06,12
python .claude/skills/ppt-master/scripts/consistency_check.py "$P"
```

Expected: 각 덱 `... 12 pages, 0 errors, N warnings` (N은 소수 — 각 건 설명 가능해야 함). 캘리브레이션에서 생긴 `anchor_vocab.json`은 코퍼스에서 삭제.

- [ ] **Step 3: 커밋**

```bash
git add .claude/skills/ppt-master/scripts/consistency_check.py
git commit -m "tool: consistency_check.py — cross-page chrome/palette/type check + anchor vocab seed"
```

---

### Task 2: `parallel-execute.md` v2 + SKILL.md 규칙 6/7 예외 + 레지스트리 등록

**Files:**
- Create: `.claude/skills/ppt-master/workflows/parallel-execute.md` (v1 브랜치 원본을 출발 재료로 전면 개정)
- Modify: `.claude/skills/ppt-master/SKILL.md` 규칙 6·7 (라인 39–40)
- Modify: `.claude/skills/ppt-master/workflows/index.md` §1 표 (verify-charts 행 근처)
- Modify: `.claude/skills/ppt-master/workflows/routing.md` §4 표

**Interfaces:**
- Consumes: Task 1의 CLI 계약 (`--emit-seed --anchors`, 기본 check 모드, `anchor_vocab.json`)
- Produces: 팬아웃 암 실행자가 따를 워크플로 (Task 5·6이 의존)

- [ ] **Step 1: v2 워크플로 작성** — 골자(전문은 v1 구조 유지, 아래 조항으로 개정; prompt-style 준수):
  - frontmatter description: bundle fan-out 명시.
  - **Trigger**: 명시 요청만("병렬 생성" / "parallel generation" / "并行生成"). 자동 발동·자발 추천 금지.
  - **When to Run**: Step 6 준비 완료, `mode: flat`, 덱 ≥ 10p, 명시 옵트인.
  - **Step 1 Anchors** (v1 유지): cover + divider 1 + 아키타입 견본, min = max(4, ~25%), 전 장 페이지 게이트 통과.
  - **Step 2 Vocabulary Seed (신규)**: `python3 ${SKILL_DIR}/scripts/consistency_check.py <project> --emit-seed --anchors <앵커 번호들>` → 팬아웃 프롬프트에 `anchor_vocab.json` 수치 + 최근접 앵커 SVG 경로 2–3개 주입.
  - **Step 3 Fan-Out**: 연속 2–3장 묶음/서브에이전트, 1웨이브 동시 ≤7. 프롬프트 계약 표: Locks(spec_lock 필독 1회 — 묶음 ≤3장이라 마일스톤 재독 불요, 컴팩션 시 재독 + 자기 페이지 §IX 항목) / Seed(anchor_vocab.json 값 + 앵커 경로) / References(ref-diet 조건부 목록의 묶음별 합집합 — 무차트 묶음은 native-objects.md 생략) / Contract(자기 `svg_output/<page>.svg`만 작성, 페이지별 checker 단일 파일 실행 0 error + text-geometry 처분 보고, **손저작 — 규칙 9 내부 적용**) / Boundaries(다른 파일 쓰기·spec_lock 수정·서버 기동 금지).
  - **Missing/failed page** → 메인이 순차 저작 (v1 유지).
  - **Step 4 Consistency Gate (기계화)**: `consistency_check.py <project>` → error 0까지 메인이 손수선(재팬아웃 금지) → 덱 전체 `svg_quality_checker.py` → SKILL Step 6 꼬리(선택 픽셀 체크 → verify-charts) → Step 7 재개.
  - **Checkpoint** 블록: 앵커 목록 / 묶음 구성 / seed 생성 / 팬아웃 결과(실패 페이지) / consistency 0 error / 덱 체커 0 error.
- [ ] **Step 2: SKILL.md 규칙 6·7 예외 문장 추가** — v1 문안 재사용 + 묶음 문구. 규칙 6 말미에 추가:

```
**Experimental exception (explicit opt-in only)**: when the user explicitly requests parallel generation, the [`parallel-execute`](workflows/parallel-execute.md) workflow governs a bounded anchored fan-out (main-agent anchor pages + seeded subagents authoring 2–3-page bundles + a mandatory machine consistency gate); outside that workflow this rule stands unchanged
```

규칙 7 말미에 추가: `The same experimental [`parallel-execute`](workflows/parallel-execute.md) exception as rule 6 applies (explicit opt-in only; its bounded bundles are part of that workflow, not a license to batch)`

- [ ] **Step 3: 레지스트리 두 곳 등록** — index.md §1에 행 추가:

```
| `parallel-execute` | [`parallel-execute.md`](./parallel-execute.md) | User explicitly requests parallel page generation during Step 6 | `mode: flat`; deck ≥ 10 pages; Step 6 setup complete | Never auto-invoked or recommended; structured routes stay sequential | Replaces the sequential tail of Step 6 | Anchor pages + bundle fan-out + machine consistency gate, then normal Step 6 gates | Falls back to sequential authoring for failed pages |
```

routing.md §4 표에 행 추가:

```
| Parallel page generation (experimental) | User explicitly asks for parallel generation ("병렬 생성", "parallel generation") | [`parallel-execute`](./parallel-execute.md) inside Step 6 | `mode: flat`, deck ≥ 10 pages, explicit opt-in this run | Anchored bundle fan-out + consistency gate, then normal gates | Stop (stay sequential) when mode is structured or deck < 10 pages |
```

- [ ] **Step 4: preflight 스모크** — `python .claude/skills/ppt-master/scripts/preflight.py` PASS 확인(스텁 신선도 포함 — SKILL frontmatter 무변경이므로 통과해야 정상).
- [ ] **Step 5: 커밋**

```bash
git add .claude/skills/ppt-master/workflows/parallel-execute.md .claude/skills/ppt-master/SKILL.md .claude/skills/ppt-master/workflows/index.md .claude/skills/ppt-master/workflows/routing.md
git commit -m "lite-P v2: bundle fan-out workflow, SKILL rules 6/7 narrow exception, registry rows"
```

---

### Task 3: 벤치 준비 — 24p 소스 저작 · 코퍼스 보존 · 환경 청소

**Files:**
- Create: `projects/_incoming/global_semiconductor_outlook_2026.md` (양 체크아웃, gitignore — 커밋 없음)
- Copy: 구 워크트리 `pipeline-lite/projects/20260721_bench_semis_{refdiet,roundA,coldA}` → 메인 체크아웃 `projects/`

**Interfaces:**
- Produces: Task 4·5가 읽는 24p 소스(동일 파일), Task 6이 읽는 12p 소스(`samsung_vs_hynix_2025.md` 사본)

- [ ] **Step 1: 24p급 소스 저작** — 기존 반도체 주제 확장판, 한국어, ~500–700줄. 24p를 지탱할 구조: ①2025 결산(삼성/하이닉스 역전 — 기존 12p 소재 요약 재사용) ②메모리 사이클과 HBM 수요 전개 ③파운드리 경쟁(TSMC/삼성/인텔 점유·공정 로드맵) ④AI 가속기 생태계(NVIDIA/AMD/커스텀 ASIC) ⑤소재·장비 공급망(ASML EUV·HBM CoWoS 병목) ⑥지정학·수출통제 ⑦2026 전망 시나리오(수치 표 3개 이상 — 차트 소재). 수치는 표로 제공(차트 페이지 유도), 이미지 소재 없음. 12p 소스(`samsung_vs_hynix_2025.md`)를 coldA 코퍼스 `sources/`에서 확보해 재료로 참조하되 표절이 아니라 확장.
- [ ] **Step 2: 소스 배치** — 동일 파일을 두 체크아웃 `projects/_incoming/`에 복사. 12p 소스 사본도 이 워크트리 `projects/_incoming/`에 배치.
- [ ] **Step 3: 코퍼스 보존** — `pipeline-lite/projects/20260721_bench_semis_{refdiet,roundA,coldA}` → 메인 `projects/` 복사(이름 그대로, 기존 항목과 충돌 없음 확인).
- [ ] **Step 4: 데몬 청소** — 5050+ 포트의 잔존 svg_editor/confirm_ui 데몬을 각 프로젝트 `--shutdown`으로 정리하거나 프로세스 확인 후 종료. 벤치 포트 간섭 제거.

---

### Task 4: 벤치 런 1 — seq-24p (대조군, 메인 체크아웃 · main 동결)

- [ ] **Step 1: 콜드 GP 서브에이전트 기동** (`run_in_background: true`, 이후 Task 5·6과 직렬). 프롬프트 원문:

```
당신은 ppt-master 파이프라인의 자율 벤치 실행자다. 아래 계약으로 프레젠테이션을 처음부터 끝까지 생성하라.

- 작업 루트: C:\Users\byung\WorkOS\AI Work\slide-master (이 디렉터리에서만 작업)
- 먼저 .claude/skills/ppt-master/SKILL.md 를 읽고 그 워크플로를 순서대로 따른다.
- 소스: projects/_incoming/global_semiconductor_outlook_2026.md · 프로젝트명 20260722_bench_semi24_seq · 캔버스 ppt169 · 페이지 수 24 고정.
- Step 4 확인 게이트: Confirm UI 서버를 띄우지 말 것(confirm_ui/server.py 실행 금지, --wait 금지). 채팅 폴백 상황으로 간주하고 추천값 전부를 스스로 도출해 즉시 수락된 것으로 진행. confirm_ui/result.json 은 절대 쓰지 말 것.
- 확정값: image_usage = none(이미지 없음), 스피커 노트 없음, formula 정책 text-only, 언어 한국어.
- 금지: 다른 projects/ 디렉터리 열람, docs/superpowers/ 열람, 저장소 파일 수정, git 조작, 병렬 생성/서브에이전트 위임(순차 규율 그대로).
- 종료 절차: svg_quality_checker 0 error → 차트 페이지가 있으면 verify-charts 워크플로 → python .claude/skills/ppt-master/scripts/verify_deck.py projects/20260722_bench_semi24_seq (렌더 포함 — --no-render 붙이지 말 것) → python .claude/skills/ppt-master/scripts/measure_run.py projects/20260722_bench_semi24_seq → 라이브 프리뷰 데몬 --shutdown.
- 최종 보고(반드시 전부): 단계별 자가 타임라인(시각 포함), checker/verify-charts/verify_deck 결과 요약, measure_run 출력 전문.
```

- [ ] **Step 2: 완료 수신 후 검수** — measure_run 전문·타임라인 기록, `_pptx_render/*-grid.png` 콘택트시트 Read로 육안 결함 집계, 결과를 스크래치 노트에 적재. 메인 체크아웃 상태 오염 없음 확인(`git -C <main> status`).

### Task 5: 벤치 런 2 — fan-24p (이 워크트리, 병렬 생성 옵트인)

- [ ] **Step 1: Task 4 완료 후 기동.** 프롬프트 = Task 4와 동일하되 아래만 교체:
  - 작업 루트: `C:\Users\byung\WorkOS\AI Work\slide-master\.claude\worktrees\lite-p-v2`
  - 프로젝트명 `20260722_bench_semi24_fan`
  - 금지 항목에서 "병렬 생성/서브에이전트 위임" 제거하고 다음으로 대체: `사용자가 "병렬 생성"을 명시 요청했다 — Step 6에서 workflows/parallel-execute.md 를 읽고 그 워크플로(앵커 손저작 → 어휘 시드 → 묶음 팬아웃 → 기계 일관성 게이트)를 따르라. 팬아웃 묶음 구성(페이지 배정·동시 수)과 각 서브에이전트 소요를 최종 보고에 포함하라.`
- [ ] **Step 2: 검수** — Task 4 Step 2와 동일 + `consistency_check.py` 재실행으로 위반 0 확인 + 콘택트시트에서 페이지 간 일관성(톤·간격·크롬) 집중 검수.

### Task 6: 벤치 런 3 — fan-12p

- [ ] **Step 1: Task 5 완료 후 기동.** 프롬프트 = Task 5와 동일하되: 소스 `projects/_incoming/samsung_vs_hynix_2025.md`, 프로젝트명 `20260722_bench_semi12_fan`, 페이지 수 12 고정.
- [ ] **Step 2: 검수** — Task 5 Step 2와 동일.

### Task 7: 판정·기록·마무리

**Files:**
- Modify: `docs/superpowers/specs/2026-07-22-lite-p-v2-fanout-design.md` §7 결과 표 + 판정 추기
- Modify: `C:\Users\byung\.claude\projects\...\memory\pipeline-lite-ab.md` + `MEMORY.md`

- [ ] **Step 1: 판정** — 스펙 §5 기준 그대로: fan-24p Step 6 팬아웃 구간 vs seq-24p 동일 구간 산술 비교(총량 % 주장 금지) / 품질 전수(checker·verify·육안·verify-charts·validate_spec) / consistency 위반 0. 미달 축이 있으면 Task 2 커밋 드롭(revert)하고 그 사실을 스펙에 기록.
- [ ] **Step 2: 스펙 §7 기입 + 커밋** — `bench: record lite-P v2 A/B results` (측정치·판정·캐비앗 — 콜드 n=1 한계 명시).
- [ ] **Step 3: 메모리 갱신** — `pipeline-lite-ab.md`에 라운드 B 결과 1블록 추가(fork 미지원 실증 포함), MEMORY.md 훅 갱신.
- [ ] **Step 4: 사용자 보고** — 머지 권고(하거나 드롭 사실), 구 워크트리 정리·main 푸시는 사용자 결정 대기임을 명시.
