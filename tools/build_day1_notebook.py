#!/usr/bin/env python
"""Day1 Challenge 노트북 `labs/day1/d1_challenge.ipynb`를 nbformat으로 만든다(출력 없는 수강생용).

(v3 — 이번 과정은 쓰지 않는다) 1일차 Challenge 노트북(Step 1–6) 생성기.
v3(2026-10-07): 섹션 안내의 실습 위치를 v2 Lab1·Lab2에서 v3 블록 A·B Step 번호로 바꿨다(계산 셀은 그대로).
섹션: 0 준비 · A 공시 재무비율(SEC companyfacts) · B 인보이스 원장 EDA(d1_invoices) · C AI와 함께 확장 · D 셀프 체크.

사용(저장소 루트에서):
  python tools/build_day1_notebook.py                     # 노트북만 만든다(출력·실행 번호 없음)
  python tools/build_day1_notebook.py --org myorg         # Colab 배지·RAW_BASE의 <org>를 바꿔서 만든다
  python tools/build_day1_notebook.py --execute --user-agent "Gildong Hong gildong.hong@mycompany.com"
                                                          # + 실행 검사: 사본을 임시 폴더에서 위→아래로 실행해
                                                          #   강사용 실행본(../instructor/day1/answers/d1_challenge_executed.ipynb) 저장
  python tools/build_day1_notebook.py --execute --user-agent "..." --colab-sim --no-write
                                                          # Colab 흉내: 저장소 밖 빈 폴더에서 실행, 데이터는 로컬 HTTP(RAW_BASE)로
                                                          #   내려받고 글꼴은 GitHub에서 받는다(인터넷 필요). 실행본은 임시 폴더에

실행 검사(--execute)에서만 하는 일 — 수강생 노트북 파일은 바뀌지 않는다:
  - A-1 셀의 USER_AGENT 자리표시자를 --user-agent 값으로 바꿔 SEC에 접속한다. 값은 실행하는 사람의 영문 이름 + 이메일
    (SEC 규칙, 예: "Gildong Hong gildong.hong@mycompany.com"). 기본값은 없다 — --execute에 --user-agent가 없으면 멈춘다.
  - 맨 끝에 '강사용 검산 셀'을 붙여 핵심 값을 JSON으로 뽑고, 아래 기준 파일과 대조한다(파일이 없으면 그 항목은 건너뜀).
      · docs/assets/day1/day1_fig4_dpd_distribution.csv(연체 인보이스 수) · data/raw/invoices.csv(dpd_final 정답 열)
      · data/day1/real_buyers_ratios.csv(iRobot FY2024 · Wolfspeed FY2025)
      · ../instructor/day1/answers/d1_buyers_clean.csv(바이어 단위 연체·에이징, 강사 정답)
  - 셀 오류가 나면 실패한 셀까지 '*_FAILED.ipynb'로 저장하고, 오류나 대조 불일치가 있으면 종료 코드 1.
  - 공개 저장소 파일이므로 누구의 연락처(이메일)도 코드에 기본값으로 적지 않는다.
필요 패키지: nbformat(생성), nbclient·ipykernel·pandas(실행 검사).
"""
from __future__ import annotations

import argparse
import copy
import functools
import http.server
import json
import os
import re
import shutil
import sys
import tempfile
import textwrap
import threading
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = Path(__file__).resolve().parents[1]
NB_PATH = REPO / "labs" / "day1" / "d1_challenge.ipynb"
ANSWERS = REPO.parent / "instructor" / "day1" / "answers"   # config.yaml outputs.answers_dir 기본값과 같은 곳(공개 저장소 밖)
UA_PLACEHOLDER = 'USER_AGENT = "Your Name your.email@example.com"'


def user_agent_problem(ua: str | None) -> str | None:
    """--user-agent 값 점검(노트북 A-1 셀의 ua_ok()와 같은 기준 + 파이썬 문자열에 그대로 넣을 수 있는지). 문제가 없으면 None."""
    if not ua or not ua.strip():
        return "--execute에는 --user-agent \"영문 이름 이메일\"이 필요합니다(기본값 없음)"
    if not ua.isascii() or "@" not in ua or "example.com" in ua:
        return "--user-agent는 영문 이름과 실제 이메일이어야 합니다(한글·예시 주소 example.com 불가)"
    if any(ch in ua for ch in '"\\\n\r'):
        return "--user-agent에 따옴표·역슬래시·줄바꿈은 넣을 수 없습니다"
    return None


def md(cid: str, text: str):
    return ("markdown", cid, text)


def code(cid: str, text: str):
    return ("code", cid, text)


# ----------------------------------------------------------------------------------------------------
# 노트북 셀 — 순서가 곧 노트북 순서. 코드 셀 첫 줄은 "이 셀이 하는 일" 한국어 주석 한 줄.
# ----------------------------------------------------------------------------------------------------
CELLS = [
    md("title", r'''
# Day1 Challenge 노트북 — 공시 재무비율 · 인보이스 원장 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<org>/tradefin-ai-2026/blob/main/labs/day1/d1_challenge.ipynb)

**생성형 AI 기반 무역 금융 리스크 최적화 과정 · Day1 (2026-10-14) · Challenge 트랙**

오늘 실습 두 개를 코드로 한 번 더 합니다. Basic 실습에서 AI가 낸 숫자를, 여기서는 **직접 계산한 숫자로 검산**합니다.

| 섹션 | 언제 | 하는 일 | 이어지는 Basic 실습 |
|---|---|---|---|
| 0 준비 | 시작 5분 | 버전 확인 · 한글 글꼴 · 데이터 불러오기 | — |
| A 공시 재무비율 | 블록 A Step 2–3 (13:28–14:20) | 미국 SEC 공시 데이터로 비율 4개를 계산하고 AI 답과 대조 | Step 3 (P1-2 비율 → SEC 수치 대조) |
| B 인보이스 원장 EDA | 블록 A Step 4 → 블록 B Step 5–6 (14:24–16:10) | 인보이스 원장으로 연체일 분포 · 결제방식별 연체(B-1~B-4) · 코호트 연체율 · 구간 전이 · DSO(B-5~B-7) · 3자 대조(B-8, 16:00 정답 공개 뒤) | Step 4 (P1-4 요약) · Step 6 (AI 숫자와 피벗 숫자 대조) |
| C AI와 함께 확장 | 남는 시간 | Gemini in Colab 또는 Claude에게 분석 확장을 맡기고 검증하기 | — |
| D 셀프 체크 | 마지막 5분 | 질문 3개에 답 적기 | — |

### 시작하기
1. 위의 **Open in Colab** 배지를 누릅니다. 배지가 안 열리면 colab.research.google.com에 들어가 **파일(File) → 노트북 업로드(Upload notebook)** 를 누르고 `d1_challenge.ipynb`를 고릅니다.
2. Colab 메뉴에서 **파일(File) → Drive에 사본 저장(Save a copy in Drive)** 을 누릅니다. 내 사본에서 작업해야 저장됩니다.
3. 첫 번째 코드 셀을 클릭하고 **Shift + Enter** 를 누릅니다. 셀이 실행되고 다음 셀로 넘어갑니다.
4. 같은 방법으로 위에서 아래로 한 셀씩 실행합니다. 코드 셀 첫 줄의 `#` 주석이 "이 셀이 하는 일"입니다.

> **데이터 위생** — 이 노트북은 (가상) 한빛정밀(주) 교육용 합성 데이터와 미국 SEC 공개 공시만 씁니다. 회사 실데이터(바이어명·담당자·계좌)는 이 노트북에도, Colab AI에도 넣지 않습니다. AI 대화창은 외부 채널입니다.

> **막히면** — 오류 메시지의 마지막 줄을 옆 사람이나 강사에게 보여 주세요. 실행이 꼬이면 **런타임(Runtime) → 세션 다시 시작(Restart session)** 을 누르고 맨 위부터 다시 실행합니다.
'''),
    md("s0", r'''
## 0. 준비 (5분)

아래 코드 셀 세 개를 차례로 실행합니다.

1. **0-1 버전 확인** — 숫자만 보고 넘어갑니다.
2. **0-2 한글 글꼴** — 그래프의 한글이 □로 깨지지 않게 합니다. Colab에서는 글꼴 파일을 한 번 내려받습니다(몇 초).
3. **0-3 데이터 도우미** — 파일을 ① 내 컴퓨터의 과정 저장소 폴더 → ② 과정 저장소 웹 주소(`RAW_BASE`) → ③ 직접 업로드 순서로 찾습니다. ③이 뜨면 셀 아래 **파일 선택(Choose Files)** 버튼을 누르고, 과정 사이트 → Day1 → 파일 받기에서 미리 받아 둔 파일을 고릅니다.
'''),
    code("c0-1", r'''
# 0-1. 파이썬·라이브러리 버전을 확인하고, 표의 숫자를 읽기 쉽게(천 단위 쉼표·소수 둘째 자리) 보이게 한다
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

print("Python    ", sys.version.split()[0])   # Colab 2026.07 런타임은 3.12, 다음 런타임은 3.13 — 둘 다 동작
print("pandas    ", pd.__version__)
print("numpy     ", np.__version__)
print("matplotlib", matplotlib.__version__)
pd.set_option("display.float_format", "{:,.2f}".format)
pd.set_option("display.max_columns", 30)
'''),
    code("c0-2", r'''
# 0-2. 그래프 한글이 깨지지 않게 나눔고딕 글꼴을 등록하고 그래프 기본 모양을 정한다
import urllib.request
from pathlib import Path
from matplotlib import font_manager

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"

def find_upwards(rel):
    """지금 폴더와 위쪽 폴더(3단계까지)에서 rel 파일을 찾아 경로를 돌려준다. 없으면 None."""
    here = Path.cwd().resolve()
    for base in [here, *here.parents][:4]:
        if (base / rel).is_file():
            return base / rel
    return None

font_file = find_upwards("tools/fonts/NanumGothic-Regular.ttf") or Path("NanumGothic-Regular.ttf")
try:
    if not font_file.is_file():                                   # Colab: 저장소의 글꼴과 같은 파일을 한 번 받는다
        urllib.request.urlretrieve(FONT_URL, font_file.with_suffix(".part"))
        font_file.with_suffix(".part").rename(font_file)
    font_manager.fontManager.addfont(str(font_file))
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font_file)).get_name()
except Exception as e:
    print("글꼴 등록 실패 — 그래프 한글이 □로 보일 수 있지만 계산은 그대로 됩니다:", e)

plt.rcParams.update({"axes.unicode_minus": False, "figure.dpi": 100, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
BLUE, ORANGE, GRAY = "#1F5FD1", "#C2410C", "#666666"               # 과정 슬라이드 색(색각 이상 구분 검사 통과)
print("글꼴:", plt.rcParams["font.family"])
'''),
    code("c0-3", r'''
# 0-3. 데이터 파일을 찾아 주는 도우미 — ① 내 컴퓨터(과정 저장소 폴더) → ② 과정 저장소 웹 주소 → ③ 직접 업로드
RAW_BASE = "https://raw.githubusercontent.com/<org>/tradefin-ai-2026/main"   # <org>가 남아 있으면 강사가 알려 준 이름으로 바꾼다

def get_file(rel):
    """rel 예: 'data/day1/d1_invoices.csv' → 읽을 수 있는 파일 경로를 돌려준다."""
    found = find_upwards(rel) or find_upwards(Path(rel).name)     # ① 저장소 폴더나 지금 폴더에 있으면 그대로 쓴다
    if found:
        return found
    target = Path(rel)
    if "<org>" not in RAW_BASE:                                   # ② 웹 주소에서 한 번 받아 같은 경로에 저장한다
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"{RAW_BASE}/{rel}", target)
            return target
        except Exception as e:
            print("내려받기 실패:", e)
    try:                                                          # ③ Colab: 셀 아래 [파일 선택] 버튼으로 올린다
        from google.colab import files
    except ImportError:
        raise FileNotFoundError(f"{rel} 을(를) 찾지 못했습니다. 과정 저장소 폴더 안에서 실행하거나 RAW_BASE를 확인하세요.") from None
    print(f"'{target.name}' 파일을 골라 올려 주세요.")
    return Path(next(iter(files.upload())))

print("RAW_BASE:", RAW_BASE)
'''),
    # ------------------------------------------------------------------------------------------ A
    md("sA", r'''
## A. 공시 재무비율 — SEC 공시 데이터로 직접 계산해 AI 답과 대조하기 (Step 2–3 Challenge · 20–30분)

Step 3 Basic에서는 AI가 iRobot 발췌 파일을 읽고 비율을 계산했습니다(P1-2). 여기서는 같은 숫자를 **1차 출처**인 미국 SEC의 XBRL 공시 데이터에서 직접 꺼내 계산합니다. AI 숫자와 다르면, 어느 쪽이 왜 다른지 찾는 것이 목표입니다.

**용어 3개**
- **XBRL 태그** — 공시 숫자에 붙은 영문 이름표입니다. 예: 유동자산 = `AssetsCurrent`. 같은 항목이라도 회사·공시마다 다른 태그를 쓸 수 있습니다.
- **companyfacts API** — 한 회사가 공시한 모든 태그 값을 파일(JSON) 하나로 주는 SEC 서비스입니다. 무료이고 키가 필요 없습니다.
- **CIK · 공시번호(accn)** — CIK는 SEC의 회사 번호, accn은 공시 한 건의 접수 번호입니다. 같은 날짜의 숫자라도 어느 공시에서 왔는지 accn으로 확인합니다.

**변수 정의서** — 슬라이드 D1-34의 7칸 약속(변수·정의·공식·단위·출처·기준일·주의)에 영업이익률을 더했습니다.

| 변수 | 정의 | 공식 | 단위 | 출처 (XBRL 태그, 왼쪽부터 찾음) | 기준일 | 주의 |
|---|---|---|---|---|---|---|
| current_ratio (유동비율) | 단기 지급능력 | 유동자산 ÷ 유동부채 | 배 | AssetsCurrent · LiabilitiesCurrent | 회계연도 말 | 업종별 차이 |
| debt_to_equity (부채비율) | 재무 레버리지 | 총부채 ÷ 자기자본 | 배 | Liabilities → 없으면 LiabilitiesCurrent + LiabilitiesNoncurrent → 그래도 없으면 부채와자본총계 − 자본(근사) · StockholdersEquity | 회계연도 말 | 자본이 0 이하면 해석 불가 → 빈칸 |
| dso_days (매출채권회전일) | 외상 회수 속도 | 매출채권 ÷ 매출 × 365 | 일 | AccountsReceivableNetCurrent → AccountsAndOtherReceivablesNetCurrent · Revenues → RevenueFromContractWithCustomerExcludingAssessedTax | 기간 일치(1년치 매출) | 분기 매출을 쓰면 4배 왜곡 |
| op_margin (영업이익률) — 코드의 `op_margin_pct` | 본업 수익성 | 영업이익 ÷ 매출 × 100 | % | OperatingIncomeLoss · 매출 태그는 위와 같음 | 회계연도 | 일회성 손익이 섞일 수 있음 |

> **SEC 이용 규칙** — 요청마다 **영문 이름과 이메일(User-Agent)** 을 밝히고, 1초에 10번보다 적게 요청합니다. 아래 코드는 회사마다 한 번만 받아 `sec_cache` 폴더에 저장해 두고 다시 씁니다.

> **SEC 접속이 막힌 네트워크라면** — A-5·A-6을 건너뛰고 A-7 첫 셀을 실행한 뒤, **+ 코드(+ Code)** 로 새 셀을 만들어 `ratios(ref.iloc[0])`를 실행합니다. 비교표 첫 행(iRobot FY2024)의 숫자로 같은 공식을 계산해 볼 수 있습니다.
'''),
    md("sA-1", r'''
### A-1. 내 영문 이름과 이메일 적기 (필수)
1. 아래 셀에서 `Your Name your.email@example.com` 을 지웁니다.
2. 그 자리에 **영문 이름 + 빈칸 + 이메일**을 씁니다. 예: `Gildong Hong gildong.hong@mycompany.com`
3. 한글은 쓰지 않습니다. 요청 머리글에 한글이 들어가면 오류가 납니다.
4. Shift + Enter로 실행하고 "확인 완료"가 나오는지 봅니다.
'''),
    code("cA-1", r'''
# A-1. SEC에 보낼 내 정보(User-Agent)를 적는다 — 영문 이름과 이메일만
USER_AGENT = "Your Name your.email@example.com"

def ua_ok():
    return USER_AGENT.isascii() and "@" in USER_AGENT and "example.com" not in USER_AGENT

print("확인 완료:" if ua_ok() else "아직 예시 그대로입니다. 위 줄을 내 영문 이름·이메일로 바꾸세요:", USER_AGENT)
'''),
    code("cA-2", r'''
# A-2. SEC에서 회사 공시 데이터(JSON)를 받는 함수 — 압축(gzip)을 풀고, 한 번 받은 파일은 저장해 다시 쓴다
import gzip, json, time, zlib, urllib.error

def sec_json(url, cache_name):
    cache = Path("sec_cache") / cache_name
    if cache.is_file():                                           # 이미 받은 파일이면 SEC에 다시 묻지 않는다
        return json.loads(cache.read_bytes())
    if not ua_ok():
        raise ValueError("A-1 셀에서 USER_AGENT를 내 영문 이름과 이메일로 바꾼 뒤 다시 실행하세요.")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body, enc = r.read(), r.headers.get("Content-Encoding", "")
    except urllib.error.HTTPError as e:
        hint = "CIK 번호를 확인하세요" if e.code == 404 else "USER_AGENT를 확인하고 1분 뒤 다시 실행하세요"
        raise RuntimeError(f"SEC 응답 오류({e.code}). {hint}.") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"SEC에 접속하지 못했습니다({e.reason}). 네트워크가 막혔다면 A 섹션 맨 위 안내를 따르세요.") from None
    if enc == "gzip":
        body = gzip.decompress(body)                              # SEC는 gzip으로 압축해 보낸다
    elif enc == "deflate":
        body = zlib.decompress(body)
    time.sleep(0.2)                                               # 1초에 10번 미만 규칙
    cache.parent.mkdir(exist_ok=True)
    cache.write_bytes(body)
    return json.loads(body)

def companyfacts(cik):
    cik10 = f"{int(cik):010d}"                                    # CIK는 앞을 0으로 채운 10자리
    return sec_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json", f"CIK{cik10}.json")
'''),
    code("cA-3", r'''
# A-3. 회계연도의 연간보고서(10-K) 한 건을 고르고, 그 공시에 실린 값만 태그 순서대로 꺼내는 함수
from datetime import date

def usd_facts(facts, tag):
    return facts["facts"].get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", [])

def find_10k(facts, fy):
    """fy 회계연도 10-K의 (공시번호, 회계연도 말일, 접수일)을 돌려준다."""
    rows = [u for u in usd_facts(facts, "Assets") if u.get("form") == "10-K" and u.get("fy") == fy]
    if not rows:
        raise ValueError(f"FY{fy} 10-K를 찾지 못했습니다. 연도를 바꿔 보세요(외국 기업의 20-F는 이 코드로 안 됩니다).")
    end = max(u["end"] for u in rows)                             # 그 공시의 가장 최근 날짜 = 당기 말(전년 비교 열 제외)
    filed, accn = min((u["filed"], u["accn"]) for u in rows if u["end"] == end)
    return accn, end, filed

def pick(facts, tags, accn, end, yearly=False):
    """tags를 왼쪽부터 찾아, 같은 공시(accn)·같은 기준일(end) 값이 있으면 (값, 태그)를 돌려준다."""
    for tag in tags:
        for u in usd_facts(facts, tag):
            if u.get("accn") != accn or u.get("end") != end:
                continue
            days = (date.fromisoformat(end) - date.fromisoformat(u.get("start", end))).days
            if yearly and not 350 <= days <= 380:                 # 손익 항목은 1년치만 — 분기 값이 섞이지 않게
                continue
            return u["val"], tag
    return None, "없음"
'''),
    code("cA-4", r'''
# A-4. 숫자 7개를 꺼내 표로 만드는 함수 (총부채 태그가 없을 때의 대체 규칙 포함)
TAGS = {
    "current_assets":          (["AssetsCurrent"], False),
    "current_liabilities":     (["LiabilitiesCurrent"], False),
    "total_liabilities":       (["Liabilities"], False),
    "stockholders_equity":     (["StockholdersEquity"], False),
    "accounts_receivable_net": (["AccountsReceivableNetCurrent", "AccountsAndOtherReceivablesNetCurrent"], False),
    "revenue":                 (["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"], True),
    "operating_income":        (["OperatingIncomeLoss"], True),
}

def get_inputs(cik, fy):
    facts = companyfacts(cik)
    accn, end, filed = find_10k(facts, fy)
    got = {k: pick(facts, tags, accn, end, yearly) for k, (tags, yearly) in TAGS.items()}
    cl, eq = got["current_liabilities"][0], got["stockholders_equity"][0]
    ncl = pick(facts, ["LiabilitiesNoncurrent"], accn, end)[0]
    tle = pick(facts, ["LiabilitiesAndStockholdersEquity"], accn, end)[0]
    if got["total_liabilities"][0] is None and None not in (cl, ncl):     # 대체 1: 유동 + 비유동 부채
        got["total_liabilities"] = (cl + ncl, "LiabilitiesCurrent + LiabilitiesNoncurrent")
    if got["total_liabilities"][0] is None and None not in (tle, eq):     # 대체 2: 부채와자본총계 − 자본(근사)
        got["total_liabilities"] = (tle - eq, "LiabilitiesAndStockholdersEquity − StockholdersEquity (근사)")
    table = pd.DataFrame(got, index=["value_usd", "xbrl_tag"]).T
    table["value_usd"] = pd.to_numeric(table["value_usd"]).astype(float)   # 없는 값은 NaN(빈칸)
    table.insert(1, "천 달러", table["value_usd"] / 1000)             # 발췌 파일의 재무표는 천 달러 단위
    print(f"{facts['entityName']} · FY{fy} 10-K · 기준일 {end} · 접수일 {filed} · 공시번호 {accn}")
    return table, end
'''),
    code("cA-4b", r'''
# A-4. 비율 4개를 변수 정의서 공식대로 계산하는 함수 (인터넷 없이도 정의된다)
def ratios(v):
    """변수 정의서 공식대로 비율 4개 (자본이 0 이하면 부채비율은 빈칸 = 해석 불가)"""
    eq = v["stockholders_equity"]
    return pd.Series({
        "current_ratio":  v["current_assets"] / v["current_liabilities"],
        "debt_to_equity": v["total_liabilities"] / eq if eq > 0 else np.nan,
        "dso_days":       v["accounts_receivable_net"] / v["revenue"] * 365,
        "op_margin_pct":  v["operating_income"] / v["revenue"] * 100,
    })
'''),
    code("cA-5", r'''
# A-5. iRobot의 FY2024 10-K에서 숫자 7개를 꺼낸다 (iRobot은 상장폐지돼 티커 검색에 안 나오므로 CIK를 직접 쓴다)
COMPANY_CIK, FISCAL_YEAR = 1159167, 2024
inputs, period_end = get_inputs(COMPANY_CIK, FISCAL_YEAR)
inputs
'''),
    code("cA-6", r'''
# A-6. 변수 정의서 공식대로 비율 4개를 계산한다 (자본이 0 이하면 부채비율은 빈칸 = 해석 불가)
mine = ratios(inputs["value_usd"])
mine
'''),
    md("sA-7", r'''
### A-7. 비교표와 맞춰 보기
강사가 SEC에서 미리 뽑아 둔 비교표 `data/day1/real_buyers_ratios.csv`에서 같은 회사·같은 기준일 행을 찾아 내 계산과 나란히 놓습니다.
- **판정** 열: 차이율 1% 이하는 "일치", 넘으면 "다름 → 원인 찾기". 빈칸끼리면 "둘 다 빈칸".
- 비교표의 **메모**(`data_note`)에 그 회사의 태그 함정이 적혀 있습니다. 결과 표 위에 함께 출력됩니다.
'''),
    code("cA-7", r'''
# A-7. 비교표(real_buyers_ratios.csv)를 읽고, 같은 회사·같은 기준일 행을 찾아 내 계산과 나란히 놓는 함수를 만든다
ref = pd.read_csv(get_file("data/day1/real_buyers_ratios.csv"), encoding="utf-8-sig", dtype={"cik": str})

def compare_csv(cik, end, inputs, mine):
    row = ref[(ref.cik.astype(int) == int(cik)) & (ref.fiscal_period_end == end) & (ref.form == "10-K")]
    if row.empty:
        print("비교표에 이 회사·기준일 행이 없습니다(직접 고른 회사라면 정상입니다).")
        return None
    r = row.iloc[0]
    mine_all = pd.concat([inputs["value_usd"], mine])
    out = pd.DataFrame({"내 계산(SEC API)": mine_all, "비교표(CSV)": pd.to_numeric(r[mine_all.index], errors="coerce")})
    a, b = out.iloc[:, 0], out.iloc[:, 1]
    out["차이율(%)"] = (a - b).abs() / b.abs() * 100
    out["판정"] = np.select([a.isna() & b.isna(), a.isna() | b.isna(), out["차이율(%)"] > 1],
                          ["둘 다 빈칸", "한쪽만 빈칸", "다름 → 원인 찾기"], "일치")
    if isinstance(r["data_note"], str):
        print("비교표 메모:", r["data_note"])
    return out
'''),
    code("cA-7b", r'''
# A-7. iRobot FY2024: 내 계산과 비교표를 나란히 놓는다
compare_csv(COMPANY_CIK, period_end, inputs, mine)
'''),
    md("sA-8", r'''
### A-8. AI 답과 대조하기
1. Step 3 ④에서 AI(P1-2)가 iRobot FY2024로 낸 비율 4개를 찾습니다.
2. 아래 셀의 `None`을 그 숫자로 바꿉니다. 예: `"current_ratio": 1.23`
3. 실행해서 **차이** 열을 봅니다.
4. 차이가 크면 먼저 세 가지를 확인합니다. ① 단위(발췌 표는 천 달러, SEC 값은 달러) ② 기간(전년 열을 당기로 읽지 않았나) ③ 계정(매출 대신 매출총이익, 총부채 대신 유동부채를 쓰지 않았나)
'''),
    code("cA-8", r'''
# A-8. AI가 낸 비율을 적어 넣고 SEC 계산과의 차이를 본다 — None 자리에 숫자만 바꿔 넣는다
ai = {"current_ratio": None, "debt_to_equity": None, "dso_days": None, "op_margin_pct": None}

vs = pd.DataFrame({"AI 답": pd.Series(ai, dtype="float64"), "SEC 계산": mine})
vs["차이"] = vs["AI 답"] - vs["SEC 계산"]
vs
'''),
    md("sA-9", r'''
### A-9. 다른 회사로 바꿔 보기
1. 아래 셀을 그대로 실행합니다. 기본값은 **Wolfspeed FY2025**(2025-06-29 결산)입니다. `xbrl_tag` 열에서 총부채 대체 규칙이 쓰였는지, 자본이 음수일 때 부채비율이 빈칸으로 나오는지 봅니다.
2. 셀의 숫자 두 개를 `OTHER_CIK, OTHER_FY = 1093691, 2023` 으로 바꿔 다시 실행합니다. **Plug Power**는 10-Q 2023년 3분기에 계속기업 의문이 처음 나왔다가, FY2023 10-K에서 "의문 해소"로 바뀐 회사입니다(경고 ≠ 부도 — 오탐 사례).
3. Plug Power FY2023의 비율을 A-6의 iRobot과 비교하고, 비율만 보고 그 경고를 알아챌 수 있었을지 생각해 봅니다.
4. 다른 회사도 해 봅니다. 과정 자료 회사의 CIK: iRobot 1159167 · Wolfspeed 895419 · Plug Power 1093691 · Big Lots 768835(`real_buyers_ratios.csv`의 `cik` 열). 지금 상장된 회사는 A-10 셀의 `find_cik("티커")`로 CIK를 찾습니다.
'''),
    code("cA-9", r'''
# A-9. 다른 회사·연도로 같은 계산을 반복하고 비교표와 맞춰 본다 (기본: Wolfspeed FY2025)
OTHER_CIK, OTHER_FY = 895419, 2025
other, other_end = get_inputs(OTHER_CIK, OTHER_FY)
display(other)
compare_csv(OTHER_CIK, other_end, other, ratios(other["value_usd"]))
'''),
    code("cA-10", r'''
# A-10. (선택) 티커로 CIK 찾기 — 상장폐지된 회사(iRobot·Big Lots)는 목록에 없어 None이 나온다
def find_cik(ticker):
    data = sec_json("https://www.sec.gov/files/company_tickers.json", "company_tickers.json")
    hit = [v for v in data.values() if v["ticker"] == ticker.upper()]
    return (hit[0]["cik_str"], hit[0]["title"]) if hit else None

find_cik("PLUG")
'''),
    md("sA-end", r'''
### A 정리 — 숫자를 쓰기 전에
- 내 계산과 비교표가 같으면 "1차 출처에서 같은 숫자를 확인"한 것입니다. 검증 4단계 라벨로 **검증가능**입니다.
- 태그 이름은 회사·공시마다 다릅니다. 첫 번째 태그에서 값이 안 나오면 다음 태그를 찾고, 결과 표의 `xbrl_tag` 열로 **값이 어디서 왔는지** 남깁니다.
- 자본 줄이 둘인 회사(모회사 귀속 자본 / 비지배지분까지 넣은 총자본)는 어느 줄을 쓰느냐에 따라 부채비율이 달라집니다. Step 3의 P1-2는 총자본을 쓰고, 이 노트북의 기본 태그 `StockholdersEquity`는 모회사 귀속 자본입니다. 차이가 나면 비교표 메모를 확인합니다(예: Plug Power FY2024).
- 분기 보고서(10-Q)로 DSO를 구할 때는 365가 아니라 그 분기의 일수(약 91일)를 씁니다. 이 노트북은 1년치(10-K)만 다룹니다.
- 비율은 위험의 일부만 보여 줍니다. 계속기업 의문 같은 문장 신호는 Step 2의 P1-1(원문 인용)로 함께 봅니다.
'''),
    # ------------------------------------------------------------------------------------------ B
    md("sB", r'''
## B. 인보이스 원장 EDA — 연체와 회수 속도를 건 단위로 보기 (Step 4–6 Challenge · 40–60분)

Step 4–6 Basic은 바이어 150곳의 **스냅샷**(바이어당 1행, 기준일 2026-09-30)을 봅니다. 여기서는 그 스냅샷의 재료인 **인보이스 원장** — 2023-10 ~ 2026-09, 36개월치 인보이스 한 건 한 건 — 을 직접 봅니다.

**B 섹션 공통 정의** — 아래 모든 셀이 이 정의를 씁니다.

| 용어 | 정의 |
|---|---|
| 기준일 | 2026-09-30 (데이터 마지막 날) |
| DPD (연체일수) | max(0, 완납일 − 결제기일). 기준일까지 미결이면 완납일 대신 기준일을 넣는다 |
| 연체 인보이스 | DPD > 0 — 결제기일보다 하루라도 늦게 완납했거나, 결제기일이 지났는데 아직 미결 |
| 연체 구간 (CRF 표준) | Current(DPD 0) · 1-30 · 31-60 · 61-90 · 91+ |
| 미결 (어떤 날 t에) | t까지 발행됐고 t에 아직 완납 전인 인보이스. 대손 처리(`status` = written_off)된 건은 장부에서 빠진 것으로 보고 뺀다 |
| 미결 잔액 | 미결 인보이스의 `amount_usd × (1 − advance_pct)` — 선수금으로 미리 받은 부분은 채권이 아니다 |

- 금액은 발행일 환율로 바꾼 USD(`amount_usd`)입니다.
- 단순화 두 가지: 이 원장에는 ① 부분 입금 기록과 ② 대손 처리 날짜가 없습니다. 그래서 미결 건은 금액 전체를 잔액으로 보고, 대손 처리 건은 날짜와 상관없이 뺍니다. 실제 잔액과 조금 다를 수 있습니다.
'''),
    code("cB-1", r'''
# B-1. 인보이스 원장을 불러오고 날짜 열 3개를 날짜 형식으로 읽는다
inv = pd.read_csv(get_file("data/day1/d1_invoices.csv"), encoding="utf-8-sig",
                  parse_dates=["invoice_date", "due_date", "settled_date"])
REF = pd.Timestamp("2026-09-30")                                  # 기준일 = 데이터 마지막 날
print(f"인보이스 {len(inv):,}건 · 거래 바이어 {inv.buyer_id.nunique()}곳 · 발행일 {inv.invoice_date.min():%Y-%m-%d} ~ {inv.invoice_date.max():%Y-%m-%d}")
inv.head(3)
'''),
    code("cB-2", r'''
# B-2. 인보이스마다 DPD(연체일수)·연체 여부·연체 구간을 계산해 새 열로 붙인다
BUCKETS = ["Current", "1-30", "31-60", "61-90", "91+"]

def aging(days):
    """연체일수 → CRF 표준 연체 구간 이름"""
    return pd.cut(days, [-1, 0, 30, 60, 90, np.inf], labels=BUCKETS).astype(str)

inv["dpd"] = (inv.settled_date.fillna(REF) - inv.due_date).dt.days.clip(lower=0)   # 미결이면 기준일까지 센다
inv["is_late"] = inv.dpd > 0
inv["over30"] = inv.dpd > 30
inv["bucket"] = aging(inv.dpd)
inv.loc[inv.is_late, ["invoice_id", "payment_method", "due_date", "settled_date", "status", "dpd", "bucket"]].head()
'''),
    md("sB-3", r'''
### B-3. 연체일(DPD) 분포 — 늦게 낸 건은 얼마나 늦었나
- 대상: 연체 인보이스(DPD > 0)만 봅니다.
- **중앙값**: 늦은 건을 DPD 순서로 줄 세웠을 때 한가운데 값입니다. **P90**: 90%가 이 값 이하 — 꼬리가 얼마나 긴지 봅니다.
- 그래프의 세로선: **30일** = K-SURE 연속수출 면책선이자 IFRS 9 '30일 초과' 추정 기준, **90일** = IFRS 9 채무불이행 추정 기준입니다.
'''),
    code("cB-3a", r'''
# B-3. 연체 인보이스 수·DPD 중앙값·P90과 연체 구간별 비중(%)을 계산한다
late = inv[inv.is_late]
print(f"연체 인보이스 {len(late):,}건 (전체 {len(inv):,}건 중 {len(late) / len(inv):.1%})")
print(f"DPD 중앙값 {late.dpd.median():.0f}일 · P90 {late.dpd.quantile(0.9):.0f}일 · 최대 {late.dpd.max()}일")
late.bucket.value_counts(normalize=True).reindex(BUCKETS[1:]).mul(100).rename_axis("연체 구간").rename("비중(%)")
'''),
    code("cB-3b", r'''
# B-3. DPD 분포를 5일 간격 막대로 그린다 (121일 이상은 맨 오른쪽 막대 하나로 묶는다)
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.hist(late.dpd.clip(upper=121), bins=np.arange(0.5, 126, 5), color=BLUE, edgecolor="white", linewidth=1)
for x in (30, 90):
    ax.axvline(x + 0.5, color=GRAY, linewidth=1)
    ax.text(x + 2, ax.get_ylim()[1] * 0.92, f"{x}일", color=GRAY, fontsize=9)
ax.set(title="연체 인보이스의 DPD 분포 (기준일 2026-09-30)", xlabel="DPD(일) · 맨 오른쪽 막대 = 121일 이상", ylabel="인보이스 수")
plt.show()
'''),
    md("sB-4", r'''
### B-4. 결제방식별 연체 — 위험 사다리 순서로 보기
- 대상: **결제기일이 기준일(2026-09-30)까지 돌아온** 인보이스 — 연체인지 아닌지 이미 알 수 있는 건입니다.
- **late_pct** = 연체율(%, DPD > 0 비율), **over30_pct** = 30일 초과 비율(%, DPD > 30), **late_dpd_median · late_dpd_p90** = 늦은 건만 놓고 본 DPD.
- 표의 순서는 수출자 위험이 낮은 것부터입니다: 선수금(TT_ADV) → 분할 송금(TT_SPLIT_30_70) → L/C 일람불 → L/C 기한부 → D/P → D/A → O/A.
- 상자그림: 상자 = 가운데 50%, 상자 안 선 = 중앙값. 아주 긴 꼬리(대손·부도 건)는 그림이 눌리지 않게 숨겼습니다. 표의 P90을 같이 보세요.
'''),
    code("cB-4a", r'''
# B-4. 결제방식별 연체율·30일 초과 비율·연체 건 DPD를 한 표로 만든다 (위험이 낮은 결제방식부터)
LADDER = ["TT_ADV", "TT_SPLIT_30_70", "LC_SIGHT", "LC_USANCE", "DP", "DA", "OA"]
due = inv[inv.due_date <= REF]                                        # 결제기일이 이미 온 건
pm = due.groupby("payment_method").agg(invoices=("invoice_id", "size"), late=("is_late", "sum"),
                                       late_pct=("is_late", "mean"), over30_pct=("over30", "mean"))
pm[["late_pct", "over30_pct"]] *= 100
pm["late_dpd_median"] = late.groupby("payment_method").dpd.median()
pm["late_dpd_p90"] = late.groupby("payment_method").dpd.quantile(0.9)
pm.reindex(LADDER)
'''),
    code("cB-4b", r'''
# B-4. 연체 건의 DPD를 결제방식별 상자그림으로 비교한다 (연체가 한 건도 없는 결제방식은 빠진다)
order = [m for m in LADDER if m in set(late.payment_method)]
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.boxplot([late.loc[late.payment_method == m, "dpd"] for m in order], showfliers=False, widths=0.5,
           medianprops={"color": BLUE, "linewidth": 2})
ax.set_xticks(range(1, len(order) + 1), order)
ax.set(title="연체 건의 DPD — 결제방식별 (긴 꼬리는 숨김)", ylabel="DPD(일)")
plt.show()
'''),
    md("sB-5", r'''
### B-5. 월별 코호트 연체율 — 언제 판 외상이 더 자주 늦었나
- **코호트** = 인보이스 발행월. 대상은 외상 거래(선수금 TT_ADV 제외)입니다.
- **연체율(late_pct)** = 그 달 발행분 중 **결제기일이 기준일까지 돌아온** 건에서 DPD > 0인 비율.
- **30일 초과 연체율(over30_pct)** = 그 달 발행분 중 **결제기일 + 30일이 기준일까지 돌아온** 건에서 DPD > 30인 비율.
- 결제기일이 아직 오지 않은 건은 늦을지 알 수 없어서 분모에서 뺍니다. 그래서 최근 몇 달은 표본이 작습니다(오른쪽이 잘린 데이터). 그래프에는 표본이 30건 이상인 달만 그립니다.
'''),
    code("cB-5a", r'''
# B-5. 발행월(코호트)별 연체율과 30일 초과 연체율을 계산한다 — 외상 거래만, 결과를 이미 아는 건만
credit = inv[inv.payment_method != "TT_ADV"].assign(cohort=lambda d: d.invoice_date.dt.to_period("M"))
seen = credit[credit.due_date <= REF]                                   # 결제기일이 지나 연체 여부를 아는 건
seen30 = credit[credit.due_date <= REF - pd.Timedelta(days=30)]         # 결제기일 + 30일이 지난 건
coh = pd.DataFrame({
    "n_seen": seen.groupby("cohort").size(),
    "late_pct": seen.groupby("cohort").is_late.mean() * 100,
    "n_seen30": seen30.groupby("cohort").size(),
    "over30_pct": seen30.groupby("cohort").over30.mean() * 100,
})
coh["n_seen30"] = coh["n_seen30"].fillna(0).astype(int)              # 아직 한 건도 없는 달은 0건
coh.tail(6)
'''),
    code("cB-5b", r'''
# B-5. 표본이 30건 이상인 달만 두 연체율을 선 그래프로 그린다
show = coh.copy()
show.loc[~(show.n_seen >= 30), "late_pct"] = np.nan
show.loc[~(show.n_seen30 >= 30), "over30_pct"] = np.nan
x = show.index.to_timestamp()
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.plot(x, show.late_pct, color=BLUE, linewidth=2, marker="o", markersize=5, label="연체율 (DPD > 0)")
ax.plot(x, show.over30_pct, color=ORANGE, linewidth=2, marker="o", markersize=5, label="30일 초과 연체율 (DPD > 30)")
ax.set_title("발행월 코호트별 연체율 — 외상 거래(선수금 제외)")
ax.set_ylabel("%", rotation=0, labelpad=10)
ax.set_ylim(0, show.late_pct.max() * 1.35)                           # 위쪽에 범례 자리를 비운다
ax.legend(frameon=False, ncol=2, loc="upper left")
plt.show()
'''),
    md("sB-6", r'''
### B-6. 연체 구간 전이표(roll rate) — 한 달 뒤 어디로 굴러갔나
- 두 월말 **T0 = 2026-08-31**과 **T1 = 2026-09-30**을 비교합니다.
- **행** = T0에 미결이던 인보이스의 연체 구간. **열** = T1의 상태 — 그사이 완납했으면 "회수", 아니면 T1의 연체 구간.
- 한 달이 지나면 연체일이 약 30일 늘어나므로, 회수되지 않은 건은 오른쪽 구간으로 한 칸 **굴러갑니다(roll)**. 실무에서는 이 비율로 다음 달 연체를 예상하고, 충당금 설정률표(Day4)의 재료로 씁니다.
- 행 비율(%) 표는 행 합계 대비입니다. 건수가 몇 건뿐인 행은 비율이 크게 흔들리니 `T0_건수` 열을 같이 봅니다.
- T0·T1 날짜를 바꿔 다른 달도 볼 수 있습니다(월말 날짜로 넣기).
'''),
    code("cB-6a", r'''
# B-6. 두 월말 사이 연체 구간 전이표(건수)를 만든다 — 행 = T0의 구간, 열 = T1의 상태
def is_open(df, t):
    """t에 이미 발행됐고 아직 완납 전인 건 (대손 처리 written_off 건은 장부에서 빠진 것으로 보고 제외)"""
    return (df.invoice_date <= t) & (df.settled_date.isna() | (df.settled_date > t)) & (df.status != "written_off")

T0, T1 = pd.Timestamp("2026-08-31"), pd.Timestamp("2026-09-30")
base = inv[is_open(inv, T0)].copy()
base["from"] = aging((T0 - base.due_date).dt.days.clip(lower=0))
base["to"] = aging((T1 - base.due_date).dt.days.clip(lower=0)).where(is_open(base, T1), "회수")
roll = pd.crosstab(base["from"], base["to"]).reindex(index=BUCKETS, columns=["회수"] + BUCKETS, fill_value=0)
roll
'''),
    code("cB-6b", r'''
# B-6. 행 비율(%)로 바꿔 '회수된 비율'과 '다음 구간으로 굴러간 비율(roll rate)'을 읽는다
roll_pct = roll.div(roll.sum(axis=1), axis=0) * 100
roll_pct.assign(T0_건수=roll.sum(axis=1))
'''),
    md("sB-7", r'''
### B-7. 단순 DSO vs 역산(countback) DSO — 2026년 9월
- **DSO** = "지금 남아 있는 매출채권이 며칠치 매출인가"입니다. 슬라이드 D1-34처럼 매출채권 ÷ 매출 × 일수로 셉니다.
- **매출채권** = 월말 미결 잔액(B 공통 정의). **매출** = 그 달 발행 인보이스 금액 합계(USD, 모든 결제방식). 외상 매출만 쓰는 정의도 있으니, 어느 쪽을 썼는지 변수 정의서에 적어 둡니다.
- **단순 DSO(최근 3개월 평균법)** = 월말 매출채권 ÷ (최근 3개월 매출 합계 ÷ 3개월 일수).
- **역산 DSO(countback)** = 월말 매출채권에서 가장 최근 달 매출부터 차례로 뺍니다. 다 빠지는 달은 그 달 일수를 통째로 더하고, 남은 잔액이 그 달 매출보다 작아지면 (남은 잔액 ÷ 그 달 매출 × 그 달 일수)를 더하고 멈춥니다.
- 왜 두 개인가: 매출이 들쭉날쭉하면 3개월 평균은 늦게 반응합니다. 역산법은 최근 달 매출부터 쓰므로 최근 상황이 바로 반영됩니다.
- 먼저 손계산 예시로 함수가 맞는지 검산하고 원장에 씁니다. 예시: 기말 매출채권 1,400 · 9월 매출 700(30일) · 8월 600(31일) · 7월 500(31일) → 단순 71.6일, 역산 67.2일.
'''),
    code("cB-7a", r'''
# B-7. DSO 함수 두 개를 만들고, 손계산 예시(단순 71.6일 · 역산 67.2일)로 먼저 검산한다
def simple_dso(ar, sales, days):
    """sales·days: 최근 달부터 3개월치"""
    return ar / (sum(sales) / sum(days))

def countback_dso(ar, sales, days):
    """sales·days: 최근 달부터 과거로 가는 목록"""
    total = 0.0
    for s, d in zip(sales, days):
        if ar <= s:
            return total + ar / s * d                             # 남은 잔액이 이 달 매출 안에 들어오면 비례로 더하고 끝
        ar, total = ar - s, total + d                             # 이 달 매출을 다 빼고 일수를 통째로 더한다
    return float("nan")                                           # 매출을 다 빼도 잔액이 남으면 계산 불가

print("단순:", round(simple_dso(1400, [700, 600, 500], [30, 31, 31]), 1), "← 손계산 71.6")
print("역산:", round(countback_dso(1400, [700, 600, 500], [30, 31, 31]), 1), "← 손계산 67.2")
'''),
    code("cB-7b", r'''
# B-7. 월말 매출채권과 월별 매출을 만들고, 2026년 9월의 두 DSO를 계산한다
def ar_at(t):
    """t의 미결 잔액(USD) — 선수금으로 이미 받은 부분(advance_pct)은 채권이 아니다"""
    o = inv[is_open(inv, t)]
    return (o.amount_usd * (1 - o.advance_pct)).sum()

sales_m = inv.groupby(inv.invoice_date.dt.to_period("M")).amount_usd.sum()      # 월별 매출(USD)

def month_lists(p, n=36):
    """p 달부터 과거로 n개월의 매출·일수 목록"""
    back = pd.period_range(end=p, periods=n, freq="M")[::-1]
    return [sales_m.get(q, 0.0) for q in back], [q.days_in_month for q in back]

sales, days = month_lists(pd.Period("2026-09", freq="M"))
ar_sep = ar_at(REF)
dso_simple_sep, dso_countback_sep = simple_dso(ar_sep, sales[:3], days[:3]), countback_dso(ar_sep, sales, days)
print(f"2026-09-30 매출채권 USD {ar_sep:,.0f} · 최근 3개월 매출 USD {sum(sales[:3]):,.0f} ({sum(days[:3])}일)")
print(f"단순 DSO {dso_simple_sep:.1f}일 · 역산 DSO {dso_countback_sep:.1f}일")
'''),
    code("cB-7c", r'''
# B-7. (더 보기) 최근 12개 월말의 두 DSO를 월 매출과 함께 표로 만든다
rows = []
for p in pd.period_range(end="2026-09", periods=12, freq="M"):
    s, d = month_lists(p)
    a = ar_at(p.end_time.normalize())
    rows.append({"month": str(p), "sales_usd": s[0], "ar_usd": a,
                 "simple_dso": simple_dso(a, s[:3], d[:3]), "countback_dso": countback_dso(a, s, d)})
dso = pd.DataFrame(rows).set_index("month")
dso
'''),
    code("cB-7d", r'''
# B-7. 두 DSO를 선 그래프로 겹쳐 본다 (어느 달에 벌어지는지, 그달 매출은 어땠는지)
ax = dso[["simple_dso", "countback_dso"]].plot(figsize=(10, 3.8), color=[BLUE, ORANGE], linewidth=2, marker="o", markersize=5)
ax.set(title="월말 DSO — 단순(최근 3개월 평균) vs 역산(countback)", xlabel="")
ax.set_ylabel("일", rotation=0, labelpad=10)
ax.legend(["단순 DSO", "역산 DSO"], frameon=False, ncol=2, loc="upper left")
plt.show()
'''),
    md("sB-8", r'''
### B-8. (선택 · 16:00 정답 공개 뒤) 원장으로 Step 5–6 숫자 검산하기 — 바이어 단위로 올려 보기
- 바이어 스냅샷(`d1_buyers_raw`)의 `max_dpd_days`는 "기준일에 미결인 인보이스 중 가장 오래 연체된 일수"입니다. 원장으로 같은 숫자를 다시 만들 수 있습니다.
- 바이어 목록은 스냅샷 파일에서 가져옵니다. 원장에 거래가 한 건도 없는 바이어도 목록에 남기고 연체 0일로 셉니다.
- 아래 결과를 Step 5 피벗①(결제방식 × 연체구간)의 합계 줄, AI가 P1-4로 낸 숫자와 나란히 놓아 봅니다(Step 6).
- 셋이 다르면 어느 쪽이 틀렸다고 단정하지 말고, 각 숫자가 무엇을 셌는지(행 수·연체의 정의·빈칸 처리)부터 비교합니다. 찾은 원인은 03_EDA 시트에 적습니다.
'''),
    code("cB-8", r'''
# B-8. 기준일에 미결인 건으로 바이어별 최악 연체일을 구하고, 연체 구간별 바이어 수를 센다
buyers = pd.read_csv(get_file("data/day1/d1_buyers_raw.csv"), encoding="utf-8-sig").buyer_id.unique()   # 같은 ID는 한 번만
open_now = inv[is_open(inv, REF)]
worst = (REF - open_now.due_date).dt.days.clip(lower=0).groupby(open_now.buyer_id).max()
worst = worst.reindex(sorted(buyers), fill_value=0)                     # 미결이 없는 바이어 = 0일
print(f"스냅샷 바이어 {len(buyers)}곳(원장에 거래가 있는 바이어 {inv.buyer_id.nunique()}곳)")
print(f"연체 바이어 {(worst > 0).sum()}곳 ({(worst > 0).mean():.1%})")
aging(worst).value_counts().reindex(BUCKETS, fill_value=0).rename_axis("연체 구간").rename("바이어 수")
'''),
    # ------------------------------------------------------------------------------------------ C
    md("sC", r'''
## C. AI와 함께 확장하기 (남는 시간)

**Gemini in Colab으로 묻기**
1. Colab 화면 오른쪽 위의 **Gemini** 버튼(반짝이 모양)을 누릅니다. 오른쪽에 채팅 창이 열립니다(버튼이 안 보이면 Claude로 합니다).
2. 아래 프롬프트 하나를 복사해 채팅 창에 붙여 넣고 보냅니다.
3. 받은 코드는 맨 아래에 **+ 코드(+ Code)** 로 새 셀을 만들어 붙이고 실행합니다.
4. 한국어 답이 어색하면 같은 내용을 영어로 다시 묻습니다.

**Claude로 묻기**
1. claude.ai에서 **새 채팅**을 엽니다.
2. 입력창의 클립(또는 +) 아이콘을 눌러 `d1_invoices.csv`를 올립니다. C3은 `real_buyers_ratios.csv`를 올립니다.
3. 프롬프트를 붙여 넣고 보냅니다.
4. 받은 코드는 이 노트북 맨 아래에 **+ 코드(+ Code)** 로 새 셀을 만들어 붙이고 실행해, 같은 숫자가 나오는지 봅니다.

**먼저 지킬 것**
- 이 노트북의 합성 데이터와 공개 공시만 씁니다. Colab AI 기능은 프롬프트·코드·출력을 사람 검토자가 볼 수 있고 최대 18개월 보관합니다. 회사 실데이터는 넣지 않습니다.
- AI가 준 코드와 숫자는 **검증 전까지 가설**입니다. 맨 아래 '검증 체크 4가지'를 통과한 결과만 산출물에 씁니다.

**C1 — 금액 기준 전이율, 6개월 평균**
```text
[역할] 너는 수출기업의 매출채권을 분석하는 파이썬 분석가다.
[과제] d1_invoices.csv(인보이스 원장)로 2026-03-31→04-30부터 2026-08-31→09-30까지 연속된 월말 6쌍의 연체 구간 전이표를 '금액 기준'으로 만들고, 6개월 평균 전이율을 구하라.
[맥락] 연체 구간은 Current(DPD 0)·1-30·31-60·61-90·91+다. 월말 t의 미결 = invoice_date ≤ t이고, settled_date가 비었거나 t보다 늦으며, status가 written_off가 아닌 건이다. 미결 금액 = amount_usd × (1 − advance_pct). t의 DPD = max(0, t − due_date). 다음 월말까지(그날 포함) 완납했으면 '회수'로 본다.
[형식] ① 월말 쌍별 전이표를 세로로 이어 붙인 표 ② 6개월 평균 전이율 표(행 비율 %) ③ 사용한 코드와 계산식 전체(정의는 주석으로)
[제약] 위 정의만 쓴다. 행 금액이 0인 칸은 평균에서 뺀다. 계산하지 않은 숫자는 쓰지 마라.
```

**C2 — 연체 잔액 상위 10곳과 국가 × 결제방식 히트맵**
```text
[역할] 너는 수출 신용관리 담당자를 돕는 데이터 분석가다.
[과제] d1_invoices.csv로 기준일 2026-09-30에 연체 잔액이 큰 바이어 상위 10곳을 표로 만들고, 전체 연체 잔액 중 상위 10곳의 비중을 계산하라. 이어서 country_code × payment_method별 연체율 히트맵을 그려라.
[맥락] DPD = max(0, (settled_date가 비었으면 2026-09-30) − due_date), 연체 = DPD > 0. 미결 금액 = amount_usd × (1 − advance_pct)이고 status가 written_off인 건은 뺀다. 연체 잔액 = 기준일에 결제기일이 지난 미결 금액. 히트맵 연체율의 분모는 결제기일이 2026-09-30까지(그날 포함) 돌아온 인보이스다.
[형식] ① 상위 10곳 표(buyer_id, country_code, 주 결제방식, 미결 잔액 USD, 연체 잔액 USD, 최악 DPD) ② 히트맵 1개 ③ 표에 있는 숫자만 인용한 해석 3줄 ④ 사용한 코드와 계산식
[제약] 인보이스가 30건 미만인 칸은 회색으로 두고 "표본 작음"이라고 적는다. 상관을 원인으로 단정하지 않는다.
```

**C3 — Plug Power: 경고가 나온 공시와 해소된 공시 비교**
```text
[역할] 너는 해외 바이어의 재무를 검토하는 신용분석가다.
[과제] real_buyers_ratios.csv에서 Plug Power의 3개 행(10-Q 2023년 3분기, 10-K FY2023, 10-K FY2024)을 골라 current_ratio, debt_to_equity, dso_days, op_margin_pct, going_concern_flag를 한 표로 비교하라.
[맥락] Plug Power는 10-Q 2023년 3분기에 계속기업 의문이 처음 제기됐다가, FY2023 10-K에서 그 의문이 해소됐다고 적은 회사다(경고 ≠ 부도, 오탐 사례). 분기 행과 연간 행은 dso_basis_days(DSO 계산 일수)가 다르다.
[형식] ① 비교표 ② 분기 행과 연간 행을 그대로 비교하면 안 되는 지표와 그 이유 ③ "비율만 보고 이 경고를 미리 알 수 있었나"에 대한 3줄 의견 ④ 사용한 코드
[제약] 파일에 없는 숫자·사건은 쓰지 마라. 모르면 "파일에 없음"이라고 적어라.
```

**검증 체크 4가지 — AI 결과를 쓰기 전에**
1. **정의** — AI 코드의 조건(DPD, 미결, written_off 제외, 분모)이 B 섹션 정의와 같은가?
2. **재현** — 숫자 하나를 골라 이 노트북 셀이나 엑셀 피벗으로 같은 값을 다시 만들 수 있는가? 예: C1 코드로 2026-08-31→09-30 '건수' 표를 뽑으면 B-6 표와 같아야 한다.
3. **합계** — 행 합계와 건수가 원래 데이터 건수와 맞는가?
4. **설명** — 코드를 한 줄씩 내 말로 설명할 수 있는가? 설명할 수 없으면 제출하지 않는다.
'''),
    # ------------------------------------------------------------------------------------------ D
    md("sD", r'''
## D. 셀프 체크 (5분)

이 셀을 더블클릭해 각 질문의 **내 답:** 뒤에 한두 줄로 적습니다. 근거가 된 셀 번호도 함께 적습니다.

1. **태그 함정** — A-5에서 iRobot FY2024의 매출채권은 어떤 XBRL 태그에서 나왔나요? 첫 번째 후보 태그로는 왜 값을 찾지 못했을까요? 이 경험이 "AI가 준 숫자를 검증하는 법"에 주는 교훈은 무엇인가요?
   - 내 답:
2. **정의가 숫자를 바꾼다** — B-7 표에서 단순 DSO와 역산 DSO의 차이가 가장 큰 달은 언제인가요? 그 달 전후의 월 매출(`sales_usd`)을 보고, 어느 쪽이 최근 상황을 더 빨리 반영하는지 한 문장으로 설명해 보세요.
   - 내 답:
3. **아직 모르는 것** — B-5에서 최근 몇 달을 그래프에서 뺀 이유는 무엇인가요? 이 처리를 하지 않고 "최근 연체율이 크게 좋아졌다"고 보고하면 무엇이 잘못일까요?
   - 내 답:

## 마치며 — 저장과 제출
1. **파일(File) → 저장(Save)** 을 누릅니다(Ctrl + S).
2. 오른쪽 위 **공유(Share)** 를 누릅니다.
3. 일반 액세스를 **링크가 있는 모든 사용자(Anyone with the link)**, 역할을 **뷰어(Viewer)** 로 바꿉니다.
4. **링크 복사(Copy link)** 를 누르고, 제출 폼(과정 사이트 → 1일차 → 1.9 산출물과 제출)의 Challenge 칸에 붙여 넣습니다.
5. AI가 만든 셀이 있다면 그 셀 첫 줄에 `# AI 생성 — 검증: (무엇과 대조했는지)` 를 남깁니다.
'''),
]

# 실행 검사 때만 맨 끝에 붙이는 강사용 검산 셀(수강생 노트북에는 없다)
CHECK_CELL = r'''
# [강사용 실행본 전용 — 수강생 노트북에는 없는 셀] 실행 검사 값(JSON)을 뽑는다 → tools/build_day1_notebook.py가 기준 파일과 대조
import json as _json
def _num(v):
    return None if pd.isna(v) else round(float(v), 4)
_chk = {
    "late_invoices": int(len(late)), "late_dpd_median": float(late.dpd.median()), "late_dpd_p90": float(late.dpd.quantile(0.9)),
    "late_bucket_pct": {k: _num(v) for k, v in late.bucket.value_counts(normalize=True).reindex(BUCKETS[1:]).mul(100).items()},
    "buyers": int(len(worst)), "overdue_buyers": int((worst > 0).sum()),
    "buyer_aging": {k: int(v) for k, v in aging(worst).value_counts().reindex(BUCKETS, fill_value=0).items()},
    "irbt_fy2024_end": period_end, "irbt_fy2024_inputs": {k: _num(v) for k, v in inputs["value_usd"].items()},
    "irbt_fy2024_ratios": {k: _num(v) for k, v in mine.items()}, "irbt_fy2024_tags": inputs["xbrl_tag"].to_dict(),
    "other_cik": OTHER_CIK, "other_end": other_end, "other_ratios": {k: _num(v) for k, v in ratios(other["value_usd"]).items()},
    "other_tags": other["xbrl_tag"].to_dict(),
    "roll_counts": {k: {c: int(n) for c, n in r.items()} for k, r in roll.to_dict(orient="index").items()},
    "dso_2026_09": {"ar_usd": _num(ar_sep), "simple": _num(dso_simple_sep), "countback": _num(dso_countback_sep)},
    "dso_selftest": [_num(simple_dso(1400, [700, 600, 500], [30, 31, 31])), _num(countback_dso(1400, [700, 600, 500], [30, 31, 31]))],
}
print("CHECK_JSON=" + _json.dumps(_chk, ensure_ascii=False))
'''


# ----------------------------------------------------------------------------------------------------
def build_notebook(org: str | None = None):
    nb = new_notebook()
    for kind, cid, text in CELLS:
        src = textwrap.dedent(text).strip("\n")
        if org:  # 배지 링크와 RAW_BASE 값만 바꾼다(0-3 셀의 '<org>' 자리표시자 검사 문장·주석은 그대로)
            src = src.replace("github/<org>/tradefin-ai-2026", f"github/{org}/tradefin-ai-2026")
            src = src.replace("githubusercontent.com/<org>/tradefin-ai-2026", f"githubusercontent.com/{org}/tradefin-ai-2026")
        cell = new_markdown_cell(src, id=cid) if kind == "markdown" else new_code_cell(src, id=cid)
        nb.cells.append(cell)
    nb.metadata = {
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "toc_visible": True},
    }
    nbformat.validate(nb)
    return nb


def lint_notebook(nb) -> list[str]:
    """수강생 노트북 규칙 점검: 코드 셀 첫 줄은 한국어 주석, 출력·실행 번호 없음, 강사 정답 파일명 언급 없음."""
    problems = []
    for c in nb.cells:
        if c.cell_type == "code":
            first = c.source.splitlines()[0]
            if not (first.startswith("# ") and re.search(r"[가-힣]", first)):
                problems.append(f"{c.id}: 첫 줄이 한국어 주석이 아님 → {first[:50]}")
            if c.get("outputs") or c.get("execution_count"):
                problems.append(f"{c.id}: 출력이 남아 있음")
        for bad in ("d1_buyers_clean", "lab2_expected", "lab1_expected", "d1_dirt_log", "instructor/", "answers/"):
            if bad in c.source:
                problems.append(f"{c.id}: 강사 자료 언급({bad})")
    if sum(UA_PLACEHOLDER in c.source for c in nb.cells if c.cell_type == "code") != 1:
        problems.append("USER_AGENT 자리표시자 줄이 정확히 한 번 있어야 함")
    return problems


def write_if_changed(nb, path: Path) -> bool:
    text = nbformat.writes(nb) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------------------------- 실행 검사
class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D401 — 접속 로그를 끈다
        pass


def _start_repo_server():
    handler = functools.partial(_QuietHandler, directory=str(REPO))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def execute(nb, user_agent: str, colab_sim: bool, timeout: int):
    from nbclient import NotebookClient

    nb = copy.deepcopy(nb)
    replaced = 0
    for c in nb.cells:
        if c.cell_type == "code" and UA_PLACEHOLDER in c.source:
            c.source = c.source.replace(UA_PLACEHOLDER, f'USER_AGENT = "{user_agent}"')
            replaced += 1
    assert replaced == 1, "USER_AGENT 자리표시자를 찾지 못함"
    nb.cells.append(new_code_cell(textwrap.dedent(CHECK_CELL).strip("\n"), id="instructor-check"))

    tmp = Path(tempfile.mkdtemp(prefix="d1nb_"))
    server = None
    try:
        if colab_sim:  # 저장소 밖 빈 폴더 + RAW_BASE = 로컬 HTTP(저장소 루트) → ②번 경로(내려받기)와 글꼴 내려받기를 시험
            server = _start_repo_server()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            for c in nb.cells:
                if c.cell_type == "code" and c.source.lstrip().startswith("# 0-3"):
                    c.source = re.sub(r'^RAW_BASE = ".*?"', f'RAW_BASE = "{base}"', c.source, count=1, flags=re.M)
            run_dir = tmp
        else:  # 저장소 구조를 흉내 낸 임시 폴더(labs/day1에서 실행, data·tools는 링크) → ①번 경로(로컬 파일)
            run_dir = tmp / "labs" / "day1"
            run_dir.mkdir(parents=True)
            for name in ("data", "tools"):
                try:
                    os.symlink(REPO / name, tmp / name, target_is_directory=True)
                except OSError:
                    shutil.copytree(REPO / name, tmp / name)
        client = NotebookClient(nb, timeout=timeout, kernel_name="python3",
                                resources={"metadata": {"path": str(run_dir)}})
        try:
            client.execute()
            err = None
        except Exception as e:  # CellExecutionError 등 — 실패한 셀까지의 출력은 nb에 남는다
            err = e
    finally:
        if server:
            server.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return nb, err


def extract_check(nb) -> dict:
    for c in nb.cells:
        if c.get("id") == "instructor-check":
            for out in c.get("outputs", []):
                text = out.get("text", "")
                for line in text.splitlines():
                    if line.startswith("CHECK_JSON="):
                        return json.loads(line[len("CHECK_JSON="):])
    raise RuntimeError("검산 셀 출력(CHECK_JSON)을 찾지 못함")


def stderr_outputs(nb) -> list[str]:
    msgs = []
    for c in nb.cells:
        for out in c.get("outputs", []):
            if out.get("output_type") == "stream" and out.get("name") == "stderr":
                msgs.append(f"{c.get('id')}: {out.get('text', '').strip()[:300]}")
    return msgs


def cross_check(chk: dict) -> list[tuple[str, str, str, bool]]:
    """실행 결과를 기준 파일과 대조한다. 반환: (항목, 노트북 값, 기준 값, 일치)"""
    import pandas as pd

    rows = []

    def add(name, got, exp, ok=None):
        rows.append((name, str(got), str(exp), (got == exp) if ok is None else ok))

    def close(a, b, rel=0.001):
        if a is None or b is None or (isinstance(b, float) and b != b):
            return a is None and (b is None or b != b)
        return abs(a - b) <= rel * max(abs(b), 1e-9)

    fig4 = REPO / "docs" / "assets" / "day1" / "day1_fig4_dpd_distribution.csv"
    if fig4.exists():
        add("연체 인보이스 수 vs 차트 fig4 표", chk["late_invoices"], int(pd.read_csv(fig4, encoding="utf-8-sig").invoices.sum()))
    raw_inv = REPO / "data" / "raw" / "invoices.csv"
    if raw_inv.exists():
        d = pd.read_csv(raw_inv, encoding="utf-8-sig", usecols=["dpd_final"]).dpd_final
        d = d[d > 0]
        add("연체 인보이스 수 vs raw dpd_final>0", chk["late_invoices"], int(len(d)))
        add("DPD 중앙값 vs raw", chk["late_dpd_median"], float(d.median()))
        add("DPD P90 vs raw", chk["late_dpd_p90"], float(d.quantile(0.9)))
    clean = ANSWERS / "d1_buyers_clean.csv"
    if clean.exists():
        cl = pd.read_csv(clean, encoding="utf-8-sig")
        add("바이어 수 vs d1_buyers_clean", chk["buyers"], int(len(cl)))
        add("연체 바이어 수 vs d1_buyers_clean", chk["overdue_buyers"], int((cl.max_dpd_days > 0).sum()))
        exp = {k: int(v) for k, v in cl.aging_bucket.value_counts().reindex(
            ["Current", "1-30", "31-60", "61-90", "91+"], fill_value=0).items()}
        add("바이어 에이징 분포 vs d1_buyers_clean", chk["buyer_aging"], exp)
    ref_csv = REPO / "data" / "day1" / "real_buyers_ratios.csv"
    if ref_csv.exists():
        ref = pd.read_csv(ref_csv, encoding="utf-8-sig", dtype={"cik": str})
        for label, cik, end, got_r, got_in in [
            ("iRobot FY2024", 1159167, chk["irbt_fy2024_end"], chk["irbt_fy2024_ratios"], chk["irbt_fy2024_inputs"]),
            (f"CIK {chk['other_cik']}", chk["other_cik"], chk["other_end"], chk["other_ratios"], None),
        ]:
            r = ref[(ref.cik.astype(int) == cik) & (ref.fiscal_period_end == end) & (ref.form == "10-K")]
            if r.empty:
                add(f"{label} 비교표 행", "없음", "있어야 함", False)
                continue
            r = r.iloc[0]
            for k, v in got_r.items():
                e = None if pd.isna(r[k]) else float(r[k])
                add(f"{label} {k} vs real_buyers_ratios", v, e, close(v, e))
            for k, v in (got_in or {}).items():
                e = None if pd.isna(r[k]) else float(r[k])
                add(f"{label} {k} vs real_buyers_ratios", v, e, close(v, e, 0))
    add("DSO 함수 자체 검산(손계산 71.6·67.2)", [round(x, 1) for x in chk["dso_selftest"]], [71.6, 67.2])
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", help="Colab 배지·RAW_BASE의 <org>를 이 값으로 바꾼다(기본: 그대로 둠)")
    ap.add_argument("--out", type=Path, default=NB_PATH, help="수강생 노트북 경로")
    ap.add_argument("--no-write", action="store_true", help="수강생 노트북 파일을 쓰지 않는다(실행 검사만)")
    ap.add_argument("--execute", action="store_true", help="임시 폴더에서 위→아래로 실행해 강사용 실행본을 저장하고 대조")
    ap.add_argument("--user-agent", default=None,
                    help="실행 검사(--execute) 때 SEC에 보낼 User-Agent — 본인 영문 이름 + 이메일(필수, 기본값 없음)")
    ap.add_argument("--colab-sim", action="store_true", help="Colab 흉내(저장소 밖 폴더, RAW_BASE 내려받기, 글꼴 내려받기)")
    ap.add_argument("--executed-out", type=Path, default=None, help="실행본 저장 경로(기본: 강사 answers 폴더)")
    ap.add_argument("--timeout", type=int, default=600, help="셀당 제한 시간(초)")
    a = ap.parse_args(argv)
    if a.execute:
        why = user_agent_problem(a.user_agent)
        if why:
            print("실행 검사를 시작하지 않음:", why)
            return 2

    nb = build_notebook(a.org)
    problems = lint_notebook(nb)
    if problems:
        print("노트북 규칙 위반:\n  " + "\n  ".join(problems))
        return 1
    n_code = sum(c.cell_type == "code" for c in nb.cells)
    print(f"셀 {len(nb.cells)}개(코드 {n_code} · 마크다운 {len(nb.cells) - n_code}) · 규칙 점검 통과")
    if not a.no_write:
        changed = write_if_changed(nb, a.out)
        print(("작성" if changed else "변경 없음") + f": {a.out}")
    if not a.execute:
        return 0

    executed, err = execute(nb, a.user_agent, a.colab_sim, a.timeout)
    default_out = (Path(tempfile.gettempdir()) / "d1_challenge_colab_sim.ipynb") if a.colab_sim \
        else (ANSWERS / "d1_challenge_executed.ipynb")          # Colab 흉내 실행은 강사 실행본을 덮어쓰지 않는다
    out = a.executed_out or default_out
    if err is not None:
        out = out.with_name(out.stem + "_FAILED.ipynb")
    out.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(executed, str(out))
    if err is not None:
        print(f"실행 실패 — 실패한 셀까지 저장: {out}\n{str(err)[-2000:]}")
        return 1
    print(f"실행 완료(오류 없음) → {out}")
    warn = stderr_outputs(executed)
    if warn:
        print("경고·stderr 출력:\n  " + "\n  ".join(warn))
    chk = extract_check(executed)
    print(f"iRobot FY2024 비율: {chk['irbt_fy2024_ratios']}")
    print(f"2026-09 DSO: {chk['dso_2026_09']}")
    rows = cross_check(chk)
    width = max(len(r[0]) for r in rows)
    for name, got, exp, ok in rows:
        print(f"  [{'OK' if ok else 'FAIL'}] {name:<{width}}  노트북={got}  기준={exp}")
    bad = [r for r in rows if not r[3]]
    print(f"대조 {len(rows)}건 중 불일치 {len(bad)}건")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
