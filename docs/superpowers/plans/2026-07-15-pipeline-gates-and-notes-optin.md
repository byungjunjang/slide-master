# Pipeline Gates + Speaker-Notes Opt-in

> Implementation plan, 2026-07-15. Selective adoption from the sibling `slide-svg` pipeline,
> filtered by two constraints: (1) must not lengthen deck-generation wall-clock,
> (2) must not rewire the upstream ppt-master flow — additive scripts and minimal doc touches only.

## Motivation

- Generation runs are long; the dominant time loss is **rework** (bad outline discovered after
  20 pages, broken export discovered by the user) and **mid-run environment death**
  (missing dep at Step 5/7 after a 40-minute run).
- Speaker-notes generation is the only default-on, every-run feature with real per-page cost
  that the repo owner does not use. Export already tolerates a missing `notes/`
  (`svg_to_pptx/pptx_package/discovery.find_notes_files` returns empty; `--no-notes` exists),
  so this is a prompt-layer change only.

## Scope (4 items)

### 1. Speaker notes → opt-in (default OFF)

Contract: notes are generated only when the user explicitly requests speaker notes /
narration / audio / video export. `design_spec.md §X` records the decision
("None requested" default). No script changes.

Touch points:

| File | Edit |
|---|---|
| `SKILL.md` | Step 6 Logic Construction conditional; Step 6 checkpoint; Step 7 GATE; Step 7.1 conditional; Step 7.3 comment |
| `references/strategist.md` | §1 Speaker Notes Requirements → opt-in; §6.2 row X conditional |
| `references/executor-base.md` | §8 gate line; Logic Construction step line |
| `templates/design_spec_reference.md` | §X opt-in note + default |
| `references/artifact-ownership.md` | notes rows marked opt-in |
| `workflows/generate-audio.md` | fallback: no notes yet → generate per executor-base §8, split, continue |
| `CLAUDE.md` | quick-reference comment on `total_md_split.py` |

### 2. `scripts/preflight.py` (new)

Pre-pipeline environment gate, run once after Step 2 (recommended). FAIL: `python-pptx`,
`Pillow` missing. WARN: `flask` (Confirm UI/live preview have chat fallback), `numpy`,
Pretendard not installed, `IMAGE_BACKEND` unset under `--needs-images` (Path B host-native
still works), `officecli` absent. `--strict` promotes warnings.

### 3. `scripts/validate_spec.py` (new)

Machine gate for the planning artifacts, run right after Strategist writes
`design_spec.md` + `spec_lock.md`. Checks: §IX pages parse + per-page core message
(cover/chapter/closing exemptions), Cover impact presence (warn), `page_rhythm`
coverage + enum, colors/typography/mode/visual_style presence, `pptx_structure`
flat/structured section rules, `page_charts` ⊆ charts_index + §VII, §VII template names
+ verbatim summary-quote audit against `templates/charts/charts_index.json`.
Errors exit non-zero. Tuned against the three real projects in `projects/`.

### 4. `scripts/verify_deck.py` (new)

One-command final gate after Step 7 (recommended, non-numbered so the canonical
7.1–7.3 pipeline wording stays intact): svg_output/svg_final parity + freshness,
native PPTX zip integrity + per-slide editable DrawingML + slide count, canvas lock
(`project_meta.json` × `CANVAS_FORMATS`), subprocess `svg_quality_checker` +
`validate_spec`, placeholder-image suspects (WARN, alpha-skipped), notes mapping (WARN),
and optional OfficeCLI OpenXML validation + contact-sheet grid render to
`_pptx_render/<stem>-grid.png` (auto-skip when absent; `OFFICECLI_BIN` override,
same contract as slide-svg).

## Explicitly rejected (reviewed, not adopted)

- `slide-plan`/`ppt-plan` skill port — duplicates Step 4 Strategist; schema non-portable.
- `theme-init` baking — collides with Confirm UI free-design identity.
- Eight-Confirmations chat flow — Confirm UI supersedes it.
- Full speaker-notes removal — breaks generate-audio / native narration; opt-in keeps both.
- No other default-on feature has per-run cost: animations, narration, visual-review,
  verify-charts, formula rendering, refine-spec, split-mode are already conditional/opt-in.

## Verification

- Smoke-run all three scripts on this machine against `projects/20260714_ai_agent_adoption`
  (has full svg_output/svg_final/exports) and the other two real projects for validate_spec.
- No automated tests (repo convention: docs/rules/code-style.md §11).
