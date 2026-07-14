# jangpm 디자인 시스템 포팅 설계 — deck + brand 추출본

- 날짜: 2026-07-14
- 상태: 사용자 승인 대기
- 결정: 적용 구조 **C안 (deck 주 패키지 + 얇은 brand 추출본)**, 폰트 체인 **repo install-local Pretendard 정책 스택**

## 1. 배경과 목표

slide-svg 리포지토리(`C:\Users\byung\WorkOS\AI Work\slide-svg`)의 **jangpm 디자인 시스템**을 ppt-master 스킬의 템플릿 라이브러리(`.claude/skills/ppt-master/templates/`)로 이식한다. 목표는 jangpm의 시각 언어를 **최대한 그대로 재현**하는 것 — 에디토리얼·미니멀·한국어 강의/리포트 톤, 모노크롬 + 단일 액센트, 헤어라인 시그니처 패턴, GM(governing message) 라인 계약까지 포함한다.

### 소스 자산 인벤토리 (slide-svg)

| 자산 | 경로 | 내용 |
|---|---|---|
| 테마 토큰 | `.claude/skills/slide/assets/design-systems/jangpm/theme.json` | 14토큰 팔레트, 7단계 타입 스케일, radius/stroke/spacing, 보이스 규칙 |
| 디자인 문법 | `.claude/skills/slide/templates/layouts/jangpm/DESIGN.md` | 레이아웃 패밀리, ★시그니처 헤어라인 패턴, 하이브리드 카탈로그 + 변주, 차트/테이블/아이콘 규칙, 18개 안티패턴 |
| 프로젝트 스펙 | `.claude/skills/slide/templates/layouts/jangpm/design_spec.md` | ppt-master 계열 design_spec 형식의 잠금 기록 (GM 규칙, 캔버스, 색/타이포 잠금) |
| SVG 셸 4장 | 동 디렉터리 `01_cover / 02_chapter / 03_content / 04_ending.svg` | 플레인 SVG + `{{PLACEHOLDER}}` 토큰 (pptx 구조 메타데이터 없음) |
| 캐릭터 자산 | `assets/brand/jangpm-character.png` | 브랜드 캐릭터 비트맵 |
| 패턴 갤러리 | `references/jangpm-patterns.tar.gz` (25 HTML) | 시각 참고용 — 파이프라인 비소비 |

## 2. 구조 결정 (사용자 확정)

**C안: deck 주 패키지 + brand 추출본.**

- jangpm은 아이덴티티와 구조가 분리 불가능하게 결합돼 있다(헤어라인 = `#E5E7EB` 1px이라는 색 값이 곧 구조; 액센트 예산 ≤2 = 색 규칙이자 레이아웃 규칙). 세 세그먼트(identity/structure/middle)를 한 spec에 담는 **deck kind**만 이 결합을 온전히 기록하며, "Strategist locks all segments"라는 deck 소비 방식이 jangpm의 "lock forbids deviation" 철학과 일치한다.
- **brand 추출본**은 색/타이포/보이스/아이콘만 담아 다른 layout/deck과의 융합용 아이덴티티 재사용을 지원한다.
- brand + layout 분리안은 기각: brand 스키마가 레이아웃/여백/시그니처 요소를 명시적으로 금지해 에디토리얼 문법이 찢어지고, layout 단독 소비 시 색 잠금이 강제되지 않는다.

## 3. 산출물 1 — deck 패키지 `templates/decks/jangpm/`

```
templates/decks/jangpm/
├── templates/
│   ├── design_spec.md        # kind: deck — 아래 §3.1
│   ├── 01_cover.svg          # §3.2 포팅 규약 적용
│   ├── 02_chapter.svg
│   ├── 03_content.svg
│   └── 04_ending.svg
└── images/
    └── jangpm-character.png  # 커버/엔딩 한정 선택 자산
```

### 3.1 `design_spec.md` (kind: deck)

프론트매터:

```yaml
deck_id: jangpm
kind: deck
native_structure_mode: template
summary: Korean editorial lecture / report decks — 강의, 워크숍, 전략 브리핑, 분석 리포트
canvas_format: ppt169
page_count: 4
primary_color: "#4633E3"
```

섹션 구성은 **아래 표가 권위 소스**다(기존 deck spec들의 영어 스캐폴딩 관례를 따르되, jangpm 문법을 담기 위해 섹션을 확장). 섹션 제목은 영어, 값은 한국어 허용(리포지토리 Markdown 언어 규칙 준수 — templates 디렉터리 스펙은 영어 스캐폴딩).

| 섹션 | 담을 내용 (소스) |
|---|---|
| I. Template Overview | 용도(강의/워크숍/전략 브리핑), 디자인 톤(editorial · analytical · declarative), 안티무드("colorful SaaS dashboard" 금지), 리트머스("한국 비즈니스 주간지에 그대로 실려도 어색하지 않으면 통과") — DESIGN.md §1 |
| II. Canvas Specification | 1280×720, 좌우 56px / 상 56px / 하 64px(GM 예약), 콘텐츠 영역 x=56 y=160 w=1168 h=480 — jangpm design_spec §II·V |
| III. Color Scheme | **14토큰 전체 잠금 테이블** + 색 규칙: 그레이스케일 우선, 액센트 이벤트 ≤2/페이지, 시맨틱 3색은 데이터 의미 전용, 배경 위계 사다리(bg→surface-alt→surface→accent-soft, 한 단계씩), 차트 단일액센트 투명도 사다리 `rgba(70,51,227, .85/.60/.40/.25)`, 그라디언트·그림자·글로우 금지 — theme.json + DESIGN.md §2 |
| IV. Typography | 7단계 스케일(Display 56/800/-1.68 → Label 12.8/600/+0.64 uppercase) 수치 원본 그대로, 폰트 패밀리는 repo 정책 스택으로 기록(§5 참조). Body 15.2px = "리포트 밀도" 기준이라는 주석, 저밀도 예외(18.4) 명시 — theme.json + DESIGN.md §3 |
| V. Page Structure | 페이지 해부도(헤더존 y56–96 / 타이틀 y96–148 / 바디 y168–656 / GM y672–696), **GM 라인 계약**(모든 content 페이지 필수, 선언형 so-what ≤30자, 제목 재진술 금지, 금지 어구 여러분/우리는/함께해요, cover/chapter/ending 면제), 페이지 번호 `01 / 12` 우하단 — DESIGN.md §6 |
| VI. Page Types | 4개 셸 각각의 구성 설명(cover: 액센트 룰 + eyebrow + Display 타이틀; chapter: 섹션 구분; content: 헤드라인 + 자유 바디 + GM; ending: 클로징) — 아젠다/TOC는 body 패밀리 자유 구성 페이지임을 명시(별도 TOC 셸 없음) |
| VII. SVG Page Roster | 4행 로스터 테이블 (file / role / description) |
| VIII. Layout Patterns | ★시그니처 패턴 2종(`ruled-list-with-eyebrow`, `columns-with-vertical-rules`)의 시각 스펙 + 구현 규율(`<line>` 헤어라인이지 rect 스트립 아님, `rx` 래핑 금지, eyebrow는 Label 스타일), 하이브리드 카탈로그 요약(콘텐츠 형태 → 1순위 프리미티브 매핑 테이블), 변주 규율(슬라이드당 변주 1개, 같은 변주 유형 덱 내 ≤2회, ★남용 금지), 밀도 플로어(카드 ≥3레이어, 텍스트 온리 슬라이드 금지, 수치엔 컨텍스트, 단일 차트 높이 ≥400px) — DESIGN.md §4·5 증류 |
| IX. Chart & Table Treatment | 차트: 단일액센트 사다리, 멀티휴 금지, 범례 크롬 금지(인라인 라벨), 축 라벨 `#6B7280` 12.8/500, 데이터 라벨은 차트 위에 직접; 테이블: 헤더행 surface-alt + Label 타이포, 추천 컬럼 accent-soft + 액센트 좌측 2px, 숫자는 tabular-nums 우정렬, verdict row; **data 슬라이드는 차트 + 테이크어웨이 카드 페어링 필수** — DESIGN.md §8 |
| X. Icon System | `tabler-outline` 잠금(2px stroke, bare — 원형 래퍼/컬러 배지 금지), 폴백 `tabler-filled`만 허용, `chunk`·이모지·팩 혼용 금지, 사이즈(카드 28–32 / 히어로 56–64 / 인라인 16), 번호 배지는 순서가 1차 정보일 때만 — DESIGN.md §9 (ppt-master `templates/icons/tabler-outline` 라이브러리와 직결) |
| XI. Component Specifications | SVG 스니펫: eyebrow + 헤어라인 헤더, ruled-list 행(라벨 15.2/700 + 바디 15.2/400 + `<line>` 디바이더), 세로 컬럼 룰, accent-soft 밴드(verdict), GM 라인, 페이지 번호 — DESIGN.md §5 시각 스펙을 SVG로 번역 |
| XII. Anti-Pattern Checklist | 축약 체크리스트: 액센트 >2 / 팔레트 외 HEX / 그라디언트·그림자 / GM 제목 재진술 / 금지 어구 / 텍스트 온리 / 균등 카드 그리드 / 2레이어 카드 / 이모지 / 타이틀 줄바꿈 — DESIGN.md §10 |
| XIII. Usage Instructions | Step 3 경로 소비 안내, strict/adaptive 어드히어런스 노트 |

### 3.2 SVG 셸 포팅 규약

지오메트리·타이포 수치·색 값은 **원본 그대로**, 메타데이터만 기존 라이브러리 규약(`academic_defense`/`招商银行`과 동일 형태)으로 추가:

1. 루트: `data-pptx-layout="<파일키>" data-pptx-layout-name="<Cover|Chapter|Content|Ending>"`
2. 배경 rect: `id="layout-<키>-background" data-pptx-layer="layout" data-pptx-editable="false"`
3. 텍스트 슬롯: `id="slot-<키>-<role>-<n>" data-pptx-placeholder="<role>"`; `{{PLACEHOLDER}}` 토큰 유지 (cover: EYEBROW / TITLE / TITLE_ACCENT / SUBTITLE / PRESENTER / DATE, content: PAGE_TITLE / GM / PAGE_NUM 등 — 셸별 원본 토큰 존중)
4. 장식 요소(액센트 룰 rect, 헤어라인 `<line>`)는 기존 라이브러리 셸과 동일하게 플레인 유지 — 배경 rect만 layout 레이어 표기(`academic_defense` 관례 준수)
5. 폰트 패밀리: §5의 repo 정책 스택으로 교체 (수치 유지)
6. `shared-standards.md` 금지 요소(`<style>`, `class`, gradient 등) 부재 확인 — 원본 셸은 이미 플랫 SVG라 위반 없음 예상, 포팅 시 재검증

### 3.3 자산

- `jangpm-character.png` → `decks/jangpm/images/`. spec §I 또는 자산 섹션에 "커버/엔딩 한정, 선택적" 기록.
- 포팅 제외: 25개 HTML 패턴 갤러리(비소비 — 문법은 §VIII로 증류), specimen HTML/CSS, `_preview/`(필요 시 `template_preview_pptx.py`로 재생성).

## 4. 산출물 2 — brand 추출본 `templates/brands/jangpm/`

```
templates/brands/jangpm/
├── templates/
│   └── design_spec.md        # kind: brand — create-brand.md 스키마 준수
└── images/
    └── jangpm-character.png
```

- 프론트매터: `brand_id: jangpm`, `kind: brand`, `primary_color: "#4633E3"`, summary/keywords.
- §II Color Scheme: 14토큰 테이블 (provenance `fact` — theme.json 직추출). 액센트 예산 ≤2, 시맨틱 데이터 전용 규칙은 anthropic 브랜드 예시처럼 노트 프로즈로 기재.
- §III Typography: 패밀리 + 웨이트만 (사이즈 위계는 layout/deck 소관 — create-brand 스키마 준수).
- §IV Logo: 없음 — 캐릭터는 §VII Visual Assets로.
- §V Voice & Tone: professional-neutral, 3인칭 기관 시점, 이모지 금지, 금지 어구 3종, GM 스타일 힌트를 톤 노트로.
- §VI Icon Style: stroke (tabler-outline 우선).
- 문서 상단에 provenance 인용구: **`templates/decks/jangpm/`이 원본(source of truth)이며 이 brand는 그 identity 추출본 — 색/타이포 변경 시 deck에서 먼저 고치고 여기 동기화**.

## 5. 폰트 체인 규칙 (사용자 확정: repo 정책 스택)

jangpm 원본 체인(`Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', Arial, sans-serif`) 대신 repo install-local 정책을 따른다:

- 기본: `Pretendard, "Malgun Gothic", sans-serif`
- 중간 웨이트는 설치 패밀리명 사용: 800 → `"Pretendard ExtraBold"`, 600 → `"Pretendard SemiBold"`, 500 → `"Pretendard Medium"` (각각 + 폴백 체인); 400/700은 기본 패밀리 + `font-weight`
- 정확한 표기는 구현 시 `references/strategist.md` §g 잠금 계약을 재확인해 그대로 따른다
- **사이즈/웨이트/트래킹/행간 수치는 jangpm 원본 유지** (Body 15.2px 리포트 밀도 포함 — ppt-master의 delivery_purpose 고정 바디 20/24/32px와 다르지만, deck 스킨은 확인 단계 Stage 2에서 추천 후보로 제시되는 기존 동작에 맡긴다)

## 6. 등록·검증

1. 등록: `python .claude/skills/ppt-master/scripts/register_template.py jangpm --kind deck` 및 `--kind brand` (인덱스 JSON이 단일 소스 — README는 템플릿을 열거하지 않으므로 README 수정 불요)
2. 검증:
   - SVG 메타데이터를 `academic_defense` 셸과 나란히 비교(루트 키, 레이어, 슬롯 id 형식)
   - `python .claude/skills/ppt-master/scripts/template_preview_pptx.py .claude/skills/ppt-master/templates/decks/jangpm` → `exports/`에 리뷰 덱 생성(리포지토리 ignore 대상), OfficeCLI 스크린샷으로 원본 `_preview/*.png` 대비 육안 대조 (플랫 계약 라이브러리 덱은 `--visual-only` 플래그가 필요함 — 실행 시 확인됨)
   - `register_template.py`가 수행하는 frontmatter/인덱스 정합 검사 통과 확인

## 7. 범위 밖 (명시)

- slide-svg 리포지토리는 수정하지 않는다 (읽기 전용 소스).
- ppt-master 파이프라인/워크플로 문서 수정 없음 — 순수 템플릿 라이브러리 추가.
- TOC 셸 신규 제작 없음 (jangpm에서 아젠다는 body 패밀리 자유 구성).
- 차트 템플릿(`templates/charts/`) 재스킨 없음 — jangpm 차트 규칙은 deck spec §IX가 생성 시점에 지배.

## 8. 유지보수 규칙

- **deck이 원본**: jangpm 시스템 값 변경은 `decks/jangpm/`에서 먼저, brand 추출본은 후속 동기화.
- slide-svg 쪽 jangpm이 진화하면(theme.json/DESIGN.md 갱신) 이 설계 문서의 인벤토리 기준으로 diff 후 수동 재이식.
