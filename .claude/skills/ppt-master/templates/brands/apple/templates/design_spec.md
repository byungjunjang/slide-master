---
brand_id: apple
kind: brand
summary: Apple 계열 모노크롬 미니멀 아이덴티티 — 잉크 단일 시그널, 서피스 반전 강조, 조용한 프리미엄 보이스
keywords: [monochrome, minimal, keynote, apple-style, gallery, premium]
primary_color: "#1D1D1F"
---

# Apple Monochrome Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
>
> **Provenance**: extracted from [`templates/decks/apple/`](../../../decks/apple/templates/design_spec.md) (source of truth). 색/타이포/보이스 변경은 deck에서 먼저 고치고 이 파일에 동기화한다. 페이지 구조(서피스 교대 리듬 / 푸터 크롬 / 페이지별 마진)와 크기 램프는 deck 소관이며 여기 기록하지 않는다.
>
> Ported from the **Vitrine** design system — an original photography-first minimalist system built on widely-used, non-proprietary Apple-adjacent principles. Not a recreation of Apple's branded product or proprietary UI; no trademark assets, logos, or wordmarks are bundled.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Apple Monochrome (Vitrine port) |
| Use Cases | 제품 발표, 브랜드 스토리, 디자인 리뷰, 비전 키노트, 조용한 프리미엄 톤의 전략 브리핑 |
| Tone | Reverent, premium, unhurried — museum-gallery quiet. The page reads, it doesn't scan |

**Anti-mood**: "gradient SaaS dashboard", "consulting density grid", "decorative infographics", "emoji-flecked marketing deck", "rainbow category palette".

## II. Color Scheme

Pure monochrome. **악센트 컬러가 존재하지 않는다** — 아래 15개가 전부다.

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| canvas | `#ffffff` | fact | 지배적 라이트 캔버스 |
| pearl | `#fafafc` | fact | 니어-화이트 고스트 필 (희소) |
| parchment | `#f5f5f7` | fact | 시그니처 오프화이트 — 교대 서피스, 이미지 플레이스홀더 배경, 아이콘 칩 |
| hatch-fg | `#ececef` | fact | 이미지 플레이스홀더 해칭 전경 |
| hairline | `#e0e0e0` | fact | 1px 카드/행/차트 그리드 보더 |
| tint-4 | `#d2d2d7` | fact | 차트 래더 최희석 단계 |
| tint-3 | `#c7c7cc` | fact | 차트 래더 — 비강조 바/세그먼트 |
| label-muted | `#a8a8ad` | fact | 플레이스홀더 안내 라벨 |
| ink-muted-48 | `#7a7a7a` | fact | 푸터 페이지 라벨, legal fine-print |
| ink-muted-60 | `#6e6e73` | fact | 키커, 본문 보조, 축 라벨, 푸터 마크 |
| ink-muted-80 | `#333333` | fact | pearl 서피스 위 완화 본문 (희소) |
| tile-dark-2 | `#272729` | fact | 다크 타일 마이크로스텝 (확장용) |
| ink | `#1d1d1f` | fact | 헤드라인·본문·차트 단일 강조 — 시스템의 유일한 시그널 |
| tile-dark-3 | `#161617` | fact | 다크 타일 마이크로스텝 (확장용) |
| black | `#000000` | fact | 풀블리드 포토그래픽 보이드 + 그림자 flood 전용 — 텍스트 색으로 절대 금지 |

전 값 `fact` — 소스 `colors_and_type.css` 직독. 원본 브리프의 블루 악센트는 모노크롬 빌드에서 이미 제거되었으며 복원하지 않는다.

아이덴티티와 함께 이동하는 사용 규칙: **one ink, one signal** — `#1d1d1f`가 라이트 서피스 위 모든 강조를 담당하고 인터랙티브/강조 신호에 색상(hue)은 없다. **강조는 서피스 반전이 먼저**(white ↔ parchment), 그 다음이 웨이트이며 세 번째 수단은 없다. 차트는 `#1d1d1f → #6e6e73 → #c7c7cc → #d2d2d7` 래더를 쓰고 최농도 잉크는 페이지당 단일 강조 1개(피크 바 / 주 계열 / 최대 세그먼트)에만 부여한다. 본문 뮤트 기본값은 `#6e6e73`이고 `#7a7a7a`는 푸터 라인 전용. **그림자는 시스템 전체에 단 1종** — `feDropShadow dx=3 dy=5 stdDeviation=15 flood-opacity=0.22`, **서피스 위 이미지에만**. 카드·버튼·텍스트 그림자, 악센트 컬러, 그라디언트 장식, 글로우, 3D는 금지. 카드는 1px `#e0e0e0` 헤어라인만 두른다. 모서리 문법은 `0` / `4`(차트 스와치·바) / `8` / `12`(인라인 이미지) / `18`(카드) / `9999`(필)뿐이며 중간값을 섞지 않는다.

## III. Typography

Install-local Pretendard lock (see `references/strategist.md` §g). SF Pro Display의 타이트 케이던스를 Pretendard로 재현한다 — Pretendard는 본래 Apple 시스템 폰트의 크로스플랫폼 대체로 설계되어 외형 친화도가 높다. SF Pro는 사용하지 않는다.

| Role | `font-family` | Weight |
|---|---|---|
| airy lead / closing copy | `'Pretendard Light', Pretendard, 'Malgun Gothic', sans-serif` | 300 |
| body / labels / axis | `Pretendard, 'Malgun Gothic', sans-serif` | 400 |
| headline / kicker / stat / mark | `'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif` | 600 |
| reserve (unused in ported roster) | `Pretendard, 'Malgun Gothic', sans-serif` + `font-weight="700"` | 700 |

중간 웨이트는 설치 패밀리명 + normal weight로 저작한다(`font-weight` 속성은 700에만).

**웨이트 래더는 300 / 400 / 600 / 700 네 단계뿐이다. 500(`'Pretendard Medium'`)은 의도적으로 부재하며 사용 금지.** 헤드라인은 **600**이지 700이 아니다. 300은 실재하지만 희소하다.

**자간 문법**: 디스플레이 사이즈일수록 강한 음수 자간이 시그니처다 — 112px `-3`, 96px `-2.6`, 60px `-1.6`, 52px `-1.2`, 44px `-1`, 본문 17px `-0.374`. 본문은 16px이 아니라 **17px**(읽는 속도를 정하는 1px). 키커는 14px 600 대문자에 양수 자간 `+0.84`.

**한글 자간 완화**: 위 값은 라틴 기준이다. 한글 비중 ≥ 50%인 런은 **× 0.5**로 완화한다(112px → `-1.5`, 52px → `-0.6`, 17px → `-0.19`). 혼합 런은 지배 언어 기준 1개 값을 런 전체에 적용하고 `<tspan>`별로 쪼개지 않는다. 양수 자간은 언어와 무관하게 유지한다.

## IV. Logo

**로고 자산 없음.** 이 브랜드는 로고·워드마크 파일을 번들하지 않는다(소스의 워드마크는 플레이스홀더였으므로 이식하지 않았다).

- 브랜드 마크는 **텍스트 슬롯**으로 운용한다 — 푸터 좌측(600 / 12px / `-0.4` / `#6e6e73`)과 클로징 페이지의 대형 마크(600 / 104px / `-3` / `#1d1d1f`).
- 마크는 디스플레이 페이스에 타이트 트래킹, 잉크(라이트 서피스) 또는 화이트(다크 서피스) 단색으로 세운다.
- 실제 로고 이미지를 보유했다면 브랜드 워크스페이스의 `images/`에 넣고 이 섹션에 경로·사용 규칙을 기록한 뒤 사용한다. 그 전까지 로고 이미지 삽입은 금지.

## V. Voice & Tone

**확신에 차고, 조용하고, 선언적으로.** 카피는 짧고 단호하며 절대 얼버무리지 않는다. 헤드라인은 명사구 또는 2~3어 선언문이다 — 사물의 이름을 부르고 나머지는 이미지와 여백에 맡긴다.

| 항목 | 규칙 |
|---|---|
| 케이싱 | 문장 케이스 전면. Title Case·ALL CAPS 금지 (예외: 키커는 대문자로 저작) |
| 인칭 | 중립/제품 중심. 헤드라인에서 "우리"/"저희"를 쓰지 않는다 |
| 구두점 | 헤드라인은 마침표로 끝나는 케이던스를 허용한다 — 마침표가 리듬의 일부다 |
| 숫자 | 구체적·무장식. 무게를 지닌 값만 올린다. 장식용 지표(stat-slop) 금지 |
| 이모지 | **절대 금지** — 갤러리의 정적을 깬다 |
| 길이 | 서브카피는 1~2행 현재형, 혜택 우선 |

**Tone examples**: 헤드라인 *"Titanium. So strong. So light. So Pro."* / 서브카피 *"The most advanced display we've ever made."* / 리걸 *"Available in the second half of 2026. Subject to change."*

한국어 카피에도 동일 문법: 체언 종결 또는 단문 평서형("가볍게. 그리고 앞서서."), 감탄부호·물결표·이모지 금지, 존대 남용 금지.

## VI. Icon Style

- **접근**: 미니멀·희소·라인 기반. 콘텐츠 페이지는 아이콘 없이 타입과 여백이 일한다 — 아이콘을 추가하고 싶어지면 먼저 "이 아이콘이 없으면 의미가 사라지는가"를 묻는다. 대개 답은 아니오다
- **스타일**: 씬 스트로크 모노라인, `stroke-width="1.5"`, `fill="none"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, 26px 박스
- **색**: 라이트 서피스 위 잉크(`#1d1d1f`) 단색
- **컨테이너 칩**: parchment 원(r=28, `#f5f5f7`) — white 서피스에서만 보이는 조용한 칩이다. parchment 서피스에서는 배경과 동색이라 보이지 않으므로 아예 넣지 않는다. 보이지 않는 칩을 흰 원으로 승격해 원본에 없던 크롬을 만들지 않는다
- **라이브러리**: [`templates/icons/`](../../../icons/)의 line 계열만 사용
- **금지**: 이모지(유니코드 글리프 아이콘 해킹 포함), 필드/솔리드 아이콘, 다색 아이콘, 콘텐츠 타일 장식 아이콘
