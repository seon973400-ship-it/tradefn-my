---
title: 1일차 — 무역 금융 AI 트렌드 및 글로벌 바이어 데이터 탐색
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">1일차 · 10/14(수) · 09:00–17:50 · 원리 · 도구 · 환경 · 데이터 <span class="tf-daystate" data-tf-daystate="1"></span></span>

# 무역 금융 AI 트렌드 및 글로벌 바이어 데이터 탐색

**AI를 고르고, 근거를 요구하고, 데이터를 의심한다.** 오전에는 AI가 답을 만드는 원리와 도구 고르는 법, 일 시키는 법, 작업 환경(VS Code · Claude Code · Git)과 데이터 탐색 방법을 시연으로 보고, 오후에는 그 시연을 **작게, 그리고 조금 다르게** 모두가 직접 합니다.

<div class="tf-buttons" markdown>
[실습 A · 13:00](lab-a.md){ .md-button .md-button--primary }
[실습 B · 15:00](lab-b.md){ .md-button .md-button--primary }
[이론 요약](theory.md){ .md-button }
[프롬프트](../prompts/day1.md){ .md-button }
[파일 받기](#files){ .md-button }
</div>
</div>

## 오늘의 목표 {#goals}

<div class="grid cards tf-cols-3" markdown>

-   :material-numeric-1-circle-outline:{ .lg .middle } **AI를 고르고, 근거를 요구하며 시킨다**

    LLM의 원리를 알고 일에 맞게 ChatGPT · Claude · Claude Code · Cowork를 고른다

-   :material-numeric-2-circle-outline:{ .lg .middle } **내 작업 환경을 만든다**

    VS Code · Claude Code · Git · GitHub로 일하고, 보고서의 위험 신호를 인용과 함께 뽑는다

-   :material-numeric-3-circle-outline:{ .lg .middle } **데이터를 의심하며 탐색한다**

    바이어 데이터의 품질 · 분포 · 결제방식별 위험을 EDA로 정리하고 커밋으로 남긴다

</div>

오늘 끝에 남는 것 — **내 GitHub 저장소 · `CLAUDE.md` · 결과 파일 9종 · 커밋 2개 이상**. "들었다"가 아니라 "파일로 남았다"가 오늘의 기준이고, 오늘의 결과물은 내일 2일차 정제 · 특성 만들기의 입력이 됩니다.

## 시간표 {#schedule}

<div class="tf-timeline" markdown>

1. <time>08:40–09:00</time> **점검 데스크** 설치 · 로그인 확인(VS Code · 확장 3종 · Git · uv · Claude Code · GitHub) — 안 된 칸은 [사전 준비](../setup.md)
2. <time>09:00–09:50</time> **1교시** 시작하며(목표 · 데이터 위생) · AI 지형 2026 · LLM 원리 — 시연 1 딥 리서치 · 짧은 라이브 1 그라운딩
3. <time>10:00–10:50</time> **2교시** Claude 도구 3종 · AI에게 일 시키는 법 · 개발 환경 · Git 입문(앞) — 시연 2 PDF 공시 위험 신호
4. <time>11:00–11:50</time> **3교시** Git 입문(이어서) · EDA 방법론 · 무역금융 기초 — 시연 3 첫 프로젝트와 첫 커밋 · 시연 4 엑셀 → EDA 노트북 · 짧은 라이브 2 재무비율
5. <time>11:50–13:00</time> **점심** 12:30부터 설치 도움 데스크(계정 · 접속 문제는 이때)
6. <time>13:00–14:50</time> **4–5교시** <span class="tf-chip tf-chip--must">실습 A</span> [내 작업 환경 · 첫 커밋(A-1) → AI로 보고서 읽고 검증하기(A-2)](lab-a.md) · 14:40 기준값 공개
7. <time>15:00–16:50</time> **6–7교시** <span class="tf-chip tf-chip--must">실습 B</span> [바이어 데이터 진단과 사전(B-1) → EDA 노트북 · 검산 · 현안 정의(B-2)](lab-b.md)
8. <time>17:00–17:50</time> **8교시** 실습 해설 · 시연 5 Cowork로 오늘을 보고서로 · 결과 공유 · 정리 · 내일 예고

</div>

쉬는 시간은 09:50 · 10:50 · 13:50 · 14:50 · 15:50 · 16:50(각 10분)입니다.

## 오전 시연 {#demos}

시연은 늘 **문제 상황 → 입력 → 진행 과정 → 결과** 순서로 봅니다. 자세한 내용은 [이론 요약](theory.md)에 있습니다.

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">시연 1 · 딥 리서치</span>

    **다른 회사는 무역금융에 AI를 어떻게 쓰나**

    조사 질문 → 근거 링크가 달린 사례 표 + 진행 기록

    <small>오후: 근거를 열어 대조하는 습관 → 실습 A-2 · 02 인용 확인</small>

-   <span class="tf-eyebrow">시연 2 · PDF 공시 위험 신호</span>

    **영문 분기 공시로 신규 바이어의 지급 위험 보기**

    공시 PDF → 인용 · 쪽이 달린 위험 신호 표 + JSON + 두 AI 비교

    <small>오후: 실습 A-2 — 다른 회사(Halden)를 Claude Code로, 비율 · 교차 확인까지</small>

-   <span class="tf-eyebrow">시연 3 · Claude Code 첫 프로젝트</span>

    **결제방식별 미수금 · 연체 집계를 스크립트로**

    인보이스 CSV 5,033건 → 스크립트 · 표 · 차트 · GitHub 커밋 2개

    <small>오후: 실습 A-1 — 템플릿 → clone → CLAUDE.md → 첫 커밋</small>

-   <span class="tf-eyebrow">시연 4 · 엉망인 엑셀 → EDA 노트북</span>

    **병합 · 소계투성이 엑셀에서 연체가 몰린 곳 찾기**

    다중 시트 엑셀 → 품질 보고서 · 데이터 사전 · 실행된 EDA 노트북

    <small>오후: 실습 B — 바이어 150곳 파일로 같은 순서, 오류는 직접 찾기</small>

-   <span class="tf-eyebrow">시연 5 · Cowork</span>

    **하루 동안 흩어진 결과 파일을 보고서로**

    결과 폴더 → Word 메모 1쪽 + 메일 초안(숫자마다 근거 파일)

    <small>17:10 정리 시간에 함께 봅니다</small>

</div>

## 오후 실습 지도 {#map}

<div class="grid cards tf-cols-2" markdown>

-   <span class="tf-eyebrow">실습 A-1 · 13:00–13:50</span>

    **[내 작업 환경과 첫 커밋](lab-a.md#a1)**

    01 설치 점검 → 02 템플릿으로 내 공개 저장소 → 03 Clone · `uv sync` → 04 모드 Manual · CLAUDE.md에 내 규칙 → 05 첫 커밋 · push · 주소 제출

    <small>만드는 것: 내 저장소 주소 · `CLAUDE.md` · 커밋 1개</small>

-   <span class="tf-eyebrow">실습 A-2 · 14:00–14:50</span>

    **[AI로 보고서 읽고 검증하기](lab-a.md#a2)**

    01 위험 신호 표(A1) → 02 인용 2개 Ctrl+F → 03 비율 4개 코드로(A2) → 04 다른 AI 교차 확인(A3) → 05 기준값 비교 · 커밋

    <small>만드는 것: `d1_signals_halden.md` · `d1_ratios_halden.md` · 커밋 2개째</small>

-   <span class="tf-eyebrow">실습 B-1 · 15:00–15:50</span>

    **[바이어 데이터 진단과 사전](lab-b.md#b1)**

    01 진단(B1) → 02 AI가 놓친 문제 직접 찾기 → 03 결제조건 코드표(B2) · 내 판단 → 04 변수 정의서(B3) · 커밋

    <small>만드는 것: `d1_quality_report.md` · `d1_code_table.csv` · `d1_data_dictionary.md`</small>

-   <span class="tf-eyebrow">실습 B-2 · 16:00–16:50</span>

    **[EDA 노트북 · 검산 · 현안 정의](lab-b.md#b2)**

    01 EDA 노트북(B4) → 02 완성본 엑셀과 숫자 대조 → 03 현안 정의서(B5) → 04 조별 3분 → 05 재실행 · 커밋

    <small>만드는 것: `d1_eda.ipynb` · `charts/*.png` · `d1_eda_notes.md` · `d1_issue_definition.md`</small>

</div>

**점검 시각** — 13:20 설치 · 13:35 clone · 13:50 첫 push · 14:20 인용 표시 · 14:40 기준값 · 14:50 두 번째 push · 15:20 진단 · 15:50 사전 커밋 · 16:15 차트 · 16:35 현안 초안 · 16:50 재실행 · push. 실습 쪽 오른쪽(휴대폰은 화면 아래)의 진행 카드가 **지금 권장 단계와 다음 점검 시각**을 알려 줍니다.

막히면 손을 들거나 노트북 위에 빨간 표시를 올리세요. 강사가 돌며 한 분씩 2–3분 확인합니다. 빨리 끝난 사람을 위한 **'다 했으면'** 카드가 실습 A · B 끝에 있습니다.

**오늘 쓰는 프롬프트** — 실습 쪽 단계마다 들어 있고, 한곳에 모은 것은 [프롬프트 라이브러리](../prompts/day1.md)입니다.

| 단계 | 프롬프트 |
|---|---|
| A-1 · 04 | [S0 연결 확인](../prompts/day1.md#s0) · [A0 CLAUDE.md에 내 규칙](../prompts/day1.md#a0) |
| A-2 · 01–05 | [A1 위험 신호 표](../prompts/day1.md#a1) · [A1 재질문](../prompts/day1.md#a1-retry) · [A2 비율 계산](../prompts/day1.md#a2) · [A3 교차 확인](../prompts/day1.md#a3) · [S1](../prompts/day1.md#s1) · [S2](../prompts/day1.md#s2) · [S7](../prompts/day1.md#s7) |
| B-1 · 01–04 | [B1 진단](../prompts/day1.md#b1) · [S3 열 값 목록](../prompts/day1.md#s3) · [B2 코드표](../prompts/day1.md#b2) · [S4 내 판단](../prompts/day1.md#s4) · [B3 변수 정의서](../prompts/day1.md#b3) · [S7](../prompts/day1.md#s7) |
| B-2 · 01–05 | [B4 EDA 노트북](../prompts/day1.md#b4) · [S6 완성본과 대조](../prompts/day1.md#s6) · [B5 현안 정의서](../prompts/day1.md#b5) · [S7](../prompts/day1.md#s7) |

## 쓰는 도구 {#tools}

<div class="tf-stack" markdown>

| 도구 | 어디서 | 오늘 쓰는 곳 |
|---|---|---|
| **Claude Code** (VS Code 확장) | 내 PC의 VS Code | 실습 A · B 대부분 — 파일 읽기 · 코드 실행 · 커밋. 모드는 **Manual**(허락 창을 읽고 승인) |
| **ChatGPT 또는 Claude 웹** | 브라우저 | 실습 A-2 · 04 교차 확인(둘 중 하나), Claude Code를 못 쓸 때의 채팅 경로 |
| **Git · GitHub** | VS Code 소스 제어 · github.com | 내 공개 저장소에 커밋 · push — 과정 템플릿으로 만듭니다 |
| **Jupyter** (VS Code 확장) | VS Code | 실습 B-2 · 01 · 05 EDA 노트북 · 재실행 |
| **엑셀**(또는 웹용 Excel) | 내 PC · office.com | 실습 B-2 · 02 완성본 열어 숫자 대조 · 깨진 CSV 비교(A-1 · 01) |

</div>

!!! note "Claude Code는 유료 구독이 필요합니다"

    Claude Code는 Pro 이상 구독이나 API(Console) 계정으로 로그인합니다. 무료(Free) 플랜으로는 쓸 수 없습니다. 설치가 막힌 PC는 내 저장소에서 **Codespaces**를, 계정이 없으면 **채팅 경로**로 같은 실습을 합니다 → [실습 A 대체 경로](lab-a.md#chat-path) · [실습 B 채팅 경로](lab-b.md#chat-path).

## 파일 받기 {#files}

**내 저장소를 만들었다면 받을 것이 거의 없습니다.** 오늘 쓰는 파일은 과정 템플릿에 들어 있어 `data/day1/` · `labs/day1/` 아래에 있습니다. 저장소 없이 채팅 경로로 하는 사람이나 파일 하나가 필요한 사람은 아래 카드에서 받습니다 — 맨 위 **한 번에 받기**(ZIP)를 받아 압축을 풀면(Windows: 오른쪽 클릭 → **모두 압축 풀기**, Mac: 더블클릭) `D1` 폴더가 나옵니다. 보고서 발췌(`.md`)는 `D1/reports` 안에 있습니다. 강의 슬라이드 PDF도 여기 있습니다.

--8<-- "docs/_snippets/day1/files_all_cards.md"

`.md` 파일을 눌렀는데 글자 화면만 뜨면 링크를 **오른쪽 클릭 → 다른 이름으로 링크 저장**으로 받습니다. 늦게 저장소를 만들었다면 터미널에서 `uv run python tools/get_day_files.py 1`로 빠진 1일차 파일을 받습니다.

## 데이터와 이용 조건 {#data}

- 오늘 쓰는 데이터는 모두 **(가상) 한빛정밀(주)의 합성 데이터**이거나 **공개 공시**입니다. 한빛정밀(주)과 Halden은 교육용 가상 회사이며 실존 기업과 무관합니다.
- SEC 공시 발췌(iRobot · Wolfspeed 등)는 미국 SEC EDGAR의 공개 공시를 교육 목적으로 일부 옮긴 것입니다. 원문의 저작권과 책임은 각 회사에 있고, 투자 · 여신 판단 자료가 아닙니다.
- 열 하나하나의 뜻은 [데이터 → 바이어 스냅샷 핵심 컬럼](../data.md#buyers)에, 라이선스 전문은 저장소의 `LICENSE-DATA.md` · `NOTICE.md`에 있습니다.
- **회사 실데이터 · 개인정보는 올리지 않습니다 — 익명화본도.** AI 서비스의 '모델 개선(학습)' 설정은 끄고 시작하고([사전 준비 — AI 학습 설정 끄기](../setup.md#ai-training)), 내 저장소는 공개이므로 키 · 비밀번호 · 회사 자료는 커밋하지 않습니다.

## 오늘의 결과물과 제출 {#submit}

오늘 결과물은 **일곱 묶음, 파일로는 아홉 가지**입니다. 결과 파일은 `workbench/day1/outputs/`에, 노트북은 `workbench/day1/notebooks/`에 둡니다. 점검 기준은 '파일이 있다'가 아니라 **검증한 흔적**입니다.

<div class="tf-checklist" data-title="오늘 남길 것" markdown>

- [ ] **작업 환경** — 내 저장소 · `CLAUDE.md`(내 규칙 2줄) · 커밋 2개 이상, 메시지에 '왜' 줄
- [ ] **위험 신호 표** `d1_signals_halden.md` — 인용 2개 일치 · 불일치 표시
- [ ] **재무비율** `d1_ratios_halden.md` — 공식 · 대입값 · 두 AI 대조(+ `scripts/ratios_halden.py`)
- [ ] **품질 보고서 · 변수 정의서** `d1_quality_report.md` · `d1_data_dictionary.md` — 재무 지표 4개 정의 포함
- [ ] **코드표** `d1_code_table.csv` — '검토 필요' 0행
- [ ] **EDA 노트북 · 차트 · 메모** `d1_eda.ipynb` · `charts/*.png` · `d1_eda_notes.md` — 해석 3줄 · 피벗 대조 1개(손 검산 절)
- [ ] **현안 정의서** `d1_issue_definition.md` — 결제방식별 근거 숫자 · '내 업무라면'은 내 글

</div>

- **제출 = push**입니다. 실습 A-1 · 05에서 내 저장소 주소를 <span data-tf-link="submit_form" data-tf-empty="제출 폼(수업 중 화면 · 오픈채팅 공지로 받은 주소)">제출 폼</span>으로 한 번 내면, 그 뒤로 push한 커밋을 강사가 저장소 주소 목록으로 확인합니다.
- 현안 정의서의 '내 업무라면' 칸과 메모에는 **회사 이름 · 실명 · 실제 숫자를 쓰지 않습니다.** 저장소가 공개입니다.
- 다 끝내지 못했어도 그대로 push하세요. 내일 아침 **첫 명령 하나**(`uv run python tools/get_day_files.py 2`)로 2일차 시작 파일을 받아 모두 같은 출발점에서 시작합니다.
- 17:00에는 이 목록을 다시 띄우고 흔한 실수를 함께 짚습니다. 정답 파일은 그때 강사 화면으로만 보여 드립니다.

## 함께하는 규칙 {#rules}

- **1:1 순회** — 강사가 실습 동안 한 분씩 2–3분 확인합니다. 막히면 손을 들거나 빨간 표시를 올립니다.
- **짝과 한 화면** — 막히면 짝과 한 화면을 같이 봐도 좋습니다. 정답을 베끼는 것이 아니라 **AI가 놓친 문제를 서로 찾아 견주는** 용도입니다.
- **새 일 = 새 대화** — 한 대화에서는 문서(파일) 하나만 다룹니다. 같은 문서로 이어 가는 프롬프트(A1 → A2)는 같은 대화에, 다른 문서나 다른 일은 새 대화에서 시작합니다.
- **허락 창은 읽고 승인** — 무엇을 · 어디에 · 지우는지 세 가지를 읽고 `1 Yes`. 파일 삭제 · 강제 push · `git reset --hard`는 거절합니다.
- **손일은 AI에게, 판단은 내가** — 옮겨 적기 · 표 만들기 · 커밋은 보조 프롬프트로 맡기고, 일치 · 불일치와 원인 한 줄은 직접 씁니다.
- **현장 이야기를 들려 주세요** — "우리 회사에서는 이렇게 한다"는 이야기는 6일차 도입 기획의 재료가 됩니다(파일에는 회사 이름 · 숫자 없이).

## 정리 · 자가 점검 · 내일 예고 {#tomorrow}

**오늘 배운 것 다섯 줄**

1. LLM은 다음 토큰을 확률로 고른다 — 근거를 주고 검증한다.
2. 일에 맞는 작업대를 고른다 — 대화 · 조사 · 맡기기 · 만들기.
3. 프롬프트보다 컨텍스트 — 6요소 · 태그 · 형식 · 근거.
4. 재현과 이력 — 스크립트 · 노트북 · CLAUDE.md · Git 커밋.
5. EDA는 구조 → 품질 → 분포 → 관계 → 질문 — 오늘은 결제방식별 위험까지 왔다.

<div class="tf-checklist" data-title="자가 점검" markdown>

- [ ] LLM이 답을 만드는 방식(다음 토큰 예측)과 할루시네이션이 생기는 이유를 설명할 수 있다
- [ ] 일에 맞는 AI 도구(대화 · 조사 · 맡기기 · 만들기)를 고르고, 학습 설정을 끌 수 있다
- [ ] 6요소 프롬프트로 근거(인용 · 위치)를 요구하고, 인용을 원문에서 확인할 수 있다
- [ ] VS Code · Claude Code · Git · GitHub로 커밋을 올릴 수 있다
- [ ] 데이터를 EDA 다섯 단계로 의심하며 탐색하고, 결제방식별 현안을 한 쪽으로 정의할 수 있다
- [ ] L/C · T/T · O/A와 유동비율 · 부채비율 · DSO · 영업이익률의 뜻을 설명할 수 있다

</div>

- **복습** — [용어집 → 1일차](../glossary.md#day1)의 학습 모드 퀴즈로 오늘 용어를 복습합니다.
- **내일 2일차 · 10/15(목)** — 금융/재무 데이터 전처리 및 리스크 평가지표 변수화. 첫 장은 Git 협업입니다 — 이슈 → 브랜치 → PR → 리뷰 → 머지를 직접 해 보고, worktree로 Claude Code 세션 두 개를 나란히 돌립니다. 아침 첫 명령은 `uv run python tools/get_day_files.py 2`입니다. 나가시기 전에 오늘 push가 GitHub에 올라갔는지 한 번만 확인해 주세요 → [2일차](../day2/index.md)
