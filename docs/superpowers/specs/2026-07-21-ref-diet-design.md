# 참조 다이어트 (ref-diet) — Executor 고정 참조 핫/콜드 재배치 A/B 실험 설계

- 날짜: 2026-07-21
- 상태: 설계 확정 — 워크트리 구현 (브랜치 `ref-diet`, base = main `0f971774`)
- 선행: [`2026-07-21-pipeline-lite-design.md`](./2026-07-21-pipeline-lite-design.md) (lite-S 머지 완료, lite-P 드롭). 인수인계: `C:\Users\byung\AppData\Local\Temp\2026-07-21-ref-diet-handoff.md`
- 목표: Step 6(Executor)이 매 런 고정으로 읽는 참조(~2,400줄)를 **저작 핫패스 / 콜드 세부**로 재배치해 부트스트랩 비용을 줄인다. 규칙 삭제 없음 — 로딩 경로 재배치만.

## 0. 현 고정 로드 실측 (Step 6 진입 시, flat 자유설계 덱)

| 파일 | 줄 수 | 성격 |
|---|---|---|
| `shared-standards.md` | 1,494 | 저작 계약 + 변환기/임포트 계약 혼재 |
| `executor-base.md` | 633 | 저작 핫패스 위주 + structured/미러/노트 혼재 |
| `native-shape-authoring.md` | 152 | 저작 행동 규칙 (전부 핫) |
| `modes/<mode>.md` + `visual-styles/<style>.md` | ~97 | 이미 소형 |
| 합계 | **~2,376** | lite-P 실측: 서브에이전트당 부트스트랩 ~6분의 주 원인 |

콜드 후보 (페이지 저작 중 실제 참조되지 않는 구간):

| 구간 | 줄 수 | 실제 소비자 |
|---|---|---|
| shared-standards §7 Native PPTX Table/Chart Markers | ~347 | 차트/표 덱의 Executor(저작 시 전사) + checker/export |
| shared-standards §7 PPTX Structure Routing + Master/Layout/Placeholder + Legacy | ~144 | structured 템플릿 라우트만 |
| shared-standards §1.4 Imported Native Shapes | ~79 | 임포트/미러/뷰티파이 라우트만 |
| shared-standards §1.5 Authored Presets 기계 계약 | ~60 | checker/export (저작 행동은 native-shape-authoring.md가 전담) |
| executor-base §1.1 미러 소비 + §1.2 structured 매핑 + §2.1 structured 스캐폴드 | ~89 | structured/미러 라우트만 |
| executor-base §8 스피커 노트 | ~45 | 옵트인 (기본 OFF) |
| executor-base §9 Step 7 중복 서술 | ~19 | SKILL.md Step 7이 권위 (중복) |

## 1. 접근안 비교 (SSOT 유지 방식)

| 옵션 | 내용 | 판정 |
|---|---|---|
| (a) 물리 핫/콜드 분할 | 콜드 구간을 원문 그대로(verbatim) 새 파일로 이동, 핫 파일에 트리거+포인터 잔류 | **채택** — SSOT 유지(사본 없음), 드리프트 구조적으로 불가 |
| (b) 파생 다이제스트 + 동기화 검증 | 압축 다이제스트 생성 + 원본 대조 스크립트 | 기각 — 압축=재서술=드리프트 위험, 검증 기계 비용, 이번 라운드 범위 초과 |
| (c) 읽기 목록 §단위 포인터 | Step 6 읽기 목록을 라우트 조건부로 좁힘 | **채택(a와 결합)** — 파일 단위 조건부 로드. §단위 offset 읽기는 라인 침식으로 기각 |

## 2. 분할 설계 (verbatim move 명세)

### 2.1 신설 `references/native-objects.md` (콜드, ~500줄)

이동(원문 그대로): shared-standards §1.4 Imported Native PowerPoint Shapes, §1.5 Authored Native Presets 기계 계약, §7 Native PPTX Table / Chart Markers 전체 블록.

로드 트리거(SKILL.md Step 6 읽기 목록): `spec_lock.md page_charts`에 데이터 차트 항목이 있거나 §VII에 데이터 차트/텍스트 그리드 표 페이지가 계획된 덱 — 마커 전사(executor-base §3.2)가 이 파일의 스키마를 소비. 임포트/미러 라우트와 checker/export 디버깅도 이 파일 참조.

### 2.2 신설 `references/structured-templates.md` (콜드, ~250줄)

이동(원문 그대로): shared-standards §7 PPTX Structure Routing / Explicit Master·Layout·Placeholder Metadata / Legacy Structure Migration Boundary, executor-base §1.1 미러 소비 경로, §1.2 PowerPoint Master/Layout Mapping, §2.1의 structured 전용 룩업+스캐폴드.

로드 트리거: `spec_lock.md pptx_structure.mode: structured`(덱/레이아웃 템플릿 라우트) 또는 미러 템플릿. flat 자유설계/브랜드 덱은 로드하지 않는다 — flat 규칙("메타데이터 전면 금지 + `data-pptx-page-role`만 필수")은 핫 파일에 잔류.

### 2.3 신설 `references/speaker-notes.md` (콜드, ~50줄)

이동: executor-base §8 전체. 트리거: `design_spec.md §X` 노트 요청(기본 OFF) 또는 [`generate-audio`](../../../.claude/skills/ppt-master/workflows/generate-audio.md).

### 2.4 핫 파일 잔류 편집

| 파일 | 편집 |
|---|---|
| `shared-standards.md` | 이동 구간을 트리거+포인터 스텁(각 §당 3–5줄)으로 대체, 문서 맵/능력 색인 갱신. §1.0–1.3, §2–§6, §7 패턴 필, §8은 무변경 |
| `executor-base.md` | §1.1/§1.2/§8 포인터화, §2.1 structured 룩업 포인터화(flat 규칙 잔류), §3.2에 스키마 위치 1줄, §9를 SKILL.md Step 7 포인터 4줄로 압축 |
| `native-shape-authoring.md` | 헤더 교차참조를 native-objects.md로 갱신 |
| `SKILL.md` Step 6 | 읽기 목록을 조건부로: 상시 5개(executor-base, shared-standards, native-shape-authoring, mode, style) + 조건 3개(native-objects / structured-templates / speaker-notes) + 기존 diagram-design 조건 유지 |

### 2.5 기대 로드량

| 덱 유형 | 고정 로드 | 현재 대비 |
|---|---|---|
| flat·차트 없음 | ~1,620줄 | **−32%** |
| flat·차트/표 있음 (벤치 덱) | ~2,120줄 | **−11%** |
| structured 템플릿 | ~2,370줄 | ±0 (재배치만, 손실 없음) |

> Note: 순차 모드 벽시계 절감은 소폭(로딩 1–3분 구간의 축소 + 컨텍스트 압박 완화)으로 정직하게 추정한다. 주 전략 가치는 ① lite-P v2(신규 서브에이전트 부트스트랩 절감)의 전제 확보, ② 장덱에서 컨텍스트 압축 빈도 감소다. −50% 총 목표는 fork 팬아웃(16–24p 덱) 결합 시 도달 전망(인수인계 §3.5).

## 3. 품질 게이트 정합 논거

- 이동된 규칙은 전부 **스크립트 게이트가 이중 강제**한다: 마커 스키마·프리셋 지문·패턴 enum·금지 피처·spec_lock 드리프트는 `svg_quality_checker.py`(페이지별 게이트)가, structured 계약은 export read-back 게이트가 잡는다. 콜드 파일 미로드 상태에서 규칙 위반이 나와도 침묵 통과가 아니라 에러/경고로 표면화된다.
- 저작 행동 규칙(무엇을 그리는가)은 전부 핫 잔류: §1.0–1.3 금지/조건 계약, §4 페이지 계약·그룹핑, §6 이펙트 계약, executor-base §2–§7.
- 규칙 무손실 검증: 이동 구간 전부가 핫 파일 포인터 1개 이상으로 도달 가능해야 하며, repo 전체 교차참조를 grep으로 감사해 링크를 재배선한다.

## 4. A/B 프로토콜 (이전 설계 §4 재사용 + 변인 통제 강화)

1. 소스: `samsung_vs_hynix_2025.md` (기존 3런과 동일), 12p 고정, 자율 모드.
2. **확인값 선고정**: lite-S 코퍼스(`projects/20260721_bench_semis_lite/`)의 확정값을 그대로 핀 — pyramid / swiss-minimal / flat / ppt169 / Pretendard 락 / tabler-outline stroke 2 / 이미지 없음. Strategist 재량 변인을 제거.
3. **B런(ref-diet)**: 이 워크트리에서 풀 파이프라인 1회. verify_deck는 렌더 **포함**(3개 기존 런과 동일 조건).
4. 기록: `measure_run.py` 단계별 시간 + Step 6 부트스트랩 구간(spec 완료→첫 SVG mtime) + 페이지 케이던스, checker E/W, verify 결과, 콘택트시트 육안 결함 수, 로드된 참조 줄 수 실측.
5. 대조군: 기존 코퍼스 실측치(재실행 없음) — baseline 27m05s / lite-S 29m30s(보정 ~27m30s).

> Note: 런 1회/암(arm)이므로 ±2분급 API 노이즈 안에서는 총 시간만으로 판정하지 않는다 — 부트스트랩 구간·로드 줄 수·페이지 케이던스가 보조 판정 지표.

## 5. 판정 기준

| 항목 | 기준 | 미충족 시 |
|---|---|---|
| 품질 (필수) | checker 최종 0 error + verify_deck PASS(렌더 포함) + 콘택트시트 육안 결함 0 | 원인 페이지 수선 후 재판정; 구조적이면 실험 드롭 |
| 규칙 무손실 (필수) | 이동 구간 전량 링크 도달 가능 + preflight 통과 + 교차참조 grep 감사 0건 누락 | 링크 재배선 후 재감사 |
| 시간 | 총 시간 lite-S 대비 악화 없음(±노이즈) + Step 6 부트스트랩 구간 단축 실측 | 부트스트랩 단축이 확인되면 총 시간 동률이어도 머지 후보(전략 가치 ① 때문) |
| 머지 | 위 3항 충족 시 머지 권고 — 최종 결정은 사용자 | 사용자 결정 대기 |

## 6. 범위 제외 (차기 후보)

- Step 4 레버(strategist.md 919줄 + design_spec_reference 357줄 핫/콜드 분할, 구조 캡, 소형 소스 단일 패스) — 인수인계 §3.5 ①–④. 이번 런은 Step 6 변인만 격리.
- (b) 파생 다이제스트 + 동기화 스크립트.
- lite-P v2 (fork 팬아웃) — 본 실험 성공이 전제 조건.

## 7. 리스크·주의

- 내용 이동은 verbatim — 문장 재서술 금지(스타일 규칙 위반이 보여도 이번 라운드는 이동만; `docs/rules/prompt-style.md` §12 기존 파일 우선).
- 신설 references 파일은 영어(디렉터리 언어 일관성), 본 설계 문서는 한국어(specs 디렉터리 관례).
- SKILL.md frontmatter 무변경 → `sync_codex_stubs.py` 불요; 편집 후 `preflight.py` 확인.
- projects/ 벤치 코퍼스는 읽기 전용(회귀 대조군) — 소스 .md만 복사해 신규 프로젝트 생성.
- 로컬 main은 origin보다 4커밋 앞선 미푸시 상태 — 푸시는 사용자 확인 대기(인수인계 §5), 본 실험은 건드리지 않음.

## 8. 실측 결과 (런 후 기입)

(벤치 완료 후 기록)
