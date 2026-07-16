---
deck_id: naver_ir
kind: deck
native_structure_mode: structured
category: brand
summary: NAVER IR 실적발표 스타일 — 분기 실적발표, 재무 보고, 투자자 미팅, 절제된 재무 데이터 덱
keywords: [naver, ir, earnings, 실적발표, finance]
primary_color: "#03C75A"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
source_canvas_width: 1280
source_canvas_height: 720
source_viewbox: "0 0 1280 720"
replication_mode: standard
page_count: 7
placeholders:
  01_cover: ["{{TITLE}}", "{{DATE}}"]
  02_notice: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}"]
  03a_content_table: ["{{PAGE_TITLE}}", "{{FOOTNOTE}}"]
  03b_content_segment: ["{{PAGE_TITLE}}", "{{PAGE_SUBTITLE}}"]
  03c_content_charts: ["{{PAGE_TITLE}}", "{{UNIT_NOTE}}"]
  03d_content_two_tables: ["{{PAGE_TITLE}}", "{{COL_LEFT_TITLE}}", "{{COL_RIGHT_TITLE}}"]
  04_ending: ["{{CLOSING_MESSAGE}}"]
---

# Naver IR Earnings Deck — Design Specification

> Authored 2026-07-16 from the Naver IR Design System bundle: token CSS + sample slides verified
> against the official NAVER 4Q25 (16p) / 1Q26 (12p) 실적발표 PDFs. Visual fidelity: literal —
> the fixed pages reproduce the source deck geometry and conventions. Identity-only reuse lives in
> the companion brand workspace `templates/brands/naver/`.

---

## I. Template Overview

| Property | Description |
| --- | --- |
| **Template Name** | naver_ir |
| **Display Name** | Naver IR Earnings Deck |
| **Use Cases** | 분기 실적발표, 연간 실적/재무 보고, 투자자 미팅, IR 스타일 데이터 브리핑 |
| **Design Tone** | 절제된 프린트형 재무 매체 — 색·굵기·헤어라인만으로 위계, 장식 전무 |
| **Theme Mode** | Light white content pages + full-bleed light-green structural pages (cover / closing) |

**Anti-mood** (reject at design time): "마케팅 키노트", "그라디언트 SaaS 대시보드", "라운드 카드 덱", "아이콘 그리드 인포그래픽".

**Litmus test**: 페이지가 흑백 인쇄물로도 완전히 읽히고, 모든 수치에 단위·기간·증감 방향이 붙어 있으면 통과.

---

## II. Canvas Specification

| Property | Value |
| --- | --- |
| **Format** | Standard 16:9 (`ppt169`) |
| **Dimensions** | 1280 × 720 px |
| **viewBox** | `0 0 1280 720` |
| **Page Margins** | Left/Right 64px (x: 64 → 1216), top 44px |
| **Title row** | 30px title baseline y=74, then ≈36px gap before content |
| **Content Area** | x=64, y=110–124, w=1152 (content pages; footnote reserve at y≥672 on table pages) |
| **Column split** | segment pages: chart 520px left + 56px gap + right zone 576px; two-column pages: 548px + 56px + 548px |

---

## III. Color Scheme — LOCKED

The ONLY hex values that may appear in any generated SVG (all `fact`, from the design-system token CSS):

| Role | HEX | Token | Purpose |
| --- | --- | --- | --- |
| Background | `#FFFFFF` | `--canvas` | Content page background |
| Cover surface | `#5BDB7D` | `--green-cover` | Full-bleed cover/closing background ONLY — never an accent |
| Identity green | `#03C75A` | `--naver-green` | Core segment title/KPI, key table rows, highlight boxes, current-quarter box |
| Green deep | `#02A94D` | `--green-deep` | Chart series (광고 등 주력 시리즈) |
| Green mid | `#3ED47E` | `--green-mid` | Chart series 2 |
| Green mint / pale | `#9BE9BC` / `#D2F3DF` | `--green-mint` / `--green-pale` | Past-quarter pale tints of the green series |
| Finance slate | `#4E7599` | `--finance` | 파이낸셜 플랫폼 segment title/KPI/line |
| Finance deep / tint | `#2C4A66` / `#C7D7E6` | `--finance-deep` / `--finance-tint` | Finance chart bars / past-quarter tint |
| IR blue | `#4472C4` | `--ir-blue` | 글로벌/투자/재분류 계열 차트 및 다이어그램 |
| IR blue tint | `#BDD7EE` | `--ir-blue-tint` | IR blue past-quarter tint |
| Title ink | `#000000` | `--ink` | Page titles (진짜 검정 사용이 이 덱의 관례) |
| Body ink | `#262626` | `--ink-body` | Body/bullet text |
| Muted | `#7F7F7F` | `--muted` | Captions("단위: 십억 원"), footnotes, disclaimer body |
| Faint | `#BFBFBF` | `--faint` | Non-current x-axis labels, de-emphasized text |
| Watermark | `#D9D9D9` | `--watermark` | (reference) wordmark watermark tone |
| Hairline | `#E5E5E5` | `--hairline` | Table row separators |
| Table header bg | `#F5F5F5` | `--table-header-bg` | Table header band |
| Chart gray / dark | `#D9D9D9` / `#A6A6A6` | `--chart-gray(-dark)` | Neutral chart series |

### Color Rules

- **Max two accent hues per slide** — green family + one of (finance slate / IR blue); everything else neutral
- **Segment color discipline**: 네이버 플랫폼 = green, 파이낸셜 플랫폼 = finance slate, 글로벌 도전/투자 = IR blue; the segment page title, KPI headline, bracket tags, and chart series all take that one segment color
- **`#5BDB7D` is a surface, not an accent** — cover/closing background only; accents on white always use `#03C75A`
- **Grayscale first**: every slide must read in grayscale before color is applied
- **Forbidden**: gradients, drop shadows, glow, 3D, images/photos/textures/illustrations of any kind

---

## IV. Typography System

Install-local Pretendard lock (see `references/strategist.md` §g). Weight cuts as installed family names:

| Weight | `font-family` attribute | `font-weight` |
| --- | --- | --- |
| 400 | `Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 500 | `'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 700 | `Pretendard, 'Malgun Gothic', sans-serif` | `700` |
| 800 | `'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif` | (none) |

Type scale (from the design-system token CSS — `fact`):

| Role | Size (px) | Weight | Use |
| --- | --- | --- | --- |
| Cover title | 40 | 800 | cover/closing message, white, letter-spacing -0.8 |
| Cover date | 18 | 500 | cover date line, white |
| Page title | 30 | 800 | content-page titles, `#000000` (segment pages: segment color), letter-spacing -0.6 |
| Page subtitle | 16 | 700 | inline bold subtitle after segment title ("광고, 서비스") |
| KPI headline | 21 | 700 | "1Q26 YoY 14.7%, QoQ -0.6%" in segment color; sub-lines 13px |
| Body / bullets | 16 | 400 | 개조식 bullets, line-height 1.6, `#262626` |
| Table | 13–13.5 | 400 | tabular numerals, right-aligned; key rows 700 green |
| Caption | 12 | 400 | "단위: 십억 원" unit notes, `#7F7F7F` |
| Footnote | 11 | 400 | "1) …" bottom-left footnotes, `#7F7F7F` |

---

## V. Page Structure & Conventions

### Content-page anatomy

```
┌──────────────────────────────────────────────────┐
│ PAGE TITLE (y=74, 30/800)     [wordmark y=40 →]  │  ← gray wordmark watermark 86px, top-right
│ …≈36px gap…                                      │
│ Content (y≈110–660, x 64→1216)                   │
│ Footnotes (11px #7F7F7F, bottom-left, y≥672)     │
└──────────────────────────────────────────────────┘
```

- **Watermark**: gray NAVER wordmark (86×18px) top-right (x=1130, y=40) on every content page; absent on cover/closing
- **No page numbers** anywhere — the source decks carry none
- **KPI headline format**: quarter first, then YoY, then QoQ — "1Q26 YoY 14.7%, QoQ -0.6%"; percentage-point deltas as "%p"; losses in parentheses "(31.0)"; non-meaningful cells "n/a"
- **Footnotes**: superscript-style markers "1)" in text, definitions bottom-left 11px `#7F7F7F`
- **Bullets**: small dot marker, no terminal period, dense factual clauses; sub-topic bullets open with a bracket tag in the segment color — "[광고] AI 기반의 광고 효율 증대 등으로…"

---

## VI. Page Types

### 1. Cover (01_cover.svg)
Full-bleed `#5BDB7D` + white wordmark top-left (150px, x=72 y=56) + centered 40/800 white title ("2026년도 1분기 실적발표") + centered 18/500 date ("2026.4.30"). Nothing else.

### 2. Notice (02_notice.svg)
유의 사항 disclaimer: white page + watermark + 30/800 title + one muted long-form paragraph block (15px `#7F7F7F`, generous line-height ≈2.1). Every IR deck's page 2.

### 3. Content · Table (03a_content_table.svg)
실적요약/비용·손익/Appendix형: title + 1–2 intro 개조식 bullets + full-width financial table (header band `#F5F5F5`, hairline rows, green bold key rows, right-aligned tabular numerals, italic Y/Y·Q/Q columns, 2px `#03C75A` box around the current-quarter column group) + bottom-left footnote slot.

### 4. Content · Segment (03b_content_segment.svg)
세그먼트 실적형: segment-colored 30/800 title + inline 16/700 black subtitle (baseline-aligned, x=318) + two-column body — left quarterly stacked-bar chart (520px, §VIII treatment), right KPI headline + bullets. Title/KPI/chart/tags all take the one segment color (green / finance slate / IR blue).

### 5. Content · Chart Grid (03c_content_charts.svg)
사업부문별 손익형: title + small unit-note slot (12px gray, x=640) + 2–3 chart panels in a row, each with a 16/700 sub-header. For margin/% trends riding above bars.

### 6. Content · Two Column (03d_content_two_tables.svg)
현금·차입금/FCF형: title + two 16/700 column-title slots (x=64 / x=668) + two 548px columns of compact tables and/or small charts; footnote definitions at column bottoms.

### 7. Closing (04_ending.svg)
Full-bleed `#5BDB7D` + centered 40/800 white "감사합니다". No wordmark, no contact block — the source convention is a bare thank-you surface.

---

## VII. SVG Page Roster

| File | Role | Layout key / picker name | Description |
| --- | --- | --- | --- |
| `01_cover.svg` | cover | `01_cover` / Cover | Full-bleed green cover; title + date |
| `02_notice.svg` | content (disclaimer) | `02_notice` / Notice | 유의 사항 muted paragraph page |
| `03a_content_table.svg` | content | `03a_content_table` / Content Table | Bullets + full-width financial table + footnote |
| `03b_content_segment.svg` | content | `03b_content_segment` / Content Segment | Segment title/subtitle; chart left, KPI+bullets right |
| `03c_content_charts.svg` | content | `03c_content_charts` / Content Chart Grid | Multi-chart row + unit note |
| `03d_content_two_tables.svg` | content | `03d_content_two_tables` / Content Two Column | Two column-title slots + twin panels |
| `04_ending.svg` | ending | `04_ending` / Closing | Full-bleed green thank-you |

All pages share master `naver-ir-master` ("Naver IR", white background).

---

## VIII. Chart & Table Treatment (IR grammar)

### Charts — quarterly stacked bars are the house form

- **Past quarters in pale tints, current quarter saturated**: green series `#D2F3DF/#9BE9BC → #02A94D/#3ED47E`; finance `#C7D7E6 → #2C4A66`; IR blue `#BDD7EE → #4472C4`
- Totals above bars (13px, 700 for current quarter); segment stack labels inside/beside bars
- YoY %-line or TPV line rides above bars: labeled round markers, white fill + segment-color stroke; current-quarter label bold with unit suffix ("24.2조 원")
- x-labels 12px `#BFBFBF` gray with the current quarter `#262626` bold
- **No gridlines, no y-axis, no legend chrome** — inline series labels below/beside bars
- 5–6 quarters per chart (4Q24 → current)

### Tables

- Header band `#F5F5F5`, 13px 700; hairline row separators `#E5E5E5`; stronger 1.5px rules at table top/bottom
- Key rows (매출액/영업비용/영업이익) bold `#03C75A`; indent hierarchy with 1-level (segment) and 2-level ("- 인건비") rows
- Numerals right-aligned tabular; delta columns (Y/Y, Q/Q) italic; ratio rows ("영업이익률 (%)") italic gray
- **2px `#03C75A` box around the current-quarter column group** (value + deltas) — the signature highlight
- Unit caption "단위: 십억 원" as the first header cell or a 12px gray caption above

### Depth & shape

- Corner radius 0 (4px max, reserved for highlight boxes); no shadows, no rounded cards — hierarchy from weight, color, hairlines only

---

## IX. Voice (content register)

- Formal written Korean: 합니다체 prose, noun-ending 개조식 bullets ("…YoY 16.3% 달성")
- Finance vocabulary stays English: YoY, QoQ, FCF, CapEx, TPV, GPUaaS, quarter labels (1Q26)
- Numbers: thousands separators + one decimal (3,241.1); no emoji, no exclamation, no marketing filler; named products in quotes ('Npay Connect'); strategy phrasing "…할 계획", "…확대 진행 중"

---

## X. Assets

| File | Size | Usage |
| --- | --- | --- |
| `../images/naver-wordmark-white.png` | 357×75 | Cover top-left lockup (150px wide) |
| `../images/naver-wordmark-gray.png` | 357×75 | Content-page top-right watermark (86px wide) |

No icon system: the source decks use no icons, pictograms, or emoji. If a glyph is unavoidable, use a plain unicode arrow (→) and flag it as an addition.

---

## XI. Anti-Pattern Checklist (reject at authoring time)

- [ ] Any hex outside §III table
- [ ] Three or more accent hues on one slide
- [ ] `#5BDB7D` used as an accent on a white page
- [ ] Photos, illustrations, textures, gradients, shadows, or rounded cards
- [ ] Icon grids or emoji; page numbers
- [ ] Chart with gridlines / y-axis / legend chrome
- [ ] Financial table without unit declaration or current-quarter highlight
- [ ] Bare numbers without period + delta context; fabricated cells
- [ ] 여러분/우리는 direct address; exclamation marks; marketing filler

---

## XII. Usage Instructions

1. SKILL.md Step 3에 이 워크스페이스 경로를 명시적으로 전달: `.claude/skills/ppt-master/templates/decks/naver_ir/`
2. deck kind이므로 Strategist가 identity + structure를 모두 잠근다; 확인 단계에서 template adherence(`strict` / `adaptive`)를 선택한다
3. Executor는 각 콘텐츠 페이지의 주석 처리된 CONTENT AREA를 §VIII 문법으로 자유 구성하되 title/watermark/slot 크롬을 보존한다. 세그먼트 페이지의 세그먼트 색(title-carrier fill)은 콘텐츠에 따라 §III의 세 세그먼트 색 중 하나로 교체한다
4. Identity만 재사용하려면 brand 추출본 `.claude/skills/ppt-master/templates/brands/naver/`를 다른 layout/deck과 융합한다
5. **Delivery-purpose seeding**: 이 덱이 Step 3 템플릿으로 지정되면 Strategist는 Stage 1에서 `delivery_purpose: balanced`를 추천값으로 제시한다 — IR 덱은 발표와 정독을 겸하는 문서다. §IV가 타입 램프(Body 16px)를 잠그므로 `delivery_purpose`는 글자 크기가 아니라 페이지당 콘텐츠 분배량·`page_rhythm`·페이지 수 추천에 작용한다
