---
name: chart-design
description: >
  Data-driven chart generation for ppt-master decks. Renders 21 chart types
  (bar/line/area/scatter/combo/waterfall/bullet, pie/donut/gauge/radar,
  KPI cards/progress/funnel/heatmap/treemap) as native SVG fragments styled
  entirely by the deck's spec_lock.md (colors + typography) — zero network
  calls, zero chart libraries, converter-safe output with the mandatory
  chart-plot-area marker built in. Use whenever a slide needs a chart built
  from real numbers: "차트 만들어", "그래프로 보여줘", "매출 추이 시각화",
  a design_spec §VII visualization row, a spec_lock page_charts entry, or any
  quantitative evidence on a page. Also use to REJECT a bad chart choice —
  this skill's judgment rules (bar-first, pie/radar gates) decide the chart
  type from the data shape.
license: MIT
metadata:
  version: "1.0"
  benchmark: "Selection heuristics adapted from antvis/chart-visualization-skills (MIT); rendering is original, pure SVG."
---

# chart-design — 데이터 → 슬라이드 차트 (ppt-master)

Deterministic chart renderer for ppt-master decks. You describe the DATA in a
small JSON spec; the engine computes geometry (scales, ticks, arcs, squarify)
and emits a page-ready `<g>` fragment. You never hand-draw bars or eyeball
pixel positions, and you never pick colors — style is resolved at render time
from the deck's `spec_lock.md`. This replaces hand-adapting
`templates/charts/*.svg` geometry for the 21 quantitative types (hand-adapted
geometry is where mis-scaled bars and wrong percentages come from).

```
data + judgment (you) ──spec.json──▶ render_chart.py --project <deck>
                                          │
                     <project>/spec_lock.md (colors + typography 잠금)
                                          ▼
        <g data-chart-type> + <g id="chartArea"> + §3.1 plot-area marker
```

**Hard boundaries** (violating any of these is a bug, not a style choice):

1. **SPEC_LOCK discipline** — every color/font in output comes from the deck's
   `spec_lock.md` (or is emitted as a locked hex + opacity so the quality
   checker's drift scan stays clean). If the lock can't be read the render
   FAILS (`TokenResolutionError`); there are no fallback palettes.
2. **No network, no chart libraries** — pure stdlib geometry. Deck data never
   leaves the machine.
3. **Text stays `<text>`** — labels are real text elements using the locked
   font stack (Pretendard-led under this install's font policy), never
   outlined to paths, so exported PPTX text remains editable.
4. **Converter-safe SVG only** — no mask/style/class/use/textPath
   (shared-standards.md §1). Series colors are the single-accent opacity
   ladder on the locked accent. Every fragment ships `<g id="chartArea">` +
   the `chart-plot-area` marker that executor-base §3.1 mandates and
   verify-charts consumes.

---

## 1. Chart selection — decide from the data shape, not from taste

Ask: **what is the ONE thing the audience must read off this chart?**
Then map the data shape:

| Data shape / intent | Chart | Notes |
|---|---|---|
| Categories compared by one metric | **`bar`** (DEFAULT) | one hero category → `options.focus` |
| Long Korean labels, ranking, 5–12 items | **`horizontal_bar`** | labels never rotate; horizontal IS the fix |
| Same categories × 2–4 series, absolute values | **`grouped_bar`** | >4 series → aggregate or split |
| Parts stacking to a meaningful total | **`stacked_bar`** | 2–4 parts; mixed signs forbidden |
| Share structure across groups (totals differ) | **`stacked_bar_100`** | only 2 parts → `line`/`area` of the share instead |
| One metric over ≥4 time points | **`line`** | <4 points → `bar` or `kpi_cards` |
| 2–3 metrics' trajectories compared | **`multi_line`** | same unit only; different units → `combo` |
| Trend where cumulative volume matters | **`area`** | 1–2 series; more → `line` |
| Two numeric variables' relationship | **`scatter`** | both axes must be numeric |
| Quantity (bars) + rate (line), different units | **`combo`** | e.g. 매출 + 영업이익률 |
| Decomposing a change into +/− contributions | **`waterfall`** | bridge analysis, 증감 분해 |
| Actual vs target per metric | **`bullet`** | KPI 달성률 rows |
| Share of a whole, ≤5 parts | **`pie` / `donut`** | gate-enforced; donut center = total |
| Single completion rate | **`gauge`** | one number vs max |
| 5–8 dimensions, one shared scale | **`radar`** | gate-enforced |
| 1–8 headline numbers | **`kpi_cards`** | ≤3 data points? This is usually the answer |
| Per-item completion % | **`progress`** | OKR rows |
| Sequential narrowing stages, 3–5 | **`funnel`** | conversion between stages auto-annotated |
| Two categorical axes × intensity | **`heatmap`** | ≤12×14 cells |
| 3–12 items' share by area | **`treemap`** | >12 → table |

Deeper rationale + anti-pattern catalog:
[references/chart-selection.md](references/chart-selection.md).
Types OUTSIDE these 21 (sankey, gantt, org chart, SWOT, process flows …)
stay on the `templates/charts/` template-adaptation path.

### Negative rules (read before picking anything fancy)

Enforced by the renderer where possible (`ChartJudgmentError` names the
better chart):

1. **Default is `bar`.** Any other type must be justified by the data shape
   above. "보기 좋아서" is not a justification.
2. **`pie`/`donut` only when ≤5 slices AND parts of one whole.** Otherwise
   `horizontal_bar` (sorted). Never for precise comparison; negatives never.
3. **`radar` only when 5–8 axes share one scale.** Different units → normalize
   first or use `grouped_bar`. Max 3 polygons.
4. **≤3 data points → `kpi_cards`,** not a chart.
5. **No 3D, shadows, gradients, glow, or decorative effects.** The engine
   never emits them; do not post-edit them in.
6. **Colors come ONLY from spec_lock.** Never specify colors in specs or
   post-edit hexes. Series = single-accent opacity ladder on the locked
   accent; semantic green/red only where data means gain/loss (waterfall,
   KPI deltas) — lock `positive:`/`negative:` rows to override the defaults.
7. **Series cap is 4** (ladder depth). More → aggregate to top-3 + 기타.
8. **Every chart page pairs with a takeaway line** — the chart shows the
   shape; an adjacent line states the so-what.

---

## 2. Usage

### Render one chart

```bash
# spec.json 작성 후 (schema: references/spec-format.md)
python3 .claude/skills/chart-design/scripts/render_chart.py spec.json \
    --project <project_path> -o chart_frag.svg --pos 60,220

# 미리보기 (배경 포함 완전한 SVG)
python3 ... spec.json --project <project_path> -o preview.svg --standalone

# 스펙/판단 게이트만 검사
python3 ... spec.json --project <project_path> --validate-only
```

`--project` points at the deck project directory (the one holding
`spec_lock.md`). Minimal spec:

```json
{
  "type": "bar",
  "unit": "억",
  "width": 720, "height": 420,
  "data": [
    {"label": "서울", "value": 124},
    {"label": "부산", "value": 87}
  ],
  "options": {"focus": "서울"}
}
```

### Embed into a page

Output is `<g id="chart_bar" data-chart-type="bar">` containing
`<g id="chartArea">` + the plot-area marker, with **absolute page coordinates
baked in** via `--pos X,Y` (no wrapper transform). Paste into the page SVG in
`svg_output/`. One chart per page keeps the default `chartArea` id; a second
chart on the same page needs `--area-id chartArea2`. Keep the spec JSON next
to the project — it is the data source of truth for re-renders.
Full contract: [references/integration.md](references/integration.md).

### Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 2 | `SpecError` — malformed spec | fix the JSON per references/spec-format.md |
| 3 | `TokenResolutionError` — spec_lock unreadable/incomplete | run the Strategist flow / update_spec.py to lock the missing values; NEVER hand-substitute colors |
| 4 | `ChartJudgmentError` — wrong chart for this data | the message names the correct type; restructure and re-render |

---

## 3. What lives where

```
chart-design/
├── SKILL.md                     ← you are here (selection judgment + rules)
├── references/
│   ├── spec-format.md           ← full JSON schema for all 21 types
│   ├── chart-selection.md       ← extended judgment: channel accuracy, anti-patterns
│   └── integration.md           ← ppt-master embedding + spec_lock token flow
├── scripts/
│   ├── render_chart.py          ← CLI entry point (--project <deck>)
│   ├── build_examples.py        ← re-render examples/ (optionally from a real deck)
│   └── chartlib/                ← tokens (spec_lock adapter) + 3 engines + 21 renderers
└── examples/                    ← 1 rendered SVG + spec per type (Korean labels)
    └── sample_project/          ← minimal spec_lock used by the examples
```

### After a spec_lock change

Charts are pure functions of (spec, spec_lock). When colors/fonts change via
`update_spec.py`, re-render every chart spec of that deck and re-paste the
fragments — same discipline as update_spec's SVG propagation, but through the
renderer instead of hand-editing hexes.
