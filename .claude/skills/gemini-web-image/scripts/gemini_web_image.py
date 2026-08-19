#!/usr/bin/env python3
"""
PPT Master - Gemini Web Image Generator

Generate an `image_prompts.json` manifest's `ai` rows through the Gemini web app
driven by the Kimi WebBridge daemon, for hosts that have a Gemini subscription
but no keyless CLI image path. Submits every prompt first so the generations
overlap, then collects the finished images one tab at a time.

Usage:
    python3 scripts/gemini_web_image.py --manifest <image_prompts.json> [options]

Examples:
    python3 .claude/skills/gemini-web-image/scripts/gemini_web_image.py \
        --manifest projects/demo/images/image_prompts.json
    python3 .claude/skills/gemini-web-image/scripts/gemini_web_image.py \
        --manifest projects/demo/images/image_prompts.json --collect-only

Dependencies:
    Kimi WebBridge daemon on http://127.0.0.1:10086 and a browser already
    signed in to Gemini. Standard library only.
"""

import sys
from pathlib import Path

if __name__ == "__main__" and any(a in {"-h", "--help", "help"} for a in sys.argv[1:]):
    print(__doc__)
    raise SystemExit(0)

import argparse
import base64
import json
import re
import subprocess
import tempfile
import time

DAEMON = "http://127.0.0.1:10086/command"
IMAGES_URL = "https://gemini.google.com/images"
CONVERSATION_MARK = "/app/"

# The web app exposes no aspect-ratio control, but Nano Banana 2 honors the
# ratio when the request opens with it: 16:9 returned 1024x572 and 4:3 returned
# 1024x765 on 2026-08-19.
RATIO_PREFIX = "Generate a {ar} image (aspect ratio exactly {ar}).\n\n"

# A data URL for a 1024px image runs past 600k characters, which one bridge
# response will not carry.
CHUNK = 120_000
RATIO_TOLERANCE = 0.04

PROMPT_BOX_RE = re.compile(
    r"'role': 'textbox', 'name': 'Gemini 프롬프트 입력'[^}]*?'ref': '(@e\d+)'"
)
SEND_BUTTON_RE = re.compile(r"'role': 'button', 'name': '메시지 보내기', 'ref': '(@e\d+)'")
ONBOARDING_RE = re.compile(r"'role': 'button', 'name': '사용해 보기', 'ref': '(@e\d+)'")

# The generated image is only ever a blob: URL on the page. Reading it needs a
# canvas — fetch() on a blob URL fails from the bridge's isolated world.
PROBE_JS = """(() => {
  const img = [...document.querySelectorAll('img')]
    .find(i => i.src.startsWith('blob:') && i.complete && i.naturalWidth > 300);
  const text = (document.body.innerText || '').replace(/\\s+/g, ' ');
  return JSON.stringify({
    ready: !!img,
    w: img ? img.naturalWidth : 0,
    h: img ? img.naturalHeight : 0,
    text: text.slice(0, 6000)
  });
})()"""

EXPORT_JS = """(() => {
  const img = [...document.querySelectorAll('img')]
    .find(i => i.src.startsWith('blob:') && i.complete && i.naturalWidth > 300);
  if (!img) return JSON.stringify({error: 'image element vanished'});
  const c = document.createElement('canvas');
  c.width = img.naturalWidth;
  c.height = img.naturalHeight;
  c.getContext('2d').drawImage(img, 0, 0);
  window.__pptMasterGrab = c.toDataURL('image/png');
  return JSON.stringify({len: window.__pptMasterGrab.length, w: c.width, h: c.height});
})()"""


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def call(action: str, args: dict = None, session: str = "ppt-master-images") -> dict:
    """Post one bridge command. The body always goes through a file, because a
    shell-inlined prompt loses non-ASCII text and breaks on quoting."""
    body = {"action": action, "args": args or {}, "session": session}
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    )
    with handle as fh:
        json.dump(body, fh)
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", "120", "-X", "POST", DAEMON,
             "-H", "Content-Type: application/json",
             "--data-binary", f"@{handle.name}"],
            capture_output=True, text=True, timeout=130,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": {"message": "bridge timed out"}}
    finally:
        Path(handle.name).unlink(missing_ok=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": {"message": result.stdout[:400]}}


def require_daemon() -> None:
    probe = call("list_tabs")
    if not probe.get("ok"):
        raise RuntimeError(
            "Kimi WebBridge is not answering on 127.0.0.1:10086. Start the "
            "daemon and confirm the browser extension is connected, then rerun."
        )


def evaluate(code: str) -> str:
    result = call("evaluate", {"code": code})
    return result["data"]["value"] if result.get("ok") else ""


def snapshot_tree() -> str:
    return str(call("snapshot").get("data", {}).get("tree", ""))


def aspect_ratio_value(text: str) -> float:
    try:
        w, h = text.split(":")
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        return 0.0


def fingerprint(prompt: str) -> str:
    """A distinctive slice of the prompt, matched against the page's own text.

    Conversations must be identified by what they contain. Position fails: the
    browser may hold conversations from earlier runs, and one extra tab shifts
    every later item onto the wrong file name."""
    body = prompt.split("\n\n")[-1] if "\n\n" in prompt else prompt
    return " ".join(body.split())[:70]


def submit(item: dict) -> bool:
    """Open one tab and send one prompt. Returns whether it was accepted."""
    ratio = item["aspect_ratio"]
    prompt = RATIO_PREFIX.format(ar=ratio) + item["prompt"]

    if not call("navigate", {"url": IMAGES_URL, "newTab": True}).get("ok"):
        log(f"  navigate failed for {item['filename']}")
        return False

    box = None
    for _ in range(15):
        time.sleep(2)
        tree = snapshot_tree()
        onboarding = ONBOARDING_RE.search(tree)
        if onboarding:
            call("click", {"selector": onboarding.group(1)})
            continue
        found = PROMPT_BOX_RE.search(tree)
        if found:
            box = found.group(1)
            break
    if not box:
        log(f"  prompt box never appeared for {item['filename']}")
        return False

    if not call("fill", {"selector": box, "value": prompt}).get("ok"):
        log(f"  fill failed for {item['filename']}")
        return False

    # The send button only renders once the box holds text.
    send = None
    for _ in range(10):
        time.sleep(1)
        found = SEND_BUTTON_RE.search(snapshot_tree())
        if found:
            send = found.group(1)
            break
    if not send:
        log(f"  send button never appeared for {item['filename']}")
        return False

    accepted = call("click", {"selector": send}).get("ok")
    log(f"  submitted {item['filename']} ({ratio})" if accepted
        else f"  send click failed for {item['filename']}")
    return bool(accepted)


def conversation_urls() -> list:
    tabs = call("list_tabs").get("data", {}).get("tabs", [])
    return sorted({t["url"] for t in tabs if CONVERSATION_MARK in t.get("url", "")})


def export_to(dest: Path) -> tuple:
    """Copy the current tab's generated image into dest. Returns (w, h, bytes)."""
    meta_raw = evaluate(EXPORT_JS)
    if not meta_raw:
        return ()
    meta = json.loads(meta_raw)
    if "error" in meta:
        return ()

    parts, offset = [], 0
    while offset < meta["len"]:
        piece = evaluate(
            f"(() => window.__pptMasterGrab.slice({offset}, {offset + CHUNK}))()"
        )
        if not piece:
            break
        parts.append(piece)
        offset += len(piece)

    data_url = "".join(parts)
    if not data_url.startswith("data:image/png;base64,"):
        return ()
    raw = base64.b64decode(data_url.split(",", 1)[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return meta["w"], meta["h"], len(raw)


def collect(manifest: dict, manifest_path: Path, out_dir: Path,
            urls: list, settle_seconds: int) -> int:
    """Visit each conversation and save whatever image it holds."""
    wanted = {fingerprint(it["prompt"]): it
              for it in manifest["items"] if it["status"] != "Generated"}
    log(f"collecting {len(wanted)} item(s) from {len(urls)} conversation(s)")

    saved = 0
    for url in urls:
        if not wanted:
            break
        if not call("navigate", {"url": url}).get("ok"):
            log(f"  could not open {url[-16:]}")
            continue

        state = {}
        for _ in range(settle_seconds // 5):
            time.sleep(5)
            raw = evaluate(PROBE_JS)
            if not raw:
                continue
            state = json.loads(raw)
            if state.get("ready"):
                break
        if not state.get("ready"):
            # A blob whose creating tab was navigated away can stay undecodable.
            log(f"  {url[-16:]} holds no readable image — leave it Pending "
                "and resubmit that row")
            continue

        match = next((fp for fp in wanted if fp in state["text"]), None)
        if match is None:
            log(f"  {url[-16:]} is not one of this manifest's prompts, skipping")
            continue

        item = wanted.pop(match)
        got = export_to(out_dir / item["filename"])
        if not got:
            log(f"  extraction failed for {item['filename']}")
            continue

        width, height, size = got
        actual = width / height
        wanted_ratio = aspect_ratio_value(item["aspect_ratio"])
        drift = abs(actual - wanted_ratio) / wanted_ratio if wanted_ratio else 0
        note = "" if drift <= RATIO_TOLERANCE else "  ** ratio off, review this row"
        log(f"  saved {item['filename']} {width}x{height} "
            f"ratio {actual:.3f} vs {item['aspect_ratio']} "
            f"({size:,} bytes){note}")

        item["status"] = "Generated"
        item.pop("last_error", None)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        saved += 1

    for item in wanted.values():
        item["last_error"] = "gemini-web: no image collected for this prompt"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an image manifest through the Gemini web app."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", "-o", default=None,
                        help="Output directory (default: the manifest's folder)")
    parser.add_argument("--batch", type=int, default=8,
                        help="Rows to submit in one pass (default 8)")
    parser.add_argument("--settle", type=int, default=180,
                        help="Seconds to wait per conversation for its image")
    parser.add_argument("--collect-only", action="store_true",
                        help="Skip submission and collect open conversations")
    parser.add_argument("--url", action="append", default=[],
                        help="Collect this conversation URL (repeatable)")
    args = parser.parse_args()

    require_daemon()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir = Path(args.output).resolve() if args.output else manifest_path.parent

    pending = [it for it in manifest["items"] if it["status"] != "Generated"]
    if not pending:
        log("nothing to do — every row is already Generated")
        return

    if args.collect_only:
        urls = args.url or conversation_urls()
        saved = collect(manifest, manifest_path, out_dir, urls, args.settle)
    else:
        batch = pending[:args.batch]
        if len(pending) > len(batch):
            log(f"{len(pending)} rows pending; submitting {len(batch)} this pass")
        log(f"submitting {len(batch)} prompt(s)")
        before = set(conversation_urls())
        accepted = [it for it in batch if submit(it)]
        log(f"{len(accepted)} submitted; waiting for conversation ids")
        time.sleep(45)
        fresh = [u for u in conversation_urls() if u not in before]
        log(f"{len(fresh)} new conversation(s)")
        saved = collect(manifest, manifest_path, out_dir, fresh, args.settle)

    total = sum(1 for it in manifest["items"] if it["status"] == "Generated")
    log(f"saved {saved} this run · manifest {total}/{len(manifest['items'])}")


if __name__ == "__main__":
    main()
