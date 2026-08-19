#!/usr/bin/env python3
"""
Antigravity CLI backend — image generation through the built-in generate_image
tool using an authenticated Antigravity subscription.

Usage:
    python3 .claude/skills/ppt-master/scripts/image_gen.py \
        "A clean editorial illustration" --backend agy

Examples:
    IMAGE_BACKEND=agy python3 .claude/skills/ppt-master/scripts/image_gen.py \
        --manifest projects/demo/images/image_prompts.json

Dependencies:
    Antigravity CLI (`agy`) with an active subscription login; Pillow is needed
    only when its JPEG result must be transcoded to the requested PNG filename.

The CLI tool does not accept an output path. It writes generated images under
~/.gemini/antigravity-cli/brain/<conversation-id>/ and records what it wrote in
that conversation's transcript, so this adapter identifies the conversation from
the per-run log, reads the transcript for proof that generate_image ran and for
the file name the tool reported, then copies that image into the normal
ppt-master output contract.
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
    print(
        "Use via: python3 .claude/skills/ppt-master/scripts/image_gen.py "
        '"prompt" --backend agy'
    )
    raise SystemExit(
        0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1
    )

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid

from image_backends.backend_common import (
    AllowanceExhausted,
    normalize_image_size,
    resolve_output_path,
    save_image_bytes,
)


DEFAULT_MODEL = "gemini-3.1-pro"
# One tool call needs no deliberation, and the low tier reaches it far sooner.
DEFAULT_EFFORT = "low"
DEFAULT_TIMEOUT_MINUTES = 10
# The CLI does occasionally end a session without finishing the image, so one
# transient error must not end the run. Three attempts cost nothing on a healthy
# run, since a retry only follows a failure. (An earlier note here blamed the
# upstream for dropping about half of all calls; that was this adapter misreading
# finished runs, not a real upstream failure rate.)
MAX_ATTEMPTS = 3

_CONVERSATION_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
# The tool closes with one sentence naming the file it wrote. That sentence is
# the only exact statement of the output path the CLI ever gives us.
_SAVED_IMAGE_RE = re.compile(
    r"Generated image is saved at\s+(?P<path>\S.*?\.(?:png|jpe?g|webp))",
    re.IGNORECASE,
)
# The CLI reports a spent image allowance only as model-written prose, and the
# wording is different every time — 2026-08-19 alone produced "the model's
# capacity has been exhausted", "I encountered a quota exhaustion error", and
# "the image generation quota is currently exhausted". Nothing machine-readable
# comes with it: exit code 0, empty stderr, no error line in the log. Chasing
# each phrasing leaked two of the three, so a line qualifies when it names the
# resource AND says that resource is gone. The CLI's own logs mention quota
# routinely while healthy (`quota_manager`, `doRefreshQuota`) but never pair it
# with an exhaustion word, which is what keeps those out.
_QUOTA_RESOURCE_RE = re.compile(
    r"quota|capacity|allowance|credits|RESOURCE_EXHAUSTED|\b429\b",
    re.IGNORECASE,
)
_QUOTA_SPENT_RE = re.compile(
    r"exhaust|exceed|depleted|spent|ran\s+out|run\s+out|used\s+up"
    r"|insufficient|reach|throttl|rate[\s-]*limit|too\s+many\s+requests",
    re.IGNORECASE,
)




def _find_agy() -> str:
    """Return the configured Antigravity CLI or raise with a recovery hint."""
    configured = os.environ.get("AGY_BIN", "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_file():
            return str(path)
        raise RuntimeError(
            f"AGY_BIN points to a missing file: {path}. "
            "Fix AGY_BIN or remove it so the adapter can resolve `agy` from PATH."
        )

    found = shutil.which("agy")
    if found:
        return found

    fallback = Path("~/.local/bin/agy").expanduser()
    if fallback.is_file():
        return str(fallback)

    raise RuntimeError(
        "Antigravity CLI not found. Install/configure `agy`, authenticate the "
        "subscription, then confirm that `agy --version` succeeds."
    )


def _brain_root() -> Path:
    configured = os.environ.get("AGY_BRAIN_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path("~/.gemini/antigravity-cli/brain").expanduser()


def _effort() -> str:
    """Reasoning effort for the run. Reasoning models such as gemini-3.1-pro
    reject a selection that omits it, so one is always sent unless the caller
    explicitly blanks ``AGY_EFFORT`` for a model that refuses the flag."""
    raw = os.environ.get("AGY_EFFORT")
    if raw is None:
        return DEFAULT_EFFORT
    return raw.strip()


def _timeout_minutes() -> int:
    raw = os.environ.get("AGY_TIMEOUT_MINUTES", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_MINUTES
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            "AGY_TIMEOUT_MINUTES must be a positive integer."
        ) from exc
    if value < 1:
        raise RuntimeError("AGY_TIMEOUT_MINUTES must be at least 1.")
    return value


def _build_task(
    prompt: str,
    *,
    image_name: str,
    aspect_ratio: str,
    token: str,
) -> str:
    """Wrap the ppt-master prompt without changing its visual instructions."""
    return f"""Act strictly as a Text-to-Image synthesis engine.
DO NOT output code. DO NOT write a script. DO NOT use Python, PIL, matplotlib, SVG, or shell commands.
DO NOT explain. Call the built-in generate_image tool exactly once, then stop.

Use ImageName exactly: {image_name}
Use AspectRatio exactly: {aspect_ratio}
Job token (bookkeeping only; never draw it): {token}

Use the following image prompt verbatim as the visual specification:
---PROMPT---
{prompt}
---END PROMPT---
"""


def _quota_evidence(text: str) -> str:
    """The line that reads as a spent subscription allowance, or "" for none.

    The CLI states a spent allowance in prose on stdout rather than as an error
    code, and its internal logs mention quota routinely, so this matches the
    sentence it actually prints plus the other signatures such limits arrive
    under. Returning the matched line rather than a bare yes/no is what makes
    the verdict checkable: the CLI log is discarded when the run ends, so a
    caller that only learned "quota" could never tell a real limit from a false
    hit on an unrelated log line."""
    for line in text.splitlines():
        if _QUOTA_RESOURCE_RE.search(line) and _QUOTA_SPENT_RE.search(line):
            stripped = line.strip()
            return stripped[:300] + ("..." if len(stripped) > 300 else "")
    return ""


def _cli_error(result: subprocess.CompletedProcess) -> str:
    """First error line the CLI printed. Without it a setup mistake such as a
    rejected model surfaces only as an unrecoverable conversation id."""
    for stream in (result.stderr, result.stdout):
        for line in (stream or "").splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("error"):
                return f"agy reported: {stripped}"
    return ""


def _conversation_from_text(text: str) -> str:
    for line in text.splitlines():
        if "Created conversation" not in line:
            continue
        match = _CONVERSATION_RE.search(line)
        if match:
            return match.group(0)
    return ""


def _transcript_path(brain_root: Path, conversation: str) -> Path:
    return brain_root / conversation / ".system_generated" / "logs" / "transcript.jsonl"


def _conversation_from_token(brain_root: Path, token: str, started_at: float) -> str:
    """Recover a conversation when the CLI log omitted its creation line."""
    if not brain_root.is_dir():
        return ""
    for conversation_dir in brain_root.iterdir():
        if not conversation_dir.is_dir():
            continue
        transcript = _transcript_path(brain_root, conversation_dir.name)
        try:
            if transcript.stat().st_mtime < started_at - 5:
                continue
            if token in transcript.read_text(encoding="utf-8", errors="replace"):
                return conversation_dir.name
        except OSError:
            continue
    return ""


def _scan_transcript(brain_root: Path, conversation: str) -> tuple[bool, list[Path]]:
    """Read one conversation for proof that the built-in image tool ran.

    The CLI labels the tool-result step "GENERATE_IMAGE" in some runs and the
    unspecific "GENERIC" in others, so that label alone cannot decide whether an
    image was made — runs whose image was already on disk were being rejected on
    it. Both shapes do record the `generate_image` tool call and the sentence the
    tool writes naming the file it saved, so those two signals are read instead.

    Returns whether the tool ran and every output path the transcript reported.
    """
    transcript = _transcript_path(brain_root, conversation)
    try:
        text = transcript.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise RuntimeError(
            "Antigravity conversation was created, but its transcript could not be read. "
            "Check AGY_BRAIN_DIR and the Antigravity login state."
        ) from exc

    tool_called = False
    saved: list[Path] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            record = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        if record.get("type") == "GENERATE_IMAGE":
            tool_called = True
        for call in record.get("tool_calls") or []:
            # A bare text search would also hit the tool inventory the CLI
            # pastes into every conversation, so read the recorded call itself.
            if isinstance(call, dict) and call.get("name") == "generate_image":
                tool_called = True
        content = record.get("content")
        if isinstance(content, str):
            saved += [
                Path(match.group("path")) for match in _SAVED_IMAGE_RE.finditer(content)
            ]
    return tool_called, saved


def _reported_image(
    brain_root: Path,
    conversation: str,
    reported: list[Path],
) -> Path | None:
    """Resolve the file the tool reported, confined to its own conversation.

    Every conversation that holds an image also names that image in its
    transcript, so no directory scan is needed. Declining to look past the
    reported name is also what keeps a script-written stand-in out: a fallback
    that ranked the directory by modification time would accept one.
    """
    conversation_dir = brain_root / conversation
    if not conversation_dir.is_dir():
        return None

    root = conversation_dir.resolve()
    for path in reversed(reported):
        candidate = path.expanduser()
        if not candidate.is_absolute():
            candidate = conversation_dir / candidate
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file() and resolved.is_relative_to(root):
            return resolved
    return None


def generate(
    prompt: str,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
    output_dir: str = None,
    filename: str = None,
    model: str = None,
    max_retries: int = MAX_ATTEMPTS - 1,
) -> str:
    """Generate one image through the authenticated Antigravity CLI."""
    agy_bin = _find_agy()
    brain_root = _brain_root()
    timeout_minutes = _timeout_minutes()
    selected_model = model or os.environ.get("AGY_MODEL", "").strip() or DEFAULT_MODEL
    selected_effort = _effort()
    normalized_size = normalize_image_size(image_size)

    out_path = Path(
        resolve_output_path(prompt, output_dir, filename, ".png")
    ).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image_name = out_path.stem

    print("[Antigravity CLI - subscription auth]")
    print(f"  Model:        {selected_model}")
    print(f"  Effort:       {selected_effort or '(omitted)'}")
    print(f"  Prompt:       {prompt[:120]}{'...' if len(prompt) > 120 else ''}")
    print(f"  Aspect ratio: {aspect_ratio} (requested from generate_image)")
    print(f"  Image size:   {normalized_size} (provider controls native resolution)")
    print()

    attempts = max(1, max_retries + 1)
    last_detail = ""
    for attempt in range(1, attempts + 1):
        token = f"ppt-master-{uuid.uuid4().hex}"
        task = _build_task(
            prompt,
            image_name=image_name,
            aspect_ratio=aspect_ratio,
            token=token,
        )
        started_at = time.time()

        with tempfile.TemporaryDirectory(prefix="ppt-master-agy-") as tmp_dir:
            log_path = Path(tmp_dir) / "agy.log"
            cmd = [agy_bin, f"--model={selected_model}"]
            if selected_effort:
                cmd.append(f"--effort={selected_effort}")
            cmd += [
                "--print-timeout",
                f"{timeout_minutes}m",
                "--log-file",
                str(log_path),
                "-p",
                task,
            ]
            print(f"  [..] Generating (attempt {attempt}/{attempts})...", flush=True)
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_minutes * 60 + 90,
                )
            except subprocess.TimeoutExpired:
                last_detail = f"agy timed out after {timeout_minutes} minutes"
                print(f"  [FAIL] {last_detail}")
                continue

            log_text = ""
            try:
                log_text = log_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
            combined = "\n".join((log_text, result.stdout or "", result.stderr or ""))

            conversation = _conversation_from_text(combined)
            if not conversation:
                conversation = _conversation_from_token(brain_root, token, started_at)

            # Ask what came out before asking what went wrong. A run that met a
            # transient 429, retried inside the session, and finished the image
            # still complains about quota in its log — judging the complaint
            # first would throw that finished image away.
            generated = None
            tool_called = False
            if conversation:
                try:
                    tool_called, reported = _scan_transcript(brain_root, conversation)
                except RuntimeError as exc:
                    last_detail = str(exc)
                    print(f"  [FAIL] {last_detail}")
                    continue
                generated = _reported_image(brain_root, conversation, reported)

            if generated is None:
                quota_line = _quota_evidence(combined)
                if quota_line:
                    raise AllowanceExhausted(
                        "Antigravity reports its image allowance as spent, so this run "
                        "stops rather than spend more of it on retries. This limit is "
                        "the image path's own and is not the model quota the Antigravity "
                        "usage panel shows — that panel can read nearly full while image "
                        "generation is blocked. Wait for it to reset, or acquire the "
                        f"images another way. CLI reported: {quota_line}"
                    )

                if not conversation:
                    last_detail = (
                        f"agy exit={result.returncode}; conversation id was not "
                        f"recoverable. {_cli_error(result)}"
                    ).strip()
                elif not tool_called:
                    last_detail = (
                        "Antigravity did not execute its generate_image tool. The "
                        "subscription image-generation path may be unavailable; no "
                        "fallback image was accepted."
                    )
                else:
                    last_detail = (
                        "Antigravity started generate_image, but conversation "
                        f"{conversation} names no image file it finished writing. "
                        f"agy exit={result.returncode}. {_cli_error(result)}"
                    ).strip()
                print(f"  [FAIL] {last_detail}")
                continue

            elapsed = time.time() - started_at
            saved_path = save_image_bytes(generated.read_bytes(), str(out_path))
            print(f"  [DONE] Image generated ({elapsed:.1f}s)")
            return saved_path

    raise RuntimeError(
        f"Antigravity image generation failed after {attempts} attempts. "
        f"{last_detail} A spent daily allowance looks the same from here as a "
        "transient upstream error, so check the subscription's remaining image "
        "usage before treating this as a fault."
    )
