"""⓪ 통합 상황판 — 첫 화면(1페이지). 결정 질문 하나에 답한다: "오늘 누구에게 선적·독촉·통지를 해야 하나?"

위에서 아래로: KPI 줄 → P1·P2 경보 → 바이어 표 → 근거·기준일(대시보드 4원칙: 결정 질문 하나 · 요약 숫자 → 경보 → 표 → 근거 ·
색은 위험에만(글자와 함께) · 숫자마다 기준일). 계산은 core/overview.py, 경보 규칙은 ④ 조기경보(core/alerts.py)와 같다.
입력: ① 정제 원장(없으면 기본 원장 d5_start.csv를 자동으로 정제) · (있으면) ② 점수표. 새 세션 키는 없다.
"""
import streamlit as st

import ui
from core import alerts as AL
from core import overview as OV

asof = ui.asof()
st.title("TradeRisk Control Tower — 통합 상황판")
st.markdown(f"**오늘 결정할 것** — 누구에게 선적 · 독촉 · 통지를 해야 하나?  ·  기준일(AsOf) **{asof:%Y-%m-%d}**")
L = ui.need_ledger()
if L is None:
    st.stop()
sc = st.session_state.get("scored")
t = float(st.session_state.get("threshold", 0.1698))
al = AL.run_rules(L, asof=asof, buyers=sc, threshold=t)       # ④의 기본 설정(보험 개별 · 뉴스 7.0)과 같다
k = OV.kpis(L, al, asof)

# ── KPI 줄 ────────────────────────────────────────────────────────────────────────────
nd = k["notice_min_days"]
tiles = [
    ("미결 채권", OV.usd_short(k["open_usd"]),
     f"{k['open_count']}건 · {k['buyers']}곳 · 연체 {k['overdue_count']}건 {OV.usd_short(k['overdue_usd'])}",
     "선수금을 뺀 미결 인보이스의 미결 잔액(USD) 합계. 연체 = 결제기일이 지난 건"),
    ("연체 30일+", OV.usd_short(k["hold_usd"]), f"{k['hold_count']}건 · {k['hold_buyers']}곳 · 선적 보류선",
     "신용장·선수금을 뺀, 결제기일 + 30일을 넘긴 미결. 무신용장 거래의 추가 선적은 연속수출 면책 위험(약관 제7조 제1항 제2호)"),
    ("🔴 P1 즉시", k["p1"], f"파산·부도 {k['p1_bankrupt']} · 사기 신호 {k['p1_fraud']}", "신규 선적 중단·계좌 변경 금지 — 사람이 바로 확인"),
    ("🟠 P2 오늘", k["p2"], f"선적 {k['p2_hold']} · 통지 임박 {k['p2_notice']} · 경과 {k['p2_notice_late']}",
     "선적 = 선적 보류선(결제기일 + 30일 초과) · 통지 임박 = 사고발생통지 기한 7일 전부터 · 경과 = 기한이 지난 건(결제기일 + 1개월)"),
    ("통지 기한", "–" if nd is None else f"D-{nd}", "임박한 통지 없음" if nd is None else f"가장 가까운 기한 · {k['notice_buyer']} {k['notice_invoice']}",
     "부보 건의 사고발생통지 기한까지 남은 일수(결제기일 + 1개월). 늦으면 손실을 보상받지 못할 수 있다(약관 제21조·제7조)"),
    ("독촉 초안 대상", f"{k['draft']}건", f"사람 처리 {k['human']} · 이미 보냄 {k['skip']}",
     "⑤ 독촉메일에서 AI 초안을 만들 수 있는 인보이스. 파산·사기·D+45 이후는 사람이 직접 처리"),
]
for col, (label, value, sub, hint) in zip(st.columns(len(tiles)), tiles):
    with col.container(border=True):
        st.metric(label, value, help=hint)
        st.caption(sub)

# ── 경보 ──────────────────────────────────────────────────────────────────────────────
st.subheader("P1·P2 경보 — 사람이 확인할 일")
urgent_n = k["p1"] + k["p2"]
shown = 8
if urgent_n:
    st.dataframe(OV.alert_table(al, shown), hide_index=True,
                 column_config={"우선순위": st.column_config.TextColumn("우선순위", width="small"), "rule": st.column_config.TextColumn("규칙", width="medium"),
                                "buyer_id": st.column_config.TextColumn("바이어", width="small"),
                                "invoice_id": st.column_config.TextColumn("인보이스", width="medium"),
                                "detail": st.column_config.TextColumn("내용", width="medium"),
                                "action": st.column_config.TextColumn("조치(사람)", width="large")})
else:
    st.success(f"기준일 {asof:%Y-%m-%d}에는 P1·P2 경보가 없습니다.")
more = f"외 {urgent_n - shown}건 · " if urgent_n > shown else ""
st.caption(f"{more}P3 {k['p3']}건 · P4 {k['p4']}건은 ④ 조기경보에서." +
           ("" if sc is not None else " P4(등급 하락·뉴스 위험·pd_30d ≥ t)는 ② 예측·등급을 열면 계산된다.") +
           (" ✅ P1·P2 확인 기록됨(⑦ 로그)." if st.session_state.get("alert_ack") else ""))
st.page_link("views/p4_alerts.py", label="④ 조기경보 — 전체 보기 · 확인하고 기록", icon="🚨")

# ── 바이어 표 ─────────────────────────────────────────────────────────────────────────
st.subheader("바이어 — 오늘 볼 순서")
st.caption("경보가 높은 순(P1 → P2 → P3 → P4 → 없음), 같으면 연체 금액이 큰 순. 등급·pd_30d는 ② 점수표가 있으면 그 값, 없으면 원장 열(Day3 체크포인트).")
bt = OV.buyer_table(L, al, sc)
everyone = st.toggle(f"전체 {len(bt)}곳 보기", value=False)
view = bt if everyone else bt.head(15)
cols = ["alert", "buyer_label", "signals", "grade", "pd_30d", "open_usd", "overdue_usd", "max_dpd", "limit_text"]
st.dataframe(view[cols], hide_index=True, height=560 if everyone else 35 * len(view) + 40,
             column_config={"alert": st.column_config.TextColumn("경보", width="small"),
                            "buyer_label": st.column_config.TextColumn("바이어", width="medium"),
                            "signals": st.column_config.TextColumn("P1·P2 신호", width="medium"),
                            "grade": st.column_config.TextColumn("등급", width="small"),
                            "pd_30d": st.column_config.ProgressColumn("pd_30d", min_value=0.0, max_value=1.0, format="%.3f", width="small"),
                            "open_usd": st.column_config.NumberColumn("미결(USD)", format="$%,d"),
                            "overdue_usd": st.column_config.NumberColumn("연체(USD)", format="$%,d"),
                            "max_dpd": st.column_config.NumberColumn("최장 연체일", format="%d", width="small"),
                            "limit_text": st.column_config.TextColumn("한도 사용", width="small")})

# ── 근거·기준일 ───────────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"**근거·기준일** — 모든 숫자의 기준일은 **{asof:%Y-%m-%d}**입니다. 원장: {st.session_state.get('ledger_source', '')}")
    st.caption("경보 근거 = 가상 여신관리규정 제20조·제23조·제24조·제28조 · K-SURE 단기수출보험 약관 제7조·제21조(④ 조기경보의 '근거' 열과 같은 규칙). "
               "연체일·독촉 단계·통지 기한은 ① 전처리가 계산한 값이라 기준일을 바꾸면 ①을 다시 실행합니다. "
               "규칙으로 계산한 목록이며 AI가 판단한 것이 아닙니다 — 조치는 사람이 결정하고 기록합니다(합성 데이터 · 실제 발송 없음).")
st.markdown("**다음 할 일**")
nav = st.columns(4)
nav[0].page_link("views/p5_dunning.py", label="⑤ 독촉메일 — 초안 만들기", icon="✉️")
nav[1].page_link("views/p3_limits.py", label="③ 한도·시나리오", icon="🧮")
nav[2].page_link("views/p7_log.py", label="⑦ 로그 — 감사로그 내려받기", icon="🧾")
nav[3].page_link("views/p1_upload.py", label="① 다른 원장 올리기", icon="📥")
