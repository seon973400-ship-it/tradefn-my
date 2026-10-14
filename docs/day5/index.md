---
title: 5일차 — AI 금융 에이전트 및 채권 관리 종합 제어 대시보드 구축
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">5일차 · 10/20(화) · 09:00–17:50 · 웹 · API · 실시간 연동 · DB · RAG · 에이전트 <span class="tf-daystate" data-tf-daystate="5"></span></span>

# AI 금융 에이전트 및 채권 관리 종합 제어 대시보드 구축

**웹 · API · DB로 화면을 만들고, RAG와 에이전트로 일을 맡긴다.** 어제까지 만든 등급 · 한도 · 경보를 사람이 매일 아침 여는 화면과 반복 업무를 맡는 AI 일손으로 바꿉니다. 오전에는 시연 네 건, 오후에는 그 시연을 작게 · 조금 다르게 내 저장소에서, 저녁에는 에이전트와 시연 5.

<div class="tf-buttons" markdown>
[실습 A · 13:00](lab-a.md){ .md-button .md-button--primary }
[실습 B · 15:00](lab-b.md){ .md-button .md-button--primary }
[이론 요약](theory.md){ .md-button }
[프롬프트](../prompts/day5.md){ .md-button }
[파일 받기](#files){ .md-button }
</div>
</div>

## 오늘의 목표 {#goals}

<div class="grid cards tf-cols-3" markdown>

-   :material-numeric-1-circle-outline:{ .lg .middle } **실시간 환율을 반영한 채권 상황판을 만들어 내 주소로 배포한다**

    웹 · API · 실시간 연동 · DB가 어떻게 이어지는지 알고, 요구사항 → Claude Code → 검증 → PR → 배포 순서로 — [실습 B](lab-b.md)

-   :material-numeric-2-circle-outline:{ .lg .middle } **근거를 인용하고 모르면 기권하는 규정 챗봇을 만들고 숫자로 잰다**

    골든셋 20문항으로 검색 정확도(F1@K)를 재서 Top-K를 고른다 — [실습 A](lab-a.md)

-   :material-numeric-3-circle-outline:{ .lg .middle } **독촉 업무를 워크플로와 에이전트로 설계한다**

    되돌릴 수 없는 행동 앞에는 사람 승인 · 가드레일 · 기록을 둔다 — [실습 B4](lab-b.md#b4) 워크플로와 8교시 시연 5 에이전트

</div>

"기억에만 맡기지 않고 **근거를 찾아 붙이고**, 맡기되 **되돌릴 수 없는 일은 사람이 누른다**"가 오늘의 기준입니다. 오늘 쓰는 독촉 메일은 모두 초안이라 **실제로 나가는 메일은 0통**입니다. 하루 끝(17:36)에 이 세 문장으로 자가 점검을 합니다.

어제까지의 결과가 오늘의 입력입니다 — 앱의 ⓪ 통합 상황판이 읽는 `d5_start.csv`는 1–4일차의 등급 · 한도 · 경보 규칙이 반영된 **2026-09-30 기준 미결 인보이스 300건**(바이어 91곳)입니다. 내 결과 파일과 상관없이 모두 같은 기준 파일로 시작하니 옆 사람과 숫자를 견주기 쉽습니다.

## 시간표 {#schedule}

<div class="tf-timeline" markdown>

1. <time>08:30</time> (자동) 시작 파일 `d5_start.csv`가 열립니다 — 내 저장소에서 `uv run python tools/get_day_files.py 5` · Claude Code 로그인과 모드 표시 점검
2. <time>09:00–09:50</time> **1교시** 시작하며 · 웹과 API(URL · HTTP · 상태 코드 · 프론트엔드와 백엔드 · API · JSON · 인증 · CORS) · 현장: 외화 채권 환산 — **시연 1** 실시간 환율로 미수금 다시 보기
3. <time>10:00–10:50</time> **2교시** 실시간 연동(폴링 · 캐시) · 웹앱 만들기와 배포(React · Next.js · TypeScript · Streamlit · 환경변수) — **시연 2** Next.js 대시보드
4. <time>11:00–11:50</time> **3교시** 데이터베이스(표와 키 · SQL · 트랜잭션) · 현장: 독촉 운영 · RAG(청킹 · BM25 · 인용 · 기권 · F1@K) — **시연 3** 채권 DB · **시연 4** 규정 PDF 챗봇
5. <time>11:50–13:00</time> 점심 — 내 저장소를 VS Code로 열고 `uv sync` · Claude Code 로그인을 미리 확인해 두세요
6. <time>13:00–14:50</time> **4–5교시** <span class="tf-chip tf-chip--must">실습 A</span> [규정 RAG 챗봇과 검색 평가](lab-a.md) — 13:50–14:00 쉬는 시간
7. <time>15:00–16:50</time> **6–7교시** <span class="tf-chip tf-chip--must">실습 B</span> [환율 타일 · 독촉 워크플로 · 배포 · 승인 기록 DB](lab-b.md) — 15:50–16:00 쉬는 시간
8. <time>17:00–17:50</time> **8교시** AI 에이전트(워크플로 대 에이전트 · 5패턴 · 사람 승인 · MCP · SDK · 가드레일) · 운영 — **시연 5** 독촉 에이전트 · [내일의 작업대(팀 저장소)](lab-b.md#period8) · 정리
9. <time>21:00</time> 개인 AI 도입 기획서 초안 1–6장 → <span data-tf-link="plan_form" data-tf-empty="기획서 비공개 폼(수업 중 화면 · 오픈채팅 공지로 받은 주소)">기획서 비공개 폼</span>

</div>

쉬는 시간은 09:50 · 10:50 · 13:50 · 14:50 · 15:50 · 16:50(각 10분)입니다. 슬라이드 PDF(발표자 노트 제외)는 [이론 요약](theory.md) 맨 위와 아래 '파일 받기'에 있습니다.

## 시연 다섯 건 {#demos}

시연은 늘 **문제 상황 → 입력 → 결과** 순서로 봅니다. 오후 실습은 오전 시연 네 건을 작게, 조금 다르게 내 손으로 해 보는 것이고, 시연 5는 저녁 8교시에 오후의 워크플로와 견줍니다.

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">시연 1 · 09:32 · Claude Code</span>

    **실시간 환율로 미수금 다시 보기**

    9/30 환율에 묶인 미결 300건(4개 통화) → 환율 API(9/30 · 오늘) → 바이어별 원화표 · 요약(받은 시각 · 제공처 포함)

    <small>오후: 실습 B3 — 같은 API를 앱 안의 타일 하나로</small>

-   <span class="tf-eyebrow">시연 2 · 10:23 · Claude Code(Plan)</span>

    **환율 반영 바이어 리스크 대시보드**

    요구사항 1쪽 + 와이어프레임 + CSV 3개 + 환율 API → Next.js 대시보드 · 커밋 · PR 설명

    <small>오후: 실습 B2 · B3 · B5 — 요구사항 카드 먼저, 계획 승인, 검증, PR</small>

-   <span class="tf-eyebrow">시연 3 · 11:08 · Claude Code</span>

    **흩어진 채권 파일을 하나의 DB로**

    CSV · Parquet · JSON 네 파일 → `receivables.db` · ERD · 등급별 연령분석 · 롤백

    <small>오후: 실습 B7 — 승인 1건 = 두 표를 한 트랜잭션으로</small>

-   <span class="tf-eyebrow">시연 4 · 11:33 · 프로젝트 + Claude Code</span>

    **규정 PDF 챗봇 — 인용 · 기권 · 평가**

    가상 규정 PDF(35조) + 골든셋 20문항 → 인용 답 · 기권 답 · 조각 40개 · F1@K 막대

    <small>오후: 실습 A 전체 — 줄인 단계 + 개선 실험 하나</small>

-   <span class="tf-eyebrow">시연 5 · 17:19 · Claude Code</span>

    **독촉 에이전트 — 도구 · 승인 · 추적**

    채권 DB + 규정 검색기 + 템플릿 + 바이어 메모 3건 → 영문 초안 · 감사로그 · 실행 추적

    <small>8교시: 실습 B4의 워크플로와 견준다</small>

</div>

## 오후 실습 지도 {#map}

<div class="grid cards tf-cols-3" markdown>

-   <span class="tf-eyebrow">실습 A · 13:00–14:50</span>

    **[규정 RAG 챗봇과 검색 평가](lab-a.md)**

    A1 준비 → A2 기준선 → A3 청킹 → A4 검색기 → A5 평가 → A6 K 고르기 → A7 개선 실험 → A8 PR

    <small>만드는 것: `baseline.md` · `chunks.jsonl` · `scripts/rag_lab/` · `rag_eval.csv` · `f1_at_k.png` · `rag_report.md` · PR 1개</small>

-   <span class="tf-eyebrow">실습 B · 15:00–16:50</span>

    **[환율 상황판 · 독촉 워크플로 · 배포 · 승인 기록 DB](lab-b.md)**

    B1 앱 한 바퀴 → B2 요구사항 카드 → B3 환율 타일 → B4 독촉 워크플로 → B5 커밋·PR·병합 → B6 배포 → B7 승인 기록을 SQLite에 → B8 점검

    <small>만드는 것: 환율 타일 · 톤 규칙 · 감사로그 2행 · 내 앱 주소 · `receivables.db` · `links.md` · PR 2개</small>

-   <span class="tf-eyebrow">8교시 · 17:31–17:36</span>

    **[내일의 작업대 — 팀 저장소](lab-b.md#period8)**

    조장이 [킷 템플릿](https://github.com/brainini/tradefin-kit-template)으로 `tradefin-kit-T{조}`를 만들고 팀원 · 강사를 초대 → 팀원은 오늘 밤 수락 · README 한 줄 PR

    <small>만드는 것: 팀 저장소 주소 · 팀원 PR 1건씩(내일 09:00 전)</small>

</div>

**점검 시각 한눈에** — 실습 A: 13:25 기준선 · 13:50 검색기 · 14:30 평가표 · 14:45 개선 실험 · 14:50 PR / 실습 B: 15:13 앱 한 바퀴 · 15:35 환율 타일 · 15:50 독촉 워크플로 · 16:22 배포 · 16:45 DB · 제출. 막히면 ① 그 AI에게 오류 전문 ② 짝 ③ 손들기, **20분 넘게 막히면 강사 완성본**(막힌 단계의 파일만)으로 합류합니다. **실습 B는 실습 A의 결과를 쓰지 않으므로** A를 못 끝내도 B는 15:00에 새로 시작합니다.

## 쓰는 도구 {#tools}

| 도구 | 어디서 | 오늘 쓰는 곳 |
|---|---|---|
| **Claude Code** (VS Code 확장) | 내 PC의 VS Code | 실습 A3–A8 · B3–B8 — 큰 작업의 첫 프롬프트는 **Plan**, 계획 승인 창에서 `2 Yes, and manually approve edits`, 명령은 허락 창을 읽고 승인 |
| **Claude** · **ChatGPT** (웹) | 브라우저 — **프로젝트** 기능 | 실습 A2 기준선(규정 PDF + 지침 칸) · Claude Code를 못 쓸 때의 채팅 경로 |
| **Git · GitHub** | VS Code 터미널 · github.com | 브랜치 `d5-rag` · `d5-dashboard` · `d5-store` · PR(커밋 · push까지 Claude Code) · **병합은 내가** · 배포용 `git add -f` · 팀 저장소 |
| **uv · Python** | VS Code 터미널 | `uv sync --group dash` · `uv run streamlit run app/streamlit_app.py` · `uv run pytest app/tests -q` |
| **Streamlit Community Cloud** | share.streamlit.io(GitHub 로그인) | 실습 B6 — 내 앱을 내 주소로. 12시간 접속이 없으면 잠듭니다 |

Claude Code는 Pro 이상 구독이나 API(Console) 계정으로 로그인합니다(무료 플랜은 쓸 수 없습니다). 설치가 막힌 PC는 내 저장소의 **Codespaces**를, 계정이 없으면 **채팅 경로**로 같은 실습을 합니다 → [실습 A 채팅 경로](lab-a.md#chat-path) · [실습 B 채팅 경로](lab-b.md#chat-path). 오늘 새로 필요한 패키지는 실습 A의 `pypdf` · `rank-bm25`뿐이고(Claude Code가 `uv add`를 먼저 물으면 승인), 대시보드 패키지는 `uv sync --group dash`로 받습니다 — 그룹 없이 `uv sync`만 다시 하면 streamlit이 지워집니다.

## 파일 받기 {#files}

**내 저장소에서 명령 하나**면 됩니다. 규정 PDF · 골든셋 · 질문 목록 · 평가 시트 · 요구사항 카드 · 톤 표 · 양식은 **이미 내 저장소에 있고**, 명령이 기본 원장 `d5_start.csv` · 앞선 날의 결과(`d3_*` · `d4_*` · `models/`) · 완성본(채점 카드 · 검산표 · 칸 영향표)을 같은 경로로 받습니다. 고쳐 쓸 파일은 `workbench/day5/data/`에 **작업 사본**도 만들어 줍니다.

```bash
uv run python tools/get_day_files.py 5
```

- 카드에 잠금 표시가 있는 파일은 그 시각 뒤에 받습니다 — `d5_start.csv`와 칸 영향표는 **10/20(화) 08:30**. 그 전에는 명령도 `[열기 전]`으로 알려 주고, 시각이 지난 뒤 같은 명령을 다시 실행하면 새로 열린 파일만 더 받습니다.
- **원본(`data/` · `labs/` · `rag/`)은 고치지 않습니다.** 요구사항 카드 · 톤 표는 `workbench/day5/data/`의 작업 사본에서, 코드는 `scripts/`와 `app/`에, 결과는 `workbench/day5/outputs/`에 둡니다.
- 저장소 없이 채팅 경로로 하는 분은 아래 카드에서 받습니다 — 맨 위 **`day5_files.zip`**을 받아 압축을 풀면 `D5` 폴더 하나에 지금 열린 파일이 들어 있습니다. 규정 PDF(`hanbit_credit_policy.pdf`)는 압축 파일 안 `rag/corpus/` 폴더에 있습니다 — 실습 A2에서 채팅 프로젝트에 올리는 파일입니다(카드에서 따로 받아도 됩니다).

--8<-- "docs/_snippets/day5/files_all_cards.md"

## 데이터와 이용 조건 {#data}

- 오늘 쓰는 데이터는 모두 **(가상) 한빛정밀(주)의 합성 데이터**이거나 공개 데이터입니다. 한빛정밀(주)과 바이어 · 인보이스 · 등급 · 한도 · 가상 규정(`rag/corpus/hanbit_credit_policy.pdf` · `.md`)은 교육용 가상이며 실존 기업 · 기관과 무관하고, 숫자는 실제 거래 기록이 아닙니다. 투자 · 여신 · 보험 판단 자료가 아닙니다.
- 합성 데이터와 문서는 CC BY 4.0, 코드는 MIT입니다. 저장소의 환율 파일(`fx_krw_daily.csv`)은 미국 연준 H.10 환율(FRED 제공, Public Domain: Citation Requested)이고 인용 방법은 저장소의 `data/external/ATTRIBUTION.md`에 있습니다.
- 시연 1과 실습 B3의 **실시간 환율**은 키 없이 쓰는 공개 환율 서비스(`api.frankfurter.dev`)를 부릅니다. 응답 원문을 저장한 파일은 커밋하지 않고, 화면에는 **환율 날짜 · 받은 시각 · 제공처**를 함께 적습니다. 환율 숫자는 거래용이 아닙니다.
- 보험 약관 본문은 이 저장소에 없습니다(재배포하지 않습니다). 실습 A7 ④(심화)에서 쓰려면 [rag/corpus/README.md](https://github.com/brainini/tradefin-ai-2026/blob/main/rag/corpus/README.md)의 공식 링크에서 각자 받아 파일 이름에 `약관`을 넣어 `rag/corpus/`에 둡니다 — 커밋에서 자동으로 빠집니다.
- 열 하나하나의 뜻은 [데이터 → 시작 파일의 주요 열](../data.md#checkpoint-columns)에 있습니다.
- **오늘 파일은 합성 데이터라 ChatGPT · Claude에 올리거나 붙여 넣어도 됩니다.** 단 **회사 실데이터 · 개인정보는 어떤 AI 도구에도 넣지 않습니다 — 익명화본도.** AI 서비스의 '모델 개선(학습)' 설정은 끄고 시작하고([사전 준비 — AI 학습 설정 끄기](../setup.md#ai-training)), 내 저장소는 공개이므로 **키 · 비밀번호 · 회사 자료는 커밋하지 않습니다.** 배포하는 앱의 비밀값은 Streamlit **Secrets** 칸에만 두고, 오늘은 비워 두면 모의 모드로 끝까지 돕니다.
- 앱의 독촉 메일 예제의 회사 · 주소는 모두 가상(`buyer+B017@example.com` 꼴)이고, 실제로 나가는 메일은 0통입니다 — 초안과 승인 기록만 남깁니다.

## 오늘의 결과물과 제출 {#submit}

<div class="tf-checklist" data-title="오늘 남길 것" markdown>

- [ ] **PR① 실습 A**(`d5-rag`) — `baseline.md` · `scripts/rag_lab/` · `rag_eval.csv` · `f1_at_k.png` · `rag_report.md`
- [ ] **PR② 실습 B**(`d5-dashboard`) — 환율 타일 · 톤 표를 읽는 라우팅 · 테스트, **병합은 내가**
- [ ] **PR③ 실습 B**(`d5-store`) — 승인 기록 SQLite(`receivables.db`는 커밋 제외), **병합은 내가**
- [ ] **내 앱 주소** — ⓪이 내 PC와 같은 화면 · 저장소에 키 0
- [ ] **`links.md`** — 앱 주소 · PR 3개 · 점검 네 칸
- [ ] **제출** — PR 링크와 앱 주소를 <span data-tf-link="submit_form" data-tf-empty="제출 폼(수업 중 화면 · 오픈채팅 공지로 받은 주소)">제출 폼</span>에
- [ ] **21:00 기획서 초안 1–6장** — 양식 `ax_proposal_template.md`를 Word · Google Docs로 옮겨 `plan_draft__T{조}-{번호}.docx`로 → <span data-tf-link="plan_form" data-tf-empty="기획서 비공개 폼(수업 중 화면 · 오픈채팅 공지로 받은 주소)">기획서 비공개 폼</span>. 저장소에 올리지 않고, 실명 · 회사 이름은 익명화합니다 — [6일차 기획서 11장](../day6/submit.md#proposal)
- [ ] **팀 저장소** — 조장은 `tradefin-kit-T{조}` 만들기 · 초대, 팀원은 오늘 밤 수락 + PR 1건

</div>

- 점검 기준은 '파일이 있다'가 아니라 **검증한 흔적**입니다 — 테스트 통과 · 숫자 대조 · 화면에서 Then 확인 같은 것들.
- PR 본문 · 커밋 메시지 · 보고서에 **회사 이름 · 실명 · 실제 숫자를 쓰지 않습니다.** 저장소가 공개입니다.
- 다 끝내지 못했어도 그대로 push하세요. 못 끝낸 단계는 내일 팀 저장소에서 이어 가도 됩니다.

## 함께하는 규칙 {#rules}

- **1:1 순회**: 강사가 실습 동안 한 분씩 2–3분 확인합니다. 막히면 손을 들거나 빨간 스티커를 올립니다.
- **짝과 서로 PR 리뷰**: 서로의 PR에 코멘트 하나씩 — 바뀐 파일 · 커밋 메시지의 '왜' · 실데이터 없음 · 키 없음 · 한 줄 코멘트.
- **숫자보다 절차**: AI가 고른 토큰 방식에 따라 F1@K의 끝자리, 받은 시각에 따라 환율 총액의 끝자리가 사람마다 다릅니다. **정의대로 계산했다면 정상**입니다 — 이상하면 [안 맞을 때](../prompts/day5.md#mismatch)부터.
- **요구사항을 먼저, 한 번에 하나**: 이미 도는 앱에 기능을 더할 때는 "기존 것은 바꾸지 말 것 · 새 패키지 금지 · 테스트 통과"를 매번 적습니다.
- **허락 창은 읽고 승인**: 무엇을 · 어디에 · 지우는지 세 가지를 읽고 `1 Yes`. 파일 삭제 · 강제 push · `git reset --hard`는 거절하고, **병합은 내가 GitHub 화면에서** 누릅니다.
- **키는 금고에**: Secrets에만 두고 저장소 · 채팅창 · 단체방에 붙이지 않습니다. 노출되면 폐기와 재발급이 먼저입니다.
- **현장 이야기**: "우리 회사에서는 이렇게 한다"는 이야기는 6일차 도입 기획의 재료가 됩니다 — <span data-tf-link="open_chat" data-tf-empty="오픈채팅(과정 안내 메시지(문자 · 메일)로 받은 주소)">오픈채팅</span>에도 남겨 주세요.

## 정리 · 자가 점검 · 내일 예고 {#tomorrow}

**오늘 정리 다섯 줄**

1. 웹 = 클라이언트 · 서버의 HTTP 요청 · 응답 · API = 프로그램용 창구 — 키는 서버에만.
2. 실시간은 원천의 갱신 주기가 정한다 — 폴링 + 캐시 + 기준 시각.
3. 대시보드 = 결정 질문 → 요구사항 → Plan 모드 → 검증 → PR → 배포.
4. 함께 쓰는 기록은 DB로, 규정 답은 근거로 — F1@K로 재서 K를 고른다.
5. 에이전트는 워크플로부터 — 되돌릴 수 없는 행동 앞엔 사람 승인 · 가드레일 · 로그.

**자가 점검**(17:36 — [오늘의 목표](#goals) 세 문장) — 수업에서는 문항마다 손가락으로 1점(전혀 못 한다)부터 4점(혼자 할 수 있다)까지 표시합니다.

<div class="tf-checklist" data-title="자가 점검" markdown>

- [ ] 나는 실시간 환율을 반영한 채권 상황판을 만들어 내 주소로 배포하고, 비밀값은 저장소 밖에 둘 수 있다
- [ ] 나는 근거를 인용하고 모르면 기권하는 규정 챗봇을 만들고 골든셋과 F1@K로 잴 수 있다
- [ ] 나는 독촉 업무를 워크플로와 에이전트로 설계하고, 되돌릴 수 없는 행동 앞에 사람 승인 · 가드레일 · 기록을 둘 수 있다

</div>

복습은 [용어집 → 5일차](../glossary.md#day5)의 퀴즈로 합니다.

**6일차 · 10/21(수)는 해커톤**입니다. 오늘 만든 규정 챗봇 · 상황판 · 승인 기록 DB · 에이전트의 사고방식이 위기 카드에 대응하는 팀의 도구가 됩니다. 팀 저장소는 오늘 8교시에 조장이 만든 `tradefin-kit-T{조}`에서 시작하니, 오늘 밤 팀원은 초대를 수락하고 README 팀원 표에 한 줄을 쓴 뒤 PR 1건을 올립니다 → [6일차](../day6/index.md) · [오늘의 8교시](lab-b.md#period8). 저녁에 앱 주소 · PR 링크 · `links.md`를 한 번 점검해 두세요.
