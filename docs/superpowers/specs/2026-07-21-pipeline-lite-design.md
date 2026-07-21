# 파이프라인 경량화 (pipeline-lite) — 소요 시간 50% 목표 A/B 실험 설계

- 날짜: 2026-07-21
- 상태: 설계 확정 — 워크트리 구현 (브랜치 `worktree-pipeline-lite`)
- 목표: **품질(게이트·손저작 규율) 유지** 조건에서 전체 파이프라인 총 소요 시간을 현재 대비 50% 이하로.
- 검증 방식: 같은 소스로 main 체크아웃 vs 이 워크트리에서 각각 생성 → 시간·품질 비교 → 기준 충족 시 머지.

## 0. 시간 소모 분석 (구조 기반)

계측 데이터가 없어 구조와 산출물 크기 기반 추정. `measure_run.py`(본 브랜치 신규)가 이후 실측을 담당.

| 구간 | 지배 비용 | 추정 비중 | 비고 |
|---|---|---|---|
| Step 1–2 (변환·초기화) | 스크립트 | 소액 | 레버 없음 |
| Step 4 (Strategist) | 3-stage Confirm 왕복 ×3 (사용자 대기 3회 + LLM 재파생 2회) + design_spec/spec_lock 서술 | 중간~큼 | recommendations.json을 3회 저작, 매 stage `--wait` 왕복 |
| Step 5 (이미지) | AI 생성 | 중간 | 매니페스트 모드는 이미 병렬 (`ThreadPoolExecutor`) |
| Step 6 (Executor) | 순차 페이지 손저작 + 종료 시 일괄 QC 수선 루프 | **최대** | 페이지당 저작 + 덱 말미 수선은 식은 컨텍스트 재로딩 비용 |
| Step 7 (후처리·검증) | 스크립트 + OfficeCLI 렌더 | 소액~중간 | 렌더는 측정 전용 (OfficeCLI 역할 합의) |

## 1. 레버 채택 표

| 레버 | 채택 | 기대 절감 | 품질 영향 |
|---|---|---|---|
| ① Step 4 원샷 확인 (single-pass Confirm UI) | **lite-S** | 사용자 대기 3→1회, 재파생 턴 2회 제거 | 낮음 — 서버가 legacy single-pass 렌더를 이미 지원(카드 캐스케이드는 클라이언트), 확인 후 재조정 규칙(기존 single-pass 규칙)이 일관성 보장 |
| ② 간결 스펙 서술 규칙 | **lite-S** | design_spec 서술 축소 | 낮음 — §IX 페이지 항목은 완전성 유지, 잉여 서사만 금지 |
| ③ Step 6 페이지별 QC 게이트 | **lite-S** | 덱 말미 수선 루프 → 핫 컨텍스트 즉시 수선 | 없음~개선 — 게이트 강도는 동일, 시점만 이동 |
| ④ verify_deck `--no-render` 기본값 | **lite-S** | OfficeCLI 렌더 1–3분 | 낮음 — 렌더는 명시 요청/릴리스 시 유지, A/B 품질 비교에서는 렌더 포함 실행 |
| ④′ Step 7.2 finalize(svg_final) 지연 생성 (2026-07-21 사용자 승인으로 추가) | **lite-S** | 스크립트 1–3분 | 낮음 — 익스포트는 `svg_output/` 직접 소비(SKILL.md 지원 경계); SVG 프리뷰/수동 삽입 요청 시에만 생성. verify_deck는 `svg_final/` 완전 부재를 '지연'으로 통과시키고, 존재하면 기존 패리티·신선도 검사를 그대로 적용 |
| ⑤ 앵커 주도 병렬 페이지 생성 | **lite-P (옵트인, 별도 커밋)** | Step 6 벽시계 50–70% (대형 덱) | **실험** — 규칙 6/7의 좁은 예외. 앵커(견본) 페이지 손저작 → 잔여 페이지 팬아웃 → 메인 에이전트 일관성 리뷰. 품질 저하 시 커밋 드롭 |
| shared-standards.md 핫/콜드 분할 | 보류 | 참조 로딩 축소 | 내용 드리프트 위험 대비 이득 불확실 — 차기 검토 |
| Step 5/6 오버랩 | 보류 | 이미지 생성 시간 은닉 | 직렬 규율·이미지 실측 의존성과 충돌 |
| 스크립트 SVG 생성 | **기각** | — | 규칙 9 — 과거 브랜치에서 품질 실패로 폐기된 경로 |
| 품질 게이트(지오메트리·checker·verify-charts) 완화 | **기각** | — | 사용자가 유지 원하는 품질의 원천 |

## 2. 레버 설계 요약

### ① 원샷 확인
`recommendations.json`에 최상위 `stage` 키를 **쓰지 않으면** 서버가 legacy single-pass로 전 섹션을 한 페이지에 렌더한다(`scripts/docs/confirm_ui.md` 스키마 표의 "(absent)" 행 — 서버 수정 불요). Strategist는 앵커+디자인 시스템+이미지/실행 필드를 한 번에 저작하고, `--daemon --wait` 1회로 최종 확인을 받는다. 사용자가 앵커를 바꾼 경우 기존 "single-pass 상류 변경 → 미수정 하류 재파생" 규칙으로 정합화한다. 3-stage 흐름은 사용자가 단계별 확인을 명시 요청할 때의 대안으로 존치(confirm_ui.md가 권위).

### ② 간결 스펙
design_spec.md는 명령형·표 우선으로 쓰고, 근거 서사는 섹션당 1줄 `> Note`로 제한. spec_lock 값의 산문 중복 금지. §IX 페이지 항목의 완전성(콘텐츠·차트·이미지 배정)은 축소 대상이 아님.

### ③ 페이지별 QC
기존 "첫 페이지 게이트"를 "매 페이지 게이트"로 확장: 각 페이지 저작 직후 해당 파일만 checker 실행, error 즉시 수정 + text-geometry warning 건별 처분. 덱 전체 게이트는 교차 페이지·spec_lock 드리프트 확인용 패리티 스윕으로 유지.

### ④ verify_deck --no-render
`verify_deck.py`에 `--no-render` 플래그 추가(OfficeCLI 콘택트시트 렌더만 스킵, OpenXML 검증 등 나머지 검사는 유지). lite 기본 실행은 `--no-render`, 릴리스·요청 시 풀 실행.

### ⑤ 병렬 생성 (실험)
`workflows/parallel-execute.md` 신규. 발동은 **사용자 명시 요청만**. 절차: 메인 에이전트가 Step 6 준비 + 앵커 페이지(표지·섹션 구분자·아키타입별 견본, 최소 4页 또는 덱의 ~25%)를 순차 손저작·게이트 통과 → 잔여 페이지를 서브에이전트에 팬아웃(각자 spec_lock/§IX 항목/앵커 SVG/참조 문서를 읽고 1페이지 저작 + 자체 checker 통과) → 메인 에이전트가 전 페이지 checker + 앵커 대비 일관성 리뷰 + 드리프트 수정 → 이후 기존 게이트 동일. 규칙 8(페이지 전 spec_lock 재독)은 서브에이전트 내부에서도 유지.

## 3. 측정 — `scripts/measure_run.py`

아티팩트 타임스탬프로 단계 경계를 재구성하는 사후·읽기 전용 리포트. 마커: 프로젝트 생성(project_meta.json) → sources 최신 → recommendations.json → result.json(`confirmed_at`) → design_spec/spec_lock → images 최신 → svg_output 첫/마지막 페이지(+페이지 간 케이던스) → svg_final → exports/*.pptx → _pptx_render. 한계: mtime은 마지막 수정 기준 — 재수정·재익스포트가 마커를 이동시키므로 **런 간 비교 계기**이지 감사 로그가 아니다. 기존 main 프로젝트에도 소급 적용 가능.

## 4. A/B 비교 프로토콜

1. 소스 1벌 선정 (기존 실측 코퍼스 재사용 권장 — 예: HD 한국조선해양 소스).
2. **기준선**: main 체크아웃에서 신규 프로젝트로 풀 파이프라인 1회. 확인 게이트 응답은 전부 추천값 그대로 수락(변인 통제).
3. **lite-S**: 워크트리에서 같은 소스·같은 응답으로 1회.
4. **lite-P**(선택): 워크트리에서 병렬 생성 옵트인으로 1회.
5. 각 런에서 기록:
   - `measure_run.py` 단계별 시간 + 총 시간 + 페이지 케이던스
   - `svg_quality_checker.py` error/warning 수 (수선 후 최종치와 수선 루프 횟수)
   - `verify_deck.py`(렌더 **포함**, 3개 런 동일 조건) 결과
   - 사용자 실물 리뷰: 콘택트시트로 겹침·오버플로우·어중간한 줄바꿈·페이지 간 일관성 결함 수 집계 (2026-07-17 HD 리뷰와 같은 방식)

### 결과 기록 표 (2026-07-21 실측 — 소스 samsung_vs_hynix_2025.md, 12p 고정, 자율 벤치)

| 런 | 총 시간 | Step4(스펙까지) | 페이지 저작 | 페이지 중앙값 케이던스 | checker E/W | verify_deck | 실물 결함 수 |
|---|---|---|---|---|---|---|---|
| baseline (fa88d7f9) | 27m05s | 14m20s | 12m34s | 50s | 0 / 4(마커 해시, benign) | PASS | 0 |
| lite-S | 29m30s (API 공백 ~2m 보정 시 ~27m30s) | 9m35s (실질 ~7m30s) | 16m11s | 1m43s | 0 / 6(마커 해시, benign) | PASS | 0 |
| lite-P | 45m07s | 9m33s | 26m20s (앵커 5장 7m39s + 팬아웃 7장 18m41s) | — | 0 / 4(마커 해시, benign) | PASS | 0 |

## 7. 실측 판정 (2026-07-21)

| 항목 | 판정 | 근거 |
|---|---|---|
| 레버 ①② (원샷 확인+간결 스펙) | **작동 — 재현됨** | Step 4 14m20s → 9m33s/9m35s (2회 재현, −33~47%); 실사용 대기 절감(3→1회)은 자율 벤치에 미반영(추가 이득) |
| 레버 ③ (페이지별 QC) | **순 시간 손실 (+~3.6m/12p)** — 품질 효과는 확인(팔레트 이탈 2건 조기 검출) | 교란 요인: lite 덱이 차트 5장으로 더 무거움 + baseline이 규칙 8 재독 11회 생략(자기 스펙보다 빠르게 주행). 대응: "클린 페이지 침묵 통과" 조항 추가(본 브랜치 반영) |
| 레버 ④④′ (렌더 스킵+finalize 지연) | 작동 (~2m) | baseline finalize 2m13s vs lite 스킵; 렌더는 lite 런이 자발적으로 실행해 +25s 보수 측정 |
| 레버 ⑤ (lite-P 병렬) | **기준 미달 — 드롭 권고** | 총 45m07s (+67% vs baseline). 원인: 서브에이전트당 참조 부트스트랩(~2,400줄)+체커가 페이지당 고정 ~9m — 동시 4로는 순차(1m43s/장)를 이길 수 없는 구조. 품질은 통과(드리프트 0, 결함 0) — 실패는 시간뿐. 재도전 전제: 참조 다이어트(Executor 다이제스트)로 부트스트랩 절감 + 대형 덱(팬아웃 ≥16장) + 동시 8 |
| 총평 | lite-S: 자율-모드 순수 AI 시간은 baseline과 동률(품질 동급), 실사용(확인 대기 포함) 기준으로만 우위. 50% 목표는 현 레버로 미달성 — 다음 후보는 참조 다이어트(§1 보류 레버)와 lite-P 재설계의 결합 | |

## 5. 머지 기준

| 대상 | 시간 기준 | 품질 기준 | 미충족 시 |
|---|---|---|---|
| 커밋 1 (measure_run.py) | — | 무해(읽기 전용) | 항상 머지 가능 |
| 커밋 2 (lite-S: 레버 ①–④) | 총 시간 ≥25% 단축 | checker 최종 0 error + verify_deck 통과 + 실물 결함 수 baseline 이하 | 미달 레버만 되돌려 부분 머지 |
| 커밋 3 (lite-P: 레버 ⑤) | 총 시간 ≥50% 단축 (baseline 대비) | 위와 동일 + **페이지 간 일관성 결함 0** (톤·간격·크롬 어긋남) | 커밋 드롭 (lite-S만 머지) |

> Note: 50% 목표는 ①–④만으로는 도달하기 어렵다는 것이 본 설계의 정직한 추정이다. ⑤가 기준을 통과해야 50%가 실현되고, 실패하면 25–35% 단축(lite-S)이 확보선이다.

## 6. 커밋 구조

1. `measure: run timing report tool` — measure_run.py + 본 설계 문서
2. `lite-S: one-shot confirm, concise spec, per-page QC, verify --no-render` — SKILL.md / strategist.md / confirm_ui.md / verify_deck.py
3. `lite-P (experimental): anchored parallel page generation` — workflows/parallel-execute.md + SKILL.md 규칙 6/7 예외 + index/routing 등록
