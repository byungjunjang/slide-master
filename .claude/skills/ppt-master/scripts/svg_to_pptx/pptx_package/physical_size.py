"""Rescale an exported PPTX to a fixed physical slide size.

The exporter maps 1 SVG px to 9525 EMU (96 DPI), so a 1280x840 canvas opens as
33.87 x 22.23 cm.  Some decks must open at an exact physical size instead (the
Kyobo form is 29.016 x 19.05 cm = 10445750 x 6858000 EMU).  This post-process
sets ``p:sldSz`` to that size and scales every geometry value, font size and
line width by the same ratio, so the slide looks identical at the new size.

It only acts on the canvases listed in ``PHYSICAL_SIZE_TARGETS`` and leaves
every other deck untouched.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

# (width_emu, height_emu) produced by the exporter -> exact physical size
PHYSICAL_SIZE_TARGETS: dict[tuple[int, int], tuple[int, int]] = {
    (1280 * 9525, 840 * 9525): (10445750, 6858000),  # Kyobo PPT 29.016 x 19.05 cm
}

_SCALED_PARTS = re.compile(
    r"^ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$"
)


def _scale(value: str, factor: float) -> str:
    return str(int(round(float(value) * factor)))


def _scale_xml(xml: str, fx: float, fy: float) -> str:
    # position / size pairs (a:off, a:chOff use x,y ; a:ext, a:chExt use cx,cy)
    xml = re.sub(
        r'(<a:(?:off|chOff)\b[^>]*?\bx=")(-?\d+)(")([^>]*?\by=")(-?\d+)(")',
        lambda m: f"{m[1]}{_scale(m[2], fx)}{m[3]}{m[4]}{_scale(m[5], fy)}{m[6]}",
        xml,
    )
    xml = re.sub(
        r'(<a:(?:ext|chExt)\b[^>]*?\bcx=")(\d+)(")([^>]*?\bcy=")(\d+)(")',
        lambda m: f"{m[1]}{_scale(m[2], fx)}{m[3]}{m[4]}{_scale(m[5], fy)}{m[6]}",
        xml,
    )

    def scale_attrs(tag_pattern: str, attrs: dict[str, float], text: str) -> str:
        def fix_tag(m: re.Match) -> str:
            tag = m.group(0)
            for name, factor in attrs.items():
                tag = re.sub(
                    rf'(\b{name}=")(-?\d+)(")',
                    lambda a: f"{a[1]}{_scale(a[2], factor)}{a[3]}",
                    tag,
                )
            return tag

        return re.sub(tag_pattern, fix_tag, text)

    # font size (hundredths of a point) and character spacing
    xml = scale_attrs(r"<a:(?:rPr|defRPr|endParaRPr)\b[^>]*>", {"sz": fx, "spc": fx}, xml)
    # line widths (EMU)
    xml = scale_attrs(r"<a:ln\b[^>]*>", {"w": fx}, xml)
    # text-frame insets (EMU)
    xml = scale_attrs(
        r"<a:bodyPr\b[^>]*>", {"lIns": fx, "rIns": fx, "tIns": fy, "bIns": fy}, xml
    )
    # paragraph spacing in points (hundredths)
    xml = re.sub(
        r'(<a:spcPts\b[^>]*?\bval=")(\d+)(")',
        lambda m: f"{m[1]}{_scale(m[2], fx)}{m[3]}",
        xml,
    )
    # shadow / glow distances (EMU)
    xml = scale_attrs(
        r"<a:(?:outerShdw|innerShdw|glow|softEdge)\b[^>]*>",
        {"blurRad": fx, "dist": fx, "rad": fx},
        xml,
    )
    return xml


def _patch_presentation(xml: str, target: tuple[int, int], fx: float) -> str:
    xml = re.sub(
        r"<p:sldSz\b[^>]*/>",
        f'<p:sldSz cx="{target[0]}" cy="{target[1]}"/>',
        xml,
        count=1,
    )
    # default text style font sizes follow the same ratio
    xml = re.sub(
        r"<a:(?:defRPr|rPr)\b[^>]*>",
        lambda m: re.sub(
            r'(\bsz=")(\d+)(")', lambda a: f"{a[1]}{_scale(a[2], fx)}{a[3]}", m.group(0)
        ),
        xml,
    )
    return xml


def rescale_to_physical_size(pptx_path: Path, width_emu: int, height_emu: int) -> bool:
    """Rescale ``pptx_path`` in place when its canvas has a fixed physical size.

    Returns True when the package was rescaled.
    """
    target = PHYSICAL_SIZE_TARGETS.get((int(width_emu), int(height_emu)))
    if target is None:
        return False
    fx = target[0] / width_emu
    fy = target[1] / height_emu
    pptx_path = Path(pptx_path)
    tmp_path = pptx_path.with_suffix(".rescaled.tmp")
    with zipfile.ZipFile(pptx_path) as zin, zipfile.ZipFile(
        tmp_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "ppt/presentation.xml":
                data = _patch_presentation(data.decode("utf-8"), target, fx).encode("utf-8")
            elif _SCALED_PARTS.match(item.filename):
                data = _scale_xml(data.decode("utf-8"), fx, fy).encode("utf-8")
            zout.writestr(item, data)
    tmp_path.replace(pptx_path)
    return True
