# apple 템플릿 (deck + brand) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vitrine 모노크롬 HTML 슬라이드 13종을 `templates/decks/apple/`(SVG 로스터 + deck spec)과 `templates/brands/apple/`(아이덴티티 추출본)으로 이식·등록한다.

**Architecture:** create-template 워크플로(Type C, standard)를 따르되 HTML/CSS 직독 값을 1차 팩트로 사용. 각 SVG는 mckinsey 덱과 동일한 메타데이터 계약(`data-pptx-master/layout`, placeholder slot, `{{TOKEN}}` 캐리어)을 따른다. 검증은 svg_quality_checker(template-mode) + Playwright 렌더 대 원본 스크린샷 시각 대조.

**Tech Stack:** SVG(DrawingML 변환 대상), Python(playwright, repo 스크립트), Pretendard 폰트 스택.

**승인된 스펙:** [`docs/superpowers/specs/2026-07-16-apple-template-design.md`](../specs/2026-07-16-apple-template-design.md) — 모든 태스크의 상위 요구사항.

## Global Constraints

모든 태스크에 공통 적용. 위반은 곧 태스크 실패다.

- **캔버스**: `ppt169`, `width="1280" height="720" viewBox="0 0 1280 720"`.
- **모노크롬만**: 허용 HEX = `#ffffff #fafafc #f5f5f7 #ececef #e0e0e0 #d2d2d7 #c7c7cc #a8a8ad #7a7a7a #6e6e73 #333333 #272729 #1d1d1f #161617 #000000`. 이외의 색(특히 유채색) 사용 금지.
- **폰트 스택** — repo 규약(strategist.md §g, mckinsey 덱): 중간 웨이트는 **설치 패밀리명 + normal weight**로 저작한다. `font-weight` 속성은 700에만 붙인다:
  - 300: `font-family="'Pretendard Light', Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 없음)
  - 400: `font-family="Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 없음)
  - 600: `font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"` (font-weight 없음)
  - 700: `font-family="Pretendard, 'Malgun Gothic', sans-serif" font-weight="700"`
  - **500 금지**(= `'Pretendard Medium'` 사용 금지). **헤드라인은 600(700 아님).**
- **자간**: 원본 px 값을 `letter-spacing` 속성으로 그대로 이관(예: `letter-spacing="-3"`). 이 템플릿의 샘플 텍스트는 영문이므로 완화 없이 원본 값 사용. 한글 완화 규칙(½)은 deck spec 문서에만 기술한다(생성 시점 규칙).
- **그림자**: 시스템 전체 단 1종 — `feDropShadow dx="3" dy="5" stdDeviation="15" flood-color="#000000" flood-opacity="0.22"`. **이미지 플레이스홀더 rect에만**(09_image, 해당 시 04_split) 허용. 카드/텍스트/버튼 그림자 금지. 필터는 `<defs>` 직계 `<filter>` + 대상 단일 요소의 `filter="url(#...)"` 직접 속성(shared-standards §6.4).
- **모서리 문법**: 0 / rx=4(차트 스와치·바) / rx=8 / rx=12(인라인 이미지) / rx=18(카드) / 9999(필)만.
- **악센트 컬러 0, 그라디언트 장식 0, 이모지 0.**
- **서피스**: 13장 전부 라이트 모드. white 9장 + parchment(`#f5f5f7`) 4장(03/05/07/13). `is-dark`/`is-black`은 이 로스터에 등장하지 않는다.
- **공통 크롬**: 푸터 = 좌 `{{BRAND_MARK}}`(x=64, anchor start) + 우 `{{PAGE_LABEL}}`(x=1216, anchor end), baseline y≈682(렌더 대조로 ±4px 보정), 12px. mark는 600 ls−0.4 `#6e6e73`, label은 400 ls−0.12 `#7a7a7a`.
- **커밋 메시지**: `apple deck: ...` / `apple brand: ...` 형식, 본문 마지막에 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- **작업 문서 외 repo 루트/타 디렉터리 오염 금지**: 분석 산출물(스크린샷 등)은 스크래치패드에만 둔다.

## File Structure

| 경로 | 책임 | 생성 태스크 |
|---|---|---|
| `<scratchpad>/apple_ds_ref/*.png` | 원본 HTML 렌더 스크린샷 13장 (repo 밖, 검증 기준) | 1 |
| `<scratchpad>/apple_ds_ref/render_ref.py` | 스크린샷 렌더 스크립트 | 1 |
| `.claude/skills/ppt-master/templates/decks/apple/templates/design_spec.md` | deck 스펙 (아이덴티티+구조+미들) | 3 |
| `.claude/skills/ppt-master/templates/decks/apple/templates/01_title.svg` … `13_closing.svg` | SVG 로스터 13장 | 4–9 |
| `.claude/skills/ppt-master/templates/decks/decks_index.json` | deck 등록 (스크립트가 갱신) | 11 |
| `.claude/skills/ppt-master/templates/brands/apple/templates/design_spec.md` | brand 스펙 (아이덴티티 I~VI) | 12 |
| `.claude/skills/ppt-master/templates/brands/brands_index.json` | brand 등록 (스크립트가 갱신) | 12 |

소스(읽기 전용): `C:\Users\byung\Downloads\Apple Design System\` — `slides/*.html`, `slides/slides.css`, `colors_and_type.css`, `README.md`.

## 공통 팩트 시트 (모든 SVG 태스크가 참조)

### 공유 스타일

| 요소 | 값 |
|---|---|
| kicker | 600 14px, line-height 1.29, `letter-spacing="0.84"`(=0.06em), 대문자, `#6e6e73` |
| 푸터 | Global Constraints 참조 |
| 헤어라인 | `stroke="#e0e0e0" stroke-width="1"` |
| 이미지 플레이스홀더(imgph) | 대각선 해칭 rect + 중앙 400 12px `#a8a8ad` 라벨 텍스트(원본 안내문 리터럴, 토큰 아님). 해칭은 네이티브 프리셋 주석을 단 `<pattern>`으로 구현(shared-standards §7 Pattern Fill): `<pattern id="imgph-hatch" patternUnits="userSpaceOnUse" width="20" height="20" patternTransform="rotate(45)" data-pptx-pattern="ltUpDiag"><rect width="20" height="20" fill="#f5f5f7"/><rect width="10" height="20" fill="#ececef"/></pattern>` → 첫 rect=배경 `#f5f5f7`, 둘째 rect=전경 `#ececef`. 사용 rect는 `fill="url(#imgph-hatch)"` |
| 본문 색 | 잉크 `#1d1d1f`, 뮤트 `#6e6e73` |
| 콘텐츠 마진 | 페이지별 상이(아래) — 푸터만 64px 고정 |

### 페이지별 팩트 (원본 HTML 직독 값)

**01_title (white)** — 중앙 정렬 세로 스택(gap 30): kicker `{{KICKER}}` → h1 `{{TITLE}}` 600 112px lh1.03 ls−3 `#1d1d1f` max-w 1080 (2행 샘플 "Light.\nYears ahead.") → sub `{{SUBTITLE}}` 300 28px lh1.25 ls+0.1 `#6e6e73` max-w 640 (2행). 블록 전체 수직 중앙. 근사 baseline: kicker 182 / h1 306, 421 / sub 504, 539 (렌더 대조로 보정).

**02_agenda (white)** — 헤더 top88 left/right120: kicker → h2 `{{TITLE}}` 600 52px lh1.06 ls−1.2 (kicker 아래 10px). 리스트 top262 left/right120: 행 4개 `{{ITEM_n_TITLE}}`/`{{ITEM_n_TAG}}`, 각 행 상단 헤어라인 + 상하 padding 26 → 행 피치 ≈ 88px, 제목 600 36px ls−0.8 잉크(좌), 태그 400 17px ls−0.374 `#6e6e73`(우, anchor end x=1160).

**03_section (parchment)** — 중앙 스택(gap 26): kicker `{{KICKER}}` → h2 `{{TITLE}}` 600 96px lh1.04 ls−2.6 잉크 max-w 1020 (2행 샘플).

**04_split (white)** — imgph rect x0 y0 w600 h720 (rx 0, 풀블리드—헤어라인 테두리는 우변만 생략 가능, 라벨 "product photograph"). 텍스트 칼럼 x688~1180, 수직 중앙 스택(gap 26): kicker → h2 `{{TITLE}}` 600 56px lh1.05 ls−1.4 (2행) → 본문 `{{BODY}}` 300 21px lh1.5 ls−0.2 `#6e6e73` max-w 420. 푸터는 left=688부터.

**05_feature_grid (parchment)** — 중앙 헤더 top96: kicker → h2 600 52px. 그리드 top300, left/right120, 3열(열폭 ≈ 320, gap 40, 열 중심 x ≈ 280/640/1000): 각 열 중앙 정렬 — 원 56px(`fill="#ffffff"` — 원본은 #f5f5f7이나 parchment 캔버스와 동색이라 흰 원으로 승격, spec에 명기) + 라인 아이콘 26px `stroke="#1d1d1f" stroke-width="1.5"` fill none round cap/join → 제목 600 26px lh1.12 ls−0.5 → 본문 400 17px lh1.5 ls−0.2 `#6e6e73` max-w 300. 아이콘 3종은 원본 HTML의 `<svg viewBox="0 0 24 24">` 패스 그대로 이식(반원/사각+가로선/상승꺾은선+베이스라인).

**06_stat (white)** — 중앙 헤더 top100: kicker → h2 600 52px. 스탯 3개 top330 중앙 flex: 각 셀 좌우 padding 64, 2·3번째 셀 왼쪽 세로 헤어라인(높이 ≈ 셀 높이), 값 `{{STAT_n_VALUE}}` 600 120px lh0.95 ls−4 잉크, 라벨 `{{STAT_n_LABEL}}` 400 19px lh1.4 ls−0.2 `#6e6e73` max-w 240 (값 아래 gap 16).

**07_quote (parchment)** — 중앙 스택(gap 44, 좌우 padding 140): 인용 `{{QUOTE}}` 600 60px lh1.1 ls−1.6 잉크 max-w 980, 유니코드 커리 따옴표(U+201C/U+201D) 포함 2행 → 이름 `{{ATTRIBUTION_NAME}}` 600 19px ls−0.3 잉크 + 직함 `{{ATTRIBUTION_ROLE}}` 400 15px ls−0.2 `#6e6e73` (gap 6).

**08_comparison (white)** — 중앙 헤더 top80: kicker → h2 600 52px. 2열 top266 left/right120 gap56(열폭 492, 열 x 120/676): 각 열 = imgph h180 rx12 → 옵션명 `{{OPTION_x_NAME}}` 600 34px lh1.1 ls−0.7 (gap 20) → 스펙 3행(행 상단 헤어라인, padding 14/0, 17px ls−0.374; 키 `#6e6e73` 좌, 값 600 잉크 우 anchor end).

**09_image (white)** — 중앙 헤더 top88(gap 14): kicker → h2 600 52px max-w 860. imgph x120 y270 w1040 h362 rx12 + **filter="url(#shadow-product)"** (이 덱에서 그림자가 존재하는 유일한 요소), 중앙 라벨.

**10_bar_chart (white)** — 헤더 top80 left/right120: 좌측 kicker+제목 600 44px lh1.08 ls−1, 우측 레전드 2항(스와치 16px rx4 `#1d1d1f`=Peak / `#c7c7cc`=others, 텍스트 400 15px `#6e6e73`). 플롯(원본 SVG를 +120,+250 평행이동해 캔버스 좌표로 이식): 그리드 가로선 5개 y=270/340/410/480/550, x=180→1160, `#e0e0e0`; y축 라벨 40/30/20/10/0 400 13px `#6e6e73` anchor end x=166; 바 6개 w112 rx4 x=224/376/528/680/832/984, 값 18/22/28/35/24/30 — 4번째(35)만 `#1d1d1f`, 나머지 `#c7c7cc`, 높이 = 값×7px, 바닥 y=550; 값 라벨 600 18px ls−0.3 잉크 바 위 14px; 월 라벨 Jan~Jun 13px y=578. 차트 그룹 직전에 `<!-- chart-plot-area: 180,270,1160,550 -->`.

**11_line_chart (white)** — 헤더/그리드/축은 10과 동일 기하(y축 라벨 100/75/50/25/0). 레전드: 26px 선 스와치 — solid 3px `#1d1d1f` "This year" / dashed `#6e6e73` "Last year". 시리즈(캔버스 좌표): dashed polyline `stroke="#6e6e73" stroke-width="3" stroke-dasharray="7 6"` points `302,500 547,460 792,455 1037,400`; solid polyline `stroke="#1d1d1f" stroke-width="3.5"` points `302,480 547,410 792,370 1037,302` + 데이터 점 r5 `#1d1d1f` 4개(동일 좌표). 분기 라벨 Q1~Q4 x=302/547/792/1037 y=580. 마커 `<!-- chart-plot-area: 180,270,1160,550 -->`.

**12_donut_chart (white)** — 헤더 top80 left/right120(제목 44px). 도넛: 중심 (330,420), 반지름 136(스케일 340/300 반영), 스트로크 폭 52, 4개 `<circle fill="none">` — `#1d1d1f` 45% / `#6e6e73` 30% / `#c7c7cc` 17% / `#d2d2d7` 8%, `stroke-dasharray="<비율×854.5> 854.5"`(둘레 2π×136≈854.5) + 누적 `stroke-dashoffset`, 그룹 `transform="rotate(-90 330 420)"`. 중앙 `{{DONUT_CENTER_VALUE}}` 600 52px ls−1.5 + `{{DONUT_CENTER_LABEL}}` 400 15px `#6e6e73`. 레전드 x620~1160 top310, 행 4개(피치 ≈ 46px): 스와치 16 rx4 + 이름 600 22px ls−0.4 잉크 + 값 400 18px `#6e6e73` 우측 anchor end. 마커 `<!-- chart-plot-area: donut | center: 330,420 | outer-radius: 162 | inner-radius: 110 -->`.

**13_closing (parchment)** — 중앙 스택(gap 28): `{{BRAND_MARK}}` 600 104px ls−3 잉크 → 클로징 카피 `{{CLOSING_LINE}}` 300 26px lh1.4 `#6e6e73` max-w 560 (2행). 푸터: 중앙 정렬 단일 텍스트 `{{CONTACT_LINE}}` 400 12px `#7a7a7a`.

---

### Task 1: 원본 레퍼런스 스크린샷 13장 렌더

**Files:**
- Create: `<scratchpad>/apple_ds_ref/render_ref.py`
- Create: `<scratchpad>/apple_ds_ref/<SlideName>.png` ×13

**Interfaces:**
- Produces: 이후 모든 SVG 태스크의 시각 대조 기준 PNG. 파일명 = HTML 파일명 그대로(`TitleSlide.png` 등).

- [x] **Step 1: 렌더 스크립트 작성**

`<scratchpad>`는 세션 스크래치패드 디렉터리(시스템 프롬프트에 명시된 경로)를 사용한다.

```python
# render_ref.py — 13개 슬라이드 HTML을 1280x720 PNG로 캡처
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC = Path(r"C:\Users\byung\Downloads\Apple Design System\slides")
OUT = Path(__file__).parent
SKIP = {"index.html"}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    for f in sorted(SRC.glob("*.html")):
        if f.name in SKIP:
            continue
        page.goto(f.as_uri())
        page.wait_for_timeout(400)  # @font-face 로드 대기
        page.screenshot(path=str(OUT / f"{f.stem}.png"),
                        clip={"x": 0, "y": 0, "width": 1280, "height": 720})
        print("captured", f.stem)
    browser.close()
```

- [x] **Step 2: 실행 및 검증**

Run: `python3 "<scratchpad>/apple_ds_ref/render_ref.py"`
Expected: `captured ...` 13행 출력, PNG 13개 생성.

- [x] **Step 3: 캡처 품질 확인**

`TitleSlide.png`와 `DonutChartSlide.png`를 Read(멀티모달)로 열어 텍스트/도형이 정상 렌더됐는지 확인. 빈 화면이면 `wait_for_timeout`을 1000으로 올려 재실행.

커밋 없음(repo 밖 산출물).

---

### Task 2: 템플릿 브리프 확정 게이트 — 사용자 체크포인트

**Files:** 없음 (대화 산출물)

**Interfaces:**
- Consumes: 스펙 §3–§4, 공통 팩트 시트, Task 1 스크린샷.
- Produces: `[TEMPLATE_BRIEF_CONFIRMED]` 선언 — Task 3 이후의 모든 최종 파일 쓰기 전제조건.

- [x] **Step 1: 브리프 요약 제시**

create-template.md Step 3 형식에 맞춰 사용자에게 제시: kind=deck, template_id=apple, scope=library, canvas=ppt169, 로스터 13장(팩트 시트 표), 아이덴티티 요약(모노크롬 팔레트/Pretendard 래더/단일 그림자), 대표 스크린샷 2~3장 첨부.

- [x] **Step 2: 사용자 확인 대기**

사용자가 승인하면 응답에 `[TEMPLATE_BRIEF_CONFIRMED]`를 명시하고 다음 태스크로. 수정 요청 시 브리프를 고쳐 재제시(최종 디렉터리는 아직 건드리지 않는다).

---

### Task 3: deck design_spec.md 작성

**Files:**
- Create: `.claude/skills/ppt-master/templates/decks/apple/templates/design_spec.md`

**Interfaces:**
- Consumes: 스펙 §2–§4, 공통 팩트 시트.
- Produces: 이후 SVG 태스크가 준수할 스펙 문서. frontmatter `deck_id: apple`, 로스터 파일명 13개(§VIII)는 SVG 태스크의 파일명과 정확히 일치해야 한다.

- [x] **Step 1: 프리플라이트 — 충돌 확인**

Run: `ls .claude/skills/ppt-master/templates/decks/apple 2>&1; ls .claude/skills/ppt-master/templates/brands/apple 2>&1`
Expected: 둘 다 "No such file or directory" (존재하면 중단하고 사용자에게 update/replace/새 id 질의 — create-brand.md 규칙).

- [x] **Step 2: 참조 문서 확인**

`templates/decks/mckinsey/templates/design_spec.md`(구조 모델)와 `templates/design_spec_reference.md`를 읽고 섹션 골격을 파악한다.

- [x] **Step 3: design_spec.md 작성**

frontmatter(정확히):

```yaml
---
deck_id: apple
kind: deck
native_structure_mode: structured
summary: Apple 계열 모노크롬 미니멀 키노트 — 제품 발표, 브랜드 스토리, 디자인 리뷰, 조용한 프리미엄 톤의 전략 브리핑
canvas_format: ppt169
page_count: 13
primary_color: "#1D1D1F"
---
```

본문 섹션(mckinsey 골격 준용): §I 개요(Vitrine 오리지널 시스템 출처 명기 — Apple 고유 자산 아님, 워드마크/로고 미포함), §II 캔버스, §III 컬러(Global Constraints의 허용 HEX 표 + 악센트 금지 + "강조 = 서피스 반전" 규칙), §IV 타이포(Pretendard 래더 300/400/600/700·500 금지·원본 자간 표 + **한글 자간 ½ 완화 규칙**), §V 페이지 구조(마진·푸터 크롬·white/parchment 교대 리듬), §VI 페이지 타입(13종 각 1문단), §VII 시각화 방침(모노크롬 차트 문법: 단일 강조=최농도 잉크 1개, 나머지 그레이 래더 `#6e6e73→#c7c7cc→#d2d2d7`, 헤어라인 그리드, chart-design 스킬 연동), §VIII SVG 로스터(01_title~13_closing 파일명+용도 표), §IX 스페이싱(8px 베이스, 페이지별 마진 표), §X Placeholder(imgph = `ltUpDiag` 프리셋 해칭 패턴, 실사진 교체 지점, 라벨 리터럴 규칙), §XI 아이콘(씬 모노라인 1.5px round, 콘텐츠 타일 최소주의), §XII 보이스&톤(선언형 헤드라인+마침표 케이던스, 문장 케이스, 이모지 금지), §XIII 안티패턴 체크리스트(악센트색/500웨이트/카드 그림자/그라디언트/Title Case/이모지).

- [x] **Step 4: 스펙 대조 검증**

design_spec.md의 로스터 파일명 13개가 이 계획의 File Structure와 1:1인지, frontmatter 7개 필드가 위와 정확히 같은지 눈으로 검증.

- [x] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/design_spec.md
git commit -m "apple deck: design spec (Vitrine monochrome port, 13-page roster)"
```

---

### Task 4: 공통 SVG 계약 확립 + 01_title.svg

**Files:**
- Create: `.claude/skills/ppt-master/templates/decks/apple/templates/01_title.svg`

**Interfaces:**
- Produces: 이후 모든 SVG가 복제할 **공통 계약**: 루트 속성 `data-pptx-master="apple-master" data-pptx-master-name="Apple"` + 페이지별 `data-pptx-layout`/`data-pptx-layout-name`, master 레이어(`id="master-bg"` 흰 rect, `data-pptx-layer="master" data-pptx-editable="false"`), 푸터 크롬, title placeholder slot 패턴.

- [x] **Step 1: 저작 규칙 확인**

`references/template-designer.md`와 `references/shared-standards.md` §6.4(그림자)·§7(구조 메타데이터)을 읽는다. mckinsey `01_cover.svg`를 참조 모델로 연다.

- [x] **Step 2: 01_title.svg 작성**

아래 코드를 기준으로 작성(baseline은 Step 3에서 보정):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" data-pptx-master="apple-master" data-pptx-master-name="Apple" data-pptx-layout="01_title" data-pptx-layout-name="Title">
  <!-- Apple (Vitrine monochrome) — 01 Title -->

  <rect id="master-bg" width="1280" height="720" fill="#FFFFFF" data-pptx-layer="master" data-pptx-editable="false"/>

  <g id="title-kicker">
    <text x="640" y="182" text-anchor="middle"
          font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
          font-size="14" letter-spacing="0.84"
          fill="#6e6e73">{{KICKER}}</text>
  </g>

  <g id="title-slot" data-pptx-placeholder="title" data-pptx-placeholder-bounds="100 219 1080 231">
    <text id="title-carrier" data-pptx-placeholder-carrier="true" x="640" y="306" text-anchor="middle"
          font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
          font-size="112" letter-spacing="-3"
          fill="#1d1d1f">{{TITLE}}</text>
  </g>

  <g id="subtitle-slot" data-pptx-placeholder="subtitle" data-pptx-placeholder-idx="2" data-pptx-placeholder-bounds="320 480 640 70">
    <text id="subtitle-carrier" data-pptx-placeholder-carrier="true" x="640" y="504" text-anchor="middle"
          font-family="'Pretendard Light', Pretendard, 'Malgun Gothic', sans-serif"
          font-size="28" letter-spacing="0.1"
          fill="#6e6e73">{{SUBTITLE}}</text>
  </g>

  <g id="page-foot">
    <text x="64" y="682"
          font-family="'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif"
          font-size="12" letter-spacing="-0.4"
          fill="#6e6e73">{{BRAND_MARK}}</text>
    <text x="1216" y="682" text-anchor="end"
          font-family="Pretendard, 'Malgun Gothic', sans-serif"
          font-size="12" letter-spacing="-0.12"
          fill="#7a7a7a">{{PAGE_LABEL}}</text>
  </g>
</svg>
```

토큰에는 원본 샘플 카피를 넣지 않는다 — `{{TOKEN}}` 그대로가 템플릿 계약이다(mckinsey 방식).

- [x] **Step 3: 렌더 대조**

Task 1 스크립트를 변형해 이 SVG를 PNG로 렌더(`page.goto(svg_path.as_uri())`)한 뒤 `TitleSlide.png`와 나란히 Read로 열어 비교. 기준: 세로 배치(키커/타이틀/서브 중심선), 마진, 크기 감각이 ±4px 이내. 어긋나면 y값 보정 후 재렌더.

- [x] **Step 4: 단일 파일 품질 확인**

Run: `python3 -c "import xml.dom.minidom,sys; xml.dom.minidom.parse('.claude/skills/ppt-master/templates/decks/apple/templates/01_title.svg'); print('well-formed')"`
Expected: `well-formed`

- [x] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/01_title.svg
git commit -m "apple deck: 01_title template (establishes master/layout contract)"
```

---

### Task 5: parchment 센터 3장 — 03_section, 07_quote, 13_closing

**Files:**
- Create: `templates/decks/apple/templates/03_section.svg`, `07_quote.svg`, `13_closing.svg` (전체 경로는 Task 4와 동일 디렉터리)

**Interfaces:**
- Consumes: Task 4의 공통 계약(루트 속성·master-bg·푸터 블록을 그대로 복제, `data-pptx-layout`만 페이지별로 변경).
- Produces: parchment 서피스 패턴 — master-bg 아래에 `<rect id="layout-bg-parchment" width="1280" height="720" fill="#f5f5f7" data-pptx-layer="layout" data-pptx-editable="false"/>`.

- [x] **Step 1: 03_section.svg 작성** — 팩트 시트 03 적용. 구조는 01_title과 동일 골격에서: parchment layout-bg 추가, kicker(y≈250)+`{{TITLE}}` 96px ls−2.6 title slot(2행 중앙, baseline ≈ 340/440), 푸터 `{{PAGE_LABEL}}`.

- [x] **Step 2: 07_quote.svg 작성** — 팩트 시트 07 적용: `{{QUOTE}}` 60px ls−1.6 title slot(중앙, max-w 980 → bounds "150 260 980 132"), 이름/직함 토큰 텍스트 2행(gap 6, 인용 아래 44px).

- [x] **Step 3: 13_closing.svg 작성** — 팩트 시트 13 적용: `{{BRAND_MARK}}` 104px ls−3 중앙(title slot), `{{CLOSING_LINE}}` 300 26px 2행, 푸터는 중앙 단일 `{{CONTACT_LINE}}`(x=640 anchor middle).

- [x] **Step 4: 렌더 대조** — 3장을 각각 렌더해 `SectionSlide.png`/`QuoteSlide.png`/`ClosingSlide.png`와 비교(±4px), well-formed 확인(Task 4 Step 4 명령을 파일별 반복).

- [x] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/0{3,7}_*.svg .claude/skills/ppt-master/templates/decks/apple/templates/13_closing.svg
git commit -m "apple deck: parchment centered pages (section, quote, closing)"
```

---

### Task 6: 리스트/지표 2장 — 02_agenda, 06_stat

**Files:**
- Create: `02_agenda.svg`, `06_stat.svg`

**Interfaces:**
- Consumes: Task 4 공통 계약.
- Produces: 헤어라인 행 패턴(agenda)과 세로 구분선 스탯 패턴(stat) — 08_comparison이 헤어라인 행 패턴을 재사용.

- [x] **Step 1: 02_agenda.svg 작성** — 팩트 시트 02 적용: 헤더(kicker y≈110, `{{TITLE}}` 52px title slot y≈180), 행 4개 — 각 행: `<line>` 헤어라인(x 120→1160, y=262/350/438/526) + `{{ITEM_n_TITLE}}` 600 36px(x=120, 헤어라인 아래 baseline +54) + `{{ITEM_n_TAG}}` 400 17px `#6e6e73`(x=1160 anchor end, 동일 baseline).

- [x] **Step 2: 06_stat.svg 작성** — 팩트 시트 06 적용: 중앙 헤더, 스탯 3셀(중심 x ≈ 320/640/960 — 렌더 대조로 보정), 셀 사이 세로 헤어라인 2개(y 330→560), `{{STAT_n_VALUE}}` 120px ls−4 + `{{STAT_n_LABEL}}` 19px max-w 240 중앙 정렬.

- [x] **Step 3: 렌더 대조 + well-formed** — `AgendaSlide.png`/`StatSlide.png` 대비.

- [x] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/02_agenda.svg .claude/skills/ppt-master/templates/decks/apple/templates/06_stat.svg
git commit -m "apple deck: agenda and stat pages"
```

---

### Task 7: 이미지 2장 — 04_split, 09_image (단일 그림자 도입)

**Files:**
- Create: `04_split.svg`, `09_image.svg`

**Interfaces:**
- Consumes: Task 4 공통 계약.
- Produces: imgph 플레이스홀더 패턴 + 시스템 유일 그림자 필터 `id="shadow-product"` — 08_comparison이 imgph(그림자 없는 변형)를 재사용.

- [x] **Step 1: 그림자 필터 정의(09에서만)**

```xml
<defs>
  <filter id="shadow-product" x="-15%" y="-20%" width="130%" height="150%">
    <feDropShadow dx="3" dy="5" stdDeviation="15" flood-color="#000000" flood-opacity="0.22"/>
  </filter>
</defs>
```

- [x] **Step 2: 04_split.svg 작성** — 팩트 시트 04: `<defs>`에 imgph-hatch 패턴(공통 팩트 시트 정의 그대로) → imgph rect(0,0,600,720, rx0, `fill="url(#imgph-hatch)"`, **그림자 없음** — 원본도 split은 무그림자) + 라벨 텍스트(x=300 y=364 middle), 우측 텍스트 스택(kicker/`{{TITLE}}` 56px title slot/`{{BODY}}` 300 21px), 푸터 좌단 x=688.

- [x] **Step 3: 09_image.svg 작성** — 팩트 시트 09: `<defs>`에 imgph-hatch 패턴 + shadow-product 필터 → 중앙 헤더 + imgph rect(120,270,1040,362, rx12, `fill="url(#imgph-hatch)"`) `filter="url(#shadow-product)"` + 라벨.

- [x] **Step 4: 렌더 대조 + well-formed** — `SplitSlide.png`/`ImageSlide.png` 대비. 그림자가 rect 아래·우측으로 부드럽게 퍼지는지 확인.

- [x] **Step 5: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/04_split.svg .claude/skills/ppt-master/templates/decks/apple/templates/09_image.svg
git commit -m "apple deck: split and image pages (single system shadow)"
```

---

### Task 8: 그리드/비교 2장 — 05_feature_grid, 08_comparison

**Files:**
- Create: `05_feature_grid.svg`, `08_comparison.svg`

**Interfaces:**
- Consumes: Task 4 공통 계약, Task 5 parchment 패턴(05), Task 6 헤어라인 행 + Task 7 imgph 패턴(08).

- [x] **Step 1: 05_feature_grid.svg 작성** — 팩트 시트 05: parchment layout-bg, 중앙 헤더, 3열(중심 x=280/640/1000) — 각 열: `<circle r="28" fill="#ffffff">` + 원본 24×24 아이콘 패스를 26px로 스케일(`transform="translate(cx-13, y) scale(1.0833)"`, stroke 1.5 round) + `{{FEAT_n_TITLE}}` 600 26px + `{{FEAT_n_BODY}}` 400 17px max-w 300(2~3행 tspan). 원본 아이콘 패스 3종은 `FeatureGridSlide.html` 26~38행에서 그대로 복사.

- [x] **Step 2: 08_comparison.svg 작성** — 팩트 시트 08: `<defs>`에 imgph-hatch 패턴 → 중앙 헤더, 2열(x=120/676, 폭 492) — 각 열: imgph(h180 rx12, `fill="url(#imgph-hatch)"`, 그림자 없음) + `{{OPTION_x_NAME}}` 600 34px + 스펙 3행(헤어라인 + `{{SPEC_x_n_KEY}}` `#6e6e73` / `{{SPEC_x_n_VALUE}}` 600 잉크 anchor end).

- [x] **Step 3: 렌더 대조 + well-formed** — `FeatureGridSlide.png`/`ComparisonSlide.png` 대비.

- [x] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/05_feature_grid.svg .claude/skills/ppt-master/templates/decks/apple/templates/08_comparison.svg
git commit -m "apple deck: feature grid and comparison pages"
```

---

### Task 9: 차트 3장 — 10_bar_chart, 11_line_chart, 12_donut_chart

**Files:**
- Create: `10_bar_chart.svg`, `11_line_chart.svg`, `12_donut_chart.svg`

**Interfaces:**
- Consumes: Task 4 공통 계약. 원본 HTML의 인라인 SVG(BarChart 28~53행, LineChart 28~47행, DonutChart 23~34행)를 캔버스 좌표로 평행이동해 이식.
- Produces: `chart-plot-area` 마커 3개 — verify-charts 워크플로와 chart-design 스킬이 소비.

- [x] **Step 1: 10_bar_chart.svg 작성** — 팩트 시트 10의 좌표 그대로. 차트 요소 전체를 `<g id="chart-body">`로 묶고 그룹 직전 줄에 `<!-- chart-plot-area: 180,270,1160,550 -->`. 샘플 데이터(18/22/28/35/24/30, Jan~Jun)는 실데이터 교체 전 시연용으로 유지. 헤더 제목은 `{{TITLE}}` title slot, 레전드 라벨은 `{{LEGEND_PEAK}}`/`{{LEGEND_OTHERS}}`.

- [x] **Step 2: 11_line_chart.svg 작성** — 팩트 시트 11 좌표 그대로(dashed 먼저, solid+점 나중 = 원본 페인트 순서). 레전드 라벨 토큰은 `{{LEGEND_SERIES_A}}`(solid)/`{{LEGEND_SERIES_B}}`(dashed). 마커 동일 형식.

- [x] **Step 3: 12_donut_chart.svg 작성** — 팩트 시트 12: dasharray 값 계산 — 둘레 854.5 기준 45%=384.5 / 30%=256.4 / 17%=145.3 / 8%=68.4, offset 누적 0/−384.5/−640.9/−786.1(음수, 원본 방식). 그룹 `transform="rotate(-90 330 420)"`. 레전드 행 4개 토큰(`{{SEG_n_NAME}}`/`{{SEG_n_VALUE}}`). 도넛 마커는 팩트 시트의 donut 형식 그대로.

- [x] **Step 4: 마커 존재 검증**

Run: `grep -c "chart-plot-area" .claude/skills/ppt-master/templates/decks/apple/templates/1{0,1,2}_*.svg`
Expected: 각 파일 1.

- [x] **Step 5: 렌더 대조 + well-formed** — 3장을 원본 PNG와 대비. 특히 도넛 세그먼트 시작각(12시)과 바 차트 피크 강조 확인.

- [x] **Step 6: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/1{0,1,2}_*.svg
git commit -m "apple deck: chart pages with chart-plot-area markers"
```

---

### Task 10: 전체 로스터 검증 및 수정

**Files:**
- Modify: 검증에서 걸린 SVG / design_spec.md

**Interfaces:**
- Consumes: 13장 전체 + design_spec.md.
- Produces: 체커 통과 상태의 로스터 — Task 11 등록 전제조건.

- [x] **Step 1: 품질 체커 실행**

Run: `python3 .claude/skills/ppt-master/scripts/svg_quality_checker.py ".claude/skills/ppt-master/templates/decks/apple/templates" --template-mode --format ppt169`
Expected: 오류 0. 오류 발생 시 메시지 단위로 수정 → 재실행 루프.

- [x] **Step 2: 금지 패턴 grep 스위프**

```bash
grep -rn 'font-weight="500"\|Pretendard Medium' .claude/skills/ppt-master/templates/decks/apple/templates/ ; \
grep -rln "feDropShadow" .claude/skills/ppt-master/templates/decks/apple/templates/ | grep -v 09_image ; \
grep -rhoE '(fill|stroke|flood-color)="#[0-9a-fA-F]+"' .claude/skills/ppt-master/templates/decks/apple/templates/*.svg | sort -u
```
Expected: 첫째·둘째 명령 출력 0행(= 500 웨이트 없음, 그림자는 09_image에만). 셋째 명령의 유니크 색 목록이 Global Constraints 허용 HEX 15종의 부분집합인지 눈으로 대조(대소문자 무시).

- [x] **Step 3: 13장 일괄 렌더 시각 대조** — 13장 SVG를 모두 렌더해 원본 PNG와 페이지별 비교. 스펙 §6 기준: 서피스 모드/골격/타이포 위계/모노크롬/차트 문법 보존.

- [x] **Step 4: Commit (수정이 있었다면)**

```bash
git add .claude/skills/ppt-master/templates/decks/apple/templates/
git commit -m "apple deck: quality-checker and visual-parity fixes"
```

---

### Task 11: deck 등록

**Files:**
- Modify: `.claude/skills/ppt-master/templates/decks/decks_index.json` (스크립트가 수정)

- [x] **Step 1: dry-run**

Run: `python3 .claude/skills/ppt-master/scripts/register_template.py apple --kind deck --dry-run`
Expected: apple 항목 추가 미리보기(summary/canvas_format/page_count=13/primary_color="#1D1D1F").

- [x] **Step 2: 등록 실행**

Run: `python3 .claude/skills/ppt-master/scripts/register_template.py apple --kind deck`
Expected: decks_index.json에 apple 항목 기록.

- [x] **Step 3: 검증**

Run: `python3 -c "import json;print(json.load(open('.claude/skills/ppt-master/templates/decks/decks_index.json',encoding='utf-8'))['apple'])"`
Expected: `{'summary': ..., 'canvas_format': 'ppt169', 'page_count': 13, 'primary_color': '#1D1D1F'}` (인덱스는 `deck_id → dict` 평면 구조).

- [x] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/templates/decks/decks_index.json
git commit -m "apple deck: register in decks index"
```

---

### Task 12: brand 추출본 작성 및 등록

**Files:**
- Create: `.claude/skills/ppt-master/templates/brands/apple/templates/design_spec.md`
- Modify: `.claude/skills/ppt-master/templates/brands/brands_index.json` (스크립트가 수정)

**Interfaces:**
- Consumes: Task 3의 deck design_spec.md 아이덴티티 세그먼트(§III 컬러/§IV 타이포/§XII 보이스/§XI 아이콘).

- [x] **Step 1: create-brand 규칙 확인** — `workflows/create-brand.md`의 Step 4(스펙 작성)와 기존 `templates/brands/anthropic/templates/design_spec.md`(형식 모델)를 읽는다.

- [x] **Step 2: brand design_spec.md 작성**

frontmatter: `brand_id: apple` / `kind: brand` / `summary: Apple 계열 모노크롬 미니멀 아이덴티티 — 잉크 단일 시그널, 서피스 반전 강조, 조용한 프리미엄 보이스` / `primary_color: "#1D1D1F"`.

필수 6섹션: §I Brand Overview(Vitrine 출처 + deck `templates/decks/apple/`과의 쌍 관계 명기), §II Color Scheme(deck §III에서 이관, 전 필드 provenance `[fact]` — colors_and_type.css 직독), §III Typography(Pretendard 래더 + 자간 규칙 + 한글 완화), §IV Logo(로고 파일 미보유 — `{{BRAND_MARK}}` 텍스트 슬롯 운용 명기), §V Voice & Tone(선언형·마침표 케이던스·문장 케이스·이모지 금지), §VI Icon Style(씬 모노라인 1.5px round).

- [x] **Step 3: 등록 및 검증**

Run: `python3 .claude/skills/ppt-master/scripts/register_template.py apple --kind brand --dry-run` → 확인 후 `python3 .claude/skills/ppt-master/scripts/register_template.py apple --kind brand`
Expected: brands_index.json에 apple 항목.

- [x] **Step 4: Commit**

```bash
git add .claude/skills/ppt-master/templates/brands/apple/ .claude/skills/ppt-master/templates/brands/brands_index.json
git commit -m "apple brand: identity preset extracted from apple deck"
```

---

### Task 13: 수용 기준 최종 체크

**Files:** 없음 (검증만)

- [x] **Step 1: 스펙 §6 체크리스트 실행** — 6개 항목을 하나씩 확인하고 결과를 사용자에게 보고:
1. 품질 체커 오류 0 (Task 10 Step 1 재실행)
2. 13장 시각 대조 통과 (Task 10 Step 3 결과 인용)
3. 그림자 = 09_image 1곳뿐 (Task 10 Step 2 grep 재실행)
4. 웨이트 500 / 악센트색 / 이모지 = 0 (동일 grep)
5. 양쪽 인덱스에 apple 등록 (Task 11/12 Step 3 재실행)
6. 워크스페이스 계약: `templates/design_spec.md` + SVG 13장 존재, `images/`·`icons/`·`exports/` 부재 확인 — `ls .claude/skills/ppt-master/templates/decks/apple/ .claude/skills/ppt-master/templates/decks/apple/templates/`

- [x] **Step 2: 미충족 항목이 있으면** 해당 태스크로 돌아가 수정 후 재검증. 전부 통과면 완료 보고(등록된 두 인덱스 항목과 대표 렌더 2장 첨부).
