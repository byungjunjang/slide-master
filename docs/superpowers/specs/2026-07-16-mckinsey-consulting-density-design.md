# mckinsey 템플릿 컨설팅 밀도 심화 설계 — 조판 문법 + accent 단일 초점 + delivery_purpose 시딩

- 날짜: 2026-07-16
- 상태: 구현 완료 — 재조판 dry-run 3장 체크리스트 통과 (2026-07-16)
- 결정: **방향 1 (deck/brand 스펙 심화)** 채택 — 밀도 변수 신설(방향 2)은 기각. 크롬 현행 유지, accent는 단일 초점 규칙으로 강화, `delivery_purpose`는 dense(`text`) 추천 시딩.

## 1. 배경과 목표

mckinsey 템플릿(`templates/decks/mckinsey/`, `templates/brands/mckinsey/`)의 산출물이 실제 컨설팅 분석 덱 대비 다음 3요소가 부족하다:

1. **Rich data visualization** — 정밀 차트 + 상세 데이터 테이블
2. **Structured frameworks** — 2×2, 전략 다이어그램 (thin clean line)
3. **High information density** — 멀티컬럼 분석 밀도

### 실증 근거 (dry-run, 2026-07-16)

- 실제 생성 프로젝트 `projects/20260715_samsung_vs_hynix_2025_mckinsey`(13장, `delivery_purpose: balanced` 기본값 실행)를 분석: 크롬(액션 타이틀·Source 라인·차트 래더)은 컨설팅 문법이나, **페이지당 exhibit 1개**, 전체 덱에 **프레임워크 exhibit 0개**, 최대 테이블 4행.
- 동일 콘텐츠·동일 팔레트·동일 크롬으로 5페이지를 "심화 문법"(멀티 exhibit: 분기 추이 차트 A + 6×7 분기 상세 테이블 B + Key Findings 레일 + Verdict + 마이크로 KPI)으로 재조판한 결과: 텍스트 요소 29→98(3.4배), 데이터 포인트 4→53. 렌더 검수 결과 겹침·오버플로 없음.
- 결론: 격차의 원인은 밀도 슬라이더가 아니라 **deck design_spec이 소유하는 조판 문법**. 밀도 축은 이미 `delivery_purpose`(text/balanced/presentation, confirm UI "전달 목적")로 존재하므로 별도 density 변수 신설은 중복이며 3요소 중 1개(밀도)의 절반만 해결한다.

### 사용자 확정 사항

- 참고자료(Consultant Toolkit)의 주제목/부제목+Head Message 크롬은 **흡수하지 않음** — 현행 액션 타이틀 크롬 유지.
- accent 예산은 늘리지 않고 **단일 초점 규칙으로 오히려 강화** (강조가 적은 쪽 선호).

## 2. 산출물 1 — deck 스펙 개정 `templates/decks/mckinsey/templates/design_spec.md`

### 2.1 §VIII 조판 문법 심화

**(1) Evidence 페이지 = 최소 2존 원칙**
모든 evidence 페이지는 exhibit 존 + takeaway 존으로 구성한다. takeaway 존은 3형태 중 택1:
- (a) **Key Findings 레일** — 우측 x=776→1236, 구분 헤어라인 x=758 (1px `#E8E8E8`)
- (b) 차트 우측 takeaway 스택 (현행 chart-led 패턴)
- (c) 하단 verdict 밴드

단일 존 페이지는 선언된 예외(stat-hero, 전폭(x=44→1236) 테이블, 밀도 플로어 전환에 따른 텍스트 패턴)만 허용.

**(2) 멀티 exhibit 문법**
소스가 추이+내역을 함께 제공하면 차트(A) + 상세 테이블(B)을 페어링한다. 좌측 존 x=44→740 지오메트리는 레일형(1-a) 페이지 기준이며, takeaway 스택형(1-b)에서는 exhibit 존이 좌측 ≈60% 차트 존을 쓰고, verdict 밴드형(1-c)에서는 콘텐츠 영역 전폭을 쓴다. exhibit 레터링 관례: `A ·`, `B ·` 접두(15px/600, `#1A1A1A`) — exhibit이 2개 이상일 때만.

**(3) Key Findings 레일 패턴 정식화** (신규 패턴 등록)
레일 구성: `KEY FINDINGS` 라벨(13.3/600, letter-spacing 0.6, `#888888`) + 번호 매긴 findings 2–3개(행잉 넘버 24/700 `--navy` + 제목 16.5/600 + 근거 1–2줄 13.3/400 `#888888`, 사이 헤어라인) + verdict 밴드(2px accent 룰 + VERDICT 라벨 + 판정문 18.7/600 + 근거 14/400) + 선택적 마이크로 KPI 스트립(2–4개: 값 24/700 `--navy` + 라벨 12 `#888888`). numbered-takeaway-stack의 레일 축소판으로 기존 문법과 같은 계보.

**(4) 상세 테이블 승격**
다기간·다엔티티 정량 콘텐츠에서 상세 테이블(최소 4행×4열, §XII 처리 규정 그대로: 네이비 헤더·밴딩·숫자 우측 정렬 + 하단 주석 라인 12px `#888888`)을 차트의 **동반 1순위**로 승격 — "차트 아니면 테이블"이 아니라 "차트 + 테이블"이 기본형.

**(5) 프레임워크 노출 의무 (덱 레벨)**
소스에 우선순위/인과/단계 구조가 있는 전략 덱은 프레임워크 exhibit(2×2, 트리, 프로세스 등 — 기존 §VIII content-shape 매핑 유지)을 최소 1회 노출한다. 미노출은 소스 형상으로 정당화되어야 하며 편의상 생략은 anti-pattern.

**(6) 조건부 밀도 플로어 — "증거가 있으면 펼치고, 없으면 패턴을 바꾼다"**
evidence 페이지는 소스가 제공하는 한 데이터 포인트 ≥12개를 목표로 한다. 소스가 얇으면 테이블을 억지로 채우지 말고 takeaway-stack 등 텍스트 패턴으로 전환한다. **수치 조작·페이크 셀 절대 금지.**

기존 규칙(variation discipline, 같은 패턴 ≤2연속, 차트-테이크어웨이 페어 의무, 최소 3 레이아웃 타입)은 유지하고 위 규칙이 그 위에 얹힌다.

### 2.2 §III Color Rules 개정 — accent 단일 초점 규칙

현행 "Accent budget ≤ 2 events per content slide"를 다음으로 교체:

- accent(`#2E9BD6`)는 **페이지당 단 하나의 초점**(엔티티·시리즈·숫자·셀)만 가리킨다.
- **같은 초점의 exhibit 간 반복은 허용** — 차트의 focus 시리즈와 테이블의 같은 엔티티 행은 하나의 초점. 서로 다른 두 대상을 각각 강조하는 것은 금지.
- **verdict 밴드의 2px accent 룰은 구조 관례로 분리** — 데이터 초점 예산과 별도 계정, 페이지당 1개, 위치는 takeaway 존 안.
- 나머지 위계는 전부 무채색 수단(굵기·네이비·밴딩·헤어라인)으로 해결 — grayscale-first 규칙 유지.

차트 래더(`#0F2A4A → #1F6FA8 → #4FB2E5`), focus 시리즈 accent 관례("그 시리즈가 페이지의 초점일 때"라는 조건 명시), traffic-light data-only 규칙은 변경 없음.

### 2.3 §XIII Anti-Pattern Checklist 갱신

- 교체: "Accent (`#2E9BD6`) events > 2 on one content slide" → "accent가 서로 다른 두 초점을 가리킴"
- 추가: 선언된 예외 없이 단일 존으로 구성된 evidence 페이지
- 추가: 소스에 다기간/다엔티티 수치가 있는데 상세 테이블 없이 요약 숫자만 노출
- 추가: 소스에 우선순위/인과/단계 구조가 있는데 프레임워크 exhibit 0개
- 추가: 밀도를 채우기 위한 페이크 셀·무표기 추정치

### 2.4 §XIV Usage Instructions — delivery_purpose 시딩

- mckinsey 덱이 Step 3 템플릿으로 지정되면 Strategist가 Stage 1에서 `delivery_purpose: text`(read-close·dense)를 **추천값**으로 제시한다. 근거 문구: "컨설팅 덱은 발표용이 아니라 정독용 문서다." 사용자는 확인 단계에서 오버라이드 가능(강제 아님).
- 주석 1: 이 덱은 §IV가 타입 램프(Body 16px)를 잠그므로 `delivery_purpose`는 글자 크기가 아니라 **페이지당 콘텐츠 분배량·page_rhythm·페이지 수 추천**에 작용한다.
- 주석 2: dense 페이지는 수용량이 크므로 같은 소스에서 페이지 수 추천(§b)을 한 단계 낮게 잡는 경향을 허용한다 (예: 12–14 → 10–12).

## 3. 산출물 2 — brand 스펙 동기화 `templates/brands/mckinsey/templates/design_spec.md`

- §II usage 문단의 accent 예산 문구만 교체: "budget of ≤ 2 events per slide" → 단일 초점 규칙 + verdict 룰 별도 계정 (§2.2와 동일 문구).
- 페이지 구조 규칙(2존 원칙·레일 지오메트리)은 deck 소관이므로 brand에 기록하지 않음 — 기존 provenance 원칙 유지.

## 4. 비변경 범위

- **SVG 셸 신설 없음** — `03_content.svg`는 자유 조판 셸 유지, 레일 지오메트리는 §VIII 문법으로만 문서화.
- **크롬 불변** — 액션 타이틀 독트린, 타이틀 룰 y=112, footer 룰 y=676, Source 라인 관례 그대로. Head Message 크롬 흡수 안 함.
- **코드/UI 불변** — confirm UI, validate_spec.py, svg_quality_checker.py, preflight 미변경. SKILL.md frontmatter 변경 없음 → sync_codex_stubs 불필요.
- **다른 템플릿 불변** — jangpm 등 형제 템플릿 파급 없음.

## 5. 검증 계획

1. 스펙 수정 후 worktree에서 기존 프로젝트(`samsung_vs_hynix_2025_mckinsey`)의 evidence 페이지 2–3장을 개정 스펙으로 재조판, ver1과 Playwright 렌더로 나란히 비교 (dry-run과 동일 방식).
2. 개정 §XIII 체크리스트를 dry-run 페이지에 역적용해 판별력 확인 — 예: "서로 다른 두 초점" 규칙이 dry-run의 테이블 셀 accent(차트 SK 시리즈와 같은 초점이므로 통과)와 가상의 이질 초점 케이스를 올바르게 가르는지.
3. deck spec 개정 후 언어 규칙(templates 스펙 = 영어 스캐폴딩 + 한국어 값 허용, `docs/rules/` 준수) 확인.

## 6. 기각한 대안

- **방향 2 (contents density 변수 신설)**: 밀도 축은 `delivery_purpose`로 이미 존재(중복), 3요소 중 프레임워크·데이터 시각화는 밀도 변수로 해결 불가, 매 실행 사용자 결정 1개 추가, 전 템플릿×밀도 QA 표면 확대. 기각.
- **Head Message 크롬 흡수**: 현행 액션 타이틀 크롬과 계보가 다른 한국형 컨설팅 문법 — 사용자 결정으로 기각(별도 템플릿 신설도 현 시점 보류).
