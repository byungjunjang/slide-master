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

Usage:
  # direct zone width
  text_fit.py "학습지와 평가지를 몇 분 만에" --font-size 40 --zone 1136

  # derive available from x on a 1280 canvas (right margin auto)
  text_fit.py "문항·정답·해설·활동지까지 초안 생성" --font-size 24 --x 560

  # right column bounded by a divider/right edge
  text_fit.py "..." --font-size 24 --x 560 --right-bound 1208

  # batch: JSON array of {text, font_size, x?|zone?, right_bound?, vb_width?,
  #         letter_spacing?, label?}
  text_fit.py --batch blocks.json
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


def _fmt(r: dict) -> str:
    tag = f"[{r['label']}] " if r.get('label') else ''
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
    ap.add_argument('--batch', help='JSON array of block dicts')
    ap.add_argument('--json', action='store_true', help='emit JSON')
    args = ap.parse_args(argv)

    results = []
    if args.batch:
        with open(args.batch, encoding='utf-8') as fh:
            blocks = json.load(fh)
        for b in blocks:
            results.append(evaluate(
                b['text'], float(b.get('font_size', args.font_size or 24)),
                zone=b.get('zone'), x=b.get('x'), right_bound=b.get('right_bound'),
                vb_width=float(b.get('vb_width', 1280.0)),
                letter_spacing=float(b.get('letter_spacing', 0.0)),
                label=b.get('label')))
    else:
        if args.text is None or args.font_size is None:
            ap.error('provide TEXT and --font-size (or use --batch)')
        if args.zone is None and args.x is None:
            ap.error('provide --zone OR --x (to derive available width)')
        results.append(evaluate(
            args.text, args.font_size, zone=args.zone, x=args.x,
            right_bound=args.right_bound, vb_width=args.vb_width,
            letter_spacing=args.letter_spacing))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(_fmt(r))
    # exit non-zero if any block would wrap unexpectedly (useful in checks)
    return 0 if all(r['fits_one_line'] for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
