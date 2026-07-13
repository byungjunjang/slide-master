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

import os
import re
import shutil
import subprocess
import time

from image_backends.backend_common import (
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
MAX_ATTEMPTS = 2


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

    attempts = max(1, max_retries + 1)
    last_detail = ""
    for attempt in range(1, attempts + 1):
        start_time = time.time()
        print(f"  [..] Generating (attempt {attempt}/{attempts})...", flush=True)
        try:
            result = _run_codex(codex_bin, task, out_path.parent)
        except subprocess.TimeoutExpired as exc:
            last_detail = f"codex exec timed out after {GENERATION_TIMEOUT_SECONDS}s"
            print(f"  [FAIL] {last_detail}")
            continue

        elapsed = time.time() - start_time
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"  [DONE] Image generated ({elapsed:.1f}s)")
            print(f"  File saved to: {out_path}")
            report_resolution(str(out_path))
            return str(out_path)

        output_tail = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()[-500:]
        last_detail = (
            f"codex exec exit={result.returncode}, output file missing. "
            f"Output tail: {output_tail}"
        )
        print(f"  [FAIL] attempt {attempt}: no output file after {elapsed:.1f}s")

    hint = ""
    lowered = last_detail.lower()
    if "login" in lowered or "auth" in lowered or "401" in lowered:
        hint = " Run `codex login` to refresh ChatGPT OAuth."
    raise RuntimeError(f"Codex image generation failed. {last_detail}{hint}")
