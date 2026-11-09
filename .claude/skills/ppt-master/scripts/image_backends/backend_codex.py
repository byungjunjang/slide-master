#!/usr/bin/env python3
"""
Codex CLI backend — image generation through Codex's built-in image_gen tool
(gpt-image-2) using ChatGPT OAuth.

No API key and no .env required. Prerequisites:
  npm install -g @openai/codex
  codex login          (ChatGPT OAuth)

OAuth tokens cannot call the OpenAI REST API directly (401); generation must go
through `codex exec`, which handles auth internally and saves images under
~/.codex/generated_images/ before copying them to the requested output path.

Codex sometimes leaves the image in ~/.codex/generated_images/<session-id>/
without copying it. After each `codex exec`, a missing target file triggers a
recovery pass: the session id comes from the CLI output (`session id: ...`) or
from the rollout file under ~/.codex/sessions/ that mentions the target path,
and the newest PNG written to that session folder since the run started is
copied to the target. A recovered image counts as success and is never
regenerated. A "usage limit" reply raises QuotaExhaustedError immediately
(no retry) with the reset time Codex reported. See scripts/docs/image.md.
"""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

if __name__ == "__main__":
    print(__doc__)
    print("Use via: python3 .claude/skills/ppt-master/scripts/image_gen.py \"prompt\" --backend codex")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import json
import os
import re
import shutil
import subprocess
import time

from image_backends.backend_common import (
    QuotaExhaustedError,
    normalize_image_size,
    report_resolution,
    resolve_output_path,
)


DEFAULT_MODEL = "gpt-image-2"

# gpt-image-2 (via codex image_gen) only supports these fixed output sizes.
SIZE_SQUARE = "1024x1024"
SIZE_LANDSCAPE = "1536x1024"
SIZE_PORTRAIT = "1024x1536"

# image_size -> image_gen quality knob
IMAGE_SIZE_TO_QUALITY = {
    "512px": "low",
    "1K": "medium",
    "2K": "high",
    "4K": "high",
}

GENERATION_TIMEOUT_SECONDS = 600
# Hard cap on `codex exec` calls per image, whatever max_retries asks for.
MAX_ATTEMPTS = 2
# Slack for filesystem mtime vs. time.time() when matching files to a run.
MTIME_SLACK_SECONDS = 5

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_SESSION_ID_RE = re.compile(r"session[ _]id[\"']?\s*[:=]\s*[\"']?(" + _UUID + ")", re.IGNORECASE)
_ROLLOUT_ID_RE = re.compile(r"rollout-.*-(" + _UUID + r")\.jsonl$", re.IGNORECASE)
_USAGE_LIMIT_RE = re.compile(r"usage limit", re.IGNORECASE)
_RESET_AT_RE = re.compile(r"try again (?:at|in) ([^.\n\"]+)", re.IGNORECASE)


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))


def _select_size(aspect_ratio: str) -> str:
    """Map a W:H aspect ratio onto the nearest gpt-image-2 fixed size."""
    try:
        w_str, h_str = aspect_ratio.split(":", 1)
        width, height = float(w_str), float(h_str)
    except (ValueError, ZeroDivisionError):
        return SIZE_SQUARE
    if width <= 0 or height <= 0:
        return SIZE_SQUARE
    if width > height:
        return SIZE_LANDSCAPE
    if width < height:
        return SIZE_PORTRAIT
    return SIZE_SQUARE


def _normalize_background_phrasing(prompt: str) -> str:
    """
    Known gpt-image-2 failure mode: asked for a transparent background, it paints
    a literal gray-and-white checkerboard into the RGB pixels instead of emitting
    alpha. Rewrite transparency requests to a clean solid background.
    """
    prompt = re.sub(
        r"(fully |truly )?transparent[ -]+(background|bg)",
        "clean solid background",
        prompt,
        flags=re.IGNORECASE,
    )
    prompt = re.sub(
        r"\bno background\b", "clean solid background", prompt, flags=re.IGNORECASE
    )
    return prompt


def _find_codex() -> str:
    for candidate in ("codex", "codex.cmd", "codex.exe"):
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError(
        "Codex CLI not found. Install with `npm install -g @openai/codex`, "
        "then run `codex login` (ChatGPT OAuth)."
    )


def _build_task(prompt: str, size: str, quality: str, out_path: Path) -> str:
    return f"""Perform the following tasks:
1. Use the built-in image_gen tool to generate exactly one image.
2. Image prompt (everything between the markers, verbatim):
---PROMPT---
{prompt}
---END PROMPT---
3. Background rule (MUST follow): the image must have a clean, single solid flat background. NEVER paint a transparency/alpha checkerboard — i.e. no alternating gray-and-white squares anywhere. If the prompt implies a 'transparent' or 'no' background, render a clean solid background of the nearest plain color instead (use the backdrop color named in the prompt if any, otherwise plain white).
4. Size: {size}
5. Quality: {quality}
6. Copy the generated image to '{out_path}' (overwriting any existing file at that exact path is allowed).
7. Print the saved file path.
"""


def _run_codex(codex_bin: str, task: str, out_dir: Path) -> subprocess.CompletedProcess:
    cmd = [
        codex_bin,
        "exec",
        "-",
        "-C", str(out_dir),
        "-s", "workspace-write",
        "--skip-git-repo-check",
    ]
    return subprocess.run(
        cmd,
        input=task,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GENERATION_TIMEOUT_SECONDS,
    )


def _output_text(stdout, stderr) -> str:
    parts = []
    for chunk in (stdout, stderr):
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8", errors="replace")
        parts.append(chunk or "")
    return "\n".join(parts)


def _rollouts_for_target(out_path: Path, since: float) -> list[Path]:
    """Rollout files written since `since` whose content mentions `out_path`."""
    sessions_dir = _codex_home() / "sessions"
    if not sessions_dir.is_dir():
        return []
    # Rollouts store the task text JSON-escaped (Windows backslashes doubled).
    needles = {str(out_path), json.dumps(str(out_path), ensure_ascii=False)[1:-1]}
    found = []
    for rollout in sessions_dir.rglob("rollout-*.jsonl"):
        try:
            if rollout.stat().st_mtime < since - MTIME_SLACK_SECONDS:
                continue
            text = rollout.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(needle in text for needle in needles):
            found.append(rollout)
    return found


def _session_ids(output: str, rollouts: list[Path]) -> list[str]:
    ids = [m.group(1).lower() for m in _SESSION_ID_RE.finditer(output)]
    for rollout in rollouts:
        match = _ROLLOUT_ID_RE.search(rollout.name)
        if match:
            ids.append(match.group(1).lower())
    return list(dict.fromkeys(ids))


def _recover_session_image(session_ids: list[str], since: float,
                           out_path: Path) -> Path | None:
    """Copy the newest PNG Codex left in generated_images/<session-id>/ to out_path."""
    images_root = _codex_home() / "generated_images"
    candidates = []
    for session_id in session_ids:
        session_dir = images_root / session_id
        if not session_dir.is_dir():
            continue
        for png in session_dir.glob("*.png"):
            try:
                stat = png.stat()
            except OSError:
                continue
            if stat.st_size > 0 and stat.st_mtime >= since - MTIME_SLACK_SECONDS:
                candidates.append((stat.st_mtime, png))
    if not candidates:
        return None
    source = max(candidates)[1]
    shutil.copyfile(source, out_path)
    return source


def _usage_limit_message(text: str) -> str | None:
    """Return a one-line usage-limit report (with reset time) or None."""
    if not _USAGE_LIMIT_RE.search(text):
        return None
    reset = _RESET_AT_RE.search(text)
    reset_note = f"resets at {reset.group(1).strip()}" if reset else "reset time not reported"
    return f"Codex usage limit reached ({reset_note})"


def generate(prompt: str,
             aspect_ratio: str = "1:1", image_size: str = "1K",
             output_dir: str = None, filename: str = None,
             model: str = None, max_retries: int = MAX_ATTEMPTS - 1) -> str:
    """
    Generate an image through Codex CLI (`codex exec` + built-in image_gen tool).

    Auth comes from Codex OAuth (`codex login`); no environment keys are read.
    `model` is accepted for interface compatibility but ignored — the codex
    image_gen tool always uses gpt-image-2.

    Returns:
        Path of the saved image file

    Raises:
        RuntimeError: When the CLI is missing, auth fails, or no file is produced
    """
    codex_bin = _find_codex()

    image_size = normalize_image_size(image_size)
    size = _select_size(aspect_ratio)
    quality = IMAGE_SIZE_TO_QUALITY.get(image_size, "medium")
    prompt = _normalize_background_phrasing(prompt)

    out_path = Path(resolve_output_path(prompt, output_dir, filename, ".png")).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    task = _build_task(prompt, size, quality, out_path)

    print("[Codex CLI - ChatGPT OAuth]")
    print(f"  Model:        {DEFAULT_MODEL} (via codex image_gen)")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Size:         {size} (from aspect_ratio={aspect_ratio})")
    print(f"  Quality:      {quality} (from image_size={image_size})")
    print()

    attempts = max(1, min(max_retries + 1, MAX_ATTEMPTS))
    last_detail = ""
    for attempt in range(1, attempts + 1):
        start_time = time.time()
        print(f"  [..] Generating (attempt {attempt}/{attempts})...", flush=True)
        try:
            result = _run_codex(codex_bin, task, out_path.parent)
            output = _output_text(result.stdout, result.stderr)
            status = f"exit={result.returncode}"
        except subprocess.TimeoutExpired as exc:
            output = _output_text(exc.stdout, exc.stderr)
            status = f"timed out after {GENERATION_TIMEOUT_SECONDS}s"

        elapsed = time.time() - start_time
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"  [DONE] Image generated ({elapsed:.1f}s)")
            print(f"  File saved to: {out_path}")
            report_resolution(str(out_path))
            return str(out_path)

        # Codex may have drawn the image but left it in its own session folder.
        rollouts = _rollouts_for_target(out_path, start_time)
        session_ids = _session_ids(output, rollouts)
        source = _recover_session_image(session_ids, start_time, out_path)
        if source is not None:
            print(f"  [DONE] Image recovered from Codex session folder ({elapsed:.1f}s)")
            print(f"  Source:        {source}")
            print(f"  File saved to: {out_path}")
            report_resolution(str(out_path))
            return str(out_path)

        rollout_text = ""
        for rollout in rollouts:
            try:
                rollout_text += rollout.read_text(encoding="utf-8", errors="replace")[-4000:]
            except OSError:
                pass
        limit_message = _usage_limit_message(output + "\n" + rollout_text)
        if limit_message:
            print(f"  [STOP] {limit_message}; not retrying")
            raise QuotaExhaustedError(
                f"{limit_message}. Wait for the reset or switch IMAGE_BACKEND, "
                "then rerun the manifest."
            )

        output_tail = output.strip()[-500:]
        sessions_note = ", ".join(session_ids) or "none found"
        last_detail = (
            f"codex exec {status}, output file missing and no image in session "
            f"folder(s) [{sessions_note}]. Output tail: {output_tail}"
        )
        print(f"  [FAIL] attempt {attempt}: no image after {elapsed:.1f}s ({status})")

    hint = ""
    lowered = last_detail.lower()
    if "login" in lowered or "auth" in lowered or "401" in lowered:
        hint = " Run `codex login` to refresh ChatGPT OAuth."
    raise RuntimeError(f"Codex image generation failed. {last_detail}{hint}")
