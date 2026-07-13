"""21 chart renderers on top of the three engines.

Every renderer: (spec, style) → inner SVG markup for a <g> fragment sized
spec.width × spec.height. Judgment gates that protect against misuse (pie
slice count, radar axis count, series caps) are enforced HERE so a bad chart
cannot be produced even by a careless caller — the error text names the
better chart to use instead.
"""
from __future__ import annotations

import math
import sys

from . import cartesian as ca
from . import layout as lay
from . import polar as po
from .svgutil import SvgWriter, fmt_number, text_width, truncate_to_width
from .tokens import ChartStyle, MAX_SERIES


class ChartJudgmentError(ValueError):
    """The requested chart type is wrong for this data. Message says what to use."""


class SpecError(ValueError):
    """The spec JSON is malformed for the requested type."""


def _warn(msg: str) -> None:
    print(f"[chart-design] WARN: {msg}", file=sys.stderr)


# --------------------------------------------------------------------------
# spec accessors
# --------------------------------------------------------------------------

def _pairs(spec: dict) -> list[tuple[str, float]]:
    data = spec.get("data")
    if not isinstance(data, list) or not data:
        raise SpecError("data must be a non-empty list of {label, value}")
    out = []
    for row in data:
        try:
            out.append((str(row["label"]), float(row["value"])))
        except (KeyError, TypeError, ValueError) as exc:
            raise SpecError(f"bad data row {row!r}: need label + numeric value") from exc
    return out


def _series_table(spec: dict, max_series: int = MAX_SERIES
                  ) -> tuple[list[str], list[tuple[str, list[float]]]]:
    data = spec.get("data")
    if not isinstance(data, dict):
        raise SpecError("data must be {categories: [...], series: [{name, values}]}")
    cats = [str(c) for c in data.get("categories", [])]
    raw = data.get("series", [])
    if not cats or not raw:
        raise SpecError("data.categories and data.series must be non-empty")
    series = []
    for s in raw:
        try:
            vals = [float(v) for v in s["values"]]
        except (KeyError, TypeError, ValueError) as exc:
            raise SpecError(f"bad series {s!r}") from exc
        if len(vals) != len(cats):
            raise SpecError(
                f"series '{s.get('name')}' has {len(vals)} values for {len(cats)} categories")
        series.append((str(s.get("name", f"S{len(series) + 1}")), vals))
    if len(series) > max_series:
        raise ChartJudgmentError(
            f"{len(series)} series exceeds the single-accent ladder cap "
            f"({max_series}). Aggregate minor series (top-{max_series - 1} + 기타) "
            "or split into two charts.")
    return cats, series


def _dims(spec: dict) -> tuple[float, float]:
    return float(spec.get("width", 720)), float(spec.get("height", 420))


def _unit(spec: dict) -> str:
    return str(spec.get("unit", ""))


# --------------------------------------------------------------------------
# CARTESIAN (12)
# --------------------------------------------------------------------------

def render_bar(spec: dict, st: ChartStyle) -> str:
    return _bar_impl(spec, st, horizontal=False)


def render_horizontal_bar(spec: dict, st: ChartStyle) -> str:
    return _bar_impl(spec, st, horizontal=True)


def _bar_impl(spec: dict, st: ChartStyle, horizontal: bool) -> str:
    pairs = _pairs(spec)
    if len(pairs) > 12:
        raise ChartJudgmentError(
            f"{len(pairs)} categories is unreadable as bars. Rank and keep the "
            "top 8-10 (+기타), or use a table.")
    if len(pairs) <= 3 and not spec.get("options", {}).get("allow_tiny"):
        _warn(f"{len(pairs)} data points — consider kpi_cards instead of a bar chart "
              "(negative rule: ≤3 points reads better as stat cards).")
    W, H = _dims(spec)
    unit = _unit(spec)
    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]
    focus = spec.get("options", {}).get("focus")
    focus_idx = None
    if focus is not None:
        focus_idx = focus if isinstance(focus, int) else (
            labels.index(focus) if focus in labels else None)

    w = SvgWriter(st)
    f, val, band = ca.build_frame(w, W, H, (min(values), max(values)), labels,
                                  horizontal=horizontal, unit=unit)
    accent_paint = st.series_paints(1)[0]
    rx = min(st.radius["xs"], 4.0)
    cap = st.type["caption"]
    for i, v in enumerate(values):
        fill, fop = accent_paint if focus_idx in (None, i) else st.muted_paint
        if horizontal:
            x0 = val(min(0.0, v)) if val.lo <= 0 else f.x0
            y = band.start(i)
            w.rect(min(x0, val(v)), y, abs(val(v) - x0), band.band, fill, rx=rx,
                   fill_opacity=fop)
            lx = max(val(v), x0) + 8
            w.text(lx, band.center(i) + cap.size * 0.34, fmt_number(v, unit),
                   role="caption", fill=st.color["text"], weight=cap.weight + 100)
        else:
            zero_y = val(0.0) if val.lo <= 0 <= val.hi else f.y1
            y_top = min(val(v), zero_y)
            h = abs(val(v) - zero_y)
            w.rect(band.start(i), y_top, band.band, h, fill, rx=rx,
                   fill_opacity=fop)
            if band.band >= text_width(fmt_number(v, unit), cap.size) * 0.7:
                ca.value_label(w, band.center(i), y_top - 6, v, unit)
    return w


def render_grouped_bar(spec: dict, st: ChartStyle) -> str:
    cats, series = _series_table(spec)
    if len(series) < 2:
        raise ChartJudgmentError("grouped_bar needs ≥2 series; use bar for one series.")
    W, H = _dims(spec)
    unit = _unit(spec)
    paints = st.series_paints(len(series))
    all_vals = [v for _, vals in series for v in vals]

    w = SvgWriter(st)
    legend = list(zip((n for n, _ in series), paints))
    f, val, band = ca.build_frame(w, W, H, (min(all_vals), max(all_vals)), cats,
                                  unit=unit, legend_items=legend)
    zero_y = val(0.0) if val.lo <= 0 <= val.hi else f.y1
    inner_gap = 2.0
    sub_w = (band.band - inner_gap * (len(series) - 1)) / len(series)
    rx = min(st.radius["xs"], 3.0)
    for ci in range(len(cats)):
        x = band.start(ci)
        for si, (_, vals) in enumerate(series):
            v = vals[ci]
            y_top = min(val(v), zero_y)
            fill, fop = paints[si]
            w.rect(x + si * (sub_w + inner_gap), y_top, sub_w,
                   abs(val(v) - zero_y), fill, rx=rx, fill_opacity=fop)
    return w


def render_stacked_bar(spec: dict, st: ChartStyle) -> str:
    return _stacked_impl(spec, st, normalized=False)


def render_stacked_bar_100(spec: dict, st: ChartStyle) -> str:
    return _stacked_impl(spec, st, normalized=True)


def _stacked_impl(spec: dict, st: ChartStyle, normalized: bool) -> str:
    cats, series = _series_table(spec)
    if len(series) < 2:
        raise ChartJudgmentError("stacked bars need ≥2 series; use bar for one series.")
    for name, vals in series:
        if any(v < 0 for v in vals):
            raise ChartJudgmentError(
                f"series '{name}' has negative values — stacking mixes signs into a "
                "misleading total. Use grouped_bar or waterfall.")
    W, H = _dims(spec)
    unit = "%" if normalized else _unit(spec)
    paints = st.series_paints(len(series))
    totals = [sum(vals[ci] for _, vals in series) for ci in range(len(cats))]
    if normalized:
        vmax = 100.0
    else:
        vmax = max(totals)

    w = SvgWriter(st)
    legend = list(zip((n for n, _ in series), paints))
    f, val, band = ca.build_frame(w, W, H, (0.0, vmax), cats, unit=unit,
                                  legend_items=legend)
    for ci in range(len(cats)):
        x = band.start(ci)
        cum = 0.0
        total = totals[ci] or 1.0
        for si, (_, vals) in enumerate(series):
            v = vals[ci] / total * 100.0 if normalized else vals[ci]
            y1 = val(cum)
            y2 = val(cum + v)
            fill, fop = paints[si]
            w.rect(x, min(y1, y2), band.band, abs(y1 - y2), fill,
                   fill_opacity=fop)
            cum += v
        if not normalized:
            ca.value_label(w, band.center(ci), val(cum) - 6, totals[ci], unit)
    return w


def render_line(spec: dict, st: ChartStyle) -> str:
    return _line_impl(spec, st, area=False)


def render_multi_line(spec: dict, st: ChartStyle) -> str:
    spec.setdefault("options", {})["_require_multi"] = True
    return _line_impl(spec, st, area=False)


def render_area(spec: dict, st: ChartStyle) -> str:
    return _line_impl(spec, st, area=True)


def _line_impl(spec: dict, st: ChartStyle, area: bool) -> str:
    cats, series = _series_table(spec, max_series=3 if not area else 2)
    opts = spec.get("options", {})
    if opts.get("_require_multi") and len(series) < 2:
        raise ChartJudgmentError("multi_line needs ≥2 series; use line for one.")
    if len(cats) < 4:
        _warn(f"only {len(cats)} points on a time axis — a trend needs ≥4 points; "
              "consider bar or a hero stat (kpi_cards).")
    W, H = _dims(spec)
    unit = _unit(spec)
    paints = st.series_paints(max(len(series), 1))
    all_vals = [v for _, vals in series for v in vals]

    w = SvgWriter(st)
    legend = (list(zip((n for n, _ in series), paints))
              if len(series) > 1 else None)
    f, val, band = ca.build_frame(w, W, H, (min(all_vals), max(all_vals)), cats,
                                  unit=unit, include_zero=area,
                                  legend_items=legend)
    lw = max(st.stroke["emphasis"], 2.0)
    cap = st.type["caption"]
    for si, (name, vals) in enumerate(series):
        pts = [(band.center(i), val(v)) for i, v in enumerate(vals)]
        stroke_hex, stroke_op = paints[si]
        if area:
            base = val(max(0.0, val.lo))
            # translucent fill so gridlines read through; converter maps to alpha
            w.path(ca.area_path(pts, base), fill=st.color["accent"],
                   fill_opacity=0.18 if si == 0 else 0.32)
        w.path(ca.polyline_path(pts), stroke=stroke_hex, stroke_width=lw,
               linejoin="round", linecap="round",
               stroke_opacity=None if stroke_op >= 0.84 else stroke_op)
        # end-point marker + last-value label (presentation style)
        ex, ey = pts[-1]
        w.circle(ex, ey, lw + 1.2, stroke_hex,
                 fill_opacity=None if stroke_op >= 0.84 else stroke_op)
        w.text(ex + 8, ey + cap.size * 0.34, fmt_number(vals[-1], unit),
               role="caption", fill=st.color["text"], weight=cap.weight + 100)
    return w


def render_scatter(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, list) or len(data) < 3:
        raise SpecError("scatter data must be a list of ≥3 {x, y[, label]} points")
    pts = []
    for row in data:
        try:
            pts.append((float(row["x"]), float(row["y"]), str(row.get("label", ""))))
        except (KeyError, TypeError, ValueError) as exc:
            raise SpecError(f"bad scatter point {row!r}") from exc
    W, H = _dims(spec)
    opts = spec.get("options", {})
    w = SvgWriter(st)
    f, val, xs = ca.build_frame(
        w, W, H, (min(p[1] for p in pts), max(p[1] for p in pts)), None,
        x_numeric_domain=(min(p[0] for p in pts), max(p[0] for p in pts)),
        unit=_unit(spec))
    accent_hex, accent_op = st.series_paints(1)[0]
    cap = st.type["caption"]
    r = 5.0
    for x, y, label in pts:
        w.circle(xs(x), val(y), r, accent_hex, fill_opacity=accent_op)
        if label:
            w.text(xs(x) + r + 4, val(y) + cap.size * 0.34,
                   truncate_to_width(label, cap.size, 110),
                   role="caption", fill=st.color["text-secondary"])
    ax_label = opts.get("x_label")
    ay_label = opts.get("y_label")
    tt_hex, tt_op = st.neutral_paint("text-tertiary", "text", 0.45)
    if ax_label:
        w.text(f.x1, f.y1 - 8, str(ax_label), role="caption",
               fill=tt_hex, fill_opacity=tt_op, anchor="end")
    if ay_label:
        w.text(f.x0 + 4, f.y0 + cap.size, str(ay_label), role="caption",
               fill=tt_hex, fill_opacity=tt_op)
    return w


def render_combo(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, dict) or "bars" not in data or "line" not in data:
        raise SpecError("combo data must be {categories, bars:{name,values}, "
                        "line:{name,values}}")
    cats = [str(c) for c in data.get("categories", [])]
    bars = data["bars"]
    line = data["line"]
    bvals = [float(v) for v in bars["values"]]
    lvals = [float(v) for v in line["values"]]
    if len(bvals) != len(cats) or len(lvals) != len(cats):
        raise SpecError("bars/line values must match categories length")
    W, H = _dims(spec)
    unit = _unit(spec)
    line_unit = str(spec.get("options", {}).get("line_unit", ""))

    w = SvgWriter(st)
    bar_paint = st.series_paints(2)[1]      # lighter ladder step for bars
    line_color = st.color["accent"]         # solid accent vs 0.60 bars
    legend = [(str(bars.get("name", "값")), bar_paint),
              (str(line.get("name", "추이")), line_color)]
    f, val, band = ca.build_frame(w, W, H, (0.0, max(bvals)), cats, unit=unit,
                                  legend_items=legend)
    rx = min(st.radius["xs"], 3.0)
    for i, v in enumerate(bvals):
        w.rect(band.start(i), val(v), band.band, f.y1 - val(v), bar_paint[0],
               rx=rx, fill_opacity=bar_paint[1])
    # secondary axis for the line, labels on the right edge
    lval = ca.LinearScale((min(lvals), max(lvals)), (f.y1, f.y0), include_zero=False)
    cap = st.type["caption"]
    tt_hex, tt_op = st.neutral_paint("text-tertiary", "text", 0.45)
    for t in lval.ticks:
        w.text(f.x1 + 6, lval(t) + cap.size * 0.34, fmt_number(t, line_unit),
               role="caption", fill=tt_hex, fill_opacity=tt_op)
    pts = [(band.center(i), lval(v)) for i, v in enumerate(lvals)]
    w.path(ca.polyline_path(pts), stroke=line_color,
           stroke_width=max(st.stroke["emphasis"], 2.0), linejoin="round",
           linecap="round")
    for x, y in pts:
        w.circle(x, y, 3.4, line_color)
    return w


def render_waterfall(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, list) or len(data) < 3:
        raise SpecError("waterfall data must be ≥3 rows of {label, value} or "
                        "{label, total: true}")
    W, H = _dims(spec)
    unit = _unit(spec)
    rows = []
    run = 0.0
    for r in data:
        label = str(r.get("label", ""))
        if r.get("total"):
            # Anchor bar drawn from zero: with an explicit value it (re)sets the
            # running level (base/기초); without one it reports the level so far.
            if "value" in r:
                run = float(r["value"])
            rows.append((label, 0.0, 0.0, run, "total"))
        else:
            v = float(r.get("value", 0.0))
            rows.append((label, run, v, run + v, "pos" if v >= 0 else "neg"))
            run += v
    lo = min(min(r[1], r[3]) for r in rows)
    hi = max(max(r[1], r[3]) for r in rows)

    w = SvgWriter(st)
    labels = [r[0] for r in rows]
    f, val, band = ca.build_frame(w, W, H, (lo, hi), labels, unit=unit)
    colors = {"pos": st.semantic("positive"), "neg": st.semantic("negative"),
              "total": st.color["accent"]}
    cap = st.type["caption"]
    prev_edge: tuple[float, float] | None = None
    for i, (label, start, delta, end, kind) in enumerate(rows):
        y_a = val(0.0 if kind == "total" else start)
        y_b = val(end)
        top, bh = min(y_a, y_b), max(abs(y_a - y_b), 2.0)
        w.rect(band.start(i), top, band.band, bh, colors[kind],
               rx=min(st.radius["xs"], 3.0))
        shown = end if kind == "total" else delta
        prefix = "" if kind == "total" else ("+" if delta >= 0 else "")
        w.text(band.center(i), top - 6, prefix + fmt_number(shown, unit),
               role="caption", fill=st.color["text"], anchor="middle",
               weight=cap.weight + 100)
        edge_y = val(end)
        if prev_edge is not None:
            c_hex, c_op = st.neutral_paint("border-strong", "text", 0.26)
            w.line(prev_edge[0], prev_edge[1], band.start(i), prev_edge[1],
                   c_hex, st.stroke["divider"], dash="3,3", stroke_opacity=c_op)
        prev_edge = (band.start(i) + band.band, edge_y)
    return w


def render_bullet(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, list) or not data:
        raise SpecError("bullet data must be a list of {label, value, target[, max]}")
    W, H = _dims(spec)
    unit = _unit(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    rows = []
    for r in data:
        try:
            rows.append((str(r["label"]), float(r["value"]), float(r["target"]),
                         float(r.get("max", 0.0))))
        except (KeyError, TypeError, ValueError) as exc:
            raise SpecError(f"bad bullet row {r!r}") from exc
    label_w = min(max(text_width(r[0], cap.size, cap.weight) for r in rows) + 14,
                  W * 0.3)
    value_w = 84.0
    track_x = label_w
    track_w = W - label_w - value_w
    row_h = H / len(rows)
    bar_h = min(18.0, row_h * 0.34)
    accent = st.color["accent"]
    for i, (label, value, target, vmax) in enumerate(rows):
        m = max(vmax, value, target) * 1.06 or 1.0
        cy = row_h * i + row_h / 2
        w.text(track_x - 10, cy + cap.size * 0.34, label, role="caption",
               fill=st.color["text-secondary"], anchor="end")
        t_hex, t_op = st.neutral_paint("surface-alt", "text", 0.06)
        w.rect(track_x, cy - bar_h, track_w, bar_h * 2, t_hex,
               rx=min(st.radius["xs"], bar_h), fill_opacity=t_op)
        w.rect(track_x, cy - bar_h / 2, track_w * (value / m), bar_h, accent,
               rx=min(st.radius["xs"], bar_h / 2))
        tx = track_x + track_w * (target / m)
        w.line(tx, cy - bar_h * 1.35, tx, cy + bar_h * 1.35, st.color["text"],
               st.stroke["emphasis"])
        pct = value / target * 100 if target else 0.0
        w.text(track_x + track_w + 10, cy + cap.size * 0.34,
               f"{fmt_number(value, unit)} ({pct:.0f}%)", role="caption",
               fill=st.color["text"], weight=cap.weight + 100)
    return w


# --------------------------------------------------------------------------
# POLAR (4)
# --------------------------------------------------------------------------

def render_pie(spec: dict, st: ChartStyle) -> str:
    return _pie_impl(spec, st, inner_ratio=0.0)


def render_donut(spec: dict, st: ChartStyle) -> str:
    return _pie_impl(spec, st, inner_ratio=0.62)


def _pie_impl(spec: dict, st: ChartStyle, inner_ratio: float) -> str:
    pairs = _pairs(spec)
    if len(pairs) > 5:
        raise ChartJudgmentError(
            f"{len(pairs)} slices — a pie stops being readable past 5. Use "
            "horizontal_bar (sorted) instead, or aggregate to top-4 + 기타.")
    if len(pairs) < 2:
        raise ChartJudgmentError("a one-slice pie is a KPI; use kpi_cards or gauge.")
    if any(v < 0 for _, v in pairs):
        raise ChartJudgmentError("negative values cannot be pie slices; use bar "
                                 "or waterfall for signed data.")
    total = sum(v for _, v in pairs)
    if total <= 0:
        raise SpecError("pie values must sum to a positive number")
    W, H = _dims(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    cx, cy = W / 2, H / 2
    r_out = min(W, H) / 2 - cap.size * 2.6
    r_in = r_out * inner_ratio
    paints = st.series_paints(min(len(pairs), MAX_SERIES))
    if len(pairs) > len(paints):  # 5 slices, 4-step ladder → last uses muted
        paints = paints + [st.muted_paint] * (len(pairs) - len(paints))
    w.radial_area = ("donut" if inner_ratio > 0 else "pie", cx, cy, r_out, r_in)
    angles = po.slice_angles([v for _, v in pairs])
    for i, ((label, v), (a0, a1)) in enumerate(zip(pairs, angles)):
        fill, fop = paints[i]
        w.path(po.arc_segment_path(cx, cy, r_out, r_in, a0, a1), fill=fill,
               fill_opacity=fop,
               stroke=st.color["bg"], stroke_width=2.0, linejoin="round")
        mid = (a0 + a1) / 2
        lx, ly = po.polar_xy(cx, cy, r_out + 10, mid)
        anchor = po.label_anchor_for_angle(mid)
        pct = v / total * 100
        w.text(lx, ly + cap.size * 0.2, f"{label} {pct:.0f}%", role="caption",
               fill=st.color["text-secondary"], anchor=anchor)
    if inner_ratio > 0:
        center = spec.get("options", {}).get("center_label")
        ds = st.type["display-sm"]
        if center:
            w.text(cx, cy + ds.size * 0.36, str(center), role="display-sm",
                   fill=st.color["text"], anchor="middle",
                   size=min(ds.size, r_in * 0.72))
    return w


def render_gauge(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, dict) or "value" not in data:
        raise SpecError("gauge data must be {value, max[, label]}")
    value = float(data["value"])
    vmax = float(data.get("max", 100.0))
    if vmax <= 0:
        raise SpecError("gauge max must be positive")
    frac = max(0.0, min(1.0, value / vmax))
    W, H = _dims(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    cx = W / 2
    r_out = min(W / 2, H * 0.86) - 6
    cy = H * 0.92
    r_in = r_out * 0.68
    w.radial_area = ("donut", cx, cy, r_out, r_in)
    half = math.tau / 4
    t_hex, t_op = st.neutral_paint("surface-alt", "text", 0.06)
    w.path(po.arc_segment_path(cx, cy, r_out, r_in, -half, half),
           fill=t_hex, fill_opacity=t_op)
    if frac > 0.002:
        w.path(po.arc_segment_path(cx, cy, r_out, r_in, -half,
                                   -half + frac * math.pi),
               fill=st.color["accent"])
    ds = st.type["display-sm"]
    w.text(cx, cy - r_in * 0.16, fmt_number(value, _unit(spec) or "%"),
           role="display-sm", fill=st.color["text"], anchor="middle",
           size=min(ds.size, r_in * 0.62))
    label = data.get("label")
    if label:
        w.text(cx, cy - r_in * 0.16 + cap.size * 1.7, str(label), role="caption",
               fill=st.color["text-secondary"], anchor="middle")
    tt_hex, tt_op = st.neutral_paint("text-tertiary", "text", 0.45)
    w.text(cx - (r_out + r_in) / 2, cy + cap.size * 1.35, "0", role="caption",
           fill=tt_hex, fill_opacity=tt_op, anchor="middle")
    w.text(cx + (r_out + r_in) / 2, cy + cap.size * 1.35, fmt_number(vmax),
           role="caption", fill=tt_hex, fill_opacity=tt_op, anchor="middle")
    return w


def render_radar(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, dict):
        raise SpecError("radar data must be {axes: [...], series: [{name, values}]}")
    axes = [str(a) for a in data.get("axes", [])]
    if not (5 <= len(axes) <= 8):
        raise ChartJudgmentError(
            f"radar needs 5-8 axes on one shared scale; got {len(axes)}. "
            "Use grouped_bar for fewer axes or differing scales.")
    raw = data.get("series", [])
    if not raw:
        raise SpecError("radar needs at least one series")
    if len(raw) > 3:
        raise ChartJudgmentError("more than 3 radar polygons are unreadable; "
                                 "compare pairwise or use grouped_bar.")
    series = []
    for s in raw:
        vals = [float(v) for v in s["values"]]
        if len(vals) != len(axes):
            raise SpecError(f"series '{s.get('name')}' length != axes length")
        series.append((str(s.get("name", "?")), vals))
    vmax = float(data.get("max", max(v for _, vals in series for v in vals)))

    W, H = _dims(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    cx, cy = W / 2, H / 2 + cap.size * 0.4
    r = min(W, H) / 2 - cap.size * 2.8
    w.radial_area = ("radar", cx, cy, r, 0.0)
    for ring in po.radar_grid_points(cx, cy, r, len(axes), 4):
        w.polygon(ring, fill="none", stroke=st.grid_stroke,
                  stroke_width=st.stroke["divider"], linejoin="round")
    for i in range(len(axes)):
        ax, ay = po.polar_xy(cx, cy, r, i * math.tau / len(axes))
        w.line(cx, cy, ax, ay, st.grid_stroke, st.stroke["divider"])
        lx, ly = po.polar_xy(cx, cy, r + 12, i * math.tau / len(axes))
        w.text(lx, ly + cap.size * 0.3, axes[i], role="caption",
               fill=st.color["text-secondary"],
               anchor=po.label_anchor_for_angle(i * math.tau / len(axes)))
    paints = st.series_paints(max(len(series), 2))
    for si, (name, vals) in enumerate(series):
        pts = po.radar_points(cx, cy, r, vals, vmax)
        s_hex, s_op = paints[si]
        w.polygon(pts, fill=st.color["accent"],
                  fill_opacity=0.16 if si == 0 else 0.10,
                  stroke=s_hex, stroke_opacity=None if s_op >= 0.84 else s_op,
                  stroke_width=max(st.stroke["emphasis"], 2.0), linejoin="round")
        for x, y in pts:
            w.circle(x, y, 3.0, s_hex,
                     fill_opacity=None if s_op >= 0.84 else s_op)
    if len(series) > 1:
        lx = 8.0
        for si, (name, _) in enumerate(series):
            s_hex, s_op = paints[si]
            w.rect(lx, 4, 10, 10, s_hex, rx=2, fill_opacity=s_op)
            lx += 16
            w.text(lx, 4 + cap.size * 0.85, name, role="caption",
                   fill=st.color["text-secondary"])
            lx += text_width(name, cap.size, cap.weight) + 18
    return w


# --------------------------------------------------------------------------
# LAYOUT (5)
# --------------------------------------------------------------------------

def render_kpi_cards(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, list) or not (1 <= len(data) <= 8):
        raise SpecError("kpi_cards data must be a list of 1-8 "
                        "{label, value[, delta][, unit]} rows")
    W, H = _dims(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    ds = st.type["display-sm"]
    cells = lay.grid_cells(len(data), W, H, gap=float(st.spacing.get("4", 16)))
    for (cx, cy, cw, ch), row in zip(cells, data):
        label = str(row.get("label", ""))
        value = row.get("value", "")
        unit = str(row.get("unit", ""))
        value_s = fmt_number(float(value), unit) if isinstance(
            value, (int, float)) else f"{value}{unit}"
        if st.card_style == "filled":
            t_hex, t_op = st.neutral_paint("surface-alt", "text", 0.06)
            w.rect(cx, cy, cw, ch, t_hex, rx=st.radius["md"], fill_opacity=t_op)
        elif st.card_style == "hairline":
            w.rect(cx, cy, cw, ch, st.color["surface"], rx=st.radius["md"],
                   stroke=st.color["border"], stroke_width=st.stroke["divider"])
        else:  # borderless
            w.line(cx, cy + ch, cx + cw, cy + ch, st.color["border"],
                   st.stroke["divider"])
        pad = float(st.spacing.get("4", 16))
        lab = st.type["label"]
        w.text(cx + pad, cy + pad + lab.size, label, role="label",
               fill=st.color["text-secondary"])
        vsize = min(ds.size, ch * 0.34, cw / max(1, len(value_s)) * 1.7)
        w.text(cx + pad, cy + ch * 0.62, value_s, role="display-sm",
               fill=st.color["text"], size=vsize)
        delta = row.get("delta")
        if delta is not None:
            dv = float(delta)
            col = st.semantic("positive") if dv >= 0 else st.semantic("negative")
            arrow = "▲" if dv >= 0 else "▼"
            w.text(cx + pad, cy + ch * 0.62 + cap.size * 1.6,
                   f"{arrow} {fmt_number(abs(dv), str(row.get('delta_unit', '%')))}",
                   role="caption", fill=col, weight=cap.weight + 100)
    return w


def render_progress(spec: dict, st: ChartStyle) -> str:
    pairs = _pairs(spec)
    if len(pairs) > 8:
        raise ChartJudgmentError("more than 8 progress rows → use a table.")
    W, H = _dims(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    label_w = min(max(text_width(p[0], cap.size, cap.weight) for p in pairs) + 14,
                  W * 0.32)
    value_w = 64.0
    bar_x = label_w
    bar_w = W - label_w - value_w
    row_h = H / len(pairs)
    bh = min(12.0, row_h * 0.3)
    for i, (label, v) in enumerate(pairs):
        frac = max(0.0, min(1.0, v / 100.0))
        cy = row_h * i + row_h / 2
        w.text(bar_x - 10, cy + cap.size * 0.34, label, role="caption",
               fill=st.color["text-secondary"], anchor="end")
        t_hex, t_op = st.neutral_paint("surface-alt", "text", 0.06)
        w.rect(bar_x, cy - bh / 2, bar_w, bh, t_hex,
               rx=min(st.radius["pill"], bh / 2), fill_opacity=t_op)
        if frac > 0.005:
            w.rect(bar_x, cy - bh / 2, bar_w * frac, bh, st.color["accent"],
                   rx=min(st.radius["pill"], bh / 2))
        w.text(bar_x + bar_w + 10, cy + cap.size * 0.34, f"{v:.0f}%",
               role="caption", fill=st.color["text"], weight=cap.weight + 100)
    return w


def render_funnel(spec: dict, st: ChartStyle) -> str:
    pairs = _pairs(spec)
    if not (3 <= len(pairs) <= 5):
        raise ChartJudgmentError(
            f"funnel reads best with 3-5 stages; got {len(pairs)}. Merge stages "
            "or use horizontal_bar.")
    values = [v for _, v in pairs]
    if any(values[i] < values[i + 1] for i in range(len(values) - 1)):
        _warn("funnel stages increase mid-flow — a funnel implies monotone "
              "narrowing; verify the data or use bar.")
    W, H = _dims(spec)
    unit = _unit(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    side_w = W * 0.30
    fw = W - side_w
    paints = st.series_paints(4)
    stages = lay.funnel_trapezoids(values, fw * 0.9, H, gap=6.0)
    cx = fw / 2
    for i, ((label, v), (y, tw, bw, h, _)) in enumerate(zip(pairs, stages)):
        paint = paints[min(i, len(paints) - 1)]
        w.polygon([(cx - tw / 2, y), (cx + tw / 2, y),
                   (cx + bw / 2, y + h), (cx - bw / 2, y + h)],
                  fill=paint[0], fill_opacity=paint[1], linejoin="round")
        ty = y + h / 2
        inner = st.contrast_text(st.paint_solid(paint))
        w.text(cx, ty - 2, label, role="caption", fill=inner, anchor="middle",
               weight=cap.weight + 100)
        w.text(cx, ty + cap.size * 1.15, fmt_number(v, unit), role="caption",
               fill=inner, anchor="middle")
        if i > 0:
            conv = v / values[i - 1] * 100 if values[i - 1] else 0.0
            w.text(fw + 12, y + cap.size * 0.5, f"▸ 전환 {conv:.0f}%",
                   role="caption", fill=st.color["text-secondary"])
    total_conv = values[-1] / values[0] * 100 if values[0] else 0.0
    w.text(fw + 12, H - 4, f"전체 전환율 {total_conv:.1f}%", role="caption",
           fill=st.color["text"], weight=cap.weight + 100)
    return w


def render_heatmap(spec: dict, st: ChartStyle) -> str:
    data = spec.get("data")
    if not isinstance(data, dict):
        raise SpecError("heatmap data must be {rows: [...], cols: [...], "
                        "values: [[...]]}")
    rows = [str(r) for r in data.get("rows", [])]
    cols = [str(c) for c in data.get("cols", [])]
    values = data.get("values")
    if not rows or not cols or not isinstance(values, list):
        raise SpecError("heatmap needs rows, cols, values")
    if len(rows) > 12 or len(cols) > 14:
        raise ChartJudgmentError("heatmap beyond 12×14 cells is unreadable on a "
                                 "slide; aggregate buckets first.")
    grid = [[float(v) for v in row] for row in values]
    if len(grid) != len(rows) or any(len(r) != len(cols) for r in grid):
        raise SpecError("values shape must be rows × cols")
    flat = [v for row in grid for v in row]
    vmin, vmax = min(flat), max(flat)
    span = (vmax - vmin) or 1.0

    W, H = _dims(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    label_w = min(max(text_width(r, cap.size, cap.weight) for r in rows) + 12,
                  W * 0.28)
    header_h = cap.size * 1.8
    cells = lay.heat_matrix_cells(len(rows), len(cols), W - label_w,
                                  H - header_h, gap=3.0)
    show_values = bool(spec.get("options", {}).get("show_values", True))
    for ci, cname in enumerate(cols):
        x, _, cw, _ = cells[0][ci]
        w.text(label_w + x + cw / 2, cap.size, cname, role="caption",
               fill=st.color["text-secondary"], anchor="middle")
    for ri, rname in enumerate(rows):
        x, y, cw, ch = cells[ri][0]
        w.text(label_w - 8, header_h + y + ch / 2 + cap.size * 0.34, rname,
               role="caption", fill=st.color["text-secondary"], anchor="end")
        for ci in range(len(cols)):
            x, y, cw, ch = cells[ri][ci]
            t = (grid[ri][ci] - vmin) / span
            alpha = st.sequential_alpha(t)
            w.rect(label_w + x, header_h + y, cw, ch, st.color["accent"],
                   rx=min(st.radius["xs"], 4.0), fill_opacity=alpha)
            if show_values and cw > 34:
                solid = st.paint_solid((st.color["accent"], alpha))
                w.text(label_w + x + cw / 2, header_h + y + ch / 2 + cap.size * 0.34,
                       fmt_number(grid[ri][ci]), role="caption",
                       fill=st.contrast_text(solid), anchor="middle")
    return w


def render_treemap(spec: dict, st: ChartStyle) -> str:
    pairs = _pairs(spec)
    if not (3 <= len(pairs) <= 12):
        raise ChartJudgmentError(
            f"treemap works for 3-12 items; got {len(pairs)}. Under 3 → donut/bar; "
            "over 12 → aggregate or use a table.")
    if any(v <= 0 for _, v in pairs):
        raise ChartJudgmentError("treemap areas must be positive values.")
    W, H = _dims(spec)
    unit = _unit(spec)
    w = SvgWriter(st)
    cap = st.type["caption"]
    values = [v for _, v in pairs]
    rects = lay.squarify(values, 0, 0, W, H)
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    rank = {idx: pos for pos, idx in enumerate(order)}
    total = sum(values)
    for i, ((label, v), (x, y, cw, ch)) in enumerate(zip(pairs, rects)):
        t = 1.0 - (rank[i] / max(1, len(pairs) - 1)) * 0.82
        alpha = st.sequential_alpha(t)
        w.rect(x + 1.5, y + 1.5, cw - 3, ch - 3, st.color["accent"],
               rx=min(st.radius["xs"], 4.0), fill_opacity=alpha)
        if cw > 64 and ch > 40:
            inner = st.contrast_text(st.paint_solid((st.color["accent"], alpha)))
            lbl = truncate_to_width(label, cap.size, cw - 16, cap.weight)
            w.text(x + 10, y + cap.size * 1.5, lbl, role="caption", fill=inner,
                   weight=cap.weight + 100)
            w.text(x + 10, y + cap.size * 2.9,
                   f"{fmt_number(v, unit)} · {v / total * 100:.0f}%",
                   role="caption", fill=inner)
    return w


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

RENDERERS = {
    # cartesian (12)
    "bar": render_bar,
    "horizontal_bar": render_horizontal_bar,
    "grouped_bar": render_grouped_bar,
    "stacked_bar": render_stacked_bar,
    "stacked_bar_100": render_stacked_bar_100,
    "line": render_line,
    "multi_line": render_multi_line,
    "area": render_area,
    "scatter": render_scatter,
    "combo": render_combo,
    "waterfall": render_waterfall,
    "bullet": render_bullet,
    # polar (4)
    "pie": render_pie,
    "donut": render_donut,
    "gauge": render_gauge,
    "radar": render_radar,
    # layout (5)
    "kpi_cards": render_kpi_cards,
    "progress": render_progress,
    "funnel": render_funnel,
    "heatmap": render_heatmap,
    "treemap": render_treemap,
}


def render(spec: dict, st: ChartStyle):
    """Render a spec; returns the SvgWriter (markup via .fragment(), plot-area
    info via .plot_rect / .radial_area for the ppt-master §3.1 marker)."""
    ctype = spec.get("type")
    if ctype not in RENDERERS:
        raise SpecError(
            f"unknown chart type {ctype!r}. Supported: {', '.join(sorted(RENDERERS))}")
    return RENDERERS[ctype](spec, st)


def plot_marker(w, spec: dict) -> tuple:
    """Marker tuple for wrap_fragment: renderer-provided area, else the region."""
    if w.radial_area is not None:
        return w.radial_area
    if w.plot_rect is not None:
        return ("rect",) + tuple(w.plot_rect)
    return ("rect", 0.0, 0.0, float(spec.get("width", 720)),
            float(spec.get("height", 420)))
