#!/usr/bin/env python3
"""
PPT Master - Environment Preflight

Pre-pipeline environment gate. Run once after project init (SKILL.md Step 2)
so a long deck run never dies mid-pipeline on a missing dependency. Fails
loudly on toolchain gaps that would break Step 6/7 and on stale Codex stubs
(.codex/skills drift — dual-host contract); warns on gaps that only degrade
optional surfaces (Confirm UI page, image API path, OfficeCLI render).

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
from sync_codex_stubs import SYNC_CMD, stale_stub_paths  # noqa: E402

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
# Per-directory guard against a pathological scan. Hitting it means "unknown",
# never "not installed" — see font_installed().
FONT_SCAN_CAP = 20000
FONT_SUFFIXES = {".ttf", ".otf", ".ttc"}


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
    """Font directories, user-level first — that is where an install-local
    family like Pretendard lands, so we find it before scanning the much
    larger system directory."""
    home = Path.home()
    if sys.platform == "win32":
        dirs = [
            home / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
            Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
        ]
    elif sys.platform == "darwin":
        dirs = [home / "Library" / "Fonts", Path("/Library/Fonts"),
                Path("/System/Library/Fonts")]
    else:
        dirs = [home / ".local" / "share" / "fonts", home / ".fonts",
                Path("/usr/share/fonts"), Path("/usr/local/share/fonts")]
    return [d for d in dirs if d.is_dir()]


def font_installed(family: str = FONT_FAMILY) -> Optional[bool]:
    """Whether the family is installed. ``None`` means undetermined — a
    directory exceeded the scan cap, so absence was never established."""
    needle = family.lower().replace(" ", "")
    truncated = False
    for d in _font_dirs():
        for i, p in enumerate(d.rglob("*")):
            if i >= FONT_SCAN_CAP:
                truncated = True
                break
            if p.suffix.lower() in FONT_SUFFIXES and \
                    needle in p.stem.lower().replace(" ", "").replace("-", ""):
                return True
    return None if truncated else False


def check_fonts() -> list[str]:
    state = font_installed()
    if state is True:
        return []
    if state is None:
        return [
            f"could not determine whether '{FONT_FAMILY}' is installed — a font "
            f"directory exceeded {FONT_SCAN_CAP} entries; verify manually if the "
            f"deck renders with fallback fonts"
        ]
    return [
        f"'{FONT_FAMILY}' font not found in system/user font directories — "
        f"decks render with fallback fonts in preview and export. Install from "
        f".claude/skills/ppt-master/assets/fonts/Pretendard/ (see CLAUDE.md font policy)"
    ]


def check_image_backend() -> list[str]:
    if shutil.which("codex"):
        return []
    if os.environ.get("IMAGE_BACKEND", "").strip():
        return []
    return [
        "Codex CLI not found and IMAGE_BACKEND not set — image_gen.py Path A "
        "(codex backend, ChatGPT OAuth) would fail at Step 5. Install: "
        "npm install -g @openai/codex, then codex login. Remaining fallbacks: "
        "Path B API backend (IMAGE_BACKEND + provider key in .env), web "
        "sourcing, or user-supplied images (user-drop)"
    ]


def check_codex_stubs() -> list[str]:
    """Dual-host drift gate: .codex/skills stubs must match a fresh build from
    the canonical .claude/skills tree (see AGENTS.md / CLAUDE.md cross-harness
    note). Stale stubs mean Codex triggers on outdated skill frontmatter."""
    stale = stale_stub_paths()
    if not stale:
        return []
    sample = ", ".join(stale[:3]) + (", ..." if len(stale) > 3 else "")
    return [
        f".codex/skills Codex stubs are stale ({len(stale)} file(s): {sample}) "
        f"— regenerate: {SYNC_CMD}"
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

    failures = check_core_deps() + check_codex_stubs()
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
