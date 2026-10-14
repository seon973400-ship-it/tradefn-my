"""③ 한도·시나리오 — 규칙 기반 한도(가상 규정 제13조) · (선택) LP 재배정 · 4단계 충격 기대손실(EL).

입력: ② 점수표 · 바이어 특성(d3_start_scoring) · (있으면) Day4 d4_start_scored.csv(인수한도·월평균 매출·현행 한도)
      · d4_params.csv(파라미터) · d4_scenarios.csv(시나리오) — 없으면 앱 내장 기본값
출력: st.session_state['limits'] — 한도 변경은 사람이 승인한다(가상 규정 제6조 전결권, 제15조③ 감액 30% 이상)
"""
import copy

import pandas as pd
import streamlit as st

import ui
from core import data_io as IO
from core import limits as LM

st.title("③ 한도·시나리오")
st.caption("한도 = min(필요한도, 등급 상한, 인수한도 + 자기부담 허용액). 신용장·선수금·선적 보류·파산·C등급은 0.")
L = ui.need_ledger()
if L is None:
    st.stop()
sc = st.session_state.get("scored")
if sc is None:
    st.warning("먼저 **② 예측·등급**을 열어 점수표를 만드세요.")
    st.page_link("views/p2_score.py", label="② 예측·등급으로 가기", icon="📊")
    st.stop()
feats = ui.load_features(str(IO.FEATURES_SCORING))
if feats is None:
    st.error("바이어 특성 파일(d3_start_scoring.csv)이 없습니다.")
    st.stop()
d4 = ui.load_features(str(IO.D4_START))
base, psrc = LM.load_params(IO.PARAMS)
p = copy.deepcopy(base)
with st.sidebar.expander("③ 파라미터(바꿔 보기)", expanded=False):
    st.caption(f"기본값: {psrc}")
    p["tsofr3m"] = st.slider("Term SOFR 3M", 0.0, 0.10, float(base["tsofr3m"]), 0.0005, format="%.4f")
    for g in LM.GR:
        p["pd"][g] = st.slider(f"PD {g}(연)", 0.0, 0.30, float(base["pd"][g]), 0.001, format="%.3f")
    p["lgd"] = st.slider("LGD(무보험)", 0.0, 1.0, float(base["lgd"]), 0.05)
    p["cov"] = st.slider("보상비율 Cov", 0.0, 1.0, float(base["cov"]), 0.05)
    p["equity"] = st.number_input("자기자본(USD)", 1_000_000, 100_000_000, int(base["equity"]), 1_000_000)
    p["alpha"] = st.slider("α(미부보 EL 예산 비율)", 0.0, 0.10, float(base["alpha"]), 0.005, format="%.3f")

b = LM.buyer_inputs(feats, sc, L, d4, ui.load_history(), ui.asof())
r = LM.rule_limits(b, p)
use_lp = st.toggle("선형계획(LP)으로 재배정(선택)", value=False,
                   help="목적: 한도 1달러당 기대마진 − 금융비용 − 보험료 − 기대손실 최대화. 제약: 총허용익스포저·미부보 EL 예산·국가 한도·B등급 비중")
summary = None
if use_lp:
    r, summary = LM.lp_limits(b, p)
    r["proposed_limit"] = r["lp_limit"]
    r["delta"] = (r["proposed_limit"] - pd.to_numeric(r["current_limit_usd"], errors="coerce")).round(0)
st.session_state["limits"], st.session_state["lp_summary"] = r, summary

pe = LM.portfolio_el(r, p)
m1, m2, m3, m4 = st.columns(4)
m1.metric("현행 한도 합계", ui.money(pd.to_numeric(r["current_limit_usd"], errors="coerce").sum()))
m2.metric("제안 한도 합계", ui.money(r["proposed_limit"].sum()))
m3.metric("감액 30%↑(사람 승인)", int(r["approval_level"].str.startswith("사람 승인").sum()))
m4.metric("미부보 EL / 예산", f"{pe['usage_pct']:.0f}%", delta="초과" if not pe["ok"] else "예산 안", delta_color="inverse" if not pe["ok"] else "off")
st.caption(f"입력: {b.attrs.get('source', '')} · 파라미터: {psrc}")
if summary:
    st.info(f"LP: {summary['status']} · 목적값 {summary.get('objective') or 0:,.0f} · 총허용익스포저 {ui.money(summary['total_cap'])} · "
            f"걸린 제약 {summary.get('binding', [])} · 그림자 가격 {summary.get('shadow_prices', {})}")

cols = ["buyer_id", "buyer_name", "grade", "payment_method", "terms_days", "ksure_insured", "open_ar_usd", "current_limit_usd",
        "need", "ub", "proposed_limit", "delta", "approval_level", "ub_reason", "terms_violation"]
only = st.checkbox("원장에 있는 바이어만", value=True)
view = r[r["buyer_id"].isin(L["buyer_id"])] if only else r
st.dataframe(view[[c for c in cols if c in view.columns]].sort_values("delta"), hide_index=True, height=380)
st.download_button("한도 표 CSV", view.to_csv(index=False).encode("utf-8-sig"), file_name="limits_proposed.csv", mime="text/csv")

st.subheader("4단계 충격 시나리오 — 기대손실(EL)")
scn = LM.load_scenarios(IO.scenarios_path())
el = LM.scenario_el(b.assign(grade=r["grade"]), p, scn)
sel = st.selectbox("시나리오", el["scenario_id"] + " " + el["name_ko"], index=0)
row = el[el["scenario_id"] == sel.split(" ")[0]].iloc[0]
s1, s2, s3 = st.columns(3)
s1.metric("EL(USD)", ui.money(row["el_usd"]), delta=f"{row['el_usd'] - el.iloc[0]['el_usd']:+,.0f} vs 기준")
s2.metric("채권 원화 가치(십억 원)", f"{row['krw_value_bn']:.2f}", delta=f"원/달러 {row['usd_krw_level']:,.0f}")
s3.metric("금융비용(USD)", ui.money(row["finance_cost_usd"]))
st.bar_chart(el.set_index("scenario_id")[["el_usd", "el_budget_usd"]])
st.dataframe(el, hide_index=True)
st.caption("EL_s = Σ 미결 잔액 × min(1, PD_g × 배수) × LGD_s × (1 − 보상비율·부보 시). PD 배수·LGD 상향은 교육용 가정.")
