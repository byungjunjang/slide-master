# Handoff — Confirm UI Stage 1 템플릿 선택 필드 (A안) 구현

> **✅ [2026-07-16] 구현 완료** — A안(Stage 1 decks-only 템플릿 카드 + 지연 설치) + 절충안(경로 없는 명시 의사·덱 이름 언급 → 1회 좁힘 질문)이 구현·검증됨. 이 문서는 이력 보존용.
> - 스펙: `docs/superpowers/specs/2026-07-16-stage1-template-field-design.md`
> - 계획: `docs/superpowers/plans/2026-07-16-stage1-template-field.md`
> - 커밋: `546c428`~`4e0d466` (구현 8건; 변경 파일 목록은 각 커밋 본문)

- 작성일: 2026-07-14
- 대상: 이 repo에서 A안을 구현할 다음 세션의 에이전트
- 전제: **사용자가 create-template으로 템플릿을 몇 개 더 추가한 뒤** 착수한다 (템플릿이 jangpm 하나뿐인 동안은 선택 필드의 실익이 낮다는 판단으로 보류된 작업)

## 0. 시작 전 필수

1. `CLAUDE.md` 규칙에 따라 `.claude/skills/ppt-master/SKILL.md` **전체를 먼저 읽을 것** (파이프라인 수정 작업이므로 예외 없음). 특히 Step 3(템플릿 트리거 규칙)과 Step 4(3단계 Confirm UI 오케스트레이션).
2. `.claude/skills/ppt-master/scripts/docs/confirm_ui.md` — Confirm UI 스키마·서버 수명주기·stage progression guard의 단일 권위 문서.
3. `.claude/skills/ppt-master/references/strategist.md` §1 — 3단계 확인의 필드 소속표.

## 1. 목표 (사용자 확정 결정)

현재 프리셋 템플릿은 **초기 요청에 명시적 디렉터리 경로**가 있을 때만 발동한다(Step 3 기계적 트리거 — 이름/스타일 묘사/침묵은 절대 발동 금지). 사용자는 "가급적 템플릿 기반 생성"으로 기울이고 싶어 하며, 다음 방식을 채택했다:

> **A안 — 추가 질문 게이트를 만들지 않고, 이미 존재하는 유일한 확인 게이트(Confirm UI Stage 1: 캔버스·모드·비주얼 스타일·어드히어런스) 안에 '템플릿' 선택 카드를 추가한다. Stage 1 확정 시 선택된 템플릿에 대해 Step 3 설치를 소급 실행하고, Stage 2는 기존 설계대로 "템플릿 스킨 = 추천 색/타이포 후보"로 재도출된다.**

기각된 대안(맥락): B안 = 생성 전 AskUserQuestion 1회(게이트 +1이라 기각), C안 = 무조건 기본 템플릿(선택지가 늘어나면 부적합).

## 2. 현재 상태 (2026-07-14 기준, 로컬 main)

- **라이브러리 전체가 현행 structured 계약**: `decks/jangpm`(4셸) + `layouts/` 7종(academic_defense, ai_ops, government_blue, government_red, medical_university, pixel_retro, psychology_attachment — 36셸) 전부 승격 완료, 템플릿별 `template_preview_pptx.py --force` structured 프리뷰 검증 통과. 커밋: `10b039c`(jangpm), `7a21888`~`b9ad9f5`(layouts 7종, 템플릿당 1커밋).
- **중국어 자산 제거됨**: brands 中国电建·中汽研, decks 重庆大学·中国电建·中国电信·中汽研·招商银行 (커밋 `018c596`). 남은 브랜드: anthropic, google, jangpm.
- **소비 E2E 검증 표본**: `projects/20260714_ai_agent_adoption/` — jangpm deck을 Step 3~7 전체로 소비해 structured PPTX(ver2)까지 낸 프로젝트. 신계약 셸 형식의 표본이자 A안 구현 후 회귀 테스트 재료.
- 커밋은 전부 로컬 main에만 있음 (push 안 됨).

## 3. 신계약(현행 structured) 셸 형식 요약

모든 셸이 이 형식을 따른다 (표본: 아무 라이브러리 셸이나 열어볼 것):

```xml
<svg ... data-pptx-master="<id>-master" data-pptx-master-name="<Display>"
         data-pptx-layout="<key>" data-pptx-layout-name="<Name>">
  <rect id="master-bg" ... data-pptx-layer="master" data-pptx-editable="false"/>   <!-- 전 셸 동일 -->
  <rect id="layout-..." ... data-pptx-layer="layout" .../>                          <!-- 레이아웃 고정물, 아톰만 -->
  <g id="title-slot" data-pptx-placeholder="title" data-pptx-placeholder-bounds="x y w h">
    <text ... data-pptx-placeholder-carrier="true">{{TOKEN}}</text>
  </g>
  <!-- 나머지 {{TOKEN}} 텍스트/장식은 Slide-local -->
</svg>
```

역사적 맥락: 업스트림 코드(익스포터·검사기)는 신계약으로 진화했는데 라이브러리 자산이 구계약에 머물러 있었고, jangpm 수동 포팅이 그 형식을 미러링하면서 첫 소비 때 드러났다. 지금은 전부 해소됨. 상세: `docs/superpowers/specs/2026-07-14-jangpm-deck-brand-port-design.md` + 메모리 `jangpm-templates.md`.

## 4. A안 구현 범위 스케치 (설계는 brainstorming에서 확정할 것)

| 수정 지점 | 내용 |
|---|---|
| `scripts/confirm_ui/` (server.py, static/catalogs.json, 프런트 JS/HTML) | Stage 1에 `template` 필드 추가. 카탈로그는 정적이 아니라 **3개 인덱스(brands/layouts/decks_index.json)에서 동적 로드** 필요 (canvas가 config.py에서 동기화되는 기존 패턴 참고). 옵션: "자유 디자인(기본)" + 덱/레이아웃/브랜드 엔트리. 추천 배지는 AI가 recommendations.json에 지정 |
| `template_adherence` 상호작용 | 현재 서버가 `<project>/templates/design_spec.md` 프론트매터에서 `_template_adherence_enabled`를 도출하는데, A안에서는 **Stage 1 시점에 아직 설치 전**이라 이 로직이 깨짐 → 선택된 템플릿의 kind(deck/layout일 때만 어드히어런스 표시)로 동적 전환 필요. Stage 1 내 필드 간 의존성(템플릿 선택 → 어드히어런스 표시)을 프런트에서 처리 |
| `SKILL.md` Step 3 | 트리거 규칙 확장: "초기 메시지의 명시 경로" **또는** "Stage 1 확인에서 사용자가 선택한 템플릿"(선택지가 곧 명시 경로이므로 퍼지 매칭 금지 규칙과 충돌 없음). 설치 시점이 Step 4 Stage 1 확정 직후로 이동하는 흐름 명문화 |
| `SKILL.md` Step 4 | Stage 1 필드 목록에 template 추가, Stage 1 확정 → 설치 → Stage 2 재도출 순서 명시 |
| `references/strategist.md` §1 | 3단계 필드 소속표 갱신 + 추천 로직(콘텐츠와 어울리는 템플릿이 있으면 추천, 아니면 자유 디자인 추천) |
| `scripts/docs/confirm_ui.md` | 스키마 문서 갱신 (recommendations.json / result.json 필드, 카탈로그 키) |
| 안전장치 | 선택된 템플릿은 Step 3의 기존 structured preflight를 그대로 통과해야 함. 향후 추가되는 템플릿이 구계약이면 여기서 걸린다 — preflight를 우회하지 말 것 |

## 5. 제약·주의

- **게이트 수 불변이 이 안의 존재 이유** — Stage 1 외에 새 블로킹 지점을 만들지 말 것 (Global Execution Discipline 규칙 3·10).
- 언어 규칙: `.claude/skills/ppt-master/` 하위 문서는 영어 스캐폴딩 (CLAUDE.md Markdown 규칙). catalogs.json 라벨은 zh/en/ja/ko 4개 언어 필수 (2026-07-14부로 Confirm UI 한국어 지원 + 이 설치본 기본 언어 ko — 한국어 대화에서는 recommendations.json에 `lang: "ko"` 사용).
- upstream 재동기화(재클론) 시 이 수정들이 충돌 지점이 됨 — 변경 파일 목록을 커밋 메시지/문서에 남길 것.
- Confirm UI는 px-only, stage progression guard 있음 (stage 건너뛰기 금지).
- repo 관례: main 직접 커밋, 커밋 말미 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`, `tests/` 만들지 않기.

## 6. 검증 방법

1. 단위: confirm 서버 기동 → Stage 1에 템플릿 카드 표시·선택·result.json 기록 확인.
2. E2E: 주제만으로 덱 생성 요청 → Stage 1에서 템플릿 선택 → 설치 → Stage 2에 템플릿 스킨이 추천 후보로 뜨는지 → 최종 PPTX까지. 표본 프로젝트(`projects/20260714_ai_agent_adoption/`)와 동일 품질 게이트(svg_quality_checker 0 errors) 통과.
3. 회귀: 경로 명시 방식(기존 트리거)과 자유 디자인(무선택)이 그대로 동작하는지.

## 7. 참조 아티팩트 (중복 서술 대신 경로)

- 포팅 설계: `docs/superpowers/specs/2026-07-14-jangpm-deck-brand-port-design.md`
- 포팅 구현 계획: `docs/superpowers/plans/2026-07-14-jangpm-deck-brand-port.md`
- 이 세션 커밋 이력: `git log --oneline 277dd42..b9ad9f5`
- 메모리: `~/.claude/projects/C--Users-byung-WorkOS-AI-Work-slide-master/memory/jangpm-templates.md`
- 테스트 덱 프로젝트: `projects/20260714_ai_agent_adoption/` (로컬 전용, git 미추적)

## Suggested skills

1. **superpowers:brainstorming** — 착수 시 최초 호출. §4 스케치를 출발점으로 설계 확정 (특히 template_adherence 시점 문제, 카탈로그 동적 로드 방식, 추천 로직). 스펙은 `docs/superpowers/specs/`에.
2. **superpowers:writing-plans** — 스펙 승인 후 구현 계획을 `docs/superpowers/plans/`에.
3. **superpowers:subagent-driven-development** — 계획 실행 (이 repo에서 검증된 패턴; 단, SVG 페이지 생성이 아닌 코드/문서 수정이므로 위임 제약 없음).
4. **ppt-master** — 파이프라인 검증용 테스트 덱 생성 시.
