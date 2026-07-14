# jangpm Deck + Brand Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** slide-svg의 jangpm 디자인 시스템을 ppt-master 템플릿 라이브러리에 `templates/decks/jangpm/`(원본) + `templates/brands/jangpm/`(identity 추출본)으로 이식한다.

**Architecture:** deck 패키지가 source of truth — 4개 SVG 셸(기존 라이브러리의 `data-pptx-*` 메타데이터 규약 적용) + `kind: deck` design_spec(14토큰 색 잠금·타입 스케일·GM 계약·에디토리얼 문법 증류). brand 패키지는 identity 세그먼트만 미러링. 등록은 `register_template.py`, 검증은 `template_preview_pptx.py`.

**Tech Stack:** 손 편집 SVG/Markdown + 기존 스크립트 (`register_template.py`, `template_preview_pptx.py`). 새 코드 없음.

**Spec:** `docs/superpowers/specs/2026-07-14-jangpm-deck-brand-port-design.md`

## Global Constraints

- 작업 디렉터리: repo 루트 `C:\Users\byung\WorkOS\AI Work\slide-master` (모든 상대경로 기준)
- Windows: `python` 사용 (`python3` 아님)
- slide-svg repo(`C:\Users\byung\WorkOS\AI Work\slide-svg`)는 **읽기 전용 소스** — 절대 수정 금지
- 이 repo는 워크플로/스킬 패키지 — `tests/`·브랜치 생성 금지, main에 직접 커밋 (기존 관례)
- SVG에 허용되는 HEX는 14토큰만: `#FAFAF9 #FFFFFF #F5F5F4 #1A1A1A #6B7280 #9CA3AF #E5E7EB #D4D4D4 #4633E3 #E8E5FC #2E1FB3 #059669 #E11D48 #D97706`
- 폰트 표기(install-local Pretendard 정책, strategist.md §g / 기존 프로젝트 SVG 관례와 동일):
  - weight 400 → `font-family="Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 속성 없음)
  - weight 500 → `font-family="'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 없음)
  - weight 600 → `font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 없음)
  - weight 700 → `font-family="Pretendard, 'Malgun Gothic', sans-serif"` + `font-weight="700"`
  - weight 800 → `font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 없음)
- 라이브러리 `exports/`는 git-ignore 대상 — 절대 커밋하지 않음
- design_spec.md는 영어 스캐폴딩(섹션 제목/필드명) + 한국어 값 허용
- 커밋 메시지 끝에 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` 추가

---

### Task 1: deck SVG 셸 4장 포팅 + 캐릭터 자산

**Files:**
- Create: `.claude/skills/ppt-master/templates/decks/jangpm/templates/01_cover.svg`
- Create: `.claude/skills/ppt-master/templates/decks/jangpm/templates/02_chapter.svg`
- Create: `.claude/skills/ppt-master/templates/decks/jangpm/templates/03_content.svg`
- Create: `.claude/skills/ppt-master/templates/decks/jangpm/templates/04_ending.svg`
- Create: `.claude/skills/ppt-master/templates/decks/jangpm/images/jangpm-character.png` (복사)

**Interfaces:**
- Consumes: slide-svg 원본 셸 (`C:\Users\byung\WorkOS\AI Work\slide-svg\.claude\skills\slide\templates\layouts\jangpm\*.svg`) — 참고용; 아래 코드 블록이 이미 포팅 완료본이므로 그대로 쓰면 된다
- Produces: Task 2의 design_spec.md §VII 로스터가 참조하는 4개 셸 파일명, Task 3 등록이 요구하는 워크스페이스 구조

- [ ] **Step 1: 4개 SVG 셸 파일 작성**

아래 내용 그대로 각 파일에 저장 (원본 대비 변경점: 루트 `data-pptx-layout` 키, 배경 rect 메타데이터, title/subtitle 슬롯 id, 폰트 스택 교체 — 지오메트리·색·수치는 원본 그대로).

`01_cover.svg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" data-pptx-layout="01_cover" data-pptx-layout-name="Cover">
  <!-- Jangpm — 01 Cover -->

  <!-- Page background -->
  <rect width="1280" height="720" fill="#FAFAF9" id="layout-01_cover-background" data-pptx-layer="layout" data-pptx-editable="false"/>

  <!-- Accent rule (single editorial cue) -->
  <rect x="56" y="140" width="80" height="3" fill="#4633E3"/>

  <!-- Eyebrow / program label -->
  <text x="56" y="180"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        letter-spacing="0.64"
        fill="#6B7280">
    {{EYEBROW}}
  </text>

  <!-- Primary title (Display) -->
  <text x="56" y="340"
        font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="56"
        letter-spacing="-1.68"
        fill="#1A1A1A"
        id="slot-01_cover-title-1" data-pptx-placeholder="title">
    {{TITLE}}
  </text>

  <!-- Optional secondary line (Display-sm, accent) -->
  <text x="56" y="410"
        font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="40"
        letter-spacing="-0.8"
        fill="#4633E3">
    {{TITLE_ACCENT}}
  </text>

  <!-- Subtitle (Title) -->
  <text x="56" y="470"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="18.4"
        fill="#1A1A1A"
        id="slot-01_cover-subtitle-2" data-pptx-placeholder="subtitle">
    {{SUBTITLE}}
  </text>

  <!-- Presenter / date line (Body) -->
  <text x="56" y="656"
        font-family="Pretendard, 'Malgun Gothic', sans-serif"
        font-size="15.2"
        fill="#6B7280">
    {{PRESENTER}} · {{DATE}}
  </text>

  <!-- Thin divider at the bottom edge (structural) -->
  <line x1="56" y1="672" x2="1224" y2="672" stroke="#E5E7EB" stroke-width="1"/>
</svg>
```

`02_chapter.svg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" data-pptx-layout="02_chapter" data-pptx-layout-name="Chapter">
  <!-- Jangpm — 02 Chapter / Section Divider -->

  <rect width="1280" height="720" fill="#FAFAF9" id="layout-02_chapter-background" data-pptx-layer="layout" data-pptx-editable="false"/>

  <!-- Chapter number (Display-sm, accent) -->
  <text x="56" y="260"
        font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="40"
        letter-spacing="-0.8"
        fill="#4633E3">
    {{CHAPTER_NUMBER}}
  </text>

  <!-- Chapter label (uppercase eyebrow) -->
  <text x="56" y="300"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        letter-spacing="0.64"
        fill="#6B7280">
    {{CHAPTER_LABEL}}
  </text>

  <!-- Chapter title (Display) -->
  <text x="56" y="400"
        font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="56"
        letter-spacing="-1.68"
        fill="#1A1A1A"
        id="slot-02_chapter-title-1" data-pptx-placeholder="title">
    {{CHAPTER_TITLE}}
  </text>

  <!-- Supporting line (Title, secondary color) -->
  <text x="56" y="450"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="18.4"
        fill="#6B7280">
    {{CHAPTER_SUMMARY}}
  </text>

  <!-- Structural divider -->
  <line x1="56" y1="672" x2="1224" y2="672" stroke="#E5E7EB" stroke-width="1"/>

  <!-- Page number (bottom right) -->
  <text x="1224" y="696"
        font-family="'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        text-anchor="end"
        fill="#9CA3AF">
    {{PAGE_NUM}}
  </text>
</svg>
```

`03_content.svg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" data-pptx-layout="03_content" data-pptx-layout-name="Content">
  <!-- Jangpm — 03 Content (header/footer shell; body composed by Executor) -->

  <rect width="1280" height="720" fill="#FAFAF9" id="layout-03_content-background" data-pptx-layer="layout" data-pptx-editable="false"/>

  <!-- Headline (content slide title) -->
  <text x="56" y="96"
        font-family="Pretendard, 'Malgun Gothic', sans-serif"
        font-size="32" font-weight="700"
        letter-spacing="-0.64"
        fill="#1A1A1A"
        id="slot-03_content-title-1" data-pptx-placeholder="title">
    {{PAGE_TITLE}}
  </text>

  <!-- Optional eyebrow under headline (Label, uppercase, tracked) -->
  <text x="56" y="124"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        letter-spacing="0.64"
        fill="#6B7280">
    {{PAGE_EYEBROW}}
  </text>

  <!-- Thin accent rule under headline (editorial) -->
  <rect x="56" y="140" width="48" height="2" fill="#4633E3"/>

  <!-- CONTENT AREA (Executor fills this region freely) -->
  <!-- x=56, y=160, w=1168, h=480 — everything above GM, below headline -->

  <!-- Governing Message (GM) — mandatory on every content slide -->
  <text x="640" y="680"
        font-family="Pretendard, 'Malgun Gothic', sans-serif"
        font-size="15.2" font-weight="700"
        text-anchor="middle"
        fill="#6B7280">
    {{GOVERNING_MESSAGE}}
  </text>

  <!-- Page number (bottom right, caption) -->
  <text x="1224" y="696"
        font-family="'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        text-anchor="end"
        fill="#9CA3AF">
    {{PAGE_NUM}}
  </text>
</svg>
```

`04_ending.svg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" data-pptx-layout="04_ending" data-pptx-layout-name="Ending">
  <!-- Jangpm — 04 Ending -->

  <rect width="1280" height="720" fill="#FAFAF9" id="layout-04_ending-background" data-pptx-layer="layout" data-pptx-editable="false"/>

  <!-- Accent rule -->
  <rect x="56" y="140" width="80" height="3" fill="#4633E3"/>

  <!-- Eyebrow -->
  <text x="56" y="180"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        letter-spacing="0.64"
        fill="#6B7280">
    {{CLOSING_LABEL}}
  </text>

  <!-- Primary closing message (Display) -->
  <text x="56" y="340"
        font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="56"
        letter-spacing="-1.68"
        fill="#1A1A1A"
        id="slot-04_ending-title-1" data-pptx-placeholder="title">
    {{CLOSING_HEADLINE}}
  </text>

  <!-- Secondary line (accent) -->
  <text x="56" y="410"
        font-family="'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="40"
        letter-spacing="-0.8"
        fill="#4633E3">
    {{CLOSING_ACCENT}}
  </text>

  <!-- Contact / follow-up (Title) -->
  <text x="56" y="470"
        font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="18.4"
        fill="#1A1A1A">
    {{CONTACT_LINE}}
  </text>

  <!-- Divider -->
  <line x1="56" y1="672" x2="1224" y2="672" stroke="#E5E7EB" stroke-width="1"/>

  <!-- Presenter footer -->
  <text x="56" y="696"
        font-family="'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif"
        font-size="12.8"
        fill="#9CA3AF">
    {{PRESENTER}} · {{DATE}}
  </text>
</svg>
```

- [ ] **Step 2: 캐릭터 자산 복사**

Run (bash, repo 루트에서):
```bash
mkdir -p ".claude/skills/ppt-master/templates/decks/jangpm/images"
cp "C:/Users/byung/WorkOS/AI Work/slide-svg/.claude/skills/slide/templates/layouts/jangpm/assets/brand/jangpm-character.png" ".claude/skills/ppt-master/templates/decks/jangpm/images/jangpm-character.png"
```

- [ ] **Step 3: 검증 — XML 파싱 + 메타데이터/금지 요소 체크**

Run:
```bash
python -c "import xml.etree.ElementTree as ET, glob; paths = glob.glob('.claude/skills/ppt-master/templates/decks/jangpm/templates/*.svg'); assert len(paths) == 4, paths; [ET.parse(p) for p in paths]; print('XML OK:', len(paths))"
grep -L "data-pptx-layout=" .claude/skills/ppt-master/templates/decks/jangpm/templates/*.svg
grep -l "Apple SD Gothic\|linearGradient\|font-weight=\"800\"\|font-weight=\"600\"\|font-weight=\"500\"\|font-weight=\"400\"" .claude/skills/ppt-master/templates/decks/jangpm/templates/*.svg
```
Expected: 첫 명령 `XML OK: 4`; 둘째(메타데이터 없는 파일 목록)·셋째(금지 패턴 있는 파일 목록) 모두 **출력 없음** (grep은 exit 1이어도 정상).

- [ ] **Step 4: 커밋**

```bash
git add .claude/skills/ppt-master/templates/decks/jangpm/
git commit -m "Add jangpm deck template: SVG shells ported from slide-svg

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: deck design_spec.md 작성

**Files:**
- Create: `.claude/skills/ppt-master/templates/decks/jangpm/templates/design_spec.md`

**Interfaces:**
- Consumes: Task 1의 셸 파일명 4개 (`01_cover.svg` / `02_chapter.svg` / `03_content.svg` / `04_ending.svg`), `images/jangpm-character.png`
- Produces: `kind: deck` 프론트매터 (`deck_id: jangpm`, `summary`, `canvas_format: ppt169`, `page_count: 4`, `primary_color: "#4633E3"`) — Task 3의 `register_template.py`가 읽음; Task 4 brand 추출본의 원본

- [ ] **Step 1: design_spec.md 작성**

아래 내용 그대로 저장:

````markdown
---
deck_id: jangpm
kind: deck
native_structure_mode: template
summary: Korean editorial lecture / report decks — 강의, 워크숍, 전략 브리핑, 분석 리포트
canvas_format: ppt169
page_count: 4
primary_color: "#4633E3"
---

# Jangpm Editorial Lecture Deck - Design Specification

> Ported 2026-07-14 from the slide-svg jangpm design system (`theme.json` + `DESIGN.md`). Editorial, minimal, Korean lecture / report visual language — Notion / Linear / Vercel sensibility adapted to instructional content.

---

## I. Template Overview

| Property | Description |
| --- | --- |
| **Template Name** | jangpm |
| **Display Name** | Jangpm Editorial Lecture Deck |
| **Use Cases** | 강의, 워크숍, 전략 브리핑, 분석 리포트, 사내 교육 자료 |
| **Design Tone** | Editorial, analytical, declarative — Korean lecture / report register |
| **Theme Mode** | Light warm off-white (`#FAFAF9`) + monochrome + single indigo accent |

**Anti-mood** (reject at design time): "colorful SaaS dashboard", "marketing keynote with rainbow gradients", "PowerPoint with clip art".

**Litmus test**: 슬라이드를 잘라 한국 비즈니스 주간지에 붙여도 어색하지 않으면 통과. Reads as a *report*, not a *deck*.

---

## II. Canvas Specification

| Property | Value |
| --- | --- |
| **Format** | Standard 16:9 (`ppt169`) |
| **Dimensions** | 1280 × 720 px |
| **viewBox** | `0 0 1280 720` |
| **Page Margins** | Left/Right 56px, Top 56px, Bottom 64px (GM line reserve) |
| **Content Area** | x=56, y=160, w=1168, h=480 (content pages — below headline, above GM) |

---

## III. Color Scheme — LOCKED

Monochrome + single accent. The ONLY hex values that may appear in any generated SVG:

| Role | HEX | Token | Purpose |
| --- | --- | --- | --- |
| Background | `#FAFAF9` | `--bg` | Page background (warm off-white) |
| Surface | `#FFFFFF` | `--surface` | Card / container |
| Surface alt | `#F5F5F4` | `--surface-alt` | Grouped row / nested card |
| Text primary | `#1A1A1A` | `--text` | Main text (never pure `#000`) |
| Text secondary | `#6B7280` | `--text-secondary` | Secondary text, GM line |
| Text tertiary | `#9CA3AF` | `--text-tertiary` | Captions, page numbers |
| Border | `#E5E7EB` | `--border` | Default divider / hairline |
| Border strong | `#D4D4D4` | `--border-strong` | Emphasis divider |
| Accent | `#4633E3` | `--accent` | Sole brand pointer |
| Accent soft | `#E8E5FC` | `--accent-soft` | Accent-tinted highlight bg, recommended column |
| Accent ink | `#2E1FB3` | `--accent-ink` | Accent pressed / dark |
| Positive | `#059669` | `--positive` | Data context only — growth / success |
| Negative | `#E11D48` | `--negative` | Data context only — decline / error |
| Warning | `#D97706` | `--warning` | Data context only — caution |

### Color Rules

- **Monochrome first**: every slide must read in grayscale before accent is applied
- **Accent budget ≤ 2 events per content slide** — an "event" is any of: accent text fill, accent-soft container, accent-stroked emphasis rule. More than two cancels the pointer effect
- **Background hierarchy ladder**: `#FAFAF9` (page) → `#F5F5F4` (grouped) → `#FFFFFF` (focal card) → `#E8E5FC` (highlighted card). Drop one rung at a time; skipping rungs reads as visual stuttering
- **Semantic colors are data-only**: `--positive` / `--negative` / `--warning` only when the color encodes a meaning the reader must decode (trend arrow, status pill) — never decorative
- **Charts use the single-accent opacity ladder**: `rgba(70, 51, 227, 0.85 / 0.60 / 0.40 / 0.25)`. Multi-hue palettes are forbidden
- **Card differentiation**: in any card grid, exactly one card is visually distinct (accent-soft bg or highlighted metric); equal-weight grids are a design smell
- **Forbidden**: gradients (`<linearGradient>` / `<radialGradient>`), drop shadows, glow, 3D effects

---

## IV. Typography System

Install-local Pretendard lock (see `references/strategist.md` §g). Weight cuts are authored as installed family names:

| Weight | `font-family` attribute | `font-weight` |
| --- | --- | --- |
| 400 | `Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 500 | `'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 600 | `'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 700 | `Pretendard, 'Malgun Gothic', sans-serif` | `700` |
| 800 | `'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif` | (none) |

Type scale (px values verbatim from the jangpm system — report density):

| Role | Size (px) | Weight | Line-height | Letter-spacing | Use |
| --- | --- | --- | --- | --- | --- |
| Display | 56 | 800 | 1.08 | -1.68 | cover / chapter / closing hero |
| Display-sm | 40 | 800 | 1.10 | -0.8 | hero stat, closing accent, chapter number |
| Headline | 32 | 700 | 1.20 | -0.64 | content slide title |
| Title | 18.4 | 600 | 1.30 | 0 | card title, subtitle |
| Body | 15.2 | 400 | 1.60 | 0 | body text (report-density default) |
| Caption | 12.8 | 500 | 1.40 | 0 | annotations, page numbers |
| Label | 12.8 | 600 | 1.40 | 0.64 | uppercase eyebrow / taxonomy (`text-transform: uppercase` — author label text ALREADY uppercase in SVG) |

- **Display vs Headline**: Display is reserved for cover / chapter / closing slides; content slides use Headline. Title never breaks across lines
- **Body 15.2px** is the report-density baseline. Low-density decks (3–4 items/page) may raise body to 18.4px — exception, not norm
- **Label** uppercase + 0.64 tracking only when the text labels a taxonomy/category; regular captions stay sentence-case

---

## V. Page Structure

### Page anatomy (content pages, 1280×720)

```
┌─────────────────────────────────────────────┐
│ Headline           (y≈96)   32/700          │
│ Eyebrow (optional) (y≈124)  12.8/600 upper  │
│ Accent rule        (y=140)  48×2 #4633E3    │
│ Body               (y: 160–640, h: 480)     │
│ GM line            (y=680, centered)        │
│ Page number        (y=696, right)  01 / 12  │
└─────────────────────────────────────────────┘
```

### GM (Governing Message) line — non-negotiable

- **Every content slide** carries exactly one GM line: y=680, centered (x=640), 15.2px weight 700, `#6B7280`
- Voice: declarative third-person institutional, Korean-first, ≤ 30 chars ideal
- The GM is the editorial *so-what* / takeaway — **NEVER a restatement of the page title**
- Forbidden phrases: 여러분, 우리는, 함께해요
- Cover / chapter / ending pages carry **no** GM line

### Footer

- Page number bottom-right (`#9CA3AF`, 12.8/500, format `01 / 12`) on chapter + content pages
- Brand character / mark bottom-left **only** on cover and ending

---

## VI. Page Types

### 1. Cover (01_cover.svg)

Accent rule (80×3) + uppercase eyebrow + Display title + optional Display-sm accent second line + Title subtitle + presenter/date body line + bottom hairline. No GM, no page number.

### 2. Chapter (02_chapter.svg)

Display-sm accent chapter number + uppercase chapter label + Display chapter title + secondary-color summary line + bottom hairline + page number. Insert every 4–6 body slides for decks ≥ 12 pages; optional for short decks.

### 3. Content (03_content.svg)

Headline + optional eyebrow + accent rule (48×2); **body region (x=56, y=160, w=1168, h=480) is composed freely by the Executor** using §VIII patterns while preserving the headline / GM / page-number chrome. GM line mandatory.

### 4. Ending (04_ending.svg)

Mirror of cover: accent rule + eyebrow + Display closing message + Display-sm accent line + contact line + presenter/date footer. No GM.

> **No TOC shell**: 아젠다/목차는 content(body) 페이지로 자유 구성한다 — `ruled-list-with-eyebrow` 패턴 권장. 별도 TOC 레이아웃을 만들지 않는 것이 jangpm 원본 설계다.

---

## VII. SVG Page Roster

| File | Role | Description |
| --- | --- | --- |
| `01_cover.svg` | cover | Title slide; program label, title, subtitle, presenter/date |
| `02_chapter.svg` | chapter | Section divider; chapter number + label + title + summary |
| `03_content.svg` | content | Content shell (headline / GM / page number); body composed freely |
| `04_ending.svg` | ending | Closing; message + accent line + contact |

---

## VIII. Layout Patterns (Editorial Grammar)

### Signature patterns ★ — first choice for list-of-items / parallel components

**`ruled-list-with-eyebrow`** ★ — uppercase eyebrow + horizontal hairline + stack of `bold-label : body-text` rows separated by hairlines. NO card boxes, NO `rx` containment.

```
EYEBROW LABEL              ← 12.8 / SemiBold / 0.64 tracking / #6B7280 / uppercase
─────────────────          ← <line stroke="#E5E7EB" stroke-width="1"/>
ROW 1 LABEL    BODY TEXT   ← label: 15.2/700/#1A1A1A, body: 15.2/400/#6B7280
─────────────────
ROW 2 LABEL    BODY TEXT
─────────────────
```

**`columns-with-vertical-rules`** ★ — uppercase eyebrow + horizontal hairline + 3–4 columns separated by full-height vertical hairlines (`#E5E7EB` 1px). Each column = bold title + body lines, no surrounding `<rect>`. Bottom hairline closes the section.

**Implementation discipline for ★ patterns:**
- Hairlines are `<line ... stroke="#E5E7EB" stroke-width="1"/>` — NOT thin `<rect>` strips
- NO `<rect rx="12">` wrapping the list/columns — that turns it back into a card
- The eyebrow (Label style) is the only typographic flag the section needs
- One accent event per section is enough — usually a single accent-soft horizontal band at the bottom for the verdict/takeaway

### Content shape → first-choice pattern

| Content shape | First choice | Composition |
| --- | --- | --- |
| List of items with name + description (3–6) | ★ `ruled-list-with-eyebrow` | eyebrow + hairline rows |
| Parallel concepts / pillars / categories (3–4) | ★ `columns-with-vertical-rules` | eyebrow + vertical-rule columns |
| Numeric evidence / growth / share / forecast | `chart-led-with-takeaway-stack` | left chart ≈60% + right 2–3 stacked takeaway cards |
| Structured comparison (A vs B / matrix) | `table-with-adjacent-cards` | left table ≈55% + right mini-cards; one column accent-soft |
| Time-ordered / step-ordered methodology | `process-with-callout-band` | numbered step row + bottom accent-soft rule-of-thumb band |
| Stat-anchored decomposition | `breakdown-with-anchor-stat` | top Display-sm hero stat + bottom 1×3/1×4 cards |
| Single-thought body insight (definition / metaphor) | `definition-with-side-data` / `paired-concept-asymmetric` | concept 50% + paired evidence visual 50% |
| Quote / voice evidence | `quote-with-attribution-data` | pull quote + attribution + 1 supporting data card |

★ patterns are the jangpm signature but NOT a universal default — data/comparison/process content takes its own first-choice pattern above. Falling back to ★ for every slide produces "monolithic gray editorial" decks.

### Variation discipline

- Every body slide applies **exactly ONE intentional variation** of its pattern (hero first row, accent-soft row/column highlight, rightmost number column, asymmetric widths, one dark card `#1A1A1A`, verdict band closer, numbered eyebrow, inline mini-chart, …) — or is consciously marked standard
- Same variation type ≤ 2 uses per deck; target ≥ 70% of body slides on a non-standard variation
- The pattern's silhouette must remain recognizable; stacking 2+ variations on one slide is forbidden
- No consecutive identical patterns (except chapter); minimum 3 layout types per deck

### Density floors

- Every card has ≥ 3 content layers (icon/badge + title + body + caption/metric); 2-layer cards read as unfinished
- **No text-only slides** — every content slide carries ≥ 1 visual element (chart, diagram, micro-chart, ruled structure, icon group)
- Stats include context ("vs industry avg 3.2%"); bare numbers read as placeholder
- Single-chart container height ≥ 400px
- Bounded by: one dominant message, ≤ 3 bullets, ≥ 30% whitespace, clear quiet zone — "dense" means a dominant evidence visual, never a text wall

---

## IX. Spacing Specification

| Element | Value |
| --- | --- |
| Grid | 8px 배수 (4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 56 / 64) |
| Slide outer padding | 56px (bottom 64px, GM reserve) |
| Card padding | 24px |
| Card gap | 24px |
| Card border radius | 12px |
| Internal card stacking | 5–8px between icon → label → metric → context; never > 24px empty gap inside a card |
| Hairline divider | 1px `#E5E7EB` |
| Emphasis rule | 2px |

---

## X. Placeholder Specification

Templates use `{{PLACEHOLDER}}` tokens:

| Shell | Placeholders |
| --- | --- |
| `01_cover.svg` | `{{EYEBROW}}` `{{TITLE}}` `{{TITLE_ACCENT}}`* `{{SUBTITLE}}` `{{PRESENTER}}` `{{DATE}}` |
| `02_chapter.svg` | `{{CHAPTER_NUMBER}}` `{{CHAPTER_LABEL}}` `{{CHAPTER_TITLE}}` `{{CHAPTER_SUMMARY}}` `{{PAGE_NUM}}` |
| `03_content.svg` | `{{PAGE_TITLE}}` `{{PAGE_EYEBROW}}`* `{{GOVERNING_MESSAGE}}` `{{PAGE_NUM}}` |
| `04_ending.svg` | `{{CLOSING_LABEL}}` `{{CLOSING_HEADLINE}}` `{{CLOSING_ACCENT}}`* `{{CONTACT_LINE}}` `{{PRESENTER}}` `{{DATE}}` |

\* optional — delete the whole `<text>` element when unused. `{{PAGE_NUM}}` format: `01 / 12`.

---

## XI. Icon System

- **Library lock**: `templates/icons/tabler-outline/` (2px stroke line-art). Fallback `tabler-filled` only when an editorial reason demands a solid glyph. **Forbidden**: `chunk` pack, emoji, unicode glyph icons, mixing packs in one deck
- Usage: `<use data-icon="tabler-outline/<name>" x="…" y="…" width="…" height="…" fill="none" stroke="currentColor" stroke-width="2"/>` — `finalize_svg.py` resolves the glyph; do NOT inline SVG content
- Search before use: `ls .claude/skills/ppt-master/templates/icons/tabler-outline/ | grep <keyword>` — cite verified filenames only
- **Bare icons only**: no circle wrappers, no colored badges, no semantic-soft backplates
- Sizes: card icon 28–32px, hero icon 56–64px, inline icon 16px
- Number badges (01–04) only when sequential order is the primary information; icon + number mix across sections is allowed

---

## XII. Chart & Table Treatment

### Charts

- Single-accent opacity ladder `rgba(70, 51, 227, 0.85 / 0.60 / 0.40 / 0.25)`; multi-series uses opacity tiers, not hue tiers
- Semantic exception: growth bar `#059669`, decline bar `#E11D48` only when color encodes data meaning
- No legend chrome — inline labels at the end of each line/bar; data labels on the chart itself, accent for the focus value
- Axis labels `#6B7280`, 12.8/500. No drop shadows, no 3D, no gradient fills
- Role mapping: growth-trend → line; focus-comparison → bar with one accent bar (others grayscale); share/proportion → pie ≤ 6 segments; forecast → line with dashed lighter-opacity right region; funnel → decreasing-width nodes
- **Required adjacency**: every data slide pairs the chart with a takeaway card (1 metric Display-sm + 1 trend annotation + 1 contextual line). A chart without a takeaway is rejected

### Tables

- Header row: `#F5F5F4` background, Label typography (uppercase, 0.64 tracking)
- Recommended column: `#E8E5FC` background + 2px accent left border — comparison tables need a winner
- Cell text: body 15.2; numerics right-aligned
- Verdict row at the bottom summarizing the recommendation in one sentence

---

## XIII. Asset Specification

| File | Usage |
| --- | --- |
| `../images/jangpm-character.png` | Brand character — cover / ending bottom-left only, optional; never on content pages; never scaled above ~120px height |

---

## XIV. Anti-Pattern Checklist (reject at authoring time)

- [ ] Accent events > 2 on one slide
- [ ] Any hex outside §III table
- [ ] Gradient / drop-shadow / glow / 3D
- [ ] GM restating the page title, or containing 여러분 / 우리는 / 함께해요
- [ ] Text-only slide (no visual element)
- [ ] Equal-weight card grid (no distinct card)
- [ ] 2-layer cards (icon + title only)
- [ ] Emoji or unicode glyph icons; icon pack mixing
- [ ] Line break inside a title
- [ ] Same pattern 3+ consecutive slides; same variation type 3+ uses
- [ ] Multi-hue chart palette; chart without takeaway card

---

## XV. Usage Instructions

1. SKILL.md Step 3에 이 워크스페이스 경로를 명시적으로 전달: `.claude/skills/ppt-master/templates/decks/jangpm/`
2. deck kind이므로 Strategist가 identity + structure를 모두 잠근다; 확인 단계에서 template adherence(`strict` / `adaptive`)를 선택한다. Stage 2에서 이 스킨(색/타이포)이 추천 후보로 제시된다
3. Executor는 `03_content.svg`의 콘텐츠 영역(x=56, y=160, w=1168, h=480)을 §VIII 문법으로 자유 구성하되 headline / GM / page-number 크롬을 보존한다
4. Identity만 재사용하려면 brand 추출본 `.claude/skills/ppt-master/templates/brands/jangpm/`을 다른 layout/deck과 융합한다
````

- [ ] **Step 2: 검증 — 프론트매터 필드 + 허용 HEX 확인**

Run:
```bash
python -c "
import re
text = open('.claude/skills/ppt-master/templates/decks/jangpm/templates/design_spec.md', encoding='utf-8').read()
fm = text.split('---')[1]
for key in ('deck_id: jangpm', 'kind: deck', 'canvas_format: ppt169', 'page_count: 4', 'primary_color'):
    assert key in fm, key
allowed = {'#FAFAF9','#FFFFFF','#F5F5F4','#1A1A1A','#6B7280','#9CA3AF','#E5E7EB','#D4D4D4','#4633E3','#E8E5FC','#2E1FB3','#059669','#E11D48','#D97706','#000'}
bad = set(re.findall(r'#[0-9A-Fa-f]{3,6}\b', text)) - allowed
assert not bad, bad
print('spec OK')
"
```
Expected: `spec OK` (`#000`은 "never pure #000" 서술 안의 문자열이라 허용 목록에 포함).

- [ ] **Step 3: 커밋**

```bash
git add .claude/skills/ppt-master/templates/decks/jangpm/templates/design_spec.md
git commit -m "Add jangpm deck design_spec: color/type lock, GM contract, editorial grammar

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: deck 등록

**Files:**
- Modify: `.claude/skills/ppt-master/templates/decks/decks_index.json` (스크립트가 수정)

**Interfaces:**
- Consumes: Task 2의 프론트매터 (`deck_id: jangpm`, `summary`, `canvas_format`, `page_count`, `primary_color`)
- Produces: `decks_index.json`의 `"jangpm"` 엔트리 — Step 3 out-of-band 질의("어떤 템플릿 있어?")가 읽음

- [ ] **Step 1: 등록 스크립트 실행**

Run:
```bash
python .claude/skills/ppt-master/scripts/register_template.py jangpm --kind deck
```
Expected: exit 0. 실패 시 에러 메시지가 지목하는 프론트매터/구조 문제를 고치고 재실행 (스크립트가 워크스페이스 정합성을 검사한다).

- [ ] **Step 2: 인덱스 확인**

Run:
```bash
python -c "
import json
idx = json.load(open('.claude/skills/ppt-master/templates/decks/decks_index.json', encoding='utf-8'))
e = idx['jangpm']
assert e['canvas_format'] == 'ppt169' and e['page_count'] == 4 and e['primary_color'] == '#4633E3', e
print('index OK:', e['summary'])
"
```
Expected: `index OK: Korean editorial lecture / report decks — 강의, 워크숍, 전략 브리핑, 분석 리포트`

- [ ] **Step 3: 커밋**

```bash
git add .claude/skills/ppt-master/templates/decks/decks_index.json
git commit -m "Register jangpm deck in decks_index

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: brand 추출본 작성

**Files:**
- Create: `.claude/skills/ppt-master/templates/brands/jangpm/templates/design_spec.md`
- Create: `.claude/skills/ppt-master/templates/brands/jangpm/images/jangpm-character.png` (deck 것 복사)

**Interfaces:**
- Consumes: Task 2 deck spec §III(색)·§IV(타이포 패밀리/웨이트) 값 — 이 brand는 그 identity 미러
- Produces: `kind: brand` 프론트매터 (`brand_id: jangpm`) — Task 5 등록이 읽음; Step 3 융합(brand + 타 layout/deck)의 identity 소스

- [ ] **Step 1: brand design_spec.md 작성**

아래 내용 그대로 저장:

````markdown
---
brand_id: jangpm
kind: brand
summary: Jangpm editorial identity — Korean lecture / report decks, 모노크롬 + 단일 인디고 액센트
keywords: [editorial, minimal, korean, lecture, report]
primary_color: "#4633E3"
---

# Jangpm Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
>
> **Provenance**: extracted from [`templates/decks/jangpm/`](../../../decks/jangpm/templates/design_spec.md) (source of truth). 색/타이포/보이스 변경은 deck에서 먼저 고치고 이 파일에 동기화한다. 페이지 구조·레이아웃 문법·GM 위치는 deck 소관이며 여기 기록하지 않는다.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Jangpm |
| Use Cases | 강의, 워크숍, 전략 브리핑, 분석 리포트, 사내 교육 자료 |
| Tone | Editorial, analytical, declarative — Korean lecture / report register |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| bg | `#FAFAF9` | fact | Warm off-white page background |
| surface | `#FFFFFF` | fact | Card / container |
| surface-alt | `#F5F5F4` | fact | Grouped row / nested card |
| text | `#1A1A1A` | fact | Primary text — never pure `#000` |
| text-secondary | `#6B7280` | fact | Secondary text |
| text-tertiary | `#9CA3AF` | fact | Captions, page numbers |
| border | `#E5E7EB` | fact | Default divider / hairline |
| border-strong | `#D4D4D4` | fact | Emphasis divider |
| primary (accent) | `#4633E3` | fact | Sole brand pointer — indigo |
| accent-soft | `#E8E5FC` | fact | Accent-tinted highlight background |
| accent-ink | `#2E1FB3` | fact | Accent pressed / dark |
| positive | `#059669` | fact | Data context only — growth / success |
| negative | `#E11D48` | fact | Data context only — decline / error |
| warning | `#D97706` | fact | Data context only — caution |

All values extracted verbatim from the jangpm `theme.json` (slide-svg). Usage conventions that travel with the identity: monochrome-first (slides must read in grayscale before accent); accent budget ≤ 2 events per slide; semantic colors (positive/negative/warning) are data-meaning only, never decorative; gradients / drop shadows / glow forbidden; charts use the single-accent opacity ladder `rgba(70, 51, 227, 0.85 / 0.60 / 0.40 / 0.25)`, never multi-hue.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif` (display) / `Pretendard, 'Malgun Gothic', sans-serif` + `font-weight: 700` (headline) | 700–800 |
| body | `Pretendard, 'Malgun Gothic', sans-serif` | 400 |
| sub / card title | `'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif` | 600 |

> Install-local Pretendard lock (`references/strategist.md` §g): intermediate weights are authored as installed family names. Size hierarchy / type scale is deck-layout scope — see the jangpm deck spec §IV; not locked here.

## IV. Logo

- None. The brand has no logo mark; see §VII for the character asset (optional decoration, not a logo).

## V. Voice & Tone

- Formality: professional-neutral
- Person: third-person institutional (직접 호명 없음)
- Emoji: forbidden
- Abbreviations: spell-out-first-use
- Forbidden phrases: 여러분 / 우리는 / 함께해요
- Takeaway style: one declarative so-what sentence per slide, Korean-first, ≤ 30 chars ideal, never restating the title

## VI. Icon Style

- Preference: stroke

> `tabler-outline` line-art, 2px stroke, bare icons only — no circle wrappers, no colored badges, no pack mixing, no emoji. Fallback `tabler-filled` only for a deliberate solid glyph.

## VII. Visual Assets

- Images and illustrations: `../images/` — `jangpm-character.png` (브랜드 캐릭터; 커버/엔딩 하단 한정, 선택적)
````

- [ ] **Step 2: 캐릭터 자산 복사**

Run:
```bash
mkdir -p ".claude/skills/ppt-master/templates/brands/jangpm/images"
cp ".claude/skills/ppt-master/templates/decks/jangpm/images/jangpm-character.png" ".claude/skills/ppt-master/templates/brands/jangpm/images/jangpm-character.png"
```

- [ ] **Step 3: 검증 — deck spec과 색 값 일치 확인**

Run:
```bash
python -c "
import re
deck = open('.claude/skills/ppt-master/templates/decks/jangpm/templates/design_spec.md', encoding='utf-8').read()
brand = open('.claude/skills/ppt-master/templates/brands/jangpm/templates/design_spec.md', encoding='utf-8').read()
tokens = ['#FAFAF9','#FFFFFF','#F5F5F4','#1A1A1A','#6B7280','#9CA3AF','#E5E7EB','#D4D4D4','#4633E3','#E8E5FC','#2E1FB3','#059669','#E11D48','#D97706']
missing = [t for t in tokens if t not in brand or t not in deck]
assert not missing, missing
assert 'brand_id: jangpm' in brand and 'kind: brand' in brand
print('brand mirror OK')
"
```
Expected: `brand mirror OK`

- [ ] **Step 4: 커밋**

```bash
git add .claude/skills/ppt-master/templates/brands/jangpm/
git commit -m "Add jangpm brand extract: identity-only mirror of the jangpm deck

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: brand 등록

**Files:**
- Modify: `.claude/skills/ppt-master/templates/brands/brands_index.json` (스크립트가 수정)

**Interfaces:**
- Consumes: Task 4의 프론트매터 (`brand_id: jangpm`, `summary`, `primary_color`)
- Produces: `brands_index.json`의 `"jangpm"` 엔트리

- [ ] **Step 1: 등록 + 인덱스 확인**

Run:
```bash
python .claude/skills/ppt-master/scripts/register_template.py jangpm --kind brand
python -c "
import json
idx = json.load(open('.claude/skills/ppt-master/templates/brands/brands_index.json', encoding='utf-8'))
assert idx['jangpm']['primary_color'] == '#4633E3', idx.get('jangpm')
print('brand index OK:', idx['jangpm']['summary'])
"
```
Expected: 두 명령 모두 exit 0, 마지막 줄 `brand index OK: …`.

- [ ] **Step 2: 커밋**

```bash
git add .claude/skills/ppt-master/templates/brands/brands_index.json
git commit -m "Register jangpm brand in brands_index

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: 리뷰 덱 생성 + 시각 검증

**Files:**
- Create (git-ignored, 커밋 금지): `.claude/skills/ppt-master/templates/decks/jangpm/exports/…` (스크립트 산출)

**Interfaces:**
- Consumes: Task 1–3 완성된 deck 워크스페이스
- Produces: 리뷰 PPTX — 사람이 원본과 대조하는 최종 게이트

- [ ] **Step 1: 리뷰 덱 생성**

Run:
```bash
python .claude/skills/ppt-master/scripts/template_preview_pptx.py ".claude/skills/ppt-master/templates/decks/jangpm"
```
Expected: exit 0, 산출 PPTX 경로 출력 (워크스페이스 `exports/` 아래). (플랫 계약 라이브러리 덱은 `--visual-only` 플래그가 필요함 — 실행 시 확인됨)

- [ ] **Step 2: 시각 대조**

생성된 PPTX의 4페이지를 원본 프리뷰와 대조한다 — 원본: `C:\Users\byung\WorkOS\AI Work\slide-svg\.claude\skills\slide\templates\layouts\jangpm\_preview\01_cover.png … 04_ending.png`. OfficeCLI가 있으면 스크린샷으로, 없으면 PowerPoint로 열어 확인. 체크 항목:
- 배경 `#FAFAF9` (순백 아님), 액센트 룰 위치(커버/엔딩 y=140, 콘텐츠 y=140 48×2)
- 타이틀 웨이트가 ExtraBold로 렌더 (Pretendard 미설치 폴백이면 Regular로 보임 — 이 머신엔 설치됨)
- 헤어라인 1px `#E5E7EB`, GM 라인 중앙 y=680, 페이지 번호 우하단
- 레이아웃이 원본 PNG와 동일한 실루엣

- [ ] **Step 3: exports 미커밋 확인 + 종료**

Run:
```bash
git status --porcelain
```
Expected: 출력 없음 (`exports/`는 ignore). 무언가 나오면 원인 확인 — `exports/`가 스테이징되면 안 된다.

시각 대조에서 차이가 발견되면 해당 셸/spec을 수정하고 Task 1/2의 검증 단계를 재실행한 뒤 수정 커밋을 만든다.
