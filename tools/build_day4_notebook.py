#!/usr/bin/env python
"""Day4 Challenge 노트북 `labs/day4/d4_challenge.ipynb`를 nbformat으로 만든다(출력 없는 수강생용).

(v3 — 이번 과정은 쓰지 않는다) PuLP · linprog 교차검증 · 몬테카를로 1-요인 · LP 정식화.
섹션: 0 준비 · A LP 입력(워크북 02_Buyers와 같은 식) · B PuLP 3.3.2 · C scipy linprog(HiGHS) 교차검증 ·
      D 16_Compare로 보내기 · E 제약 실험 · F 몬테카를로(독립 vs 1-요인) · G AI와 함께 확장 · H 셀프 체크

사용(저장소 루트에서):
  python tools/build_day4_notebook.py                 # 노트북만 만든다(출력·실행 번호 없음) + 규칙 점검
  python tools/build_day4_notebook.py --org myorg     # Colab 배지·RAW_BASE의 조직 이름(기본: config day4.github_org 또는 brainini)
  python tools/build_day4_notebook.py --execute       # + 실행 검사: 저장소 구조를 흉내 낸 임시 폴더에서 위→아래로 실행해
                                                      #   강사용 실행본(../instructor/day4/answers/d4_challenge_executed.ipynb)을 저장하고
                                                      #   목적함수·걸린 제약·몬테카를로를 강사 정답(_summary.json)과 대조
필요 패키지: nbformat(생성), nbclient·ipykernel·pandas·scipy·PuLP 3.3.2(실행 검사).
공개 저장소 파일 — 정답 숫자·강사 파일 이름을 노트북에 적지 않는다(실행 검사의 대조 셀은 사본에만 붙인다).
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = Path(__file__).resolve().parents[1]
NB_PATH = REPO / "labs" / "day4" / "d4_challenge.ipynb"
ANSWERS = REPO.parent / "instructor" / "day4" / "answers"
DEFAULT_ORG = "brainini"



def _private_tokens(day: str) -> list[str]:
    """린트용 정답 토큰을 비공개 파일에서 읽는다(D30) — 없으면 빈 목록."""
    import json as _json
    from pathlib import Path as _Path
    p = _Path(__file__).with_name("lint_tokens_private.json")
    return list(_json.loads(p.read_text(encoding="utf-8")).get(day, [])) if p.is_file() else []

def md(cid: str, text: str):
    return ("markdown", cid, text)


def code(cid: str, text: str):
    return ("code", cid, text)


CELLS = [
    md("title", r'''
# Day4 Challenge 노트북 — 한도 LP 교차검증(PuLP · linprog) · 몬테카를로 꼬리위험

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<org>/tradefin-ai-2026/blob/main/labs/day4/d4_challenge.ipynb)

Excel 해 찾기로 푼 **바이어별 신용한도 LP**를 파이썬으로 다시 풀어 같은 답이 나오는지 확인하고, Excel 몬테카를로(부도 독립 가정)와 **공통요인 모형**의 꼬리위험(P99)을 비교합니다.

| 절 | 시간 | 하는 일 | 워크북 연결 |
|---|---|---|---|
| 0 준비 | 5분 | 버전 확인(PuLP 3.3.2) · 글꼴 · 데이터 | — |
| A LP 입력 | 10분 | 워크북 02_Buyers와 같은 식으로 UB·LB·coef 만들기 | 02_Buyers · 10_LimitLP |
| B PuLP | 10분 | LP를 풀고 걸린 제약·잠재가격 읽기 | 10_LimitLP · 민감도 보고서 |
| C linprog | 5분 | 다른 풀이기(HiGHS)로 같은 최적값인지 확인 | — |
| D 비교 | 5분 | 해를 CSV로 받아 16_Compare에 붙이기 | 16_Compare |
| E 제약 실험 | 10분 | 제약을 끄거나 정책값을 바꿔 목적함수·걸린 제약 비교 | 01_Params |
| F 몬테카를로 | 10분 | 10,000회 · 독립 vs 1-요인(ρ = 0.2) · P95·P99 | 11_Scenario |
| G·H | 남는 시간 | AI와 함께 확장 · 셀프 체크 | — |

**Colab에서 여는 법**: 위 배지를 누르고 **파일 → Drive에 사본 저장**을 누릅니다(내 사본에서 작업해야 저장됩니다). 셀은 위에서 아래로 **Shift+Enter**로 실행합니다.

> **데이터 위생** — (가상) 한빛정밀(주) 교육용 합성 데이터만 씁니다. 회사 실데이터(바이어명·담당자·계좌)는 이 노트북에도, Colab AI에도 넣지 않습니다.

> **막히면** — 오류 메시지의 마지막 줄을 옆 사람이나 강사에게 보여 주세요. 꼬이면 **런타임 → 세션 다시 시작** 후 맨 위부터.
'''),
    md("s0", r'''
## 0. 준비 (5분)

1. **0-1 버전** — PuLP는 수업 고정 버전 **3.3.2**입니다. 4.0.0(2026-09-25 출시)은 `LpVariable` 쓰는 법이 바뀌고 CBC 풀이기가 빠져 이 노트북이 멈춥니다. 셀이 3.3.2를 알아서 설치합니다(`-U` 업그레이드 금지).
2. **0-2 한글 글꼴** — 그래프 한글이 □로 깨지지 않게 합니다.
3. **0-3 데이터** — ① 내 컴퓨터의 과정 저장소 폴더 → ② 과정 저장소 웹 주소(`RAW_BASE`, Day4 08:30 공개) → ③ 직접 업로드 순서로 찾습니다.
'''),
    code("c0-1", r'''
# 0-1. 파이썬·라이브러리 버전을 확인하고 PuLP 3.3.2를 준비한다(없거나 다른 버전이면 설치)
import sys, subprocess, importlib, importlib.metadata as md_
import numpy as np
import pandas as pd

def pulp_version():
    try:
        return md_.version("pulp")
    except md_.PackageNotFoundError:
        return None

if pulp_version() != "3.3.2":
    if "pulp" in sys.modules:
        print("다른 버전의 PuLP가 이미 불러와져 있습니다 → 설치 후 '런타임 → 세션 다시 시작'을 누르고 이 셀부터 다시 실행하세요.")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "PuLP==3.3.2"], check=True)
    importlib.invalidate_caches()
import pulp
from scipy.optimize import linprog
import scipy

print("Python", sys.version.split()[0], "| pandas", pd.__version__, "| numpy", np.__version__, "| scipy", scipy.__version__)
print("PuLP  ", pulp.__version__, "| 쓸 수 있는 풀이기:", pulp.listSolvers(onlyAvailable=True))
assert pulp.__version__ == "3.3.2", "PuLP 3.3.2가 아닙니다 — 런타임을 다시 시작하고 이 셀부터 실행하세요"
pd.set_option("display.float_format", "{:,.2f}".format)
pd.set_option("display.max_columns", 30)
'''),
    code("c0-2", r'''
# 0-2. 그래프 한글이 깨지지 않게 나눔고딕 글꼴을 등록한다(Colab은 한 번 내려받는다)
import urllib.request
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"

def find_upwards(rel):
    """지금 폴더와 위쪽 폴더(3단계까지)에서 rel 파일을 찾는다. 없으면 None."""
    here = Path.cwd().resolve()
    for base in [here, *here.parents][:4]:
        if (base / rel).is_file():
            return base / rel
    return None

font_file = find_upwards("tools/fonts/NanumGothic-Regular.ttf") or Path("NanumGothic-Regular.ttf")
try:
    if not font_file.is_file():
        urllib.request.urlretrieve(FONT_URL, font_file.with_suffix(".part"))
        font_file.with_suffix(".part").rename(font_file)
    font_manager.fontManager.addfont(str(font_file))
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font_file)).get_name()
except Exception as e:
    print("글꼴 등록 실패 — 그래프 한글이 □로 보일 수 있지만 계산은 그대로 됩니다:", e)
plt.rcParams.update({"axes.unicode_minus": False, "figure.dpi": 100, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
BLUE, ORANGE, GRAY = "#1F5FD1", "#C2410C", "#666666"
print("글꼴:", plt.rcParams["font.family"])
'''),
    code("c0-3", r'''
# 0-3. 데이터 파일을 찾아 읽는다 — ① 과정 저장소 폴더 → ② 과정 저장소 웹 주소 → ③ 직접 업로드
RAW_BASE = "https://raw.githubusercontent.com/<org>/tradefin-ai-2026/main"   # <org>가 남아 있으면 강사가 알려 준 이름으로 바꾼다

def get_file(rel):
    """rel 예: 'data/checkpoints/d4_params.csv' → 읽을 수 있는 파일 경로."""
    found = find_upwards(rel) or find_upwards(Path(rel).name)
    if found:
        return found
    target = Path(rel)
    if "<org>" not in RAW_BASE:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"{RAW_BASE}/{rel}", target)
            return target
        except Exception as e:
            print("내려받기 실패(Day4 08:30 공개 전이면 정상):", e)
    try:
        from google.colab import files
    except ImportError:
        raise FileNotFoundError(f"{rel} 을(를) 찾지 못했습니다. 과정 저장소 폴더에서 실행하거나 RAW_BASE를 확인하세요.") from None
    print(f"'{target.name}' 파일을 골라 올려 주세요.")
    return Path(next(iter(files.upload())))

d4 = pd.read_csv(get_file("data/checkpoints/d4_start_scored.csv"), encoding="utf-8-sig", dtype={"buyer_id": str})
params = pd.read_csv(get_file("data/checkpoints/d4_params.csv"), encoding="utf-8-sig")
scen = pd.read_csv(get_file("data/checkpoints/d4_scenarios.csv"), encoding="utf-8-sig")
open_inv = pd.read_csv(get_file("data/checkpoints/d4_open_inv.csv"), encoding="utf-8-sig", keep_default_na=False)
P = dict(zip(params.excel_name, params.value.astype(float)))   # 워크북 01_Params의 이름 그대로(TSOFR3M, PD_S, …)
ASOF = pd.Timestamp("2026-09-30")
print(f"바이어 {len(d4)} · 파라미터 {len(P)} · 시나리오 {len(scen)} · 미결 인보이스 {len(open_inv)}")
print("Term SOFR 3M:", f"{P['TSOFR3M']:.3%}", "| 자기자본:", f"{P['Equity_USD']:,.0f}", "| α:", f"{P['Alpha']:.0%}")
'''),
    # ------------------------------------------------------------------------------------------ A
    md("sA", r'''
## A. LP 입력 만들기 — 워크북 02_Buyers와 같은 식 (10분)

워크북의 회색 열을 파이썬으로 그대로 옮깁니다. **판단(IF·MIN)은 모두 여기서 미리 계산하고, LP에는 숫자(UB·LB·coef)만 넘긴다** — Excel에서 결정변수에 IF를 걸면 '선형 조건 불충족'이 나는 이유와 같습니다.

| 기호 | 뜻 | 식 |
|---|---|---|
| r_i | 위험조정 할인율 | TSOFR3M + 가산(등급) + [부보: 보험료 × 365 ÷ 결제기간 + PD × LGD × (1 − 보상비율) / 무보험: PD × LGD] |
| coef_i | 한도 1달러의 연간 가치 | 사용률 × (매출총이익률 × 365 ÷ 결제기간 − r_i) |
| Need | 필요 한도 | 월평균 매출 × (결제기간 + 15) ÷ 30 |
| UB | 상한 | MIN(Need, 등급 상한, 보험 한도 + 자기 감당 한도). L/C·선수금·선적 보류·신용사건이면 0 |
| LB | 하한 | 전략 바이어만 MIN(50% × 현행 한도, UB) |
'''),
    code("cA-1", r'''
# A-1. 바이어별 UB·LB·coef·EL 계수를 만든다(워크북 02_Buyers 계산 열과 같은 정의)
GRADE_RULE = "t"            # 워크북 01_Params GradeRule과 같게 — "t"(Day3 정본 등급) 또는 "quantile"(분위수 등급)
GR = ["S", "A", "B", "C"]

def lp_inputs(d4, P, open_inv, rule="t"):
    g = (d4.grade_quantile if rule == "quantile" else d4.grade).astype(str)
    pick = lambda name: g.map({k: P[f"{name}_{k}"] for k in GR}).astype(float)
    terms = d4.terms_days.astype(float)
    ins = d4.ksure_insured.eq("Y")
    lc = d4.payment_method.isin(["LC_SIGHT", "LC_USANCE"])
    f = pd.DataFrame({"buyer_id": d4.buyer_id, "country": d4.country_code, "grade_used": g})
    f["PD_g"] = pick("PD")
    f["PD_eff"] = np.where(d4.bankruptcy_flag.eq(1), 1.0, f.PD_g)        # 신용사건 바이어 잔액 = 이미 손상
    f["LGD_i"] = np.where(lc, P["LGD_LC"], P["LGD"])
    f["cov_i"] = np.where(ins, P["Cov"], 0.0)
    spread, prem = pick("Spread"), pick("Prem")
    f["spread_g"] = spread
    with np.errstate(divide="ignore", invalid="ignore"):
        r_un = P["TSOFR3M"] + spread + f.PD_g * f.LGD_i
        r_in = P["TSOFR3M"] + spread + prem * 365 / terms + f.PD_g * f.LGD_i * (1 - P["Cov"])
        r_i = np.where(ins, r_in, r_un)
        coef = P["Util"] * (P["GM"] * 365 / terms - r_i)
    f["need"] = d4.monthly_sales_usd * (terms + P["Grace"]) / 30
    cap = g.map({"S": np.nan, "A": P["Cap_A"], "B": P["Cap_B"], "C": P["Cap_C_OA"]}).astype(float)
    f["cap"] = np.where(g.eq("S"), f.need, cap)
    f["ins"] = np.where(ins, d4.ksure_limit_usd, 0.0)
    f["self"] = P["Equity_USD"] * pick("s")
    # 선적 보류 = 신용사건 또는 비 L/C 미결이 결제기일 + 30일 이상(13_EarlyWarning과 같은 규칙)
    o = open_inv.assign(dpd=(ASOF - pd.to_datetime(open_inv.due_date)).dt.days)
    nonlc = o.paid.eq("N") & ~o.payment_method.isin(["LC_SIGHT", "LC_USANCE", "TT_ADV"])
    over30 = o[nonlc & (o.dpd >= 30)].groupby("buyer_id").size()
    hold = d4.bankruptcy_flag.eq(1) | d4.buyer_id.map(over30).fillna(0).gt(0)
    scope = d4.payment_method.isin(["LC_SIGHT", "LC_USANCE", "TT_ADV"])
    f["ship_hold"] = hold
    f["ub"] = np.where(scope | hold, 0.0, np.minimum(np.minimum(f.need, f.cap), f.ins + f["self"]))
    f["lb"] = np.where(d4.strategic_flag.eq(1), np.minimum(P["StratMin"] * d4.current_limit_usd, f.ub), 0.0)
    f["coef"] = np.where((terms > 0) & (f.ub > 0), coef, 0.0)
    f["elc"] = P["Util"] * f.PD_g * f.LGD_i * (1 - f.cov_i)
    return f

f = lp_inputs(d4, P, open_inv, GRADE_RULE)
print("등급:", f.grade_used.value_counts().reindex(GR).to_dict(), "| 선적 보류", int(f.ship_hold.sum()), "곳")
print(f"상한 합 ΣUB = {f.ub.sum():,.0f} · 하한 합 ΣLB = {f.lb.sum():,.0f} · UB > 0인 바이어 {int((f.ub > 0).sum())}곳")
f.sort_values("coef", ascending=False).head(8)[["buyer_id", "country", "grade_used", "ub", "lb", "coef", "elc"]]
'''),
    code("cA-2", r'''
# A-2. 제약 행렬 A·b를 만든다: ① 총허용익스포저 ② 미부보 EL 예산 ③ 국가 한도 20개 ④ B등급 비중
def excel_round(x, nd):                      # Excel ROUND와 같게(0.5는 0에서 먼 쪽)
    q = 10.0 ** nd
    return np.sign(x) * np.floor(abs(x) * q + 0.5) / q

def band(crc):
    if pd.isna(crc) or crc <= 2:
        return "CtryCap_02"
    return {3: "CtryCap_3", 4: "CtryCap_45", 5: "CtryCap_45"}.get(int(crc), "CtryCap_67")

def lp_system(f, d4, P, drop=()):
    total_cap = excel_round(P["TotalCapShare"] * f.ub.sum(), -5)
    rows, rhs, names = [np.ones(len(f))], [total_cap], ["total_cap"]
    rows.append(f.elc.to_numpy()); rhs.append(P["Equity_USD"] * P["Alpha"]); names.append("el_budget")
    crc_by_country = d4.groupby("country_code").oecd_crc.first()
    for c, crc in crc_by_country.items():
        rows.append(d4.country_code.eq(c).to_numpy(float)); rhs.append(P[band(crc)] * total_cap); names.append(f"ctry_{c}")
    rows.append(f.grade_used.eq("B").to_numpy(float)); rhs.append(P["ShareCap_B"] * total_cap); names.append("b_share")
    keep = [k for k, n in enumerate(names) if not any(n.startswith(p) for p in drop)]
    return {"A": np.vstack(rows)[keep], "b": np.array(rhs)[keep], "names": [names[k] for k in keep], "total_cap": total_cap}

S = lp_system(f, d4, P)
print(f"총허용익스포저 TotalCap = ROUND(70% × ΣUB, −5) = {S['total_cap']:,.0f}")
print(f"제약(변수 상·하한 제외) {len(S['names'])}개 — Excel 해 찾기 한도 100개 안 · 결정변수 {len(f)}개 — 한도 200개 안")
'''),
    code("cA-3", r'''
# A-3. (선택) 내가 Excel에서 '저장한' 워크북이 있으면 10_LimitLP 값과 파이썬 입력을 대조한다
#      데스크톱 Excel에서 저장해야 수식 결과(캐시 값)가 파일에 들어 있다 — 저장하지 않은 파일은 빈칸으로 읽힌다
MY_WORKBOOK = ""            # 예: "d4_end_limits__T1-01.xlsx" (Colab이면 왼쪽 폴더 아이콘으로 올린 뒤 이름을 적는다)
if MY_WORKBOOK and Path(MY_WORKBOOK).is_file():
    mine = pd.read_excel(MY_WORKBOOK, sheet_name="10_LimitLP", header=3, usecols="A:H", nrows=150)
    mine.columns = ["buyer_id", "country", "grade", "UB", "LB", "L", "coef", "elc"]
    chk = mine.merge(f[["buyer_id", "ub", "lb", "coef"]], on="buyer_id", suffixes=("_xl", "_py"))
    print("UB 최대 차이", (chk.UB - chk.ub).abs().max(), "| LB 최대 차이", (chk.LB - chk.lb).abs().max(),
          "| coef 최대 차이", (chk.coef_xl - chk.coef_py).abs().max(), " (0에 가까우면 같은 입력)")
else:
    print("건너뜀 — MY_WORKBOOK에 파일 이름을 적으면 대조합니다")
'''),
    # ------------------------------------------------------------------------------------------ B
    md("sB", r'''
## B. PuLP 3.3.2로 풀기 (10분)

03 Part2 §4.11의 셀 2를 그대로 씁니다. `lowBound`·`upBound`는 **키워드로** 넘깁니다(4.0.0에서도 같은 코드가 돌게).

- **잠재가격(`pi`)** = 그 제약의 오른쪽 값을 1 늘리면 목적함수가 얼마나 늘어나는가. Excel 민감도 보고서의 '잠재 가격'과 같은 숫자입니다.
- **걸린 제약(binding)** = 여유(slack)가 0인 제약. 걸리지 않은 제약의 잠재가격은 0입니다.
'''),
    code("cB-1", r'''
# B-1. PuLP 모델을 만들고 CBC로 푼다
ids = f.buyer_id.tolist()
prob = pulp.LpProblem("hanbit_limit_lp", pulp.LpMaximize)
L = {b: pulp.LpVariable(f"L_{b}", lowBound=float(lo), upBound=float(hi)) for b, lo, hi in zip(ids, f.lb, f.ub)}
prob += pulp.lpSum(float(c) * L[b] for b, c in zip(ids, f.coef)), "obj"
for k, name in enumerate(S["names"]):
    row = S["A"][k]
    prob += pulp.lpSum(float(row[i]) * L[b] for i, b in enumerate(ids) if row[i] != 0) <= float(S["b"][k]), name
status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
obj_pulp = pulp.value(prob.objective)
x_pulp = np.array([L[b].value() for b in ids])
print("상태:", pulp.LpStatus[status], "| 목적함수(연간 기대 이익 지표):", f"{obj_pulp:,.2f}")
print("제안 한도 합계:", f"{x_pulp.sum():,.0f}", "= TotalCap", f"{S['total_cap']:,.0f}")
'''),
    code("cB-2", r'''
# B-2. 걸린 제약과 잠재가격(민감도 보고서와 같은 숫자)을 표로 본다
cons = pd.DataFrame([{"제약": n, "여유(slack)": prob.constraints[n].slack, "잠재가격(pi)": prob.constraints[n].pi}
                     for n in S["names"]])
cons["걸림"] = np.where(cons["여유(slack)"].abs() < 0.5, "걸림", "")
display(cons[cons["걸림"].eq("걸림") | cons["잠재가격(pi)"].abs().gt(1e-9)])
print("읽는 법: total_cap의 pi = '총허용익스포저 1달러를 늘리면 연간 기대 이익이 pi달러 늘어난다'")
'''),
    code("cB-3", r'''
# B-3. 바이어 위치: 상한까지 채움(UB) · 하한(LB) · 그 사이(한계 바이어) · 0
pos = np.select([f.ub <= 0, x_pulp >= f.ub - 0.01, (f.lb > 0) & (x_pulp <= f.lb + 0.01), x_pulp <= 0.01],
                ["UB 0(대상 아님·C·보류·신용사건·매출 0)", "UB까지", "LB(전략 하한)", "0"], "사이(한계 바이어)")
print(pd.Series(pos).value_counts().to_string())
res = f.assign(L_pulp=x_pulp, dj=[L[b].dj for b in ids], current=d4.current_limit_usd)
res[pos == "사이(한계 바이어)"][["buyer_id", "country", "grade_used", "coef", "lb", "ub", "L_pulp"]]
'''),
    # ------------------------------------------------------------------------------------------ C
    md("sC", r'''
## C. scipy `linprog`(HiGHS)로 교차검증 (5분)

다른 풀이기로 **같은 최적값**이 나오는지 봅니다. `linprog`는 최소화만 하므로 목적함수에 −1을 곱합니다.
바이어별 L은 다를 수 있습니다 — **같은 coef(같은 등급·결제기간·부보)인 바이어끼리는 누구를 채워도 목적함수가 같기 때문**(대안 최적해)입니다.
'''),
    code("cC-1", r'''
# C-1. linprog(HiGHS)로 같은 LP를 풀고 목적함수·잠재가격을 PuLP와 비교한다
r = linprog(-f.coef.to_numpy(), A_ub=S["A"], b_ub=S["b"], bounds=list(zip(f.lb, f.ub)), method="highs")
obj_highs = -r.fun
duals = dict(zip(S["names"], -r.ineqlin.marginals))
print("HiGHS:", r.message)
print(f"목적함수 PuLP {obj_pulp:,.4f} · HiGHS {obj_highs:,.4f} · 상대 차이 {abs(obj_pulp - obj_highs) / obj_highs:.2e}  (< 0.01% 이면 같은 최적값)")
for n in cons.loc[cons["걸림"].eq("걸림"), "제약"]:
    print(f"  {n}: 잠재가격 PuLP {prob.constraints[n].pi:.4f} · HiGHS {duals[n]:.4f}")
diff = pd.DataFrame({"buyer_id": ids, "coef": f.coef.round(6), "L_pulp": x_pulp, "L_highs": r.x})
diff = diff[(diff.L_pulp - diff.L_highs).abs() > 1]
tie = f.coef.round(6).where(f.ub > 0).value_counts()
diff["같은 coef 바이어 수"] = diff.coef.map(tie)
print(f"바이어별 L이 1달러 넘게 다른 곳 {len(diff)}곳 — 모두 같은 coef 그룹(대안 최적해)인지 확인:")
diff
'''),
    # ------------------------------------------------------------------------------------------ D
    md("sD", r'''
## D. 워크북 16_Compare로 보내기 (5분)

1. 아래 셀이 `lp_limits_pulp.csv`를 만듭니다(Colab이면 자동으로 내려받기 창이 뜹니다).
2. CSV를 열어 `L_pulp` 열 150칸을 복사 → 워크북 **10_LimitLP의 P5**에 값 붙여넣기(P열이 접혀 있으면 열 머리글의 + 를 누른다).
3. 16_Compare에서 '같은 최적값' ✔, 잠재가격 표(민감도 보고서 값을 10_LimitLP Z열에 적었다면)를 확인합니다.
'''),
    code("cD-1", r'''
# D-1. PuLP 해를 바이어 순서 그대로 CSV로 저장한다(워크북 10_LimitLP P열에 붙여 넣을 값)
out = pd.DataFrame({"buyer_id": ids, "L_pulp": np.round(x_pulp, 2), "L_highs": np.round(r.x, 2)})
out.to_csv("lp_limits_pulp.csv", index=False, encoding="utf-8-sig")
print("저장: lp_limits_pulp.csv", out.shape)
try:
    from google.colab import files
    files.download("lp_limits_pulp.csv")
except ImportError:
    pass
'''),
    # ------------------------------------------------------------------------------------------ E
    md("sE", r'''
## E. 제약 실험 — "끄면 무엇이 바뀌나" (10분)

03 Part2 §4.6 13단계(Excel)와 같은 실험을 한 번에 돌립니다. **걸리지 않은 제약은 꺼도 해가 그대로**이고, 정책값(α·TotalCap 비율·등급 규칙)을 바꾸면 걸리는 제약이 달라집니다.
'''),
    code("cE-1", r'''
# E-1. 실험 표: 제약 끄기 · α · 총량 비율 · 등급 규칙 → 목적함수와 걸린 제약
def solve_case(rule="t", drop=(), **over):
    P2 = dict(P, **over)
    f2 = lp_inputs(d4, P2, open_inv, rule)
    S2 = lp_system(f2, d4, P2, drop)
    r2 = linprog(-f2.coef.to_numpy(), A_ub=S2["A"], b_ub=S2["b"], bounds=list(zip(f2.lb, f2.ub)), method="highs")
    slack = S2["b"] - S2["A"] @ r2.x
    du = -r2.ineqlin.marginals
    bind = [f"{n}({d:.2f})" for n, s, d in zip(S2["names"], slack, du) if s < 0.5 and abs(d) > 1e-9]
    return {"목적함수": -r2.fun, "Σ L": r2.x.sum(), "EL 사용": f2.elc.to_numpy() @ r2.x, "걸린 제약(잠재가격)": " · ".join(bind)}

cases = {"기준": solve_case(), "② EL 예산 끔": solve_case(drop=("el_budget",)), "③ 국가 한도 끔": solve_case(drop=("ctry_",)),
         "④ B등급 비중 끔": solve_case(drop=("b_share",)), "α 3% → 0.02%": solve_case(Alpha=0.0002),
         "총량 70% → 80%": solve_case(TotalCapShare=0.80), "등급 = 분위수(quantile)": solve_case(rule="quantile")}
exp = pd.DataFrame(cases).T
exp["목적함수 변화"] = exp["목적함수"] - exp.loc["기준", "목적함수"]
exp[["목적함수", "목적함수 변화", "Σ L", "EL 사용", "걸린 제약(잠재가격)"]]
'''),
    md("sE2", r'''
**생각해 볼 것** — ② EL 예산(자기자본 × 3%)은 왜 걸리지 않을까요? 연 EL 사용액이 예산의 몇 %인지 보세요. α를 0.02%로 낮추면 어떤 나라·바이어의 한도가 줄고, 왜 **부보(보상비율 95%)한 바이어가 살아남는지** 설명해 보세요(EL 계수의 (1 − 보상비율)).
'''),
    # ------------------------------------------------------------------------------------------ F
    md("sF", r'''
## F. 몬테카를로 — 독립 가정 vs 공통요인 (10분)

Excel 11_Scenario의 몬테카를로는 바이어마다 `RAND() < PD`로 **독립적으로** 부도를 뽑습니다. 실제로는 경기·환율 같은 **공통 충격**에 바이어가 함께 흔들립니다. 1-요인 모형은 이 상관을 넣습니다.

- 부도 조건: √ρ · Z + √(1−ρ) · ε_i < Φ⁻¹(PD_i) — Z는 모든 바이어 공통, ε_i는 바이어별(ρ = 0이면 독립 = Excel과 같다).
- 같은 평균 손실(EL)에서 **P99(100번 중 가장 나쁜 1번)**가 얼마나 커지는지가 핵심입니다.
'''),
    code("cF-1", r'''
# F-1. 시나리오별 손실 분포를 10,000회 뽑는다(현재 미결 잔액, 1년) — 독립(ρ=0)과 1-요인(ρ=0.2)
from scipy.stats import norm

def simulate(sid, n=10_000, rho=0.0, seed=20261019):
    s = scen.set_index("scenario_id").loc[sid]
    p = np.minimum(1.0, f.PD_eff.to_numpy() * s.pd_multiplier)
    lc = d4.payment_method.isin(["LC_SIGHT", "LC_USANCE"]).to_numpy()
    lgd = np.where(lc, P["LGD_LC"], np.minimum(1.0, P["LGD"] + s.lgd_adj))
    loss = d4.open_ar_usd.to_numpy() * lgd * (1 - f.cov_i.to_numpy())
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n, 1))
    e = rng.standard_normal((n, len(p)))
    default = np.sqrt(rho) * z + np.sqrt(1 - rho) * e < norm.ppf(np.clip(p, 1e-12, 1 - 1e-12))
    default[:, p >= 1] = True
    return (default * loss).sum(axis=1), float((p * loss).sum())

rows, dists = [], {}
for sid in ["S0", "S3", "S4"]:
    for rho in (0.0, 0.2):
        tot, el = simulate(sid, rho=rho)
        dists[(sid, rho)] = tot
        rows.append({"시나리오": sid, "ρ": rho, "해석적 EL": el, "평균": tot.mean(), "P95": np.percentile(tot, 95),
                     "P99": np.percentile(tot, 99), "평균/EL − 1": tot.mean() / el - 1})
mc = pd.DataFrame(rows)
mc
'''),
    code("cF-2", r'''
# F-2. S3(심각)의 손실 분포를 겹쳐 그린다 — 꼬리(오른쪽 끝)가 어떻게 달라지나
fig, ax = plt.subplots(figsize=(8, 3.6))
for rho, color in [(0.0, BLUE), (0.2, ORANGE)]:
    ax.hist(dists[("S3", rho)] / 1000, bins=60, alpha=0.55, color=color, label=f"상관 rho = {rho}")
    ax.axvline(np.percentile(dists[("S3", rho)], 99) / 1000, color=color, ls="--", lw=1.2)
ax.set_xlabel("1년 손실(USD 천)")
ax.set_ylabel("횟수(10,000회 중)")
ax.set_title("S3 심각 시나리오 손실 분포 — 점선 = P99")
ax.legend()
plt.show()
print("메시지: 같은 평균(EL)이어도 공통요인이 있으면 P99가 커진다 → '독립 가정은 꼬리위험을 과소평가한다'")
'''),
    # ------------------------------------------------------------------------------------------ G
    md("sG", r'''
## G. AI와 함께 확장 (남는 시간)

Colab의 **Gemini** 버튼(또는 Claude)에 아래처럼 요청하고, **나온 코드를 그대로 믿지 말고** 결과를 B·C절 숫자와 대조합니다.

1. "B-1의 LP에 '바이어 1곳 한도 ≤ 자기자본 × 2%'(집중한도) 제약을 추가하는 코드를 써 줘. 걸린 제약이 어떻게 바뀌는지도 출력해 줘."
2. "F-1에서 ρ를 0, 0.1, 0.2, 0.3으로 바꿔 S3의 P99를 표로 비교하는 코드를 써 줘."
3. "E-1 표를 경영진에게 설명하는 3줄을 써 줘. 표에 없는 숫자는 쓰지 마."

> Colab AI 기능은 프롬프트·코드·출력을 사람 검토자가 볼 수 있고 일정 기간 보관합니다. 회사 실데이터는 넣지 않습니다.
'''),
    md("sH", r'''
## H. 셀프 체크

- [ ] PuLP 버전 3.3.2, 상태 Optimal
- [ ] PuLP와 HiGHS 목적함수 상대 차이 < 0.01%
- [ ] 걸린 제약 2개(총허용익스포저 · 국가 한도 1개)와 그 잠재가격을 Excel 민감도 보고서와 대조
- [ ] 바이어별 L이 다른 곳은 모두 같은 coef 그룹(대안 최적해)
- [ ] 몬테카를로 평균이 해석적 EL과 ±5% 안 · ρ = 0.2의 P99 > ρ = 0의 P99
- [ ] `lp_limits_pulp.csv`를 16_Compare에 붙였다
'''),
]

CHECK_CELL = r'''
# (강사용 검산 셀 — 실행 검사 사본에만 붙는다) 핵심 값을 JSON으로 출력
import json as _json
_chk = {"pulp_version": pulp.__version__, "status": pulp.LpStatus[status], "obj_pulp": obj_pulp, "obj_highs": obj_highs,
        "total_cap": S["total_cap"], "sum_ub": float(f.ub.sum()),
        "binding": {n: prob.constraints[n].pi for n in S["names"] if abs(prob.constraints[n].slack) < 0.5 and abs(prob.constraints[n].pi) > 1e-9},
        "diff_all_ties": bool((diff["같은 coef 바이어 수"] > 1).all()) if len(diff) else True,
        "exp": {k: round(float(v), 2) for k, v in exp["목적함수"].items()},
        "mc": {f"{r_.시나리오}|{r_.ρ}": {"el": r_["해석적 EL"], "mean": r_.평균, "p99": r_.P99} for _, r_ in mc.iterrows()}}
print("CHECK_JSON=" + _json.dumps(_chk, ensure_ascii=False, default=float))
'''


def build_notebook(org: str):
    nb = new_notebook()
    for kind, cid, text in CELLS:
        src = textwrap.dedent(text).strip("\n")
        src = src.replace("github/<org>/tradefin-ai-2026", f"github/{org}/tradefin-ai-2026")
        src = src.replace("githubusercontent.com/<org>/tradefin-ai-2026", f"githubusercontent.com/{org}/tradefin-ai-2026")
        nb.cells.append(new_markdown_cell(src, id=cid) if kind == "markdown" else new_code_cell(src, id=cid))
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"}, "colab": {"provenance": [], "toc_visible": True}}
    nbformat.validate(nb)
    return nb


def lint_notebook(nb) -> list[str]:
    """수강생 노트북 규칙: 코드 셀 첫 줄 = 한국어 주석, 출력·실행 번호 없음, 강사 자료·정답 숫자 언급 없음."""
    problems = []
    for c in nb.cells:
        if c.cell_type == "code":
            first = c.source.splitlines()[0]
            if not (first.startswith("# ") and re.search(r"[가-힣]", first)):
                problems.append(f"{c.id}: 첫 줄이 한국어 주석이 아님 → {first[:50]}")
            if c.get("outputs") or c.get("execution_count"):
                problems.append(f"{c.id}: 출력이 남아 있음")
        for bad in ("instructor/", "answers/", "lp_solution", "_summary.json", "d4_end_limits.xlsx", "solved", *_private_tokens("day4")):
            if bad in c.source:
                problems.append(f"{c.id}: 강사 자료·정답 언급({bad})")
    return problems


def write_if_changed(nb, path: Path) -> bool:
    text = nbformat.writes(nb) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def execute(nb, timeout: int):
    from nbclient import NotebookClient
    nb = copy.deepcopy(nb)
    nb.cells.append(new_code_cell(textwrap.dedent(CHECK_CELL).strip("\n"), id="instructor-check"))
    tmp = Path(tempfile.mkdtemp(prefix="d4nb_"))
    try:
        run_dir = tmp / "labs" / "day4"
        run_dir.mkdir(parents=True)
        for name in ("data", "tools"):
            try:
                os.symlink(REPO / name, tmp / name, target_is_directory=True)
            except OSError:
                shutil.copytree(REPO / name, tmp / name)
        client = NotebookClient(nb, timeout=timeout, kernel_name="python3", resources={"metadata": {"path": str(run_dir)}})
        try:
            client.execute()
            err = None
        except Exception as e:  # 실패한 셀까지의 출력은 nb에 남는다
            err = e
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return nb, err


def extract_check(nb) -> dict:
    for c in nb.cells:
        if c.get("id") == "instructor-check":
            for out in c.get("outputs", []):
                for line in out.get("text", "").splitlines():
                    if line.startswith("CHECK_JSON="):
                        return json.loads(line[len("CHECK_JSON="):])
    raise RuntimeError("검산 셀 출력(CHECK_JSON)을 찾지 못함")


def cross_check(chk: dict) -> list[tuple[str, bool, str]]:
    out = []
    p = ANSWERS / "_summary.json"
    if not p.exists():
        return [("강사 정답(_summary.json)", True, "없음 — 대조 생략(solve_day4_lp.py 먼저)")]
    s = json.loads(p.read_text(encoding="utf-8"))
    lp = s["lp"]
    out.append(("PuLP 3.3.2 · Optimal", chk["pulp_version"] == "3.3.2" and chk["status"] == "Optimal", f"{chk['pulp_version']} {chk['status']}"))
    out.append(("목적함수 = 강사 정답(상대 1e-6)", abs(chk["obj_pulp"] - lp["objective"]) / lp["objective"] < 1e-6,
                f"{chk['obj_pulp']:,.4f} vs {lp['objective']:,.4f}"))
    out.append(("HiGHS 목적함수 = PuLP(0.01%)", abs(chk["obj_highs"] - chk["obj_pulp"]) / chk["obj_pulp"] < 1e-4, f"{chk['obj_highs']:,.4f}"))
    out.append(("TotalCap", abs(chk["total_cap"] - lp["total_cap"]) < 0.5, f"{chk['total_cap']:,.0f}"))
    out.append(("걸린 제약·잠재가격 = 강사 정답", set(chk["binding"]) == set(lp["binding"]) and
                all(abs(chk["binding"][k] - lp["binding"][k]) < 1e-4 for k in lp["binding"]), json.dumps(chk["binding"])))
    out.append(("PuLP·HiGHS 바이어 차이는 모두 동점 그룹", chk["diff_all_ties"], str(chk["diff_all_ties"])))
    ex = {e["experiment"]: e["objective"] for e in s.get("experiments", [])}
    pairs = [("기준", "기준(정본)"), ("② EL 예산 끔", "② EL 예산 끔"), ("③ 국가 한도 끔", "③ 국가 한도 끔"),
             ("α 3% → 0.02%", "α 3% → 0.02%(EL 예산 2천 달러)"), ("총량 70% → 80%", "TotalCapShare 70% → 80%"),
             ("등급 = 분위수(quantile)", "GradeRule = quantile(🔵)")]
    bad = [a for a, b in pairs if b in ex and abs(chk["exp"][a] - ex[b]) > 0.05]
    out.append(("제약 실험 목적함수 = 강사 정답", not bad, f"불일치 {bad}"))
    sc = {r["scenario_id"]: r["el_usd"] for r in s["scenarios"]}
    mbad = []
    for key, v in chk["mc"].items():
        sid, rho = key.split("|")
        if abs(v["el"] - sc[sid]) > 0.01 or abs(v["mean"] / v["el"] - 1) > 0.05:
            mbad.append(key)
    tail = all(chk["mc"][f"{sid}|0.2"]["p99"] > chk["mc"][f"{sid}|0.0"]["p99"] for sid in ("S0", "S3", "S4"))
    out.append(("몬테카를로: 해석적 EL = 강사 시나리오 EL · 평균 ±5% · ρ0.2 P99 > 독립", not mbad and tail, f"불일치 {mbad} · 꼬리 {tail}"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", default=None, help="GitHub 조직 이름(기본: config day4.github_org 또는 brainini)")
    ap.add_argument("--execute", action="store_true", help="실행 검사 + 강사용 실행본 저장")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)
    org = a.org
    if not org:
        try:
            import yaml
            org = yaml.safe_load((REPO / "tools" / "config.yaml").read_text(encoding="utf-8"))["day4"]["github_org"]
        except Exception:
            org = DEFAULT_ORG
    nb = build_notebook(org)
    probs = lint_notebook(nb)
    if probs:
        print("규칙 점검 실패:", *probs, sep="\n  ")
        return 1
    changed = write_if_changed(nb, NB_PATH)
    print(f"{'썼음' if changed else '변경 없음'}: {NB_PATH.relative_to(REPO)} (셀 {len(nb.cells)}개, 조직 {org}) · 규칙 점검 통과")
    if not a.execute:
        return 0
    ex, err = execute(nb, a.timeout)
    ANSWERS.mkdir(parents=True, exist_ok=True)
    out_p = ANSWERS / ("d4_challenge_executed.ipynb" if err is None else "d4_challenge_executed_FAILED.ipynb")
    out_p.write_text(nbformat.writes(ex) + "\n", encoding="utf-8")
    if err is not None:
        print("실행 실패:", str(err).splitlines()[-1] if str(err) else err, "→", out_p)
        return 1
    res = cross_check(extract_check(ex))
    for n, ok, d in res:
        print(f"[{'PASS' if ok else 'FAIL'}] {n}  {d}")
    print("실행본 →", out_p)
    return 0 if all(ok for _, ok, _ in res) else 1


if __name__ == "__main__":
    sys.exit(main())
