#!/usr/bin/env python3
"""
PPT Master - Final Deck Verification Gate

One-command verification for a finished deck, run after SKILL.md Step 7.
Catches the failure modes that otherwise surface only when the user opens the
exported PPTX: stale finalize/export, corrupt or image-only slides, page-count
drift, off-spec planning artifacts, placeholder images.

Checks (FAIL → non-zero exit):
    - svg_output/ non-empty; every page matches the project canvas viewBox
    - svg_final/ page parity with svg_output/ and not stale (finalize re-run
      needed after SVG edits)
    - a native PPTX exists in exports/, is a valid zip, has one slide per SVG
      page, every slide carries editable DrawingML, and is not stale
    - validate_spec.py passes on design_spec.md + spec_lock.md
    - svg_quality_checker.py reports 0 errors on svg_output/
    - officecli (optional, auto-skip when absent): OpenXML validation of the
      newest native PPTX — unopenable file fails; schema warnings warn

Warnings (reported, non-blocking):
    - placeholder/degenerate suspects in images/ (tiny or near-uniform;
      alpha images are skipped — sliced spot illustrations are legitimate)
    - notes/*.md count differs from the SVG page count (when notes exist)
    - officecli contact-sheet render of the exported PPTX to
      _pptx_render/<stem>-grid.png — on success, Read that PNG to eyeball
      overflow / collisions in the converted deck

Usage:
    python3 scripts/verify_deck.py <project_path> [--strict] [--no-render]

Examples:
    python3 scripts/verify_deck.py projects/20260714_ai_agent_adoption
    python3 scripts/verify_deck.py projects/<name> --no-render   # skip only the contact-sheet render

Environment:
    OFFICECLI_BIN — path forces that binary; empty string disables the
    officecli layer entirely.

Dependencies:
    None required (standard library; Pillow+numpy improve the image check,
    officecli adds the OpenXML/render layer)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from project_utils import CANVAS_FORMATS  # noqa: E402

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
NATIVE_SHAPE_TAGS = ("sp", "grpSp", "cxnSp", "graphicFrame")
PLACEHOLDER_MIN_BYTES = 4_000
PLACEHOLDER_MIN_STD = 4.0


def _svgs(d: Path) -> list[Path]:
    return sorted(d.glob("*.svg")) if d.is_dir() else []


def _newest_mtime(paths: list[Path]) -> float:
    return max((p.stat().st_mtime for p in paths), default=0.0)


def _native_pptx_files(project: Path) -> list[Path]:
    exports = project / "exports"
    if not exports.is_dir():
        return []
    return sorted(p for p in exports.glob("*.pptx") if not p.stem.endswith("_svg"))


def _tag_count(xml: str, local_name: str) -> int:
    return len(re.findall(rf"<(?:\w+:)?{re.escape(local_name)}\b", xml))


def expected_viewbox(project: Path) -> Optional[str]:
    meta_path = project / "project_meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    fmt = CANVAS_FORMATS.get(meta.get("canvas_format", ""))
    return fmt["viewbox"] if fmt else None


def svg_canvas_ok(svg_text: str, viewbox: str) -> bool:
    pattern = r'viewBox="' + r"\s+".join(re.escape(t) for t in viewbox.split()) + r'"'
    return bool(re.search(pattern, svg_text))


def validate_native_pptx(path: Path, expected_slides: int) -> list[str]:
    """Zip integrity + slide count + editable DrawingML per slide."""
    failures: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            bad_member = zf.testzip()
            if bad_member:
                return [f"corrupt zip member: {bad_member}"]
            slide_names = sorted(
                n for n in zf.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
            )
            if not slide_names:
                return ["no ppt/slides/slide*.xml entries"]
            if expected_slides and len(slide_names) != expected_slides:
                failures.append(f"slide count {len(slide_names)} != "
                                f"{expected_slides} svg_output pages")
            flattened: list[str] = []
            for name in slide_names:
                xml = zf.read(name).decode("utf-8", errors="replace")
                native_count = sum(_tag_count(xml, tag) for tag in NATIVE_SHAPE_TAGS)
                if native_count == 0:
                    pic_count = _tag_count(xml, "pic")
                    suffix = " (image-only)" if pic_count else ""
                    flattened.append(f"{Path(name).name}{suffix}")
            if flattened:
                failures.append("slides lack editable DrawingML: "
                                + ", ".join(flattened))
    except zipfile.BadZipFile:
        failures.append("not a valid PPTX zip")
    except OSError as e:
        failures.append(f"unreadable PPTX: {e}")
    return failures


def image_is_placeholder(path: Path) -> bool:
    """Tiny OR near-uniform opaque image ⇒ placeholder suspect.

    Alpha-channel images are skipped: trimmed spot-illustration cutouts are
    legitimately small and low-variance. Without Pillow/numpy only the size
    heuristic runs.
    """
    try:
        if path.stat().st_size < PLACEHOLDER_MIN_BYTES:
            return True
    except OSError:
        return True
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return False
    try:
        with Image.open(path) as im:
            if im.mode in {"RGBA", "LA", "PA"} or \
                    (im.mode == "P" and "transparency" in im.info):
                return False
            arr = np.asarray(im.convert("RGB"), dtype="float32")
        return float(arr.std()) < PLACEHOLDER_MIN_STD
    except Exception:
        return True


def _run_script(script: str, args: list[str]) -> int:
    """Run a sibling gate script quietly; replay its output only on failure."""
    path = _SCRIPTS_DIR / script
    if not path.exists():
        return 0
    proc = subprocess.run([sys.executable, str(path), *args],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-30:])
        print(f"--- {script} output (rc={proc.returncode}) ---\n{tail}\n---",
              file=sys.stderr)
    return proc.returncode


def _officecli_bin() -> Optional[str]:
    env = os.environ.get("OFFICECLI_BIN")
    if env is not None:
        return env or None
    return shutil.which("officecli")


def _run_officecli(args: list[str], timeout: int) -> Optional[subprocess.CompletedProcess]:
    try:
        return subprocess.run(args, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None


def officecli_checks(project: Path, render: bool = True) -> tuple[list[str], list[str]]:
    """OpenXML validation + converted-PPTX contact sheet. Measurement-only:
    skipped entirely when officecli is absent. render=False keeps the
    validation and skips only the contact-sheet screenshot."""
    binary = _officecli_bin()
    if binary is None:
        return [], []
    natives = _native_pptx_files(project)
    if not natives:
        return [], []
    pptx = max(natives, key=lambda p: p.stat().st_mtime)
    failures: list[str] = []
    warnings: list[str] = []

    rc = _run_officecli([binary, "validate", str(pptx), "--json"], timeout=120)
    verdict = None
    if rc is not None:
        try:
            verdict = json.loads(rc.stdout)
        except (json.JSONDecodeError, TypeError):
            verdict = None
    if verdict is None:
        warnings.append("officecli validate produced no parseable verdict "
                        "(timeout or bad output) — non-blocking")
    elif verdict.get("error"):
        failures.append(f"officecli validate: {pptx.name} unopenable — "
                        f"{verdict['error']}")
    elif not verdict.get("success"):
        warns = verdict.get("warnings") or []
        head = warns[0].get("message", "") if warns else ""
        warnings.append(f"officecli validate schema warnings on {pptx.name} "
                        f"({len(warns)} line(s), non-blocking): {head[:200]}")

    if not render:
        return failures, warnings

    if not failures:
        out = project / "_pptx_render" / f"{pptx.stem}-grid.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        rs = _run_officecli([binary, "view", str(pptx), "screenshot",
                             "--grid", "auto", "--out", str(out), "--json"],
                            timeout=180)
        if rs is not None and rs.returncode == 0 and out.exists():
            print(f"[verify_deck] pptx render: {out} — Read it to eyeball "
                  f"overflow/collision issues in the exported deck")
        else:
            detail = "" if rs is None else (rs.stderr or rs.stdout or "")[-300:]
            warnings.append(f"officecli screenshot failed (non-blocking): {detail}")
    return failures, warnings


def run_checks(project: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    out_dir, fin_dir = project / "svg_output", project / "svg_final"
    pages = _svgs(out_dir)

    # 1. author source present
    if not pages:
        return ["svg_output/ has no SVG pages — Executor stage did not run"], []

    # 2. canvas lock
    viewbox = expected_viewbox(project)
    if viewbox is None:
        warnings.append("project_meta.json missing/unknown canvas_format — "
                        "canvas check skipped")
    else:
        bad = [p.name for p in pages
               if not svg_canvas_ok(p.read_text(encoding="utf-8",
                                                errors="replace"), viewbox)]
        if bad:
            failures.append(f"pages not on canvas viewBox \"{viewbox}\": "
                            + ", ".join(bad))

    # 3. stage parity + freshness
    fin_pages = _svgs(fin_dir)
    if len(fin_pages) != len(pages):
        failures.append(f"svg_final/ ({len(fin_pages)}) != svg_output/ "
                        f"({len(pages)}) — re-run finalize_svg.py")
    elif _newest_mtime(fin_pages) < _newest_mtime(pages):
        failures.append("svg_final/ is older than svg_output/ — SVGs were "
                        "edited after finalize; re-run finalize_svg.py")

    # 4. native pptx presence + integrity + freshness
    natives = _native_pptx_files(project)
    if not natives:
        failures.append("no native .pptx in exports/ — run svg_to_pptx.py")
    else:
        newest = max(natives, key=lambda p: p.stat().st_mtime)
        errs = validate_native_pptx(newest, len(pages))
        if errs:
            failures.append(f"exports/{newest.name}: " + "; ".join(errs))
        if newest.stat().st_mtime < _newest_mtime(pages):
            failures.append(f"exports/{newest.name} is older than svg_output/ "
                            f"— re-run finalize_svg.py + svg_to_pptx.py")

    # 5. planning artifacts
    if (project / "design_spec.md").exists() and (project / "spec_lock.md").exists():
        if _run_script("validate_spec.py", [str(project)]) != 0:
            failures.append("validate_spec.py reported errors on "
                            "design_spec.md / spec_lock.md")
    else:
        warnings.append("design_spec.md / spec_lock.md missing — plan "
                        "validation skipped")

    # 6. SVG quality (svg_output is the checked source; finalize masks violations)
    if _run_script("svg_quality_checker.py", [str(project)]) != 0:
        failures.append("svg_quality_checker.py reported errors on svg_output/")

    # 7. notes mapping (opt-in artifact; only checked when present)
    notes = [p for p in (project / "notes").glob("*.md")
             if p.name != "total.md"] if (project / "notes").is_dir() else []
    if notes and len(notes) != len(pages):
        warnings.append(f"notes/ has {len(notes)} page files for {len(pages)} "
                        f"SVG pages — re-run total_md_split.py if notes are stale")

    # 8. image placeholder suspects
    imgs_dir = project / "images"
    suspects = [p.name for p in (sorted(imgs_dir.iterdir())
                                 if imgs_dir.is_dir() else [])
                if p.suffix.lower() in IMAGE_SUFFIXES and image_is_placeholder(p)]
    if suspects:
        warnings.append("placeholder/degenerate image suspects: "
                        + ", ".join(suspects))

    return failures, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Final verification gate for a finished deck.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project", help="path to projects/<project_name>")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures")
    parser.add_argument("--no-render", action="store_true",
                        help="skip only the OfficeCLI contact-sheet render; "
                             "OpenXML validation and all other checks stay on")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"[verify_deck] not a directory: {project}", file=sys.stderr)
        return 2

    failures, warnings = run_checks(project)
    cli_failures, cli_warnings = officecli_checks(project, render=not args.no_render)
    failures += cli_failures
    warnings += cli_warnings

    for w in warnings:
        print(f"  ! WARN {w}", file=sys.stderr)
    if args.strict:
        failures += warnings
    if failures:
        print(f"[verify_deck] FAIL ({len(failures)} issue(s)):", file=sys.stderr)
        for f in failures:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1
    print(f"[verify_deck] PASS — {project.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
