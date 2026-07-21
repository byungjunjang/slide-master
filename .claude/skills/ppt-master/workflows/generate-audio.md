---
description: Generate per-slide narration audio with AI-recommended voice selection, then optionally re-export PPTX with embedded audio
---

# Generate Audio Workflow

> Standalone post-export step. Run when the user asks for "生成音频" / "录制旁白" / "narrated PPT" / "video export with voice", or proactively offer it after a deck is exported. Produces one audio file per slide via `edge-tts` by default, or a cloud TTS provider (`elevenlabs` / `minimax` / `qwen` / `cosyvoice`) when the user chooses high-quality narration or a cloned voice, then optionally re-exports a video-ready PPTX with audio embedded and per-slide auto-advance timings.

This workflow is **independent**: it reads `notes/*.md` and queries the selected TTS voice catalog — no upstream conversation context required. Safe to invoke in a fresh session.

## When to Run

- `notes/total.md` exists and has been split into per-page files at `notes/*.md` (post-processing Step 7.1 done).
- Default mode: `edge-tts` is installed (`python3 -m pip install edge-tts`).
- The workflow is page-level only: one notes file becomes one audio file. Do not use a single long audio track or attempt automatic long-audio splitting.
- PPT narration assets must be PowerPoint-reliable audio: `m4a` (AAC), `mp3`, or `wav`. The built-in TTS path defaults to `mp3`; provider formats such as `pcm`, `opus`, or `flac` must be transcoded before embedding.
- PowerPoint recorded narration export requires `ffprobe` so slide timings can be written from actual audio duration.
- High-quality cloud mode: provider API key is set before use:
  - ElevenLabs: `ELEVENLABS_API_KEY`
  - MiniMax: `MINIMAX_API_KEY`
  - Qwen: `QWEN_API_KEY` or `DASHSCOPE_API_KEY`
  - CosyVoice: `COSYVOICE_API_KEY` or `DASHSCOPE_API_KEY`
  - Keys may live in the current process environment or the first `.env` found in this order: current working directory, skill directory (e.g. `~/.agents/skills/ppt-master/.env`), clone repo root, `~/.ppt-master/.env`
- The deck is in a single dominant language (mixed-language decks: pick the dominant one — the AI uses judgment, not a heuristic).

If `notes/*.md` are missing but `notes/total.md` exists, run `total_md_split.py <project_path>` first.

If the deck has no notes at all (the default pipeline skips speaker notes unless requested), generate them now: write `notes/total.md` per [`speaker-notes.md`](../references/speaker-notes.md) (reading `design_spec.md §IX` for per-page core messages), then run `total_md_split.py <project_path>`, then continue below.

---

## Step 1: Determine the deck's language

The AI already knows the deck's language from writing the notes. No detection script needed.

- Identify the primary language from the notes content: `zh` / `en` / `ja` / `ko` / etc.
- For mixed-language decks (e.g. Chinese with English technical terms), pick the language the audience will hear most of.
- For Chinese specifically: pick the locale based on context — `zh-CN` (mainland mandarin, default), `zh-TW` (Taiwanese mandarin), or `zh-HK` (Cantonese). Ask the user only if the project context doesn't make it clear.

---

## Step 2: Choose audio backend and pull the voice catalog

Default to **edge** unless the user explicitly asks for a cloud provider / higher-quality cloud narration / a cloned voice.

**edge backend**:

```bash
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py --list-voices --locale <locale>
```

**ElevenLabs backend**:

```bash
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py --provider elevenlabs --list-voices
```

**Cloud providers using explicit voice IDs/names**:

```bash
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py --provider minimax --list-voices
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py --provider qwen --list-voices
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py --provider cosyvoice --list-voices
```

The output is a flat list of all available voices for the selected provider. From this list, the AI picks **3–6 candidates** to recommend, applying these rules:

- **Cover both genders** when both exist for the locale.
- **For edge**: prefer `COMMON_VOICES`-listed voices (curated set inside `notes_to_audio.py`) when the locale has them — they are battle-tested.
- **For ElevenLabs**: prefer voices already present in the user's account; if the user provides a specific `voice_id`, do not override it.
- **For MiniMax / Qwen / CosyVoice**: if the user provides a cloned `voice_id`, use it directly. Do not attempt voice cloning inside the narration workflow.
- **Match the deck's tone** — pick the strongest recommendation based on style:
  - Consultant / data-driven / earnings report → steady male voice (e.g. `zh-CN-YunjianNeural`) or clear female voice (e.g. `zh-CN-XiaoxiaoNeural`)
  - General / teaching / product intro → bright female voice / young male voice (e.g. `zh-CN-XiaoyiNeural` / `zh-CN-YunxiNeural`)
  - Launch event / broadcast → announcer-style male voice (e.g. `zh-CN-YunyangNeural`)
  - English consultant deck → `en-US-GuyNeural` (steady) or `en-US-JennyNeural` (clear)
  - Japanese / Korean → pick from `ja-JP-*` / `ko-KR-*` neural voices, mark gender + tone

For each candidate, write a **one-line description in the user's chat language** covering: gender · tone · typical use. For cloud providers, include the voice name/ID exactly as it must be passed to `--voice-id`.

---

## Step 3: One-shot user interaction (mandatory)

Send a single message to the user that asks all three questions at once and provides a recommended value for each. Do NOT split into multiple rounds.

**Cloned-voice fast path**: if the user mentioned a cloned voice / 克隆音色 / 复刻音色 / "my own voice" along with a `voice_id`, skip the voice-recommendation list — set the provider to whichever the user named (`elevenlabs` / `minimax` / `qwen` / `cosyvoice`), pin the `voice_id` they gave you, and only confirm rate + embed-or-not.

**Message template** (render in the user's chat language):

> Detected the notes' primary language as **<language>** (locale: `<locale>`). Based on the deck's tone (<style>), I recommend:
>
> **Generation mode**: ⭐ recommended `<edge|elevenlabs|minimax|qwen|cosyvoice>` (reason: <one sentence, e.g. "zero setup, reliable generation" or "you asked for high-quality cloud narration">).
>
> **Voice**:
> - **[1] <ShortName>** — <gender · tone · typical use> ⭐ **recommended**
> - [2] <ShortName> — <gender · tone · typical use>
> - [3] <ShortName> — <gender · tone · typical use>
> - [4] <ShortName> — <gender · tone · typical use>
> - [5] <ShortName> — <gender · tone · typical use>
> - Or type any other ShortName from the catalog directly.
>
> **Rate / style settings**: ⭐ recommended `<rate or provider defaults>` (reason: <one sentence, e.g. "2–3 sentences per page reads most naturally at normal speed" or "ElevenLabs default voice settings best preserve the voice's original character">).
>
> **Re-export a PPTX with the audio embedded when done**: ⭐ recommended **yes** (one pass; slide dwell times are set from actual audio durations).
>
> Reply "ok" to take every recommendation, or name what to change (e.g. "voice 2, rate -5%" or "use MiniMax voice_id xxx").

**Recommended-value rules**:
- Generation mode: default `edge`; when the user explicitly wants high-quality cloud narration or supplies a cloud voice ID, pick `elevenlabs` / `minimax` / `qwen` / `cosyvoice` as the user named.
- Voice: pick the Step 2 candidate that best fits the deck's tone.
- Rate: edge default `+0%`; dense notes (>4 long sentences per page) suggest `-5%`; short, punchy notes suggest `+5%`; going outside this range needs a stated reason. Cloud providers stay on provider defaults unless the user explicitly asks to change speed or style.
- Embedding: recommend "yes" by default — unless the user has a customized PPTX they don't want overwritten.

---

## Step 4: Execute (no further interaction)

Run sequentially — do NOT bundle:

```bash
# 1A. Generate audio with edge (default)
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --voice <chosen-ShortName> --rate <chosen-rate>

# 1B. Or generate audio with ElevenLabs
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider elevenlabs --voice-id <chosen-voice-id> \
  --elevenlabs-model eleven_multilingual_v2

# 1C. Or generate audio with MiniMax
# Defaults to the China endpoint; set MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2 for overseas access.
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider minimax --voice-id <chosen-voice-id> \
  --minimax-model speech-2.8-hd

# 1D. Or generate audio with Qwen TTS
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider qwen --voice-id <chosen-voice> \
  --qwen-model qwen3-tts-flash --qwen-language-type Chinese

# 1E. Or generate audio with CosyVoice
python3 .claude/skills/ppt-master/scripts/notes_to_audio.py <project_path> \
  --provider cosyvoice --voice-id <chosen-voice> \
  --cosyvoice-model cosyvoice-v3-flash

# 2. (If user kept embedding) Re-export PPTX with audio embedded
python3 .claude/skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --recorded-narration audio
```

If `notes_to_audio.py` errors with a missing dependency or missing provider API key, fix the prerequisite and re-run — do NOT swallow the error.

`--recorded-narration audio` prepares PowerPoint's recorded timings and narrations: every slide must have a matching supported audio file, every duration must be readable by `ffprobe`, and object animations must not use `--animation-trigger on-click`. Use `after-previous` or `with-previous` for narrated/video export. Narration changes the slide-advance layer only: the resolved page-transition effect remains unchanged, `-t none` remains visually transition-free, and narration advance disables click while using audio duration plus padding. The re-export is saved as `exports/<title>_ver<N>_narrated.pptx`, telling it apart from silent exports.

---

## Step 5: Completion report

Output one summary block listing:

- Number of audio files generated and their location (`<project_path>/audio/*`).
- The provider, voice, and rate/settings actually used.
- (If embedded) the new narrated PPTX path under `<project_path>/exports/`.
- (If skipped embedding) one-line hint on how to embed later: `python3 .claude/skills/ppt-master/scripts/svg_to_pptx.py <project_path> --recorded-narration audio`.
