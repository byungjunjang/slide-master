#!/usr/bin/env python3
"""text_fit.py — pre-draw line-fit oracle for hand-authored SVG text.

Speed accelerator (Executor). Answers "does this text fit on one line in this
zone, or must it wrap?" *before* you write the <text>, so you skip the
write -> svg_quality_checker warning -> edit loop.

The width model is copied VERBATIM from svg_quality_checker.py
(`_geom_char_width` / `_geom_text_width`): CJK/full-width glyph = 1.0 x fs,
Latin letter/digit/ASCII punct = 0.55 x fs, ASCII space = 0.25 x fs, plus
letter-spacing x (chars-1). The wrap verdict mirrors the checker's
`_check_text_geometry`:  est_width <= available  =>  ONE LINE ; otherwise WRAP.
Keep this file in sync if the checker constants ever change.

Zone / available width:
  available = right_bound - x
  right_bound defaults to  vb_width - vb_width * 0.05  (the checker's 5% content
  margin; 1216 on a 1280 canvas). Pass --zone to give `available` directly, or
  --x (+ optional --right-bound / --vb-width) to have it derived.

Vertical / collision (stack mode): the same pre-draw contract for the
checker's A-class errors. Line i baseline = y + i*dy; line box top/bottom =
baseline -+ GEOM_ASCENT/GEOM_DESCENT x fs (verbatim from the checker). A
STACK finding here == a checker `error` after drawing: CANVAS_V (exceeds the
canvas vertically), CANVAS_H (right/left canvas overflow), COLLIDE (edge-
crossing intrusion into another group's box), BOUND (declared bottom_bound
overshoot — the pre-draw stand-in for a collision with the element below).

Usage:
  # direct zone width
  text_fit.py "학습지와 평가지를 몇 분 만에" --font-size 40 --zone 1136

  # derive available from x on a 1280 canvas (right margin auto)
  text_fit.py "문항·정답·해설·활동지까지 초안 생성" --font-size 24 --x 560

  # right column bounded by a divider/right edge
  text_fit.py "..." --font-size 24 --x 560 --right-bound 1208

  # vertical: does this 3-line body block clear the footer at y=668?
  text_fit.py "본문 첫 줄" --font-size 24 --x 72 --y 520 --dy 34 \
      --num-lines 3 --bottom-bound 668

  # batch (legacy list form): JSON array of {text|lines, font_size, x?|zone?,
  #         right_bound?, vb_width?, letter_spacing?, label?}
  text_fit.py --batch blocks.json

  # batch (page form) — ONE call pre-checks the whole page: width + vertical
  # + cross-block collision. JSON object:
  #   {"vb_width": 1280, "vb_height": 720,
  #    "blocks": [{"label": "title", "x": 72, "y": 96, "dy": 0,
  #                "font_size": 40, "lines": ["페이지 제목"]},
  #               {"label": "body", "x": 72, "y": 520, "dy": 34,
  #                "font_size": 24, "lines": ["첫 줄", "둘째 줄"],
  #                "bottom_bound": 668}],
  #    "obstacles": [{"label": "footer", "box": [72, 668, 1208, 700]}]}
  text_fit.py --batch page.json
"""
from __future__ import annotations

import argparse
import json
import sys

# --- width model (verbatim from svg_quality_checker.py) ---------------------
GEOM_CJK_WIDTH = 1.0
GEOM_LATIN_WIDTH = 0.55
GEOM_SPACE_WIDTH = 0.25
GEOM_MARGIN_RATIO = 0.05
GEOM_CONSERVATIVE = 0.95    # shrink width estimates before firing errors
GEOM_ASCENT = 0.8           # line-box rise above baseline, x font-size
GEOM_DESCENT = 0.2          # line-box drop below baseline, x font-size
GEOM_MIN_OVERLAP = 4.0      # px; ignore hairline intersections
_GEOM_CJK_EXTRA = set('—…「」『』《》〈〉【】〔〕')


def _char_width(ch: str, font_size: float) -> float:
    if ch in (' ', ' '):
        return GEOM_SPACE_WIDTH * font_size
    cp = ord(ch)
    if (
        0x1100 <= cp <= 0x11FF       # Hangul jamo
        or 0x2E80 <= cp <= 0xA4CF    # CJK radicals / kana / unified ideographs
        or 0xAC00 <= cp <= 0xD7AF    # Hangul syllables
        or 0xF900 <= cp <= 0xFAFF    # CJK compatibility ideographs
        or 0xFE30 <= cp <= 0xFE4F    # CJK compatibility forms
        or 0xFF00 <= cp <= 0xFF60    # full-width forms
        or ch in _GEOM_CJK_EXTRA
    ):
        return GEOM_CJK_WIDTH * font_size
    return GEOM_LATIN_WIDTH * font_size


def text_width(s: str, font_size: float, letter_spacing: float = 0.0) -> float:
    if not s:
        return 0.0
    width = sum(_char_width(ch, font_size) for ch in s)
    if letter_spacing and len(s) > 1:
        width += letter_spacing * (len(s) - 1)
    return width


# --- fit / break planning ---------------------------------------------------
def _balanced_break(text: str, font_size: float, letter_spacing: float,
                    available: float):
    """Suggest a 2-line split at a space boundary minimizing the longer line,
    keeping line 1 within `available` when possible. Returns (l1, l2) or None
    when the text has no interior space to break on."""
    spaces = [i for i, ch in enumerate(text) if ch == ' ']
    if not spaces:
        return None
    best = None
    for i in spaces:
        l1, l2 = text[:i].rstrip(), text[i + 1:].lstrip()
        if not l1 or not l2:
            continue
        w1 = text_width(l1, font_size, letter_spacing)
        w2 = text_width(l2, font_size, letter_spacing)
        longer = max(w1, w2)
        fits = w1 <= available and w2 <= available
        # prefer splits where both fit; then minimize the longer line
        key = (0 if fits else 1, longer)
        if best is None or key < best[0]:
            best = (key, (l1, l2, w1, w2))
    return best[1] if best else None


def evaluate_wrap(lines, font_size: float, *, x: float | None = None,
                  right_bound: float | None = None, vb_width: float = 1280.0,
                  letter_spacing: float = 0.0, label: str | None = None) -> dict:
    """Checker-parity oracle for an *intended multi-line block*.

    Mirrors svg_quality_checker `_geom_b_checks`: a wrapped <text> block whose
    joined text fits on one line at the block's available width is flagged
    ("wraps into N lines but fits on one"). The checker's available width is
    ``full_canvas_right_bound - x`` UNLESS a sibling SHAPE (rect/line/icon)
    sits to the block's right within its y-band and narrows it — a column
    separated only by whitespace is NOT narrowed, so the checker measures the
    full canvas. Pass the same ``right_bound`` you will actually bound the
    column with (e.g. a vertical divider x, or the next column's left edge) to
    model that; omit it to get the pessimistic full-canvas verdict the checker
    uses when no bounding shape exists.

    CHECKER_FLAG  -> joined text fits one line at `available`; the checker WILL
                     warn. Draw one line, add a right-edge shape spanning the
                     block's y-band so the checker bounds the column, or split
                     into separate <text> paragraphs (each its own block).
    CHECKER_OK    -> joined text exceeds `available`; the wrap is justified.
    """
    lines = [str(s) for s in lines if str(s)]
    n = max(len(lines), 2)
    xs = 0.0 if x is None else float(x)
    rb = right_bound if right_bound is not None else (
        vb_width - vb_width * GEOM_MARGIN_RATIO)
    available = float(rb) - xs
    joined = ' '.join(lines)
    full_w = text_width(joined, font_size, letter_spacing)
    flags = full_w <= available if available > 0 else False
    return {
        'label': label,
        'mode': 'wrap',
        'text': joined,
        'lines': lines,
        'font_size': font_size,
        'letter_spacing': letter_spacing,
        'est_width': round(full_w, 1),
        'available': round(available, 1),
        'right_bound': round(float(rb), 1),
        'fits_one_line': flags,            # True == checker flags the wrap
        'lines_needed': n,
        'verdict': 'CHECKER_FLAG' if flags else 'CHECKER_OK',
    }


def evaluate(text: str, font_size: float, *, zone: float | None = None,
             x: float | None = None, right_bound: float | None = None,
             vb_width: float = 1280.0, letter_spacing: float = 0.0,
             label: str | None = None) -> dict:
    if zone is not None:
        available = float(zone)
    else:
        xs = 0.0 if x is None else float(x)
        rb = right_bound if right_bound is not None else (
            vb_width - vb_width * GEOM_MARGIN_RATIO)
        available = float(rb) - xs
    est = text_width(text, font_size, letter_spacing)
    fits = est <= available
    import math
    lines_needed = 1 if fits else max(2, math.ceil(est / available)) if available > 0 else 0
    out = {
        'label': label,
        'text': text,
        'font_size': font_size,
        'letter_spacing': letter_spacing,
        'est_width': round(est, 1),
        'available': round(available, 1),
        'fits_one_line': fits,
        'lines_needed': lines_needed,
        'verdict': 'ONE_LINE' if fits else f'WRAP_{lines_needed}',
    }
    if not fits and lines_needed == 2:
        brk = _balanced_break(text, font_size, letter_spacing, available)
        if brk:
            l1, l2, w1, w2 = brk
            out['suggested_break'] = {
                'line1': l1, 'line1_width': round(w1, 1),
                'line2': l2, 'line2_width': round(w2, 1),
                'both_fit': w1 <= available and w2 <= available,
            }
    return out


# --- vertical stack / collision oracle (mirrors checker A-class) ------------
def _line_extent(x: float, width: float, anchor: str):
    """Raw line box (x0, x1) + the checker's conservative extent (ex0, ex1).

    Mirrors `_geom_text_block` (x0 by anchor) and `_geom_a_checks`
    (GEOM_CONSERVATIVE gap applied on the far side of the anchor).
    """
    if anchor == 'middle':
        x0 = x - width / 2.0
    elif anchor == 'end':
        x0 = x - width
    else:
        x0 = x
    x1 = x0 + width
    gap = width * (1.0 - GEOM_CONSERVATIVE)
    if anchor == 'middle':
        return x0, x1, x0 + gap / 2.0, x1 - gap / 2.0
    if anchor == 'end':
        return x0, x1, x0 + gap, x1
    return x0, x1, x0, x1 - gap


def evaluate_stack(font_size: float, *, x: float, y: float, dy: float = 0.0,
                   lines=None, num_lines: int | None = None,
                   anchor: str = 'start', letter_spacing: float = 0.0,
                   vb_width: float = 1280.0, vb_height: float = 720.0,
                   bottom_bound: float | None = None,
                   label: str | None = None) -> dict:
    """Checker-parity vertical oracle for a planned dy-stacked block.

    Line i baseline = ``y + i*dy``; line box = baseline - GEOM_ASCENT*fs ..
    baseline + GEOM_DESCENT*fs (verbatim from `_geom_text_block`). Findings
    mirror the checker's A-class *errors*:

    CANVAS_V -> a line box crosses the canvas top/bottom edge
    CANVAS_H -> a line's conservative extent crosses the canvas left/right edge
    BOUND    -> block bottom overshoots the declared ``bottom_bound`` by more
                than GEOM_MIN_OVERLAP (pre-draw stand-in for a collision with
                the element known to sit below)

    ``margin_tight`` (bottom inside the last 5% of the canvas) is advisory
    only — the checker does not error on it.
    """
    texts = [str(s) for s in lines if str(s)] if lines else None
    n = len(texts) if texts else max(int(num_lines or 1), 1)
    fs = float(font_size)
    findings = []
    line_boxes = []
    for i in range(n):
        baseline = y + i * dy
        top = baseline - GEOM_ASCENT * fs
        bottom = baseline + GEOM_DESCENT * fs
        box = {'index': i, 'baseline': baseline, 'top': top, 'bottom': bottom}
        if texts:
            w = text_width(texts[i], fs, letter_spacing)
            x0, x1, ex0, ex1 = _line_extent(x, w, anchor)
            box.update({'text': texts[i], 'width': w, 'x0': x0, 'x1': x1,
                        'ex0': ex0, 'ex1': ex1})
            if ex1 > vb_width + 0.5:
                findings.append({
                    'kind': 'CANVAS_H', 'line': i,
                    'detail': f"line {i + 1} overflows the canvas right edge "
                              f"by ~{ex1 - vb_width:.0f}px"})
            if ex0 < -0.5:
                findings.append({
                    'kind': 'CANVAS_H', 'line': i,
                    'detail': f"line {i + 1} starts ~{-ex0:.0f}px left of "
                              f"the canvas"})
        if bottom > vb_height + 0.5 or top < -0.5:
            findings.append({
                'kind': 'CANVAS_V', 'line': i,
                'detail': f"line {i + 1} exceeds the canvas vertically "
                          f"(box {top:.0f}..{bottom:.0f}, canvas 0.."
                          f"{vb_height:.0f})"})
        line_boxes.append(box)
    block_bottom = y + (n - 1) * dy + GEOM_DESCENT * fs
    if bottom_bound is not None:
        overshoot = block_bottom - float(bottom_bound)
        if overshoot > GEOM_MIN_OVERLAP:
            findings.append({
                'kind': 'BOUND',
                'detail': f"block bottom {block_bottom:.0f} overshoots "
                          f"bottom_bound {float(bottom_bound):.0f} by "
                          f"~{overshoot:.0f}px — cut a line, tighten dy, "
                          f"raise y, or move the element below"})
    margin_line = vb_height * (1.0 - GEOM_MARGIN_RATIO)
    return {
        'label': label,
        'mode': 'stack',
        'font_size': fs,
        'anchor': anchor,
        'n_lines': n,
        'x': x,
        'first_baseline': y,
        'last_baseline': y + (n - 1) * dy,
        'block_top': round(y - GEOM_ASCENT * fs, 1),
        'block_bottom': round(block_bottom, 1),
        'bottom_bound': bottom_bound,
        'margin_tight': block_bottom > margin_line,
        'line_boxes': line_boxes,
        'findings': findings,
        'verdict': 'STACK_ERROR' if findings else 'STACK_OK',
    }


def _collide(ex0, ex1, top, bottom, box):
    """Mirror of the checker's intrusion test: >GEOM_MIN_OVERLAP overlap on
    both axes AND the moving line crosses one of the obstacle's edges
    (containment = deliberate underlay, not a defect)."""
    bx0, by0, bx1, by1 = box
    ox = min(ex1, bx1) - max(ex0, bx0)
    oy = min(bottom, by1) - max(top, by0)
    if ox <= GEOM_MIN_OVERLAP or oy <= GEOM_MIN_OVERLAP:
        return None
    h_cross = (
        (ex0 < bx0 - GEOM_MIN_OVERLAP and ex1 > bx0 + GEOM_MIN_OVERLAP)
        or (ex1 > bx1 + GEOM_MIN_OVERLAP and ex0 < bx1 - GEOM_MIN_OVERLAP)
    )
    v_cross = (
        (top < by0 - GEOM_MIN_OVERLAP and bottom > by0 + GEOM_MIN_OVERLAP)
        or (bottom > by1 + GEOM_MIN_OVERLAP and top < by1 - GEOM_MIN_OVERLAP)
    )
    return ox if (h_cross or v_cross) else None


def evaluate_page(spec: dict) -> list[dict]:
    """Whole-page pre-draw check from one JSON object: per-block width +
    vertical (`evaluate_stack`), wrap parity (`evaluate_wrap`, blocks with
    >= 2 lines), and cross-block / obstacle collision — all mirroring the
    checker's conditions so a clean page here draws through the gate."""
    vb_w = float(spec.get('vb_width', 1280.0))
    vb_h = float(spec.get('vb_height', 720.0))
    results = []
    stacks = []
    for b in spec.get('blocks', []):
        fs = float(b.get('font_size', 24))
        ls = float(b.get('letter_spacing', 0.0))
        lines = b.get('lines') or ([b['text']] if b.get('text') else None)
        r = evaluate_stack(
            fs, x=float(b.get('x', 0.0)), y=float(b.get('y', 0.0)),
            dy=float(b.get('dy', 0.0)), lines=lines,
            num_lines=b.get('num_lines'), anchor=b.get('anchor', 'start'),
            letter_spacing=ls, vb_width=vb_w, vb_height=vb_h,
            bottom_bound=b.get('bottom_bound'), label=b.get('label'))
        results.append(r)
        stacks.append(r)
        if lines and len(lines) >= 2:
            results.append(evaluate_wrap(
                lines, fs, x=b.get('x'), right_bound=b.get('right_bound'),
                vb_width=vb_w, letter_spacing=ls, label=b.get('label')))
    obstacle_boxes = [
        (o.get('label') or f'obstacle{i + 1}', tuple(map(float, o['box'])))
        for i, o in enumerate(spec.get('obstacles', []))
    ]
    for r in stacks:
        others = list(obstacle_boxes)
        for other in stacks:
            if other is r:
                continue
            for lb in other['line_boxes']:
                if 'x0' in lb:
                    others.append((other['label'] or 'block',
                                   (lb['x0'], lb['top'],
                                    lb['x1'], lb['bottom'])))
        for lb in r['line_boxes']:
            if 'ex0' not in lb:
                continue
            for name, box in others:
                ox = _collide(lb['ex0'], lb['ex1'], lb['top'], lb['bottom'],
                              box)
                if ox is not None:
                    r['findings'].append({
                        'kind': 'COLLIDE', 'line': lb['index'],
                        'detail': f"line {lb['index'] + 1} "
                                  f"\"{lb.get('text', '')[:18]}\" intrudes "
                                  f"~{ox:.0f}px into '{name}' (box "
                                  f"x={box[0]:.0f}..{box[2]:.0f}, "
                                  f"y={box[1]:.0f}..{box[3]:.0f})"})
                    break  # one report per (line, obstacle set), like checker
        if r['findings']:
            r['verdict'] = 'STACK_ERROR'
    return results


def _fmt(r: dict) -> str:
    tag = f"[{r['label']}] " if r.get('label') else ''
    if r.get('mode') == 'stack':
        head = (f"{tag}{r['verdict']:12s}  {r['n_lines']}L  baseline "
                f"{r['first_baseline']:g}->{r['last_baseline']:g}  bottom "
                f"{r['block_bottom']:g}"
                + (f"  bound {r['bottom_bound']:g}"
                   if r.get('bottom_bound') is not None else '')
                + (f"  fs={r['font_size']:g}"))
        lines = [head]
        for f in r['findings']:
            lines.append(f"           {f['kind']}: {f['detail']}")
        if not r['findings'] and r.get('margin_tight'):
            lines.append("           note: bottom sits inside the last 5% of "
                         "the canvas (advisory — checker won't error)")
        return "\n".join(lines)
    if r.get('mode') == 'wrap':
        preview = ' | '.join(r['lines'])
        head = (f"{tag}{r['verdict']:12s}  full {r['est_width']:.0f}px "
                f"{'<=' if r['fits_one_line'] else '>'} avail {r['available']:.0f}px "
                f"(rb={r['right_bound']:.0f})  fs={r['font_size']:g}  "
                f"{r['lines_needed']}L \"{preview[:48]}{'…' if len(preview) > 48 else ''}\"")
        if r['fits_one_line']:
            return (head + "\n           -> checker WILL warn 'fits on one line'. "
                    "Draw ONE line, bound the column with a right-edge shape in "
                    "the block's y-band, or split into separate <text> paragraphs.")
        return head + "  -> wrap justified; checker won't flag."
    head = (f"{tag}{r['verdict']:8s}  est {r['est_width']:.0f}px / "
            f"avail {r['available']:.0f}px  fs={r['font_size']:g}  "
            f"\"{r['text'][:42]}{'…' if len(r['text']) > 42 else ''}\"")
    if r['verdict'] == 'ONE_LINE':
        return head + "  -> write as ONE line"
    lines = [head]
    if 'suggested_break' in r:
        b = r['suggested_break']
        ok = 'both fit' if b['both_fit'] else 'still tight — consider ① redistribute'
        lines.append(f"           balanced 2-line ({ok}):")
        lines.append(f"             1: \"{b['line1']}\"  ({b['line1_width']:.0f}px)")
        lines.append(f"             2: \"{b['line2']}\"  ({b['line2_width']:.0f}px)")
    else:
        lines.append(f"           needs {r['lines_needed']} lines — shorten (ladder ③) "
                     f"or widen the zone (①)")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pre-draw line-fit oracle for SVG text.")
    ap.add_argument('text', nargs='?', help='the text to measure')
    ap.add_argument('--font-size', '-s', type=float, help='px font size')
    ap.add_argument('--zone', '-z', type=float, help='available width (px), given directly')
    ap.add_argument('--x', type=float, help='text x; available derived as right_bound - x')
    ap.add_argument('--right-bound', type=float, help='right boundary x (default: vb_width - 5%%)')
    ap.add_argument('--vb-width', type=float, default=1280.0, help='canvas viewBox width (default 1280)')
    ap.add_argument('--letter-spacing', '-l', type=float, default=0.0)
    ap.add_argument('--y', type=float,
                    help='first-line baseline y (enables the vertical check)')
    ap.add_argument('--dy', type=float, default=0.0,
                    help='line height (tspan dy) for the vertical check')
    ap.add_argument('--num-lines', type=int,
                    help='planned line count (vertical check without texts)')
    ap.add_argument('--vb-height', type=float, default=720.0,
                    help='canvas viewBox height (default 720)')
    ap.add_argument('--bottom-bound', type=float,
                    help='top edge of the element below / bottom margin the '
                         'block must clear')
    ap.add_argument('--batch',
                    help='JSON file: array of block dicts, or a page object '
                         '{vb_width, vb_height, blocks, obstacles}')
    ap.add_argument('--json', action='store_true', help='emit JSON')
    args = ap.parse_args(argv)

    results = []
    if args.batch:
        with open(args.batch, encoding='utf-8-sig') as fh:
            blocks = json.load(fh)
        if isinstance(blocks, dict):  # page form -> width + vertical + collision
            results.extend(evaluate_page(blocks))
        else:
            for b in blocks:
                fs = float(b.get('font_size', args.font_size or 24))
                ls = float(b.get('letter_spacing', 0.0))
                vbw = float(b.get('vb_width', 1280.0))
                if 'y' in b:  # planned stack -> vertical view
                    results.append(evaluate_stack(
                        fs, x=float(b.get('x', 0.0)), y=float(b['y']),
                        dy=float(b.get('dy', 0.0)), lines=b.get('lines'),
                        num_lines=b.get('num_lines'),
                        anchor=b.get('anchor', 'start'), letter_spacing=ls,
                        vb_width=vbw,
                        vb_height=float(b.get('vb_height', 720.0)),
                        bottom_bound=b.get('bottom_bound'),
                        label=b.get('label')))
                    if b.get('lines') and len(b['lines']) >= 2:
                        results.append(evaluate_wrap(
                            b['lines'], fs, x=b.get('x'),
                            right_bound=b.get('right_bound'), vb_width=vbw,
                            letter_spacing=ls, label=b.get('label')))
                elif 'lines' in b:  # intended multi-line -> checker-parity view
                    results.append(evaluate_wrap(
                        b['lines'], fs, x=b.get('x'), right_bound=b.get('right_bound'),
                        vb_width=vbw, letter_spacing=ls, label=b.get('label')))
                else:
                    results.append(evaluate(
                        b['text'], fs, zone=b.get('zone'), x=b.get('x'),
                        right_bound=b.get('right_bound'), vb_width=vbw,
                        letter_spacing=ls, label=b.get('label')))
    else:
        if args.font_size is None:
            ap.error('provide --font-size (or use --batch)')
        if args.text is None and not (args.y is not None and args.num_lines):
            ap.error('provide TEXT (or --y with --num-lines for a '
                     'vertical-only check, or use --batch)')
        if args.text is not None:
            if args.zone is None and args.x is None:
                ap.error('provide --zone OR --x (to derive available width)')
            results.append(evaluate(
                args.text, args.font_size, zone=args.zone, x=args.x,
                right_bound=args.right_bound, vb_width=args.vb_width,
                letter_spacing=args.letter_spacing))
        if args.y is not None:
            results.append(evaluate_stack(
                args.font_size, x=args.x if args.x is not None else 0.0,
                y=args.y, dy=args.dy,
                lines=[args.text] if args.text and not args.num_lines else None,
                num_lines=args.num_lines, letter_spacing=args.letter_spacing,
                vb_width=args.vb_width, vb_height=args.vb_height,
                bottom_bound=args.bottom_bound))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(_fmt(r))
    # exit non-zero if any block is not clean: a single-line block that would
    # wrap, an intended-wrap block the checker will flag as "fits on one
    # line", or a stack with any A-class finding (canvas/collision/bound)
    def _clean(r):
        mode = r.get('mode')
        if mode == 'wrap':
            return not r['fits_one_line']
        if mode == 'stack':
            return not r['findings']
        return r['fits_one_line']
    return 0 if all(_clean(r) for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
