# ppt-master Integration

How chart-design plugs into the ppt-master pipeline: spec_lock token flow,
embedding contract, workflow interplay, and re-render discipline.

## 1. Token flow (SPEC_LOCK discipline, by construction)

```
Strategist confirmation → <project>/spec_lock.md   (deck's execution lock)
        └─▶ chartlib/tokens.py resolve_style(project=…)   (read at every render)
               └─▶ ChartStyle contract → renderers
```

- **Single source per deck**: `<project_path>/spec_lock.md` — the same file
  the Executor re-reads before every page. chart-design parses `## colors`
  and `## typography` at RENDER time; nothing is cached in the skill.
- **Required locks**: `bg`, `text`, `text_secondary`, `border`,
  `accent` (or `primary`), a `font_family`/`body_family` stack, and the
  `body` px anchor — all present in the spec_lock skeleton. Missing any →
  `TokenResolutionError` (exit 3); extend the lock via the Strategist /
  `update_spec.py`, never by hand-patching chart colors.
- **Derived roles, drift-clean**: roles the lock doesn't define
  (border-strong, surface-alt tints, text-tertiary, accent-soft) are emitted
  as **locked hex + fill/stroke-opacity** — every literal hex in chart output
  exists in spec_lock, so `svg_quality_checker.py`'s spec_lock-drift scan
  reports clean. Decks that DO lock those roles get the locked solids.
- **Series palette**: single-accent opacity ladder
  `(accent, 0.85 / 0.60 / 0.40 / 0.25)` — max 4 series, judgment-gated.
- **Semantics**: waterfall deltas and KPI deltas use `positive` / `negative`
  (/ `warning`) rows when locked; otherwise conventional green/red/amber
  fallbacks. Lock the rows to override deck-wide.
- **Typography mapping**: chart text roles map from locked px slots —
  caption ← `chart_annotation`|`annotation`, label ← `footnote`,
  title ← `subtitle`, headline ← `title`, KPI/center numbers ←
  `hero_number` (falls back to clean ratios of `body`). Font stack is the
  locked `body_family`/`font_family` verbatim (Pretendard-led under this
  install's font policy).

## 2. Embedding contract (Executor)

1. Decide the chart region on the canvas (`## canvas` in spec_lock; ppt169 =
   1280×720). Typical content-area chart: below the headline block,
   x 60–1220, y ≈ 190–660.
2. Write the spec with that region's `width`/`height`; keep the spec JSON in
   the project (it is the numbers' source of truth).
3. Render with `--project <project_path> --pos X,Y` — coordinates are baked
   into the fragment (no wrapper transform; regex-based checks resolve
   absolute text positions).
4. Paste the `<g id="chart_…" data-chart-type="…">` fragment into the page
   SVG in `svg_output/`. The wrapper `<g id>` satisfies the element-grouping
   rule; the inner `<g id="chartArea">` + `chart-plot-area` comment satisfies
   executor-base **§3.1 (MANDATORY)** — verify with
   `grep "chart-plot-area" <page>.svg` like any hand-drawn chart page.
5. Multiple charts on one page: give the second `--area-id chartArea2` (ids
   must stay unique) and keep ≥24px between fragment bounding boxes.
6. Charts assume the page `bg` behind them; don't place fragments on accent
   bands.
7. **Takeaway adjacency**: every chart page pairs the chart with a takeaway
   line (1 metric + 1 trend + 1 context) per ppt-master's chart-page rhythm.

Post-processing: fragments pass `svg_quality_checker.py` (0 errors, 0
warnings, spec_lock drift: none — validated end-to-end) and both
`svg_to_pptx.py` export modes; `<text>` survives as editable DrawingML runs.

## 3. Workflow interplay

- **`design_spec.md §VII` / `spec_lock page_charts`**: `page_charts` maps
  pages to `templates/charts/` template adaptations. For the 21 quantitative
  types chart-design covers, prefer rendering with real data over adapting
  the static template — leave the page OUT of `page_charts` (the
  "no-template-match / design from scratch" branch) and render here instead.
  Types outside the 21 (sankey, gantt, org, SWOT, process flows, …) stay on
  the template path.
- **`verify-charts` workflow**: consumes the `chart-plot-area` marker each
  fragment already carries — no extra authoring step.
- **`update_spec.py`**: after a color/font change, re-render the deck's chart
  specs and re-paste fragments (charts are derived artifacts; specs are
  source). update_spec's regex propagation also works on chart fragments
  since fills are literal locked hexes, but re-rendering is the supported
  path (opacity paints and derived text sizes stay consistent).
- **Page metadata**: `data-pptx-page-role` (flat routes) and structured
  Master/Layout identity remain page-level Executor responsibilities —
  chart-design only owns its fragment.

## 4. Relationship to `templates/charts/` (52-type static library)

The static library remains the browsing/selection REFERENCE and still owns
non-quantitative visualization types and the CHART_STYLE_GUIDE card patterns.
chart-design is the data-driven RENDERER for the 21 quantitative types: real
numbers in, correct geometry out, spec_lock styling guaranteed, plot-area
marker included.
