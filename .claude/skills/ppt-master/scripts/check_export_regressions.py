#!/usr/bin/env python3
"""
PPT Master - Native Export Regression Check

Reproduce two native-export defects that made PowerPoint desktop reject a deck
or re-wrap text, and assert the fixes still hold. Contributor diagnostic, not a
runtime gate.

    1. Partial preset adjustment list: a ``rightArrow`` with only
       ``data-pptx-av-adj1`` exported ``<a:avLst>`` with adj1 alone and
       PowerPoint refused to open the whole file. Export and
       ``preset_shape_svg.py render`` must write every handle (defaults fill
       gaps) and the quality checker must warn about the partial source.
    2. Paragraph-mode frame width: frames were sized to the bare width
       estimate and same-leading lines were joined into one run, so wide
       display fonts (Gmarket Sans digits/Latin) re-wrapped in PowerPoint.
       Visual lines must stay explicit ``<a:br/>`` breaks and the frame must
       carry width headroom (placeholder carriers use their design zone).

Usage:
    python3 scripts/check_export_regressions.py

Dependencies:
    None beyond the repository scripts (standard library only)
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from console_encoding import configure_utf8_stdio
from pptx_to_svg.preset_authoring import render_preset_shape_fragment
from svg_quality_checker import SVGQualityChecker
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from xml.etree import ElementTree as ET

EMU_PER_PX = 9525
_SVG_NS = 'http://www.w3.org/2000/svg'

_PARTIAL_ARROW_SVG = f"""<svg xmlns="{_SVG_NS}" viewBox="0 0 1280 720" width="1280" height="720">
  <path id="arrow" data-pptx-prst="rightArrow" data-pptx-av-adj1="val 50000"
        d="M800 300 L1000 300 L1000 250 L1100 350 L1000 450 L1000 400 L800 400 Z"
        fill="#C99B45"/>
</svg>
"""

# Measured Gmarket Sans TTF Bold widths at 64px: "2026 WORKSHOP 2027" is
# 832px against a 640px estimate; "2026 자체점검" is 440px against 416px.
_TITLE_SVG = f"""<svg xmlns="{_SVG_NS}" viewBox="0 0 1280 720" width="1280" height="720">
  <text id="latin" x="88" y="120" font-family="'Gmarket Sans TTF Bold', Pretendard, sans-serif"
        font-size="64" fill="#000000">2026 WORKSHOP 2027<tspan x="88" dy="82">자체점검 업무 담당자</tspan><tspan x="88" dy="82">12345678 0000</tspan></text>
  <g id="title-slot" data-pptx-placeholder="title" data-pptx-placeholder-bounds="88 400 640 252">
    <text id="title-carrier" data-pptx-placeholder-carrier="true" x="88" y="456"
          font-family="'Gmarket Sans TTF Bold', Pretendard, sans-serif"
          font-size="64" fill="#000000">2026 자체점검<tspan x="88" dy="82">업무 담당자</tspan><tspan x="88" dy="82">소통 워크숍</tspan></text>
  </g>
</svg>
"""


def _slide_xml(svg_text: str, tmp: Path, name: str) -> str:
    path = tmp / name
    path.write_text(svg_text, encoding='utf-8')
    return convert_svg_to_slide_shapes(path)[0]


def _text_shape(slide_xml: str, needle: str) -> str:
    for shape in re.findall(r'<p:sp>.*?</p:sp>', slide_xml, re.S):
        if needle in shape:
            return shape
    raise AssertionError(f'no exported shape contains {needle!r}')


def _shape_width_px(shape_xml: str) -> float:
    match = re.search(r'<a:ext cx="(\d+)"', shape_xml)
    if match is None:
        raise AssertionError('exported shape has no a:ext')
    return int(match.group(1)) / EMU_PER_PX


def check_partial_adjustments(tmp: Path) -> None:
    slide = _slide_xml(_PARTIAL_ARROW_SVG, tmp, 'arrow.svg')
    geom = re.search(r'<a:prstGeom prst="rightArrow">.*?</a:prstGeom>', slide, re.S)
    assert geom is not None, 'rightArrow preset was not exported'
    names = re.findall(r'<a:gd name="([^"]+)"', geom.group(0))
    assert names == ['adj1', 'adj2'], f'avLst must list every handle, got {names}'

    fragment = render_preset_shape_fragment(
        'rightArrow',
        (800, 300, 300, 100),
        adjustments={'adj1': 'val 50000'},
        element_id='arrow',
        style={'fill': '#C99B45'},
    )
    assert 'data-pptx-av-adj2=' in fragment, 'render must fill missing handles'

    from svg_to_pptx.drawingml.elements import find_partial_preset_adjustments

    elem = ET.fromstring(_PARTIAL_ARROW_SVG).find(f'{{{_SVG_NS}}}path')
    assert find_partial_preset_adjustments(elem) == ['adj2']

    result = SVGQualityChecker().check_file(str(tmp / 'arrow.svg'))
    assert any(
        'adjustment list' in warning for warning in result.get('warnings', [])
    ), 'quality checker must warn about a partial adjustment list'


def check_paragraph_frames(tmp: Path) -> None:
    slide = _slide_xml(_TITLE_SVG, tmp, 'title.svg')

    latin = _text_shape(slide, 'WORKSHOP')
    assert latin.count('<a:p>') == 1 and latin.count('<a:br>') == 2, (
        'same-leading visual lines must stay explicit <a:br/> breaks'
    )
    assert _shape_width_px(latin) >= 832, (
        f'Latin-heavy frame {_shape_width_px(latin):.0f}px is narrower than '
        'the measured Gmarket line (832px)'
    )

    carrier = _text_shape(slide, '소통 워크숍')
    assert carrier.count('<a:br>') == 2
    # Box starts one padding left of x=88; the placeholder zone ends at 728.
    assert _shape_width_px(carrier) >= 728 - 88, (
        f'placeholder carrier {_shape_width_px(carrier):.0f}px does not use '
        'its 640px design zone'
    )


def main() -> int:
    configure_utf8_stdio()
    checks = (
        ('partial preset adjustment list', check_partial_adjustments),
        ('paragraph-mode frame width', check_paragraph_frames),
    )
    failures = 0
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        for label, check in checks:
            try:
                check(tmp)
            except (AssertionError, ImportError) as exc:
                failures += 1
                print(f'[FAIL] {label}: {exc}')
            else:
                print(f'[OK] {label}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
