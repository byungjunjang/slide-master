"""Layout engine — placement logic for coordinate-free visualizations.

KPI cards, progress bars, funnel, heatmap matrix, treemap. No axes; each
helper solves one geometry problem and renderers apply token styling.
"""
from __future__ import annotations


def grid_cells(n: int, width: float, height: float, gap: float,
               max_cols: int = 4) -> list[tuple[float, float, float, float]]:
    """Card grid: n cells → (x, y, w, h). 2x2 for 4, single row up to max_cols."""
    if n <= max_cols:
        cols, rows = n, 1
    else:
        cols = max_cols if n > 6 else 3
        rows = (n + cols - 1) // cols
    cw = (width - gap * (cols - 1)) / cols
    ch = (height - gap * (rows - 1)) / rows
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        out.append((c * (cw + gap), r * (ch + gap), cw, ch))
    return out


def funnel_trapezoids(values: list[float], width: float, height: float,
                      gap: float, min_ratio: float = 0.28
                      ) -> list[tuple[float, float, float, float, float]]:
    """Symmetric funnel stages → (y, top_w, bottom_w, h, cx_offset=0).

    Widths are proportional to values, floored at min_ratio of full width so
    late stages stay labelable.
    """
    if not values:
        return []
    vmax = max(values)
    if vmax <= 0:
        raise ValueError("funnel values must contain a positive maximum")
    n = len(values)
    stage_h = (height - gap * (n - 1)) / n
    widths = [max(min_ratio, v / vmax) * width for v in values]
    out = []
    y = 0.0
    for i in range(n):
        top_w = widths[i]
        bottom_w = widths[i + 1] if i + 1 < n else widths[i] * 0.82
        out.append((y, top_w, bottom_w, stage_h, 0.0))
        y += stage_h + gap
    return out


def squarify(values: list[float], x: float, y: float, w: float, h: float
             ) -> list[tuple[float, float, float, float]]:
    """Bruls squarified treemap. values must be positive; order is preserved
    in the returned rect list (rects[i] corresponds to values[i])."""
    idx = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    total = sum(values)
    if total <= 0:
        raise ValueError("treemap values must sum to a positive number")
    area = w * h
    scaled = [values[i] / total * area for i in idx]
    rects_sorted: list[tuple[float, float, float, float]] = []
    _squarify_rec(scaled, [], x, y, w, h, rects_sorted)
    out: list[tuple[float, float, float, float] | None] = [None] * len(values)
    for pos, i in enumerate(idx):
        out[i] = rects_sorted[pos]
    return out  # type: ignore[return-value]


def _worst(row: list[float], side: float) -> float:
    s = sum(row)
    if s <= 0 or side <= 0:
        return float("inf")
    mx, mn = max(row), min(row)
    return max((side * side * mx) / (s * s), (s * s) / (side * side * mn))


def _squarify_rec(children: list[float], row: list[float], x: float, y: float,
                  w: float, h: float, out: list) -> None:
    if not children:
        if row:
            _layout_row(row, x, y, w, h, out)
        return
    side = min(w, h)
    head, rest = children[0], children[1:]
    if not row or _worst(row + [head], side) <= _worst(row, side):
        _squarify_rec(rest, row + [head], x, y, w, h, out)
    else:
        nx, ny, nw, nh = _layout_row(row, x, y, w, h, out)
        _squarify_rec(children, [], nx, ny, nw, nh, out)


def _layout_row(row: list[float], x: float, y: float, w: float, h: float,
                out: list) -> tuple[float, float, float, float]:
    s = sum(row)
    if w >= h:  # lay the row vertically along the left edge
        rw = s / h if h > 0 else 0
        cy = y
        for v in row:
            ch = v / rw if rw > 0 else 0
            out.append((x, cy, rw, ch))
            cy += ch
        return x + rw, y, w - rw, h
    rh = s / w if w > 0 else 0
    cx = x
    for v in row:
        cw = v / rh if rh > 0 else 0
        out.append((cx, y, cw, rh))
        cx += cw
    return x, y + rh, w, h - rh


def heat_matrix_cells(rows: int, cols: int, width: float, height: float,
                      gap: float) -> list[list[tuple[float, float, float, float]]]:
    cw = (width - gap * (cols - 1)) / cols
    ch = (height - gap * (rows - 1)) / rows
    return [[(c * (cw + gap), r * (ch + gap), cw, ch) for c in range(cols)]
            for r in range(rows)]
