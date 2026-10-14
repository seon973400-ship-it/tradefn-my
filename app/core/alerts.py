"""④ 조기경보 — 규칙 엔진(P1~P4). 경보는 '사람이 확인할 일'의 목록이며 자동 조치는 하지 않는다.

P1 파산 인지 · 사기 신호 → 대화상자(st.dialog, 닫으려면 '확인하고 기록')
P2 선적 보류선(결제기일 + 30일 초과 미결, 신용장·선수금 제외) · 사고발생통지 기한(결제기일 + 1개월, 7일 전부터)
P3 결제조건 변경 통지 · 한도 사용률 80%/100% · 수출통지 기한(보험 운영방식 선택)
P4 위험 신호(등급 하락 · 뉴스 위험 ≥ 7 · pd_30d ≥ 임계값 t)
15/1000 위약금은 경보 문구에 쓰지 않는다(약관 제21조③의 한정 조항).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NON_CREDIT = ("LC_SIGHT", "LC_USANCE", "TT_ADV")
PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
FRAUD_KO = {"account_change": "입금 계좌 변경 요청", "similar_domain": "유사 도메인 메일", "third_country": "제3국 송금",
            "surrender_bl": "대금 확인 전 surrender B/L 요구", "broker_rating_jump": "재무제표 제출 뒤 등급 급상승·외상 비중 확대 요구"}
COLUMNS = ["priority", "rule", "buyer_id", "buyer_name", "invoice_id", "days", "detail", "action", "basis"]


def _row(priority, rule, r, detail, action, basis, invoice_id="", days=None) -> dict:
    return {"priority": priority, "rule": rule, "buyer_id": r["buyer_id"], "buyer_name": r.get("buyer_name", ""),
            "invoice_id": invoice_id, "days": days, "detail": detail, "action": action, "basis": basis}


def business_days_after(start: pd.Timestamp, n: int) -> pd.Timestamp:
    """영업일 n일 뒤(주말만 뺀다 — 공휴일은 담당자가 확인)."""
    d = np.busday_offset(np.datetime64(pd.Timestamp(start).date()), n, roll="forward")
    return pd.Timestamp(d)


def run_rules(ledger: pd.DataFrame, asof="2026-09-30", buyers: pd.DataFrame | None = None, threshold: float = 0.1698,
              insurance_mode: str = "개별", news_cut: float = 7.0) -> pd.DataFrame:
    """ledger = 정제된 원장(clean_ledger 결과). buyers(선택) = 점수표(buyer_id, pd_30d, grade, grade_prev, news_risk_30d)."""
    asof = pd.Timestamp(asof)
    L = ledger.copy()
    if "dpd" not in L.columns:
        L["dpd"] = (asof - L["due_date"]).dt.days
    L["dpd"] = pd.to_numeric(L["dpd"], errors="coerce")
    out: list[dict] = []
    by = L.groupby("buyer_id", sort=True)
    first = by.first()

    for c in ("bankruptcy_flag", "fraud_flag", "term_change_flag"):
        if c not in first.columns:
            first[c] = 0
        if c not in L.columns:
            L[c] = 0
    # P1 파산·부도 인지
    for bid, r in first[pd.to_numeric(first["bankruptcy_flag"], errors="coerce").fillna(0) == 1].iterrows():
        rr = {"buyer_id": bid, "buyer_name": r.get("buyer_name", "")}
        out.append(_row("P1", "파산·부도 인지", rr, f"미결 {int(by.size()[bid])}건 · 최장 {int(by['dpd'].max()[bid])}일",
                        "신규 선적 즉시 중단 · 사고발생통지·보험금 청구 절차 검토(담당자 결정)", "약관 제7조①6 · 규정 제20조④ · 제28조"))
    # P1 사기 신호
    for bid, r in first[pd.to_numeric(first["fraud_flag"], errors="coerce").fillna(0) == 1].iterrows():
        kinds = [FRAUD_KO.get(k, k) for k in str(r.get("fraud_type", "")).split(";") if k]
        rr = {"buyer_id": bid, "buyer_name": r.get("buyer_name", "")}
        out.append(_row("P1", "사기 신호", rr, " · ".join(kinds) or "사기 신호",
                        "입금 계좌 변경 금지 · 기존 등록 연락처로 전화 확인 · 확인 전 선적 보류", "규정 제23조①6·② · 제24조"))
    # P2 선적 보류선(신용장·선수금 제외)
    credit = L[~L["payment_method"].isin(NON_CREDIT) & L["dpd"].notna()]
    hold = credit[credit["dpd"] > 30]
    for bid, g in hold.groupby("buyer_id"):
        r = g.iloc[0]
        ins = "부보 거래 포함 — " if (g["ksure_insured"] == "Y").any() else ""
        out.append(_row("P2", "선적 보류선(결제기일 + 30일 초과)", r,
                        f"{len(g)}건 · 최장 {int(g['dpd'].max())}일",
                        f"추가 선적 보류 · {ins}연속수출 면책 위험(1년 소급·미부보 거래도 포함)", "약관 제7조①2", days=int(g["dpd"].max())))
    # P2 사고발생통지 기한(부보 · 결제기일 + 1개월 − 7일부터)
    if "ksure_notice_deadline" in L.columns:
        ins = L[(L["ksure_insured"] == "Y") & L["ksure_notice_deadline"].notna() & ~L["payment_method"].isin(NON_CREDIT)]
        for _, r in ins.iterrows():
            left = int((pd.Timestamp(r["ksure_notice_deadline"]) - asof).days)
            if left > 7:
                continue
            if left >= 0:
                out.append(_row("P2", "사고발생통지 기한", r, f"기한 {pd.Timestamp(r['ksure_notice_deadline']).date()} · D-{left}",
                                "사고발생통지 여부 결재 요청(채권관리팀장 준비 · 대표이사 결재)", "약관 제21조② · 규정 제20조③",
                                invoice_id=r["invoice_id"], days=left))
            else:
                out.append(_row("P2", "사고발생통지 기한 경과", r, f"기한 {pd.Timestamp(r['ksure_notice_deadline']).date()} · {-left}일 지남",
                                "즉시 보고 — 통지했는지 확인(통지 태만으로 생긴 손실은 보상받지 못할 수 있음)", "약관 제21조② · 제7조②2",
                                invoice_id=r["invoice_id"], days=left))
    # P3 결제조건 변경
    if "term_change_flag" in L.columns:
        for bid, g in L[pd.to_numeric(L["term_change_flag"], errors="coerce").fillna(0) == 1].groupby("buyer_id"):
            out.append(_row("P3", "결제조건 변경", g.iloc[0], f"변경된 조건으로 선적된 미결 {len(g)}건",
                            "계약변경 통지(10영업일 이내 서면) 했는지 확인", "약관 제18조 · 규정 제20조②"))
    # P3 한도 사용률
    if "limit_usage_pct" in L.columns:
        u = first.copy()
        u["limit_usage_pct"] = pd.to_numeric(u["limit_usage_pct"], errors="coerce")
        u["limit_usd"] = pd.to_numeric(u.get("limit_usd"), errors="coerce")
        for bid, r in u.iterrows():
            rr = {"buyer_id": bid, "buyer_name": r.get("buyer_name", "")}
            if r["limit_usd"] == 0 and by.size()[bid] > 0 and str(r.get("payment_method", "")) not in NON_CREDIT:
                out.append(_row("P3", "한도 없음(0)", rr, "신용한도 0인데 미결 외상 있음", "신용공여 조건 출고 보류", "규정 제13조② · 제18조②"))
            elif pd.notna(r["limit_usage_pct"]) and r["limit_usage_pct"] >= 100:
                out.append(_row("P3", "한도 사용률 100% 이상", rr, f"사용률 {r['limit_usage_pct']:.0f}%", "출고 보류(미결이 줄 때까지)", "규정 제18조②"))
            elif pd.notna(r["limit_usage_pct"]) and r["limit_usage_pct"] >= 80:
                out.append(_row("P3", "한도 사용률 80% 이상", rr, f"사용률 {r['limit_usage_pct']:.0f}%", "출고 전 전결권자 사전 승인", "규정 제18조①"))
    # P3 수출통지 기한(부보 · 최근 선적) — insurance_mode가 개별·포괄일 때만
    insd = L[(L["ksure_insured"] == "Y") & L["invoice_date"].notna()] if insurance_mode in ("개별", "포괄") else L.iloc[0:0]
    for _, r in insd.iterrows():
        ship = pd.Timestamp(r["invoice_date"])
        if insurance_mode == "포괄":
            due = (ship + pd.offsets.MonthBegin(1)) + pd.Timedelta(days=19)
        else:
            due = business_days_after(ship, 10)
        left = int((due - asof).days)
        if 0 <= left <= 10:
            out.append(_row("P3", f"수출통지 기한({insurance_mode})", r, f"선적 {ship.date()} → 기한 {due.date()} · D-{left}",
                            "수출통지 했는지 확인", "약관 제16조 · 규정 제20조①", invoice_id=r["invoice_id"], days=left))
    # P4 위험 신호(점수표가 있을 때)
    if buyers is not None and len(buyers):
        bb = buyers.set_index("buyer_id")
        names = first["buyer_name"] if "buyer_name" in first.columns else pd.Series(dtype=str)
        for bid, r in bb.iterrows():
            if bid not in first.index:
                continue
            sig = []
            if str(r.get("grade_change", "")) == "down":
                sig.append(f"등급 하락 {r.get('grade_prev', '')}→{r.get('grade', '')}")
            nr = pd.to_numeric(r.get("news_risk_30d", np.nan), errors="coerce")
            if pd.notna(nr) and nr >= news_cut:
                sig.append(f"뉴스 위험 {nr:.1f}")
            pdv = pd.to_numeric(r.get("pd_30d", np.nan), errors="coerce")
            if pd.notna(pdv) and pdv >= threshold:
                sig.append(f"pd_30d {pdv:.3f} ≥ t {threshold:.3f}")
            if sig:
                out.append(_row("P4", "위험 신호", {"buyer_id": bid, "buyer_name": names.get(bid, "")}, " · ".join(sig),
                                "등급 재평가 · 한도 재검토", "규정 제9조② · 제23조①"))
    df = pd.DataFrame(out, columns=COLUMNS)
    if len(df):
        df["_o"] = df["priority"].map(PRIORITY_ORDER)
        df = df.sort_values(["_o", "rule", "buyer_id", "invoice_id"]).drop(columns="_o").reset_index(drop=True)
    return df


def summary(alerts: pd.DataFrame) -> dict:
    return {p: int((alerts["priority"] == p).sum()) for p in ("P1", "P2", "P3", "P4")}
