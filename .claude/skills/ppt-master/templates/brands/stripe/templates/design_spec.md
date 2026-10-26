---
brand_id: stripe
kind: brand
summary: Stripe 브랜드 아이덴티티 — 금융/핀테크 인프라 제품 소개, 개발자 대상 브리핑, 투자·재무 데크
keywords: [stripe, fintech, infrastructure, indigo, editorial]
primary_color: "#533AFD"
---

# Stripe Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
> Source: getdesign.md DESIGN-stripe.md (site design-system analysis, alpha — "an inspired interpretation").

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Stripe |
| Use Cases | 금융/핀테크 인프라 제품 소개, 개발자 대상 기술 브리핑, 투자·재무 데크 |
| Tone | 금융 인프라 브랜드 — 딥 네이비 + 일렉트릭 인디고, 얇은 웨이트의 에디토리얼 밀도 |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#533AFD` | fact | 일렉트릭 인디고 — 브랜드 시그널·CTA |
| primary-deep | `#4434D4` | fact | 프레스 상태 |
| secondary (dark) | `#1C1E54` | fact | 딥 네이비 — 다크 서피스 |
| accent (ruby) | `#EA2261` | fact | 보조 강조 |
| accent (magenta) | `#F96BEE` | fact | 그라디언트 메시 보조색 |
| text | `#0D253D` | fact | 본문 잉크 |
| text-muted | `#64748D` | fact | 보조 텍스트 |
| bg | `#FFFFFF` | fact | 기본 캔버스 |
| bg-soft | `#F6F9FC` | fact | 소프트 서피스 |
| border | `#E3E8EE` | fact | 헤어라인 |

상단 1/3 영역에 반복되는 그라디언트 메시(인디고→마젠타)가 시그니처 장식 — 커버 페이지 배경에 은은하게 재현 가능. 숫자/금액 표기는 tabular figures 사용.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `"SF Pro Display", system-ui, -apple-system, "Microsoft YaHei", sans-serif` | 300 |
| body | `"SF Pro Display", system-ui, -apple-system, "Microsoft YaHei", sans-serif` | 300 |

> 원본은 독점 가변폰트 Söhne(sohne-var). 디스플레이는 시그니처인 **얇은 웨이트(300) + 음수 자간**을 유지 — 두껍게 대체하면 브랜드 톤이 깨진다. 숫자가 들어가는 본문은 tabular-nums 스타일 권장.

## IV. Logo

- 번들된 로고 파일 없음. 필요 시 사용자가 `images/`에 추가.

## V. Voice & Tone

- Formality: professional-precise
- Person: we / you
- Emoji: avoid
- Abbreviations: common-abbrev-allowed (개발자 대상 약어 허용)

## VI. Icon Style

- Preference: stroke

> 핀테크 정밀함에 어울리는 얇은 스트로크 아이콘 권장 (`tabler-outline` 등).
