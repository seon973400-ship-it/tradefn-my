"""④ 조기경보 — 규칙 엔진(P1~P4)으로 '사람이 확인할 일' 목록을 만든다. P1·P2가 있으면 대화상자를 한 번 띄운다.

P1 파산·부도 인지 · 사기 신호 / P2 선적 보류선(결제기일 + 30일 초과) · 사고발생통지 기한(결제기일 + 1개월)
P3 결제조건 변경 · 한도 사용률 · 수출통지 기한 / P4 등급 하락 · 뉴스 위험 ≥ 7 · pd_30d ≥ t
15/1000 위약금은 경보에 쓰지 않는다(약관 제21조③ 한정 조항).
"""
import pandas as pd
import streamlit as st

import ui
from core import alerts as AL
from core import audit as AU
from core import dunning as DN

st.title("④ 조기경보")
L = ui.need_ledger()
if L is None:
    st.stop()
c1, c2 = st.columns(2)
mode = c1.radio("보험 운영방식(수출통지 기한)", ["개별", "포괄", "끔"], horizontal=True,
                help="개별: 선적 후 10영업일 · 포괄·준포괄: 선적 다음 달 20일(약관 제16조)")
news_cut = c2.slider("뉴스 위험 경보 기준", 5.0, 9.0, 7.0, 0.5)
sc = st.session_state.get("scored")
t = float(st.session_state.get("threshold", 0.1698))
al = AL.run_rules(L, asof=ui.asof(), buyers=sc, threshold=t, insurance_mode=mode, news_cut=news_cut)
st.session_state["alerts"] = al
cnt = AL.summary(al)

urgent = al[al["priority"].isin(["P1", "P2"])]


@st.dialog("🚨 지금 확인할 경보(P1·P2)", width="large", dismissible=False)
def show_alerts(df: pd.DataFrame):
    st.write(f"P1 {cnt['P1']}건 · P2 {cnt['P2']}건 — 사람이 확인하고 조치한다(자동 조치 없음).")
    st.dataframe(df[["priority", "rule", "buyer_id", "buyer_name", "invoice_id", "detail", "action"]].head(15), hide_index=True,
                 column_config={"invoice_id": st.column_config.TextColumn("invoice_id", width="medium")})
    if len(df) > 15:
        st.caption(f"외 {len(df) - 15}건은 아래 표에서")
    if st.button("확인하고 기록", type="primary"):
        a = ui.app_settings()
        AU.new_entry(st.session_state["audit_log"], learner_id=a["learner_id"], decision="ack", alert_type=f"alert_ack P1={cnt['P1']} P2={cnt['P2']}",
                     approver=a["approver_name"] or "담당자")
        st.session_state["alert_ack"] = True
        st.rerun()


if len(urgent) and not st.session_state.get("alert_ack"):
    show_alerts(urgent)

m = st.columns(4)
for i, pr in enumerate(["P1", "P2", "P3", "P4"]):
    m[i].metric({"P1": "P1 즉시", "P2": "P2 오늘", "P3": "P3 이번 주", "P4": "P4 검토"}[pr], cnt[pr])
if st.session_state.get("alert_ack"):
    st.caption("✅ P1·P2 경보 확인 기록됨(⑦ 로그)")
if sc is None:
    st.caption("P4(등급 하락 · 뉴스 위험 · pd_30d ≥ t)는 ② 예측·등급 점수표가 있어야 계산된다.")
    st.page_link("views/p2_score.py", label="② 예측·등급 열기", icon="📊")

pri = st.multiselect("우선순위", ["P1", "P2", "P3", "P4"], default=["P1", "P2"])
view = al[al["priority"].isin(pri)]
st.dataframe(view, hide_index=True, height=380,
             column_config={"invoice_id": st.column_config.TextColumn("invoice_id", width="medium"),
                            "detail": st.column_config.TextColumn("내용", width="medium"),
                            "action": st.column_config.TextColumn("조치(사람)", width="large")})
with st.expander("규칙별 건수"):
    st.dataframe(al.groupby(["priority", "rule"]).size().rename("건수").reset_index(), hide_index=True)
st.download_button("경보 CSV", al.to_csv(index=False).encode("utf-8-sig"), file_name="alerts.csv", mime="text/csv")

st.subheader("독촉 초안으로 넘기기")
q = DN.queue(L, ui.asof())
cand = q[q["route"] == "DRAFT"]
if len(cand):
    pick = st.selectbox("초안 대상 인보이스(독촉 단계 · 아직 안 보낸 단계)", cand["invoice_id"] + " · " + cand["buyer_id"] + " · D" +
                        cand["dpd"].map(lambda d: f"{int(d):+d}") + " · " + cand["stage_key"].astype(str))
    if st.button("⑤ 독촉메일에서 초안 만들기"):
        st.session_state["dunning_target"] = pick.split(" · ")[0]
        st.switch_page("views/p5_dunning.py")
else:
    st.caption("지금 기준일에 초안을 만들 인보이스가 없습니다.")
