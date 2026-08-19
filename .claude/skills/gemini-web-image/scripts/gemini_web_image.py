#!/usr/bin/env python3
"""
PPT Master - Gemini Web Image Generator

Generate an `image_prompts.json` manifest's Pending and Failed rows through the
Gemini web app
driven by the Kimi WebBridge daemon, for hosts that have a Gemini subscription
but no keyless CLI image path. Each row gets its own bridge session, so each row
gets its own tab that nothing else touches: submit them all, wait once, then
read each tab where it stands.

Usage:
    python3 scripts/gemini_web_image.py --manifest <image_prompts.json> [options]

Options:
    --manifest PATH     image_prompts.json to read and write back (required)
    --output, -o DIR    where images land (default: the manifest's folder)
    --batch N           rows submitted this pass, one tab each (default 10).
                        Ten rows at the displayed size measured 245s; ten
                        originals are near the 300s deadline. Lower it only if a
                        run hits Google's unusual-traffic challenge.
    --generate-wait S   settle before the first sweep (default 10)
    --deadline S        hard wall-clock budget for the whole run (default 300).
                        On expiry the run stops and reports what is missing.
    --displayed-size    keep the 1024px canvas copy instead of downloading the
                        original; saves about 12s per row
    --collect-only      skip submission; read the slots already open

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
import binascii
import json
import random
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

DAEMON = "http://127.0.0.1:10086/command"
IMAGES_URL = "https://gemini.google.com/images"

# One session per row. The bridge scopes its "current tab" to the session, so a
# session is a handle on one tab that no other session can move. That is what
# makes this deterministic: nothing navigates, nothing reloads, and which tab
# holds which row is the slot number rather than something to infer.
SESSION_PREFIX = "ppt-master-image"

# Rows this path may take. Generated is done; Needs-Manual belongs to the user.
RETRYABLE = {"Pending", "Failed"}

# The page has no aspect-ratio control, but the model honors a ratio asked for
# in the opening line: asking for 16:9 came back 2752x1536, 4:3 came back
# 2400x1792, and 1:1 came back 2048x2048.
RATIO_PREFIX = "Generate a {ar} image (aspect ratio exactly {ar}).\n\n"
RATIO_LINE_RE = re.compile(
    r"Generate a (\d+:\d+) image \(aspect ratio exactly \d+:\d+\)\.")

DOWNLOADS = Path("~/Downloads").expanduser()
DOWNLOAD_GLOB = "Gemini_Generated_Image_*"
# The original is a multi-megabyte PNG and takes 11-17s from click to file. Six
# seconds was too short and silently sent every row to the low-resolution
# fallback while reporting nothing wrong.
DOWNLOAD_WAIT = 25
# Sweeps are cheap now that slots are polled concurrently, so the interval is
# the detection latency and nothing else. Ten seconds added an average five
# seconds of dead time to every row for no benefit.
SWEEP_INTERVAL = 5
# How long a tab may show no image and no "creating" state before it is treated
# as a dropped submission rather than a slow one.
DEAD_ROW_GRACE = 75
# A browser that refuses one download refuses them all, so the wait is dropped
# for the rest of the run once that is established. It has to be established,
# though: latching on a viewer that failed to open, or on a file that was still
# arriving, demotes every later row to the 1024px canvas copy over one bad
# moment. Only a click whose file never appeared counts as a refusal.
_download_refused = False
_canvas_rows = []
# Set when a navigation lands on Google's unusual-traffic interstitial. Only a
# person can clear it, and every submission after it fails the same way, so the
# run stops instead of spending its whole budget discovering that ten times.
_challenge_url = None
# The canvas readback ships a base64 data URL through repeated evaluate calls.
# A 1024-wide PNG is roughly 400 KB of base64, so a 120 KB chunk cost four round
# trips per image where one is enough.
CHUNK = 600_000
RATIO_TOLERANCE = 0.04

# Elements are located by their accessible name, which the page renders in the
# browser's UI language. These are the Korean names; a browser set to another
# language will not match them, and that is what a "never appeared" failure
# below almost always means.
PROMPT_BOX_RE = re.compile(
    r"'role': 'textbox', 'name': 'Gemini 프롬프트 입력'[^}]*?'ref': '(@e\d+)'"
)
SEND_BUTTON_RE = re.compile(r"'role': 'button', 'name': '메시지 보내기', 'ref': '(@e\d+)'")
ONBOARDING_RE = re.compile(r"'role': 'button', 'name': '사용해 보기', 'ref': '(@e\d+)'")
DOWNLOAD_BUTTON_RE = re.compile(
    r"'role': 'button', 'name': '원본 크기 이미지 다운로드', 'ref': '(@e\d+)'"
)
VIEWER_CLOSE_RE = re.compile(r"'role': 'button', 'name': '닫기', 'ref': '(@e\d+)'")

# The download control does not exist beside the inline result. The result <img>
# sits inside a <button class="image-button">; clicking it opens the viewer, and
# only there do 이미지 공유 / 이미지 복사 / 원본 크기 이미지 다운로드 render.
# Skipping this step is why every earlier run fell back to the canvas copy.
OPEN_VIEWER_JS = """(() => {
  const img = [...document.querySelectorAll('img')].find(i => i.src.startsWith('blob:'));
  if (!img) return 'no-image';
  const btn = img.closest('button');
  if (!btn) return 'no-button';
  btn.click();
  return 'opened';
})()"""

# The result carries loading="lazy" and decodes only inside the viewport.
READY_JS = """(() => {
  const img = [...document.querySelectorAll('img')].find(i => i.src.startsWith('blob:'));
  if (img && img.naturalWidth < 300) {
    // Scrolling alone is not enough: the result <img> is frequently laid out at
    // zero size, and scrollIntoView on a zero-box element is a no-op, so its
    // lazy decode never fires and the row polls forever. Drop the lazy flag and
    // ask for the decode directly; decode() resolves before the next sweep.
    img.loading = 'eager';
    img.scrollIntoView({block: 'center'});
    if (img.decode) img.decode().catch(() => {});
  }
  // Two separate facts, so a run can prove which half is slow. "finished" is
  // Gemini's clock: the answer has stopped rendering. "decoded" is ours: the
  // bytes are readable. When finished runs far ahead of decoded, the delay is a
  // detection bug on this side, not generation latency on theirs.
  const creating = document.body.innerText.includes('Creating your image');
  return JSON.stringify({
    present: !!img,
    creating: creating,
    finished: !!img && !creating,
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


def human_pause(low: float, high: float) -> None:
    """Sleep a random beat inside [low, high].

    Fixed intervals are a machine signature. Google served its unusual-traffic
    challenge after a run whose every step was metronomic, so the waits that a
    person would vary are varied here too.
    """
    time.sleep(random.uniform(low, high))


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


def evaluate(code: str, session: str):
    """The evaluated value, or None when the bridge itself did not answer.

    Returning "" for both cases made a flaky daemon indistinguishable from a tab
    showing nothing, which is what starts the dead-row clock — so a hiccup could
    retire a healthy row 75 seconds later."""
    result = call("evaluate", {"code": code}, session)
    return result["data"]["value"] if result.get("ok") else None


def snapshot(session: str) -> str:
    return str(call("snapshot", {}, session).get("data", {}).get("tree", ""))


def current_url(session: str) -> str:
    return evaluate("location.href", session) or ""


def with_ratio(prompt: str, ratio: str) -> str:
    """Put the ratio line in front of the prompt, once.

    The skill also tells whoever writes the manifest that the ratio has to ride
    in the prompt's first line, so manifests turn up with it already there and
    this prepended a second identical sentence, sent verbatim to the page. The
    line belongs to this path alone — image_gen.py passes aspect_ratio to its
    backend as a parameter — so it is added here, and only if it is missing."""
    lead = RATIO_PREFIX.format(ar=ratio)
    if prompt.lstrip().startswith(lead.strip()):
        return prompt
    # A prompt carrying a *different* ratio is a manifest error, not something
    # to paper over: the two sentences would contradict each other on the page.
    stale = RATIO_LINE_RE.match(prompt.lstrip())
    if stale and stale.group(1) != ratio:
        log(f"  ** prompt opens with a {stale.group(1)} ratio line but the row "
            f"asks for {ratio}; sending the row's ratio in front of it")
    return lead + prompt


def slot_name(index: int) -> str:
    return f"{SESSION_PREFIX}-{index + 1}"


def require_daemon() -> None:
    """Stop on the first precondition, in the log's own voice.

    Raising here printed a traceback over an otherwise careful log, which reads
    as a crash rather than as the gate doing its job."""
    if not call("list_tabs", {}, SESSION_PREFIX).get("ok"):
        log("Kimi WebBridge is not answering on 127.0.0.1:10086. Start the "
            "daemon and confirm the browser extension is connected, then rerun. "
            "Nothing was submitted and the manifest is untouched.")
        sys.exit(1)


def aspect_ratio_value(text: str) -> float:
    try:
        width, height = text.split(":")
        return float(width) / float(height)
    except (ValueError, ZeroDivisionError):
        return 0.0


SUBMITTED_JS = """(() => {
  const url = location.href;
  const t = document.body.innerText;
  return JSON.stringify({
    conv: url.includes('/app/'),
    // A conversation URL alone is not proof: the tab reaches /app/<id> with a
    // blank body when the send is dropped. The answer having started — an image
    // element, or the model saying it is working — is the real signal.
    answering: t.includes('Creating your image')
               || !![...document.querySelectorAll('img')].find(i => i.src.startsWith('blob:'))
  });
})()"""


def submission_took(session: str, tries: int = 9) -> bool:
    """True once the tab holds a conversation that has actually begun answering."""
    for i in range(tries):
        if i:
            human_pause(0.8, 1.6)
        try:
            state = json.loads(evaluate(SUBMITTED_JS, session) or "{}")
        except ValueError:
            state = {}
        if state.get("conv") and state.get("answering"):
            return True
    return False


def submit(item: dict, session: str) -> bool:
    """Open this slot's tab and send its prompt."""
    prompt = with_ratio(item["prompt"], item["aspect_ratio"])

    # One retry: the bridge answers a navigate with a plain failure for a beat
    # after tabs are closed, and losing the row to a transient blip is worse than
    # spending two seconds.
    for attempt in range(2):
        if call("navigate", {"url": IMAGES_URL, "newTab": True}, session).get("ok"):
            break
        if attempt == 0:
            time.sleep(2)
            continue
        log(f"  navigate failed twice for {item['filename']}")
        return False

    global _challenge_url
    box = None
    for attempt in range(15):
        human_pause(1.4, 2.6)
        tree = snapshot(session)
        onboarding = ONBOARDING_RE.search(tree)
        if onboarding:
            call("click", {"selector": onboarding.group(1)}, session)
            continue
        found = PROMPT_BOX_RE.search(tree)
        if found:
            box = found.group(1)
            break
        # Three misses is enough to stop assuming the page is merely slow. The
        # abuse interstitial has no prompt box either, and waiting out fifteen
        # polls on every remaining row is how one challenge consumed a whole run
        # while the log blamed the browser's UI language.
        if attempt == 2:
            url = current_url(session)
            if "/sorry/" in url:
                _challenge_url = url
                log(f"  Google served its unusual-traffic challenge at {url}")
                return False
    if not box:
        log(f"  prompt box never appeared for {item['filename']} — the page may "
            "still be loading, the session may be signed out, or the browser's "
            "UI language may not be Korean (this skill matches Korean labels)")
        return False

    if not call("fill", {"selector": box, "value": prompt}, session).get("ok"):
        log(f"  fill failed for {item['filename']}")
        return False

    # A person reads what they typed before sending.
    human_pause(0.5, 1.4)

    # The send button renders only once the box holds text.
    send = None
    for _ in range(10):
        human_pause(0.7, 1.5)
        found = SEND_BUTTON_RE.search(snapshot(session))
        if found:
            send = found.group(1)
            break
    if not send:
        log(f"  send button never appeared for {item['filename']} — check the "
            "browser's UI language if the prompt box was found by luck")
        return False

    if not call("click", {"selector": send}, session).get("ok"):
        log(f"  send click failed for {item['filename']}")
        return False

    # The send click reports success even when the page never accepts it: the
    # prompt stays in the box, no conversation is created, and the row then
    # sweeps until the deadline for an image nobody asked for. A real submission
    # leaves /images for a conversation URL, so that is what gets verified.
    if not submission_took(session):
        log(f"  send did not take for {item['filename']}; retrying once")
        human_pause(1.0, 2.0)
        # The failure this retry exists for leaves the tab on a blank /app/<id>,
        # so the box reference captured on /images no longer addresses anything.
        # Find the box again on whatever page the tab is actually showing.
        tree = snapshot(session)
        again_box = PROMPT_BOX_RE.search(tree)
        if not again_box:
            log(f"  no prompt box to retry into for {item['filename']}")
            return False
        if not call("fill", {"selector": again_box.group(1),
                             "value": prompt}, session).get("ok"):
            log(f"  refill failed for {item['filename']}")
            return False
        human_pause(0.6, 1.4)
        again = SEND_BUTTON_RE.search(snapshot(session))
        if not again or not call("click", {"selector": again.group(1)}, session).get("ok"):
            log(f"  resend failed for {item['filename']}")
            return False
        if not submission_took(session):
            log(f"  send never took for {item['filename']} — leaving it Pending")
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


def clear_downloads_since(after: float) -> None:
    """Remove every downloaded original newer than `after`.

    One click can produce more than one file, and a click that timed out can
    still land its file a moment later. Anything left behind both fails the
    run's own "no leftovers" check and makes the next row's newest-since test
    read a stale file as its own."""
    for path in DOWNLOADS.glob(DOWNLOAD_GLOB):
        try:
            if path.stat().st_mtime > after:
                path.unlink(missing_ok=True)
        except OSError:
            continue


def png_size(raw: bytes) -> tuple:
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    return (int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big"))


def close_viewer(session: str) -> None:
    """Leave the tab as it was found; a viewer left open hides the next probe."""
    found = VIEWER_CLOSE_RE.search(snapshot(session))
    if found:
        call("click", {"selector": found.group(1)}, session)


def export_to(dest: Path, session: str) -> tuple:
    """Save this slot's image into dest. Returns (width, height, bytes).

    The page's download control is tried first because it hands over the
    original file. Its click reports success even when the browser refuses the
    download, so a file's arrival is the only proof, and the canvas readback
    covers the refusal."""
    global _download_refused
    dest.parent.mkdir(parents=True, exist_ok=True)
    clicked = False

    if not _download_refused:
        started = time.time()
        opened = evaluate(OPEN_VIEWER_JS, session)
        found = None
        if opened == "opened":
            # The viewer animates in; the action bar is not in the tree yet.
            for i in range(7):
                if i:
                    human_pause(0.35, 0.8)
                found = DOWNLOAD_BUTTON_RE.search(snapshot(session))
                if found:
                    break

        if found:
            clicked = True
            human_pause(0.3, 0.9)
            call("click", {"selector": found.group(1)}, session)
            landed = None
            for _ in range(DOWNLOAD_WAIT):
                time.sleep(1)
                landed = newest_download(started)
                if landed:
                    break
            if landed:
                # A multi-megabyte PNG is still growing when it first appears.
                # One comparison a second apart called that a refusal, dropped
                # the row to the canvas copy, and left the partial behind.
                size = -1
                for _ in range(8):
                    time.sleep(1)
                    now = landed.stat().st_size
                    if now and now == size:
                        break
                    size = now
                if size > 0 and landed.stat().st_size == size:
                    raw = landed.read_bytes()
                    dest.write_bytes(raw)
                    took = time.time() - started
                    # One click can produce more than one file; clear them all so
                    # the next row's "newest since" test stays honest.
                    clear_downloads_since(started)
                    close_viewer(session)
                    log(f"    original file via the viewer download ({took:.0f}s)")
                    return png_size(raw) + (len(raw),)

        close_viewer(session)
        # A partial may be sitting in ~/Downloads either way; leaving it there
        # fails the run's own "no leftovers" check and poisons the next row's
        # newest-since test.
        clear_downloads_since(started)
        if clicked:
            # The control was there and was clicked, and no file arrived. That is
            # the browser refusing, and it will refuse every later row too.
            _download_refused = True
            log("    the browser refused the download; reading the rendered "
                "image instead, and not attempting it again this run")
        else:
            # The viewer did not open, or its action bar never rendered. That is
            # this row's bad luck, not a browser setting — the next row still
            # gets its chance at the original.
            why = ("the viewer opened but its download control never rendered"
                   if opened == "opened" else f"the viewer never opened ({opened})")
            log(f"    {why}; reading the rendered image for this row only")

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
    try:
        raw = base64.b64decode(data_url.split(",", 1)[1], validate=True)
    except (ValueError, binascii.Error):
        # A chunk that came back empty truncates the data URL mid-character.
        # The row is retried on the next sweep; crashing here would abandon
        # every other slot that is still open.
        return ()
    dest.write_bytes(raw)
    _canvas_rows.append(dest.name)
    return meta["w"], meta["h"], len(raw)


def collect(manifest: dict, manifest_path: Path, out_dir: Path,
            slots: list, deadline_at: float) -> int:
    """Sweep every slot's own tab, repeatedly, until each gives up its image.

    A slot is checked once per sweep and never blocks the others. The first
    version waited on each slot in turn for its full share of the budget, so a
    slow slot spent that share while the rest finished behind it — and because
    the sweep never came back, two images that completed during that wait were
    reported as failures with the files sitting ready in their tabs.
    """
    remaining = list(slots)
    saved = 0
    deadline = deadline_at
    started = time.time()
    sweep = 0
    finished_at = {}
    dead_since = {}

    while remaining and time.time() < deadline:
        sweep += 1
        still_waiting = []

        # Poll every slot at once. Serially this cost one round trip per slot per
        # sweep, so a ten-slot sweep took longer than the interval between them
        # and the "every 5s" cadence was a fiction.
        def probe(pair):
            index, _item = pair
            raw = evaluate(READY_JS, slot_name(index))
            if raw is None:
                # The bridge did not answer. That says nothing about the tab, so
                # the row is left alone rather than aged toward being dropped.
                return False, False, None
            try:
                state = json.loads(raw) if raw else {}
            except ValueError:
                state = {}
            alive = bool(state.get("present")) or bool(state.get("creating"))
            return bool(state.get("finished")), bool(state.get("decoded")), alive

        with ThreadPoolExecutor(max_workers=max(1, len(remaining))) as pool:
            states = list(pool.map(probe, remaining))

        for (index, item), (is_finished, is_ready, alive) in zip(remaining, states):
            session = slot_name(index)
            if is_finished and item["filename"] not in finished_at:
                finished_at[item["filename"]] = time.time() - started

            # A tab that shows neither an image nor "Creating your image" is not
            # slow, it is empty: the send was dropped and the conversation opened
            # blank. Two such rows once ate the entire remaining budget while the
            # sweep waited for an image nobody was making.
            if alive is None:
                still_waiting.append((index, item))
                continue
            if alive:
                dead_since.pop(item["filename"], None)
            else:
                first = dead_since.setdefault(item["filename"], time.time())
                if time.time() - first > DEAD_ROW_GRACE:
                    item["last_error"] = ("gemini-web: conversation opened but no "
                                          "answer ever started; resubmit this row")
                    # Its tab is blank, so a later --collect-only must not be
                    # pointed back at it.
                    item.pop("slot", None)
                    log(f"  {item['filename']}: no answer started — dropping it "
                        f"so it stops spending the budget")
                    continue

            if not is_ready:
                still_waiting.append((index, item))
                continue

            got = export_to(out_dir / item["filename"], session)
            if not got:
                # Kept in the sweep rather than dropped: the overall budget bounds
                # the retries, and dropping it here silently ended the row's run.
                item["last_error"] = "gemini-web: image could not be extracted yet"
                log(f"  {item['filename']}: extraction failed, retrying next sweep")
                still_waiting.append((index, item))
                continue

            width, height, size = got
            actual = width / height if height else 0
            target = aspect_ratio_value(item["aspect_ratio"])
            if not target:
                # Returning 0.0 for an unparseable ratio made drift 0 as well,
                # so the row whose ratio field was broken was the one row whose
                # ratio nobody checked.
                note = ("  ** aspect_ratio "
                        f"{item['aspect_ratio']!r} is not W:H — ratio unchecked")
                drift = 0
            else:
                drift = abs(actual - target) / target
                note = ("" if drift <= RATIO_TOLERANCE
                        else "  ** ratio off, review this row")
            read_at = time.time() - started
            gen_at = finished_at.get(item["filename"])
            lag = ("" if gen_at is None
                   else f", gemini done at {gen_at:.0f}s, lag {read_at - gen_at:.0f}s")
            log(f"  saved {item['filename']} {width}x{height} "
                f"ratio {actual:.3f} vs {item['aspect_ratio']} ({size:,} bytes) "
                f"[sweep {sweep}, read at {read_at:.0f}s{lag}]{note}")

            item["status"] = "Generated"
            item.pop("last_error", None)
            item.pop("slot", None)
            saved += 1
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")

        remaining = still_waiting
        if remaining:
            log(f"  sweep {sweep}: {len(remaining)} still generating")
            human_pause(SWEEP_INTERVAL * 0.7, SWEEP_INTERVAL * 1.4)

    for _index, item in remaining:
        item["last_error"] = "gemini-web: still generating when the deadline expired"
        log(f"  {item['filename']}: not ready before the deadline — left Pending")

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
    parser.add_argument("--batch", type=int, default=10,
                        help="Rows submitted in one pass, one tab each (default 10). "
                             "Ten measured 245s at the displayed size end to end, inside the default "
                             "deadline, and concurrency showed no per-image "
                             "penalty: nine finished within 85s and the tenth was "
                             "one slow generation on Gemini's side. Splitting a "
                             "ten-row deck into passes only repeats the ~48s "
                             "submission. Lower it if a run hits Google's "
                             "unusual-traffic challenge (see the skill's §7)")
    parser.add_argument("--generate-wait", type=int, default=10,
                        help="Seconds to settle before the first sweep (default 10). "
                             "A single image was ready about 28s after submit, so a "
                             "long pre-wait is dead time; sweeping early costs one "
                             "cheap probe per slot")
    parser.add_argument("--deadline", type=int, default=300,
                        help="Hard wall-clock budget for the whole run in seconds "
                             "(default 300). Measured from process start and "
                             "covering submission, generation, and download. When "
                             "it expires the run stops and reports what is missing "
                             "rather than dragging on")
    parser.add_argument("--displayed-size", action="store_true",
                        help="Skip the viewer download and keep the canvas copy "
                             "(1024px instead of 2752px). Trades resolution for "
                             "roughly 12s per row — reach for it only when the "
                             "deadline matters more than the pixels")
    parser.add_argument("--collect-only", action="store_true",
                        help="Skip submission and read the slots already open")
    args = parser.parse_args()

    run_started = time.time()
    deadline_at = run_started + args.deadline

    global _download_refused
    if args.displayed_size:
        _download_refused = True

    require_daemon()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir = Path(args.output).resolve() if args.output else manifest_path.parent

    # The same statuses image_gen.py retries. Selecting on "not Generated"
    # instead swept in Needs-Manual rows — the figures the user supplies by
    # hand — and would have sent them to Gemini as prompts.
    pending = [it for it in manifest["items"] if it["status"] in RETRYABLE]
    if not pending:
        manual = sum(1 for it in manifest["items"]
                     if it["status"] == "Needs-Manual")
        tail = (f"; {manual} row(s) are Needs-Manual and wait for the user's own "
                "files" if manual else "")
        log(f"nothing to do — no Pending or Failed rows{tail}")
        return

    batch = pending[:args.batch]
    if len(pending) > len(batch):
        log(f"{len(pending)} rows pending; taking {len(batch)} this pass")

    if args.collect_only:
        slots = [(it["slot"], it) for it in batch if isinstance(it.get("slot"), int)]
        missing = [it["filename"] for it in batch if not isinstance(it.get("slot"), int)]
        if missing:
            log("no recorded slot for " + ", ".join(missing) +
                " — these rows were never submitted from this manifest, so their "
                "tabs cannot be identified. Resubmit them instead of collecting.")
        if not slots:
            log("nothing to collect")
            return
    else:
        log(f"submitting {len(batch)} prompt(s), one tab each")
        submit_started = time.time()
        slots = []
        for i, item in enumerate(batch):
            if time.time() >= deadline_at:
                # Only collect() used to check this, so a slow submission spent
                # the whole budget and every row was then reported as "still
                # generating when the deadline expired" — blaming Gemini for
                # time this loop had already spent.
                log(f"  deadline reached during submission; {len(batch) - i} "
                    "row(s) were never sent and stay as they were")
                break
            if i:
                human_pause(1.0, 2.6)
            if not submit(item, slot_name(i)):
                # An earlier attempt's slot would otherwise survive the write-back
                # below and point --collect-only at a tab this row does not own.
                item.pop("slot", None)
                if _challenge_url:
                    log("  stopping: only a person can clear that challenge. "
                        "Open the tab, clear it, then rerun — rows already "
                        "generating are unaffected")
                    break
                continue
            # The slot is written down because a later --collect-only cannot
            # recompute it: by then some rows are Generated, so re-numbering the
            # survivors points them at other rows' tabs.
            item["slot"] = i
            slots.append((i, item))
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        log(f"{len(slots)} submitted in {time.time() - submit_started:.0f}s; "
            f"settling {args.generate_wait}s before the first sweep")
        time.sleep(args.generate_wait)

    saved = collect(manifest, manifest_path, out_dir, slots, deadline_at)
    elapsed = time.time() - run_started
    total = sum(1 for it in manifest["items"] if it["status"] == "Generated")
    verdict = "within" if elapsed <= args.deadline else "OVER"
    log(f"saved {saved} this run · manifest {total}/{len(manifest['items'])} · "
        f"{elapsed:.0f}s elapsed ({verdict} the {args.deadline}s deadline)")
    if _canvas_rows and not args.displayed_size:
        # Never let this be silent again: the fallback works, so a run that took
        # it end to end still reports success while every image is 1024px.
        log(f"** {len(_canvas_rows)} of {saved} row(s) fell back to the 1024px "
            f"rendered copy instead of the original: {', '.join(_canvas_rows)}")
    if elapsed > args.deadline:
        log("over budget — lower --batch and re-measure. Note which rows were "
            "slow: a row whose tab shows a finished answer is a detection "
            "problem, not a generation one")
    elif len(slots) != saved:
        recoverable = sum(1 for _i, it in slots
                          if isinstance(it.get("slot"), int)
                          and it["status"] != "Generated")
        log(f"finished inside the deadline with {len(slots) - saved} row(s) "
            f"unsaved; {recoverable} still hold a slot and can be picked up with "
            "--collect-only. The rest lost their tab and have to be resubmitted")


if __name__ == "__main__":
    main()
