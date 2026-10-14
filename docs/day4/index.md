---
title: 4일차 — 수출채권 회수 전략 최적화 및 조기 경보 시뮬레이션
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">4일차 · 10/19(월) · 09:00–17:50 · 최적화 · 시뮬레이션 · 경보 자동화 · 보고서 파이프라인 <span class="tf-daystate" data-tf-daystate="4"></span></span>

# 수출채권 회수 전략 최적화 및 조기 경보 시뮬레이션

**예측을 한도 · 경보 · 보고로 바꾼다.** 오전에는 정책 문장을 최적화 모델로 옮겨 바이어별 한도를 구하고, 쇼크 손실을 분포로 읽고, 규칙으로 경보를 설계해 자동으로 돌리고, 숫자는 코드가 · 문장은 AI가 · 서명은 사람이 하는 보고서 파이프라인을 시연 다섯 건으로 봅니다. 오후에는 그 시연을 **작게, 조금 다르게** 내 저장소에서 직접 합니다.

<div class="tf-buttons" markdown>
[실습 A · 13:00](lab-a.md){ .md-button .md-button--primary }
[실습 B · 15:00](lab-b.md){ .md-button .md-button--primary }
[이론 요약](theory.md){ .md-button }
[프롬프트](../prompts/day4.md){ .md-button }
[파일 받기](#files){ .md-button }
</div>
</div>

## 오늘의 목표 {#goals}

<div class="grid cards tf-cols-3" markdown>

-   :material-numeric-1-circle-outline:{ .lg .middle } **정책을 모델로**

    정책 문장을 최적화 모델로 옮겨 바이어별 안전 한도를 계산하고, **잠재가격**으로 '왜 그 한도인가'를 설명합니다.

-   :material-numeric-2-circle-outline:{ .lg .middle } **분포로 위험을**

    몬테카를로 · 시나리오로 거시 쇼크 때 채권 손실(평균 · P95 · P99)과 한도 재배정의 절감액을 숫자로 냅니다.

-   :material-numeric-3-circle-outline:{ .lg .middle } **자동화와 보고**

    조기경보 규칙을 GitHub Actions로 자동 실행하고, 경영진 리포트를 AI 초안 + 숫자 추적 + 사람 서명으로 만듭니다.

</div>

"LLM은 번역가 · 솔버는 계산기 · 테스트는 감사인 / 자동은 알림까지 · 결정은 사람이 한다"가 오늘의 기준입니다.

!!! info "금요일에서 월요일로 — 모두 같은 기준 파일로 시작합니다"

    3일차에 각자 만든 `d3_end_scored.csv`는 **제출물**이고, 오늘 입력은 모두 같은 **3일차 기준 등급 파일 `d4_start_scored.csv`**(바이어 150곳 · 등급 S 127 · A 2 · B 3 · C 18)입니다. 같은 숫자에서 출발하니 옆 사람과 결과를 견주기 쉽습니다. 내 등급 분포는 점심 전에 1분만 이 기준과 견주어 보세요 — 다르면 임계값이나 특성이 어디서 갈렸는지가 좋은 질문입니다.

## 시간표 {#schedule}

<div class="tf-timeline" markdown>

1. <time>08:30–09:00</time> **입실** 시작 파일이 열립니다 — 내 저장소에서 `uv run python tools/get_day_files.py 4` · Claude Code 로그인 · 입력창 아래 모드 확인
2. <time>09:00–09:50</time> **1교시** 현업 문제(한도 · 쇼크 손실 · 경보) · 의사결정 최적화(결정변수 · 목적 · 제약 · LP/MIP · 솔버 · 잠재가격 · LLM 코파일럿) — 시연 1
3. <time>10:00–10:50</time> **2교시** 시뮬레이션(몬테카를로 · 시드 · VaR · 시나리오 · 수렴 · 상관) · 조기경보 설계(회수 사다리 · 규칙 대 모델 · P1–P4 · 정밀도) — 시연 2 · 3
4. <time>11:00–11:50</time> **3교시** 규칙 파일 · 자동화(트리거 · cron · Actions · 웹훅 · 멱등성) · 문서·보고 자동화(파이프라인 · 구조화 출력 · 레드팀) — 시연 4 · 5 · 오후 안내
5. <time>11:50–13:00</time> **점심** 점심 전에 내 저장소를 VS Code로 열고 `get_day_files.py 4` · `uv sync`가 되는지 확인해 둡니다
6. <time>13:00–14:50</time> **4–5교시** <span class="tf-chip tf-chip--must">실습 A</span> [한도 최적화와 스트레스 테스트](lab-a.md) — 14:00 worktree 장 · 14:45 기대값 테스트
7. <time>15:00–16:50</time> **6–7교시** <span class="tf-chip tf-chip--must">실습 B</span> [경보 자동화와 경영진 리포트](lab-b.md) — 15:00 실습 B 파일 · 16:45 PR
8. <time>17:00–17:50</time> **8교시** 실험 카드 결과 공유 · 아침에 건 예약 실행 확인 · 시연 6 엑셀 안의 AI · 정리 · 질문

</div>

쉬는 시간은 09:50 · 10:50 · 13:50 · 14:50 · 15:50 · 16:50(각 10분)입니다. 이론의 요약은 [이론 요약](theory.md)에 있습니다.

## 시연 여섯 건 — 오전 다섯 · 8교시 하나 {#demos}

시연은 늘 **상황 → 입력 → 결과** 순서로 봅니다. 오후에는 그 시연을 줄이거나 바꿔서 내 저장소에서 합니다.

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">시연 1 · Claude Code(Plan)</span>

    **규정 문장에서 한도 엔진까지**

    규정 · CSV 3종 · 설계 1쪽 → 한도안(한도 · 걸린 제약 · 잠재가격) · 모델 카드 · 테스트 로그

    <small>오후: 실습 A 02–03 — 설계 1쪽 · 답안 카드 · 속성 테스트로 줄인 판</small>

-   <span class="tf-eyebrow">시연 2 · Claude Code</span>

    **쇼크 시뮬레이터와 웹 리포트**

    3일차 결과 · 원/달러 3년 · CSV 3종 → HTML 한 장(시나리오 표 · 손실 분포) · 결과 CSV

    <small>오후: 실습 A 05 — 제공 스크립트 + 내 시나리오 U1</small>

-   <span class="tf-eyebrow">시연 3 · Claude Code</span>

    **계좌 변경 메일을 먼저 읽는다**

    메일 4통 · 연락처 · 사기 신호 점수표 → 위험 점수 · 콜백 목록(사람 승인 전)

    <small>오후: 실습 B 확장 — 메일 한 통을 두 AI로</small>

-   <span class="tf-eyebrow">시연 4 · Claude Code + GitHub Actions</span>

    **조기경보를 평일 아침 9시에**

    경보 규칙 YAML · CSV 2종 · 저장소 → 녹색 체크 · 자동 이슈(다시 돌려도 1건) · 결과 4종

    <small>오후: 실습 B 01–02 — 내 규칙 1개 + 수동 버튼 실행</small>

-   <span class="tf-eyebrow">시연 5 · Claude Code + Claude + ChatGPT</span>

    **경영진 신용 리스크 리포트**

    지표 JSON · Word 템플릿 → 보고서 2쪽 · 숫자 대조표 · 레드팀 판단표

    <small>오후: 실습 B 03–05 — 독자 카드 1장 · 레드팀</small>

-   <span class="tf-eyebrow">시연 6 · Excel + Claude for Excel · 8교시</span>

    **엑셀 안의 AI와 한도 워크북**

    오류가 든 한도 워크북 → 오류 원인 · 셀 인용 설명 · 변경 내역 표 · 해 찾기는 사람

    <small>실습 A의 완성본(엑셀판 같은 모델)과 같은 워크북</small>

</div>

## 오후 실습 지도 {#map}

<div class="grid cards tf-cols-2" markdown>

-   <span class="tf-eyebrow">실습 A · 13:00–14:50</span>

    **[한도 최적화와 스트레스 테스트](lab-a.md)**

    01 준비 → 02 모델(Plan 표 · 질문 → 답안 카드) → 03 검증(속성 테스트 8개 · 기록) → 04 실험 카드(worktree) → 05 스트레스(내 시나리오) → 06 기대값 테스트 · PR

    <small>만드는 것: 한도 엔진 · 한도안 xlsx · 모델 카드 · 실험 기록 · 스트레스 표 · PR 1개</small>

-   <span class="tf-eyebrow">실습 B · 15:00–16:50</span>

    **[경보 자동화와 경영진 리포트](lab-b.md)**

    01 규칙·엔진(내 규칙 1개) → 02 자동 실행(PR → 병합 → Run workflow → 이슈) → 03 독자 카드 1장 → 04 레드팀 → 05 기록(PR)

    <small>만드는 것: 경보 엔진 · 워크플로 · 자동 이슈 · 보고 파일 · 대조표 · 레드팀 표 · PR 2개</small>

</div>

**점검 시각 한눈에** — 13:10 브랜치 · 13:35 Plan 표 · 13:50 속성 테스트 8개 · 14:15 실험 한 줄 · 14:40 스트레스 해석 · **14:45 기대값 테스트** · 14:50 PR · 15:20 경보 건수 · 15:45 녹색 체크와 이슈 1건 · 16:20 렌더된 파일 1개 · 16:35 불일치 0과 레드팀 반영 · **16:45 PR**. 막히면 손을 들거나 노트북 위에 빨간 표시를 올리세요 — 강사가 돌며 한 분씩 2–3분 확인합니다. **실습 B는 실습 A가 끝나지 않아도 할 수 있습니다**(경보 엔진은 실습 A의 결과를 쓰지 않습니다).

**오늘 쓰는 프롬프트** — 실습 쪽의 단계 카드마다 들어 있고, [프롬프트 라이브러리](../prompts/day4.md)에 모두 모여 있습니다.

| 실습 | 프롬프트 |
|---|---|
| A 01–06 | [A1 시작(Plan)](../prompts/day4.md#a1) · [A2 질문에 답하기](../prompts/day4.md#a2) · [A3 테스트 실패 시](../prompts/day4.md#a3) · [A3-기록](../prompts/day4.md#a3-log) · [A4 정책 실험](../prompts/day4.md#a4) · [A4-가져오기](../prompts/day4.md#a4-bring) · [A5 스트레스](../prompts/day4.md#a5) · [A6 PR](../prompts/day4.md#a6) |
| B 01–05 | [B1 경보 엔진 + 자동 실행](../prompts/day4.md#b1) · [B1-기준일](../prompts/day4.md#b1-asof) · [B1-멱등](../prompts/day4.md#b1-idem) · [B2-CC 해석](../prompts/day4.md#b2-cc) · [B3 독자 카드 ② ③](../prompts/day4.md#b3) · [B4 레드팀](../prompts/day4.md#b4) · [B4-표](../prompts/day4.md#b4-table) · [B4-고침](../prompts/day4.md#b4-fix) · [B4-점검](../prompts/day4.md#b4-check) · [B6 PR](../prompts/day4.md#b6) |
| 막힐 때 · 더 하기 | [어디서 갈렸나](../prompts/day4.md#mismatch) · [채팅 경로](../prompts/day4.md#chat-path) · [확장 프롬프트](../prompts/day4.md#more) · [시연 프롬프트](../prompts/day4.md#demos) |

## 쓰는 도구 {#tools}

| 도구 | 어디서 | 오늘 쓰는 곳 |
|---|---|---|
| **Claude Code** (VS Code 확장) | 내 PC의 VS Code | 실습 A · B 대부분 — 첫 프롬프트는 **Plan**, 계획 승인 창에서 **`2 Yes, and manually approve edits`**, 명령은 허락 창을 읽고 승인 |
| **Git · GitHub** | VS Code 소스 제어 · github.com | 브랜치 `d4-limits` · `d4-ews` · `d4-report` · worktree · 커밋 · push · PR · **Actions 탭** · Issues · 짝 리뷰 |
| **uv · Python** | VS Code 터미널 | `uv run`으로 한도 엔진(PuLP · SciPy) · 시뮬레이터 · 경보 엔진 · pytest — `uv sync`로 만든 환경 |
| **ChatGPT** · **Claude** | 브라우저 | 보고서 해석 · **레드팀은 초안과 다른 쪽**으로 · Claude Code를 못 쓸 때의 채팅 경로 |
| **엑셀** | 내 PC · 웹용 Excel | 결과 보기 · 8교시 시연 6 · 엑셀판 같은 모델(완성본) |

!!! note "Claude Code는 유료 구독이 필요합니다"

    Claude Code는 Pro 이상 구독이나 API(Console) 계정으로 로그인합니다. 설치가 막힌 PC는 내 저장소의 **Codespaces**를, 계정이 없으면 **채팅 경로**로 같은 실습을 합니다 → [실습 A 채팅 경로](lab-a.md#chat-path) · [실습 B 채팅 경로](lab-b.md#chat-path). 실습 B 03의 Word 렌더에 쓰는 `docxtpl`은 과정 환경에 들어 있습니다 — 없다고 나오면 `uv sync`를 한 번 합니다.

## 파일 받기 {#files}

**내 저장소에서 명령 하나**면 됩니다. 오늘 파일을 같은 경로로 받고, 작업 사본을 `workbench/day4/data/`에 만들어 줍니다.

```text
uv run python tools/get_day_files.py 4
```

- 카드에 잠금 표시가 있는 파일은 그 시각 뒤에 받습니다 — 시작 파일 · 엑셀판 모델 **08:30**, 카드 ⑥ ⑧ ⑨ 확인표 **14:15**, 기대값 테스트 **14:45**, 실습 B 파일(경보 테스트 · 참고 엔진 · 렌더 · 숫자 대조 · 지표 JSON) **15:00**, 기준 결과 워크북 **18:00**(수업 뒤 복습용). 같은 명령을 다시 실행하면 새로 열린 파일만 받습니다.
- **원본(`data/`, `labs/`)은 고치지 않습니다.** 고쳐 쓸 파일(정책 숫자 · 시나리오 · 데이터 사본)은 `workbench/day4/data/`의 작업 사본에서 하고, 테스트와 참고 스크립트는 원본 자리(`labs/day4/`)에서 돌립니다.
- 새 폴더(worktree)에는 `.venv`와 받은 파일이 없습니다 — `uv sync`와 위 명령을 한 번 더 실행합니다.
- 막히면 아래 카드에서 직접 받습니다. 맨 위 **`day4_files.zip`**을 받아 압축을 풀면 `D4` 폴더가 생깁니다(그 시각까지 열린 파일만 들어 있습니다). 저장소 없이 채팅 경로로 하는 사람은 이 방법을 씁니다.

--8<-- "docs/_snippets/day4/files_all_cards.md"

## 데이터와 이용 조건 {#data}

- 오늘 쓰는 데이터는 모두 **(가상) 한빛정밀(주)의 합성 데이터**이거나 **공개 데이터**입니다. 한빛정밀(주)과 바이어 150곳, 연체 · 등급 · 한도 · 가상 메일과 여신관리규정(`rag/corpus/hanbit_credit_policy.md`)은 교육용 가상이며 실존 기업 · 기관과 무관하고, 숫자는 실제 거래 기록이 아닙니다. 투자 · 여신 · 보험 판단 자료가 아닙니다.
- 합성 데이터와 문서는 CC BY 4.0, 코드는 MIT입니다. 환율(`fx_forecast_inputs.csv` · `fx_krw_daily.csv`)은 미국 연준 H.10 환율(FRED 제공)로 'Public Domain: Citation Requested'이며 인용 방법은 저장소의 `data/external/ATTRIBUTION.md`에 있습니다. 정책 숫자 표(`d4_params.csv`)의 금리 · 환율 값은 교육용 기준일의 공개 값을 옮긴 것이고 거래용이 아닙니다. 국가위험등급은 OECD 국가위험분류를 옮겨 적은 값입니다. 라이선스 전문은 저장소의 `LICENSE-DATA.md` · `NOTICE.md`에 있습니다.
- 보험 약관 본문은 이 저장소에 없습니다(재배포하지 않습니다). 오늘 슬라이드와 점수표가 말하는 약관 관련 내용은 개념 설명이고, 실제 조항은 각자 공식 자료와 담당 부서로 확인합니다.
- 열 하나하나의 뜻은 [데이터 → 시작 파일의 주요 열](../data.md#checkpoint-columns)에 있습니다.
- **오늘 파일은 합성 데이터라 ChatGPT · Claude 같은 AI 도구에 올리거나 붙여 넣어도 됩니다.** 다만 **회사 실데이터 · 개인정보는 어떤 AI 도구에도 넣지 않습니다 — 익명화본도.** AI 서비스의 '모델 개선(학습)' 설정은 끄고 시작하고([사전 준비 — AI 학습 설정 끄기](../setup.md#ai-training)), 내 저장소는 공개이므로 **키 · 비밀번호 · 회사 자료는 커밋하지 않습니다.**
- 오늘 메일 예제의 회사 · 도메인 · 전화번호 · 계좌는 모두 가상이고, 실제로 존재하지 않는 도메인입니다.

## 오늘의 결과물과 제출 {#submit}

<div class="tf-checklist" data-title="오늘 남길 것" markdown>

- [ ] **한도안** — `scripts/limits_lp.py` · `limits_proposed.xlsx`(limits · constraints · summary) · `model_card.md` · 속성 테스트 8개 통과
- [ ] **실험 기록** — `workbench/day4/experiments.md`(기준 모델 · 실험 한 줄 · 스트레스 3줄 · 기대값 대조)
- [ ] **스트레스 표** — `stress_results.csv` · `loss_hist.png` · 내 시나리오 해석('가정 시나리오에서의 추정')
- [ ] **경보 워크플로** — 내 규칙 1개 · `scripts/ews.py` · `.github/workflows/d4-ews.yml` · 초록 체크 · 자동 이슈 1건
- [ ] **보고 파일** — 독자 카드 1장(docx · xlsx · txt) · `number_trace.csv` 불일치 0 · `redteam.md`(반영 / 기각과 이유) · 체크리스트 사본 `review_checklist.md`(체크 · 서명)
- [ ] **PR 3개** — `d4-limits` · `d4-ews`(병합) · `d4-report` — 링크를 <span data-tf-link="submit_form">제출 폼</span>에

</div>

- **제출 = push · PR**입니다. 점검 기준은 **'파일이 있다'가 아니라 검증한 흔적** — 테스트 통과 · 기대값과의 대조 · 숫자 대조 · 레드팀 판단입니다.
- **병합(merge)은 내가 GitHub 화면에서 직접** 누릅니다. 오늘은 워크플로 PR(`d4-ews`)만 main에 병합합니다 — `Run workflow` 버튼은 main에 있는 워크플로 파일에만 생깁니다.
- PR 본문 · 커밋 메시지 · 보고서에 **회사 이름 · 실명 · 실제 숫자를 쓰지 않습니다.** 저장소가 공개입니다. 다 끝내지 못했어도 그대로 push하세요.

## 함께하는 규칙 {#rules}

- **1:1 순회**: 강사가 실습 동안 한 분씩 2–3분 확인합니다. 막히면 손을 들거나 빨간 표시를 올립니다.
- **짝과 서로 PR을 리뷰**: 서로의 PR에 코멘트 하나씩 — 바뀐 파일 · 커밋 메시지의 '왜' · 실데이터가 없는지 · 키가 없는지 · 한 줄 코멘트.
- **숫자보다 절차**: 난수 방식 · 솔버에 따라 P99나 바이어별 한도의 끝자리는 조금씩 다릅니다. **목적함수 · 걸린 제약 · 평균이 공식 기대손실의 ±3% 안**이면 정상입니다. 이상하면 [어디서 갈렸나](../prompts/day4.md#mismatch)를 먼저 묻습니다.
- **옮겨 적기는 AI가, 대조와 판단은 사람이**: 결과 숫자를 손으로 옮기지 않습니다. AI가 파일 값 그대로 기록하게 하고, 사람은 두세 개를 원본과 맞춰 봅니다.
- **허락 창은 읽고 승인**: 무엇을 · 어디에 · 지우는지 세 가지를 읽고 `1 Yes`. 파일 삭제 · 강제 push · `git reset --hard`는 거절합니다. 권한(`permissions`)과 예약(`cron`) 줄은 반드시 내가 읽고 승인합니다.
- **예약 실행은 수업 뒤에 끕니다**: 워크플로에 예약 줄을 더했다면 연습이 끝난 뒤 Actions 화면에서 **Disable workflow**를 누릅니다.
- **현장 이야기를 들려 주세요**: "우리 회사에서는 이렇게 한다"는 이야기는 6일차 도입 기획의 재료가 됩니다.

## 정리 · 자가 점검 · 내일 예고 {#tomorrow}

**오늘의 다섯 문장**

1. 식은 LLM, 계산은 솔버, 확인은 테스트.
2. 잠재가격 = 제약 1단위의 값 — 경영 질문에 숫자로 답한다.
3. 평균이 아니라 분포 — P99와 상관을 본다.
4. 경보 = 규칙 + 모델 + 사람, 자동은 알림까지.
5. 보고서 = 템플릿 + 구조화 출력 + 숫자 추적 + 서명.

**자가 점검** — 체크 표시를 눌러 보세요. 수업에서는 문항마다 손가락으로 1–5점을 매기고, 3점 이하가 많은 문항은 5일차 아침 복습 질문이 됩니다.

- [ ] 나는 매출과 손실을 함께 고려한 바이어별 한도를 산정하고, 위기 때 울릴 경보 로직을 설계할 수 있다
- [ ] 나는 잠재가격으로 제약의 값을 설명할 수 있다
- [ ] 나는 손실 분포의 평균 · P95 · P99를 읽을 수 있다
- [ ] 나는 경보 규칙을 GitHub Actions로 자동 실행할 수 있다
- [ ] 나는 AI 리포트를 숫자 추적 · 레드팀 · 서명으로 확정할 수 있다

- **복습**: [용어집 → 4일차](../glossary.md#day4)의 학습 모드 퀴즈로 오늘 용어를 복습합니다. 수업 뒤에는 4일차 기준 결과 워크북으로 내 한도안을 견줘 봅니다([A6-비교](../prompts/day4.md#a6-compare)).
- **내일 5일차 · 10/20(화)** — AI 금융 에이전트 및 채권 관리 종합 제어 대시보드 구축. 오늘의 한도 · 경보 · 리포트를 **웹 대시보드와 AI 에이전트**로 묶고, 경보 등급 P1–P4를 대시보드가 그대로 씁니다. 오늘 저장소에 남긴 PR · 이슈 · 실행 기록은 다시 돌릴 수 있는 형태여야 합니다 — 저녁에 한 번 점검해 두세요 → [5일차](../day5/index.md)
