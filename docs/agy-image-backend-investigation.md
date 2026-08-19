# agy 다중 이미지 생성 테스트 기록 (2026-08-19)

교수님 피드백 "agy 사용 시 이미지가 여러 장 생성되지 않는다"를 재현하고 원인을 찾기 위한
작업 기록입니다. 소재는 `angl-article-p311.pdf`(post-orthodontic white spot lesion에
대한 resin infiltration 24개월 RCT)이며, 이 논문을 설명하는 슬라이드용 이미지 10장을
한 번의 매니페스트 실행으로 요청했습니다.

- 대상 어댑터: [`backend_agy.py`](../.claude/skills/ppt-master/scripts/image_backends/backend_agy.py)
- Antigravity CLI: `agy` 1.1.13 (`~/.local/bin/agy`)
- 매니페스트: 10항목. 원본과 실행 로그는 `.gitignore` 대상인 작업 폴더
  `projects/20260819_agy-batch-test/`에 남아 있어 저장소에는 포함되지 않습니다.

---

## 1. agy에 입력을 넣는 경로

어댑터는 이미지 한 장마다 `agy` 프로세스를 새로 띄웁니다. 실제로 실행된 명령은
다음과 같은 형태입니다.

```bash
~/.local/bin/agy \
  --model=gemini-3.1-pro \
  --effort=low \
  --print-timeout 10m \
  --log-file /var/folders/.../ppt-master-agy-<random>/agy.log \
  -p "<작업 지시문>"
```

| 입력 요소 | 전달 방식 | 비고 |
|---|---|---|
| 프롬프트 | `-p` 인자 하나에 담긴 평문 지시문 | stdin이나 파일 입력을 쓰지 않습니다 |
| 모델 | `--model=` | 기본값 `gemini-3.1-pro`, `AGY_MODEL`로 변경 |
| 추론 강도 | `--effort=` | 코드 기본값 `low`, `AGY_EFFORT`로 변경 |
| 제한 시간 | `--print-timeout 10m` | `AGY_TIMEOUT_MINUTES`로 변경 |
| CLI 로그 | `--log-file <임시경로>` | 실행마다 임시 디렉터리를 새로 만듭니다 |
| 출력 경로 | **전달 불가** | CLI가 출력 경로 인자를 받지 않습니다 |

`-p`로 넘기는 지시문은 `_build_task()`가 다음 형태로 조립합니다. 매니페스트의
프롬프트 원문은 손대지 않고 구분자 사이에 그대로 넣습니다.

```
Act strictly as a Text-to-Image synthesis engine.
DO NOT output code. DO NOT write a script. DO NOT use Python, PIL, matplotlib, SVG, or shell commands.
DO NOT explain. Call the built-in generate_image tool exactly once, then stop.

Use ImageName exactly: p01_wsl_overview
Use AspectRatio exactly: 16:9
Job token (bookkeeping only; never draw it): ppt-master-351bef45d01f48748f7c31242e3dd161

Use the following image prompt verbatim as the visual specification:
---PROMPT---
<매니페스트 prompt 원문>
---END PROMPT---
```

`ImageName`은 최종 저장 파일명의 stem이고, job token은 CLI 로그가 대화 ID를 남기지
않았을 때 대화를 역추적하는 용도입니다.

---

## 2. agy에서 출력을 받는 경로

`agy`는 표준출력으로 이미지를 돌려주지 않습니다. 실행 결과는 세 곳에 흩어져 있고,
어댑터는 그중 두 곳을 읽습니다.

| 경로 | 내용 | 어댑터 사용 |
|---|---|---|
| `--log-file`이 가리키는 CLI 로그 | gRPC/HTTP 수준 로그. `Created conversation <uuid>` 줄 | 대화 ID 추출 |
| `~/.gemini/antigravity-cli/brain/<대화ID>/.system_generated/logs/transcript.jsonl` | 대화 단계별 JSON Lines | 생성 여부 검증 |
| `~/.gemini/antigravity-cli/brain/<대화ID>/<ImageName>_<epoch_ms>.jpg` | 실제 이미지 파일 | 최종 파일 회수 |

`transcript.jsonl` 한 줄이 대화의 한 단계이고, 이미지 생성은 두 단계로 남습니다.

```jsonc
// 1) 모델이 도구를 부른 단계
{"step_index": 2, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
 "tool_calls": [{"name": "generate_image",
                 "args": {"AspectRatio": "\"16:9\"", "ImageName": "\"p01_wsl_overview\"",
                          "Prompt": "\"...\""}}]}

// 2) 도구가 결과를 돌려준 단계
{"step_index": 3, "source": "MODEL", "type": "GENERIC", "status": "DONE",
 "content": "Created At: ...\nCompleted At: ...\nUsing prompt: ...\n\nGenerated image is saved at /Users/.../brain/<대화ID>/p01_wsl_overview_1787103656145.jpg.\n\n Do not output the path ..."}
```

즉 **저장 경로는 결과 단계의 `content` 안에 문장으로 들어 있습니다.** 조사 시점의
어댑터는 이 문장을 읽지 않고, 대화 디렉터리에서 실행 시각 이후에 수정된 이미지
파일을 훑어 가장 최근 것을 고르고 있었습니다. 이 부분은 §5에서 바꿨습니다.

---

## 3. 재현 (수정 전)

`IMAGE_BACKEND=agy`, 동시 실행 3개(기본값)로 10항목 매니페스트를 돌렸습니다.

```bash
IMAGE_BACKEND=agy python3 .claude/skills/ppt-master/scripts/image_gen.py \
  --manifest projects/20260819_agy-batch-test/images/image_prompts.json \
  --output projects/20260819_agy-batch-test/images
```

첫 배치 3항목이 모두 아래 메시지로 실패했고, 어댑터는 항목마다 3회씩 재시도했습니다.

```
[FAIL] Antigravity did not execute its generate_image tool.
       The subscription image-generation path may be unavailable; no fallback image was accepted.
```

그런데 대화 디렉터리를 확인하면 **이미지는 실제로 만들어져 있었습니다.**

| 대화 ID | ImageName | 디스크의 파일 | 어댑터 판정 |
|---|---|---|---|
| `67c61400…` | p01_wsl_overview | `p01_wsl_overview_1787103656145.jpg` | 실패 처리 |
| `fb702e00…` | p02_bracket_plaque | `p02_bracket_plaque_1787103676366.jpg` | 실패 처리 |
| `1c705ca5…` | p03_enamel_demineralization | `p03_enamel_demineralization_1787103815265.jpg` | 실패 처리 |

즉 "여러 장이 생성되지 않는다"의 실체는 생성 실패가 아니라 **회수 실패**였습니다.
프로젝트 폴더에는 한 장도 도착하지 않았고, 매니페스트는 `Failed`로 남았습니다.

---

## 4. 원인

`_verify_generation()`이 transcript 원문에서 `"type": "GENERATE_IMAGE"` 문자열을
찾아 생성 여부를 판정하고 있었습니다. 그런데 CLI가 도구 결과 단계에 붙이는 라벨이
실행마다 다릅니다.

| 실행 | 단계 구성 | 도구 결과 라벨 |
|---|---|---|
| 8월 16일 단건 성공 | `USER_INPUT → CONVERSATION_HISTORY → EPHEMERAL_MESSAGE → PLANNER_RESPONSE → GENERATE_IMAGE` | `GENERATE_IMAGE` |
| 8월 19일 배치 | `USER_INPUT → CHECKPOINT → PLANNER_RESPONSE → GENERIC` | `GENERIC` |

배치 실행에서는 대화 첫머리에 `CHECKPOINT`(컨텍스트 요약)가 끼면서 단계 구성이
달라지고, 도구 결과가 `GENERIC`으로 기록됩니다. 라벨만 다를 뿐 내용은 동일해서,
같은 단계의 `content`에는 `Generated image is saved at …` 문장이 그대로 들어 있고
직전 `PLANNER_RESPONSE`에는 `tool_calls: [{"name": "generate_image", …}]`가 남습니다.

라벨 검사에서 걸리면 그 뒤의 파일 회수 로직은 아예 실행되지 않습니다. 그래서
멀쩡한 이미지가 대화 디렉터리에 남은 채로 항목이 `Failed`이 되고, 재시도 3회가
같은 실패를 반복하면서 구독 사용량만 3배로 소모했습니다.

과거 단건 테스트가 통과했던 이유도 여기서 설명됩니다. 한 장만 만들면 `CHECKPOINT`
없이 `GENERATE_IMAGE` 라벨이 붙는 경로로 들어가는 경우가 많아, 라벨 검사가 우연히
맞아떨어졌습니다. 여러 장을 돌릴수록 `GENERIC` 경로에 걸릴 확률이 올라가므로,
증상이 "여러 장일 때 안 된다"로 보였습니다.

한편 어댑터 주석이 "upstream이 generate_image 호출을 절반 정도 흘린다"고 적어 둔
관찰도 같은 착오였습니다. 호출은 정상이었고, 판정만 틀렸습니다.

---

## 5. 수정

[`backend_agy.py`](../.claude/skills/ppt-master/scripts/image_backends/backend_agy.py)의
판정 근거를 라벨에서 **실제 증거**로 바꿨습니다.

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| 생성 여부 판정 | transcript 원문에 `"type": "GENERATE_IMAGE"`가 있는지 | 레코드를 JSON으로 파싱해 `tool_calls`에 `generate_image`가 있는지 (`GENERATE_IMAGE` 라벨도 계속 인정) |
| 출력 파일 회수 | 대화 디렉터리를 훑어 실행 시각 이후 수정된 이미지 중 최신 파일 | `Generated image is saved at …` 문장이 지목한 경로를 그대로 사용 |
| 위조 방지 | 최신 파일 선택 규칙에 의존 | 도구가 보고한 경로만 인정하고, 그 경로가 해당 대화 디렉터리 안에 있는지 확인 |

도구 인벤토리 설명에도 `generate_image`라는 문자열이 들어가므로, 원문 검색 대신
레코드를 파싱해 실제 호출만 인정합니다.

### 회귀 검증

브레인 디렉터리에 쌓여 있던 대화 505건 전체에 새 판정 로직을 적용했습니다.

| 구분 | 건수 | 결과 |
|---|---|---|
| 이미지가 실제로 있는 대화 | 135 | 135건 모두 정확한 파일을 회수 (오판 0) |
| 이미지가 없는 대화 | 370 | 이미지로 오인한 건 0 |

이미지가 있는 대화 135건은 예외 없이 transcript에 저장 경로 문장을 남기고 있어,
디렉터리 훑기 경로는 더 이상 필요하지 않아 제거했습니다.

---

## 6. 수정 후 재실행

같은 매니페스트를 같은 조건(동시 실행 3)으로 다시 돌렸습니다.

| 결과 | 항목 |
|---|---|
| 성공 4장 | `p01`, `p02`, `p03`, `p06` — 전부 첫 시도에 통과 |
| 실패 6장 | `p04`, `p05`, `p07`, `p08`, `p09`, `p10` |

앞선 네 장은 재시도 없이 통과했고 파일도 프로젝트 폴더에 정상 도착했습니다. 즉
판정 로직 수정은 의도대로 동작했습니다. 그런데 다섯 번째부터 전부 실패로 돌아섰고,
실패 사유가 앞의 버그와 달랐습니다.

```
[FAIL] Antigravity started generate_image, but conversation <id> names no image file it finished writing.
[FAIL] p05_resin_infiltration.png: Antigravity reports its image-generation allowance as spent.
```

이 실패 대화들은 `generate_image` 호출 단계까지만 기록되고 결과 단계가 아예 없으며,
디스크에도 파일이 없습니다. 판정 문제가 아니라 실제로 생성이 안 된 것입니다.

생성 소요 시간은 성공한 네 장 기준 41초, 314초, 413초, 518초로 편차가 컸습니다.

---

## 7. 두 번째 원인 — 별도로 매겨지는 이미지 생성 한도

할당량 소진 판정이 정규식 휴리스틱이라 오탐 가능성이 있어서, CLI 로그를 지우지 않는
단건 프로브를 따로 돌렸습니다. 파란 원 하나만 그리는 최소 프롬프트입니다.

```
$ agy --model=gemini-3.1-pro --effort=low ... -p "<파란 원 하나>"
The image generation failed because the model's capacity has been exhausted.
You will need to try again later once your quota resets.
```

CLI가 직접 답한 내용이므로 오탐이 아닙니다. 다만 **어느 할당량인지**는 이 문장만으로
정해지지 않습니다. Antigravity 사용량 화면은 같은 시각에 Gemini 모델 주간 한도 99%,
5시간 한도 93%가 남았다고 표시하고 있었습니다. 즉 플랜의 모델 할당량은 거의 손대지
않은 상태에서 이미지 생성만 막힌 것입니다.

부하 때문인지 확인하려고 동시 실행 없이 단건 프로브를 한 번 더 돌렸습니다.

```
I encountered a quota exhaustion error while trying to generate the image.
```

동시 요청이 하나도 없는 상태에서도 막혔으므로 순간 부하나 rate limit이 아닙니다.
정리하면 **이미지 생성에는 사용량 화면에 표시되지 않는 별도의 작은 한도가 있고**,
오늘 관측된 상한은 11장입니다.

프로브에서 세 가지를 더 확인했습니다.

첫째, 할당량 소진은 **stdout에 평문 문장으로** 나옵니다. 종료 코드는 `0`이고
stderr는 비어 있으며, `agy.log`에는 해당 오류 줄이 아예 없습니다. 기계가 읽을 수 있는
신호가 하나도 없는 셈입니다.

둘째, 그 문장은 모델이 매번 새로 쓰는 문장이라 표현이 고정되어 있지 않습니다. 오늘만
해도 `the model's capacity has been exhausted ... once your quota resets`와
`I encountered a quota exhaustion error` 두 가지가 나왔습니다. 그래서 판정 정규식은
좁게 못 잡고 여러 표현을 함께 받도록 넓혀 두었습니다.

셋째, 내부 로그에는 `quota_manager.go`, `doRefreshQuota` 같은 문구가 정상 동작 중에도
계속 찍히므로, 로그 전체에서 "quota"를 찾는 방식은 오탐을 부릅니다. 판정은 줄 단위로
하고, 판정 근거가 된 줄을 오류 메시지에 함께 싣도록 고쳤습니다. 로그가 실행 종료와
함께 삭제되므로, 근거가 메시지에 실리지 않으면 나중에 검증할 방법이 없습니다.

### 오늘 할당량을 태운 주범

브레인 디렉터리를 세어 보면 이렇습니다.

| 실행 | 세션 | 이미지 실제 생성 | 회수 |
|---|---|---|---|
| 수정 전 | 7 | 7장 | **0장 (전부 폐기)** |
| 수정 후 | 18 | 4장 | 4장 |
| 합계 | 25 | 11장 | 4장 |

오늘 실제로 소모한 이미지 생성은 11장이고, 그중 7장을 수정 전 버그가 만들어 놓고
버렸습니다. 할당량의 3분의 2가 결과물 없이 사라진 셈입니다. 교수님이 겪은 "여러 장이
생성되지 않는다"는 이 두 가지가 겹친 결과입니다. 판정 버그가 초반 몇 장을 버리고,
버려진 장수만큼 할당량이 줄어들어 뒷장은 아예 만들어지지도 못했습니다.

---

## 8. 운영 기준 — agy만으로 충분한 범위

수정 후 실행에서 한도 벽에 닿기 전까지의 성공률은 **11회 시도 중 11회**였습니다.
호출이 실패한 경우가 한 건도 없었습니다. 수정 전 어댑터 주석이 "upstream이 호출을
절반쯤 흘린다"고 적어 둔 관찰은 전부 판정 버그였고, agy 자체는 부르면 그린다고
보아도 됩니다.

여기서 나오는 기준은 다음과 같습니다.

| 덱의 `ai` 행 수 | 판단 |
|---|---|
| 8장 이하 | agy만으로 처리한다. 사용자에게 넘기지 않는다 |
| 9~11장 | agy로 시도하되 재생성 여지가 없다. 한 장이라도 다시 뽑으면 한도를 넘는다 |
| 12장 이상 | 초과분은 처음부터 다른 경로로 계획한다 |

8장을 기준으로 잡는 이유는 관측 상한 11장에서 재생성 몫 2~3장을 남겨 두기 위해서입니다.
구도가 마음에 들지 않아 다시 뽑는 일은 정상 작업 과정이고, 그 여지가 없으면 첫 결과를
그대로 써야 합니다.

덱 하나의 `ai` 행 수는 페이지 수보다 대체로 적습니다. 작은 장식용 일러스트는 행마다
따로 생성하지 않고 시트 한 장을 생성해 잘라 쓰는 규칙이 있기 때문입니다
([strategist-images.md](../.claude/skills/ppt-master/references/strategist-images.md)
"Spot illustrations → one sheet, not N rows"). 그래서 실제로 8장 기준을 넘는 덱은
많지 않습니다.

### 이번 수정이 바꾼 것

같은 한도로 얻는 결과물이 달라집니다. 수정 전에는 항목 하나가 재시도 3회를 쓰면서
생성 3장을 태우고 결과물은 0장이었으므로, 한도 11장으로는 슬라이드 3~4장이 한계였습니다.
수정 후에는 생성 1회가 곧 슬라이드 1장이 되므로 같은 한도가 10장 남짓을 냅니다.

동시 실행 수를 올리는 것은 처리량을 늘려 주지 않습니다. 병목이 시간이 아니라 한도이기
때문입니다. 한도가 남아 있을 때 대기 시간을 줄이는 효과만 있습니다.

---

## 9. 남은 과제

- 한도가 리셋된 뒤 `--concurrency 10`으로 10장 동시 실행 시간을 측정한다.
- 이미지 한도의 리셋 주기를 확인한다. 오늘 관측 상한은 11장이지만 주기가 일 단위인지
  5시간 단위인지는 아직 모른다.
- 한도가 얼마 남지 않았을 때 매니페스트를 통째로 던지지 않고 미리 멈추는 방법을
  검토한다. 지금은 한도에 부딪힌 항목부터 순서대로 실패한다.
