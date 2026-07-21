#!/usr/bin/env python3
"""
PPT Master - Run Timing Report

Reconstruct per-stage wall-clock durations for a project run from artifact
timestamps and print a stage table plus per-page SVG generation cadence.
Post-hoc and read-only: works on any project, including runs produced before
this tool existed, so it can baseline the pre-lite pipeline for A/B comparison.

Usage:
    python3 scripts/measure_run.py <project_path> [--json]

Examples:
    python3 scripts/measure_run.py projects/20260717_ppt169_hd_korea_shipbuilding
    python3 scripts/measure_run.py projects/<name> --json

Dependencies:
    None (only uses standard library)

Caveats:
    Markers are file mtimes: a later edit or re-export moves the marker, so
    durations approximate the LAST completed pass, not the first. Treat the
    report as a comparison instrument between runs, not an audit log.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from console_encoding import configure_utf8_stdio

# (marker key, human label, evidence description)
STAGE_ORDER = [
    ("project_created", "Project created", "project_meta.json birth"),
    ("sources_ready", "Sources ready", "newest file under sources/"),
    ("recommendations_written", "Confirm recommendations written", "confirm_ui/recommendations.json"),
    ("user_confirmed", "User confirmed", "confirm_ui/result.json confirmed_at"),
    ("spec_written", "Spec written", "design_spec.md / spec_lock.md"),
    ("images_done", "Images acquired", "newest file under images/"),
    ("first_page", "First SVG page", "oldest svg_output/*.svg"),
    ("last_page", "Last SVG page", "newest svg_output/*.svg"),
    ("finalize_done", "SVG finalized", "newest file under svg_final/"),
    ("export_done", "PPTX exported", "newest exports/*.pptx"),
    ("render_done", "Verify render", "newest file under _pptx_render/"),
]


def _newest_mtime(root: Path, pattern: str = "**/*") -> Optional[float]:
    """Return the newest file mtime under root matching pattern, or None."""
    times = [p.stat().st_mtime for p in root.glob(pattern) if p.is_file()]
    return max(times) if times else None


def _oldest_mtime(root: Path, pattern: str = "**/*") -> Optional[float]:
    times = [p.stat().st_mtime for p in root.glob(pattern) if p.is_file()]
    return min(times) if times else None


def _result_confirmed_at(project: Path) -> Optional[float]:
    """Prefer result.json's confirmed_at field; fall back to file mtime."""
    result_path = project / "confirm_ui" / "result.json"
    if not result_path.is_file():
        return None
    try:
        data = json.loads(result_path.read_text(encoding="utf-8"))
        stamp = data.get("confirmed_at", "")
        if stamp:
            return datetime.fromisoformat(stamp).timestamp()
    except (ValueError, OSError, json.JSONDecodeError):
        pass
    return result_path.stat().st_mtime


def collect_markers(project: Path) -> dict[str, float]:
    """Gather stage-boundary timestamps from project artifacts."""
    markers: dict[str, Optional[float]] = {}
    meta = project / "project_meta.json"
    if meta.is_file():
        stat = meta.stat()
        # On Windows st_ctime is creation time; elsewhere fall back to mtime.
        markers["project_created"] = min(stat.st_ctime, stat.st_mtime)
    markers["sources_ready"] = _newest_mtime(project / "sources") if (project / "sources").is_dir() else None
    rec = project / "confirm_ui" / "recommendations.json"
    markers["recommendations_written"] = rec.stat().st_mtime if rec.is_file() else None
    markers["user_confirmed"] = _result_confirmed_at(project)
    spec_times = [p.stat().st_mtime for p in (project / "design_spec.md", project / "spec_lock.md") if p.is_file()]
    markers["spec_written"] = max(spec_times) if spec_times else None
    markers["images_done"] = _newest_mtime(project / "images") if (project / "images").is_dir() else None
    svg_dir = project / "svg_output"
    if svg_dir.is_dir():
        markers["first_page"] = _oldest_mtime(svg_dir, "*.svg")
        markers["last_page"] = _newest_mtime(svg_dir, "*.svg")
    markers["finalize_done"] = _newest_mtime(project / "svg_final") if (project / "svg_final").is_dir() else None
    markers["export_done"] = _newest_mtime(project / "exports", "*.pptx") if (project / "exports").is_dir() else None
    markers["render_done"] = _newest_mtime(project / "_pptx_render") if (project / "_pptx_render").is_dir() else None
    return {key: ts for key, ts in markers.items() if ts is not None}


def page_cadence(project: Path) -> dict:
    """Per-page mtime sequence and interval stats for svg_output/*.svg."""
    svg_dir = project / "svg_output"
    if not svg_dir.is_dir():
        return {}
    pages = sorted(
        ((p.stat().st_mtime, p.name) for p in svg_dir.glob("*.svg")),
        key=lambda item: item[0],
    )
    intervals = [b[0] - a[0] for a, b in zip(pages, pages[1:])]
    stats = {}
    if intervals:
        stats = {
            "min_s": round(min(intervals), 1),
            "median_s": round(statistics.median(intervals), 1),
            "max_s": round(max(intervals), 1),
            "mean_s": round(statistics.mean(intervals), 1),
        }
    return {
        "pages": [{"name": name, "mtime": ts} for ts, name in pages],
        "interval_stats": stats,
    }


def _fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M:%S")


def _fmt_dur(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def print_report(project: Path, markers: dict[str, float], cadence: dict) -> None:
    print(f"Run timing report — {project}")
    print()
    present = [(key, label, desc) for key, label, desc in STAGE_ORDER if key in markers]
    if not present:
        print("No stage markers found (is this a project directory?)")
        return
    print(f"{'Stage':<34}{'At':<18}{'Δ from previous':<16}")
    prev_ts: Optional[float] = None
    for key, label, _desc in present:
        ts = markers[key]
        delta = _fmt_dur(ts - prev_ts) if prev_ts is not None and ts >= prev_ts else "-"
        print(f"{label:<34}{_fmt_ts(ts):<18}{delta:<16}")
        prev_ts = ts
    first_key = present[0][0]
    last_key = present[-1][0]
    total = markers[last_key] - markers[first_key]
    print()
    print(f"Total ({first_key} → {last_key}): {_fmt_dur(total)}")

    stats = cadence.get("interval_stats") or {}
    pages = cadence.get("pages") or []
    if pages:
        print()
        print(f"SVG page cadence — {len(pages)} pages")
        if stats:
            print(
                f"  interval min/median/mean/max: "
                f"{_fmt_dur(stats['min_s'])} / {_fmt_dur(stats['median_s'])} / "
                f"{_fmt_dur(stats['mean_s'])} / {_fmt_dur(stats['max_s'])}"
            )
        prev: Optional[float] = None
        for page in pages:
            delta = _fmt_dur(page["mtime"] - prev) if prev is not None else "-"
            print(f"  {_fmt_ts(page['mtime'])}  {delta:>8}  {page['name']}")
            prev = page["mtime"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reconstruct per-stage run timings from project artifact timestamps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project", help="path to projects/<project_name>")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of the table")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    project = Path(args.project)
    if not project.is_dir():
        print(f"Error: not a directory: {project}", file=sys.stderr)
        return 1
    markers = collect_markers(project)
    cadence = page_cadence(project)
    if args.json:
        payload = {
            "project": str(project),
            "markers": {key: {"ts": ts, "iso": datetime.fromtimestamp(ts).isoformat()} for key, ts in markers.items()},
            "cadence": cadence,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_report(project, markers, cadence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
