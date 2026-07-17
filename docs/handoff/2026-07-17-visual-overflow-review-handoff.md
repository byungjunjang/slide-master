# Handoff — SVG 생성 후 겹침·텍스트 오버플로우·원치 않는 줄바꿈 검수 루프를 기본 파이프라인에 내장

> **✅ [2026-07-17] 구현 완료** — §3.1 지오메트리 게이트(`svg_quality_checker.py` A류 error / B류 warning + 오탐 예외 3규칙) + §3.2 예방 규칙(executor-base 폭 산수 의무·수선 사다리 ①–④, strategist 카피 길이 예산; 축약 권한은 brainstorming에서 **ⓑ Executor 한정**으로 확정) + §3.3 선별 픽셀 패스(**채택** — 조건부 보조층, playwright 부재 시 조용히 스킵; B류 warning은 게이트에서 건별 처분 의무) 구현·검증됨. 이 문서는 이력 보존용.
> - 검증: 동결 코퍼스 A류 3/3 error·B류 5/5 warning 검출, 스크림(P01/05/09/12/16/19/24)·저투명 numeral(P03/P11) 오탐 0. 수정본 재검사 지오메트리 error/warning 0. E2E 미니 덱(`projects/20260717_e2e_overflow_loop`) Executor→게이트→선별 픽셀→Step 7 무개입 완주.
> - 실덱 수선: 기존 8건 + 신규 검출분(P01 A류 2·P17/P18/P20 A류 6·P09/11/12/13/14/15/16/19/23 B류) 전부 수정 처분 → finalize → `exports/ppt169_hd_korea_shipbuilding_ver2.pptx` + verify_deck PASS.
> - 스펙: `docs/superpowers/specs/2026-07-17-visual-overflow-review-design.md`
> - 계획: `docs/superpowers/plans/2026-07-17-visual-overflow-review.md`
> - 커밋: 구현 전체 + 이 마크 단일 커밋 (main)

- 작성일: 2026-07-17 (사용자 P1–P10 실물 리뷰 반영으로 동일 자 갱신)
- 대상: 이 repo에서 본 작업을 구현할 다음 세션의 에이전트
- 발단: `projects/20260717_ppt169_hd_korea_shipbuilding` 생성 세션에서 사용자가 두 가지를 지적. ① "SVG 생성 후 요소 겹침/오버플로우를 결과물 기준으로 리뷰·수정하는 절차가 기본 파이프라인에 없다" ② 실제 산출물 P1–P10을 직접 리뷰해 **8건의 구체 결함**을 제시 (§1.1 코퍼스). 이 문서는 그 대응 작업의 handoff.

## 0. 시작 전 필수

1. `CLAUDE.md` 규칙에 따라 `.claude/skills/ppt-master/SKILL.md` **전체를 먼저 읽을 것** (파이프라인 수정 작업이므로 예외 없음). 특히 Global Execution Discipline(블로킹 게이트 추가 금지·서브에이전트 SVG 생성 금지·SVG 손 저작 규칙)과 Step 6 Quality Check Gate.
2. `.claude/skills/ppt-master/workflows/visual-review.md` + `references/visual-review.md` — 이미 존재하는 옵트인 시각 리뷰의 오케스트레이션·루브릭. **바퀴를 재발명하지 말 것** — 이 작업은 "새 리뷰 시스템 발명"이 아니라 "기본 경로에 얇은 예방·검출·수정 루프를 넣고 기존 자산(렌더러·루브릭)을 재사용"이다.
3. `.claude/skills/ppt-master/scripts/visual_review.py` — playwright 기반 페이지 PNG 렌더러 (`--pages` 단일 페이지 렌더 지원, live-preview 서버 필요).
4. `.claude/skills/ppt-master/scripts/svg_quality_checker.py` — 현행 정적 게이트. 지오메트리 검사를 추가한다면 여기가 자리.
5. `.claude/skills/ppt-master/references/executor-base.md` §2.1(프로즈 렌더 레시피)·§1.0(타이포 실행 순서) / `references/strategist.md` §IX 작성 규칙 — 예방 규칙이 꽂힐 자리.

## 1. 문제 정의 (현행 격차)

기본 파이프라인(Step 6→7)의 시각 품질 체크포인트와 각각의 한계:

| 체크포인트 | 시점 | 잡는 것 | 못 잡는 것 |
|---|---|---|---|
| `svg_quality_checker.py` | Step 6 필수 게이트 | 금지 문법, viewBox, spec_lock 드리프트, 폰트 크기 역할, 일부 일러스트 배치 휴리스틱 | **텍스트 폭 추정 기반의 겹침·캔버스 이탈·존 침범, 불필요한 줄바꿈** |
| `visual-review` 워크플로우 | 옵트인 (명시 요청 전용) | 겹침·정렬·리듬 전반 (PNG 픽셀 기준) | 기본 실행 안 됨 — "auto-invoke 금지"가 명문 규칙. 토큰 비용 20페이지 기준 100–150K+ |
| `verify_deck.py` 컨택트시트 | Step 7 **export 이후** | 전 페이지 저해상도 육안 확인 ("eyeball" 지시만 있고 수정 루프 절차 없음) | 썸네일이라 미세 오버플로우 판별 불가; 발견해도 finalize+export 재실행 비용 |

SVG는 자동 줄바꿈이 없으므로 모든 줄바꿈은 저작자의 수동 tspan 분할이다. 따라서 "의도하지 않은 줄바꿈/겹침"의 실체는 **작성 시점 글리프 폭 산수의 부재**이고, 이는 (a) 사후 검출이 쉽고 (b) 사전 예방은 더 쉽다 — §1.1 코퍼스가 이를 실증한다.

### 1.1 사용자 리뷰 결함 코퍼스 (2026-07-17, P1–P10 실물 리뷰 — ground truth)

사용자가 P1–P10만 리뷰해 8건을 지적. **동결 스냅샷**: `projects/20260717_ppt169_hd_korea_shipbuilding/backup/20260717_100007/svg_output/` (export 시점 자동 백업 — 8건 결함이 모두 그대로 들어 있음. 라이브 `svg_output/`을 나중에 수정하더라도 이 백업은 회귀 코퍼스로 보존할 것). P11–P24는 미리뷰 — 새 검출기가 찾는 항목은 사람 확인 필요.

글리프 폭 근사(CJK=1.0×fs, digit/Latin=0.55×fs, space=0.25×fs)로 8건 전부 재현 검증 완료:

| # | 페이지 | 사용자 지적 | 산수 검증 | 분류 |
|---|---|---|---|---|
| 1 | P01 cover | 부제 "반세기의 항해—…" 줄바꿈 | 전문 954px, 한도 1152px — **여유 198px인데 감음** | B-1 불필요 줄바꿈 |
| 2 | P03 | "극심한 외화 부족…" 줄바꿈 | 1050px, 여유 102px — **한 줄에 들어가는데 감음** | B-1 |
| 3 | P04 | "현대건설은 1970년…" 줄바꿈 | 994px vs 존 폭 676px — 초과 +318px, 한 줄 불가 | B-2 카피 과길이 |
| 4 | P05 | "정주영은 미포만…" 줄바꿈 | 1237px vs 1152px — 초과 +85px, 근소 초과 | B-2 |
| 5 | P06 | 리드가 우측 패널 박스와 겹침 | 리드 1행 종점 x=894 vs 패널 x=840 — **+54px 침범** | A 기하 결함 |
| 6 | P07 | 리드가 화면 밖으로 넘침 | 종점 x=1344 vs 캔버스 1280 — **+64px 이탈** | A |
| 7 | P08 | 리드가 사진과 겹침 | 종점 x=848 vs 사진 x=760 — **+88px 침범** | A |
| 8 | P08 | "유례없이 빠른…" 두 줄 | 842px vs 존 폭 696px — 초과 +146px | B-2 |

**핵심 발견**: 8건 전부가 위의 단순 근사식 하나로 예측된다. 픽셀 렌더 없이도 A류는 error로 확정 검출 가능하고, B류는 같은 산수로 예방 가능하다.

**분류 정의**:
- **A류 (기하 결함)** — 그린 텍스트 줄이 캔버스/이웃 요소 경계를 물리적으로 침범. 검출기가 error로 잡아야 함.
- **B-1류 (불필요 줄바꿈)** — 한 줄에 들어가는 문장을 산수 없이 감음. 검출기가 warning으로 잡고, 예방 규칙으로 근절.
- **B-2류 (카피 과길이 줄바꿈)** — 존 폭 대비 문장이 길어 감을 수밖에 없었음. 검출기는 "리드/단문 블록 다줄화"를 warning으로 표면화하되, **근본 대책은 저작 시점 카피 길이 예산**(§3.2). 사용자 취향: 한 문장 리드/코어메시지가 어중간하게 두 줄로 감기는 것 자체를 결함으로 봄.

## 2. 목표

1. **예방**: Strategist/Executor 저작 규칙에 글리프 폭 예산을 넣어 B류를 원천 차단.
2. **검출**: Executor 완료 후 ~ Step 7 진입 전, 사용자 개입 없는(비블로킹) 자동 검출→수정 루프. A류는 error(수정 필수), B류는 warning(카피/줄바꿈 재조정).
3. 기존 옵트인 `visual-review`(전면 루브릭·서브에이전트 병렬)는 그대로 옵트인으로 존치.

## 3. 설계 스케치 (확정은 brainstorming에서; 아래는 조사·실증된 방향)

### 3.1 검출 — 정적 지오메트리 검사 확장 (`svg_quality_checker.py`) 【1순위·필수】

§1.1의 근사식으로 각 `<text>`/tspan 줄의 폭을 추정해:
- **error**: ① 캔버스(viewBox) 이탈 ② 다른 top-level `<g>`의 bbox(패널 rect·`<image>` 등) 침범 ③ tspan 스택 하단의 푸터/이웃 침범 (세로).
- **warning**: ④ lead/subtitle 역할(≥body 크기, 다줄 tspan 스택)의 문장이 **한 줄 예산 안에 들어가는데 감겨 있음**(B-1) ⑤ lead 역할 블록의 다줄화 자체(B-2 표면화 — "카피 축약 검토" 문구).
- **오탐 예외 규칙 필수**: 같은 `<g>` 내부 요소 간, 스크림/저투명(`fill-opacity`≤0.15) 워터마크 위 텍스트(P03/P11 display numeral), hero 이미지+스크림 위 오버레이 텍스트(P01/05/09/12/16/19/24)는 겹침으로 판정하지 말 것. §6-2 오탐 0 회귀가 이 규칙의 수용 기준.
- 근사 계수는 상수로 두되 보수 마진(예: 추정폭 × 0.95만 넘어도 error)을 튜닝 — 폰트 메트릭 정밀화로 과설계하지 말 것.

### 3.2 예방 — 저작 규칙 (문서 수정) 【1순위·필수】

- `references/executor-base.md`: **텍스트 블록을 그리기 전 폭 산수 의무화** — `est_width(문장, fs) ≤ 존 폭`이면 한 줄로(감지 말 것 — B-1 근절), 초과면 아래 수선 사다리 적용. 기존 세로 산수 규칙( `y + Σdy + font-size ≤ 경계` ) 병기.
- `references/strategist.md` §IX 작성 규칙: **코어메시지/리드 카피 길이 예산** — 페이지 레이아웃별 가용 폭에서 역산한 글자수 상한(예: 40px 리드·전폭 기준 CJK ≈ 26자)을 §IX 저작 시 의식하도록 명문화. 한 문장 리드가 두 줄로 감기는 것은 결함이라는 사용자 규범 기록.

**수선 사다리 (예산 초과 시 적용 우선순위 — 사용자 확정, 2026-07-17)**:

| 순위 | 전략 | 적용 조건·근거 |
|---|---|---|
| ① | **카피 축약** | 리드/코어메시지 1순위. CJK는 글자당 폰트크기만큼 폭을 먹어 몇 글자 축약의 효과가 큼. 코어메시지는 정의상 "한 문장 스파인"이라 punchy가 규범이고, 잘린 세부는 supporting 블록으로 이관 (예: P05 "정주영은 미포만 백사장 사진 한 장과 지도 한 장만으로 26만 톤급 VLCC 2척을 수주했다"(+85px) → "백사장 사진 한 장과 지도 한 장으로 VLCC 2척을 수주했다" — 세부는 아래 블록이 이미 보유) |
| ② | **존 재배분** | 충돌 상대가 움직일 수 있을 때 — 패널/이미지 컬럼 폭 축소, 여백 재배분 (예: P07 사이드바 480→400px). 한계: 전폭 페이지(P05)엔 무효, 레이아웃 균형이 대가 |
| ③ | **균형 줄바꿈** | **본문 프로즈 한정** — 어절/구 경계, 두 줄 길이 균형, 고아 단어 2행 금지. **리드/코어메시지에는 비허용** (한 문장 리드의 두 줄 감김 자체가 결함이라는 사용자 규범) |
| ④ | **폰트 축소** | **원칙 금지** — 구조 역할 크기는 덱 전체 잠금(executor-base §1.0 기존 규칙 유지: 본문만·지역적·최대 −4px 최후수단, 리드/타이틀 절대 불가). 크기 축소는 덱 일관성을 깨고 폭 이득도 미미(40→36px = 10%) |

- **공개 질문 (brainstorming에서 확정)**: 사다리 ①(카피 축약)의 권한 소속 — 현행 규칙상 콘텐츠는 §IX 계약이고 Executor는 "주어진 페이지를 그린다" — ⓐ Strategist 예산 준수로 원천 차단(순수) ⓑ Executor에 리드 한정 미세 축약 허용(실용) ⓒ Executor는 warning만 내고 메인 루프가 §IX를 고쳐 재작성(안전) 중 택일. 어느 쪽이든 사다리 순서 자체는 확정.

### 3.3 검출 — 선별 픽셀 확인 (경량 인라인 패스) 【2순위·옵션】

3.1 warning이 뜬 페이지 + hero/scrim 페이지에 한해 `visual_review.py`로 PNG 렌더 → **메인 에이전트가 Read로 보고** 수정 (수정 주체가 메인이므로 서브에이전트 SVG 생성 금지 규칙과 충돌 없음). playwright 의존은 옵션 의존성으로 — 없으면 3.1만 동작. §1.1 실증상 8/8이 정적 산수로 잡혔으므로 이 층은 보조.

### 3.4 비채택 — `visual-review` 워크플로우 기본화

토큰 비용(100–150K+)과 서브에이전트 병렬 디스패치가 기본 경로 철학과 충돌. 옵트인 존치.

## 4. 수정 지점 스케치

| 파일 | 내용 |
|---|---|
| `scripts/svg_quality_checker.py` | §3.1 휴리스틱 (폭 추정기, top-level g bbox 대조, error/warning 분리, 오탐 예외) |
| `references/executor-base.md` | §3.2 가로 폭 산수 의무 + 줄바꿈 정책 (어절 경계·균형·고아 금지) + 세로 산수 병기 |
| `references/strategist.md` | §IX 코어메시지/리드 카피 길이 예산 + "리드 한 줄 규범" |
| `SKILL.md` Step 6 | Quality Check Gate에 A류 error 수정 필수 명시 + (3.3 채택 시) 선별 픽셀 패스 절차 삽입 (자동·비블로킹) |
| `workflows/visual-review.md` | Positioning 문구 갱신 — 기본 경량 패스와 옵트인 전면 리뷰의 관계 |
| `scripts/preflight.py` | 3.3 채택 시 playwright 옵션 의존성 검사 여부 |
| `workflows/failure-recovery.md` / verify_deck 문서 | export 후 발견 시 수정 루프(svg_output 수정 → finalize → export 재실행) 절차화 |

## 5. 제약·주의

- **블로킹 게이트 추가 금지** (Global Execution Discipline 3·10) — 새 패스는 자동 진행, 사용자 정지점 아님.
- **SVG 수정은 메인 에이전트 손 저작** (규칙 6·9) — 검출은 스크립트 OK, 수정을 스크립트/서브에이전트로 배치 처리하지 말 것.
- 검사기를 "시각 취향 엔진"으로 키우지 말 것 — 기하 결함(A)과 산수로 판정 가능한 줄바꿈(B)만. 레이아웃 미감 전반은 옵트인 visual-review의 영역.
- 언어 규칙: `.claude/skills/ppt-master/` 하위 문서는 시블링 언어(영문 스캐폴딩) 준수.
- repo 관례: main 직접 커밋, `tests/` 만들지 않기, 커밋 말미 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

## 6. 검증 방법 (수용 기준)

1. **코퍼스 검출률**: 동결 코퍼스 `backup/20260717_100007/svg_output/`에 새 검사기를 돌려 — §1.1의 **A류 3건(P06·P07·P08 리드) 전부 error**, **B류 5건(P01·P03·P04·P05·P08 본문) 전부 warning**으로 검출.
2. **오탐 0 회귀**: 결함 수정 후의 라이브 `svg_output/` 24페이지에서 오탐 0. 특히 스크림 위 텍스트(P01/05/09/12/16/19/24)와 저투명 워터마크 numeral(P03/P11)이 오탐 후보.
3. **E2E**: 새 덱 1회 생성으로 "예방 규칙 반영 저작 → 지오메트리 게이트 → (선별) 픽셀 확인 → Step 7" 흐름이 사용자 개입 없이 완주되고, 산출물에 A/B류가 없는지.
4. **(권장) 실덱 수선**: 구현 완료 후 새 루프를 라이브 덱에 적용 — 8건(+P11–24에서 새로 검출되는 것) 수정 → finalize → export ver2. 사용자가 지적한 결함의 실제 해소가 최종 확인.

## 7. 새 세션 시작 프롬프트 (복사용)

```
docs/handoff/2026-07-17-visual-overflow-review-handoff.md 를 읽고 그 작업을 구현해줘.

- 문서 §0의 필수 읽기(SKILL.md 전체 포함)를 먼저 끝낼 것.
- superpowers brainstorming으로 §3 설계(3.1+3.2 필수, 3.3 채택 여부)와 §3.2의 공개 질문
  (예산 초과 카피의 축약 권한 소속)을 확정하고, writing-plans로 계획을 남긴 뒤 구현할 것.
- 수용 기준은 §6: 동결 코퍼스 backup/20260717_100007/svg_output 에서 A류 3건 전부 error,
  B류 5건 전부 warning 검출 + 수정본에서 오탐 0 + E2E 1회.
- 구현 후 새 루프를 projects/20260717_ppt169_hd_korea_shipbuilding 라이브 덱에 적용해
  8건(및 P11–24 신규 검출분)을 수정하고 finalize → export ver2까지 낼 것.
- 완료 시 이 handoff 문서 머리에 구현 완료 마크를 남길 것 (2026-07-14 handoff 관례 참조).
```

## 8. 참조 아티팩트

- 발단 프로젝트: `projects/20260717_ppt169_hd_korea_shipbuilding/` (24p, HD한국조선해양 기업사 덱)
- **동결 결함 코퍼스**: 같은 프로젝트 `backup/20260717_100007/svg_output/` (8건 결함 포함 스냅샷 — 삭제 금지)
- 기존 옵트인 리뷰: `.claude/skills/ppt-master/workflows/visual-review.md`, `references/visual-review.md`, `scripts/visual_review.py`
- 차트 좌표 전용 검증(참고 선례 — "조건부 권장 standalone" 포지셔닝): `.claude/skills/ppt-master/workflows/verify-charts.md`
