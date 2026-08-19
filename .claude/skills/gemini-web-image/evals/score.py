#!/usr/bin/env python3
"""Score one experiment's plans against the gemini-web-image eval suite.

Usage: python3 score.py runs/exp-N
"""
import json
import re
import sys
from pathlib import Path

NEGATION = re.compile(
    r"never|not use|don't|do not|avoid|forbidden|instead of|rather than"
    r"|금지|쓰지|사용하지|대신", re.IGNORECASE)

# Plans are markdown. Emphasis lands mid-phrase ("do **not** use", "Submits
# **all** rows first") and split every phrase match until it was stripped.
MARKUP = re.compile(r"[*`_]+")


def flatten(text):
    return MARKUP.sub("", text)


def lines_with(text, needle):
    return [ln for ln in flatten(text).splitlines() if needle.lower() in ln.lower()]


def b1_no_find_tab(text, sid):
    """find_tab must never appear as an action — it silently fails to switch."""
    hits = lines_with(text, "find_tab")
    if not hits:
        return True
    return all(NEGATION.search(ln) for ln in hits)


def b2_download_first(text, sid):
    """The original file is worth one attempt before reading the rendered copy."""
    if sid == "S3":
        return None
    return bool(re.search(
        r"원본 크기 이미지 다운로드|download (?:control|button)|Gemini_Generated_Image",
        flatten(text), re.I))


def b8_lazy_scroll(text, sid):
    """naturalWidth 0 means not yet in the viewport, not a dead conversation."""
    if sid in {"S3", "S6"}:
        return None
    return bool(re.search(r"scrollIntoView|scroll .{0,25}(?:into view|viewport)"
                          r"|lazy|뷰포트|스크롤", flatten(text), re.I))


def b3_click_unproven(text, sid):
    """A click that reports success proves nothing; the file's arrival does."""
    if sid == "S3":
        return None
    flat = flatten(text)
    return bool(re.search(
        r"canvas|toDataURL|drawImage|fall (?:back|through)|fallback|대체 ?경로",
        flat, re.I)) and bool(re.search(
        r"~/Downloads|file .{0,30}(?:lands|arriv)|아무 ?것도 ?안|파일이 ?(?:안|도착)",
        flat, re.I))


def b4_session_per_row(text, sid):
    """One bridge session per row is what pins a tab to a row."""
    if sid == "S3":
        return None
    return bool(re.search(
        r"one session per row|session per (?:row|image|slot)|ppt-master-image-"
        r"|slot_name|세션.{0,10}(?:하나|당|per)|슬롯", flatten(text), re.I))


def b9_no_slot_navigation(text, sid):
    """Re-opening a slot's conversation is what breaks this path."""
    if sid == "S3":
        return None
    flat = flatten(text)
    return bool(re.search(
        r"n(?:ever|o|ot) [^.]{0,40}(?:navigat|reload|re-open|re-?fetch)"
        r"|without (?:re-?load|navigating)"
        r"|이동하지|새로고침하지|재방문하지", flat, re.I))


def b5_ratio_line(text, sid):
    # Only scenarios that actually submit a prompt can carry the ratio line.
    if sid in {"S3", "S5", "S6", "S7"}:
        return None
    return bool(re.search(r"aspect ratio exactly|RATIO_PREFIX|비율.{0,12}첫 ?줄",
                          flatten(text), re.I))


def b7_precondition_stop(text, sid):
    if sid != "S3":
        return None
    flat = flatten(text)
    stops = re.search(r"stop|halt|abort|report .{0,30}(?:precondition|failure)"
                      r"|중단|보고", flat, re.I)
    # The skill's own error string tells the user to start the daemon, so a plan
    # that quotes it is not improvising. Only an unquoted action counts.
    # A plan that repeats the skill's own error text is not improvising. Quoted
    # lines, blockquotes, and lines attributing the words to the skill or script
    # all read as citation.
    quoted = re.compile(
        r"^\s*>|[\"\u201c\u201d]|message|raises|error string|report"
        r"|the (?:skill|script|adapter) (?:says|states|prints|reports)"
        r"|remedy|guidance|wording", re.I)
    improvises = any(
        re.search(r"start the daemon|launch the daemon|brew install|npm install", ln, re.I)
        and not quoted.search(ln)
        for ln in flat.splitlines())
    return bool(stops) and not improvises


BINARY = [
    ("B1_no_find_tab", b1_no_find_tab),
    ("B2_download_first", b2_download_first),
    ("B3_click_unproven", b3_click_unproven),
    ("B4_session_per_row", b4_session_per_row),
    ("B5_ratio_in_prompt", b5_ratio_line),
    ("B7_precondition_stop", b7_precondition_stop),
    ("B8_lazy_scroll", b8_lazy_scroll),
    ("B9_no_slot_navigation", b9_no_slot_navigation),
]


def main():
    run_dir = Path(sys.argv[1])
    results, passes, applicable = {}, 0, 0
    for plan in sorted(run_dir.glob("S*.md")):
        sid = plan.stem
        text = plan.read_text(encoding="utf-8")
        row = {}
        for name, fn in BINARY:
            verdict = fn(text, sid)
            if verdict is None:
                row[name] = "n/a"
                continue
            applicable += 1
            passes += bool(verdict)
            row[name] = bool(verdict)
        results[sid] = row

    summary = {
        "binary_passes": passes,
        "binary_applicable": applicable,
        "binary_pass_rate": round(passes / applicable, 4) if applicable else 0.0,
        "per_scenario": results,
    }
    (run_dir / "scores.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
