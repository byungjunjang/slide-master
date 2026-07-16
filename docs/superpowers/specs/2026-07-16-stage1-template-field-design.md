# Confirm UI Stage 1 템플릿 선택 카드 + 좁힘 질문 설계 (A안 + 절충안)

- 날짜: 2026-07-16
- 상태: 설계 확정 — 구현 전
- 선행 문서: `docs/handoff/2026-07-14-confirm-ui-template-field-handoff.md` (A안 채택 경위 + 구현 범위 스케치)
- 결정 요약: Stage 1 카드는 **decks만** 노출(단일 선택 + "자유 디자인" 기본), 카드 프리뷰는 **쉘 SVG 라이브 렌더**({{TOKEN}} 샘플 치환), 좁힘 질문은 **명시적 템플릿 의사 또는 덱 이름 언급**일 때만 발동.

## 0. 배경

프리셋 템플릿은 현재 **초기 요청의 명시적 디렉터리 경로**로만 발동한다(SKILL.md Step 3 기계적 트리거). 경로를 모르는 사용자는 사실상 항상 자유 디자인으로 흘러간다. 2026-07-14 세션에서 해법으로 A안(기존 Confirm UI Stage 1 게이트 안에 템플릿 선택 카드 추가)이 채택되었고, B안(생성 전 AskUserQuestion 1회)은 게이트 +1이라 기각되었다. 이번 세션에서 사용자가 A안 착수 + 절충안(모호한 템플릿 의사에 한정한 좁힘 질문 — 매 실행 게이트가 아니라 사용자 스스로 모호하게 요청한 경우에만 발동하므로 게이트 불변 원칙과 충돌하지 않음)을 함께 승인했다.

착수 전제였던 "덱이 jangpm 하나뿐"은 해소됨: decks 3종(apple / jangpm / mckinsey), brands 5종, layouts 7종 — 전부 현행 structured 계약.

## 1. 범위

**목표 두 가지:**

1. **Stage 1 템플릿 카드** — Confirm UI Stage 1(캔버스·키정보·모드/비주얼 스타일·어드히어런스)에 `template` 선택 카드를 추가한다. decks 3종만, 단일 선택, 기본값 "자유 디자인(free)". 덱이 선택되면 Stage 1 확정 직후 Step 3 설치를 소급 실행하고 Stage 2를 템플릿 스킨 기반으로 재도출한다.
2. **좁힘 질문 규칙** — 초기 메시지에 (a) 명시적 템플릿 의사("템플릿 써줘", "양식대로") 또는 (b) 라이브러리 덱 id와 일치하는 이름 언급("apple 템플릿으로")이 있는데 경로가 없으면, 파이프라인 진입 전에 1회 좁힘 질문을 한다(옵션: 매칭 덱 = 경로 확정 / 자유 디자인). 덱을 고르면 일반 Step 3 경로 트리거와 동일하게 처리되어 설치가 Stage 1 이전에 일어난다(소급 설치 불필요). Claude Code에서는 AskUserQuestion, 기타 호스트는 채팅 질문 — SKILL.md 문구는 하네스 중립으로 쓴다.

**비범위:**

- layouts / brands는 카드에 노출하지 않는다(경로 방식 유지).
- 카드를 통한 다중 융합 없음 — brand+layout 등 융합은 기존대로 초기 메시지 다중 경로로만.
- 스타일 묘사("컨설팅 느낌", "미니멀하게")는 지금처럼 좁힘 질문 없이 스타일 브리프(§d~§g)로만 흐른다.
- 카드에서 layouts/brands까지 고르게 하는 확장은 후속 과제로 남긴다(카탈로그 빌드가 인덱스 기반이므로 확장 여지는 있음).

## 2. Confirm UI 서버 (`scripts/confirm_ui/server.py`)

- **`/api/catalogs`에 `templates` 키 추가** — `templates/decks/decks_index.json`에서 라이브 빌드: 엔트리 `{ id, summary, canvas_format, page_count, primary_color }` + 맨 앞 `free` 엔트리. canvas가 `config.py CANVAS_FORMATS`에서 동기화되는 기존 패턴을 미러한다 — 인덱스가 단일 진실이고, catalogs.json에는 UI 크롬 라벨(필드 제목, "자유 디자인" 라벨/설명)만 4개 언어(zh/en/ja/ko)로 유지한다. 덱 summary는 인덱스 원문 그대로 노출(단일 언어 자산).
- **새 라우트 `/api/template_preview/<deck_id>`** — 해당 덱 워크스페이스의 커버 쉘 SVG(로스터 첫 페이지)를 읽어 `{{TOKEN}}`을 페이지 언어의 고정 역할 샘플 문구(큰 제목/부제/본문 — visual_style 프리뷰와 같은 원칙: 프로젝트 콘텐츠가 아닌 고정 문구)로 치환해 서빙한다. `deck_id`는 인덱스 키와 대조해 경로 조작을 방어하고, 응답은 `no-store`. 외부 이미지 참조가 해석되지 않으면 그 요소만 빠진 채 렌더된다(점진적 저하 — 오류로 처리하지 않음).
- **어드히어런스 시점 문제(핸드오프 §4의 핵심 이슈) 해결** — 기존 `_template_adherence_enabled`(설치된 `<project>/templates/design_spec.md` frontmatter 기반)는 유지하되, 서버가 recommendations 응답에 템플릿 필드 상태를 함께 내려준다:
  - 설치된 템플릿 없음 → 카드는 **활성 셀렉터**. 어드히어런스 서브필드는 프런트가 동적 표시(카드에 decks만 있으므로 규칙은 "free가 아니면 표시"로 단순). 기본 추천 `adaptive`.
  - 경로로 이미 설치됨(kind 무관) → 카드는 **잠금 정보 표시**(활성 템플릿 이름 배지, 변경 불가). 어드히어런스 표시는 기존 서버 로직 그대로(deck/layout일 때만).
- 스테이지 진행 가드, 포트/락/수명주기 동작은 불변.

## 3. 프런트 (`static/app.js` / `index.html` / `style.css` / `catalogs.json`)

- Stage 1에 템플릿 섹션 추가: "자유 디자인" 카드 + 덱 카드 그리드. 덱 카드는 쉘 SVG 프리뷰 + summary + 페이지 수·캔버스 + primary_color 스와치. `recommend.template` 배지·기본 선택(생략 시 첫 카탈로그 옵션 = free로 폴백 — 기존 enumerable 필드 보장과 동일).
- 덱 카드 선택 → `template_adherence` 필드 표시(기본 `adaptive`), free 선택 → 숨김 + 결과 미기록.
- `result.json` stage1 페이로드에 `template: "<deck_id>" | "free"` (+ 덱 선택 시 `template_adherence`) 기록. 잠금 카드(경로 설치됨) 상태에서도 설치된 식별자를 `template`에 그대로 기록해 결과 형태를 통일한다(AI는 이미 설치를 알고 있으므로 재설치 트리거가 아님 — 정보 기록). 이후 스테이지 리렌더 시 확정값 폴드백은 기존 메커니즘 재사용.
- 필드 분류: **closed enumerable**(Custom 박스 없음 — 카탈로그 외 값은 추천값으로 스냅백).

## 4. SKILL.md Step 3 / Step 4

- **Step 3 트리거 테이블 확장** — 새 행: "명시적 템플릿 의사 또는 라이브러리 덱 이름 언급, 경로 없음 → 좁힘 질문 1회(매칭 덱 = 경로 확정 / 자유 디자인; free를 고르면 Stage 1 카드에서 재선택 기회가 남음)". 매칭이 특정되지 않는 순수 의사 표시("템플릿 써줘")는 덱 전체(현재 3종) + 자유 디자인을 제시한다. 덱이 4종 이상으로 늘면 콘텐츠와 가장 부합하는 3종 + 자유 디자인으로 캡하고 나머지는 채팅 텍스트로 언급한다.
- **"Bare names never trigger" 노트 재작성** — 원칙은 "질문 없이 이름을 경로로 해석·설치하는 것 금지"로 유지된다. 확정은 항상 사용자 답변이며, AI가 자동으로 해석해 설치하는 것은 여전히 금지. 침묵·스타일 묘사 행은 그대로 free design.
- **Step 3에 "지연 설치(Deferred install)" 절 추가** — Stage 1 결과의 `template`이 덱이면 그 시점에 동일한 kind 매트릭스 + structured preflight로 설치한다(우회 금지 — 핸드오프 §4 안전장치 승계). preflight 실패 시 침묵 다운그레이드 금지: 오류를 보고하고 채팅으로 재선택(다른 덱 or 자유 디자인)을 받는다. 이는 failure-recovery 관례의 오류 경로이지 새 게이트가 아니다.
- **Step 4** — Stage 1 필드 목록(오케스트레이션 표 포함)에 `template` 추가. 순서 명시: Stage 1 반환 → (덱 선택 시) **같은 턴에서** 설치 → Stage 2 재도출. "Steps 2→3→4는 중단 없는 한 런" 규칙에 설치 단계가 턴 종료 지점이 아님을 명시. Stage 2의 기존 규칙("템플릿 스킨 = 추천 색/타이포 후보, Stage 2는 절대 생략 불가")을 그대로 재사용 — 새 규칙 불필요.
- Global Execution Discipline rule 10과의 정합: 좁힘 질문은 스킬이 정의한 route의 일부가 되므로 "defined route를 우회하는 임의 질문 금지" 원칙과 모순 없음. rule 텍스트 자체는 수정하지 않는다.

## 5. strategist.md §1

- 3단계 필드 소속표의 Stage 1 행에 `template` 추가(덱 카드 선택 필드, free 기본).
- 추천 로직 한 단락 추가: 콘텐츠·청중·목적이 특정 덱의 summary·use-case와 **실질적으로** 부합할 때만 그 덱을 `recommend.template`으로 추천하고, 아니면 `free`를 추천한다. 과잉 추천 금지 — free가 정직한 기본.
- template_adherence 문단에 카드 선택 경로에서도 동일 규칙(기본 `adaptive`) 적용을 명시.

## 6. confirm_ui.md / routing.md

- **confirm_ui.md**: 스키마 전체 갱신 — `recommend.template`, `result.json.template`(+ 조건부 `template_adherence`), catalogs의 `templates` 키(인덱스 라이브 빌드), `/api/template_preview` 엔드포인트, 어드히어런스 동적 표시 규칙, 잠금 카드 상태, Stage 1 필드 목록. 스테이지 가드 불변 명시.
- **routing.md**: "Bare template name … → Do not trigger Step 3" 행과 "Forbidden - fuzzy resolution" 단락을 좁힘 질문 규칙과 정합하게 갱신 — 이름 언급은 좁힘 질문을 발동하되, 질문 없는 자동 해석은 여전히 금지.

## 7. 검증

1. **단위**: confirm 서버 기동 → Stage 1 템플릿 카드 렌더·선택·어드히어런스 동적 표시·`result.json` 기록 확인; `/api/template_preview` 토큰 치환·경로 방어; catalogs 4언어 라벨.
2. **E2E**: 주제만으로 덱 생성 요청 → Stage 1에서 덱 선택 → 소급 설치 → Stage 2에 템플릿 스킨이 추천 후보로 표시 → 최종 PPTX까지. 표본 프로젝트(`projects/20260714_ai_agent_adoption/`)와 동일 품질 게이트(svg_quality_checker 0 errors).
3. **회귀 3종**: (a) 경로 명시 트리거 기존 동작 + Stage 1 카드 잠금 표시, (b) 침묵 → free design + 카드에서 free 확정, (c) "apple 템플릿으로" → 좁힘 질문 → 덱 확정 → 일반 경로.

## 8. 제약 (핸드오프 §5 승계)

- **게이트 수 불변** — Stage 1 외 새 상시 블로킹 지점 금지. 좁힘 질문은 사용자 자신의 모호한 요청에서만 발동.
- 언어 규칙: `.claude/skills/ppt-master/` 하위 문서는 영어 스캐폴딩; catalogs.json 신규 라벨은 zh/en/ja/ko 4언어 필수(이 설치본 기본 언어 ko).
- Confirm UI는 px-only, stage progression guard 유지(스테이지 건너뛰기 금지).
- repo 관례: main 직접 커밋, 커밋 말미 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`, `tests/` 만들지 않기.
- SKILL.md frontmatter 불변 → `.codex/skills/` stub 재동기화 불필요.
- upstream 재동기화 시 충돌 지점이 되므로 변경 파일 목록을 커밋 메시지에 남긴다.

## 9. 변경 파일 목록 (예상)

| 파일 | 변경 |
|---|---|
| `scripts/confirm_ui/server.py` | catalogs `templates` 키 빌드, `/api/template_preview` 라우트, 템플릿 필드 상태 주입 |
| `scripts/confirm_ui/static/catalogs.json` | 템플릿 필드 UI 크롬 라벨 4언어 |
| `scripts/confirm_ui/static/app.js` / `index.html` / `style.css` | Stage 1 템플릿 카드 섹션 + 어드히어런스 동적 표시 |
| `SKILL.md` | Step 3 트리거 테이블 + 지연 설치 절, Step 4 Stage 1 필드/오케스트레이션 |
| `references/strategist.md` | §1 필드 소속표 + 템플릿 추천 로직 |
| `scripts/docs/confirm_ui.md` | 스키마/카탈로그/엔드포인트 문서 갱신 |
| `workflows/routing.md` | 이름 언급 → 좁힘 질문 행 갱신 |
