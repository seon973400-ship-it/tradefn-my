"""모의 모드(LLM 없음) 끝까지: d5_start.csv → 정제 → 점수·등급 → 한도·시나리오 → 경보 → 독촉 초안·가드레일·승인 → 감사로그 → RAG."""
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from conftest import ASOF
from core import alerts as AL
from core import audit as AU
from core import clean as CL
from core import data_io as IO
from core import dunning as DN
from core import guardrails as GR
from core import limits as LM
from core import model as MD
from core import overview as OV
from core import rag as RG

CLASS_TIME = datetime(2026, 10, 20, 15, 0, tzinfo=ZoneInfo("Asia/Seoul"))   # Day5 6교시


def test_clean_default_ledger(d5_raw, ledger):
    assert len(ledger) == len(d5_raw) <= 300
    res = CL.clean_ledger(d5_raw, asof=ASOF)
    fixes = res.report.set_index("code")["건수"]
    assert fixes[["duplicate", "ccy_variant", "amount_text", "date_format", "missing", "unparsed", "decimal_error"]].sum() == 0
    assert (ledger["dpd"].astype(int).to_numpy() == pd.to_numeric(d5_raw["dpd"]).to_numpy()).all()
    st_raw = pd.to_numeric(d5_raw["dunning_stage"], errors="coerce")
    assert ((ledger["dunning_stage"].isna().to_numpy() & st_raw.isna().to_numpy()) |
            (ledger["dunning_stage"].astype("float").to_numpy() == st_raw.to_numpy())).all()


def test_upload_sample_cleaning():
    raw = IO.read_csv_any(IO.SAMPLE_UPLOAD)
    res = CL.clean_ledger(raw, asof=ASOF, fx=IO.load_fx(), hist_median=IO.load_history_median())
    c = res.counts
    assert len(res.df) == len(raw) - c["duplicate"]
    assert set(res.df["currency"].dropna()) <= set(CL.CANON_CCY)
    assert res.df["invoice_date"].notna().sum() >= len(res.df) - 1
    assert c["date_format"] >= 1 and c["ccy_variant"] >= 1 and c["amount_text"] >= 1 and c["duplicate"] == 1
    assert c["decimal_error"] >= 1                                  # ×100 단위 오류를 잡는다
    log = IO.REPO.parent / "instructor" / "day5" / "answers" / "upload_sample_dirt_log.csv"
    if log.exists():                                                 # 강사 정답 로그가 있으면 건수까지 대조
        exp = pd.read_csv(log, encoding="utf-8-sig")["error_type"].value_counts()
        for k in ("date_format", "ccy_variant", "amount_text", "duplicate", "missing"):
            assert c[k] == exp.get(k, 0), k
        assert c["decimal_error"] >= exp.get("decimal_error", 0)


def test_model_reproduces_day3():
    feats = pd.read_csv(IO.FEATURES_SCORING, encoding="utf-8-sig") if IO.FEATURES_SCORING.exists() else None
    if feats is None:
        pytest.skip("d3_start_scoring.csv 없음")
    b = MD.load_model(IO.models_dir())
    sc = MD.score(feats, b)
    assert len(sc) == 150 and sc["grade"].isin(MD.GRADES).all()
    d3 = IO.CK / "d3_end_scored.csv"
    if d3.exists():
        e = pd.read_csv(d3, encoding="utf-8-sig").set_index("buyer_id")
        m = sc.set_index("buyer_id")
        assert np.abs(m["pd_30d"] - e["pd_30d"]).max() < 1e-4
        assert (m["grade"] == e["grade"]).all()


def _scored(ledger):
    feats = pd.read_csv(IO.FEATURES_SCORING, encoding="utf-8-sig")
    return feats, MD.score(feats, MD.load_model(IO.models_dir()))


def test_limits_and_scenarios(ledger):
    feats, sc = _scored(ledger)
    d4 = pd.read_csv(IO.D4_START, encoding="utf-8-sig") if IO.D4_START.exists() else None
    p, _ = LM.load_params(IO.PARAMS)
    b = LM.buyer_inputs(feats, sc, ledger, d4, IO.load_invoice_history(), ASOF)
    r = LM.rule_limits(b, p)
    assert len(r) == 150
    zero = r[r["payment_method"].isin(LM.NO_LIMIT_METHODS) | (r["grade"] == "C") | (r["bankruptcy_flag"] == 1)]
    assert (zero["proposed_limit"] == 0).all()
    assert (r["proposed_limit"] <= r["need"] + 1e-6).all()
    lp, s = LM.lp_limits(b, p)
    assert s["success"] and lp["lp_limit"].sum() <= s["total_cap"] + 1
    el = LM.scenario_el(b.assign(grade=r["grade"]), p, LM.load_scenarios(IO.scenarios_path()))
    assert list(el["scenario_id"][:5]) == ["S0", "S1", "S2", "S3", "S4"]
    assert el["el_usd"].is_monotonic_increasing
    assert LM.portfolio_el(r, p)["budget_usd"] == p["equity"] * p["alpha"]


def test_alert_rules(ledger):
    al = AL.run_rules(ledger, asof=ASOF)
    p1 = al[al.priority == "P1"]
    assert len(set(p1[p1.rule == "사기 신호"].buyer_id)) >= 2                 # 사기 신호 P1 바이어가 둘 이상(ID는 정답이라 적지 않는다)
    assert set(ledger.loc[ledger.bankruptcy_flag == 1, "buyer_id"]) == set(p1[p1.rule.str.startswith("파산")].buyer_id)
    d3 = al[(al.rule == "사고발생통지 기한") & (al.days == 3)]
    assert len(d3) >= 2                                              # 인젝트 I-2: 결제기일 2026-09-03 → 기한 10-03(D-3)
    hold = al[al.rule.str.startswith("선적 보류선")]
    lc_buyers = set(ledger.loc[ledger.payment_method.isin(["LC_SIGHT", "LC_USANCE"]), "buyer_id"])
    over = ledger[(ledger.dpd > 30) & ~ledger.payment_method.isin(["LC_SIGHT", "LC_USANCE", "TT_ADV"])]
    assert set(hold.buyer_id) == set(over.buyer_id)
    assert not (set(hold.buyer_id) & (lc_buyers - set(over.buyer_id)))
    assert not al["action"].str.contains("15/1000").any()          # 한정 조항을 경보 문구에 쓰지 않는다



def test_alert_p4_needs_scores(ledger):
    """P4(위험 신호)는 ② 점수표가 있어야 생긴다 — 등급 하락 바이어(원장에 있는)는 모두 P4에 오른다."""
    feats = pd.read_csv(IO.FEATURES_SCORING, encoding="utf-8-sig")
    prev = pd.read_csv(IO.FEATURES_PREV, encoding="utf-8-sig") if IO.FEATURES_PREV.exists() else None
    b = MD.load_model(IO.models_dir())
    sc = MD.score_table(feats, b, prev)
    assert {"grade_prev", "grade_change", "news_risk_30d"} <= set(sc.columns)
    assert (AL.run_rules(ledger, asof=ASOF)["priority"] == "P4").sum() == 0
    al = AL.run_rules(ledger, asof=ASOF, buyers=sc, threshold=float(b.cutoffs.get("threshold", 0.5)))
    p4 = al[al.priority == "P4"]
    assert len(p4) > 0 and set(p4.buyer_id) <= set(ledger.buyer_id)
    down = set(sc.loc[sc.grade_change == "down", "buyer_id"]) & set(ledger.buyer_id)
    assert down and down <= set(p4.buyer_id)

def test_dunning_mock_flow(ledger):
    q = DN.queue(ledger, ASOF)
    dr = q[q.route == "DRAFT"]
    assert {"DM3", "D15", "D30"} <= set(dr.stage_key)
    assert not dr.payment_method.isin(["LC_SIGHT", "LC_USANCE"]).any()
    flagged = set(ledger.loc[(ledger.bankruptcy_flag == 1) | (ledger.fraud_flag == 1), "invoice_id"])
    assert not (set(dr.invoice_id) & flagged)
    assert (q[q.invoice_id.isin(flagged)].route.isin(["HUMAN", "NONE"])).all()
    templates = DN.load_templates(IO.PROMPTS / "dunning_v1.md")
    assert set(templates) == {"T0", "T1", "T2", "T3", "T4"}
    log = []
    for stage in sorted(set(dr.stage_key)):
        inv = dr[dr.stage_key == stage].invoice_id.iloc[0]
        row = ledger[ledger.invoice_id == inv].iloc[0].to_dict()
        d = DN.generate(row, stage, ASOF, templates, None)
        assert not d.used_llm and d.model_alias == "mock"
        facts = DN.build_facts(row, ASOF)
        res = GR.check_draft(d.subject, d.body, stage, facts, row["contact_email"], now=CLASS_TIME)
        assert GR.passed(res), (stage, res)
        assert GR.word_count(d.body) <= {"DM3": 80, "D7": 120, "D15": 150, "D30": 170, "PRE": 140}[stage] + 25
        AU.new_entry(log, learner_id="L07", buyer_id=row["buyer_id"], invoice_no=inv, template_stage=stage,
                     draft_hash=AU.draft_hash(d.body), guardrail_result=GR.summary_text(res), decision="approve", approver="홍길동")
    # 이관 사전 통지(T4): 사람이 이관을 결정한 D+30 건
    d30 = ledger[(ledger.dpd >= 30) & (ledger.dpd < 45) & (ledger.bankruptcy_flag == 0) & (ledger.fraud_flag == 0)
                 & ~ledger.payment_method.isin(["LC_SIGHT", "LC_USANCE"])].iloc[0].to_dict()
    d30["escalation_approved"] = "Y"
    assert DN.route(d30, ASOF)["stage_key"] == "PRE"
    pre = DN.generate(d30, "PRE", ASOF, templates, None)
    assert GR.passed(GR.check_draft(pre.subject, pre.body, "PRE", DN.build_facts(d30, ASOF), d30["contact_email"], now=CLASS_TIME))
    # 가드레일이 막아야 하는 것
    row = ledger[ledger.invoice_id == dr.invoice_id.iloc[0]].iloc[0].to_dict()
    d = DN.generate(row, dr.stage_key.iloc[0], ASOF, templates, None)
    facts = DN.build_facts(row, ASOF)
    bad = d.body + "\nOtherwise our lawyer will start legal action and report you to the police."
    r = GR.check_draft(d.subject, bad, dr.stage_key.iloc[0], facts, row["contact_email"], now=CLASS_TIME)
    assert not r[0]["ok"] and "lawyer" in r[0]["detail"]
    assert not GR.check_draft(d.subject, d.body + "\nPlease pay to our new bank account.", dr.stage_key.iloc[0], facts,
                              row["contact_email"], now=CLASS_TIME)[0]["ok"]
    assert not GR.check_draft(d.subject, d.body, dr.stage_key.iloc[0], facts, "someone@other.com", now=CLASS_TIME)[3]["ok"]
    night = datetime(2026, 10, 20, 22, 30, tzinfo=ZoneInfo("Asia/Seoul"))
    assert not GR.check_draft(d.subject, d.body, dr.stage_key.iloc[0], facts, row["contact_email"], now=night)[4]["ok"]
    assert not GR.blocked_terms("This is a courtesy reminder about the issue of payment.")   # courtesy·issue 오탐 없음
    # 감사로그 CSV
    raw = AU.to_csv_bytes(log)
    assert raw[:3] == b"\xef\xbb\xbf"
    df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
    assert list(df.columns) == AU.AUDIT_FIELDS and len(df) == len(log) and (df.sent_at == "NA(Draft-only)").all()


def test_rag_goldset():
    gold = pd.read_csv(IO.GOLDSET, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    retr = RG.Retriever(RG.load_corpus(IO.RAG_CORPUS))
    assert sum(1 for c in retr.chunks if c.cid.startswith("HB-") and c.cid[3:].isdigit()) == 35
    res = RG.run_goldset(gold, retr).set_index("q_id")
    assert res.loc["Q19", "abstained"] == "Y" and res.loc["Q20", "abstained"] == "Y"
    for q in ("Q07", "Q08", "Q15", "Q16", "Q18"):
        assert res.loc[q, "hit3"] == 1, q
        assert res.loc[q, "abstained"] == "N", q
    assert res.loc["Q07", "r1"] == "HB-27"                          # 충돌 조항 ①이 1순위
    ans, abst, _ = RG.answer_mock("사내 규정상 C등급 바이어에게 허용되는 결제조건은?", retr.search("사내 규정상 C등급 바이어에게 허용되는 결제조건은?"), retr.corpus_text)
    assert not abst and "제10조" in ans and "선수금 또는 신용장" in ans
    s = RG.goldset_summary(res.reset_index())
    assert s["abstain_accuracy"] == 1.0 and s["hit_at_3"] >= 0.4
    # LLM 답 검사: 기권 · 인용 있음 · 근거 약한 질문에 답하면 경고
    q = "사내 규정상 C등급 바이어에게 허용되는 결제조건은?"
    assert RG.check_llm_answer(q, RG.ABSTAIN, retr.search(q), retr.corpus_text) == ("기권", "")
    assert RG.check_llm_answer(q, "선수금 또는 신용장만 허용 [가상 규정 제10조 제2항]", retr.search(q), retr.corpus_text) == ("인용 있음", "")
    off = "2026년 회사 워크숍 장소는 어디인가요?"
    chk, warn = RG.check_llm_answer(off, "워크숍은 본사에서 한다 [가상 규정 제20조]", retr.search(off), retr.corpus_text)
    assert chk == "인용 있음" and "근거가 약하다" in warn
    assert RG.check_llm_answer(q, "선수금만 허용", retr.search(q), retr.corpus_text)[0] == "인용 없음"


def test_overview_kpis_and_buyer_table(ledger):
    """⓪ 상황판: KPI는 원장·④ 규칙에서 독립적으로 센 값과 같고, 바이어 표는 경보 우선 → 연체 금액 순이다."""
    al = AL.run_rules(ledger, asof=ASOF)
    k = OV.kpis(ledger, al, ASOF)
    amt = ledger["open_amount_usd"].fillna(ledger["amount_usd"])
    assert k["asof"] == "2026-09-30" and k["open_count"] == len(ledger) and k["buyers"] == ledger["buyer_id"].nunique()
    assert abs(k["open_usd"] - amt.sum()) < 0.01
    assert abs(k["overdue_usd"] - amt[ledger["dpd"] > 0].sum()) < 0.01
    hold = ~ledger["payment_method"].isin(["LC_SIGHT", "LC_USANCE", "TT_ADV"]) & (ledger["dpd"] > 30)
    assert k["hold_count"] == int(hold.sum()) and k["hold_buyers"] == ledger.loc[hold, "buyer_id"].nunique()
    assert k["hold_buyers"] == k["p2_hold"]                          # ④ P2 '선적 보류선'은 바이어당 1건
    cnt = AL.summary(al)
    assert (k["p1"], k["p2"], k["p3"], k["p4"]) == (cnt["P1"], cnt["P2"], cnt["P3"], cnt["P4"]) and cnt["P4"] == 0
    assert k["p1"] == k["p1_bankrupt"] + k["p1_fraud"] and k["p2"] == k["p2_hold"] + k["p2_notice"] + k["p2_notice_late"]
    notice = al[al["rule"] == "사고발생통지 기한"]
    assert k["notice_min_days"] == int(notice["days"].min()) and k["notice_invoice"] in set(notice["invoice_id"])
    q = DN.queue(ledger, ASOF)
    assert k["draft"] == int((q["route"] == "DRAFT").sum()) and k["human"] == int((q["route"] == "HUMAN").sum())
    # 바이어 표: 원장 바이어 전부 한 줄씩, P1 → P2 → P3 → P4 → 없음 순, 같은 등급 안에서 연체 금액 큰 순
    bt = OV.buyer_table(ledger, al)
    assert len(bt) == ledger["buyer_id"].nunique() and bt["buyer_id"].is_unique and list(bt["rank"]) == list(range(1, len(bt) + 1))
    rank = bt["top_priority"].map({"P1": 1, "P2": 2, "P3": 3, "P4": 4}).fillna(9)
    assert rank.is_monotonic_increasing
    for _, g in bt.groupby(rank):
        assert g["overdue_usd"].is_monotonic_decreasing
    bk = set(ledger.loc[ledger.bankruptcy_flag == 1, "buyer_id"])
    fraud = set(ledger.loc[ledger.fraud_flag == 1, "buyer_id"])
    assert set(bt[bt["top_priority"] == "P1"]["buyer_id"]) == bk | fraud
    assert all("파산·부도" in s for s in bt[bt["buyer_id"].isin(bk)]["signals"])
    assert abs(bt["open_usd"].sum() - k["open_usd"]) < 0.01
    # ② 점수표가 있으면 등급·pd_30d는 점수표 값, P4가 생긴다
    feats = pd.read_csv(IO.FEATURES_SCORING, encoding="utf-8-sig")
    b = MD.load_model(IO.models_dir())
    sc = MD.score_table(feats, b, pd.read_csv(IO.FEATURES_PREV, encoding="utf-8-sig") if IO.FEATURES_PREV.exists() else None)
    al2 = AL.run_rules(ledger, asof=ASOF, buyers=sc, threshold=float(b.cutoffs.get("threshold", 0.5)))
    bt2 = OV.buyer_table(ledger, al2, sc).set_index("buyer_id")
    assert OV.kpis(ledger, al2, ASOF)["p4"] == AL.summary(al2)["P4"] > 0
    assert (bt2["pd_30d"] - sc.set_index("buyer_id")["pd_30d"].reindex(bt2.index)).abs().max() < 1e-9
    assert OV.usd_short(4_275_410.9) == "$4.28M" and OV.usd_short(233_455) == "$233K" and OV.usd_short(None) == "–"


def test_policy_caps_match_day4_workbook():
    """D9: 가상 규정 별표2 한도 상한 = 앱 기본값 = Day4 워크북 Cap(A US$200,000 · B US$100,000 · C 0, S는 필요한도까지 = 상한 없음)."""
    import re
    md = (IO.RAG_CORPUS / "hanbit_credit_policy.md").read_text(encoding="utf-8")
    table = md.split("## 별표2", 1)[1].split("\n## ", 1)[0]
    caps = {}
    for line in table.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] in ("S", "A", "B", "C"):
            usd = re.search(r"US\$\s*([\d,]+)", cells[2])
            caps[cells[0]] = int(usd.group(1).replace(",", "")) if usd else (0 if cells[2].startswith("0") else None)
    assert caps == {"S": None, "A": 200_000, "B": 100_000, "C": 0}
    assert {g: LM.DEFAULT_PARAMS["cap"][g] for g in "SABC"} == caps
    if IO.PARAMS.exists():                                           # Day4 파일이 있으면 워크북(01_Params)과 같은 값인지도 본다
        pr = pd.read_csv(IO.PARAMS, encoding="utf-8-sig").set_index("excel_name")["value"]
        assert (pr["Cap_A"], pr["Cap_B"], pr["Cap_C_OA"]) == (200_000, 100_000, 0)

