"""Bind hand-authored connector routes to native shapes (a:stCxn / a:endCxn).

A plain ``<line>``, ``<polyline>``, or ``<path>`` route names the shapes it
joins with ``data-pptx-start`` / ``data-pptx-end`` (SVG ids on the same page)
and may pin a connection site with ``data-pptx-start-site`` /
``data-pptx-end-site``. Export writes the route as a ``p:cxnSp`` whose preset
matches it (``straightConnector1`` or ``bentConnector2/3``). The authoring
contract lives in references/native-shape-authoring.md §6.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from pptx_shapes import get_preset_registry

from .context import IDENTITY_MATRIX, AffineMatrix
from .paths import normalize_path_commands, parse_svg_path, svg_path_to_absolute
from .utils import (
    matrix_multiply,
    parse_svg_length,
    parse_transform_matrix,
    transform_point,
)


START_ATTR = 'data-pptx-start'
END_ATTR = 'data-pptx-end'
_ROUTE_TAGS = frozenset({'line', 'polyline', 'path'})
_SKIPPED_TAGS = frozenset({
    'defs', 'metadata', 'title', 'desc', 'style', 'clipPath', 'mask',
    'marker', 'pattern', 'symbol', 'svg',
})
_ADJUSTMENT_PREFIX = 'data-pptx-av-'
# Route points closer than this (SVG px) are one point; a segment whose
# cross-axis drift stays within it counts as horizontal or vertical.
_TOLERANCE_PX = 0.5
# A bound end must touch its shape's box (arrowhead gaps allowed). PowerPoint
# snaps the end onto the site when the shape moves, so a far end would jump.
_MAX_ENDPOINT_GAP_PX = 16.0
_U_TURN_RUN_PX = 4 / 3  # 1 pt, the run PowerPoint writes for a U-shaped elbow


@dataclass
class ConnectorEnd:
    """One resolved attachment of a bound route."""

    carrier: ET.Element  # element that claims the target's native shape id
    svg_id: str
    site: int
    presets: frozenset[str]  # native presets the carrier may export as


@dataclass
class ConnectorBinding:
    """A bound route with its resolved start and end attachments."""

    route: ET.Element
    start: ConnectorEnd | None
    end: ConnectorEnd | None


def is_bound_route(elem: ET.Element) -> bool:
    return elem.get(START_ATTR) is not None or elem.get(END_ATTR) is not None


def validate_connector_bindings(root: ET.Element) -> list[str]:
    """Return authoring errors for every bound route on one SVG page."""
    return resolve_connector_bindings(root)[1]


def resolve_connector_bindings(
    root: ET.Element,
) -> tuple[list[ConnectorBinding], list[str]]:
    """Resolve every ``data-pptx-start/end`` route on one SVG page.

    Each route reports at most one error. Export stops on any error; the
    quality checker reports them before export.
    """
    viewport = _viewport_size(root)
    by_id: dict[str, list[tuple[ET.Element, AffineMatrix]]] = {}
    routes: list[tuple[ET.Element, AffineMatrix]] = []
    for elem, matrix in _rendered_elements(root, IDENTITY_MATRIX):
        elem_id = elem.get('id')
        if elem_id:
            by_id.setdefault(elem_id, []).append((elem, matrix))
        if is_bound_route(elem):
            routes.append((elem, matrix))
    # Master/Layout atoms leave the slide after conversion.
    fixed_layer = {
        node
        for elem in root.iter()
        if elem.get('data-pptx-layer') in {'master', 'layout'}
        for node in elem.iter()
    }

    bindings: list[ConnectorBinding] = []
    errors: list[str] = []
    for index, (route, matrix) in enumerate(routes, start=1):
        try:
            binding = _resolve_route(route, matrix, by_id, viewport)
            for end in (binding.start, binding.end):
                if end is not None and end.carrier in fixed_layer:
                    raise ValueError(
                        f'"{end.svg_id}" is a Master/Layout atom; bind only '
                        'slide shapes'
                    )
            bindings.append(binding)
        except ValueError as exc:
            label = route.get('id') or f'#{index}'
            errors.append(
                f'Bound connector <{_local_tag(route)}> {label}: {exc}'
            )
    return bindings, errors


def route_points(
    route: ET.Element,
    viewport: tuple[float, float],
) -> list[tuple[float, float]]:
    """Return a route's points in its own SVG user space."""
    tag = _local_tag(route)
    if tag == 'line':
        width, height = viewport
        return [
            (
                parse_svg_length(route.get('x1'), percent_base=width),
                parse_svg_length(route.get('y1'), percent_base=height),
            ),
            (
                parse_svg_length(route.get('x2'), percent_base=width),
                parse_svg_length(route.get('y2'), percent_base=height),
            ),
        ]
    if tag == 'polyline':
        data = f"M{route.get('points', '')}"
    else:
        data = route.get('d', '')
    commands = normalize_path_commands(svg_path_to_absolute(parse_svg_path(data)))
    if (
        not commands
        or commands[0].cmd != 'M'
        or any(command.cmd != 'L' for command in commands[1:])
    ):
        raise ValueError(
            'a bound route must be one open run of straight segments '
            '(M followed by L/H/V only)'
        )
    return [(command.args[0], command.args[1]) for command in commands]


def classify_route(
    points: list[tuple[float, float]],
) -> tuple[str, list[tuple[float, float]]]:
    """Return the connector preset and corner points of a slide-space route.

    One segment is ``straightConnector1``; an orthogonal route with one or two
    bends is ``bentConnector2`` / ``bentConnector3``.
    """
    corners = [points[0]]
    axes: list[str] = []
    for point in points[1:]:
        last = corners[-1]
        dx = point[0] - last[0]
        dy = point[1] - last[1]
        if math.hypot(dx, dy) <= _TOLERANCE_PX:
            continue
        if abs(dy) <= _TOLERANCE_PX:
            axis = 'h'
        elif abs(dx) <= _TOLERANCE_PX:
            axis = 'v'
        else:
            axis = 'd'
        if axes and axis == axes[-1] != 'd':
            k = 0 if axis == 'h' else 1
            if (point[k] - last[k]) * (last[k] - corners[-2][k]) < 0:
                raise ValueError('the route doubles back on itself')
            corners[-1] = point
            continue
        corners.append(point)
        axes.append(axis)

    if not axes:
        raise ValueError('the route needs two distinct points')
    if len(axes) == 1:
        return 'straightConnector1', corners
    if 'd' in axes:
        raise ValueError(
            'an elbow route may use only horizontal and vertical segments'
        )
    if len(axes) > 3:
        raise ValueError('an elbow route may bend at most twice')
    return ('bentConnector2', 'bentConnector3')[len(axes) - 2], corners


def connector_frame(
    preset: str,
    corners: list[tuple[float, float]],
) -> tuple[float, float, float, float, int, bool, bool, int | None]:
    """Map route corners to ``(x, y, w, h, rot, flipH, flipV, adj1)`` in px.

    The connector box spans start to end. A vertical first segment rotates
    the preset 90 degrees, which swaps the box's width and height.
    """
    (sx, sy), (ex, ey) = corners[0], corners[-1]
    vertical_first = (
        preset != 'straightConnector1'
        and abs(corners[1][0] - sx) <= _TOLERANCE_PX
    )
    if preset == 'bentConnector3':
        # A U-shaped elbow's ends share the first-axis coordinate; like
        # PowerPoint, give it a 1 pt run toward the bend so adj1 stays finite.
        if vertical_first and abs(ey - sy) <= _TOLERANCE_PX:
            ey = sy + math.copysign(_U_TURN_RUN_PX, corners[1][1] - sy)
        elif not vertical_first and abs(ex - sx) <= _TOLERANCE_PX:
            ex = sx + math.copysign(_U_TURN_RUN_PX, corners[1][0] - sx)
    if vertical_first:
        rotation = 5400000
        width, height = abs(ey - sy), abs(ex - sx)
        flip_h, flip_v = ey < sy, ex > sx
        start, end, bend = sy, ey, corners[1][1]
    else:
        rotation = 0
        width, height = abs(ex - sx), abs(ey - sy)
        flip_h, flip_v = ex < sx, ey < sy
        start, end, bend = sx, ex, corners[1][0]

    adj1 = None
    if preset == 'bentConnector3':
        adj1 = round((bend - start) / (end - start) * 100000)
    center_x = (sx + ex) / 2
    center_y = (sy + ey) / 2
    return (
        center_x - width / 2,
        center_y - height / 2,
        width,
        height,
        rotation,
        flip_h,
        flip_v,
        adj1,
    )


def _resolve_route(
    route: ET.Element,
    matrix: AffineMatrix,
    by_id: dict[str, list[tuple[ET.Element, AffineMatrix]]],
    viewport: tuple[float, float],
) -> ConnectorBinding:
    if _local_tag(route) not in _ROUTE_TAGS:
        raise ValueError(
            'data-pptx-start/end binds only a <line>, <polyline>, or <path> route'
        )
    if route.get('data-pptx-object') is not None or route.get('data-pptx-prst') is not None:
        raise ValueError(
            'a bound route must be plain SVG; preset_shape_svg.py connector '
            'fragments stay unbound'
        )
    points = [
        transform_point(matrix, x, y)
        for x, y in route_points(route, viewport)
    ]
    classify_route(points)
    return ConnectorBinding(
        route=route,
        start=_resolve_end(route, START_ATTR, points[0], by_id, viewport),
        end=_resolve_end(route, END_ATTR, points[-1], by_id, viewport),
    )


def _resolve_end(
    route: ET.Element,
    attr: str,
    point: tuple[float, float],
    by_id: dict[str, list[tuple[ET.Element, AffineMatrix]]],
    viewport: tuple[float, float],
) -> ConnectorEnd | None:
    target_id = route.get(attr)
    raw_site = route.get(f'{attr}-site')
    if route.get(f'{attr}-shape-id') is not None:
        raise ValueError(f'{attr} cannot be combined with imported {attr}-shape-id')
    if target_id is None:
        if raw_site is not None:
            raise ValueError(f'{attr}-site requires {attr}')
        return None
    matches = by_id.get(target_id, [])
    if not matches:
        raise ValueError(f'{attr}="{target_id}" names no shape on this page')
    if len(matches) > 1:
        raise ValueError(f'{attr}="{target_id}" matches {len(matches)} elements')
    target, matrix = matches[0]
    try:
        carrier, matrix, presets, preset, adjustments, frame = _native_target(
            target, matrix, viewport
        )
        x, y, width, height = frame
        geometry = get_preset_registry().evaluate(
            preset, width, height, adjustments=adjustments or None,
        )
    except (ValueError, KeyError) as exc:
        raise ValueError(f'{attr}="{target_id}": {exc}') from exc
    sites = [
        transform_point(matrix, x + site.position.x, y + site.position.y)
        for site in geometry.connections
    ]
    if not sites:
        raise ValueError(f'{attr}="{target_id}" ({preset}) has no connection sites')
    corners = [
        transform_point(matrix, corner_x, corner_y)
        for corner_x in (x, x + width)
        for corner_y in (y, y + height)
    ]
    xs = [corner[0] for corner in corners]
    ys = [corner[1] for corner in corners]
    gap = math.hypot(
        max(min(xs) - point[0], 0.0, point[0] - max(xs)),
        max(min(ys) - point[1], 0.0, point[1] - max(ys)),
    )
    if gap > _MAX_ENDPOINT_GAP_PX:
        raise ValueError(
            f'the route {attr[len("data-pptx-"):]} point is {gap:.0f} px from '
            f'"{target_id}"; draw it on that shape or swap start/end'
        )
    if raw_site is None:
        site = min(range(len(sites)), key=lambda index: math.dist(sites[index], point))
    else:
        try:
            site = int(raw_site)
        except ValueError:
            raise ValueError(
                f'{attr}-site must be an integer, got {raw_site!r}'
            ) from None
        if not 0 <= site < len(sites):
            raise ValueError(
                f'{attr}-site {site} is out of range; {preset} has sites '
                f'0-{len(sites) - 1}'
            )
    return ConnectorEnd(carrier=carrier, svg_id=target_id, site=site, presets=presets)


def _native_target(
    elem: ET.Element,
    matrix: AffineMatrix,
    viewport: tuple[float, float],
) -> tuple[
    ET.Element,
    AffineMatrix,
    frozenset[str],
    str,
    dict[str, str],
    tuple[float, float, float, float],
]:
    """Return carrier, matrix, export presets, preset, adjustments, frame."""
    tag = _local_tag(elem)
    carrier = elem
    if tag == 'g':
        carriers = [child for child in elem if child.get('data-pptx-part') == 'geometry']
        if elem.get('data-pptx-object') != 'shape' or len(carriers) != 1:
            raise ValueError(
                'names a group; put the id on the shape itself (rect, '
                'circle, ellipse, or preset shape fragment)'
            )
        carrier = carriers[0]
        if carrier.get('transform'):
            matrix = matrix_multiply(
                matrix, parse_transform_matrix(carrier.get('transform'))
            )
        tag = _local_tag(carrier)

    preset = carrier.get('data-pptx-prst')
    if preset is not None:
        raw_frame = carrier.get('data-pptx-frame')
        frame = _parse_frame(raw_frame) if raw_frame else _shape_frame(carrier, tag, viewport)
        adjustments = {
            name[len(_ADJUSTMENT_PREFIX):]: value
            for name, value in carrier.attrib.items()
            if name.startswith(_ADJUSTMENT_PREFIX)
        }
        return carrier, matrix, frozenset({preset}), preset, adjustments, frame

    frame = _shape_frame(carrier, tag, viewport)
    if tag == 'rect':
        rx, ry = _corner_radii(carrier, viewport)
        if (rx > 0 or ry > 0) and abs(rx - ry) >= 0.5:
            raise ValueError(
                'unequal rx/ry corners export as custom geometry without '
                'connection sites'
            )
        preset = 'roundRect' if rx > 0 else 'rect'
        return carrier, matrix, frozenset({'rect', 'roundRect'}), preset, {}, frame
    return carrier, matrix, frozenset({'ellipse'}), 'ellipse', {}, frame


def _shape_frame(
    elem: ET.Element,
    tag: str,
    viewport: tuple[float, float],
) -> tuple[float, float, float, float]:
    width, height = viewport
    size_base = min(width, height)
    if tag == 'rect':
        frame = (
            parse_svg_length(elem.get('x'), percent_base=width),
            parse_svg_length(elem.get('y'), percent_base=height),
            parse_svg_length(elem.get('width'), percent_base=width),
            parse_svg_length(elem.get('height'), percent_base=height),
        )
    elif tag == 'circle':
        radius = parse_svg_length(elem.get('r'), percent_base=size_base)
        cx = parse_svg_length(elem.get('cx'), percent_base=width)
        cy = parse_svg_length(elem.get('cy'), percent_base=height)
        frame = (cx - radius, cy - radius, radius * 2, radius * 2)
    elif tag == 'ellipse':
        rx, ry = _corner_radii(elem, viewport)
        cx = parse_svg_length(elem.get('cx'), percent_base=width)
        cy = parse_svg_length(elem.get('cy'), percent_base=height)
        frame = (cx - rx, cy - ry, rx * 2, ry * 2)
    else:
        raise ValueError(
            f'<{tag}> is not a connectable shape; name a rect, circle, '
            'ellipse, or preset shape fragment'
        )
    if frame[2] <= 0 or frame[3] <= 0:
        raise ValueError('the shape has no area to connect to')
    return frame


def _corner_radii(
    elem: ET.Element,
    viewport: tuple[float, float],
) -> tuple[float, float]:
    """Return rx/ry with SVG's rule that a missing radius copies the other."""
    width, height = viewport
    raw_rx = elem.get('rx')
    raw_ry = elem.get('ry')
    rx = parse_svg_length(raw_rx, percent_base=width) if raw_rx is not None else 0.0
    ry = parse_svg_length(raw_ry, percent_base=height) if raw_ry is not None else 0.0
    if raw_rx is not None and raw_ry is None:
        ry = rx
    elif raw_ry is not None and raw_rx is None:
        rx = ry
    return rx, ry


def _parse_frame(raw: str) -> tuple[float, float, float, float]:
    try:
        x, y, width, height = (float(part) for part in raw.replace(',', ' ').split())
    except ValueError:
        raise ValueError(f'invalid target data-pptx-frame {raw!r}') from None
    return x, y, width, height


def _rendered_elements(
    parent: ET.Element,
    matrix: AffineMatrix,
):
    """Yield rendered elements with their full SVG transform, in document order."""
    for child in parent:
        if not isinstance(child.tag, str) or _local_tag(child) in _SKIPPED_TAGS:
            continue
        child_matrix = matrix
        transform = child.get('transform')
        if transform:
            try:
                child_matrix = matrix_multiply(matrix, parse_transform_matrix(transform))
            except ValueError:
                continue  # the quality checker and exporter report bad transforms
        yield child, child_matrix
        yield from _rendered_elements(child, child_matrix)


def _viewport_size(root: ET.Element) -> tuple[float, float]:
    parts = (root.get('viewBox') or '').replace(',', ' ').split()
    if len(parts) == 4:
        try:
            width, height = float(parts[2]), float(parts[3])
        except ValueError:
            width = height = 0.0
        if width > 0 and height > 0:
            return width, height
    return (
        parse_svg_length(root.get('width'), 1280.0),
        parse_svg_length(root.get('height'), 720.0),
    )


def _local_tag(elem: ET.Element) -> str:
    return elem.tag.rsplit('}', 1)[-1]
