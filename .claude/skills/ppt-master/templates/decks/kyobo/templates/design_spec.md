---
deck_id: kyobo
kind: deck
native_structure_mode: structured
category: brand
summary: 교보문고 PPT 양식 — 사내 업무 보고, 과제 추진 현황, 전략·실행 계획, 팀 단위 정기 보고용 네이비·그린 덱
keywords: [kyobo, 교보문고, 사내보고, 업무보고, 추진현황, 로드맵]
primary_color: "#003975"
canvas_format: ppt_kyobo
canvas_width: 1280
canvas_height: 840
canvas_viewbox: "0 0 1280 840"
source_canvas_width: 1280
source_canvas_height: 840
source_viewbox: "0 0 1280 840"
replication_mode: fidelity
page_count: 26
placeholders:
  01_cover: ["{{TITLE}}", "{{DATE}}", "{{AUTHOR}}"]
  02_chapter: ["{{CHAPTER_NUM}}", "{{CHAPTER_TITLE}}"]
  02_toc: ["{{PAGE_TITLE}}", "{{TOC_ITEM_1_TITLE}}", "{{TOC_ITEM_1_DESC}}", "{{PAGE_NUM}}"]
  03_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{PAGE_NUM}}"]
  03a_content_phase: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03b_content_tiles: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03c_content_compare: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03d_content_table: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03e_content_kpi: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03f_content_timeline: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03g_content_asis_tobe: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03h_content_summary: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03i_content_chart: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03j_content_action: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  04_ending: ["{{THANK_YOU}}", "{{CONTACT_INFO}}"]
  03k_content_photo_split: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03l_content_feature_cards: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03m_content_kpi_hero: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03n_content_process_steps: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03o_content_matrix: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03p_content_quote: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03q_content_layers: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03r_content_hub_spoke: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03s_content_gallery: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03t_content_plan_compare: ["{{PAGE_TITLE}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  05_photo_hero: ["{{TITLE}}", "{{SUBTITLE}}"]
---

# Kyobo PPT — Design Specification

> 첨부된 교보문고 PPT 양식(`PPT_양식.pptx`, 5장)에서 역추출했다. 원본 슬라이드는 10445750×6858000 EMU(1280×840 비율)로 ppt169가 아니다. 이 덱은 **ppt169(1280×720)로 정규화**했으며, 세로 좌표는 720/840 비율로 환산했고 글자 크기·선 굵기는 환산하지 않았다.

---

## I. Template Overview

| Property | Description |
| --- | --- |
| **Template Name** | kyobo |
| **Use Cases** | 사내 업무 보고, 과제 추진 현황, 단계별 실행 계획, 현황·개선 비교, 지표 요약, 이슈·액션 관리 |
| **Design Tone** | 절제된 흰 바탕 + 네이비·그린 두 색. 장식은 표지 곡선과 제목 아래 라인뿐 |
| **Theme Mode** | Light (white) |

한눈에 보이는 식별 요소: 표지를 가로지르는 **녹색→네이비 곡선**, 본문 상단의 **좌 1/4 그린 + 나머지 네이비 라인**, 우측 상단 **KYOBO 교보문고 로고**.

**Fidelity notes**: 원본 5장 중 표지(01)·본문 빈 페이지(03)·단계 칩(03a)·라벨 타일(03b)·비교 카드+결론(03c)은 원본 구성을 그대로 따른다. 원본에 없는 02_chapter, 02_toc, 03d~03j, 04_ending은 **원본 스타일을 유지해 새로 설계한 확장 페이지**다.

---

## II. Color Scheme

| Role | HEX | Source | Purpose |
| --- | --- | --- | --- |
| Navy (primary) | `#003975` | master / layout | 제목 라인 우측, 활성 칩, 표 헤더 밴드, 강조 면, KPI 수치 |
| Green (accent) | `#4DB848` | master / layout | 제목 라인 좌측 1/4, 로고 새싹. 면·선에만 사용, 텍스트 금지 |
| Wave navy | `#1E3B71` | cover image | 표지·챕터·엔딩 곡선 우측 구간 |
| Wave green | `#4CB848` | cover image | 표지·챕터·엔딩 곡선 좌측 구간 |
| Cover navy | `#002060` | slide 1 | 표지 제목, 표지 세로선 |
| Steel | `#1F497D` | slide 1 | 표지 날짜·팀명 |
| Ink | `#000000` | slides | 제목과 본문 |
| Ink muted | `#444462` | slide 3 | 보조 설명, 점선 박스 테두리 |
| Gray tile | `#F2F2F2` | slide 4 | 라벨 타일, 요약 박스 배경 |
| Gray chip | `#D9D9D9` | slides 3, 5 | 비활성 단계 칩, 번호 칸 |
| Gray line | `#E8EBED` | slide 5 | 카드 외곽선, 행 구분선 |
| Rule gray | `#808080` | slide 5 | 카드 제목 밑줄 |
| Dashed gray | `#BFBFBF` | slide 5 | 결론 박스 점선 |

### Color Rules

- 한 슬라이드의 강조색은 네이비 하나. 그린은 로고와 제목 라인 외에는 쓰지 않는다.
- 강조할 항목(활성 단계, 표 헤더, 현재 마일스톤)만 네이비 면 + 흰 글자, 나머지는 회색 계열.
- 상태 칩은 색상 외에 글자(진행중/예정/완료)를 반드시 함께 넣는다.
- 원본에 없는 오렌지(`#FBAE40`)·코랄(`#F26B43`)은 마스터에만 있고 쓰이지 않으므로 이 덱에서는 사용하지 않는다.

---

## III. Typography

설치형 Pretendard 고정 정책(`references/strategist.md` §g)을 따른다. 원본의 나눔고딕·맑은 고딕 지정은 이 정책에 따라 Pretendard로 대체했다.

| Weight | `font-family` | `font-weight` |
| --- | --- | --- |
| 400 | `Pretendard, 'Malgun Gothic', sans-serif` | (none) |
| 700 | `Pretendard, 'Malgun Gothic', sans-serif` | `700` |
| 800 | `'Pretendard ExtraBold', Pretendard, 'Malgun Gothic', sans-serif` | (none) |

| Role | px | Weight | Use |
| --- | --- | --- | --- |
| Cover / chapter / ending title | 48 | 800 | 원본 36pt |
| Page title | 32 | 800 | 원본 24pt |
| Key message | 32 | 700 | 원본 24pt, 가운데 정렬, 따옴표로 감쌈 |
| Subhead / label | 21.33 | 700 | 원본 16pt |
| Body strong | 18.67 | 700 | 원본 14pt |
| Body | 16 | 400 | 원본 12pt |
| Caption | 13.33 | 400 | 원본 10pt |
| KPI figure | 56 | 800 | 확장 페이지(03e) |

---

## IV. Signature Design Elements

- **표지 곡선**: 좌측 가장자리(y≈404)에서 시작해 하단 중앙(y≈538)에서 그린→네이비로 바뀌고 우측으로 올라가는(y≈300) 두께 18px 곡선. 원본 이미지의 중심선을 샘플링해 벡터 경로로 재현했다.
- **제목 라인**: y=87, 높이 6px, 전폭. x 0–317 그린, 317–1280 네이비.
- **로고**: 본문 우측 상단 `images/kyobo-logo-body.jpeg`, 표지·엔딩 우측 하단 `images/kyobo-logo-cover.jpeg`. 원본 해상도가 낮으므로 확대하지 않는다.
- **박스 문법**: 모서리는 직각, 그림자 없음. 일반 박스는 점선(dotted), 활성·결론 박스는 파선(dashed).
- **목록 기호**: `○`(주 항목), `-`(하위), `▪`(타일 옆). 키 메시지는 `“ ”`로 감싼다.
- **레이아웃 리듬**: 제목(y 16–64) → 라인(y 87) → 키 메시지(y 107–155) → 본문(y 190–680) → 페이지 번호(우하단 `#003975` 12.6px).
- **Layout 구조**: `01_cover`, `02_chapter`, `02_toc`, `03_content`, `03c_content_subhead`, `04_ending`은 각자의 Layout, 나머지 키 메시지형 변형(03a·03b·03d~03j)은 `03_content_keymsg` Layout 하나를 공유하며 슬라이드 내부 구성만 다르다.

---

## V. Page Roster

| File | Layout key / picker name | Role | Description |
| --- | --- | --- | --- |
| `01_cover.svg` | `01_cover` / Cover | cover | 곡선, 가운데 정렬 제목, 세로선이 붙은 날짜·팀명, 우하단 로고 |
| `02_chapter.svg` | `02_chapter` / Chapter | chapter | *확장.* 곡선 + 큰 그린 번호 + 챕터 제목 |
| `02_toc.svg` | `02_toc` / Table of Contents | toc | *확장.* 제목 라인 + 번호 칸 5행(제목·설명) |
| `03_content.svg` | `03_content` / Content | content | 제목, 라인, 로고, 자유 본문 영역 |
| `03a_content_phase.svg` | `03_content_keymsg` | content | 단계 라벨 + 화살표 칩 3개(활성 1) + 점선 세부과제 박스 |
| `03b_content_tiles.svg` | `03_content_keymsg` | content | 회색 라벨 타일 + ▪ 목록 3행 |
| `03c_content_compare.svg` | `03c_content_subhead` / Content Subhead | content | 소제목, ○ 요점, 번호 카드 2개, 깔때기, 결론 박스 |
| `03d_content_table.svg` | `03_content_keymsg` | content | *확장.* 네이비 헤더 밴드, 회색 라벨 열, 행 구분선 표 |
| `03e_content_kpi.svg` | `03_content_keymsg` | content | *확장.* 지표 카드 4개 + 시사점 박스 |
| `03f_content_timeline.svg` | `03_content_keymsg` | content | *확장.* 5개 마일스톤 타임라인 + 점선 과제 박스 |
| `03g_content_asis_tobe.svg` | `03_content_keymsg` | content | *확장.* 현황(회색)/개선방향(네이비) 비교 + 화살표 |
| `03h_content_summary.svg` | `03_content_keymsg` | content | *확장.* 배경·현황·이슈·제언 4행 요약 |
| `03i_content_chart.svg` | `03_content_keymsg` | content | *확장.* 차트 영역 + Insight 목록 |
| `03j_content_action.svg` | `03_content_keymsg` | content | *확장.* 과제·담당·일정·상태 칩 관리표 |
| `03k_content_photo_split.svg` | `03_content_keymsg` | content | *확장 v2.* 좌측 이미지 패널 + 번호 원 포인트 3개 + 시사점 박스 |
| `03l_content_feature_cards.svg` | `03_content_keymsg` | content | *확장 v2.* 아이콘 원 + 제목 + 설명 카드 3개(녹색/네이비 상단 바) |
| `03m_content_kpi_hero.svg` | `03_content_keymsg` | content | *확장 v2.* 네이비 대형 지표 패널(140px) + 보조 지표 타일 3개 |
| `03n_content_process_steps.svg` | `03_content_keymsg` | content | *확장 v2.* 번호 원 5단계 프로세스 + 현재 단계 강조 + 결과 바 |
| `03o_content_matrix.svg` | `03_content_keymsg` | content | *확장 v2.* 2×2 매트릭스(축 라벨, 우선 사분면 네이비) |
| `03p_content_quote.svg` | `03_content_keymsg` | content | *확장 v2.* 큰 인용부호 + 48px 핵심 문장 + 근거 칩 3개 |
| `03q_content_layers.svg` | `03_content_keymsg` | content | *확장 v2.* 네이비 틴트 4단 계층 + 우측 설명선 |
| `03r_content_hub_spoke.svg` | `03_content_keymsg` | content | *확장 v2.* 중앙 허브 원 + 4개 영역 노드 |
| `03s_content_gallery.svg` | `03_content_keymsg` | content | *확장 v2.* 이미지 카드 3개(번호 태그·캡션) + 출처 바 |
| `03t_content_plan_compare.svg` | `03_content_keymsg` | content | *확장 v2.* 3개 대안 비교(권고안 네이비 강조) + 권고 결론 박스 |
| `05_photo_hero.svg` | `05_photo_hero` / Photo Hero | section | *확장 v2.* 전면 이미지 + 네이비 스크림 + 64px 제목(구분 페이지·슬로건) |
| `04_ending.svg` | `04_ending` / Ending | ending | *확장.* 곡선 + 감사 문구 + 연락처, 우하단 로고 |

---

## VI. Assets

| File | Size | Usage |
| --- | --- | --- |
| `images/kyobo-logo-body.jpeg` | 288×121 | 본문 페이지 우측 상단 로고(KYOBO 교보문고, 흰 배경) |
| `images/kyobo-logo-cover.jpeg` | 214×100 | 표지·엔딩 우측 하단 로고(흰 배경) |

로고는 흰 바탕 전용이며 색 반전·재채색 금지.

---

## VII. Variation Guide (v2 — 색 톤 유지, 형태 확장)

**유지하는 것**: 네이비 `#003975`·그린 `#4DB848` 두 색, 제목 라인·로고 위치, 직각 박스 기본, 그림자 없음, `○ - ▪` 기호, 한 슬라이드 한 강조색(네이비).

**새로 허용하는 것** (원본 테마 팔레트의 보조색 `#3264C8`·`#4BACC6`·`#32B432`는 차트 계열 구분이 꼭 필요할 때만):

| 요소 | 값 | 용도 |
| --- | --- | --- |
| navy-50 | `#E6EEF7` | 강조 카드 배경, 결론 박스 |
| navy-100 | `#CBD9EA` | 이미지 자리, 큰 인용부호, 어두운 면 위 보조 글자 |
| navy-300 | `#8FAFD4` | 계층·막대 그래프 중간 단계 |
| navy-500 | `#4D7FB5` | 계층·막대 그래프 진한 단계 |
| green-50 | `#EAF6E9` | 보조 카드 배경(텍스트 아님) |
| 둥근 모서리 | `rx=6` 만 | 카드·노드(원형 아이콘 배경은 원) |
| 원·번호 배지 | navy 원 + 흰 숫자 | 단계·포인트 번호 |
| 상단 바 | 높이 8px, 그린 또는 네이비 | 카드 상단 강조 |
| 아이콘 | `tabler-outline`, 네이비 원 위 흰색 60px | 특징 카드 |
| 전면 이미지 | 네이비 `#002060` 스크림 투명도 0.5 | 구분·슬로건 페이지 |

**페이지 선택 가이드**

| 전달하려는 것 | 쓸 페이지 |
| --- | --- |
| 단계·로드맵 | `03a` 화살표 칩 / `03n` 번호 프로세스 / `03f` 타임라인 |
| 현재→개선 | `03g` AS-IS/TO-BE |
| 숫자 하나가 핵심 | `03m` 대표 지표 |
| 숫자 여러 개 | `03e` KPI 카드 / `03i` 차트 |
| 개념 3가지 설명 | `03l` 특징 카드 |
| 현장·사례 사진 | `03k` 이미지 분할 / `03s` 갤러리 |
| 구조·관계 | `03q` 계층 / `03r` 허브 |
| 우선순위·분류 | `03o` 매트릭스 |
| 대안 선택 | `03t` 대안 비교 |
| 한 문장 메시지 | `03p` 인용 / `05` 전면 이미지 |
| 목록 요약 | `03h` 요약 / `03b` 라벨 타일 / `03d` 표 |

**크기 기준(발표용 권장)**: 페이지 제목 32~40, 핵심 메시지 32, 라벨·본문 24, 설명 18, 대표 지표 56~140. 원본 보고서용 기준(본문 16~18)은 인쇄·검토용 문서에만 쓴다.

**이미지 규칙**: 사진은 색 보정 없이 그대로 쓰고, 텍스트를 올릴 때만 네이비 스크림을 깐다. 이미지 자리는 `#CBD9EA` 사각형으로 두고 프로젝트에서 사진으로 교체한다. 주제와 어긋나는 사진은 쓰지 않고 아이콘·도형으로 대체한다.

**글꼴**: 원본은 나눔고딕이지만 이 설치본은 Pretendard로 고정한다(PC에 글꼴 필요). 제목 굵기는 ExtraBold, 없으면 Bold로 대체된다.
