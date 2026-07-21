> See [`strategist.md`](./strategist.md) §h for the image-source confirmation stub that triggers this file. This file owns the full image-strategy system and loads conditionally.

# Strategist Image Strategy Reference

Illustration roles, the deck motif through-line, spot-illustration sheet planning, the AI generation path ladder, the §VIII row legend, and the h.5 rendering × palette lock. [`strategist.md`](./strategist.md) §h keeps only the A–E source choice, the inventory GATE, and the confirmed-value mapping.

**Trigger**: read before authoring an image recommendation other than `none` / `placeholder`, when supplied assets already exist in `images/`, or whenever the confirmed `image_usage` includes `ai` / `web` / `slice`. A data-only deck recommending `none` never loads this file.

---

> **Illustration roles at a glance (Reference).** Within the `image_usage` source boundary, illustrations can play several roles — pick by what the page needs; the **deck illustration motif** rule below threads them into one system. Mechanics live in the linked files.
>
> | Role | When | Mechanism | Source |
> |---|---|---|---|
> | Body spot | scattered decorative accent (the icon-counterpart) | `page_role: local`, sheet→slice `#63` ([image-generator §4.3](./image-generator.md)) | `slice` (from an `ai` sheet) / `provided` / `web` |
> | Hero anchor | cover or a single big statement | `page_role: hero_page` + §4.1 Primitive A or D | per `image_usage` |
> | Section divider | chapter identity, often recurring | `page_role: hero_page` + `#75` divider layout | same motif family |
> | Atmospheric background | mood wash behind editable SVG text | `page_role: hero_page` + §4.1 Primitive D | per `image_usage` |
> | Motif through-line | one family across the roles above, deck-wide (a designed system) | combination of the above | `ai`: generate one family; `provided` / `web`: only if the assets already form one family |

> **Spot illustrations follow the locked `visual_style`'s propensity — a default lean, not a confirmation field.** The user confirms image *source* via `image_usage`; illustrations are not a separate confirmation control, page-role map, or user-facing picker. Within that boundary, whether the deck leans into decorative spot illustrations is anchored by the locked `visual_style`'s **illustration propensity** (`core` / `supportive` / `sparse` — see that style's §6 and the [`visual-styles/_index.md`](./visual-styles/_index.md) `Illus.` column):
>
> - **`core`** (e.g. sketch-notes, memphis, paper-cut) — illustration is intrinsic; default to planning a coherent spot family.
> - **`supportive`** — use where it genuinely lifts rhythm or section identity, kept restrained.
> - **`sparse`** (e.g. swiss-minimal, photo-editorial, data-journalism) — the style's lead visual competes; default to none.
>
> **Precedence (high → low): `image_usage: none` → explicit user intent → visual_style propensity → none.** `image_usage: none` always wins and produces no illustration rows. Otherwise an **explicit user request** to use or skip illustrations (stated in chat — the canonical channel) overrides the propensity default *in either direction*: use them even on a `sparse` style, skip them even on a `core` style. Propensity is only the default when the user gives no steer. Record the decision and its reason in `image_notes` / `design_spec`.
>
> **Propensity sets *whether* and the lean — never the *source* or the *how*.** Source still comes from `image_usage`: a `core` style does **not** silently generate AI spots when the user did not select AI — with no AI source it draws only on a confirmed source (`provided` / `web`) or goes without. How heavily and where stays Strategist judgment, and the locked style still governs deployment (a `sparse` style used on explicit request stays very few, very light). Do not force a quota, and do not phrase it as "few pages." Suitable means the spot improves rhythm, warmth, continuity, or section identity without carrying facts or competing with charts, photos, tables, screenshots, or key text.

> **Deck illustration motif — deploy one family as a through-line, not isolated spots.** When the deck leans into illustration (a `core` propensity, or an explicit user request for a designed, illustrated feel), the strongest use is **one coherent motif family** — a single subject world in the deck-wide rendering + palette locked at h.5 — deployed across scales: a cover anchor (`page_role: hero_page`), recurring section dividers for chapter identity ([image-layout-patterns](./image-layout-patterns.md) `#75`), and small body spots (`local` sheet→slice, `#63`). They read as one designed system because they share a family, not just a palette. **Source still bounds it** (same precedence as above): the AI motif — `hero_page` generations plus the sheet→slice spots — is planned **only when the confirmed `image_usage` includes `ai`**. With `provided` / `web`, a through-line is possible only when the supplied or sourced assets already form one visual family to carry across pages; otherwise the deck goes without rather than silently generating AI. Reach for it only when the deck suits it — **not a quota**: not every section needs a divider, a deck with no clear sections or no room for decoration is not forced into a motif, and the through-line never competes with charts, photos, tables, or key text. When a motif is in play, the cover / divider pages surfaced by the **hero_page suggestion** below and the body spots should be drawn from the same family. **The family is not one giant sheet** — the slicer cuts a uniform grid, so cover / divider anchors are their own `hero_page` generations (mechanics: [image-generator.md](./image-generator.md) §4.1) sharing the spot sheet's (§4.3) rendering, palette, and subject world.

**AI generation path — one sheet, then slice.** When spot illustrations are AI-generated and the deck needs ≥3 same-family elements, write one `ai` Illustration Sheet row plus one `slice` row per used element. Step 5 generates the sheet, then slices transparent PNG elements for placement. This is just AI-generated imagery batched for consistency and efficiency; do not generate one image per spot.

**Plan illustration shape from placement, not from a square default.** Before writing the sheet row, group the planned spot illustrations by intended placement shape: compact object, tall side accent, wide banner/vignette, or another explicit shape family. Do not ask for generic "small illustrations" with no shape intent. If one deck needs incompatible shapes, write separate sheet intents instead of forcing every element into one implied square set; Image_Generator owns the exact sheet ratio and grid.

**When recommending C** — surface its resolution ladder so the user knows "no API key" is a supported state:

| Order | Path | Trigger | Mechanism |
|---|---|---|---|
| 1 | **Path A — codex** | Default — `IMAGE_BACKEND` unset uses the `codex` backend (Codex CLI, ChatGPT OAuth via `codex login`; no API key / `.env`) | `image_gen.py --manifest` runs in Step 5; on failure the agent prints install/login guidance and retries after the user fixes it |
| 2 | **Path B — API backend** | Path A unrecovered AND `IMAGE_BACKEND` + provider key already configured — the lowest-priority generation engine | Same `image_gen.py --manifest` with the explicit backend |
| 3 | **Web-sourcing switch** | No generation engine available; user accepts the offer | Rows flip to `Acquire Via: web`; [`image-searcher.md`](./image-searcher.md) pipeline (keyless first) |
| 4 | **User-drop** | Everything above unavailable or declined | Agent lists each missing image's filename / purpose / size; user places chosen images at `project/images/<filename>` |

Selection is automatic in Step 5. Detailed contract: [`image-generator.md`](./image-generator.md) §7 Path Selection (Deterministic).

Selections may be mixed at the row level — e.g. a deck can use C for hero illustrations while sourcing D for supporting team photos.

> **Spot illustrations → one sheet, not N rows.** When the deck wants ≥3 small same-family spot illustrations as decorative accessories across pages (the illustration counterpart to icons), do not write one `ai` row per element. Write **one `ai` sheet row** (the sheet prompt intent — generated but never placed, kept out of `spec_lock.md images`) **plus one `slice` element row per used element** (each placed, each listed in `spec_lock.md images` so the Executor may reference it). The sheet row's `Reference` must name the intended cell shape family and placement purpose, such as "portrait side-accent spot set" or "landscape footer-vignette spot set"; the slice rows reference the parent sheet + cell. Step 5 / Image_Generator chooses the exact sheet ratio, grid, and slice command. Plan these sparingly, only where decoration genuinely lifts the page. Full resource contract + slice command: [`image-generator.md`](./image-generator.md) §4.3.

#### h.5 AI Image Strategy — lock rendering + palette (only when C is selected)

When the deck includes any `ai` rows, Strategist locks a **deck-wide rendering** and **deck-wide palette** here. These two values are written into `design_spec.md §III` and `spec_lock.md colors` / `images` sections, then consumed by Image_Generator. Every AI image in the deck shares them — this is what makes multiple AI images feel like one deck.

🚧 **GATE — before recommending values**: `read_file references/image-renderings/_index.md` and `read_file references/image-palettes/_index.md`. They contain the catalog, auto-selection tables, and a rendering × palette compatibility matrix.

#### Three-candidate presentation (default path)

**Hard rule**: Unless the user has already named a specific rendering or palette (chat or template), present **≥3 distinct rendering × palette combinations** and let the user pick. Never auto-lock a single combination silently.

**Per-candidate schema** (exactly 4 lines, no extras):

```
[Plan A] <temperament label> — <rendering> × <palette>
  Visual: <shape / line / material / light, 1-2 phrases>
  Color: <secondary HEX (ratio) + primary HEX (ratio) + accent HEX (ratio); HEX values from e.>
  Mood: <2-3 traits>; like <real-world analogy: company / publication / event>
```

After the candidates, append one line:

```
> Reference images: see references/ai-image-comparison/ for matching preview images by name.
```

**Confirm UI packaging**: when writing the `recommendations.json` image fields, put **exactly three non-custom** generated-image recommendations in `image_strategy.candidates`. The page appends one built-in **Custom** card after those three recommendations, so do not use a `custom` candidate as a fourth option or as a slot filler in the UI payload.

**Confirmed Custom card prose**: when `result.json.image_strategy.custom` is non-empty, treat it as a confirmed deck-wide image-direction constraint. Write the prose into `design_spec.md §III` image direction notes and carry it into every `Acquire Via: ai` prompt brief / `images/image_prompts.json` prompt guidance that it applies to. It augments the locked `rendering` + `palette` ids; preserve those ids for catalog / comparison-reference behavior, and use the custom prose for subject, composition, texture, avoidance, or other prompt specifics.

**Hard rules for candidate construction**:

| Rule | Behavior |
|---|---|
| Filter by e.'s HEX | Only include palettes whose temperament can carry the user's HEX. Vivid red → exclude `cool-corporate` / `mono-ink`; include `vivid-launch` / `warm-earth` / `editorial-classic`. |
| HEX values in `Color` line MUST be e.'s real values | Palette contributes only the 60-30-10 ratio + role assignment. Never substitute the palette's typical HEX. |
| Span a personality spectrum | Typically: one conservative-default (industry norm), one shifted-tone (same fit, 1-2 ticks different), one bold-contrast (more expressive, may challenge default). No near-duplicates. |
| `Mood` line MUST include a real-world analogy | Company / publication / event the user can picture. Adjective stacks alone are forbidden. |
| Adapt labels to chat language | Schema is English by default. Chinese chat → render as 「方案 A / 视觉 / 色彩 / 情绪」. Structure stays the same; only the labels translate. |
| Skip presentation when user has specified | User-named rendering or palette (chat / brand / template), **or a Confirm UI pick in `result.json.image_strategy`** (same shape as color / typography honoring their confirmed candidate), bypasses the candidate flow — lock *that chosen candidate's* `rendering` + `palette` directly per the truth-precedence rule; do not re-pick. |
| `custom` is a tail-case, not a default | When no preset fits, a candidate may set `rendering: custom` and / or `palette: custom` (rules: [`image-renderings/_index.md`](./image-renderings/_index.md) §1.5, [`image-palettes/_index.md`](./image-palettes/_index.md) §2). At most one candidate per dimension may carry `custom`; one candidate may carry both dimensions as `custom`. `Visual` / `Color` lines describe the behavior in prose, never by naming a competing preset. |

**Forbidden — padding with conflicts**: if e.'s HEX cannot find ≥3 compatible palettes, present the smaller set (2 candidates) and state "your color is unusual — only N palettes can carry it without conflict." A `custom` candidate is allowed only when its prose genuinely describes a tail-case the presets cannot — not as a slot-filler. Never fill remaining slots with known-conflicting options.

**Worked example** (e. = `#1E3A5F` navy + `#F8F9FA` off-white + `#D4AF37` gold; d. = consulting; chat in English):

```
[Plan A] Restrained Professional — vector-illustration × cool-corporate
  Visual: flat vector, solid color blocks, no gradients or shadows
  Color: off-white #F8F9FA (60-70%) + deep navy #1E3A5F main (25-30%) + gold #D4AF37 accent (<5%)
  Mood: steady, trustworthy, restrained gravitas; like a McKinsey consulting report

[Plan B] Editorial Depth — editorial × editorial-classic
  Visual: magazine layout, 8% paper texture, column-based partitioning
  Color: off-white #F8F9FA paper (55%) + deep navy #1E3A5F column (30%) + gold #D4AF37 rule line (10-14%)
  Mood: refined, considered, paced; like an Economist feature spread

[Plan C] Future Energy — 3d-isometric × tech-neon
  Visual: isometric 3D, soft shading, 8% glow halos around bright elements
  Color: off-white #F8F9FA digital field (50%) + deep navy #1E3A5F main (35%) + gold #D4AF37 emphasis (10-15%)
  Mood: forward, energetic, futuristic; like an Apple or Stripe product keynote

> Reference images: see references/ai-image-comparison/ for matching preview images by name.
```

**Worked example — `custom × custom`** (tail-case; e.g. 新中式 deck with `#1A1A1A` + `#F5EFE0` + `#A52A2A`):

```
[Plan A] 文人雅致 — custom × custom
  Visual: dry-brush burnt-ink, five tonal gradations, 宣纸 paper-grain, deliberate negative space; 朱泥 seal as single red mark
  Color: cream #F5EFE0 ~65% negative space + burnt-ink #1A1A1A ~20% strokes + cinnabar #A52A2A 3-5% seal
  Mood: literati restraint; like 苏州博物馆 pacing
```

`Visual` / `Color` lines feed `spec_lock.md`'s `image_*_behavior` rows verbatim.

After the user picks a candidate (or supplies a custom variant), proceed to "Recording the lock" below.

#### Prompt depth for §VIII rows

**Hard rule**: When §VIII contains paper-figure or subject-domain rows (scientific subjects, specialized fields, regulated content), each row's `generation description` follows [`image-generator.md`](./image-generator.md) §4.2 Prompt depth — expand to the depth the subject demands; 500-1000+ words is normal.

**Forbidden — generic shortening**: never drop a paper-figure row's prompt to a 50-word generic illustration brief.

---

#### Catalog reference (for candidate construction)

The tables below are source data Strategist reads when constructing the three candidates above. They are no longer the final output by themselves.

**Rendering recommendation** (soft — user may override with any other rendering from the catalog):

| `d. Style` signal | Recommended rendering | Alternates |
|---|---|---|
| Strategic / MBB / board | `editorial` or `vector-illustration` | `blueprint`, `minimalist-swiss` |
| Corporate report / analysis / 学术答辩 | `vector-illustration` | `flat`, `editorial` |
| High-end consulting / luxury / 高端 / design-firm | `minimalist-swiss` | `editorial`, `vector-illustration` |
| Tech / SaaS / AI / 架构 | `3d-isometric`, `blueprint`, `digital-dashboard` | `flat` |
| Modern SaaS / fintech / health-tech / premium app | `glassmorphism` | `digital-dashboard`, `flat` |
| Product launch / brand / marketing | `flat`, `3d-isometric`, `corporate-photo` | `vector-illustration` |
| Education / training / 教学 / 培训 | `sketch-notes` | `vector-illustration`, `paper-cut` |
| Children / storybook / 儿童 / 治愈 | `fantasy-animation` | `paper-cut`, `watercolor`, `sketch-notes` |
| Cultural / folk / festival / 文化 / 节日 | `paper-cut` | `vintage-poster`, `screen-print` |
| Methodology / Before-After / 方法论 / manifesto | `ink-notes` | `editorial` |
| Government / formal / 政务 | `editorial` or `corporate-photo` | `vector-illustration` |
| Finance / journalism / 财经 | `editorial`, `digital-dashboard` | `vector-illustration` |
| Personal story / 个人成长 / lifestyle | `watercolor`, `warm-scene` | `corporate-photo`, `paper-cut` |
| Cultural / media / opinion / cinematic | `screen-print`, `vintage-poster` | `editorial`, `warm-scene` |
| Brand heritage / hospitality / 老字号 / 周年 | `vintage-poster` | `screen-print`, `editorial` |
| Gaming / retro / 复古 / 像素 | `pixel-art` | `vintage-poster` |
| Environment / wellness / 环保 | `nature` | `watercolor`, `paper-cut` |
| Classroom / blackboard / 课堂 | `chalkboard` | `sketch-notes` |
| Team / company / product photo | `corporate-photo` | — |

**Palette recommendation** (soft — user may override):

| Content vibe / industry | Recommended palette | Alternates |
|---|---|---|
| Consulting / finance / B2B / corporate / 学术答辩 | `cool-corporate` | `editorial-classic`, `frost-ice` |
| Tech / SaaS / AI | `tech-neon` | `cool-corporate`, `dark-cinematic` |
| Modern SaaS / fintech / health-tech | `frost-ice` | `cool-corporate`, `tech-neon` |
| Health / medical / beauty / skincare | `frost-ice` | `nature-organic`, `earthy-dusty` |
| Education / training | `macaron` | `warm-earth` |
| Methodology / Before-After | `mono-ink` | `editorial-classic` |
| Personal / lifestyle / brand story | `warm-earth` | `nature-organic`, `earthy-dusty` |
| Interior / wellness / mindfulness / slow living | `earthy-dusty` | `warm-earth`, `nature-organic` |
| Product launch / marketing | `vivid-launch` | `tech-neon`, `sunset-gradient` |
| Creative agency / travel / music / lifestyle | `sunset-gradient` | `vivid-launch`, `warm-earth` |
| Luxury / fashion / jewelry / premium / heritage | `jewel-tone` | `dark-cinematic`, `editorial-classic` |
| Children / storybook | `macaron` | `warm-earth` |
| Premium / film / entertainment | `dark-cinematic` | `jewel-tone`, `duotone` |
| Cultural / media / cover-art | `duotone` | `editorial-classic` |
| Environment / wellness | `nature-organic` | `warm-earth`, `earthy-dusty` |
| Finance / journalism | `editorial-classic` | `cool-corporate` |

After auto-selecting, cross-check `image-palettes/_index.md` compatibility matrix — if rendering × palette is `✗`, swap to the alternate palette.

**d-e-f-g linkage sanity check** (do this after picking rendering + palette):

| Linkage | What to verify |
|---|---|
| **d. Style ↔ rendering** | Rendering family should match the Style descriptor's temperament (corporate ≠ sketch-notes; tech ≠ watercolor). Already enforced by the recommendation table above. |
| **e. Color HEX ↔ palette** | HEX is truth — palette is just the "how to use these HEX" rulebook for AI images (saturation / contrast / 60-30-10 / material). Mismatch → **always swap palette to fit the HEX, never adjust the HEX to fit a palette**. E.g. user gives a vivid red but you auto-picked cool-corporate — switch to vivid-launch or warm-earth, do not propose dimming the red. |
| **f. Icon library ↔ rendering** | `tabler-outline` pairs well with all renderings (most versatile). `chunk-filled` / `tabler-filled` pair better with `vector-illustration` / `flat` / `editorial`. `phosphor-duotone` pairs with `flat` / `digital-dashboard`. Mismatch is not fatal but worth flagging. |
| **g. Typography ↔ rendering** | Serif title → pairs well with `editorial`, `corporate-photo`, `screen-print`. Hand-lettered direction → already implied by `sketch-notes` / `ink-notes` (the rendering carries the lettering, no separate font requirement). Display font → `vivid-launch` / `screen-print`. Mismatch is rarely fatal; note in conversation if it feels off. |

**Recording the lock** — after picking, write to:

- `design_spec.md §III Visual Theme` — add lines under the color table:
  ```
  - **Image Rendering**: vector-illustration
  - **Image Palette**: cool-corporate
  ```
- `spec_lock.md colors` section — add rows at the bottom:
  ```
  - image_rendering: vector-illustration
  - image_palette: cool-corporate
  ```

**Hard rule — `custom` recording**: when the picked candidate has `rendering: custom` or `palette: custom`, also write the sibling `*_behavior` row. Source: the candidate's `Visual` line (for rendering) / `Color` line (for palette), expanded to cover the prose requirements in [`image-renderings/_index.md`](./image-renderings/_index.md) §1.5 / [`image-palettes/_index.md`](./image-palettes/_index.md) §2 (chat candidates are compressed; spec_lock prose covers all axes). Both `design_spec.md` and `spec_lock.md` must carry the behavior line. Example for the `custom × custom` candidate above:

```
- image_rendering: custom
- image_rendering_behavior: "Dry-brush burnt-ink with five tonal gradations, 宣纸 paper-grain at 12% opacity, deliberate negative space; 朱泥 seal as a single red mark; no Western outlines, no gradients."
- image_palette: custom
- image_palette_behavior: "宣纸 cream `#F5EFE0` carries ~65% as negative space; burnt-ink `#1A1A1A` anchors ~20% as brush strokes; cinnabar `#A52A2A` only in 3-5% as seal. Literati restraint — no fourth color."
```

Image_Generator reads these fields and applies them deck-wide. If both are absent (legacy decks), it falls back to inferring from `d. Style` and `e. Color` — quality is acceptable but not optimal. Always lock both when C is selected.

#### hero_page suggestion (same confirmation turn)

After the user picks a candidate, scan the outline and surface any pages where the image makes more sense as the page's main voice than as a local block. Present them as a short list and let the user confirm, edit, or skip. Result is recorded as `page_role: hero_page` on the matching `ai` rows. Density is judgment-based — no fixed quota.

**Per hero_page title**: lock where it lives — `embedded` (fused into the image: neon, carved, smoke, 3D-lit lettering) or `none` (editable SVG title over an atmospheric backdrop, Primitive D). Default `none`; flip to `embedded` only when the words must be *part of the visual*, not merely a display font. Per page — may bake only the keyword while subtitle / date / chrome stay SVG. Surface it with the hero_page list for the same confirm / edit / skip.

**When selection includes B**, you must run `python3 scripts/analyze_images.py <project_path>/images` before outputting the spec, and integrate scan results into the image resource list.

**When B / C / D / E is selected**, add an image resource list to the spec:

| Column | Description |
|--------|-------------|
| Filename | e.g., `cover_bg.png` |
| Dimensions | e.g., `1280x720` |
| Ratio | e.g., `1.78` |
| Layout suggestion | e.g., `Wide landscape (suitable for full-screen/illustration)` |
| **Layout pattern** | **MANDATORY** — one or more `#<id> <name>` joined by ` + ` from `image-layout-patterns.md`. Combine a Primary id with optional Modifier ids when the page needs it (e.g. `#48 side-by-side comparison + #21 rounded rectangle crop + #29 two-stop scrim`). A single Primary is fine when the page calls for it. See the GATE earlier in this section. Empty cells or invented ids are invalid. |
| Purpose | e.g., `Cover background` |
| Type | Free-form category tag — `Background`, `Photography`, `Illustration`, `Diagram`, `Portrait`, `Latex Formula`, etc. Required for formula rows (`Latex Formula`). |
| **Acquire Via** | `ai` / `web` / `user` / `formula` / `placeholder` / `slice` — only `ai` and `web` drive Step 5 dispatch; `slice` is derived after its `ai` sheet generates (§4.3) |
| Status | Initial status must be `Pending`, `Existing`, `Rendered`, or `Placeholder`; see [`svg-image-embedding.md`](svg-image-embedding.md) for the full status enum |
| **Reference** | Free-form **intent description** (NOT a search query); feeds Image_Generator (ai) or Image_Searcher (web) |
| `text_policy` (optional, `ai` rows only) | `none` (no text in image) or `embedded` (text is part of the artwork). Leave blank when Image_Generator should decide per row. Long body / data / lists stay in SVG. |
| `page_role` (optional, `ai` rows only) | `local` (image is a region block on an SVG page) or `hero_page` (image is the page's main voice). Leave blank when Image_Generator should decide per row. |

**No-crop flag (exception only)**: most images are croppable — Executor defaults to `preserveAspectRatio="xMidYMid slice"`. When an image must NOT lose pixels (data screenshots, charts, certificates, contracts, dense diagrams), append `no-crop` to its `spec_lock.md images` entry. Executor will then size the container to the native ratio and use `meet`. Don't tag the rest.

**Formula rows**: rendered LaTeX PNGs are image rows with `Acquire Via: formula`, `Status: Rendered`, and `Type: Latex Formula`. Always append `no-crop` in `spec_lock.md images`. They are not AI images and never go through Step 5.

**Reference field**: Write visual intent, not provider mechanics.

| ✅ Intent description | ❌ Avoid |
|---|---|
| "Diverse engineering team collaborating around a laptop, modern office, natural light" | "team laptop office" |
| "Abstract atmospheric backdrop for academic-defense cover, calm center for text overlay, hint of campus skyline" | "use openverse, search 'office'" |
| "Sunlit forest path in autumn" | "team photo" |

**Per-row Reference grammar**:

| Acquire Via | Reference pattern |
|---|---|
| `ai` | **Subject + intent + composition** only. Do NOT repeat style words ("flat design", "modern", "vector") or HEX values — both are already locked deck-wide by h.5 (rendering + palette) and `design_spec §III` (colors). Image_Generator's prompt assembler injects them automatically. |
| `web` | Concrete subject/place/object first, then 1-3 quality descriptors |
| `formula` | Original LaTeX plus short placement intent, e.g. `formula_001: block energy-mass equation for P03` |

**Allowed web quality descriptors**:

| Descriptor | Use |
|---|---|
| `professional editorial photography` | Stock-style photography |
| `clean composition` | Covers, section dividers, image-text layouts |
| `natural light` | People, workplace, travel, lifestyle scenes |
| `high-resolution` | Large visual areas |

**Forbidden — web negative prompts**: `not tourist snapshot`, `no phone photo`, `avoid amateur style`.

| Mode | Good Reference |
|---|---|
| `web` | "Diverse team collaborating at a modern office desk, professional editorial photography, natural light, laptop visible" |
| `ai` | "Atmospheric backdrop suggesting digital innovation; calm central area reserved for slide title overlay; light geometric anchor at one edge" |
| `ai` | "Four-stage value chain from raw input to R&D output; icons should suggest tax-form → cost-reduction → equipment-upgrade → innovation; no text labels (SVG overlays them)" |

🚧 **GATE — before writing §VIII Image Resource List**: when image approach is B/C/D/E (anything other than A "no images"), this is a three-layer hard requirement, not a suggestion:

1. **Read** — `read_file references/image-layout-patterns.md`. The file enumerates 72 numbered techniques split into **Part 1 — Primary Structures** (#1–#19 container layouts, #38–#46 image-as-canvas + native overlay, #47–#56 multi-image) and **Part 2 — Modifier Layers** (#20–#26 non-rectangular crops, #27–#37 overlays & masks, #57–#61 texture, #62–#72 special). The four `Image narrative intent` values below cover only broad categories.
2. **Produce** — every non-formula row in §VIII Image Resource List MUST fill the `Layout pattern` column with one or more `#<id> <name>` joined by ` + ` drawn verbatim from this file (Primary + optional Modifiers). Rows with empty cells, paraphrased names, or invented ids are invalid. Formula rows are the only exception; use `formula-inline` or `formula-block`.
3. **Image-as-canvas coverage** — for any deck with ≥4 image-bearing pages, at least one page MUST use a `#38–#46` pattern (image-as-canvas + native overlay) unless every image is a pure cover / chapter divider / atmosphere backdrop. This family is the most-skipped one and is usually the right answer for content-rich pages with photographs. If the deck legitimately has no opportunity for it, state the reason in §VIII directly under the table.

**Skip-detection signal for self-audit**: if you notice that every page's `Layout pattern` column resolves to #2/#3 (left-third or right-third), #5/#6 (top-bottom band), or generic side-by-side, you have not actually consulted the file — re-read and reconsider. The default left/right and top/bottom split bias is the failure mode this gate exists to break.

**Skip-detection signal — `text_policy` column**: if every `ai` row resolves to `none` and the deck contains any paper-figure / academic schematic / panel-comparison / data-axis page, you defaulted instead of judging per row. Consult [`image-generator.md`](image-generator.md) §5.3 positive-trigger table and re-decide each row. `none` for every row is correct only when no row matches a trigger; otherwise this is the same class of failure as the layout-pattern signal above.

**Image narrative intent** (decide *before* the ratio table — determines whether the image lives in a container at all):

| Intent | Form | When to use |
|--------|------|-------------|
| **Hero / full-bleed** | Image fills canvas/dominant zone; title floats over with gradient or opacity overlay | Covers, chapter dividers, `breathing` pages — image *is* the message |
| **Atmosphere / background** | Image as low-contrast backdrop (reduced opacity or dark overlay); text reads on top | Section backgrounds, mood-setting — image sets tone, text carries info |
| **Side-by-side** | Image and text as adjacent coequal blocks — ratio table below governs container sizing | Most content pages — image and text read together |
| **Accent / inline** | Small image beside related text, not a container; no ratio matching | Supporting visuals, spot illustrations |

> Intent follows narrative purpose, not image ratio. Don't default every image page to side-by-side.

**Side-by-side ratio alignment** (consult only when the chosen intent is *side-by-side*; detailed calculation rules in `references/image-layout-spec.md`):

| Image Ratio | Recommended Container Layout |
|-------------|-----------------------------|
| > 2.0 (ultra-wide) | Top-bottom split, top full-width |
| 1.5-2.0 (wide) | Top-bottom split |
| 1.2-1.5 (standard landscape) | Left-right split |
| 0.8-1.2 (square) | Left-right split |
| < 0.8 (portrait) | Left-right split, image on left |

Side-by-side only: container ratio must match image ratio. Hero / atmosphere / accent intents ignore ratio alignment.

> **Portrait canvases** (Xiaohongshu, Story): Layout rules differ — top-bottom is preferred for most ratios since left-right columns become too narrow. See "Portrait Canvas Override" in `references/image-layout-spec.md`.

> **Multi-image slides**: When multiple images appear on one page, use the grid formulas in the "Multi-Image Layout" section of `references/image-layout-spec.md`.

> **Pipeline handoff**: When C) AI generation is selected, Image_Generator consumes `Pending` rows and updates them to `Generated` or `Needs-Manual` before Executor proceeds. Status names are defined in [`svg-image-embedding.md`](svg-image-embedding.md).

---

## §VIII Row Legend (moved from `templates/design_spec_reference.md`)

> **Layout pattern column is MANDATORY** — for non-formula rows, value is one or more `#<id> <name>` joined by ` + ` drawn verbatim from [`references/image-layout-patterns.md`](../references/image-layout-patterns.md) (Primary + optional Modifiers). Empty cells, paraphrased names, or invented ids invalidate the row. Formula rows are the only exception; use `formula-inline` or `formula-block`. See `strategist.md §h` GATE for the three-layer requirement (read → produce → image-as-canvas coverage).

**Type** (free-form category tag; common values):

- `Background` — cover / chapter / full-bleed atmosphere
- `Photography` — real-world photo
- `Illustration` — vector / flat / painterly art
- `Illustration Sheet` — a grid of several spot illustrations generated as one image to be sliced (the `ai` sheet row of a `slice` set; never placed itself)
- `Diagram` — schematic / architecture / flowchart
- `Portrait` — single-subject person
- `Latex Formula` — formula PNG rendered by `latex_render.py`

**Status**:

- **Pending** — needs AI generation or web sourcing
- **Rendered** — deterministic formula asset already exists under `images/`
- **Existing** — user-supplied, place in `images/`
- **Placeholder** — not yet processed, use dashed border in SVG

**Acquire Via**:

- `ai` — Step 5 Image_Generator
- `web` — Step 5 Image_Searcher
- `formula` — already rendered by `latex_render.py` before this spec was written
- `user` — user-supplied
- `placeholder` — intentionally deferred
- `slice` — a spot-illustration element derived in Step 5 by cutting it out of an `ai` sheet row (not generated on its own)

> **Spot-illustration sheets (`slice`).** When the deck draws several same-family spot illustrations from one generated sheet (see [`image-generator.md`](../references/image-generator.md) §4.3), write **two kinds of rows**: one **sheet row** (`Acquire Via: ai`, `Type: Illustration Sheet`, name the intended cell shape + placement purpose in `Reference`, e.g. `portrait side-accent spot set` or `landscape footer-vignette spot set`) that is generated but **never placed** — keep it out of `spec_lock.md images`; and one **element row per used element** (`Acquire Via: slice`, `Reference` naming the parent sheet + cell/element, dimensions filled after slicing) that **is** placed — list every element row in `spec_lock.md images` so the Executor may reference it. Strategist states the shape intent; Image_Generator chooses the exact sheet ratio, grid, and slice command. An element row with no sheet row, or a sliced file absent from `spec_lock.md images`, is an invalid spec. **Each element row's Layout pattern must come from the decorative-cutout family** (`#63` sticker, `#4` edge bleed, `#58` corner fragment, `#66` fade-out, `#69` rotation, `#49` cluster) — a transparent spot is an accessory placed at the margins / off-edge / behind text, never centered in a boxed tile.

**text_policy** (`ai` rows only; AI judges per row, no global default bias):

- `none` — image carries no text; SVG overlays all labels
- `embedded` — image contains in-artwork text: decorative lettering, a designed title, hand-lettered keywords, or stable visual identifiers (axis labels, subplot letters, unit symbols). Body copy / data points / long quotes never go inside the image regardless — they must stay editable. Embedded text is frozen into the raster, so the exact characters are named literally in the prompt

**page_role** (`ai` rows only; leave blank for default):

- *blank / `local`* — image is a region block on an SVG page
- `hero_page` — image is the page's main voice; SVG overlay is minimal or empty. Use on covers, chapter dividers, mood transitions, single-number data heroes, closing quotes. Same rendering and palette as the rest of the deck regardless

**Reference grammar** (`ai` rows): write **subject + intent + composition** only. Do NOT repeat style words ("flat design", "modern") or HEX values — both are already locked deck-wide by `design_spec §III AI Image Strategy` (rendering + palette) and `§III Color Scheme` (HEX triplet). Image_Generator's prompt assembler injects them.
