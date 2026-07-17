# Visual Overflow Review Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> ⚠️ **이 계획은 인라인 실행 전용** — Task 7(E2E)·Task 8(라이브 덱 수선)은 SVG 손 저작이 필요하고, ppt-master Global Execution Discipline 6·9가 서브에이전트 SVG 생성을 금지한다. Task 1의 검증도 코퍼스 실행 결과 판독이 필요해 메인 에이전트가 직접 수행한다.

**Goal:** SVG 생성 후 겹침·텍스트 오버플로우·원치 않는 줄바꿈을 기본 파이프라인이 스스로 검출·수정하는 루프를 내장한다 (검출: 정적 지오메트리 게이트 + 선별 픽셀 확인, 예방: 저작 규칙).

**Architecture:** `svg_quality_checker.py`에 글리프 폭 근사 기반 지오메트리 검사(A류 error / B류 warning)를 추가하고, executor-base.md/strategist.md에 폭 산수 의무 + 수선 사다리 + 카피 예산을 명문화하며, SKILL.md Step 6 게이트에 B류 건별 처분 의무와 선별 픽셀 패스를 배선한다. 스펙: `docs/superpowers/specs/2026-07-17-visual-overflow-review-design.md`.

**Tech Stack:** Python 3 (stdlib만 — xml.etree, re), 기존 visual_review.py(playwright, 옵션), Markdown 프롬프트 문서.

## Global Constraints

- 블로킹 게이트 추가 금지 (SKILL.md Global Execution Discipline 3·10) — 새 패스는 자동 진행.
- SVG 수정·생성은 메인 에이전트 손 저작 (규칙 6·9) — 검출만 스크립트.
- `tests/` 디렉터리 금지 (repo 관례) — 검증은 동결 코퍼스 실행 = 테스트.
- `.claude/skills/ppt-master/` 하위 문서는 영문 스캐폴딩 (시블링 언어 준수).
- 폰트 메트릭 정밀화 금지 — 근사 상수 튜닝만 (핸드오프 §3.1).
- 동결 코퍼스 `projects/20260717_ppt169_hd_korea_shipbuilding/backup/20260717_100007/svg_output/` 삭제·수정 금지.
- **커밋 규칙**: Task 1–6의 구현 변경분은 커밋하지 않고 working tree에 유지 → Task 9에서 핸드오프 완료 마크와 **한 커밋**으로 main에 커밋·푸시 (사용자 지시). 커밋 말미 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- `projects/`는 gitignore — Task 7·8의 덱 산출물은 로컬 전용, 커밋 대상 아님.
- Windows: `python3` 실패 시 `python`으로 재실행.

---

### Task 1: `svg_quality_checker.py` 지오메트리 검사 (검출기 본체)

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/svg_quality_checker.py`
  - 모듈 상수 추가: `RAMP_MIN_RATIO` 근처 (~line 570)
  - 새 메서드들: `_check_spec_lock_drift` 앞(~line 2198) 또는 클래스 말미의 논리적 위치
  - 호출 배선: `check_file` step 5 뒤 (~line 877)
  - `_categorize_issue`(~line 2505)에 분류 추가

**Interfaces:**
- Consumes: 기존 `_parse_viewbox_values`, `_local_name`, `_is_tspan`, `_is_line_tspan`, `_parse_spec_lock`(update_spec), `self._lock_cache`.
- Produces: `result['errors']`에 `"text geometry: ..."` A류 3형(캔버스 이탈/그룹 침범/세로 이탈), `result['warnings']`에 B류 3형(B-1 unwrap / B-2 lead / B-2 body). Task 5의 SKILL.md 문구와 Task 7·8의 실행 절차가 이 메시지 프리픽스(`text geometry:`)에 의존.

- [ ] **Step 1: 베이스라인 실행 (실패하는 테스트에 해당)**

```bash
python .claude/skills/ppt-master/scripts/svg_quality_checker.py "projects/20260717_ppt169_hd_korea_shipbuilding/backup/20260717_100007/svg_output"
```

Expected: `text geometry:` 메시지 0건 (기능 부재 확인). 기존 검사의 다른 출력(이미지 해상도 warning 등)은 그대로 둔다 — 이 출력을 기록해 Step 4에서 diff 기준으로 쓴다.

- [ ] **Step 2: 모듈 상수 + 순수 함수 추가** (`RAMP_MAX_RATIO = 5.0` 선언 직후에 삽입)

```python
# --- Text-geometry heuristics (overflow / collision / wrap checks) ---
# Glyph-width approximation validated against the 2026-07-17 defect corpus
# (docs/handoff/2026-07-17-visual-overflow-review-handoff.md §1.1): all 8
# user-reported defects reproduce with these constants. Deliberately coarse —
# do not "improve" with real font metrics; tune the constants instead.
GEOM_CJK_WIDTH = 1.0        # CJK / full-width glyph advance, x font-size
GEOM_LATIN_WIDTH = 0.55     # Latin letters, digits, ASCII punctuation
GEOM_SPACE_WIDTH = 0.25     # ASCII space
GEOM_CONSERVATIVE = 0.95    # shrink width estimates before firing errors
GEOM_ASCENT = 0.8           # line-box rise above baseline, x font-size
GEOM_DESCENT = 0.2          # line-box drop below baseline, x font-size
GEOM_OPACITY_EXEMPT = 0.15  # <= this (fill-)opacity => watermark, not an obstacle
GEOM_BG_COVERAGE = 0.85     # rect/image covering >= this of the canvas = background/hero
GEOM_MARGIN_RATIO = 0.05    # assumed content margin for wrap-budget checks
GEOM_MIN_OVERLAP = 4.0      # px; ignore hairline intersections

_GEOM_CJK_EXTRA = set('—…「」『』《》〈〉【】〔〕')
_GEOM_TRANSLATE_RE = re.compile(
    r'^\s*translate\(\s*(-?[\d.]+)(?:[\s,]+(-?[\d.]+))?\s*\)\s*$'
)


def _geom_char_width(ch: str, font_size: float) -> float:
    if ch in (' ', ' '):
        return GEOM_SPACE_WIDTH * font_size
    cp = ord(ch)
    if (
        0x1100 <= cp <= 0x11FF       # Hangul jamo
        or 0x2E80 <= cp <= 0xA4CF    # CJK radicals / kana / unified ideographs
        or 0xAC00 <= cp <= 0xD7AF    # Hangul syllables
        or 0xF900 <= cp <= 0xFAFF    # CJK compatibility ideographs
        or 0xFE30 <= cp <= 0xFE4F    # CJK compatibility forms
        or 0xFF00 <= cp <= 0xFF60    # full-width forms
        or ch in _GEOM_CJK_EXTRA
    ):
        return GEOM_CJK_WIDTH * font_size
    return GEOM_LATIN_WIDTH * font_size


def _geom_text_width(s: str, font_size: float, letter_spacing: float = 0.0) -> float:
    if not s:
        return 0.0
    width = sum(_geom_char_width(ch, font_size) for ch in s)
    if letter_spacing and len(s) > 1:
        width += letter_spacing * (len(s) - 1)
    return width


def _geom_sentence_count(text: str) -> int:
    """Terminal-punctuation count; '.' terminal only before whitespace/end
    (protects decimals like 2.5%)."""
    count = 0
    n = len(text)
    for i, ch in enumerate(text):
        if ch in '。！？!?':
            count += 1
        elif ch in '.．' and (i == n - 1 or text[i + 1].isspace()):
            count += 1
    return max(count, 1)
```

- [ ] **Step 3: 클래스 메서드 추가** (`_get_spec_lock` 정의 앞에 삽입; 시그니처는 기존 스타일과 동일하게 `self`/`cls` 사용)

```python
    # ------------------------------------------------------------------
    # Text geometry: canvas overflow, cross-group collision, wrap budget
    # (A-class geometry defects are errors; B-class wrap defects are
    # warnings. Exemptions: same-group intersections, low-opacity
    # watermarks, background/hero elements covering most of the canvas.)
    # ------------------------------------------------------------------

    @staticmethod
    def _geom_float(value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _find_spec_lock_upward(self, svg_path: Path):
        """spec_lock.md via bounded upward search (<= 4 levels).

        The geometry B-checks need `typography.body`, and re-checks of frozen
        corpora live at <project>/backup/<ts>/svg_output/ — two levels deeper
        than the drift check's two-level search. Separate helper on purpose:
        `_get_spec_lock` keeps its existing behavior.
        """
        if _parse_spec_lock is None:
            return None
        d = svg_path.parent
        for _ in range(4):
            cand = d / 'spec_lock.md'
            if cand in self._lock_cache:
                return self._lock_cache[cand]
            if cand.exists():
                try:
                    data = _parse_spec_lock(cand)
                except Exception:
                    data = None
                self._lock_cache[cand] = data
                return data
            if d.parent == d:
                break
            d = d.parent
        return None

    def _geom_body_px(self, svg_path: Path):
        lock = self._find_spec_lock_upward(svg_path)
        if not lock:
            return None
        body = (lock.get('typography') or {}).get('body')
        return self._geom_float(body)

    @classmethod
    def _geom_translate(cls, elem):
        """(tx, ty) for translate-only transforms, (0, 0) when absent, None
        for any other transform (that subtree's geometry is not estimated)."""
        raw = elem.get('transform')
        if raw is None:
            return (0.0, 0.0)
        m = _GEOM_TRANSLATE_RE.match(raw)
        if not m:
            return None
        return (float(m.group(1)), float(m.group(2) or 0.0))

    @classmethod
    def _geom_opacity_exempt(cls, elem) -> bool:
        for attr in ('fill-opacity', 'opacity'):
            v = cls._geom_float(elem.get(attr))
            if v is not None and v <= GEOM_OPACITY_EXEMPT:
                return True
        return False

    @classmethod
    def _geom_shape_box(cls, elem, tag, dx, dy):
        gf = cls._geom_float
        if tag in ('rect', 'image', 'use'):
            x, y = gf(elem.get('x'), 0.0), gf(elem.get('y'), 0.0)
            w, h = gf(elem.get('width'), 0.0), gf(elem.get('height'), 0.0)
            if w <= 0 or h <= 0:
                return None
            if tag == 'rect' \
                    and (elem.get('fill') or '').strip().lower() == 'none' \
                    and elem.get('stroke') in (None, 'none'):
                return None  # invisible layout helper
            return (x + dx, y + dy, x + dx + w, y + dy + h)
        if tag in ('circle', 'ellipse'):
            cx, cy = gf(elem.get('cx'), 0.0), gf(elem.get('cy'), 0.0)
            rx = gf(elem.get('rx')) or gf(elem.get('r'), 0.0)
            ry = gf(elem.get('ry')) or gf(elem.get('r'), 0.0)
            if not rx or not ry or rx <= 0 or ry <= 0:
                return None
            return (cx - rx + dx, cy - ry + dy, cx + rx + dx, cy + ry + dy)
        if tag == 'line':
            x1, y1 = gf(elem.get('x1'), 0.0), gf(elem.get('y1'), 0.0)
            x2, y2 = gf(elem.get('x2'), 0.0), gf(elem.get('y2'), 0.0)
            return (min(x1, x2) + dx, min(y1, y2) + dy,
                    max(x1, x2) + dx, max(y1, y2) + dy)
        if tag in ('polygon', 'polyline'):
            pts = re.findall(r'(-?[\d.]+)[\s,]+(-?[\d.]+)',
                             elem.get('points') or '')
            if not pts:
                return None
            xs = [float(px) for px, _ in pts]
            ys = [float(py) for _, py in pts]
            return (min(xs) + dx, min(ys) + dy, max(xs) + dx, max(ys) + dy)
        return None  # path etc.: not estimated (documented limitation)

    def _geom_text_block(self, text_el, dx, dy):
        gf = self._geom_float
        fs = gf(text_el.get('font-size'))
        x = gf(text_el.get('x'))
        y = gf(text_el.get('y'))
        if fs is None or fs <= 0 or x is None or y is None:
            return None
        anchor = (text_el.get('text-anchor') or 'start').strip()
        ls = gf(text_el.get('letter-spacing'), 0.0) or 0.0

        mixed_sizes = False
        lines = []  # (content, x_abs, baseline)
        cur_text = (text_el.text or '').strip()
        cur_x, cur_y = x, y
        started = bool(cur_text)
        for child in list(text_el):
            if not self._is_tspan(child):
                continue
            if child.get('font-size') is not None:
                mixed_sizes = True
            seg = (child.text or '').strip()
            if self._is_line_tspan(child):
                if started and cur_text:
                    lines.append((cur_text, cur_x, cur_y))
                ty = gf(child.get('y'))
                dy_v = gf(child.get('dy'), 0.0) or 0.0
                cur_y = ty if ty is not None else cur_y + dy_v
                cur_x = gf(child.get('x'), x)
                cur_text = seg
                started = True
            elif seg:
                cur_text = (cur_text + ' ' + seg).strip()
            tail = (child.tail or '').strip()
            if tail:
                cur_text = (cur_text + ' ' + tail).strip()
        if started and cur_text:
            lines.append((cur_text, cur_x, cur_y))
        if not lines:
            return None

        line_boxes = []
        for content, lx, baseline in lines:
            w = _geom_text_width(content, fs, ls)
            if anchor == 'middle':
                x0 = lx - w / 2.0
            elif anchor == 'end':
                x0 = lx - w
            else:
                x0 = lx
            line_boxes.append({
                'text': content,
                'width': w,
                'x0': x0 + dx,
                'x1': x0 + w + dx,
                'top': baseline - GEOM_ASCENT * fs + dy,
                'bottom': baseline + GEOM_DESCENT * fs + dy,
            })
        return {
            'font_size': fs,
            'anchor': anchor,
            'letter_spacing': ls,
            'x': x + dx,
            'lines': line_boxes,
            'mixed_sizes': mixed_sizes,
        }

    def _geom_collect(self, top, vb_w, vb_h):
        """One top-level child -> (obstacle boxes, text blocks).

        Boxes stay per-element (no union): a union bbox would let two footer
        texts span the whole page width and false-fire on anything between
        them.
        """
        boxes = []
        blocks = []
        canvas_area = vb_w * vb_h

        def visit(elem, dx, dy):
            shift = self._geom_translate(elem)
            if shift is None:
                return  # non-translate transform: skip subtree
            dx, dy = dx + shift[0], dy + shift[1]
            tag = _local_name(elem)
            if tag in ('defs', 'metadata', 'title', 'desc', 'symbol',
                       'clipPath', 'linearGradient', 'radialGradient',
                       'pattern', 'filter', 'style', 'script'):
                return
            if self._geom_opacity_exempt(elem):
                return  # watermark: neither obstacle nor checked text
            if tag == 'text':
                block = self._geom_text_block(elem, dx, dy)
                if block is not None:
                    blocks.append(block)
                    for line in block['lines']:
                        boxes.append((line['x0'], line['top'],
                                      line['x1'], line['bottom']))
                return  # tspans already consumed
            box = self._geom_shape_box(elem, tag, dx, dy)
            if box is not None:
                area = (box[2] - box[0]) * (box[3] - box[1])
                if not (tag in ('rect', 'image')
                        and area >= GEOM_BG_COVERAGE * canvas_area):
                    boxes.append(box)
            for sub in list(elem):
                visit(sub, dx, dy)

        visit(top, 0.0, 0.0)
        return boxes, blocks

    def _check_text_geometry(self, root, svg_path: Path, result: Dict) -> None:
        """Static text overflow / collision / wrap-budget checks.

        Width model: CJK 1.0 x fs, Latin 0.55 x fs, space 0.25 x fs
        (validated against the 2026-07-17 defect corpus — 8/8 reproduced).
        A-class (canvas overflow, cross-group intrusion) -> error;
        B-class (unnecessary wrap, over-width single-sentence wrap) -> warning.
        """
        parsed = _parse_viewbox_values(root.get('viewBox') or '')
        if parsed is None:
            return
        _vx, _vy, vb_w, vb_h = parsed
        if vb_w <= 0 or vb_h <= 0:
            return

        groups = []  # (key, label, boxes, blocks)
        for child in list(root):
            tag = _local_name(child)
            if tag in _NON_VISUAL_SVG_TAGS or tag == 'metadata':
                continue
            label = child.get('id') or f'<{tag}>'
            boxes, blocks = self._geom_collect(child, vb_w, vb_h)
            groups.append((id(child), label, boxes, blocks))

        body_px = self._geom_body_px(svg_path)
        margin = vb_w * GEOM_MARGIN_RATIO

        for key, label, _boxes, blocks in groups:
            for block in blocks:
                self._geom_a_checks(block, label, key, groups, vb_w, vb_h,
                                    result)
                if body_px:
                    self._geom_b_checks(block, label, key, groups, vb_w,
                                        margin, body_px, result)

    def _geom_a_checks(self, block, label, own_key, groups, vb_w, vb_h,
                       result):
        for line in block['lines']:
            gap = line['width'] * (1.0 - GEOM_CONSERVATIVE)
            if block['anchor'] == 'middle':
                ex0, ex1 = line['x0'] + gap / 2.0, line['x1'] - gap / 2.0
            elif block['anchor'] == 'end':
                ex0, ex1 = line['x0'] + gap, line['x1']
            else:
                ex0, ex1 = line['x0'], line['x1'] - gap
            snippet = line['text'][:18] + ('…' if len(line['text']) > 18
                                           else '')
            if ex1 > vb_w + 0.5:
                result['errors'].append(
                    f"text geometry: line \"{snippet}\" in group '{label}' "
                    f"overflows the canvas right edge by ~{ex1 - vb_w:.0f}px "
                    f"(est. end x={ex1:.0f} > {vb_w:.0f})"
                )
            if ex0 < -0.5:
                result['errors'].append(
                    f"text geometry: line \"{snippet}\" in group '{label}' "
                    f"starts ~{-ex0:.0f}px left of the canvas"
                )
            if line['bottom'] > vb_h + 0.5 or line['top'] < -0.5:
                result['errors'].append(
                    f"text geometry: line \"{snippet}\" in group '{label}' "
                    f"exceeds the canvas vertically"
                )
            for other_key, other_label, boxes, _blocks in groups:
                if other_key == own_key:
                    continue
                for bx0, by0, bx1, by1 in boxes:
                    ox = min(ex1, bx1) - max(ex0, bx0)
                    oy = min(line['bottom'], by1) - max(line['top'], by0)
                    if ox <= GEOM_MIN_OVERLAP or oy <= GEOM_MIN_OVERLAP:
                        continue
                    # Containment = deliberate underlay (text on a panel);
                    # a defect crosses the obstacle's edge instead.
                    h_cross = (
                        (ex0 < bx0 - GEOM_MIN_OVERLAP
                         and ex1 > bx0 + GEOM_MIN_OVERLAP)
                        or (ex1 > bx1 + GEOM_MIN_OVERLAP
                            and ex0 < bx1 - GEOM_MIN_OVERLAP)
                    )
                    v_cross = (
                        (line['top'] < by0 - GEOM_MIN_OVERLAP
                         and line['bottom'] > by0 + GEOM_MIN_OVERLAP)
                        or (line['bottom'] > by1 + GEOM_MIN_OVERLAP
                            and line['top'] < by1 - GEOM_MIN_OVERLAP)
                    )
                    if h_cross or v_cross:
                        result['errors'].append(
                            f"text geometry: line \"{snippet}\" in group "
                            f"'{label}' intrudes ~{ox:.0f}px into group "
                            f"'{other_label}' (obstacle x={bx0:.0f}..{bx1:.0f}"
                            f", y={by0:.0f}..{by1:.0f})"
                        )
                        break  # one report per (line, group) pair

    def _geom_b_checks(self, block, label, own_key, groups, vb_w, margin,
                       body_px, result):
        if (
            len(block['lines']) < 2
            or block['anchor'] != 'start'
            or block['mixed_sizes']
            or block['font_size'] < body_px - 0.01
        ):
            return
        x_start = block['x']
        top = min(line['top'] for line in block['lines'])
        bottom = max(line['bottom'] for line in block['lines'])
        right_bound = vb_w - margin
        for other_key, _other_label, boxes, _blocks in groups:
            if other_key == own_key:
                continue
            for bx0, by0, bx1, by1 in boxes:
                if bx0 <= x_start:
                    continue  # not a right-side obstacle
                if min(bottom, by1) - max(top, by0) <= GEOM_MIN_OVERLAP:
                    continue  # no vertical overlap with the block
                right_bound = min(right_bound, bx0)
        available = right_bound - x_start
        if available <= 0:
            return

        full_text = ' '.join(line['text'] for line in block['lines'])
        full_w = _geom_text_width(full_text, block['font_size'],
                                  block['letter_spacing'])
        n = len(block['lines'])
        fs = block['font_size']
        if full_w <= available:
            result['warnings'].append(
                f"text geometry: block in group '{label}' wraps into {n} "
                f"lines but fits on one (est {full_w:.0f}px <= "
                f"{available:.0f}px available) — draw it as a single line "
                f"(executor-base.md width budget)"
            )
        elif fs > body_px + 0.01:
            result['warnings'].append(
                f"text geometry: lead-size block ({fs:.0f}px > body "
                f"{body_px:.0f}px) in group '{label}' wraps (est "
                f"{full_w:.0f}px > {available:.0f}px available) — shorten "
                f"the copy (repair ladder ①) or redistribute the zone (②); "
                f"a one-sentence lead must not wrap"
            )
        elif n == 2 and _geom_sentence_count(full_text) <= 1:
            result['warnings'].append(
                f"text geometry: single-sentence block in group '{label}' "
                f"wraps to 2 lines (est {full_w:.0f}px > {available:.0f}px "
                f"available) — consider shortening (ladder ①) or a balanced "
                f"word-boundary break (③)"
            )
```

- [ ] **Step 4: `check_file` 배선 + `_categorize_issue` 분류 추가**

`check_file`의 `self._check_text_elements(content, root, result)` 호출 직후에 삽입:

```python
                # 5b. Text geometry: overflow / collision / wrap budget.
                #     Templates carry placeholder copy; skip in template mode.
                if not self.template_mode:
                    self._check_text_geometry(root, svg_path, result)
```

`_categorize_issue` 본문 맨 앞에 분기 추가:

```python
        if 'text geometry' in error_msg:
            return 'Text geometry (overflow/collision)'
```

- [ ] **Step 5: 코퍼스 수용 실행 (§6-1)**

```bash
python .claude/skills/ppt-master/scripts/svg_quality_checker.py "projects/20260717_ppt169_hd_korea_shipbuilding/backup/20260717_100007/svg_output"
```

Expected (수용 기준 — 반드시 전부 충족):
- `06_barclays.svg` — error ≥1: core-message 줄이 `highlight-panel` 침범
- `07_groundbreaking.svg` — error ≥1: core-message 줄 캔버스 우측 이탈
- `08_speed_myth.svg` — error ≥1: core-message 줄이 `vlcc-photo` 침범
- `01_cover.svg` — warning: B-1 (부제 954px ≤ 1152px인데 2줄)
- `03_1960s_background.svg` — warning: B-1 (supporting 1050px ≤ 1152px인데 2줄)
- `04_chung_juyung.svg` — warning: B-2 body (994px > 676px, 한 문장 2줄)
- `05_founding_myth.svg` — warning: B-2 lead (1237px > 1152px)
- `08_speed_myth.svg` — warning: B-2 (supporting 842px > 696px)
- **P06·P07·P08 이외 페이지에 `text geometry:` error 0건** — 특히 스크림 페이지(01/05/09/12/16/19/24)와 워터마크 페이지(03/11)에서 A류 오탐 0.

불일치 시: 상수(`GEOM_MIN_OVERLAP`, `GEOM_CONSERVATIVE`, ascent/descent)나 예외 규칙을 튜닝하고 재실행 — 근사식 자체를 정밀화하지 말 것. P11–24에서 나오는 **신규 B warning은 오탐이 아니라 신규 검출분**으로 기록해 Task 8로 넘긴다 (핸드오프 §1.1: 미리뷰 페이지의 검출은 사람 확인 필요).

참고: 코퍼스 디렉터리는 `images/`가 없어 이미지 참조 error가 섞여 나올 수 있음(백업 스냅샷 한계, `resource_paths`가 프로젝트 루트로 해석하면 없음). A/B 검출 판정과 무관하므로 무시하되 기록.

- [ ] **Step 6: 단일 파일 모드 확인 (first-page gate 경로)**

```bash
python .claude/skills/ppt-master/scripts/svg_quality_checker.py "projects/20260717_ppt169_hd_korea_shipbuilding/backup/20260717_100007/svg_output/06_barclays.svg"
```

Expected: 같은 A류 error 재현 (단일 파일 경로에서도 동작).

- [ ] **Step 7: 커밋하지 않음** — Global Constraints의 커밋 규칙에 따라 working tree 유지. `git status`로 변경 파일만 확인.

---

### Task 2: `preflight.py` playwright 옵션 의존성 warn

**Files:**
- Modify: `.claude/skills/ppt-master/scripts/preflight.py:45-49` (`OPTIONAL_MODULES`)

**Interfaces:**
- Produces: playwright 부재 시 `! WARN missing Python dep 'playwright' — ...` (정보성, PASS 유지).

- [ ] **Step 1: `OPTIONAL_MODULES` 튜플에 항목 추가**

```python
OPTIONAL_MODULES = (
    ("flask", "flask", "Confirm UI page + live preview fall back to chat-only"),
    ("numpy", "numpy", "image placeholder detection and watermark tooling degrade"),
    ("requests", "requests", "web image search / web_to_md unavailable"),
    ("playwright", "playwright", "Step 6 selective pixel check and visual-review "
     "rendering are skipped (static geometry gate still runs)"),
)
```

- [ ] **Step 2: 실행 확인**

```bash
python .claude/skills/ppt-master/scripts/preflight.py
```

Expected: exit 0 (PASS). playwright 미설치 환경이면 WARN 1줄 추가 — FAIL로 승격되지 않아야 함.

---

### Task 3: `executor-base.md` 예방 규칙 (폭 산수 의무 + 수선 사다리)

**Files:**
- Modify: `.claude/skills/ppt-master/references/executor-base.md`
  - §2.1 종료 지점(“**If `spec_lock.md` is missing**” 문단 앞)에 새 하위 절 삽입
  - §3 Phased batch generation 2번(Quality Check Gate) 문장 보강

**Interfaces:**
- Consumes: Task 1의 근사 상수(문서에 동일 값 명기), spec §3.1 결정(ⓑ Executor 한정 축약).
- Produces: Task 5 SKILL.md와 Task 7·8 실행이 참조하는 “width budget” / “repair ladder” 용어.

- [ ] **Step 1: §2.1 내부, “If spec_lock.md is missing” 문단 바로 앞에 삽입**

```markdown
**Text width & wrap budget (Mandatory)**: SVG has no auto-wrap — every line
break is the author's manual `<tspan>` split, so every wrap decision is width
arithmetic done (or skipped) at draw time. Run the arithmetic **before**
drawing any text block, with the same approximation the quality checker uses:
`est_width = Σ glyph widths + letter-spacing × (chars − 1)`, where a CJK /
full-width glyph is `1.0 × font-size`, a Latin letter / digit / ASCII symbol
is `0.55 × font-size`, and a space is `0.25 × font-size`.

1. Determine the zone width: from the text `x` to the nearest right boundary —
   content margin (canvas width − ~5%), panel edge, image edge, or column
   gutter, whichever is nearest.
2. `est_width(sentence, font-size) ≤ zone width` → draw it as **one line**.
   Never wrap a sentence that fits — an unnecessarily wrapped line is a
   defect the quality checker flags.
3. Over budget → apply the repair ladder below, in order.
4. Vertical is arithmetic too: last baseline = `y + Σdy`; the block bottom
   (`+ 0.2 × font-size` descent) MUST clear the next element's top edge and
   the canvas bottom margin. Allocate wrapped-line count × line-height before
   placing the block (§1.0).

**Repair ladder (over-budget copy — apply in order)**:

| # | Strategy | Bounds |
|---|---|---|
| ① | **Shorten the copy** — lead / core-message first | Executor-owned micro-shortening at draw time: meaning preserved, no fact distortion; the dropped detail must already exist in — or be moved into — a supporting block on the page. CJK costs a full font-size px per glyph, so trimming a few characters buys real room. |
| ② | **Redistribute the zone** | When the colliding neighbor can move: narrow the panel / image column, rebalance margins. Useless on full-width pages; costs layout balance. |
| ③ | **Balanced line break** | **Body prose only** — break at word / phrase boundaries, balance the line lengths, never leave an orphan word on the last line. **Not permitted for lead / core-message / subtitle**: a one-sentence lead wrapping to two lines is itself a defect (user norm, 2026-07-17). |
| ④ | **Font reduction** | Forbidden in principle. The §1.0 bounded last resort (body only, local, max −4px) is unchanged; lead / title sizes never shrink to fit. |
```

- [ ] **Step 2: §3 “2. Quality Check Gate” 문단 끝에 한 문장 추가**

기존 문장 “Flat free-design/brand-only routes have no Master/Layout checkpoint.” 뒤에:

```markdown
Text-geometry B-class warnings (unnecessary wrap / over-width copy) are likewise never acknowledge-and-release: disposition each one — fix it (unwrap, shorten per the repair ladder, redistribute the zone, or re-break at a word boundary) or state why the flagged break is intended.
```

- [ ] **Step 3: 확인** — `grep -n "Repair ladder" .claude/skills/ppt-master/references/executor-base.md` → 1건. 커밋하지 않음.

---

### Task 4: `strategist.md` 카피 길이 예산

**Files:**
- Modify: `.claude/skills/ppt-master/references/strategist.md` §6.2 “Generation steps” 4번 항목의 하위 불릿 (Cover impact 불릿 앞)

**Interfaces:**
- Consumes: spec §3.2 (전폭 26자 / 분할 16자 예산).

- [ ] **Step 1: §6.2 step 4 하위 불릿 목록에서 “**Cover impact is mandatory**” 불릿 바로 앞에 삽입**

```markdown
   - **Core-message / lead copy-length budget (mandatory)**: each page's core-message / lead line renders at the locked `lead` size and MUST fit its zone on one line — **a one-sentence lead that wraps to two lines is a defect** (user norm, 2026-07-17). Budget the copy while writing §IX: usable width ÷ lead px ≈ max CJK glyphs. For PPT 16:9 with a 40px `lead` that is ≈ 26 CJK glyphs on a full-width zone (~1152px) and ≈ 16 glyphs beside a side panel / image column; scale by the actual lead px, and assume the split-zone budget whenever the page plans a side visual. The core message is a one-sentence spine — keep it punchy; details it sheds belong in the supporting blocks. (The Executor may micro-shorten an over-budget lead at draw time — executor-base.md §2.1 repair ladder ① — but authoring within budget is the primary defense.)
```

- [ ] **Step 2: 확인** — `grep -n "copy-length budget" .claude/skills/ppt-master/references/strategist.md` → 1건. 커밋하지 않음.

---

### Task 5: SKILL.md Step 6 게이트 배선 + 선별 픽셀 패스

**Files:**
- Modify: `.claude/skills/ppt-master/SKILL.md` Step 6 (Quality Check Gate 블록, 체크포인트 체크리스트)

**Interfaces:**
- Consumes: Task 1 메시지 프리픽스 `text geometry:`, Task 3의 repair ladder 용어, `visual_review.py` CLI(`--pages`, `--server-url`).

- [ ] **Step 1: Quality Check Gate 첫 불릿의 괄호 보강**

`- Any \`error\` (banned SVG features, viewBox mismatch, spec_lock drift, etc.)` →

```markdown
- Any `error` (banned SVG features, viewBox mismatch, spec_lock drift, text-geometry overflow / cross-group collision, etc.) MUST be fixed before proceeding — return to Visual Construction, regenerate that page, re-run check.
```

- [ ] **Step 2: warning 불릿 뒤에 B류 처분 불릿 추가** (구조화 템플릿 불릿 앞)

```markdown
- **Text-geometry warnings are never acknowledge-and-release.** For each `text geometry:` warning (unnecessary wrap / over-width copy), output one disposition line: the fix applied (unwrap to one line, shorten the copy per the executor-base.md repair ladder, redistribute the zone, or re-break at a word boundary) or why the flagged break is intended (e.g. quoted verse keeps its authored line breaks). Default is fix.
```

- [ ] **Step 3: Quality Check Gate 블록 마지막 불릿(“Run against svg_output/...”) 뒤에 선별 픽셀 패스 문단 추가**

```markdown
**Selective pixel check (automatic, non-blocking)** — after the gate reaches 0 errors: if any page carried `text geometry:` findings, or overlays text on a full-bleed hero / scrim or a low-opacity watermark (the static checker exempts those zones, so arithmetic alone cannot clear them), render just those pages and eyeball them:

```bash
python3 ${SKILL_DIR}/scripts/visual_review.py <project_path> --pages <tokens> --server-url <live-preview URL>
```

The Step 6 live-preview server is already running — pass its actual URL from the launch log. Read each rendered PNG from `<project_path>/.preview/` and fix any real overlap / overflow by hand-editing the SVG (main agent; discipline rules 6 and 9 apply — no sub-agents, no script-generated SVG). If playwright or the server is unavailable, skip silently — the static gate stands alone. This pass is automatic and never a user stop; the full-rubric [`visual-review`](workflows/visual-review.md) workflow remains opt-in.
```

- [ ] **Step 4: Executor 체크포인트 체크리스트에 2줄 추가** (`- [x] svg_quality_checker.py passed (0 errors)` 뒤)

```markdown
- [x] Text-geometry warnings dispositioned one by one (fix or stated intent)
- [x] Selective pixel check run on flagged + hero/scrim pages (silently skipped when playwright or the preview server is absent)
```

- [ ] **Step 5: Codex 스텁 동기화** (SKILL.md 수정 후 관례)

```bash
python .claude/skills/ppt-master/scripts/sync_codex_stubs.py
```

Expected: exit 0. 변경된 스텁이 있으면 Task 9 커밋에 포함.

---

### Task 6: `visual-review.md` 포지셔닝 + `failure-recovery.md` 수정 루프

**Files:**
- Modify: `.claude/skills/ppt-master/workflows/visual-review.md` (Positioning 절)
- Modify: `.claude/skills/ppt-master/workflows/failure-recovery.md` (§1 매트릭스, §3 Resume Pointers)

- [ ] **Step 1: visual-review.md Positioning 절 첫 문단 교체**

기존 “This is an **optional auxiliary loop**, opt-in only. The main pipeline (SKILL.md Step 1–7) does not invoke it; ...” 문단을:

```markdown
The main pipeline now runs a **default lightweight geometry loop** of its own: `svg_quality_checker.py` statically detects text overflow / cross-group collision (errors) and unnecessary or over-width wraps (warnings), and SKILL.md Step 6 follows it with a selective pixel check (flagged + hero/scrim pages only, main-agent Read, silently skipped without playwright). That default loop owns arithmetic-detectable geometry defects only.

This workflow remains the **optional full visual re-pass**, opt-in only: per-page rubric coverage (rhythm, alignment, centroid, readability, emphasis) via parallel subagents over every rendered page. The main pipeline does not invoke it; trigger only when the user explicitly asks for a visual re-pass on the generated SVGs before export.
```

- [ ] **Step 2: failure-recovery.md §1 매트릭스에 2행 추가** (`svg_quality_checker.py warning` 행 뒤)

```markdown
| Post-export visual defect (verify_deck contact sheet / user review) | No | Hand-edit the owning `svg_output/` page (main agent), rerun Step 7.2 + 7.3 (finalize + export; verN auto-increments) | Only when the fix needs a content decision | Step 7.2 |
| Selective pixel check unavailable (playwright or preview server missing) | No | Skip silently — the static geometry gate already ran | No | Step 6 gate |
```

- [ ] **Step 3: failure-recovery.md §3 Resume Pointers에 1행 추가** (`Browser annotations saved after export` 행 뒤)

```markdown
| Visual defect found after export | Fix `svg_output/`, then Step 7.2 → 7.3 re-run (new verN) |
```

- [ ] **Step 4: 확인** — 두 파일 diff 육안 점검, 표 정렬 유지. 커밋하지 않음.

---

### Task 7: E2E 검증 — 미니 덱 1회 완주 (§6-3)

**Files:**
- Create: `projects/<YYYYMMDD>_ppt169_<slug>/` (로컬 전용, 커밋 안 함) — 5페이지 무이미지 free-design 미니 덱

**Interfaces:**
- Consumes: Task 1–6 전부 (예방 규칙 반영 저작 → 게이트 → 선별 픽셀 → Step 7).

- [ ] **Step 1: 프로젝트 init + preflight**

```bash
python .claude/skills/ppt-master/scripts/project_manager.py init e2e_overflow_loop --format ppt169
python .claude/skills/ppt-master/scripts/preflight.py
```

- [ ] **Step 2: 계획 산출물 직접 저작** — 대화 컨텍스트를 소스로 5페이지(cover / 3 content / closing) `design_spec.md`(§I–X 전체) + `spec_lock.md`(body 32 / lead 40 등 표준 램프, 이미지 없음, 아이콘 최소) 작성. 이 저작 자체가 Task 4의 카피 예산 규칙을 따르는지 자기 점검 (리드 ≤ 26자).

```bash
python .claude/skills/ppt-master/scripts/validate_spec.py projects/<e2e_project>
```

Expected: 0 errors.

- [ ] **Step 3: Executor 실행** — 라이브 프리뷰 서버 기동(`svg_editor/server.py <project> --live --daemon`), Task 3의 폭 산수 의무를 적용해 5페이지를 순차 손 저작 (첫 페이지 게이트 포함).

- [ ] **Step 4: 게이트 + 수정 루프** — `svg_quality_checker.py <project>` 실행: error 0 + `text geometry:` warning 0(또는 건별 처분) 도달까지 수정. 선별 픽셀 패스: 플래그/스크림 페이지가 있으면 `visual_review.py <project> --pages ... --server-url <URL>` → PNG Read → 필요 시 수정.

- [ ] **Step 5: Step 7 완주**

```bash
python .claude/skills/ppt-master/scripts/finalize_svg.py projects/<e2e_project>
python .claude/skills/ppt-master/scripts/svg_to_pptx.py projects/<e2e_project>
python .claude/skills/ppt-master/scripts/verify_deck.py projects/<e2e_project>
```

Expected: export 성공, verify_deck 통과, **전 과정에 사용자 정지점 0** (Step 4 확인 단계는 이 검증의 범위 밖 — Executor 이후 흐름만 판정).

- [ ] **Step 6: 판정 기록** — 산출물에 A/B류 결함 없음(게이트 로그 + 픽셀 PNG 육안)을 로그로 남김.

---

### Task 8: 라이브 덱 수선 + export ver2 (§6-2·§6-4)

**Files:**
- Modify: `projects/20260717_ppt169_hd_korea_shipbuilding/svg_output/*.svg` (로컬 전용 — 커밋 안 함; 동결 코퍼스 `backup/20260717_100007/`은 절대 건드리지 않음)

**Interfaces:**
- Consumes: Task 1 검사기, Task 3 수선 사다리 (핸드오프 §3.2의 P05 축약 예시·P07 사이드바 480→400 예시 포함).

- [ ] **Step 1: 라이브 svg_output 전수 검사**

```bash
python .claude/skills/ppt-master/scripts/svg_quality_checker.py "projects/20260717_ppt169_hd_korea_shipbuilding"
```

기존 8건 재검출 + P11–24 신규 검출분 목록화.

- [ ] **Step 2: 손 저작 수선 (수선 사다리 적용, 페이지별)** — 알려진 8건의 방향:
  - P01 부제: 한 줄로 unwrap (여유 198px)
  - P03 supporting: 한 줄로 unwrap (여유 102px)
  - P04 supporting: 카피 축약(①) 또는 균형 재분할(③ — body 프로즈 허용)
  - P05 리드: 축약(① — 핸드오프 예시: “백사장 사진 한 장과 지도 한 장으로 VLCC 2척을 수주했다”)
  - P06 리드: 축약(①) 및/또는 패널 존 재배분(②)
  - P07 리드: 축약(①) 또는 사이드바 480→400(②)
  - P08 리드: 축약(①); P08 supporting: 축약(①) 또는 균형 재분할(③)
  - 신규 검출분: 건별 처분 (수정 또는 의도 사유 기록)

- [ ] **Step 3: 재검사 → 오탐 0 판정 (§6-2)**

```bash
python .claude/skills/ppt-master/scripts/svg_quality_checker.py "projects/20260717_ppt169_hd_korea_shipbuilding"
```

Expected: `text geometry:` error 0. warning은 전부 처분 완료 상태(수정됐거나 의도 사유 명시). 스크림 페이지(01/05/09/12/16/19/24)·워터마크(03/11)에서 지오메트리 오탐 0.

- [ ] **Step 4: 선별 픽셀 패스** — 수정 페이지 + 스크림/워터마크 페이지를 렌더해 육안 확인:

```bash
python .claude/skills/ppt-master/scripts/svg_editor/server.py "projects/20260717_ppt169_hd_korea_shipbuilding" --live --daemon
python .claude/skills/ppt-master/scripts/visual_review.py "projects/20260717_ppt169_hd_korea_shipbuilding" --pages 01 03 04 05 06 07 08 09 11 12 16 19 24 --server-url <URL>
```

PNG Read → 잔여 결함 있으면 Step 2로 루프.

- [ ] **Step 5: finalize + export ver2 + verify**

```bash
python .claude/skills/ppt-master/scripts/finalize_svg.py "projects/20260717_ppt169_hd_korea_shipbuilding"
python .claude/skills/ppt-master/scripts/svg_to_pptx.py "projects/20260717_ppt169_hd_korea_shipbuilding"
python .claude/skills/ppt-master/scripts/verify_deck.py "projects/20260717_ppt169_hd_korea_shipbuilding"
```

Expected: `exports/<title>_ver2.pptx` 생성(verN 자동 증가), verify_deck 통과.

---

### Task 9: 핸드오프 완료 마크 + 단일 커밋·푸시

**Files:**
- Modify: `docs/handoff/2026-07-17-visual-overflow-review-handoff.md` (머리에 완료 마크)
- Commit: Task 1–6 변경 전부 + 핸드오프 (한 커밋)

- [ ] **Step 1: 핸드오프 머리(작성일 줄 앞)에 완료 마크 삽입** — 2026-07-14 핸드오프 관례:

```markdown
> **✅ [2026-07-17] 구현 완료** — §3.1 지오메트리 게이트(A류 error/B류 warning + 오탐 예외) + §3.2 예방 규칙(폭 산수 의무·수선 사다리·카피 예산, 축약 권한 ⓑ Executor 한정) + §3.3 선별 픽셀 패스(조건부 보조층) 구현·검증됨. 코퍼스 A류 3/3 error·B류 5/5 warning, 수정본 오탐 0, E2E 1회 완주, 라이브 덱 ver2 export까지 완료. 이 문서는 이력 보존용.
> - 스펙: `docs/superpowers/specs/2026-07-17-visual-overflow-review-design.md`
> - 계획: `docs/superpowers/plans/2026-07-17-visual-overflow-review.md`
> - 커밋: `<hash>` (구현 전체 + 이 마크)
```

(커밋 해시는 커밋 후 알 수 없으므로 마크에는 커밋 제목만 적거나, 이 줄은 “구현 전체 + 이 마크 단일 커밋”으로 표기.)

- [ ] **Step 2: 검증 요약을 실측값으로 갱신** — 마크의 검출 수치가 Task 1·7·8 실측과 일치하는지 확인.

- [ ] **Step 3: 단일 커밋 + 푸시**

```bash
git add .claude/skills/ppt-master/scripts/svg_quality_checker.py .claude/skills/ppt-master/scripts/preflight.py .claude/skills/ppt-master/references/executor-base.md .claude/skills/ppt-master/references/strategist.md .claude/skills/ppt-master/SKILL.md .claude/skills/ppt-master/workflows/visual-review.md .claude/skills/ppt-master/workflows/failure-recovery.md docs/handoff/2026-07-17-visual-overflow-review-handoff.md
git add .codex/skills  # sync_codex_stubs 변경분이 있을 때만
git commit -m "geometry gate: overflow/collision/wrap detection + prevention in default pipeline ..."
git push
```

커밋 메시지 본문에: A류 error/B류 warning 요약, 오탐 예외 3규칙, 수선 사다리 ①–④와 축약 권한 ⓑ, 선별 픽셀 패스, 코퍼스 3/3+5/5 검증 결과. 말미 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

Expected: push 성공, `git status` 클린(projects/ 제외).

---

## Self-Review 결과

- **Spec coverage**: 스펙 §2(검출)=Task 1, §2.6(상향 lock)=Task 1 Step 3, §3.1(executor)=Task 3, §3.2(strategist)=Task 4, §4(픽셀 패스)=Task 5 Step 3 + preflight=Task 2, §5(배선)=Task 5·6, §6(검증)=Task 1 Step 5 + Task 7 + Task 8. 갭 없음.
- **Placeholder scan**: 코드 블록 전부 실제 구현; “적절히 처리” 류 없음. Task 7 Step 2의 덱 저작은 이 repo의 본질상 생성 작업(계획이 대신 쓸 수 없음)으로 허용.
- **Type consistency**: `_geom_*` 명명, `text geometry:` 프리픽스, GEOM_* 상수가 Task 1/3/5에서 동일.
