"""Cartesian coordinate engine.

One shared frame (scales, axes, ticks, gridlines, label collision handling)
reused by all 12 rectangular chart types. Renderers only map data → shapes;
everything about where the plot area sits and how labels behave lives here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .svgutil import SvgWriter, fmt_number, text_width, truncate_to_width


# -- scales -----------------------------------------------------------------

def nice_ticks(lo: float, hi: float, target: int = 5) -> list[float]:
    """Heckbert 'nice numbers' ticks covering [lo, hi]."""
    if lo == hi:
        hi = lo + 1.0
    if hi < lo:
        lo, hi = hi, lo
    span = hi - lo
    raw_step = span / max(1, target)
    mag = 10 ** math.floor(math.log10(raw_step))
    residual = raw_step / mag
    if residual < 1.5:
        step = 1 * mag
    elif residual < 3:
        step = 2 * mag
    elif residual < 7:
        step = 5 * mag
    else:
        step = 10 * mag
    start = math.floor(lo / step) * step
    end = math.ceil(hi / step) * step  # loose labeling: ticks must COVER the data
    ticks = []
    t = start
    while t <= end + step * 1e-9:
        ticks.append(round(t, 10) + 0.0)
        t += step
    return ticks


class LinearScale:
    def __init__(self, domain: tuple[float, float], range_px: tuple[float, float],
                 include_zero: bool = False, tick_target: int = 5):
        lo, hi = min(domain), max(domain)
        if include_zero:
            lo, hi = min(lo, 0.0), max(hi, 0.0)
        self.ticks = nice_ticks(lo, hi, tick_target)
        self.lo, self.hi = self.ticks[0], self.ticks[-1]
        self.r0, self.r1 = range_px

    def __call__(self, v: float) -> float:
        if self.hi == self.lo:
            return self.r0
        t = (v - self.lo) / (self.hi - self.lo)
        return self.r0 + t * (self.r1 - self.r0)


class BandScale:
    """Categorical positions with proportional padding."""

    def __init__(self, n: int, range_px: tuple[float, float],
                 padding_outer: float = 0.5, padding_inner: float = 0.35):
        self.n = max(1, n)
        self.r0, self.r1 = range_px
        span = self.r1 - self.r0
        denom = self.n + padding_inner * (self.n - 1) + padding_outer * 2
        self.band = span / denom
        self.step = self.band * (1 + padding_inner)
        self.offset = self.band * padding_outer

    def start(self, i: int) -> float:
        return self.r0 + self.offset + i * self.step

    def center(self, i: int) -> float:
        return self.start(i) + self.band / 2


# -- frame -------------------------------------------------------------------

@dataclass
class Frame:
    """Computed plot area + drawing services for one cartesian chart."""
    w: SvgWriter
    width: float
    height: float
    x0: float = 0.0
    y0: float = 0.0
    x1: float = field(default=0.0)
    y1: float = field(default=0.0)

    def plot_size(self) -> tuple[float, float]:
        return self.x1 - self.x0, self.y1 - self.y0


def build_frame(w: SvgWriter, width: float, height: float,
                value_scale_domain: tuple[float, float],
                categories: list[str] | None,
                *,
                horizontal: bool = False,
                include_zero: bool = True,
                unit: str = "",
                legend_items: list[tuple[str, str]] | None = None,
                x_numeric_domain: tuple[float, float] | None = None,
                tick_target: int = 5) -> tuple[Frame, LinearScale, BandScale | LinearScale]:
    """Lay out margins, draw grid + axes + labels; return mapping scales.

    Vertical charts: categories on x, values on y.
    Horizontal charts: categories on y, values on x.
    Scatter-style charts pass x_numeric_domain instead of categories.
    """
    st = w.style
    cap = st.type["caption"]
    legend_h = (cap.size * 1.6 + 8) if legend_items else 0.0

    # Probe value ticks once to size the label gutter before fixing the range.
    probe = LinearScale(value_scale_domain, (0, 1), include_zero, tick_target)
    tick_labels = [fmt_number(t, unit) for t in probe.ticks]
    tick_w = max(text_width(s, cap.size, cap.weight) for s in tick_labels)

    if horizontal:
        cat_w = max((text_width(c, cap.size, cap.weight) for c in (categories or [""])),
                    default=0.0)
        # +16 so the truncation budget in _cat_labels_left (f.x0 - 12) still
        # covers the longest label — a smaller pad clips its last glyph.
        left = min(cat_w, width * 0.32) + 16
        bottom = cap.size * 1.8
        right = 8.0
    else:
        left = tick_w + 12
        bottom = cap.size * 1.9
        right = 8.0
    top = 6.0 + legend_h

    f = Frame(w, width, height, x0=left, y0=top, x1=width - right,
              y1=height - bottom)
    # ppt-master verify-charts reads this via the §3.1 plot-area marker.
    w.plot_rect = (f.x0, f.y0, f.x1, f.y1)

    if legend_items:
        _draw_legend(w, legend_items, f.x0, 2.0 + cap.size * 0.5)

    if horizontal:
        val = LinearScale(value_scale_domain, (f.x0, f.x1), include_zero, tick_target)
        band = BandScale(len(categories or [""]), (f.y0, f.y1))
        _grid_vertical_lines(w, f, val, unit)
        _cat_labels_left(w, f, categories or [], band)
        # baseline (value axis zero or left edge)
        zx = val(0.0) if val.lo <= 0.0 <= val.hi else f.x0
        ax_hex, ax_op = st.neutral_paint("border-strong", "text", 0.26)
        w.line(zx, f.y0, zx, f.y1, ax_hex, st.stroke["divider"],
               stroke_opacity=ax_op)
        return f, val, band

    val = LinearScale(value_scale_domain, (f.y1, f.y0), include_zero, tick_target)
    _grid_horizontal_lines(w, f, val, unit)
    if categories is not None:
        band = BandScale(len(categories), (f.x0, f.x1))
        _cat_labels_bottom(w, f, categories, band)
        zy = val(0.0) if val.lo <= 0.0 <= val.hi else f.y1
        ax_hex, ax_op = st.neutral_paint("border-strong", "text", 0.26)
        w.line(f.x0, zy, f.x1, zy, ax_hex, st.stroke["divider"],
               stroke_opacity=ax_op)
        return f, val, band

    assert x_numeric_domain is not None, "numeric x requires x_numeric_domain"
    xs = LinearScale(x_numeric_domain, (f.x0, f.x1), False, tick_target)
    _x_numeric_labels(w, f, xs)
    ax_hex, ax_op = st.neutral_paint("border-strong", "text", 0.26)
    w.line(f.x0, f.y1, f.x1, f.y1, ax_hex, st.stroke["divider"],
           stroke_opacity=ax_op)
    return f, val, xs


# -- internals ----------------------------------------------------------------

def _draw_legend(w: SvgWriter, items: list[tuple[str, object]], x: float,
                 cy: float) -> None:
    st = w.style
    cap = st.type["caption"]
    sw = 10.0
    for name, paint in items:
        fill, fop = paint if isinstance(paint, tuple) else (paint, None)
        w.rect(x, cy - sw / 2, sw, sw, fill, rx=min(st.radius["xs"], sw / 2),
               fill_opacity=fop)
        x += sw + 6
        w.text(x, cy + cap.size * 0.34, name, role="caption",
               fill=st.color["text-secondary"])
        x += text_width(name, cap.size, cap.weight) + 18


def _grid_horizontal_lines(w: SvgWriter, f: Frame, val: LinearScale, unit: str) -> None:
    st = w.style
    for t in val.ticks:
        y = val(t)
        if abs(t) > 1e-12:  # zero line drawn as axis
            w.line(f.x0, y, f.x1, y, st.grid_stroke, st.stroke["divider"])
        w.text(f.x0 - 8, y + st.type["caption"].size * 0.34, fmt_number(t, unit),
               role="caption", fill=st.color["text-secondary"], anchor="end")


def _grid_vertical_lines(w: SvgWriter, f: Frame, val: LinearScale, unit: str) -> None:
    st = w.style
    for t in val.ticks:
        x = val(t)
        if abs(t) > 1e-12:
            w.line(x, f.y0, x, f.y1, st.grid_stroke, st.stroke["divider"])
        w.text(x, f.y1 + st.type["caption"].size * 1.3, fmt_number(t, unit),
               role="caption", fill=st.color["text-secondary"], anchor="middle")


def _thin_indices(labels: list[str], available_step: float, size: float,
                  weight: int) -> set[int]:
    """Pick which category labels to keep so neighbors never collide."""
    if not labels:
        return set()
    max_w = max(text_width(s, size, weight) for s in labels)
    keep_every = max(1, math.ceil((max_w + 10) / max(available_step, 1.0)))
    kept = set(range(0, len(labels), keep_every))
    kept.add(len(labels) - 1)  # always label the last category (latest period)
    if keep_every > 1 and (len(labels) - 1) % keep_every != 0:
        drop = len(labels) - 1 - keep_every // 2
        kept.discard(drop)
    return kept


def _cat_labels_bottom(w: SvgWriter, f: Frame, cats: list[str], band: BandScale) -> None:
    st = w.style
    cap = st.type["caption"]
    kept = _thin_indices(cats, band.step, cap.size, cap.weight)
    y = f.y1 + cap.size * 1.35
    for i, c in enumerate(cats):
        if i not in kept:
            continue
        label = truncate_to_width(c, cap.size, band.step * 1.9, cap.weight)
        w.text(band.center(i), y, label, role="caption",
               fill=st.color["text-secondary"], anchor="middle")


def _cat_labels_left(w: SvgWriter, f: Frame, cats: list[str], band: BandScale) -> None:
    st = w.style
    cap = st.type["caption"]
    for i, c in enumerate(cats):
        label = truncate_to_width(c, cap.size, f.x0 - 12, cap.weight)
        w.text(f.x0 - 10, band.center(i) + cap.size * 0.34, label, role="caption",
               fill=st.color["text-secondary"], anchor="end")


def _x_numeric_labels(w: SvgWriter, f: Frame, xs: LinearScale) -> None:
    st = w.style
    cap = st.type["caption"]
    for t in xs.ticks:
        x = xs(t)
        w.line(x, f.y0, x, f.y1, st.grid_stroke, st.stroke["divider"])
        w.text(x, f.y1 + cap.size * 1.3, fmt_number(t), role="caption",
               fill=st.color["text-secondary"], anchor="middle")


# -- shared shape helpers ------------------------------------------------------

def polyline_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)


def area_path(points: list[tuple[float, float]], baseline_y: float) -> str:
    if not points:
        return ""
    d = polyline_path(points)
    last_x = points[-1][0]
    first_x = points[0][0]
    return f"{d} L{last_x:.2f},{baseline_y:.2f} L{first_x:.2f},{baseline_y:.2f} Z"


def value_label(w: SvgWriter, x: float, y: float, value: float, unit: str,
                anchor: str = "middle", fill: str | None = None,
                weight: int | None = None) -> None:
    st = w.style
    w.text(x, y, fmt_number(value, unit), role="caption",
           fill=fill or st.color["text"], anchor=anchor,
           weight=weight if weight is not None else st.type["caption"].weight + 100)
