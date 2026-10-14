---
title: 2일차 — 금융/재무 데이터 전처리 및 리스크 평가지표 변수화
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">2일차 · 10/15(목) · 09:00–17:50 · 협업 · 정제 · 특성 · SQL · 텍스트 점수화 <span class="tf-daystate" data-tf-daystate="2"></span></span>

# 금융/재무 데이터 전처리 및 리스크 평가지표 변수화

**규칙으로 고치고, 숫자로 검증하고, 기록으로 남긴다.** 오전에는 AI와 일을 나누고 합치는 법(브랜치 · PR · worktree), 지저분한 표를 규칙 · 스크립트 · 테스트로 정제하는 법, 기준일 시점의 특성 · SQL · 뉴스 점수화를 시연으로 봅니다. 오후에는 그 시연을 작게 · 조금 다르게 내 저장소에서 직접 해 **융합 특성표 `d2_end_features.csv`(150행)와 PR 2개**를 남깁니다 — 내일 3일차 연체 예측의 입력입니다.

<div class="tf-buttons" markdown>
[실습 A · 13:00](lab-a.md){ .md-button .md-button--primary }
[실습 B · 15:00](lab-b.md){ .md-button .md-button--primary }
[이론 요약](theory.md){ .md-button }
[프롬프트](../prompts/day2.md){ .md-button }
[파일 받기](#files){ .md-button }
</div>
</div>

## 오늘의 목표 {#goals}

<div class="grid cards tf-cols-3" markdown>

-   :material-numeric-1-circle-outline:{ .lg .middle } **일을 나누고 안전하게 합친다**

    이슈 → 브랜치 → 커밋 → PR → 리뷰 → 머지, worktree로 두 작업을 나란히 — AI가 바꾼 일도 같은 길로

-   :material-numeric-2-circle-outline:{ .lg .middle } **규칙으로 정제하고 기준일 특성을 만든다**

    진단 → 규칙 문서 → 스크립트 → 테스트 → 기록. 특성은 기준일 이전 정보만, SQL로 잇고 숫자로 검증

-   :material-numeric-3-circle-outline:{ .lg .middle } **글을 검증된 숫자 열로 바꾼다**

    뉴스를 0–10 점수와 근거로 바꾸고 정답 20건으로 재서, 30일 창 위험지수를 특성표에 붙인다

</div>

"규칙을 적었다 · 검사가 통과했다 · 커밋으로 남았다"가 오늘의 기준입니다.

## 시간표 {#schedule}

<div class="tf-timeline" markdown>

1. <time>08:30</time> 시작 파일 `d2_start.xlsx`가 열립니다 — 내 저장소에서 `uv run python tools/get_day_files.py 2` · Claude Code 로그인 점검
2. <time>09:00–09:50</time> **1교시** Git · GitHub 협업(브랜치 · 충돌 · PR · GitHub flow · 커밋 위생 · worktree · Actions) · 전처리 시작(품질 6잣대 · 5단계 · 결측) — **시연 1** 이슈 2개를 동시에
3. <time>10:00–10:50</time> **2교시** 이상치 ~ 프로젝트 구조 · 특성 공학 · SQL 시작 — **시연 2** 지저분한 엑셀 → 정제 파이프라인
4. <time>11:00–11:50</time> **3교시** 윈도 함수 · AI가 쓴 SQL 검증 · 텍스트를 지표로 — **시연 3** CSV 3개를 DuckDB로 · 짧은 라이브 스캔 인보이스 → JSON · **시연 4** 공식 API로 공시 · **시연 5** 뉴스 → 위험지수
5. <time>11:50–13:00</time> 점심 — 내 저장소를 VS Code로 열고 Claude Code 로그인 상태를 확인해 둡니다
6. <time>13:00–14:50</time> **4–5교시** <span class="tf-chip tf-chip--must">실습 A</span> [바이어 표 정제 파이프라인](lab-a.md) — 14:15 확인표
7. <time>15:00–16:50</time> **6–7교시** <span class="tf-chip tf-chip--must">실습 B</span> [뉴스 위험지수와 융합 특성표](lab-b.md) — 15:35 정답 20건 열림 · 16:30 확인표
8. <time>17:00–17:20</time> **8교시** <span class="tf-chip tf-chip--must">합치기</span> [PR 리뷰 · 머지 · worktree 정리](lab-b.md#period8)
9. <time>17:20–17:50</time> 결과 공유 · 정리 · 자가 점검 · [내일 예고](#tomorrow)

</div>

쉬는 시간은 09:50 · 10:50 · 14:50 · 16:50(각 10분)입니다. 이론은 [이론 요약](theory.md)에 장별로 있습니다.

## 오전 시연 {#demos}

시연은 늘 **상황 → 입력 → 진행 → 결과** 순서로 봅니다. 오후 실습은 이 시연을 작게, 조금 다르게 내 저장소에서 합니다.

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">시연 1 · 09:22 · Git 협업</span>

    **이슈 2개를 동시에 처리**

    통화 매핑표와 데이터 사전 보강을 worktree 2개 · Claude Code 세션 2개로 → PR 2개 · 리뷰 · 충돌 해결 · 커밋 그래프

    <small>오후: 실습 A 06 · 실습 B 01 · 8교시</small>

-   <span class="tf-eyebrow">시연 2 · 10:14 · 정제</span>

    **지저분한 엑셀 → 정제 파이프라인**

    바이어 150행 · 인보이스 1,902행 → 규칙 문서 · 스크립트 · 테스트 · 품질 보고서 · PR

    <small>오후: 실습 A 전체 — 시트 하나 · 프롬프트 4개</small>

-   <span class="tf-eyebrow">시연 3 · 11:03 · SQL</span>

    **CSV 3개를 DuckDB로 잇기**

    인보이스 · 환율 · 바이어 표 → 연체 구간 · ASOF 환율 조인 · 검증표 · 차트 — 쿼리가 돈다고 맞는 것은 아니다

    <small>오후: 실습 B 05 창 집계 · LEFT JOIN</small>

-   <span class="tf-eyebrow">짧은 라이브 · 11:13 · 이미지 → JSON</span>

    **스캔 인보이스를 JSON 한 줄로**

    가상 송장 이미지 → 두 모델의 JSON → 다르게 읽은 칸만 원천과 대조

    <small>오후: 실습 A 규칙 문서의 날짜 형식</small>

-   <span class="tf-eyebrow">시연 4 · 11:20 · 수집</span>

    **공식 API로 공시 · 재무 모으기**

    정책 확인 → 수집 스크립트(간격 · 기록 · 캐시) → 비율 CSV · 8-K 위험 공시 표

    <small>오후: 실습 B 02 수집 점검 5칸</small>

-   <span class="tf-eyebrow">시연 5 · 11:37 · 텍스트 점수화</span>

    **뉴스 · 코멘트 → 위험지수**

    다국어 뉴스 300건 → 구조화 출력 JSONL → 골든셋 평가 → 프롬프트 v2 → 바이어별 30일 특성

    <small>오후: 실습 B 03–05 — 100건을 세션 안에서 직접 채점</small>

</div>

## 오후 실습 지도 {#map}

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">실습 A · 13:00–14:50</span>

    **[바이어 표 정제 파이프라인](lab-a.md)**

    01 준비 → 02 진단(Plan) → 03 규칙 → 04 스크립트 → 05 검증 → 06 기록 · PR

    <small>만드는 것: 정제규칙.md · clean_buyers.py · 테스트 · 정제 CSV 150행 · 품질 보고서 · PR 1개(머지)</small>

-   <span class="tf-eyebrow">실습 B · 15:00–16:50</span>

    **[뉴스 위험지수와 융합 특성표](lab-b.md)**

    01 작업대(worktree) → 02 수집 점검 → 03 채점 → 04 평가 → 05 융합 → 06 기록 · PR

    <small>만드는 것: 수집점검.md · news_scored.jsonl · eval.md · d2_end_features.csv(150행) · PR 1개</small>

-   <span class="tf-eyebrow">8교시 · 17:00–17:20</span>

    **[두 작업을 main으로 합치기](lab-b.md#period8)**

    01 셀프 리뷰 → 02 짝 코멘트 · 반영 → 03 머지 → 04 worktree 정리 · 이력

    <small>만드는 것: main에 오늘 결과 전부 · PR 2개 이력</small>

</div>

**손 점검 시각** — 13:15 브랜치 · 모드 · 13:50 규칙 7칸 · 14:15 확인표 · 14:35 테스트 · 14:50 PR 머지 · 15:10 새 작업대 · 15:45 JSONL 100줄 · 16:30 확인표 · 16:50 PR 열림 · 17:20 이력. 막히면 손을 들거나 노트북 위에 빨간 표시를 올리세요. 손작업 대신 쓰는 **완성본**(엑셀 검산본)과 보조 프롬프트가 단계마다 있고, 빨리 끝난 분을 위한 **'다 했으면'** 카드가 실습 쪽 끝에 있습니다.

## 쓰는 도구 {#tools}

| 도구 | 어디서 | 오늘 쓰는 곳 |
|---|---|---|
| **Claude Code**(VS Code 확장) | 내 PC의 VS Code | 실습 A · B 대부분 — 시작은 **Manual**, 진단은 **Plan**, 만들기는 **Edit automatically**. 명령 실행은 허락 창을 읽고 승인 |
| **Git · GitHub** | VS Code 소스 제어 · github.com | 이슈 → 브랜치 → 커밋 → PR → 리뷰 → 머지, worktree(소스 제어 › Worktrees) |
| **Claude · ChatGPT** | 브라우저 | 실습 B 02 robots.txt · 약관 읽기(Claude 웹) · Claude Code를 못 쓸 때의 채팅 경로 · 더 해 보기의 두 번째 채점자 |
| **엑셀** | 내 PC(또는 웹용 Excel) | 실습 A 05 완성본 엑셀 검산본 열기 — 수식을 보고 AI 결과와 대조 |
| **uv · pytest** | VS Code 터미널 | `uv run`으로 스크립트 · 테스트 실행(`uv sync`로 만든 환경) |

!!! note "Claude Code는 유료 구독이 필요합니다"

    Pro 이상 구독이나 API(Console) 계정으로 로그인합니다. 무료 플랜으로는 쓸 수 없습니다. 설치가 막힌 PC는 내 저장소의 **Codespaces**를, 계정이 없으면 **채팅 경로**로 같은 실습을 합니다 → [실습 A 채팅 경로](lab-a.md#chat-path) · [실습 B 채팅 경로](lab-b.md#chat-path).

## 파일 받기 {#files}

**내 저장소에서 명령 하나**면 됩니다. 오늘 파일을 같은 경로로 받고, 작업 사본을 `workbench/day2/data/`에 만들어 줍니다.

```text
uv run python tools/get_day_files.py 2
```

- 카드에 잠금 표시가 있는 파일은 그 시각 뒤에 받습니다 — `d2_start.xlsx` · 엑셀 검산본은 **08:30**, 정답 20건 `d2_news_answer.csv`는 **15:35**(먼저 내 점수를 만든 뒤). 그 전에는 명령이 `[열기 전]`으로 알려 주고, 시각이 지난 뒤 같은 명령을 다시 실행하면 새로 열린 파일만 더 받습니다.
- 받은 파일의 사본이 `git status`에 '추적 안 됨'으로 보이는 것은 정상입니다(커밋하지 않아도 됩니다).
- 명령이 막히거나 채팅 경로로 하는 분은 아래 카드에서 직접 받습니다. 첫 카드(ZIP)를 받아 압축을 풀면 `D2` 폴더가 나옵니다.

--8<-- "docs/_snippets/day2/files_all_cards.md"

## 데이터와 이용 조건 {#data}

- 오늘 쓰는 데이터는 모두 **(가상) 한빛정밀(주)의 합성 데이터**이거나 **공개 데이터**입니다. 바이어 150곳과 뉴스 300건은 교육용 가상이며 실존 기업과 무관하고, 숫자는 실제 거래 기록이 아닙니다. 투자 · 여신 판단 자료가 아닙니다.
- 합성 데이터와 문서는 CC BY 4.0, 코드는 MIT입니다. 환율(`fx_krw_daily.csv` · 시트 `fx_at_ref`)은 미국 연준 H.10 환율(FRED 제공)로 'Public Domain: Citation Requested'이며 인용 방법은 저장소의 `data/external/ATTRIBUTION.md`에 있습니다. 오전 시연 4의 SEC 공시 값은 공개 공시이고 원문의 권리는 각 회사에 있습니다.
- 열 하나하나의 뜻은 [데이터 → 바이어 스냅샷 핵심 컬럼](../data.md#buyers)과 시작 파일의 `dictionary` 시트에 있습니다.
- **회사 실데이터 · 개인정보는 올리지 않습니다 — 익명화본도.** AI 서비스의 '모델 개선(학습)' 설정은 끄고 시작하고([사전 준비 — AI 학습 설정 끄기](../setup.md#ai-training)), 내 저장소는 공개이므로 **키 · 비밀번호 · 회사 자료는 커밋하지 않습니다.**
- 수집 점검은 **점검만** 합니다. 실제 뉴스 사이트에서 기사를 수집하거나 본문을 복사해 올리지 않습니다(남기는 것은 제목 · 날짜 · 주소 · 점수).

## 오늘의 결과물과 제출 {#submit}

<div class="tf-checklist" data-title="오늘 남길 것" markdown>

- [ ] 이슈 1개(닫힘) · PR A(머지) — 본문 첫 줄 `Closes #번호` · 짝 리뷰 코멘트 1개 반영
- [ ] `workbench/day2/rules/정제규칙.md`(1–8칸) · `scripts/clean_buyers.py` · `workbench/day2/tests/`의 테스트 파일 — `uv run pytest -q` 통과
- [ ] `workbench/day2/outputs/d2_buyers_clean.csv`(150행) · `dq_report.md` · `profile.md` · `scaling.md` — 확인표 여섯 줄 · 원본 그대로
- [ ] `workbench/day2/rules/수집점검.md` — 다섯 칸 + 결론 하나
- [ ] `news_scored.jsonl`(100줄 · 위반 0) · `scripts/validate_scores.py`와 평가 · 결합 스크립트 · `eval.md`(숫자 3개 + 오차 원인 2건)
- [ ] **`d2_end_features.csv`(150행 · 32열)** · `workbench/day2/data/데이터사전.md`(새 열 7개 · 시점 점검)
- [ ] PR B 머지 · worktree 정리 · `main`에 오늘 결과 전부

</div>

- **제출 = push · PR**입니다. 강사는 1일차에 <span data-tf-link="submit_form">제출 폼</span>으로 낸 내 저장소 주소에서 오늘 PR을 확인합니다 — 따로 올릴 파일은 없습니다. 1일차에 저장소 주소를 내지 못했다면 오늘 같은 폼으로 냅니다.
- 점검 기준은 '파일이 있다'가 아니라 **검증한 흔적**입니다 — 테스트 통과 · 확인표 일치 · 위반 0 · 9월 기사 0건.
- PR 본문 · 커밋 메시지 · 규칙 문서에 **회사 이름 · 실명 · 실제 숫자를 쓰지 않습니다.** 저장소가 공개입니다.
- 다 끝내지 못했어도 그대로 push하세요. 내일 아침에는 모두 같은 기준 특성표로 시작합니다.

## 함께하는 규칙 {#rules}

<div class="tf-rules" markdown>

1. **규칙을 먼저 문서로** — 무엇을 어떻게 고칠지는 사람이 정하고, 스크립트와 테스트는 그 규칙을 따릅니다.
2. **변환했으면 검증한다** — 행 수 · 합계 · 손계산 한 건(완성본) · 정답과의 비교. AI가 쓴 쿼리와 점수도 숫자로 확인합니다.
3. **기준일 이전 정보만** — 환율은 기준일 또는 직전 영업일, 뉴스는 기준일 전 30일. 성능이 너무 좋으면 먼저 의심합니다.
4. **일 하나 = 브랜치 하나 = PR 하나** — 커밋 메시지에 무엇과 왜, 머지는 Claude Code에게 시키지 않고 **내가 직접**. 허락 창은 무엇을 · 어디에 · 지우는지 읽고 승인합니다.
5. **짝과 서로 리뷰** — 정답을 베끼는 것이 아니라 AI가 놓친 곳을 서로 찾아 견줍니다. 강사는 실습 동안 한 분씩 2–3분 확인합니다.

</div>

## 정리 · 자가 점검 · 내일 예고 {#tomorrow}

**오늘 배운 것 다섯 줄**

1. 브랜치 · PR · 리뷰 · worktree로 AI 작업을 나누고 안전하게 합친다.
2. 전처리 = 진단 → 규칙 → 스크립트 → 검증 → 기록.
3. 특성은 기준일 이전 정보만 — 특성 사전에 시점 점검 칸을 둔다.
4. SQL · DuckDB로 표를 잇고, AI가 쓴 쿼리는 숫자로 검증한다.
5. 텍스트 → 구조화 출력 → 골든셋 평가 → 프롬프트 버전 관리.

<div class="tf-checklist" data-title="자가 점검" markdown>

- [ ] 이슈 → 브랜치 → 커밋 → PR → 리뷰 → 머지의 흐름을 직접 밟고, worktree로 두 작업을 나란히 할 수 있다
- [ ] 데이터를 규칙 문서 · 스크립트 · 테스트로 정제하고, 결측의 이유에 따라 채우는 법을 고를 수 있다
- [ ] 특성이 기준일 이전 정보만으로 만들어졌는지 점검하고 특성 사전에 남길 수 있다
- [ ] AI가 쓴 SQL · 스크립트의 결과를 행 수 · 합계 · 다른 길(엑셀)로 검증할 수 있다
- [ ] 가져와도 되는 데이터인지 점검하고(API · robots.txt · 약관), 뉴스를 점수화해 골든셋으로 검증할 수 있다

</div>

**손을 들어 답해 보세요**

1. 결측이 **MNAR**이면 왜 플래그를 남길까요? — 결측 자체가 위험 신호이기 때문입니다.
2. LEFT JOIN 뒤 행 수가 150보다 늘었다면? — 오른쪽 표의 키가 중복된 1:N입니다.
3. 라벨 일치율이 90%인데 카파가 0.3이라면? — 다수 범주인 low만 맞힌 것입니다.

- **복습**: [용어집 → 2일차](../glossary.md#day2)의 학습 모드 퀴즈로 오늘 용어를 복습합니다.
- **내일 3일차 · 10/16(금)** — AI 기반 대금 결제 연체 및 바이어 부도 리스크 예측. 불균형 데이터 · LightGBM · 평가지표 · SHAP. 오늘 만든 특성표의 마지막 열 `late_30d`가 내일의 정답 열입니다(150곳 가운데 13곳만 1인 드문 사건). 기준 특성표는 내일 **08:30**에 열리고 아침 첫 명령은 `uv run python tools/get_day_files.py 3`입니다. 나가시기 전에 **내 저장소에서 PR 두 개가 머지됐는지** 한 번만 확인해 주세요 → [3일차](../day3/index.md)
