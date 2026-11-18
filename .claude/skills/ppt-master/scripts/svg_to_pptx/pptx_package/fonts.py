"""Installed TrueType faces of the deck font, wrapped as EOT for PPTX embedding.

PowerPoint stores embedded fonts as EOT parts (`ppt/fonts/fontN.fntdata`).
Only TrueType outlines can go in: the bundled `assets/fonts/` OTF (CFF) files
cannot, so the faces come from the TTF files installed on this machine.
"""

from __future__ import annotations

import os
import re
import struct
import sys
from pathlib import Path

# ponytail: the Font Policy family only; widen when another family must travel.
EMBED_FAMILY_PREFIX = 'Pretendard'
FONT_REL_TYPE = (
    'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'
)
FONT_CONTENT_TYPE = 'application/x-fontdata'

_EOT_VERSION = 0x00020001
_EOT_MAGIC = 0x504C
_NO_EMBED_BITS = 0x0202  # fsType: restricted license (0x0002), bitmap only (0x0200)
_TRUETYPE_TAGS = (b'\x00\x01\x00\x00', b'true')
_TYPEFACE_RE = re.compile(r'<a:(?:latin|ea|cs)\b[^>]*?\btypeface="([^"+][^"]*)"')
_BOLD_RE = re.compile(r'<a:(?:rPr|defRPr|endParaRPr)\b[^>]*?\bb="(?:1|true)"')


def _font_dirs() -> list[Path]:
    home = Path.home()
    if sys.platform == 'win32':
        local = Path(os.environ.get('LOCALAPPDATA', home / 'AppData' / 'Local'))
        dirs = [local / 'Microsoft' / 'Windows' / 'Fonts',
                Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts']
    elif sys.platform == 'darwin':
        dirs = [home / 'Library' / 'Fonts', Path('/Library/Fonts')]
    else:
        dirs = [home / '.local' / 'share' / 'fonts', home / '.fonts',
                Path('/usr/local/share/fonts'), Path('/usr/share/fonts')]
    return [d for d in dirs if d.is_dir()]


def _tables(data: bytes) -> dict[bytes, int]:
    """sfnt table tag -> offset."""
    count = struct.unpack_from('>H', data, 4)[0]
    return {
        data[12 + 16 * i:16 + 16 * i]: struct.unpack_from('>I', data, 20 + 16 * i)[0]
        for i in range(count)
    }


def _names(data: bytes, name_offset: int) -> dict[int, str]:
    """Windows-platform name records (English preferred), nameID -> text."""
    count, string_offset = struct.unpack_from('>HH', data, name_offset + 2)
    names: dict[int, str] = {}
    for i in range(count):
        platform, encoding, language, name_id, length, offset = struct.unpack_from(
            '>6H', data, name_offset + 6 + 12 * i)
        if platform == 3 and encoding in (0, 1) and (
                name_id not in names or language == 0x0409):
            start = name_offset + string_offset + offset
            names[name_id] = data[start:start + length].decode('utf-16-be', 'replace')
    return names


def find_faces(prefix: str = EMBED_FAMILY_PREFIX) -> dict[tuple[str, str], Path]:
    """(family, subfamily) -> installed TrueType file, e.g. ('Pretendard', 'Bold').

    Family and subfamily are name IDs 1 and 2 — the names PowerPoint uses, so
    'Pretendard SemiBold' is its own family with a 'Regular' face. The user
    font folder wins over the system folder.
    """
    faces: dict[tuple[str, str], Path] = {}
    for font_dir in _font_dirs():
        for path in sorted(font_dir.rglob(f'{prefix}*.ttf')):
            try:
                data = path.read_bytes()
                if data[:4] not in _TRUETYPE_TAGS:
                    continue
                names = _names(data, _tables(data)[b'name'])
            except (OSError, KeyError, struct.error):
                continue
            faces.setdefault((names.get(1, ''), names.get(2, '')), path)
    return faces


def used_typefaces(ppt_dir: Path) -> tuple[set[str], bool]:
    """Typefaces named in the package parts (theme fonts included), and
    whether any run is bold."""
    typefaces: set[str] = set()
    bold = False
    for part in ppt_dir.rglob('*.xml'):
        xml = part.read_text(encoding='utf-8')
        typefaces.update(_TYPEFACE_RE.findall(xml))
        bold = bold or bool(_BOLD_RE.search(xml))
    return typefaces, bold


def select_faces(ppt_dir: Path) -> tuple[list[tuple[str, dict[str, Path]]], list[str]]:
    """Faces to embed: [(typeface, {'regular'|'bold': ttf})], plus warnings.

    Each used typeface of the deck font family gets its Regular face, and its
    Bold face when the deck has any bold run.
    """
    typefaces, bold = used_typefaces(ppt_dir)
    wanted = sorted(t for t in typefaces if t.startswith(EMBED_FAMILY_PREFIX))
    if not wanted:
        return [], []
    faces = find_faces()
    picks: list[tuple[str, dict[str, Path]]] = []
    warnings: list[str] = []
    for typeface in wanted:
        styles = {'regular': faces.get((typeface, 'Regular'))}
        if bold:
            styles['bold'] = faces.get((typeface, 'Bold'))
        found = {style: path for style, path in styles.items() if path}
        if found:
            picks.append((typeface, found))
        else:
            warnings.append(
                f"font '{typeface}' not embedded: no installed TrueType (.ttf) "
                "file — the recipient needs the font installed")
    return picks, warnings


def ttf_to_eot(data: bytes) -> bytes:
    """Wrap a TrueType file in an uncompressed EOT, version 0x00020001."""
    try:
        tables = _tables(data)
        os2 = tables[b'OS/2']
        os2_version, _, weight, _, fs_type = struct.unpack_from('>HhHHH', data, os2)
        panose = data[os2 + 32:os2 + 42]
        unicode_ranges = struct.unpack_from('>4I', data, os2 + 42)
        fs_selection = struct.unpack_from('>H', data, os2 + 62)[0]
        code_pages = (struct.unpack_from('>2I', data, os2 + 78)
                      if os2_version >= 1 else (0, 0))
        checksum_adjustment = struct.unpack_from('>I', data, tables[b'head'] + 8)[0]
        names = _names(data, tables[b'name'])
    except (KeyError, struct.error) as exc:
        raise ValueError(f'unreadable TrueType file ({exc!r})') from exc
    if fs_type & _NO_EMBED_BITS:
        raise ValueError(f'the font license forbids embedding (fsType {fs_type:#06x})')

    eot = bytearray(struct.pack('<4I', 0, len(data), _EOT_VERSION, 0))  # size set below
    eot += panose
    eot += struct.pack(
        '<2BI2H4I2I5I',
        1,                  # Charset: DEFAULT_CHARSET
        fs_selection & 1,   # Italic
        weight, fs_type, _EOT_MAGIC,
        *unicode_ranges, *code_pages,
        checksum_adjustment, 0, 0, 0, 0,  # + Reserved1-4
    )
    for name_id in (1, 2, 5, 4):  # family, style, version, full name
        raw = names.get(name_id, '').encode('utf-16-le')
        eot += struct.pack('<2H', 0, len(raw)) + raw  # padding, size, string
    eot += struct.pack('<2H', 0, 0)  # padding, empty RootString
    eot += data
    struct.pack_into('<I', eot, 0, len(eot))
    return bytes(eot)
