"""화면 공용 도우미 — 사이드바·캐시·세션 상태·LLM 설정. 페이지 파일(views/*.py)이 import 한다.

세션 상태 키(다른 파일에서 이름을 바꾸지 말 것):
  ledger · clean_report · clean_issues · ledger_source   ① 정제 원장
  scored                                               ② 바이어 점수표(150곳)
  limits · lp_summary                                  ③ 한도 표
  alerts · alert_ack                                   ④ 경보 · 대화상자 확인 여부
  dunning_target · draft                               ⑤ 독촉 대상 인보이스 · 현재 초안
  rag_extra · rag_history · goldset_run                ⑥ 올린 문서 · 질문 기록 · 골든셋 결과
  audit_log · llm_usage                                ⑦ 감사로그 · LLM 사용량
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from core import clean as CL
from core import data_io as IO
from core import llm as LLM
from core import model as MD
from core import rag as RG


def init_state() -> None:
    ss = st.session_state
    for k, v in {"audit_log": [], "llm_usage": [], "alert_ack": False, "rag_extra": [], "rag_history": [],
                 "asof": IO.ASOF_DEFAULT, "use_llm": True}.items():
        ss.setdefault(k, v)


def secrets_section(name: str) -> dict:
    """st.secrets의 [name] 칸. secrets 파일이 없으면 빈 dict(모의 모드)."""
    try:
        return dict(st.secrets[name])
    except Exception:
        return {}


def llm_config() -> LLM.LLMConfig | None:
    """Secrets [llm]이 있고 사이드바 'LLM 사용'이 켜져 있으면 설정, 아니면 None(모의 모드)."""
    if not st.session_state.get("use_llm", True):
        return None
    try:
        return LLM.from_secrets(st.secrets)
    except Exception:
        return None


def app_settings() -> dict:
    a = secrets_section("app")
    wl = a.get("recipient_whitelist", [])
    if isinstance(wl, str):
        wl = [wl]
    return {"learner_id": str(a.get("learner_id", "L00")), "approver_name": str(a.get("approver_name", "")),
            "recipient_whitelist": list(wl) or None, "send_tz": str(a.get("send_tz", "Asia/Seoul")),
            "sender": {k: str(a[k]) for k in ("company_name", "sender_name", "sender_title", "account_manager") if k in a}}


def now():
    """가드레일 발송 시간창에 쓰는 시각. Secrets [app] demo_clock(예: "2026-10-20 15:00", 한국 시각) 또는
    세션 'demo_clock'이 있으면 그 시각 — 밤에 리허설할 때·테스트용. 없으면 지금 시각."""
    from zoneinfo import ZoneInfo
    v = st.session_state.get("demo_clock") or secrets_section("app").get("demo_clock")
    if v:
        try:
            return pd.Timestamp(v).tz_localize("Asia/Seoul").to_pydatetime()
        except Exception:
            pass
    return dt.datetime.now(ZoneInfo("Asia/Seoul"))


def asof() -> pd.Timestamp:
    return pd.Timestamp(st.session_state.get("asof", IO.ASOF_DEFAULT))


def sidebar():
    """모든 페이지 공통 사이드바(진입점이 한 번 그린다). 건수 칸을 돌려준다 — 페이지가 끝난 뒤 fill_counter로 다시 채운다."""
    ss = st.session_state
    with st.sidebar:
        st.markdown("**TradeRisk Control Tower** · (가상) 한빛정밀(주)")
        st.date_input("기준일(AsOf)", key="asof", help="연체일·독촉 단계·통지 기한 계산 기준. 수업 데이터 = 2026-09-30")
        has_secret = LLM.from_secrets(_safe_secrets()) is not None
        st.toggle("LLM 사용(LiteLLM)", key="use_llm", disabled=not has_secret,
                  help="Secrets [llm]이 있어야 켤 수 있다. 끄면 모의 모드(템플릿 초안·검색 결과 인용)")
        if not has_secret:
            st.caption("🔒 Secrets 없음 → **모의 모드**(LLM 호출 없음)")
        elif ss.get("use_llm"):
            st.caption("🟢 LLM 연결됨 — 사용량은 ⑦ 로그에서 확인")
        counter = st.empty()
        fill_counter(counter)
        with st.expander("입력 파일 상태"):
            for name, ok in IO.available().items():
                st.write(("✅ " if ok else "⬜ ") + name)
        st.caption("합성 데이터 전용 · 실제 발송 없음(Draft-only) · 모든 결정은 사람이 승인")
    return counter


def fill_counter(slot) -> None:
    """사이드바 건수(감사로그·LLM 호출). 승인·경보 확인 직후에도 맞는 숫자가 보이게 페이지 실행 뒤 한 번 더 부른다."""
    ss = st.session_state
    slot.caption(f"감사로그 {len(ss.get('audit_log', []))}건 · LLM 호출 {len(ss.get('llm_usage', []))}회")


def _safe_secrets():
    try:
        return st.secrets
    except Exception:
        return {}


# ------------------------------------------------------------------------------------------ 캐시 로더
@st.cache_data(show_spinner=False)
def load_fx():
    return IO.load_fx()


@st.cache_data(show_spinner=False)
def load_history_median():
    return IO.load_history_median()


@st.cache_data(show_spinner=False)
def load_history():
    return IO.load_invoice_history()


@st.cache_data(show_spinner=False)
def load_features(path: str) -> pd.DataFrame | None:
    from pathlib import Path
    p = Path(path)
    return pd.read_csv(p, encoding="utf-8-sig") if p.exists() else None


@st.cache_resource(show_spinner="모델을 불러오는 중…")
def load_model():
    return MD.load_model(IO.models_dir())


@st.cache_resource(show_spinner=False)
def base_corpus():
    return RG.load_corpus(IO.RAG_CORPUS)


def retriever(extra: list) -> RG.Retriever:
    key = tuple((d, p, len(b)) for d, p, b in extra)
    cache = st.session_state.setdefault("_retr_cache", {})
    if key not in cache:
        cache.clear()
        cache[key] = RG.Retriever(base_corpus() + sum((RG.split_markdown(b, p, d) for d, p, b in extra), []))
    return cache[key]


def clean_default_ledger() -> bool:
    """세션에 원장이 없고 기본 원장(d5_start.csv)이 있으면 자동으로 정제해 둔다(다른 페이지부터 열어도 되게)."""
    ss = st.session_state
    if "ledger" in ss or not IO.DEFAULT_LEDGER.exists():
        return "ledger" in ss
    res = CL.clean_ledger(IO.read_csv_any(IO.DEFAULT_LEDGER), asof=asof(), fx=load_fx(), hist_median=load_history_median())
    ss["ledger"], ss["clean_report"], ss["clean_issues"] = res.df, res.report, res.issues
    ss["ledger_source"] = "기본 원장 d5_start.csv(자동)"
    return True


def need_ledger() -> pd.DataFrame | None:
    if not clean_default_ledger():
        st.warning("먼저 **① 업로드·전처리**에서 원장을 불러오세요(기본 원장 d5_start.csv는 Day5 아침에 공개됩니다).")
        st.page_link("views/p1_upload.py", label="① 업로드·전처리로 가기", icon="📥")
        return None
    return st.session_state["ledger"]


def log_llm(alias: str, resolved: str, tin: int, tout: int, purpose: str) -> None:
    st.session_state["llm_usage"].append({"time": dt.datetime.now().strftime("%H:%M:%S"), "purpose": purpose, "model_alias": alias,
                                          "model_resolved": resolved, "tokens_in": tin, "tokens_out": tout,
                                          "cost_usd": LLM.cost_usd(alias, tin, tout)})


def date_config(df: pd.DataFrame) -> dict:
    """표의 날짜 열을 YYYY-MM-DD로 보이게 하는 column_config."""
    return {c: st.column_config.DateColumn(c, format="YYYY-MM-DD") for c in df.columns
            if pd.api.types.is_datetime64_any_dtype(df[c])}


def money(v) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "–"
