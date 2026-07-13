"""SVG authoring helpers shared by all three engines.

Emits only converter-safe SVG (shared-standards.md §1 blacklist): plain shapes,
<text>/<tspan> that stay text, <g id> grouping. No <style>, class, mask, use,
textPath, filters, or gradients.
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from .tokens import ChartStyle, TypeScale

# Real Pretendard metrics from the slide skill's converter when available;
# measurement only affects label thinning/truncation, never token values.
_SLIDE_SCRIPTS = Path(__file__).resolve().parents[3] / "slide" / "scripts"
_measure = None
try:
    if str(_SLIDE_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SLIDE_SCRIPTS))
    from svg_to_pptx.font_metrics import measure_text as _mt, metrics_available
    if metrics_available():
        _measure = _mt
except Exception:  # metrics cache missing → heuristic below
    _measure = None


def text_width(text: str, size: float, weight: int = 400) -> float:
    """Estimated rendered width in px."""
    if _measure is not None:
        try:
            w = _measure(text, size, str(weight))
            if isinstance(w, (int, float)):
                return float(w)
            if isinstance(w, (tuple, list)) and w and isinstance(w[0], (int, float)):
                return float(w[0])
        except Exception:
            pass
    width = 0.0
    for ch in text:
        cp = ord(ch)
        if 0xAC00 <= cp <= 0xD7A3 or 0x4E00 <= cp <= 0x9FFF or 0x3000 <= cp <= 0x303F:
            width += size  # full-width CJK/Hangul
        elif ch == " ":
            width += size * 0.28
        elif ch in "iIlj.,'|!:;":
            width += size * 0.30
        elif ch.isdigit():
            width += size * 0.56
        elif ch.isupper():
            width += size * 0.66
        else:
            width += size * 0.52
    if weight >= 600:
        width *= 1.04
    return width


def truncate_to_width(text: str, size: float, max_width: float,
                      weight: int = 400) -> str:
    if text_width(text, size, weight) <= max_width:
        return text
    ell = "…"
    lo = ""
    for i in range(len(text), 0, -1):
        lo = text[:i].rstrip()
        if text_width(lo + ell, size, weight) <= max_width:
            return lo + ell
    return ell


def fmt_number(value: float, unit: str = "", decimals: int | None = None) -> str:
    """Locale-stable number label: thousands commas, trimmed decimals, unit suffix."""
    if decimals is None:
        decimals = 0 if float(value).is_integer() or abs(value) >= 100 else 1
    s = f"{value:,.{decimals}f}"
    if decimals > 0:
        s = s.rstrip("0").rstrip(".")
    return f"{s}{unit}"


class SvgWriter:
    """Accumulates SVG markup with indentation; renderers stay declarative."""

    def __init__(self, style: ChartStyle):
        self.style = style
        self._parts: list[str] = []
        self._depth = 0
        # Plot-area info for ppt-master's mandatory chart marker
        # (executor-base.md §3.1). cartesian.build_frame fills plot_rect;
        # polar renderers fill radial_area = (kind, cx, cy, r_outer, r_inner).
        self.plot_rect: tuple[float, float, float, float] | None = None
        self.radial_area: tuple[str, float, float, float, float] | None = None

    # -- low level -------------------------------------------------------

    def raw(self, line: str) -> None:
        self._parts.append("  " * self._depth + line)

    def open_group(self, gid: str, transform: str | None = None, **attrs: str) -> None:
        a = [f"id={quoteattr(gid)}"]
        if transform:
            a.append(f"transform={quoteattr(transform)}")
        for k, v in attrs.items():
            a.append(f"{k.replace('_', '-')}={quoteattr(str(v))}")
        self.raw(f"<g {' '.join(a)}>")
        self._depth += 1

    def close_group(self) -> None:
        self._depth -= 1
        self.raw("</g>")

    def _shape(self, tag: str, **attrs) -> None:
        parts = []
        for k, v in attrs.items():
            if v is None:
                continue
            key = k.replace("_", "-")
            if isinstance(v, float):
                v = f"{v:.2f}".rstrip("0").rstrip(".")
            parts.append(f"{key}={quoteattr(str(v))}")
        self.raw(f"<{tag} {' '.join(parts)}/>")

    def rect(self, x: float, y: float, w: float, h: float, fill: str,
             rx: float | None = None, stroke: str | None = None,
             stroke_width: float | None = None, opacity: float | None = None,
             fill_opacity: float | None = None) -> None:
        self._shape("rect", x=x, y=y, width=max(w, 0.0), height=max(h, 0.0),
                    fill=fill, rx=rx, stroke=stroke, stroke_width=stroke_width,
                    opacity=opacity, fill_opacity=fill_opacity)

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str,
             stroke_width: float, dash: str | None = None,
             linecap: str | None = None,
             stroke_opacity: float | None = None) -> None:
        self._shape("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke,
                    stroke_width=stroke_width, stroke_dasharray=dash,
                    stroke_linecap=linecap, stroke_opacity=stroke_opacity)

    def circle(self, cx: float, cy: float, r: float, fill: str,
               stroke: str | None = None, stroke_width: float | None = None,
               fill_opacity: float | None = None) -> None:
        self._shape("circle", cx=cx, cy=cy, r=r, fill=fill, stroke=stroke,
                    stroke_width=stroke_width, fill_opacity=fill_opacity)

    def path(self, d: str, fill: str = "none", stroke: str | None = None,
             stroke_width: float | None = None, linejoin: str | None = None,
             linecap: str | None = None, dash: str | None = None,
             fill_opacity: float | None = None,
             stroke_opacity: float | None = None) -> None:
        self._shape("path", d=d, fill=fill, stroke=stroke,
                    stroke_width=stroke_width, stroke_linejoin=linejoin,
                    stroke_linecap=linecap, stroke_dasharray=dash,
                    fill_opacity=fill_opacity, stroke_opacity=stroke_opacity)

    def polygon(self, points: list[tuple[float, float]], fill: str = "none",
                stroke: str | None = None, stroke_width: float | None = None,
                linejoin: str | None = None, opacity: float | None = None,
                fill_opacity: float | None = None,
                stroke_opacity: float | None = None) -> None:
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        self._shape("polygon", points=pts, fill=fill, stroke=stroke,
                    stroke_width=stroke_width, stroke_linejoin=linejoin,
                    opacity=opacity, fill_opacity=fill_opacity,
                    stroke_opacity=stroke_opacity)

    # -- text --------------------------------------------------------------

    def text(self, x: float, y: float, content: str, role: str = "caption",
             fill: str | None = None, anchor: str = "start",
             size: float | None = None, weight: int | None = None,
             letter_spacing: float | None = None,
             fill_opacity: float | None = None) -> None:
        """One <text> element styled by a typography token role.

        Text always stays a real <text> node (never outlined to path) so the
        SVG→PPTX converter emits an editable DrawingML text run.
        """
        ts: TypeScale = self.style.type[role]
        f_size = size if size is not None else ts.size
        f_weight = weight if weight is not None else ts.weight
        f_ls = letter_spacing if letter_spacing is not None else ts.letter_spacing
        if ts.transform == "uppercase":
            content = content.upper()
        attrs = [
            f"x={quoteattr(f'{x:.2f}')}",
            f"y={quoteattr(f'{y:.2f}')}",
            f"font-family={quoteattr(self.style.font_chain)}",
            f"font-size={quoteattr(f'{f_size:g}')}",
            f"font-weight={quoteattr(str(f_weight))}",
            f"fill={quoteattr(fill or self.style.color['text'])}",
        ]
        if anchor != "start":
            attrs.append(f"text-anchor={quoteattr(anchor)}")
        if f_ls:
            attrs.append(f"letter-spacing={quoteattr(f'{f_ls:g}')}")
        if fill_opacity is not None:
            attrs.append(f"fill-opacity={quoteattr(f'{fill_opacity:.2f}')}")
        self.raw(f"<text {' '.join(attrs)}>{escape(content)}</text>")

    # -- output -----------------------------------------------------------

    def fragment(self) -> str:
        return "\n".join(self._parts)


import re as _re

_COORD_X_ATTRS = ("x", "x1", "x2", "cx")
_COORD_Y_ATTRS = ("y", "y1", "y2", "cy")
_ATTR_RE = _re.compile(r'\b(x|y|x1|y1|x2|y2|cx|cy)="(-?[0-9.]+)"')
_POINTS_RE = _re.compile(r'\bpoints="([^"]+)"')
_PATH_RE = _re.compile(r'\bd="([^"]+)"')
_NUM_PAIR_RE = _re.compile(r"(-?[0-9.]+),(-?[0-9.]+)")


def _shift_pair(token: str, dx: float, dy: float, cmd: str = "") -> str:
    m = _NUM_PAIR_RE.fullmatch(token)
    if not m:
        return cmd + token
    return f"{cmd}{float(m.group(1)) + dx:.2f},{float(m.group(2)) + dy:.2f}"


def _offset_path_d(d: str, dx: float, dy: float) -> str:
    """Shift a path built by this module (absolute M/L/A/Z, "x,y" pair tokens).

    Grammar emitted by polyline_path/area_path/arc_segment_path only. Arc
    commands carry "A{rx},{ry} rot large sweep x,y" — radii and the three flag
    tokens pass through untouched; only the endpoint pair is shifted.
    """
    toks = d.split()
    out: list[str] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("Z", "z"):
            out.append(t)
            i += 1
        elif t.startswith("A"):
            out.append(t)                      # A{rx},{ry} — radii, unshifted
            out.extend(toks[i + 1:i + 4])      # rot, large-arc, sweep flags
            if i + 4 < len(toks):
                out.append(_shift_pair(toks[i + 4], dx, dy))
            i += 5
        else:
            cmd = t[0] if t[0] in "ML" else ""
            out.append(_shift_pair(t[1:] if cmd else t, dx, dy, cmd))
            i += 1
    return " ".join(out)


def offset_fragment(svg_text: str, dx: float, dy: float) -> str:
    """Shift every coordinate in generated chart markup by (dx, dy).

    Charts are placed at absolute slide coordinates instead of a wrapper
    transform because slide-svg's svg_quality_checker resolves text positions
    with a regex parser that cannot apply ancestor <g transform> — baked-in
    coordinates keep safe-area and overlap checks accurate.
    """
    if not dx and not dy:
        return svg_text

    def _attr(m: _re.Match) -> str:
        name, val = m.group(1), float(m.group(2))
        d = dx if name in _COORD_X_ATTRS else dy
        return f'{name}="{val + d:.2f}"'

    def _points(m: _re.Match) -> str:
        shifted = _NUM_PAIR_RE.sub(
            lambda p: f"{float(p.group(1)) + dx:.2f},{float(p.group(2)) + dy:.2f}",
            m.group(1))
        return f'points="{shifted}"'

    def _path(m: _re.Match) -> str:
        return f'd="{_offset_path_d(m.group(1), dx, dy)}"'

    svg_text = _ATTR_RE.sub(_attr, svg_text)
    svg_text = _POINTS_RE.sub(_points, svg_text)
    svg_text = _PATH_RE.sub(_path, svg_text)
    return svg_text


def _marker_comment(marker: tuple, dx: float, dy: float) -> str:
    """ppt-master plot-area marker (executor-base.md §3.1), shifted to slide coords."""
    kind = marker[0]
    if kind == "rect":
        x0, y0, x1, y1 = marker[1:5]
        return (f"<!-- chart-plot-area: {x0 + dx:.0f},{y0 + dy:.0f},"
                f"{x1 + dx:.0f},{y1 + dy:.0f} -->")
    _, cx, cy, r_out, r_in = marker
    cx, cy = cx + dx, cy + dy
    if kind == "donut":
        return (f"<!-- chart-plot-area: donut | center: {cx:.0f},{cy:.0f} | "
                f"outer-radius: {r_out:.0f} | inner-radius: {r_in:.0f} -->")
    return (f"<!-- chart-plot-area: {kind} | center: {cx:.0f},{cy:.0f} | "
            f"radius: {r_out:.0f} -->")


def wrap_fragment(gid: str, chart_type: str, inner: str, x: float = 0.0,
                  y: float = 0.0, marker: tuple | None = None,
                  area_id: str = "chartArea") -> str:
    """Wrap renderer output in the mandatory top-level content group.

    Placement bakes (x, y) into every coordinate — no transform on the group —
    so quality checkers can resolve absolute text positions. When `marker` is
    given, content is wrapped in <g id="chartArea"> carrying the ppt-master
    plot-area comment that the verify-charts workflow reads.
    """
    inner = offset_fragment(inner, x, y)
    if marker is not None:
        inner = (f'<g id="{area_id}">\n{_marker_comment(marker, x, y)}\n'
                 f"{inner}\n</g>")
    return (f'<g id="{gid}" data-chart-type="{chart_type}">\n'
            f"{inner}\n</g>")


def wrap_standalone(style: ChartStyle, inner: str, width: float,
                    height: float, pad: float = 40.0) -> str:
    """Full SVG document for previewing a fragment outside a slide."""
    w, h = width + pad * 2, height + pad * 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" '
        f'width="{w:g}" height="{h:g}">\n'
        f'  <rect width="{w:g}" height="{h:g}" fill="{style.color["bg"]}"/>\n'
        f'  <g transform="translate({pad:g},{pad:g})">\n{inner}\n  </g>\n'
        f"</svg>"
    )
