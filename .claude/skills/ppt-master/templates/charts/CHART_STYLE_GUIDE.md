# Chart SVG Style Guide

> This document defines the visual standards for every SVG chart template under `templates/charts/`.
> When adding or modifying a chart you **MUST** follow these standards so the whole library stays visually consistent.

## 0. Upstream Standards Reference

This guide defines only the **chart-template-specific** aesthetics and implementation recipes. Project-level SVG
authoring, compatibility exceptions, and conditional mappings are owned by
[`references/shared-standards.md`](../../references/shared-standards.md);
this guide neither excerpts nor relaxes that contract.

---

## 1. Color System (Tailwind CSS Palette)

### 1.1 Text colors

| Use | Value | Tailwind Token | Example |
|------|------|----------------|------|
| **Main title** | `#0F172A` | Slate 900 | Chart headline |
| **Value labels** | `#0F172A` | Slate 900 | Bar-top values, key metrics |
| **Subtitle** | `#64748B` | Slate 500 | Dates, unit notes |
| **Axis tick labels** | `#64748B` | Slate 500 | X/Y tick values |
| **Axis titles / legend** | `#475569` | Slate 600 | "Annual salary (USD k)", legend text |
| **Data source** | `#94A3B8` | Slate 400 | Bottom-of-page source note |
| **Footnotes / muted hints** | `#CBD5E1` | Slate 300 | "Each phase is adjustable" |

### 1.2 Theme colors (data series)

| Name | Primary | Dark (gradient end) | Use |
|------|------|------------------|------|
| **Blue** | `#3B82F6` | `#2563EB` | Series 1 (default first pick) |
| **Emerald** | `#10B981` | `#059669` | Series 2 |
| **Amber** | `#F59E0B` | `#D97706` | Series 3 |
| **Violet** | `#8B5CF6` | `#7C3AED` | Series 4 |
| **Rose** | `#FB7185` | `#E11D48` | Series 5 / warnings |
| **Pink** | `#EC4899` | `#BE185D` | Contrast group (e.g. butterfly-chart female side) |

> Radial gradients (e.g. bubble charts) use the light variants: `#60A5FA`, `#34D399`, `#FBBF24`, `#A78BFA`, `#FB7185`

### 1.3 Semantic colors

| Use | Value | Note |
|------|------|------|
| On target / positive | `#10B981` | Emerald 500 |
| Warning / neutral | `#F59E0B` | Amber 500 |
| Below target / negative | `#EF4444` | Red 500 |
| Outlier annotation | `#F43F5E` | Rose 500 |

### 1.4 UI support colors

| Use | Value | Note |
|------|------|------|
| **Axis lines** | `#94A3B8` | Slate 400, stroke-width="2" |
| **Grid lines** | `#E2E8F0` or `#E0E0E0` | stroke-dasharray="4,4" |
| **Center dividers** | `#CBD5E1` | e.g. quadrant crosshairs |
| **Card background** | `#F8FAFC` / `#F8F9FA` | Slate 50 |
| **Card border** | `#E2E8F0` | Slate 200 |
| **Row separators** | `#F1F5F9` | Slate 100 (very light) |
| **Tint background** (blue) | `#EFF6FF` | Blue 50 |
| **Tint background** (green) | `#ECFDF5` | Emerald 50 |
| **Tint background** (red) | `#FFF1F2` | Rose 50 |
| **Tint background** (yellow) | `#FFFBEB` | Amber 50 |

---

## 2. Typography

### 2.1 Font stack

```
font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif"
```

- Pure-Latin content may omit `'PingFang SC', 'Microsoft YaHei'`

### 2.2 Size scale

| Level | Size | font-weight | Use |
|------|------|-------------|------|
| H1 | `34px` | `bold` (700) | Chart main title |
| H2 | `22px` | `600` | Region titles (e.g. "Detailed Data") |
| Body L | `18-20px` | `600` | Key values, percentages |
| Body M | `15-16px` | `600` | Data labels, category names |
| Body S | `14px` | normal | Subtitles, legends, sources |
| Caption | `12-13px` | normal | Axis ticks, annotations |

> **Minimum font size: 12px.** No text may be smaller than 12px.

### 2.3 Inline formatting within one chart label

When a chart label must stay one editable text frame in PPT, write the whole logical line in a single `<text>` and express multiple colors or weights with inline `<tspan>`. If genuinely independent text frames are wanted, separate `<text>` elements are fine:

```xml
<!-- Correct: one text frame, three runs -->
<text x="100" y="200" font-size="24" fill="#333333">
  Achieved a <tspan fill="#3B82F6" font-weight="bold">10x</tspan> efficiency gain
</text>

<!-- Not for a single text frame: the following produces three independent frames -->
<text x="100" y="200">Achieved a</text>
<text x="160" y="200" fill="#3B82F6">10x</text>
<text x="240" y="200">efficiency gain</text>
```

> Only inline tspans meant to stay in the same text frame omit `x` / `y` / `dy`; a tspan carrying those positioning attributes is treated as an independent text frame. `dx` may be used for kerning micro-adjustments.

### 2.4 Default data highlighting

Key data text in a chart is highlighted by default:
- **Numeric results** — percentages, multiples, amounts → `<tspan fill="theme color" font-weight="bold">`
- **Comparatives** — up/down, on/below target → semantic color (green/red)
- **Never highlighted** — connectives, ordinary verbs, structural text (axis labels, legends, page numbers)

---

## 3. Shadow Filters

This section prescribes only the shadow recipe the chart template library uses; it does not define
project-level filter support boundaries. Chart shadows uniformly use the `feFlood` scheme; this guide
does not use `<feComponentTransfer>`:

```xml
<filter id="chartShadow" x="-15%" y="-15%" width="130%" height="130%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="2-4"/>
    <feOffset dx="0" dy="1-3" result="offsetBlur"/>
    <feFlood flood-color="#0F172A" flood-opacity="0.08-0.15" result="shadowColor"/>
    <feComposite in="shadowColor" in2="offsetBlur" operator="in" result="shadow"/>
    <feMerge>
        <feMergeNode in="shadow"/>
        <feMergeNode in="SourceGraphic"/>
    </feMerge>
</filter>
```

### Parameter reference

| Scenario | stdDeviation | dy | flood-opacity |
|------|-------------|-----|---------------|
| Heavy elements (arrows, cards) | 4-6 | 2-4 | 0.12-0.15 |
| Medium elements (bars, boxes) | 2-3 | 1-2 | 0.10-0.15 |
| Light elements (bottom cards) | 4-6 | 2-4 | 0.06-0.08 |

### Implementation conventions of this guide

- `flood-color="#000000"` → MUST be `#0F172A`
- `<feComponentTransfer>` + `<feFuncA slope=...>` → replace with `<feFlood flood-color flood-opacity>`
- `flood-opacity > 0.20` → shadow too heavy; maximum 0.15-0.20

> This is the library's color-consistency convention, not a project-level SVG blacklist.
> `feComponentTransfer/feFuncA(slope)` is singled out because it can only adjust opacity and cannot
> carry a color, so shadows fall back to pure black and clash — visibly warmer/cooler — with
> same-page cards using `feFlood` `flood-color="#0F172A"`.
>
> In short: chart shadows in this library must express their color explicitly, not opacity alone.

### Chart shadow usage principles

> **Shadow is an aesthetic ingredient, not a default treatment.** Restraint, not abundance, produces the "designed" feel. "Shadows are felt, not seen" is the premium aesthetic bar.

**Add a shadow to**: cards floating above photos/colored panels, the single primary CTA, overlays (tooltips, callouts)

**Do not add a shadow to**: background panels/divider bars, equal sibling cards in a grid, containers that already carry a border/gradient, body-text containers, decorative lines/icons, anything on dark backgrounds (black shadows are invisible there)

**Per-page budget**: at most 2-3 shadowed elements. When a 4th needs a shadow, remove one existing shadow first.

**Single light source**: all `feOffset` `dx`/`dy` directions on a page must agree (default `dx=0, dy=positive` — light from above).

**Two elevation levels maximum**:

| Level | Scenario | dy | stdDeviation | flood-opacity |
|------|------|----|--------------|---------------|
| Ground (no shadow) | Backgrounds, sibling grid cards, dividers, body containers | — | — | — |
| Resting | Cards on photos/panels, secondary callouts | 2-4 | 4-8 | 0.06-0.10 |
| Raised | Primary CTA, focal/recommended cards, overlays | 6-10 | 10-16 | 0.12-0.20 |

**No stacking**: shadow + border + rounded corners + gradient fill together = template-feel. A container's "look at me" budget is tiny — pick one.

---

## 4. Gradients

### 4.1 Linear gradients (bar/column charts)

```xml
<linearGradient id="barGrad1" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" style="stop-color:#3B82F6;stop-opacity:1" />
    <stop offset="100%" style="stop-color:#2563EB;stop-opacity:1" />
</linearGradient>
```

- Direction: light to dark (top→bottom or left→right)
- Every gradient ID is semantic: `barGrad1`, `leftGrad`, `actualBarBlue`

### 4.2 Radial gradients (bubble charts)

```xml
<radialGradient id="bubbleGrad1" cx="30%" cy="30%">
    <stop offset="0%" style="stop-color:#60A5FA;stop-opacity:0.9" />
    <stop offset="100%" style="stop-color:#2563EB;stop-opacity:0.7" />
</radialGradient>
```

- Highlight sits upper-left (`cx="30%" cy="30%"`)
- Edge opacity drops to 0.7 for a translucent feel

---

## 5. Structure

### 5.1 Chart-level grouping

Group semantically with `<g id="...">` so elements can be manipulated/animated one by one in PPT:

```xml
<g id="chartArea">        <!-- chart body -->
    <g id="bar-1">...</g>  <!-- each data element in its own group -->
    <g id="bar-2">...</g>
</g>
<g id="legend">            <!-- legend region -->
    <g id="legend-high">...</g>
</g>
<g id="detailList">        <!-- detail panel -->
    <g id="list-items">
        <g id="item-1">...</g>
    </g>
</g>
```

**Chart template grouping units**:

| Group unit | Contains |
|---------|---------|
| Card / panel | Background rect + shadow (if any) + icon + title + body |
| Process step | Numbered circle + icon + label + description |
| List item | Bullet/number + icon + title + description |
| Icon-text combo | Icon element + adjacent label |
| Page header | Title + subtitle + decoration |
| Decoration cluster | Related decorative shapes (rings, orbs, dots) |

**Naming convention**: descriptive `id`s (e.g. `card-1`, `step-discover`, `header`, `footer`).

### 5.2 viewBox

Fixed at `0 0 1280 720` (PPT 16:9). Never change it.

### 5.3 Background

The first element is always a white full-canvas background:
```xml
<rect width="1280" height="720" fill="#FFFFFF"/>
```

### 5.4 Data source

Bottom of the page, fixed format:
```xml
<text x="60" y="695" font-family="..." font-size="14" fill="#94A3B8">
    <tspan>Data source: XXX</tspan>
</text>
```

---

## 6. General SVG Technical Constraints

This guide does not define or excerpt the project-level SVG allowlist, banned features, or conditional
mappings. The current contract lives in
[`shared-standards.md`](../../references/shared-standards.md); when adding or modifying a template,
run `svg_quality_checker.py` against the target file and pass validation.

---

## 7. Legacy Color Mapping Cheat Sheet

When maintaining old templates, use this mapping for quick replacement:

| Old (Material/Flat) | → | New (Tailwind) | Role |
|----------------------|---|-----------------|------|
| `#2C3E50` | → | `#0F172A` | Primary text |
| `#7F8C8D` | → | `#64748B` | Secondary text |
| `#5D6D7E` | → | `#475569` | Legend text |
| `#95A5A6` | → | `#94A3B8` | Data source |
| `#BDC3C7` | → | `#CBD5E1` | Muted elements |
| `#2196F3` / `#1976D2` | → | `#3B82F6` / `#2563EB` | Blue series |
| `#4CAF50` / `#388E3C` | → | `#10B981` / `#059669` | Green series |
| `#FF9800` / `#F57C00` | → | `#F59E0B` / `#D97706` | Orange series |
| `#E91E63` | → | `#F43F5E` | Outliers |
| `#000000` (shadow) | → | `#0F172A` | Shadow base |

---

## 8. Placeholder Content Strategy

These SVG files are "templates" for later AI consumption: their core value is demonstrating **graphic structure, typographic constraints, and visual space**, not carrying real business data. Text written into a template therefore follows these placeholder principles:

### 8.0 English-Only Rule
**Mandatory**: all placeholder text in chart templates (titles, subtitles, axes, legends, data nodes, detail descriptions, and the bottom source note) **must be written in English**.
- **Purpose**: downstream LLMs in the automation pipeline map semantics and structured content more precisely, and the natural length characteristics of English words better demonstrate the template's line-wrapping logic and spatial boundaries.

### 8.1 Demonstrating structural boundaries
- **Show maximum width / wrapping logic**: deliberately use strings of typical length (two-to-three-word phrases, multi-line `tspan`s) to make text-box boundaries explicit. This gives the AI a concrete reference when filling in real text and prevents overflow.
- **Show data formats**: use placeholder values that exhibit the full format (`$1,234.5M`, `98.5%`) rather than a bare `10`, to verify that symbols and character widths fit.

### 8.2 Generality and neutrality
- Use generic, professional business placeholders; avoid overly vertical or concrete business data (unless the template itself is strongly industry-specific).
- **Preferred**: `Category A`, `Q1 Revenue`, `Strategic Objective`, `Phase 01`.
- **Avoid**: specific long-form real-world data (e.g. "Brand X 2023 special-equipment sales analysis").

### 8.3 Visual balance
- Placeholder text should keep the chart visually balanced (e.g. the two sides of a butterfly chart roughly equal in length; list text varied in length) so the layout intent reads at a glance.

---

## 9. Registering in charts_index.json

After adding an SVG template you **MUST** register it in [`charts_index.json`](./charts_index.json), or the Strategist will never discover it during selection.

### 9.1 Field spec

```json
"<key>": {
  "summary": "Pick for <content shape + scale>. Skip if <counter-case → alternative template>."
}
```

- **`key`** = the SVG filename minus `.svg`, lowercase with underscores (e.g. `bullet_chart`)
- **`summary`** is a **selection sentence**, not a description. Grammar per `meta.summaryGrammar`: first say when to pick it, then use `Skip if ... (use <other_key>)` to point at the most easily confused sibling template
- Increment **`meta.total`** by 1

> **No** `label` / `categories` / `quickLookup` / `keywords` — all removed. The Strategist reads the full summary list and matches semantically; no precomputed index is used. **Note**: summaries are English, but source documents often carry Chinese / industry terms ("中台", "架构图", "管道") — the Strategist translates semantically before matching. If a template's hit rate depends heavily on one such phrase, put its English equivalent into the summary's Pick clause.

### 9.2 Counter-examples

❌ Describing only "what it is": `"summary": "Bidirectional comparison chart for two datasets"`
✅ Saying "when to pick": `"summary": "Pick for two mirrored datasets sharing a common axis (age pyramid, A/B). Skip for >2 sides (use grouped_bar_chart)."`

❌ Overlong summary (>400 chars) — harder to grasp at selection time; target 150-300 chars.

> **Why not stricter**: a single structural template often covers several business frameworks/scenarios (`quadrant_text_bullets` covers SWOT + Ansoff; `top_down_tree` covers org + OKR). The summary needs keyword anchors ("principles, key takeaways, action items") for the Strategist to semantically hit "non-numeric structure pages", so the old 100-180-char baseline became too tight after the structure-family renaming.

---

## 10. Checklist

After adding or modifying a chart, check each item:

### Basic validation
- [ ] `xmllint --noout` passes
- [ ] viewBox is `0 0 1280 720`
- [ ] First element is the white background `<rect width="1280" height="720" fill="#FFFFFF"/>`

### Color
- [ ] No legacy colors remain (`grep` check — command below)
- [ ] Shadow `flood-color` is `#0F172A`, opacity ≤ 0.20
- [ ] Data source uses `#94A3B8`

### Typography
- [ ] No text with `font-size < 12`
- [ ] Multi-format labels that must stay one PPT text frame use inline `<tspan>`; only such inline runs omit `x` / `y` / `dy`
- [ ] Title 34px, subtitle 18px, source 14px

### Structure
- [ ] Major elements carry semantic `<g id="...">`
- [ ] `svg_quality_checker.py` passes for the target template; the general SVG contract is not restated in this checklist

### Shadows
- [ ] `feFlood` scheme used (not `feComponentTransfer`)
- [ ] Same-page shadow `dx`/`dy` directions agree
- [ ] At most 3 shadowed elements per page

### Registration (new templates only)
- [ ] `charts_index.json` `charts.<key>` carries a `summary` field
- [ ] `summary` is a selection sentence (`Pick for ... Skip if ... (use <other>)`), not a description
- [ ] `summary` is 150-300 chars (>400 → rewrite); templates covering several business frameworks may stretch to 350 to fit keyword anchors
- [ ] `meta.total` incremented

### Plot-area calibration markers (required for calculator-supported charts)
- [ ] Rectangular-coordinate charts (bar / horizontal_bar / grouped_bar / stacked_bar / line / area / stacked_area / scatter / waterfall / pareto / butterfly) contain the `<!-- chart-plot-area: x_min,y_min,x_max,y_max -->` marker
- [ ] Pie / donut / radar charts contain the `<!-- chart-plot-area: <type> | center: cx,cy | radius: r -->` marker
- [ ] The marker sits inside `<g id="chartArea">`, after the axes, before the data elements
- [ ] Marker coordinates match the axes' actual SVG coordinates

### Validation commands
```bash
# One-shot check
f="your_chart.svg"
xmllint --noout ".claude/skills/ppt-master/templates/charts/$f" && echo "XML OK" || echo "XML FAIL"
echo "Old colors:" && grep -c '#2C3E50\|#7F8C8D\|#95A5A6\|#5D6D7E\|#000000' ".claude/skills/ppt-master/templates/charts/$f"
echo "Small fonts:" && grep -c 'font-size="[0-9]"' ".claude/skills/ppt-master/templates/charts/$f"
```

---

## 11. Card Container Patterns

Container cards are the most-reused visual unit in PPT Master (KPI cards, section cards, info cards). The patterns below are verified, PPTX-roundtrip-compatible reference implementations — new templates reuse them first rather than inventing equivalent-but-dirty alternatives.

### 11.1 Half-Rounded Section Tab

**Use**: give a card or block a colored "tab header" identifying its category (S/W/O/T, Political/Economic, About Me/Awards, …). Easier to recognize than a bare heading, more compact than a standalone label bar.

**Two forms** — choose by whether the tab's visual anchor sits above or below:

| Form | Shape | Visual semantics | Typical scenario |
|------|------|---------|---------|
| **Round-top, square-bottom** | Top corners rounded, bottom square | A tab "growing out of" the card | Section-card headers, quadrant titles, info-card categories |
| **Square-top, round-bottom** | Top corners square, bottom rounded | A tag "hanging down from" the page header/section bar | Section anchors, header-bar extensions, TOC jump markers |

> Both forms share one requirement: **round only one pair of corners**, drawing the whole shape as a single path. Do not use the "fully-rounded rect + same-color rect covering one edge" hack (the PPTX roundtrip turns it into two independent objects whose colors detach when edited).

**Implementation 1: round-top, square-bottom (default)**

```xml
<!-- Template: width W, height H, radius R, top-left origin (x, y) -->
<path d="M {x+R} {y} h {W-2R} a {R} {R} 0 0 1 {R} {R} v {H-R} h -{W} v -{H-R} a {R} {R} 0 0 1 {R} -{R} Z"
      fill="#2563EB"/>

<!-- Instance: 240×50, r=25, origin (245, 140) -->
<path d="M 245 140 h 190 a 25 25 0 0 1 25 25 v 25 h -240 v -25 a 25 25 0 0 1 25 -25 Z" fill="#2563EB"/>
```

**Implementation 2: square-top, round-bottom (hanging tag)**

```xml
<!-- Template: width W, height H, radius R, top-left origin (x, y) -->
<path d="M {x} {y} h {W} v {H-R} a {R} {R} 0 0 1 -{R} {R} h -{W-2R} a {R} {R} 0 0 1 -{R} -{R} Z"
      fill="#2563EB"/>

<!-- Instance: 240×50, r=25, origin (245, 140) -->
<path d="M 245 140 h 240 v 25 a 25 25 0 0 1 -25 25 h -190 a 25 25 0 0 1 -25 -25 Z" fill="#2563EB"/>
```

**Banned counter-example** (common in old PEST/SWOT/comparison_columns implementations):

```xml
<!-- ❌ Never: fully-rounded rect + white rect covering one edge's corners -->
<rect width="260" height="120" rx="12" fill="#EFF6FF"/>
<rect y="100" width="260" height="20" fill="#EFF6FF"/>
```

The covering rect survives the SVG→PPTX roundtrip as an independent object color-bound to the header; editing the header color in PPT easily misses it and the seam shows.

### 11.2 Nested Card Border

**Use**: give a card a "bordered" layered feel without stroke. Stroke often renders as thin layered lines in PPTX, and combined with shadow it produces template-feel.

**Recipe**: outer light-gray rounded rect + inner slightly smaller white rounded rect; an 8–20px gap between the layers reads as a border.

```xml
<!-- Outer "border" layer -->
<rect x="60" y="140" width="560" height="255" rx="20" fill="#F1F5F9"/>
<!-- Inner white content card (inset 20px, smaller radius) -->
<rect x="80" y="210" width="520" height="165" rx="12" fill="#FFFFFF"/>
```

**Applicability**:
- When the card also carries a §11.1 section tab, the outer layer doubles as the tab's backing board
- Use only **one** border expression per page: outer layer OR stroke OR shadow — never together (see §3 shadow principles)

### 11.3 Card Grid as Page Skeleton

**Use**: when a page presents 4 equal aspects side by side (pillar / aspect / quadrant), prefer a 2×2 grid over vertical stacking.

**Grid size suggestions** (1280×720 canvas):

| Grid | Card W × H | Gap | Origins (x, y) |
|------|-------------|------|-------------|
| 2×2 | 560 × 255 | 40 | (60, 140) (660, 140) (60, 420) (660, 420) |
| 2×3 (landscape) | 370 × 260 | 25 | (50, 130), row pitch 290 |
| 1×3 (tall columns) | 400 × 540 | 30 | (60, 130), column pitch 430 |
| 1×4 (top row) | 280 × 250 | 20 | (60, 150), column pitch 300 |

**Decision rule**: "4 parallel aspects" → 2×2; "3 parallel aspects" → 1×3; "6 capability points" → 2×3; "4 key metrics" → 1×4. Pages whose `page_rhythm` is `breathing` do **not** use card grids (see executor-base.md §2.1).

### 11.5 Diagonal Dashed Connector

**Use**: express a "cross-quadrant / cross-level" relationship — priority migration, influence propagation, dotted-line reporting, diagonal trends. Horizontal/vertical arrows express process progression; a diagonal dashed arrow expresses relationship or directional guidance — different semantics.

**Recipe**: a single `<line>` + `stroke-dasharray="6 5"` + `marker-end`. Define a dedicated marker for this line (do not reuse the main flow's arrow color; Slate 600 `#475569` conveys an advisory, non-mandatory tone).

```xml
<defs>
  <marker id="migrationArrow" markerWidth="12" markerHeight="12"
          refX="10" refY="6" orient="auto" markerUnits="strokeWidth">
    <path d="M 0,0 L 10,6 L 0,12 Z" fill="#475569"/>
  </marker>
</defs>

<!-- Priority-migration arrow from Q4 (bottom-right) to Q2 (top-left) -->
<line x1="850" y1="605" x2="385" y2="200"
      stroke="#475569" stroke-width="2"
      stroke-dasharray="6 5" stroke-linecap="round"
      marker-end="url(#migrationArrow)"/>

<!-- Mid-line label: a white capsule pressed onto the arrow to avoid visual clash -->
<rect x="525" y="385" width="190" height="28" rx="14"
      fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
<text x="620" y="403" text-anchor="middle" font-size="12"
      font-weight="700" fill="#475569" letter-spacing="1">PRIORITY MIGRATION</text>
```

> **Pairing requirement**: every diagonal dashed arrow must carry a mid-line label (a small capsule or one line of text), otherwise the reader is left asking "what is this line saying?". Unlabeled arrows are allowed only in horizontal/vertical flows (e.g. `process_flow`).

### 11.6 Ground Anchor Ellipse — non-filter depth

**Use**: give a floating circle / icon / avatar / trophy / character badge a "touching the ground" visual anchor **without a `<filter>` shadow**.

**Why it works**:
1. It's a native PPTX circle/ellipse object — consistent across renderers, never parsed into `<a:outerShdw>` (avoiding shadow-color loss or reflow issues)
2. It complements §3's shadow restraint — with the 2-3 shadow budget spent, remaining elements that need "depth" can take this route
3. **Easier to re-edit in PPT** than a filter shadow (users can drag it, recolor it, delete it)

**Recipe**: draw a **flat ellipse** (`ry << rx`) directly **below** the floating element, low opacity, in the subject color or Slate 900:

```xml
<!-- Grounding pad under an avatar/badge; cy sits 10-15px below the subject's bottom edge -->
<ellipse cx="80" cy="172" rx="70" ry="5" fill="#0F172A" opacity="0.10"/>
<!-- Then draw the subject itself (order matters — the ellipse goes first) -->
<circle cx="80" cy="80" r="80" fill="#E2E8F0"/>
```

**Parameter reference**:

| Floating-element radius | Ellipse rx | Ellipse ry | opacity |
|-------------|---------|---------|---------|
| 30-50 px | r × 0.85 | 3-4 | 0.10-0.15 |
| 50-100 px | r × 0.85 | 5-6 | 0.10-0.12 |
| 100+ px | r × 0.85 | 7-9 | 0.08-0.10 |

Color: default `#0F172A` (neutral dark gray); a darker variant of the subject color (e.g. `#1E3A8A` under an avatar) expresses a "brand-color shadow".

**Banned**: do not draw the ellipse as a circle or near-circle (`ry/rx > 0.25` already reads as fake). Do not stack it on a `<filter>` shadow — pick one.

### 11.7 Bidirectional Interaction Arrows

**Use**: express paired relationships — request/response, push/pull, uplink/downlink, supply/demand. Distinct from one-way process arrows.

**Recipe**: two parallel `<line>`s with differently colored `marker-end`s, opposite directions, and **an action label on each line**:

```xml
<defs>
  <marker id="reqArrow" markerWidth="10" markerHeight="10" refX="9" refY="5"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,5 L0,10 Z" fill="#3B82F6"/>
  </marker>
  <marker id="respArrow" markerWidth="10" markerHeight="10" refX="9" refY="5"
          orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,5 L0,10 Z" fill="#10B981"/>
  </marker>
</defs>

<!-- Request: left to right, blue -->
<line x1="380" y1="250" x2="926" y2="250" stroke="#3B82F6" stroke-width="2.5"
      marker-end="url(#reqArrow)"/>
<rect x="500" y="216" width="280" height="26" rx="11" fill="#FFFFFF"
      stroke="#3B82F6" stroke-width="1"/>
<text x="640" y="234" text-anchor="middle" font-size="14" font-weight="700"
      fill="#3B82F6">① Login Request · POST /auth/login</text>

<!-- Response: right to left, green -->
<line x1="926" y1="290" x2="384" y2="290" stroke="#10B981" stroke-width="2.5"
      marker-end="url(#reqArrow)"/>
<!-- ...with its own label likewise... -->
```

**Color convention**: initiator side blue `#3B82F6`, responder side green `#10B981`. For peer relationships (A↔B collaboration), use Slate 600 `#475569` on both without distinguishing.

**Banned**: no "bare lines" — **each** direction of a bidirectional pair must carry an action label; otherwise the direction semantics are unreadable.

### 11.8 Reference implementations

| Pattern | Reference templates |
|------|---------|
| §11.1 Half-rounded section tab (round-top) | `quadrant_text_bullets.svg`, `labeled_card.svg`, `vertical_pillars.svg`, `comparison_columns.svg` |
| §11.2 Nested card border | `labeled_card.svg` |
| §11.3 2×2 card grid | `kpi_cards.svg`, `quadrant_text_bullets.svg`, `labeled_card.svg` |
| §11.3 2×3 card grid | `icon_grid.svg` |
| §11.3 1×3/1×4 card grid | `comparison_columns.svg`, `vertical_pillars.svg` |
| §11.5 Diagonal dashed connector | `matrix_2x2.svg` |
| §11.6 Ground anchor ellipse | `team_roster.svg` |
| §11.7 Bidirectional interaction arrows | `client_server_flow.svg` |
