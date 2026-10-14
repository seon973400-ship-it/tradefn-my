# CLAUDE.md — tradefin-kit-T{조}

- 데이터: 가상 한빛정밀 데이터만 · 실명 · 이메일 · 키 금지
- 흐름: data/ → app/pipeline/ → out/ → docs/ · sop/ · roi/
- 숫자는 스크립트로 계산, 결과 끝에 검산 3줄
- 한도 변경 · 선적 보류 · 보험 통지 · 바이어 발송 = "승인 필요"만
- 작업 하나 = 이슈 하나 = 브랜치 하나 = PR 하나
- 커밋 메시지: 첫 줄 "무엇: …", 빈 줄, "왜: …" — 빈 줄이 있어야 git log 첫 줄이 깔끔하다

## 환경
- 처음 한 번 `uv sync` — `.venv`(Python 3.13)를 `uv.lock` 그대로 만든다. 실행은 `uv run python app/pipeline/…`.
- 그날 파일 받기: `uv run python tools/get_day_files.py 6` (공개 시각마다 다시 실행하면 새로 공개된 파일만 더 온다).
- 답은 한국어, 표는 Markdown 표로 쓴다.

## 우리 팀 규칙 (10시 첫 5분에 3줄을 적는다)
- {예: data/의 원본은 고치지 않고 out/에 새 파일로 쓴다}
- {…}
- {…}
