#!/usr/bin/env python3
"""
PPT Master - Environment Preflight

Pre-pipeline environment gate. Run once after project init (SKILL.md Step 2)
so a long deck run never dies mid-pipeline on a missing dependency. Fails
loudly on toolchain gaps that would break Step 6/7; warns on gaps that only
degrade optional surfaces (Confirm UI page, image API path, OfficeCLI render).

Usage:
    python3 scripts/preflight.py [options]

Examples:
    python3 scripts/preflight.py
    python3 scripts/preflight.py --needs-images
    python3 scripts/preflight.py --strict

Dependencies:
    None (only uses standard library; probes third-party deps by import)
"""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

# (module, pip name, why it is required)
CORE_MODULES = (
    ("pptx", "python-pptx", "svg_to_pptx.py export (Step 7.3)"),
    ("PIL", "Pillow", "analyze_images.py / finalize_svg.py image handling"),
)
# (module, pip name, degraded surface when missing)
OPTIONAL_MODULES = (
    ("flask", "flask", "Confirm UI page + live preview fall back to chat-only"),
    ("numpy", "numpy", "image placeholder detection and watermark tooling degrade"),
    ("requests", "requests", "web image search / web_to_md unavailable"),
)
FONT_FAMILY = "Pretendard"
FONT_SCAN_CAP = 5000


def _module_missing(module: str) -> bool:
    try:
        importlib.import_module(module)
        return False
    except ImportError:
        return True


def check_core_deps() -> list[str]:
    fails = []
    for module, pip_name, why in CORE_MODULES:
        if _module_missing(module):
            fails.append(
                f"missing Python dep '{pip_name}' (needed for {why}) — "
                f"pip install {pip_name}"
            )
    return fails


def check_optional_deps() -> list[str]:
    warns = []
    for module, pip_name, surface in OPTIONAL_MODULES:
        if _module_missing(module):
            warns.append(
                f"missing Python dep '{pip_name}' — {surface}; pip install {pip_name}"
            )
    return warns


def _font_dirs() -> list[Path]:
    home = Path.home()
    if sys.platform == "win32":
        dirs = [
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
            home / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
        ]
    elif sys.platform == "darwin":
        dirs = [home / "Library" / "Fonts", Path("/Library/Fonts"),
                Path("/System/Library/Fonts")]
    else:
        dirs = [home / ".local" / "share" / "fonts", home / ".fonts",
                Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]
    return [d for d in dirs if d.is_dir()]


def font_installed(family: str = FONT_FAMILY) -> bool:
    needle = family.lower().replace(" ", "")
    scanned = 0
    for d in _font_dirs():
        for p in d.rglob("*"):
            scanned += 1
            if scanned > FONT_SCAN_CAP:
                return False
            if p.suffix.lower() in {".ttf", ".otf", ".ttc"} and \
                    needle in p.stem.lower().replace(" ", "").replace("-", ""):
                return True
    return False


def check_fonts() -> list[str]:
    if font_installed():
        return []
    return [
        f"'{FONT_FAMILY}' font not found in system/user font directories — "
        f"decks render with fallback fonts in preview and export. Install from "
        f".claude/skills/ppt-master/assets/fonts/Pretendard/ (see CLAUDE.md font policy)"
    ]


def check_image_backend() -> list[str]:
    if os.environ.get("IMAGE_BACKEND", "").strip():
        return []
    return [
        "IMAGE_BACKEND not set in the current environment (a .env may still "
        "provide it at run time) — image_gen.py Path A (api) would be "
        "unavailable; host-native Path B and manual mode still work"
    ]


def check_officecli() -> list[str]:
    if shutil.which("officecli"):
        return []
    return [
        "officecli not on PATH — verify_deck.py skips OpenXML validation and "
        "the exported-PPTX contact sheet (optional layer; npm install -g officecli)"
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pre-pipeline environment gate for PPT Master.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--needs-images", action="store_true",
                        help="also check AI image generation (Path A) readiness")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    failures = check_core_deps()
    warnings = check_optional_deps() + check_fonts() + check_officecli()
    if args.needs_images:
        warnings += check_image_backend()

    for w in warnings:
        print(f"  ! WARN {w}", file=sys.stderr)
    if args.strict:
        failures += warnings
        warnings = []

    if failures:
        print(f"[preflight] FAIL ({len(failures)} issue(s)):", file=sys.stderr)
        for f in failures:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1
    suffix = f" ({len(warnings)} warning(s))" if warnings else ""
    print(f"[preflight] PASS — environment ready{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
