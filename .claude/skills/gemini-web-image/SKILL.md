---
name: gemini-web-image
description: >
  Generate an image_prompts.json manifest's ai rows through the Gemini web app,
  driven by the Kimi WebBridge daemon and the user's signed-in browser. Use on a
  host that has a Gemini subscription but no usable keyless CLI image path —
  agy's image allowance is spent, or codex is unavailable. Do not use when
  image_gen.py can run a CLI or API backend; those are faster and need no
  browser.
---

# Gemini Web Image

> Fallback image path for the ppt-master manifest contract. Reads
> `images/image_prompts.json`, writes `images/<filename>`, and sets each row's
> `status` — the same contract [`image_gen.py`](../ppt-master/scripts/image_gen.py)
> honors, so Step 6 needs no change.

**Trigger**: a manifest with `Pending` / `Failed` `ai` rows on a host where no
CLI or API backend can run, and the browser is signed in to Gemini.

---

## 1. The one idea this skill rests on

**One bridge session per row.** The bridge scopes its "current tab" to the
session name, so a session is a handle on one tab that nothing else can move.
Give row *n* the session `ppt-master-image-n` and that row owns a tab for the
whole run.

Everything else follows from it. Submit every row into its own tab, wait once
for the batch, then read each tab exactly where it stands. Nothing navigates,
nothing reloads, and which tab holds which row is the slot number — not
something to infer from URLs or page text.

**The slot is 0-based and the session name is 1-based.** The manifest stores
`slot: 0` for the first row and its tab is `ppt-master-image-1`; row *n*'s
session is `ppt-master-image-<slot + 1>`. Reading the number off a tab group's
title and using it as a slot points one row too far.

Sharing one tab across rows is what makes this path fail. Every reload
re-fetches an image that then decodes slowly or not at all, the SPA sometimes
answers a conversation URL with `/app`, and `list_tabs` starts reporting the
moved tab's new URL instead of the conversation it used to hold.

---

## 2. Preconditions

| Requirement | Check |
|---|---|
| WebBridge daemon | `list_tabs` on any session returns `"ok": true` |
| Gemini signed in | The account chip renders on `gemini.google.com`; a signed-out page has no prompt box |
| Browser UI in Korean | Elements are found by accessible name, and the names this skill matches are Korean. There are five: `Gemini 프롬프트 입력` (the prompt box), `메시지 보내기`, `사용해 보기`, `원본 크기 이미지 다운로드`, and the viewer's `닫기`. Another UI language needs all five re-read from a live page first — do not guess them |
| Manifest | Valid `image_prompts.json` with at least one non-`Generated` row |
| Downloads land silently (optional) | With `gemini.google.com` allowed under the browser's automatic-downloads setting, images arrive at original size; without it the canvas fallback still finishes the run at the displayed size |

Stop and name the failed precondition. Do not fall back to another image path
from inside this skill — that decision belongs to the caller.

---

## 3. Run

```bash
python3 .claude/skills/gemini-web-image/scripts/gemini_web_image.py \
  --manifest projects/<name>/images/image_prompts.json
```

| Flag | Meaning | Default |
|---|---|---|
| `--manifest` | Path to `image_prompts.json` | — |
| `--output` / `-o` | Output directory | Manifest's folder |
| `--batch` | Rows submitted in one pass, one tab each | `10` |
| `--generate-wait` | Seconds to settle before the first sweep | `10` |
| `--deadline` | Hard wall-clock budget for the whole run | `300` |
| `--displayed-size` | Keep the 1024px canvas copy instead of downloading the original; the viewer is never opened and the `**` fallback warning is suppressed, because the smaller file was asked for | off |
| `--collect-only` | Skip submission; read the slots already open | off |

Collection sweeps every slot repeatedly rather than waiting on each in turn, and
polls all of them concurrently, so the interval really is the detection latency.
A slot that is still generating is skipped and looked at again next sweep.

`--deadline` is the whole run's wall clock — submission, generation, and
download together — measured from process start. It exists so a run can fail
loudly at five minutes instead of quietly dragging to twenty. When it expires,
unfinished rows stay `Pending` with their `last_error` set.

Generate the whole set in one pass. Concurrency shows no per-image penalty
(§5.1), so splitting a deck into passes only repeats the ~48s submission cost.
Ten rows fit the deadline comfortably at the displayed size (245s measured) and
only barely at the original size, where the serial download dominates — read
§5.1 before promising a ten-row deck of originals inside five minutes. The one
reason to lower `--batch` is Google's unusual-traffic challenge (§7): it has
appeared once after a ten-tab run, it stops everything, and only a person can
clear it.

Idempotent: only `Pending` and `Failed` rows are taken — the same statuses
`image_gen.py` retries — and each saved file is written back to the manifest
immediately, so an interrupted run keeps what it finished. `Needs-Manual` rows
belong to the user and are never submitted. Re-doing a row that already reads
`Generated` means setting its status back to `Failed` first; no flag does it.

**The tabs pile up, and one group per row is the cost of the isolation.** The
bridge names a Chrome tab group after the session, so ten rows leave ten groups
titled `agent:ppt-master-image-N` — not one shared group. Sessions cannot be
merged without merging the tabs, which is the failure §1 exists to prevent. Say
this once at submit time so the clutter is expected, and offer to clear it when
the run is done: `close_tab` on each slot session removes the tab and its group.
Do not close them before every row is `Generated` — a `--collect-only` rerun
needs those tabs.

---

## 4. Rules the browser path forces

Each of these is a failure that already happened, not a preference.

| Rule | Why |
|---|---|
| Drive `gemini.google.com/images`, never `/app` | That surface runs the image model and takes a bare prompt. The chat surface may answer with text |
| The ratio rides in the prompt's first line, and the script puts it there | The page exposes no aspect-ratio control, so `submit()` prepends `Generate a <ar> image (aspect ratio exactly <ar>).` from the row's own `aspect_ratio`. **The manifest's `prompt` must not carry that line itself** — when it did, the page received the sentence twice. It is added only if missing now, and a prompt whose line names a different ratio is reported rather than silently doubled. Measured: 16:9 → 2752x1536, 4:3 → 2400x1792, 1:1 → 2048x2048 |
| Sweep the slots repeatedly; never block on one | Waiting out a slow row in place spends the budget the others needed, and a single pass never returns — two finished images were reported as failures with the files sitting ready in their tabs |
| **Never use `find_tab`** | It returns `"ok": true` without switching tabs. A collection loop built on it wrote one image under four different file names |
| Write the slot number down at submit time | `--collect-only` runs in a fresh process, and by then some rows are `Generated`. Re-numbering the survivors points them at other rows' tabs — the third row alone becomes slot 0 and saves the first row's image under the third row's name. The submitted row carries `slot` in the manifest, and its tab is `ppt-master-image-<slot + 1>`; a row without a slot is resubmitted, never guessed |
| **Never navigate a slot after submitting** | The tab already holds the finished image. Re-opening the conversation is what makes it slow to decode or bounce to `/app` |
| Open the image before looking for its download control | There is no download button beside the inline result. The result `<img>` sits inside a `<button class="image-button">`; clicking that opens the viewer, and only there do `이미지 공유` / `이미지 복사` / `원본 크기 이미지 다운로드` exist. Every run that skipped this step searched a tree that never had the button and fell back to the canvas copy — 1024px instead of 2752px. Close the viewer afterwards so the next probe sees the page as it was |
| Give the download real time to land | The original is a multi-megabyte PNG and takes 11–17s from click to file. A six-second wait sent every row to the low-resolution fallback while reporting nothing wrong. Only a new `~/Downloads/Gemini_Generated_Image_*` proves the download happened, and it is still growing when it first appears — wait for its size to stop changing. Clear every file newer than the click on both paths, because one click can produce more than one and a partial left behind is read as the next row's file |
| Give up on the download only for the reason you have | A browser that refuses one download refuses them all, so the wait is dropped for the rest of the run — but only a click that produced no file proves refusal. Latching on a viewer that failed to open demoted every later row to 1024px over one bad moment, which is the same silent degradation this rule exists to stop. A viewer that never opened is that row's problem alone |
| Force the decode; scrolling alone is not enough | The result carries `loading="lazy"`, and it is routinely laid out at zero size — `scrollIntoView` on a zero-box element does nothing, so the decode never fires and the row polls until the deadline expires. Set `loading = 'eager'` and call `img.decode()` as well. A 10-row batch stalled four rows on exactly this; three of them were finished images reporting `naturalWidth` 0 |
| Pace the submissions, and stop on a `/sorry/` redirect | Ten tabs opened and ten prompts sent inside 50 seconds tripped Google's abuse detection: a later navigation landed on `https://www.google.com/sorry/index?continue=…`, the anti-bot interstitial. There is no prompt box there, so every submission after it fails with "prompt box never appeared". Do not try to answer the challenge — stop, tell the user, and let them clear it in the browser. Already-generated tabs are unaffected; only new navigations are |
| A conversation URL is not proof the prompt was sent | The send click reports success, the tab reaches `/app/<id>`, and the body stays blank — no image, no "Creating your image", nothing. Require the answer to have *started* before counting the row as submitted, and resend once if it has not |
| Drop a tab that is showing nothing | A slot with neither an image nor the generating state is empty, not slow. Two such rows once spent an entire run's remaining budget. After a short grace period, stop sweeping it and hand it back for resubmission |
| Vary every wait | Fixed intervals are a machine signature, and Google's unusual-traffic challenge followed a run whose every step was metronomic. Submission polls, the gap between rows, and the sweep cadence all jitter |
| Click the send button; do not press Enter | The bridge has no key-press tool, and the button renders only once the box holds text |
| Send every bridge body as a file | An inlined JSON body loses non-ASCII prompt text and breaks on quoting |
| Dismiss the onboarding dialog | A first visit shows `사용해 보기` over the prompt box |

> The thread running through half of these: **this bridge reports success for
> actions it did not perform.** `find_tab`, `click`, and `navigate` all do it.
> Verify the effect — the tab's URL, the file on disk — never the return value.

---

## 5. Verify before reporting success

1. Every requested row reads `Generated` and its file exists.
2. Each file's ratio is within 4% of its row's `aspect_ratio`. The script prints
   `** ratio off` otherwise; that row needs a resubmit, not a footnote.
3. No two output files share a checksum. Identical files mean slot isolation
   broke and the run must be redone.
4. No file is 1024px on its long edge unless `--displayed-size` was asked for.
   Ratio and checksum both pass on a canvas copy, so resolution is the only
   check that catches a run that silently degraded. The run prints a `**` line
   naming every row that fell back; an absent line is the pass.
5. `~/Downloads` holds no leftover `Gemini_Generated_Image_*`.

```bash
shasum -a 256 projects/<name>/images/*.png | awk '{print substr($1,1,12), $2}' | sort
```

### 5.1 Timing — measured

Runs on 2026-08-20, after the decode fix and the viewer-download fix. The
original size is 2752x1536 for 16:9, 2400x1792 for 4:3, and 2048x2048 for 1:1;
the table says which runs got it, because the middle row predates the viewer fix
and did not.

| Rows at once | Submit | Per-row download | Total |
|---:|---:|---:|---:|
| 2 | 21s | 11–12s | **81s** |
| 10 (canvas copy, before the viewer fix) | 48s | — | **245s** |
| 10 (originals, before pacing was trimmed) | 117s | 13–17s | 424s, 8/10 |
| **10 (originals, current script)** | **101s** | **13–18s** | **272s, 10/10** |

**Where the time goes.** Two costs are serial and dominate: submitting a row
(~10s, including proving the send took) and downloading its original (~15s).
That is about 250s of unavoidable serial work for ten rows, and the measured
272s is very close to it — generation itself contributes almost nothing to the
wall clock, because it overlaps the downloads. Nine of the ten rows were ready
before their turn came.

**Ten originals fit five minutes, with about 30s of margin.** That margin is the
whole of it, so a deck larger than ten rows needs a raised `--deadline` rather
than optimism. `--displayed-size` trades the download for the 1024px canvas copy
and buys back about 15s per row when the deadline matters more than the pixels.

**One instrument is not earning its keep.** Across ten rows the `finished` clock
never fired: every row read as decoded before it was ever seen as finished,
because the page keeps "Creating your image" in the DOM past the point where the
image is readable. So the `gemini done at … lag …` note, which exists to prove a
slow row is Gemini's fault rather than ours, has never actually printed. Do not
lean on it until it does.

**The superseded figure.** An earlier ten-row run took 10m29s and appeared to
show Gemini taking 7m24s for its first image. That reading was wrong: its
readiness probe reported finished images as still generating whenever the result
element had no layout box (the bug §4 names), and the six saves clustered into
three sweeps — a detection cascade, not six independent completions. Do not
quote that run. The probe now reports Gemini's clock (`finished`) separately
from ours (`decoded`) and logs the lag, so a slow row can always be attributed.

---

## 6. Checking the skill after a change

The rules above are load-bearing, and each one is a failure that already
happened. [`evals/`](evals/run-harness.md) keeps them honest: seven scenarios,
and a scorer that reads an execution plan for the rules rather than running
anything.

```bash
python3 .claude/skills/gemini-web-image/evals/score.py <dir-of-plans>
```

Run it after editing this file or the script. When a check fails, read the plan
before touching the skill — the check is a pattern match over prose and has been
wrong more often than the skill has.

---

## 7. When a row does not come back

| Symptom | Action |
|---|---|
| `naturalWidth` stays 0 | Check whether the answer is still rendering (the page ends with "Creating your image") or already finished. If finished, the image is laid out at zero size and its lazy decode never fired: set `loading = 'eager'` and call `img.decode()`. Scrolling alone cannot fix a zero-box element |
| No download button in the snapshot | The answer is still rendering. Keep polling; it appears with the finished image |
| Rows land at 1024px | The run says so itself now: a `**` line at the end names every row that fell back. `the browser refused the download` means the click produced no file and the run stopped trying — check the browser's automatic-downloads setting for `gemini.google.com`. A viewer failure is that row alone. **Recovering either costs a hand-edit**: the row saved, so it reads `Generated` and its `slot` was dropped, and `--collect-only` takes neither. Set `status` back to `Failed` and restore `slot` from the run log, or resubmit the row outright |
| `prompt box never appeared` on every row | Check the tab's URL before blaming the UI language. `google.com/sorry/index` means Google served its unusual-traffic challenge; the run cannot continue until a person clears it. A signed-out session and a non-Korean UI look the same from the log, so read the URL |
| Still nothing when the deadline expires | Raise `--deadline`, or re-run with `--collect-only` to sweep the tabs that are still open — they hold their images and nothing has to be regenerated. Do not lower `--batch` on this evidence alone: the one measurement that appeared to show concurrent generations slowing each other down came from the broken readiness probe (§5.1) |

Rows this skill cannot finish stay `Pending`. Hand them back to the caller; the
manifest is the record.
