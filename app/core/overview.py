"""⓪ 통합 상황판 — 계산(Streamlit 없이 테스트 가능): KPI 줄 · 경보 목록 · 바이어 표.

결정 질문 하나: "오늘 누구에게 선적·독촉·통지를 해야 하나?" — 위에서 아래로 요약 숫자 → 경보 → 표 → 근거(대시보드 4원칙).
경보는 ④(core/alerts.py)와 같은 규칙이다. 상황판의 P1·P2 건수 = ④를 기본 설정(보험 개별 · 뉴스 7.0)으로 열었을 때의 건수.
선적 보류선(결제기일 + 30일 초과) · 독촉 초안 대상(route = DRAFT)도 ④·⑤와 같은 코드를 쓴다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import alerts as AL
from . import dunning as DN

PRIORITY_LABEL = {"P1": "🔴 P1 즉시", "P2": "🟠 P2 오늘", "P3": "🟡 P3 이번 주", "P4": "🔵 P4 검토"}
PRIORITY_SHORT = {"P1": "🔴 P1", "P2": "🟠 P2", "P3": "🟡 P3", "P4": "🔵 P4"}     # 표 칸용(글자 + 색)
PRIORITY_RANK = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
RULE_NOTICE, RULE_NOTICE_LATE = "사고발생통지 기한", "사고발생통지 기한 경과"
RULE_HOLD = "선적 보류선(결제기일 + 30일 초과)"
RULE_SHORT = {"파산·부도 인지": "파산·부도", "사기 신호": "사기 신호", RULE_HOLD: "선적 보류선"}


def usd_short(v) -> str:
    """KPI 칸용 짧은 금액: $12.3M · $845K · $1,234."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "–"
    if abs(x) >= 1_000_000:
        return f"${x / 1_000_000:,.2f}M"
    if abs(x) >= 100_000:
        return f"${x / 1_000:,.0f}K"
    return f"${x:,.0f}"


def open_usd(L: pd.DataFrame) -> pd.Series:
    """행별 미결 잔액(USD) — open_amount_usd가 비어 있으면 amount_usd."""
    amt = pd.to_numeric(L["open_amount_usd"], errors="coerce") if "open_amount_usd" in L.columns else pd.Series(np.nan, index=L.index)
    if "amount_usd" in L.columns:
        amt = amt.fillna(pd.to_numeric(L["amount_usd"], errors="coerce"))
    return amt.fillna(0.0)


def _count(al: pd.DataFrame, priority: str, rule: str) -> int:
    return int(((al["priority"] == priority) & (al["rule"] == rule)).sum())


def kpis(L: pd.DataFrame, al: pd.DataFrame, asof) -> dict:
    """KPI 줄 — 미결 채권 · 연체 30일+(선적 보류선) · P1 · P2 · 통지 기한 D-n · 독촉 초안 대상.
    L = 정제 원장(clean_ledger 결과) · al = AL.run_rules 결과 · asof = 기준일."""
    amt = open_usd(L)
    dpd = pd.to_numeric(L["dpd"], errors="coerce")
    hold = ~L["payment_method"].isin(AL.NON_CREDIT) & (dpd > 30)        # ④ P2 '선적 보류선'과 같은 정의
    cnt = AL.summary(al)
    notice = al[al["rule"] == RULE_NOTICE].sort_values(["days", "buyer_id", "invoice_id"])
    route = DN.queue(L, asof)["route"]
    return {
        "asof": str(pd.Timestamp(asof).date()),
        "open_usd": float(amt.sum()), "open_count": int(len(L)), "buyers": int(L["buyer_id"].nunique()),
        "overdue_usd": float(amt[dpd > 0].sum()), "overdue_count": int((dpd > 0).sum()),
        "hold_usd": float(amt[hold].sum()), "hold_count": int(hold.sum()), "hold_buyers": int(L.loc[hold, "buyer_id"].nunique()),
        "p1": cnt["P1"], "p2": cnt["P2"], "p3": cnt["P3"], "p4": cnt["P4"],
        "p1_bankrupt": _count(al, "P1", "파산·부도 인지"), "p1_fraud": _count(al, "P1", "사기 신호"),
        "p2_hold": _count(al, "P2", RULE_HOLD), "p2_notice": _count(al, "P2", RULE_NOTICE), "p2_notice_late": _count(al, "P2", RULE_NOTICE_LATE),
        "notice_min_days": int(notice["days"].iloc[0]) if len(notice) else None,
        "notice_invoice": str(notice["invoice_id"].iloc[0]) if len(notice) else "",
        "notice_buyer": str(notice["buyer_id"].iloc[0]) if len(notice) else "",
        "draft": int((route == "DRAFT").sum()), "human": int((route == "HUMAN").sum()), "skip": int((route == "SKIP").sum()),
    }


def alert_table(al: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """P1·P2 경보 상위 limit건(우선순위 → 규칙 → 바이어 순). 색 대신 글자(🔴 P1 즉시 · 🟠 P2 오늘)로도 구분한다."""
    urgent = al[al["priority"].isin(["P1", "P2"])].head(limit).copy()
    urgent["우선순위"] = urgent["priority"].map(PRIORITY_LABEL)
    return urgent[["우선순위", "rule", "buyer_id", "invoice_id", "detail", "action"]].reset_index(drop=True)


def _signals(rows: pd.DataFrame) -> str:
    """바이어 한 곳의 P1·P2 신호를 짧은 글자로: '파산·부도 · 선적 보류선 · 통지 D-3'."""
    out = []
    for rule in rows["rule"].drop_duplicates():
        sub = rows[rows["rule"] == rule]
        if rule == RULE_NOTICE:
            out.append(f"통지 D-{int(sub['days'].min())}")
        elif rule == RULE_NOTICE_LATE:
            out.append(f"통지 경과 {len(sub)}건")
        else:
            out.append(RULE_SHORT.get(rule, rule))
    return " · ".join(out)


def buyer_table(L: pd.DataFrame, al: pd.DataFrame, scored: pd.DataFrame | None = None) -> pd.DataFrame:
    """원장에 있는 바이어 한 줄씩 — 경보 우선(P1 → P2 → P3 → P4 → 없음), 같으면 연체 금액이 큰 순.
    등급·pd_30d는 ② 점수표(scored)가 있으면 그 값, 없으면 원장 열(Day3 체크포인트)."""
    amt = open_usd(L)
    dpd = pd.to_numeric(L["dpd"], errors="coerce")
    d = pd.DataFrame({"buyer_id": L["buyer_id"].to_numpy(), "_open": amt.to_numpy(),
                      "_over": amt.where(dpd > 0, 0.0).to_numpy(), "_dpd": dpd.clip(lower=0).to_numpy()})
    g = d.groupby("buyer_id")
    first = L.groupby("buyer_id").first()
    t = pd.DataFrame({
        "buyer_name": first["buyer_name"] if "buyer_name" in first.columns else "",
        "country_code": first["country_code"] if "country_code" in first.columns else "",
        "grade": first["grade"] if "grade" in first.columns else "",
        "pd_30d": pd.to_numeric(first["pd_30d"], errors="coerce") if "pd_30d" in first.columns else np.nan,
        "open_usd": g["_open"].sum(), "overdue_usd": g["_over"].sum(), "max_dpd": g["_dpd"].max().astype("Int64"),
        "invoices": g.size(),
        "limit_usd": pd.to_numeric(first["limit_usd"], errors="coerce") if "limit_usd" in first.columns else np.nan,
        "limit_usage_pct": pd.to_numeric(first["limit_usage_pct"], errors="coerce") if "limit_usage_pct" in first.columns else np.nan,
    })
    if scored is not None and len(scored) and {"buyer_id", "grade", "pd_30d"} <= set(scored.columns):
        s = scored.drop_duplicates("buyer_id").set_index("buyer_id")
        t["grade"] = s["grade"].reindex(t.index).where(lambda x: x.notna(), t["grade"])
        t["pd_30d"] = pd.to_numeric(s["pd_30d"].reindex(t.index), errors="coerce").where(lambda x: x.notna(), t["pd_30d"])
    top = al.groupby("buyer_id")["priority"].min() if len(al) else pd.Series(dtype=str)
    t["top_priority"] = top.reindex(t.index).fillna("")
    urgent = al[al["priority"].isin(["P1", "P2"])]
    sig = {b: _signals(rows) for b, rows in urgent.groupby("buyer_id")}
    t["signals"] = [sig.get(b, "") for b in t.index]
    t["urgent_count"] = urgent.groupby("buyer_id").size().reindex(t.index).fillna(0).astype(int)
    t["alert"] = t["top_priority"].map(PRIORITY_SHORT).fillna("")
    t["buyer_label"] = [f"{b} · {n[:24] + '…' if len(n) > 25 else n}" for b, n in zip(t.index, t["buyer_name"].fillna("").astype(str))]
    t["limit_text"] = [f"{u:.0f}%" if pd.notna(u) else ("한도 0" if lim == 0 else "–")
                       for u, lim in zip(t["limit_usage_pct"], t["limit_usd"])]
    t["_rank"] = t["top_priority"].map(PRIORITY_RANK).fillna(9)
    t = t.sort_values(["_rank", "overdue_usd", "open_usd"], ascending=[True, False, False]).drop(columns="_rank")
    t.insert(0, "rank", range(1, len(t) + 1))
    return t.reset_index()
