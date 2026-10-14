"""③ 한도·시나리오 — 규칙 기반 한도(가상 규정 제13조) + (선택) 선형계획(LP) 재배정 + 4단계 충격 기대손실.

규칙(가상 규정 제13조): 한도 = min(필요한도, 등급 상한, 인수한도 + 자기부담 허용액)
  필요한도 = 월평균 매출 × (결제기간 + 15) ÷ 30 · 자기부담 = 자기자본 × s(등급)
  상한 0: 신용장·선수금 거래, 선적 보류(결제기일 + 30일 초과 미결), 파산 인지, C등급
LP(4일차 한도 모델과 같은 식): max Σ coef·L  s.t. 총허용익스포저 · 미부보 EL 예산 · 국가 한도 · B등급 비중
기본 파라미터 = 4일차 파라미터(d4_params.csv)와 같은 값(공개 금리 + 회사 가정값). 모두 화면에서 바꿀 수 있다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

GR = ["S", "A", "B", "C"]
NO_LIMIT_METHODS = ("LC_SIGHT", "LC_USANCE", "TT_ADV")

DEFAULT_PARAMS = {
    "tsofr3m": 0.04047,                                          # Term SOFR 3M(2026-09-23)
    "spread": {"S": 0.010, "A": 0.015, "B": 0.020, "C": 0.025},  # [가정]
    "prem": {"S": 0.0030, "A": 0.0040, "B": 0.0050, "C": 0.0100},  # 90일 1건 보험료율 [가정]
    "pd": {"S": 0.005, "A": 0.015, "B": 0.040, "C": 0.100},      # 연 PD [가정]
    "lgd": 0.60,                                                  # 무보험 LGD [가정]
    "cov": 0.95,                                                  # 보상비율 [규정]
    "equity": 10_000_000,                                         # 자기자본 USD [교육용 가정]
    "alpha": 0.03,                                                # 미부보 EL 예산 = 자기자본 × α [가정]
    "s": {"S": 0.05, "A": 0.03, "B": 0.01, "C": 0.0},            # 자기부담 비율 [가정]
    "grace": 15,                                                  # 필요한도 유예일 [가정]
    "cap": {"S": None, "A": 200_000, "B": 100_000, "C": 0},      # 등급 상한(S = 필요한도) [가정, 규정 별표2]
    "util": 0.70, "gm": 0.25, "strat_min": 0.50, "share_cap_b": 0.30, "total_cap_ratio": 0.70,
    "ctry_cap": {"0-2": 0.20, "3": 0.12, "4-5": 0.06, "6-7": 0.03},   # 총허용익스포저 대비 [교육용 가정]
    "usd_krw": 1360.0,
}

DEFAULT_SCENARIOS = pd.DataFrame([
    {"scenario_id": "S0", "name_ko": "기준", "local_fx_chg": 0.0, "usd_krw_level": 1360.0, "rate_shock_bp": 0, "oil_chg": 0.0, "pd_multiplier": 1.0, "lgd": 0.60, "transfer_restriction": "N"},
    {"scenario_id": "S1", "name_ko": "경미", "local_fx_chg": -0.10, "usd_krw_level": 1292.0, "rate_shock_bp": 100, "oil_chg": 0.20, "pd_multiplier": 1.2, "lgd": 0.60, "transfer_restriction": "N"},
    {"scenario_id": "S2", "name_ko": "중간", "local_fx_chg": -0.25, "usd_krw_level": 1550.0, "rate_shock_bp": 250, "oil_chg": 0.50, "pd_multiplier": 1.5, "lgd": 0.60, "transfer_restriction": "N"},
    {"scenario_id": "S3", "name_ko": "심각", "local_fx_chg": -0.45, "usd_krw_level": 1570.0, "rate_shock_bp": 450, "oil_chg": 0.94, "pd_multiplier": 2.5, "lgd": 0.60, "transfer_restriction": "N"},
    {"scenario_id": "S4", "name_ko": "극단", "local_fx_chg": -0.70, "usd_krw_level": 1960.0, "rate_shock_bp": 450, "oil_chg": 1.00, "pd_multiplier": 4.0, "lgd": 0.80, "transfer_restriction": "Y"},
])


def load_scenarios(path=None) -> pd.DataFrame:
    """Day4 시나리오 파일(d4_scenarios.csv · scenarios.csv)이 있으면 그것을, 없으면 내장 기본값.
    LGD: lgd_scenario(절대값) → lgd → lgd_adj(0.3 초과면 절대값, 이하면 기본 LGD + 값). 참고 행(row_type = reference)은 뺀다."""
    if path is None or not Path(path).exists():
        return DEFAULT_SCENARIOS.copy()
    try:
        s = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return DEFAULT_SCENARIOS.copy()
    if "row_type" in s.columns:
        s = s[s["row_type"].astype(str) == "scenario"].reset_index(drop=True)
    if "lgd_scenario" in s.columns:
        s["lgd"] = pd.to_numeric(s["lgd_scenario"], errors="coerce")
    if "lgd" not in s.columns:
        adj = pd.to_numeric(s.get("lgd_adj", 0), errors="coerce").fillna(0)
        s["lgd"] = np.where(adj > 0.3, adj, DEFAULT_PARAMS["lgd"] + adj)
    if "usd_krw_level" not in s.columns and "krw_per_usd" in s.columns:
        s["usd_krw_level"] = s["krw_per_usd"]
    need = ["scenario_id", "name_ko", "usd_krw_level", "rate_shock_bp", "pd_multiplier", "lgd"]
    if any(c not in s.columns for c in need):
        return DEFAULT_SCENARIOS.copy()
    return s


PARAM_MAP = {  # d4_params.csv excel_name → DEFAULT_PARAMS 키(Day4 워크북 01_Params와 같은 값을 쓰기 위해)
    "TSOFR3M": ("tsofr3m", None), "LGD": ("lgd", None), "Cov": ("cov", None), "Equity_USD": ("equity", None),
    "Alpha": ("alpha", None), "Grace": ("grace", None), "Util": ("util", None), "GM": ("gm", None),
    "StratMin": ("strat_min", None), "ShareCap_B": ("share_cap_b", None), "TotalCapShare": ("total_cap_ratio", None),
    "USDKRW": ("usd_krw", None), "Cap_A": ("cap", "A"), "Cap_B": ("cap", "B"), "Cap_C_OA": ("cap", "C"),
    "CtryCap_02": ("ctry_cap", "0-2"), "CtryCap_3": ("ctry_cap", "3"), "CtryCap_45": ("ctry_cap", "4-5"), "CtryCap_67": ("ctry_cap", "6-7"),
    **{f"{p}_{g}": (k, g) for p, k in (("Spread", "spread"), ("Prem", "prem"), ("PD", "pd"), ("s", "s")) for g in GR},
}


def load_params(path=None) -> tuple[dict, str]:
    """Day4 d4_params.csv가 있으면 그 값으로 기본 파라미터를 덮는다. 반환: (파라미터, 출처 설명)."""
    import copy
    p = copy.deepcopy(DEFAULT_PARAMS)
    if path is None or not Path(path).exists():
        return p, "앱 내장 기본값"
    try:
        d = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return p, "앱 내장 기본값(d4_params.csv 읽기 실패)"
    n = 0
    for name, val in zip(d.get("excel_name", []), pd.to_numeric(d.get("value", []), errors="coerce")):
        if name in PARAM_MAP and pd.notna(val):
            k, sub = PARAM_MAP[name]
            if sub is None:
                p[k] = float(val)
            else:
                p[k][sub] = float(val)
            n += 1
    return p, f"Day4 d4_params.csv({n}개 값)"


def crc_bucket(country_risk, unclassified) -> str:
    if unclassified == 1 or pd.isna(country_risk):
        return "0-2"
    r = int(country_risk)
    return "0-2" if r <= 2 else ("3" if r == 3 else ("4-5" if r <= 5 else "6-7"))


def buyer_inputs(features: pd.DataFrame, scored: pd.DataFrame, ledger: pd.DataFrame | None = None,
                 d4_start: pd.DataFrame | None = None, history: pd.DataFrame | None = None, asof="2026-09-30") -> pd.DataFrame:
    """바이어 150곳의 한도 계산 입력. 인수한도·월평균 매출·현행 한도는 Day4 파일(d4_start_scored)이 있으면 그 값,
    없으면 매출 = 직전 12개월 인보이스 합 ÷ 12, 현행 한도 = 원장 limit_usd, 인수한도 = 0(모름)."""
    asof = pd.Timestamp(asof)
    f = features.set_index("buyer_id")
    b = pd.DataFrame(index=f.index)
    for c in ("country_code", "payment_method", "terms_days", "ksure_insured", "country_risk", "crc_unclassified",
              "open_ar_usd", "overdue_amount_usd", "ksure_30d_flag", "oldest_open_days"):
        b[c] = f[c] if c in f.columns else np.nan
    s = scored.set_index("buyer_id")
    b["grade"] = s["grade"].reindex(b.index)
    b["pd_30d"] = s["pd_30d"].reindex(b.index)
    b["buyer_name"] = ""
    b["current_limit_usd"] = np.nan
    b["bankruptcy_flag"] = 0
    b["fraud_flag"] = 0
    if ledger is not None and len(ledger):
        g = ledger.groupby("buyer_id")
        b["buyer_name"] = g["buyer_name"].first().reindex(b.index).fillna("")
        if "limit_usd" in ledger.columns:
            b["current_limit_usd"] = pd.to_numeric(g["limit_usd"].max(), errors="coerce").reindex(b.index)
        b["bankruptcy_flag"] = g["bankruptcy_flag"].max().reindex(b.index).fillna(0).astype(int)
        b["fraud_flag"] = g["fraud_flag"].max().reindex(b.index).fillna(0).astype(int)
    b["ksure_limit_usd"] = 0.0
    b["monthly_sales_usd"] = np.nan
    b["strategic_flag"] = 0
    src = "원장·인보이스 이력(인수한도 모름 = 0)"
    if d4_start is not None and len(d4_start):
        d4 = d4_start.set_index("buyer_id")
        for c in ("ksure_limit_usd", "monthly_sales_usd", "current_limit_usd", "strategic_flag", "bankruptcy_flag"):
            if c in d4.columns:
                b[c] = pd.to_numeric(d4[c], errors="coerce").reindex(b.index).fillna(b[c] if c in b else 0)
        if "buyer_name" in d4.columns:
            b["buyer_name"] = d4["buyer_name"].reindex(b.index).fillna(b["buyer_name"])
        src = "Day4 d4_start_scored.csv"
    if b["monthly_sales_usd"].isna().any() and history is not None:
        h = history[(history["invoice_date"] > asof - pd.Timedelta(days=365)) & (history["invoice_date"] <= asof)]
        ms = h.groupby("buyer_id")["amount_usd"].sum() / 12.0
        b["monthly_sales_usd"] = b["monthly_sales_usd"].fillna(ms.reindex(b.index)).fillna(0.0)
    b["monthly_sales_usd"] = b["monthly_sales_usd"].fillna(0.0)
    b["ship_hold"] = (pd.to_numeric(b["ksure_30d_flag"], errors="coerce").fillna(0) > 0).astype(int)
    if ledger is not None and len(ledger) and "dpd" in ledger.columns:
        L = ledger[~ledger["payment_method"].isin(NO_LIMIT_METHODS)]
        hold = L[pd.to_numeric(L["dpd"], errors="coerce") > 30].groupby("buyer_id").size()
        b.loc[b.index.isin(hold.index), "ship_hold"] = 1
    b["crc_bucket"] = [crc_bucket(r, u) for r, u in zip(b["country_risk"], b["crc_unclassified"])]
    b.attrs["source"] = src
    return b.reset_index()


def approval_level(amount: float) -> str:
    """가상 규정 제6조①: ≤ 5만 팀장 · ≤ 20만 본부장 · 초과 대표이사."""
    if amount <= 50_000:
        return "채권관리팀장"
    if amount <= 200_000:
        return "영업본부장"
    return "대표이사"


def terms_violation(grade, method, terms, insured) -> str:
    """가상 규정 제10조 등급별 허용 결제조건을 넘으면 Y."""
    try:
        t = float(terms)
    except (TypeError, ValueError):
        t = 0.0
    if method in ("TT_ADV", "LC_SIGHT", "LC_USANCE"):
        return "N"
    if grade == "C":
        return "Y"
    if method == "TT_SPLIT_30_70":
        return "N" if grade in ("S", "A", "B") else "Y"
    limit = {"S": 90, "A": 60, "B": 30}.get(grade, 0)
    if t > limit:
        return "Y"
    if grade == "B" and insured != "Y":
        return "Y"
    return "N"


def rule_limits(b: pd.DataFrame, p: dict | None = None) -> pd.DataFrame:
    p = {**DEFAULT_PARAMS, **(p or {})}
    out = b.copy()
    terms = pd.to_numeric(out["terms_days"], errors="coerce").fillna(0)
    out["need"] = (out["monthly_sales_usd"] * (terms + p["grace"]) / 30.0).round(0)
    out["cap"] = [np.inf if p["cap"].get(g) is None else float(p["cap"].get(g, 0)) for g in out["grade"]]
    out["ins"] = np.where(out["ksure_insured"] == "Y", out["ksure_limit_usd"].fillna(0), 0.0)
    out["self"] = [p["equity"] * p["s"].get(g, 0.0) for g in out["grade"]]
    ub = np.minimum(np.minimum(out["need"], out["cap"]), out["ins"] + out["self"])
    zero = (out["payment_method"].isin(NO_LIMIT_METHODS) | (out["ship_hold"] == 1) | (out["bankruptcy_flag"] == 1)
            | (out["grade"] == "C"))
    out["ub"] = np.where(zero, 0.0, np.round(ub, 2))
    out["ub_reason"] = np.select(
        [out["payment_method"].isin(NO_LIMIT_METHODS), out["bankruptcy_flag"] == 1, out["ship_hold"] == 1, out["grade"] == "C"],
        ["신용장·선수금(한도 대상 아님)", "파산 인지(선적 중단)", "선적 보류(결제기일+30일 초과 미결)", "C등급(신용공여 없음)"], "")
    out["proposed_limit"] = out["ub"]
    cur = pd.to_numeric(out["current_limit_usd"], errors="coerce")
    out["delta"] = (out["proposed_limit"] - cur).round(0)
    cut30 = (cur > 0) & (out["proposed_limit"] < cur * 0.7)
    out["approval_level"] = [("사람 승인(감액 30%↑) · " if c else "") + approval_level(v) for c, v in zip(cut30, out["proposed_limit"])]
    out["terms_violation"] = [terms_violation(g, m, t, i) for g, m, t, i in
                              zip(out["grade"], out["payment_method"], out["terms_days"], out["ksure_insured"])]
    return out


def lp_limits(b: pd.DataFrame, p: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """LP 재배정(scipy HiGHS). 반환: (표, 요약). 결정변수 = 바이어별 한도 L(150개)."""
    from scipy.optimize import linprog
    p = {**DEFAULT_PARAMS, **(p or {})}
    r = rule_limits(b, p)
    terms = pd.to_numeric(r["terms_days"], errors="coerce").fillna(0).to_numpy()
    ins = (r["ksure_insured"] == "Y").to_numpy()
    g = r["grade"].to_numpy()
    pdg = np.array([p["pd"].get(x, 0.1) for x in g])
    spread = np.array([p["spread"].get(x, 0.025) for x in g])
    prem = np.array([p["prem"].get(x, 0.01) for x in g])
    with np.errstate(divide="ignore", invalid="ignore"):
        turn = np.where(terms > 0, 365.0 / np.maximum(terms, 1), 0.0)
        r_i = p["tsofr3m"] + spread + np.where(ins, prem * turn + pdg * p["lgd"] * (1 - p["cov"]), pdg * p["lgd"])
        coef = p["util"] * (p["gm"] * turn - r_i)
    ub = r["ub"].to_numpy(dtype=float)
    coef = np.where((terms <= 0) | (ub <= 0), 0.0, coef)
    cur = pd.to_numeric(r["current_limit_usd"], errors="coerce").fillna(0).to_numpy()
    lb = np.where(r["strategic_flag"].to_numpy() == 1, np.minimum(p["strat_min"] * cur, ub), 0.0)
    total_cap = round(p["total_cap_ratio"] * ub.sum(), -5)
    cov_i = np.where(ins, p["cov"], 0.0)
    A, bnd, names = [], [], []
    A.append(np.ones_like(ub)); bnd.append(total_cap); names.append("총허용익스포저")
    A.append(p["util"] * pdg * p["lgd"] * (1 - cov_i)); bnd.append(p["equity"] * p["alpha"]); names.append("미부보 EL 예산")
    for c in sorted(r["country_code"].dropna().unique()):
        m = (r["country_code"] == c).to_numpy()
        cap = p["ctry_cap"][r.loc[m, "crc_bucket"].iloc[0]] * total_cap
        A.append(m.astype(float)); bnd.append(cap); names.append(f"국가 {c}")
    A.append((g == "B").astype(float)); bnd.append(p["share_cap_b"] * total_cap); names.append("B등급 비중")
    res = linprog(-coef, A_ub=np.vstack(A), b_ub=np.array(bnd), bounds=list(zip(lb, ub)), method="highs")
    r["lp_limit"] = np.round(np.clip(res.x, 0, None), 0) if res.success else np.nan
    r["coef"] = np.round(coef, 4)
    summary = {"status": res.message, "success": bool(res.success), "objective": float(-res.fun) if res.success else None,
               "total_cap": float(total_cap), "el_budget": float(p["equity"] * p["alpha"])}
    if res.success:
        marg = getattr(res, "ineqlin", None)
        if marg is not None:
            summary["shadow_prices"] = {n: round(float(-v), 4) for n, v in zip(names, marg.marginals) if abs(v) > 1e-9}
        summary["binding"] = [n for n, a, bb in zip(names, A, bnd) if abs(float(np.dot(a, res.x)) - bb) < 1e-6 * max(1, bb)]
    return r, summary


def scenario_el(b: pd.DataFrame, p: dict | None = None, scenarios: pd.DataFrame | None = None,
                exposure_col: str = "open_ar_usd") -> pd.DataFrame:
    """시나리오별 기대손실(EL)·원화 가치·금융비용(4일차 시나리오 표와 같은 식).
    EL_s = Σ AR × min(1, PD_g × 배수) × LGD_s × (1 − cov_i) · 원화 = Σ AR × 원/달러 · 금융비용 = Σ AR × (TSOFR3M + bp + spread_g) × terms/360"""
    p = {**DEFAULT_PARAMS, **(p or {})}
    sc = DEFAULT_SCENARIOS if scenarios is None else scenarios
    ar = pd.to_numeric(b[exposure_col], errors="coerce").fillna(0).to_numpy()
    g = b["grade"].to_numpy()
    pdg = np.array([p["pd"].get(x, 0.1) for x in g])
    spread = np.array([p["spread"].get(x, 0.025) for x in g])
    cov_i = np.where((b["ksure_insured"] == "Y").to_numpy(), p["cov"], 0.0)
    terms = pd.to_numeric(b["terms_days"], errors="coerce").fillna(0).to_numpy()
    rows = []
    for _, s in sc.iterrows():
        pd_s = np.minimum(1.0, pdg * float(s["pd_multiplier"]))
        el = float(np.sum(ar * pd_s * float(s["lgd"]) * (1 - cov_i)))
        rows.append({"scenario_id": s["scenario_id"], "name_ko": s["name_ko"], "pd_multiplier": float(s["pd_multiplier"]),
                     "lgd": float(s["lgd"]), "usd_krw_level": float(s["usd_krw_level"]),
                     "exposure_usd": round(float(ar.sum()), 0), "el_usd": round(el, 0),
                     "el_budget_usd": round(p["equity"] * p["alpha"], 0),
                     "krw_value_bn": round(float(ar.sum()) * float(s["usd_krw_level"]) / 1e9, 2),
                     "finance_cost_usd": round(float(np.sum(ar * (p["tsofr3m"] + float(s["rate_shock_bp"]) / 10000 + spread) * terms / 360)), 0)})
    out = pd.DataFrame(rows)
    out["over_budget"] = (out["el_usd"] > out["el_budget_usd"]).map({True: "초과", False: ""})
    return out


def portfolio_el(r: pd.DataFrame, p: dict | None = None, limit_col: str = "proposed_limit") -> dict:
    """한도 기준 미부보 EL = Σ Util × PD_g × LGD × (1 − cov_i) × L_i  vs  자기자본 × α(가상 규정 제16조)."""
    p = {**DEFAULT_PARAMS, **(p or {})}
    L = pd.to_numeric(r[limit_col], errors="coerce").fillna(0).to_numpy()
    pdg = np.array([p["pd"].get(x, 0.1) for x in r["grade"]])
    cov_i = np.where((r["ksure_insured"] == "Y").to_numpy(), p["cov"], 0.0)
    el = float(np.sum(p["util"] * pdg * p["lgd"] * (1 - cov_i) * L))
    budget = p["equity"] * p["alpha"]
    return {"el_usd": round(el, 0), "budget_usd": round(budget, 0), "ok": el <= budget, "usage_pct": round(el / budget * 100, 1)}
