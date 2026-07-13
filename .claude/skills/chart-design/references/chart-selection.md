# Chart Selection — extended judgment reference

Deeper rationale behind SKILL.md §1. Selection heuristics adapted from
antvis/chart-visualization-skills (MIT) — judgment only; all rendering here is
original pure SVG.

## Visual channel accuracy (why bar is the default)

Human perception decodes channels with very different precision:

| Channel | Precision | Used by |
|---|---|---|
| Position on a common scale | highest | bar, line, scatter, bullet |
| Length | high | bar family, progress |
| Angle / arc | mediocre | pie, donut, gauge |
| Area | mediocre-low | treemap, bubble |
| Color luminance | low (ordinal at best) | heatmap, treemap intensity |

Bar charts sit on the two most accurate channels — that's the entire argument
for "default is bar". Every step down the table needs a reason the weaker
channel still communicates the ONE thing the slide must say.

## Per-type anti-patterns (gate rationale)

| Type | Don't use when… | Because → use instead |
|---|---|---|
| `bar` | showing a continuous trend | bars hide slope → `line`/`area` |
| `bar` | part-to-whole is the point | separate bars don't sum visually → `stacked_bar`/`donut` |
| `grouped_bar` | >4 series | sub-bars get too thin to compare → aggregate or split charts |
| `grouped_bar` | share matters more than absolutes | → `stacked_bar`/`stacked_bar_100` |
| `stacked_bar` | comparing ONE series' trend across columns | non-aligned baselines mislead → `line` per series |
| `stacked_bar_100` | absolute totals matter | normalization hides scale → `stacked_bar` |
| `line` | categories have no order (지역, 제품명) | a slope between 서울 and 부산 is fiction → `bar` |
| `line` | <4 time points | trend not established → `bar`/`kpi_cards` |
| `area` (multi, unstacked) | series overlap | occlusion → stacked area or `multi_line` |
| `scatter` | either axis is categorical | position carries no relation → `bar`/`heatmap` |
| `pie`/`donut` | >5 slices | slivers become indistinguishable → sorted `horizontal_bar` |
| `pie`/`donut` | precise comparison needed | angle decoding is imprecise → `bar` |
| `pie`/`donut` | zero/negative values | a negative slice is meaningless → `bar`/`waterfall` |
| `radar` | axes on different scales | polygon shape becomes an artifact of units → normalize or `grouped_bar` |
| `radar` | >8 axes or >3 series | overlap soup → split or `grouped_bar` |
| `funnel` | values don't narrow monotonically | "funnel" implies conversion loss → `bar` |
| `heatmap` | continuous x/y | cells imply discrete crossings → `scatter` |
| `treemap` | <3 or >12 items | tiny sets → `donut`; big sets → table |
| `combo` | both metrics share a unit | dual axes invite fake correlation → `multi_line` |
| any chart | ≤3 data points | a chart is slower than the numbers → `kpi_cards` |

## Common mistakes (❌ → ✅)

**❌ Line chart over unordered categories**
지역별 GDP를 folded line으로 → 지역 간 "추세"라는 착시.
**✅** `bar` (값 내림차순 정렬 + `options.focus`로 주인공 하나).

**❌ 10-slice pie**
시장점유율 10개사 파이 → 5도짜리 조각들은 읽히지 않음.
**✅** `horizontal_bar` 내림차순, 상위 1개 focus, 나머지 muted.

**❌ Radar with 매출(억)·성장률(%)·NPS(점) axes**
단위가 다른 축의 다각형 모양은 데이터가 아니라 단위 선택의 결과.
**✅** 축을 0–100으로 정규화한 뒤 radar, 또는 축별 `grouped_bar`.

**❌ Series-per-color rainbow**
계열마다 새 hue → 대시보드 미학, anti-slop T4 위반.
**✅** 단일 액센트 투명도 사다리(자동) — 4계열 초과면 데이터를 합쳐라.

**❌ "화려하니까 treemap"**
5개 항목 구성비를 treemap으로 → donut이 두 배 빨리 읽힘.
**✅** 항목 6개 이상 + 면적 비교가 요점일 때만 treemap.

## Decision procedure (when the table doesn't settle it)

1. Write the takeaway sentence first (e.g. "구독 매출이 절반을 넘었다").
2. The sentence's verb picks the family: 비교한다→bar, 변한다→line,
   구성한다→pie/stacked, 관계있다→scatter, 도달했다→gauge/bullet.
3. Count the data: points, series, categories — run the gates in SKILL.md §1.
4. If two types survive, pick the one higher in the visual-channel table.
5. If you're still torn, it's `bar`.
