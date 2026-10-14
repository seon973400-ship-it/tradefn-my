---
title: 3일차 — AI 기반 대금 결제 연체 및 바이어 부도 리스크 예측
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">3일차 · 10/16(금) · 09:00–17:50 · 확률 · 검증 · 비용 임계값 · 설명 · 재현 <span class="tf-daystate" data-tf-daystate="3"></span></span>

# AI 기반 대금 결제 연체 및 바이어 부도 리스크 예측

**연체를 확률로 예측하고, 비용으로 자르고, 근거를 남긴다.** 오전에는 위험을 확률로 읽는 법 · 데이터로 확률을 배우는 모델 · 평가하고 정하고 설명하는 법을 시연 다섯 건으로 보고, 오후에는 그 시연을 작게, 조금 다르게 내 저장소에서 직접 합니다. 하루가 끝나면 **바이어 150곳의 연체 확률 · 등급 파일과 등급의 근거 메모, 내 저장소의 PR**이 남습니다.

<div class="tf-buttons" markdown>
[실습 A · 13:00](lab-a.md){ .md-button .md-button--primary }
[실습 B · 15:00](lab-b.md){ .md-button .md-button--primary }
[이론 요약](theory.md){ .md-button }
[프롬프트](../prompts/day3.md){ .md-button }
[파일 받기](#files){ .md-button }
</div>
</div>

## 오늘의 목표 {#goals}

<div class="grid cards tf-cols-3" markdown>

-   :material-numeric-1-circle-outline:{ .lg .middle } **만들고 검증한다**

    드문 연체를 예측하는 분류 모델을 AI 코딩 도구로 만들고, 시간 · 바이어 단위로 누수 없이 검증합니다

-   :material-numeric-2-circle-outline:{ .lg .middle } **평가하고 정한다**

    혼동행렬 · 정밀도/재현율 · ROC/PR-AUC · 보정으로 평가하고, 오분류 비용으로 임계값과 S/A/B/C 등급을 정합니다

-   :material-numeric-3-circle-outline:{ .lg .middle } **설명하고 남긴다**

    SHAP으로 등급의 근거를 쓰고 환율의 예측 구간을 읽은 뒤, 같은 입력이면 같은 결과가 나오게 기록합니다

</div>

오늘의 기준 — **숫자가 너무 좋으면 먼저 의심한다 · 임계값은 비용으로 정한다 · 결정은 사람이 한다.**

## 시간표 {#schedule}

<div class="tf-timeline" markdown>

1. <time>08:40–09:00</time> **입실** 내 저장소에서 `uv run python tools/get_day_files.py 3` · Claude Code 로그인 점검
2. <time>09:00–09:50</time> **1교시** 위험을 확률로 정의하기(현업 문제 · 통계 기초 · 시계열 예측) — 시연 1 · 시연 2
3. <time>10:00–10:50</time> **2교시** 데이터로 학습하는 모델(레이블 · 분할 · 과적합 · 누수 · 부스팅 · 불균형) — 시연 3
4. <time>11:00–11:50</time> **3교시** 평가하고, 정하고, 설명하기(혼동행렬 · 지표 · 보정 · 비용 임계값 · 등급 · SHAP) — 시연 4 · 시연 5 · 11:44 오후 안내
5. <time>11:50–13:00</time> **점심** 내 저장소를 VS Code로 열고 폴더 '신뢰' · Claude Code 로그인 · 권한 모드를 확인해 둡니다
6. <time>13:00–14:50</time> **4–5교시** <span class="tf-chip tf-chip--must">실습 A</span> [내 첫 연체 예측 모델](lab-a.md) — 14:45 기대 범위 확인
7. <time>15:00–16:50</time> **6–7교시** <span class="tf-chip tf-chip--must">실습 B</span> [등급 · 근거 · 환율](lab-b.md) — **16:45 저장 확인** · 16:50 PR
8. <time>17:00–17:50</time> **8교시** 같은 입력이면 같은 결과(MLOps 입문) — 시연 6 · 수강생 PR 리뷰 · 정리

</div>

쉬는 시간은 09:50 · 10:50 · 13:50 · 14:50 · 15:50(각 10분)입니다. **금요일이라 16:45에 결과 파일 저장을 한 번 더 확인합니다.**

## 시연 여섯 건과 오후에 해 보는 것 {#demos}

시연은 늘 **문제 상황 → 입력 → 진행 → 결과** 순서로 봅니다. 자세한 내용은 [이론 요약](theory.md)에 있습니다.

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">시연 1 · ChatGPT</span>

    **연체율은 얼마나 확실한가**

    팀장이 "우리 연체율 5%대라던데 확실해?" — 숫자 하나 대신 구간으로 답합니다. 패널 CSV → 표 2 · 그래프 2 · 실행된 코드

    <small>오후: 실습 A — 시험 연체가 4건뿐이라 AUC가 사람마다 다른 이유 · 도전 ② 부트스트랩</small>

-   <span class="tf-eyebrow">시연 2 · Claude Code</span>

    **공개 환율로 90일 위험 구간**

    석 달 안에 원/달러가 손익분기 1,300원(가정) 아래로 갈 위험은 언제 커지나. FRED CSV → 백테스트 그림 · 표 · 90일 전망 · 3줄 요약

    <small>오후: 실습 B-2 · 03 — 제공 CSV로 5/29까지 학습 → 95% 구간</small>

-   <span class="tf-eyebrow">시연 3 · Claude Code + Claude</span>

    **누수 탐정과 모델 리그전**

    동료가 'AUC 1.0' 연체 모델을 보고했다 — 믿어도 되나. 패널 · 데이터 사전 · 40행 표 → HTML 리포트 · 시험 예측 · 규칙 한 줄

    <small>오후: 실습 A-1 — 300행 · 모델 2개 · 누수 실험</small>

-   <span class="tf-eyebrow">시연 4 · Claude Code + 엑셀</span>

    **비용으로 움직이는 임계값 엑셀**

    위원회가 "놓친 연체를 10배로 보면 경보가 얼마나 늘어나나?"를 묻는다. 시험 예측 · 규정 → 수식이 살아 있는 엑셀 · 검산표

    <small>오후: 실습 A-2 비용표 · 내 비용비 — 실습 B-1 등급 · 단조성(완성본 엑셀과 AI 대조)</small>

-   <span class="tf-eyebrow">시연 5 · Claude Code + Cowork</span>

    **SHAP 근거를 위원회 슬라이드로**

    C등급 B118을 내일 위원회에 올린다 — 숫자는 정확하게, 양식은 회사 것으로. 모델 · CSV · 규정 · 양식 → SHAP 그림 · 슬라이드 3장 · 대조표

    <small>오후: 실습 B-2 · 01–02 — SHAP 그림 2장 · 메모 5칸</small>

-   <span class="tf-eyebrow">시연 6 · MLflow + GitHub Actions</span>

    **실험 기록과 PR 자동 검증**

    "나무를 깊게 하니 AUC가 올랐다"는 설정 변경 PR — 감으로 병합하지 않는다. 저장소 · `params.yaml` · PR → MLflow 비교 · PR 체크 · 코멘트

    <small>8교시 시연 — 수업 뒤 [품질 게이트를 내 PR에](lab-b.md#more)</small>

</div>

## 오후 실습 지도 {#map}

**오후의 흐름**(슬라이드 59) — ① 데이터 결합 확인 → ② 예측 모델 실행 → ③ 정확도 지표 검증은 **실습 A**, ④ 연체 확률 확인 → ⑤ 등급 · 근거 · 환율 → ⑥ 저장 · PR은 **실습 B**입니다. 트랙은 셋 — 기본(300행) · 표준(패널 시간 분할) · 도전(불균형 비교 · 부트스트랩 · worktree).

<div class="grid cards tf-cols-2" markdown>

-   <span class="tf-eyebrow">실습 A · 13:00–14:50</span>

    **[내 첫 연체 예측 모델](lab-a.md)**

    A-1 · 01 파일 · 브랜치 · 규칙 → 02 데이터 카드(Plan) → 03 첫 모델 → 04 누수 실험 → 05 커밋 / A-2 · 01 비용표 → 02 놓친 바이어 → 03 내 비용비 → 04 트랙(선택) → 05 기대 범위 · push

    <small>만드는 것: `d3_data_card.md` · `d3_train.py` · `d3_eval.md` · `d3_test_pred.csv` · `model_v1.txt` · `d3_threshold.md` · 커밋 2개 이상</small>

-   <span class="tf-eyebrow">실습 B · 15:00–16:50</span>

    **[등급 · 근거 · 환율](lab-b.md)**

    B-1 · 01 150곳 점수 → 02 완성본 엑셀 읽기 → 03 분포 대조 → 04 단조성 → 05 AI 대조 / B-2 · 01 SHAP → 02 근거 메모 → 03 환율 구간 → 04 16:45 저장 → 05 PR

    <small>만드는 것: `d3_scores.csv` · `d3_grade_compare.md` · `d3_end_scored.csv`(150행 · 6열) · `d3_shap_memo.md` · `d3_fx.md` · `notes.md` · PR</small>

</div>

**점검 시각 한눈에** — 13:10 브랜치 · 13:20 데이터 카드 · 13:40 시험 88행 · 13:50 커밋 1 · 14:20 비용표 · 14:45 기대 범위 · 14:50 커밋 2 + push · 15:15 점수 150행 · 15:35 등급 분포 · 15:42 단조성 · 15:50 6열 CSV · 16:15 SHAP 그림 · 16:25 메모 · 16:40 환율 · **16:45 저장 확인** · 16:50 PR.

**실습 B-1의 엑셀 손작업은 완성본으로 대신합니다.** 슬라이드 B-1 · 02–04(붙여넣기 · IFS · 채우기 핸들 · 조건부 서식 · 피벗)는 이미 만들어 둔 완성본 `d3_grade_banding_example.xlsx`를 열어 읽고, AI가 같은 규칙을 내 점수에 적용한 결과와 대조하는 시간으로 씁니다 — 번호와 시각은 슬라이드 그대로입니다.

막히면 손을 들거나 노트북 위에 빨간 표시(스티커 등)를 올리세요. 강사가 돌며 한 분씩 2–3분 확인합니다. 짝과는 서로의 PR을 리뷰하는 사이입니다.

| 단계 | 오늘 쓰는 프롬프트 |
|---|---|
| 실습 A-1 · 01–05 | [A0 규칙 읽히기](../prompts/day3.md#a0) · [A1 데이터 카드(Plan)](../prompts/day3.md#a1) · [A2 첫 모델](../prompts/day3.md#a2) · [A3 누수 실험](../prompts/day3.md#a3) · [커밋](../prompts/day3.md#commit) |
| 실습 A-2 · 01–05 | [A4 비용표 · 내 비용비](../prompts/day3.md#a4) · [A5 트랙](../prompts/day3.md#a5) · [커밋 · push](../prompts/day3.md#commit) |
| 실습 B-1 · 01–05 | [B1 150곳 점수](../prompts/day3.md#b1) · [B1b 완성본 읽기](../prompts/day3.md#b1b) · [B1c 분포 대조](../prompts/day3.md#b1c) · [B1d 단조성](../prompts/day3.md#b1d) · [B2 AI 대조](../prompts/day3.md#b2) |
| 실습 B-2 · 01–05 | [B3 SHAP](../prompts/day3.md#b3) · [B4 근거 메모](../prompts/day3.md#b4) · [B5 환율](../prompts/day3.md#b5) · [B6 재현 메모 · PR](../prompts/day3.md#b6) |
| 막힐 때 · 수업 뒤 | [어디서 갈렸나](../prompts/day3.md#mismatch) · [채팅 경로](../prompts/day3.md#chat-path) · [시연 프롬프트](../prompts/day3.md#demos) |

## 쓰는 도구 {#tools}

| 도구 | 어디서 | 오늘 쓰는 곳 |
|---|---|---|
| **Claude Code**(VS Code 확장) | 내 PC의 VS Code | 실습 A · B 대부분 — 첫 프롬프트는 **Plan**, 계획 승인 창에서 **`2 Yes, and manually approve edits`**, 명령은 허락 창을 읽고 승인 |
| **Git · GitHub** | VS Code 소스 제어 · github.com | 브랜치 `d3-model` · 커밋 · push · PR · 짝 리뷰 |
| **엑셀** | 내 PC(또는 웹용 Excel) | 실습 B-1 · 02–04 **완성본 열어 보기**(수식 · 조건부 서식 · 분포 · 단조성) — 손으로 매기지 않습니다 |
| **ChatGPT** · **Claude** | 브라우저 | 오전 시연 1 · Claude Code를 못 쓸 때의 채팅 경로 |
| **uv · Python** | VS Code 터미널 | `uv run`으로 학습 코드 실행(LightGBM · scikit-learn · statsmodels). Prophet은 선택(`uv sync --group forecast`) |

!!! note "Claude Code는 유료 구독이 필요합니다"

    Claude Code는 Pro 이상 구독이나 API(Console) 계정으로 로그인합니다. 무료(Free) 플랜으로는 쓸 수 없습니다. 설치가 막힌 PC는 내 저장소의 **Codespaces**를, 계정이 없으면 **채팅 경로**로 같은 실습을 합니다 → [실습 A 채팅 경로](lab-a.md#chat-path) · [실습 B 채팅 경로](lab-b.md#chat-path).

## 파일 받기 {#files}

**내 저장소에서 명령 하나**면 됩니다. 오늘 파일을 같은 경로로 내려받고 작업 사본을 `workbench/day3/data/`에 만들어 줍니다. 오늘의 규칙 파일(`workbench/day3/rules/d3_rules.md`)이 내 저장소에 없으면 그것도 받습니다.

```text
uv run python tools/get_day_files.py 3
```

- 카드에 **잠금 표시**가 있는 파일은 그 시각 뒤에 받습니다 — 그 전에는 `get_day_files.py`도 '열기 전'이라고 알려 주고 받지 않습니다. 시작 파일 · 완성본 · SHAP 표본은 **10/16(금) 08:30**(2일차 실습의 결과가 들어 있어서), 강사 기준 등급 파일 `d3_end_scored.csv`는 **10/16(금) 18:00**(먼저 내 결과를 만든 뒤 견주는 비교 기준)입니다. 시각이 지난 뒤 같은 명령을 다시 실행하면 새로 열린 파일만 받습니다.
- 강사 기준 `d3_end_scored.csv`는 **내 결과와 이름이 같지만 폴더가 다릅니다** — 강사 것은 `data/checkpoints/`(비교 기준이라 작업 사본은 만들지 않습니다), 내 것은 `workbench/day3/outputs/`입니다. 월요일 4일차는 모두 같은 기준 등급으로 시작합니다.
- 8교시 품질 게이트의 수강생판(`labs/day3/quality_gate/`)도 같은 명령이 받습니다 — 수업 뒤 [실습 B '다 했으면'](lab-b.md#more).
- 막히면 아래 카드에서 직접 받습니다. 맨 위 ZIP 카드를 받아 압축을 풀면(Windows: 마우스 오른쪽 → **모두 압축 풀기**, Mac: 더블클릭) **`D3`** 폴더가 나옵니다. 폴더 안에는 파일만 있으니 자리를 나눠 둡니다 — `d3_start_features.csv` · `d3_start_scoring.csv` · `d3_features_panel.csv`(18:00 뒤에는 `d3_end_scored.csv`도)는 `data/checkpoints/`에, 나머지는 `labs/day3/`에 둡니다(`fred_dexkous.csv`는 이미 `data/external/`에 있습니다). 프롬프트의 경로가 이 자리를 가리킵니다. 저장소 없이 채팅 경로로 하는 분도 여기서 받습니다.

--8<-- "docs/_snippets/day3/files_all_cards.md"

## 데이터와 이용 조건 {#data}

- 오늘 쓰는 데이터는 모두 **(가상) 한빛정밀(주)의 합성 데이터**이거나 **공개 데이터**입니다. 한빛정밀(주)과 바이어 150곳, 연체 · 등급은 교육용 가상이며 실존 기업과 무관하고, 숫자는 실제 거래 기록이 아닙니다. 투자 · 여신 판단 자료가 아닙니다. 오전 시연 5의 여신관리규정과 위원회 양식도 교육용 가상 문서입니다.
- 합성 데이터와 문서는 CC BY 4.0, 코드는 MIT입니다. 환율(`fx_forecast_inputs.csv` · `fred_dexkous.csv`)은 미국 연준 H.10 환율(FRED 제공)로 'Public Domain: Citation Requested'이며 인용 방법은 저장소의 `data/external/ATTRIBUTION.md`에 있습니다. 라이선스 전문은 저장소의 `LICENSE-DATA.md` · `NOTICE.md`에 있습니다.
- 열 하나하나의 뜻은 [데이터 → 바이어 스냅샷 핵심 컬럼](../data.md#buyers)과 `data/data_dictionary.xlsx`의 `columns` 시트에 있습니다.
- **오늘 파일은 합성 데이터라 ChatGPT · Claude 같은 AI 도구에 올리거나 붙여 넣어도 됩니다.** 다만 **회사 실데이터 · 개인정보는 어떤 AI 도구에도 넣지 않습니다 — 익명화본도.** AI 서비스의 '모델 개선(학습)' 설정은 끄고 시작하고([사전 준비 — AI 학습 설정 끄기](../setup.md#ai-training)), 내 저장소는 공개이므로 **키 · 비밀번호 · 회사 자료는 커밋하지 않습니다.**
- 오전 시연 5의 Claude Cowork는 연결한 폴더의 파일이 앱을 거쳐 Anthropic 클라우드에서 처리됩니다. 오늘처럼 합성 데이터일 때만 씁니다.

## 오늘의 결과물과 제출 {#submit}

오늘 결과물은 **내 저장소의 PR 1개와 연체 확률 · 등급 파일, 근거 메모**입니다. 결과 파일은 `workbench/day3/outputs/`에, 재현 메모 `notes.md`만 `workbench/day3/` 바로 아래에 둡니다.

<div class="tf-checklist" data-title="오늘 남길 것" markdown>

- [ ] **연체 확률 · 등급** `d3_end_scored.csv` — 150행 · 6열(`buyer_id` · `ref_date` · `pd_30d` · `grade` · `threshold_used` · `model_version`) · UTF-8 · 등급이 t 규칙과 같다
- [ ] 데이터 카드 · 평가 · 임계값 `d3_data_card.md` · `d3_eval.md` · `d3_threshold.md` — 시험 88행(연체 4) · 최소 비용 t와 이론값 차이 1줄 · 내 비용비 결과 1줄
- [ ] 완성본 대조 `d3_grade_compare.md` — 분포 · 단조성 · 다른 행과 이유
- [ ] 근거 메모 `d3_shap_memo.md` + PNG 2 — 5칸 · 모든 숫자가 입력에 있다 · 마지막 줄 '사람 승인 전 초안'
- [ ] 환율 위험 구간 `d3_fx.md` + PNG — 6/5가 95% 구간 안이었는지 1줄
- [ ] 재현 메모 `notes.md` — 시드 · 패키지 버전 · 시험 AUC · t · 비용비 근거
- [ ] PR 1개(`d3-model`) — 제목 `3일차: 연체 확률 모델 · 등급 · 근거 메모` · 짝 코멘트 1개 · 링크는 <span data-tf-link="submit_form">제출 폼</span>에

</div>

- **16:45 금요일 저장 확인** — `d3_end_scored.csv`가 150행 · 6열 · UTF-8이고 `notes.md`가 있는지, push했는지 헬퍼가 자리마다 봅니다. 월요일에 모두 같은 3일차 기준 등급 파일로 시작하면서 내 결과와 견주어 보니, 오늘 결과를 남겨 두는 것이 중요합니다.
- 점검 기준은 **'파일이 있다'가 아니라 검증한 흔적**입니다 — 시험 88행 확인 · 누수 실험 · 완성본 엑셀과 AI의 대조 · 입력에 없는 숫자 0처럼요.
- PR 본문 · 커밋 메시지 · 메모에 **회사 이름 · 실명 · 실제 숫자를 쓰지 않습니다.** 저장소가 공개입니다. 다 끝내지 못했어도 그대로 push하세요.

## 함께하는 규칙 {#rules}

- **1:1 순회**: 강사가 실습 동안 한 분씩 2–3분 확인합니다. 막히면 손을 들거나 빨간 표시를 올립니다.
- **짝과 서로 PR을 리뷰**: 서로의 PR에 코멘트 하나씩. 보는 것은 다섯 가지 — 바뀐 파일 · 커밋 메시지의 '왜' · 실데이터가 없는지 · 키가 없는지 · 한 줄 코멘트.
- **숫자보다 절차**: 시험 연체가 4건뿐이라 AUC · 최소 비용 t가 사람마다 다릅니다. 옆 사람과 숫자가 달라도 절차(분할 · 특성 · 비용식)가 같으면 정상입니다. 숫자가 이상하면 [어디서 갈렸나](../prompts/day3.md#mismatch)를 먼저 묻습니다.
- **한 번에 하나**: 프롬프트는 하나 보내고 결과를 읽은 뒤 다음으로 갑니다. 새 일은 새 대화에서 시작합니다.
- **허락 창은 읽고 승인**: 무엇을 · 어디에 · 지우는지 세 가지를 읽고 `1 Yes`. 파일 삭제 · 강제 push · `git reset --hard`는 거절합니다. **머지는 Claude Code에게 시키지 않고 내가 직접** 누릅니다.
- **현장 이야기를 들려 주세요**: "우리 회사에서는 이렇게 한다"는 이야기가 나오면 말씀해 주세요 — 6일차 도입 기획의 재료가 됩니다.

!!! success "오늘의 습관 네 가지"

    1. **정답과 분할은 사람이 문장으로 정한다** — 무엇을 정답으로 볼지(`late_30d`), 어디서 나눌지(시간 · 바이어 단위)를 프롬프트에 적습니다.
    2. **숫자가 너무 좋으면 먼저 의심한다** — AUC 1.0은 기뻐할 일이 아니라 누수 신호입니다. ID · 보조 열부터 봅니다.
    3. **임계값은 비용으로 정하는 경영 결정이고, 등급에는 근거를 붙인다** — SHAP은 이유이지 원인이 아니고, 결정은 사람이 합니다.
    4. **같은 입력이면 같은 결과** — 시드 · 버전 · 기록을 남깁니다. 설명할 수 없으면 커밋하지 않습니다.

## 정리 · 자가 점검 · 내일 예고 {#tomorrow}

**오늘 배운 것 다섯 줄**

1. 드문 사건은 기저율부터 — 정확도 대신 재현율 · 정밀도 · PR-AUC.
2. 레이블과 분할이 문제를 정한다 — 시간 · 바이어 단위로, 누수는 의심부터.
3. 임계값은 비용으로 정하는 경영 결정(5:1 → 0.17), 등급은 t/4 · t/2 · t.
4. SHAP은 근거이지 원인이 아니다 — 자료의 숫자는 원본과 대조한다.
5. 같은 입력이면 같은 결과 — 실험 기록 · 버전 · 품질 게이트.

**자가 점검** — 눌러서 표시해 두세요.

- [ ] 나는 내 모델의 검증 방법(분할)을 한 문장으로 말할 수 있다
- [ ] 나는 AUC가 너무 좋을 때 누수를 의심하고 어떤 열부터 볼지 안다
- [ ] 나는 임계값을 비용으로 설명할 수 있다
- [ ] 나는 한 바이어의 등급 이유를 근거 3줄로 쓰고 한계를 함께 적을 수 있다
- [ ] 나는 같은 입력이면 같은 결과가 나오게 시드 · 버전을 남기고, 설정을 바꾼 PR을 기준과 견줄 수 있다

**손을 들어 답해 보세요**

1. 누가 "정확도 95% 연체 모델"을 가져오면 무엇부터 묻나요? — 기저율과 놓친 연체(재현율)입니다. '전부 정상'이라고만 답해도 정확도가 94.7%입니다.
2. 모델이 0.3이라고 한 바이어 100곳 중 실제로 몇 곳이 연체해야 그 확률을 믿을 수 있나요? — 30곳 안팎입니다(보정).
3. 설정을 바꿨더니 AUC는 그대로인데 비용이 90에서 144로 늘었다면 병합하나요? — 하지 않습니다. AUC 하나만 보지 않고 기준 모델과 견주는 품질 게이트가 있습니다.

- **복습**: [용어집 → 3일차](../glossary.md#day3)의 학습 모드 퀴즈로 오늘 용어를 복습합니다.
- **다음 수업 4일차 · 10/19(월)** — 수출채권 회수 전략 최적화 및 조기 경보 시뮬레이션. 오늘의 등급이 바이어별 안전 여신 한도 계산의 입력이 됩니다. 아침 첫 명령은 `uv run python tools/get_day_files.py 4`이고, 모두 같은 3일차 기준 등급 파일 `d4_start_scored.csv`(10/19(월) 08:30 열림)로 시작합니다. 나가시기 전에 **오늘 PR 링크를 제출했는지** 한 번만 확인해 주세요 → [4일차](../day4/index.md)

## 함께 보기 {#see-also}

- [기초 F3 · 같은 입력이면 같은 결과](../foundations/f3.md) · [용어집 3일차](../glossary.md#day3) · [프롬프트 3일차](../prompts/day3.md) · [데이터 → 파일 체인](../data.md#chain)
