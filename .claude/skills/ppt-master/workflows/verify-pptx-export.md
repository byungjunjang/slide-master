---
description: Post-export PPTX verification via OfficeCLI — package schema validation, issue scan, and rendered-slide visual pass
---

# Verify PPTX Export Workflow

> Standalone post-export step. Runs OfficeCLI against an exported `.pptx` to catch what SVG-stage checks cannot see: package-level schema violations, text overflow in native frames, broken part references, and SVG-to-DrawingML conversion drift. Explicit-request only.

This workflow is **independent**: it reads `<project>/exports/<file>.pptx` (plus `svg_final/` for comparison when the deck came through the SVG pipeline) — no upstream conversation context required. Safe to invoke in a fresh session.

## When to Run

- The user explicitly asks to verify / QA / check an exported PPTX.
- An export exists under `<project>/exports/` — from main pipeline Step 7.3, `template-fill-pptx`, `native-enhance-pptx`, or `beautify-pptx`.

## When NOT to Run

- No exported PPTX exists yet — finish the export first.
- The user wants a pre-export SVG check — that is [`visual-review`](./visual-review.md) / [`verify-charts`](./verify-charts.md) territory.
- Do not auto-invoke after every export; run only on explicit request.

---

## Prerequisites

OfficeCLI, installed as a pinned version (verified with `1.0.135`):

```bash
npm install -g @officecli/officecli@1.0.135
officecli --version
```

**Missing OfficeCLI** → state the install command and stop this workflow. Do not substitute a different checker.

**Render path contract** (`view screenshot`):

| Environment | Behavior | Trust level |
|---|---|---|
| Windows with PowerPoint installed (default `--render auto`) | Drives native PowerPoint | Ground truth — pixels are what PowerPoint shows |
| No Office available (`--render html` fallback) | OfficeCLI built-in HTML engine | High fidelity; apply the Step 3 known-deviation table |

---

## Step 1: Package Validation

```bash
officecli validate "<project>/exports/<file>.pptx"
```

| Result | Action |
|---|---|
| No errors | Record pass, continue |
| Schema errors in a known-benign class (e.g. negative chart `axId` failing `UInt32` — python-pptx-lineage chart parts; PowerPoint tolerates it) | Record the exact error text as tolerated, continue |
| New / unclassified schema errors | Render Step 3 first; if content is intact, record as tolerated with the exact error text; if parts fail to render, treat as an export failure and route the fix upstream (Step 4) |

> Note: `validate` is stricter than PowerPoint. A schema error is a triage signal, not an automatic failure.

---

## Step 2: Issue Scan

```bash
officecli view "<project>/exports/<file>.pptx" issues --json
```

Detects per-frame text overflow with measured need-vs-usable heights and a suggested frame height, plus pptx subtypes `low_contrast`, `slide_field_not_evaluated`, `notes_unresolved_rid`, `broken_part_ref`.

| Finding | Action |
|---|---|
| Text overflow on a content frame | Real defect — route upstream (Step 4) |
| Overflow on an intentionally overlapping decorative element | Judge; record accepted findings in the final report |
| `broken_part_ref` / `notes_unresolved_rid` | Package defect — route upstream (Step 4) |

---

## Step 3: Rendered-Slide Visual Pass

```bash
officecli view "<project>/exports/<file>.pptx" screenshot --page 1-<N> \
  -o "<project>/validation/pptx_render/deck.png"
# per page: --page <k> -o .../p<k>.png ; whole-deck contact sheet: --grid
```

Read the rendered output and check every page:

| Check | Signal |
|---|---|
| Text wrap / overflow | Lines break outside frames, truncated paragraphs |
| Fonts | Pretendard renders; tofu boxes mean font substitution |
| Images / icons | No blank rectangles or missing assets |
| Charts / tables (`--native-objects` exports) | Data, labels, and geometry match the authored page |

| Deck route | Compare against |
|---|---|
| SVG pipeline export (`svg_output/` route) | `svg_final/<page>.svg` design intent, page by page |
| `template-fill-pptx` / `native-enhance-pptx` | Source deck design — unchanged pages must look unchanged |

**Known HTML-engine deviations** (only under `--render html`) — never report these as export defects:

| Deviation | Detail |
|---|---|
| Wrap points | Line breaks may shift by roughly one character vs PowerPoint |
| Chart legend | Legend placement / plot width may differ from PowerPoint's internal chart layout |
| Date / slide-number placeholders | HTML engine renders master placeholders that PowerPoint hides |

---

## Step 4: Route Fixes Upstream

**Hard rule**: never patch `<project>/exports/*.pptx` in place. Exports are derived artifacts; fix the owning source and re-export.

| Deck route | Fix location | Re-export |
|---|---|---|
| Main SVG pipeline / beautify | `svg_output/<page>.svg` | `SKILL.md` Step 7.2–7.3 (`finalize_svg.py`, then `svg_to_pptx.py`) |
| `template-fill-pptx` | `fill_plan.json` (shorten text, re-pick page) | template-fill Step 6–7 |
| `native-enhance-pptx` | Enhancement plan / config | native-enhance apply + validate |

Re-run this workflow after re-export until no unaccepted findings remain.

```markdown
## ✅ PPTX Export Verification Complete

- [x] `officecli validate` run; every error triaged (pass, or tolerated with recorded reason)
- [x] `issues --json` run; overflow / package findings fixed upstream or explicitly accepted
- [x] All pages rendered to `<project>/validation/pptx_render/` and checked against the route's reference
- [x] Fixes (if any) applied upstream and re-exported; no direct `exports/` patching
```
