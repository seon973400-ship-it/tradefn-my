# 2일차 프롬프트 — 실습 A · 실습 B · 8교시

오후 실습에서 쓰는 프롬프트 전문입니다. A1–A4는 실습 A 프롬프트 장(d2-69)과 **글자가 같습니다**(줄 앞 번호만 뺐습니다). 실습 B 프롬프트 장(d2-72)에는 B1–B5의 한 줄 요약만 인쇄돼 있고, 전문은 여기 있습니다. B6은 8교시 실습 장(d2-74) 03단계의 문장 그대로입니다. 슬라이드에 없는 덧붙임 · 보조 프롬프트는 [보조 프롬프트](#support)에 모았습니다. 복사 버튼 :material-content-copy: 으로 통째로 복사하고, `{중괄호}` 자리만 내 상황에 맞게 바꿔 붙여 넣습니다(중괄호 기호도 지웁니다).

| 단계(인쇄 번호) | 프롬프트 |
|---|---|
| 실습 A 01 준비 | (선택) [a0 준비 맡기기](#a0) |
| 실습 A 02 진단 | [A1](#a1) → 저장 `a1-save` |
| 실습 A 03 규칙 | [A2](#a2) + 결정 줄 `a2-decide` → 규칙 먼저 커밋 `a2-commit` |
| 실습 A 04 스크립트 | [A3](#a3) + 결과 열 `a3-columns` |
| 실습 A 05 검증 | [A4](#a4) · [확인표 대조](#a-check) · [엑셀 검산본과 대조](#excel-compare) → 다르면 [어느 규칙에서 갈렸나](#mismatch) · 고치고 다시 `a-fix` · [A5](#a5) |
| 실습 A 06 기록 | [A6](#a6) · 짝 코멘트 [리뷰 코멘트 반영](#review-fix) |
| 실습 B 01 작업대 | [B1](#b1) |
| 실습 B 02 수집 점검 | [robots.txt 읽기](#robots) · [약관 읽기](#terms) · [5칸 초안](#terms-form) — Claude 웹 |
| 실습 B 03 채점 | [B2](#b2) · [B3](#b3) |
| 실습 B 04 평가 | [B4](#b4) |
| 실습 B 05 융합 | [B5](#b5) + 결과 열 `b5-columns` · 규칙 8칸 `b5-rule8` · 사전 `b5-dict` |
| 실습 B 06 기록 | [확인표 대조](#b-check) · [커밋 · PR](#b-commit) |
| 8교시 01–04 | [셀프 리뷰](#p8-review) · [리뷰 코멘트 반영](#review-fix) · [B6 충돌 풀기](#b6) |
| 막힐 때 | [어느 규칙에서 갈렸나](#mismatch) · [채팅 경로](#chat-path) · [더 해 보기](#more) |

!!! info "'2일차 작업 폴더' · 'outputs 폴더' · 'scripts 폴더'는 어디인가"

    프롬프트에 나오는 **2일차 작업 폴더**는 이 저장소에서 `workbench/day2/`입니다. `rules/`(규칙) · `prompts/`(프롬프트) · `data/`(받은 파일 사본 · 데이터 사전) · `outputs/`(결과) · `tests/`(테스트)가 그 안에 있습니다. 프롬프트의 **outputs 폴더**는 `workbench/day2/outputs/`이고, **scripts 폴더**는 저장소 맨 위의 `scripts/`입니다 — 저장소의 `CLAUDE.md`에 적혀 있어서 Claude Code가 먼저 읽습니다. 슬라이드 · 시연 화면의 `data/raw/` · `src/` · `reports/`는 시연 저장소의 이름입니다.

!!! tip "권한 모드는 일의 성격에 맞춰 바꿉니다"

    입력창 아래의 모드 표시기를 누르면 바뀝니다. **Manual**로 시작해서 → 진단할 때는 **Plan**(읽기만 · 고치지 못함) → 만들 때는 **Edit automatically**(파일 편집은 묻지 않음). Edit automatically에서도 **명령 실행은 허락 창이 뜹니다** — 읽고 `1 Yes`. `2 … for this project`처럼 허락 범위를 넓히는 선택은 쓰지 않습니다.

## 빈칸 값 {#values}

| 빈칸 | 값 | 쓰는 곳 |
|---|---|---|
| `{중위수 또는 KNN}` | **내가 고른** 결측 채우기 방식 — `중위수` 또는 `KNN` 한 단어(고른 이유는 규칙 문서 '왜' 칸에) | A2 |
| `{번호}` | 내 저장소에 만든 이슈 번호(숫자만, 예: `1`) | A6 |
| `{사이트 이름}` | 실습 B 02에서 고른 뉴스 사이트 이름(짝과 다른 곳) | robots.txt · 약관 읽기 |
| `{항목}` · `{기대값}` · `{내 값}` | 확인표에서 어긋난 줄 | 어느 규칙에서 갈렸나 |
| `{리뷰 코멘트 붙여넣기}` | 짝이 내 PR에 단 코멘트 글(GitHub에서 복사) | 리뷰 코멘트 반영 |

## 프롬프트를 쓰는 습관 {#habits}

1. **진단과 수정을 나눈다** — Plan 모드로 진단만 시키고, 무엇을 어떻게 고칠지는 **사람이 정해** 규칙 문서에 먼저 씁니다. 그다음에 스크립트로 옮기게 합니다.
2. **한 번에 하나** — 네 개를 한꺼번에 붙여 넣으면 어디서 틀렸는지 찾을 수 없습니다. 결과를 읽은 뒤 다음으로 갑니다.
3. **숫자는 코드가, 대조는 다른 길로** — 계산은 스크립트가 하고, 확인은 확인표 · 엑셀 검산본(수식) · 테스트처럼 **코드가 아닌 다른 길**과 나란히 놓습니다.
4. **틀리면 바로 고치게 하지 않는다** — "어느 규칙에서 갈렸나"를 먼저 묻습니다([안 맞을 때](#mismatch)). 테스트와 규칙 중 어느 쪽이 틀렸는지 판단하는 것이 사람의 몫입니다.
5. **허락 창은 읽고 승인한다** — 무엇을 · 어디에 · 지우는지 세 가지를 읽고 `1 Yes`. 파일 삭제 · 강제 push · `git reset --hard`는 거절합니다.
6. **잘 된 프롬프트는 저장한다** — `workbench/day2/prompts/`에 이름 + 판 번호로 두고, 고칠 때마다 커밋합니다(오늘의 `news_score_v1.md`처럼).

---

## A1 · 진단 — 고치지 않고 표로 {#a1}

**도구** Claude Code · **Plan 모드** · **실습 A 02 진단** · 결과 화면의 진단 표(저장은 아래 `a1-save`)

<!-- --8<-- [start:a1] -->
```text
[Plan 모드] data/checkpoints/d2_start.xlsx의 buyers 시트를 진단만 해 줘. 열별 타입·결측·표기 종류·의심 값을 표로. 고치지 마.
```
<!-- --8<-- [end:a1] -->

맨 앞 `[Plan 모드]`는 "이 프롬프트는 Plan 모드로 보낸다"는 표시입니다. 모드를 먼저 바꾸고 보내면 지워도 됩니다.

**어떻게 생겼나** 시연 2의 첫 프롬프트를 buyers 시트 하나로 줄인 것입니다. **"진단만 해 줘 · 고치지 마"**가 핵심입니다 — 진단과 수정을 한 번에 시키면 무엇을 왜 고쳤는지 검토할 기회가 사라집니다.

**끝난 뒤** 계획 승인 창이 뜨면 **`3 No, keep planning`**을 고릅니다(승인하면 AI가 바로 고치기 시작합니다). 그다음 모드를 **Edit automatically**로 바꾸고 표를 파일로 저장합니다(`a1-save`).

<!-- --8<-- [start:a1-save] -->
```text
방금 진단 표를 2일차 작업 폴더의 outputs/profile.md로 저장해 줘.
```
<!-- --8<-- [end:a1-save] -->

**확인할 것** 통화 표기 종류, 숫자 칸에 섞인 글자, 재무 항목 결측, 자기자본 0 이하, 신용한도에 비해 큰 잔액이 표에 보이는지 봅니다. AI가 **'사람이 정해야 한다'고 짚은 곳**이 곧 A2에서 내가 정할 규칙입니다.

---

## A2 · 규칙 문서 — 사람이 정한 규칙을 넘긴다 {#a2}

**도구** Claude Code · **Edit automatically** · **실습 A 03 규칙** · 결과 `workbench/day2/rules/정제규칙.md` 1–7칸

<!-- --8<-- [start:a2] -->
```text
진단 결과로 2일차 작업 폴더의 rules/정제규칙.md 1–7칸을 '규칙/왜' 두 줄씩 채워 줘. 결측은 {중위수 또는 KNN} + 결측 플래그.
```
<!-- --8<-- [end:a2] -->

`{중위수 또는 KNN}`은 **내가 고른 방식**으로 바꿉니다([빈칸 값](#values)). 짝과 다른 방식을 골라 결과를 비교해도 좋습니다.

**`a2-decide` · 덧붙임 — 확인표를 맞추려면(권장)** 위 프롬프트 끝에 이어 붙입니다. 확인표의 숫자(결측 플래그 47곳 · 대체값 1.4218 · 1.4579 · 66.44 · 0.0654 · 단위 의심 · 자본잠식)가 아래 정의를 전제로 하기 때문입니다. 특히 **무엇을 채우는지**(재무 원값이 아니라 비율 열)를 빼면 AI가 유동자산 · 매출 같은 원값을 먼저 채우고 비율을 계산해 대체값이 1.52 · 1.51 · 60 · 0.05 근처로 달라집니다(과정 준비 때 미리 해 본 실행에서 실제로 그랬습니다). 다르게 정하고 싶다면 정한 대로 쓰되, 확인표와 달라지는 곳이 생길 수 있습니다.

<!-- --8<-- [start:a2-decide] -->
```text
결정: 결측 플래그 fin_missing은 유동자산·유동부채·총부채·자기자본·매출 중 하나라도 빈칸이면 1 · 결측 채우기는 재무 원값이 아니라 비율 열(current_ratio·debt_to_equity·dso_buyer·op_margin)에 한다 — 비율을 먼저 계산하고 그 열의 빈칸을 채운다(중위수라면 대체 전 150행의 그 열 중위수, 자본잠식 빈칸은 그대로) · 잔액이 신용한도의 10배를 넘으면 unit_flag=1 후 ÷1,000 · 자기자본이 0 이하면 부채비율은 빈칸 + neg_equity=1 · 국가위험 '-'는 country_risk=0 + crc_unclassified=1 · 환율은 기준일 2026-08-31 값으로 USD 환산(엔화는 100엔 단위) · 환율 변화 열 fx_chg_30d는 시트 fx_at_ref의 chg_30d, fx_chg_30d_lag30은 fx_krw_daily.csv로 '30일 전 환율 ÷ 60일 전 환율 − 1'.
```
<!-- --8<-- [end:a2-decide] -->

**`a2-commit` · 이어서 — 규칙 문서만 먼저 커밋** diff를 읽은 뒤 보냅니다. A4가 마지막에 커밋하므로, 규칙을 먼저 커밋해 두어야 이 브랜치의 커밋이 '규칙 → 결과'로 나뉩니다(06 기록의 '커밋 2개+').

<!-- --8<-- [start:a2-commit] -->
```text
workbench/day2/rules/정제규칙.md만 커밋해 줘(다른 파일은 넣지 마). 메시지는 첫 줄 '2일차: 바이어 정제 규칙 1–7칸 작성', 한 줄 비우고 '왜: 고치는 이유를 규칙 문서에 먼저 남기려고'. push는 아직 하지 마.
```
<!-- --8<-- [end:a2-commit] -->

**확인할 것**

- 1–7칸마다 `규칙:`과 `왜:`가 **둘 다** 채워졌는지, 3칸에 결측 플래그의 정의가 있는지 봅니다.
- 소스 제어 화면에서 diff를 봅니다 — **규칙 문서만** 바뀌고 `data/`의 원본은 그대로여야 합니다.
- AI가 규칙을 되묻는 질문(예: "JPY 잔액을 한도와 어떻게 비교할까요?")은 **사람이 정할 결정**입니다. 짝과 의논해 답합니다.

---

## A3 · 정제 스크립트 — 규칙대로, 원본은 읽기만 {#a3}

**도구** Claude Code · **Edit automatically** · **실습 A 04 스크립트** · 결과 `scripts/clean_buyers.py` · `workbench/day2/outputs/d2_buyers_clean.csv` · `workbench/day2/outputs/dq_report.md`

<!-- --8<-- [start:a3] -->
```text
규칙대로 scripts/clean_buyers.py를 만들고 uv run으로 실행해. 원본은 읽기만, 결과는 outputs/d2_buyers_clean.csv, 전·후 비교는 outputs/dq_report.md.
```
<!-- --8<-- [end:a3] -->

**`a3-columns` · 덧붙임 — 3일차 입력으로 쓰려면(권장)** 정제 결과 표에 아래 25열이 있어야 오후 실습 B와 내일 3일차가 이어집니다. 열 이름은 이대로 맞춥니다.

<!-- --8<-- [start:a3-columns] -->
```text
결과 열: buyer_id · payment_method · ccy_clean · amt_num · ar_balance_usd · pct_current · pct_ar_31p · pct_91plus · max_dpd · avg_days_late · late_ratio · dpd_trend · dispute_ratio · current_ratio · debt_to_equity · dso_buyer · op_margin · fin_missing · neg_equity · country_risk · crc_unclassified · unit_flag · fx_chg_30d · fx_chg_30d_lag30 · late_30d(마지막 열). 150행, buyer_id는 첫 열.
```
<!-- --8<-- [end:a3-columns] -->

**확인할 것**

- `scripts/clean_buyers.py`가 **원본 엑셀을 덮어쓰지 않는지**(읽기만 하는지) 훑어봅니다. `git status`에서 맨 위 `data/` 폴더에 바뀐 파일이 없어야 합니다.
- `outputs/dq_report.md`에 **전·후 건수 표**(통화 표기 · 글자 섞인 칸 · 결측 · 단위 의심)가 있는지 봅니다.
- 실행 결과가 150행인지 봅니다. 숫자는 AI의 암산이 아니라 **스크립트가 낸 값**이어야 합니다.

---

## A4 · 테스트 — 규칙의 실행 가능한 판 {#a4}

**도구** Claude Code · **Edit automatically** · **실습 A 05 검증** · 결과 `workbench/day2/tests/test_clean.py` · 커밋

<!-- --8<-- [start:a4] -->
```text
행 수·ID 유일·통화 4종·금액 ≥ 0·B072 단위 플래그 테스트를 쓰고, 통과할 때까지 고친 뒤 커밋해 줘.
```
<!-- --8<-- [end:a4] -->

테스트 파일은 `CLAUDE.md` 규칙에 따라 2일차 작업 폴더의 `tests/`에 만들어집니다. 저장소 맨 위에서 `uv run pytest -q`를 치면 그 폴더의 테스트가 돕니다(저장소의 `pytest.ini`가 대상을 `workbench/`로 정해 둡니다). 다른 곳에 만들어졌다면 `uv run pytest -q 경로`로 돌립니다.

**테스트가 실패하면** 바로 "고쳐 줘"라고 하기 전에 **테스트와 규칙 중 어느 쪽이 틀렸는지** 먼저 판단합니다. 시연 2에서도 첫 실행에 열 하나가 빠져 실패했고, AI는 테스트가 아니라 결과를 고쳤습니다. 그 판단이 맞았는지 내가 확인하는 것이 사람의 몫입니다.

---

## A5 · 스케일 비교 표 — 특성 파일에는 넣지 않는다 {#a5}

**도구** Claude Code · **실습 A 05 검증**(확인표 '기록' 줄의 스케일 비교 표) · 결과 `workbench/day2/outputs/scaling.md`

<!-- --8<-- [start:a5] -->
```text
revenue를 로그 변환한 뒤 Min-Max와 표준화로 바꾼 비교 표(최소·중앙값 근처·최대 바이어 3곳)를 outputs/scaling.md로 만들어 줘. 특성 파일에는 넣지 마.
```
<!-- --8<-- [end:a5] -->

**확인할 것** 매출이 약 190배 차이 나는 바이어 3곳이 Min-Max · 표준화에서 어떻게 달라지는지 봅니다(극단값 한 곳이 나머지를 0 쪽으로 누릅니다). 규칙 문서에 **"정규화 열을 특성 파일에 넣지 않는 이유"** 한 줄을 적습니다 — 평가 데이터의 정보가 섞이고, 내일의 트리 모델은 스케일에 둔감합니다.

---

## A6 · 남은 변경 커밋 · PR 본문 — 슬라이드에 없음 {#a6}

**도구** Claude Code · **실습 A 06 기록** · VS Code 소스 제어와 GitHub 웹으로 직접 해도 같은 결과입니다. 규칙(03 `a2-commit`)과 테스트(05 A4)는 이미 커밋돼 있으니, 여기서는 **남은 변경**만 커밋하고 PR 본문을 받습니다.

<!-- --8<-- [start:a6] -->
```text
이 브랜치의 커밋 목록(git log --oneline main..)을 보여 주고, 아직 커밋하지 않은 변경(예: outputs/scaling.md · 규칙 문서의 정규화 한 줄)이 있으면 CLAUDE.md 형식으로 커밋해 줘. workbench/day2/data/의 받은 파일 사본은 넣지 마. push한 뒤 PR 본문 초안을 보여 줘: 첫 줄 'Closes #{번호}', 이어서 dq_report 요약 5줄과 내가 정한 규칙 목록. gh가 없으면 PR은 만들지 말고 본문만.
```
<!-- --8<-- [end:a6] -->

**확인할 것** 허락 창의 명령에서 **커밋 메시지가 두 줄인지**, **어느 브랜치로 push하는지**(`d2-clean`, `main`이 아님)를 읽고 승인합니다. PR은 GitHub 저장소 화면 위쪽의 **Compare & pull request** 단추로 만들고 본문을 붙여 넣습니다(내 PC에 `gh`가 로그인돼 있으면 AI가 PR까지 만들 수 있습니다 — 그때는 Pull requests 탭에서 그 PR을 열어 본문 첫 줄만 확인합니다). **머지는 Claude Code에게 시키지 않고** 브라우저에서 내가 누릅니다.

**짝의 리뷰 코멘트를 반영할 때** — Claude Code는 GitHub의 PR 코멘트를 직접 읽지 못하는 경우가 많습니다(`gh`가 없으면 "코멘트를 붙여 넣어 달라"고 답합니다). 코멘트 글을 복사해 [리뷰 코멘트 반영](#review-fix) 프롬프트에 붙여 보냅니다.

---

## B1 · 새 작업대에서 환경 다시 만들기 {#b1}

**도구** Claude Code(새 창 — worktree) · **실습 B 01 작업대** · 결과 `.venv` · 오늘 파일

<!-- --8<-- [start:b1] -->
```text
이 폴더는 새 worktree야. uv sync로 환경을 만들고 uv run python tools/get_day_files.py 2로 오늘 파일을 다시 받아 줘. 끝나면 현재 브랜치와 git status를 보여 줘.
```
<!-- --8<-- [end:b1] -->

**어떻게 생겼나** 새 작업 폴더에는 `.venv`와, `.gitignore`로 뺀 받은 파일(`data/checkpoints/`)이 **없습니다.** 그래서 환경과 파일을 다시 만들게 합니다 — 오전 worktree 장의 '주의'를 직접 겪는 장면입니다.

**확인할 것** 현재 브랜치가 `d2-news`인지 봅니다. `git status`에는 `workbench/day2/data/` 아래 **받은 파일 사본이 '추적 안 됨'으로 여러 줄** 보입니다 — 정상이고, 커밋하지 않아도 됩니다(맨 위 `data/`의 원본은 `.gitignore` 때문에 보이지 않습니다).

---

## B2 · 뉴스 채점 — 규칙대로, 네가 직접 {#b2}

**도구** Claude Code(`d2-news` 창) · **실습 B 03 채점** · 결과 `workbench/day2/outputs/news_scored.jsonl`

<!-- --8<-- [start:b2] -->
```text
2일차 작업 폴더의 prompts/news_score_v1.md 규칙대로 data/checkpoints/d2_news.csv 1–50행을 네가 직접 읽고 채점해 줘(외부 API나 키워드 규칙 스크립트는 쓰지 마). 결과는 outputs/news_scored.jsonl에 한 행 = JSON 한 줄(news_id · buyer_id · date · news_sent_0_10 · label · evidence · confidence)로 붙여 써. 끝나면 51–100행도 같은 방식으로.
```
<!-- --8<-- [end:b2] -->

**어떻게 생겼나** 오전 시연 5를 줄인 것입니다 — API 대신 **Claude Code 세션 안에서 AI가 직접** 읽고 채점하므로 키가 필요 없습니다. **"네가 직접"**이 핵심입니다. 키워드 규칙 스크립트로 점수를 매기게 하면 AI 채점이 아니라 규칙 코드가 됩니다. 채점 규칙은 내 저장소의 `workbench/day2/prompts/news_score_v1.md`(관점 · 척도 · 근거 · 형식)입니다.

**`b2-guard` · 정답 파일이 이미 폴더에 있다면** 15:35 뒤에 파일 받기를 다시 해서 정답 20건이 `data/checkpoints/`에 들어온 상태로 채점을 이어 간다면, B2 끝에 아래 한 줄을 덧붙입니다.

<!-- --8<-- [start:b2-guard] -->
```text
채점하는 동안에는 d2_news_answer.csv(정답 20건)를 열거나 검색하지 마. 정답은 평가 단계(B4)에서만 쓴다.
```
<!-- --8<-- [end:b2-guard] -->

**확인할 것** `news_scored.jsonl`이 한 줄에 JSON 하나인지, 키 7개가 모두 있는지 봅니다. 처음 50행 뒤에 51–100행이 **이어 붙는지**도 봅니다.

---

## B3 · 검사 스크립트 — 위반 행만 다시 채점 {#b3}

**도구** Claude Code · **실습 B 03 채점** · 결과 `scripts/validate_scores.py`

<!-- --8<-- [start:b3] -->
```text
scripts/validate_scores.py를 만들어 news_scored.jsonl을 검사해 줘: 100줄인지, 점수가 0–10 정수인지, 라벨이 점수 대역(0–2 severe, 3–4 high, 5 watch, 6–10 low)과 맞는지, evidence가 원문 headline·body_short 안에 그대로 있는지. 위반 행만 다시 채점해서 고쳐.
```
<!-- --8<-- [end:b3] -->

**어떻게 생겼나** 형식 검사는 AI의 눈이 아니라 **스크립트**가 합니다. 위반이 나온 행만 다시 채점하게 해서 이미 맞은 행의 점수는 건드리지 않습니다. evidence가 원문에 그대로 있는지 보는 검사는 AI가 번역 · 요약해서 옮긴 근거를 잡습니다.

**확인할 것** 검사 결과가 **위반 0**으로 끝나는지, 다시 채점한 행이 있다면 어느 줄이었는지 봅니다.

---

## B4 · 평가 — 정답 20건과 비교 {#b4}

**도구** Claude Code(`d2-news` 창) · **실습 B 04 평가** · 결과 `workbench/day2/outputs/eval.md`

정답 파일은 **15:35에 열립니다.** 채점(B2 · B3)을 끝낸 뒤 **`d2-news` 창의 터미널에서** `uv run python tools/get_day_files.py 2`를 한 번 더 실행하면 `d2_news_answer.csv`가 `data/checkpoints/`에 들어옵니다(메인 창에서 받으면 이 작업대에는 없습니다). 그다음 보냅니다.

<!-- --8<-- [start:b4] -->
```text
data/checkpoints/d2_news_answer.csv(정답 20건)와 비교해 MAE · ±2 이내 비율 · 라벨 일치율을 계산하고 outputs/eval.md로 써 줘. 차이가 가장 큰 2건은 원문과 함께 이유를 한 줄씩.
```
<!-- --8<-- [end:b4] -->

**확인할 것** 숫자(MAE · ±2 이내 비율 · 라벨 일치율)와 **오차가 큰 2건의 원인**이 `eval.md`에 있는지 봅니다. 평가 숫자는 사람마다 다르게 나오는 것이 정상입니다. 숫자가 나쁘면 실패가 아니라 **프롬프트 v2를 만들 이유**입니다.

---

## B5 · 융합 — 30일 창 집계와 LEFT JOIN {#b5}

**도구** Claude Code · **실습 B 05 융합** · 결과 `workbench/day2/outputs/d2_end_features.csv`

<!-- --8<-- [start:b5] -->
```text
기준일 2026-08-31, 창 (2026-08-01, 2026-08-31]로 바이어별 뉴스 건수 · 평균 · 최솟값과 news_risk_30d(10 − 평균)를 만들고 outputs/d2_buyers_clean.csv에 buyer_id로 LEFT JOIN해 줘. d2_start.xlsx의 buyer_features_raw(기준일 08-31)에서 cum_dpd_days와 overdue_amount(기준일 환율로 USD 환산 → overdue_usd)도 붙여. 뉴스가 없으면 평균 5 + no_news_flag=1. 결과는 outputs/d2_end_features.csv(buyer_id 첫 열, late_30d 끝 열). 9월 기사가 0건인지, 150행인지, ID 중복이 없는지 검사하는 줄도 넣어.
```
<!-- --8<-- [end:b5] -->

**`b5-columns` · 덧붙임 — 결과 열(권장)** 확인표와 내일 3일차가 열 이름으로 대조하므로 B5 끝에 이어 붙입니다.

<!-- --8<-- [start:b5-columns] -->
```text
결과 열: 실습 A의 열(buyer_id … fx_chg_30d_lag30) 뒤에 overdue_usd · cum_dpd_days · news_cnt_30d · news_sent_0_10_30d · news_sent_min_30d · news_risk_30d · no_news_flag를 붙이고 late_30d를 맨 끝에 — 모두 32열. buyer_features_raw는 ref_date가 2026-08-31인 행만 쓰고, 엔화는 100엔 단위 환율이다.
```
<!-- --8<-- [end:b5-columns] -->

**어떻게 생겼나** 시연 3의 시간 창 집계와 LEFT JOIN을 한 문장에 담았습니다. 창은 `(08-01, 08-31]` — 8월 1일은 빼고 8월 31일은 넣습니다. 기준일 **뒤**(9월) 기사가 섞이면 특성에 미래가 들어간 것입니다. 뉴스가 없는 바이어는 **평균 5 + `no_news_flag=1`**로 채워 행이 사라지지 않게 합니다.

**`b5-rule8` · 이어서 — 규칙 문서 8칸** 양식의 '8칸(뉴스 창)은 실습 B에서 채운다'를 오늘 쓴 규칙으로 채웁니다.

<!-- --8<-- [start:b5-rule8] -->
```text
workbench/day2/rules/정제규칙.md 8칸(뉴스 창)을 오늘 B5에서 쓴 규칙으로 '규칙/왜' 두 줄씩 채우고, 9칸 변경 기록에 한 줄 더해 줘 — 창 (2026-08-01, 2026-08-31], 뉴스 0건이면 평균 5 + no_news_flag=1, news_risk_30d = 10 − 평균, 기준일 뒤(9월) 기사를 쓰지 않는 이유.
```
<!-- --8<-- [end:b5-rule8] -->

**`b5-dict` · 이어서 — 데이터 사전에 새 열(초안만 AI)** 새 열의 뜻 · 계산은 AI에게 받아도 되지만 **'시점 점검' 칸은 내가 채웁니다**(그 열이 기준일 이전 정보만으로 만들어졌는지).

<!-- --8<-- [start:b5-dict] -->
```text
workbench/day2/data/데이터사전.md의 표에 d2_end_features.csv의 새 열(overdue_usd · cum_dpd_days · news_cnt_30d · news_sent_0_10_30d · news_sent_min_30d · news_risk_30d · no_news_flag)을 같은 모양으로 한 줄씩 추가해 줘. 뜻과 계산은 쓰고, '시점 점검' 칸은 비워 둬 — 내가 쓴다.
```
<!-- --8<-- [end:b5-dict] -->

**확인할 것** 150행 · 32열 · `buyer_id` 첫 열 · `late_30d` 끝 열 · ID 중복 0, 그리고 창 안의 9월 기사 0건. 규칙 문서 8칸과 데이터 사전 새 열 7개.

---

## B6 · 8교시 — main을 반영해 충돌 풀기 {#b6}

**도구** Claude Code · **8교시 03 머지** · 충돌이 날 때만 씁니다(슬라이드 d2-74 03의 문장 그대로).

<!-- --8<-- [start:b6] -->
```text
main을 반영해 충돌을 풀고 diff를 보여 줘
```
<!-- --8<-- [end:b6] -->

더 구체적으로 시키려면 이렇게 보냅니다 — **두 변경을 모두 살리고, 테스트 뒤에 push**하라는 말까지 넣습니다.

<!-- --8<-- [start:b6-long] -->
```text
main이 바뀌었어. origin/main을 이 브랜치에 merge하고, 충돌이 나면 두 변경을 모두 살리는 쪽으로 해결해 줘. 해결한 diff를 보여 주고 테스트 후 push해 줘.
```
<!-- --8<-- [end:b6-long] -->

**확인할 것** 해결된 diff를 **내가 읽고**, 충돌 표식(`<<<<<<<` · `=======` · `>>>>>>>`)이 파일에 남아 있지 않은지 봅니다. B6(짧은 판)은 합친 결과를 **내 PC에만** 두는 경우가 많습니다(미리 해 본 실행에서도 "push하지 않았습니다"로 끝났습니다) — diff에 동의하면 `push해 줘`(또는 소스 제어 **Sync Changes**)로 올린 뒤, PR 화면이 'no conflicts'로 바뀌면 머지 단추를 누릅니다.

---

## 안 맞을 때 — 어느 규칙에서 갈렸나 {#mismatch}

확인표의 숫자와 내 결과가 다르면 **바로 고치게 하지 말고** 먼저 원인을 묻습니다.

<!-- --8<-- [start:mismatch] -->
```text
확인표에서 {항목}은 {기대값}인데 내 결과는 {내 값}이야. 고치지 말고, 어느 규칙(정제규칙.md 몇 번 칸)에서 갈렸는지 찾아서 원인 후보와 확인 방법만 알려 줘.
```
<!-- --8<-- [end:mismatch] -->

원인이 규칙 문서에 있으면 **규칙 문서를 먼저 고치고**(+ '9. 변경 기록' 한 줄) 스크립트를 다시 돌립니다. 중위수 대신 KNN을 골랐다면 대체값이 달라지는 것이 정상이고, 결측 플래그 개수는 같아야 합니다.

**`a-fix` · 이어서 — 원인을 찾았으면 규칙부터 고치고 다시 돌리기** 원인 후보를 읽고 **내가 동의한 뒤에** 보냅니다(엑셀 검산본과의 대조 `excel-compare`로 찾은 원인에도 그대로 씁니다).

<!-- --8<-- [start:a-fix] -->
```text
방금 찾은 원인대로 rules/정제규칙.md의 해당 칸을 고치고 9칸 변경 기록에 한 줄 더한 뒤, scripts/clean_buyers.py를 다시 돌리고 uv run pytest -q로 확인해 줘. 원본은 읽기만, 커밋은 아직 하지 마.
```
<!-- --8<-- [end:a-fix] -->

고친 뒤 `a-check`(또는 `excel-compare`)를 한 번 더 보내 '같음'이 됐는지 봅니다. 남은 변경은 06의 A6이 커밋합니다.

---

## 보조 프롬프트 — 슬라이드에 없음 {#support}

인쇄된 단계를 **손작업 대신 AI에게 맡기거나, AI 결과를 다른 길과 대조**하는 데 씁니다. 모두 선택이고, 단계 번호는 인쇄본 그대로입니다.

### `a0` · 준비 맡기기 {#a0}

**도구** Claude Code(Manual) · **실습 A 01 준비** · 결과 받은 파일 목록 · 브랜치 · `git status`

<!-- --8<-- [start:a0] -->
```text
main을 최신으로 맞추고(git pull) uv run python tools/get_day_files.py 2로 오늘 파일을 받아 줘. 끝나면 받은 파일 목록과 현재 브랜치, git status를 보여 줘. 다른 것은 바꾸지 마.
```
<!-- --8<-- [end:a0] -->

### `a-check` · 확인표 대조 — 실습 A {#a-check}

**도구** Claude Code · **실습 A 05 검증** · 결과 화면의 대조 표(고치지 않음)

<!-- --8<-- [start:a-check] -->
```text
outputs/d2_buyers_clean.csv와 테스트 결과로 아래 확인표를 대조해 줘. 고치지 말고 '항목 | 기대값 | 내 값 | 같음?' 표만 보여 줘. 내 값은 파일에서 계산한 숫자로 쓰고, 계산한 코드도 보여 줘.
1 통화 정리: USD 110 · EUR 23 · JPY 10 · CNY 7
2 B001 ar_balance_usd: 21,026.82
3 unit_flag=1: B072 한 곳(9,665.37 USD)
4 neg_equity=1: B013 · B048(debt_to_equity 빈칸)
5 fin_missing=1: 47곳 · 대체값(중위수일 때) current_ratio 1.4218 · debt_to_equity 1.4579 · dso_buyer 66.44 · op_margin 0.0654
6 uv run pytest -q 통과
```
<!-- --8<-- [end:a-check] -->

### `excel-compare` · 엑셀 검산본과 대조 {#excel-compare}

**도구** Claude Code · **실습 A 05 검증**(B001 손계산을 대신하는 완성본) · 결과 화면의 대조 표(고치지 않음)

<!-- --8<-- [start:excel-compare] -->
```text
labs/day2/d2_excel_check.xlsx의 '확인표_A' 시트(엑셀 수식으로 다시 계산한 값)와 outputs/d2_buyers_clean.csv를 항목마다 나란히 놓아 줘. 고치지 마.
표: 항목 | 엑셀 검산본 | 내 CSV(코드로 계산) | 같음/다름
항목: 표준 통화별 바이어 수 · B001 · B009 · B072의 ar_balance_usd · unit_flag=1인 바이어 · neg_equity=1인 바이어 · fin_missing 합계 · 결측을 채운 값(엑셀은 대체 전 150행의 중앙값)
다른 줄마다 원인 후보를 하나씩: 환율 기준일 · 엔화 100엔 단위 · 글자 섞인 칸 처리 · 결측 정의 · 대체 방식(KNN이면 다른 것이 정상). 어느 쪽이 맞는지는 쓰지 마.
```
<!-- --8<-- [end:excel-compare] -->

### `robots` · robots.txt 읽기 — Claude 웹 {#robots}

**도구** **Claude 웹**(또는 ChatGPT) 새 대화 · **실습 B 02 수집 점검** · 결과 `수집점검.md` 3칸 초안

<!-- --8<-- [start:robots] -->
```text
아래는 {사이트 이름}의 robots.txt 원문이다. User-agent: * 에 걸린 Disallow 줄 3개와, AI 수집 봇(GPTBot · ClaudeBot · CCBot · Google-Extended 등)을 따로 막는 줄이 있으면 원문 그대로 뽑아 표로 줘. 없으면 '없음'이라고만 쓰고 추측하지 마.

{robots.txt 원문 붙여넣기}
```
<!-- --8<-- [end:robots] -->

### `terms` · 약관 읽기 — Claude 웹 {#terms}

**도구** **Claude 웹**(또는 ChatGPT) 같은 대화 · **실습 B 02 수집 점검** · 결과 `수집점검.md` 4칸(약관 조항 원문)

관심 바이어 국가의 뉴스 사이트 한 곳을 정하고, 그 사이트의 이용약관에서 크롤링 · 스크래핑 · 자동 · robot · data mining · AI 학습 같은 낱말을 Ctrl+F(macOS는 ⌘+F)로 찾아 그 절을 붙입니다(전문이 짧으면 전문). **오늘은 점검만 합니다 — 기사를 수집하지 않습니다.**

<!-- --8<-- [start:terms] -->
```text
아래는 {사이트 이름}의 이용약관이다. 자동 수집·크롤링·스크래핑·봇·AI 학습·데이터 마이닝을 금지하거나 제한하는 조항을 찾아, 원문 문장을 한 글자도 바꾸지 말고 그대로 인용해 표로 만들어 줘. 열: 조항 위치 | 원문 | 무엇을 금지하나. 해당 조항이 없으면 '없음'이라고만 쓰고 추측하지 마.

{이용약관 전문 붙여넣기}
```
<!-- --8<-- [end:terms] -->

**확인할 것** AI가 인용한 문장을 **약관 원문에서 Ctrl+F(macOS는 ⌘+F)로 직접 찾아** 글자 그대로 있는지 봅니다. 없는 문장이면 근거로 쓰지 않습니다. 원문이 영어여도 인용은 원문 그대로 둡니다.

### `terms-form` · 수집 점검 5칸 초안 — Claude 웹 {#terms-form}

**도구** **Claude 웹** 같은 대화 · **실습 B 02 수집 점검** · 결과 `수집점검.md` 2–5칸 초안(0 · 1칸과 결론은 내가)

<!-- --8<-- [start:terms-form] -->
```text
방금 두 표를 아래 수집 점검 양식의 2·3·4·5칸에 맞춰 Markdown으로 채워 줘. 원문 인용은 한 글자도 바꾸지 말고, 4칸에는 금지 내용이 담긴 핵심 문장만 위치와 함께 넣어(문단을 통째로 옮기지 마). 모르는 칸은 '확인 필요'로 둬. 0·1칸과 결론 칸은 비워 둬 — 내가 쓴다.

{수집점검.md 양식 붙여넣기}
```
<!-- --8<-- [end:terms-form] -->

**확인할 것** 0칸(사이트 · 점검한 날짜) · 1칸(목적) · 결론과 이유 한 줄은 **내가** 씁니다. 2칸에 '확인 필요'가 나오면 그 사이트에 공식 API · RSS가 있는지 직접 찾아봅니다(공식 창구가 먼저). 약관 문단을 통째로 옮기면 공개 저장소에 남의 글이 길게 남습니다 — 핵심 문장만.

### `b-check` · 확인표 대조 — 실습 B {#b-check}

**도구** Claude Code(`d2-news` 창) · **실습 B 06 기록** · 결과 화면의 대조 표(고치지 않음)

<!-- --8<-- [start:b-check] -->
```text
outputs/news_scored.jsonl과 outputs/d2_end_features.csv로 아래 확인표를 대조해 줘. 고치지 말고 '항목 | 기대값 | 내 값 | 엑셀 검산본 | 같음?' 표만 보여 줘. 2번은 date 열로 다시 세고, 엑셀 검산본 열에는 labs/day2/d2_excel_check.xlsx의 '확인표_B' 시트 값을 옮겨 줘.
1 채점 결과: 100줄 · 형식 위반 0(scripts/validate_scores.py 결과)
2 창 (2026-08-01, 2026-08-31]: 기사 46건 · 바이어 37곳 · 창 안의 9월 기사 0건(앞 100행의 9월 기사 40건은 창 밖)
3 결합 결과: 150행 · 32열 · buyer_id 첫 열 · late_30d 끝 열 · ID 중복 0
4 news_sent_0_10_30d 평균 ≈ 5.4(내 점수에 따라 다름) · 뉴스 없는 바이어 113곳 = 5
5 B001: 뉴스 0건 → 5.0 · no_news_flag 1
6 outputs/eval.md: MAE · ±2 이내 비율 · 라벨 일치율 + 오차 원인 2건
```
<!-- --8<-- [end:b-check] -->

### `b-commit` · 커밋 · PR — 실습 B {#b-commit}

**도구** Claude Code(`d2-news` 창) · **실습 B 06 기록** · 결과 커밋 · push · PR 본문 초안(머지는 8교시에 사람이)

<!-- --8<-- [start:b-commit] -->
```text
이번 실습 B에서 만든 파일만 커밋해 줘: workbench/day2/rules/수집점검.md · rules/정제규칙.md · outputs/news_scored.jsonl · outputs/eval.md · outputs/d2_end_features.csv · data/데이터사전.md · 그리고 scripts/에 이번에 만든 스크립트 전부(validate_scores.py와 평가 · 결합에 쓴 것 — 숫자를 만든 코드). workbench/day2/data/ 안에서는 데이터사전.md만 넣고 받은 파일 사본(d2_start.xlsx · d2_news.csv 같은)은 넣지 마. 메시지는 CLAUDE.md 형식. push한 뒤 PR 본문 초안(무엇을 했나 · 확인한 값 · 오차 큰 2건)을 보여 줘. 머지는 하지 마.
```
<!-- --8<-- [end:b-commit] -->

### `p8-review` · 셀프 리뷰 4가지 — 8교시 {#p8-review}

**도구** Claude Code(`d2-news` 창) · **8교시 01 셀프 리뷰** · 결과 화면의 점검 표(고치지 않음)

<!-- --8<-- [start:p8-review] -->
```text
PR B를 머지하기 전 셀프 리뷰 4가지를 점검해 줘. 앞 대화의 기억이 아니라 지금 파일과 git을 다시 읽어서, 고치지 말고 결과만 표로: ① outputs/d2_end_features.csv가 150행인가 ② uv run pytest -q 통과 · scripts/validate_scores.py 위반 0인가 ③ main 대비 바뀐 파일(git diff main --stat과 내용)에 키 · 비밀번호 · 실명 · 기사 본문 전체가 없는가 ④ rules/정제규칙.md 8칸과 data/데이터사전.md 새 열이 갱신됐는가. 덧붙여 outputs의 숫자를 만든 scripts/ 파일이 PR에 함께 들어 있는지도 한 줄로.
```
<!-- --8<-- [end:p8-review] -->

**확인할 것** AI의 점검 표를 **내 눈(Files changed)**과 맞춰 봅니다. 미리 해 본 실행에서는 AI가 이미 고친 파일을 앞 대화의 기억으로 "비어 있다"고 잘못 적은 줄이 있었습니다 — 표와 화면이 다르면 화면이 맞습니다.

### `review-fix` · 리뷰 코멘트 반영 — 실습 A 06 · 8교시 02 {#review-fix}

**도구** Claude Code(그 PR의 브랜치 창 — 실습 A는 `d2-clean`, 8교시는 `d2-news` 창) · 결과 반영 커밋 + push(PR에 저절로 붙는다)

짝이 단 코멘트 글을 GitHub에서 복사해 마지막 줄 자리에 붙입니다. Claude Code는 PR 코멘트를 직접 읽지 못하는 경우가 많습니다(`gh`가 없으면 "붙여 넣어 달라"고 답합니다).

<!-- --8<-- [start:review-fix] -->
```text
아래 PR 리뷰 코멘트를 반영해서 커밋하고 push해 줘. 고치기 전에 무엇을 바꿀지 한 줄로 먼저 보여 줘.

{리뷰 코멘트 붙여넣기}
```
<!-- --8<-- [end:review-fix] -->

**확인할 것** 반영 커밋이 PR의 Commits 탭에 붙었는지, 코멘트가 '규칙을 바꾸라'는 내용이면 규칙 문서 9칸 변경 기록에도 한 줄이 들어갔는지 봅니다. 코멘트에 동의하지 않으면 반영하지 말고 PR에 답글로 이유를 씁니다.

---

## 채팅 경로 — Claude Code를 못 쓸 때 {#chat-path}

Claude Code 계정이 없거나(무료 플랜은 쓸 수 없습니다) 확장이 로그인되지 않으면 **Claude 또는 ChatGPT 웹**에 파일을 **첨부**해 같은 일을 합니다. 붙여 넣기 대신 첨부하고, 결과는 파일로 받습니다. 필요한 파일은 사이트의 '파일 받기' 카드에 모두 있습니다.

| 바꿀 곳 | 어떻게 |
|---|---|
| 파일 경로(`data/checkpoints/…`) | 지우고 **파일을 첨부**합니다. ChatGPT 무료는 하루 업로드 수가 적으니 Claude를 먼저 권합니다 |
| "scripts/… 를 만들고 uv run으로 실행해" | **"코드를 실행해서 처리하고 결과 파일을 내려받게 해 줘"**(Claude는 코드 실행, ChatGPT는 데이터 분석 기능). 실행 코드도 보여 달라고 합니다 |
| "outputs/…에 저장해" · 양식 칸 채우기 | 양식 파일을 **첨부**하고 **"이 양식대로 채운 .md 파일로 내려받게 해 줘"** |

### 실습 A — 정제 {#chat-a}

A1 · A2를 경로만 빼고 보낸 뒤, 규칙 문서와 정제 결과를 파일로 받습니다. `d2_start.xlsx`와 `rules_template.md`를 첨부합니다.

<!-- --8<-- [start:chat-a] -->
```text
첨부한 rules_template.md 양식의 1–7칸을 방금 진단과 내 결정으로 '규칙/왜' 두 줄씩 채워 정제규칙.md 파일로 내려받게 해 줘. 이어서 그 규칙대로 첨부한 d2_start.xlsx의 buyers 시트를 정제하는 코드를 실행해(원본은 읽기만) d2_buyers_clean.csv(150행)와 전·후 비교 dq_report.md를 내려받게 해 줘. 실행한 코드도 보여 줘.
```
<!-- --8<-- [end:chat-a] -->

이어서 [결과 열 덧붙임](#a3)(`a3-columns`)을 보내고, 받은 파일은 GitHub 웹의 **Add file → Upload files**로 `d2-clean` 브랜치에 올립니다.

### 실습 B — 채점 {#chat-b}

`news_score_v1.md`와 `news_rows_001-050.csv`를 첨부합니다. 끝나면 `news_rows_051-100.csv`를 첨부해 "같은 규칙으로 51–100행을 이어 붙인 news_scored.jsonl(100줄)로 내려받게 해 줘"라고 보냅니다.

<!-- --8<-- [start:chat-b] -->
```text
첨부한 news_score_v1.md의 규칙대로 첨부한 news_rows_001-050.csv의 50행을 네가 직접 읽고 채점해 줘(키워드 규칙 코드는 쓰지 마). 출력은 JSON Lines — 한 행 = JSON 한 줄(news_id · buyer_id · date · news_sent_0_10 · label · evidence · confidence), 입력 50행 = 출력 50줄. evidence는 원문 구절 그대로. 끝나면 news_scored.jsonl 파일로 내려받게 해 줘.
```
<!-- --8<-- [end:chat-b] -->

### 실습 B — 검사 · 평가 · 결합 {#chat-b-check}

같은 대화에 `news_scored.jsonl` · `d2_news_answer.csv`(15:35 이후) · 실습 A의 `d2_buyers_clean.csv` · `d2_start.xlsx`를 첨부합니다.

<!-- --8<-- [start:chat-b-check] -->
```text
첨부한 파일로 코드를 실행해 세 가지를 해 줘. ① news_scored.jsonl 검사 — 100줄 · 점수 0–10 정수 · 라벨 대역(0–2 severe, 3–4 high, 5 watch, 6–10 low) · evidence가 첨부한 원문 안에 그대로 있는지, 위반 행 목록. ② d2_news_answer.csv(정답 20건)와 비교한 MAE · ±2 이내 비율 · 라벨 일치율과 오차가 가장 큰 2건 → eval.md. ③ 기준일 2026-08-31, 창 (2026-08-01, 2026-08-31]로 바이어별 뉴스 건수 · 평균 · 최솟값 · news_risk_30d(10 − 평균)를 d2_buyers_clean.csv에 buyer_id로 LEFT JOIN — d2_start.xlsx의 buyer_features_raw(기준일 08-31)에서 cum_dpd_days · overdue_usd도, 뉴스가 없으면 평균 5 + no_news_flag=1 → d2_end_features.csv(buyer_id 첫 열, late_30d 끝 열). 결과 파일을 내려받게 하고 9월 기사 0건 · 150행 · ID 중복 0 검사 결과도 보여 줘.
```
<!-- --8<-- [end:chat-b-check] -->

!!! warning "데이터 위생"

    이 프롬프트는 가상(합성) 데이터용입니다. 회사 실데이터는 익명화한 것이라도 올리지 않습니다. 쓰는 AI의 '모델 개선(학습)' 설정은 끄고 시작합니다. GitHub 웹의 Upload files는 `.gitignore`를 보지 않으니 올리기 전에 파일 이름과 내용을 봅니다.

---

## 더 해 보기 — 시작 프롬프트 {#more}

실습 쪽 끝의 '다 했으면' 카드에서 고른 것을 이 한 줄로 시작합니다. 모두 과정 데이터만 씁니다.

### 실습 A — 인보이스 시트도 같은 파이프라인으로 {#ax1}

<!-- --8<-- [start:ax1] -->
```text
[Plan 모드] d2_start.xlsx의 invoices_raw 시트를 진단만 해 줘 — 날짜 형식 종류 · 완전 중복 · 통화별로 비정상적으로 작은 금액을 표로. 고치지 마.
```
<!-- --8<-- [end:ax1] -->

### 실습 A — 규칙 한 줄 바꿔 보기 {#ax2}

<!-- --8<-- [start:ax2] -->
```text
지금 브랜치에서 d2-try 브랜치를 새로 만들고, 정제규칙.md 4칸 기준을 한도의 5배로 바꾸고 9칸 변경 기록에 한 줄 쓴 뒤 스크립트와 테스트를 다시 돌려 무엇이 달라졌는지 표로 보여 줘. 커밋은 하지 마.
```
<!-- --8<-- [end:ax2] -->

### 실습 A — 중위수 ↔ KNN 맞바꾸기 {#ax3}

<!-- --8<-- [start:ax3] -->
```text
결측 대체를 {다른 방식}으로 한 판을 따로 만들어 지금 판과 대체값을 바이어별로 나란히 놓은 비교 표를 outputs/impute_compare.md로 — 차이가 큰 5곳과 이유를 한 줄씩. 지금 판의 파일은 고치지 마.
```
<!-- --8<-- [end:ax3] -->

### 실습 A — 같은 정제를 DuckDB SQL로 {#ax4}

<!-- --8<-- [start:ax4] -->
```text
정제규칙 1·2·4칸을 DuckDB SQL로 다시 구현해 결과를 outputs/d2_buyers_clean.csv와 열마다 비교해 줘 — 다른 칸만 표로. SQL은 scripts/clean_buyers.sql로 남기고, 원본과 정제 CSV는 고치지 마.
```
<!-- --8<-- [end:ax4] -->

### 실습 A — 내 업무 표라면(데이터 없이 규칙만) {#ax5}

<!-- --8<-- [start:ax5] -->
```text
아래는 내 업무 엑셀의 열 이름만 일반 이름으로 바꿔 적은 목록이다(값 · 회사 정보 없음). 오늘의 정제규칙 1–7칸 틀로 열마다 '규칙/왜' 초안을 제안해 줘. 사람이 정해야 하는 곳은 '내가 정함'으로 비워 두고, 그 이유를 한 줄씩.

{일반 이름으로 바꾼 열 이름 목록}
```
<!-- --8<-- [end:ax5] -->

### 실습 B — 두 번째 채점자 · 일관성 ≠ 정확성 {#bx1}

<!-- --8<-- [start:bx1] -->
```text
outputs/news_scored.jsonl(Claude Code)과 {다른 AI의 JSONL 파일}을 같은 news_id끼리 짝지어 코헨 κ를 구하고, 정답 20건(data/checkpoints/d2_news_answer.csv)과 겹치는 건으로 모델별 MAE를 비교한 표를 outputs/kappa.md로. 두 채점이 크게 다른 3건은 원문과 함께.
```
<!-- --8<-- [end:bx1] -->

### 실습 B — 프롬프트 v2 · 한 번에 한 줄 {#bx2}

<!-- --8<-- [start:bx2] -->
```text
workbench/day2/prompts/news_score_v1.md를 news_score_v2.md로 복사하고, outputs/eval.md의 오차 큰 2건의 공통점에 맞춰 규칙 한 줄만 고쳐 줘. 같은 정답 20건으로 다시 채점 · 평가해 v1 · v2 비교 표를 outputs/eval_v2.md로 — 바꾼 줄은 git diff --no-index로 보여 주고, 같은 표본으로 다시 잰 숫자라 낙관적일 수 있다는 점도 한 줄로.
```
<!-- --8<-- [end:bx2] -->

### 실습 B — 신용평가 코멘트 점수화 {#bx3}

<!-- --8<-- [start:bx3] -->
```text
labs/day2/credit_notes/의 코멘트 2건(CN01 · CN02)을 workbench/day2/prompts/news_score_v1.md 규칙에 labs/day2/credit_notes/credit_note_v1.md 덧붙임을 더해 네가 직접 채점해 outputs/credit_notes_scored.jsonl로 써 줘. 형식은 labs/day2/credit_notes/credit_note_score.schema.json. 코멘트 날짜가 기준일(2026-08-31) 뒤라 특성표에는 넣지 마.
```
<!-- --8<-- [end:bx3] -->

### 실습 B — 다음 기준일 판(2026-09-30) {#bx4}

<!-- --8<-- [start:bx4] -->
```text
B5와 같은 방식으로 기준일 2026-09-30 뉴스 열 5개만 outputs/news_features_0930.csv로 만들고, 10월 기사 0건 · 창 안 기사 수 · 바이어 수 검사 줄을 넣어 줘. 08-31 판과 둘 다 뉴스가 있는 바이어의 news_risk_30d 변화를 표로.
```
<!-- --8<-- [end:bx4] -->

### 실습 B — API 키가 있다면 · 구조화 출력으로 300건 {#bx5}

<!-- --8<-- [start:bx5] -->
```text
anthropic 패키지를 더해야 하면 먼저 알려 줘(uv add anthropic). 환경변수 ANTHROPIC_API_KEY로 workbench/day2/schemas/news_score.schema.json 구조화 출력을 써서 data/checkpoints/d2_news.csv 300건을 채점하는 scripts/score_api.py를 만들어 줘. 키는 파일 · 커밋에 쓰지 말고, 실행 전에 예상 토큰 수와 비용을 먼저 보여 줘. 실행은 내가 승인한 뒤에.
```
<!-- --8<-- [end:bx5] -->
