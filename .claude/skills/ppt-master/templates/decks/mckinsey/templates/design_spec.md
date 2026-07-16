---
deck_id: mckinsey
kind: deck
native_structure_mode: structured
summary: McKinsey consulting-style strategy decks — 전략 보고서, 시장/산업 분석, 경영진 브리핑, 실행 로드맵
canvas_format: ppt169
page_count: 5
primary_color: "#0F2A4A"
---

# McKinsey Consulting Style Deck - Design Specification

> Style homage benchmarked 2026-07-15 from the [seulee26/mckinsey-pptx](https://github.com/seulee26/mckinsey-pptx) generator (`theme.py` tokens + 40-template catalog, MIT). Not an official McKinsey identity — no trademark assets are bundled; color values are third-party approximations. Typography follows this repository's install-local Pretendard lock, reproducing the consulting hierarchy through weight/size only.

---

## I. Template Overview

| Property | Description |
| --- | --- |
| **Template Name** | mckinsey |
| **Display Name** | McKinsey Consulting Style Deck |
| **Use Cases** | 전략 보고, 시장/산업 분석, 경영진 브리핑, 실행 로드맵, 투자 검토, 조직 진단 |
| **Design Tone** | Restrained, hypothesis-driven, evidence-first — MBB consulting register |
| **Theme Mode** | Light white pages + dark-navy structural pages (chapter / ending) |

**Anti-mood** (reject at design time): "marketing keynote", "gradient SaaS dashboard", "decorative infographics", "rounded-corner card deck".

**Litmus test**: 페이지의 액션 타이틀만 연달아 읽어도 스토리라인(피라미드 구조)이 완결되면 통과. Titles argue; bodies prove.

---

## II. Canvas Specification

| Property | Value |
| --- | --- |
| **Format** | Standard 16:9 (`ppt169`) |
| **Dimensions** | 1280 × 720 px |
| **viewBox** | `0 0 1280 720` |
| **Page Margins** | Left/Right 44px (x: 44 → 1236), bottom reserve 44px |
| **Title band** | Kicker + action title above the title rule (y=112) |
| **Content Area** | x=44, y=136, w=1192, h=524 (content pages — below title rule, above footer rule) |

Geometry is an exact 96px/in mapping of the benchmark's 13.333×7.5in chrome: margins 0.45in→44px, title rule 1.15in→112px, body top 1.40in→136px, footer rule 7.05in→676px.

---

## III. Color Scheme — LOCKED

Navy structure + single cyan pointer. The ONLY hex values that may appear in any generated SVG:

| Role | HEX | Token | Purpose |
| --- | --- | --- | --- |
| Background | `#FFFFFF` | `--bg` | Page background (pure white) |
| Primary navy | `#0F2A4A` | `--navy` | Structural anchor: cover band, kicker, table headers, key numbers, chart series 1 |
| Deep navy | `#0A1F3D` | `--navy-deep` | Full-bleed background for chapter / ending pages |
| Accent | `#2E9BD6` | `--accent` | Sole pointer: focus bar/series, emphasis rule, highlight number |
| Blue mid | `#1F6FA8` | `--blue-mid` | Chart series 2 |
| Blue light | `#4FB2E5` | `--blue-light` | Chart series 3, tint fills, secondary text on dark pages |
| Text | `#1A1A1A` | `--text` | Body text (never pure `#000`) |
| Text secondary | `#888888` | `--text-secondary` | Source line, page number, captions, secondary text |
| Title rule | `#999999` | `--rule` | Title underline rule only |
| Grid | `#D0D0D0` | `--grid` | Footer rule, chart gridlines |
| Border | `#E8E8E8` | `--border` | Hairline dividers, table row rules |
| Surface alt | `#F2F2F2` | `--surface-alt` | Table banding, quiet panel background |
| Positive | `#4CAF50` | `--positive` | Traffic light "on track" — data context only |
| Warning | `#F4C57A` | `--warning` | Traffic light "at risk" — data context only |
| Negative | `#E04E5E` | `--negative` | Traffic light "off track" — data context only |

**Provenance**: all values `approx` — derived from the seulee26/mckinsey-pptx benchmark `theme.py`, not official McKinsey brand truth. The benchmark's `#2A2AE5` (royal blue) and `#BFBFBF` (placeholder gray) are deliberately excluded as single-use outliers that break the navy/cyan system.

### Color Rules

- **Navy is structure, accent is pointer**: `#0F2A4A` carries chrome and hierarchy; `#2E9BD6` marks the one thing the reader must see
- **Single-focus accent rule**: accent points at exactly ONE focus per page (entity / series / number / cell). Repetition across exhibits is allowed only when marking the SAME focus — the focus series in chart A and that entity's row in table B count as one focus; highlighting two different targets on one page is forbidden
- **Verdict rule is a separate structural account**: the 2px accent rule of a verdict band is a fixed structural convention — max 1 per page, inside the takeaway zone, not counted against the data focus
- **Everything else stays achromatic**: remaining hierarchy is carried by weight, navy, banding, and hairlines — never by additional accent events
- **Grayscale first**: every slide must read in grayscale before blue is applied
- **Chart ladder**: multi-series charts use `#0F2A4A → #1F6FA8 → #4FB2E5` in that order; `#2E9BD6` is reserved for the single focus series/bar — and only when that series/bar is the page's single focus. Multi-hue palettes are forbidden
- **Traffic lights are data-only**: `--positive` / `--warning` / `--negative` only when color encodes a status the reader must decode, always paired with a text label or shape (legible without color) — never decorative
- **Dark pages** (chapter / ending) use `--navy-deep` full-bleed with white Display type, `--accent` rules, `--blue-light` secondary text
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

Type scale (exact pt→px conversions of the benchmark ramp; 1pt = 1.333px):

| Role | Size (px) | Weight | Line-height | Letter-spacing | Use |
| --- | --- | --- | --- | --- | --- |
| Display | 48 | 700 | 1.10 | -0.96 | cover title, chapter title, closing message (white on dark pages) |
| Display-sm | 40 | 700 | 1.10 | -0.8 | chapter number, hero stat anchor |
| Action Title | 32 | 700 | 1.20 | -0.64 | content-page action title (= 24pt); up to 2 lines |
| Title | 18.7 | 600 | 1.30 | 0 | exhibit / card titles, agenda items (= 14pt) |
| Body | 16 | 400 | 1.50 | 0 | body text, table cells (= 12pt) |
| Small | 13.3 | 500 | 1.40 | 0 | chart labels, axis text, annotations (= 10pt) |
| Label | 13.3 | 600 | 1.40 | 0.6 | uppercase kicker / taxonomy (author label text ALREADY uppercase in SVG) |
| Footer | 12 | 400 | 1.40 | 0 | source line, page number, confidentiality tag (= 9pt, `#888888`) |

- **Display vs Action Title**: Display is reserved for cover / chapter / ending; content pages use Action Title
- **Action Title may break into 2 lines** (bounds allow 68px); it is a full sentence, not a label — see §V
- **Stat hero exception**: a single-number impact page may scale the number to 64–96px weight 700 `--navy`

---

## V. Page Structure

### Page anatomy (content pages, 1280×720)

```
┌──────────────────────────────────────────────────┐
│ Kicker (optional)   (y≈32)  13.3/600 upper navy  │
│ ACTION TITLE        (y≈68, line 2 ≈104)  32/700  │
│ Title rule          (y=112) 1px #999999 44→1236  │
│ Body                (y: 136–660, 1192×524)       │
│ Footer rule         (y=676) 1px #D0D0D0 44→1236  │
│ Source line (left, y≈698) 12px | Page # (right)  │
└──────────────────────────────────────────────────┘
```

### Action title doctrine — non-negotiable

- **The action title IS the governing message.** Every content-page title is a complete declarative sentence stating the so-what ("시장은 정체되어 있다", not "시장 현황"). There is no separate takeaway line — the bottom band belongs to the source convention
- Reading the action titles in page order must reconstruct the full storyline (pyramid principle)
- Forbidden: label-only titles on evidence pages, question-mark titles on evidence pages, direct address (여러분 / 우리는 / 함께해요)

### Source line convention

- **Every evidence page** carries a `Source:` / `자료:` line at bottom-left (12px, `#888888`) — data provenance, or explicitly `Source: 내부 분석`
- Page number bottom-right, format `01 / 12` (12px, `#888888`)
- Dark pages (chapter / ending) carry no source line; cover carries no page number

---

## VI. Page Types

### 1. Cover (01_cover.svg)

Navy top band (8px full-width) + uppercase kicker + navy title rule block + Display title + Title subtitle + presenter/date line + bottom hairline + optional confidentiality tag (top-right) and organization line. No page number.

### 2. Agenda (02_toc.svg)

Action-title chrome without the full-width rule (short navy bar instead) + ruled agenda rows: hanging navy number (Display-sm) + item title (Title 18.7/600) + one-line description (Body 16/400 secondary). 3–5 rows; hairline between rows.

### 3. Chapter (02_chapter.svg)

Full-bleed `--navy-deep` + accent chapter number (Display-sm, `#2E9BD6`) + accent rule + Display chapter title (white, left-aligned) + summary line (`#4FB2E5`) + page number. Insert every 4–6 body slides for decks ≥ 12 pages.

### 4. Content (03_content.svg)

Kicker + action title + title rule (y=112) + footer rule (y=676) + source line + page number; **body region (x=44, y=136, w=1192, h=524) is composed freely by the Executor** using §VIII patterns while preserving the chrome.

### 5. Ending (04_ending.svg)

Full-bleed `--navy-deep`, centered composition: uppercase closing label + accent rule + Display closing message (white, centered) + contact line + presenter/date footer. No source line.

---

## VII. SVG Page Roster

| File | Role | Description |
| --- | --- | --- |
| `01_cover.svg` | cover | Title slide; kicker, title, subtitle, presenter/date, confidentiality tag |
| `02_toc.svg` | toc | Agenda; numbered ruled list of chapters |
| `02_chapter.svg` | chapter | Dark-navy section divider; chapter number + title + summary |
| `03_content.svg` | content | Action-title content shell; body composed freely by Executor |
| `04_ending.svg` | ending | Dark-navy closing; centered message + contact |

---

## VIII. Layout Patterns (Consulting Grammar)

### Signature pattern ★

**`numbered-takeaway-stack`** ★ — executive-summary grammar: 3–5 full-sentence findings, each with a hanging navy number (Display-sm `--navy`), a bold one-line finding (Title 18.7/600), 1–2 supporting lines (Body 16/400 `#888888`), separated by hairlines (`#E8E8E8`). NO card boxes, NO rounded containment.

```
01   시장 성장은 프리미엄 세그먼트에 집중된다        ← 18.7/600 #1A1A1A
     프리미엄 세그먼트 CAGR 12% vs 전체 3%          ← 16/400 #888888
──────────────────────────────────────            ← <line stroke="#E8E8E8"/>
02   경쟁사는 이미 채널 전환을 완료했다
     ...
```

### Content shape → first-choice pattern

| Content shape | First choice | Composition |
| --- | --- | --- |
| Executive summary / key findings (3–5) | ★ `numbered-takeaway-stack` | hanging numbers + hairline rows |
| Status / KPI assessment | `traffic-light-table` | `templates/charts/consulting_table.svg`, `harvey_balls_table.svg`; status circle + label |
| Prioritization / portfolio (2 axes) | 2×2 matrix / bubble | `templates/charts/matrix_2x2.svg`, `quadrant_bubble_scatter.svg` |
| Phased roadmap / plan | gantt / chevron / timeline | `templates/charts/gantt_chart.svg`, `chevron_process.svg`, `timeline.svg` |
| Quantified driver story | `chart-led-with-takeaway` | left chart ≈60% + right stacked takeaways; CAGR callout (§XII) |
| Decomposition / issue tree | top-down tree | `templates/charts/top_down_tree.svg` |
| Conversion / market sizing | funnel | `templates/charts/funnel_chart.svg` |
| Bridge / variance | waterfall | `templates/charts/waterfall_chart.svg` |
| Multi-metric overview | KPI cards | `templates/charts/kpi_cards.svg` |
| Single-number impact | `stat-hero` | 64–96px navy number + context line + source |
| Option comparison | comparison table + Harvey balls | `templates/charts/comparison_table.svg`, `harvey_balls_table.svg`; verdict column |

Nearest visual-style kin: `references/visual-styles/swiss-minimal.md` (grid-locked, sharp, no decoration).

### Variation discipline

- Every body slide applies **exactly ONE intentional variation** of its pattern (accent focus column, hero first row, asymmetric split, one navy panel, verdict band) — or is consciously standard
- Same pattern ≤ 2 consecutive slides; minimum 3 layout types per deck
- Every chart pairs with a takeaway (stacked right or verdict band); a chart without a takeaway is rejected
- Stats include context ("vs 업계 평균 3.2%"); bare numbers read as placeholder

---

## IX. Spacing Specification

| Element | Value |
| --- | --- |
| Grid | 4px 배수 (8px multiples preferred: 8 / 12 / 16 / 20 / 24 / 32 / 44) |
| Slide outer margin | 44px L/R, 44px bottom reserve |
| Panel padding | 20px |
| Panel gap | 20px |
| Corner radius | 0–4px max — consulting reads square; `rx="12"` cards are forbidden |
| Hairline divider | 1px `#E8E8E8` |
| Emphasis rule | 2px `#2E9BD6` |
| Title underline rule | 1px `#999999` (y=112, full content width) |
| Footer rule | 1px `#D0D0D0` (y=676, full content width) |

---

## X. Placeholder Specification

Templates use `{{PLACEHOLDER}}` tokens:

| Shell | Placeholders |
| --- | --- |
| `01_cover.svg` | `{{KICKER}}`* `{{TITLE}}` `{{SUBTITLE}}` `{{PRESENTER}}` `{{DATE}}` `{{ORGANIZATION}}`* `{{CONFIDENTIALITY}}`* |
| `02_toc.svg` | `{{PAGE_TITLE}}` `{{TOC_ITEM_n_TITLE}}` `{{TOC_ITEM_n_DESC}}` (n = 1…) `{{PAGE_NUM}}` |
| `02_chapter.svg` | `{{CHAPTER_NUMBER}}` `{{CHAPTER_TITLE}}` `{{CHAPTER_SUMMARY}}`* `{{PAGE_NUM}}` |
| `03_content.svg` | `{{KICKER}}`* `{{PAGE_TITLE}}` `{{SOURCE_LINE}}` `{{PAGE_NUM}}` |
| `04_ending.svg` | `{{CLOSING_LABEL}}`* `{{CLOSING_MESSAGE}}` `{{CONTACT_LINE}}`* `{{PRESENTER}}` `{{DATE}}` |

\* optional — delete the whole `<text>` element when unused. `{{PAGE_NUM}}` format: `01 / 12`. `{{SOURCE_LINE}}` format: `Source: <출처>` or `자료: <출처>`.

---

## XI. Icon System

- **Library lock**: `templates/icons/tabler-outline/` (2px stroke line-art). **Icons are rare in this style** — prefer rules, tables, and charts; use icons only when a taxonomy genuinely needs glyphs. **Forbidden**: `chunk` pack, emoji, unicode glyph icons, mixing packs
- Usage: `<use data-icon="tabler-outline/<name>" x="…" y="…" width="…" height="…" fill="none" stroke="currentColor" stroke-width="2"/>` — `finalize_svg.py` resolves the glyph; do NOT inline SVG content
- Search before use: `ls .claude/skills/ppt-master/templates/icons/tabler-outline/ | grep <keyword>` — cite verified filenames only
- **Bare icons only**: no circle wrappers, no colored badges. Sizes: 24–28px in rows/cards, 16px inline
- Number badges (01–04, plain navy text) are the default sequential marker — not icon circles

---

## XII. Chart & Table Treatment

### Charts

- Series order: `#0F2A4A → #1F6FA8 → #4FB2E5`; the single focus series/bar takes `#2E9BD6` while others stay in the ladder or grayscale
- Axis labels and tick text: 13.3/500 `#888888`; gridlines 1px `#D0D0D0`; zero-line 1px `#999999`
- **No legend chrome** — inline labels at the end of each line / beside each bar; data labels on the chart, accent for the focus value
- **CAGR callout convention**: bracket or arrow spanning the growth range + `+X.X%` in `#2E9BD6` 13.3/600 — the benchmark's signature growth annotation
- Forecast regions: dashed stroke + `#4FB2E5` at reduced saturation, split by a vertical dashed divider
- No drop shadows, no 3D, no gradient fills

### Tables

- Header row: `#0F2A4A` background, white 13.3/600 uppercase text
- Row banding: alternate `#F2F2F2`; row rules 1px `#E8E8E8`
- Cell text: Body 16; numerics right-aligned
- Traffic-light cell: 12px circle (`--positive` / `--warning` / `--negative`) + status text label beside it — never color alone
- Comparison tables end with a **verdict column or row** (accent 2px border or `--navy` text) — a comparison without a winner is unfinished

---

## XIII. Anti-Pattern Checklist (reject at authoring time)

- [ ] Any hex outside §III table
- [ ] Accent (`#2E9BD6`) pointing at two different focuses on one page
- [ ] Label-only or question-mark title on an evidence page
- [ ] Evidence page without a `Source:` line
- [ ] Traffic-light color without a paired text label
- [ ] Gradient / drop-shadow / glow / 3D
- [ ] Corner radius > 4px ("SaaS card" look)
- [ ] Multi-hue chart palette; chart without a takeaway
- [ ] Emoji or unicode glyph icons; icon pack mixing
- [ ] Same pattern 3+ consecutive slides
- [ ] 여러분 / 우리는 / 함께해요 direct address
- [ ] Evidence page composed as a single zone without a declared exception (stat-hero / full-bleed table)
- [ ] Source has multi-period / multi-entity figures but the page shows only summary numbers with no detail table
- [ ] Source contains prioritization / causality / phasing structure but the deck has zero framework exhibits
- [ ] Fake cells or unlabeled estimates added to fill density

---

## XIV. Usage Instructions

1. SKILL.md Step 3에 이 워크스페이스 경로를 명시적으로 전달: `.claude/skills/ppt-master/templates/decks/mckinsey/`
2. deck kind이므로 Strategist가 identity + structure를 모두 잠근다; 확인 단계에서 template adherence(`strict` / `adaptive`)를 선택한다. Stage 2에서 이 스킨(색/타이포)이 추천 후보로 제시된다
3. Executor는 `03_content.svg`의 콘텐츠 영역(x=44, y=136, w=1192, h=524)을 §VIII 문법으로 자유 구성하되 kicker / action title / title rule / source line / page-number 크롬을 보존한다
4. Identity만 재사용하려면 brand 추출본 `.claude/skills/ppt-master/templates/brands/mckinsey/`을 다른 layout/deck과 융합한다
