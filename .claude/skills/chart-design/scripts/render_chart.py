#!/usr/bin/env python3
"""render_chart.py — data → slide-ready SVG chart, styled by the deck's spec_lock.

slide-master (ppt-master) variant.

Usage:
  python3 .claude/skills/chart-design/scripts/render_chart.py spec.json       --project projects/<deck> -o chart.svg --pos 60,220
  python3 ... spec.json --project projects/<deck> -o preview.svg --standalone
  python3 ... spec.json --project projects/<deck> --validate-only
  python3 ... --list-types

Output (default): a <g id="…" data-chart-type="…"> fragment with absolute
coordinates baked in via --pos, containing <g id="chartArea"> plus the
ppt-master §3.1 chart-plot-area marker (verify-charts reads it). Paste into
the page SVG in svg_output/.

All colors and fonts come from <project>/spec_lock.md — the deck's execution
lock. There are no built-in style defaults: a missing/invalid lock is a hard
error by design (SPEC_LOCK discipline).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from chartlib.renderers import (RENDERERS, ChartJudgmentError, SpecError,
                                plot_marker, render)
from chartlib.svgutil import wrap_fragment, wrap_standalone
from chartlib.tokens import TokenResolutionError, resolve_style


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", nargs="?", help="path to spec JSON, or '-' for stdin")
    p.add_argument("-o", "--output", help="output SVG path (default: stdout)")
    p.add_argument("--standalone", action="store_true",
                   help="wrap in a full <svg> document with theme bg (preview)")
    p.add_argument("--pos", metavar="X,Y",
                   help="translate the fragment to slide coordinates")
    p.add_argument("--project", help="ppt-master deck project directory — style "
                   "comes from <project>/spec_lock.md (the normal path)")
    p.add_argument("--theme", help="contract-shaped theme JSON (testing only)")
    p.add_argument("--area-id", default="chartArea",
                   help="id of the plot-area group (default: chartArea; override "
                   "when a page embeds multiple charts)")
    p.add_argument("--no-marker", action="store_true",
                   help="omit the ppt-master chart-plot-area marker")
    p.add_argument("--id", dest="gid", help="fragment group id "
                   "(default: chart_<type>)")
    p.add_argument("--validate-only", action="store_true",
                   help="run spec + judgment checks without writing output")
    p.add_argument("--list-types", action="store_true")
    args = p.parse_args(argv)

    if args.list_types:
        for name in sorted(RENDERERS):
            print(name)
        return 0
    if not args.spec:
        p.error("spec is required (path or '-')")

    try:
        raw = (sys.stdin.read() if args.spec == "-"
               else Path(args.spec).read_text(encoding="utf-8"))
        spec = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: cannot read spec: {exc}", file=sys.stderr)
        return 2

    try:
        style = resolve_style(args.theme, args.project)
        writer = render(spec, style)
        inner = writer.fragment()
    except TokenResolutionError as exc:
        print(f"TokenResolutionError: {exc}", file=sys.stderr)
        return 3
    except ChartJudgmentError as exc:
        print(f"ChartJudgmentError [{spec.get('type')}]: {exc}", file=sys.stderr)
        return 4
    except SpecError as exc:
        print(f"SpecError [{spec.get('type')}]: {exc}", file=sys.stderr)
        return 2

    if args.validate_only:
        print(f"OK: {spec.get('type')} spec valid "
              f"(theme: {style.theme_name} @ {style.source_path})")
        return 0

    x = y = 0.0
    if args.pos:
        try:
            x, y = (float(v) for v in args.pos.split(","))
        except ValueError:
            print("Error: --pos expects X,Y numbers", file=sys.stderr)
            return 2
    gid = args.gid or f"chart_{spec.get('type')}"
    marker = None if args.no_marker else plot_marker(writer, spec)
    out = wrap_fragment(gid, str(spec.get("type")), inner, x, y,
                        marker=marker, area_id=args.area_id)
    if args.standalone:
        out = wrap_standalone(style, out,
                              float(spec.get("width", 720)),
                              float(spec.get("height", 420)))

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
