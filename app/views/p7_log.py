"""⑦ 로그 — 감사로그(21필드)와 LLM 사용량. Community Cloud 저장소는 휘발성이라 세션이 끝나기 전에 CSV로 내려받는다."""
import datetime as dt

import pandas as pd
import streamlit as st

import ui
from core import audit as AU

st.title("⑦ 로그")
ss = st.session_state
a = ui.app_settings()
log = AU.to_frame(ss["audit_log"])
c1, c2, c3 = st.columns(3)
c1.metric("감사로그", f"{len(log)}건")
c2.metric("승인·수정 승인", int(log["decision"].isin(["approve", "edit"]).sum()) if len(log) else 0)
c3.metric("반려", int((log["decision"] == "deny").sum()) if len(log) else 0)
if len(log):
    st.dataframe(log, hide_index=True, height=320)
else:
    st.info("아직 기록이 없습니다 — ④ 경보 확인, ⑤ 초안 승인·반려가 여기에 쌓입니다.")
fname = f"audit_log_{a['learner_id']}_{dt.date.today():%Y%m%d}.csv"
st.download_button("감사로그 CSV 내려받기", AU.to_csv_bytes(ss["audit_log"]), file_name=fname, mime="text/csv")

st.subheader("LLM 사용량")
u = pd.DataFrame(ss["llm_usage"], columns=["time", "purpose", "model_alias", "model_resolved", "tokens_in", "tokens_out", "cost_usd"])
m1, m2, m3 = st.columns(3)
m1.metric("호출", f"{len(u)}회")
m2.metric("토큰(입력/출력)", f"{int(u['tokens_in'].sum()):,} / {int(u['tokens_out'].sum()):,}")
m3.metric("추정 비용", f"${u['cost_usd'].sum():.4f}")
if len(u):
    st.dataframe(u, hide_index=True)
st.caption("추정 비용 = 별칭별 단가(1M 토큰당, core/llm.py PRICES) × 토큰 — 실제 청구는 공급자 콘솔 기준. 키 없이 쓰는 모의 모드에서는 0입니다.")
