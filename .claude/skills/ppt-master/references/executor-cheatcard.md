# Executor Cheat-Card — free-design flat decks (SPEED PATH)

> **What this is.** A one-screen distillation of the *hard* Executor constraints
> from [`executor-base.md`](./executor-base.md) + [`shared-standards.md`](./shared-standards.md),
> for the **free-design / brand-only `pptx_structure.mode: flat`** route with **no
> template, no data charts, no images**. On that route you MAY read this card
> instead of re-reading those two long files end-to-end, then draw.
>
> **When NOT to use this card (read the full refs instead):** structured deck/layout
> template routes (`mode: structured`), any `page_charts` / data-viz pages, any
> `§VIII` image rows, mirror/beautify/native-enhance routes, or speaker notes.
> This card omits their contracts on purpose.
>
> The mode (`references/modes/<mode>.md`) and visual-style
> (`references/visual-styles/<style>.md`) files are short — still read those two.

---

## 0. Before the first page (once)
- Output **design parameters**: canvas dims, body px, primary/accent/text HEX, font stacks (from `spec_lock.md`).
- Start live preview (non-fatal if it fails — state the failure):
  `python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project> --live --daemon`
- Re-read `spec_lock.md` before P01, P05, P09, and after any compaction. Use **only** its colors / fonts / sizes / icons / `page_rhythm`.

## 1. Every page — root + chrome
- Root: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 <W> <H>" data-pptx-page-role="cover|toc|section|content|ending">`. `viewBox` MUST equal the canvas. No root `transform`.
- First child: full-canvas solid `<rect>` background (promotes to native slide bg).
- **Flat route:** NO `data-pptx-master/layout/layer/placeholder` metadata anywhere. Every object stays Slide-local.
- **Grouping (mandatory):** wrap every logical unit in a **top-level `<g id="descriptive">`**. Aim **3–8** content groups per page. No giant page-wrapping `<g>`, no ungrouped top-level `<text>/<rect>/<path>` atoms, no one-group-per-line.

## 2. Text = well-formed XML
- Typography glyphs (— – · © → NBSP full-width): **raw Unicode**, never HTML entities (`&mdash;` etc.).
- XML reserved chars in text/attrs: `&amp; &lt; &gt; &quot; &apos;` only. One bare `&`/`<`/`>` aborts export.
- One editable paragraph = one `<text>` with sibling `<tspan>` that **repeat the parent `x`** and use the **same positive `dy`** (line-height) and **same font-size**. A changed `x`, growing `dy`, or size change splits the frame.

## 3. Type lock (the #1 "looks unprofessional" trap)
- Copy the locked px from `spec_lock.typography` **verbatim** (`body` 24 → write `24`; no pt, no "rounder" number, no long decimals).
- **Structural roles hold ONE size deck-wide:** page title, body, subtitle, annotation/caption, footnote/page-number. Never re-pick per page.
- Feature elements (hero number, cover/section display, one-off emphasis) may take an in-ramp intermediate size; if it recurs, it must be a declared slot.
- Page **core message ≥ body** (map to `lead`/`subtitle`). Never below body.
- Last-resort body-only shrink: −2px steps, floor `body − 4`. Title/subtitle/caption/footnote never shrink.

## 4. Width budget — measure BEFORE you draw (kills the warn→edit loop)
- SVG has no auto-wrap; every break is your manual `<tspan>`. So decide per block:
  `est = Σ glyph  (CJK/full-width 1.0×fs · Latin/digit/ASCII 0.55×fs · space 0.25×fs) + letter_spacing×(n−1)`
- `available = right_bound − x`, where `right_bound = canvasW − 5%` (1216 on 1280) unless a nearer right-side element.
- `est ≤ available` → **one line** (wrapping a fitting sentence is a flagged defect).
- `est > available` → wrap; a lead/core/subtitle wraps as a **balanced** 2-line at a phrase boundary (no orphan tail). Body prose may wrap freely.
- **Use the helper instead of guessing** — it returns the exact checker verdict + a balanced-break suggestion:
  `python3 ${SKILL_DIR}/scripts/text_fit.py "text" -s <fs> --x <x>` (or `--zone <w>` for a bounded column). Batch: `--batch blocks.json`.
- **Batch ONCE, not per-line.** One `--batch` covering the deck's risk lines (leads/core-messages, cover/section heroes, every column body) costs one round-trip; five ad-hoc calls cost five. Skip trivially-short lines.
- **Column-wrap trap (the checker measures the FULL canvas, not your column).** The gate's unnecessary-wrap warning uses `right_bound = canvasW − 5%` and only narrows it to a **sibling shape** (rect/line/icon) that sits to the block's right *and vertically overlaps its y-band*. A column separated only by whitespace is **not** narrowed — so a 2-line body that would fit one line at full width is flagged even though it fits *your* column. `--zone` can't predict this (it only measures single lines). For any block you intend to **wrap in a column**, pass its lines to the checker-parity mode and give the real bound:
  `{"lines":["l1","l2"],"font_size":24,"x":72,"right_bound":<column right edge>}` → `CHECKER_OK` (wrap justified) / `CHECKER_FLAG` (gate will warn). Resolve a FLAG one of three ways: **(a)** draw it as one line (shorten the copy to fit the column), **(b)** add a vertical divider / right-edge shape spanning the block's y-band so the checker bounds the column (then it's OK even wrapped), or **(c)** split it into **separate `<text>` paragraphs** (each is its own single-line block, no wrap detected).

## 5. Color / icons (from the lock only)
- Fill/stroke/stop MUST be `spec_lock.colors` values. `fill="transparent"` = no paint; use color+alpha for a painted translucent layer.
- Icons: `<use data-icon="<library>/<name>" x y width height fill="#HEX"/>` — library = `spec_lock.icons.library` (one library, no mixing), name ∈ `inventory`. **Always `fill="#HEX"`; never `stroke`/`fill="none"`.** Verify a name exists: `ls ${SKILL_DIR}/templates/icons/<library>/ | grep <kw>`.

## 6. Banned SVG (export aborts / strips)
`mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`/`<set>`, `<script>`/event attrs, `<iframe>`. No `clip-path` except on `<image>` (single supported shape). No filter on `<image>` or on a multi-element `<g>`. Shadows/glow: one `feDropShadow`/`feGaussianBlur` on `<rect>/<circle>/<path>/<text>`, single light direction per page — reach for it only on genuinely floating elements (editorial: mostly flat).

## 7. Rhythm (breaks the "AI card-grid" look)
- Read each page's `page_rhythm` tag. `anchor` = structural (cover/section/TOC/ending). `dense` = grids/columns/lists OK. `breathing` = **no multi-card grid** — naked text, dividers, whitespace, or full-bleed; single rounded elements are fine.

## 8. Per-page + milestone gate
- After P01, then after every 4th page (P04, P08…), and once on the whole project:
  `python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project>`
- Fix every `error`. Disposition each `text geometry:` warning (fix, or state the intended balanced break). Clean block = silent pass.

## 9. Then export (SKILL.md Step 7 owns it)
- No notes → skip 7.1. finalize (7.2) deferred by default. Export: `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project>`. Verify: `verify_deck.py <project> --no-render` + `unzip -t`.

---

**Layout skeletons:** [`layout-archetypes.md`](./layout-archetypes.md) has fill-in SVG for cover/closing poster, numbered list, two-column activity, horizontal steps, and breathing pull-quote — instantiate those instead of re-deriving geometry per new pattern.
