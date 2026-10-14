#!/usr/bin/env python
"""Day2 Challenge 노트북 `labs/day2/d2_challenge.ipynb`를 nbformat으로 만든다(출력 없는 수강생용).

(v3 — 이번 과정은 쓰지 않는다) 2일차 Challenge 노트북 — AsOf 2026-08-31 · 결측 대체 · 뉴스 점수 기준선. 정의는 강사 자료.
섹션: 0 준비 · A 진단(수정 금지) · B 통화·금액·기준일 환율(merge_asof) · C 결측 대체(중앙값 + 표시 vs KNN)
      · D 스케일링은 파이프라인 안에서 · E 특성 공학(정본 열 이름, 기준일 2026-08-31 150행)
      · F 뉴스 점수 — LLM 없는 사전(lexicon) 기준선 + 골든셋 일치도 · G 집계·병합·저장 · H GDELT 톤 공식·(선택) Colab AI · I 셀프 체크

사용(저장소 루트에서):
  python tools/build_day2_notebook.py                 # 노트북만 만든다(출력·실행 번호 없음) + 규칙 점검
  python tools/build_day2_notebook.py --org myorg     # Colab 배지·RAW_BASE의 조직 이름(기본: config day4.github_org 또는 brainini)
  python tools/build_day2_notebook.py --execute       # + 실행 검사: 임시 폴더에서 위→아래로 실행해 강사용 실행본
                                                      #   (../instructor/day2/answers/d2_challenge_executed.ipynb)을 저장하고
                                                      #   🟢 Excel 기대값·정본 특성표(2026-08-31 행)와 대조
  실행 검사는 15:35 공개 파일(골든셋 d2_news_answer.csv)과 강사 채점본 앞 7열(= '점수화를 못 끝낸 사람'용 d2_news_scored.csv)을
  실행 폴더에 넣어 Step 7·8 흐름까지 돌린다.
필요 패키지: nbformat(생성), nbclient·ipykernel·pandas·openpyxl·scikit-learn·matplotlib(실행 검사).
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
NB_PATH = REPO / "labs" / "day2" / "d2_challenge.ipynb"
ANSWERS = REPO.parent / "instructor" / "day2" / "answers"
DEFAULT_ORG = "brainini"


def md(cid: str, text: str):
    return ("markdown", cid, text)


def code(cid: str, text: str):
    return ("code", cid, text)


CELLS = [
    md("title", r'''
# Day2 Challenge 노트북 — 정제 규칙을 코드로: 통화·환율 시차·결측 대체·특성·뉴스 위험지수

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<org>/tradefin-ai-2026/blob/main/labs/day2/d2_challenge.ipynb)

엑셀·Orange로 하는 블록 A·B를 **같은 규칙으로 코드로** 한 번 더 합니다. 엑셀에서 만든 숫자를 여기서 **검산**하고, 손으로 하기 힘든 일(인보이스 1,902건의 날짜 형식 정리, 인보이스별 환율, KNN 대체)을 해 봅니다.

| 절 | 블록 · Step | 하는 일 | 엑셀·Orange에서 같은 일 |
|---|---|---|---|
| 0 준비 | 시작 5분 | 버전 · 글꼴 · 데이터 | — |
| A 진단 | Step 1 | 오염 유형을 **세기만** 한다(수정 금지) | 필터 · P1-3 |
| B 통화·금액·환율 | Step 3 | 통화 매핑 · 숫자 변환 · 기준일 환율(`merge_asof`) · USD 환산 · 단위 점검 · 인보이스별 환차손익 | XLOOKUP(−1) · SWITCH |
| C 결측 대체 | Step 4 | 재무비율 4종: 중앙값 + 빈칸 표시 vs KNN | Orange Impute |
| D 스케일링 | Step 4 | 스케일링은 학습 파이프라인 **안에서** | Orange Preprocess(보기만) |
| E 특성 공학 | Step 4 · 8 | 정본 열 이름으로 바이어 150곳 × 51열 | 시트 `features` |
| F 뉴스 점수 | Step 6–7 | LLM 없는 **사전 기준선** → 골든셋 일치도(MAE · ±2 비율) | P2-2 · P2-3 · `news_review` |
| G 집계·저장 | Step 8 | 30일 창 뉴스 집계 → 병합 → `d2_end_features_challenge.csv` | COUNTIFS · AVERAGEIFS · Merge Data |
| H GDELT·Colab AI | Step 5–6 🟣 | 톤 → 0–10 공식 · (선택) Colab AI로 점수화 | — |

**Colab에서 여는 법**: 위 배지 → **파일 → Drive에 사본 저장**. 셀은 위에서 아래로 **Shift+Enter**로 실행합니다.

**오늘의 기준(정제 규칙과 같다)**: 기준일 **AsOf = 2026-08-31**(시트 `buyers`의 스냅샷 날짜) · 환율은 AsOf 이전 가장 가까운 영업일 값(as-of), 엔화는 100엔 단위 → ÷100 · 뉴스 창 = **(AsOf − 30일, AsOf]** · 재무비율 빈칸 = 같은 기준일 150개사 중앙값 + 빈칸 표시 열.

> **데이터 위생** — (가상) 한빛정밀(주) 교육용 합성 데이터와 FRED 공개 환율만 씁니다. 회사 실데이터(바이어명·담당자·계좌)는 이 노트북에도, Colab AI에도 넣지 않습니다.
'''),
    md("s0", r'''
## 0. 준비 (5분)

1. **0-1 버전** — 숫자만 보고 넘어갑니다.
2. **0-2 한글 글꼴** — 그래프 한글이 □로 깨지지 않게 합니다.
3. **0-3 데이터** — ① 내 컴퓨터의 과정 저장소 폴더 → ② 과정 저장소 웹 주소(`RAW_BASE`, Day2 08:30 공개) → ③ 직접 업로드 순서로 찾습니다.
'''),
    code("c0-1", r'''
# 0-1. 파이썬·라이브러리 버전을 확인한다
import sys, re, json, warnings
import numpy as np
import pandas as pd
import sklearn, matplotlib
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
print("Python", sys.version.split()[0], "| pandas", pd.__version__, "| numpy", np.__version__,
      "| scikit-learn", sklearn.__version__, "| matplotlib", matplotlib.__version__)
pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 160)
'''),
    code("c0-2", r'''
# 0-2. 그래프 한글이 깨지지 않게 나눔고딕 글꼴을 등록한다(Colab은 한 번 내려받는다)
import urllib.request
from pathlib import Path
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
BLUE, ORANGE, GREEN, GRAY = "#1F5FD1", "#C2410C", "#15803D", "#666666"
print("글꼴:", plt.rcParams["font.family"])
'''),
    code("c0-3", r'''
# 0-3. 데이터 파일을 찾아 읽는다 — ① 과정 저장소 폴더 → ② 과정 저장소 웹 주소 → ③ 직접 업로드
RAW_BASE = "https://raw.githubusercontent.com/<org>/tradefin-ai-2026/main"   # <org>가 남아 있으면 강사가 알려 준 이름으로 바꾼다

def get_file(rel, required=True):
    """rel 예: 'data/checkpoints/d2_start.xlsx' → 읽을 수 있는 파일 경로(required=False면 못 찾을 때 None)."""
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
            print(f"내려받기 실패 — {Path(rel).name}(공개 전이면 정상):", e)
    if not required:
        return None
    try:
        from google.colab import files
    except ImportError:
        raise FileNotFoundError(f"{rel} 을(를) 찾지 못했습니다. 과정 저장소 폴더에서 실행하거나 RAW_BASE를 확인하세요.") from None
    print(f"'{target.name}' 파일을 골라 올려 주세요.")
    return Path(next(iter(files.upload())))

XLSX = get_file("data/checkpoints/d2_start.xlsx")
raw = pd.read_excel(XLSX, sheet_name="buyers")                            # 오염 그대로(수정 금지) — 글자로 저장된 숫자는 str로 들어온다
bfr = pd.read_excel(XLSX, sheet_name="buyer_features_raw")                # 정본 원천 300행(기준일 2개)
fx_ref = pd.read_excel(XLSX, sheet_name="fx_at_ref")                      # 기준일 환율표(12행)
inv_raw = pd.read_excel(XLSX, sheet_name="invoices_raw", dtype=str)       # 🟣 인보이스 1,902건(최근 12개월, 오염 포함)
fx = pd.read_csv(get_file("data/checkpoints/fx_krw_daily.csv"), encoding="utf-8-sig")
news = pd.read_csv(get_file("data/checkpoints/d2_news.csv"), encoding="utf-8-sig")
d1 = pd.read_csv(get_file("data/day1/d1_buyers_raw.csv"), encoding="utf-8-sig")   # buyer_type(공공 바이어 구분)만 가져온다
for name, df in [("buyers", raw), ("buyer_features_raw", bfr), ("fx_at_ref", fx_ref), ("invoices_raw", inv_raw),
                 ("fx_krw_daily", fx), ("d2_news", news)]:
    print(f"{name:<19} {df.shape}")
ASOF = pd.Timestamp("2026-08-31")
'''),
    # ------------------------------------------------------------------------------------------ A
    md("sA", r'''
## A. 진단 — 고치기 전에 센다 (Step 1, 수정 금지)

1일차 P1-3와 같은 습관입니다. 원본(`raw`)은 **바꾸지 않고** 유형별로 셉니다. 결과를 `dirty_list` 시트의 '내 진단'과 대조하세요.
'''),
    code("cA-1", r'''
# A-1. 오염 유형별로 센다 — 통화 표기 · 숫자 칸의 문자 · 재무 원시 항목 빈칸 · 자기자본 ≤ 0 · OECD '-' · 중복
NUM_COLS = ["ar_balance", "ar_current", "ar_1_30", "ar_31_60", "ar_61_90", "ar_91p"]
FIN = ["current_assets", "current_liabilities", "total_liabilities", "equity", "revenue"]
is_text = lambda s: s.map(lambda v: isinstance(v, str))              # 숫자 칸인데 글자로 저장된 칸(엑셀의 초록 삼각형)
diag = [
    ("통화 표기 혼재", "currency", " · ".join(f"{k} {v}" for k, v in raw.currency.value_counts().items()),
     int((~raw.currency.isin(["USD", "EUR", "JPY", "CNY"])).sum())),
    *[("숫자 칸의 문자", c, ", ".join(raw.loc[is_text(raw[c]), c].head(3)), int(is_text(raw[c]).sum())) for c in NUM_COLS if is_text(raw[c]).any()],
    ("재무 원시 항목 빈칸", "+".join(FIN), "5개 항목 중 하나라도 빈칸", int(raw[FIN].isna().any(axis=1).sum())),
    ("자기자본 ≤ 0", "equity", ", ".join(raw.loc[pd.to_numeric(raw.equity, errors="coerce") <= 0, "buyer_id"]),
     int((pd.to_numeric(raw.equity, errors="coerce") <= 0).sum())),
    ("국가위험 미분류", "oecd_crc", "'-'", int((raw.oecd_crc == "-").sum())),
    ("완전 중복 행", "(모든 열)", "", int(raw.duplicated().sum())),
]
pd.DataFrame(diag, columns=["유형", "열", "예", "행 수"])
'''),
    # ------------------------------------------------------------------------------------------ B
    md("sB", r'''
## B. 통화·금액·기준일 환율 (Step 3)

엑셀 수식과 1:1로 대응합니다.

| 엑셀(Step 3) | 이 절 |
|---|---|
| `ccy_clean = XLOOKUP(TRIM(currency), map_ccy[raw], map_ccy[clean], "확인필요")` | `MAP_CCY` 사전 + `.map()` |
| `amt_num = --SUBSTITUTE(…)` + P2-1로 남는 칸 | `to_number()` — 정규식으로 숫자·소수점·부호만 남기고 `k` = ×1,000 |
| `fx_usd = XLOOKUP(AsOf, fx[date], fx[usd_krw], , −1)` | `pd.merge_asof(…, direction="backward")` = '같은 날이 없으면 직전 영업일' |
| `ar_balance_usd = amt_num × 원/통화 ÷ 원/달러` | `krw_per_ccy / fx_usd` |
'''),
    code("cB-1", r'''
# B-1. 통화 매핑과 숫자 변환 — 바꾸지 못한 칸이 0개인지 확인한다
MAP_CCY = {"USD": "USD", "usd": "USD", "US$": "USD", "EUR": "EUR", "euro": "EUR", "JPY": "JPY", "yen": "JPY",
           "CNY": "CNY", "RMB": "CNY"}

def to_number(s):
    """'CNY 317,000' · '155,200 CNY' · '47.0k' · ' 12,480 ' → 숫자. 못 바꾸면 NaN."""
    if pd.isna(s):
        return np.nan
    t = str(s).strip().lower().replace(",", "").replace(" ", "")
    mult = 1000 if t.endswith("k") else 1
    t = re.sub(r"[^0-9.\-]", "", t)
    try:
        return float(t) * mult
    except ValueError:
        return np.nan

b = raw[["buyer_id", "currency", "credit_limit_usd", "late_30d"]].copy()
b["ccy_clean"] = raw.currency.str.strip().map(MAP_CCY).fillna("확인필요")
for c in NUM_COLS:
    b[f"{c}_num"] = raw[c].map(to_number)
left = {c: int((raw[c].notna() & b[f"{c}_num"].isna()).sum()) for c in NUM_COLS}
print("ccy_clean:", b.ccy_clean.value_counts().to_dict(), "| '확인필요'", int((b.ccy_clean == "확인필요").sum()))
print("숫자로 못 바꾼 칸:", left)
b.loc[is_text(raw.ar_balance), ["buyer_id", "currency", "ccy_clean", "ar_balance_num"]].assign(원본=raw.ar_balance[is_text(raw.ar_balance)])
'''),
    code("cB-2", r'''
# B-2. 기준일 환율(as-of) — merge_asof(direction="backward") = XLOOKUP(…, −1). 엔화는 100엔 단위 → ÷100
fx["date"] = pd.to_datetime(fx["date"]).astype("datetime64[ns]")
fx = fx.sort_values("date").reset_index(drop=True)
RATE = {"USD": "usd_krw", "EUR": "eur_krw", "CNY": "cny_krw", "JPY": "jpy100_krw"}

def krw_per_unit(dates, ccy):
    """날짜 목록 → 그날(없으면 직전 영업일) '원/통화 1단위'. JPY는 100엔당 값이라 100으로 나눈다."""
    q = pd.DataFrame({"d": pd.to_datetime(pd.Series(dates)).astype("datetime64[ns]")}).reset_index()
    m = pd.merge_asof(q.sort_values("d"), fx, left_on="d", right_on="date", direction="backward").sort_values("index")
    v = m[RATE[ccy]].to_numpy(dtype=float)
    return v / 100 if ccy == "JPY" else v

fx_asof = {c: float(krw_per_unit([ASOF], c)[0]) for c in RATE}
print("AsOf", ASOF.date(), "→ 원/통화:", {k: round(v, 4) for k, v in fx_asof.items()})
sat = pd.Timestamp("2026-02-28")       # 토요일 → 직전 영업일(금) 값이 들어와야 한다
print("2026-02-28(토) USD →", krw_per_unit([sat], "USD")[0], "(직전 영업일 값)")
ref = fx_ref[pd.to_datetime(fx_ref.ref_date) == ASOF].assign(ccy=lambda d: d.ccy.str.replace("JPY100", "JPY"))
ref = ref.assign(krw_1unit=np.where(ref.ccy == "JPY", ref.krw_close / 100, ref.krw_close))
print("시트 fx_at_ref와 같은가:", all(abs(fx_asof[c] - v) < 1e-9 for c, v in zip(ref.ccy, ref.krw_1unit)))
b["krw_per_ccy"] = b.ccy_clean.map(fx_asof)
b["ar_balance_usd"] = (b.ar_balance_num * b.krw_per_ccy / fx_asof["USD"]).round(2)
b[["buyer_id", "currency", "ccy_clean", "ar_balance_num", "krw_per_ccy", "ar_balance_usd"]].head(10)
'''),
    code("cB-3", r'''
# B-3. 변환했으면 검산한다 — ① 잔액 = 에이징 버킷 합계인가 ② USD 잔액 > 신용한도 × 10 이면 '단위 의심'([교육용 가정])
bucket_sum = b[[f"{c}_num" for c in NUM_COLS[1:]]].sum(axis=1)
b["unit_flag"] = np.where(b.ar_balance_usd > 10 * pd.to_numeric(b.credit_limit_usd), "단위 의심", "")
gap = ~np.isclose(b.ar_balance_num, bucket_sum)
print("잔액 ≠ 버킷 합계:")
display(b.loc[gap, ["buyer_id", "currency", "ar_balance_num", "unit_flag"]].assign(버킷_합계=bucket_sum[gap], 원본=raw.ar_balance[gap]))
# 원천(버킷·인보이스 원장)을 확인한 뒤 고친다 — 고친 이유는 dirty_list에 '무엇 · 왜 · 어떻게'로 남긴다
fix_unit = (b.unit_flag != "") & np.isclose(b.ar_balance_num / 1000, bucket_sum)                 # 1,000배로 입력된 값
fix_k = gap & raw.ar_balance.astype(str).str.strip().str.lower().str.endswith("k") & ((b.ar_balance_num - bucket_sum).abs() <= 50)
b.loc[fix_unit, "ar_balance_num"] = b.loc[fix_unit, "ar_balance_num"] / 1000
b.loc[fix_k, "ar_balance_num"] = bucket_sum[fix_k]                                                  # 'k' 표기는 반올림돼 정밀도를 잃는다
b["ar_balance_usd"] = (b.ar_balance_num * b.krw_per_ccy / fx_asof["USD"]).round(2)
print("고친 행 — 단위(÷1,000):", list(b.buyer_id[fix_unit]), "· 'k' 표기 반올림(→ 버킷 합계):", list(b.buyer_id[fix_k]),
      "· 남은 불일치:", int((~np.isclose(b.ar_balance_num, bucket_sum)).sum()))
yen = 1_000_000
print(f"퀴즈 — 100만 엔: ÷100 하면 USD {yen * fx_asof['JPY'] / fx_asof['USD']:,.0f} · 빠뜨리면 USD {yen * fx_asof['JPY'] * 100 / fx_asof['USD']:,.0f}")
'''),
    code("cB-4", r'''
# B-4. 🟣 인보이스 원장 — 날짜 형식 4종 · 금액 문자 정리 → 발행일·결제일 환율(merge_asof) → 환차손익(원)
def to_date(s):
    """'2025-09-01' · '16/09/2025'(일/월) · '2025.9.8' · 'Sep 7 2025' → 날짜."""
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y.%m.%d", "%b %d %Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            pass
    return pd.NaT

inv = inv_raw.copy()
inv["invoice_date"] = inv.invoice_date.map(to_date)
for c in ("due_date", "settled_date"):
    inv[c] = pd.to_datetime(inv[c], errors="coerce")
inv["ccy"] = inv.currency.str.strip().map(MAP_CCY)
inv["amount_num"] = inv.amount.map(to_number)
ym_ok = inv.invoice_date.dt.strftime("%y%m") == inv.invoice_id.str[4:8]          # INV-2509-… = 2025년 9월 발행
print(f"날짜를 못 읽은 행 {inv.invoice_date.isna().sum()} · 번호의 연월과 다른 행 {(~ym_ok).sum()}"
      f" · 금액 빈칸 {inv.amount.isna().sum()}(원천 결측 — 채우지 않고 환차손익에서 뺀다) · 금액을 못 읽은 글자 {(inv.amount.notna() & inv.amount_num.isna()).sum()}")
inv["krw_inv"] = np.nan
inv["krw_set"] = np.nan
for c in RATE:
    m = (inv.ccy == c) & inv.invoice_date.notna()
    inv.loc[m, "krw_inv"] = krw_per_unit(inv.loc[m, "invoice_date"], c)
    s = m & inv.settled_date.notna()
    inv.loc[s, "krw_set"] = krw_per_unit(inv.loc[s, "settled_date"], c)
inv["fx_gain_loss_krw"] = (inv.amount_num * (inv.krw_set - inv.krw_inv)).round(0)       # +면 받을 때 원화가 더 많다(환차익)
summary = (inv[inv.settled_date.notna()].groupby("ccy")
             .agg(결제_건수=("invoice_id", "size"), 환차손익_합계_백만원=("fx_gain_loss_krw", lambda x: round(x.sum() / 1e6, 1)),
                  환차익_건수=("fx_gain_loss_krw", lambda x: int((x > 0).sum()))))
summary
'''),
    # ------------------------------------------------------------------------------------------ C
    md("sC", r'''
## C. 결측 대체 — 중앙값 + 빈칸 표시 vs KNN (Step 4)

정제 규칙(정본): **재무비율 4종만** 같은 기준일 150개사 **중앙값**으로 채우고, 채웠다는 사실을 `is_missing_*` 열(1 = 원래 빈칸)로 남깁니다. 자기자본 ≤ 0이면 부채비율을 먼저 빈칸으로 만들고 `negative_equity_flag = 1`.
이력이 없어 '정의되지 않는' 값(`pay_score` · 180일 창 지표 · 잔액 0인 바이어의 에이징 비중 · `dpd_trend`)은 **채우지 않습니다**.

KNN(최근접 이웃) 대체는 비교용입니다 — 비슷한 바이어의 값을 빌려 오므로 분포를 덜 망가뜨리지만, **결측이 신흥국에 몰려 있으면** 이웃도 한쪽으로 치우칩니다.
'''),
    code("cC-1", r'''
# C-1. 시트 buyers의 원시 재무 항목으로 비율 4종 + 자본잠식 + 재무 빈칸 플래그(엑셀 §2.6 수식과 같은 정의)
f = raw.copy()
for c in FIN + ["accounts_receivable", "operating_income"]:
    f[c] = pd.to_numeric(f[c], errors="coerce")
b["current_ratio"] = (f.current_assets / f.current_liabilities.where(f.current_liabilities > 0)).round(4)
b["neg_equity"] = (f.equity <= 0).astype("Int64").where(f.equity.notna())
b["debt_to_equity"] = (f.total_liabilities / f.equity.where(f.equity > 0)).round(4)          # 자기자본 ≤ 0 → 빈칸
rev = f.revenue.where(f.revenue > 0)
b["dso_buyer"] = (f.accounts_receivable / rev * 365).round(2)
b["op_margin"] = (f.operating_income / rev).round(4)
b["fin_missing"] = (f[FIN].notna().sum(axis=1) < 5).astype(int)
RAT = ["current_ratio", "debt_to_equity", "dso_buyer", "op_margin"]
med = b[RAT].median()
print("빈칸 수:", b[RAT].isna().sum().to_dict(), "| fin_missing = 1:", int(b.fin_missing.sum()), "| 자본잠식:", list(b.buyer_id[b.neg_equity == 1]))
print("중앙값(Orange Impute의 Fixed value에 넣을 값):", med.round(4).to_dict())
'''),
    code("cC-2", r'''
# C-2. 중앙값 대체 vs KNN 대체(이웃 5) — 원래 빈칸이던 행만 골라 분포를 겹쳐 본다
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.preprocessing import StandardScaler
ctx = ["pct_ar_31p_tmp", "late_ratio_tmp", "country_risk_tmp"]          # KNN이 '비슷한 바이어'를 찾을 때 쓰는 열
tmp = b[RAT].copy()
tmp["pct_ar_31p_tmp"] = (b[["ar_31_60_num", "ar_61_90_num", "ar_91p_num"]].sum(axis=1) / b.ar_balance_num.where(b.ar_balance_num > 0)).fillna(0)
tmp["late_ratio_tmp"] = (pd.to_numeric(raw.late_invoices_12m) / pd.to_numeric(raw.invoices_12m).where(pd.to_numeric(raw.invoices_12m) > 0)).fillna(0)
tmp["country_risk_tmp"] = pd.to_numeric(raw.oecd_crc.replace("-", "0"))
sc = StandardScaler().fit(tmp)
knn = pd.DataFrame(sc.inverse_transform(KNNImputer(n_neighbors=5).fit_transform(sc.transform(tmp))), columns=tmp.columns)
medf = tmp[RAT].fillna(med)
miss = b.current_ratio.isna()
fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
ax[0].hist(b.current_ratio.dropna(), bins=30, color=GRAY, alpha=0.6, label="원래 값")
ax[0].hist(knn.current_ratio[miss], bins=30, color=BLUE, alpha=0.8, label="KNN으로 채운 값")
ax[0].axvline(med.current_ratio, color=ORANGE, lw=2, label=f"중앙값으로 채운 값({miss.sum()}행 모두)")
ax[0].set(title="유동비율 — 빈칸을 무엇으로 채웠나", xlabel="current_ratio"); ax[0].legend(fontsize=8)
band = np.select([raw.oecd_crc == "-", pd.to_numeric(raw.oecd_crc.replace("-", "0")) >= 3], ["미분류('-')", "CRC 3 이상"], "CRC 0–2")
share = pd.Series(b.fin_missing.to_numpy()).groupby(band).agg(["sum", "size"])
ax[1].bar(share.index, share["sum"] / share["size"], color=[GRAY, ORANGE, BLUE])
ax[1].set(title="재무 빈칸 비율 — 국가위험 구간별", ylabel="fin_missing 비율")
plt.tight_layout(); plt.show()
print("구간별 재무 빈칸(행/전체):", {k: f"{int(r['sum'])}/{int(r['size'])}" for k, r in share.iterrows()})
'''),
    # ------------------------------------------------------------------------------------------ D
    md("sD", r'''
## D. 스케일링은 학습 파이프라인 안에서 (Step 4, 5분)

Min-Max(0–1)·Standard(평균 0·표준편차 1) 스케일링은 **학습 데이터로만** 기준(최솟값·평균 등)을 정해야 합니다. 분할 전에 전체로 맞추면 시험 데이터 정보가 새어 들어갑니다(누수).
그래서 정본 특성표에는 스케일링한 열(`_z`·`_mm`)을 **저장하지 않고**, 내일 모델의 파이프라인 안에서 합니다(Orange: Test and Score의 Preprocessor 입력).
'''),
    code("cD-1", r'''
# D-1. 같은 열의 Min-Max · Standard 값 비교 → 파이프라인 안 스케일링(교차검증 폴드마다 학습 데이터로만 fit)
from sklearn.preprocessing import MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
cols = ["open_ar_usd", "avg_dpd_180d", "current_ratio"]
d31 = bfr[pd.to_datetime(bfr.ref_date) == ASOF].reset_index(drop=True)
view = d31[["buyer_id"] + cols].head(5).copy()
view[[c + "_mm" for c in cols]] = MinMaxScaler().fit_transform(d31[cols].fillna(d31[cols].median()))[:5].round(3)
view[[c + "_z" for c in cols]] = StandardScaler().fit_transform(d31[cols].fillna(d31[cols].median()))[:5].round(3)
display(view)
num = d31.select_dtypes("number").drop(columns=["late_30d", "oecd_crc"])
pipe = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()), ("clf", LogisticRegression(max_iter=2000))])
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
auc = cross_val_score(pipe, num, d31.late_30d, cv=cv, scoring="roc_auc")
print(f"파이프라인 안 스케일링 — 교차검증 AUC 평균 {auc.mean():.3f}(폴드 {np.round(auc, 3)}). 트리 모델(xgboost·LightGBM)은 스케일링이 필요 없다")
'''),
    # ------------------------------------------------------------------------------------------ E
    md("sE", r'''
## E. 특성 공학 — 정본 열 이름으로 (Step 4 · 8)

엑셀 실습 가이드의 이름(왼쪽)과 정본 이름(오른쪽)은 이렇게 대응합니다. 내일 Day3 시작 파일 `d3_start_features.csv`가 정본 이름을 씁니다.

| 실습 가이드(엑셀) | 정본 | 메모 |
|---|---|---|
| `ar_balance_usd` | `open_ar_usd` | 미결 잔액(USD) |
| `max_dpd` | `oldest_open_days` | 최장 미결 연체일 |
| `avg_days_late` | `avg_days_late_12m` | |
| `late_ratio`(12개월 발행) | `late_share_180d` | 정본은 180일 창 비율 |
| `dispute_ratio` | `dispute_share_365d` | 정본은 365일 창 |
| `neg_equity` · `fin_missing` | `negative_equity_flag` · `is_missing_*`(4개) | |
| `dso_buyer` | `dso` | |
| `oecd_crc` | `country_risk` + `crc_unclassified` | '-' → 0 + 플래그 |

이 절은 **기준일 2026-08-31 150개사**(기본 트랙과 같은 범위)를 정본 51열로 만듭니다. 이력 지표는 `buyer_features_raw`, 에이징·추세는 시트 `buyers`(B절에서 정리), 환율은 `fx_krw_daily.csv`, 뉴스는 G절에서 붙입니다.
'''),
    code("cE-1", r'''
# E-1. 정본 특성표(뉴스 열 제외) — 원천 열 + 파생 열(국가위험·연체 잔액 USD·자본잠식·빈칸 표시·중앙값 대체·에이징·추세·환율)
CANON = ["buyer_id", "ref_date", "country_code", "region", "segment", "buyer_type", "industry", "payment_method", "terms_days",
         "ksure_insured", "country_risk", "crc_unclassified", "n_invoices_cum", "avg_days_to_pay", "avg_dpd_180d", "max_dpd_180d",
         "late_share_180d", "over30_count_365d", "dispute_share_365d", "cum_dpd_days", "open_ar_usd", "overdue_amount_usd",
         "pct_current", "pct_ar_31p", "pct_91plus", "oldest_open_days", "ksure_30d_flag", "avg_days_late_12m", "dpd_trend",
         "current_ratio", "debt_to_equity", "dso", "op_margin", "negative_equity_flag", "is_missing_current_ratio",
         "is_missing_debt_to_equity", "is_missing_dso", "is_missing_op_margin", "pay_score", "fx_krw_close", "fx_chg_30d",
         "fx_chg_60d", "fx_chg_30d_lag30", "usd_krw_close", "usd_krw_chg_30d", "news_cnt_30d", "news_sent_0_10_30d",
         "news_sent_min_30d", "news_risk_30d", "no_news_flag", "late_30d"]
e = d31.copy()
e["ref_date"] = ASOF.strftime("%Y-%m-%d")
e["buyer_type"] = e.buyer_id.map(d1.drop_duplicates("buyer_id").set_index("buyer_id").buyer_type)
e["country_risk"] = e.oecd_crc.fillna(0).astype(int)
e["crc_unclassified"] = e.oecd_crc.isna().astype(int)
e["overdue_amount_usd"] = [round(a * fx_asof[c] / fx_asof["USD"], 2) for a, c in zip(e.overdue_amount, e.overdue_ccy)]
e["negative_equity_flag"] = (e.debt_to_equity < 0).astype(int)                 # D/E < 0 ⇔ 자기자본 < 0
e["debt_to_equity"] = e.debt_to_equity.where(e.debt_to_equity >= 0)
for r in ["current_ratio", "debt_to_equity", "dso", "op_margin"]:
    e[f"is_missing_{r}"] = e[r].isna().astype(int)
    e[r] = e[r].fillna(e[r].median()).round(2 if r == "dso" else 4)            # 같은 기준일 150개사 중앙값
s = b.set_index("buyer_id")                                                    # 시트 buyers(B절에서 숫자로 정리) — 2026-08-31 스냅샷
bal = s.ar_balance_num.where(s.ar_balance_num > 0)
aging = pd.DataFrame({
    "pct_current": (s.ar_current_num / bal).round(4),
    "pct_ar_31p": ((s.ar_31_60_num + s.ar_61_90_num + s.ar_91p_num) / bal).round(4),
    "pct_91plus": (s.ar_91p_num / bal).round(4),
    "oldest_open_days": pd.to_numeric(raw.set_index("buyer_id").max_dpd),
    "ksure_30d_flag": (((s.ar_31_60_num + s.ar_61_90_num + s.ar_91p_num) > 0)
                       & ~raw.set_index("buyer_id").payment_method.isin(["LC_SIGHT", "LC_USANCE", "TT_ADV"])).astype(int),
    "avg_days_late_12m": pd.to_numeric(raw.set_index("buyer_id").avg_days_late_12m),
    "dpd_trend": (pd.to_numeric(raw.set_index("buyer_id").avg_dpd_last3m) - pd.to_numeric(raw.set_index("buyer_id").avg_dpd_prev3m)).round(1),
})
e = e.join(aging, on="buyer_id")
k0, k30, k60 = ({c: float(krw_per_unit([ASOF - pd.Timedelta(days=d)], c)[0]) for c in RATE} for d in (0, 30, 60))
e["fx_krw_close"] = e.overdue_ccy.map(k0).round(4)
e["fx_chg_30d"] = (e.overdue_ccy.map(k0) / e.overdue_ccy.map(k30) - 1).round(4)
e["fx_chg_60d"] = (e.overdue_ccy.map(k0) / e.overdue_ccy.map(k60) - 1).round(4)
e["fx_chg_30d_lag30"] = (e.overdue_ccy.map(k30) / e.overdue_ccy.map(k60) - 1).round(4)
e["usd_krw_close"] = round(k0["USD"], 2)
e["usd_krw_chg_30d"] = round(k0["USD"] / k30["USD"] - 1, 4)
print("만든 열:", len([c for c in CANON if c in e.columns]), "/", len(CANON), "· 뉴스 열 5개는 G절에서")
e[["buyer_id", "country_risk", "overdue_amount_usd", "pct_ar_31p", "oldest_open_days", "debt_to_equity", "is_missing_debt_to_equity", "fx_chg_30d"]].head()
'''),
    # ------------------------------------------------------------------------------------------ F
    md("sF", r'''
## F. 뉴스 위험지수 — LLM 없는 사전(lexicon) 기준선 (Step 6–7)

AI 점수의 '바닥선'을 만듭니다. 규칙은 P2-2 v1 앵커와 같습니다(점수 방향: **부정·위험 0–5, 긍정 6–10**).

| 점수 | 앵커 | label |
|---|---|---|
| 0 | 파산·회생 신청 | severe(0–2) |
| 1–2 | 약정 위반 · 계속기업 의문 · 지급 불능 · 임금 체불 | severe |
| 3–4 | 대금 지연 · 신용등급 하향 · 주요 고객 이탈 · 대규모 감원 · 손실 | high(3–4) |
| 5 | 약한 부정(경계): 실적 둔화 전망 · 원가 상승 · 소규모 소송 · 투자·가동 연기 | watch(5) |
| 6–8 | 중립·일상: 신제품 · 전시회 · 인사 | low(6–10) |
| 9–10 | 지급 위험을 낮춤: 대형 수주 · 증자 · 대출 확보 · 등급 상향 | low |

**사전 기준선**: 금융 뉴스에 흔한 단어를 네 묶음(심각 1 · 뚜렷한 부정 3 · 약한 부정 5 · 긍정 9)으로 나누고, 걸리는 단어가 없으면 7(일상 소식)로 둡니다. 위에서부터(심각한 것부터) 검사해 **처음 맞는 묶음**의 점수를 쓰고, 헤드라인에서 못 찾으면 본문에서 찾습니다. 점수를 5단계만 쓰므로 골든셋의 0 · 2 · 4 · 8 · 10점과는 1점씩 어긋납니다 — 일부러 단순하게 둔 '바닥선'입니다.
**한계**: 이 과정의 합성 뉴스는 문형이 반복돼 사전이 잘 맞습니다. 실제 뉴스는 같은 사건을 수십 가지로 쓰고, 부정어("did **not** miss")·동명이인·국가 뉴스의 간접 영향을 사전이 읽지 못합니다 → 그래서 LLM(P2-2) + 골든셋 검증을 씁니다.
'''),
    code("cF-1", r'''
# F-1. 사전 묶음으로 300건을 점수화한다(첫 번째로 맞는 묶음 · 헤드라인 → 본문 순)
LEXICON = [   # (점수, 정규식, 설명) — 위에서부터 검사한다. 점수는 5단계(1 · 3 · 5 · 9, 나머지 7)만 쓴다
    (1, r"bankrupt|insolven|chapter 11|creditors|liquidat|receivership|default|breach|covenant|going concern|negative equity|"
        r"freez|suspends? payments|not been paid|lays off half|파산|회생|법정관리|자본잠식|계속기업|지급 (일시 )?중단|quiebra|phá sản|insolvenz",
     "심각: 파산·회생·지급 불능·약정 위반"),
    (3, r"delayed payments|late payments|slower remittances|대금 지급|지급 .*지연|결제기간 연장|verspätete zahlungen|chậm thanh toán|"
        r"downgrade|등급 하향|loses|상실|layoffs?|workforce|restructuring|감원|감축|구조조정|\bloss\b|적자|record low|사상 최저|tariff|관세|\bshuts\b",
     "뚜렷한 부정: 대금 지연·등급 하향·고객 이탈·감원·손실"),
    (5, r"weak|warns|narrow|cuts .*forecast|audit|lawsuit|소송|delay|연기|감소|slow|interest rates|금리|congestion|shortage|swings|"
        r"renegotiat|raise cash|tighten|규제",
     "약한 부정: 둔화·원가·소송·연기·금리"),
    (9, r"\bwins?\b|award|order|contract|agreement|수주|계약|record|rise in|profit|upgrade|상향|investment-grade|capital increase|증자|"
        r"credit facility|loan|대출|tín dụng|hợp đồng|contrato|guarantee|repays|strongest|exclusive|shortens payment terms",
     "긍정: 수주·계약·대출·증자·등급 상향"),
]
DEFAULT_SCORE = 7
LEX = [(s_, re.compile(p, re.I), d_) for s_, p, d_ in LEXICON]

def lex_score(headline, body):
    """헤드라인 → 본문 순서로 첫 번째로 맞는 묶음의 (점수, 근거 구절). 아무것도 안 걸리면 (7, "")."""
    for text in (str(headline), str(body)):
        for s_, rx, _ in LEX:
            m_ = rx.search(text)
            if m_:
                return s_, m_.group(0)
    return DEFAULT_SCORE, ""

def label_of(x):
    """P2-2 v1 label: 0–2 severe · 3–4 high · 5 watch · 6–10 low."""
    return "severe" if x <= 2 else "high" if x <= 4 else "watch" if x == 5 else "low"

lex = news[["news_id", "buyer_id", "date"]].copy()
lex[["news_sent_0_10", "evidence"]] = [lex_score(h, bd) for h, bd in zip(news.headline, news.body_short)]
lex["label"] = lex.news_sent_0_10.map(label_of)
lex["news_risk"] = 10 - lex.news_sent_0_10
print("사전 묶음", len(LEXICON), "개 · 점수 분포:", lex.news_sent_0_10.value_counts().sort_index().to_dict())
print("label 분포:", lex.label.value_counts().to_dict(), "· 규칙에 하나도 안 걸린 기사(기본 7점):", int((lex.evidence == "").sum()))
lex.head(8)
'''),
    code("cF-2", r'''
# F-2. 골든셋(15:35 공개 d2_news_answer.csv, 20건)과 일치도 — MAE · ±2 이내 비율 · label 일치 · 큰 오차 3건
ANS = get_file("data/checkpoints/d2_news_answer.csv", required=False)

def agreement(pred, truth, name):
    """pred·truth: news_id → 점수. MAE · ±2 이내 비율 · 정확히 같음 · label 일치 · 순위상관."""
    j = pd.DataFrame({"pred": pred, "true": truth}).dropna()
    err = (j.pred - j.true).abs()
    return {"비교": name, "건수": len(j), "MAE": round(err.mean(), 2), "±2 이내": round((err <= 2).mean(), 2),
            "정확히 같음": round((err == 0).mean(), 2),
            "label 일치": round((j.pred.map(label_of) == j.true.map(label_of)).mean(), 2),
            "순위상관": round(j.pred.corr(j.true, method="spearman"), 2)}

if ANS is None:
    print("골든셋이 아직 없습니다 — 15:35 공개 뒤 이 셀부터 다시 실행하세요.")
    ans = None
else:
    ans = pd.read_csv(ANS, encoding="utf-8-sig")
    lx = lex.set_index("news_id").news_sent_0_10
    tr = ans.set_index("news_id").news_sent_0_10_true
    display(pd.DataFrame([agreement(lx, tr, "사전 기준선 vs 골든셋")]))
    big = (ans.assign(사전=ans.news_id.map(lx)).assign(오차=lambda d: (d.사전 - d.news_sent_0_10_true).abs())
              .merge(news[["news_id", "headline"]], on="news_id").sort_values("오차", ascending=False).head(3))
    print("오차가 큰 3건 — '누가 맞았나(사전 · 정답 · 애매)'를 news_review 시트에 적는다:")
    display(big[["news_id", "headline", "사전", "news_sent_0_10_true", "오차", "note_ko"]])
    print("label 혼동표(행 = 정답, 열 = 사전):")
    display(pd.crosstab(ans.label_true, ans.news_id.map(lx).map(label_of)))
'''),
    code("cF-3", r'''
# F-3. (🔵 Standard) 내 AI 점수 d2_news_scored.csv가 있으면 AI vs 골든셋 · AI vs 사전 기준선을 같은 표로 비교한다
MINE = find_upwards("d2_news_scored.csv")            # 내 PC·Colab 폴더에 올린 P2-3 출력 CSV
mine = None
if MINE is None:
    print("d2_news_scored.csv(P2-3 출력 CSV)를 이 노트북 폴더에 올리면 AI 점수와도 비교합니다 — 없으면 건너뜀")
else:
    mine = pd.read_csv(MINE, encoding="utf-8-sig")
    ai = mine.set_index("news_id").news_sent_0_10.astype(float)
    rows = [agreement(ai, lex.set_index("news_id").news_sent_0_10, "AI vs 사전 기준선")]
    if ans is not None:
        rows.insert(0, agreement(ai, ans.set_index("news_id").news_sent_0_10_true, "AI vs 골든셋"))
    print(f"내 AI 점수 {len(mine)}행")
    display(pd.DataFrame(rows))
'''),
    # ------------------------------------------------------------------------------------------ G
    md("sG", r'''
## G. 집계 · 병합 · 저장 (Step 8 — 결과 파일 저장)

엑셀 Step 8과 같은 정의입니다: 창 = (AsOf − 30일, AsOf] → `news_cnt_30d` = 건수 · `news_sent_0_10_30d` = 평균(0건이면 **5**) · `news_sent_min_30d` = 최솟값(0건이면 빈칸) · `news_risk_30d` = 10 − 평균 · `no_news_flag` = 0건이면 1.

점수는 **내 AI 점수**(`d2_news_scored.csv`가 있으면)를 쓰고, 없으면 F절 사전 기준선을 씁니다.
'''),
    code("cG-1", r'''
# G-1. 바이어별 30일 창 뉴스 집계 → 병합 → 정본 51열 순서로 저장(UTF-8 BOM)
src_name = "내 AI 점수(d2_news_scored.csv)" if mine is not None else "사전 기준선(F절)"
sc_ = (mine if mine is not None else lex)[["news_id", "buyer_id", "date", "news_sent_0_10"]].copy()
sc_["date"] = pd.to_datetime(sc_["date"])

def news_agg(scores_df, t, ids):
    """(t − 30일, t] 창의 바이어별 건수 · 평균(0건이면 5) · 최솟값 · 위험(10 − 평균) · 0건 플래그."""
    w = scores_df[(scores_df.date > t - pd.Timedelta(days=30)) & (scores_df.date <= t)]
    g = w.groupby("buyer_id").news_sent_0_10.agg(["count", "mean", "min"]).reindex(ids)
    out = pd.DataFrame({"buyer_id": ids})
    out["news_cnt_30d"] = g["count"].fillna(0).astype(int).to_numpy()
    out["news_sent_0_10_30d"] = g["mean"].fillna(5.0).round(2).to_numpy()
    out["news_sent_min_30d"] = g["min"].to_numpy()
    out["news_risk_30d"] = (10 - out.news_sent_0_10_30d).round(2)
    out["no_news_flag"] = (out.news_cnt_30d == 0).astype(int)
    return out, w

agg, win = news_agg(sc_, ASOF, list(e.buyer_id))
final = e.drop(columns=[c for c in agg.columns if c != "buyer_id" and c in e.columns]).merge(agg, on="buyer_id", how="left")
final = final[CANON]
INT_COLS = ["terms_days", "country_risk", "crc_unclassified", "n_invoices_cum", "max_dpd_180d", "over30_count_365d",
            "cum_dpd_days", "oldest_open_days", "ksure_30d_flag", "negative_equity_flag", "pay_score", "news_cnt_30d",
            "no_news_flag", "late_30d"] + [c for c in CANON if c.startswith("is_missing_")]
for c in INT_COLS:
    final[c] = final[c].astype("Int64")
final.to_csv("d2_end_features_challenge.csv", index=False, encoding="utf-8-sig")
print(f"점수 출처: {src_name} · 창 ({(ASOF - pd.Timedelta(days=30)).date()}, {ASOF.date()}] 기사 {len(win)}건 · 바이어 {win.buyer_id.nunique()}곳"
      f" · 기사 없는 바이어 {int(final.no_news_flag.sum())}곳(평균 5 + 플래그)")
print("저장: d2_end_features_challenge.csv", final.shape, "| 첫 열", final.columns[0], "| 끝 열", final.columns[-1],
      "| 빈칸이 남은 열:", {c: int(v) for c, v in final.isna().sum().items() if v})
'''),
    code("cG-2", r'''
# G-2. (Day3 08:30 이후) 강사 정본 d3_start_features.csv의 2026-08-31 행과 열별로 대조한다
D3 = get_file("data/checkpoints/d3_start_features.csv", required=False)
if D3 is None:
    print("d3_start_features.csv는 내일(Day3) 08:30에 공개됩니다 — 그때 이 셀을 다시 실행하세요.")
else:
    ref = pd.read_csv(D3, encoding="utf-8-sig")
    ref = ref[ref.ref_date == ASOF.strftime("%Y-%m-%d")].set_index("buyer_id")
    mine_f = final.set_index("buyer_id").reindex(ref.index)
    rows = []
    for c in CANON[1:]:
        a_, r_ = mine_f[c], ref[c]
        if pd.api.types.is_numeric_dtype(r_):
            same = np.isclose(pd.to_numeric(a_, errors="coerce").astype(float), r_.astype(float), atol=1e-3, equal_nan=True)
        else:
            same = a_.astype(str).to_numpy() == r_.astype(str).to_numpy()
        rows.append({"열": c, "같은 행 비율": round(float(np.mean(same)), 3)})
    cmp = pd.DataFrame(rows)
    print("100%가 아닌 열(뉴스 열은 점수 출처가 다르면 당연히 다르다):")
    display(cmp[cmp["같은 행 비율"] < 1])
'''),
    # ------------------------------------------------------------------------------------------ H
    md("sH", r'''
## H. 🟣 GDELT 톤 → 0–10 공식 · (선택) Colab AI로 점수화 (Step 5–6)

**GDELT 톤**은 대략 −20~+20에 몰려 있습니다. −10~+10에서 자른 뒤 0–10으로 바꿉니다: 엑셀 `=(MAX(-10,MIN(10,톤))+10)/2` (0 = 위험, 10 = 긍정). 이 과정 데이터에는 GDELT 행이 없어 **예시 값**으로만 계산합니다. 실제로 쓰려면 GDELT 이용 조건·DOC API 문서를 읽고 '수집 설계서' 5줄(호출 간격 · 보관 항목 · 인용 표기 · 기간 · 개인정보)을 먼저 씁니다.

**Colab AI**: `RUN_COLAB_AI = True`로 바꾸면 P2-2 v1 요약판으로 앞 20건을 점수화하고 `json.loads`로 검증합니다(함수 이름은 Colab 버전에 따라 다를 수 있다 — 오류가 나면 건너뛴다). Colab AI 기능은 사람 검토자가 볼 수 있으니 실데이터는 넣지 않습니다.
'''),
    code("cH-1", r'''
# H-1. GDELT 톤(−∞~+∞) → news_sent_0_10(0 = 위험 … 10 = 긍정): −10~+10에서 자른 뒤 선형 변환
tone = pd.Series([-15, -4, 0, 6], name="tone_raw")
pd.DataFrame({"tone_raw": tone, "news_sent_0_10": (tone.clip(-10, 10) + 10) / 2, "news_risk": 10 - (tone.clip(-10, 10) + 10) / 2})
'''),
    code("cH-2", r'''
# H-2. (선택) Colab AI로 앞 20건 점수화 → JSON 줄 검증 · 빠진 news_id 재요청 1회 → 사전 기준선과 비교
RUN_COLAB_AI = False
PROMPT = """너는 수출채권 리스크 분석가다. 각 뉴스를 해당 바이어의 '대금 지급 능력·의사' 관점에서 0~10 정수로 매겨라.
부정·위험 = 0~5, 긍정 = 6~10. 0 파산·회생 신청 / 1–2 약정 위반·계속기업 의문·지급 불능 / 3–4 대금 지연·등급 하향·주요 고객 이탈·대규모 감원
/ 5 약한 부정(실적 둔화 전망·원가 상승·소규모 소송·투자·가동 연기) / 6–8 중립·일상 / 9–10 대형 수주·증자·대출 확보·등급 상향.
헤드라인·본문만 근거로 쓴다. 입력 1행당 JSON 1줄: {"news_id":…,"news_sent_0_10":…,"evidence":"원문 구절"}. 다른 말은 쓰지 않는다.
[입력] news_id,headline,body_short
"""
if RUN_COLAB_AI:
    try:
        from google.colab import ai
        batch = news.head(20)
        text = PROMPT + "\n".join(f"{r.news_id},{r.headline},{r.body_short}" for r in batch.itertuples())
        got = {}
        for attempt in range(2):
            for line in ai.generate_text(text).splitlines():
                try:
                    j = json.loads(line.strip().strip("`"))
                    if 0 <= int(j["news_sent_0_10"]) <= 10:
                        got[j["news_id"]] = int(j["news_sent_0_10"])
                except Exception:
                    continue
            miss_ids = [i for i in batch.news_id if i not in got]
            if not miss_ids:
                break
            text = PROMPT + "\n".join(f"{r.news_id},{r.headline},{r.body_short}" for r in batch[batch.news_id.isin(miss_ids)].itertuples())
        print(f"점수 {len(got)}/20건 · 빠진 행 {[i for i in batch.news_id if i not in got]}")
        display(pd.DataFrame([agreement(pd.Series(got), lex.set_index("news_id").news_sent_0_10, "Colab AI vs 사전 기준선")]))
    except Exception as ex:
        print("Colab AI를 쓸 수 없습니다(Colab 밖이거나 함수 이름이 다름) — 건너뜀:", ex)
else:
    print("건너뜀 — RUN_COLAB_AI = True로 바꾸면 실행합니다(Colab에서만)")
'''),
    md("sI", r'''
## I. 셀프 체크

- [ ] A절 진단 표의 유형 수가 `dirty_list` 시트의 '내 진단'과 같다(6개 이상)
- [ ] B절: '확인필요' 0건 · 숫자로 못 바꾼 칸 0개 · AsOf 환율이 시트 `fx_at_ref`와 같다 · 단위 의심 행을 고친 이유를 적었다
- [ ] B-4: 날짜 형식 4종을 모두 읽었고(못 읽은 행 0) 통화별 환차손익의 부호를 설명할 수 있다
- [ ] C절: 중앙값 대체와 KNN 대체가 어떻게 다른지, 결측이 몰린 구간이 어디인지 1줄로 적었다
- [ ] D절: 스케일링한 열을 저장하지 않는 이유를 말할 수 있다
- [ ] F절: 사전 기준선의 MAE·±2 비율과 내 AI 점수의 값을 비교했다(15:35 이후)
- [ ] G절: `d2_end_features_challenge.csv` 150행 · 첫 열 buyer_id · 끝 열 late_30d · 정본 51열
'''),
]

CHECK_CELL = r'''
# (강사용 검산 셀 — 실행 검사 사본에만 붙는다) 핵심 값을 JSON으로 출력
import json as _json
_x = b.copy()
_x["late_ratio"] = (pd.to_numeric(raw.late_invoices_12m) / pd.to_numeric(raw.invoices_12m).where(pd.to_numeric(raw.invoices_12m) > 0)).round(4)
_x["dispute_ratio"] = (pd.to_numeric(raw.dispute_cnt_12m) / pd.to_numeric(raw.invoices_12m).where(pd.to_numeric(raw.invoices_12m) > 0)).round(4)
_x = _x.merge(aging.reset_index(), on="buyer_id", how="left").merge(final[["buyer_id", "country_risk", "crc_unclassified", "fx_chg_30d",
              "fx_chg_30d_lag30", "news_cnt_30d", "news_sent_0_10_30d", "no_news_flag", "news_risk_30d", "news_sent_min_30d"]], on="buyer_id")
_chk = {"ccy": b.ccy_clean.value_counts().to_dict(), "left": left, "fx_asof": fx_asof, "unit_fixed": list(b.buyer_id[fix_unit]), "k_fixed": list(b.buyer_id[fix_k]),
        "neg_equity": list(b.buyer_id[b.neg_equity == 1]), "fin_missing": int(b.fin_missing.sum()),
        "missing": b[RAT].isna().sum().to_dict(), "median": med.round(4).to_dict(), "diag": [list(d) for d in diag],
        "inv_bad_dates": int(inv.invoice_date.isna().sum()), "inv_ym_mismatch": int((~ym_ok).sum()),
        "excel": _x.astype(object).where(_x.notna(), None).to_dict(orient="records"),
        "final": final.astype(object).where(final.notna(), None).to_dict(orient="records"),
        "lex_dist": lex.news_sent_0_10.value_counts().sort_index().to_dict(), "lex_label": lex.label.value_counts().to_dict(),
        "agree_lex": agreement(lex.set_index("news_id").news_sent_0_10, ans.set_index("news_id").news_sent_0_10_true, "lex") if ans is not None else None,
        "src": src_name, "win": [len(win), int(win.buyer_id.nunique())]}
print("CHECK_JSON=" + _json.dumps(_chk, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
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


# 회사명 검사용 — 공개 저장소에 회사명이 글자로 남지 않게 코드포인트로 적는다(한글 3자 · 영문 7자)
ORG_NAMES = ("".join(map(chr, (0xC634, 0xB2C8, 0xCF58))), "".join(map(chr, (111, 109, 110, 105, 113, 111, 110))))

def _private_tokens(day: str) -> list[str]:
    """린트용 정답 토큰(숫자 · 바이어 ID)을 비공개 파일에서 읽는다 — 공개 저장소 코드에 정답이 남지 않게 한다(D30)."""
    import json as _json
    from pathlib import Path as _Path
    p = _Path(__file__).with_name("lint_tokens_private.json")
    if not p.is_file():
        return []
    return list(_json.loads(p.read_text(encoding="utf-8")).get(day, []))

# 노트북에 나오면 안 되는 것: 강사 경로·파일, 정답 숫자(Step 1–8 기대값)
FORBIDDEN = tuple(("instructor/", "answers/", "golden", "_expected", "_summary.json")
             + tuple(_private_tokens("day2")))  # 정답 숫자·바이어 ID는 tools/lint_tokens_private.json(비공개)에서 읽는다 — D30


def lint_notebook(nb) -> list[str]:
    """수강생 노트북 규칙: 코드 셀 첫 줄 = 한국어 주석, 출력·실행 번호 없음, 강사 자료·정답 숫자 언급 없음, 회사명 없음."""
    problems = []
    for c in nb.cells:
        if c.cell_type == "code":
            first = c.source.splitlines()[0]
            if not (first.startswith("# ") and re.search(r"[가-힣]", first)):
                problems.append(f"{c.id}: 첫 줄이 한국어 주석이 아님 → {first[:50]}")
            if c.get("outputs") or c.get("execution_count"):
                problems.append(f"{c.id}: 출력이 남아 있음")
        for bad in FORBIDDEN:
            if bad in c.source:
                problems.append(f"{c.id}: 강사 자료·정답 언급({bad})")
        if any(n in c.source.lower() for n in ORG_NAMES):
            problems.append(f"{c.id}: 회사명")
    return problems


def write_if_changed(nb, path: Path) -> bool:
    text = nbformat.writes(nb) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def execute(nb, timeout: int):
    """저장소 구조를 흉내 낸 임시 폴더에서 실행. 15:35 골든셋과 강사 채점본 앞 7열(d2_news_scored.csv)을 실행 폴더에 넣는다."""
    from nbclient import NotebookClient
    nb = copy.deepcopy(nb)
    nb.cells.append(new_code_cell(textwrap.dedent(CHECK_CELL).strip("\n"), id="instructor-check"))
    tmp = Path(tempfile.mkdtemp(prefix="d2nb_"))
    try:
        run_dir = tmp / "labs" / "day2"
        run_dir.mkdir(parents=True)
        for name in ("data", "tools"):
            try:
                os.symlink(REPO / name, tmp / name, target_is_directory=True)
            except OSError:
                shutil.copytree(REPO / name, tmp / name)
        if (ANSWERS / "d2_news_answer.csv").exists():
            shutil.copy2(ANSWERS / "d2_news_answer.csv", run_dir / "d2_news_answer.csv")
        gold = ANSWERS / "d2_news_scored_golden.csv"
        if gold.exists():
            import pandas as pd
            g = pd.read_csv(gold, encoding="utf-8-sig")
            g.iloc[:, :7].to_csv(run_dir / "d2_news_scored.csv", index=False, encoding="utf-8-sig")
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


def _close(a, b, tol=1.5e-4) -> bool:
    import math
    if a is None or b is None or (isinstance(b, float) and math.isnan(b)):
        return (a is None or (isinstance(a, float) and math.isnan(a))) and (b is None or (isinstance(b, float) and math.isnan(b)))
    try:
        return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return str(a) == str(b)


def cross_check(chk: dict) -> list[tuple[str, bool, str]]:
    """노트북 숫자 ↔ 강사 정답: 🟢 Excel 기대값(150행, D10 뉴스 점수) · 정본 특성표 2026-08-31 행(뉴스 열 제외 — D10 전 점수)."""
    import pandas as pd
    out = []
    ex_p, gd_p = ANSWERS / "d2_buyers_features_expected.csv", ANSWERS / "d2_end_features_golden.csv"
    if not ex_p.exists():
        return [("강사 정답(d2_buyers_features_expected.csv)", True, "없음 — 대조 생략(build_checkpoints.py 먼저)")]
    ex = pd.read_csv(ex_p, encoding="utf-8-sig").set_index("buyer_id")
    mine = pd.DataFrame(chk["excel"]).set_index("buyer_id")
    out.append(("통화 매핑 4종 · 확인필요 0", set(chk["ccy"]) == {"USD", "EUR", "JPY", "CNY"} and
                (mine.ccy_clean == ex.ccy_clean.reindex(mine.index)).all(), json.dumps(chk["ccy"])))
    out.append(("숫자로 못 바꾼 칸 0", not any(chk["left"].values()), json.dumps(chk["left"])))
    pairs = {"amt_num": "ar_balance_num", "krw_per_ccy": "krw_per_ccy", "ar_balance_usd": "ar_balance_usd",
             "pct_current": "pct_current", "pct_ar_31p": "pct_ar_31p", "pct_91plus": "pct_91plus", "max_dpd": "oldest_open_days",
             "avg_days_late": "avg_days_late_12m", "late_ratio": "late_ratio", "dpd_trend": "dpd_trend", "dispute_ratio": "dispute_ratio",
             "current_ratio": "current_ratio", "neg_equity": "neg_equity", "debt_to_equity": "debt_to_equity", "dso_buyer": "dso_buyer",
             "op_margin": "op_margin", "fin_missing": "fin_missing", "country_risk": "country_risk", "crc_unclassified": "crc_unclassified",
             "fx_chg_30d": "fx_chg_30d", "fx_chg_30d_lag30": "fx_chg_30d_lag30", "news_cnt_30d": "news_cnt_30d",
             "news_sent_0_10_30d": "news_sent_0_10_30d", "no_news_flag": "no_news_flag", "news_risk_30d": "news_risk_30d",
             "news_sent_min_30d": "news_sent_min_30d", "late_30d": "late_30d"}
    bad = {}
    for e_col, m_col in pairs.items():
        n = sum(not _close(mine.at[i, m_col], ex.at[i, e_col]) for i in ex.index)
        if n:
            bad[e_col] = n
    out.append(("🟢 Excel 기대값 27열 × 150행(뉴스 = D10 강사 채점본)", not bad, f"다른 칸 {bad}" if bad else "일치"))
    unit_exp = list(ex.index[ex.unit_flag_expected.fillna("") != ""])
    out.append(("단위 의심 → 고친 행 = 기대값", chk["unit_fixed"] == unit_exp, f"{chk['unit_fixed']} vs {unit_exp}"))
    neg = list(ex.index[ex.neg_equity == 1])
    out.append(("자본잠식 행 = 기대값", chk["neg_equity"] == neg, f"{chk['neg_equity']}"))
    out.append(("fin_missing 수 = 기대값", chk["fin_missing"] == int(ex.fin_missing.sum()), f"{chk['fin_missing']}"))
    out.append(("인보이스 날짜 형식 전부 읽음 · 연월 일치", chk["inv_bad_dates"] == 0 and chk["inv_ym_mismatch"] == 0,
                f"못 읽음 {chk['inv_bad_dates']} · 연월 불일치 {chk['inv_ym_mismatch']}"))
    if gd_p.exists():
        gd = pd.read_csv(gd_p, encoding="utf-8-sig")
        gd = gd[gd.ref_date == "2026-08-31"].set_index("buyer_id")
        fin = pd.DataFrame(chk["final"]).set_index("buyer_id")
        news_cols = {"news_cnt_30d", "news_sent_0_10_30d", "news_sent_min_30d", "news_risk_30d", "no_news_flag"}
        cols = [c for c in gd.columns if c not in news_cols]
        same_cols = list(fin.columns) == ["ref_date"] + [c for c in gd.columns if c != "ref_date"] or list(fin.reset_index().columns) == ["buyer_id"] + list(gd.columns)
        bad = {}
        for c in cols:
            n = sum(not _close(fin.at[i, c], gd.at[i, c]) for i in gd.index)
            if n:
                bad[c] = n
        out.append(("정본 51열 순서 = 정본 특성표", same_cols, f"{len(fin.columns) + 1}열"))
        out.append(("정본 특성표 2026-08-31 행(뉴스 열 제외 46열) 일치", not bad, f"다른 칸 {bad}" if bad else "일치"))
    if chk.get("agree_lex"):
        a = chk["agree_lex"]
        out.append(("사전 기준선 vs 골든셋 일치도(기록)", True, f"MAE {a['MAE']} · ±2 {a['±2 이내']} · label {a['label 일치']} · 순위상관 {a['순위상관']}"))
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
    out_p = ANSWERS / ("d2_challenge_executed.ipynb" if err is None else "d2_challenge_executed_FAILED.ipynb")
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
