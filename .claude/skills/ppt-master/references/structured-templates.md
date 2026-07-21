> See [`shared-standards.md`](./shared-standards.md) §4 for the always-loaded page contract and [`executor-base.md`](./executor-base.md) for the common Executor guidelines. This file owns the structured deck/layout template route contracts that load conditionally.

# Structured Template Route Standards

Contracts for decks that export real PowerPoint Master / Layout / placeholder structure. Flat free-design and brand-only routes never author this metadata and do not load this file.

**Trigger**: load during SKILL.md Step 6 when `spec_lock.md` declares `pptx_structure.mode: structured` (deck/layout template route), or the chosen template's `design_spec.md` frontmatter declares `replication_mode: mirror`.

| Section | Owns |
|---|---|
| §1 PPTX Structure Routing | Route declaration, no-inference rules, Layout reuse and adaptive change |
| §2 Explicit Master / Layout / Placeholder Metadata | Root identity, layers, slots, text-style contracts, read-back gate |
| §3 Legacy Structure Migration Boundary | When `restore-pptx-structure` must run first |
| §4 Mirror-mode Templates | Reference-style page consumption |
| §5 Master / Layout Mapping | Structured authoring rules for the Executor |
| §6 Structured Per-page Lookup and Scaffold | Per-page row resolution and the root SVG scaffold |

---

## 1. PPTX Structure Routing

Every new SVG project declares one deterministic route. Free-design and brand-only projects use `pptx_structure.mode: flat`, omit `pptx_masters` / `pptx_layouts` / `page_layouts`, and author no Master/Layout/layer/placeholder metadata. Export uses PowerPoint's default Master and Blank Layout and keeps all represented content Slide-local. Deck/layout template projects use `mode: structured`; `standard` / `fidelity` templates use their authored contract, while mirror templates use restored source identities and parentage.

**Hard rule — no structure inference**: Flat export performs no promotion or deduplication; every object stays Slide-local. Structured template export compiles only declared root identities, atomic fixed layers, and slot groups—it does not assign Layout families, cluster pages, infer placeholders, or repair missing metadata. Legacy structured/template projects must run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) first.

**Layout reuse**: Reuse one Layout key only when its ordered fixed Layout atoms and slot ids/types/effective indices/default bounds/binding modes are identical. Different wording, data, imagery, crop, or Slide-local carrier geometry does not create a new Layout. A genuinely different reusable contract gets a new key even when both pages are semantically `content`.

**Zero-slot Layout**: A named Layout may contain no slots and no fixed Layout atoms. This is valid for a cover, poster, full-visual page, or other fixed composition. Do not manufacture an empty `utility` kind or full-page fake `object` slot.

**Adaptive change**: Template `strict` preserves the selected prototype contract. `adaptive` retains the prototype Master and may create a new Layout identity only when fixed Layout atoms or slot topology/bounds change. Update the page mapping immediately while authoring the first such page; never mutate a reused key silently.

## 2. Explicit PPTX Master / Layout / Placeholder Metadata

**Trigger**: This explicit metadata interface applies only to deck/layout template projects and structure-restoration workflows. `spec_lock.md` declares `pptx_structure.mode: structured`, a complete `pptx_masters` roster, one `pptx_layouts` row per page, and `page_layouts` as input-prototype provenance. Flat free-design/brand-only SVGs use none of these metadata fields.

**Project lock**: A Master row is `<master_key>: <PowerPoint picker name>`. A page row is `P<NN>: <master_key> | <layout_key> | <PowerPoint layout name>`. The SVG root values MUST match those rows. A Layout key belongs to exactly one Master and must be globally unique. Reuse one key only when pages share identical ordered Layout atoms and slot ids/types/effective indices/default bounds/binding modes. Every structured route requires numeric `spec_lock.md` typography `title` / `body` rows.

**Template behavior**: Strict preserves the selected prototype's declared Master/Layout/slot contract. Adaptive retains its Master and may allocate a new Layout key/name only when fixed Layout atoms or slot topology/bounds change; update the lock during authoring. Mirror-created prototypes preserve restored source identity, literal paint, typography, effects, atomic geometry, and referenced assets. `standard` / `fidelity` never make source topology authoritative; mirror does not synthesize a replacement topology.

**Master text-style contract**: Structured export maps the
locked `title` size to every `a:defRPr` in Master `p:titleStyle`, and map the
locked `body` size to every level in both `p:bodyStyle` and `p:otherStyle`.

| Master style | Locked source | XML field changed |
|---|---|---|
| `p:titleStyle` | `typography.title` | Every `a:defRPr@sz` |
| `p:bodyStyle` | `typography.body` | Every `a:defRPr@sz` |
| `p:otherStyle` | `typography.body` | Every `a:defRPr@sz` |

**Hard rule — narrow scope**: This Master update changes only Master
`p:txStyles//a:defRPr@sz`. It does not rewrite direct run sizes on generated
slides, so the initial slide rendering remains controlled by the authored SVG.
Missing `title` or `body` rows fail structured export.

**Layout level-one text-default contract**: For every text-bearing placeholder
whose first prototype run has a direct `a:rPr@sz`, explicit Layout export copies that
size to the generated Layout prompt run and
`p:txBody/a:lstStyle/a:lvl1pPr/a:defRPr@sz`. It does not rewrite Slide direct
runs or Layout levels 2–9. This preserves the layout-specific size when
level-one placeholder text is inserted or reset; placeholders without a direct
prototype size remain unchanged.

| Metadata | Placement | Behavior |
|---|---|---|
| `data-pptx-master="master-default"` | root `<svg>` | Binds the slide to one generated Slide Master key |
| `data-pptx-master-name="Default Master"` | root `<svg>` | Sets the Master picker/display name |
| `data-pptx-layout="content"` | root `<svg>` | Binds the slide to one generated reusable layout key |
| `data-pptx-layout-name="Title and Content"` | root `<svg>` | Sets the PowerPoint layout-picker name; defaults from the layout key |
| `data-pptx-layer="master"` | direct atomic visual child | Moves one repeated static object/background into the named Slide Master; `<g>` is forbidden |
| `data-pptx-layer="layout"` | direct atomic visual child | Moves one repeated static object/background into the selected Layout; `<g>` is forbidden |
| `data-pptx-layer="slide"` | direct full-canvas solid `<rect>` only | Writes a one-page override as Slide `p:bg` |
| `data-pptx-placeholder="..."` | direct slot `<g id>` | Declares a reusable Layout slot whose visible content remains Slide-local |
| `data-pptx-placeholder-bounds="x y width height"` | slot `<g>` | Supplies the positive reusable design-zone frame in SVG user units |
| `data-pptx-placeholder-idx="1"` | slot `<g>` | Retains an imported source Layout placeholder index; optional for reconstructed layouts |
| `data-pptx-placeholder-carrier="true"` | one compatible direct child of a normal slot | Binds that visible child as the real Slide placeholder carrier |
| `data-pptx-placeholder-binding="proxy"` | composite `object` slot `<g>` only | Keeps the visible group ordinary and creates one hidden transparent binding proxy |
| `data-pptx-editable="false"` | master/layout element or slide background | Declares intentional editing outside ordinary slide content |

**Hard rule — explicit only**: On a structured deck/layout template route, every SVG requires the four root Master/Layout identity attributes. Every Master/Layout atom and slot requires a unique stable `id` and is a direct root child. Layouts with zero slots are valid. `data-pptx-layout-kind`, `distilled`, and `utility` are legacy metadata and fail the structured contract. Flat free-design/brand-only pages omit the entire interface.

**Layer order**: Author the SVG in PowerPoint paint order: Master background,
Layout background, optional Slide background, remaining Master atoms, remaining Layout atoms,
then slot groups and Slide-local content groups. Backgrounds are a special inheritance
plane beneath every shape; this order keeps standalone SVG preview and
PowerPoint rendering aligned. The exporter rejects interleaved layers.

**Solid background ownership**: A direct full-canvas solid `<rect>` becomes a
real `p:bg`, not a selectable shape. Mark it `data-pptx-layer="master"` for the
deck-wide default, `data-pptx-layer="layout"` for a page-type override, or
`data-pptx-layer="slide"` for a one-slide override. An unmarked direct
full-canvas solid rect in the background plane is also treated as Slide scope. A
Layout background overrides the Master background; a Slide background
overrides both. Use the Master for a globally stable color and the Layout for
cover/section/content variants under the same design language. Gradients,
images, textures, transformed rects, and visible-stroke rects are not promoted
by this solid-background rule.

| Placeholder value | Direct carrier inside slot `<g>` | PowerPoint placeholder |
|---|---|---|
| `title`, `subtitle`, `body` | one `<text data-pptx-placeholder-carrier="true">` | `title`, `subTitle`, `body` |
| `date`, `footer`, `slide-number` | one `<text data-pptx-placeholder-carrier="true">` | `dt`, `ftr`, `sldNum` |
| `picture` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `pic` |
| `chart`, `table` | one matching `data-pptx-native` marker group, marked as carrier | `chart`, `tbl` |
| `object` | one text, image, or basic SVG shape marked as carrier; alternatively the slot group declares `binding="proxy"` | `obj` |
| `media` | one `<image>` or supported imported crop `<svg>`, marked as carrier | `media` |

**Text slot carrier**: A multiline text placeholder must remain one
native text frame. Use the default paragraph merge; `--no-merge` cannot supply
several line shapes as one
PowerPoint placeholder prototype/binding. Leave strict-line text Slide-local
when separate frames are the required result.

`title` is normally type-matched without an index in reconstructed layouts; if
an imported source title explicitly has one, preserve that exact index. Every
indexed placeholder on one layout uses a unique OOXML UInt32 index. Structured export writes the semantic type on both the Layout and Slide carrier (except `obj`, whose OOXML default is already `obj`) so PowerPoint and `python-pptx` retain the same identity. A composite object slot instead keeps its visible group ordinary and uses a hidden transparent proxy.
Date, footer, and slide-number placeholders enable their matching Layout `p:hf`
flags; a date placeholder also gets a `datetimeFigureOut` field in the reusable
Layout definition. The current Slide keeps its authored date content.

Because an omitted `p:ph@idx` has the effective value `0`, an omitted-index
title reserves `0`; no other placeholder on that Layout may use the same
effective index.

**Slot prototype**: The first slide using a Layout key supplies that Layout's placeholder formatting. `data-pptx-placeholder-bounds` supplies the reusable default frame and is mandatory on every slot. Derive it from
the intended design zone, column, panel inset, safe area, or picture frame —
never from text length, glyph width, line count, or a tight content bounding
box. Repeat the same slot ids/types/effective indices/default bounds/binding modes on every slide using that Layout. The Layout owns the reusable `p:ph`; normal visible carriers keep a matching Slide binding so approved rendering stays identical. A composite `object` proxy adds one hidden transparent binding shape to suppress empty inherited placeholder paint. Bounds define the Layout default only; actual Slide content and local carrier geometry may differ.

**Final-package read-back gate**: After writing a temporary structured PPTX and before publishing it, export reopens the package and
verifies that
each Slide targets exactly one Layout, one layout key always resolves to the
same part, different keys do not collapse onto one part, and every Layout is
registered through its Master and the Presentation. Physical Slide/Layout/
Master part rosters, their content-type overrides, and their Presentation/
Master registrations must be exact. It also verifies the Layout picker name,
Master picker identity, placeholder type and effective index, matching `p:hf` flags, explicit design-zone frame, direct prompt size, and level-one default size.
Every owned `p:bg` is checked as an exact zero-or-one payload against the pre-
promotion result; this includes preserving the base Master background when no
authored Master background replaces it. During the same export, every finished
Slide, Layout, and Master must reproduce its exact top-level shape-name roster
and order after packaging. The gate verifies that each carrier-bound slot owns the expected Slide binding, each composite visible carrier remains ordinary, and every composite binding proxy is hidden. A zero-slot Layout must read back with no placeholder. Later slides may keep different Slide-local geometry; only the reusable
Layout frame is checked against the explicit/prototype contract. Any mismatch
fails export without replacing the requested output.

**Static structure consistency**: Repeat the same master element ids on every
slide and the same layout element ids on every slide sharing a layout. Their
generated OOXML must be identical within the affected master/layout group.
Static structure may carry shapes, text, or images; non-image/external relationships are rejected. Every static object is atomic; a `<g data-pptx-layer="master|layout">` is forbidden. A full-canvas first rect may be marked as a Master or Layout background.

**Native object slot carriers**: `chart` / `table` slots require
`--native-objects`; fallback groups contain several shapes and cannot map to one
PowerPoint placeholder. `object` is the generic PowerPoint content slot and
uses either one carrier object or the explicit composite proxy downgrade. `media` currently binds
an authored image/crop to a native `media` placeholder; it does not synthesize
video or audio media from a decorative SVG group.

## 3. Legacy Structure Migration Boundary

Existing structured/template projects or packages that carry `native_structure.json` / `source_template.pptx`, `pptx_structure.mode: baseline|template|preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled` / `utility`, direct atomic placeholders, or an incomplete root Master identity must run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) before generation or export. A project explicitly declaring `pptx_structure.mode: flat` is the current free-design/brand-only route and does not require restoration merely because it has no Master/Layout metadata.

When original PPTX/native facts exist, migration preserves the reachable source Master roster, Layout parent relationships and picker names, placeholder type/index/bounds, and visible supported geometry while normalizing the package into the explicit contract. Source Master/Layout groups are recursively flattened into atomic SVG elements. The current structured roster cannot materialize a source Layout that no output page references, or a Master reachable only through such Layouts; stop and report those identities instead of silently dropping them or inventing a carrier page. A subsequent `create-template` run treats the result according to its selected mode: `standard` / `fidelity` author a new topology, while mirror keeps the restored source topology only when the source graph satisfies that reachability boundary. When no native facts exist, the main Agent explicitly derives a structured contract from the complete SVG pages; the exporter never performs that derivation.

---

## 4. Mirror-mode Templates — Reference-style Consumption

When the project's chosen template is a `mirror` template (`design_spec.md` frontmatter declares `replication_mode: mirror`), Executor switches to a **reference-style** consumption path that bypasses placeholder substitution:

1. **Per-page reference selection** — Strategist selects one mirror page per project page via `spec_lock.md page_layouts` (e.g., `P04: 015_content`). The basename is the mirror filename without extension; Strategist made this choice by reading `design_spec.md §V Page Roster` descriptions, not by guessing.
2. **Copy, don't fill** — open the referenced mirror SVG (already in context from the executor-base.md §1.0 batch read). Copy it as the starting point, then edit slide-specific text in place. Preserve every non-text element and every `data-pptx-*` structure attribute verbatim unless adaptive mode intentionally assigns a new Layout contract.
3. **What you may edit** — the visible text content of `<text>` / `<tspan>` elements that express slide-specific content (title, body, captions, KPI labels, dates, page numbers). Replace the source deck's example text with the project's text for this page from `design_spec.md §IX` and `notes/<NN>_*.md`.
4. **What you must not touch** — element positions, sizes, fonts, colors, fills, strokes, gradients, **which image each `<image>` points at**, `<g>` grouping, sprite-sheet `<svg viewBox>` wrappers, decorative `<rect>` / `<path>` / `<circle>` / `<polygon>` shapes, `<use data-icon="...">` markers, embedded chart data structures. Mirror's value is preserving the source deck's visual identity — any geometric / decorative drift defeats the purpose. **The `href` path is not the image**: normalizing a bare `href="cover_bg.png"` to `href="../images/<name>"` (when Step 3 relocated the asset to `images/`) points at the *same* image and changes nothing visual — that is an allowed path fix, not a fidelity edit. Leaving the bare href as-is is also fine; the exporter and live preview resolve bare hrefs against `images/` either way.
5. **Content fit** — the mirror page was chosen by Strategist because its layout matches the content slot. If the project's content for `P<NN>` legitimately needs more / fewer items than the mirror page provides (e.g. mirror shows 3 KPI cards, project has 4 metrics), keep the mirror page's visual rhythm and either drop one metric to fit or split across two pages — do **not** restructure the mirror page's grid. If neither works, surface a `warning: P<NN> content does not fit mirror reference <basename>; suggest different reference page` and proceed with the closest-fit edit.
6. **Visible text editing** — mirror SVGs may keep literal source text rather than `{{...}}` authoring markers. Edit visible text in place, but retain any imported semantic `data-pptx-placeholder` identity.
7. **Output filename** — follow the standard project SVG naming convention (`<NN>_<page_name>.svg` where `<NN>` matches the project page index, not the mirror source index). The mirror filename is the *reference*, not the *output*.

**Detecting mirror mode**: read the chosen template's `design_spec.md` frontmatter once during the executor-base.md §1.0 batch read. If `replication_mode: mirror`, every page follows §1.1 through its mandatory `page_layouts` reference.

**Mirror + chart pages**: chart structures inside a mirror SVG are already drawn (axis, series, labels). Treat them as visual references — replace the data labels and series text content to match the project's chart spec, but do not redraw the chart from a `templates/charts/<name>.svg` baseline. A mirror template's `page_charts` entries are normally absent for this reason.

**Legacy template boundary**: A template with missing root Master identity, direct atomic placeholders, `data-pptx-layout-kind`, unmapped `baseline`, `preserve`, or `layout_strategy: distill` is not a fallback input. Stop and run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) before generation.

---

## 5. PowerPoint Master / Layout Mapping

This section applies only to deck/layout template routes. `page_layouts` selects the input SVG prototype, and `pptx_masters` / `pptx_layouts` declare the structured output before the first page is drawn. Free-design and brand-only routes use `pptx_structure.mode: flat`, omit all three sections, skip the rest of this section, and keep every SVG object Slide-local.

**Hard rule — template mode only**: A deck/layout template project uses `pptx_structure.mode: structured`. Missing mode or legacy values (`baseline`, `template`, `preserve`), `layout_strategy`, Layout-kind fields, partial mappings, and old direct placeholders must stop generation and route to [`restore-pptx-structure`](../workflows/restore-pptx-structure.md). `flat` is valid only when no deck/layout template is active.

**Hard rule — root identity**: A row `P<NN>: <master_key> | <layout_key> | <layout name>` binds the page to a Master listed in `pptx_masters`. Put that Master key/name and Layout key/name on the root SVG. A Layout key belongs to exactly one Master and remains globally unique.

**Hard rule — atomic fixed layers**: Every `data-pptx-layer="master|layout"` visual is one direct root child that compiles to one DrawingML object. A marked `<g>` is forbidden. When reconstructing source PPTX groups, recursively push supported transforms, paint, opacity, and z-order into atomic children. Repeat the identical ordered Master atom contract on every page using that Master and the identical ordered Layout atom contract on every page sharing that `(master, layout)` pair.

**Hard rule — PowerPoint paint order**: Direct children appear in this order: Master background atoms, Layout background atoms, optional Slide background, remaining Master atoms, remaining Layout atoms, then slot groups and Slide-local content groups. Backgrounds are the inheritance plane beneath all shapes.

**Mandatory — slot authoring**: A reusable content slot is one direct root `<g id>` carrying `data-pptx-placeholder` and positive `data-pptx-placeholder-bounds`. A normal slot contains exactly one compatible direct drawable child marked `data-pptx-placeholder-carrier="true"`. Export unwraps that child into the real Slide placeholder binding. Decorations do not belong in the slot; move reusable decoration to a root Layout atom and keep page-specific labels/captions in another slot or Slide-local group.

**Mandatory — slot identity**: Preserve imported `data-pptx-placeholder-idx` values where available; otherwise omit the title index and assign unique indices only where repeated roles need disambiguation. Pages sharing one Layout key repeat the same slot ids/types/effective indices/default bounds/binding modes. Current text, crop, and Slide-local carrier geometry may differ.

**Composite proxy fallback**: A genuinely composite region may use a direct `<g data-pptx-placeholder="object" data-pptx-placeholder-binding="proxy">` with positive bounds. Its visible group remains Slide-local and export creates one hidden transparent matching placeholder proxy. This downgrade is valid only for `object`; do not use it for an ordinary title, body, picture, chart, table, or media slot.

**Zero-slot Layout**: A Layout may have no slot groups. Covers, posters, and fixed visual pages still declare their named Master/Layout and fixed atoms. Do not manufacture a full-page `object` slot or empty `utility` identity.

**Mandatory — per-page slot coverage**: On every mapped page, declare a slot for each standard role the page actually has: the page heading as `title`, a cover tagline as `subtitle`, the page number as `slide-number`, running footer text as `footer`, a hero / content image as `picture`, and a body block already authored as one merged text frame as `body`. A page shipping zero slots exports a Layout with no insertable placeholders — valid only for a genuinely fixed composition (see Zero-slot Layout above), never as the deck-wide default. Pages sharing one layout key ship the same slot set.

**Hard rule — variable slot content**: “Per-page headings never stay Slide-local by default” means authoring them as `title` / `subtitle` slots; it never permits page-varying text or images to become fixed Layout atoms. Any such value that varies across pages sharing one Layout key MUST be carried by a slot or remain Slide-local.

**Mandatory — master/layout layer coverage**: On every mapped page, mark the deck-wide background and every-page chrome (footer bar, running logo) `data-pptx-layer="master"`, and mark the static framing that defines this layout key's composition (header rule, divider band, zone panels — including chrome repeated on every content page but absent from the cover) `data-pptx-layer="layout"`. A mapped page with zero `data-pptx-layer` marks exports a bare Master and an empty Layout — the layer marks, not the slide content, give each Layout its visible design.

**Layout identity**: Different keys differ in fixed Layout atoms or slot topology/default bounds/binding modes. Identical contracts should share one key. Current wording, imagery, crop, and Slide-local geometry never define identity.

**Template adherence**: Strict copies the prototype Master/Layout/slot contract exactly. Adaptive keeps the prototype Master and may change reusable Layout atoms or slots only under a new explicit Layout key/name. When the completed composition genuinely needs that change, update `spec_lock.md pptx_layouts` immediately while authoring the first affected page; later pages may reuse the new key only by repeating its exact contract. Changing only a label is not a new Layout.

**Layout-content boundary**: Mark only genuinely reusable fixed framing as a Master/Layout atom. Concrete titles, body copy, metrics, chart marks, images, and page-specific groups remain inside slot groups or ordinary Slide-local content groups. The exporter never infers or clusters structure.

**Background ownership**:

| Scope | SVG authoring |
|---|---|
| Deck-wide default | Direct full-canvas solid `<rect data-pptx-layer="master">` repeated identically on every page |
| Page-type default | Direct full-canvas solid `<rect data-pptx-layer="layout">` repeated on every page sharing that layout key |
| One-page exception | Direct full-canvas solid `<rect data-pptx-layer="slide">` |

The exporter writes these solid fills as real Master/Layout/Slide `p:bg`, not selectable full-canvas shapes. Gradients, images, textures, and overlay panels stay explicit shapes unless the shared standard says otherwise.

---

## 6. Structured Per-page Layout Lookup and Scaffold

**Per-page PowerPoint layout lookup — structured deck/layout templates only**:

- When `pptx_structure.mode` is `flat`, skip this lookup and the structured scaffold below. `pptx_masters`, `pptx_layouts`, `page_layouts`, and the corresponding SVG metadata must all be absent. The root `data-pptx-page-role` is the exception — it is required on every flat page (§4.1 of [`semantic-svg.md`](./semantic-svg.md)).
- When a deck/layout template is active, `pptx_structure.mode` must equal `structured`; any other or missing value routes to legacy restoration.
- Read the current page row as `<master_key> | <layout_key> | <layout name>` and resolve `master_key` in `pptx_masters`. Missing, malformed, or partial mappings stop before drawing.
- Write matching root Master/Layout key and picker names. Do not write `data-pptx-layout-kind` or `data-pptx-page-role`.
- On strict template use, the row and SVG contract match the selected prototype exactly.
- On adaptive template use, retain the prototype Master. If the final composition changes fixed Layout atoms or slot topology/bounds, allocate a new key/name and update this row before completing the page.
- A Layout key may repeat across non-adjacent pages only when its fixed atoms and slot contracts are identical.

**Structured template-page scaffold**:

```xml
<svg viewBox="…"
     data-pptx-master="<master-key>" data-pptx-master-name="<master-name>"
     data-pptx-layout="<layout-key>" data-pptx-layout-name="<layout-name>">
  <rect id="master-bg" data-pptx-layer="master" …/>              <!-- one atomic Master object -->
  <text id="master-footer" data-pptx-layer="master" …>…</text>   <!-- no Master/Layout g -->
  <path id="layout-rule" data-pptx-layer="layout" …/>            <!-- one atomic Layout object -->
  <g id="title-slot" data-pptx-placeholder="title"
     data-pptx-placeholder-bounds="60 36 1160 64">
    <text id="title-carrier" data-pptx-placeholder-carrier="true" …>…</text>
  </g>
  <g id="body-slot" data-pptx-placeholder="body"
     data-pptx-placeholder-idx="1"
     data-pptx-placeholder-bounds="60 120 470 500">
    <text id="body-carrier" data-pptx-placeholder-carrier="true" …>…</text>
  </g>
  <g id="picture-slot" data-pptx-placeholder="picture"
     data-pptx-placeholder-idx="2"
     data-pptx-placeholder-bounds="570 120 650 500">
    <image id="picture-carrier" data-pptx-placeholder-carrier="true" …/>
  </g>
  <g id="content-block-1">…</g>                                  <!-- 3–8 content groups -->
  <g id="content-block-2">…</g>
</svg>
```

On structured template pages, Master/Layout atoms and slot groups are direct root children and precede ordinary content groups. Structural metadata nested inside an ordinary content group fails export. Flat pages use ordinary top-level semantic groups only.
