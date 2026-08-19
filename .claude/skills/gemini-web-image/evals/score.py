#!/usr/bin/env python3
"""Score one experiment's plans against the gemini-web-image eval suite.

Usage: python3 score.py runs/exp-N
"""
import json
import re
import sys
from pathlib import Path

# "No find_tab, ever" and "no find_tab anywhere" are negations, and three plans
# were failed for writing them that way. \bno\b does not match "not"/"nothing",
# so the bare quantifier can be added without swallowing unrelated prose.
NEGATION = re.compile(
    r"never|\bno\b|not use|don't|do not|avoid|forbidden|instead of|rather than"
    r"|금지|쓰지|사용하지|대신", re.IGNORECASE)

# Plans are markdown. Emphasis lands mid-phrase ("do **not** use", "Submits
# **all** rows first") and split every phrase match until it was stripped.
# Underscores are deliberately kept: stripping them turned RATIO_PREFIX into
# RATIOPREFIX and Gemini_Generated_Image into GeminiGeneratedImage, so every
# check that named a snake_case identifier could never fire. Four plans that
# quoted those identifiers exactly were scored as failures on that alone.
MARKUP = re.compile(r"[*`]+")

# Where a paragraph starts, for unwrapping.
BLOCK_START = re.compile(r"^\s*(?:[-*+>|#]|\d+[.)])")


def flatten(text):
    return MARKUP.sub("", text)


def logical_lines(text):
    """Undo the hard wrapping before any per-line test runs.

    Plans are wrapped at ~78 columns, so a sentence is routinely split across
    two lines and a per-line test sees half of it. That misread S3: the plan
    quoted the script's own "Start the daemon" error, the opening quotation mark
    fell on one line and the imperative on the next, and the line carrying the
    imperative looked like the plan improvising. The same hazard applies to
    every check that pairs a term with a qualifier on its line.
    """
    out = []
    for raw in flatten(text).splitlines():
        if not raw.strip():
            out.append("")
        elif out and out[-1].strip() and not BLOCK_START.match(raw):
            out[-1] = out[-1].rstrip() + " " + raw.strip()
        else:
            out.append(raw)
    return out


LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def contextual_lines(text):
    """Each logical line, carrying the structure that qualifies it.

    Plans state a prohibition once, in a table header ("| Do not | Why |") or a
    heading ("Things I deliberately do not do"), and then list the forbidden
    calls plainly underneath. Read alone, those rows are indistinguishable from
    instructions, and two plans that forbade find_tab in exactly this shape were
    scored as planning to call it. A table row is therefore read together with
    its header row, and a list item with whatever introduced the list.
    """
    out, table_header, list_intro = [], "", ""
    for line in logical_lines(text):
        stripped = line.strip()
        is_row = stripped.startswith("|")
        if not is_row:
            table_header = ""
        elif not table_header:
            table_header = stripped
        if stripped and not is_row and not LIST_ITEM.match(line):
            list_intro = stripped

        if is_row and table_header != stripped:
            out.append(table_header + " ¦ " + line)
        elif LIST_ITEM.match(line):
            out.append(list_intro + " ¦ " + line)
        else:
            out.append(line)
    return out


def lines_with(text, needle):
    return [ln for ln in contextual_lines(text) if needle.lower() in ln.lower()]


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


def b8_force_decode(text, sid):
    """naturalWidth 0 is an undecoded image, not a dead conversation.

    Scrolling alone was the old remedy and it does not work: the result element
    is routinely laid out at zero size, where scrollIntoView is a no-op. A plan
    that only says "scroll it into view" is repeating the superseded advice, so
    the eager/decode remedy is what earns the point; the lazy vocabulary alone
    no longer does.
    """
    if sid in {"S3", "S6"}:
        return None
    flat = flatten(text)
    # "force the decode" names the same remedy without quoting the two calls,
    # and it is still incompatible with the superseded "scroll it into view".
    return bool(re.search(
        r"loading\s*=\s*['\"]?eager|\.decode\(\)|eager"
        r"|forc\w*\s+the\s+decode|디코드를?\s*강제",
        flat, re.I))


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


def b10_recorded_slot(text, sid):
    """A slot recomputed at collect time points at another row's tab."""
    if sid not in {"S2", "S7"}:
        return None
    flat = flatten(text)
    # Either the plan follows the rule (use the slot written down at submit
    # time) or it names the hazard (recomputing slots at collect time points a
    # row at another row's tab). Both show the same understanding.
    follows = re.search(
        r"recorded slot|slot.{0,25}(?:written|recorded|persisted|manifest)"
        r"|item\[.slot.\]", flat, re.I)
    spots = any(
        re.search(r"collect[- ]?only", ln, re.I)
        and re.search(r"enumerat|index 0|slot_name\(0\)|re-?number", ln, re.I)
        for ln in logical_lines(text))
    return bool(follows or spots)


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
        for ln in logical_lines(text))
    return bool(stops) and not improvises


BINARY = [
    ("B1_no_find_tab", b1_no_find_tab),
    ("B2_download_first", b2_download_first),
    ("B3_click_unproven", b3_click_unproven),
    ("B4_session_per_row", b4_session_per_row),
    ("B5_ratio_in_prompt", b5_ratio_line),
    ("B7_precondition_stop", b7_precondition_stop),
    ("B8_force_decode", b8_force_decode),
    ("B9_no_slot_navigation", b9_no_slot_navigation),
    ("B10_recorded_slot", b10_recorded_slot),
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
