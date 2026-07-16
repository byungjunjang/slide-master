# mckinsey 컨설팅 밀도 심화 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mckinsey deck/brand design_spec에 컨설팅 조판 문법(2존 원칙·멀티 exhibit·Key Findings 레일·상세 테이블/프레임워크 승격·조건부 밀도 플로어), accent 단일 초점 규칙, `delivery_purpose: text` 추천 시딩을 명문화하고 재조판 dry-run으로 검증한다.

**Architecture:** 코드/UI/SVG 셸 변경 없음 — 프롬프트 스펙 파일 2개의 프로즈 개정이 전부다. Strategist/Executor는 이 스펙을 읽고 동작하므로, 검증은 "개정 스펙 텍스트만 보고 재조판한 페이지가 원하는 밀도·문법을 갖는가"를 Playwright 렌더로 확인한다.

**Tech Stack:** Markdown 스펙 편집, Python + Playwright(sync API, chromium) 렌더 검증, git.

**Spec:** `docs/superpowers/specs/2026-07-16-mckinsey-consulting-density-design.md` (승인됨 — 규칙 원문의 권위 소스)

## Global Constraints

- 수정 파일은 정확히 2개: `.claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md`, `.claude/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md`. 다른 템플릿·스크립트·confirm UI·SVG 셸은 절대 건드리지 않는다.
- SKILL.md frontmatter 무변경 → `sync_codex_stubs.py` 실행 불필요.
- 크롬 불변: 액션 타이틀 독트린, 타이틀 룰 y=112, footer 룰 y=676, Source 라인 관례는 수정 금지.
- 언어 규칙: deck/brand 스펙은 기존 파일 스타일(영어 스캐폴딩 + 한국어 값 허용)을 그대로 따른다. `docs/rules/` 스타일 규칙 준수.
- 팔레트 잠금: 새 텍스트에 §III 표 밖의 HEX를 쓰지 않는다.
- 검증 SVG/PNG는 스크래치패드에만 생성 — repo에 커밋하지 않는다.
- 커밋 메시지 끝: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: deck 스펙 §III accent 단일 초점 규칙 + §XIII 체크리스트

**Files:**
- Modify: `.claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md` (§III Color Rules, §XIII Anti-Pattern Checklist)

**Interfaces:**
- Produces: "Single-focus accent rule" / "Verdict rule" 불릿 명칭 — Task 4(brand 동기화)와 Task 5(검증 체크리스트)가 이 문구를 참조한다.

- [ ] **Step 1: §III Color Rules 개정**

`### Color Rules` 아래 첫 번째·세 번째 불릿을 교체한다.

기존:

```markdown
- **Navy is structure, accent is pointer**: `#0F2A4A` carries chrome and hierarchy; `#2E9BD6` marks the one thing the reader must see. **Accent budget ≤ 2 events per content slide**
- **Grayscale first**: every slide must read in grayscale before blue is applied
- **Chart ladder**: multi-series charts use `#0F2A4A → #1F6FA8 → #4FB2E5` in that order; `#2E9BD6` is reserved for the single focus series/bar. Multi-hue palettes are forbidden
```

교체 후:

```markdown
- **Navy is structure, accent is pointer**: `#0F2A4A` carries chrome and hierarchy; `#2E9BD6` marks the one thing the reader must see
- **Single-focus accent rule**: accent points at exactly ONE focus per page (entity / series / number / cell). Repetition across exhibits is allowed only when marking the SAME focus — the focus series in chart A and that entity's row in table B count as one focus; highlighting two different targets on one page is forbidden
- **Verdict rule is a separate structural account**: the 2px accent rule of a verdict band is a fixed structural convention — max 1 per page, inside the takeaway zone, not counted against the data focus
- **Everything else stays achromatic**: remaining hierarchy is carried by weight, navy, banding, and hairlines — never by additional accent events
- **Grayscale first**: every slide must read in grayscale before blue is applied
- **Chart ladder**: multi-series charts use `#0F2A4A → #1F6FA8 → #4FB2E5` in that order; `#2E9BD6` is reserved for the single focus series/bar — and only when that series/bar is the page's single focus. Multi-hue palettes are forbidden
```

(뒤따르는 Traffic lights / Dark pages / Forbidden 불릿은 무변경.)

- [ ] **Step 2: §XIII 체크리스트 갱신**

기존 항목 교체:

```markdown
- [ ] Accent (`#2E9BD6`) events > 2 on one content slide
```

→

```markdown
- [ ] Accent (`#2E9BD6`) pointing at two different focuses on one page
```

그리고 체크리스트 끝(`- [ ] 여러분 / 우리는 / 함께해요 direct address` 뒤)에 추가:

```markdown
- [ ] Evidence page composed as a single zone without a declared exception (stat-hero / full-bleed table)
- [ ] Source has multi-period / multi-entity figures but the page shows only summary numbers with no detail table
- [ ] Source contains prioritization / causality / phasing structure but the deck has zero framework exhibits
- [ ] Fake cells or unlabeled estimates added to fill density
```

- [ ] **Step 3: 검증**

Run: `grep -c "Single-focus accent rule" ".claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md"`
Expected: `1`

Run: `grep -c "events > 2\|≤ 2 events" ".claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md"`
Expected: `0`

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md
git commit -m "mckinsey deck spec: replace accent budget with single-focus rule; extend anti-pattern checklist

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: deck 스펙 §VIII 조판 문법 심화

**Files:**
- Modify: `.claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md` (§VIII Layout Patterns)

**Interfaces:**
- Consumes: Task 1의 "Single-focus accent rule" 명칭 (레일 verdict 밴드 설명이 §III 계정 규칙을 전제).
- Produces: `key-findings-rail` 패턴명, "Evidence-page composition grammar (density doctrine)" 소제목, 레일 지오메트리(x=776→1236, 헤어라인 x=758) — Task 5 검증이 이 규칙 원문을 준수 기준으로 사용한다.

- [ ] **Step 1: 밀도 독트린 + 레일 패턴 소제목 삽입**

`### Content shape → first-choice pattern` 소제목 **바로 앞**에 다음 두 소제목을 삽입한다:

```markdown
### Evidence-page composition grammar (density doctrine)

- **Two-zone minimum**: every evidence page is composed as exhibit zone + takeaway zone. The takeaway zone takes ONE of three forms — (a) `key-findings-rail` (right rail x=776→1236, separated by a 1px `#E8E8E8` hairline at x=758), (b) stacked takeaways right of the chart (the `chart-led-with-takeaway` pattern), (c) bottom verdict band. Single-zone pages are allowed only as declared exceptions: `stat-hero` or a full-bleed table
- **Multi-exhibit pairing**: when the source provides both a trend and a breakdown, pair a chart (A) with a detail table (B). On rail-form pages the exhibit zone is x=44→740; on forms (b)/(c) exhibits use the full content width. Exhibit lettering `A ·` / `B ·` prefixes (15px/600 `#1A1A1A`) apply only when a page carries 2+ exhibits
- **Detail-table promotion**: for multi-period / multi-entity quantitative content, a detail table (≥ 4 rows × 4 columns, §XII treatment, right-aligned numerics, 11px `#888888` footnote line) is the chart's first-choice companion — "chart + table" is the default form, not "chart or table"
- **Framework mandate (deck level)**: a strategy deck whose source contains prioritization / causality / phasing structure surfaces at least ONE framework exhibit (2×2, tree, process — see the content-shape mapping below). Omission must be justified by source shape; omission for convenience is an anti-pattern (§XIII)
- **Conditional density floor** — 증거가 있으면 펼치고, 없으면 패턴을 바꾼다: an evidence page targets ≥ 12 data points when the source provides them. When the source is thin, switch to a text pattern (`numbered-takeaway-stack`) instead of padding a table. Fabricated figures and fake cells are absolutely forbidden

### `key-findings-rail` pattern

Right rail (x=776→1236): `KEY FINDINGS` label (13.3/600, letter-spacing 0.6, `#888888`) + 2–3 numbered findings (hanging number 24/700 `--navy` + finding title 16.5/600 `#1A1A1A` + 1–2 evidence lines 13.5/400 `#888888`, hairline `#E8E8E8` between findings) + verdict band (2px accent rule + `VERDICT` label 13.3/600 + judgment 18/600 `#1A1A1A` + support 14/400 `#888888`) + optional micro-KPI strip (2–4 KPIs: value 24/700 `--navy` + label 11.5 `#888888`, hairline above). A rail-format reduction of `numbered-takeaway-stack` — same lineage: NO card boxes, NO rounded containment
```

- [ ] **Step 2: content-shape 표에 행 추가**

`| Option comparison | comparison table + Harvey balls | ... |` 행 **바로 아래**에 추가:

```markdown
| Dense quantified evidence (trend + breakdown) | chart (A) + detail table (B) + `key-findings-rail` | grouped/line chart + §XII detail table + right rail |
```

- [ ] **Step 3: Variation discipline에 적층 규칙 명시**

`- Stats include context ("vs 업계 평균 3.2%"); bare numbers read as placeholder` 불릿 뒤에 추가:

```markdown
- The composition grammar above stacks on top of this discipline — variation, ≤ 2 consecutive same-pattern, chart-takeaway pairing, and minimum 3 layout types all still hold
```

- [ ] **Step 4: 검증**

Run: `grep -c "key-findings-rail" ".claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md"`
Expected: `3` (독트린 불릿 1 + 패턴 소제목 1 + 표 행 1)

Run: `grep -c "Two-zone minimum" ".claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md"`
Expected: `1`

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md
git commit -m "mckinsey deck spec: add evidence-page density doctrine and key-findings-rail pattern

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: deck 스펙 §XIV delivery_purpose 시딩

**Files:**
- Modify: `.claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md` (§XIV Usage Instructions)

**Interfaces:**
- Produces: §XIV 항목 5 — Strategist가 Stage 1 추천값을 채울 때 읽는 지시문. 코드 변경 없음(recommendations.json은 Strategist가 덱 스펙을 읽고 작성).

- [ ] **Step 1: §XIV에 항목 5 추가**

`4. Identity만 재사용하려면 brand 추출본 ...` 항목 뒤에 추가:

```markdown
5. **Delivery-purpose seeding**: 이 덱이 Step 3 템플릿으로 지정되면 Strategist는 Stage 1에서 `delivery_purpose: text`(read-close · dense)를 추천값으로 제시한다 — 컨설팅 덱은 발표용이 아니라 정독용 문서다. 사용자는 확인 단계에서 오버라이드할 수 있다(강제 아님). 주의: §IV가 이 덱의 타입 램프(Body 16px)를 잠그므로 `delivery_purpose`는 글자 크기가 아니라 페이지당 콘텐츠 분배량과 `page_rhythm`에만 작용한다. dense 페이지는 수용량이 크므로 같은 소스에서 페이지 수 추천(strategist.md §b)을 한 단계 낮게 잡는 경향을 허용한다 (예: 12–14 → 10–12)
```

- [ ] **Step 2: 검증**

Run: `grep -c "Delivery-purpose seeding" ".claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md"`
Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/mckinsey/templates/design_spec.md
git commit -m "mckinsey deck spec: seed delivery_purpose=text recommendation in usage instructions

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: brand 스펙 accent 문구 동기화

**Files:**
- Modify: `.claude/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md` (§II 마지막 usage 문단)

**Interfaces:**
- Consumes: Task 1의 단일 초점 규칙 문구 (deck이 source of truth — brand 헤더의 provenance 원칙대로 deck에서 고친 것을 동기화).

- [ ] **Step 1: §II usage 문단의 예산 문구 교체**

기존 (문단 내 해당 구절):

```
navy is structure, accent is pointer with a budget of ≤ 2 events per slide;
```

→

```
navy is structure, accent is pointer under a single-focus rule (accent marks exactly ONE focus per page; cross-exhibit repetition only for the same focus; a verdict band's 2px accent rule is a separate structural account, max 1 per page);
```

문단의 나머지(grayscale-first, 차트 래더, traffic-light, forbidden, 코너 반경)는 무변경. 페이지 구조 규칙(2존·레일)은 deck 소관이므로 brand에 추가하지 않는다.

- [ ] **Step 2: 검증**

Run: `grep -c "single-focus rule" ".claude/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md"`
Expected: `1`

Run: `grep -c "≤ 2 events" ".claude/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md"`
Expected: `0`

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/ppt-master/templates/brands/mckinsey/templates/design_spec.md
git commit -m "mckinsey brand spec: sync accent single-focus rule from deck spec

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: 재조판 dry-run 검증 + 설계 문서 상태 갱신

**Files:**
- Create (스크래치패드, 커밋 안 함): `<scratchpad>/verify/09_hbm_share_dense.svg`, `<scratchpad>/verify/07_profitability_dense.svg`, `<scratchpad>/verify/render_verify.py`, 렌더 PNG 2장
- Read: `projects/20260715_samsung_vs_hynix_2025_mckinsey/svg_output/09_hbm_share.svg`, `07_profitability.svg` (데이터 소스), 개정된 deck design_spec.md (조판 규칙의 유일한 준거)
- Modify: `docs/superpowers/specs/2026-07-16-mckinsey-consulting-density-design.md` (상태 라인)

**Interfaces:**
- Consumes: Task 1–3이 개정한 deck 스펙 원문 — 재조판 시 이 텍스트 외의 지시를 쓰지 않는 것이 테스트의 요점 (스펙 텍스트만으로 원하는 조판이 유도되는가).

- [ ] **Step 1: 재조판 2장 작성**

개정 deck 스펙의 §VIII 문법**만**을 준거로, ver1 SVG에서 데이터를 가져와 스크래치패드에 재조판한다 (새 수치 창작 금지 — ver1에 있는 수치와 그 단순 파생만 사용):

- `09_hbm_share_dense.svg` — 레일형(1-a): 좌측 존에 exhibit A(분기 점유율 stacked column, ver1 데이터) + exhibit B(분기 점유율 상세 테이블 ≥4행×4열), 우측 `key-findings-rail`(findings 2–3 + verdict + 마이크로 KPI). accent 초점은 SK 시리즈 단일.
- `07_profitability_dense.svg` — verdict 밴드형(1-c): 전폭 상세 테이블(ver1의 4행 지표 표를 분기 컬럼으로 확장, §XII 처리) + 하단 verdict 밴드. accent 초점은 단일 셀/행 하나.

- [ ] **Step 2: Playwright 렌더**

`<scratchpad>/verify/render_verify.py`:

```python
from playwright.sync_api import sync_playwright
import pathlib

base = pathlib.Path(__file__).parent
files = ["09_hbm_share_dense.svg", "07_profitability_dense.svg"]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    for f in files:
        page.goto((base / f).as_uri())
        page.wait_for_timeout(400)
        page.screenshot(path=str(base / f.replace(".svg", ".png")))
        print("rendered", f)
    browser.close()
```

Run: `python3 render_verify.py`
Expected: `rendered 09_hbm_share_dense.svg` / `rendered 07_profitability_dense.svg`, PNG 2장 생성. Read 도구로 두 PNG를 열어 겹침·오버플로·잘림이 없는지 육안 검수.

- [ ] **Step 3: 개정 §XIII 체크리스트 역적용**

렌더 2장 + 기존 dry-run(`<scratchpad>/05_annual_dense.svg`) 3장에 대해 아래를 판정하고 결과를 기록한다 (전부 통과가 기대값):

1. accent가 서로 다른 두 초점을 가리키는가 → 아니오여야 통과 (05_annual: 차트 SK 시리즈 + 테이블 SK FY 셀 = 같은 초점이므로 통과, verdict 룰은 별도 계정)
2. 선언된 예외 없는 단일 존 evidence 페이지인가 → 아니오
3. 다기간/다엔티티 수치가 있는데 상세 테이블이 없는가 → 아니오
4. 페이크 셀/무표기 추정치가 있는가 → 아니오
5. 데이터 포인트 ≥12개인가 → 예
6. §III 표 밖 HEX 사용 → `grep -oE '#[0-9A-Fa-f]{6}' <svg> | sort -u`로 확인, 전부 §III 표 내여야 통과
7. 언어 규칙 — Task 1–4가 추가한 스펙 텍스트가 기존 파일 스타일(영어 스캐폴딩 + 한국어 값)과 `docs/rules/`를 따르는지 diff 재독으로 확인

하나라도 실패하면: 재조판이 스펙을 어긴 것인지, 스펙 문구가 모호한 것인지 판별해 후자면 스펙 문구를 수정하고 해당 Task를 재커밋한다.

- [ ] **Step 4: 설계 문서 상태 갱신 + 커밋**

`docs/superpowers/specs/2026-07-16-mckinsey-consulting-density-design.md`의 `- 상태: 사용자 승인 대기` →

```markdown
- 상태: 구현 완료 — 재조판 dry-run 3장 체크리스트 통과 (2026-07-16)
```

```bash
git add docs/superpowers/specs/2026-07-16-mckinsey-consulting-density-design.md
git commit -m "Mark mckinsey consulting-density design as implemented and verified

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
