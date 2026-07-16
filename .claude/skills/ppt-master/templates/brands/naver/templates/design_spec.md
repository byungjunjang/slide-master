---
brand_id: naver
kind: brand
summary: NAVER corporate identity — IR/실적발표, 재무 보고, 네이버 관련 기업·서비스 자료
keywords: [naver, green, corporate, ir, korean]
primary_color: "#03C75A"
---

# NAVER Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
> Extracted 2026-07-16 from the Naver IR Design System bundle (tokens verified against the official
> 4Q25 / 1Q26 실적발표 decks and the NAVER brand token reference; brand guide:
> https://www.navercorp.com/company/brandGuide). Fixed-page IR structure lives in the companion
> deck workspace `templates/decks/naver_ir/`.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | NAVER |
| Use Cases | IR/실적발표, 재무 보고, 투자자 미팅, 네이버 관련 기업·서비스 소개 |
| Tone | Restrained, factual, investor-grade — 절제된 프린트형 매체, 장식 없음 |

## II. Color Scheme

| Role | HEX | Provenance |
|---|---|---|
| primary | #03C75A | fact — NAVER identity green (brand token reference) |
| secondary | #4E7599 | fact — 파이낸셜 플랫폼 slate blue (IR segment color) |
| accent | #4472C4 | fact — IR accent blue (charts, reclassification, investment series) |
| text | #262626 | fact — body ink (titles use #000000) |
| bg | #FFFFFF | fact — content canvas |
| cover | #5BDB7D | fact — full-bleed cover/closing surface observed in the source decks; lighter than identity green, never used for accents |

**Application rules**: green is identity + core segment + key table rows + highlight boxes; slate blue is reserved for the financial-platform segment; accent blue for charts/투자 series. Max two accent hues per page. Neutrals: muted `#7F7F7F`, faint `#BFBFBF`, watermark `#D9D9D9`, hairline `#E5E5E5`.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | Pretendard ("Pretendard ExtraBold" install-local cut) | 800 |
| body | Pretendard | 400 |
| kpi/label | Pretendard | 700 |

Slight negative tracking (-0.02em titles / -0.01em body). Numerals use tabular figures where available. Follows the repository install-local Pretendard lock — no font files bundled here.

## IV. Logo

- Files (relative to this design_spec.md):
  - `../images/naver-wordmark-white.png` (357×75) — on the green cover/closing surface
  - `../images/naver-wordmark-gray.png` (357×75) — small top-right watermark on content pages (≈86px wide)
  - `../images/naver-wordmark-green.png` / `../images/naver-wordmark-black.png` (357×75) — light-surface lockups
  - `../images/naver-icon.svg` — official N glyph (simple-icons path); recolor via fill
- Usage: every-page (gray watermark on content pages; white lockup on brand-color surfaces)

## V. Voice & Tone

- Formality: formal — 합니다체 prose, noun-ending 개조식 bullets ("…YoY 16.3% 달성")
- Person: none (무인칭 서술; 직접 호칭 금지)
- Emoji: forbidden (느낌표·마케팅 수사도 금지)
- Abbreviations: finance vocabulary stays English (YoY, QoQ, FCF, CapEx, TPV, 1Q26); everything else Korean

## VI. Icon Style

- Preference: linear — but the brand is icon-averse: no icon system, no pictograms. If unavoidable, plain unicode arrow (→) or a 1.5px thin-stroke set, flagged as an addition.

## VII. Visual Assets

- Images and illustrations: `../images/` — wordmark lockups (4 PNG) + N glyph SVG
