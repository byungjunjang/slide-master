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

## 1. Preconditions

| Requirement | Check |
|---|---|
| Downloads land silently (optional) | With `gemini.google.com` allowed under the browser's automatic-downloads setting, images arrive at original size. Without it the run still completes through the canvas fallback at the displayed size |
| WebBridge daemon | `curl -s -m 5 -X POST http://127.0.0.1:10086/command -d '{"action":"list_tabs","args":{},"session":"ppt-master-images"}'` returns `"ok":true` |
| Gemini signed in | The account chip renders on `gemini.google.com`; a signed-out page has no prompt box |
| Manifest | Valid `image_prompts.json` with at least one non-`Generated` row |

Stop and tell the user which precondition failed. Do not fall back to another
image path from inside this skill — that decision belongs to the caller.

---

## 2. Run

```bash
python3 .claude/skills/gemini-web-image/scripts/gemini_web_image.py \
  --manifest projects/<name>/images/image_prompts.json
```

| Flag | Meaning | Default |
|---|---|---|
| `--manifest` | Path to `image_prompts.json` | — |
| `--output` / `-o` | Output directory | Manifest's folder |
| `--batch` | Rows submitted in one pass | `8` |
| `--settle` | Seconds to wait per conversation for its image | `180` |
| `--collect-only` | Skip submission; collect conversations already open | off |
| `--url` | Collect one conversation URL (repeatable) | — |

The script is idempotent: only rows that are not `Generated` are submitted, and
each saved file is written back to the manifest immediately, so an interrupted
run keeps everything it finished.

Announce the tab group once — this task's pages collect under one group and are
closed only when the user asks.

---

## 3. Rules that the browser path forces

These are not preferences. Each one is a failure that has already happened.

| Rule | Why |
|---|---|
| Drive `gemini.google.com/images`, never `/app` | The image surface runs Nano Banana 2 and accepts a bare prompt. The chat surface may answer with text instead of an image |
| Put the ratio in the prompt's first line | The page exposes no aspect-ratio control. `Generate a 16:9 image (aspect ratio exactly 16:9).` returned 1024x572; the same form with 4:3 returned 1024x765 |
| **Never use `find_tab`** | It returns `"ok": true` without switching tabs, so every later read hits one page and writes that one image under every file name. Move a single tab with `navigate` instead |
| Identify a conversation by its prompt text | Position mapping breaks the moment an unrelated conversation is open. Match `fingerprint(prompt)` against the page's own text |
| Try the page's download control first | `원본 크기 이미지 다운로드` hands over the original file — 2752x1536 where the rendered copy is 1024x572 — so it is always worth one attempt |
| Treat a click on it as unproven until a file lands | The click reports success even when the browser refuses the download. Only a new `~/Downloads/Gemini_Generated_Image_*` proves anything; after roughly 20 seconds, fall through |
| Fall back to reading the rendered image through a canvas | `fetch()` on the blob fails from the bridge's isolated world, but `drawImage` then `toDataURL` works and needs nothing from the browser's download machinery. The data URL runs past 300k characters, so slice it in ~120k pieces |
| Scroll the image into view before judging it ready | The result carries `loading="lazy"` and decodes only inside the viewport. Polling without scrolling reports `naturalWidth` 0 for an image that is perfectly fine — that reading is what made a working conversation look dead |
| Submit every row first, then collect | Generation takes about two minutes; submission takes about seven seconds. Overlapping the waits is the entire speed argument for this path |
| Send the bridge body as a file | An inlined JSON body loses non-ASCII prompt text and breaks on quoting |
| Click the send button, do not press Enter | The bridge has no key-press tool, and the button only renders after the box holds text |
| Dismiss the onboarding dialog | A first visit shows `사용해 보기` over the prompt box |

---

## 4. Verify before reporting success

1. Every row the caller asked for reads `Generated`, and the file exists.
2. Each file's ratio is within 4% of its row's `aspect_ratio`. The script prints
   `** ratio off` when it is not; that row needs a resubmit, not a note.
3. No two output files share a checksum. Identical files mean tab switching
   failed and the run must be redone.
4. `~/Downloads` holds no leftover `Gemini_Generated_Image_*`; each one is moved
   into the project, not copied.

```bash
shasum -a 256 projects/<name>/images/*.png | awk '{print substr($1,1,12), $2}' | sort
```

---

## 5. When a row does not come back

| Symptom | Action |
|---|---|
| `naturalWidth` stays 0 | The image is outside the viewport and has not lazily decoded. Scroll it into view and keep polling — do not conclude the conversation is dead |
| No download button in the snapshot | The answer is still rendering. Keep polling; it appears with the finished image |
| Download refused every time | Expected on a browser that blocks automatic downloads. The canvas fallback covers it; report the smaller size rather than stalling |
| Prompt box never appears | The page is signed out or still loading. Report the precondition failure |
| A conversation's text matches no manifest row | Someone else's conversation is open. Skip it — never guess |

Rows this skill cannot finish stay `Pending` with `last_error` set. Hand them
back to the caller; the manifest is the record.
