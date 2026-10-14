"""② 예측·등급 — Day3 강사 모델(LightGBM)로 30일 연체확률(pd_30d)을 다시 계산하고 S/A/B/C 등급을 붙인다.

입력: 바이어 특성 data/checkpoints/d3_start_scoring.csv(기준일 2026-09-30) · 모델 models/day3_lgbm.pkl(+ .txt) · feature_list.json · grade_cutoffs.json
      직전 기준일 비교: d3_start_features.csv의 2026-08-31 행(등급 변화)
출력: st.session_state['scored'](바이어 150곳 점수표)
"""
import pandas as pd
import streamlit as st

import ui
from core import data_io as IO
from core import model as MD

st.title("② 예측·등급")
st.caption("모델 점수는 판단 보조다. 등급·한도 변경은 사람이 확인하고 승인한다.")
L = ui.need_ledger()
if L is None:
    st.stop()

feats = ui.load_features(str(IO.FEATURES_SCORING))
try:
    bundle = ui.load_model()
except Exception as e:  # 모델 파일이 없거나 읽기 실패
    bundle = None
    st.warning(f"모델을 불러오지 못했습니다({type(e).__name__}). 원장에 있는 grade·pd_30d 열을 그대로 씁니다.")
if feats is None or bundle is None:
    if "grade" not in L.columns or L["grade"].eq("").all():
        st.error("바이어 특성 파일(d3_start_scoring.csv)이나 모델이 없고, 원장에도 등급이 없습니다.")
        st.stop()
    sc = L.groupby("buyer_id").agg(pd_30d=("pd_30d", "first"), grade=("grade", "first")).reset_index()
    sc["grade_prev"], sc["grade_change"], sc["top_reasons_ko"] = "", "", ""
    st.session_state["scored"] = sc
    st.dataframe(sc, hide_index=True)
    st.stop()

c1, c2 = st.columns(2)
upd = c1.toggle("업로드 원장으로 '지금 연체' 특성 갱신", value=False,
                help="원장에 있는 바이어의 oldest_open_days · ksure_30d_flag · overdue_amount_usd · open_ar_usd를 원장 기준으로 다시 계산")
rule = c2.radio("등급 규칙", ["t 규칙(t/4·t/2·t)", "분위수(15/35/35/15) 🔵"], horizontal=True)
f = MD.update_from_ledger(feats, L, ui.asof()) if upd else feats
# 점수 · 등급 · 직전 기준일(2026-08-31) 등급 · 등급 변화(grade_change) · 뉴스 위험 — 계산은 core/model.py
sc = MD.score_table(f, bundle, ui.load_features(str(IO.FEATURES_PREV)), quantile=rule.startswith("분위수"))
names = L.groupby("buyer_id")["buyer_name"].first()
sc["buyer_name"] = sc["buyer_id"].map(names).fillna("")
sc["in_ledger"] = sc["buyer_id"].isin(L["buyer_id"]).astype(int)
st.session_state["scored"] = sc
st.session_state["threshold"] = float(bundle.cutoffs.get("threshold", 0.1698))

t = st.session_state["threshold"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("모델", f"{bundle.version} ({bundle.kind})")
m2.metric("임계값 t(FN:FP = 5:1)", f"{t:.3f}")
m3.metric("C등급(원장 바이어)", int(((sc["grade"] == "C") & (sc["in_ledger"] == 1)).sum()))
m4.metric("등급 하락(전월 대비)", int((sc["grade_change"] == "down").sum()))

g1, g2 = st.columns(2)
with g1:
    st.markdown("**등급 분포 — 원장에 있는 바이어**")
    d = sc[sc["in_ledger"] == 1]["grade"].value_counts().reindex(MD.GRADES).fillna(0)
    st.bar_chart(pd.DataFrame({"바이어 수": d.values}, index=MD.GRADES))
with g2:
    st.markdown("**등급 분포 — 전체 150곳**")
    d = sc["grade"].value_counts().reindex(MD.GRADES).fillna(0)
    st.bar_chart(pd.DataFrame({"바이어 수": d.values}, index=MD.GRADES))

only = st.checkbox("원장에 있는 바이어만", value=True)
view = sc[sc["in_ledger"] == 1] if only else sc
cols = ["buyer_id", "buyer_name", "pd_30d", "grade", "grade_prev", "grade_change", "news_risk_30d", "top_reasons_ko"]
st.dataframe(view.sort_values("pd_30d", ascending=False)[[c for c in cols if c in view.columns]], hide_index=True,
             height=420,
             column_config={"pd_30d": st.column_config.ProgressColumn("pd_30d", min_value=0.0, max_value=1.0, format="%.3f"),
                            "top_reasons_ko": st.column_config.TextColumn("상위 기여(+ = 위험↑)", width="large")})
if "grade" in L.columns and L["grade"].ne("").any():
    led = L.groupby("buyer_id")["grade"].first()
    diff = sc[sc["buyer_id"].isin(led.index)]
    same = (diff["grade"].to_numpy() == diff["buyer_id"].map(led).to_numpy()).mean()
    st.caption(f"원장 grade 열(Day3 체크포인트)과 같은 등급 비율: {same:.0%} — 규칙·특성 갱신 여부에 따라 달라진다.")
st.download_button("점수표 CSV", view.to_csv(index=False).encode("utf-8-sig"), file_name="scored_buyers.csv", mime="text/csv")
