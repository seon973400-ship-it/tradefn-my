# TradeRisk Control Tower — 5일차 Streamlit 템플릿

(가상) 한빛정밀(주)의 미결 인보이스 원장으로 **전처리 → 연체확률·등급 → 한도·충격 시나리오 → 조기경보 → 영문 독촉 초안·승인 → 규정 RAG → 감사로그**를 돌리고, 맨 앞 **통합 상황판 한 장**(KPI 줄 · P1·P2 경보 · 바이어 표 · 기준일)으로 묶어 보는 실습용 대시보드입니다. 5일차 실습 B에서 이 앱에 **환율 타일**과 **톤 표를 읽는 라우팅**, **승인 기록 DB**를 더하고 내 주소로 배포합니다.

- 합성 데이터만 씁니다. 실데이터·바이어 실명·담당자 메일은 올리지 않습니다.
- **Draft-only**: 메일을 보내지 않습니다. AI 초안 → 가드레일 → 사람 승인 → 감사로그까지만 합니다.
- LLM 키가 없으면 **모의 모드**로 끝까지 돕니다(템플릿 초안·검색 결과 인용). 오늘은 키 없이 합니다.

## 페이지 — 첫 화면은 ⓪ 통합 상황판

앱을 열면 **⓪ 통합 상황판**이 먼저 뜹니다. 결정 질문 하나 — "오늘 누구에게 선적·독촉·통지를 해야 하나?" — 에 답하는 한 장이고, 위에서 아래로 *요약 숫자 → 경보 → 표 → 근거* 순서입니다(숫자마다 기준일). 나머지 ①~⑦은 그 숫자를 만드는 단계입니다.

| 페이지 | 하는 일 | 입력 파일(저장소 안) |
|---|---|---|
| ⓪ 통합 상황판 | KPI 줄(미결 채권 · 연체 30일+ · P1 · P2 · 통지 기한 D-n · 독촉 초안 대상) → P1·P2 경보 표 → 바이어 표(경보 우선 → 연체 금액 순) → 근거·기준일. 경보 규칙은 ④와 같고, ②를 열면 등급·pd_30d·P4가 점수표 값으로 바뀐다 | 기본 원장 `data/checkpoints/d5_start.csv`(자동 정제) · (있으면) ② 점수표 |
| ① 업로드·전처리 | 날짜·통화·금액 표기 통일, 중복·빈칸·단위 의심 표시, 연체일·독촉 단계·사고통지 기한 계산 | `data/checkpoints/d5_start.csv`(5일차 08:30 공개) · `sample_data/upload_sample.csv` · 내 CSV |
| ② 예측·등급 | Day3 모델로 30일 연체확률(pd_30d) → S/A/B/C, 전월 대비 등급 변화, 상위 기여 3개 | `data/checkpoints/d3_start_scoring.csv` · `models/day3_lgbm.pkl`(.txt) · `feature_list.json` · `grade_cutoffs.json` |
| ③ 한도·시나리오 | 한도 = min(필요한도, 등급 상한, 인수한도 + 자기부담) · (선택) LP 재배정 · S0~S4 충격 기대손실 | (있으면) `d4_start_scored.csv` · `d4_params.csv` · `d4_scenarios.csv` |
| ④ 조기경보 | P1 파산·사기 → P2 선적 보류선·사고발생통지 기한 → P3 조건 변경·한도 사용률·수출통지 → P4 위험 신호(② 점수표가 있을 때). P1·P2는 대화상자 | 원장 + ② 점수표 |
| ⑤ 독촉메일 | D-3 · D+7 · D+15 · D+30 · 이관 사전 통지 영문 초안 → 가드레일 5개 → 승인/반려 → 감사로그, 초안 .txt | `prompts/dunning_v1.md` |
| ⑥ RAG 규정검색 | 가상 여신관리규정 조(條) 단위 검색 + 인용 + 기권(LLM 답은 인용·근거 검사 표시), 골든셋 20문항 일괄 실행(평가 시트용 CSV) | `rag/corpus/` · `rag/goldset_20.csv` · `prompts/rag_system_v1.md` |
| ⑦ 로그 | 감사로그 21필드 CSV, LLM 호출·토큰·추정 비용 | — |

## 1. 내 PC에서 돌리기 — 저장소 맨 위 폴더의 터미널에서

```bash
uv sync --group dash                          # 처음 한 번. 'uv sync'만 다시 하면 streamlit이 지워진다 — 이 줄 그대로
uv run streamlit run app/streamlit_app.py     # 브라우저에 ⓪ 통합 상황판이 열린다(http://localhost:8501). 끄기 Ctrl+C
uv run pytest app/tests -q                    # 모의 모드 끝까지 + 상황판 포함 8페이지 검사(LLM은 가짜 로컬 서버)
```

오늘 파일은 `uv run python tools/get_day_files.py 5`로 받습니다. ⓪이 "먼저 ① 업로드·전처리에서 원장을…"이라고 하면 `data/checkpoints/d5_start.csv`가 아직 없는 것입니다.

## 2. 내 앱 배포하기 (Streamlit Community Cloud, 약 10분) — 실습 B6

1. **배포용 데이터를 커밋합니다.** 템플릿 `.gitignore`가 체크포인트와 모델을 막아 두었으므로, 기본 원장을 읽는 앱이 되려면 강제로 더합니다(모두 가상 데이터와 수업용 모델이라 공개해도 됩니다).
   ```bash
   git add -f data/checkpoints/d5_start.csv data/checkpoints/d3_start_scoring.csv data/checkpoints/d4_start_scored.csv data/checkpoints/d4_params.csv data/checkpoints/d4_scenarios.csv models/
   ```
   안 하면 앱 ①에서 직접 업로드해야 하고, ② 등급은 모델 파일이 없어 건너뜁니다.
2. [share.streamlit.io](https://share.streamlit.io) → **Continue with GitHub** → 권한 허용 → **Create app** → *Deploy a public app from GitHub*.
3. Repository = **내 저장소**(과정 템플릿에서 만든 것) · Branch = `main` · Main file path = **`app/streamlit_app.py`** · App URL = 영문 소문자·숫자·하이픈 (예: `traderisk-t2-07`).
4. **Advanced settings** → Python version **3.13** → **Secrets** 칸은 **비워 둡니다** → Save → **Deploy**(첫 배포 2~5분).
   - Secrets를 비우면 모의 모드로 뜨고 모든 페이지가 돕니다. 실제 AI 초안을 보려면 강사가 안내할 때만 [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)의 형식으로 넣습니다.
   - 키는 Secrets 칸에만 넣습니다. 저장소(공개)에 `secrets.toml`을 올리지 않습니다.
5. 앱에서 ⓪ 통합 상황판(첫 화면) → ① 기본 원장 → ② → ③ → ④(경보 대화상자 '확인하고 기록') → ⑤ 초안 → 승인 → ⑦ 감사로그 CSV 내려받기까지 한 바퀴.

- 의존성은 이 폴더의 `requirements.txt`(전부 `==` 고정)를 씁니다 — Community Cloud는 진입점 폴더의 파일을 먼저 찾습니다. 새 패키지가 필요하면 이 파일에 줄을 더합니다.
- 12시간 동안 아무도 열지 않으면 앱이 잠듭니다 → 화면의 **Yes, get this app back up!**
- Community Cloud 저장 공간은 휘발성입니다 — 감사로그는 세션이 끝나기 전에 ⑦에서 CSV로 받고, 승인 기록 DB(`receivables.db`)는 앱이 다시 시작되면 사라집니다.
- 밤에 연습하면 ⑤ 발송 시간창(현지 08–21시) 검사 때문에 [승인]이 잠깁니다. Secrets `[app]`에 `demo_clock = "2026-10-20 15:00"`을 넣으면 그 시각으로 검사합니다.
- 오류가 나면 앱 오른쪽 아래 **Manage app**의 로그를 처음부터 끝까지 복사해 [프롬프트 P5-B3](../labs/day5/prompts.md)에 붙입니다.

## 3. 실습 B에서 이 앱에 더하는 것

| 단계 | 더하는 것 | 파일 |
|---|---|---|
| B3 환율 타일 | ⓪에 '원화 환산(오늘 환율)' 타일 1개 — 환율 API(키 없음) · 10분 캐시 · 실패 시 저장된 환율 | 새 `core/fx_live.py` · `views/p0_overview.py` · `tests/` |
| B4 독촉 워크플로 | `route()`가 톤 표(`tone_matrix.csv`)를 읽어 템플릿을 정한다 | `core/dunning.py` · `tests/` |
| B7 승인 기록 DB | 승인 1건 = 기록 1행 + 단계 갱신을 한 트랜잭션으로(SQLite) | 새 `core/store.py` · `views/p5_dunning.py` · `views/p7_log.py` · `tests/` |
| 더 하기 | 국가별 연체 막대 · 등급 하락만 보기 · 금지 표현 빨간 표시 · 감사로그 필터 · 엑셀 업로드 | `views/p4_alerts.py` · `p2_score.py` · `p5_dunning.py` · `p7_log.py` · `p1_upload.py` |

요구사항 카드와 프롬프트: `labs/day5/spec_fx_tile.md` · `labs/day5/tone_matrix.csv` · `labs/day5/prompts.md`. 기존 타일 · `st.session_state` 키 · 함수 이름은 바꾸지 않고, 새 패키지는 더하지 않습니다.

- 커밋한 뒤 화면이 그대로이거나 `has no attribute` 오류가 나면(특히 `core/`·`ui.py`를 고쳤을 때): 앱 오른쪽 위 ⋮ → **Rerun** → 그래도 같으면 Community Cloud **Manage app → ⋮ → Reboot app**(로컬은 Ctrl+C 뒤 `streamlit run` 다시).

## 4. 구조 (고칠 때 참고)

```text
app/
├─ streamlit_app.py      진입점: st.navigation 8페이지(⓪ 통합 상황판 = 첫 화면 + ①~⑦) + 공통 사이드바(기준일·LLM 사용)
├─ ui.py                 화면 공용(세션 키·캐시·Secrets) — 페이지가 import
├─ views/p0~p7_*.py      화면만(계산은 core/) — p0_overview = 통합 상황판 · 메뉴 순서·이름은 streamlit_app.py의 st.Page 목록
├─ core/                 계산(Streamlit 없이 테스트 가능): clean · model · limits · alerts · overview · dunning · guardrails · rag · llm · audit · data_io
├─ prompts/              독촉 템플릿 T0~T4(dunning_v1.md) · RAG 시스템 프롬프트(rag_system_v1.md)
├─ sample_data/          upload_sample.csv(표기가 섞인 100행 + 중복 1행)
├─ tests/                pytest — 모의 모드 끝까지 · 가짜 LLM 서버 · AppTest 화면 검사(상황판 포함)
└─ .streamlit/           config.toml · secrets.toml.example
```

- 화면 폴더 이름이 `pages/`가 아닌 이유: 진입점 옆에 `pages/` 폴더가 있으면 Streamlit은 서버가 막 켜진 뒤 `st.navigation`이 한 번 실행되기 전까지 옛 방식(폴더 자동 메뉴)으로 돈다 — 잠든 앱을 페이지 주소(…/p4_alerts)로 깨우면 진입점 없이 그 페이지만 뜬다. 새 페이지(예: 6일차 `p8_scenario.py`)는 `views/`에 만들고 `streamlit_app.py`의 목록에 `st.Page("views/p8_scenario.py", title=…)` 한 줄을 더한다.
- LLM 호출은 `core/llm.py` 하나(OpenAI 호환 `/chat/completions`, 429·5xx면 `fallback_models`로 재시도, 다 실패하면 템플릿 초안). 키가 없으면 호출하지 않는다.
- 가드레일(`core/guardrails.py`): ① 금지 표현(법적 절차·국가기관·위협, 계좌 변경 문구) ② 단계별 필수 요소 ③ 180단어 ④ 수신자 허용 목록 ⑤ 발송 시간창.
- 모델은 저장소 루트 `models/`를 읽는다(`app/models/`에 복사본이 있으면 그것을 먼저).
