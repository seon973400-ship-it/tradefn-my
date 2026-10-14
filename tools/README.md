# tools — 데이터·사이트·노트북 도구

(가상) 한빛정밀(주) 합성 데이터를 만들어 Day별 파일로 나누는 파이프라인, 과정 사이트를 빌드하는 도구, 수강생이 매일 아침 쓰는 '그날 파일 받기'(`get_day_files.py`)가 들어 있습니다. 옛 Challenge 노트북 · Orange 워크플로 · Dify · n8n 생성기는 이번 과정에서 쓰지 않으며, 표에 '쓰지 않음'으로 적었습니다. 명령은 모두 **저장소 루트**에서 실행합니다.

> **과정 중에는 일부 파일이 이 저장소(main)에 없습니다.** 2일차부터의 수업 파일은 같은 저장소의 `files` 브랜치에 있고 `get_day_files.py N`이 받습니다. 실습의 정답(숨은 등급·심어 둔 결함·시나리오·정답 문구)이 들어 있는 생성기 설정과 생성기 · 원천은 `.gitignore` 2절로 막혀 있다가 **2026-10-21 19:00에 `files` 브랜치로 자동 공개**됩니다(아래 '과정 뒤 공개' 표, 봉인 묶음 r6).

## 지금 쓸 수 있는 도구

```bash
uv run python tools/get_day_files.py 1              # (수강생) 그날 파일 받기 — 1~6일차, --list · --force · --offline · --now
pip install -r requirements-docs.txt              # 사이트 빌드용(MkDocs)
python tools/sync_site_assets.py --files-root _files   # files 브랜치 색인 → docs/downloads/ · ZIP · '파일 받기' 카드 조각
mkdocs build --strict -d site                     # 사이트 빌드(tools/mkdocs_hooks.py가 훅으로 붙는다)

pip install nbformat                              # 노트북 생성용(실행 검사까지 하려면 nbclient ipykernel pandas도)
# python tools/build_day1_notebook.py            # (v3 — 쓰지 않는다) 1일차 Challenge 노트북 생성기(결과물 d1_challenge.ipynb는 강사 보관본으로 옮김)
# python tools/build_day2_notebook.py            # (v3 — 쓰지 않는다) Day2 Challenge 노트북 d2_challenge.ipynb 생성기
# python tools/build_day3_notebook.py            # (v3 — 쓰지 않는다) Day3 Challenge 노트북 d3_challenge.ipynb 생성기
python tools/build_day23_labs.py --check          # Day2·3 양식 4종(워밍업 뉴스 · BYOD 점검표 · 등급 시트 · SHAP 양식) 검사(생성은 강사 PC)
# python tools/build_day2_orange.py             # (v3 — 쓰지 않는다) Day2 Orange 전처리 .ows 생성기
# python tools/build_day3_orange.py             # (v3 — 쓰지 않는다) Day3 Orange 모델 .ows 생성기
pip install PuLP==3.3.2 scipy nbclient ipykernel  # Day4 노트북 실행 검사용(PuLP는 수업 고정 3.3.2 — 4.0.0은 API가 바뀌고 CBC가 빠짐)
# python tools/build_day4_notebook.py            # (v3 — 쓰지 않는다) Day4 Challenge 노트북 d4_challenge.ipynb 생성기
# python tools/build_day4_templates.py           # (v3 — 쓰지 않는다) Day4 옛 리포트 양식 생성기(이번 양식은 labs/day4/report_template.docx)
# python tools/build_day5_agents.py               # (v3 — 쓰지 않는다) n8n 워크플로·Dify DSL 생성. 돌리면 agents/n8n · agents/dify가 되살아난다
# python tools/build_day5_notebook.py --execute   # (v3 — 쓰지 않는다) Colab 노트북 labs/day5/d5_rag_eval.ipynb 생성. 5일차 평가는 Claude Code가 만든 eval.py로 한다
uv sync --group dash && uv run pytest app/tests -q   # Day5 앱 검사(Python 3.13 — Community Cloud와 같은 버전)
python -m pytest app/tests -q                     # 앱 모의 모드 끝까지(원장 → 등급 → 한도 → 경보 → 독촉·승인 → 로그 → RAG) + 통합 상황판 포함 8페이지 화면 스모크
```

| 파일 | 역할 | 과정 중 이 저장소만으로 실행 |
|---|---|---|
| `sync_site_assets.py` | `files` 브랜치의 색인 `_index.json`(파일 · 일차 · 실습 구역 · 구분 · 설명 · 열기 시각)대로 `docs/downloads/dayN/`에 복사하고 카드 조각(`docs/_snippets/dayN/files_<구역>_cards.md` · `files_all_cards.md` · `files_pdf_cards.md`) · 예전 표 조각 · `dayN_files.zip` · 구역별 `dayN_<구역>.zip`을 만든다. 열기 시각이 남은 파일은 카드에 `data-tf-open`(사이트 JS가 그 시각까지 잠근다)을 붙이고 ZIP에서 뺀다. 안 풀린 6일차 파일은 '자동 공개' 자리 카드. 정답 원본 · 원천 경로가 색인에 있으면 멈춘다. `--day N` · `--check` · `--now ISO`(시각 흉내) · `--check-links site`(빌드 뒤 링크 점검) | 된다(`files` 브랜치를 `_files`로) |
| `mkdocs_hooks.py` | MkDocs 훅 — 내려받기용 `.md`를 페이지로 바꾸지 않고 그대로 복사, 프롬프트 제목(`## P1-4 …`)의 앵커를 `#p1-4`로 고정 | 된다(`mkdocs.yml`이 부른다) |
| `get_day_files.py` | **수강생이 매일 아침 실행하는 '그날 파일 받기'**. 과정 저장소 `files` 브랜치의 수업 파일 목록(`_index.json`)과 main 목록을 읽어, 내 저장소에 없는 그날 파일을 같은 경로로 내려받고(SHA-256 확인) 고쳐 쓸 데이터 파일(`data/`의 표 · JSON, 5일차는 요구사항 카드 · 톤 표)만 `workbench/dayN/data/`에 작업 사본을 만든다(프롬프트 · 양식 · 코드 · 완성본 · 비교 기준은 사본 없음). 이미 있는 파일은 덮어쓰지 않는다(`--force`만). 열기 시각 전 파일은 `[열기 전]`으로 알리고 받지 않는다(`--now`로 앞당김). 6일차는 자동 공개 시각을 보여 주고, 시각이 지났는데 아직 올라오지 않은 묶음은 출력 맨 끝에 '1–2분 뒤 다시 실행'으로 알린다. 목록 · 시각 · 안내는 코드가 아니라 색인 데이터라 사본의 이 파일은 고칠 일이 없다. 표준 라이브러리만 쓴다 | 된다 |
| `release_due.py` | (GitHub Actions `d6-release.yml` 전용) `files` 브랜치의 봉인 묶음(`sealed/*.tgz.enc`) 가운데 시각이 된 것을 저장소 시크릿 키로 풀어 그 브랜치에 놓고 색인을 고친다. 시각 전 묶음은 풀지 않고, 같은 묶음은 두 번 풀지 않으며, 로그에 파일 이름을 찍지 않는다. `--verify-all`(dry-run) | 키가 있어야 한다 |
| `build_day1_notebook.py` | (v3 · v4 1일차는 쓰지 않음) Challenge 노트북 `d1_challenge.ipynb`(출력 없는 수강생용)을 만들고 규칙을 점검한다. `--execute`는 사본을 임시 폴더에서 위→아래로 실행해 SEC 값과 대조한다. **`--user-agent`는 기본값이 없다** — SEC 규칙대로 본인 영문 이름과 이메일을 넘긴다(없거나 예시 주소면 실행 검사를 시작하지 않는다) | 생성·점검은 된다. 실행 검사의 일부 대조 항목(정답 차트 표·원천·강사 정답)은 그 파일이 있을 때만 한다 |
| `build_day2_notebook.py` | **(v3 — 이번 과정은 쓰지 않는다)** Day2 Challenge 노트북 `labs/day2/d2_challenge.ipynb`(출력 없는 수강생용: 통화·환율 `merge_asof` · 결측 대체 중앙값 vs KNN · 파이프라인 안 스케일링 · 정본 특성 · LLM 없는 사전 기준선 뉴스 점수와 골든셋 일치도). `--execute`는 임시 폴더에서 실행해 🟢 기대값 · 정본 특성표와 대조하고 실행본을 강사 폴더(저장소 밖)에 저장 | 생성·점검은 된다. 실행 검사는 Day2 파일과 강사 기대값이 있어야 한다 |
| `build_day3_notebook.py` | **(v3 — 이번 과정은 쓰지 않는다)** Day3 Challenge 노트북 `labs/day3/d3_challenge.ipynb` 하나(D6: LightGBM · class weight/SMOTE 변형 · ROC/PR · 비용 5:1 임계값 · SHAP · t/4 · t/2 · t 등급 · Prophet). `--execute`는 실행해 강사 정답(`_summary.json` · `d3_variants.csv` 등)과 대조 | 생성·점검은 된다. 실행 검사는 Day3 파일과 강사 정답이 있어야 한다 |
| `build_day23_labs.py` | Day2·3 양식: `labs/day2/news_warmup_10.txt`(워밍업 10건, 한 4 · 영 6) · `labs/day2/byod_anonymize_template.xlsx`(익명화 점검표 + 가상 예시 수식) · `labs/day3/d3_grade_banding.xlsx`(pred · 이름 t 빈칸 · IFS · 단조성 · 6열 CSV) · `labs/day3/d3_shap_report_template.md`/`.docx`(P3-1 5칸 + 캡처 2칸) + 강사 채운 판(`../instructor/day3/answers/d3_grade_banding_filled.xlsx`). `--check`는 pycel로 다시 계산해 정답표와 대조 | 검사는 된다(생성은 Day2 뉴스 · Day3 정답이 있는 강사 PC) |
| `orange_ows.py` · `build_day2_orange.py` · `build_day3_orange.py` | **(v3 — 이번 과정은 쓰지 않는다)** Orange 3.40 워크플로를 캔버스와 같은 방식(WidgetsScheme → 저장)으로 만들고, .ows와 데이터만 있는 새 폴더에서 다시 열어 끝까지 실행해 검사한다. `labs/day2/d2_orange_preprocess.ows`(Fixed values 0 = 자리표시 · 강사판은 중앙값) · `labs/day3/d3_orange_model.ows`. `--expected`는 리허설 기대값 `../instructor/day3/answers/orange_expected.json` + `d3_model_report.md` §6 | 수업 requirements 밖(Orange 3.40 가상환경). xgboost ≥ 3.3이면 Explain 위젯이 실패한다 — 검사가 경고로 알려 준다 |
| `build_day4_notebook.py` | **(v3 — 이번 과정은 쓰지 않는다)** Day4 Challenge 노트북 `labs/day4/d4_challenge.ipynb`(출력 없는 수강생용: PuLP 3.3.2·linprog 교차검증, 제약 실험, 몬테카를로 독립 vs 1-요인). `--execute`는 사본을 임시 폴더에서 실행해 강사 정답과 대조하고 실행본을 강사 폴더(저장소 밖)에 저장 | 생성·점검은 된다. 실행 검사는 Day4 CSV(Day4 08:30 공개)가 있어야 한다 |
| `build_day4_templates.py` | **(v3 — 이번 과정은 쓰지 않는다)** Day4 신용 리스크 리포트 양식 `labs/day4/d4_risk_report_template.docx`/`.md`(같은 내용 두 형식: 설계도 6칸 · 본문 소제목 8개 + 숫자 대조표 · 레드팀 지적 · 수정 기록 · 사람 검토 12항목). 소제목 · 지적 표 머리 · 12항목은 `labs/day4/prompts.md`와 글자까지 대조하고, 손으로 쓴 `labs/day4/fraud_signals.md`는 구조만 검사한다. 같은 입력이면 같은 파일이 나온다 | 된다 |
| `build_day5_agents.py` | **(v3 — 쓰지 않는다)** n8n 독촉 워크플로 · Dify DSL 생성기. 5일차가 Claude · ChatGPT · Claude Code 중심으로 바뀌어 사본을 `instructor/day5/lab_v3_archive/agents_v3/`로 옮겼다 — 돌리면 `agents/n8n` · `agents/dify`가 되살아난다 | – |
| `build_day5_notebook.py` | **(v3 — 쓰지 않는다)** Colab 노트북 `labs/day5/d5_rag_eval.ipynb` 생성기. 평가는 Claude Code가 `scripts/rag_lab/eval.py`를 만들어 한다 — 돌리면 노트북이 되살아난다 | – |
| `build_preview.py` | Day1 실습 가이드 한 페이지 미리보기(강사 검토용 HTML). 사이트와 같은 md·`mkdocs.yml` 설정으로 만들고 태그 짝·내부 링크·라이브러리 프롬프트 포함을 검사한다. 먼저 `sync_site_assets.py`. 출력 기본값은 저장소 밖 `../instructor/day1/preview/`(`--out`으로 바꾼다) | 된다(`--out` 지정) |
| `fetch_external.py` | 외부 공개 데이터 캐시 수집(FRED 환율 4종 → `data/external/`) — 네트워크는 이 스크립트만 쓴다 | 안 된다(`config.yaml`을 읽는다) |
| `tf_common.py` | 경로·설정·난수 스트림·환율·xlsx/CSV 쓰기 공용 함수 | — (다른 도구가 import) |
| `snapshot.py` | 기준일 스냅샷 피처·라벨 계산 — 누수 검사에도 쓴다 | — (생성기가 import) |
| `dictionary_spec.py` | 수강생용 데이터 사전의 정의(뜻·단위·원천만 적은 중립 설명)·코드표 | — (생성기가 import) |
| `make_day1_charts.py` | Day1 차트 4종(라이트·다크) + 표 버전 CSV → `docs/assets/day1/`(정답 수치라 과정 뒤 공개) | 안 된다(`config.yaml`을 읽는다) |
| `fonts/` | 차트·노트북용 한글 글꼴 NanumGothic(SIL OFL 1.1, `fonts/OFL.txt`) | — |
| `requirements-tools.txt` | 저장소 루트 `requirements.txt`를 그대로 가리킨다 | — |

## 과정 뒤 공개 — 지금 저장소에 없는 파일

아래 파일은 `.gitignore` 2절에 있어 main에는 없고, **2026-10-21 19:00에 봉인 묶음 r6로 `files` 브랜치에 자동 공개**됩니다(결함 기록 `data/raw/dirty_log.csv`와 `lint_tokens_private.json`은 제외). 위 표의 '안 된다' 도구와 아래 순서는 그 뒤에 `files` 브랜치를 받아(`git fetch origin files && git checkout origin/files -- data/raw tools`) 돌릴 수 있습니다.

| 파일 | 역할 | 왜 지금은 없나 |
|---|---|---|
| `config.yaml` | 모든 파라미터(교육용 가정 표시). 값은 여기서만 바꾼다 | 오염 계획·시나리오 설정 |
| `generate_data.py` | 바이어 → 부도 추첨 → 인보이스 → 결제조건 믹스 보정 → 연체 보정 → 충당 → 재무·뉴스·사건 | 숨은 정답 컬럼을 만든다 |
| `build_checkpoints.py` | 오염 주입, Day별 체크포인트, 데이터 사전 두 벌(수강생용 + 강사용 전체), 강사 정답 파일 | 오염 목록·정답 문구 |
| `day1_expected.py` | 강사용 Day1 EDA 기대값 문서 | 정답 숫자 |
| `validate_data.py` | 데이터 검사 V01~V23 · C01·C02·C08·C09(V21 d3_end_scored 등급·pd · V22 d4_start 열 · V23 모델 재점수 · C08 Day2·3 구조 · C09 Day1 → Day6 사슬 값) + Day4·5·6 모듈 | 정답 컬럼을 검사한다 |
| `build_day1_template.py` | (v3 · v4 1일차는 쓰지 않음) 실습 템플릿 `d1_end_eda_template.xlsx` · AX 캔버스 `ax_canvas_template.md`(둘 다 저장소에서 빼 강사 보관본으로 옮김)와 강사 정답 워크북을 만들고 검사한다(`--check`: 검사만) | Lab1·Lab2 정답 문구 |
| `news_pool/` | 고정 헤드라인 풀(128개) | 점수 열이 Day2 정답 |
| `checkpoints_day23.py` | `build_checkpoints.py`가 부른다: Day2 뉴스 `d2_news.csv` · Day3 시작 파일 3개 · `labs/day3/fx_forecast_inputs.csv` + Day2 강사 정답(정본 특성표 · 🟢 기대값 · 뉴스 채점본 · 골든셋 20, D10 앵커는 정답 파일에만) | 정답 특성표 · 뉴스 점수 |
| `train_day3_model.py` | Day3 정답 모델(LightGBM · 비용 임계값 · SHAP · 등급 · 환율 3경로) → `d3_end_scored.csv` · `models/` · 강사 보고서. 다시 돌리면 Day4·5 입력이 바뀐다 | 정답 모델 · 등급 |
| `checkpoints_day4.py` | Day4 CSV 4개(`d4_start_scored`·`d4_params`·`d4_scenarios`·`d4_open_inv`) + 계산 모형(LP 입력·시나리오·충당금·조기경보 — 워크북 수식과 같은 정의) | 신용사건·전략 바이어 판정이 원천 정답을 읽는다 |
| `solve_day4_lp.py` | 한도 LP 정답(PuLP 3.3.2 CBC + scipy HiGHS 교차검증) · 제약 실험 · 몬테카를로 → 강사 폴더(저장소 밖: 바이어별 해·Day4 정답본·해설) | Lab 2 정답 |
| `build_day4_workbook.py` | 워크북 3종: 빈 틀 `labs/day4/d4_limit_model.xlsx`(공개 저장소) · 채운 판 `data/checkpoints/d4_limit_model.xlsx`(Day4 08:30) · 강사 정답판 + pycel 수식 검산 19항목 | 채운 판·정답판에 Day3 점수·PuLP 해 |
| `validate_day4.py` | Day4 검사 D401~D408(`validate_data.py`가 부른다) | 정답 파일을 검사한다 |
| `build_day5.py` | Day5 파일: 미결 원장 `d5_start.csv`(≤ 300행, 독촉 단계·통지 기한·연속수출 위험·사기 신호) · 골든셋 `rag/goldset_20.csv` · 질문 목록 `rag/goldset_questions.csv` · 평가 시트(v4, 채팅 경로용) `rag/eval_sheet_template.xlsx` · 앱 업로드 샘플 · 강사 정답(`../instructor/day5/answers`) · 데이터 사전 Day5 행 | 신용사건·사기 신호 판정이 원천 정답을 읽는다 · 충돌 조항 정답표 |
| `validate_day5.py` | Day5 검사 V19·V20 + C03~C07(`validate_data.py`가 부른다). C05는 규정 별표2 한도 상한 = Day4 워크북 Cap(D9)과 규정 PDF · 질문 목록 · 평가 시트(README · eval · eval_B · summary)도 본다. C04(v3 Sheets 템플릿)는 뺐고 C06은 LiteLLM 설정만 본다 | 정답 열 이름을 검사한다 |
| `build_day6_pack.py` | Day6 해커톤 파일: 위기 데이터 팩 `d6_crisis_pack.xlsx`(+ 시트별 CSV 10개) · 팀 팩 `d6_teams/team_01~05.xlsx` · 카드 ⑤ 2단계 `d6_card5_stage2.xlsx` · 위기 카드 · 인젝트 · 변형 카드(`labs/day6/crisis_cards` · `injects` · `variants`) · 공개 양식 `labs/day6/judging_rubric.xlsx`·`.md` · `roi_kpi_template.xlsx` · 강사 정답(`../instructor/day6/answers`) · 심사표 원본(`../instructor/day6/scorecard.xlsx`). `--assign 1=2,2=1,…`(08:30 팀–카드 배정 뒤) · `--check`(검사만) | 카드 원문(09:28 전 비공개) · 강사 기대값 |
| `build_day6_answers.py` · `build_day6_templates.py` | `build_day6_pack.py`가 부르는 강사 정답 쓰기 · 양식 · 카드 · 심사표 쓰기(ROI 템플릿 · 심사표는 pycel로 검산) | 같음 |
| `validate_day6.py` | Day6 검사 D601~D607(`validate_data.py`가 부른다): 팩 구조 · 카드 트리거 값 · 기준값(D11 환율 · I-2 기한) · 팀 팩 · 양식(루브릭 앵커 · SOP = 킷 템플릿 · 카드 내용 비노출) · 강사 정답 · 공개 경계(.gitignore) | 정답 파일을 검사한다 |

만드는 순서(과정 뒤, 저장소 루트):

```bash
pip install -r requirements.txt
python tools/fetch_external.py fred           # 1) FRED 환율 캐시(네트워크는 여기서만)
python tools/generate_data.py                 # 2) 원천 세계 → data/raw/ (seed 20261014, 약 40초)
python tools/build_checkpoints.py             # 3) Day1 배포본·d2_start·데이터 사전·강사 정답
python tools/validate_data.py                 # 4) V01~V20 검사(실패 시 종료코드 1)
python tools/make_day1_charts.py              # 5) Day1 실습 가이드 차트 → docs/assets/day1/
python tools/build_day1_template.py           # 6) Day1 엑셀 템플릿·AX 캔버스·강사 정답 워크북 + 검사
python tools/build_day1_notebook.py           # 7) (v3) 1일차 Challenge 노트북 — v4 1일차는 건너뛴다
python tools/train_day3_model.py              # 8) Day3 정답 모델 → data/checkpoints/d3_end_scored.csv · models/
# python tools/build_day2_notebook.py --execute # 8a) (v3 — 건너뛴다) Day2 Challenge 노트북
# python tools/build_day3_notebook.py --execute # 8b) (v3 — 건너뛴다) Day3 Challenge 노트북
python tools/build_day23_labs.py              # 8c) Day2·3 양식 4종 + 강사 채운 판 + pycel 검산
# python tools/build_day2_orange.py          # 8d) (v3 — 건너뛴다) Orange Day2 전처리 .ows
# python tools/build_day3_orange.py --expected  # 8e) (v3 — 건너뛴다) Orange Day3 모델 .ows
python tools/checkpoints_day4.py              # 9) Day4 CSV 4개(d4_start_scored · d4_params · d4_scenarios · d4_open_inv)
python tools/solve_day4_lp.py                 # 10) 한도 LP 정답(PuLP 3.3.2 + HiGHS) → ../instructor/day4/answers
python tools/build_day4_workbook.py           # 11) 워크북 3종 + pycel 검산(약 40초, FAIL 0이어야 한다)
# python tools/build_day4_notebook.py --execute # 12) (v3 — 건너뛴다) Day4 Challenge 노트북
python tools/build_day5.py                    # 14) Day5 원장·양식·골든셋·평가 시트·앱 샘플·강사 정답(Day4 정답본 한도를 쓴다) + 검사
# python tools/build_day5_agents.py          # 15) (v3 — 건너뛴다)
# python tools/build_day5_notebook.py        # 16) (v3 — 건너뛴다)
python -m pytest app/tests -q                 # 17) 앱 테스트(모의 모드)
python tools/build_day6_pack.py               # 18) Day6 해커톤 팩 · 팀 팩 · 카드 · 인젝트 · 양식 · 강사 정답 · 심사표 + 검사 D601~D607(약 40초)
python tools/validate_data.py                 # 19) 다시 검사 — V01~V23 + C08·C09(Day2·3 · 사슬) + Day4 D401~D408 + Day5 C03~C07 + Day6 D601~D607
```

- Day4 수강생용 사전 행: `config.yaml` `day4.learner_dictionary`(기본 `false` — 강사용 전체 사전에는 늘 들어 있다). 켜려면 `true`로 바꾸고 `build_checkpoints.py`를 다시 돌린다 — 학생 사본이 만들어지기(10/14 13:20) 전에.
- `build_checkpoints.py`를 다시 돌려도 `_manifest.json`의 `day4`·`day5` 절은 지워지지 않는다(뒤 단계가 덧붙인 절을 보존).
- Day6: 팀–카드 배정은 고정(1조 ← 카드 ① … 5조 ← ⑤)으로 `python tools/build_day6_pack.py --assign 1=1,2=2,3=3,4=4,5=5`를 돌려 봉인했다(공개 `_manifest.json`에는 배정표를 적지 않는다). 카드 · 팩 · 인젝트는 봉인 묶음으로 `files` 브랜치에 있다가 09:28 · 11:15 · 11:30 · 13:15에 자동으로 풀린다(`.github/workflows/d6-release.yml`). 생성기를 다시 돌렸으면 강사 PC에서 `instructor/release/seal.py`로 다시 봉인한다.
- Day5 수강생용 사전 행: `config.yaml` `day5.learner_dictionary`(기본 `false`). 켜려면 `true`로 바꾸고 `build_day5.py`를 다시 돌린다(사전을 덧붙여 고친다 — `build_checkpoints.py`를 다시 돌렸다면 그 뒤에 `build_day5.py`도 다시). Day4 정답본이 바뀌면 `build_day5.py`를 다시 돌린다(`limit_usd` 출처).

- 재현성: 같은 seed·config·라이브러리 버전이면 같은 파일 해시(`data/raw/_manifest.json`, `data/checkpoints/_manifest.json`).
- 강사 정답 출력 위치: `config.yaml`의 `outputs.answers_dir`(기본 `../instructor/day1/answers`, 공개 저장소 밖).
- 라이선스: 이 폴더의 코드는 MIT(`LICENSE`), 글꼴은 SIL OFL 1.1 — 저장소 루트의 `NOTICE.md`를 봅니다.
