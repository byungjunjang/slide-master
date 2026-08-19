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
| `--batch` | Rows submitted in one pass, one tab each | `8` |
| `--generate-wait` | Seconds to let the batch generate before reading | `150` |
| `--settle` | Extra seconds to wait per slot | `300` |
| `--collect-only` | Skip submission; read the slots already open | off |

Idempotent: only rows that are not `Generated` are taken, and each saved file is
written back to the manifest immediately, so an interrupted run keeps what it
finished. Tell the user once that this task's pages collect under a tab group,
and leave them open until the user asks otherwise.

---

## 4. Rules the browser path forces

Each of these is a failure that already happened, not a preference.

| Rule | Why |
|---|---|
| Drive `gemini.google.com/images`, never `/app` | That surface runs the image model and takes a bare prompt. The chat surface may answer with text |
| Put the ratio in the prompt's first line | The page exposes no aspect-ratio control. `Generate a 16:9 image (aspect ratio exactly 16:9).` returned 2752x1536; the 4:3 form returned 2400x1792 and 1:1 returned 2048x2048 |
| **Never use `find_tab`** | It returns `"ok": true` without switching tabs. A collection loop built on it wrote one image under four different file names |
| **Never navigate a slot after submitting** | The tab already holds the finished image. Re-opening the conversation is what makes it slow to decode or bounce to `/app` |
| Try the page's download control first | `원본 크기 이미지 다운로드` hands over the original file rather than the displayed copy |
| Treat that click as unproven until a file lands | It reports success even when the browser refuses the download. Only a new `~/Downloads/Gemini_Generated_Image_*` proves anything; after ~20s, fall through to the canvas readback |
| Scroll the image into view before judging it ready | The result carries `loading="lazy"` and decodes only inside the viewport. Polling it off-screen reports `naturalWidth` 0 for a healthy image |
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
4. `~/Downloads` holds no leftover `Gemini_Generated_Image_*`.

```bash
shasum -a 256 projects/<name>/images/*.png | awk '{print substr($1,1,12), $2}' | sort
```

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
| `naturalWidth` stays 0 | The image is outside the viewport and has not lazily decoded. Scroll it into view and keep polling |
| No download button in the snapshot | The answer is still rendering. Keep polling; it appears with the finished image |
| Download refused every time | Expected where the browser blocks automatic downloads. The canvas fallback covers it at the displayed size |
| Still nothing after `--settle` | Leave the row `Pending` with `last_error` and resubmit it in the next pass |

Rows this skill cannot finish stay `Pending`. Hand them back to the caller; the
manifest is the record.
