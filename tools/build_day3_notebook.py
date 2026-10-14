#!/usr/bin/env python
"""Day3 Challenge 노트북 `labs/day3/d3_challenge.ipynb`를 nbformat으로 만든다(출력 없는 수강생용).

(v3 — 이번 과정은 쓰지 않는다) 3일차 Challenge 노트북 하나 — 등급 t/4 · t/2 · t.
섹션: 0 준비 · A 300행 빠른 실험(무작위 vs 바이어 단위 분할) · B 패널 시간 분할 + 불균형 처리 비교(class weight · SMOTE)
      · C 비용 기반 임계값(FN:FP = 5:1) · D SHAP · E 등급 S/A/B/C + 저장 · F 환율 예측 3경로(Prophet · ARIMA · ETS)
      · G AI와 함께 확장 · H 셀프 체크

사용(저장소 루트에서):
  python tools/build_day3_notebook.py                 # 노트북만 만든다(출력·실행 번호 없음) + 규칙 점검
  python tools/build_day3_notebook.py --org myorg     # Colab 배지·RAW_BASE의 조직 이름(기본: config day4.github_org 또는 brainini)
  python tools/build_day3_notebook.py --execute       # + 실행 검사: 저장소 구조를 흉내 낸 임시 폴더에서 위→아래로 실행해
                                                      #   강사용 실행본(../instructor/day3/answers/d3_challenge_executed.ipynb)을 저장하고
                                                      #   A절·변형 비교·임계값·등급·환율 숫자를 강사 정답(_summary.json · d3_variants.csv)과 대조
필요 패키지: nbformat(생성), nbclient·ipykernel·pandas·scikit-learn·lightgbm·imbalanced-learn·shap·prophet·statsmodels(실행 검사).
공개 저장소 파일 — 정답 숫자·강사 파일 이름을 노트북에 적지 않는다(실행 검사의 대조 셀은 사본에만 붙인다).
"""
from __future__ import annotations

import argparse
import copy
import csv
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
NB_PATH = REPO / "labs" / "day3" / "d3_challenge.ipynb"
ANSWERS = REPO.parent / "instructor" / "day3" / "answers"
DEFAULT_ORG = "brainini"


def md(cid: str, text: str):
    return ("markdown", cid, text)


def code(cid: str, text: str):
    return ("code", cid, text)


CELLS = [
    md("title", r'''
# Day3 Challenge 노트북 — LightGBM · 불균형 보정 · 비용 임계값 · SHAP · 등급 · 환율 예측 구간

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<org>/tradefin-ai-2026/blob/main/labs/day3/d3_challenge.ipynb)

Orange에서 클릭으로 만든 **30일 연체확률 모델**을 원형 알고리즘(LightGBM · SMOTE · SHAP · Prophet)으로 다시 만들고, 같은 질문에 코드로 답합니다.
Orange에는 LightGBM·SMOTE·Prophet 위젯이 없어서 xgboost·복제 오버샘플·ARIMA로 대신했습니다 — **개념은 같고 구현만 다릅니다**.

| 절 | 블록 · Step | 하는 일 | Orange·엑셀에서 같은 일 |
|---|---|---|---|
| 0 준비 | 시작 5분 | 버전 확인 · 글꼴 · 데이터 · 특성 목록 | — |
| A 300행 빠른 실험 | 블록 A Step 1 | 무작위 70/30 vs 바이어 단위 분할 · 시드 5개 | Data Sampler · Select Rows |
| B 패널 시간 분할 | Step 2–3 | LightGBM · class weight · SMOTE(학습 폴드만) · 로지스틱 기준선 | Data Sampler ② · Test and Score |
| C 비용 임계값 | Step 4 | FN:FP = 5:1 → `TunedThresholdClassifierCV` · 비용 곡선 | ROC Analysis · Calibration Plot |
| D SHAP | Step 7 | 전역 beeswarm · 개별 waterfall | Explain Model · Explain Prediction |
| E 등급 | Step 5–6 | 2026-09-30 150개사 확률 → t/4·t/2·t 등급 · 단조성 · 저장 | Predictions → 엑셀 IFS |
| F 환율 예측 구간 | Step 8 | Prophet · ARIMA(1,1,1) · ETS → 95% 구간 · 2026-06-05 급등 | 엑셀 예측 시트 · Orange ARIMA |
| G·H | 남는 시간 | AI와 함께 확장 · 셀프 체크 | — |

**Colab에서 여는 법**: 위 배지를 누르고 **파일 → Drive에 사본 저장**을 누릅니다(내 사본에서 작업해야 저장됩니다). 셀은 위에서 아래로 **Shift+Enter**로 실행합니다. 모두 실행하면 2–4분 걸립니다(Prophet이 가장 느립니다).

> **데이터 위생** — (가상) 한빛정밀(주) 교육용 합성 데이터와 FRED 공개 환율만 씁니다. 회사 실데이터는 이 노트북에도, Colab AI에도 넣지 않습니다.

> **재현성** — 모든 무작위 단계에 `random_state = 42`를 씁니다. **런타임 → 세션 다시 시작 후 모두 실행**을 해도 숫자가 같아야 합니다(8교시 3.8). Colab 런타임 버전이 다르면 소수 셋째 자리가 조금 다를 수 있습니다.
'''),
    md("s0", r'''
## 0. 준비 (5분)

1. **0-1 버전** — 쓰는 라이브러리 버전을 출력합니다. 없는 것이 있으면 이 셀이 설치합니다(설치했다면 **런타임 → 세션 다시 시작** 후 이 셀부터).
2. **0-2 한글 글꼴** — 그래프 한글이 □로 깨지지 않게 합니다.
3. **0-3 데이터** — ① 내 컴퓨터의 과정 저장소 폴더 → ② 과정 저장소 웹 주소(`RAW_BASE`, Day3 08:30 공개) → ③ 직접 업로드 순서로 찾습니다.
4. **0-4 특성 목록** — 모델에 넣을 열 42개를 정합니다(아래 표). 식별자·날짜·보조 열과 '기준일만 알려 주는' 환율 수준 열은 넣지 않습니다.
'''),
    code("c0-1", r'''
# 0-1. 파이썬·라이브러리 버전을 확인하고, 없는 패키지만 설치한다
import sys, subprocess, importlib, importlib.metadata as md_
NEED = {"lightgbm": "lightgbm", "imblearn": "imbalanced-learn", "shap": "shap", "prophet": "prophet", "statsmodels": "statsmodels"}
missing = [pip for mod, pip in NEED.items() if importlib.util.find_spec(mod) is None]
if missing:
    print("설치:", missing, "→ 끝나면 '런타임 → 세션 다시 시작' 후 이 셀부터 다시 실행")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing], check=True)
import numpy as np
import pandas as pd
import sklearn
print("Python", sys.version.split()[0])
for p in ["numpy", "pandas", "scikit-learn", "lightgbm", "imbalanced-learn", "shap", "prophet", "statsmodels"]:
    try:
        print(f"  {p:<17}", md_.version(p))
    except md_.PackageNotFoundError:
        print(f"  {p:<17} 없음")
assert tuple(int(x) for x in sklearn.__version__.split(".")[:2]) >= (1, 5), "TunedThresholdClassifierCV는 scikit-learn 1.5 이상"
pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 160)
'''),
    code("c0-2", r'''
# 0-2. 그래프 한글이 깨지지 않게 나눔고딕 글꼴을 등록한다(Colab은 한 번 내려받는다)
import urllib.request, warnings, logging
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="IProgress not found")

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

def get_file(rel):
    """rel 예: 'data/checkpoints/d3_start_features.csv' → 읽을 수 있는 파일 경로."""
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
            print("내려받기 실패(Day3 08:30 공개 전이면 정상):", e)
    try:
        from google.colab import files
    except ImportError:
        raise FileNotFoundError(f"{rel} 을(를) 찾지 못했습니다. 과정 저장소 폴더에서 실행하거나 RAW_BASE를 확인하세요.") from None
    print(f"'{target.name}' 파일을 골라 올려 주세요.")
    return Path(next(iter(files.upload())))

read = lambda rel: pd.read_csv(get_file(rel), encoding="utf-8-sig")
start = read("data/checkpoints/d3_start_features.csv")      # 300행 = 150개사 × 기준일 2개(2026-02-28 · 08-31)
scoring = read("data/checkpoints/d3_start_scoring.csv")     # 150행, 기준일 2026-09-30, 라벨 없음
panel = read("data/checkpoints/d3_features_panel.csv")      # 바이어 × 월 패널(2024-01~2026-08)
fx = pd.read_csv(get_file("labs/day3/fx_forecast_inputs.csv"), encoding="utf-8-sig", parse_dates=["date"])
print(f"start {start.shape} · 연체 {int(start.late_30d.sum())}건({start.late_30d.mean():.1%}) | scoring {scoring.shape} | panel {panel.shape} | fx {fx.shape}")
'''),
    code("c0-4", r'''
# 0-4. 모델 입력 = 특성 42개(숫자 33 · 이진 2 · 결제방식 원-핫 7). 빈칸은 그대로 둔다(LightGBM이 처리)
NUM = ["terms_days", "country_risk", "crc_unclassified", "n_invoices_cum", "avg_days_to_pay", "avg_dpd_180d", "max_dpd_180d",
       "late_share_180d", "over30_count_365d", "dispute_share_365d", "cum_dpd_days", "open_ar_usd", "overdue_amount_usd",
       "pct_current", "pct_ar_31p", "pct_91plus", "oldest_open_days", "ksure_30d_flag", "avg_days_late_12m", "dpd_trend",
       "current_ratio", "debt_to_equity", "dso", "op_margin", "negative_equity_flag", "is_missing_current_ratio",
       "is_missing_debt_to_equity", "is_missing_dso", "is_missing_op_margin", "pay_score", "news_cnt_30d",
       "news_sent_min_30d", "news_risk_30d"]
PM = ["TT_ADV", "TT_SPLIT_30_70", "OA", "DA", "DP", "LC_SIGHT", "LC_USANCE"]
FEATURES = NUM + ["ksure_insured_y", "segment_public"] + [f"pm_{v}" for v in PM]

def design(df):
    """특성표 → 모델 입력 행렬. 기준일만 알려 주는 열(환율 수준·변화율)과 식별자·보조 열은 넣지 않는다."""
    X = df[NUM].astype(float).copy()
    X["ksure_insured_y"] = (df.ksure_insured == "Y").astype(float)
    X["segment_public"] = (df.segment == "public").astype(float)
    for v in PM:
        X[f"pm_{v}"] = (df.payment_method == v).astype(float)
    return X[FEATURES]

from lightgbm import LGBMClassifier
def lgbm(params, seed=42, **extra):
    """같은 입력이면 같은 결과가 나오도록 고정한 LightGBM(스레드 1개 · deterministic)."""
    return LGBMClassifier(**params, random_state=seed, n_jobs=1, deterministic=True, force_row_wise=True, verbose=-1, **extra)

from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss, confusion_matrix,
                             roc_curve, precision_recall_curve)
def scores(y, p):
    """지표 묶음: 행 수 · 양성 수 · ROC-AUC · PR-AUC · Brier(확률 오차) · 평균 확률."""
    y, p = np.asarray(y), np.asarray(p)
    return {"n": int(len(y)), "pos": int(y.sum()), "base_rate": round(float(y.mean()), 4),
            "roc_auc": round(float(roc_auc_score(y, p)), 4) if 0 < y.sum() < len(y) else None,
            "pr_auc": round(float(average_precision_score(y, p)), 4) if y.sum() else None,
            "brier": round(float(brier_score_loss(y, p)), 5), "mean_p": round(float(p.mean()), 4)}

def cm_at(y, p, t):
    """임계값 t에서 혼동행렬 TP · FN · FP · TN과 재현율·정밀도."""
    tn, fp, fn, tp = confusion_matrix(y, (np.asarray(p) >= t).astype(int), labels=[0, 1]).ravel()
    return {"t": round(float(t), 4), "tp": int(tp), "fn": int(fn), "fp": int(fp), "tn": int(tn),
            "recall": round(tp / max(tp + fn, 1), 3), "precision": round(tp / max(tp + fp, 1), 3)}

print("특성", len(FEATURES), "개 — 예:", FEATURES[:5], "…")
'''),
    # ------------------------------------------------------------------------------------------ A
    md("sA", r'''
## A. 300행 빠른 실험 — 무작위 분할 vs 바이어 단위 분할 (블록 A Step 1, 10분)

Orange의 **Data Sampler 70% · 층화 · Replicable**과 같은 분할을 코드로 합니다. 이어서 같은 바이어의 두 기준일이 학습·시험에 나뉘지 않게 **바이어 단위**(`split_suggested`)로 나눠 봅니다.

- 연체는 300행 중 16건뿐 → 시험셋 연체는 4–5건. **AUC가 크게 흔들리는 것이 정상**입니다(숫자보다 절차).
- 파라미터: 나무 200 · 학습률 0.05 · 잎 15(03 Part2 §3.10 셀 4).
'''),
    code("cA-1", r'''
# A-1. 무작위 70/30(층화, random_state 42)과 바이어 단위 분할로 같은 모델을 학습·평가한다
from sklearn.model_selection import train_test_split
NB_PARAMS = {"n_estimators": 200, "learning_rate": 0.05, "num_leaves": 15}
X, y = design(start), start.late_30d.to_numpy()
Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
p_rand = lgbm(NB_PARAMS).fit(Xa, ya).predict_proba(Xb)[:, 1]
tr = (start.split_suggested == "train").to_numpy()
p_grp = lgbm(NB_PARAMS).fit(X[tr], y[tr]).predict_proba(X[~tr])[:, 1]
A_res = pd.DataFrame({"무작위 70/30": scores(yb, p_rand), "바이어 단위(split_suggested)": scores(y[~tr], p_grp)}).T
A_res
'''),
    code("cA-2", r'''
# A-2. (P3-3 재현성) 시드만 바꿔 무작위 분할을 5번 — AUC가 얼마나 흔들리나
rows = []
for seed in [0, 1, 7, 42, 2026]:
    a_, b_, ya_, yb_ = train_test_split(X, y, test_size=0.3, stratify=y, random_state=seed)
    p_ = lgbm(NB_PARAMS, seed=seed).fit(a_, ya_).predict_proba(b_)[:, 1]
    rows.append({"seed": seed, "시험 연체 수": int(yb_.sum()), **{k: scores(yb_, p_)[k] for k in ("roc_auc", "pr_auc")}})
seeds = pd.DataFrame(rows)
print(f"ROC-AUC 범위 {seeds.roc_auc.min():.3f} ~ {seeds.roc_auc.max():.3f} — 시험 연체가 4–5건이면 한 건이 AUC를 크게 움직인다")
seeds
'''),
    # ------------------------------------------------------------------------------------------ B
    md("sB", r'''
## B. 패널 시간 분할 + 불균형 처리 비교 (Step 2–3, 15분)

300행은 연체가 너무 적어 **시간 분할 학습**이 안 됩니다. 그래서 같은 특성의 **바이어 × 월 패널**로 학습 2024-03~2025-12 → 검증 2026-01~08(앞 두 달 `burn_in`은 뺌)로 나눕니다.

| 변형 | 불균형 처리 | 주의 |
|---|---|---|
| logistic | 없음(기준선) | 빈칸 → 중앙값, 표준화 — **파이프라인 안에서**(학습 폴드로만 fit) |
| logistic_balanced | class_weight = 'balanced' | 오분류 비용을 클래스 비율로 |
| lgbm | 없음 | 확률이 그대로 보정된 상태로 나오는지 B-3에서 확인 |
| lgbm_class_weight | class_weight = 'balanced' | Orange의 'Balance class distribution'과 같은 생각 |
| lgbm_smote | SMOTE(k = 3) | imblearn `Pipeline` 안 → **fit 때 학습 데이터에만** 합성 표본 |

> 오버샘플링·SMOTE를 **분할 전에** 하면 같은(또는 거의 같은) 연체 행이 검증에도 들어가 성능이 부풀려집니다 — Orange 퀴즈와 같은 이야기입니다.
'''),
    code("cB-1", r'''
# B-1. 패널을 시간으로 나눈다(burn_in 제외) — 학습 2024-03~2025-12 / 검증 2026-01~08
P_PARAMS = {"n_estimators": 300, "learning_rate": 0.03, "num_leaves": 7, "min_child_samples": 30,
            "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8, "reg_lambda": 5.0}   # [교육용 가정] 시간 분할 검증으로 고른 값
p = panel[panel.split_suggested != "burn_in"].sort_values(["ref_date", "buyer_id"]).reset_index(drop=True)
ptr, pte = p[p.split_suggested == "train"].reset_index(drop=True), p[p.split_suggested == "test"].reset_index(drop=True)
Xtr, ytr, Xte, yte = design(ptr), ptr.late_30d.to_numpy(), design(pte), pte.late_30d.to_numpy()
print(f"학습 {len(ptr):,}행(연체 {ytr.sum()}, {ytr.mean():.1%}) · 검증 {len(pte):,}행(연체 {yte.sum()}, {yte.mean():.1%})")
'''),
    code("cB-2", r'''
# B-2. 다섯 변형을 같은 학습셋으로 학습하고 검증 기간에서 비교한다(SMOTE는 파이프라인 안 = 학습 데이터에만)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from imblearn.pipeline import Pipeline as IPipeline
from imblearn.over_sampling import SMOTE

T_THEORY = 1 / (1 + 5)            # 비용 FN:FP = 5:1이고 확률이 보정돼 있으면 최적 임계값 = 1/6
models = {
    "logistic": Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
                          ("clf", LogisticRegression(max_iter=5000))]),
    "logistic_balanced": Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
                                   ("clf", LogisticRegression(max_iter=5000, class_weight="balanced"))]),
    "lgbm": lgbm(P_PARAMS),
    "lgbm_class_weight": lgbm(P_PARAMS, class_weight="balanced"),
    "lgbm_smote": IPipeline([("imp", SimpleImputer(strategy="median")), ("smote", SMOTE(random_state=42, k_neighbors=3)),
                             ("clf", lgbm(P_PARAMS))]),
}
od = pte.overdue_amount_usd.to_numpy() > 0        # 기준일에 연체 잔액이 있는 행
rows, preds = [], {}
for name, m in models.items():
    m.fit(Xtr, ytr)
    pr = m.predict_proba(Xte)[:, 1]
    preds[name] = pr
    s = scores(yte, pr)
    c6 = cm_at(yte, pr, T_THEORY)
    rows.append({"variant": name, **s, "cond_auc_overdue": scores(yte[od], pr[od])["roc_auc"],
                 "fn_at_1_6": c6["fn"], "fp_at_1_6": c6["fp"], "cost_at_1_6": 5 * c6["fn"] + c6["fp"]})
var = pd.DataFrame(rows).set_index("variant")
print("cond_auc_overdue = 지금 연체 잔액이 있는 바이어끼리의 AUC('진짜 실력'에 가깝다) · cost = 5×FN + FP")
var[["roc_auc", "pr_auc", "brier", "mean_p", "cond_auc_overdue", "fn_at_1_6", "fp_at_1_6", "cost_at_1_6"]]
'''),
    code("cB-3", r'''
# B-3. ROC·PR 곡선과 신뢰도(보정) 표 — 불균형 처리는 AUC보다 '확률 크기'를 바꾼다
fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for name, col in [("lgbm", BLUE), ("lgbm_class_weight", ORANGE), ("lgbm_smote", GREEN), ("logistic", GRAY)]:
    f_, t_, _ = roc_curve(yte, preds[name]); ax[0].plot(f_, t_, color=col, label=f"{name} ({var.loc[name, 'roc_auc']:.3f})")
    pr_, rc_, _ = precision_recall_curve(yte, preds[name]); ax[1].plot(rc_, pr_, color=col, label=f"{name} ({var.loc[name, 'pr_auc']:.3f})")
ax[0].plot([0, 1], [0, 1], ":", color=GRAY); ax[0].set(title="ROC (검증 2026-01~08)", xlabel="FPR(괜히 막은 비율)", ylabel="TPR(잡아낸 연체 비율)")
ax[1].axhline(yte.mean(), ls=":", color=GRAY); ax[1].set(title="Precision–Recall", xlabel="Recall", ylabel="Precision")
bins = [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 1.0]
rel = (pd.DataFrame({"p": preds["lgbm"], "y": yte, "bin": pd.cut(preds["lgbm"], bins, include_lowest=True)})
         .groupby("bin", observed=True).agg(행=("y", "size"), 평균_예측=("p", "mean"), 실제_연체율=("y", "mean")))
for name, col in [("lgbm", BLUE), ("lgbm_smote", GREEN), ("lgbm_class_weight", ORANGE)]:
    r_ = pd.DataFrame({"p": preds[name], "y": yte, "bin": pd.cut(preds[name], bins, include_lowest=True)}).groupby("bin", observed=True)[["p", "y"]].mean()
    ax[2].plot(r_.p, r_.y, "o-", color=col, label=name)
ax[2].plot([0, 1], [0, 1], ":", color=GRAY); ax[2].set(title="신뢰도(보정) — 대각선에 가까울수록 좋다", xlabel="평균 예측 확률", ylabel="실제 연체율")
for a in ax: a.legend(fontsize=8)
plt.tight_layout(); plt.show()
print("LightGBM 신뢰도 표(구간별 평균 예측 vs 실제 연체율):")
rel.round(3)
'''),
    # ------------------------------------------------------------------------------------------ C
    md("sC", r'''
## C. 비용 기반 임계값 — FN:FP = 5:1 (Step 4, 15분)

연체를 놓치는 비용(FN)이 괜히 거래를 막는 비용(FP)의 5배라고 두면 [교육용 가정], 보정된 확률의 최적 임계값은 **t\* = 1 ÷ (1 + 5) ≈ 0.17**입니다(0.5가 아닙니다).

데이터로 확인합니다. 학습 기간 안에서 **월별 확장창**(2025-01~12의 각 달을 그 이전 달로 학습해 예측)으로 `TunedThresholdClassifierCV`를 돌려 비용 `5 × FN + FP`가 가장 작은 t를 찾습니다. 검증 기간(2026년)은 여기서 쓰지 않습니다 — 임계값도 '학습'이기 때문입니다.
'''),
    code("cC-1", r'''
# C-1. 월별 확장창 12개로 비용 최소 임계값을 찾는다(TunedThresholdClassifierCV, 후보 200개)
from sklearn.metrics import make_scorer
from sklearn.model_selection import TunedThresholdClassifierCV

def neg_cost(y, pred):
    """비용의 음수(클수록 좋게): −(5 × FN + 1 × FP)."""
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return -(5 * fn + 1 * fp)

def month_splits(dates, first_valid="2025-01-01"):
    """검증 월 m(2025-01 이후)마다: 학습 = m 이전 모든 월, 검증 = m."""
    d = pd.to_datetime(dates).to_numpy()
    return [(np.flatnonzero(d < m), np.flatnonzero(d == m)) for m in sorted(pd.unique(d)) if m >= np.datetime64(first_valid)]

splits = month_splits(ptr.ref_date)
tuner = TunedThresholdClassifierCV(lgbm(P_PARAMS), scoring=make_scorer(neg_cost), cv=splits, thresholds=200,
                                   refit=True, store_cv_results=True).fit(Xtr, ytr)
t = round(float(tuner.best_threshold_), 4)
print(f"확장창 {len(splits)}개 → 비용 최소 임계값 t = {t:.4f} (이론값 1/6 = {T_THEORY:.4f})")
'''),
    code("cC-2", r'''
# C-2. 같은 확장창의 예측을 모아 비용 곡선을 그린다 — t를 0.17 근처 어디로 골라도 비용 차이가 작은가?
oof = np.full(len(ytr), np.nan)
for a_, b_ in splits:
    oof[b_] = lgbm(P_PARAMS).fit(Xtr.iloc[a_], ytr[a_]).predict_proba(Xtr.iloc[b_])[:, 1]
mask = ~np.isnan(oof)
grid = np.round(np.arange(0.02, 0.81, 0.01), 2)
curve = pd.DataFrame([cm_at(ytr[mask], oof[mask], g) for g in grid])
curve["cost"] = 5 * curve.fn + curve.fp
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.plot(curve.t, curve.cost, color=BLUE)
ax.axvline(t, color=ORANGE, ls="--", label=f"t = {t:.3f}"); ax.axvline(0.5, color=GRAY, ls=":", label="0.5(기본값)")
ax.set(title="비용 곡선(학습 기간 확장창 예측) — 5×FN + FP", xlabel="임계값", ylabel="비용"); ax.legend(); plt.show()
curve[curve.t.isin([0.05, 0.10, 0.17, 0.25, 0.35, 0.50])][["t", "tp", "fn", "fp", "cost"]]
'''),
    code("cC-3", r'''
# C-3. 검증 기간(2026-01~08)에 t를 적용한 혼동행렬 — 0.5와 비교
cmp = pd.DataFrame([cm_at(yte, preds["lgbm"], x) for x in (t, T_THEORY, 0.5)], index=["t(학습 기간에서 찾음)", "1/6(이론)", "0.5(기본값)"])
cmp["cost"] = 5 * cmp.fn + cmp.fp
cmp
'''),
    # ------------------------------------------------------------------------------------------ D
    md("sD", r'''
## D. SHAP — 등급의 이유 (Step 7, 15분)

최종 모델은 **패널 전체(2024-03~2026-08)**로 다시 학습한 같은 설정의 LightGBM입니다. SHAP 값은 '이 특성이 이 바이어의 로그오즈를 얼마나 올렸나(+) 내렸나(−)'입니다.

- **전역**(beeswarm): 검증 기간 행 전체에서 기여가 큰 특성 순서 — Orange **Explain Model**과 비교합니다.
- **개별**(waterfall): 2026-09-30 위험이 가장 높은 바이어와 임계값에 가장 가까운 바이어 — Orange **Explain Prediction**과 비교합니다.
- SHAP은 **모델이 어떻게 판단했는지**이지 원인이 아닙니다. 재무제표가 조작되면 모델도 속습니다(P3-1 해석서 '한계').
'''),
    code("cD-1", r'''
# D-1. 최종 모델(패널 전체)을 학습하고 검증 기간 행으로 전역 SHAP 중요도를 본다
import shap
final = lgbm(P_PARAMS).fit(design(p), p.late_30d.to_numpy())
expl = shap.TreeExplainer(final)
sv_val = expl(design(pte))
imp = pd.Series(np.abs(sv_val.values).mean(axis=0), index=FEATURES).sort_values(ascending=False)
plt.figure(); shap.plots.beeswarm(sv_val, max_display=12, show=False)
plt.title("SHAP 전역 — 30일 연체확률(검증 기간)", fontsize=11); plt.tight_layout(); plt.show()
imp.head(10).round(3).to_frame("평균 |SHAP|")
'''),
    code("cD-2", r'''
# D-2. 2026-09-30 점수화 — 위험이 가장 높은 바이어와 t에 가장 가까운 바이어의 waterfall
Xs = design(scoring)
pd30 = final.predict_proba(Xs)[:, 1]
sv_s = expl(Xs)
hi = int(np.argmax(pd30))
near = int(pd.Series(np.abs(pd30 - t)).drop(index=hi).idxmin())
for i in (hi, near):
    plt.figure(); shap.plots.waterfall(sv_s[i], max_display=10, show=False)
    plt.title(f"{scoring.buyer_id[i]} — pd_30d {pd30[i]:.3f} (t = {t:.3f})", fontsize=11); plt.tight_layout(); plt.show()
top = pd.DataFrame({"특성": FEATURES, "값": Xs.iloc[hi].to_numpy(), "기여(+ 위험↑)": sv_s.values[hi]})
top.reindex(top["기여(+ 위험↑)"].abs().sort_values(ascending=False).index).head(5).round(3)   # P3-1 입력 표
'''),
    # ------------------------------------------------------------------------------------------ E
    md("sE", r'''
## E. 등급 S/A/B/C — t/4 · t/2 · t (Step 5–6, 10분)

엑셀 `=IFS([@pd_30d]>=t,"C",[@pd_30d]>=t/2,"B",[@pd_30d]>=t/4,"A",TRUE,"S")`와 같은 규칙입니다(**C부터 검사**). 🔵 대안은 분위수 컷(위험 순위 백분위 0.85↑ C · 0.50↑ B · 0.15↑ A).

**단조성**: 라벨이 있는 검증 기간에서 S < A < B < C 순으로 실제 연체율이 올라가야 등급이 '말이 됩니다'.
'''),
    code("cE-1", r'''
# E-1. 2026-09-30 150개사 등급(t 규칙 vs 분위수 규칙)과 검증 기간 단조성
def grade_of(p_, t_):
    """C부터 검사: pd ≥ t → C, ≥ t/2 → B, ≥ t/4 → A, 나머지 S."""
    p_ = np.asarray(p_)
    return np.select([p_ >= t_, p_ >= t_ / 2, p_ >= t_ / 4], ["C", "B", "A"], "S")

rank = pd.Series(pd30).rank(pct=True, method="average").to_numpy()
g_t, g_q = grade_of(pd30, t), np.select([rank >= 0.85, rank >= 0.50, rank >= 0.15], ["C", "B", "A"], "S")
GR = list("SABC")
dist = pd.DataFrame({"t 규칙": pd.Series(g_t).value_counts(), "분위수 규칙(🔵)": pd.Series(g_q).value_counts()}).reindex(GR).fillna(0).astype(int)
mono = (pd.DataFrame({"g": grade_of(preds["lgbm"], t), "y": yte}).groupby("g").y.agg(행="size", 연체="sum", 실제_연체율="mean").reindex(GR))
print(f"컷: S < {t/4:.4f} ≤ A < {t/2:.4f} ≤ B < {t:.4f} ≤ C")
display(dist)
print("검증 기간(2026-01~08) 등급별 실제 연체율 — S < A < B < C이면 단조성 통과:")
mono.round(4)
'''),
    code("cE-2", r'''
# E-2. 제출 형식(6열)으로 저장 — buyer_id · ref_date · pd_30d · grade · threshold_used · model_version
out = pd.DataFrame({"buyer_id": scoring.buyer_id, "ref_date": scoring.ref_date, "pd_30d": np.round(pd30, 5),
                    "grade": g_t, "threshold_used": t, "model_version": "colab_lgbm_challenge"})
out.to_csv("d3_end_scored_challenge.csv", index=False, encoding="utf-8-sig")
print("저장: d3_end_scored_challenge.csv", out.shape, "— Orange·엑셀 결과(d3_end_scored__T조-번호.csv)와 등급이 다른 바이어를 찾아본다")
out.sort_values("pd_30d", ascending=False).head(8)
'''),
    # ------------------------------------------------------------------------------------------ F
    md("sF", r'''
## F. 환율 위험 구간 — 같은 원/달러로 세 경로 (Step 8, 20분)

`fx_forecast_inputs.csv` = FRED DEXKOUS 일별(관측일만). 학습 ~2026-05-29 → 검증 2026-06-01~09-25. 검증 구간에는 **2026-06-05 급등**과 9월 급락이 있습니다.

| 경로 | 이 노트북 | 교실 |
|---|---|---|
| Prophet(일별) | F-1 | 🟣 원형 |
| ARIMA(1,1,1)(일별, 관측일 순) | F-2 | 🔵 Orange ARIMA와 같은 차수 |
| ETS(가법 오차·추세, 주평균) | F-2 | 🟢 엑셀 예측 시트(FORECAST.ETS)에 가까운 모형 — 알고리즘이 달라 몇 원 다를 수 있다 |

비교 질문은 하나입니다: **95% 예측 구간이 실제 값을 얼마나 담았나(coverage), 6/5 급등을 담았나?**
'''),
    code("cF-1", r'''
# F-1. Prophet(95% 구간)으로 학습 → 검증 기간 예측 · 구간 포함 비율 · MAPE
logging.getLogger("prophet.plot").disabled = True          # 'plotly 없음' 안내 끄기(그림은 matplotlib으로 그린다)
from prophet import Prophet
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
ftr, fva = fx[fx.split == "train"], fx[fx.split == "valid"]
np.random.seed(42)
m = Prophet(interval_width=0.95, daily_seasonality=False)
try:                                   # 최적화 seed 고정(cmdstanpy) — 안 되는 버전이면 기본값
    m.fit(ftr.rename(columns={"date": "ds", "usd_krw": "y"})[["ds", "y"]], seed=42)
except TypeError:
    m.fit(ftr.rename(columns={"date": "ds", "usd_krw": "y"})[["ds", "y"]])
np.random.seed(42)
fc = m.predict(pd.DataFrame({"ds": fva.date}))

def summarize(name, d, a, yh, lo, hi):
    """경로별 요약: 검증 점 수 · 95% 구간 포함 비율 · MAPE · 마지막 예측."""
    a, yh, lo, hi = map(np.asarray, (a, yh, lo, hi))
    return {"경로": name, "점": len(a), "coverage_95": round(float(((a >= lo) & (a <= hi)).mean()), 3),
            "MAPE_%": round(float(np.mean(np.abs(a - yh) / a) * 100), 2),
            "마지막 예측": round(float(yh[-1]), 1), "구간": f"{lo[-1]:,.1f} ~ {hi[-1]:,.1f}"}

peak = fva.loc[fva.usd_krw.idxmax()]
pk = fc.loc[fva.reset_index(drop=True).usd_krw.idxmax()]
print(f"검증 최고 {peak.date:%Y-%m-%d} {peak.usd_krw:,.2f}원 → Prophet 95% 구간 {pk.yhat_lower:,.1f} ~ {pk.yhat_upper:,.1f}"
      f" → {'안' if pk.yhat_lower <= peak.usd_krw <= pk.yhat_upper else '밖'}")
res_fx = [summarize("Prophet(일별)", fva.date, fva.usd_krw, fc.yhat, fc.yhat_lower, fc.yhat_upper)]
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.plot(fx.date[fx.date >= "2025-10-01"], fx.usd_krw[fx.date >= "2025-10-01"], color=GRAY, lw=1, label="실제")
ax.plot(fva.date, fc.yhat, color=BLUE, label="Prophet 예측"); ax.fill_between(fva.date, fc.yhat_lower, fc.yhat_upper, color=BLUE, alpha=0.15, label="95% 구간")
ax.axvline(pd.Timestamp("2026-06-01"), color=GRAY, ls=":"); ax.scatter([peak.date], [peak.usd_krw], color=ORANGE, zorder=5, label="2026-06-05 급등")
ax.set(title="원/달러 — Prophet 95% 예측 구간(학습 ~2026-05-29)", ylabel="원"); ax.legend(fontsize=8); plt.show()
'''),
    code("cF-2", r'''
# F-2. 같은 데이터로 ARIMA(1,1,1)(일별)와 ETS(주평균)도 돌려 세 경로를 한 표로 비교한다
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
ar = ARIMA(ftr.usd_krw.to_numpy(), order=(1, 1, 1)).fit()
f_ar = ar.get_forecast(steps=len(fva)); ci = np.asarray(f_ar.conf_int(alpha=0.05))
res_fx.append(summarize("ARIMA(1,1,1)(일별)", fva.date, fva.usd_krw, f_ar.predicted_mean, ci[:, 0], ci[:, 1]))
wk = (fx.assign(week=fx.date - pd.to_timedelta(fx.date.dt.weekday, unit="D"))
        .groupby("week").agg(usd_krw=("usd_krw", "mean")).reset_index())
wtr, wva = wk[wk.week <= pd.Timestamp("2026-05-29")], wk[wk.week > pd.Timestamp("2026-05-29")]
ets = ETSModel(pd.Series(wtr.usd_krw.to_numpy()), error="add", trend="add", seasonal=None).fit(disp=False)
pr_ = ets.get_prediction(start=len(wtr), end=len(wtr) + len(wva) - 1).summary_frame(alpha=0.05)
res_fx.append(summarize("ETS(주평균)", wva.week, wva.usd_krw, pr_["mean"], pr_["pi_lower"], pr_["pi_upper"]))
fx_table = pd.DataFrame(res_fx).set_index("경로")
print("세 경로 모두 '학습 끝 수준'에서 크게 벗어나지 않는 예측을 낸다 — 사건(급등·급락)은 시계열 모델이 미리 알 수 없다")
fx_table
'''),
    # ------------------------------------------------------------------------------------------ G·H
    md("sG", r'''
## G. AI와 함께 확장 (남는 시간)

Colab의 **Gemini** 버튼(또는 Claude)에 아래처럼 요청하고, **나온 코드를 그대로 믿지 말고** 위 표의 숫자와 대조합니다.

1. "B-2의 lgbm_smote에서 SMOTE를 '분할 전'에 적용하는 잘못된 버전을 만들어 검증 AUC가 어떻게 달라지는지 비교해 줘. 왜 그런지도 3줄로."
2. "C-1의 비용비를 3:1과 10:1로 바꿔 t를 다시 찾고, 등급 분포가 어떻게 바뀌는지 표로 보여 줘."
3. "D-2의 waterfall 상위 5개를 여신위원회용 문장 3줄로 바꿔 줘. 표에 없는 숫자는 쓰지 마."

> Colab AI 기능은 프롬프트·코드·출력을 사람 검토자가 볼 수 있고 일정 기간 보관합니다. 회사 실데이터는 넣지 않습니다.
'''),
    md("sH", r'''
## H. 셀프 체크

- [ ] A절: 무작위 분할과 바이어 단위 분할의 AUC가 왜 다른지 1줄로 설명할 수 있다
- [ ] B절: SMOTE·class weight가 AUC보다 **평균 확률**을 크게 바꾼다는 것을 표에서 찾았다
- [ ] C절: t가 0.5가 아니라 0.17 근처인 이유(비용비 5:1)를 말할 수 있고, 비용 곡선이 그 근처에서 평평한지 봤다
- [ ] D절: 전역 상위 3개 특성을 Orange Explain Model 결과와 비교했다
- [ ] E절: 등급 단조성(S < A < B < C)을 확인했고 `d3_end_scored_challenge.csv`를 저장했다
- [ ] F절: 6/5 급등이 세 경로의 95% 구간 안인지 밖인지 적었다
- [ ] 런타임 다시 시작 후 모두 실행 → A-1·C-1 숫자가 같다(재현성)
'''),
]

CHECK_CELL = r'''
# (강사용 검산 셀 — 실행 검사 사본에만 붙는다) 핵심 값을 JSON으로 출력
import json as _json
_chk = {"A": {"random_split": scores(yb, p_rand), "group_split": scores(y[~tr], p_grp)},
        "variants": var.reset_index().to_dict(orient="records"), "t": t, "folds": len(splits),
        "cm_at_t": cm_at(yte, preds["lgbm"], t), "valid": scores(yte, preds["lgbm"]),
        "grades": dist["t 규칙"].to_dict(), "grades_quantile": dist["분위수 규칙(🔵)"].to_dict(),
        "mono": mono["실제_연체율"].round(4).to_dict(), "shap_top5": list(imp.head(5).index),
        "hi": str(scoring.buyer_id[hi]), "near": str(scoring.buyer_id[near]),
        "fx": {r["경로"]: {"n": r["점"], "coverage_95": r["coverage_95"], "mape_pct": r["MAPE_%"], "last_yhat": r["마지막 예측"]} for r in res_fx},
        "seeds_auc": seeds.roc_auc.tolist()}
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

# 노트북에 나오면 안 되는 것: 강사 경로·파일, 정답 숫자(Day3 정답본 t·검증 AUC·등급 분포·환율 coverage)
FORBIDDEN = tuple(("instructor/", "answers/", "_summary.json", "orange_expected")
             + tuple(_private_tokens("day3")))  # 정답 숫자·바이어 ID는 tools/lint_tokens_private.json(비공개)에서 읽는다 — D30


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
    from nbclient import NotebookClient
    nb = copy.deepcopy(nb)
    nb.cells.append(new_code_cell(textwrap.dedent(CHECK_CELL).strip("\n"), id="instructor-check"))
    tmp = Path(tempfile.mkdtemp(prefix="d3nb_"))
    try:
        run_dir = tmp / "labs" / "day3"
        run_dir.mkdir(parents=True)
        for name in ("data", "tools"):
            try:
                os.symlink(REPO / name, tmp / name, target_is_directory=True)
            except OSError:
                shutil.copytree(REPO / name, tmp / name)
        shutil.copy2(REPO / "labs" / "day3" / "fx_forecast_inputs.csv", run_dir / "fx_forecast_inputs.csv")
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
    """노트북 숫자 ↔ 강사 정답(train_day3_model.py 산출). 같은 seed·버전이면 소수 넷째 자리까지 같다."""
    p = ANSWERS / "_summary.json"
    if not p.exists():
        return [("강사 정답(_summary.json)", True, "없음 — 대조 생략(train_day3_model.py 먼저)")]
    s = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for k in ("random_split", "group_split"):
        a, b = chk["A"][k], s["colab"][k]
        ok = all(a[x] == b[x] for x in ("n", "pos")) and all(abs(a[x] - b[x]) < 5e-4 for x in ("roc_auc", "pr_auc", "mean_p"))
        out.append((f"A절 {k} = 정답 §7", ok, f"AUC {a['roc_auc']} vs {b['roc_auc']} · PR {a['pr_auc']} vs {b['pr_auc']}"))
    vp = ANSWERS / "d3_variants.csv"
    if vp.exists():
        with open(vp, encoding="utf-8-sig") as f:
            ref = {r["variant"]: r for r in csv.DictReader(f)}
        bad = [r["variant"] for r in chk["variants"]
               if abs(r["roc_auc"] - float(ref[r["variant"]]["roc_auc"])) > 5e-4
               or abs(r["pr_auc"] - float(ref[r["variant"]]["pr_auc"])) > 5e-4
               or r["cost_at_1_6"] != int(ref[r["variant"]]["cost_at_1_6"])]
        out.append(("B절 변형 5개 AUC·PR-AUC·비용 = d3_variants.csv", not bad, f"불일치 {bad}"))
    out.append(("C절 t = 정답 t", abs(chk["t"] - s["t"]) < 5e-4, f"{chk['t']} vs {s['t']} (확장창 {chk['folds']}개)"))
    cm, cs = chk["cm_at_t"], s["cm_at_t"]
    out.append(("C절 검증 혼동행렬(t) = 정답", all(cm[k] == cs[k] for k in ("tp", "fn", "fp", "tn")),
                f"TP {cm['tp']} FN {cm['fn']} FP {cm['fp']} TN {cm['tn']}"))
    out.append(("B절 lgbm 검증 AUC = 정답", abs(chk["valid"]["roc_auc"] - s["valid"]["roc_auc"]) < 5e-4,
                f"{chk['valid']['roc_auc']} vs {s['valid']['roc_auc']}"))
    out.append(("E절 등급 분포(t 규칙) = 정답", chk["grades"] == s["grades"], f"{chk['grades']} vs {s['grades']}"))
    out.append(("E절 등급 분포(분위수) = 정답", chk["grades_quantile"] == s["grades_quantile"], f"{chk['grades_quantile']}"))
    mono = [chk["mono"].get(g) for g in "SABC"]
    out.append(("E절 단조성 S < B < C(A는 행 적음)", mono[0] < mono[2] < mono[3], f"{chk['mono']}"))
    hi = next((d["buyer_id"] for d in s.get("locals", []) if d["tag"] == "high"), None)
    near = next((d["buyer_id"] for d in s.get("locals", []) if d["tag"] == "near_t"), None)
    out.append(("D절 최고 위험·t 근처 바이어 = 정답 §5", (chk["hi"], chk["near"]) == (hi, near), f"{chk['hi']} · {chk['near']}"))
    fx_ref = s.get("fx") or {}
    names = {"Prophet(일별)": "prophet", "ARIMA(1,1,1)(일별)": "arima_111", "ETS(주평균)": "ets_aan_weekly"}
    bad = []
    for k, v in chk["fx"].items():
        r = fx_ref.get(names[k])
        if r and (v["n"] != r["n"] or abs(v["coverage_95"] - r["coverage_95"]) > 0.0015 or abs(v["mape_pct"] - r["mape_pct"]) > 0.015
                  or abs(v["last_yhat"] - r["last_yhat"]) > 0.15):
            bad.append(f"{k}: {v} vs {r}")
    out.append(("F절 환율 3경로(coverage·MAPE·마지막 예측) = 정답 §6", not bad, "; ".join(bad) or "일치"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", default=None, help="GitHub 조직 이름(기본: config day4.github_org 또는 brainini)")
    ap.add_argument("--execute", action="store_true", help="실행 검사 + 강사용 실행본 저장")
    ap.add_argument("--timeout", type=int, default=900)
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
    out_p = ANSWERS / ("d3_challenge_executed.ipynb" if err is None else "d3_challenge_executed_FAILED.ipynb")
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
