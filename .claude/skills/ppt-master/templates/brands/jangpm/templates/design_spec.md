---
brand_id: jangpm
kind: brand
summary: Jangpm editorial identity — Korean lecture / report decks, 모노크롬 + 단일 인디고 액센트
keywords: [editorial, minimal, korean, lecture, report]
primary_color: "#4633E3"
---

# Jangpm Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
>
> **Provenance**: extracted from [`templates/decks/jangpm/`](../../../decks/jangpm/templates/design_spec.md) (source of truth). 색/타이포/보이스 변경은 deck에서 먼저 고치고 이 파일에 동기화한다. 페이지 구조·레이아웃 문법·GM 위치는 deck 소관이며 여기 기록하지 않는다.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Jangpm |
| Use Cases | 강의, 워크숍, 전략 브리핑, 분석 리포트, 사내 교육 자료 |
| Tone | Editorial, analytical, declarative — Korean lecture / report register |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| bg | `#FAFAF9` | fact | Warm off-white page background |
| surface | `#FFFFFF` | fact | Card / container |
| surface-alt | `#F5F5F4` | fact | Grouped row / nested card |
| text | `#1A1A1A` | fact | Primary text — never pure `#000` |
| text-secondary | `#6B7280` | fact | Secondary text |
| text-tertiary | `#9CA3AF` | fact | Captions, page numbers |
| border | `#E5E7EB` | fact | Default divider / hairline |
| border-strong | `#D4D4D4` | fact | Emphasis divider |
| primary (accent) | `#4633E3` | fact | Sole brand pointer — indigo |
| accent-soft | `#E8E5FC` | fact | Accent-tinted highlight background |
| accent-ink | `#2E1FB3` | fact | Accent pressed / dark |
| positive | `#059669` | fact | Data context only — growth / success |
| negative | `#E11D48` | fact | Data context only — decline / error |
| warning | `#D97706` | fact | Data context only — caution |

All values extracted verbatim from the jangpm `theme.json` (slide-svg). Usage conventions that travel with the identity: monochrome-first (slides must read in grayscale before accent); accent budget ≤ 2 events per slide; semantic colors (positive/negative/warning) are data-meaning only, never decorative; gradients / drop shadows / glow forbidden; charts use the single-accent opacity ladder `rgba(70, 51, 227, 0.85 / 0.60 / 0.40 / 0.25)`, never multi-hue.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif` (display) / `Pretendard, 'Malgun Gothic', sans-serif` + `font-weight: 700` (headline) | 700–800 |
| body | `Pretendard, 'Malgun Gothic', sans-serif` | 400 |
| sub / card title | `'Pretendard SemiBold', Pretendard, 'Malgun Gothic', sans-serif` | 600 |

> Install-local Pretendard lock (`references/strategist.md` §g): intermediate weights are authored as installed family names. Size hierarchy / type scale is deck-layout scope — see the jangpm deck spec §IV; not locked here.

## IV. Logo

- None. The brand has no logo mark; see §VII for the character asset (optional decoration, not a logo).

## V. Voice & Tone

- Formality: professional-neutral
- Person: third-person institutional (직접 호명 없음)
- Emoji: forbidden
- Abbreviations: spell-out-first-use
- Forbidden phrases: 여러분 / 우리는 / 함께해요
- Takeaway style: one declarative so-what sentence per slide, Korean-first, ≤ 30 chars ideal, never restating the title

## VI. Icon Style

- Preference: stroke

> `tabler-outline` line-art, 2px stroke, bare icons only — no circle wrappers, no colored badges, no pack mixing, no emoji. Fallback `tabler-filled` only for a deliberate solid glyph.

## VII. Visual Assets

- Images and illustrations: `../images/` — `jangpm-character.png` (브랜드 캐릭터; 커버/엔딩 하단 한정, 선택적)
