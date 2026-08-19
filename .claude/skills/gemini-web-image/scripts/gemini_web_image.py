#!/usr/bin/env python3
"""
PPT Master - Gemini Web Image Generator

Generate an `image_prompts.json` manifest's `ai` rows through the Gemini web app
driven by the Kimi WebBridge daemon, for hosts that have a Gemini subscription
but no keyless CLI image path. Each row gets its own bridge session, so each row
gets its own tab that nothing else touches: submit them all, wait once, then
read each tab where it stands.

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

# One session per row. The bridge scopes its "current tab" to the session, so a
# session is a handle on one tab that no other session can move. That is what
# makes this deterministic: nothing navigates, nothing reloads, and which tab
# holds which row is the slot number rather than something to infer.
SESSION_PREFIX = "ppt-master-image"

# The page has no aspect-ratio control, but the model honors a ratio asked for
# in the opening line: 16:9 came back 2400x1792 on 4:3 and 2752x1536 on 16:9.
RATIO_PREFIX = "Generate a {ar} image (aspect ratio exactly {ar}).\n\n"

DOWNLOADS = Path("~/Downloads").expanduser()
DOWNLOAD_GLOB = "Gemini_Generated_Image_*"
DOWNLOAD_WAIT = 20
CHUNK = 120_000
RATIO_TOLERANCE = 0.04

PROMPT_BOX_RE = re.compile(
    r"'role': 'textbox', 'name': 'Gemini 프롬프트 입력'[^}]*?'ref': '(@e\d+)'"
)
SEND_BUTTON_RE = re.compile(r"'role': 'button', 'name': '메시지 보내기', 'ref': '(@e\d+)'")
ONBOARDING_RE = re.compile(r"'role': 'button', 'name': '사용해 보기', 'ref': '(@e\d+)'")
DOWNLOAD_BUTTON_RE = re.compile(
    r"'role': 'button', 'name': '원본 크기 이미지 다운로드', 'ref': '(@e\d+)'"
)

# The result carries loading="lazy" and decodes only inside the viewport.
READY_JS = """(() => {
  const img = [...document.querySelectorAll('img')].find(i => i.src.startsWith('blob:'));
  if (img && img.naturalWidth < 300) img.scrollIntoView({block: 'center'});
  return JSON.stringify({
    present: !!img,
    decoded: !!img && img.complete && img.naturalWidth > 300
  });
})()"""

# Fallback for a browser that refuses the page's download; yields the displayed
# copy rather than the original.
CANVAS_JS = """(() => {
  const img = [...document.querySelectorAll('img')]
    .find(i => i.src.startsWith('blob:') && i.complete && i.naturalWidth > 300);
  if (!img) return JSON.stringify({error: 'no decoded image'});
  const c = document.createElement('canvas');
  c.width = img.naturalWidth;
  c.height = img.naturalHeight;
  c.getContext('2d').drawImage(img, 0, 0);
  window.__pptMasterGrab = c.toDataURL('image/png');
  return JSON.stringify({len: window.__pptMasterGrab.length, w: c.width, h: c.height});
})()"""


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def call(action: str, args: dict, session: str) -> dict:
    """Post one bridge command. The body goes through a file, because an inlined
    prompt loses non-ASCII text and breaks on shell quoting."""
    body = {"action": action, "args": args or {}, "session": session}
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    )
    with handle:
        json.dump(body, handle)
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


def evaluate(code: str, session: str) -> str:
    result = call("evaluate", {"code": code}, session)
    return result["data"]["value"] if result.get("ok") else ""


def snapshot(session: str) -> str:
    return str(call("snapshot", {}, session).get("data", {}).get("tree", ""))


def slot_name(index: int) -> str:
    return f"{SESSION_PREFIX}-{index + 1}"


def require_daemon() -> None:
    if not call("list_tabs", {}, SESSION_PREFIX).get("ok"):
        raise RuntimeError(
            "Kimi WebBridge is not answering on 127.0.0.1:10086. Start the "
            "daemon and confirm the browser extension is connected, then rerun."
        )


def aspect_ratio_value(text: str) -> float:
    try:
        width, height = text.split(":")
        return float(width) / float(height)
    except (ValueError, ZeroDivisionError):
        return 0.0


def submit(item: dict, session: str) -> bool:
    """Open this slot's tab and send its prompt."""
    prompt = RATIO_PREFIX.format(ar=item["aspect_ratio"]) + item["prompt"]

    if not call("navigate", {"url": IMAGES_URL, "newTab": True}, session).get("ok"):
        log(f"  navigate failed for {item['filename']}")
        return False

    box = None
    for _ in range(15):
        time.sleep(2)
        tree = snapshot(session)
        onboarding = ONBOARDING_RE.search(tree)
        if onboarding:
            call("click", {"selector": onboarding.group(1)}, session)
            continue
        found = PROMPT_BOX_RE.search(tree)
        if found:
            box = found.group(1)
            break
    if not box:
        log(f"  prompt box never appeared for {item['filename']}")
        return False

    if not call("fill", {"selector": box, "value": prompt}, session).get("ok"):
        log(f"  fill failed for {item['filename']}")
        return False

    # The send button renders only once the box holds text.
    send = None
    for _ in range(10):
        time.sleep(1)
        found = SEND_BUTTON_RE.search(snapshot(session))
        if found:
            send = found.group(1)
            break
    if not send:
        log(f"  send button never appeared for {item['filename']}")
        return False

    if not call("click", {"selector": send}, session).get("ok"):
        log(f"  send click failed for {item['filename']}")
        return False
    log(f"  submitted {item['filename']} ({item['aspect_ratio']})")
    return True


def newest_download(after: float):
    newest, newest_time = None, after
    for path in DOWNLOADS.glob(DOWNLOAD_GLOB):
        try:
            stamp = path.stat().st_mtime
        except OSError:
            continue
        if stamp > newest_time:
            newest, newest_time = path, stamp
    return newest


def png_size(raw: bytes) -> tuple:
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    return (int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big"))


def export_to(dest: Path, session: str) -> tuple:
    """Save this slot's image into dest. Returns (width, height, bytes).

    The page's download control is tried first because it hands over the
    original file. Its click reports success even when the browser refuses the
    download, so a file's arrival is the only proof, and the canvas readback
    covers the refusal."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    found = DOWNLOAD_BUTTON_RE.search(snapshot(session))
    if found:
        started = time.time()
        call("click", {"selector": found.group(1)}, session)
        for _ in range(DOWNLOAD_WAIT // 2):
            time.sleep(2)
            landed = newest_download(started)
            if landed:
                size = landed.stat().st_size
                time.sleep(1)
                if size and landed.stat().st_size == size:
                    raw = landed.read_bytes()
                    dest.write_bytes(raw)
                    landed.unlink(missing_ok=True)
                    log("    original file via the page's download control")
                    return png_size(raw) + (len(raw),)
        log("    download refused; reading the rendered image instead")

    meta_raw = evaluate(CANVAS_JS, session)
    if not meta_raw:
        return ()
    meta = json.loads(meta_raw)
    if "error" in meta:
        return ()

    parts, offset = [], 0
    while offset < meta["len"]:
        piece = evaluate(
            f"(() => window.__pptMasterGrab.slice({offset}, {offset + CHUNK}))()",
            session,
        )
        if not piece:
            break
        parts.append(piece)
        offset += len(piece)

    data_url = "".join(parts)
    if not data_url.startswith("data:image/png;base64,"):
        return ()
    raw = base64.b64decode(data_url.split(",", 1)[1])
    dest.write_bytes(raw)
    return meta["w"], meta["h"], len(raw)


def collect(manifest: dict, manifest_path: Path, out_dir: Path,
            slots: list, settle: int) -> int:
    """Read every slot's own tab. No slot is ever navigated or reloaded."""
    saved = 0
    for index, item in slots:
        session = slot_name(index)
        state = {}
        deadline = time.time() + settle
        while time.time() < deadline:
            raw = evaluate(READY_JS, session)
            if raw:
                state = json.loads(raw)
                if state.get("decoded"):
                    break
            time.sleep(5)
        if not state.get("decoded"):
            item["last_error"] = "gemini-web: image not ready within the settle window"
            log(f"  {item['filename']}: not ready after {settle}s — left Pending")
            continue

        got = export_to(out_dir / item["filename"], session)
        if not got:
            item["last_error"] = "gemini-web: image could not be extracted"
            log(f"  {item['filename']}: extraction failed")
            continue

        width, height, size = got
        actual = width / height if height else 0
        target = aspect_ratio_value(item["aspect_ratio"])
        drift = abs(actual - target) / target if target else 0
        note = "" if drift <= RATIO_TOLERANCE else "  ** ratio off, review this row"
        log(f"  saved {item['filename']} {width}x{height} "
            f"ratio {actual:.3f} vs {item['aspect_ratio']} ({size:,} bytes){note}")

        item["status"] = "Generated"
        item.pop("last_error", None)
        saved += 1
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

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
                        help="Rows submitted in one pass, one tab each (default 8)")
    parser.add_argument("--generate-wait", type=int, default=150,
                        help="Seconds to let the images generate before reading")
    parser.add_argument("--settle", type=int, default=300,
                        help="Extra seconds to wait per slot for its image")
    parser.add_argument("--collect-only", action="store_true",
                        help="Skip submission and read the slots already open")
    args = parser.parse_args()

    require_daemon()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir = Path(args.output).resolve() if args.output else manifest_path.parent

    pending = [it for it in manifest["items"] if it["status"] != "Generated"]
    if not pending:
        log("nothing to do — every row is already Generated")
        return

    batch = pending[:args.batch]
    if len(pending) > len(batch):
        log(f"{len(pending)} rows pending; taking {len(batch)} this pass")

    if args.collect_only:
        slots = list(enumerate(batch))
    else:
        log(f"submitting {len(batch)} prompt(s), one tab each")
        slots = [(i, item) for i, item in enumerate(batch)
                 if submit(item, slot_name(i))]
        log(f"{len(slots)} submitted; letting them generate for "
            f"{args.generate_wait}s")
        time.sleep(args.generate_wait)

    saved = collect(manifest, manifest_path, out_dir, slots, args.settle)
    total = sum(1 for it in manifest["items"] if it["status"] == "Generated")
    log(f"saved {saved} this run · manifest {total}/{len(manifest['items'])}")


if __name__ == "__main__":
    main()
