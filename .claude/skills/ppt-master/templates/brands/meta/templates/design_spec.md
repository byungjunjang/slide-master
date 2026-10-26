---
brand_id: meta
kind: brand
summary: Meta brand identity — 하드웨어 제품 발표(VR/AR), 브랜드 캠페인, 커머스/구매 퍼널 프레젠테이션
keywords: [meta, hardware, commerce, product-launch, cobalt]
primary_color: "#0064E0"
---

# Meta Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.
> Source: getdesign.md DESIGN-meta.md (site design-system analysis, alpha).

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Meta |
| Use Cases | 하드웨어 제품 발표(Quest VR, Ray-Ban Meta AI glasses류), 브랜드 캠페인, 구매/커머스 퍼널 프레젠테이션 |
| Tone | 확신에 찬 제품 머천다이징 보이스 — tech-forward, optimistic, 사진 중심 |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#0064E0` | fact | Action/구매 CTA 코발트 블루 |
| primary-deep | `#0457CB` | fact | 프레스 상태 |
| secondary | `#1876F2` | fact | Facebook Blue 계열 링크/보조 |
| accent (positive) | `#31A24C` | fact | 성공 상태 |
| accent (alert) | `#E41E3F` | fact | 위험/경고 상태 |
| text | `#1C1E21` | fact | 본문 잉크 |
| bg | `#FFFFFF` | fact | 캔버스 |
| surface | `#F1F4F7` | fact | 소프트 서피스 |
| border | `#CED0D4` | fact | 헤어라인 |

primary는 구매/CTA 전용 시그널이며, 그 외 강조는 텍스트 웨이트와 서피스 전환(백↔소프트그레이)으로 처리한다.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `"Optimistic VF", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif` | 500 |
| body | `"Optimistic VF", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif` | 400 |

> Optimistic VF는 Meta 독점 가변 폰트. 설치되지 않은 환경에서는 Helvetica Neue/Arial 폴백. 락 시 "설치 또는 PPTX 임베드 필요" 명시.

## IV. Logo

- 번들된 로고 파일 없음. 실제 사용 시 사용자가 `images/`에 로고를 추가.
- Cover: 로고 사용 시 헤더 우측 상단 권장

## V. Voice & Tone

- Formality: neutral-confident
- Person: we / you
- Emoji: avoid
- Abbreviations: spell-out-first-use

## VI. Icon Style

- Preference: filled

> 필 아이콘 + 풀필(100px) 라운드 버튼 문법과 어울림. `chunk-filled` 또는 `tabler-filled` 권장.
