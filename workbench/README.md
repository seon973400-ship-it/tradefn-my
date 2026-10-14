# workbench — 내 작업 기록 폴더

과정 템플릿으로 만든 **내 저장소**에서, 날마다 만든 규칙 · 프롬프트 · 결과 파일을 커밋해 두는 곳입니다.
'언제 · 무엇을 · 왜' 바꿨는지가 커밋 이력으로 남습니다. 과정 저장소의 이 폴더는 빈 틀이고, 2일차 서랍에만 시작 양식이 들어 있습니다(`rules/정제규칙.md` · `rules/수집점검.md` · `prompts/news_score_v1.md` · `data/데이터사전.md` · `schemas/news_score.schema.json`).

## 구조

```text
workbench/
  day1/ … day6/        일차마다 같은 서랍 4개
    rules/             사람이 정한 규칙(.md) — 정제 규칙 · 등급 컷 · 경보 기준 · AI 사용 규칙
    prompts/           실제로 쓴 프롬프트 — 이름 + 판 번호, 고칠 때마다 커밋
    data/              그날 받은 파일의 작업 사본 · 데이터 사전
    outputs/           그날 결과 파일(CSV · 엑셀 · 보고서 · 차트)  ← 'outputs 폴더'는 이곳
  day1/notebooks/      1일차 EDA 노트북 (차트 PNG는 day1/outputs/charts/)
  day2/tests/          2일차부터 쓰는 검증 테스트(pytest) — `uv run pytest -q`가 이 폴더의 테스트를 돌립니다
```

- `.gitkeep`은 빈 서랍이 GitHub 화면에 보이게 하는 빈 파일입니다. 그대로 두어도 됩니다.
- 그날 파일은 `uv run python tools/get_day_files.py N`이 받고, 고쳐 쓸 데이터 파일은 `data/` 서랍에 **작업 사본**도 만듭니다.
  원본(`data/`, `labs/`)은 고치지 않고, 고쳐 쓸 파일은 이 사본에서 다룹니다(프롬프트 · 양식 · 완성본 · 비교 기준은 원본 자리에서 읽습니다).

## 커밋 메시지는 두 줄

```text
1일차: 결제조건 표기를 표준 코드 7개로 묶음
왜: 같은 결제방식이 60가지로 흩어져 있어 집계가 안 됨
```

## 올리면 안 되는 것

이 저장소는 **공개**가 기본입니다. 비공개로 바꿔도 아래 규칙은 같습니다.

- 회사 실데이터 — **익명화본도 포함**. 회사 문서, 고객 · 바이어 실명
- API 키 · 비밀번호 · `secrets.toml` · `.env`
- 이름 · 이메일 · 전화 · 계좌 같은 개인정보
- 실명 · 회사명이 들어간 파일 이름이나 커밋 메시지

`.gitignore`가 `secrets.toml` · `.env` · `private/` 폴더 · 이름에 `_private`가 든 파일을 막아 주지만,
**GitHub 웹 화면의 Upload files는 `.gitignore`와 관계없이 고른 파일을 그대로 올립니다.** 올리기 전에 파일을 한 번 더 봅니다.
실수로 올렸다면 파일을 지우는 것으로 끝나지 않습니다(커밋 이력에 남습니다). 바로 강사에게 알리고, 키였다면 키부터 교체합니다.

## 웹 화면만으로 하는 법

| 하고 싶은 것 | 누르는 곳 |
|---|---|
| 파일 올리기 | 서랍 폴더로 들어가 **Add file** → **Upload files** → 끌어다 놓기 → 메시지 두 줄 → **Commit changes** |
| 파일 고치기 | 파일을 열고 연필 아이콘(**Edit this file**) → 고치기 → **Commit changes** |
| 바뀐 이력 보기 | 파일 화면의 **History** → 커밋을 누르면 diff(빨강 = 지운 줄, 초록 = 더한 줄) |

버튼 이름은 GitHub가 바꿀 수 있습니다. 자세한 순서는 과정 사이트 [2일차 실습 A의 채팅 경로](https://brainini.github.io/tradefin-ai-2026/day2/lab-a.html#chat-path)에 있습니다(이슈 → 브랜치 → 업로드 → PR).
