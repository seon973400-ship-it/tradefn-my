"""TradeRisk Control Tower — (가상) 한빛정밀(주) 매출채권 리스크 대시보드(Day5 템플릿).

실행: streamlit run app/streamlit_app.py   (저장소 루트에서)
배포: Streamlit Community Cloud → Main file path = app/streamlit_app.py → Secrets에 [llm]·[app] (app/README.md)
흐름: ⓪ 통합 상황판(첫 화면) → ① 업로드·전처리 → ② 예측·등급 → ③ 한도·시나리오 → ④ 조기경보 → ⑤ 독촉메일 → ⑥ RAG 규정검색 → ⑦ 로그
원칙: 합성 데이터만 · 실제 발송 없음(Draft-only) · AI 출력은 사람이 승인한 뒤 확정 · 모든 행동은 감사로그
"""
import streamlit as st

import ui

st.set_page_config(page_title="TradeRisk Control Tower", page_icon="🛰️", layout="wide")
ui.init_state()
counter = ui.sidebar()

pages = {
    "상황판": [
        st.Page("views/p0_overview.py", title="⓪ 통합 상황판", icon="🛰️", default=True),
    ],
    "데이터": [
        st.Page("views/p1_upload.py", title="① 업로드·전처리", icon="📥"),
        st.Page("views/p2_score.py", title="② 예측·등급", icon="📊"),
        st.Page("views/p3_limits.py", title="③ 한도·시나리오", icon="🧮"),
    ],
    "운영": [
        st.Page("views/p4_alerts.py", title="④ 조기경보", icon="🚨"),
        st.Page("views/p5_dunning.py", title="⑤ 독촉메일", icon="✉️"),
        st.Page("views/p6_rag.py", title="⑥ RAG 규정검색", icon="📚"),
        st.Page("views/p7_log.py", title="⑦ 로그", icon="🧾"),
    ],
}
try:
    st.navigation(pages).run()
finally:  # 페이지가 st.stop()으로 끝나도 승인·확인 뒤 사이드바 건수를 새로 채운다
    ui.fill_counter(counter)
