#!/usr/bin/env python3
"""
PPT Master - Preset Shape SVG Fragment Tool

List DrawingML presets or print one canonical native-preset SVG fragment to
stdout for manual insertion into a hand-authored slide. `--batch` prints the
fragments of one page's shapes in one call (still stdout only).

Usage:
    python3 scripts/preset_shape_svg.py list [--search QUERY]
    python3 scripts/preset_shape_svg.py describe PRESET
    python3 scripts/preset_shape_svg.py render PRESET --id ID --frame X Y W H
    python3 scripts/preset_shape_svg.py --batch SHAPES_JSON

Examples:
    python3 scripts/preset_shape_svg.py list --search arrow
    python3 scripts/preset_shape_svg.py describe rightArrow
    python3 scripts/preset_shape_svg.py render rightArrow --id next-step \
        --frame 160 210 320 112 --fill "#2563EB" --stroke none
    python3 scripts/preset_shape_svg.py --batch p05_shapes.json
        # JSON list; each object holds one render call's parameters, keyed by
        # flag name: [{"preset": "rightArrow", "id": "next-step",
        #   "frame": [160, 210, 320, 112], "fill": "#2563EB",
        #   "adjust": ["adj1=val 50000"]}, ...]

Dependencies:
    None (only uses standard library and local PPT Master modules)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from console_encoding import configure_utf8_stdio
from pptx_shapes import CONNECTOR_PRESET_TYPES, get_preset_registry
from pptx_to_svg.preset_authoring import render_preset_shape_fragment


configure_utf8_stdio()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print one canonical DrawingML preset SVG fragment. "
            "This tool never writes SVG files or page layouts."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--batch",
        metavar="JSON",
        help=(
            "Render every object of a JSON list in one call; each object "
            "holds one render call's parameters keyed by flag name."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser(
        "list",
        help="List preset names, optionally filtered by substring.",
    )
    list_parser.add_argument(
        "--search",
        default="",
        help="Case-insensitive preset-name substring.",
    )

    describe_parser = subparsers.add_parser(
        "describe",
        help="Print preset adjustment and path metadata as JSON.",
    )
    describe_parser.add_argument("preset", help="DrawingML preset name.")

    render_parser = subparsers.add_parser(
        "render",
        help="Print one canonical authored-preset <g> fragment to stdout.",
    )
    render_parser.add_argument("preset", help="DrawingML preset name.")
    render_parser.add_argument(
        "--id",
        required=True,
        dest="element_id",
        help="Stable unique SVG group id.",
    )
    render_parser.add_argument(
        "--frame",
        required=True,
        nargs=4,
        type=float,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
        help="Absolute SVG frame in page coordinates.",
    )
    render_parser.add_argument(
        "--object-kind",
        choices=("shape", "connector"),
        default="shape",
        help="Emit a normal shape or a native PowerPoint connector.",
    )
    render_parser.add_argument(
        "--name",
        help="Optional PowerPoint object name.",
    )
    render_parser.add_argument(
        "--fill",
        default="none",
        help="Solid SVG fill from spec_lock, or none.",
    )
    render_parser.add_argument(
        "--fill-opacity",
        type=float,
        help="Fill opacity from 0 to 1.",
    )
    render_parser.add_argument(
        "--stroke",
        default="none",
        help="Solid SVG stroke from spec_lock, or none.",
    )
    render_parser.add_argument(
        "--stroke-width",
        type=float,
        help="Stroke width in SVG page units; defaults to 1 when stroked.",
    )
    render_parser.add_argument(
        "--stroke-opacity",
        type=float,
        help="Stroke opacity from 0 to 1.",
    )
    render_parser.add_argument(
        "--stroke-linecap",
        choices=("butt", "round", "square"),
    )
    render_parser.add_argument(
        "--stroke-linejoin",
        choices=("miter", "round", "bevel"),
    )
    render_parser.add_argument(
        "--adjust",
        action="append",
        default=[],
        metavar="NAME=FORMULA",
        help=(
            "DrawingML adjustment formula; repeat for multiple guides, "
            "for example --adjust 'adj1=val 50000'."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.batch is None) == (args.command is None):
        parser.error("give one command (list / describe / render) or --batch")
    if args.batch is not None:
        return _render_batch(parser, args.batch)
    registry = get_preset_registry()

    if args.command == "list":
        query = args.search.casefold().strip()
        names = [
            name for name in registry.names
            if not query or query in name.casefold()
        ]
        if not names:
            print(f"No preset names match {args.search!r}", file=sys.stderr)
            return 1
        print("\n".join(names))
        return 0

    if args.command == "describe":
        if args.preset not in registry:
            print(f"Unknown DrawingML preset: {args.preset!r}", file=sys.stderr)
            return 1
        definition = registry.get(args.preset)
        payload = {
            "preset": definition.name,
            "connector_preset": definition.name in CONNECTOR_PRESET_TYPES,
            "adjustments": [
                {"name": guide.name, "formula": guide.formula}
                for guide in definition.adjustments
            ],
            "path_count": len(definition.paths),
            "connection_site_count": len(definition.connections),
            "has_text_rectangle": definition.text_rectangle is not None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        fragment = _render(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(fragment)
    return 0


def _render(args: argparse.Namespace) -> str:
    return render_preset_shape_fragment(
        args.preset,
        tuple(args.frame),
        adjustments=_parse_adjustments(args.adjust),
        object_kind=args.object_kind,
        element_id=args.element_id,
        name=args.name,
        style=_style_from_args(args),
    )


def _render_batch(parser: argparse.ArgumentParser, path: str) -> int:
    """Render each batch object as its own `render` call; print all or none."""
    try:
        with open(path, encoding="utf-8-sig") as handle:
            entries = json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"Error: cannot read batch file {path!r}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(entries, list) or not all(
        isinstance(entry, dict) for entry in entries
    ):
        print("Error: batch file must be a JSON list of objects", file=sys.stderr)
        return 1
    fragments = []
    for index, entry in enumerate(entries, 1):
        try:
            fragments.append(_render(parser.parse_args(_entry_argv(entry))))
        except SystemExit:  # argparse already printed the reason
            print(f"Error: batch entry {index} is invalid", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"Error: batch entry {index}: {exc}", file=sys.stderr)
            return 1
    print("\n".join(fragments))
    return 0


def _entry_argv(entry: dict) -> list[str]:
    """Turn one batch object into the argv of the same `render` call."""
    argv = ["render"]
    if "preset" in entry:
        argv.append(str(entry["preset"]))
    for key, value in entry.items():
        if key == "preset":
            continue
        flag = "--" + key.replace("_", "-")
        values = value if isinstance(value, list) else [value]
        if key == "frame":  # nargs=4: one flag, four values
            argv += [flag, *map(str, values)]
            continue
        for item in values:
            argv += [flag, str(item)]
    return argv


def _parse_adjustments(values: Sequence[str]) -> dict[str, str]:
    adjustments: dict[str, str] = {}
    for value in values:
        name, separator, formula = value.partition("=")
        name = name.strip()
        formula = formula.strip()
        if not separator or not name or not formula:
            raise ValueError(
                f"Invalid adjustment {value!r}; expected NAME=FORMULA"
            )
        if name in adjustments:
            raise ValueError(f"Duplicate adjustment guide: {name!r}")
        adjustments[name] = formula
    return adjustments


def _style_from_args(args: argparse.Namespace) -> dict[str, str]:
    style = {
        "fill": args.fill,
        "stroke": args.stroke,
    }
    if args.fill_opacity is not None:
        style["fill-opacity"] = str(args.fill_opacity)
    if args.stroke != "none":
        style["stroke-width"] = str(
            1.0 if args.stroke_width is None else args.stroke_width
        )
    elif args.stroke_width is not None:
        raise ValueError("--stroke-width requires a non-none --stroke")
    if args.stroke_opacity is not None:
        style["stroke-opacity"] = str(args.stroke_opacity)
    if args.stroke_linecap is not None:
        style["stroke-linecap"] = args.stroke_linecap
    if args.stroke_linejoin is not None:
        style["stroke-linejoin"] = args.stroke_linejoin
    return style


if __name__ == "__main__":
    raise SystemExit(main())
