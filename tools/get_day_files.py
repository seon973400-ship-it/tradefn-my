#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""그날 수업 파일 받기 — 파이썬 기본 기능만 쓰므로 따로 설치할 것이 없습니다.

사용 (저장소 맨 위 폴더에서 · VS Code 터미널):
    uv run python tools/get_day_files.py 1           # 1일차 파일   (uv run tools/get_day_files.py 1 도 됩니다)
    uv run python tools/get_day_files.py 2           # 2일차 파일
    uv run python tools/get_day_files.py 2 --list    # 받지 않고 어떤 파일이 있는지만 보기
    uv run python tools/get_day_files.py 2 --force   # 이미 있는 파일도 다시 받아 덮어쓰기
    uv run python tools/get_day_files.py 2 --now     # 열기 시각 전인 비교 기준 파일도 지금 받기(먼저 내 결과를 만든 뒤에)

하는 일
  1. 그날 파일 목록을 정합니다 — 내 저장소에 이미 있는 파일 + 과정 저장소(공개)의 수업 파일 목록(files 브랜치의 _index.json).
  2. 내 저장소에 없는 파일은 과정 저장소에서 '같은 경로'로 내려받습니다(예: data/checkpoints/d2_start.xlsx).
     프롬프트의 @경로가 모든 사람에게 같게 됩니다. 받은 파일은 목록의 해시와 맞는지 확인합니다.
  3. 고쳐 쓸 데이터 파일(data/ 의 표 · JSON, 5일차는 요구사항 카드 · 톤 표)은 workbench/dayN/data/ 에 '작업 사본'도 둡니다.
     원본(data/, labs/)은 고치지 않고 사본에서 다룹니다. 프롬프트 · 양식 · 코드 · 완성본 · 비교 기준은 사본을 만들지 않습니다
     (원본 자리에서 읽습니다).
  이미 있는 파일은 덮어쓰지 않습니다(--force 를 줄 때만).

수업 파일은 모두 미리 올라와 있습니다. 다만 '먼저 내 결과를 만든 뒤 견주는' 비교 기준 파일(골든셋 · 기대값 테스트 · 강사 결과)과
전날 결과가 들어 있는 시작 파일은 정한 시각(열기 시각) 전에는 내 폴더에 들이지 않고 '[열기 전]'으로 알려 줍니다 —
AI가 내 폴더에서 정답을 미리 읽지 않게 하는 장치입니다. 시각이 지난 뒤 같은 명령을 다시 실행하면 받습니다(급하면 --now).
6일차 위기 카드 · 인젝트는 정한 시각에 자동으로 올라옵니다 — 그 시각 뒤에 같은 명령을 다시 실행하면 새로 올라온 파일만 더 받습니다
(보통 1–2분 늦게 올라옵니다. 시각이 지났는데 아직이면 그 묶음 줄과 출력 맨 끝에 '시각이 지났는데 아직 올라오지 않았습니다'라고 알려 줍니다).
막히면 과정 사이트의 '파일 받기'에서 직접 내려받을 수 있습니다.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import shutil
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent

SOURCE_REPO = "brainini/tradefin-ai-2026"  # 과정 저장소(공개). 내 저장소가 아니라 이쪽에서 받는다
BRANCH = "main"
# (TRADEFIN_* 환경 변수는 강사 리허설 · 시험용 — 평소에는 쓰지 않는다)
RAW_BASE = os.environ.get("TRADEFIN_MAIN_BASE") or f"https://raw.githubusercontent.com/{SOURCE_REPO}/{BRANCH}/"
TREE_URL = os.environ.get("TRADEFIN_TREE_URL") or f"https://api.github.com/repos/{SOURCE_REPO}/git/trees/{BRANCH}?recursive=1"
SITE_URL = "https://brainini.github.io/tradefin-ai-2026/"
# 같은 저장소의 'files' 브랜치 — 수업 파일(체크포인트 · 비교 기준 · 강사 모델 · 풀린 6일차 파일)과 목록 _index.json이 있는 곳.
# 템플릿 사본(내 저장소)에는 따라오지 않는다. 목록 · 시각 · 메시지는 코드가 아니라 이 목록(데이터)에서 읽는다 — 나중에 고칠 일이 생겨도 이 파일은 그대로 쓴다.
FILES_BRANCH = os.environ.get("TRADEFIN_FILES_BRANCH", "files")
FILES_BASE = os.environ.get("TRADEFIN_FILES_BASE") or f"https://raw.githubusercontent.com/{SOURCE_REPO}/{FILES_BRANCH}/"
TIMEOUT = 20  # 초
USER_AGENT = "tradefin-get-day-files/1.0"

CK = "data/checkpoints/"

# 6일차 팀 저장소(킷 템플릿: CLAUDE.md + app/pipeline/)에서 실행하면 '킷 모드' — workbench/ 작업 사본을 만들지 않고,
# 받은 카드 · 팀 팩을 어디에 두는지 안내한다(킷에는 workbench/ 폴더가 없다).
KIT = (REPO / "CLAUDE.md").is_file() and (REPO / "app" / "pipeline" / "README.md").is_file()

# 일차별 설정
#   date     표시용 날짜
#   when     목록(_index.json)을 읽지 못했을 때 알려 줄 안내
#   marker   목록을 읽지 못했을 때만 쓴다 — 이 이름으로 시작하는 파일이 하나라도 있으면 '그날 파일을 받을 수 있다'고 본다
#   prefixes 그날 파일로 보는 경로. 앞부분이 같으면 포함하고, 폴더는 '/'로 끝낸다
#   known    목록을 받지 못했을 때(인터넷 · 요청 한도) 이름으로 직접 받아 볼 대표 파일
DAYS: dict[int, dict] = {
    1: {
        "date": "10/14(수)", "when": "이미 공개돼 있습니다", "marker": None,
        "prefixes": ("data/day1/", "labs/day1/", "data/data_dictionary.xlsx"),
        "known": (
            "data/day1/d1_buyers_raw.xlsx", "data/day1/d1_buyers_raw.csv",
            "data/day1/d1_invoices.xlsx", "data/day1/d1_invoices.csv",
            "data/day1/d1_encoding_test.csv", "data/day1/real_buyers_ratios.csv",
            "data/day1/reports/halden_fictional_annual_report.md", "data/day1/reports/irobot.md",
            "labs/day1/issue_definition_template.md", "data/data_dictionary.xlsx",
        ),
    },
    2: {
        "date": "10/15(목)", "when": "10/15(목) 08:30에 열리는 시작 파일이 있습니다", "marker": CK + "d2_",
        # workbench/day2/ · pytest.ini: 내 저장소를 1일차에 만들었어도 2일차 시작 틀(규칙 · 프롬프트 · 수집 점검 양식)이
        # 없으면 받는다(있는 파일은 덮어쓰지 않는다)
        "prefixes": (CK + "d2_", CK + "fx_krw_daily.csv", "labs/day2/", "workbench/day2/", "pytest.ini"),
        "known": (CK + "d2_start.xlsx", CK + "d2_news.csv", CK + "fx_krw_daily.csv",
                  "labs/day2/news_warmup_10.txt", CK + "d2_news_answer.csv",
                  "workbench/day2/prompts/news_score_v1.md", "workbench/day2/rules/수집점검.md", "pytest.ini",
                  "labs/day2/d2_excel_check.xlsx", "labs/day2/news_rows_001-050.csv", "labs/day2/news_rows_051-100.csv", "labs/day2/credit_notes/CN01_B053_ko.txt", "labs/day2/credit_notes/CN02_B040_en.txt", "labs/day2/credit_notes/credit_note_v1.md", "labs/day2/credit_notes/credit_note_score.schema.json"),
    },
    3: {
        "date": "10/16(금)", "when": "10/16(금) 08:30에 열리는 시작 파일이 있습니다", "marker": CK + "d3_",
        # workbench/day3/: 내 저장소를 1일차에 만들었어도 오늘의 규칙 파일(rules/d3_rules.md)이 없으면 받는다(있는 파일은 덮어쓰지 않는다)
        # labs/day3/quality_gate/(8교시 시연 6의 수강생판)와 18:00 비교 기준 d3_end_scored.csv도 같은 명령이 받는다
        "prefixes": (CK + "d3_", "labs/day3/", "workbench/day3/", "data/external/fred_dexkous.csv"),
        "known": (CK + "d3_start_features.csv", CK + "d3_start_scoring.csv", CK + "d3_features_panel.csv",
                  CK + "d3_end_scored.csv", "labs/day3/shap_sample_3buyers.csv", "labs/day3/d3_grade_banding.xlsx",
                  "labs/day3/fx_forecast_inputs.csv", "workbench/day3/rules/d3_rules.md",
                  "labs/day3/d3_grade_banding_example.xlsx", "labs/day3/d3_grade_example.csv"),
    },
    4: {
        "date": "10/19(월)", "when": "10/19(월) 08:30에 열리는 시작 파일이 있습니다", "marker": CK + "d4_",
        # 08:30 d4_* 체크포인트 · 14:45 기대값 테스트 2개(labs/day4/tests/) · 15:00 실습 B 파일(경보 테스트 · 참고 스크립트 · d4_report_input.json) ·
        # 18:00 d4_end_limits.xlsx(열기 시각) — 같은 명령을 다시 실행하면 새로 열린 파일만 받는다. 테스트는 작업 사본을 만들지 않는다(work_name)
        "prefixes": (CK + "d4_", "labs/day4/"),
        "known": (CK + "d4_start_scored.csv", CK + "d4_params.csv", CK + "d4_scenarios.csv", CK + "d4_open_inv.csv",
                  CK + "d4_limit_model.xlsx", CK + "d4_params_bug.csv", CK + "d4_report_input.json", CK + "d4_end_limits.xlsx",
                  "labs/day4/MODEL_SPEC.md", "labs/day4/stress_mc.py", "labs/day4/alert_rules.yml", "labs/day4/experiment_cards.md",
                  "labs/day4/tests/conftest.py", "labs/day4/tests/test_limits_props.py", "labs/day4/tests/test_stress_props.py",
                  "labs/day4/tests/test_limits_expected.py", "labs/day4/tests/test_stress_expected.py", "labs/day4/tests/test_ews_props.py",
                  "labs/day4/make_report.py", "labs/day4/check_numbers.py", "labs/day4/ews_example.py",
                  "labs/day4/d4_cards_check.xlsx"),
    },
    5: {
        "date": "10/20(화)", "when": "10/20(화) 08:30에 열리는 시작 파일이 있습니다", "marker": CK + "d5_",
        # 08:30 d5_start.csv(열기 시각). 규정 PDF · 골든셋 · 질문 목록 · 평가 시트(rag/), 요구사항 카드 · 톤 표(labs/day5/), 기록 양식(workbench/day5/)은
        # 템플릿에 이미 들어 있다 — 내 저장소를 일찍 만들어 없는 파일이 있으면 같은 경로로 받는다(있는 파일은 덮어쓰지 않는다).
        # labs/day5/ 의 요구사항 카드 · 톤 표는 workbench/day5/data/ 에 작업 사본으로도 놓인다(실습 B2 · B4에서 이 사본을 고친다)
        "prefixes": (CK + "d5_", CK + "d3_start_scoring.csv", CK + "d4_start_scored.csv", CK + "d4_params.csv",
                     CK + "d4_scenarios.csv", CK + "fx_krw_daily.csv", "labs/day5/", "rag/", "workbench/day5/", "app/sample_data/", "models/",
                  CK + "d3_start_features.csv"),
        "known": (CK + "d5_start.csv", CK + "d3_start_scoring.csv", CK + "d4_start_scored.csv",
                  CK + "d4_params.csv", CK + "d4_scenarios.csv", CK + "fx_krw_daily.csv",
                  "rag/corpus/hanbit_credit_policy.pdf", "rag/corpus/hanbit_credit_policy.md", "rag/goldset_20.csv",
                  "rag/goldset_questions.csv", "rag/eval_sheet_template.xlsx",
                  "labs/day5/spec_fx_tile.md", "labs/day5/tone_matrix.csv",
                  "workbench/day5/outputs/baseline.md", "workbench/day5/outputs/rag_report.md", "workbench/day5/links.md",
                  "models/day3_lgbm.pkl", "models/day3_lgbm.txt", "models/feature_list.json",
                  "models/grade_cutoffs.json", "models/metrics.json", "models/model_card.md",
                  CK + "d3_start_features.csv", "labs/day5/a2_baseline_check.md", "labs/day5/b3_fx_check.md", "labs/day5/b4_tone_impact.md"),
    },
    6: {
        "date": "10/21(수)", "when": "10/21(수) 09:28 카드 · 데이터 팩 → 11:15 → 11:30 → 13:15 자동 공개(시각마다 같은 명령을 다시 실행합니다)", "marker": CK + "d6_",
        "prefixes": (CK + "d6_", "labs/day6/",
                  CK + "d4_start_scored.csv", CK + "d4_params.csv", CK + "d4_scenarios.csv", CK + "d4_open_inv.csv", CK + "d4_limit_model.xlsx"),
        "known": (CK + "d6_crisis_pack.xlsx", CK + "d6_card5_stage2.xlsx",
                  *(f"{CK}d6_teams/team_{t:02d}.xlsx" for t in range(1, 6)),
                  CK + "d4_start_scored.csv", CK + "d4_params.csv", CK + "d4_scenarios.csv", CK + "d4_open_inv.csv", CK + "d4_limit_model.xlsx"),
    },
}

# 목록(_index.json)을 읽지 못할 때만 쓰는 최소 '열기 시각'(UTC). 목록을 읽으면 목록이 이긴다 — 시각을 바꿀 일은 목록에서.
OPEN_AT_FALLBACK = {
    CK + "d2_start.xlsx": "2026-10-14T23:30:00Z",                 # 10/15 08:30 KST — 1일차 답이 들어 있다
    CK + "d2_news_answer.csv": "2026-10-15T06:35:00Z",            # 10/15 15:35 — 골든셋
    CK + "d3_start_features.csv": "2026-10-15T23:30:00Z",         # 10/16 08:30 — 2일차 결과
    CK + "d3_start_scoring.csv": "2026-10-15T23:30:00Z",
    CK + "d3_features_panel.csv": "2026-10-15T23:30:00Z",
    "labs/day3/shap_sample_3buyers.csv": "2026-10-15T23:30:00Z",
    CK + "d3_end_scored.csv": "2026-10-16T09:00:00Z",             # 10/16 18:00
    CK + "d4_start_scored.csv": "2026-10-18T23:30:00Z",           # 10/19 08:30 — 3일차 결과
    CK + "d4_limit_model.xlsx": "2026-10-18T23:30:00Z",
    "models/": "2026-10-18T23:30:00Z",
    "labs/day4/tests/test_limits_expected.py": "2026-10-19T05:45:00Z",   # 10/19 14:45
    "labs/day4/tests/test_stress_expected.py": "2026-10-19T05:45:00Z",
    "labs/day4/tests/test_ews_props.py": "2026-10-19T06:00:00Z",          # 15:00
    "labs/day4/ews_example.py": "2026-10-19T06:00:00Z",
    "labs/day4/make_report.py": "2026-10-19T06:00:00Z",
    "labs/day4/check_numbers.py": "2026-10-19T06:00:00Z",
    CK + "d4_report_input.json": "2026-10-19T06:00:00Z",
    CK + "d4_end_limits.xlsx": "2026-10-19T09:00:00Z",            # 18:00
    CK + "d5_start.csv": "2026-10-19T23:30:00Z",                  # 10/20 08:30 — 4일차 결과
    "labs/day2/d2_excel_check.xlsx": "2026-10-14T23:30:00Z",         # 10/15 08:30 — 2일차 엑셀 검산본(d2_start와 같은 데이터)
    "labs/day3/d3_grade_banding_example.xlsx": "2026-10-15T23:30:00Z",  # 10/16 08:30 — 3일차 등급 완성본
    "labs/day3/d3_grade_example.csv": "2026-10-15T23:30:00Z",
    "labs/day4/d4_cards_check.xlsx": "2026-10-19T05:15:00Z",         # 10/19 14:15 — 실험 카드 ⑥ ⑧ ⑨ 확인표
    "labs/day5/b4_tone_impact.md": "2026-10-19T23:30:00Z",           # 10/20 08:30 — 5일차 톤 영향 완성본
}

IGNORE_NAMES = {".gitkeep", ".DS_Store", "Thumbs.db", "desktop.ini"}
IGNORE_DIRS = {"__pycache__", ".ipynb_checkpoints", "sec_cache", ".git", ".venv"}

# 작업 사본(workbench/dayN/data/) — 실습에서 고쳐 쓰는 '데이터' 파일만 둔다(원본 data/ · labs/ 는 읽기만).
#   사본을 만드는 것: data/ 아래 표 · JSON(.csv · .xlsx · .json · .txt) — 정책 숫자 · 시나리오 · 지표 JSON처럼 바꿔 보는 파일
#   만들지 않는 것: labs/ 의 프롬프트 · 양식 · 참고 파일 · 코드 · 테스트 · 워크플로, 읽기만 하는 보고서(.md),
#                  완성본 · 비교 기준(먼저 내 결과를 만든 뒤 원본 자리에서 견준다)
COPY_EXT = (".csv", ".xlsx", ".json", ".txt")
COPY_ONLY = {                       # 이 일차는 이 파일만 사본을 만든다
    5: ("labs/day5/spec_fx_tile.md", "labs/day5/tone_matrix.csv"),   # 실습 B2 · B4에서 고친다 — 앱은 data/checkpoints/ 원본을 읽는다
    6: (),                                                          # 6일차는 팀 저장소(킷)에서 일한다
}
NO_COPY_BADGES = ("완성본", "비교 기준")
NO_COPY_NAMES = ("_check", "_example", "_answer", "_expected", "_end_", "_limit_model")   # 목록을 읽지 못했을 때 완성본 · 비교 기준을 이름으로 가린다


class NetError(Exception):
    """인터넷 문제 — 사람이 읽을 이유를 담는다."""


# ---------------------------------------------------------------- 작은 도구들
def say(msg: str = "") -> None:
    print(msg, flush=True)


def ignored(rel: str) -> bool:
    parts = rel.split("/")
    name = parts[-1]
    return (name in IGNORE_NAMES or name.startswith("~$") or name.endswith((".part", ".pyc", ".tmp"))
            or any(d in IGNORE_DIRS for d in parts[:-1]))


def safe(rel: str) -> bool:
    """과정 저장소 목록에서 온 경로가 저장소 안쪽을 가리킬 때만 쓴다."""
    p = PurePosixPath(rel)
    return bool(rel) and not p.is_absolute() and ".." not in p.parts and "\\" not in rel and ":" not in rel


def at(rel: str) -> Path:
    return REPO.joinpath(*rel.split("/"))


def work_name(rel: str, day: int, entry: dict | None = None) -> str | None:
    """작업 사본 이름(workbench/dayN/data/ 아래) — 사본을 만들지 않는 파일이면 None."""
    if day in COPY_ONLY:
        return rel.rsplit("/", 1)[-1] if rel in COPY_ONLY[day] else None
    p = rel.split("/")
    if p[0] != "data" or not p[-1].lower().endswith(COPY_EXT):
        return None
    if entry:
        if entry.get("badge") in NO_COPY_BADGES or entry.get("role") == "baseline":
            return None
    elif any(x in p[-1] for x in NO_COPY_NAMES):
        return None
    return "/".join(p[2:] if len(p) >= 3 else p[1:])   # data/day1/x · data/checkpoints/x → x,  data/파일 → 파일


def mine(rel: str) -> bool:
    """workbench/dayN/data/(작업 사본) · workbench/dayN/outputs/(내 결과) — '그날 파일'로 세지 않는다."""
    p = rel.split("/")
    return len(p) >= 3 and p[0] == "workbench" and p[2] in ("data", "outputs")


def net_reason(err: BaseException) -> str:
    reason = getattr(err, "reason", err)
    if isinstance(reason, ssl.SSLError):
        return "보안 인증서 오류(회사 망의 보안 장비 때문일 수 있습니다)"
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "응답이 없습니다(시간 초과)"
    return "인터넷에 연결하지 못했습니다"


NET_ERRORS = (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, ssl.SSLError,
              http.client.HTTPException)


# ---------------------------------------------------------------- 목록(_index.json) · 열기 시각
def load_index() -> dict | None:
    """files 브랜치의 수업 파일 목록. 못 읽으면 None(= 대표 파일 이름으로 직접 받아 본다)."""
    req = urllib.request.Request(FILES_BASE + f"_index.json?t={int(time.time())}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
    except (urllib.error.HTTPError, ValueError) + NET_ERRORS:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        return None
    return data


def utc(ts: str):
    import datetime as _dt
    return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def kst(t) -> str:
    import datetime as _dt
    k = t.astimezone(_dt.timezone(_dt.timedelta(hours=9)))
    return f"{k.month}/{k.day}({'월화수목금토일'[k.weekday()]}) {k:%H:%M}"


def later_reason(entry: dict | None, t) -> str:
    """'[열기 전]' 줄 끝의 이유 — 목록 항목의 구분(badge · role)과 열기 시각으로 고른다."""
    import datetime as _dt
    e = entry or {}
    k = t.astimezone(_dt.timezone(_dt.timedelta(hours=9)))
    morning = (k.hour, k.minute) <= (9, 0)
    if e.get("badge") == "완성본":
        return "시작 파일과 같은 데이터로 만든 완성본이라 그날 아침에 엽니다" if morning else "그날 실습 시각에 여는 완성본"
    if e.get("badge") == "비교 기준" or e.get("role") == "baseline":
        return "먼저 내 결과를 만든 뒤 견주는 비교 기준"
    if not e:
        return "정한 시각에 여는 파일"
    if morning:
        return "전날 실습의 결과가 들어 있어 그날 아침에 여는 시작 파일" if e.get("role") == "start" else "그날 아침에 여는 파일"
    return "그날 실습 시각에 맞춰 여는 파일"


def open_at_of(rel: str, entry: dict | None, have_index: bool):
    """이 파일을 내 폴더에 들이는 시각(UTC). 없으면 None."""
    ts = (entry or {}).get("open_at")
    if not ts and not have_index:
        ts = next((v for k, v in OPEN_AT_FALLBACK.items() if rel == k or (k.endswith("/") and rel.startswith(k))), None)
    return utc(ts) if ts else None


# ---------------------------------------------------------------- 파일 목록
def local_files(prefixes) -> set[str]:
    """이 저장소 안에서 그날 파일로 보는 경로를 찾는다."""
    found: set[str] = set()
    for pre in prefixes:
        if not pre.endswith("/") and at(pre).is_file():
            found.add(pre)
            continue
        folder = pre.rpartition("/")[0]
        base = at(folder) if folder else REPO
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if f.is_file():
                rel = f.relative_to(REPO).as_posix()
                if rel.startswith(pre) and not ignored(rel) and not mine(rel):
                    found.add(rel)
    return found


def remote_files(prefixes) -> tuple[set[str] | None, str]:
    """과정 저장소(공개)의 파일 목록 중 그날 것. 못 받으면 (None, 이유)."""
    req = urllib.request.Request(TREE_URL, headers={
        "User-Agent": USER_AGENT, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            return None, "GitHub 목록 조회가 잠시 막혔습니다(여럿이 동시에 쓰면 그럴 수 있습니다)"
        return None, f"GitHub가 {e.code} 오류를 돌려주었습니다"
    except NET_ERRORS + (ValueError,) as e:
        return None, net_reason(e)
    paths = {t["path"] for t in data.get("tree", []) if t.get("type") == "blob"}
    return {p for p in paths if safe(p) and not ignored(p) and any(p.startswith(x) for x in prefixes)}, ""


def fetch(rel: str, dest: Path, entry: dict | None = None) -> bool:
    """과정 저장소에서 rel 을 dest 로 받는다 — 목록이 files라고 하면 files 브랜치부터, 아니면 main부터.
    아직 없으면(404) False, 인터넷 문제 · 해시 불일치는 NetError."""
    bases = (FILES_BASE, RAW_BASE) if (entry or {}).get("where", "files") != "main" else (RAW_BASE, FILES_BASE)
    sha = (entry or {}).get("sha256") if (entry or {}).get("where") != "main" else None
    last: NetError | None = None
    for base in bases:
        try:
            if _fetch_from(base, rel, dest, sha):
                return True
        except NetError as e:          # 한쪽이 막혀도 다른 쪽(main ↔ files)을 마저 본다
            last = e
    if last:
        raise last
    return False


def _fetch_from(base: str, rel: str, dest: Path, sha256: str | None) -> bool:
    url = base + urllib.parse.quote(rel) + f"?t={int(time.time())}"  # ?t= : 방금 올라온 파일이 캐시에 가려지지 않게
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    try:
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, open(tmp, "wb") as out:
                shutil.copyfileobj(resp, out)
                want = resp.headers.get("Content-Length")
            if want and want.isdigit() and tmp.stat().st_size != int(want):
                raise NetError("받는 도중 연결이 끊겼습니다")
            if sha256:
                import hashlib
                if hashlib.sha256(tmp.read_bytes()).hexdigest() != sha256:
                    raise NetError("받은 파일이 목록의 해시와 다릅니다(방금 바뀐 파일일 수 있습니다 — 1–2분 뒤 다시 실행하세요)")
            os.replace(tmp, dest)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False
            raise NetError(f"서버가 {e.code} 오류를 돌려주었습니다") from e
        except NET_ERRORS as e:
            raise NetError(net_reason(e)) from e
    finally:
        if tmp.exists():
            tmp.unlink()


# ---------------------------------------------------------------- 본 작업
def run(day: int, args) -> int:
    cfg = DAYS[day]
    prefixes, marker, known = cfg["prefixes"], cfg["marker"], set(cfg["known"])
    say(f"== {day}일차 파일 받기 ({cfg['date']}) ==")
    import datetime as _dt
    nowu = _dt.datetime.now(_dt.timezone.utc)

    # 1) 어떤 파일인가 — 내 저장소에 있는 것 + 과정 저장소의 수업 파일 목록(files 브랜치) + main 목록
    local = local_files(prefixes)
    remote: set[str] | None = None
    index: dict | None = None
    entries: dict[str, dict] = {}
    upcoming: list[dict] = []
    if args.offline:
        say("(인터넷을 쓰지 않는 모드 — 이 저장소에 있는 파일만 다룹니다)")
        fetchable: set[str] = set()
    else:
        index = load_index()
        remote, why = remote_files(prefixes)
        if index is not None:
            for e in index.get("files", []):
                rel = str(e.get("path") or "")
                if not rel or not safe(rel) or ignored(rel) or e.get("role") in ("handout", "rehearsal", "after"):
                    continue
                if e.get("day") == day or any(rel.startswith(x) for x in prefixes):
                    if rel not in entries or e.get("day") == day:   # 같은 파일이 여러 일차에 있으면 오늘 일차의 항목(구분 · 시각)을 쓴다
                        entries[rel] = e
            upcoming = [b for b in index.get("bundles", []) if b.get("day") == day and not b.get("released")]
            say("과정 저장소(공개)의 수업 파일 목록을 확인했습니다.")
        else:
            say("(수업 파일 목록을 읽지 못했습니다 — 대표 파일 이름으로 직접 받아 봅니다)")
        if remote is None and index is None:
            say(f"(과정 저장소의 파일 목록도 확인하지 못했습니다 — {why})")
        fetchable = (remote or set()) | set(entries) | (known if index is None else set())
    listing_known = args.offline or index is not None  # 무엇이 공개됐는지 확실히 안다

    # 열기 시각 — '내 폴더에 들이는 때'(파일은 이미 공개돼 있다). --now 로 앞당길 수 있다.
    later: dict[str, object] = {}
    if not args.now:
        for rel in sorted(fetchable):
            t = open_at_of(rel, entries.get(rel), index is not None)
            if t and t > nowu and not at(rel).is_file():
                later[rel] = t
        fetchable = fetchable - set(later)
    wanted = sorted(local | fetchable | set(later))

    def released(files) -> bool:
        return marker is None or any(f.startswith(marker) for f in files)

    if index is None and listing_known and not released(wanted):
        return not_released(day, cfg, upcoming)

    # 2) 내 저장소에 없는 파일을 같은 경로로 받는다
    results: dict[str, str] = {}  # 경로 → new | have | miss | err | later
    problem = ""
    for rel in wanted:
        can_fetch = rel in fetchable
        if at(rel).is_file() and not (args.force and can_fetch):
            results[rel] = "have"
        elif rel in later:
            results[rel] = "later"
        elif not can_fetch:
            results[rel] = "miss"
        elif args.list:
            results[rel] = "new"
        else:
            try:
                hint = entries.get(rel) or ({"where": "main"} if remote and rel in remote else None)
                results[rel] = "new" if fetch(rel, at(rel), hint) else "miss"
            except NetError as e:
                results[rel], problem = "err", str(e)
            except PermissionError:
                results[rel], problem = "err", "파일을 저장하지 못했습니다(엑셀 등에서 열어 둔 파일이면 닫고 다시 실행하세요)"
            except OSError as e:
                results[rel], problem = "err", f"파일을 저장하지 못했습니다({e.__class__.__name__})"

    have_now = [r for r, s in results.items() if s in ("new", "have")]
    if index is None and not listing_known and not args.list and not released(have_now):
        if problem:  # 받아 보려 했으나 인터넷 문제
            say("")
            say(f"{day}일차 파일을 받지 못했습니다 — {problem}.")
            say("인터넷 연결을 확인하고 다시 실행하세요. 계속 안 되면 과정 사이트의 '파일 받기'에서 직접 받습니다:")
            say(f"    {SITE_URL}day{day}/index.html")
            return 1
        return not_released(day, cfg, upcoming)

    # 3) 작업 사본 — workbench/dayN/data/
    wb_root = REPO / "workbench" / f"day{day}" / "data"
    copies: dict[str, str] = {}
    for rel in ([] if KIT else have_now):
        name = work_name(rel, day, entries.get(rel))
        if name is None:
            continue
        dest = wb_root.joinpath(*name.split("/"))
        if dest.exists() and not args.force:
            copies[rel] = "have"
        elif args.list:
            copies[rel] = "new"
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(at(rel), dest)
            copies[rel] = "new"

    # 4) 결과 보고
    label = {"new": "받을 예정" if args.list else "받음", "have": "있음", "miss": "공개 전", "err": "오류", "later": "열기 전"}
    clabel = {"new": "사본 만들 예정" if args.list else "사본 만듦", "have": "사본 있음"}
    for rel in wanted:
        if results[rel] == "miss" and listing_known:
            continue
        tail = f"  ({clabel[copies[rel]]})" if rel in copies else ""
        if results[rel] == "later":
            tail = f"  ({kst(later[rel])} 이후에 받습니다 — {later_reason(entries.get(rel), later[rel])})"
        say(f"  [{label[results[rel]]}] {rel}{tail}")

    def count(d: dict, key: str) -> int:
        return sum(1 for v in d.values() if v == key)

    miss = count(results, "miss") if not listing_known else 0
    say("")
    say(f"요약: {'받을 예정' if args.list else '새로 받음'} {count(results, 'new')}개 · 이미 있음 {count(results, 'have')}개 · "
        f"작업 사본 {'만들 예정' if args.list else '새로 만듦'} {count(copies, 'new')}개 · 사본 이미 있음 {count(copies, 'have')}개"
        + (f" · 열기 전 {count(results, 'later')}개" if count(results, "later") else "")
        + (f" · 아직 공개 전 {miss}개" if miss else "") + (f" · 오류 {count(results, 'err')}개" if count(results, "err") else ""))
    if later:
        say("열기 전 파일은 그 시각이 지난 뒤 같은 명령을 다시 실행하면 받습니다. (지금 꼭 필요하면 --now — 먼저 내 결과를 만든 뒤에)")
    due: list[str] = []   # 시각은 지났는데 아직 올라오지 않은 자동 공개 묶음(보통 1–2분 늦는다) — 출력 맨 끝에 다시 알린다
    if upcoming:
        say("자동 공개 시각(그 시각 뒤에 같은 명령을 다시 실행하면 새로 올라온 파일만 더 받습니다):")
        for b in sorted(upcoming, key=lambda x: x.get("at", "")):
            t = utc(b["at"])
            if t <= nowu:
                due.append(kst(t).split(" ")[-1])
            say(f"    {kst(t)}  {b.get('note', '')}" + ("  ← 시각이 지났는데 아직 올라오지 않았습니다" if t <= nowu else ""))

    def done(code: int) -> int:
        if due:
            say("")
            say(f"{' · '.join(due)} 자동 공개 파일은 시각이 지났는데 아직 올라오지 않았습니다 — 보통 1–2분 늦게 올라오니 "
                "잠시 뒤 같은 명령을 다시 실행하세요(강사가 공개 시각을 늦췄다고 알리면 그 시각 뒤에).")
        return code

    if problem:
        say(f"일부 파일을 받지 못했습니다 — {problem}. 잠시 뒤 같은 명령을 다시 실행하세요.")
    if miss:
        say("공개 전인 파일은 공개 시각이 지난 뒤 같은 명령을 다시 실행하면 받습니다.")
    say("")
    if args.list:
        say("목록만 보았습니다 — 파일은 바꾸지 않았습니다.")
        return done(0)
    say("다음")
    if KIT:  # 팀 저장소 — workbench/ 없이 킷 폴더에 둔다
        say("  - 받은 파일은 과정 저장소와 같은 경로(data/checkpoints/ · labs/)에 들어옵니다. 이 두 폴더는 .gitignore에 있어 커밋되지 않습니다.")
        if day == 6:
            say("  - 우리 팀 카드(labs/day6/crisis_cards/card{번호}_*.md)는 cards/ 로, 우리 팀 팩(data/checkpoints/d6_teams/team_0{조}.xlsx)은 data/input/ 으로 복사한 뒤 커밋하세요(다른 팀 파일은 옮기지 않습니다).")
            say("  - 4일차 입력 4개(data/checkpoints/d4_start_scored.csv · d4_params.csv · d4_scenarios.csv · d4_open_inv.csv)와 환율 파일(fx_krw_daily.csv)도 data/input/ 으로 복사합니다.")
            say("  - 입력 커밋은 브랜치 · PR 없이 main에 바로 커밋 · push — 팀원은 git pull 한 번으로 같은 입력을 받습니다.")
            say("  - 자동 공개: 09:28 카드 · 데이터 팩 / 11:15 카드 ⑤ 2단계 / 11:30 인젝트 1 / 13:15 인젝트 2 — 그때마다 같은 명령을 다시 실행하면 새로 올라온 파일만 더 받습니다.")
        say("  - 결과 파일은 out/ (프롬프트가 정한 폴더)에, 코드는 app/pipeline/ 에 둡니다.")
        return done(1 if count(results, "err") else 0)
    if copies:
        say(f"  - 원본(data/, labs/)은 고치지 않습니다. 고쳐 쓸 데이터는 작업 사본 workbench/day{day}/data/ 에서 다룹니다"
            " (프롬프트 · 양식 · 완성본 · 비교 기준은 원본 자리에서 읽습니다).")
    else:
        say("  - 원본(data/, labs/)은 고치지 않습니다. 고쳐 쓸 파일이 있으면 복사해서 씁니다.")
    say(f"  - 결과 파일은 workbench/day{day}/outputs/ 에 저장합니다.")
    if day >= 2:
        say("  - 열기 시각이 있는 날은 그 시각 뒤에 같은 명령을 다시 실행하면 새로 열린 파일만 더 받습니다.")
    return done(1 if count(results, "err") else 0)


def not_released(day: int, cfg: dict, upcoming: list | None = None) -> int:
    say("")
    if upcoming:
        say(f"{day}일차 파일은 정한 시각에 자동으로 올라옵니다:")
        for b in sorted(upcoming, key=lambda x: x.get("at", "")):
            say(f"    {kst(utc(b['at']))}  {b.get('note', '')}")
    else:
        say(f"{day}일차 파일을 아직 받을 수 없습니다 — {cfg['when']}")
    say("그 시각이 지난 뒤 같은 명령을 다시 실행하세요:")
    say(f"    uv run python tools/get_day_files.py {day}")
    if not KIT:  # 팀 저장소(킷)에는 labs/ 가 없다
        say(f"labs/day{day}/ 의 실습 양식은 이미 저장소에 있으니 미리 열어 봐도 됩니다.")
    say(f"급하면 과정 사이트의 '파일 받기'를 확인하세요: {SITE_URL}day{day}/index.html")
    return 0


class Parser(argparse.ArgumentParser):
    def error(self, message: str):  # argparse 기본 영어 안내 대신 한국어로
        say(f"사용법이 맞지 않습니다: {message}")
        say("")
        say("예)  uv run python tools/get_day_files.py 1      (1~6 중 오늘 일차)")
        say("     uv run python tools/get_day_files.py 2 --list")
        raise SystemExit(2)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows 터미널에서도 한글이 깨지지 않게
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = Parser(add_help=False)
    ap.add_argument("day", nargs="?")
    ap.add_argument("--list", action="store_true", help="받지 않고 목록만 보기")
    ap.add_argument("--force", action="store_true", help="이미 있는 파일도 다시 받아 덮어쓰기")
    ap.add_argument("--offline", action="store_true", help="인터넷 없이, 이 저장소에 있는 파일만 다루기")
    ap.add_argument("--now", action="store_true", help="열기 시각 전인 비교 기준 파일도 지금 받기")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()
    if args.help or args.day is None:
        say(__doc__)
        return 0 if args.help else 2
    text = str(args.day).lower().replace("day", "").replace("일차", "").strip()
    if not text.isdigit() or int(text) not in DAYS:
        ap.error(f"일차는 1~6 중 하나여야 합니다(입력: {args.day})")
    return run(int(text), args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        say("\n중단했습니다. 받다 만 파일은 지워졌으니 같은 명령을 다시 실행하면 됩니다.")
        sys.exit(130)
