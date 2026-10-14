---
title: 6일차 — 실전 적응력 고도화 및 자사 솔루션 도입 기획(해커톤)
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">6일차 · 10/21(수) · 09:00–17:50 · 해커톤 — 도입 기획 · 솔루션 킷 · 거버넌스 · ROI <span class="tf-daystate" data-tf-daystate="6"></span></span>

# 실전 적응력 고도화 및 자사 솔루션 도입 기획

**위기 카드 한 장으로 6일의 도구를 한 번에 돌린다.** 오늘은 강의 대신 해커톤입니다 — 이론은 아침 30분과 10시 · 11시 · 14시 · 15시의 짧은 브리핑 네 번, 나머지는 4인 팀의 팀 저장소에서 Claude Code · ChatGPT · Claude로 직접 일합니다. 저녁에는 **다른 사람이 그대로 다시 돌릴 수 있는 팀 솔루션 킷 `v1.0`**과 **각자 회사로 들고 갈 도입 기획서**가 남습니다.

<div class="tf-buttons" markdown>
[실습 A · 09:31](lab-a.md){ .md-button .md-button--primary }
[실습 B · 14:12](lab-b.md){ .md-button .md-button--primary }
[이론 요약](theory.md){ .md-button }
[프롬프트](../prompts/day6.md){ .md-button }
[위기 카드](cards.md){ .md-button }
[솔루션 킷](kit.md){ .md-button }
[심사 기준](judging.md){ .md-button }
[제출](submit.md){ .md-button }
[파일 받기](#files){ .md-button }
</div>
</div>

## 오늘의 목표 — 저녁에 남는 세 가지 {#goals}

<div class="grid cards tf-cols-3" markdown>

-   :material-numeric-1-circle-outline:{ .lg .middle } **도구를 한 흐름으로**

    위기 카드 한 장에 1–5일차 도구를 돌려 무엇이 **먼저 깨지는지** 숫자로 보입니다.

    <small>남는 것: 팀 솔루션 킷 `v1.0`(15:50)</small>

-   :material-numeric-2-circle-outline:{ .lg .middle } **AI의 초안을 검증으로**

    AI가 쓴 SOP · ROI를 근거 조항과 **다른 모델 · 사람 승인**으로 확인하고, 결론 먼저 · 숫자와 근거로 답합니다.

    <small>남는 것: 7분 데모(16:05부터)</small>

-   :material-numeric-3-circle-outline:{ .lg .middle } **자사 도입을 기획으로**

    기준선이 있는 KPI 3개 · **보수안부터** ROI · 30일 계획으로 우리 회사 도입안을 씁니다.

    <small>남는 것: 개인 기획서 · KPI · ROI(17:50)</small>

</div>

"계산은 코드 · 해석과 초안은 AI · 결정은 사람"이 6일 내내의 기준이고, 오늘의 심사 기준도 같습니다 — 화려함이 아니라 **근거가 있는가, 다른 사람이 다시 돌릴 수 있는가**. 어제 결과물이 없거나 깨졌어도 괜찮습니다: 강사 정답본으로 합류하고 README에 어느 단계에서 합류했는지만 적으면 감점이 없습니다.

## 하루 흐름과 체크포인트 {#schedule}

<div class="tf-timeline" markdown>

1. <time>09:00–09:31</time> **킥오프** — 목표 · 규칙 · 심사 기준 · AI 도입 기획(도입 3단계 · 멈추는 곳 · 스트레스 테스트) · **시연 1**(09:10 걸기 → 09:20 결과) · 역할 = 가동 8단계(09:26) · 파일 자동 공개(09:28)
2. <time>09:31–09:50</time> **위기 카드 개봉** <span class="tf-chip tf-chip--must">실습 A</span> [Step 1 카드 해석 · 변수표](lab-a.md#a-card)
3. <time>10:00–10:11</time> **브리핑 ① 솔루션 킷** — 팀 저장소 · 이슈에서 릴리스까지 · worktree(미니 시연 1) · `CLAUDE.md`와 권한
4. <time>10:11–10:40</time> <span class="tf-chip tf-chip--must">실습 A</span> [Step 2 설계 · 이슈](lab-a.md#a-design) → **CP1 10:40** 설계도 · README 골격
5. <time>11:00–11:10</time> **브리핑 ② 거버넌스와 보안** — SOP · AI 사용 규칙서 · 권한 잠금(미니 시연 2)
6. <time>11:10–11:45</time> <span class="tf-chip tf-chip--must">실습 A</span> [Step 3 가동 ③–⑤](lab-a.md#a-run1) · 11:15 일부 카드의 추가 단계 · **11:30 인젝트 1** → **CP2 11:45** 스탠드업 · `v0.5`
7. <time>12:00–13:00</time> 점심 — 강사가 팀 저장소를 보고 오후 우선순위 카드를 씁니다.
8. <time>13:00–13:50</time> <span class="tf-chip tf-chip--must">실습 A</span> [Step 4 가동 ⑥–⑧](lab-a.md#a-run2) · **13:15 인젝트 2** · 13:20 1:1 코칭 시작
9. <time>14:00–14:12</time> **브리핑 ③ ROI와 KPI** — 기준선 · 보수안 · AI 운영비 · **시연 2**(14:00 걸기 → 14:10 결과)
10. <time>14:12–14:50</time> <span class="tf-chip tf-chip--must">실습 B</span> [Step 5 ROI · KPI](lab-b.md#b-roi) → **CP3 14:50** SOP · ROI 초안
11. <time>15:00–15:10</time> **브리핑 ④ 확산과 데모** — 사내 도입 퍼널 · 7분 데모 · **시연 3**(15:00 걸기 → 15:10 결과)
12. <time>15:10–15:50</time> <span class="tf-chip tf-chip--must">실습 B</span> [Step 6 킷 마감](lab-b.md#b-release) → **CP4 15:40** 코드 프리즈 → **15:50 `v1.0` 링크**
13. <time>16:05–17:05</time> <span class="tf-chip tf-chip--must">실습 B</span> [Step 7 7분 데모](lab-b.md#b-demo) × 5팀(16:05 · 16:15 · 16:25 · 16:35 · 16:45) → 사후 진단 · 동료 투표(17:05 마감)
14. <time>17:10–17:50</time> <span class="tf-chip tf-chip--must">실습 B</span> [Step 8 기획서 마감](lab-b.md#b-plan) — 시상 · 서면 심사표 · 6일 총정리 → **17:50 개인 제출**

</div>

- 1:1 코칭 10분은 13:20–15:30 사이 내 시각에 있습니다(순서는 09:00 봉투 첫 장). 자리를 비우는 동안 내 역할은 **대행자**가 맡습니다.
- 인젝트 시각(11:30 · 13:15)에는 **전원 기립 → 낭독 → 10분 타이머**입니다. 낭독 전에는 노트북을 만지지 않습니다.

## 시연 다섯 건과 우리가 해 보는 것 {#demos}

시연 1 · 2 · 3은 **걸어 두고** 이론을 보며 기다리고, 미니 시연 둘은 브리핑 안에서 2–3분입니다. 오후 실습은 이 시연을 줄이거나 조금 바꿔 우리 카드 · 우리 숫자로 모두가 해 봅니다.

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">시연 1 · 위기 카드 파이프라인 · Claude Code(Plan)</span>

    **핵심 바이어의 회생 공시 — 15분 안에 숫자 · 근거 · 사람이 결정할 목록**

    위기 카드 · CSV · 한도 LP · 규정 · 약관 → 한도 변경표 · EL 표 · 경보 · 근거표 · SOP 초안 · 결정 기록(결정자 칸은 빈칸)

    <small>실습 A — 우리 카드 · 팀 팩 · 역할마다 세션 하나</small>

-   <span class="tf-eyebrow">미니 시연 1 · worktree로 두 세션</span>

    **한 사람이 두 역할 — 작업대를 하나 더**

    저장소 하나 → 작업대(폴더) 둘 · 세션 둘

    <small>실습 A [2-4 겸임자의 작업대](lab-a.md#a-worktree)</small>

-   <span class="tf-eyebrow">미니 시연 2 · 권한이 실제로 막는 장면</span>

    **`CLAUDE.md`는 부탁, deny는 잠금**

    `settings.json`의 deny + 가짜 `.env` → 거부 표시 · `.env.example` 제안

    <small>실습 A [2-1 팀 규칙 · 권한](lab-a.md#a2-rules)</small>

-   <span class="tf-eyebrow">시연 2 · 엑셀 ROI를 웹 계산기로 · Claude Code</span>

    **"DSO가 하루만 줄면? 사용료가 두 배면?"에 바로 답하기**

    수식이 든 ROI 엑셀 + 모델 단가표 → 테스트로 증명한 계산기

    <small>실습 B — 우리 카드 ROI 완성본 + 가장 약한 가정(계산기는 선택)</small>

-   <span class="tf-eyebrow">시연 3 · README와 릴리스 v1.0 · Claude Code + gh</span>

    **코드 프리즈 40분 전 — README · 보안 · 재현**

    저장소 이력 · 점검표 → README · 보안 점검 · PR · 릴리스 · 새 폴더 재현 '차이 0줄'

    <small>실습 B [Step 6](lab-b.md#b-release) — 우리 저장소에서 같은 순서로</small>

</div>

## 오후까지의 실습 지도 {#map}

<div class="grid cards tf-cols-2" markdown>

-   <span class="tf-eyebrow">실습 A · 09:31–13:50</span>

    **[우리 카드로 스트레스 테스트](lab-a.md)**

    Step 1 카드 해석 · 변수표 → Step 2 설계 · 이슈(CP1) → Step 3 가동 ③–⑤ · 인젝트 1 · `v0.5`(CP2) → Step 4 가동 ⑥–⑧ · 다른 모델 검증 · 인젝트 2 결정 기록

    <small>만드는 것: 변경 데이터 · 등급 · 한도 · EL · 경보 · 근거표 · SOP v1 · 결정 기록</small>

-   <span class="tf-eyebrow">실습 B · 14:12–17:50</span>

    **[증명하고, 남기고, 보여 준다](lab-b.md)**

    Step 5 ROI · KPI(CP3) → Step 6 킷 마감(CP4 → `v1.0`) → Step 7 7분 데모 → Step 8 기획서 마감

    <small>만드는 것: ROI 3안 · 나만의 KPI · README · `v1.0` · 데모 · 개인 기획서</small>

</div>

## 오늘의 규칙 한 장 {#rules}

| 항목 | 내용 |
|---|---|
| 팀 | 4인 × 5팀 · 팀 저장소 = 5일차에 조장이 킷 템플릿으로 만든 **비공개** `tradefin-kit-T{조}`(팀원 · 강사는 협업자) |
| 카드 | 팀마다 위기 카드 1장(09:31) + 공통 인젝트 2장(11:30 · 13:15) → [위기 카드](cards.md) |
| 재료 | 1–5일차 산출물(내 것 또는 강사 정답본) · Claude Code · ChatGPT · Claude |
| 원칙 | **가상 데이터만** · 메일은 **DRY RUN**(실제 발송 0건) · AI 출력엔 **근거** · 사람 결정 4종은 **빨간색** |
| 제출 | 팀 15:50 릴리스 `v1.0` 링크 · 개인 17:50 기획서 · KPI · ROI(비공개 폼) → [제출](submit.md) |
| 막히면 | 그 AI에게 오류 전문 → 팀 → 빨간 스티커 · **20분 막히면 정답본 합류(감점 없음)** |

!!! warning "사람이 결정하는 네 가지 — 표에서 빨간색"

    **한도 변경 · 선적 보류(해제) · K-SURE 통지 · 바이어 발송.** AI와 시스템은 **초안까지**만 만들고, 결정 · 근거 · 결정자 · 시각을 `docs/decision_log.md`에 남깁니다. PR 병합 버튼도 사람이 누릅니다. 승인 창은 읽고 한 건씩 `1 Yes` — `use auto mode` · 일괄 허용은 고르지 않습니다.

## 역할이 곧 파이프라인 단계 {#roles}

<figure markdown="span">
  ![가동 8단계를 두 줄 네 칸으로 그린 도식 — 단계마다 맡는 역할, AI가 하는 일, 다음 단계로 넘기는 파일, 맨 아래 사람 결정 4종이 decision_log로 모인다](../assets/diagrams/d6-roles-8steps.png){ loading=lazy }
  <figcaption>가동 8단계 — ⑤ 칸 끝의 <code>v0.5</code>는 11:45, 오른쪽 끝 <code>v1.0</code>은 15:50</figcaption>
</figure>

| 역할 | 맡는 단계 | 넘기는 것 | 시작 프롬프트 |
|---|---|---|---|
| ① 데이터 (R1) | 데이터 갱신 | `data/d6_{카드}_scored.csv` · `_open_inv.csv` · `change_log.csv` | [R1](../prompts/day6.md#r1) |
| ② 모델 · 등급 (R2) | 재등급 | `out/{카드}/grade_changes.csv` | [R2](../prompts/day6.md#r2) |
| ③ 한도 · 시나리오 · ROI (R3) | 한도 · EL · 경보 · ROI | `limits_diff.csv` · `el_table.md` · `alerts.csv` · `roi/roi_kpi.xlsx` | [R3](../prompts/day6.md#r3) |
| ④ 규정 · 근거 · 거버넌스 (R4) | 규정 근거 · 검증 | `docs/evidence.md` · `sop/ai_usage_rules.md` | [R4](../prompts/day6.md#r4) |
| ⑤ SOP · 커뮤니케이션 · 발표 (R5) | SOP 초안 · 데모 | `sop/SOP_{카드}.md` · 메일 초안(DRY RUN) · `docs/demo_script.md` | [R5](../prompts/day6.md#r5) |
| 저장소 관리자 | 전 과정 | 입력 파일 · 이슈 · README · `v0.5` · `v1.0` | [RA](../prompts/day6.md#ra) |

4인 팀은 R1 · R2를 한 사람이 맡고 작업대(worktree) 두 개로 나눠 일합니다. 저장소 관리자는 어제 조장입니다.

## 체크포인트 — 커밋으로 확인합니다 {#checkpoints}

| CP | 시각 | 저장소에서 보는 것 | 못 했으면 |
|---|---|---|---|
| **CP1** | 10:40 | `docs/architecture.md`(설계도 + 변수표) · 역할 이슈 5개 · README 제목 · `CLAUDE.md` 팀 규칙 3줄 | 10:50 휴식에 강사와 5분 설계 점검 |
| **CP2** | 11:45 | 스탠드업 3분 · 태그 `v0.5` · `data/` 3종 · 등급 변동표 · 한도안 · EL 2열 · 인젝트 1 한 줄 | 점심 우선순위 카드의 '최소 완료 경로' |
| **CP3** | 14:50 | SOP 0–6장 · ROI 3안(보수안 먼저) · `decision_log`의 인젝트 2 결정 · 검증 커밋 | 15:10 스프린트를 SOP · ROI에만 |
| **CP4** | 15:40 → 15:50 | README 5항목 · 폴더 6개 · 보안 3검색 · `v1.0` + 릴리스 노트 → 링크 | zip `d6_team_solution__T{조}.zip` + README |

체크포인트는 말이 아니라 **저장소의 커밋과 태그**로 확인합니다.

## 쓰는 도구 {#tools}

| 도구 | 어디서 | 오늘 쓰는 곳 |
|---|---|---|
| **Claude Code**(VS Code 확장) | 팀 저장소를 연 VS Code | 역할마다 세션 하나 — 첫 프롬프트는 **Plan**, 계획 승인은 마우스로 `2 Yes, and manually approve edits`, 허락 창은 읽고 `1 Yes` |
| **Git · GitHub** | VS Code 소스 제어 · github.com | 이슈 → 브랜치(겸임자는 worktree) → PR → 태그 · 릴리스 · 보안 3검색 |
| **ChatGPT · Claude** | 브라우저 새 대화 | 카드 해석 변수표 · **초안과 다른 모델로 SOP 검증** · 가장 약한 가정 · 기획서 · Claude Code를 못 쓸 때의 [채팅 경로](lab-a.md#chat-path) |
| **엑셀** | 내 PC · 웹용 Excel | 우리 카드 ROI 완성본 읽기 · 나만의 KPI |

!!! note "Claude Code는 유료 구독이 필요합니다"

    Pro 이상 구독이나 API 계정으로 로그인합니다(무료 플랜은 쓸 수 없습니다). 설치가 막힌 PC는 **채팅 경로**로 같은 실습을 하고 README 3번에 쓴 경로를 적으면 감점이 없습니다 → [실습 A 채팅 경로](lab-a.md#chat-path) · [실습 B 채팅 경로](lab-b.md#chat-path). 새 폴더(worktree)에는 `.venv`가 없으니 `uv sync`부터 합니다.

## 파일 받기 {#files}

**팀 저장소에서는 명령 하나** — 저장소 관리자가 09:28 뒤 `uv run python tools/get_day_files.py 6`을 실행하면 카드 · 데이터 팩 · 팀 팩 · ROI 완성본과 4일차 입력 · 환율 파일이 같은 경로로 들어옵니다. 11:15 · 11:30 · 13:15에 같은 명령을 다시 실행하면 새로 열린 파일만 더 받습니다. 아래 카드에 잠금 표시가 있는 파일은 그 시각에 저절로 열립니다(사이트에는 1–3분 뒤 링크가 생깁니다). 양식과 슬라이드 PDF(사전판)는 지금 받을 수 있습니다.

--8<-- "docs/_snippets/day6/files_all_cards.md"

- 받은 폴더(`data/checkpoints/` · `labs/`)는 팀 저장소에서 커밋되지 않습니다. **우리 카드는 `cards/`로, 우리 팀 팩 · 4일차 입력 · 환율 파일은 `data/input/`으로** 복사해 커밋합니다 — 프롬프트 [RA](../prompts/day6.md#ra)가 해 줍니다. 다른 팀 파일은 옮기지 않습니다.
- 규정 `rules/hanbit_credit_policy.md`는 킷에 들어 있습니다. K-SURE 약관은 **재배포 금지**라 각자 공식 링크에서 받아 `local/`에 두고 커밋하지 않습니다.

## 데이터와 이용 조건 {#data}

- 오늘 데이터는 모두 **(가상) 한빛정밀(주)의 합성 데이터**이거나 **공개 데이터**입니다. 카드의 상황과 숫자는 교육용 가정이고, 카드 뒷면의 '실제 앵커'만 실제로 있었던 일입니다(실존 피해 기업의 이름은 쓰지 않습니다). 투자 · 여신 · 보험 판단 자료가 아닙니다.
- 합성 데이터와 문서는 CC BY 4.0, 코드는 MIT입니다. 환율은 미국 연준 H.10(FRED 제공)이며 인용 방법은 저장소의 `data/external/ATTRIBUTION.md`에 있습니다.
- 오늘 파일은 합성 데이터라 ChatGPT · Claude에 올려도 됩니다. **회사 실데이터 · 개인정보는 어떤 AI 도구에도 넣지 않습니다 — 익명화본도.** AI 서비스의 학습 설정은 끄고 시작합니다([사전 준비](../setup.md#ai-training)).
- 개인 기획서 · 개인 KPI · ROI의 자사판은 [익명화 체크리스트](../setup.md#byod)를 통과한 값만 쓰고 **비공개 폼으로만** 냅니다.

## 오늘의 결과물과 제출 {#submit}

<div class="tf-checklist" data-title="오늘 남길 것" markdown>

- [ ] **팀 솔루션 킷 `v1.0`** — README 5항목 · 폴더 6개 · 보안 3검색 · 릴리스 노트 · 새 폴더에서 같은 숫자
- [ ] 카드를 반영한 결과 — `data/` 3종 · `out/{카드}/`(등급 · 한도 · EL · 경보)
- [ ] 근거와 결정 — `docs/evidence.md`(조치마다 인용 2개) · `docs/decision_log.md`(인젝트 2개 반영)
- [ ] SOP · 규칙서 — `sop/SOP_{카드}.md` · `sop/ai_usage_rules.md`(메일 발송 0건 · '15/1000' 일반화 0건)
- [ ] ROI · KPI — 팀 `roi/roi_kpi.xlsx`(보수안 먼저) · 개인 `d6_roi__T{조}-{번호}.xlsx`
- [ ] 15:50 팀 링크는 <span data-tf-link="team_form">팀 제출 폼</span>, 17:50 개인 기획서는 <span data-tf-link="plan_form">개인 제출 비공개 폼</span>

</div>

제출 절차는 [제출](submit.md), 채점 앵커는 [심사 기준](judging.md)에 있습니다.

## 흔한 막힘과 해결 {#troubleshooting}

??? fix "Claude Code에 'use auto mode'가 미리 골라져 있어요"

    Enter만 치면 그 선택이 눌립니다 — **마우스로** `2 Yes, and manually approve edits`를 고릅니다. 모드 표시기가 Auto로 시작했다면 Plan으로 바꿉니다.

??? fix "처음 여는 폴더에서 허용 규칙이 안 먹어요"

    Workspace Trust 창에서 **'신뢰'**를 눌러야 팀 설정이 적용됩니다.

??? fix "바꾼 행 수가 buyer_changes와 달라요"

    팀 팩 `card` 시트의 `n_buyers` · `applied` ✔ 수 · `change_log` 행 수를 대조합니다. 20분 넘게 막히면 강사 정답본으로 합류합니다(감점 없음).

??? fix "한도(LP)가 안 풀려요"

    PuLP는 3.3.2. 엔진이 없으면 `labs/day4/MODEL_SPEC.md`에서 다시 만들거나 등급 상한 규칙으로 근사하고 README에 쓴 경로를 적습니다.

??? fix "SOP에 근거 없는 조항 · 숫자가 들어갔어요"

    [P6-2](../prompts/day6.md#p6-2)를 **초안과 다른 모델**로 돌리고, ④가 근거표와 한 줄씩 대조합니다. '15/1000'은 약관 제21조③의 한정 조항입니다 — 일반 규칙으로 쓰지 않습니다.

??? fix "보안 검색에 줄이 걸려요 · 키를 커밋했어요"

    실제 키 · 실제 이메일은 0건이어야 합니다. 설명 글 · 예시 이름 · 가상 주소에 걸린 줄은 이유 한 줄. 키가 커밋됐다면 지워도 이력에 남습니다 — 폐기 · 재발급 뒤 강사에게 알리고, `force push`는 하지 않습니다.

??? fix "재현 숫자가 달라요"

    새 폴더에서 `uv sync`부터 다시 돌려 README에서 빠진 줄을 찾습니다 — 결과 폴더를 지우고 다시 만들어 비교합니다.

## 오늘 쓰는 프롬프트 {#prompts}

| 단계 | 프롬프트 |
|---|---|
| 실습 A Step 1–4 | [RA](../prompts/day6.md#ra) · [S1](../prompts/day6.md#s1) · [S2](../prompts/day6.md#s2) · [R1](../prompts/day6.md#r1) · [R2](../prompts/day6.md#r2) · [R3](../prompts/day6.md#r3) · [I1](../prompts/day6.md#i1) · [R3b](../prompts/day6.md#r3b) · [R4](../prompts/day6.md#r4) · [I2](../prompts/day6.md#i2) · [R5](../prompts/day6.md#r5) · [P6-1](../prompts/day6.md#p6-1) · [P6-2](../prompts/day6.md#p6-2) · [P6-5](../prompts/day6.md#p6-5) |
| 실습 B Step 5–8 | [S5](../prompts/day6.md#s5) · [S5b](../prompts/day6.md#s5b) · [P6-6](../prompts/day6.md#p6-6) · [P6-8](../prompts/day6.md#p6-8) · [P6-9](../prompts/day6.md#p6-9) · [P6-3](../prompts/day6.md#p6-3) · [P6-4](../prompts/day6.md#p6-4) · [P6-7](../prompts/day6.md#p6-7) · [S8](../prompts/day6.md#s8) |
| 막힐 때 | [채팅 경로](../prompts/day6.md#chat-path) · [시연 1 틀](../prompts/day6.md#frame) |

## 6일을 마치며 — 다섯 문장 {#wrapup}

"나는 할 수 있다"로 읽어 보세요 — ① 카드의 변수를 데이터에 반영해 도구를 순서대로 돌린다 ② AI가 쓴 SOP에서 근거 없는 곳을 찾는다 ③ ROI를 보수안부터 계산한다 ④ 다른 사람이 다시 돌릴 수 있게 남긴다 ⑤ KPI를 기준선과 함께 세운다. 아직 '아니오'인 문장이 있다면 그것이 **30일 계획의 첫 항목**입니다. 과정에서 쓴 계정과 키는 안내된 날짜에 만료되니 계속 쓰려면 본인 계정으로 옮기고, 실데이터는 회사 규칙 안에서만 다룹니다.
