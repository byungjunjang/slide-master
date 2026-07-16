---
deck_id: apple
kind: deck
native_structure_mode: structured
summary: Apple 계열 모노크롬 미니멀 키노트 — 제품 발표, 브랜드 스토리, 디자인 리뷰, 조용한 프리미엄 톤의 전략 브리핑
canvas_format: ppt169
page_count: 13
primary_color: "#1D1D1F"
---

# Apple Monochrome Keynote Deck - Design Specification

> Ported 2026-07-16 from the **Vitrine** design system (an original photography-first minimalist system built on widely-used, non-proprietary Apple-adjacent principles — not a recreation of Apple's branded product or proprietary UI). No trademark assets, logos, or wordmarks are bundled; the source's own placeholder wordmark is replaced by a `{{BRAND_MARK}}` text slot. Typography follows this repository's install-local Pretendard lock, reproducing the tight-tracking cadence through weight/size only — SF Pro is not used.

---

## I. Template Overview

| Property | Description |
| --- | --- |
| **Template Name** | apple |
| **Display Name** | Apple Monochrome Keynote Deck |
| **Use Cases** | 제품 발표, 브랜드 스토리, 디자인 리뷰, 비전 키노트, 조용한 프리미엄 톤의 전략 브리핑 |
| **Design Tone** | Reverent, premium, unhurried — museum-gallery quiet. The page reads, it doesn't scan |
| **Theme Mode** | Light only — white canvas with parchment (`#f5f5f7`) alternation |

**Anti-mood** (reject at design time): "gradient SaaS dashboard", "consulting density grid", "decorative infographics", "emoji-flecked marketing deck", "rainbow category palette".

**Litmus test**: 페이지에서 색을 모두 제거해도 위계가 그대로면 통과 — 이 덱은 애초에 무채색이므로, 강조가 서피스 반전과 웨이트만으로 서 있는지 확인한다. Whitespace is the pedestal; 여백을 채우고 싶은 충동은 거절한다.

**Companion brand**: identity-only 사용은 [`templates/brands/apple/`](../../../brands/apple/) — 동일 아이덴티티를 페이지 로스터 없이 잠근다.

---

## II. Canvas Specification

| Property | Value |
| --- | --- |
| **Format** | Standard 16:9 (`ppt169`) |
| **Dimensions** | 1280 × 720 px |
| **viewBox** | `0 0 1280 720` |
| **Footer chrome** | Left mark x=64, right label x=1216, baseline y=682 — 전 페이지 고정 |
| **Content margins** | 페이지 유형별로 상이: 센터 페이지는 좌우 100–140px 텍스트 폭 제한, 리스트/그리드/차트 페이지는 좌우 120px |

Geometry is a 1:1 mapping of the source's 1280×720 slide viewport — no rescaling. 소스의 8px 스페이싱 베이스(4·8·12·17·24·32·48·80)를 그대로 승계한다.

---

## III. Color Scheme — LOCKED

Pure monochrome. **악센트 컬러가 존재하지 않는다.** 어떤 생성 SVG에도 아래 15개 외의 HEX가 나타나서는 안 된다:

| Role | HEX | Token | Purpose |
| --- | --- | --- | --- |
| Canvas | `#ffffff` | `--canvas` | 지배적 라이트 캔버스 (9/13 페이지) |
| Pearl | `#fafafc` | `--pearl` | 니어-화이트 고스트 필 (희소) |
| Parchment | `#f5f5f7` | `--parchment` | 시그니처 오프화이트 — 교대 타일 서피스, 이미지 플레이스홀더 배경 |
| Hatch fg | `#ececef` | `--hatch-fg` | 이미지 플레이스홀더 해칭 전경 |
| Hairline | `#e0e0e0` | `--hairline` | 1px 카드/행/차트 그리드 보더 |
| Chart tint 4 | `#d2d2d7` | `--tint-4` | 차트 래더 최희석 단계 |
| Chart tint 3 | `#c7c7cc` | `--tint-3` | 차트 래더 — 비강조 바/세그먼트 |
| Label muted | `#a8a8ad` | `--label-muted` | 플레이스홀더 안내 라벨 |
| Ink muted 48 | `#7a7a7a` | `--ink-muted-48` | 푸터 페이지 라벨, legal fine-print |
| Ink muted 60 | `#6e6e73` | `--ink-muted-60` | 키커, 본문 보조, 축 라벨, 푸터 마크 |
| Ink muted 80 | `#333333` | `--ink-muted-80` | pearl 서피스 위 완화 본문 (희소) |
| Tile dark 2 | `#272729` | `--tile-dark-2` | 다크 타일 마이크로스텝 (이 로스터 미사용, 확장용) |
| Ink | `#1d1d1f` | `--ink` | 헤드라인·본문·차트 단일 강조 — 시스템의 유일한 시그널 |
| Tile dark 3 | `#161617` | `--tile-dark-3` | 다크 타일 마이크로스텝 (이 로스터 미사용, 확장용) |
| Black | `#000000` | `--black` | 풀블리드 포토그래픽 보이드 전용 — 텍스트 색으로 절대 사용 금지 |

**Provenance**: 전 값 `fact` — 소스 `colors_and_type.css` 직독. 원본 브리프의 블루 악센트는 모노크롬 빌드에서 이미 제거된 상태이며, 이 이식본도 복원하지 않는다.

### Color Rules

- **One ink, one signal**: `#1d1d1f`가 라이트 서피스 위 모든 강조를 담당한다. 인터랙티브/강조 신호에 색상(hue)은 존재하지 않는다
- **강조는 서피스 반전이 먼저**: 크롬을 추가하기 전에 서피스를 바꾼다(white ↔ parchment). 그래도 부족하면 웨이트를 올린다. 세 번째 수단은 없다
- **Grayscale-native**: 이 시스템은 처음부터 무채색이므로 "그레이스케일에서 읽히는가" 테스트는 자동 통과 — 대신 **여백 테스트**를 적용한다(요소를 하나 빼도 의미가 유지되면 뺀다)
- **차트 래더**: 다계열 차트는 `#1d1d1f → #6e6e73 → #c7c7cc → #d2d2d7` 순서. 최농도 잉크는 페이지의 **단일 강조 1개**(피크 바 / 주 계열 / 최대 세그먼트)에만 부여하고 나머지는 그레이 래더로 내린다
- **본문 뮤트는 `#6e6e73`**: 보조 카피·축 라벨·키커의 기본값. `#7a7a7a`는 푸터 라인 전용
- **Forbidden**: 악센트 컬러, 그라디언트(`<linearGradient>` / `<radialGradient>`) 장식, 글로우, 3D 효과, 유채색 일체

---

## IV. Typography System

Install-local Pretendard lock (see `references/strategist.md` §g). SF Pro Display의 타이트 케이던스를 Pretendard로 재현한다 — Pretendard는 본래 Apple 시스템 폰트의 크로스플랫폼 대체로 설계되어 외형 친화도가 높다. 중간 웨이트는 설치 패밀리명 + normal weight로 저작한다:

| Weight | `font-family` attribute | `font-weight` |
| --- | --- | --- |
| 300 | `'Pretendard Light', Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 400 | `Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 600 | `'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 700 | `Pretendard, 'Malgun Gothic', sans-serif` | `700` |

**웨이트 래더는 300 / 400 / 600 / 700 네 단계뿐이다. 500(`'Pretendard Medium'`)은 의도적으로 부재하며 사용 금지.** 헤드라인은 **600**이지 700이 아니다 — 700은 이 로스터에 등장하지 않는 예비 단계다. 300은 실재하지만 희소하다(에어리 리드, 클로징 카피).

### 🔒 본문 baseline 락 — 이 램프가 `delivery_purpose` 기본값보다 **우선한다**

**이 템플릿의 본문 baseline은 `17`이다.** Strategist는 확인 단계(Stage 2)에서 `delivery_purpose`의 일반 기본값(`text` 20 / `balanced` 24 / `presentation` 32)이 아니라 **아래 네이티브 램프를 추천값으로 제시**해야 한다. 사용자가 명시적으로 다른 값을 확정하면 그 값이 이긴다(확정값 우선 규칙은 그대로).

**근거 — 이 시스템의 정체성은 크기가 아니라 대비다.** 페이지 타이틀:본문 = **52/17 ≈ 3.1배**, 커버:본문 = **112/17 ≈ 6.6배**. 거대한 디스플레이와 작은 본문 사이의 이 격차가 "조용한 갤러리"를 만든다. 본문만 일반 기본값(24)으로 부풀리면 디스플레이 슬롯은 그대로인 채 대비가 **1.8배로 붕괴**하고, 덱 전체가 중간 크기로 수렴해 **촌스럽게 읽힌다** — 실제로 2026-07-16 생성분에서 이 현상이 재현되어 사용자 피드백으로 확인됐다(본문 17→22 +29%, 분할 본문 21→30 +43%, 대비 3.1→1.8배).

| 상황 | 처방 |
| --- | --- |
| `delivery_purpose: text` / `balanced` | 본문 **17** — 네이티브 그대로. 이 덱은 본문 텍스트 자체가 희소해서 17로 충분히 읽힌다 |
| `delivery_purpose: presentation` (대형 투사) | 본문 최대 **20**까지만 올리고, **동시에 페이지 타이틀을 60·커버를 128로 올려 대비 3.1배/6.4배를 유지**한다. 본문만 올리는 것은 금지 |
| 사용자가 24 이상을 명시 확정 | 확정값을 따르되, 대비가 무너진다는 점과 타이틀 동반 상향을 §8 핸드오프에서 고지한다 |

> **checker 관련**: 이 램프는 시스템의 일반 비율 밴드(페이지 타이틀 1.5–2×, 커버 2.5–5×)를 의도적으로 벗어난다(커버 6.6×, 지표 7.1×). `svg_quality_checker`는 `spec_lock.typography`에 **선언된 슬롯을 드리프트 검사에서 면제**하므로(0.5–5.0× 봉투는 미선언 중간값에만 적용), 아래 슬롯을 전부 `spec_lock`에 명시 선언하면 대비를 유지한 채 통과한다. 선언을 빠뜨리면 봉투에 걸린다.

Type scale (소스 인라인 스타일 직독 — **이것이 이 템플릿의 램프 truth**):

| Role | Size (px) | Weight | Line-height | Letter-spacing | Use |
| --- | --- | --- | --- | --- | --- |
| Hero | 112 | 600 | 1.03 | -3 | 타이틀 페이지 초대형 헤드라인 |
| Closing mark | 104 | 600 | 1.0 | -3 | 클로징 브랜드 마크 |
| Stat | 120 | 600 | 0.95 | -4 | 지표 페이지 대형 숫자 |
| Section | 96 | 600 | 1.04 | -2.6 | 챕터 헤드라인 |
| Quote | 60 | 600 | 1.10 | -1.6 | 풀-인용 |
| Split head | 56 | 600 | 1.05 | -1.4 | 분할 페이지 헤드라인 |
| Page head | 52 | 600 | 1.06 | -1.2 | 표준 페이지 제목 (agenda/grid/stat/comparison/image) |
| Chart head | 44 | 600 | 1.08 | -1 | 차트 페이지 제목 |
| List item | 36 | 600 | 1.0 | -0.8 | 아젠다 항목 |
| Option name | 34 | 600 | 1.10 | -0.7 | 비교 옵션명 |
| Lead | 28 | 300 | 1.25 | +0.1 | 타이틀 서브카피 (에어리) |
| Closing lead | 26 | 300 | 1.40 | 0 | 클로징 카피 |
| Feature head | 26 | 600 | 1.12 | -0.5 | 그리드 카드 제목 |
| Legend name | 22 | 600 | 1.0 | -0.4 | 도넛 레전드 항목명 |
| Body airy | 21 | 300 | 1.50 | -0.2 | 분할 페이지 본문 |
| Stat label | 19 | 400 | 1.40 | -0.2 | 지표 설명 |
| Attribution | 19 | 600 | 1.0 | -0.3 | 인용 출처 이름 |
| Chart value | 18 | 600 | 1.0 | -0.3 | 바 값 라벨 |
| Legend value | 18 | 400 | 1.0 | -0.3 | 도넛 레전드 수치 |
| Body | 17 | 400 | 1.50 | -0.374 | 기본 본문·스펙 행 (16px이 아니라 17px — 읽는 속도를 정하는 1px) |
| Caption | 15 | 400 | 1.0 | -0.2 | 차트 레전드 캡션, 직함, 도넛 중앙 라벨 |
| Kicker | 14 | 600 | 1.29 | +0.84 | 대문자 키커 (라벨 텍스트를 SVG에 이미 대문자로 저작) |
| Axis | 13 | 400 | 1.0 | -0.1 | 차트 축 라벨 |
| Footer | 12 | 600(mark) / 400(label) | 1.0 | -0.4 / -0.12 | 푸터 마크·페이지 라벨 |
| Placeholder | 12 | 400 | 1.0 | -0.08 | 이미지 플레이스홀더 안내 라벨 |

### 자간 규칙 — 라틴 기준값과 한글 완화

위 표의 `letter-spacing`은 **라틴 기준값**이다(원본이 영문 조판). 한글 위주 텍스트 런에는 **약 ½로 완화**한다 — 한글은 글리프 폭이 균일해 라틴과 같은 음수 자간을 주면 자소가 붙어 읽힌다.

| 텍스트 성격 | 적용 |
| --- | --- |
| 라틴/숫자 전용 런 | 표의 값 그대로 (예: 112px → `-3`) |
| 한글 위주 런 (한글 비중 ≥ 50%) | 표의 값 × 0.5 (예: 112px → `-1.5`, 52px → `-0.6`, 17px → `-0.19`) |
| 혼합 런 | 지배 언어 기준 1개 값을 런 전체에 적용 — `<tspan>`별로 자간을 쪼개지 않는다 |

양수 자간(키커 `+0.84`, 리드 `+0.1`)은 언어와 무관하게 그대로 유지한다.

---

## V. Page Structure

### 서피스 리듬

13장은 전부 라이트 모드다. white 9장과 parchment(`#f5f5f7`) 4장이 교대하며, **서피스 전환 자체가 구분선**이다 — 페이지 경계에 선이나 그림자를 넣지 않는다.

| Surface | Pages |
| --- | --- |
| white (`#ffffff`) | 01_title · 02_agenda · 04_split · 06_stat · 08_comparison · 09_image · 10_bar_chart · 11_line_chart · 12_donut_chart |
| parchment (`#f5f5f7`) | 03_section · 05_feature_grid · 07_quote · 13_closing |

parchment 페이지는 master-bg(흰 rect) **위에** layout 레이어 rect로 얹는다:

```xml
<rect id="master-bg" width="1280" height="720" fill="#FFFFFF" data-pptx-layer="master" data-pptx-editable="false"/>
<rect id="layout-bg-parchment" width="1280" height="720" fill="#f5f5f7" data-pptx-layer="layout" data-pptx-editable="false"/>
```

### 공통 크롬 — 푸터

```
┌──────────────────────────────────────────────────┐
│                                                  │
│              (페이지별 콘텐츠 영역)                │
│                                                  │
│ {{BRAND_MARK}} (x=64, 600/12/-0.4, #6e6e73)      │
│                  {{PAGE_LABEL}} (x=1216, anchor  │
│                  end, 400/12/-0.12, #7a7a7a)     │
│                            baseline y=682        │
└──────────────────────────────────────────────────┘
```

- 04_split은 이미지가 좌측 600px를 점유하므로 푸터 마크가 x=688에서 시작한다
- 13_closing은 좌우 2분할 대신 중앙 단일 `{{CONTACT_LINE}}`(x=640, anchor middle)을 쓴다
- 푸터에 로고 이미지는 없다 — `{{BRAND_MARK}}`는 순수 텍스트 슬롯

### 페이지 해부 — 센터 페이지 (01/03/07/13)

```
┌──────────────────────────────────────────────────┐
│                                                  │
│                  KICKER (600/14/+0.84 upper)     │
│                                                  │
│              HEADLINE (600, 96–112px, 음수 자간)   │
│                                                  │
│                  lead copy (300, 26–28px)        │
│                                                  │
│ {{BRAND_MARK}}                    {{PAGE_LABEL}} │
└──────────────────────────────────────────────────┘
```

### 페이지 해부 — 헤더+바디 페이지 (02/05/06/08/09/10/11/12)

```
┌──────────────────────────────────────────────────┐
│ KICKER            (y≈110)  600/14 #6e6e73        │
│ PAGE HEAD         (y≈180)  600/52 (차트는 44)     │
│                                                  │
│ 바디 (y≈262–600) — 리스트 / 그리드 / 차트 / 이미지  │
│                                                  │
│ {{BRAND_MARK}}                    {{PAGE_LABEL}} │
└──────────────────────────────────────────────────┘
```

헤더 정렬은 페이지 성격을 따른다: 중앙 정렬(05/06/08/09), 좌측 정렬(02/10/11/12).

---

## VI. Page Types

### 1. Title (01_title.svg) — white

중앙 수직 스택: 키커 → 112px 헤드라인(2행) → 300 웨이트 28px 서브카피(2행). 덱 전체에서 가장 큰 타입이 놓이는 유일한 페이지. 헤드라인은 선언문이며 마침표로 끝난다.

### 2. Agenda (02_agenda.svg) — white

좌측 정렬 헤더 + 헤어라인으로 구분된 4개 항목 행. 각 행은 제목(600/36, 좌)과 분류 태그(400/17 `#6e6e73`, 우)의 baseline 정렬. 번호를 붙이지 않는다 — 헤어라인이 리듬을 만든다.

### 3. Section (03_section.svg) — parchment

챕터 전환. 키커(챕터 번호/이름) + 96px 헤드라인(2행)만. 서피스가 white에서 parchment로 바뀌는 것이 챕터 경계 신호다.

### 4. Split (04_split.svg) — white

좌 600px 풀블리드 이미지 / 우 텍스트. 이미지는 캔버스 가장자리까지 닿고 라운딩이 없다(풀블리드 문법 = rx 0). 텍스트 칼럼은 수직 중앙 정렬, 본문은 300 웨이트 21px.

### 5. Feature Grid (05_feature_grid.svg) — parchment

3열 원칙 카드. 각 열: 흰 원(r=28) 안의 씬 라인 아이콘 → 600/26 제목 → 400/17 본문(max 300px). 이 로스터에서 아이콘이 등장하는 **유일한** 페이지 — 나머지는 타입과 여백이 일한다.

### 6. Stat (06_stat.svg) — white

3-up 지표. 120px 숫자 + 19px 라벨, 셀 사이 세로 헤어라인. 숫자는 장식이 아니라 무게를 지닌 값만 올린다(stat-slop 금지).

### 7. Quote (07_quote.svg) — parchment

중앙 풀-인용. 60px 600 인용문(커리 따옴표 U+201C/U+201D 포함) + 이름(600/19)/직함(400/15). 인용부호 장식 그래픽을 넣지 않는다.

### 8. Comparison (08_comparison.svg) — white

2-up 스펙 비교. 각 열: 이미지(h180, rx12) → 옵션명(600/34) → 헤어라인 스펙 3행(키 `#6e6e73` 좌 / 값 600 잉크 우). 승자를 색으로 표시하지 않는다 — 값의 웨이트가 이미 위계다.

### 9. Image (09_image.svg) — white

헤드라인 + 대형 이미지. **시스템 유일 그림자가 존재하는 페이지** — 이미지가 캔버스 위에 놓인 물리적 무게를 표현한다.

### 10. Bar Chart (10_bar_chart.svg) — white

월별 바 6개 + 레전드 2항. 피크 바만 잉크(`#1d1d1f`), 나머지는 `#c7c7cc`. 값 라벨을 바 위에 직접 얹어 축 읽기를 생략시킨다.

### 11. Line Chart (11_line_chart.svg) — white

2계열 추이. 주 계열 = 실선 3.5px 잉크 + 데이터 점, 비교 계열 = 점선 3px `#6e6e73`. 색이 아니라 선 스타일이 계열을 가른다.

### 12. Donut Chart (12_donut_chart.svg) — white

4세그먼트 도넛 + 중앙 합계 + 우측 레전드. 그레이스케일 래더 `#1d1d1f → #6e6e73 → #c7c7cc → #d2d2d7`, 12시에서 시계방향 시작(그룹 `rotate(-90)`).

### 13. Closing (13_closing.svg) — parchment

브랜드 마크(104px) + 300 웨이트 클로징 카피 + 중앙 정렬 연락처 푸터. CTA 버튼을 넣지 않는다.

---

## VII. Chart & Visualization Treatment

### 차트 문법

- **단일 강조 원칙**: 페이지당 최농도 잉크(`#1d1d1f`)는 **정확히 1개 대상**(피크 바 / 주 계열 / 최대 세그먼트)에만. 나머지는 `#6e6e73 → #c7c7cc → #d2d2d7` 래더로 내린다
- **그리드는 헤어라인**: 가로선 5개 `#e0e0e0` 1px. 세로 그리드·플롯 배경·축선 프레임은 넣지 않는다
- **축 라벨**: 400/13 `#6e6e73`. y축은 anchor end, x축은 anchor middle
- **값 직접 표기**: 바 차트는 값 라벨을 바 위에 얹어 축 스캔을 없앤다
- **레전드**: 우상단(바/라인) 또는 우측 열(도넛). 스와치는 16px rx4(면 계열) 또는 26px 선(라인 계열)
- **Forbidden**: 3D, 그림자, 그라디언트 필, 다색 카테고리 팔레트, 파이(도넛만), 유채색 강조

### chart-design 스킬 연동

차트 3장은 **샘플 데이터로 저작된 시연용 페이지**다. 실제 덱 생성 시 [`chart-design`](../../../../../chart-design/SKILL.md) 스킬이 이 덱의 `spec_lock.md` 토큰(위 팔레트 + 타이포)을 상속해 실데이터 차트로 교체한다.

각 차트 페이지는 `<!-- chart-plot-area: ... -->` 마커를 보유한다(executor-base.md §3.1) — verify-charts 워크플로와 `svg_position_calculator.py`가 이 마커를 읽는다:

| Page | Marker |
| --- | --- |
| 10_bar_chart | `<!-- chart-plot-area: 180,270,1160,550 -->` |
| 11_line_chart | `<!-- chart-plot-area: 180,270,1160,550 -->` |
| 12_donut_chart | `<!-- chart-plot-area: donut \| center: 330,420 \| outer-radius: 162 \| inner-radius: 110 -->` |

---

## VIII. SVG Page Roster

| File | Page Type | Surface | Purpose |
| --- | --- | --- | --- |
| `01_title.svg` | Title | white | 덱 표지 — 초대형 중앙 헤드라인 + 서브카피 |
| `02_agenda.svg` | Agenda | white | 목차 — 헤어라인 4행 리스트 |
| `03_section.svg` | Section | parchment | 챕터 전환 — 96px 헤드라인 |
| `04_split.svg` | Split | white | 좌 이미지 / 우 텍스트 분할 |
| `05_feature_grid.svg` | Feature Grid | parchment | 3열 원칙 카드 (아이콘 유일 등장) |
| `06_stat.svg` | Stat | white | 3-up 대형 지표 |
| `07_quote.svg` | Quote | parchment | 중앙 풀-인용 + 출처 |
| `08_comparison.svg` | Comparison | white | 2-up 스펙 비교 |
| `09_image.svg` | Image | white | 헤드라인 + 대형 이미지 (단일 그림자) |
| `10_bar_chart.svg` | Bar Chart | white | 6-바 추이 + 피크 강조 |
| `11_line_chart.svg` | Line Chart | white | 2계열 추이 (실선/점선) |
| `12_donut_chart.svg` | Donut Chart | white | 4세그먼트 구성비 + 레전드 |
| `13_closing.svg` | Closing | parchment | 브랜드 마크 + 클로징 카피 |

---

## IX. Spacing Specification

8px 베이스. 소스 토큰을 그대로 승계한다:

| Token | Value | Use |
| --- | --- | --- |
| `--space-xxs` | 4px | 미세 조정 |
| `--space-xs` | 8px | 인접 라벨 간격 |
| `--space-sm` | 12px | 밀착 스택 |
| `--space-md` | 17px | 본문 리듬 |
| `--space-lg` | 24px | 카드 패딩, 스택 gap |
| `--space-xl` | 32px | 블록 간격 |
| `--space-xxl` | 48px | 섹션 내 분리 |
| `--space-section` | 80px | 타일 수직 패딩 |

페이지별 마진:

| Page | Content margins |
| --- | --- |
| 01_title | 헤드라인 max-w 1080 (중앙), 서브 max-w 640 |
| 02_agenda / 05_feature_grid / 06_stat / 08_comparison / 09_image / 10–12 charts | 좌우 120px (x: 120 → 1160) |
| 03_section | 헤드라인 max-w 1020 (중앙) |
| 04_split | 이미지 0→600, 텍스트 688→1180 |
| 07_quote | 좌우 패딩 140, 인용 max-w 980 |
| 13_closing | 카피 max-w 560 (중앙) |
| 전 페이지 푸터 | 좌 64 / 우 1216, baseline 682 |

**Zero-gap 원칙**: 소스의 타일은 간격 없이 맞닿고 서피스 색 변화가 구분자다. 슬라이드에서는 페이지 자체가 타일이므로, 페이지 내부에 장식 구분선을 추가하지 않는다(헤어라인은 데이터 행/셀 구분에만).

---

## X. Placeholder Specification

### 텍스트 슬롯

| Token | Pages | Content |
| --- | --- | --- |
| `{{TITLE}}` | 01/02/03/04/05/06/08/09/10/11/12 | 페이지 헤드라인 |
| `{{KICKER}}` | 01/02/03/04/05/06/08/09/10/11/12 | 대문자 키커 (SVG에 이미 대문자로 저작) |
| `{{SUBTITLE}}` | 01 | 타이틀 서브카피 |
| `{{BODY}}` | 04 | 분할 페이지 본문 |
| `{{ITEM_n_TITLE}}` / `{{ITEM_n_TAG}}` | 02 | 아젠다 항목 (n=1..4) |
| `{{FEAT_n_TITLE}}` / `{{FEAT_n_BODY}}` | 05 | 그리드 카드 (n=1..3) |
| `{{STAT_n_VALUE}}` / `{{STAT_n_LABEL}}` | 06 | 지표 (n=1..3) |
| `{{QUOTE}}` / `{{ATTRIBUTION_NAME}}` / `{{ATTRIBUTION_ROLE}}` | 07 | 인용 |
| `{{OPTION_x_NAME}}` / `{{SPEC_x_n_KEY}}` / `{{SPEC_x_n_VALUE}}` | 08 | 비교 (x=A/B, n=1..3) |
| `{{LEGEND_PEAK}}` / `{{LEGEND_OTHERS}}` | 10 | 바 차트 레전드 |
| `{{LEGEND_SERIES_A}}` / `{{LEGEND_SERIES_B}}` | 11 | 라인 차트 레전드 |
| `{{DONUT_CENTER_VALUE}}` / `{{DONUT_CENTER_LABEL}}` / `{{SEG_n_NAME}}` / `{{SEG_n_VALUE}}` | 12 | 도넛 (n=1..4) |
| `{{CLOSING_LINE}}` / `{{CONTACT_LINE}}` | 13 | 클로징 카피 / 연락처 |
| `{{BRAND_MARK}}` | 전 페이지 푸터 + 13 대형 마크 | 브랜드명 텍스트 — **로고 이미지가 아니다** |
| `{{PAGE_LABEL}}` | 전 페이지 푸터 | 페이지 번호 또는 섹션 라벨 |

### 이미지 플레이스홀더

이미지 자리는 45° 해칭 패턴 + 중앙 안내 라벨로 표시한다. 해칭은 네이티브 프리셋 주석을 단 `<pattern>`으로 저작한다(shared-standards §7 Pattern Fill — `ltUpDiag` 프리셋으로 매핑):

```xml
<pattern id="imgph-hatch" patternUnits="userSpaceOnUse" width="20" height="20"
         patternTransform="rotate(45)" data-pptx-pattern="ltUpDiag">
  <rect width="20" height="20" fill="#f5f5f7"/>
  <rect width="10" height="20" fill="#ececef"/>
</pattern>
```

- 사용: `<rect ... fill="url(#imgph-hatch)"/>`
- 안내 라벨은 400/12 `#a8a8ad` 중앙 — 토큰이 아니라 리터럴 안내문("product photograph" 등)
- 라운딩: 풀블리드(04)는 rx 0, 인라인(08/09)은 rx 12
- **실사진으로 교체할 때 해칭 rect를 `<image>`로 대체한다.** 이미지는 사진-리얼리스틱, 저채도/흑백 그레이드 — 워밍/쿨링 그레이드와 헤비 그레인 금지

---

## XI. Icon System

- **접근**: 미니멀·희소·라인 기반. 콘텐츠 페이지는 아이콘 없이 타입과 여백이 일한다 — 이 로스터에서 아이콘은 **05_feature_grid 단 한 페이지**에만 등장한다
- **스타일**: 씬 스트로크 모노라인, `stroke-width="1.5"`, `fill="none"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, 26px 박스
- **색**: 라이트 서피스 위 잉크(`#1d1d1f`) 단색. 다색 아이콘·필드 아이콘 금지
- **컨테이너 칩**: parchment 원(r=28, `#f5f5f7`) — white 서피스에서만 보이는 조용한 칩이다. **parchment 페이지에서는 배경과 동색이라 보이지 않으므로 아예 넣지 않는다**(05_feature_grid가 이 경우). 보이지 않는 칩을 흰 원으로 "승격"해서 원본에 없던 크롬을 만들지 않는다 — 칩은 서피스가 필요로 할 때만 존재한다
- **라이브러리**: [`templates/icons/`](../../../icons/)의 line 계열만 사용. 아이콘을 추가하고 싶어지면 먼저 "이 아이콘이 없으면 의미가 사라지는가"를 묻는다 — 대개 답은 아니오다
- **Forbidden**: 이모지(유니코드 글리프 아이콘 해킹 포함), 필드/솔리드 아이콘, 다색 아이콘, 콘텐츠 타일 장식 아이콘

---

## XII. Voice & Tone

**확신에 차고, 조용하고, 선언적으로.** 카피는 짧고 단호하며 절대 얼버무리지 않는다. 헤드라인은 명사구 또는 2~3어 선언문이다 — 사물의 이름을 부르고 나머지는 이미지와 여백에 맡긴다.

| 항목 | 규칙 |
| --- | --- |
| **케이싱** | 문장 케이스 전면 적용. Title Case와 ALL CAPS 금지 (예외: 키커는 대문자 — SVG에 이미 대문자로 저작) |
| **인칭** | 중립/제품 중심. 헤드라인에서 "우리"/"저희"를 쓰지 않는다 ("Built to last." not "We built it to last.") |
| **구두점** | 헤드라인은 마침표로 끝나는 케이던스를 허용한다 — 마침표가 리듬의 일부다 ("Light. Years ahead.") |
| **숫자** | 구체적이고 무장식. 무게를 지닌 값만 올린다. 장식용 지표(stat-slop) 금지 |
| **이모지** | **절대 금지.** 갤러리의 정적을 깬다 |
| **길이** | 서브카피는 1~2행 현재형, 혜택 우선 |

**Tone examples**: 헤드라인 *"Titanium. So strong. So light. So Pro."* / 서브카피 *"The most advanced display we've ever made."* / 리걸 *"Available in the second half of 2026. Subject to change."*

한국어 카피에서도 동일 문법을 적용한다: 체언 종결 또는 단문 평서형("가볍게. 그리고 앞서서."), 감탄부호·물결표·이모지 금지, 존대 남용 금지.

---

## XIII. Anti-Pattern Checklist (reject at authoring time)

| ✗ 금지 | 이유 / 대안 |
| --- | --- |
| 악센트 컬러 도입 (블루/그린/어떤 hue든) | 이 시스템에 악센트는 존재하지 않는다 — 강조는 서피스 반전 → 웨이트 순 |
| 웨이트 500 (`'Pretendard Medium'`) | 래더에서 의도적으로 삭제된 단계 |
| 헤드라인 700 | 헤드라인은 600. 700은 이 로스터 미사용 |
| 카드/버튼/텍스트 그림자 | 그림자는 시스템 전체에 1개, 이미지 전용(09_image) |
| 그라디언트 배경/장식 | 분위기는 사진에서 오지 CSS에서 오지 않는다 |
| 라운딩 문법 혼용 (rx 6, rx 15 등) | 허용값: 0 / 4(차트 스와치·바) / 8 / 12(인라인 이미지) / 18(카드) / 9999(필) |
| 페이지 내부 장식 구분선 | 헤어라인은 데이터 행/셀 구분 전용. 나머지는 여백이 나눈다 |
| 이모지 · Title Case · ALL CAPS 본문 | §XII 보이스 규칙 위반 |
| 다색 차트 팔레트 / 파이 차트 / 3D | §VII 차트 문법 위반 — 그레이 래더 + 단일 잉크 강조, 파이 대신 도넛 |
| 로고 이미지 삽입 | 브랜드 마크는 `{{BRAND_MARK}}` 텍스트 슬롯 — 이 덱은 로고 자산을 번들하지 않는다 |
| 여백 채우기 | Whitespace is the pedestal. 요소를 빼도 의미가 유지되면 뺀다 |
| 한글 런에 라틴 자간 그대로 적용 | §IV 자간 완화 규칙(×0.5) 적용 |
