---
brand_id: mckinsey
kind: brand
summary: McKinsey consulting-style identity — 전략 보고/분석 브리핑, 네이비 구조색 + 시안 포인트, 액션 타이틀 보이스
keywords: [consulting, strategy, navy, mckinsey-style, executive]
primary_color: "#0F2A4A"
---

# McKinsey Style Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
>
> **Provenance**: extracted from [`templates/decks/mckinsey/`](../../../decks/mckinsey/templates/design_spec.md) (source of truth). 색/타이포/보이스 변경은 deck에서 먼저 고치고 이 파일에 동기화한다. 페이지 구조(타이틀 룰 / Source 라인 / 다크 디바이더)와 크기 램프는 deck 소관이며 여기 기록하지 않는다.
>
> Style homage benchmarked from the seulee26/mckinsey-pptx generator — not an official McKinsey identity; no trademark assets.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | McKinsey Style (homage) |
| Use Cases | 전략 보고, 시장/산업 분석, 경영진 브리핑, 실행 로드맵, 투자 검토 |
| Tone | Restrained, hypothesis-driven, evidence-first — MBB consulting register |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| bg | `#FFFFFF` | approx | Pure white page background |
| primary (navy) | `#0F2A4A` | approx | Structural anchor — chrome, table headers, key numbers, chart series 1 |
| navy-deep | `#0A1F3D` | approx | Full-bleed background for dark structural pages |
| accent | `#2E9BD6` | approx | Sole pointer — focus series, emphasis rule, highlight number |
| blue-mid | `#1F6FA8` | approx | Chart series 2 |
| blue-light | `#4FB2E5` | approx | Chart series 3, tint fills, secondary text on dark pages |
| text | `#1A1A1A` | approx | Primary text — never pure `#000` |
| text-secondary | `#888888` | approx | Source lines, page numbers, captions |
| rule | `#999999` | approx | Title underline rule |
| grid | `#D0D0D0` | approx | Footer rule, chart gridlines |
| border | `#E8E8E8` | approx | Hairline dividers, table row rules |
| surface-alt | `#F2F2F2` | approx | Table banding, quiet panel background |
| positive | `#4CAF50` | approx | Traffic light "on track" — data context only |
| warning | `#F4C57A` | approx | Traffic light "at risk" — data context only |
| negative | `#E04E5E` | approx | Traffic light "off track" — data context only |

All values derived from the seulee26/mckinsey-pptx benchmark `theme.py` — third-party approximations, not official McKinsey brand values. Usage conventions that travel with the identity: navy is structure, accent is pointer under a single-focus rule (accent marks exactly ONE focus per page; cross-exhibit repetition only for the same focus; a verdict band's 2px accent rule is a separate structural account, max 1 per page); grayscale-first (slides must read without blue); charts use the navy ladder `#0F2A4A → #1F6FA8 → #4FB2E5` with `#2E9BD6` reserved for the single focus series, never multi-hue; traffic-light colors are data-meaning only and always pair with a text label; gradients / drop shadows / glow / 3D forbidden; corners square (radius ≤ 4px).

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `Pretendard, 'Malgun Gothic', sans-serif` + `font-weight: 700` | 700 |
| body | `Pretendard, 'Malgun Gothic', sans-serif` | 400 |
| sub / exhibit title | `'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif` | 600 |
| caption / label | `'Pretendard Medium', Pretendard, 'Malgun Gothic', sans-serif` | 500 |

> Install-local Pretendard lock (`references/strategist.md` §g): intermediate weights are authored as installed family names. Consulting hierarchy comes from weight/size only — no serif or Arial substitution. Size hierarchy / type scale is deck-layout scope — see the mckinsey deck spec §IV; not locked here.

## IV. Logo

- None. No logo mark is bundled (style homage; no trademark assets). Text-only self-identification is permitted (e.g., organization name in the cover footer).

## V. Voice & Tone

- Formality: formal-institutional
- Person: third-person (직접 호명 없음)
- Emoji: forbidden
- Abbreviations: spell-out-first-use
- Forbidden phrases: 여러분 / 우리는 / 함께해요
- **Action-title doctrine**: every content-page title is a complete declarative sentence stating the so-what ("시장은 정체되어 있다", not "시장 현황"); reading titles in page order must reconstruct the storyline (pyramid principle); no label-only or question-mark titles on evidence pages
- Evidence discipline: every data claim carries a `Source:` / `자료:` attribution

## VI. Icon Style

- Preference: stroke

> `tabler-outline` line-art, 2px stroke, bare icons only — no circle wrappers, no colored badges, no pack mixing, no emoji. Icons are rare in this identity: prefer rules, tables, and charts. Sequential number markers are agenda-only in the paired deck; elsewhere taxonomy is carried by keyword kickers (13.3/600 labels), ballot squares (18px outline), 6×6px square marks, or short navy rules (28×4px).
