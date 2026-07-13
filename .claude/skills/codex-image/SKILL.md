---
name: codex-image
description: |
  Generate images via Codex CLI's built-in image_gen tool (gpt-image-2). OAuth auth — no API key needed.
  Codex CLI의 내장 image_gen 도구로 이미지 생성. OAuth 인증으로 API 키 불필요.
  Usage: /codex-image cherry blossom hanok, /codex-image --size 1024x1536 space cat, /codex-image --quality high seoul night
argument-hint: "[--size <WxH>] [--quality low|medium|high] [--out <path>] [--filename <name>] [-n <count>] <image prompt>"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# codex-image — AI Image Generation via Codex OAuth

Generate images using OpenAI's `gpt-image-2` model through Codex CLI.
**No API key required** — uses Codex OAuth (ChatGPT login) authentication.

OpenAI Codex CLI의 내장 `image_gen` 도구를 통해 `gpt-image-2` 모델로 이미지를 생성한다.
**API 키 불필요** — Codex OAuth(ChatGPT 로그인) 인증 사용.

## How it works / 동작 원리

```
User prompt → Claude Code (/codex-image)
  → codex exec (OAuth token auto-managed)
    → built-in image_gen tool (gpt-image-2)
      → ~/.codex/generated_images/<session>/
        → copy to project root
```

> **Important**: OAuth tokens cannot call OpenAI REST API directly (returns 401).
> Must go through `codex exec` which handles auth internally.
>
> OAuth 토큰으로 OpenAI REST API 직접 호출 불가 (401 반환).
> 반드시 `codex exec` 경유 — Codex가 내부적으로 인증 처리.

---

## Step 1 — Verify Codex CLI & Auth / Codex CLI 및 인증 확인

```bash
which codex 2>/dev/null && codex --version 2>/dev/null || echo "NOT_FOUND"
```

If `NOT_FOUND`, stop:
> "Codex CLI not installed. Run `npm install -g @openai/codex` then `codex login`."
> "Codex CLI 없음. `npm install -g @openai/codex` 후 `codex login` 실행해."

```bash
codex login status 2>&1
```

If not "Logged in":
> "Codex login required. Run `codex login` in terminal. OAuth login enables image generation without API key."
> "Codex 로그인 필요. 터미널에서 `codex login` 실행. OAuth 로그인하면 API 키 없이 이미지 생성 가능."

## Step 2 — Parse Arguments / 인자 파싱

Extract from `$ARGUMENTS`:

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--size` | `1024x1024`, `1024x1536`, `1536x1024`, `auto` | `1024x1024` | Image dimensions / 이미지 크기 |
| `--quality` | `low`, `medium`, `high`, `auto` | `auto` | Generation quality / 생성 품질 |
| `--out` | directory path | project root | Save location / 저장 위치 |
| `--filename` | name without extension | `codex-image-<timestamp>` | Output filename stem / 출력 파일명 (확장자 제외) |
| `-n` | 1–10 | `1` | Number of images / 생성 장수 |

Remaining text → image prompt / 나머지 텍스트 → 이미지 프롬프트

If prompt is empty, ask via AskUserQuestion:
> "What image should I generate? Enter a prompt."
> "어떤 이미지를 생성할까? 프롬프트를 입력해줘."

## Step 2.5 — Background normalization (avoid the transparency checkerboard) / 배경 정규화

> **Known `gpt-image-2` failure mode.** When a prompt asks for a `transparent background`,
> `gpt-image-2` does NOT return true alpha — it **paints a literal gray-and-white
> checkerboard** (the pattern editors use to *display* transparency) into the RGB pixels.
> The result looks broken on any real backdrop. This skill therefore never passes a
> transparency request straight through.
>
> **알려진 `gpt-image-2` 버그.** 프롬프트가 `transparent background`를 요청하면 실제 알파
> 투명도가 아니라 **회색·흰색 체커보드 무늬를 픽셀로 그려 넣는다**(편집기가 투명도를 *표시*할
> 때 쓰는 격자). 어떤 배경에 올려도 깨져 보인다. 그래서 이 스킬은 투명 요청을 그대로 넘기지 않는다.

Strip transparency phrasing from the prompt before generating (the Step 4 task carries a
hard background rule as a second guard, so this is belt-and-suspenders):

```bash
# Neutralize "transparent background" / "transparent bg" / "no background" so the model
# does not bake a checkerboard. Caller-named backdrop colors (e.g. "#FAFAF9 background",
# "white background") are kept and become the clean solid fill.
_PROMPT=$(printf '%s' "${_PROMPT}" \
  | sed -E 's/(fully |truly )?transparent[ -]+(background|bg)/clean solid background/Ig' \
  | sed -E 's/\bno background\b/clean solid background/Ig')
```

If the user genuinely needs a cut-out asset, tell them `gpt-image-2` (via the codex
`image_gen` tool) cannot emit reliable alpha; generate on a **flat solid color** and remove
the background afterward with an image editor. Do NOT request "transparent" to get it.

## Step 3 — Determine Save Path / 저장 경로 결정

```bash
_PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
_OUT_DIR="${_PROJECT_ROOT}"
_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
# --filename takes precedence; fall back to timestamp stem
_FILENAME="${_FILENAME_ARG:-codex-image-${_TIMESTAMP}}"
```

- If `--out` specified, use that path / `--out` 지정 시 해당 경로 사용
- If `--filename` specified, that stem is used as-is / `--filename` 지정 시 해당 stem 그대로 사용
- Single image (default stem): `codex-image-<timestamp>.png`
- Single image (`--filename foo`): `foo.png`
- Multiple (`-n > 1`): `<stem>-1.png`, `<stem>-2.png`, ...
- Never overwrite existing files / 기존 파일 덮어쓰기 금지 (named outputs included — 같은 `--filename`을 다시 쓰려면 기존 파일을 먼저 지우거나 `--out`을 바꿔야 함)

## Step 4 — Generate Image / 이미지 생성

```bash
codex exec "Perform the following tasks:
1. Use the built-in image_gen tool to generate an image.
2. Prompt: '${_PROMPT}'
3. Background rule (MUST follow): the image must have a clean, single solid flat background. NEVER paint a transparency/alpha checkerboard — i.e. no alternating gray-and-white squares anywhere. If the prompt implies a 'transparent' or 'no' background, render a clean solid background of the nearest plain color instead (use the backdrop color named in the prompt if any, otherwise plain white).
4. Size: ${_SIZE}
5. Quality: ${_QUALITY}
6. Count: ${_N}
7. Copy the generated image to '${_OUT_DIR}/${_FILENAME}.png'. For multiple images use -1.png, -2.png suffix.
8. Print the saved file path and size." \
  -C "${_PROJECT_ROOT}" \
  -s workspace-write \
  -c 'model_reasoning_effort="medium"' \
  --skip-git-repo-check \
  2>&1
```

timeout: 120000ms (2 min)

### Required flags / 필수 플래그

- `-s workspace-write` — file write permission / 파일 쓰기 권한
- `--skip-git-repo-check` — works outside git repos / git 레포 외부에서도 실행 가능

### Internal flow (Codex side) / 내부 동작 흐름

1. Codex calls built-in `image_gen` tool (gpt-image-2)
2. Image saved to `~/.codex/generated_images/<session-id>/ig_*.png`
3. Codex copies file to specified project path
4. Reports file path and size

## Step 5 — Display Result / 결과 출력

```
═══════════════════════════════════════════════
IMAGE GENERATED / 이미지 생성 완료
═══════════════════════════════════════════════
Prompt: <prompt used>
Size: <size>
Quality: <quality>
Count: <n>
Auth: OAuth (ChatGPT)
───────────────────────────────────────────────
<saved file path(s)>
═══════════════════════════════════════════════
```

**Always display the generated image using the Read tool.**
**생성된 이미지를 반드시 Read 도구로 표시한다.**

## Step 6 — Follow-up / 후속 안내

- "Run `/codex-image` again to generate another image."
- For Next.js projects: suggest moving to `public/images/` if needed.
- **ppt-master integration**: this project's PPT pipeline generates images through `image_gen.py --manifest` whose default backend `codex` (`scripts/image_backends/backend_codex.py`) uses the same `codex exec` + `image_gen` mechanism as this skill — no API key or `.env` needed, only `codex login`. Use `/codex-image` directly for one-off images outside the pipeline (e.g. re-rolling a single asset with `--out <project>/images --filename <slot>`). / ppt-master 파이프라인은 `image_gen.py --manifest`의 기본 백엔드 `codex`로 이미지를 생성하며, 이 스킬과 동일하게 `codex exec`를 사용한다 (API 키·`.env` 불필요, `codex login`만 필요). 파이프라인 밖에서 단발 이미지가 필요할 때 `/codex-image`를 직접 사용.

## Error Handling / 에러 처리

| Error | Message |
|-------|---------|
| Auth expired | "Codex OAuth expired. Run `codex login` again." / "OAuth 인증 만료. `codex login` 다시 실행." |
| Model access denied | "No access to gpt-image-2. Check your OpenAI plan." / "gpt-image-2 접근 권한 없음. OpenAI 플랜 확인." |
| Timeout (>2min) | "Generation timed out. Try `--quality low`." / "생성 시간 초과. `--quality low`로 재시도." |
| Rate limit | "API rate limited. Wait and retry." / "API 호출 제한. 잠시 후 재시도." |
| Trust error | Check `--skip-git-repo-check` flag or add project to `~/.codex/config.toml` |

## Rules / 규칙

- Always use the Read tool to display generated images / 생성된 이미지는 반드시 Read로 표시
- Never overwrite existing files — always use timestamped filenames / 기존 파일 덮어쓰기 금지
- OAuth only — do not attempt direct REST API calls with OAuth token (returns 401) / OAuth 토큰으로 REST API 직접 호출 금지
- Verify prompt intent before generating / 생성 전 프롬프트 의도 확인
