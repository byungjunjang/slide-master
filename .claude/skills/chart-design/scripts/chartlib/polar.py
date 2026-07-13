"""Polar coordinate engine — angle/radius math and arc paths.

Shared by pie, donut, gauge (half-donut), radar. Angles are radians measured
clockwise from 12 o'clock (SVG y grows downward), matching how presentation
audiences read circular charts.
"""
from __future__ import annotations

import math


def polar_xy(cx: float, cy: float, r: float, angle: float) -> tuple[float, float]:
    """angle=0 at 12 o'clock, clockwise positive."""
    return cx + r * math.sin(angle), cy - r * math.cos(angle)


def arc_segment_path(cx: float, cy: float, r_outer: float, r_inner: float,
                     a0: float, a1: float) -> str:
    """Closed donut-segment path from angle a0 to a1 (a1 > a0).

    A full circle can't be one SVG arc; segments >= ~355° are split internally.
    """
    span = a1 - a0
    if span >= math.tau - 1e-6:
        mid = a0 + span / 2
        return (arc_segment_path(cx, cy, r_outer, r_inner, a0, mid) + " " +
                arc_segment_path(cx, cy, r_outer, r_inner, mid, a1))
    large = 1 if span > math.pi else 0
    ox0, oy0 = polar_xy(cx, cy, r_outer, a0)
    ox1, oy1 = polar_xy(cx, cy, r_outer, a1)
    if r_inner <= 0.01:
        return (f"M{cx:.2f},{cy:.2f} L{ox0:.2f},{oy0:.2f} "
                f"A{r_outer:.2f},{r_outer:.2f} 0 {large} 1 {ox1:.2f},{oy1:.2f} Z")
    ix0, iy0 = polar_xy(cx, cy, r_inner, a0)
    ix1, iy1 = polar_xy(cx, cy, r_inner, a1)
    return (f"M{ix0:.2f},{iy0:.2f} L{ox0:.2f},{oy0:.2f} "
            f"A{r_outer:.2f},{r_outer:.2f} 0 {large} 1 {ox1:.2f},{oy1:.2f} "
            f"L{ix1:.2f},{iy1:.2f} "
            f"A{r_inner:.2f},{r_inner:.2f} 0 {large} 0 {ix0:.2f},{iy0:.2f} Z")


def slice_angles(values: list[float], start: float = 0.0,
                 total: float | None = None) -> list[tuple[float, float]]:
    """Cumulative (a0, a1) pairs over a full turn (or a fraction if total>sum)."""
    s = total if total is not None else sum(values)
    if s <= 0:
        raise ValueError("polar slice values must sum to a positive number")
    out = []
    a = start
    for v in values:
        span = (v / s) * math.tau
        out.append((a, a + span))
        a += span
    return out


def radar_grid_points(cx: float, cy: float, r: float, axes: int,
                      levels: int) -> list[list[tuple[float, float]]]:
    """Concentric polygon rings, outermost last."""
    rings = []
    for lv in range(1, levels + 1):
        rr = r * lv / levels
        ring = [polar_xy(cx, cy, rr, i * math.tau / axes) for i in range(axes)]
        rings.append(ring)
    return rings


def radar_points(cx: float, cy: float, r: float, values: list[float],
                 vmax: float) -> list[tuple[float, float]]:
    n = len(values)
    return [polar_xy(cx, cy, r * max(0.0, min(1.0, v / vmax)), i * math.tau / n)
            for i, v in enumerate(values)]


def label_anchor_for_angle(angle: float) -> str:
    """text-anchor for a label placed just outside radius at `angle`."""
    a = angle % math.tau
    if a < math.radians(15) or a > math.tau - math.radians(15):
        return "middle"
    if abs(a - math.pi) < math.radians(15):
        return "middle"
    return "start" if a < math.pi else "end"
