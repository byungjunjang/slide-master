# Shared Technical Standards

Mandatory reference for every PPT Master route that authors or regenerates slide visuals through SVG: owns shared XML/SVG constraints, editable PPTX mappings, advanced effects, geometry recipes, and PPT-specific interfaces.
Other files link here instead of restating its contracts.

**Document map**:

| Section | Owns | Strength |
|---|---|---|
| §1 Required Foundation, Forbidden Features, and Conditional Interfaces | XML validity, the exhaustive structural blacklist, native line ends, image clipping, static local reuse, and imported/authored native-shape semantics | Required / Forbidden / Conditional |
| §2 Conditional Compatibility Mappings | Inline geometry and approximate group opacity | Conditional |
| §3 Canvas Format Quick Reference | Pointer to the complete canvas catalog | Reference |
| §4 Required Page Contract and Conditional Packaging | Complete-page authority, semantic markers, editable text/grouping, and package promotion | Required / Conditional |
| §5 Workflow Authority | Pointer to the serial post-processing/export procedure | Workflow pointer |
| §6 Advanced SVG Effects and Authoring Techniques | Color/alpha, gradients, shadows, glow, overlays, lines, text treatments, transforms, freeform geometry, chart geometry, and constructed visual styles | Contract + optional recipes |
| §7 Conditional PPT Interfaces | Pattern fills; pointers to the conditionally loaded [`native-objects.md`](./native-objects.md) and [`structured-templates.md`](./structured-templates.md) contracts | Conditional |
| §8 Scope Boundary | Concerns intentionally owned by another reference or workflow | Boundary |

**Advanced capability index**:

| Capability family | Available authoring vocabulary | Detail |
|---|---|---|
| Color and transparency | CSS alpha colors; fill, stroke, text, picture, stop, element, and group opacity | §2.2, §6.2 |
| Gradients and paint | Linear/radial fills, transparent stops, gradient text, gradient strokes, and preset patterns | §6.3, §7 |
| Depth and light | Soft/colored/directional shadow, glow, layered-geometry fallback, and paper-layer elevation | §6.4 |
| Image treatment | Directional scrim, bottom fade, vignette, spotlight, brand wash, picture fading, and glass-like surfaces | §1.2, §6.5 |
| Lines and connectors | Preset/custom dash, cap/join, gradient flow strokes, markers, and explicit-grid paths | §1.1, §6.6 |
| Text treatments | Mixed runs, tracking, underline, strikethrough, gradient fill, outline, transparency, watermark text, and text glow | §4.2, §6.7 |
| Transforms and composition | Translate, scale, rotate, mirror, supported matrix composition, layering, and static local reuse | §1.3, §6.8 |
| Freeform geometry | Full SVG path vocabulary, curves, organic containers, multi-subpaths, and asymmetric rounded rectangles | §6.9 |
| Imported PowerPoint shapes | Lossless import payload, lightweight inspection projection, and selective restoration of preset/custom geometry, connectors, and unchanged native text bodies | [`native-objects.md`](./native-objects.md) §1 |
| Authored PowerPoint preset shapes | Registry-generated visible fragments that export as one native preset shape or connector | [`native-shape-authoring.md`](./native-shape-authoring.md); [`native-objects.md`](./native-objects.md) §2 |
| Radial/chart geometry | Pie/donut arcs, dashed-circle ring segments, gauges, progress rings, sunbursts, and diagonal polygon arrowheads | §6.10 |
| Constructed visual styles | Faux glass, hand-drawn marks, ink wash, Riso offset, pixel grid, halftone, isometric facets, paper cut, and line-plus-area data treatment | §6.11 |
| Unsupported-effect fallbacks | Raster baking or explicit-geometry alternatives for blur, inner shadow, soft edge, reflection, turbulence, blend modes, and arbitrary masks | §6.12 |
| Selection quick reference | Grouped scenario routing; fidelity remains in owning subsections | §6.13 |

**Fidelity labels**:

| Label | Meaning |
|---|---|
| `Native-stable` | Generated PPTX uses the corresponding native DrawingML property or object and retains the documented semantics within the technique-specific limits. |
| `Native-normalized` | Export targets an editable DrawingML equivalent, but normalizes the SVG into another structure such as a freeform, run property, or simplified paint/effect. |
| `Approximate` | DrawingML has no exact SVG equivalent; export targets the intended effect through a documented approximation, and material differences require output review. |
| `Bake-required` | The runtime effect is outside the native contract; pre-render it into an image or rebuild it with explicit supported geometry. |

**Reading rules**:

- **Required** / **Forbidden** statements are non-negotiable technical boundaries.
- **Conditional** contracts apply only when the corresponding feature is used.
- **Reference — not a constraint** passages expose capabilities and recipes; they do not require every page or visual style to use them.
- The locked `visual_style` controls whether and how strongly a compatible effect is used. It never expands the technical boundary.

**Hard rule — one-way fidelity vocabulary**: the labels above describe the
`svg_output/` → generated PPTX path. They do not promise reconstruction of the
original SVG syntax, `<defs>` graph, `<use>` structure, path commands, or
`<tspan>` layout after PPTX-to-SVG import, nor pixel identity across PowerPoint,
LibreOffice, Keynote, and WPS.

**Hard rule — capability boundary**: a recipe never expands converter support.
Use only the target elements and syntax documented by each conditional
contract. Unsupported element tags fail preflight; browser-rendered attributes
outside these contracts must not be assumed to have a DrawingML mapping.

---

## 1. Required Foundation, Forbidden Features, and Conditional Interfaces

### 1.0 Text characters: must be well-formed XML

SVG is strict XML. Two rules for all text and attribute values:

| Character category | Required form | Forbidden form |
|---|---|---|
| Typography & symbols (em dash, en dash, ©, ®, →, ·, NBSP, full-width punctuation, emoji…) | **Raw Unicode characters** — write `—` `–` `©` `®` `→` directly | HTML named entities — `&mdash;` `&ndash;` `&copy;` `&reg;` `&rarr;` `&middot;` `&nbsp;` `&hellip;` `&bull;` etc. |
| XML reserved characters (`&`, `<`, `>`, `"`, `'`) | **XML entities only** — `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`) | Bare `&` `<` `>` (e.g. `R&D`, `error < 5%`) |

One offending character invalidates the file and aborts export.

**Structural blacklist** (in addition to the character rules above):

| Banned Feature | Description |
|----------------|-------------|
| `mask` | Masks |
| `<style>` | Embedded stylesheets |
| `class` | CSS selector attributes |
| External CSS | External stylesheet links |
| `<foreignObject>` | Embedded external content |
| `textPath` | Text along a path |
| `@font-face` | Custom font declarations |
| `<animate*>` / `<set>` | SVG animations |
| `<script>` / event attributes | Scripts and interactivity |
| `<iframe>` | Embedded frames |

The blacklist above is exhaustive for globally forbidden SVG syntax. Features
that require a restricted form are not globally forbidden; they are documented
under the conditional contracts below.

> **`marker-start` / `marker-end` is conditional** — see §1.1.
>
> **`clipPath` on `<image>` is conditional** — see §1.2.
>
> **Static same-document `<use>` is conditional** — see §1.3.
>
> **Imported native-shape metadata is conditional** — see §1.4.
>
> **Authored native preset fragments are conditional** — see §1.5.
>
> **Inline CSS geometry, group opacity, simple gradients, and filters are
> conditional** — see §2 and §6.
>
> **PPT preset patterns and native chart/table/template metadata are
> conditional** — see §7.

DrawingML has no arbitrary per-pixel alpha-compositing path. Effects that rely
on one, including text-knockout image fills and arbitrary alpha composites,
must be baked into a raster asset before SVG export.

---

### 1.1 Line-end Markers (Conditional Contract)

`marker-start` and `marker-end` are supported on `<line>` and `<path>` only
when the referenced marker fits this native-arrow contract:

| Concern | Required form |
|---|---|
| Reference | Exact local `url(#id)` to a `<marker>` in `<defs>` |
| Orientation | `orient="auto"` |
| Shape | A 3-vertex `<polygon>` / closed M/L-only path (triangle), 4-vertex `<polygon>` / closed M/L-only path (diamond), or one `<circle>` / `<ellipse>` (oval) |
| Path grammar | One explicit `M`/`L` command per vertex followed by `Z`; do not use `H`, `V`, curves, or an implicit multi-point `L` command inside a marker path |
| Color parity | Marker fill matches the parent line stroke; DrawingML arrows inherit the line color |

The converter maps the three shapes to DrawingML triangle, diamond, and oval
line ends. Prefer `<polygon>` for triangle/diamond markers because the vertex
count is unambiguous. Other marker shapes do not have a native mapping and are
dropped with a warning.

---

### 1.2 Image Clipping (Conditional Contract)

`clip-path` has a native picture-geometry mapping only on `<image>` elements and
only under this contract:

| Concern | Required form |
|---|---|
| `<clipPath>` element defined inside `<defs>` | Converter looks up clip defs via id index |
| Contains a **single supported** shape child | The converter uses the first supported child; multiple shapes are not composited |
| Shape is one of: `<circle>`, `<ellipse>`, `<rect>` (with rx/ry), `<path>`, `<polygon>` | These map to DrawingML geometry (preset or custom) |
| Used **only on `<image>` elements** | Non-image elements with clip-path are **forbidden** |

| SVG clip shape | DrawingML output |
|---|---|
| `<circle>` / `<ellipse>` | Full-frame `<a:prstGeom prst="ellipse"/>`; child center/radii are not preserved |
| `<rect rx="..."/>` | Full-frame `<a:prstGeom prst="roundRect"/>` with one radius adjustment; child x/y/width/height are not preserved |
| `<path>` / `<polygon>` | `<a:custGeom>` with coordinates mapped into the image frame |

`clip-path` on shapes, groups, or text is forbidden; author the target geometry
directly instead. Use a path/polygon clip when the intended contour does not
cover the full picture frame.

---

### 1.3 Static Same-Document `<use>` (Conditional Contract)

**Expansion contract**: Static local reuse is compile-time authoring shorthand. `finalize_svg.py` and
native export replace each qualifying instance with cloned primitive content;
PPTX-to-SVG import emits the resulting primitives and does **not** reconstruct
the original `<use>` / `<symbol>` structure.

| Concern | Required form |
|---|---|
| Reference syntax | Exact same-document fragment: `href="#id"` or `xlink:href="#id"`. If both attributes exist, their values MUST match. |
| Referenced target | One of `<symbol>`, `<g>`, `<use>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<path>`, `<polygon>`, `<polyline>`, `<text>`, or `<image>`. Nested local `<use>` is recursively expanded. |
| Instance position | `<use x>` / `<use y>` are finite unitless or `px` values; omitted values default to `0`. |
| Symbol viewport | A referenced `<symbol>` MUST have a finite four-number `viewBox` with positive width/height. Its `<use>` MUST have positive finite unitless or `px` `width` and `height`. |
| Aspect ratio | Default/aligned `meet` values and plain `preserveAspectRatio="none"` are supported. `slice`, `refX`, and `refY` are forbidden. |
| Viewport boundary | Symbol artwork MUST stay inside its `viewBox`; expansion does not reproduce symbol overflow clipping. |
| Internal references | Reusable subtrees use exact fragment forms: `href="#id"`, `xlink:href="#id"`, and `url(#id)`. The expander rewrites these references together with instance-local cloned IDs. |
| Structural metadata | Neither the `<use>` instance nor its referenced subtree may carry `data-pptx-layer*`, `data-pptx-native*`, or `data-pptx-placeholder*`. Author those objects directly instead of reusing them. |
| Safety limits | A reachable reference chain may contain at most 64 instances, and one SVG may expand at most 10,000 local `<use>` instances. |

**Forbidden — unsafe local references**:

- External/file/data URLs, missing targets, conflicting `href` / `xlink:href`,
  unsupported target elements, and circular reference chains
- Duplicate IDs on the referenced target, the `<use>` instance, or anywhere in
  the reused subtree
- Quoted/whitespace CSS fragment variants such as `url('#id')`; use exact
  `url(#id)` when an internal paint/filter/clip reference must be rewritten

**Contract example**:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <symbol id="statusDot" viewBox="0 0 20 20" preserveAspectRatio="xMidYMid meet">
      <circle cx="10" cy="10" r="8" fill="#16A34A"/>
    </symbol>
    <g id="legendRow">
      <rect width="120" height="32" rx="8" fill="#F1F5F9"/>
      <text x="42" y="22" font-size="16" fill="#0F172A">Ready</text>
    </g>
  </defs>
  <use href="#statusDot" x="80" y="120" width="32" height="32"/>
  <use xlink:href="#legendRow" x="120" y="120"/>
</svg>
```

---

### 1.4 Imported Native PowerPoint Shapes (Conditional Contract)

Moved to [`native-objects.md`](./native-objects.md) §1. Applies only to lossless import SVGs and unchanged imported objects on import / mirror / beautify routes; ordinary authored SVG never carries these attributes. Read that file before editing pages that contain imported native-shape metadata.

---

### 1.5 Authored Native PowerPoint Presets (Conditional Contract)

Machine contract moved to [`native-objects.md`](./native-objects.md) §2. Authoring behavior — selection gate, fragment generation, atomicity, regeneration, solid-paint boundary — stays in [`native-shape-authoring.md`](./native-shape-authoring.md), always loaded in Step 6. `svg_quality_checker.py` and export validate fragments against the registry regardless of context.

---

## 2. Conditional Compatibility Mappings

### 2.1 Literal Inline Geometry

The following geometry properties may appear in the same element's
`style="..."`. The pipeline materializes them as
XML geometry attributes before SVG post-processing and native PPTX conversion.
An inline geometry declaration overrides an existing same-name XML attribute.

| Element | Recognized properties |
|---|---|
| `<rect>` | `x`, `y`, `width`, `height`, `rx`, `ry` |
| `<circle>` | `cx`, `cy`, `r` |
| `<ellipse>` | `cx`, `cy`, `rx`, `ry` |
| `<image>` | `x`, `y`, `width`, `height` |
| `<svg>` | `x`, `y`, `width`, `height` |
| `<use>` | `x`, `y`, `width`, `height` |

**Hard rule — inline geometry grammar**: every non-zero value is one finite
`px` literal, such as `120px` or `-8.5px`; exact zero may be unitless. `width`,
`height`, `rx`, `ry`, and `r` must be non-negative. Percentages, `auto`,
`calc()`, `var()`, `!important`, `inherit`, and every other unit are forbidden.
Do not put geometry on an unsupported element: line endpoints, text positions,
path data, and polygon/polyline points remain XML attributes.

**Forbidden — CSS geometry cascade**: `<style>`, `class`, selector rules,
external stylesheets, and imported styles remain forbidden. This contract is
only for literal declarations in an element's own `style` attribute; PPT Master
does not compute CSS cascade or custom properties. Root canvas authority remains
the `viewBox`, regardless of root `<svg>` compatibility width/height values.

### 2.2 Group Opacity Is Approximate

`<g opacity="0.3">...</g>` maps the group alpha onto each descendant shape,
text run, picture, and supported
shadow/glow effect. Nested group and child opacity values multiply. Overlapping
children may differ from SVG isolated-group compositing because DrawingML has no
equivalent group-alpha model. With `--native-objects`, transparent native
table/chart markers are rejected; omit that flag to export their SVG fallback.

---

## 3. Canvas Format Quick Reference

> See [`canvas-formats.md`](canvas-formats.md) for the full format table (presentations / social / marketing) and the format-selection decision tree.

---

## 4. Required Page Contract and Conditional Packaging

### 4.0 Complete Page-Design Contract

| Concern | Requirement |
|---|---|
| Visible slide result | The completed `svg_output/<slide>.svg` MUST contain every visible text, image, shape, diagram, chart/table fallback, background, and template-derived layout element intended for that slide. External visual assets are valid when the SVG references them explicitly. |
| Template/control inputs | Templates, `design_spec.md`, and `spec_lock.md` guide authoring. Do not depend on them to add visible elements after the page SVG is complete. |
| PPTX translation | The exporter may map represented SVG content to DrawingML/native objects and deduplicate represented elements into Master/Layout/Slide parts. It MUST NOT invent visible slide content absent from the SVG. |
| Excluded package behavior | Speaker notes, animations, transitions, narration audio, PPTX relationships, and direct native-PPTX workflows remain separately owned. They are not part of the SVG page-design contract. |

**Hard rule — page-design closure**: A final page SVG is the sole visual/design authority for that page on every SVG-authoring route. SVG is not the authority for the entire PPTX package.

### 4.1 Semantic SVG Marker Contract

Semantic markers are minimal compiler hints orthogonal to native SVG semantics. Free-design and brand-only pages use flat export and omit Master/Layout/layer/placeholder markers. On deck/layout template routes, root Master/Layout identity, atomic layer elements, grouped slots, and native-object metadata are authoritative and read first; each page carries its final structured contract from the start of SVG authoring. Add `data-pptx-role` only when no specialized marker expresses the required page-frame behavior; the element also uses a stable unique `id`. Do not classify ordinary page content or move visible facts out of SVG attributes/text into metadata. See [`semantic-svg.md`](semantic-svg.md) for the canonical vocabulary and examples.

- **Canvas authority**: `viewBox` MUST match the selected canvas dimensions.
  Root `width` and `height` are optional and do not override it. Root `<svg>`
  `transform` is forbidden; apply transforms to child elements or groups.
- **Font portability**: font families used by the deck must resolve to installed
  export faces. `@font-face` remains forbidden; the typography contract lives in
  [`strategist.md §g`](strategist.md). On this install typography is locked to
  **Pretendard** (installed user-level; bundled at `assets/fonts/Pretendard/`);
  the converter registers it as a dual-script (Latin + EA) family.
- **Icon placeholders**: `<use data-icon="library/name">` is a pipeline-specific
  form, distinct from local SVG reuse. Follow the contract in
  [`../templates/icons/README.md`](../templates/icons/README.md).
- **Local reuse**: ordinary same-document `<use>` follows §1.3.

### 4.2 Conditional Editability and Package Promotion

These forms are needed only when the stated PPT behavior matters:

| Desired behavior | Required form |
|---|---|
| One editable PPT text frame with mixed inline formatting | Put the logical line in one `<text>` with non-positional `<tspan>` children. A `<tspan>` with `x`/`y`/`dy` starts a new positioned line. Evenly `dy`-stacked lines that repeat the parent `<text>`'s `x` stay in one frame: equal effective `font-size` may flow in the current paragraph, while a font-size change, list marker, or accepted larger gap starts a new paragraph. An unmergeable gap or mismatched `x` flattens to separate frames. Separate `<text>` elements stay valid when separate frames are intended. |
| Stable object grouping or object-level animation anchor | Wrap the intended object in `<g id="...">`. Content grouping is **mandatory** per §4.3 — a top-level `<g id>` is also the animation anchor; it is not an optional convenience. |
| Native PowerPoint background promotion | Use a direct, full-canvas, solid `<rect>` without transform, filter, clip, rounding, or visible stroke. Other SVG backgrounds remain ordinary slide shapes. Template routes add the ownership metadata per [`structured-templates.md`](./structured-templates.md). |
| Free-design / brand-only PowerPoint structure | Use `pptx_structure.mode: flat`. Keep every represented object Slide-local; export uses PowerPoint's default Master and Blank Layout. Do not author Master/Layout identities, layers, or placeholder slots. |
| Reusable template-based PowerPoint Layout | Select one complete input SVG per page in `page_layouts` and declare the output Master/Layout mapping at planning time. Strict preserves the prototype contract; adaptive retains its Master and may assign a new explicit Layout key during page authoring. Non-mirror skin follows `spec_lock`. |

**Hard rule — supported shape conversion**: Every PPT editability claim in this specification refers to the project converter reading `svg_output/` and emitting native DrawingML. `svg_final/` is a self-contained visual preview that may be inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is unsupported; do not narrow the authoring contract to its undocumented SVG subset.

### 4.3 Element Grouping (Mandatory)

Wrap logically related Slide-local elements in top-level `<g id="...">` groups. This is **required on every generated page**, not an optional convenience: it produces real PowerPoint groups in the exported PPTX and gives each content unit a stable animation anchor. Plain `<g>` is the normal grouping primitive; `<g opacity="0..1">` additionally maps to the per-descendant alpha approximation in §2.2. Flat free-design/brand-only pages use only ordinary semantic groups. On structured template pages, direct atomic Master/Layout elements are the required exception and a top-level slot `<g>` is already a semantic group.

**Semantic-group rule**: direct Slide content uses semantic groups. Aim for **3–8 ordinary top-level content `<g id>` groups per slide**; on structured template pages, slot groups and atomic Master/Layout objects are excluded. Each ordinary group becomes one entrance step under the chosen animation trigger. Leaving Slide-local titles, body lines, list items, cards, or decorative clusters as ungrouped top-level atoms is a contract violation.

**Structural atoms and slots are excluded automatically.** `data-pptx-layer` and `data-pptx-placeholder` semantics are read first; otherwise explicit `data-pptx-role` values (`background`, `decoration`, `header`, `footer`, `chrome`, `watermark`, `page-number`, `logo`) mark Slide-local static framing (§4.1, [`semantic-svg.md`](semantic-svg.md)). A normal slot group has exactly one direct compatible carrier; several drawing atoms require the explicit composite `object` proxy fallback. Native chart/table carrier groups retain their specialized marker contract ([`native-objects.md`](./native-objects.md) §3).

**What to group** (one `<g id>` per unit):

| Grouping unit | Contains |
|---|---|
| Card / panel | Background rect + optional shadow (only if it floats over a photo/colored panel, §6.4) + icon + title + body text |
| Process step | Number/marker + icon + label + description |
| List item | Bullet / number + icon + title + description |
| Icon-text combo | Icon element + adjacent label |
| Page header | Title + subtitle + accent decoration |
| Page footer | Page number + branding |
| Decorative cluster | Related decorative shapes (rings, dots, orbs) |

An authored native preset fragment (§1.5) is already an atomic `<g id>` and counts as one content group; keep its labels / decorations in a sibling parent `<g>`, never inside the preset group.

**Forbidden**:

- One giant `<g>` around the whole slide (collapses to a single animation step).
- Many ungrouped Slide-local `<rect>` / `<text>` / `<path>` atoms — fallback animation caps at 8 primitives, dense pages may skip animation, and selection/editing degrades.
- One group per icon / text line / mark (too many steps).
- Anonymous top-level groups — every top-level semantic group needs a descriptive `id`.

**Naming — required.** A descriptive `id` on every top-level content `<g>` (`card-1`, `step-discover`, `header`, `footer`) is mandatory; it is the animation anchor and the group identity in PPTX. Without it, the exporter falls back to at most 8 top-level primitives or skips animation on dense pages.

```xml
<g id="card-benefits-1">
  <!-- Shadow only if the card floats over a colored panel; on flat white, omit it. -->
  <rect x="60" y="115" width="565" height="260" rx="20" fill="#FFFFFF" filter="url(#shadow)"/>
  <use data-icon="chunk-filled/bolt" x="108" y="163" width="44" height="44" fill="#0071E3"/>
  <text x="105" y="270" font-size="56" font-weight="bold" fill="#0071E3">10×</text>
  <text x="250" y="270" font-size="30" font-weight="bold" fill="#1D1D1F">Faster</text>
  <text x="105" y="310" font-size="18" fill="#6E6E73">Reduce production time from days to hours.</text>
</g>
```

---

## 5. Workflow Authority

The serial post-processing and export workflow belongs to
[`SKILL.md` Step 7](../SKILL.md). This file defines SVG authoring boundaries
and intentionally does not mirror commands, flags, or output behavior.

---

## 6. Advanced SVG Effects and Authoring Techniques

**Reference — not a constraint**: “Advanced” means capability depth, not rarity.
Use any compatible technique when it serves the locked visual style and content.

### 6.1 Availability, Precedence, and Fidelity

| Decision layer | Authority |
|---|---|
| Technical validity | Required / Forbidden / Conditional contracts in this file |
| Project values | `<project_path>/spec_lock.md` colors, fonts, icons, and images |
| Aesthetic fit | Locked `visual_style` / `visual_style_behavior` |
| Per-page choice | Content purpose, hierarchy, legibility, semantics, and rhythm |

**Hard rule — illustrative colors**: colors below demonstrate syntax only;
generated pages use matching `spec_lock.md` roles. Fidelity labels are defined
at the front of this document. Review an `Approximate` result in native PPTX
when the effect carries material meaning.

---

### 6.2 Color, Alpha, and Opacity

Supported paint grammar: recognized named colors, `rgb()` / `rgba()`, `hsl()` /
`hsla()`, and `#RGB` / `#RGBA` / `#RRGGBB` / `#RRGGBBAA`. Bare hexadecimal
without `#` is invalid.

| Authoring surface | Native result | Fidelity |
|---|---|---|
| `fill-opacity`; `stroke-opacity` | Fill, text, line, or outline alpha | `Native-stable` |
| CSS color alpha | Alpha-bearing named/functional/HEX paint | `Native-normalized` |
| Element `opacity` | Alpha compiled into supported paint/effect channels | `Native-normalized` |
| `<image opacity>` | Picture `<a:alphaModFix>` | `Native-stable` |
| `<stop stop-opacity>` | Per-stop gradient alpha | `Native-stable` |
| `<g opacity>` | Alpha multiplied into each supported descendant shape, text run, picture, and effect | `Approximate` |
| Pattern child/color alpha | Preset-pattern foreground/background alpha | Conditional; §7 |

```text
effective fill alpha
= color alpha × element opacity × fill-opacity × ancestor group opacity
```

**Hard rule — alpha grammar**: write `opacity`, `fill-opacity`,
`stroke-opacity`, and `stop-opacity` as finite numbers from `0` to `1`.
`fill="transparent"` / `stroke="transparent"` become no fill/line; use a color
plus alpha when a painted transparent layer must remain represented. Group
alpha is not isolated compositing, so overlapping descendants may differ from
the browser. Transparent groups around `data-pptx-native` chart/table markers
cannot be promoted under `--native-objects`; export the SVG fallback or remove
the group opacity.

---

### 6.3 Gradients and Paint Effects

| Concern | Contract |
|---|---|
| Definition | Direct `<linearGradient>` / `<radialGradient>` child of `<defs>` with unique `id` |
| Reference | Exact local `url(#id)` |
| Stops | Direct `<stop>` children; explicit color; finite offset `0..1` or `0%..100%`; optional stop alpha |
| Coordinates | Normalized values / percentages; do not depend on `gradientUnits` user-space geometry |
| Forbidden | External/quoted refs, `href` inheritance, `gradientTransform`, `spreadMethod`, CSS gradients |

| Target | Contract and fidelity |
|---|---|
| `<rect>`, `<circle>`, `<ellipse>`, `<path>`, `<polygon>` fill/stroke | Linear `Native-normalized`; radial `Approximate` |
| `<line>` / `<polyline>` | Gradient stroke only; linear `Native-normalized`, radial `Approximate` |
| `<text>` / non-positional `<tspan>` | Gradient fill only; no gradient text outline |
| `<image>` | No gradient paint; use §6.5 overlays |

Linear export preserves stops/alpha/direction but reduces coordinates to an
angle. Radial export becomes a centered circular gradient and does not preserve
`cx/cy/r/fx/fy`. Gradient strokes remain editable, but PPTX-to-SVG re-import may
retain only the first stop. Stop alpha and element opacity multiply.
The quality checker validates definition location, references, and paint context.

```xml
<defs>
  <linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#2563EB"/>
    <stop offset="100%" stop-color="#10B981" stop-opacity="0.7"/>
  </linearGradient>
</defs>
<path d="M100 200 C260 80 420 320 620 180" fill="none"
      stroke="url(#flow)" stroke-width="12"/>
```

Preset patterns are a separate PPT interface in §7.

---

### 6.4 Shadows, Glow, and Elevation

Filters are native-effect metadata, not a general pixel-filter surface.

| Concern | Contract |
|---|---|
| Definition/reference | Direct `<defs><filter id="...">` child with unique id; direct `filter="url(#id)"` attribute, never inline style |
| Public targets | `<rect>`, `<circle>`, `<path>`, `<text>` |
| Required primitive | `feDropShadow` or `feGaussianBlur` |
| Accepted helpers | `feOffset`, `feFlood`, `feComposite`, `feMerge`, `feMergeNode`, `feComponentTransfer`, linear `feFuncA` |
| Classification | Meaningful non-zero offset → one outer shadow; zero/no offset → one glow |
| Fidelity | `Approximate`; one filter becomes one DrawingML effect |

Flood/color alpha, linear `feFuncA slope`, element opacity, and ancestor opacity
multiply. Native export does not preserve filter-region, `in/in2/result`, merge
order, or composite topology. Other primitives, multiple independent effects,
filters on `<image>` / `<tspan>` / unsupported targets are forbidden. Do not
put a filter on a multi-element `<g>`; apply it to supported objects or use
explicit layers.

```xml
<defs>
  <filter id="softShadow" x="-15%" y="-20%" width="130%" height="150%">
    <feDropShadow dx="0" dy="6" stdDeviation="8"
                  flood-color="#000000" flood-opacity="0.10"/>
  </filter>
  <filter id="expandedShadow" x="-15%" y="-20%" width="130%" height="150%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="8" result="b"/>
    <feOffset in="b" dx="0" dy="6" result="o"/>
    <feFlood flood-color="#000000" flood-opacity="0.10" result="c"/>
    <feComposite in="c" in2="o" operator="in" result="s"/>
    <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="titleGlow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="b"/>
    <feFlood flood-color="#38BDF8" flood-opacity="0.45" result="c"/>
    <feComposite in="c" in2="b" operator="in" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
```

Even `feDropShadow` with `dx="0" dy="0"` becomes glow. Use an existing accent
color for glow; black reads as diffuse shadow.

| Elevation | Use | `dy` | `stdDeviation` | Alpha |
|---|---|---:|---:|---:|
| Floor | Backgrounds, dividers, equal peers, body containers, decorative lines/icons, single-layer pages | — | — | — |
| Resting | Card over photo/panel, secondary callout | 2–4 | 4–8 | 0.06–0.10 |
| Raised | Primary CTA, focused card, overlay | 6–10 | 10–16 | 0.12–0.20 |
| Glow | Short display text, metric, focus accent | 0 offset | 4–8 | 0.35–0.55 |

**Strong default — single light source per page**: every `feOffset` shadow on
one slide shares the same `dx`/`dy` direction (default `dx="0"`, `dy="4"`–`dy="8"`,
light from upper front). Contradictory shadow directions read as multiple light
sources — a clear low-quality tell. The one sanctioned exception is a deliberate
upward paper-layer light, where every affected layer flips direction together;
never mix directions on the same plane. This is a strong default, not a
checker-enforced hard rule.

**Reference — not a constraint**: keep at most two
non-floor tiers; two or three shadowed objects usually suffice. Do not lift
every peer card or stack strong shadow, border, gradient, and tint on one
container. Same-family colored shadow is reserved for a focal accent. On dark
backgrounds, prefer a light hairline or restrained glow; never glow body copy.
Negative `dy` is valid for an intentional upward paper-layer light source when
every affected layer uses the same direction. For older/strict renderers,
replace a filter with two or three offset translucent shapes behind the object:
alpha `0.03–0.05`, increasing offset/radius, and optional same-family tint near
`0.04` (`Native-stable`).

---

### 6.5 Image Treatments, Overlays, and Glass-like Surfaces

| Need | Authoring contract | Fidelity |
|---|---|---|
| Cover/crop | Readable raster dimensions + aligned `slice` | Native `srcRect`; `Native-stable`; otherwise native crop cannot be guaranteed |
| Contain/fit | Aligned `meet` | Fitted picture frame; `Native-normalized` |
| Stretch | `preserveAspectRatio="none"` | Native stretched frame |
| Uniform fade | `<image opacity="...">` | Native picture alpha |
| Shaped picture | §1.2 image-only `clip-path` | Preset/custom picture geometry |

**Hard rule — fit/clip interaction**: a non-trivial clip disables `meet`
frame-fit. Match the image box to the source ratio or use `slice`. Do not apply
filters directly to `<image>`.

| Overlay | Construction | Typical stops / alpha |
|---|---|---|
| Directional scrim | Linear rect, darkest beside text | `0%: 0.88; 55%: 0.30; 100%: 0` |
| Bottom title fade | Vertical rect over lower image | black `0 → 0.72` |
| Vignette/spotlight | Centered radial rect (`cx=50%`, `cy=50%`, `r=70%`); native center only | black `0 → 0.58` |
| Brand wash | Directional existing brand-color gradient | `0.80 → 0.10` |
| Faux glass | Visible fields + diagonal linear panel (`0,0 → 1,1`) + highlight stroke; optional §6.4 elevation | white `0.38 → 0.12`; stroke about `0.55` |

Layer in document order: image → scrim/wash → text. True source/backdrop blur is
`Bake-required`; faux glass is explicit layering, not blur. Validate contrast
against the actual image. All overlay gradients follow §6.3 linear/radial
fidelity.

---

### 6.6 Lines, Connectors, Borders, and Markers

| Surface | Contract / native result |
|---|---|
| Solid stroke/width/alpha | `Native-stable` editable line |
| `4,4`; `2,2`; `8,4`; `8,4,2,4` | `dash`; `sysDot`; `lgDash`; `lgDashDot` (`Native-normalized`) |
| Other custom dash | Exactly two positive finite unitless numbers (`dash gap`); export scales/quantizes against stroke width; longer arrays reduce to the first pair; `Native-normalized` |
| `stroke-linecap` | `butt`, `round`, `square`; `Native-stable` |
| `stroke-linejoin` | `miter`, `round`, `bevel`; `Native-stable` |
| Gradient stroke | §6.3; re-import may flatten to first stop |
| `marker-start` / `marker-end` | §1.1 native line end; type `Native-normalized`, size `Approximate` (`sm/med/lg`) |

Match marker fill to the parent stroke. Use markers for connectors and §6.10
calculated geometry for a manual diagonal arrowhead. When exact grid spacing
matters, use one multi-subpath path rather than a fixed-density preset pattern:

```xml
<path d="M40 0V120 M80 0V120 M0 40H120 M0 80H120"
      fill="none" stroke="#2E6EA8" stroke-width="0.8"/>
```

---

### 6.7 Advanced Text Treatments

| Treatment | SVG surface | Result / boundary |
|---|---|---|
| Underline / strike / both | `text-decoration="underline"`, `line-through`, or both | `Native-stable`; both emits both run properties |
| Mixed runs | Non-positional `<tspan>` | One `Native-normalized` editable frame; §4.2 |
| Tracking | Numeric `letter-spacing` | `Native-normalized`; unitless/`px` = SVG px, `pt` converts to px, `em` resolves against run size |
| Transparency | `opacity` / `fill-opacity` on text/run | `Native-normalized` run alpha, not isolated compositing |
| Gradient fill | §6.3 gradient on text/run | Editable fill; geometry normalizes |
| Outline | Solid `stroke`, `stroke-width`, `stroke-opacity` | `Native-normalized` editable run outline; re-import does not reconstruct it |
| Shadow/glow | §6.4 filter on `<text>` only | Shape shadow / run glow; `Approximate` |
| Native bullet | Leading `· • ● ▪ ■ ◆ ◇ ◦ ‣` + non-empty content | `·`/`•` → `•`; others unchanged; color/alpha from marker run; font/size follow text |

```xml
<text x="100" y="200" font-size="20" xml:space="preserve">Current <tspan
  fill="#999999" text-decoration="line-through">old</tspan> value</text>
```

Use strikethrough for removed/former values; it is ordinary notation, not a
style-exclusive effect. Imported double underline/strike normalizes to single.
Bullet detection allows optional leading whitespace, requires non-empty content,
and leaves non-leading decorative glyphs as ordinary text.
Keep body tracking normal; CJK tracking defaults near/below 2% of font size and
above 5% triggers review. Text outline is solid only. `textPath`, masks, blend
modes, generated effects, and text-image knockouts are outside editable text.

---

### 6.8 Transforms, Layering, and Static Reuse

| Surface | Contract / fidelity |
|---|---|
| `rotate(angle[, cx, cy])` | Geometry/image/text/ordinary group; `Native-normalized` |
| `translate(x y)` | Geometry/image/group; pure translation also safe on text; `Native-normalized` |
| Positive scale / negative mirror | Geometry/image only; explicit pivot; `Native-normalized` |
| `matrix(a b c d e f)` | Geometry/image only; transformed axes finite, non-zero, orthogonal; excludes rounded rects; `Native-normalized` |
| Source order | Back-to-front PPT z-order; `Native-stable` |
| `<g opacity>` | Descendant alpha; `Approximate`, §2.2 |
| Local `<use>` | §1.3 compile-time reuse; `Native-normalized` |

Set text size/position directly; do not scale or general-matrix text. `skewX`,
`skewY`, zero/non-orthogonal axes, and shear matrices are forbidden. Native
chart/table markers allow translate/scale only. The §6.10 thick-circle shortcut
does not inherit general transform support. Positive rotation is clockwise and
pivoted rotation normalizes the native frame. A legal transform sequence can
still produce non-orthogonal axes; importer/live-editor matrices do not expand
the hand-authored contract.
Mirror around vertical pivot `cx` with
`translate(cx 0) scale(-1 1) translate(-cx 0)`; use the analogous Y sequence
for a horizontal pivot.

Layer back-to-front: background/image → scrim/shadow → main geometry → labels /
icons → top annotation. Finalization and native export independently expand
`<use>` into cloned editable primitives; PowerPoint does not retain a symbol /
instance graph.

---

### 6.9 Freeform Shapes and Curves

| Input | Native normalization | Fidelity |
|---|---|---|
| `M/L/H/V`, absolute or relative | Absolute `M/L` | `Native-normalized` |
| `C` | Cubic Bézier | `Native-normalized` |
| `S/Q/T` | Explicit cubic controls | `Native-normalized` |
| `A` | Cubic segments of at most 90° | `Approximate` |
| `Z`; polygon/polyline | Closed/open freeform | `Native-normalized` |

Command identity, relative coordinates, shorthand, arc parameters, and original
handles are not retained. Geometry needs non-zero bounds. Use a closed cubic
path for organic silhouettes, polygon/closed path for ribbons/facets, open path
for curved connectors, multi-`M` path for exact linework, and a §1.2 path clip
for organic pictures. Filled silhouettes end with `Z`; open paths use
`fill="none"`. Do not depend on `fill-rule="evenodd"`; build explicit visible
geometry or bake an essential knockout.
For a fixed background, a background-colored overlay is also valid.

| Rounded rect input | Result |
|---|---|
| One positive radius, or `0 < rx == ry <= min(width,height)/2` | `Native-stable` adjustable `roundRect` without distorting transforms; the same short-side limit applies to one-radius input |
| `0 < abs(rx-ry) < 0.5px` after scaling | One normalized native radius; `Approximate` |
| `abs(rx-ry) >= 0.5px`, either positive | Cubic custom geometry; no radius handle; `Approximate` |
| Equal radius above half the short side | Native short-side clamp may differ from SVG; `Approximate` |

---

### 6.10 Radial Geometry, Donuts, Gauges, Sunbursts, and Diagonal Arrowheads

For center `(cx,cy)`, radius `r`, and degrees `θ`:

```text
x = cx + r × cos(θ × π / 180)
y = cy + r × sin(θ × π / 180)
```

For clockwise pie/donut sectors, default to `-90°` only when the chart starts at
12 o'clock. A full-circle percentage sector spans `percentage × 360°`;
large-arc is `1` above `180°`; outer sweep is `1`, inner return is `0`. Split
both outer and inner boundaries of a full ring into at least two arcs each.
Calculated endpoints survive subject to EMU rounding; `A` curves remain cubic
approximations. Verify all spans plus gaps against the planned sweep.
Explicit arc sectors are editable `Approximate` freeforms. Thin circles using a
§6.6 preset/two-number dash stay `Native-normalized` ellipse lines.

```xml
<!-- 75% donut: center 400,400; outer 180; inner 100; -90° → 180°. -->
<path d="M400 220 A180 180 0 1 1 220 400
         L300 400 A100 100 0 1 0 400 300 Z" fill="#2563EB"/>
```

**Gauge**: require `max > min`, `p = clamp((value-min)/(max-min),0,1)`, and
`0 < planned clockwise sweep <= 360°`; value sweep is `p × planned sweep`.
`valueEndAngle = startAngle + valueSweep`; large-arc is `1` iff
`abs(valueSweep) > 180°`.
Omit the value sector at `p=0`. At `p=1` with `360°`, split both boundaries into
at least two arcs. Track/value share center, radii, start, and sweep flags.

**Sunburst — `Approximate`**: one explicit annular sector per node; each depth owns one radius
band and child angular intervals partition the parent. Do not use one `evenodd`
compound ring.

**Thick-circle shorthand — `Approximate`, non-position-sensitive only**:

- One circle per segment; `fill="none"`; no element transform or ancestor full-matrix.
- Exactly two non-preset finite unitless values (`dash gap`); finite unitless `stroke-dashoffset`.
- `0 < stroke-width < 2r`, `stroke-width/r >= 0.15`,
  `0 < dash < 2πr`, `gap >= 0`, and `dash + gap >= 2πr`.
- Native construction uses only the first dash and re-imports as a freeform.
  Its native start is 90° counterclockwise from the SVG preview; use explicit
  arcs whenever start angle, cap, or radial precision matters.

```xml
<circle cx="400" cy="400" r="140" fill="none" stroke="#2563EB"
        stroke-width="48" stroke-dasharray="615.75 263.90" stroke-dashoffset="0"/>
```

**Diagonal polygon arrowhead**: for a non-zero line, calculate rather than use a
fixed triangle:

```text
dx=x2-x1; dy=y2-y1; len=√(dx²+dy²); ux=dx/len; uy=dy/len
px=-uy; py=ux
tip=(x2,y2)
back1=(x2-ux×12+px×5, y2-uy×12+py×5)
back2=(x2-ux×12-px×5, y2-uy×12-py×5)
```

Use §1.1 markers for ordinary connectors; the polygon is for a manually drawn
filled `Native-normalized` arrowhead. Example:
`<polygon points="370,430 365.6,417.8 358.2,424.6"/>`.

---

### 6.11 Constructed Visual Styles

**Hard rule — explicit construction**: these are supported-layer recipes, not
browser-filter permissions.

**Reference — not a constraint**: use them only when they match the locked style.

| Intent | Construction | Boundary / fidelity |
|---|---|---|
| Faux glass | §6.5 translucent panel + highlight stroke + visible fields | No backdrop blur; `Native-normalized` |
| Hand-drawn mark | Rotated translucent bar + irregular `Q/C` paths + round caps | No roughness filter; `Native-normalized` |
| Ink wash | Few same-family translucent closed curves/strokes | No feather/wet edge; `Native-normalized` |
| Riso offset | Duplicate text/shape with small offset, second ink, lower alpha | No blend mode; `Native-normalized` |
| Pixel grid | Integer-aligned rects on one cell grid | `shape-rendering` preview-only; `Native-stable` |
| Halftone | Sparse calculated circles | `Native-stable`; bake dense screens / use suitable §7 preset |
| Isometric facets | Shared-vertex top/front/side polygons, one light direction | 2D only; `Native-normalized` |
| Paper cut | Ordered organic paths + consistent §6.4 shadow per layer | Filter each layer, not group; `Approximate` |
| Gradient ribbon | Thick cubic path + §6.3 gradient stroke | `Native-normalized`; no mesh gradient; re-import may flatten color |
| Line-plus-area data | Low-alpha closed area first, crisp line above | Keep area subordinate; `Native-normalized` |

**Minimal construction anchors**:

```xml
<!-- Hand-drawn + ink. -->
<rect x="80" y="80" width="240" height="28" fill="#FDE68A"
      opacity="0.72" transform="rotate(-1,200,94)"/>
<path d="M90 150 Q210 142 330 151" fill="none" stroke="#1F2937"
      stroke-width="3" stroke-linecap="round"/>
<path d="M80 220 C160 160 250 180 330 230 Z" fill="#1F2937" opacity="0.16"/>
<path d="M90 240 C180 210 250 260 340 220" fill="none" stroke="#1F2937"
      stroke-width="10" stroke-linecap="round" opacity="0.70"/>

<!-- Riso, pixel cells, sparse dots. -->
<text x="86" y="320" font-family="Arial, sans-serif" font-size="64"
      fill="#EC4899" opacity="0.85">PRINT</text>
<text x="92" y="326" font-family="Arial, sans-serif" font-size="64"
      fill="#2563EB">PRINT</text>
<g id="pixel-cells" shape-rendering="crispEdges" fill="#2563EB">
  <rect x="400" y="80" width="16" height="16"/><rect x="416" y="80" width="16" height="16"/>
</g>
<g id="sparse-dots" fill="#EC4899"><circle cx="410" cy="140" r="3"/><circle cx="426" cy="140" r="6"/></g>

<!-- Isometric facets + line-over-area. -->
<g id="isometric-facets" transform="translate(520 160)">
  <polygon points="0,0 80,-24 160,0 80,24" fill="#60A5FA"/>
  <polygon points="0,0 0,48 80,72 80,24" fill="#3B82F6"/>
  <polygon points="80,24 80,72 160,48 160,0" fill="#2563EB"/>
</g>
<path d="M760 260 L860 220 L960 250 L960 340 L760 340 Z" fill="#2563EB" opacity="0.10"/>
<path d="M760 260 L860 220 L960 250" fill="none" stroke="#2563EB" stroke-width="4"/>
```

**Default — integer pixel grid (may override for deliberate irregular
treatment)**: avoid soft scaling; use explicit dots only for sparse editable
halftone and route dense full-slide texture to §6.12.

---

### 6.12 Unsupported Effects and Native-Safe Alternatives

| Unsupported intent | Do not author | Fidelity | Alternative |
|---|---|---|---|
| Source/backdrop blur; procedural texture | Plain blur, `feTurbulence`, `feDisplacementMap`, `feColorMatrix`, arbitrary filter graph | `Bake-required` | §6.4 effect, explicit geometry, translucent layers, or baked texture |
| Inner shadow, soft edge, reflection | Non-outer-shadow/glow graph | `Bake-required` | Explicit inset/highlight/shadow layers or image |
| Per-pixel compositing | Mask, blend mode, knockout, arbitrary alpha composite | `Bake-required` | Direct geometry; §1.2 image clip; otherwise bake |
| Exact custom tile | Unannotated `<pattern>` / `patternTransform` | `Bake-required` | Multi-subpath geometry, suitable §7 preset, or bake |
| Sheared object | Skew/shear matrix | `Bake-required` | Pre-transform geometry path; bake text/image |

**Hard rule — blur semantics**: within §6.4, zero-offset `feGaussianBlur` means
glow; it does not blur the object or backdrop. Use a low-alpha raster for dense
grain and explicit circles/paths only for sparse editable marks.

---

### 6.13 Scenario Quick Reference

**Reference — not a constraint**: fidelity remains authoritative in the owning
subsection; this table only routes scenarios.

| Decision family | Scenario routing | Authority / boundary |
|---|---|---|
| Elevation | Floating card → resting shadow; one CTA → colored shadow; equal peers/background → flat; maximum predictability → layered shapes; title/metric → glow | §6.4; never body-copy glow |
| Image/material | Text over image → directional scrim; bottom title → bottom fade; centered hero → vignette; brand wash → brand overlay; glass card → faux glass | §6.5; no backdrop blur |
| Lines | Draft/optional → dash; process direction → marker; flow/series → gradient stroke; exact grid → multi-subpath path | §6.6 / §6.3 |
| Text | Removed/former value → line-through; eyebrow → tracking; watermark/outline heading → text outline; list → native bullet | §6.7 |
| Composition | Move/rotate/mirror → §6.8 transform; repeated static mark → local `<use>` | §6.8; preserve z-order |
| Hand/print | Annotation → highlighter/curve; ink wash → layered alpha paths; Riso → offset duplicate | §6.11; no turbulence, true bleed, or blend mode |
| Pixel/halftone | Pixel accent → integer rect grid; sparse screen → circles | §6.11; dense screen → §6.12 |
| Faceted/layered | Pseudo-3D → 2D facets; paper cut → direct shadow per layer | §6.11; no 3D transform/group composite shadow |
| Data/freeform | Series depth → area first + line above; organic card → closed cubic; shaped image → §1.2 path clip | §6.11 / §6.9 |
| Radial | Donut/gauge → explicit arcs; sunburst → sector per node; position-insensitive ring → shorthand | §6.10; shorthand has 90° preview/native offset |
| Arrow | Manual diagonal arrowhead → calculated triangle; ordinary connector → marker | §6.10 / §1.1 |
| Unsupported | Dense grain, complex composite, or skew → explicit alternative or baked asset | §6.12; foreground text/data stay editable SVG |

---
## 7. Conditional PPT Interfaces

The interfaces below exist only for PPT behavior that ordinary SVG semantics
cannot express. Use them only when the corresponding native capability is
required.

### Pattern Fill — `<pattern>` with PPTX preset annotation

`<pattern>` requests one fixed DrawingML preset; the converter does not render
the tile's arbitrary geometry. Use this interface only when that preset mapping
is intended.

`data-pptx-pattern="<preset>"` is required to select the intended preset from
the enum below; without it, export falls back to `ltUpDiag`.

Pattern colors may come from importer metadata (`data-pptx-fg` /
`data-pptx-bg`) or from the pattern's child paint. Without metadata, the first
child `<rect>` fill becomes the background and the first stroke (or other fill)
becomes the foreground. A missing background defaults to white; a missing
foreground means no native pattern fill can be emitted. The child geometry
itself is never used as a repeatable tile.

**Valid `data-pptx-pattern` values** (OOXML `ST_PresetPatternVal` — closed enum, anything outside makes PowerPoint open with "needs to be repaired"):

| Category | Values |
|---|---|
| Grids | `smGrid` · `lgGrid` · `dotGrid` *(no `ltGrid` — common typo)* |
| Diagonal lines | `ltUpDiag` · `ltDnDiag` · `dkUpDiag` · `dkDnDiag` · `wdUpDiag` · `wdDnDiag` · `dashUpDiag` · `dashDnDiag` · `diagCross` |
| Horizontal / vertical lines | `horz` · `vert` · `ltHorz` · `ltVert` · `dkHorz` · `dkVert` · `narHorz` · `narVert` · `dashHorz` · `dashVert` · `cross` |
| Percent fills | `pct5` · `pct10` · `pct20` · `pct25` · `pct30` · `pct40` · `pct50` · `pct60` · `pct70` · `pct75` · `pct80` · `pct90` |
| Checks & confetti | `smCheck` · `lgCheck` · `smConfetti` · `lgConfetti` |
| Decorative | `horzBrick` · `diagBrick` · `weave` · `plaid` · `trellis` · `zigZag` · `wave` · `sphere` · `divot` · `shingle` · `solidDmnd` · `openDmnd` · `dotDmnd` |

`svg_quality_checker.py` warns when the annotation is missing and errors when
the preset is outside this enum.

### Native PPTX Table / Chart Markers (Opt-in)

Moved to [`native-objects.md`](./native-objects.md) §3 — marker structure, JSON schemas, bounds, chrome, supported chart types, and the import boundary. Executor transcribes these markers at draw time on eligible pages ([`executor-base.md`](./executor-base.md) §3.2); SKILL.md Step 6 loads `native-objects.md` whenever the deck plans data-chart or text-grid table pages.

---

### PPTX Structure Routing, Master / Layout / Placeholder Metadata, and Legacy Migration

Moved to [`structured-templates.md`](./structured-templates.md) §§1–3. Applies only to structured deck/layout template routes and structure-restoration workflows; SKILL.md Step 6 loads that file when `spec_lock.md` declares `pptx_structure.mode: structured`. Flat free-design and brand-only routes keep `mode: flat`, omit `pptx_masters` / `pptx_layouts` / `page_layouts`, author no Master/Layout/layer/placeholder metadata, and export Slide-local under PowerPoint's default Master and Blank Layout (§4.2).

---

## 8. Scope Boundary

Project structure, commands, quality-gate order, and export products are owned
by [`SKILL.md`](../SKILL.md). They are intentionally outside this SVG
authoring policy.
