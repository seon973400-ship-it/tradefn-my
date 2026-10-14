# tradefin-ai-2026 — 생성형 AI 기반 무역 금융 리스크 최적화 과정 실습 저장소

6일 동안 **AI로 일하는 법**을 손으로 익히는 실습 과정의 **과정 사이트 원고, 실습 파일, (가상) 한빛정밀(주) 합성 데이터**를 담은 저장소입니다.
무역 금융은 그 방법을 연습하는 주제입니다. 도구는 **ChatGPT · Claude · Claude Code**(VS Code 확장)와 **Git · GitHub**입니다.
무역금융 판단은 수강생 여러분이 하고, 이 저장소는 AI로 읽고 · 검증하고 · 정리하고 · 서비스로 만드는 방법을 손으로 익히도록 돕습니다.

> (가상) 한빛정밀(주)과 Halden은 교육용 가상 회사이며 실존 기업과 무관합니다.
> 이 저장소의 어떤 자료도 투자·여신 판단 자료가 아닙니다.

## 과정 정보

| 항목 | 내용 |
|---|---|
| 과정 | 생성형 AI 기반 무역 금융 리스크 최적화 과정(재직자) |
| 기간 | 2026-10-14(수) ~ 10-21(수), 주말 빼고 6일 · 매일 09:00–18:00 |
| 강사 | 한태구 |
| 과정 사이트 | [https://brainini.github.io/tradefin-ai-2026/](https://brainini.github.io/tradefin-ai-2026/) (GitHub Pages) |
| 문의 | 과정 오픈채팅 |

매일 오전에는 AI 개념과 방법론을 **시연**으로 보고, 오후에는 그 시연을 작게 · 조금 다르게 **내 저장소에서 직접** 해 봅니다. 결과는 파일과 커밋(PR)으로 남깁니다.

| 일차 | 날짜 | 주제 | AI로 일하는 법 | 오늘의 파일 |
|---|---|---|---|---|
| 1 | 10/14(수) | 무역 금융 AI 트렌드 및 글로벌 바이어 데이터 탐색 | 원리 · 도구 · 환경 · 데이터 탐색 | 내 저장소의 `data/day1/` ([1일차 페이지](docs/day1/index.md)) |
| 2 | 10/15(목) | 금융/재무 데이터 전처리 및 리스크 평가지표 변수화 | 협업(브랜치 · PR · worktree) · 정제 · 특성 · SQL · 텍스트 점수화 | `get_day_files.py 2` · 사이트 '파일 받기' |
| 3 | 10/16(금) | AI 기반 대금 결제 연체 및 바이어 부도 리스크 예측 | 확률 · 검증 · 비용 임계값 · 설명 · 재현 | `get_day_files.py 3` · 사이트 '파일 받기' |
| 4 | 10/19(월) | 수출채권 회수 전략 최적화 및 조기 경보 시뮬레이션 | 최적화 · 시뮬레이션 · 경보 자동화 · 보고서 파이프라인 | `get_day_files.py 4` · 사이트 '파일 받기' |
| 5 | 10/20(화) | AI 금융 에이전트 및 채권 관리 종합 제어 대시보드 구축 | 웹 · API · 실시간 연동 · DB · RAG · 에이전트 | `get_day_files.py 5` · 사이트 '파일 받기' |
| 6 | 10/21(수) | 실전 적응력 고도화 및 자사 솔루션 도입 기획(해커톤) | 도입 기획 · 솔루션 킷(Git/GitHub) · 거버넌스 · ROI | 위기 카드 · 데이터 팩은 09:28 자동 공개 |

## 시작하기 — 1일차 오후에 모두 같은 출발점에서

1일차 오후(실습 A-1)에 전원이 이 저장소를 **템플릿**으로 **내 공개 저장소**를 만들고 첫 커밋을 올립니다. 개강 전에 GitHub 가입과 이메일 인증, VS Code · Git · uv 설치, Claude Code 확장 로그인을 끝내 주세요 → [사전 준비](docs/setup.md).

1. GitHub에 로그인한 뒤 이 저장소 첫 화면의 **Use this template → Create a new repository**를 누릅니다. Owner는 내 계정, 이름은 `tradefin-my-T{조}-{번호}`(예: `tradefin-my-T1-01`), 공개 범위는 **Public**입니다.
2. VS Code에서 **Git: Clone**으로 내 저장소를 받고, 폴더를 열어 '작성자 신뢰'를 누른 뒤 터미널에서 `uv sync` → `uv run python scripts/hello.py`로 환경을 확인합니다.
3. Claude Code 패널의 입력창 아래 **모드 표시**를 확인해 **Manual**(또는 Plan)로 바꾸고, 이미 들어 있는 `CLAUDE.md`에 내 업무 규칙을 더해 첫 커밋 · push 합니다.
4. 그날의 실습은 과정 사이트의 일차 페이지(실습 A · B)를 따릅니다. 오늘 쓸 파일은 내 저장소에 이미 있고, 둘째 날부터는 **아침 첫 명령** `uv run python tools/get_day_files.py N`(N = 일차)으로 그날 파일을 받습니다.

저장소를 만들 수 없거나 Claude Code를 쓸 수 없으면 과정 사이트의 채팅 경로(claude.ai · ChatGPT)와 `Codespaces`가 대신 길입니다. 못 끝낸 실습이 있어도 괜찮습니다 — 다음 날 아침 시작 파일로 바로 합류합니다.

바로가기: [사이트 홈 원고](docs/index.md) · [과정 소개](docs/course.md) · [사전 준비](docs/setup.md) · [1일차](docs/day1/index.md) · [이론 요약](docs/day1/theory.md) · [실습 A](docs/day1/lab-a.md) · [실습 B](docs/day1/lab-b.md) · [프롬프트 원문](labs/day1/prompts.md) · [데이터 설명](docs/data.md) · [FAQ](docs/faq.md)

## 저장소 지도

| 경로 | 무엇 |
|---|---|
| `CLAUDE.md` | Claude Code가 매번 먼저 읽는 규칙 파일 — 폴더 구조와 일하는 방식이 적혀 있고, 내 업무 규칙을 더해 씁니다 |
| `pyproject.toml` · `uv.lock` · `.python-version` | 수강생 실습 환경(uv 프로젝트, Python 3.13) — `uv sync` 한 줄로 모두 같은 환경 |
| `.vscode/` · `.devcontainer/` | VS Code 권장 확장 · 설정 / 설치가 막힌 PC를 위한 Codespaces 설정 |
| `scripts/` | 계산 · 정리 코드를 남기는 곳(`hello.py`로 환경 확인) |
| `workbench/` | **개인 작업 폴더** — 1일차 오후에 이 저장소를 템플릿으로 만든 개인 저장소에서 날마다 결과(규칙 · 프롬프트 · 데이터 사전 · 결과 파일 · 노트북)를 커밋하는 곳. 쓰는 법은 `workbench/README.md` |
| `labs/dayN/` | 일차별 실습 양식 · 프롬프트 원문(`prompts.md`) · 예제 스크립트와 테스트 |
| `data/` | `day1/` 1일차 배포 파일(바이어 스냅샷 · 인보이스 원장 · 해외 기업 보고서 발췌 `reports/` · SEC 비율표) · `checkpoints/` 1일차 체크포인트와 공용 환율(2일차부터의 파일은 `get_day_files.py N`이 이 폴더에 받는다) · `external/` FRED 환율 원본 캐시와 출처 표기(`ATTRIBUTION.md`) · `data_dictionary.xlsx` 데이터 사전 |
| `app/` · `rag/` | 5일차 Streamlit 상황판 원본 · 규정 챗봇 자료(규정 PDF · 질문 목록 · 평가 시트) |
| `kit_template/` | 6일차 **팀 솔루션 킷 템플릿**의 원본(README 5항목 · data · app · sop · roi · docs · 이슈·PR 양식) — 강사가 `brainini/tradefin-kit-template`으로 공개합니다 |
| `agents/` | 강사용 LLM 관문 설정(선택) — 수강생은 쓰지 않습니다 |
| `tools/` | 그날 파일 받기(`get_day_files.py`) · 사이트 동기화·빌드 훅 · 외부 데이터 수집 · 차트용 글꼴 |
| `docs/` · `mkdocs.yml` · `.github/workflows/pages.yml` | 과정 사이트 원고(MkDocs Material)와 설정, 자동 배포(이 저장소에서만 돈다 — 템플릿 사본·fork에서는 건너뜀). 사이트에서 보는 것이 가장 편합니다 |
| `LICENSE` · `LICENSE-DATA.md` · `NOTICE.md` | 라이선스 전문(코드 MIT · 데이터·문서 CC BY 4.0)과 제3자 자료 출처 표기 |

## 데이터 위생

- 이 저장소의 실습 데이터는 전부 **합성 데이터**이거나 **공개 공시**입니다.
- 회사 실데이터(익명화본도), 고객사 실명, 담당자 이름·이메일·계좌, API 키는 이 저장소에도, 내 저장소에도, 포크에도 올리지 않습니다.
- **AI 대화창은 외부 채널입니다.** AI 서비스의 '모델 개선(학습)' 설정은 끄고 시작합니다. 자세한 규칙은 [데이터 위생 5원칙과 익명화 체크리스트](docs/setup.md#hygiene)에 있습니다. 회사 보안 규정이 있으면 그것이 우선입니다.

## 라이선스와 출처

Copyright (c) 2026 Taegu Han. 전문은 [`LICENSE`](LICENSE)(코드 · MIT) · [`LICENSE-DATA.md`](LICENSE-DATA.md)(데이터·문서 · CC BY 4.0, 제3자 자료의 이용 조건)에, 제3자 자료의 출처 표기는 [`NOTICE.md`](NOTICE.md)에 있습니다.

| 대상 | 조건 | 전문·자세히 |
|---|---|---|
| 코드(`tools/`, `labs/`의 노트북·수식, 사이트 설정·워크플로) | **MIT License** | [`LICENSE`](LICENSE) |
| (가상) 한빛정밀 합성 데이터 · Halden 가상 보고서 · 사이트 글 · 템플릿 · 프롬프트 원문 | **CC BY 4.0** — 출처를 밝히면 자유롭게 쓸 수 있습니다. 표기 예: "생성형 AI 기반 무역 금융 리스크 최적화 과정(한태구), CC BY 4.0" | [`LICENSE-DATA.md`](LICENSE-DATA.md) 1절 |
| SEC 공시 발췌(iRobot · Plug Power · Wolfspeed · Big Lots) | 미국 SEC EDGAR의 **공개 공시를 교육 목적으로 일부 발췌**했습니다. 원문의 저작권과 책임은 각 회사에 있고(CC BY 4.0을 붙이지 않음), 원문 링크는 [데이터 페이지](docs/data.md)의 '보고서 발췌' 표에 있습니다 | [`LICENSE-DATA.md`](LICENSE-DATA.md) 2절 · [`NOTICE.md`](NOTICE.md) |
| SEC 비율표(`real_buyers_ratios`) | SEC XBRL companyfacts API(data.sec.gov)에서 2026-10-01에 추출·계산 | 같음 |
| D&B Gorman 샘플 보고서 | **링크만** 제공합니다. PDF는 이 저장소·공유 드라이브·단체방에 올리지 않습니다 | 같음 |
| 환율(`data/external/`) | FRED H.10 — "Public Domain: Citation Requested". 인용 방법은 `data/external/ATTRIBUTION.md` | [`NOTICE.md`](NOTICE.md) |
| 글꼴(`tools/fonts/`) | NanumGothic, SIL Open Font License 1.1(`tools/fonts/OFL.txt`) | [`NOTICE.md`](NOTICE.md) |
| 외부 공개 데이터(UCI 등) | 아직 넣지 않았습니다. 넣을 때 원본 조건·DOI·조회일을 `data/external/ATTRIBUTION.md`에 적습니다 | [`LICENSE-DATA.md`](LICENSE-DATA.md) 3절 |

## 다시 만들기

### 과정 사이트

저장소 루트에서 실행합니다(Python 3.12 이상).

```bash
pip install -r requirements-docs.txt
python tools/sync_site_assets.py              # 수강생 파일을 docs/downloads/로 복사하고 '파일 받기' 표를 만든다
mkdocs serve                                  # http://127.0.0.1:8000 에서 미리 보기
mkdocs build --strict -d site                 # 정적 사이트를 site/에 만든다(경고가 하나라도 있으면 실패)
OFFLINE=true mkdocs build -d site_offline     # USB·file:// 배포판(검색까지 오프라인으로 동작)
```

- **배포**: GitHub 저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 한 번 정하면, `main`에 push할 때마다 `.github/workflows/pages.yml`이 파일 복사 → strict 빌드 → 배포를 합니다. Actions 탭의 **Run workflow**로 직접 돌려도 됩니다.
- `docs/downloads/`, `site/`, `site_offline/`은 빌드할 때마다 새로 만드는 결과물이라 커밋하지 않습니다(`.gitignore`).
- `tools/sync_site_assets.py`는 같은 저장소 `files` 브랜치의 수업 파일 색인(`_index.json`)대로 '파일 받기' 카드 · ZIP을 만듭니다(빌드는 그 브랜치를 `_files`로 받아 `--files-root _files`). 정답 원본 · 원천 경로가 섞이면 멈춥니다. 열기 시각이 있는 파일은 그 시각까지 카드가 잠겨 보입니다.

### 데이터

- 모든 합성 데이터는 고정 seed(`20261014`)로 만들었습니다. 같은 라이브러리 버전(`requirements.txt`)이면 같은 파일이 나오고, 파일별 SHA-256은 `data/checkpoints/_manifest.json`에 있습니다.
- 만드는 순서(자세한 설명은 `tools/README.md`):

    ```bash
    pip install -r requirements.txt
    python tools/fetch_external.py fred     # 1) FRED 환율 캐시(네트워크는 여기서만)
    python tools/generate_data.py           # 2) 원천 세계 → data/raw/
    python tools/build_checkpoints.py       # 3) Day별 배포 파일 · 체크포인트 · 데이터 사전
    python tools/validate_data.py           # 4) 검사(실패하면 종료코드 1)
    ```

    3일차 모델 · 4일차 한도 · 5일차 원장 · 6일차 해커톤 팩 같은 일차별 생성기는 `tools/README.md`의 순서를 따릅니다.

- **과정 중에는 이 순서를 이 저장소만으로 돌릴 수 없습니다.** 모든 단계가 생성기 설정(`tools/config.yaml`)을 읽는데, 이 설정과 일부 생성기, 원천(`data/raw/`)에는 실습의 정답(숨은 등급·심어 둔 결함·시나리오)이 들어 있어 **과정이 끝난 뒤(2026-10-21 19:00)** `files` 브랜치에 자동으로 올라갑니다. 그 전에 쓸 데이터는 `data/day1/`·`data/external/`과 `files` 브랜치(`get_day_files.py N`)에 이미 만들어져 있습니다.
- SEC 보고서 발췌와 비율표는 강사가 SEC에서 추출해 만들었습니다. 원문 링크는 각 발췌 파일 머리와 [데이터 페이지](docs/data.md)에 있습니다. SEC 자료를 직접 받을 때는 User-Agent에 **본인 영문 이름과 이메일**을 적고, 초당 10회 미만으로 요청합니다.

## 공개 범위 — 이 저장소에 없는 것

이 저장소의 `main`은 **수강생 템플릿**입니다(실습 양식 · 노트북 · 프롬프트 · 1일차 데이터 · 사이트 원고 · 도구). 2일차부터의 수업 파일은 같은 저장소의 **`files` 브랜치**에 모두 미리 올라와 있고, `uv run python tools/get_day_files.py N`이 내 저장소의 같은 경로로 받습니다. 그중 **먼저 내 결과를 만든 뒤 견주는 파일(골든셋 · 기대값 테스트 · 강사 결과)과 전날 결과가 들어 있는 시작 파일은 정한 시각(열기 시각) 전에는 내 폴더에 들이지 않습니다**(AI가 정답을 미리 읽지 않게). 아래는 `main`에 두지 않습니다(`.gitignore`).

| 무엇 | 왜 | 언제 공개 |
|---|---|---|
| 강사 정답지 · 정답 워크북 · 결함 기록 · 강사 운영 자료 | 실습 정답 | 공개하지 않습니다 |
| 수업 파일(`data/checkpoints/d2_start.xlsx` 등 · 비교 기준 · 강사 모델) | 전날 실습의 결과 · 비교 기준이 들어 있다 | 지금 `files` 브랜치에 — 열기 시각(그날 08:30 · 15:35 · 18:00 등)부터 내 폴더로 |
| 원천 `data/raw/` · 생성기 설정과 일부 생성기 · `tools/news_pool/` | 숨은 정답 컬럼 · 결함 계획 · 점수 | 10/21(수) 19:00 `files` 브랜치에 자동 공개(결함 기록은 제외) |
| Day1 정답 차트(`docs/assets/day1/`) | 정제한 결과 수치 | 과정이 끝난 뒤 |
| 슬라이드 PDF(`handouts/dayN_slides.pdf`, 발표자 노트 제외) | 크다(일차마다 약 10 MB) | 지금 `files` 브랜치 · 사이트 '파일 받기'(6일차는 위기 카드 · 인젝트 3쪽을 비운 판 → 10/21 18:00 완성판) |
| 6일차 위기 카드 · 데이터 팩 · 인젝트 | 수업 중 정한 시각의 깜짝 상황 | 10/21(수) 09:28 · 11:15 · 11:30 · 13:15 자동 공개 |
| 사이트 빌드 결과(`site/`, `docs/downloads/`, `docs/_snippets/`) | 배포 때마다 새로 만든다 | 커밋하지 않습니다 |

오류를 발견하면 과정 오픈채팅으로 알려 주세요. 과정 중 수정 사항은 사이트 위쪽 공지로 안내합니다.
