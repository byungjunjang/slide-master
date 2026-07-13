# Spec Format — all 21 chart types

Every spec is one JSON object:

| Field | Type | Default | Meaning |
|---|---|---|---|
| `type` | string | required | one of the 21 type names below |
| `data` | varies | required | see per-type shapes |
| `unit` | string | `""` | value suffix rendered into labels (`"억"`, `"%"`, `"만"`) |
| `width` / `height` | number | 720 / 420 | fragment region size in slide px |
| `options` | object | `{}` | per-type extras |

Values are plain numbers (no formatting) — the renderer adds thousands commas
and the unit. Labels may be Korean; text is measured with real Pretendard
metrics for truncation/thinning.

Judgment gates raise `ChartJudgmentError` (exit 4) with the correct
alternative; do not work around them.

---

## Cartesian (12)

### `bar` / `horizontal_bar`
```json
{"type": "bar", "unit": "억",
 "data": [{"label": "서울", "value": 124}, {"label": "부산", "value": 87}],
 "options": {"focus": "서울"}}
```
- `data`: 2–12 `{label, value}` rows. >12 → gate. ≤3 → stderr warning
  (kpi_cards 권장; suppress with `options.allow_tiny: true` when intentional).
- `options.focus`: label string or index — that bar gets the accent, the rest
  are muted (focus-comparison lock). Omit → all bars accent.
- Long labels or >8 items → prefer `horizontal_bar`.

### `grouped_bar`
```json
{"type": "grouped_bar", "unit": "억",
 "data": {"categories": ["1분기", "2분기"],
          "series": [{"name": "국내", "values": [42, 48]},
                     {"name": "해외", "values": [18, 24]}]}}
```
- 2–4 series (T4 ladder cap). Legend renders automatically.

### `stacked_bar` / `stacked_bar_100`
Same `data` shape as `grouped_bar`. Constraints: 2–4 series, values ≥ 0.
`stacked_bar` labels each column's total; `stacked_bar_100` normalizes each
column to 100% (unit fixed to `%`).

### `line` / `multi_line` / `area`
Same `data` shape as `grouped_bar` (categories = time points, in order).
- `line`: 1–3 series. `multi_line`: alias that requires ≥2.
- `area`: 1–2 series; first series fill-opacity 0.18, second 0.32.
- <4 time points → stderr warning (trend needs ≥4; consider bar/kpi_cards).
- Last value of each series is labeled at the line end automatically.

### `scatter`
```json
{"type": "scatter",
 "data": [{"x": 3.2, "y": 68, "label": "A제품"}, {"x": 5.5, "y": 74}],
 "options": {"x_label": "마케팅 투자(억)", "y_label": "만족도(점)"}}
```
- ≥3 points; `label` optional (annotate only the points worth naming).

### `combo` (bar + line, dual axis)
```json
{"type": "combo", "unit": "억",
 "data": {"categories": ["2024", "2025", "2026"],
          "bars": {"name": "매출", "values": [168, 190, 224]},
          "line": {"name": "영업이익률", "values": [10.4, 11.8, 13.5]}},
 "options": {"line_unit": "%"}}
```
- Left axis = bars, right axis = line. Use ONLY when units differ and the two
  metrics tell one story.

### `waterfall`
```json
{"type": "waterfall", "unit": "억",
 "data": [{"label": "기초 이익", "value": 120, "total": true},
          {"label": "매출 증가", "value": 45},
          {"label": "원가 상승", "value": -28},
          {"label": "기말 이익", "total": true}]}
```
- `total: true` + `value` → anchor bar that (re)sets the running level (기초).
- `total: true` without `value` → reports the running level (기말/중간 합계).
- Positive deltas fill `positive`, negative `negative`, anchors `accent`
  (the only semantic-color charts besides KPI deltas).

### `bullet`
```json
{"type": "bullet", "unit": "억",
 "data": [{"label": "매출", "value": 92, "target": 100, "max": 120}]}
```
- 1–5 rows; `max` optional (defaults to fitting value/target).
- Renders track / measure / target tick / `값 (달성%)`.

---

## Polar (4)

### `pie` / `donut`
```json
{"type": "donut",
 "data": [{"label": "구독", "value": 58}, {"label": "광고", "value": 27},
          {"label": "커머스", "value": 15}],
 "options": {"center_label": "1,240억"}}
```
- GATE: 2–5 slices, values ≥ 0. Labels show `이름 NN%` computed from the sum.
- `center_label` (donut only): the headline total in the hole.

### `gauge`
```json
{"type": "gauge", "unit": "%", "data": {"value": 73, "max": 100, "label": "연간 목표 달성률"}}
```

### `radar`
```json
{"type": "radar",
 "data": {"axes": ["기획", "개발", "디자인", "마케팅", "운영"], "max": 100,
          "series": [{"name": "우리 팀", "values": [82, 91, 74, 63, 78]}]}}
```
- GATE: 5–8 axes, ≤3 series. `max` sets the shared scale (default: data max) —
  axes MUST be same-scale; normalize before writing the spec if they aren't.

---

## Layout (5)

### `kpi_cards`
```json
{"type": "kpi_cards", "width": 900, "height": 220,
 "data": [{"label": "연 매출", "value": "1,240억", "delta": 18.2},
          {"label": "NPS", "value": 62, "delta": -3.0, "delta_unit": "p"}]}
```
- 1–8 cards (2×2 grid at 4+, row otherwise). `value` may be a preformatted
  string or a number. `delta` colors positive/negative with ▲/▼.
- Card treatment follows the theme's `surface.card_style` automatically.

### `progress`
```json
{"type": "progress",
 "data": [{"label": "제품 로드맵", "value": 82}, {"label": "보안 인증", "value": 91}]}
```
- `value` = percent 0–100. ≤8 rows.

### `funnel`
```json
{"type": "funnel", "unit": "만",
 "data": [{"label": "방문", "value": 120}, {"label": "가입", "value": 48},
          {"label": "결제", "value": 9}]}
```
- GATE: 3–5 stages. Stage-to-stage 전환% and 전체 전환율 annotate automatically.
- Values should narrow monotonically (warning otherwise).

### `heatmap`
```json
{"type": "heatmap",
 "data": {"rows": ["월", "화"], "cols": ["09시", "11시"],
          "values": [[12, 28], [15, 30]]},
 "options": {"show_values": true}}
```
- GATE: ≤12 rows × ≤14 cols. Intensity = accent opacity scale; cell text
  auto-switches for contrast.

### `treemap`
```json
{"type": "treemap", "unit": "억",
 "data": [{"label": "클라우드", "value": 420}, {"label": "모바일", "value": 310}]}
```
- GATE: 3–12 positive items, single level (squarified). Labels show
  `값 · NN%`; tiny cells drop labels automatically.
