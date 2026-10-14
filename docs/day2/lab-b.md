---
title: 2일차 실습 B · 뉴스 위험지수와 융합 특성표
---

<div class="tf-lab" markdown>
<span class="tf-eyebrow">2일차 · 실습 B · 6–7교시 · 15:00–16:50 · 8교시 17:00–17:20 <span class="tf-daystate" data-tf-daystate="2"></span></span>

# 실습 B · 뉴스 위험지수와 융합 특성표

<div class="tf-meta" markdown>
<span class="tf-chip tf-chip--time">15:00–16:50 · 110분</span>
<span class="tf-chip tf-chip--time">8교시 17:00–17:20</span>
<span class="tf-chip tf-chip--tool">Claude Code · Edit automatically</span>
<span class="tf-chip tf-chip--tool">VS Code Worktrees</span>
<span class="tf-chip tf-chip--tool">Claude 웹 · 약관 읽기</span>
<span class="tf-chip tf-chip--tool">Git · GitHub</span>
</div>

<div class="tf-flow" markdown>
<div markdown><b>상황</b> 바이어 관련 해외 기사가 쌓이지만 아무도 다 읽지 못합니다. AI가 기사마다 '대금 지급 능력 · 의사' 관점의 점수와 근거 구절을 달고, 형식은 스크립트로 · 정확도는 사람이 단 정답 20건으로 확인합니다. 기준일 전 30일 기사만 바이어별로 모아 실습 A의 정제 표 옆에 붙이면 내일 연체 예측의 입력이 됩니다.</div>
<span>→</span>
<div markdown><b>넣는 것</b> `d2_news.csv` 앞 100행 + 채점 규칙 `news_score_v1.md` + 정답 20건(15:35) + 실습 A의 `d2_buyers_clean.csv` + `d2_start.xlsx`(기준일 행 · 환율) + 뉴스 사이트 1곳의 robots.txt · 약관</div>
<span>→</span>
<div markdown><b>얻는 것</b> 수집점검.md · 뉴스 점수 JSONL(100줄) · 검사 스크립트 · eval.md · **융합 특성표 d2_end_features.csv(150행 × 32열)** · 데이터 사전 · 규칙 8칸 · PR(8교시에 머지)</div>
</div>

<div class="tf-lab__grid" markdown>
<div class="tf-lab__cell" markdown><span class="tf-lab__label">목표</span> 뉴스 100건을 AI가 0–10 점수로 바꾸고 **믿을 만한지 잰 뒤**, 기준일 전 30일 뉴스 위험지수를 정제 표에 붙인 **융합 특성표**를 PR로 올립니다</div>
<div class="tf-lab__cell" markdown><span class="tf-lab__label">오전 시연과의 관계</span> 시연 5의 축소판 — API 대신 Claude Code 세션 안에서 직접 채점(키 불필요) · 300건 → 100건 · 골든셋 20건. 시연 3의 창 집계 · LEFT JOIN, 시연 4의 수집 점검, 시연 1의 worktree를 직접</div>
</div>

<small>macOS에서는 이 쪽 단축키의 ++ctrl++ 을 ++cmd++ 로 누릅니다. 터미널 ++ctrl+grave++ 과 소스 제어 ++ctrl+shift+g++ 만 macOS도 ++ctrl++ 그대로입니다.</small>

<div data-tf-map></div>
</div>

## 입력 파일 받기 {#files}

새 작업대(01)에서 프롬프트 B1이 `uv run python tools/get_day_files.py 2`로 **다시** 받습니다 — 새 폴더에는 `.gitignore`로 뺀 받은 파일이 없기 때문입니다. 채팅 경로로 하는 분은 아래 카드에서 받습니다(채점용으로 50행씩 나눈 `news_rows_*.csv`와 양식 3개도 있습니다).

--8<-- "docs/_snippets/day2/files_lab-b_cards.md"

카드에 잠금 표시가 있으면 그 시각 뒤에 받습니다 — 정답 20건 `d2_news_answer.csv`는 **15:35**에 열립니다(그 전에는 `get_day_files.py`도 `[열기 전]`). 먼저 내 점수를 만든 뒤 04에서 받습니다. 슬라이드 · 시연 화면의 경로(`data/raw/` · `src/` · `reports/`)와 내 저장소의 자리는 [실습 A의 대응표](lab-a.md#paths)와 같습니다.

## 실습 B · 뉴스 위험지수와 융합 특성표 {#lab-b}

<div class="tf-phase" id="time" markdown>

<span class="tf-eyebrow">슬라이드 d2-71 · 실습 B · 15:00–16:50 · Claude Code · Git · GitHub</span>

**목표** 뉴스 100건을 점수로 바꿔 검증하고, 위험지수를 넣은 융합 특성표를 PR로

- **01** 작업대 — worktree d2-news → 새 창 · uv sync · 파일 받기
- **02** 수집 점검 — 뉴스 사이트 1곳의 robots.txt·약관 → 5칸
- **03** 채점 — 1–100행을 50행씩 → JSONL → 검사
- **04** 평가 — 정답 20건(15:35)으로 MAE · ±2 · 일치율
- **05** 융합 — 30일 창 집계 → LEFT JOIN → 특성표
- **06** 기록 — 특성 사전 갱신 → 커밋 → PR

**산출물** 특성표 150행 · eval.md · 수집점검.md · PR · **시간** 110분

</div>

### 01. 작업대 — worktree d2-news → 새 창 · uv sync · 파일 받기 (15:00–15:10) { #b-bench .step data-tool="VS Code, Claude Code" data-phase="실습 B" }

**왜** 실습 A의 폴더는 그대로 두고 같은 저장소의 다른 브랜치를 **별도 폴더**로 꺼냅니다. 오전 worktree 장의 '주의'를 직접 겪는 장면입니다 — 새 작업대에는 `.venv`와 받은 파일이 없습니다. `main` → worktree `d2-news` → 새 창 → B1

!!! me "내가 할 일"

    1. 메인 창 터미널에서 `git switch main` · `git pull`(실습 A의 머지를 받습니다).
    2. 소스 제어(++ctrl+shift+g++) 제목줄의 `…` → **Repositories**에 체크합니다(처음 한 번 — 저장소 줄이 보입니다).
    3. **저장소 줄** 오른쪽 `…` → **Worktrees → Create Worktree…** → `+ Create new branch…` → 이름 **`d2-news`** → 위치는 기본값 그대로 Enter.
    4. Worktrees 목록의 `d2-news`를 오른쪽 단추로 눌러 **Open Worktree in New Window**. 새 창의 **왼쪽 아래 상태 표시줄이 `d2-news`**인지 봅니다.
    5. 새 창에서 Claude Code 패널을 열고 모드를 확인한 뒤 **B1**을 보냅니다.

<figure markdown="span">
  ![VS Code 소스 제어에서 worktree를 만드는 세 장면 — 저장소 줄의 … 단추, Worktrees › Create Worktree… 메뉴, 새 브랜치 이름 d2-news 입력 칸](../assets/screens/d2-worktree-create.png){ width="620" loading=lazy }
  <figcaption>① 저장소 줄의 <code>…</code> → ② <code>Worktrees › Create Worktree…</code> → ③ 새 브랜치 이름 <code>d2-news</code>. 메뉴 이름은 VS Code 버전에 따라 조금 다를 수 있습니다</figcaption>
</figure>

!!! prompt "프롬프트 B1 — 새 작업대에서 환경 다시 만들기"

    --8<-- "labs/day2/prompts.md:b1"

!!! ai "AI가 하는 일"

    `uv sync`(허락 창 1번 · 보통 1분 안팎 — 패키지를 전역 캐시에서 복사합니다)로 새 폴더에 `.venv`를 만들고, 파일 받기 명령(허락 창 1번)으로 `data/checkpoints/` · `labs/day2/` 파일을 받습니다. 끝나면 현재 브랜치(`d2-news`)와 `git status`를 보여 줍니다.

<figure markdown="span">
  ![git 저장소 하나에 작업 폴더 세 개가 붙은 모습 — 공유하는 것은 커밋 · 브랜치 · 원격, 폴더마다 따로인 것은 파일 · .venv · .env](../assets/diagrams/d2-worktree-benches.png){ width="560" loading=lazy }
  <figcaption>이력 · 브랜치는 공유하고 파일 · <code>.venv</code> · <code>.gitignore</code>로 뺀 데이터는 폴더마다 따로 — 그래서 B1이 환경과 파일을 다시 만듭니다</figcaption>
</figure>

!!! ok "확인"

    - [ ] 새 창 상태 표시줄이 `d2-news`이고, 새 폴더에 `.venv`가 생겼다
    - [ ] B1 보고에 `d2_news.csv` · `d2_start.xlsx`를 받았다는 줄이 있다

    `git status`에 `workbench/day2/data/` 아래 **받은 파일 사본이 '추적 안 됨'으로 여러 줄** 보이는 것은 정상입니다 — 커밋하지 않아도 됩니다.

??? fix "Repositories · Worktrees 메뉴가 없어요"

    VS Code를 업데이트하거나, 메인 창 터미널에서 `git worktree add ../내저장소-news -b d2-news`를 친 뒤 **File → Open Folder…**로 그 폴더를 새 창에서 엽니다.

??? fix "worktree가 어려워요"

    원래 폴더에서 브랜치만 만들어도 됩니다 — `git switch -c d2-news`(또는 상태 표시줄의 브랜치 이름 → `+ Create new branch…`). 새 창이 없는 대신 B1은 건너뜁니다.

??? fix "실습 A가 아직 머지 전이에요"

    `main` 대신 **`d2-clean`에서** worktree를 만듭니다 — A 결과(`d2_buyers_clean.csv`)가 05의 입력입니다. 8교시에 두 PR을 차례로 머지합니다.

??? fix "uv sync가 느리거나 실패해요 · 새 창이 로그인을 다시 물어요"

    교실 망이 붐비면 몇 분 걸립니다. 계속 실패하면 원래 폴더에서 브랜치만 만들어 진행합니다. 새 창의 Claude Code는 같은 계정으로 다시 로그인합니다.

<p class="tf-check"><time>15:10</time> 손 점검 — 새 창 상태 표시줄 <code>d2-news</code></p>

### 02. 수집 점검 — 뉴스 사이트 1곳의 robots.txt·약관 → 5칸 (15:10–15:20) { #b-collect .step data-tool="Claude 웹, VS Code" data-phase="실습 B" }

**왜** 모으기 전에 **가져와도 되는 글인지** 봅니다 — 공식 API가 먼저, 스크래핑은 robots.txt · 약관 · 법을 본 뒤. 옮겨 적기는 AI가, **원문 확인과 결론은 사람이** 합니다. 오늘은 **점검만** 하고 기사를 수집하지 않습니다. 사이트 1곳 → robots · 약관 → `수집점검.md` 5칸 + 결론

!!! me "내가 할 일"

    1. 관심 바이어 국가의 **뉴스 사이트 한 곳**을 정합니다(짝과 다른 곳).
    2. 브라우저 주소창에 `사이트주소/robots.txt` → 전체를 복사해 **Claude 웹**에 `robots` 프롬프트와 함께 보냅니다.
    3. 그 사이트의 **이용약관**에서 ++ctrl+f++ 로 crawl · scrap · robot · automated · data mining · AI(한글이면 수집 · 크롤링 · 자동)를 찾아 그 절을 같은 대화에 `terms` 프롬프트와 함께 붙입니다.
    4. AI가 인용한 문장을 **약관 원문에서 ++ctrl+f++ 로 직접 찾습니다** — 글자 그대로 없으면 근거로 쓰지 않습니다.
    5. `terms-form`으로 2–5칸 초안을 받아 `workbench/day2/rules/수집점검.md`에 붙이고, **0칸(사이트 · 날짜) · 1칸(목적) · 결론 하나**(API 사용 / 수동 열람만 / 수집 불가)와 이유 한 줄을 직접 씁니다. 2칸이 '확인 필요'이면 그 사이트의 공식 API · RSS를 직접 찾아봅니다.

!!! prompt "`robots` · robots.txt 읽기 — Claude 웹(원문 그대로 · 추측 금지)"

    --8<-- "labs/day2/prompts.md:robots"

    빈칸 `{사이트 이름}` — 고른 사이트 이름 · 마지막 줄 자리에 robots.txt 원문을 붙입니다 · [빈칸 값 표](../prompts/day2.md#values)

!!! prompt "`terms` · 약관 읽기 — Claude 웹(같은 대화)"

    --8<-- "labs/day2/prompts.md:terms"

    마지막 줄 자리에 약관에서 찾은 절(짧으면 전문)을 붙입니다.

???+ prompt "`terms-form` · 5칸 초안 — Claude 웹(결론은 비워 둔다)"

    --8<-- "labs/day2/prompts.md:terms-form"

!!! ai "AI가 하는 일"

    Claude 웹이 Disallow 줄 · AI 수집 봇 줄과 금지 조항을 **원문 그대로 인용한 표**로 정리하고, 양식의 2–5칸 초안을 씁니다 — 4칸은 금지 내용이 담긴 핵심 문장만, 모르는 칸은 '확인 필요', 0 · 1칸과 결론 칸은 비워 둡니다(미리 해 본 실행: 세 프롬프트에 합쳐 40초 안팎). 인용이 원문과 한 글자라도 다를 수 있으니 확인은 사람이 합니다.

<figure class="result" markdown="span">
  ![정체를 밝힌 curl로 받은 robots.txt와 Claude Code가 정리한 수집 조건 표](../assets/screens/d2-robots-conditions.png){ width="680" loading=lazy }
  <figcaption>robots.txt를 읽는 예(오전 시연 4 — 미국 SEC의 공식 데이터 창구). 허용 · 금지 경로 · 요청 간격 · 정체 밝히기가 한 표로 정리됩니다. robots.txt를 지켰다고 허락을 받은 것은 아닙니다</figcaption>
</figure>

<figure class="result" markdown="span">
  ![수집점검.md의 Markdown 미리보기 — 목적 · API · robots.txt · 약관 · 남길 항목 다섯 칸과 결론](../assets/screens/d2-collect-check.png){ width="420" loading=lazy }
  <figcaption>채워진 수집 점검표의 예(공식 API가 있는 사이트 기준) — 칸마다 근거, 결론은 하나</figcaption>
</figure>

!!! ok "확인"

    - [ ] `수집점검.md` 5칸이 모두 있고, 인용은 원문 그대로 + 찾은 위치
    - [ ] 결론 하나 + 이유 한 줄
    - [ ] 기사를 수집하거나 본문을 복사하지 않았다(남기는 것은 제목 · 날짜 · 주소 · 점수)

??? fix "약관 페이지를 못 찾겠어요"

    사이트 맨 아래(푸터)의 Terms · Terms of use · 이용약관 · AGB · Nutzungsbedingungen 같은 링크를 봅니다. 없으면 검색창에 `사이트이름 terms of use`. 5분 안에 못 찾으면 4칸에 '찾지 못함'으로 쓰고, 근거가 없으니 결론은 **수동 열람만**으로 둡니다.

??? fix "robots.txt가 없어요(404)"

    '없음'도 결과입니다. 3칸에 적고 약관으로 판단합니다.

??? fix "약관이 너무 길어요 · 영어예요"

    금지 낱말로 찾은 절만 붙입니다. 영어 약관은 **인용은 원문 그대로**, 설명만 한국어로 받습니다.

??? fix "AI가 인용한 문장을 원문에서 못 찾겠어요"

    근거로 쓰지 않습니다. "원문 그대로, 한 글자도 바꾸지 말고 다시"라고 요청합니다 → [FAQ](../faq.md#q-quote).

??? fix "사이트가 열리지 않아요(회사망)"

    오전 시연 4의 SEC(공식 API가 있는 창구)를 예로 써도 됩니다 — 위 두 그림의 모양입니다.

### 03. 채점 — 1–100행을 50행씩 → JSONL → 검사 (15:20–15:45) { #b-score .step data-tool="Claude Code" data-phase="실습 B" }

**왜** AI가 기사마다 **점수 · 라벨 · 근거 · 확신도**를 답니다. 형식은 AI의 눈이 아니라 **스크립트**가 검사합니다. `d2_news.csv` 1–100행 + `news_score_v1.md` → B2 → `news_scored.jsonl` → B3 → 위반 0

!!! me "내가 할 일"

    1. `workbench/day2/prompts/news_score_v1.md`를 한 번 읽습니다 — **관점**(대금 지급 능력 · 의사만) · **척도**(0 파산 … 10 지급 위험을 낮춤) · **근거**(원문 구절 그대로) · **형식**(입력 1행 = JSON 1줄).
    2. 모드를 **Edit automatically**로 바꾸고 **B2**를 보냅니다. **"네가 직접"**이 핵심입니다 — 키워드 규칙 스크립트로 점수를 매기게 하지 않습니다.
    3. 51–100행이 **이어 붙었는지** 봅니다(파일이 100줄).
    4. **B3**을 보내 검사 스크립트를 만들고, 위반 행만 다시 채점하게 합니다.

!!! prompt "프롬프트 B2 — 뉴스 채점(네가 직접 · 50행씩)"

    --8<-- "labs/day2/prompts.md:b2"

!!! prompt "프롬프트 B3 — 검사 스크립트 · 위반 행만 다시 채점"

    --8<-- "labs/day2/prompts.md:b3"

??? prompt "`b2-guard` · 15:35 뒤에 채점을 이어 간다면 — B2 끝에 덧붙이기"

    --8<-- "labs/day2/prompts.md:b2-guard"

!!! ai "AI가 하는 일"

    50행씩 기사를 읽고 한 줄씩 JSON을 씁니다(1–50행 → 51–100행, 10분 안팎). 한 줄은 이런 모양입니다(앞 100행 밖의 행으로 만든 **모양 예시** — 점수는 내 결과와 다를 수 있습니다).

    ```text
    {"news_id":"N00995","buyer_id":"B014","date":"2026-01-22","news_sent_0_10":3,"label":"high","evidence":"has delayed payments by up to 79 days","confidence":0.8}
    ```

    B3은 `scripts/validate_scores.py`로 **줄 수 · 0–10 정수 · 라벨 대역 · 근거가 원문에 그대로 있는지**를 검사해 위반 행 목록을 보이고, 그 행만 다시 채점합니다.

<figure class="result" markdown="span">
  ![VS Code 편집기에 나란히 열린 채점 규칙 파일 news_score_v1.md와 출력 스키마 파일](../assets/screens/d2-prompt-v1.png){ loading=lazy }
  <figcaption>채점 규칙과 출력 스키마(오전 시연 5) — 내 저장소의 <code>news_score_v1.md</code>가 같은 모양입니다</figcaption>
</figure>

<figure markdown="span">
  ![뉴스 점수 0–10 척도 — 0 파산, 1–2 심각, 3–4 뚜렷한 부정, 5 경계, 6–8 중립, 9–10 지급 위험을 낮춤](../assets/diagrams/d2-risk-scale.png){ loading=lazy }
  <figcaption>점수는 높을수록 안전합니다 — 라벨 대역 0–2 severe · 3–4 high · 5 watch · 6–10 low, 위험지수 = 10 − 점수</figcaption>
</figure>

!!! ok "확인"

    - [ ] `news_scored.jsonl` **100줄**, 한 줄에 키 7개(news_id · buyer_id · date · news_sent_0_10 · label · evidence · confidence)
    - [ ] B3 검사 **위반 0** · 다시 채점한 행이 어느 줄이었는지 안다
    - [ ] 점수가 5(경계)에 몰리지 않았다 — 애매한 기사는 5가 아니라 confidence를 낮췄다(6–8 '중립 · 일상'이 많은 것은 정상)

??? fix "AI가 키워드 규칙 스크립트를 쓰려고 해요"

    멈추고 B2를 다시 보냅니다. AI가 기사마다 **판단한 점수를 파일에 쓰는** 스크립트는 괜찮습니다.

??? fix "51–100행이 앞 결과를 덮어썼어요 · 줄이 모자라요"

    "outputs/news_scored.jsonl에 51–100행을 **이어서** 붙여 써"라고 보냅니다. B3 검사가 빠진 `news_id`를 찾아 줍니다.

??? fix "점수가 5에 몰려요 · 거의 모두 같은 점수예요"

    "척도 앵커를 다시 읽고, 애매하면 5로 뭉개지 말고 confidence를 낮춰라"라고 덧붙여 다시 채점하게 합니다. 중립 소식에 7을 많이 주는 것은 규칙(6–8) 안이라 괜찮습니다 — 미리 해 본 실행에서는 100건 중 47건이 7이었고, 정답 20건과의 차이는 모두 1점 이내였습니다.

??? fix "evidence가 번역 · 요약돼 있어요 · 헤드라인과 본문을 이어 붙인 인용이 위반으로 잡혀요"

    B3이 잡은 행만 "evidence는 원문 구절 그대로"로 다시 채점합니다. 이어 붙인 인용(오전 시연 5에서 49건)은 검사 규칙을 "두 조각이 모두 원문에 있으면 통과"로 정하거나, 인용을 한 곳에서만 하게 합니다.

??? fix "JSON의 한글이 \uXXXX로 보여요 · 사용 한도에 걸렸어요"

    `\uXXXX`는 정상입니다 — 검사는 `json.loads` 뒤에 비교합니다. 한도에 걸리면 앞 50행만 하거나 채팅 경로 · 짝 화면으로 이어 갑니다(풀리는 시각은 안내 메시지에) → [FAQ](../faq.md#q-usage-limit).

??? fix "AI가 d2_news_answer.csv(정답)를 열었어요"

    그 채점은 무효입니다. 새 대화에서 B2에 `b2-guard`를 덧붙여 다시 합니다.

<p class="tf-check"><time>15:35</time> 정답 20건이 열립니다 — 채점을 끝낸 뒤 04에서 받습니다</p>

<p class="tf-check"><time>15:45</time> 손 점검 — JSONL 100줄 · 검사 위반 0</p>

### 04. 평가 — 정답 20건(15:35)으로 MAE · ±2 · 일치율 (15:45–16:05) { #b-eval .step data-tool="Claude Code" data-phase="실습 B" }

**왜** 일관성은 정확성이 아닙니다 — 같은 점수를 늘 내도 틀릴 수 있습니다. 사람이 정답을 단 20건과 비교해 **AI 점수가 얼마나 맞는지** 숫자로 봅니다. JSONL + 정답 20건 → B4 → `eval.md`

!!! me "내가 할 일"

    1. **`d2-news` 창의 터미널에서** `uv run python tools/get_day_files.py 2` — 15:35 이후면 `d2_news_answer.csv`가 들어옵니다(메인 창에서 받으면 이 작업대에는 없습니다).
    2. **B4**를 보냅니다.
    3. 오차가 가장 큰 2건의 **원문을 읽고** 이유를 `eval.md` 끝에 한 줄씩 씁니다 — 국가 · 업황 기사인가, 점수가 가운데로 몰렸나, 근거를 잘못 읽었나. 8교시 공유 때 씁니다.

    | 지표 | 뜻 | 읽는 법 |
    |---|---|---|
    | **MAE** | AI 점수와 정답 차이의 절댓값 평균 | 1.0이면 평균 1점 차이 |
    | **±2 이내 비율** | 차이가 2점 이하인 건의 비율 | 실무 허용 오차 안의 비율 |
    | **라벨 일치율** | severe · high · watch · low가 같은 비율 | 경보 단위의 정확도 — 다수 범주(low)에 속기 쉽습니다 |

[정답 20건 받기(15:35 이후)](../downloads/day2/d2_news_answer.csv){ .md-button download data-tf-open="2026-10-15T06:35:00Z" } — 채팅 경로 · CLI가 막혔을 때

!!! prompt "프롬프트 B4 — 정답 20건과 비교"

    --8<-- "labs/day2/prompts.md:b4"

!!! ai "AI가 하는 일"

    `news_id`로 정답 20건과 내 점수를 잇고 세 숫자를 계산하는 코드를 실행합니다(허락 창 1–2번). `eval.md`에 숫자와 **오차가 가장 큰 2건**(원문 · 내 점수 · 정답 · 이유 한 줄)을 씁니다.

<figure class="result" markdown="span">
  ![프롬프트 v1 평가 보고서의 지표 표와 혼동행렬](../assets/screens/d2-eval-confusion.png){ loading=lazy }
  <figcaption>평가 보고서의 예(오전 시연 5 — 골든셋 30건 · 지표가 더 많습니다). 어디서 틀리는지가 보입니다</figcaption>
</figure>

!!! ok "확인"

    - [ ] `eval.md`에 MAE · ±2 이내 비율 · 라벨 일치율
    - [ ] 오차 큰 2건의 원문을 **내가** 읽고 원인을 한 줄씩 적었다

    숫자는 사람마다 다른 것이 정상입니다(정답 20건의 점수는 0–10에 넓게 퍼져 있습니다). 나쁘면 실패가 아니라 **프롬프트 v2를 만들 이유**입니다 → 더 해 보기 ②.

??? fix "정답 파일이 없다고 해요"

    15:35 전이거나, 메인 창에서 받아 이 작업대에 없는 것입니다. **`d2-news` 창** 터미널에서 다시 받습니다. 시각이 지났는데 `[열기 전]`이면 PC 시계를 보고 `--now`를 붙입니다.

??? fix "대조되는 건이 0이에요"

    `news_id`로 잇게 합니다. 정답 20건은 모두 앞 100행 안에 있습니다.

### 05. 융합 — 30일 창 집계 → LEFT JOIN → 특성표 (16:05–16:30) { #b-join .step data-tool="Claude Code" data-phase="실습 B" }

**왜** 뉴스를 **바이어 × 기준일 한 줄**로 모아 정제 표 옆에 붙입니다 — 기준일 **이전** 30일 기사만. 9월 기사가 섞이면 특성에 미래가 들어간 것입니다. JSONL + `d2_buyers_clean.csv` + `buyer_features_raw`(08-31) → B5 → `d2_end_features.csv` → 규칙 8칸 · 데이터 사전

!!! me "내가 할 일"

    1. **B5**에 **결과 열**(`b5-columns`)을 이어 붙여 보냅니다.
    2. `workbench/day2/outputs/d2_end_features.csv`를 열어 150행 · 열 순서를 봅니다.
    3. `b5-rule8`로 규칙 문서 **8칸(뉴스 창)**을 채웁니다.
    4. `b5-dict`로 데이터 사전에 새 열 7개를 더한 뒤, **'시점 점검' 칸은 내가** 씁니다 — 그 열이 기준일 이전 정보만으로 만들어졌는지.

!!! prompt "프롬프트 B5 — 30일 창 집계와 LEFT JOIN"

    --8<-- "labs/day2/prompts.md:b5"

???+ prompt "`b5-columns` · B5 덧붙임 — 결과 32열(권장)"

    --8<-- "labs/day2/prompts.md:b5-columns"

!!! prompt "`b5-rule8` · 이어서 — 규칙 문서 8칸(뉴스 창)"

    --8<-- "labs/day2/prompts.md:b5-rule8"

!!! prompt "`b5-dict` · 이어서 — 데이터 사전에 새 열(시점 점검은 비워 둔다)"

    --8<-- "labs/day2/prompts.md:b5-dict"

!!! ai "AI가 하는 일"

    창 `(2026-08-01, 2026-08-31]`의 기사만 바이어별로 **먼저 집계**(건수 · 평균 · 최솟값 · 위험지수)한 뒤 정제 표에 `buyer_id`로 LEFT JOIN하고, `buyer_features_raw`의 기준일 08-31 행에서 연체 금액(USD 환산) · 누적 연체일을 붙입니다. 뉴스가 없는 바이어는 평균 5 + `no_news_flag=1`. 끝에 **9월 기사 0건 · 150행 · ID 중복 0** 검사 줄을 출력합니다(허락 창 2–3번).

<figure markdown="span">
  ![기준일 08-31까지 알 수 있던 정보(초록)와 9월에 생긴 정보(빨강)를 나눈 시간선](../assets/diagrams/d2-pit-timeline.png){ loading=lazy }
  <figcaption>창은 8월 1일 초과 · 8월 31일 이하 — 9월 기사는 정답 쪽(<code>late_30d</code>)의 시간입니다</figcaption>
</figure>

<figure markdown="span">
  ![INNER JOIN · LEFT JOIN · 키 중복 시 행 폭발을 비교한 그림](../assets/diagrams/d2-join-three.png){ loading=lazy }
  <figcaption>150행 ⋈ 뉴스 집계 → LEFT는 150행 그대로(뉴스 없는 곳은 5 + 플래그) · 집계 전에 붙이면 1:N으로 행이 불어납니다</figcaption>
</figure>

<figure class="result" markdown="span">
  ![바이어별 30일 뉴스 특성 CSV와 아래 터미널의 검증 줄 — 창 안 기사 46건, 바이어 37곳, 창 밖 기사 0건](../assets/screens/d2-news-features.png){ loading=lazy }
  <figcaption>30일 창 집계의 예(오전 시연 5의 뉴스 특성 37곳) — 아래 검증 줄이 창 · 건수 · 중복을 한 번에 확인합니다</figcaption>
</figure>

!!! ok "확인"

    - [ ] `d2_end_features.csv` **150행 · 32열** · `buyer_id` 첫 열 · `late_30d` 끝 열 · ID 중복 0
    - [ ] 검사 줄에 창 안의 9월 기사 **0건**
    - [ ] 규칙 문서 8칸 · 데이터 사전 새 열 7개 + 내가 쓴 '시점 점검'

??? fix "결합 뒤 159행이에요"

    기사를 바이어별로 **집계하기 전에** 조인했습니다(37곳에 기사 46건 → 9행 늘어남). 먼저 집계하게 합니다.

??? fix "300행이에요"

    `buyer_features_raw`의 두 기준일(02-28 · 08-31)을 모두 붙였습니다. **08-31만** 씁니다(`b5-columns`).

??? fix "창 안 기사 수가 46이 아니에요(86 · 40 등)"

    9월 기사가 섞였거나 기준일을 09-30으로 잡았습니다. 창 조건을 확인하고, AI가 `ref_window` 열로 창을 골랐다면 **`date` 열로 다시 세어** 46건인지 대조하게 합니다.

??? fix "late_30d_x · late_30d_y가 생겼어요 · 엔화 바이어 overdue_usd가 100배예요"

    실습 A 표의 `late_30d`만 남깁니다(두 시트 값은 같습니다). 엔화 환율은 100엔 단위라 ÷100 합니다.

??? fix "d2_buyers_clean.csv가 없어요"

    worktree를 실습 A 머지 전의 `main`에서 만들었습니다. `main`을 pull한 뒤 worktree를 다시 만들거나 `d2-clean`에서 만듭니다. 그래도 없으면 손을 드세요 — 강사가 이어 갈 정제 표를 드립니다.

<p class="tf-check"><time>16:30</time> 확인표 — 슬라이드 d2-73이 화면에 뜹니다</p>

### 06. 기록 — 특성 사전 갱신 → 커밋 → PR (16:30–16:50) { #b-pr .step data-tool="Claude Code, GitHub" data-phase="실습 B" }

**왜** 오늘 결과를 PR로 올리고, 확인한 값과 오차 원인을 본문에 남깁니다. 평가 숫자는 사람마다 다르니 **구조**가 맞는지 봅니다. 머지는 8교시에 합니다. 확인표 대조 → 커밋 → push → PR(base `main`)

??? ok "실습 B 확인표 — 슬라이드 d2-73(내 결과를 만든 뒤 펼칩니다)"

    | 확인 | 기대값 |
    |---|---|
    | 채점 결과 | 100줄 = 입력 100행 · 형식 위반 0 |
    | 30일 창 | 기사 46건 · 바이어 37곳 · 9월 기사 0건 |
    | 결합 결과 | 150행 · buyer_id 첫 열 · late_30d 끝 열 · ID 중복 0 |
    | 뉴스 평균 | news_sent_0_10_30d ≈ 5.4(내 점수에 따라 조금 다름) |
    | B001 | 뉴스 0건 → 5.0 · no_news_flag 1 |
    | 평가 | MAE · ±2 비율 · 일치율 + 오차 원인 2건 |

!!! me "내가 할 일"

    1. 16:30 확인표를 펼치고 **`b-check`**로 내 파일에서 계산한 값과 나란히 놓습니다 — 같은 표에 **엑셀 검산본**(`d2_excel_check.xlsx`의 '확인표_B' 시트: 창 안 기사 · 바이어 수를 엑셀 수식으로 센 값) 열도 붙습니다.
    2. 소스 제어에서 바뀐 파일을 훑습니다 — 키 · 실데이터 · 기사 본문 전체가 없어야 합니다.
    3. **`b-commit`**으로 이번에 만든 파일만 커밋 · push합니다(받은 파일 사본은 빼고, B4 · B5에서 AI가 만든 **평가 · 결합 스크립트는 넣고** — 숫자를 만든 코드입니다). 직접 하려면 소스 제어에서 파일을 골라 Commit → Publish Branch.
    4. **Compare & pull request** → base **`main`** → 본문에 무엇을 했나 · 확인한 값(150행 · 9월 0건 · 평가 숫자) · 오차 큰 2건 → **Create pull request**. 머지는 8교시에.

!!! prompt "`b-check` · 확인표 대조 — 내 값 · 엑셀 검산본 · 기대값을 한 표로(고치지 않음)"

    --8<-- "labs/day2/prompts.md:b-check"

!!! prompt "`b-commit` · 커밋 · push · PR 본문 초안(머지는 하지 않음)"

    --8<-- "labs/day2/prompts.md:b-commit"

!!! ai "AI가 하는 일"

    확인표 여섯 줄을 내 파일에서 다시 계산하고(창 기사 수는 `date` 열로) 엑셀 검산본 값과 함께 '같음?' 표로 보여 줍니다. `b-commit`은 파일 목록을 보여 주고 커밋 · push(허락 창 2–3번 — 목록에 `workbench/day2/data/`의 받은 사본이 없는지, push 대상이 `d2-news`인지 읽습니다) 후 PR 본문 초안을 씁니다.

!!! ok "확인"

    - [ ] 확인표 대조 표가 구조 줄(1 · 2 · 3 · 5)에서 '같음'이다
    - [ ] PR이 열렸고(base `main`) 본문에 확인한 값과 오차 원인 2건이 있다

??? fix "PR의 base가 d2-clean으로 잡혀요"

    PR 화면 위쪽의 base를 **`main`**으로 바꿉니다.

??? fix "받은 파일 사본까지 커밋하려고 해요"

    넣어도 문제는 없지만 PR이 커집니다. `b-commit`처럼 `workbench/day2/data/`에서는 `데이터사전.md`만 넣게 합니다.

??? fix "evidence 인용을 저장소에 올려도 되나요"

    20단어 이내 인용은 괜찮습니다. 기사 본문 전체는 올리지 않습니다(오늘 뉴스는 합성 데이터지만 습관으로).

<p class="tf-check"><time>16:50</time> 손 점검 — PR 열림 · <code>수집점검.md</code> · 데이터 사전</p>

## 8교시 · 두 작업을 main으로 합치기 {#period8}

<div class="tf-phase" markdown>

<span class="tf-eyebrow">슬라이드 d2-74 · 8교시 · 17:00–17:20 · 약 5분씩 · Claude Code · Git · GitHub</span>

**목표** 오늘 결과를 main에 모으고 이력을 확인한다

- **01** PR B 셀프 리뷰 4가지 — 행 수 · 테스트 · 비밀값 · 규칙 문서
- **02** 짝이 코멘트 1개 → 반영 커밋
- **03** 머지 — 충돌이 나면 Claude Code에게 'main을 반영해 충돌을 풀고 diff를 보여 줘' → 확인 후 머지
- **04** worktree 정리(소스 제어 › Worktrees) → git log --graph --oneline으로 오늘 이력

**산출물** main에 오늘 결과 전부 + PR 2개 이력 · **시간** 20분

</div>

오전 시연 1의 마지막 장면을 각자 재현합니다. 인쇄본에는 단계별 시각이 없습니다 — 약 5분씩입니다.

### 01. PR B 셀프 리뷰 4가지 — 행 수 · 테스트 · 비밀값 · 규칙 문서 { #p8-review .step data-tool="Claude Code, GitHub" data-phase="8교시" }

!!! me "내가 할 일"

    1. PR B의 **Files changed**를 내가 먼저 훑습니다.
    2. `p8-review`로 네 가지를 점검 표로 받아 내 눈과 맞춰 봅니다. **테스트**는 두 가지로 봅니다 — `uv run pytest -q`(실습 A 테스트가 그대로 통과) + `validate_scores.py` 위반 0.

!!! prompt "`p8-review` · 셀프 리뷰 4가지 — 점검 표만(고치지 않음)"

    --8<-- "labs/day2/prompts.md:p8-review"

!!! ok "확인"

    - [ ] 150행 · 테스트 통과 · 위반 0 · 키 / 실명 / 기사 본문 없음 · 규칙 8칸과 사전 갱신

### 02. 짝이 코멘트 1개 → 반영 커밋 { #p8-comment .step data-tool="GitHub, Claude Code" data-phase="8교시" }

!!! me "내가 할 일"

    1. 짝의 PR B에 코멘트를 **하나** 남깁니다(실습 A 06과 같은 방법 — Files changed의 줄 왼쪽 `+`).
    2. 받은 코멘트를 반영합니다 — 코멘트 글을 GitHub에서 복사해 `d2-news` 창의 Claude Code에 `review-fix`로 붙여 보냅니다(Claude Code는 PR 코멘트를 직접 못 읽는 경우가 많습니다). 반영 커밋을 push하면 PR에 저절로 붙습니다.

??? prompt "`review-fix` · 짝의 리뷰 코멘트 반영 — 코멘트 글을 붙여 넣는다"

    --8<-- "labs/day2/prompts.md:review-fix"

!!! ok "확인"

    - [ ] 반영 커밋이 PR B에 붙었다

### 03. 머지 — 충돌이 나면 Claude Code에게 'main을 반영해 충돌을 풀고 diff를 보여 줘' → 확인 후 머지 { #p8-merge .step data-tool="GitHub, Claude Code" data-phase="8교시" }

!!! me "내가 할 일"

    1. PR 화면 아래 **Merge pull request → Create a merge commit → Confirm**. 스쿼시 · 리베이스를 고르면 그래프에 갈래가 보이지 않습니다.
    2. 충돌이 나면 `d2-news` 창의 Claude Code에 **B6**을 보내고, **해결된 diff를 내가 읽습니다.**
    3. diff에 동의하면 `push해 줘`(또는 소스 제어 **Sync Changes**) — B6은 합친 결과를 내 PC에만 두고 끝나는 경우가 많습니다(미리 해 본 실행도 그랬습니다). PR 화면이 'This branch has no conflicts'로 바뀌면 1처럼 머지합니다.

!!! prompt "프롬프트 B6 — 충돌이 날 때(슬라이드 문장 그대로)"

    --8<-- "labs/day2/prompts.md:b6"

??? prompt "더 구체적으로 — 두 변경을 모두 살리고 테스트 뒤 push"

    --8<-- "labs/day2/prompts.md:b6-long"

!!! ok "확인"

    - [ ] PR 두 개가 머지됐고, 파일에 충돌 표식(`<<<<<<<` · `=======` · `>>>>>>>`)이 없다(충돌을 풀었다면 push까지 했다)

### 04. worktree 정리(소스 제어 › Worktrees) → git log --graph --oneline으로 오늘 이력 { #p8-cleanup .step data-tool="VS Code, Git" data-phase="8교시" }

!!! me "내가 할 일"

    1. `d2-news` 새 창을 닫습니다(Windows는 창을 먼저 닫아야 폴더를 지울 수 있습니다).
    2. 메인 창의 소스 제어 › **Worktrees**에서 `d2-news` 작업대를 삭제합니다.
    3. 터미널에서 `git switch main` · `git pull` · `git log --graph --oneline -n 12`로 두 갈래가 `main`으로 합쳐진 그래프를 봅니다.

<figure class="result" markdown="span">
  ![git log --graph 출력 — 두 갈래가 병합 커밋으로 main에 합쳐지는 그래프](../assets/screens/d2-git-graph.png){ loading=lazy }
  <figcaption>갈래 두 개가 <code>main</code>으로 합쳐진 이력의 예(오전 시연 1) — 내 그래프에서는 커밋 이름이 다릅니다</figcaption>
</figure>

!!! ok "확인"

    - [ ] `main`에 `workbench/day2/outputs/d2_end_features.csv`가 있다
    - [ ] 그래프에 두 갈래와 병합 커밋 · 이슈가 닫혔다

??? fix "worktree 삭제가 거부돼요"

    받은 파일 사본(추적 안 된 파일) 때문입니다. 같은 파일이 원래 폴더에도 있으니 지워도 됩니다 — 터미널에서 `git worktree list`로 경로를 보고 `git worktree remove --force <경로>`.

??? fix "worktree를 지우지 않으면 무엇이 남나요"

    폴더와 그 안의 `.venv`가 디스크를 차지하고, 같은 브랜치를 다른 폴더에서 다시 꺼낼 때 막힙니다.

<p class="tf-check"><time>17:20</time> 이력 확인 — 그래프 · PR 2개 머지 · 이슈 닫힘</p>

**17:20–17:35 결과 공유** — 두세 분이 그래프 화면 · 평가 숫자 · 오차 원인 하나를 보여 줍니다. 이어서 정리 · 자가 점검 · 내일 예고는 [2일차 개요](index.md#tomorrow)에 있습니다.

## 완료 기준 {#checkpoint}

<div class="tf-checklist" data-title="실습 B · 8교시에서 남길 것" markdown>

- [ ] `workbench/day2/rules/수집점검.md` 5칸과 결론 하나
- [ ] `news_scored.jsonl` 100줄 · `scripts/validate_scores.py` 위반 0
- [ ] `eval.md`에 MAE · ±2 이내 비율 · 라벨 일치율 + 오차 원인 2건
- [ ] `d2_end_features.csv` 150행 · 32열 · `buyer_id` 첫 열 · `late_30d` 끝 열 · 창 안의 9월 기사 0건
- [ ] 규칙 문서 8칸 · 데이터 사전 새 열 7개(시점 점검은 내가)
- [ ] PR B 머지 · worktree 정리 · `main`에 오늘 결과 전부

</div>

!!! late "늦었다면"

    15:45에 JSONL이 100줄이 안 되면 **앞 50행만** 채점하고 04로 갑니다. 16:30에 특성표가 없으면 05만 하고 06의 PR을 엽니다. 실습 A 정제 표가 없거나 채점을 끝내지 못했으면 손을 드세요 — 강사가 이어 갈 파일을 드립니다. 내일 아침에는 모두 같은 기준 특성표로 시작합니다.

## 다 했으면 — 내 손으로 넓혀 보기 {#extend}

오늘 이론(골든셋 · 프롬프트 버전 · 시점 정합성 · 구조화 출력)을 하나 골라 **AI가 어디까지 하는지** 직접 재 봅니다. 시작 프롬프트는 [프롬프트 → 더 해 보기](../prompts/day2.md#more)에 있습니다.

<div class="grid cards tf-ext" markdown>

-   <span class="tf-level">기본 · 15분 · ChatGPT · Claude 웹</span>

    **두 번째 채점자 — 일관성 ≠ 정확성**

    같은 50건(`news_rows_001-050.csv`)을 ChatGPT와 Claude 웹에서 같은 규칙으로 채점하고, 두 JSONL을 Claude Code에 줘 코헨 κ와 모델별 MAE를 봅니다. 시작: [bx1](../prompts/day2.md#bx1)

-   <span class="tf-level">응용 · 15분 · Claude Code</span>

    **프롬프트 v2 — 한 번에 한 줄**

    오차 큰 2건의 공통점으로 규칙 **한 줄만** 고친 v2를 같은 20건으로 다시 잽니다. 고칠 때 본 표본으로 다시 재면 낙관적 — 101–110행 10건을 내가 직접 판정해 새 표본으로 한 번 더. 시작: [bx2](../prompts/day2.md#bx2)

-   <span class="tf-level">응용 · 10분 · Claude Code</span>

    **신용평가 코멘트 점수화**

    가상 코멘트 2건(한국어 등급 하향 · 영어 Watch Negative)을 덧붙임 규칙과 스키마(`rating_action` · `outlook`)로 채점합니다 — 파일은 위 카드의 `credit_notes/`. 날짜가 기준일 뒤라 특성표에는 넣지 않습니다. 시작: [bx3](../prompts/day2.md#bx3)

-   <span class="tf-level">도전 · 15분 · Claude Code</span>

    **다음 기준일 판 — 2026-09-30**

    앞 100행의 9월 기사 40건으로 창 `(08-31, 09-30]` 뉴스 열을 만들고, 08-31 판과 둘 다 뉴스가 있는 바이어의 위험지수 변화를 봅니다 — 10월 기사 0건 검사 줄까지. 시작: [bx4](../prompts/day2.md#bx4)

-   <span class="tf-level">도전 · 20분 · Claude Code · API 키</span>

    **구조화 출력으로 300건**

    API 키가 있으면 스키마(`news_score.schema.json`)로 형식을 강제해 300건을 채점합니다. 키는 환경변수로만, 실행 전에 예상 비용부터 — 오전 '300건 채점의 비용' 장과 견줍니다. 시작: [bx5](../prompts/day2.md#bx5)

</div>

<figure class="result" markdown="span">
  ![뉴스 300건 채점 진행 화면 — 300/300 성공, 토큰 합계와 추정 비용, 결과 JSONL 앞 5줄](../assets/day2/d2-api-batch.png){ width="680" loading=lazy }
  <figcaption>300건을 스크립트로 채점한 기록의 예(오전 시연 5 리허설) — 토큰 합계 · 추정 비용이 함께 남습니다</figcaption>
</figure>

## 채팅 경로 — Claude Code를 못 쓸 때 {#chat-path}

Claude Code를 못 쓰면 **Claude 웹**(코드 실행) 또는 **ChatGPT**(데이터 분석)에 파일을 **첨부**해 같은 결과에 도착합니다. worktree 대신 GitHub 웹에서 `d2-news` 브랜치를 만들어 올립니다.

1. 위 카드에서 `news_score_v1.md` · `news_rows_001-050.csv` · `news_rows_051-100.csv` · `수집점검.md` · `데이터사전.md`를 받습니다. 형식을 먼저 시험하려면 `news_warmup_10.txt`(10건).
2. **수집 점검(02)**은 그대로 Claude 웹에서 합니다.
3. **채점(03)**: `news_score_v1.md`와 `news_rows_001-050.csv`를 첨부하고 아래 프롬프트를 보냅니다. 이어서 `news_rows_051-100.csv`를 첨부해 "같은 규칙으로 51–100행을 이어 붙인 news_scored.jsonl(100줄)로 내려받게 해 줘". 답이 끊기면 `계속`.
4. **검사 · 평가 · 결합(03–05)**: 같은 대화에 `news_scored.jsonl` · `d2_news_answer.csv`(15:35 이후) · 실습 A의 `d2_buyers_clean.csv` · `d2_start.xlsx`를 첨부하고 아래 두 번째 프롬프트를 보냅니다.
5. **올리기(06)**: 브랜치 선택에 `d2-news` 입력 → **Create branch** → `workbench/day2/outputs/`에 **Add file → Upload files** → **Commit directly to the `d2-news` branch** → **Compare & pull request**. 머지는 8교시에.

??? prompt "채팅 경로 — 채점(첨부한 50행을 규칙대로)"

    --8<-- "labs/day2/prompts.md:chat-b"

??? prompt "채팅 경로 — 검사 · 평가 · 결합을 코드 실행으로"

    --8<-- "labs/day2/prompts.md:chat-b-check"

!!! warning "GitHub 웹의 Upload files는 .gitignore를 보지 않습니다"

    고른 파일을 그대로 올립니다. 올리기 전에 파일 이름과 내용을 봅니다 — 키 · 실데이터 · 기사 본문은 올리지 않습니다. 쓰는 AI의 '모델 개선(학습)' 설정은 끄고 시작합니다 → [사전 준비](../setup.md#ai-training).

## 막힐 때 {#troubleshooting}

| 증상 | 이렇게 해 보세요 |
|---|---|
| 새 창의 Claude Code가 `data/checkpoints/…` 파일이 없다고 한다 | 정상입니다 — 새 작업대에는 받은 파일이 없습니다. B1(또는 `uv run python tools/get_day_files.py 2`)을 새 창에서 다시 |
| `git status`에 `workbench/day2/data/…`가 '추적 안 됨'으로 여러 줄 | 받은 파일의 작업 사본입니다. 정상이고 커밋하지 않아도 됩니다 |
| 허락 창이 너무 자주 뜬다 | 명령을 읽고 `1 Yes`, 모르는 명령이면 `No` 후 "이 명령이 뭐 하는 거야?" → [FAQ](../faq.md#q-permission) |
| `d2_news_answer.csv`가 `[열기 전]` | 15:35 뒤 `d2-news` 창에서 다시 받습니다. 시각이 지났으면 PC 시계 · `--now` |
| 결합 뒤 150행이 아니다 | 뉴스를 바이어별로 **먼저 집계**한 뒤 `buyer_id`로 LEFT JOIN했는지 봅니다 |
| 9월 기사가 섞인다 | 창 조건 `(2026-08-01, 2026-08-31]` — 8월 31일 이하만 |
| 머지 때 충돌이 난다 | B6으로 맡기고 **해결된 diff를 읽은 뒤** 머지 → [FAQ](../faq.md#q-conflict) |
| 사용 한도에 걸렸다 | 앞 50행만 · 채팅 경로 · 짝 화면 → [FAQ](../faq.md#q-usage-limit) |
