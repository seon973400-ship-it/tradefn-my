"""화면 스모크 테스트(Streamlit AppTest, 모의 모드) — 상황판(첫 화면) + 7페이지가 예외 없이 그려지고, ⑤에서 초안 → 승인 → 감사로그가 쌓이는지."""
import pandas as pd
from streamlit.testing.v1 import AppTest

from core import data_io as IO

ENTRY = str(IO.APP_DIR / "streamlit_app.py")
PAGES = ["views/p0_overview.py", "views/p1_upload.py", "views/p2_score.py", "views/p3_limits.py", "views/p4_alerts.py",
         "views/p5_dunning.py", "views/p6_rag.py", "views/p7_log.py"]


def _app():
    at = AppTest.from_file(ENTRY, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def test_all_pages_render(d5_raw):
    at = _app()
    assert any("상황판" in t.value for t in at.title)           # 첫 화면 = 통합 상황판
    for p in PAGES[1:]:
        at.switch_page(p)
        at.run()
        assert not at.exception, (p, at.exception)
        assert len(at.title) >= 1, p


def test_overview_is_first_view(d5_raw):
    """첫 화면(상황판)에 KPI 줄 · P1·P2 건수 · 바이어 표 · 기준일이 보이고, 건수는 ④와 같은 규칙 결과다."""
    from core import alerts as AL
    from core import clean as CL
    at = _app()
    labels = [m.label for m in at.metric]
    for need in ("미결 채권", "연체 30일+", "P1 즉시", "P2 오늘", "통지 기한", "독촉 초안 대상"):
        assert any(need in x for x in labels), (need, labels)
    led = CL.clean_ledger(d5_raw, asof=pd.Timestamp("2026-09-30"), fx=IO.load_fx(), hist_median=IO.load_history_median()).df
    cnt = AL.summary(AL.run_rules(led, asof="2026-09-30"))
    val = {m.label: m.value for m in at.metric}
    assert str(cnt["P1"]) == next(v for k, v in val.items() if "P1" in k)
    assert str(cnt["P2"]) == next(v for k, v in val.items() if "P2" in k)
    assert any("2026-09-30" in m.value for m in at.markdown)       # 기준일 표시
    assert len(at.dataframe) >= 2                                   # 경보 표 + 바이어 표
    assert not at.exception
    top = len(at.dataframe[-1].value)                               # 기본 = 오늘 볼 순서 상위 15곳
    assert top == 15
    tog = [x for x in at.toggle if "보기" in x.label][0]
    tog.set_value(True)
    at.run()
    assert not at.exception
    assert len(at.dataframe[-1].value) == led["buyer_id"].nunique() > top   # 전체 바이어


def test_upload_sample_page(d5_raw):
    at = _app()
    at.switch_page("views/p1_upload.py")
    at.run()
    at.radio[0].set_value("샘플(표기가 섞인 100행)")
    at.button[0].click()
    at.run()
    assert not at.exception
    assert any("정제 후" in s.value for s in at.success)


def test_dunning_approve_logs(d5_raw):
    at = _app()
    at.session_state["demo_clock"] = "2026-10-20 15:00"   # 발송 시간창(한국 08–21시) 안 — 실제 시각과 무관하게
    at.switch_page("views/p5_dunning.py")
    at.run()
    btn = [b for b in at.button if b.label == "초안 만들기"]
    assert btn, "초안 만들기 버튼 없음"
    btn[0].click()
    at.run()
    assert not at.exception, at.exception
    assert at.session_state["draft"]["model_alias"] == "mock"
    approver = [t for t in at.text_input if t.label == "승인자"][0]
    approver.set_value("홍길동")
    at.run()
    ok = [b for b in at.button if b.label.startswith("승인")][0]
    assert not ok.disabled, "가드레일 통과했는데 승인 버튼이 막혀 있다(발송 시간창은 Asia/Seoul 08–21시 기준)"
    ok.click()
    at.run()
    assert len(at.session_state["audit_log"]) == 1
    assert at.session_state["audit_log"][0]["guardrail_result"] == "pass"
    assert at.session_state["audit_log"][0]["decision"] == "approve"
    at.switch_page("views/p7_log.py")
    at.run()
    assert not at.exception


def test_send_window_blocks_at_night(d5_raw):
    at = _app()
    at.session_state["demo_clock"] = "2026-10-20 22:30"
    at.switch_page("views/p5_dunning.py")
    at.run()
    [b for b in at.button if b.label == "초안 만들기"][0].click()
    at.run()
    [t for t in at.text_input if t.label == "승인자"][0].set_value("홍길동")
    at.run()
    assert [b for b in at.button if b.label.startswith("승인")][0].disabled


def test_alert_dialog_and_ack(d5_raw):
    at = _app()
    at.switch_page("views/p4_alerts.py")
    at.run()
    assert not at.exception
    ack = [b for b in at.button if b.label == "확인하고 기록"]
    if ack:                       # 대화상자 안 버튼(AppTest가 대화상자 내용을 그릴 때)
        ack[0].click()
        at.run()
        assert at.session_state["alert_ack"] is True
        assert at.session_state["audit_log"][-1]["decision"] == "ack"
