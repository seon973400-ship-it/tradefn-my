"""기준일(as-of) 스냅샷 파생 컬럼과 라벨.

모든 피처 창은 기준일 t '이전'만 본다. 라벨 late_30d만 (t, t+30]을 본다.
build_checkpoints.py(체크포인트 생성)와 validate_data.py(누수·양성률 검사)가 함께 쓴다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tf_common import FX, RAW, load_fx, paydex_from_days, ts

LC = ("LC_SIGHT", "LC_USANCE")
DATE_COLS = {
    "buyers": ["since_date", "default_event_date"],
    "invoices": ["invoice_date", "due_date", "settled_date", "writeoff_date"],
    "payments": ["pay_date"],
    "financials": ["fy_end"],
    "news": ["date"],
    "events": ["event_date", "signal_start", "stop_pay_date", "deadline_date"],
}


def load_raw(raw_dir=RAW) -> dict[str, pd.DataFrame]:
    out = {}
    for name in ["buyers", "invoices", "payments", "financials", "news", "events", "country_risk", "bonds_public"]:
        df = pd.read_csv(raw_dir / f"{name}.csv", encoding="utf-8-sig", keep_default_na=True,
                         dtype={"scenario_role": str, "scenario_tag": str})
        for c in DATE_COLS.get(name, []):
            if c in df:
                df[c] = pd.to_datetime(df[c])
        out[name] = df
    return out


def normalize_tables(T: dict) -> dict:
    """생성기 메모리 결과(dict of DataFrame)도 같은 형식(날짜 = datetime64)으로 맞춘다."""
    out = {}
    for k, v in T.items():
        df = v.copy()
        for c in DATE_COLS.get(k, []):
            if c in df:
                df[c] = pd.to_datetime(df[c])
        out[k] = df
    return out


class Snapshot:
    def __init__(self, T: dict, cfg: dict, fx: FX | None = None):
        self.cfg = cfg
        self.b = T["buyers"].set_index("buyer_id", drop=False)
        inv = T["invoices"].copy()
        inv["receivable"] = np.where(inv.payment_method == "TT_ADV", 0.0, inv.amount_ccy * (1 - inv.advance_pct))
        inv["credit"] = inv.payment_method != "TT_ADV"
        inv["nonlc_credit"] = inv.credit & ~inv.payment_method.isin(LC)
        self.inv = inv
        pay = T["payments"]
        self.pay = pay[pay.payment_kind != "advance"][["allocated_invoice_id", "pay_date", "amount_ccy"]].copy()
        self.fin = T["financials"].copy()
        self.fx = fx or FX(load_fx(cfg))
        self.end = ts(cfg["meta"]["end_date"])
        self.seed = cfg["meta"]["seed"]

    # ---------------------------------------------------------------- 인보이스 상태(as-of t)
    def inv_state(self, t) -> pd.DataFrame:
        t = ts(t)
        inv = self.inv
        paid = self.pay[self.pay.pay_date <= t].groupby("allocated_invoice_id").amount_ccy.sum()
        s = inv[["invoice_id", "buyer_id", "invoice_date", "due_date", "payment_method", "currency", "amount_ccy",
                 "amount_usd", "dispute_flag", "credit", "nonlc_credit", "receivable", "settled_date",
                 "writeoff_date"]].copy()
        s["issued"] = s.invoice_date <= t
        removed = s.writeoff_date.notna() & (s.writeoff_date <= t)
        out = (s.receivable - s.invoice_id.map(paid).fillna(0)).clip(lower=0)
        out = np.where(s.issued & ~removed & (out > 0.005), out, 0.0)
        s["out_t"] = out
        s["settled_t"] = s.settled_date.where(s.settled_date <= t)
        s["due_le_t"] = s.due_date <= t
        dpd = np.where(s.settled_t.notna(), (s.settled_t - s.due_date).dt.days, (t - s.due_date).dt.days)
        s["dpd_t"] = np.where(s.due_le_t & s.issued, np.clip(dpd, 0, None), np.nan)
        s.loc[s.payment_method == "TT_ADV", "dpd_t"] = np.where(s.loc[s.payment_method == "TT_ADV", "issued"], 0.0, np.nan)
        s["open_dpd_t"] = np.where(s.out_t > 0, np.clip((t - s.due_date).dt.days, 0, None), np.nan)
        return s

    # ---------------------------------------------------------------- 바이어 스냅샷
    def snapshot(self, t, buyer_ids=None) -> pd.DataFrame:
        t = ts(t)
        b = self.b
        ids = list(b.buyer_id) if buyer_ids is None else list(buyer_ids)
        s = self.inv_state(t)
        cr = s[s.credit & s.issued]
        g_open = s[s.out_t > 0]
        res = pd.DataFrame(index=pd.Index(ids, name="buyer_id"))
        res["ar_balance"] = g_open.groupby("buyer_id").out_t.sum().reindex(ids).fillna(0).round(2)
        ccy = b.currency.reindex(ids)
        usd_per = self.fx.usd_per_unit([t] * len(ids), ccy.to_numpy())
        res["open_ar_usd"] = (res.ar_balance * usd_per).round(2)
        res["max_dpd_days"] = g_open.groupby("buyer_id").open_dpd_t.max().reindex(ids).fillna(0).astype(int)
        od = g_open[g_open.due_date < t]
        res["overdue_amount"] = od.groupby("buyer_id").out_t.sum().reindex(ids).fillna(0).round(2)
        res["overdue_ccy"] = ccy
        res["overdue_amount_usd"] = (res.overdue_amount * usd_per).round(2)
        res["oldest_open_days"] = res.max_dpd_days
        # 에이징 버킷(CRF: Current / 1-30 / 31-60 / 61-90 / 91+), 원통화
        d = g_open.open_dpd_t
        bk = pd.cut(d, [-1, 0, 30, 60, 90, 1e9], labels=["ar_current", "ar_1_30", "ar_31_60", "ar_61_90", "ar_91p"])
        aging = g_open.assign(bk=bk).pivot_table(index="buyer_id", columns="bk", values="out_t", aggfunc="sum",
                                                 observed=False).reindex(ids).fillna(0)
        for c in ["ar_current", "ar_1_30", "ar_31_60", "ar_61_90", "ar_91p"]:
            res[c] = aging[c].round(2) if c in aging else 0.0
        res["ksure_30d_flag"] = g_open[g_open.nonlc_credit & (g_open.due_date + pd.Timedelta(days=30) < t)] \
            .groupby("buyer_id").size().reindex(ids).fillna(0).gt(0).astype(int)
        # 거래 이력
        res["n_invoices_cum"] = s[s.issued].groupby("buyer_id").size().reindex(ids).fillna(0).astype(int)
        w180 = cr[cr.settled_t.notna() & (cr.settled_t > t - pd.Timedelta(days=180))]
        res["avg_days_to_pay"] = w180.assign(x=(w180.settled_t - w180.invoice_date).dt.days).groupby("buyer_id").x.mean().reindex(ids).round(1)
        res["avg_dpd_180d"] = w180.groupby("buyer_id").dpd_t.mean().reindex(ids).round(2)
        res["max_dpd_180d"] = w180.groupby("buyer_id").dpd_t.max().reindex(ids)
        res["late_share_180d"] = w180.assign(x=(w180.dpd_t > 0).astype(float)).groupby("buyer_id").x.mean().reindex(ids).round(3)
        due365 = cr[cr.due_le_t & (cr.due_date > t - pd.Timedelta(days=365))]
        res["over30_count_365d"] = due365[due365.dpd_t > 30].groupby("buyer_id").size().reindex(ids).fillna(0).astype(int)
        iss365 = cr[cr.invoice_date > t - pd.Timedelta(days=365)]
        res["dispute_share_365d"] = iss365.groupby("buyer_id").dispute_flag.mean().reindex(ids).round(3)
        res["cum_dpd_days"] = cr[cr.due_le_t].groupby("buyer_id").dpd_t.sum().reindex(ids).fillna(0).astype(int)
        # 12개월 원시 집계(d2 `buyers` 시트, 부록 B19)
        res["invoices_12m"] = iss365.groupby("buyer_id").size().reindex(ids).fillna(0).astype(int)
        late12 = iss365[iss365.dpd_t > 0]
        res["late_invoices_12m"] = late12.groupby("buyer_id").size().reindex(ids).fillna(0).astype(int)
        res["dispute_cnt_12m"] = iss365.groupby("buyer_id").dispute_flag.sum().reindex(ids).fillna(0).astype(int)
        avg_late = late12.groupby("buyer_id").dpd_t.mean().reindex(ids)
        res["avg_days_late_12m"] = np.where(res.invoices_12m > 0, avg_late.fillna(0), np.nan).round(1)
        l3 = cr[cr.due_le_t & (cr.due_date > t - pd.Timedelta(days=90))]
        p3 = cr[(cr.due_date <= t - pd.Timedelta(days=90)) & (cr.due_date > t - pd.Timedelta(days=180))]
        res["avg_dpd_last3m"] = l3.groupby("buyer_id").dpd_t.mean().reindex(ids).round(1)
        res["avg_dpd_prev3m"] = p3.groupby("buyer_id").dpd_t.mean().reindex(ids).round(1)
        res["pay_score"] = self.pay_score(s, t, ids)
        # 재무(결산일 + 90일이 지난 최신 FY만)
        fin = self.fin
        lag = pd.Timedelta(days=self.cfg["financials"]["publish_lag_days"])
        avail = fin[fin.fy_end + lag <= t].sort_values("fiscal_year").groupby("buyer_id").tail(1).set_index("buyer_id")
        for c in ["fiscal_year", "revenue_usd", "current_ratio", "debt_to_equity", "dso", "op_margin", "current_assets",
                  "current_liabilities", "total_liabilities", "equity", "accounts_receivable", "operating_income",
                  "negative_equity_flag", "going_concern_flag", "statement_status", "fin_summary_text"]:
            res[c if c != "fiscal_year" else "fin_fy"] = avail[c].reindex(ids)
        res["late_30d"] = self.late_30d(t, ids)
        return res

    def pay_score(self, s: pd.DataFrame, t, ids) -> pd.Series:
        """PAYDEX형 1~100: t 이전 12개월 완납(외상: O/A·D/A·D/P·분할) 건의 금액가중 평균 지연일 → D&B 키 보간 + N(0,3)."""
        sc = self.cfg["snapshot"]
        w = s[s.nonlc_credit & s.settled_t.notna() & (s.settled_t > t - pd.Timedelta(days=sc["pay_score_window_days"]))]
        w = w.assign(wd=w.dpd_t * w.amount_usd)
        g = w.groupby("buyer_id").agg(n=("dpd_t", "size"), wd=("wd", "sum"), amt=("amount_usd", "sum"))
        g = g.reindex(ids)
        days = (g.wd / g.amt).to_numpy()
        base = paydex_from_days(np.nan_to_num(days), sc["paydex_key"])
        rng = np.random.Generator(np.random.PCG64([self.seed, int(t.strftime("%Y%m%d"))]))
        noise = rng.normal(0, sc["pay_score_noise_sd"], size=len(ids))
        score = np.clip(np.round(base + noise), 1, 100)
        ok = (g.n.fillna(0) >= sc["pay_score_min_paid"]).to_numpy()
        return pd.Series(np.where(ok, score, np.nan), index=pd.Index(ids, name="buyer_id"))

    def late_30d(self, t, ids) -> pd.Series:
        """(t, t+30] 사이에 신용거래 인보이스(선수금 제외)가 미결 상태로 '만기+30일'선을 새로 넘으면 1."""
        t = ts(t)
        inv = self.inv
        line = inv.due_date + pd.Timedelta(days=30)
        cross = inv.credit & (line > t) & (line <= t + pd.Timedelta(days=30)) & \
            (inv.settled_date.isna() | (inv.settled_date > line))
        hit = inv[cross].groupby("buyer_id").size()
        return hit.reindex(ids).fillna(0).gt(0).astype(int)

    # ---------------------------------------------------------------- 누수 검사용: t 이후 정보를 지운 세계
    def censored(self, t) -> "Snapshot":
        """t 이후 정보(발행·입금·완납·대손)를 지운 복사본 → 같은 피처가 나오면 누수 없음."""
        t = ts(t)
        c = object.__new__(Snapshot)
        c.cfg, c.fx, c.end, c.seed = self.cfg, self.fx, self.end, self.seed
        c.b = self.b
        inv = self.inv[self.inv.invoice_date <= t].copy()
        inv.loc[inv.settled_date > t, "settled_date"] = pd.NaT
        inv.loc[inv.writeoff_date > t, "writeoff_date"] = pd.NaT
        c.inv = inv
        c.pay = self.pay[self.pay.pay_date <= t].copy()
        c.fin = self.fin
        return c


def active_mask(snap: pd.DataFrame, buyers: pd.DataFrame, t) -> pd.Series:
    """월 패널 분모: t에 거래 중인 바이어(최근 12개월 신용 인보이스 또는 미결 잔액 있음, 부도 인식 전)."""
    t = ts(t)
    b = buyers.set_index("buyer_id").reindex(snap.index)
    not_def = b.default_event_date.isna() | (b.default_event_date > t)
    return ((snap.invoices_12m > 0) | (snap.ar_balance > 0)) & not_def & (b.since_date <= t)
