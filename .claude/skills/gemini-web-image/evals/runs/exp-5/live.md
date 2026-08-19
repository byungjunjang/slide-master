# Live check — exp-5

Run 2026-08-20 01:41:29–01:46:01 against a ten-row manifest built from the
`20260819_wsl-resin-infiltration` deck's own prompts, writing to a scratch
directory so the deck's images were not touched. Default flags, `--deadline 300`.

## Result

**10/10 saved, every row at the original size, 272s — inside the 300s deadline.**

| Phase | Measured |
|---|---|
| Submission, ten rows | 101s (~10s per row, jittered gaps included) |
| Settle before the first sweep | 10s |
| First image saved | 13s after the first sweep began |
| Per-row download | 13–18s |
| Nine rows saved by | 125s into collection (sweep 2) |
| Last two rows | sweep 3, 147s and 161s |
| Total | 272s |

Verification, all five checks in §5: ten `Generated` rows with no `slot` and no
`last_error`; 2752x1536 for every 16:9 row and 2048x2048 for every 1:1 row; ten
distinct checksums; no file at the 1024px canvas size; `~/Downloads` clean. The
ten slot tabs were closed afterwards and `list_tabs` confirmed zero remaining.

## What this run establishes

- **Ten originals fit the five-minute budget.** The previous figure was
  extrapolated from a two-row run plus a ten-row run on older code; this is the
  first end-to-end measurement of the current script.
- **The ratio line is no longer doubled.** All ten prompts already opened with
  their ratio sentence, and none was sent twice.
- **No row fell back.** The `**` fallback warning did not print, which is the
  pass condition for §5's resolution check.

## What it exposed

**The `finished` clock never fired.** Not one save carried a `gemini done at`
note, so every row was read as decoded before it was ever seen as finished. The
probe computes `finished = present && !creating`, and the page apparently keeps
"Creating your image" in the DOM past the point where the image is readable. The
two-clock instrumentation therefore reports nothing on a healthy run, which is
the case where it is least needed but also the case that would have proved it
works. It has not been shown to attribute a slow row correctly — treat that
claim in §5.1 as untested until a slow row actually produces the note.
