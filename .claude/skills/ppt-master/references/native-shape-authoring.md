> See [`native-objects.md`](./native-objects.md) §§1–2 for the native-shape metadata and validation contracts.

# Native Preset Shape Authoring Reference

Use this reference during Executor SVG construction when one standard
PowerPoint shape can express one complete geometric object. The helper does
not create the preset shape's own `p:txBody`; keep visible text outside the
atomic fragment. §6 binds diagram lines to the shapes they join.

## 1. Selection Gate

Apply this decision order before drawing a stock geometric object.

> This gate is for picking the **right** native shape, not for avoiding presets.
> When a page needs an arrow, chevron, callout, banner, flowchart node, or a
> literal Office symbol, authoring it as a preset is the **default** — the
> ordinary-SVG rows below are deliberate exceptions, not the norm.

| Condition | Action |
|---|---|
| Plain rectangle, symmetric rounded rectangle, circle, or ellipse | Write the ordinary SVG primitive; the exporter already emits an editable native shape. |
| Line that joins two diagram shapes | Write a bound `<line>` / `<polyline>` / `<path>` route (§6), not a helper connector fragment. |
| One DrawingML preset exactly expresses the intended object | Run `preset_shape_svg.py render`, then insert its complete stdout fragment into the hand-authored page. |
| The visual meaning or contour exceeds one stock shape | Write ordinary `<path>` / `<polygon>` geometry; export keeps it as editable custom geometry. |
| The shape only resembles a preset | Keep ordinary SVG; never infer a preset from contour similarity. |
| Mirror/preserve input already owns native-shape metadata | Keep the existing object and metadata; never reselect its preset. |

**Hard rule**: `preset_shape_svg.py` is the only authoring entry for
`data-pptx-authoring="preset"`. Never add `data-pptx-prst`, frame, adjustment,
carrier, preview, or fingerprint attributes to a hand-written path.

---

## 2. Semantic Preset Candidate Guide

Use the table below as the **go-to menu**: match the page's visual intent to a
candidate preset *before* defaulting to a plain rect or path. Reaching here
first is exactly how presets get used instead of forgotten.

"Automatic" means the Executor independently applies this semantic decision
gate before drawing a new object. It does not scan existing SVG, classify
paths or contours, or upgrade ordinary SVG during export.

| Visual intent | Candidate presets | Boundary |
|---|---|---|
| Literal geometric body | `triangle`, `diamond`, `pentagon`, `hexagon`, `octagon`, `star5` | Use only when the named geometry itself is the intent. |
| Solid block direction | `rightArrow`, `leftArrow`, `upArrow`, `downArrow`, `leftRightArrow`, `upDownArrow`, `chevron` | Thin relationship lines stay ordinary SVG `<line>` / `<path>`; bind them (§6) when both ends touch shapes. |
| Standard flowchart node | `flowChartProcess`, `flowChartDecision`, `flowChartInputOutput`, `flowChartTerminator`, `flowChartDocument` | Use only for an actual flowchart; ordinary content cards remain cards. |
| Standard connector route | `straightConnector1`, `bentConnector*`, `curvedConnector*` | Helper fragments export unattached; use one only for a free-standing connector. A connector that joins shapes is a bound route (§6). |
| Stock callout | `wedgeRectCallout`, `wedgeRoundRectCallout`, `wedgeEllipseCallout`, `cloudCallout` | Brand-specific or custom-tail callouts remain free SVG. |
| Stock ribbon or scroll | `ribbon*`, `ellipseRibbon*`, `verticalScroll`, `horizontalScroll` | Select only when the stock contour is visually acceptable. |
| Standalone math symbol | `mathPlus`, `mathMinus`, `mathMultiply`, `mathDivide`, `mathEqual`, `mathNotEqual` | Inline formulas and prose symbols remain text/formula assets. |
| Literal Office symbol | `heart`, `sun`, `moon`, `lightningBolt`, `gear6`, `gear9` | Never replace an icon required by `spec_lock.icons`. |

Use registry search for a less common literal shape:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py list --search arrow
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py describe rightArrow
```

**Forbidden — false native semantics**:

- `actionButton*` when navigation or trigger behavior is expected; the helper
  maps its visual preset geometry only and never creates an action or hyperlink;
- `chartX`, `chartStar`, or `chartPlus` as a substitute for native charts;
- logo, icon glyph, illustration, brand contour, or data-chart marks.

---

## 3. Fragment Generation

Run one command for one selected object. Colors must come from the current
page's re-read `spec_lock.md`.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render rightArrow \
  --id p03-growth-arrow \
  --frame 160 210 320 112 \
  --fill "#2563EB" \
  --stroke none \
  --adjust "adj1=val 50000"
```

For a native connector:

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py render bentConnector3 \
  --id p03-flow-connector \
  --object-kind connector \
  --frame 420 180 220 140 \
  --fill none \
  --stroke "#475569" \
  --stroke-width 2
```

Every connector-family preset requires `--object-kind connector`, `--fill none`,
and a visible stroke. It exports as an unconnected `p:cxnSp`; a connector
preset can never be authored as an ordinary `shape`. To attach a connector to
shapes, write a bound route (§6) instead.

For several presets on the current page, write each object's `render`
parameters (keys = flag names) into one JSON list and run one call. The output
equals the single calls in list order; one invalid entry stops the call before
any fragment prints.

```bash
python3 ${SKILL_DIR}/scripts/preset_shape_svg.py --batch <page_shapes.json>
# [{"preset": "chevron", "id": "p12-phase-1", "frame": [44, 150, 376, 52],
#   "fill": "#0F2A4A", "adjust": ["adj=val 30000"]}, ...]
```

**Hard rule — stdout-only exception**: the helper prints deterministic `<g>`
fragments, one per object. Read that output and insert it through a normal hand edit of
the page file (Edit / `apply_patch`, whichever the host provides). Do not redirect it into `svg_output/`, loop over pages,
batch shapes from more than one page, or let it choose layout. The main Agent still authors every
complete SVG page sequentially.

---

## 4. Atomic Fragment Contract

The helper emits one logical group containing exactly one hidden native carrier
and one complete visible preview.

| Component | Ownership |
|---|---|
| Logical `<g data-pptx-authoring="preset">` | Stable id, object kind, preset, frame, adjustments, and preview fingerprint. |
| `path[data-pptx-part="geometry"]` | Native PowerPoint export authority; hidden from the browser. |
| `g[data-pptx-part="geometry-preview"]` | Browser-visible preset drawing. |
| `path[data-pptx-part="geometry-detail"]` | One visible layer per DrawingML path, including path-level fill/stroke behavior. |

**Hard rule**: treat the returned group as atomic. Put labels, icons, or other
decorations beside it in a parent `<g>`, never inside the preset group.

**Frame coordinate space**: `--frame x y w h` is expressed in the coordinate
space where you insert the fragment. At the page root that is page coordinates;
inside a `<g transform="translate(…)">` use **group-local** coordinates — the
ancestor transform stacks on top, so page-absolute values would double-offset
the shape off-canvas.

**Regeneration rule**: rerun the helper when preset, frame, adjustment, fill,
stroke, or stroke width changes. Moving, scaling, rotating, or flipping the
complete logical group is allowed; zero-scale transforms and shear/skew are
forbidden, and the transformed frame must remain inside DrawingML's coordinate
range. Stroke width must remain inside DrawingML's line-width range. To freely
edit the contour, replace the whole fragment with ordinary SVG rather than
modifying a `geometry-detail` path.

---

## 5. Boundaries

| Concern | Behavior |
|---|---|
| Shape text | Keep visible SVG `<text>` outside the atomic fragment. It remains editable but may export as a grouped text box rather than the preset's own `p:txBody`. |
| Connector attachment | Helper connector fragments export an unconnected `p:cxnSp` and accept no endpoint metadata. Attach a connector with a bound route (§6). Never hand-add `data-pptx-start-shape-id` / `data-pptx-end-shape-id`; that pair belongs to imported decks. |
| Action button behavior | `actionButton*` presets map visual geometry only. No action, navigation target, or hyperlink is created automatically. |
| Gradient/pattern paint | Authoring helper v1 accepts solid HEX paint only. Use ordinary SVG when a complex paint treatment is essential. |
| Multi-path darken/lighten | Browser preview uses the shared normalized paint behavior from the PPTX importer. |
| External edits | Any preview or semantic mismatch fails quality check and export; regenerate the fragment. |

**Validation**: `svg_quality_checker.py` independently rerenders every authored
preset from registry metadata and compares the carrier, visible layers, style,
and fingerprint before export.

---

## 6. Connector Binding

A bound route exports as a native `p:cxnSp` with `a:stCxn` / `a:endCxn`, so
the line stays attached when a user moves either shape in PowerPoint. An
unbound line exports exactly as before.

**Default — bind (may override for a rule, bracket, divider, or leader line)**:
every line whose two ends touch diagram shapes — flowchart, deal structure,
hub-and-spoke, org chart.

| Step | Action |
|---|---|
| 1. Name each target | Put an `id` on the shape element the line touches: `<rect>`, `<circle>`, `<ellipse>`, or a helper shape fragment `<g>`. An id on a wrapper `<g>` (card with text) does not bind. |
| 2. Draw the route | First point = start, last point = end. Straight: `<line>`. Elbow: `<polyline>` or `<path>` (`M` then `H` / `V` / `L`) with horizontal and vertical segments and one or two bends. |
| 3. Bind | Add `data-pptx-start="<id>"` and `data-pptx-end="<id>"` to the route. Omit one to leave that end free. |
| 4. Pin a site (optional) | Add `data-pptx-start-site="N"` / `data-pptx-end-site="N"`. Without it, export takes the target's site nearest to the route end. |

```xml
<rect id="p05-step-1" x="80" y="300" width="200" height="96" rx="8" fill="#F4F5F7"/>
<rect id="p05-step-2" x="400" y="300" width="200" height="96" rx="8" fill="#F4F5F7"/>
<line x1="280" y1="348" x2="400" y2="348" stroke="#4B5563" stroke-width="2"
      marker-end="url(#arrow)" data-pptx-start="p05-step-1" data-pptx-end="p05-step-2"/>
<polyline points="500,396 500,440 180,440 180,396" fill="none" stroke="#4B5563"
          stroke-width="2" data-pptx-start="p05-step-2" data-pptx-end="p05-step-1"/>
```

| Route | Native connector |
|---|---|
| `<line>`, or one straight segment | `straightConnector1` |
| Orthogonal, one bend | `bentConnector2` |
| Orthogonal, two bends (U-turns included) | `bentConnector3`; the bend position becomes `adj1` |

Stroke, dash, opacity, and `marker-start` / `marker-end` arrowheads export as
on any line; route fill is ignored.

**Reference — not a constraint**: connection sites by index, for `-site`
overrides.

| Target | Sites |
|---|---|
| `<rect>` (rect / roundRect), `flowChartProcess`, `flowChartAlternateProcess`, `flowChartDecision`, `flowChartTerminator`, `flowChartPredefinedProcess`, `diamond` | 0 top · 1 left · 2 bottom · 3 right (edge midpoints) |
| `<circle>`, `<ellipse>`, `flowChartConnector` | 0 top · 1 upper-left · 2 left · 3 lower-left · 4 bottom · 5 lower-right · 6 right · 7 upper-right |
| `chevron` | 0 top edge · 1 left notch · 2 bottom edge · 3 right tip |
| `homePlate` | 0 top edge · 1 left · 2 bottom edge · 3 right tip |
| Other presets | Keep the nearest-site default; `preset_shape_svg.py describe <preset>` prints `connection_site_count`. |

**Default — end each route on its site (may stop a few px short for an
arrowhead)**: PowerPoint moves an off-site end onto its site the first time a
connected shape moves, so the line jumps.

**Forbidden — routes and targets export cannot bind** (quality-check error;
export stops):

- curves, diagonal elbow segments, more than two bends, or a route that
  doubles back;
- a target that is text, an image, a line, an ordinary `<path>` / `<polygon>`,
  a plain `<g>`, a Master/Layout atom, or a `<rect>` with unequal `rx` / `ry`;
- a route end more than 16 px outside its target's box (usually swapped
  start/end);
- `data-pptx-start` / `data-pptx-end` on a helper connector fragment; helper
  fragments stay unconnected.

> Note: one route joins one pair of shapes. For an org-chart bus, draw one
> elbow per parent–child pair; the shared trunk segments overlap.

**Validation**: `svg_quality_checker.py` runs the exporter's resolver
([`connectors.py`](../scripts/svg_to_pptx/drawingml/connectors.py)) and reports
an unknown id, an unconnectable target, an out-of-range site, or an unsupported
route as an error.
