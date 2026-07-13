#!/usr/bin/env python3
"""Regenerate example specs + rendered SVGs for every chart type.

slide-master variant — styles come from the bundled sample project's
spec_lock.md (examples/sample_project/). Pass a real deck project path to
preview the whole catalog in that deck's locked palette:
  python3 .claude/skills/chart-design/scripts/build_examples.py [project_path]

Writes examples/specs/<type>.json (only if missing — specs are documentation,
hand-edits survive) and always re-renders examples/<type>.svg from each spec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from chartlib.renderers import plot_marker, render
from chartlib.svgutil import wrap_fragment, wrap_standalone
from chartlib.tokens import resolve_style

EXAMPLES = _HERE.parent / "examples"
SAMPLE_PROJECT = EXAMPLES / "sample_project"

SPECS: dict[str, dict] = {
    "bar": {
        "type": "bar", "unit": "억", "width": 720, "height": 420,
        "data": [{"label": "서울", "value": 124}, {"label": "부산", "value": 87},
                 {"label": "대구", "value": 62}, {"label": "인천", "value": 95},
                 {"label": "광주", "value": 41}],
        "options": {"focus": "서울"},
    },
    "horizontal_bar": {
        "type": "horizontal_bar", "unit": "점", "width": 720, "height": 420,
        "data": [{"label": "고객 만족도 개선", "value": 88},
                 {"label": "신규 기능 출시 속도", "value": 76},
                 {"label": "운영 비용 절감", "value": 69},
                 {"label": "브랜드 인지도 상승", "value": 64},
                 {"label": "내부 협업 효율", "value": 57},
                 {"label": "파트너 생태계 확장", "value": 45}],
        "options": {"focus": 0},
    },
    "grouped_bar": {
        "type": "grouped_bar", "unit": "억", "width": 720, "height": 420,
        "data": {"categories": ["1분기", "2분기", "3분기", "4분기"],
                 "series": [{"name": "국내", "values": [42, 48, 55, 61]},
                            {"name": "해외", "values": [18, 24, 31, 44]}]},
    },
    "stacked_bar": {
        "type": "stacked_bar", "unit": "억", "width": 720, "height": 420,
        "data": {"categories": ["2023", "2024", "2025", "2026"],
                 "series": [{"name": "구독", "values": [30, 42, 58, 74]},
                            {"name": "광고", "values": [22, 25, 27, 30]},
                            {"name": "기타", "values": [8, 9, 11, 12]}]},
    },
    "stacked_bar_100": {
        "type": "stacked_bar_100", "width": 720, "height": 420,
        "data": {"categories": ["20대", "30대", "40대", "50대"],
                 "series": [{"name": "모바일", "values": [82, 74, 61, 45]},
                            {"name": "PC", "values": [14, 21, 30, 38]},
                            {"name": "태블릿", "values": [4, 5, 9, 17]}]},
    },
    "line": {
        "type": "line", "unit": "만", "width": 720, "height": 420,
        "data": {"categories": ["1월", "2월", "3월", "4월", "5월", "6월",
                                "7월", "8월", "9월", "10월", "11월", "12월"],
                 "series": [{"name": "MAU",
                             "values": [102, 108, 115, 121, 128, 137, 145,
                                        151, 160, 172, 181, 194]}]},
    },
    "multi_line": {
        "type": "multi_line", "unit": "%", "width": 720, "height": 420,
        "data": {"categories": ["1월", "2월", "3월", "4월", "5월", "6월"],
                 "series": [{"name": "리텐션", "values": [42, 44, 47, 51, 55, 58]},
                            {"name": "전환율", "values": [12, 13, 15, 14, 17, 19]}]},
    },
    "area": {
        "type": "area", "unit": "TB", "width": 720, "height": 420,
        "data": {"categories": ["2021", "2022", "2023", "2024", "2025", "2026"],
                 "series": [{"name": "누적 데이터", "values": [12, 25, 44, 78, 130, 210]}]},
    },
    "scatter": {
        "type": "scatter", "width": 720, "height": 420,
        "data": [{"x": 3.2, "y": 68, "label": "A제품"}, {"x": 5.5, "y": 74},
                 {"x": 7.1, "y": 82, "label": "B제품"}, {"x": 4.8, "y": 71},
                 {"x": 9.4, "y": 91, "label": "C제품"}, {"x": 6.3, "y": 77},
                 {"x": 8.2, "y": 85}, {"x": 2.4, "y": 62}, {"x": 5.9, "y": 79}],
        "options": {"x_label": "마케팅 투자(억)", "y_label": "만족도(점)"},
    },
    "combo": {
        "type": "combo", "unit": "억", "width": 720, "height": 420,
        "data": {"categories": ["2022", "2023", "2024", "2025", "2026"],
                 "bars": {"name": "매출", "values": [120, 145, 168, 190, 224]},
                 "line": {"name": "영업이익률", "values": [8.2, 9.1, 10.4, 11.8, 13.5]}},
        "options": {"line_unit": "%"},
    },
    "waterfall": {
        "type": "waterfall", "unit": "억", "width": 720, "height": 420,
        "data": [{"label": "기초 이익", "value": 120},
                 {"label": "매출 증가", "value": 45},
                 {"label": "원가 상승", "value": -28},
                 {"label": "환율 효과", "value": -12},
                 {"label": "비용 절감", "value": 18},
                 {"label": "기말 이익", "total": True}],
    },
    "bullet": {
        "type": "bullet", "unit": "억", "width": 720, "height": 300,
        "data": [{"label": "매출", "value": 92, "target": 100, "max": 120},
                 {"label": "신규 고객", "value": 78, "target": 70, "max": 100},
                 {"label": "NPS", "value": 54, "target": 60, "max": 100}],
    },
    "pie": {
        "type": "pie", "width": 560, "height": 420,
        "data": [{"label": "네이버", "value": 42}, {"label": "구글", "value": 31},
                 {"label": "다음", "value": 14}, {"label": "기타", "value": 13}],
    },
    "donut": {
        "type": "donut", "width": 560, "height": 420,
        "data": [{"label": "구독", "value": 58}, {"label": "광고", "value": 27},
                 {"label": "커머스", "value": 15}],
        "options": {"center_label": "1,240억"},
    },
    "gauge": {
        "type": "gauge", "unit": "%", "width": 480, "height": 300,
        "data": {"value": 73, "max": 100, "label": "연간 목표 달성률"},
    },
    "radar": {
        "type": "radar", "width": 560, "height": 460,
        "data": {"axes": ["기획", "개발", "디자인", "마케팅", "운영", "데이터"],
                 "max": 100,
                 "series": [{"name": "우리 팀", "values": [82, 91, 74, 63, 78, 85]},
                            {"name": "업계 평균", "values": [70, 75, 68, 72, 66, 61]}]},
    },
    "kpi_cards": {
        "type": "kpi_cards", "width": 900, "height": 220,
        "data": [{"label": "연 매출", "value": "1,240억", "delta": 18.2},
                 {"label": "MAU", "value": "194만", "delta": 12.4},
                 {"label": "NPS", "value": 62, "delta": -3.0,
                  "delta_unit": "p"},
                 {"label": "구독 전환율", "value": "8.7%", "delta": 1.1,
                  "delta_unit": "%p"}],
    },
    "progress": {
        "type": "progress", "width": 720, "height": 300,
        "data": [{"label": "제품 로드맵", "value": 82},
                 {"label": "글로벌 진출", "value": 64},
                 {"label": "조직 확장", "value": 45},
                 {"label": "보안 인증", "value": 91}],
    },
    "funnel": {
        "type": "funnel", "unit": "만", "width": 720, "height": 420,
        "data": [{"label": "방문", "value": 120},
                 {"label": "가입", "value": 48},
                 {"label": "활성화", "value": 26},
                 {"label": "결제", "value": 9}],
    },
    "heatmap": {
        "type": "heatmap", "width": 720, "height": 420,
        "data": {"rows": ["월", "화", "수", "목", "금"],
                 "cols": ["09시", "11시", "13시", "15시", "17시", "19시", "21시"],
                 "values": [[12, 28, 35, 30, 42, 55, 38],
                            [15, 30, 38, 33, 45, 58, 41],
                            [14, 27, 36, 35, 48, 62, 45],
                            [16, 31, 40, 37, 52, 66, 48],
                            [18, 35, 44, 42, 60, 74, 52]]},
    },
    "treemap": {
        "type": "treemap", "unit": "억", "width": 720, "height": 420,
        "data": [{"label": "클라우드", "value": 420},
                 {"label": "모바일", "value": 310},
                 {"label": "커머스", "value": 200},
                 {"label": "콘텐츠", "value": 150},
                 {"label": "광고", "value": 120},
                 {"label": "기타", "value": 80}],
    },
}


def main() -> int:
    project = Path(sys.argv[1]) if len(sys.argv) > 1 else SAMPLE_PROJECT
    style = resolve_style(project=project)
    spec_dir = EXAMPLES / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    for name, spec in SPECS.items():
        spec_path = spec_dir / f"{name}.json"
        if not spec_path.exists():
            spec_path.write_text(
                json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
        spec_live = json.loads(spec_path.read_text(encoding="utf-8"))
        try:
            writer = render(spec_live, style)
        except Exception as exc:  # keep going; report at the end
            failures.append((name, exc))
            continue
        frag = wrap_fragment(f"chart_{name}", name, writer.fragment(),
                             marker=plot_marker(writer, spec_live))
        svg = wrap_standalone(style, frag,
                              float(spec_live.get("width", 720)),
                              float(spec_live.get("height", 420)))
        (EXAMPLES / f"{name}.svg").write_text(svg + "\n", encoding="utf-8")
        print(f"[ok] {name}")
    if failures:
        for name, exc in failures:
            print(f"[FAIL] {name}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"\n{len(SPECS)} examples rendered with theme "
          f"'{style.theme_name}' → {EXAMPLES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
