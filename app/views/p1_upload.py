"""① 업로드·전처리 — 미결 인보이스 원장(CSV)을 읽어 표기를 통일하고 연체일·독촉 단계를 계산한다.

입력: 기본 원장 data/checkpoints/d5_start.csv · 샘플 app/sample_data/upload_sample.csv(표기가 섞인 100행) · 내 CSV(≤ 5MB)
출력: st.session_state['ledger'](정제 원장) · 정제 리포트 · 확인 목록 · 정제 CSV 다운로드
"""
import pandas as pd
import streamlit as st

import ui
from core import clean as CL
from core import data_io as IO

st.title("① 업로드·전처리")
st.caption("날짜·통화·금액 표기를 통일하고 중복·빈칸·단위 의심을 찾는다. 원본은 그대로 두고 정제본을 따로 만든다.")

options = []
if IO.DEFAULT_LEDGER.exists():
    options.append("기본 원장(d5_start.csv)")
options += ["샘플(표기가 섞인 100행)", "내 CSV 올리기"]
src = st.radio("원장 고르기", options, horizontal=True)
up = None
if src == "내 CSV 올리기":
    up = st.file_uploader("미결 인보이스 원장 CSV(d5_start.csv 형식, 5MB 이하)", type=["csv"])
    st.caption("필수 열: invoice_id · buyer_id · currency · amount_ccy · invoice_date · due_date. 실데이터는 올리지 마세요(합성·익명화 데이터만).")

if st.button("전처리 실행", type="primary"):
    try:
        if src.startswith("기본"):
            raw, name = IO.read_csv_any(IO.DEFAULT_LEDGER), "기본 원장 d5_start.csv"
        elif src.startswith("샘플"):
            raw, name = IO.read_csv_any(IO.SAMPLE_UPLOAD), "샘플 upload_sample.csv"
        else:
            if up is None:
                st.error("CSV 파일을 먼저 올리세요.")
                st.stop()
            if up.size > 5 * 1024 * 1024:
                st.error("5MB를 넘는 파일은 받지 않습니다.")
                st.stop()
            raw, name = IO.read_csv_any(up), f"업로드 {up.name}"
        res = CL.clean_ledger(raw, asof=ui.asof(), fx=ui.load_fx(), hist_median=ui.load_history_median())
    except ValueError as e:
        st.error(str(e))
        st.stop()
    st.session_state.update({"ledger": res.df, "clean_report": res.report, "clean_issues": res.issues, "ledger_source": name})
    for k in ("scored", "limits", "alerts", "draft", "dunning_target"):   # 원장이 바뀌면 뒤 단계 결과를 지운다
        st.session_state.pop(k, None)
    st.session_state["alert_ack"] = False
    st.success(f"{name}: {len(raw)}행 읽음 → 정제 후 {len(res.df)}행")

ui.clean_default_ledger()
L = st.session_state.get("ledger")
if L is None:
    st.info("원장을 고르고 **전처리 실행**을 누르세요.")
    st.stop()

st.subheader(f"정제 결과 — {st.session_state.get('ledger_source', '')}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("인보이스", f"{len(L):,}행")
c2.metric("연체(dpd > 0)", f"{int((L['dpd'] > 0).sum())}행")
c3.metric("독촉 단계 대상", f"{int(L['dunning_stage'].notna().sum())}행")
c4.metric("확인 필요", f"{int(L['needs_review'].sum())}행")

st.markdown("**정제 리포트** — 유형별로 고친(또는 표시한) 건수")
rep = st.session_state["clean_report"]
st.dataframe(rep[["유형", "건수", "처리"]], hide_index=True)
iss = st.session_state["clean_issues"]
if len(iss):
    with st.expander(f"확인 목록 {len(iss)}건 — 사람이 원본을 보고 판단할 행"):
        st.dataframe(iss, hide_index=True)

st.markdown("**독촉 단계 분포**(0 = D-3 · 1 = D+7 · 2 = D+15 · 3 = D+30)")
dist = L["dunning_stage"].value_counts().sort_index()
st.bar_chart(pd.DataFrame({"행 수": dist.values}, index=[f"단계 {int(i)}" for i in dist.index]))

show = ["invoice_id", "buyer_id", "buyer_name", "currency", "amount_ccy", "open_amount_ccy", "amount_usd", "invoice_date",
        "due_date", "dpd", "dunning_stage", "payment_method", "ksure_insured", "ksure_notice_deadline", "needs_review"]
view = L[[c for c in show if c in L.columns]]
st.dataframe(view, hide_index=True, height=360, column_config=ui.date_config(view))
st.download_button("정제 CSV 내려받기", CL.to_export(L).to_csv(index=False).encode("utf-8-sig"),
                   file_name="ledger_clean.csv", mime="text/csv")
