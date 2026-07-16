# apple 템플릿 추가 설계 — Vitrine 모노크롬 HTML 슬라이드 13종의 deck+brand 이식

- 날짜: 2026-07-16
- 상태: 설계 확정 — 구현 전
- 결정: **deck + brand 한 쌍** 등록(jangpm 전례와 동일한 원본+추출본 구조), 폰트는 **Pretendard 유지**(SF Pro 미사용), 차트 슬라이드 3종은 **로스터 SVG로 포함**, 실행은 **create-template Type C 하이브리드**(HTML/CSS 직독 = 1차 팩트 소스, 브라우저 렌더 스크린샷 = 시각 검증 기준).

## 1. 배경과 소스 자산

사용자가 `C:\Users\byung\Downloads\Apple Design System\`에 보유한 디자인 시스템 패키지를 ppt-master 템플릿 라이브러리에 apple 스타일로 이식한다. 특히 `slides/`의 HTML 슬라이드 스타일 재현이 목표.

소스의 실체는 **Vitrine**이라는 이름의 오리지널 모노크롬 디자인 시스템(Apple 계열 photography-first 미니멀리즘 원칙 기반, Apple 고유 브랜드 자산의 복제물 아님)이며 구성은:

| 소스 경로 | 내용 | 이식에서의 역할 |
|---|---|---|
| `slides/*.html` (13종) + `slides/slides.css` | 1280×720 슬라이드 레이아웃 — 인라인 스타일에 정확한 px 좌표·폰트 크기·자간 명시 | 페이지 로스터의 1차 팩트 소스 |
| `colors_and_type.css` | 색/타이포/스페이싱/radius/elevation CSS 토큰 | 아이덴티티 세그먼트의 1차 팩트 소스 |
| `README.md` | 보이스·톤, 시각 원칙, 아이콘 원칙 서술 | design_spec §V/§VI(보이스/아이콘) 근거 |
| `fonts/SF-Pro-Display-*.otf` | SF Pro Display 웨이트 세트 | **사용하지 않음** (Pretendard 유지 결정) |
| `assets/wordmark-*.svg` | "Vitrine" 워드마크 | **싣지 않음** — 푸터 mark는 텍스트 슬롯화 |
| `preview/`, `styles.css`, `_ds_*.js` 등 | 웹 컴포넌트 프리뷰 | 이식 대상 아님 |

## 2. 산출물 구조

```text
.claude/skills/ppt-master/templates/
├── decks/apple/
│   └── templates/
│       ├── design_spec.md            # kind: deck — 아이덴티티+구조+미들 전 세그먼트
│       └── 01_title.svg … 13_closing.svg
└── brands/apple/
    └── templates/
        └── design_spec.md            # kind: brand — 아이덴티티만 (I~VI 필수 섹션)
```

- `images/` / `icons/` / `exports/`는 사용하지 않으므로 생성하지 않는다(빈 디렉터리 플레이스홀더 금지 규약).
- 로고 파일 없음: 원본 워드마크는 라이브러리 범용성을 위해 배제하고, 슬라이드 푸터의 `mark` 위치를 "프로젝트 브랜드명 텍스트 슬롯"으로 spec에 정의한다. brand spec §IV(Logo)는 로고 미보유·워드마크 텍스트 슬롯 운용을 명시한다.
- design_spec §I(개요)에 출처를 명시: "Vitrine 모노크롬 시스템(Apple 계열 미니멀리즘 원칙의 오리지널 구현) HTML 슬라이드 13종에서 이식".
- 등록: `register_template.py apple --kind deck`, `register_template.py apple --kind brand`.

## 3. 아이덴티티 매핑

### 3.1 색 — 순수 모노크롬, 악센트 없음

| 역할 | HEX | 비고 |
|---|---|---|
| 라이트 캔버스 | `#ffffff` | 지배적 서피스 |
| parchment | `#f5f5f7` | 시그니처 오프화이트, 교대 타일 |
| pearl | `#fafafc` | 고스트 필 |
| 다크 타일 래더 | `#1d1d1f` / `#272729` / `#161617` | primary / micro-step 밝게 / 어둡게 |
| 트루 블랙 | `#000000` | 풀블리드 보이드 |
| 잉크(텍스트) | `#1d1d1f`, muted `#333333` / `#7a7a7a` | 라이트 서피스 위 |
| on-dark | `#ffffff`, muted `#cccccc` | 다크 서피스 위 |
| 헤어라인 | `#e0e0e0` (소프트 링 `#f0f0f0`) | 카드/칩 1px 보더 |

**악센트 컬러 금지.** 강조 수단은 서피스 반전(라이트↔다크 타일)과 웨이트다. 그라디언트 장식 금지, 이모지 금지.

### 3.2 타이포 — SF Pro Display → Pretendard 매핑

- 패밀리: `Pretendard, "Malgun Gothic", sans-serif` (repo 폰트 정책 그대로). 중간 웨이트는 설치 패밀리명(`"Pretendard Light"`, `"Pretendard SemiBold"`) 사용.
- 웨이트 래더: **300 / 400 / 600 / 700 — 500 사용 금지.** 헤드라인은 600(700 아님). 300은 희소하게(에어리 리드).
- 음수 자간을 원본 값 그대로 이관: 초대형 타이틀(112px) `-3px`, 디스플레이 `-0.374px` 계열, 본문 17px `-0.374px`.
- **한글 자간 완화 규칙**: 원본 자간은 라틴 기준값이므로, 한글 위주 텍스트 런에는 약 ½로 완화(예: `-3px` → `-1.5px`)를 deck spec 타이포 섹션에 명문화한다.
- 보이스 문법(spec §V): 헤드라인은 명사구/2~3어 선언문이며 마침표로 끝나는 케이던스 허용("Light. Years ahead."), 문장 케이스(Title Case·ALL CAPS 금지), 히든 스탯 금지, 이모지 절대 금지.

### 3.3 그림자·모서리·구조 DNA

- **단 하나의 그림자**: `feDropShadow dx=3 dy=5 stdDeviation≈15 flood-opacity=0.22` — **서피스 위 이미지에만** 허용(shared-standards §6.4의 단일 outer shadow 계약과 부합). 카드·버튼·텍스트 그림자 금지. 카드는 1px `#e0e0e0` 헤어라인만.
- 모서리 문법: `0`(풀블리드) / `8px`(인라인 이미지·유틸리티) / `18px`(카드) / `9999px`(필) — 중간값 금지.
- 스페이싱: 8px 베이스 토큰(4·8·12·17·24·32·48·80), 좌우 마진 64px, 푸터 하단 36px.
- 이미지 플레이스홀더: 원본 대각선 해칭(`repeating-linear-gradient 45°`, 10px 주기)을 SVG `<pattern>`으로 재현해 실사진 교체 지점을 표시. 라이트 계열 `#ececef`/`#f5f5f7`, 다크 계열 `#2f2f32`/`#272729`.
- 아이콘(spec §VI): 씬-스트로크 모노라인, 콘텐츠 타일에는 아이콘 최소화 — 라이브러리 아이콘 사용 시 line 계열만.

## 4. 페이지 로스터 (13장)

| SVG | 원본 HTML | 성격 |
|---|---|---|
| `01_title.svg` | TitleSlide | 초대형 중앙 헤드라인 + 키커 + 푸터 mark |
| `02_agenda.svg` | AgendaSlide | 목차 리스트 |
| `03_section.svg` | SectionSlide | 챕터 대형 헤드라인 |
| `04_split.svg` | SplitSlide | 좌우 이미지/텍스트 분할 |
| `05_feature_grid.svg` | FeatureGridSlide | 3열 원칙 카드 |
| `06_stat.svg` | StatSlide | 3-up 대형 지표 |
| `07_quote.svg` | QuoteSlide | 중앙 풀-인용 |
| `08_comparison.svg` | ComparisonSlide | 2-up 스펙 비교 |
| `09_image.svg` | ImageSlide | 헤드라인 + 포토(단일 그림자 적용 지점) |
| `10_bar_chart.svg` | BarChartSlide | 바 차트 — 피크 바만 화이트 |
| `11_line_chart.svg` | LineChartSlide | 라인 차트 — 실선 라이트 + 점선 그레이 |
| `12_donut_chart.svg` | DonutChartSlide | 도넛 — 그레이스케일 래더 + 레전드 |
| `13_closing.svg` | ClosingSlide | 클로징 |

- 캔버스: `ppt169` (1280×720) — 원본 뷰포트와 동일.
- 각 페이지의 서피스 모드(white/parchment/dark/black)는 **각 HTML의 실제 클래스(`is-dark`/`is-black`/`is-parchment`)를 직독해 그대로 따른다.** `@dsCard` 주석의 subtitle 표기는 실제 마크업과 어긋나는 경우가 있어 팩트 소스로 쓰지 않는다.
- 차트 3장은 샘플 데이터 + **`chart-plot-area` 마커**를 포함해 작성하고, 실제 덱 생성 시 chart-design 스킬이 spec_lock 토큰을 상속해 실데이터 차트로 교체한다. deck spec에 모노크롬 차트 문법(단일 강조 = 화이트/최농도 1개, 나머지 그레이 래더, 헤어라인 그리드)을 명문화한다.
- 웹 전용 효과(backdrop blur, press scale 애니메이션, hover)는 슬라이드 13종에 등장하지 않으므로 이식 대상에서 제외.

## 5. 실행 절차

create-template.md 워크플로(Type C 시각 레퍼런스, `standard` 모드) 준수. 단 HTML/CSS라는 정밀 소스가 있으므로 하이브리드로 팩트를 수집한다.

1. **Step 1 분석**: 13개 HTML + `colors_and_type.css` + `slides.css` 직독(px/hex/자간/웨이트 수치 확보). 브라우저로 각 HTML을 1280×720 렌더 → 스크린샷 13장을 임시 분석 워크스페이스에 저장(시각 검증 기준). 이 단계는 분석 산출물만 만들고 최종 디렉터리를 건드리지 않는다.
2. **Step 2~3 브리프**: 팩트 기반 브리프 작성 → 사용자 확인 게이트 **`[TEMPLATE_BRIEF_CONFIRMED]`** 통과 전에는 최종 템플릿 디렉터리·design_spec·SVG를 일절 쓰지 않는다.
3. **Template_Designer 실행**: `decks/apple/templates/`에 SVG 13장 + deck design_spec.md 작성(충돌 프리플라이트: templates/ 비어 있음 확인).
4. **검증**: `svg_quality_checker.py ".claude/skills/ppt-master/templates/decks/apple/templates" --template-mode --format ppt169` 통과 + 스크린샷 13장과 페이지별 시각 대조(§6 기준).
5. **deck 등록**: `register_template.py apple --kind deck` → `decks_index.json` 갱신.
6. **brand 추출**: deck spec의 아이덴티티 세그먼트를 `create-brand.md` 워크플로(verbal spec 경로)로 `brands/apple/templates/design_spec.md`에 작성 → `register_template.py apple --kind brand`.
7. **(선택) 리뷰 PPTX**: 사용자가 PowerPoint 검토를 요청할 때만 `template_preview_pptx.py`로 `exports/` 생성.

## 6. 수용 기준

1. `svg_quality_checker.py --template-mode --format ppt169` 오류 0.
2. 13장 각각이 원본 스크린샷과 시각 대조에서 다음을 보존: 서피스 모드, 레이아웃 골격(좌우 64px 마진·푸터 위치), 타이포 위계(크기·웨이트·자간 감각), 모노크롬 팔레트(비의도 색상 0), 차트 문법(단일 화이트 강조).
3. 그림자는 전체 로스터에서 이미지 요소에만 존재(카드/텍스트 그림자 0).
4. 웨이트 500 사용 0, 악센트 컬러 사용 0, 이모지 0.
5. `decks_index.json` / `brands_index.json`에 apple 항목 등록.
6. deck 단독 경로 입력으로 SKILL.md Step 3 진입이 가능한 워크스페이스 계약 충족(`templates/design_spec.md` + SVG 로스터).

## 7. 리스크와 완화

| 리스크 | 완화 |
|---|---|
| 한글 텍스트에 라틴 음수 자간이 과도 | §3.2 한글 자간 완화 규칙을 spec에 명문화 |
| SF Pro 라이선스(Apple 플랫폼 한정) | SF Pro 미사용 — Pretendard 매핑으로 원천 회피 |
| `@dsCard` subtitle과 실제 마크업 불일치 | HTML 클래스 직독을 팩트 소스로 고정 |
| 그림자 필터의 변환 손실 | shared-standards §6.4 단일 `feDropShadow` 계약 준수(Approximate 등급 허용) |
| "apple" 명칭이 Apple 고유 자산으로 오인될 소지 | spec §I에 Vitrine 오리지널 시스템 출처 명시, 로고·워드마크 미포함 |
