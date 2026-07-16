---
deck_id: jangpm
kind: deck
native_structure_mode: structured
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
| Headline metrics at a glance (exec summary, 4–8 KPIs) | `kpi-metric-grid` | 2×N white cards (rx 12, hairline border) — Caption label + Display-sm(40/800) value + semantic delta line (▲/▼, data-only green/red); exactly ONE card accent-soft highlighted per the card-differentiation rule |
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
