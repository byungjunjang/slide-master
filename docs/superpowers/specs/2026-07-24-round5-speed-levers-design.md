# 5라운드 속도 레버 설계 — 이미지 오버랩 · text_fit 세로/충돌 · checker 증분화 (2026-07-24)

브랜치: `worktree-speed-round5` (워크트리 `.claude/worktrees/speed-round5`, base main=3084c116)

## 1. 배경 — 실측 근거

7/23 실런 2건(10p 이미지 덱, measure_run 실측; 두 런 동시 실행이라 상호 오염 가능) = 총 ~45–47m:

| 구간 | 시간 | 비고 |
|---|---|---|
| 확인 전 추천 저작 | ~5m | |
| **확인 → 첫 SVG 데드존** | **18–23m** | 스펙 작성 ~12m + AI 이미지 직렬 ~5–7m + 부트스트랩 ~3.5m |
| 페이지 저작 | 13–15m | 1m30–41s/장 |
| 꼬리(스윕+export+verify) | 2.5–5.5m | |

콜드 벤치(이미지 없음, cold-A 40m57s)는 저작 56–63% / Step 4 27–32% / 부트스트랩 ~10% / 후처리 ~7%. 기존 라운드(lite-S·ref-diet·round-A·speed accelerators)는 케이던스와 참조 로드를 겨눴고, **실사용 이미지 덱의 데드존(이미지 직렬 게이트)과 세로/충돌 rework 루프가 미봉으로 남아 있었다.** fork 팬아웃은 v1/v2에서 시간 미승으로 종결(재도전 금지).

## 2. 레버 ① — Step 5 이미지 백그라운드 오버랩

**변경**: 확인 직후 §VIII 이미지 계획을 선확정 → `image_prompts.json`/`image_queries.json` 선작성 → `image_gen.py --manifest` / `image_search.py --batch`를 **백그라운드 프로세스로 발사** → 스펙 나머지 작성과 병행. Step 5는 수집·복구 지점으로 전환(상태 확인, Failed만 §7 사다리, 슬라이스, analyze_images). Step 6은 미도착 시 **이미지-없는 페이지 먼저** 저작(deferred-image-pages 규칙; 이미지 페이지 저작 전 terminal+analyze_images 필수).

**불변**: 매니페스트 계약·§7 경로 선택(`manual`=발사 안 함)·복구 사다리·Step 7 readiness 게이트·규칙 6/7(메인 에이전트·순차 단일 패스). 슬라이스는 Step 5 잔류. split 모드는 수집 완료 후 핸드오프(백그라운드는 세션 넘어 생존 못 함). 백그라운드 불가 호스트는 기존 포그라운드 폴백.

**편집 파일**: `SKILL.md`(Step 4 발사 블록+체크리스트, Step 5 수집 전환+게이트 문구, Step 6 GATE+유예 규칙, split 캐비앗) · `references/image-generator.md` §7(발사 지점 노트) · `workflows/failure-recovery.md`(매트릭스+resume 행) · `CLAUDE.md`(퀵레퍼런스 주석).

**기대**: 이미지 5–7m가 스펙 작성 ~12m 뒤로 숨어 데드존에서 소멸(이미지 생성 < 스펙 작성이면 전액).

## 3. 레버 ② — text_fit 세로/충돌 모드 (A-class 사전 차단)

**변경**: `text_fit.py`에 체커-정합 상수(GEOM_ASCENT 0.8 / DESCENT 0.2 / CONSERVATIVE 0.95 / MIN_OVERLAP 4.0)와 `evaluate_stack`(세로: CANVAS_V·CANVAS_H·BOUND) + `evaluate_page`(페이지 객체 1콜: 폭+세로+장애물/블록 간 충돌 COLLIDE) 추가. 판정 조건은 체커 `_geom_a_checks` 미러(포함=언더레이 면제, 경계 가로지름=결함). CLI `--y/--dy/--num-lines/--vb-height/--bottom-bound`, `--batch`가 페이지 객체(JSON dict) 수용, BOM 톨러런트(utf-8-sig).

**검증(교차)**: 동일 기하의 손저작 SVG로 체커와 대조 — 세로 오버플로·침범(픽셀 추정 ~205px까지 동일)·포함-면제 3케이스 판정 일치. 레거시 모드/종료코드 회귀 없음.

**편집 파일**: `scripts/text_fit.py` · `references/executor-base.md`(폭 예산 4항) · `references/executor-cheatcard.md` §4(페이지 객체 우선) · `references/layout-archetypes.md`(배치-1회 정합) · `SKILL.md`(액셀러레이터 3항).

**기대**: 마일스톤 게이트에서 터지던 세로/충돌 error → 페이지 재작성(1–3m/건) 루프가 사전 1콜로 대체.

**후속 보정 (A/B 판정 후, 2026-07-25)**: 실험 arm에서 P05 **부분 스크림**(불투명 rect, 커버리지<85%·opacity>0.15)을 `obstacles`에 열거하지 않아 사전 프리엠프트가 놓쳤고, 게이트에서 cross-group 충돌 error 2건→재작성 2회가 발생. `evaluate_page`의 **판정 로직은 체커 정합**이나, 장애물 **입력이 손저작 `obstacles` 배열**이라 실행자가 스크림을 빠뜨리면 갈라지는 것이 원인(코드 버그 아님, 열거 규약 갭). 기존 가이던스가 obstacles를 "cards/panels/images"로만 안내한 것을 보정: `executor-base.md`·`executor-cheatcard.md §4`·`text_fit.py` docstring에 **"체커가 obstacle로 세는 모든 불투명 rect/image(카드·패널·사진 + 부분 스크림/그라디언트/배지)를 열거하고, 텍스트 배경 스크림은 full-canvas(≥85%) 또는 opacity ≤0.15로 두어 양쪽 모두 면제"**를 명문화. 판정 기준 ②(충돌 0)를 다음 실사에서 충족하기 위한 규약 수정.

## 4. 레버 ④ — checker `--pages` 증분화 + verify_deck 중복 단락

**변경**:
- `svg_quality_checker.py --pages <spec>`(번호·N-M 범위·이름 토큰): 마일스톤 게이트는 직전 블록만 검사(P01은 풀 런 유지 — 그 시점 전수=1장 + 구조 계약 조기 검증). 부분 검사는 덱-와이드 계약 검사 스킵(최종 풀 스윕이 소유), 스탬프 미작성. 매치 0건=error.
- 풀 프로젝트 0-error 런이 `<project>/.qc_pass.json`, validate_spec PASS가 `.spec_pass.json` 스탬프 기록. `verify_deck.py`는 스탬프가 입력(svg_output 전체+spec 2파일)보다 새로우면 두 서브프로세스 재실행을 스킵(페이지 수 불일치·스테일 시 정상 재실행 — touch 테스트로 무효화 확인).

**검증**: --pages 2-4/이름/no-match 스모크, verify_deck 2연속(7.8s→1.0s) + touch 무효화, 벤치 12p 풀 런 회귀 0 error.

**편집 파일**: `scripts/svg_quality_checker.py` · `scripts/validate_spec.py` · `scripts/verify_deck.py` · `SKILL.md`(마일스톤 명령) · `references/executor-cheatcard.md` §8 · `references/executor-base.md`(마일스톤 문구).

**기대**: 스크립트 시간 자체(~2s)보다 **이미 처분한 warning 재노출 → LLM 재검토 왕복 제거**가 실효.

## 5. A/B 판정 기준 (사전등록)

- **대상**: 이미지 있는 10–12p 덱, 동일 소스, 콜드(신규 세션) 2암 — 대조=main, 실험=`worktree-speed-round5`. **벤치 중인 체크아웃에 머지 금지**(cold-B 교훈).
- **1차 판정(산술·n=1 판정 가능)**: ① 이미지 오버랩 실동작 — 이미지 파일 mtime이 스펙 작성 창(확인→design_spec mtime) **안**에 들어오는가(타임스탬프 직접 관찰). ② 세로/충돌 error로 인한 페이지 재생성 **0건**(체커 로그 기준). ③ verify_deck 스킵 라인 출력.
- **2차 판정(시간·편차 주의)**: 확인→첫 SVG 데드존 −4m↑(이미지 덱), 총시간 단축. cold-B 교훈상 n=1 시간 판정은 참고치 — 1차 판정과 품질이 우선.
- **품질 전제(미달 시 시간 무관 기각)**: checker 0 error·text-geometry 처분 완료·verify_deck PASS·콘택트시트/육안 결함 0·카피 과축약 없음.
- **원상복구 조건**: 유예 규칙이 페이지 응집을 해치는 육안 신호(이미지 페이지만 이질적), text_fit 세로 모드 오탐으로 불필요한 재배치 유발, --pages 게이트가 실결함을 놓침(최종 스윕에서 2건↑ 신규 error).

## 6. 아티팩트 노트

- `.qc_pass.json` / `.spec_pass.json`: 프로젝트 루트 스탬프(gitignored 영역). measure_run 무영향.
- 스킬 frontmatter 무변경 → codex 스텁 재동기화 불필요.
