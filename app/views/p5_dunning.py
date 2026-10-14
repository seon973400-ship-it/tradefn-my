"""⑤ 독촉메일 — 톤 사다리(D-3 · D+7 · D+15 · D+30 · 이관 사전 통지) 영문 초안 → 가드레일 → 사람 승인 → 감사로그.

LLM: Secrets [llm]이 있으면 LiteLLM 프록시(OpenAI 호환)로 초안, 없으면 모의 모드(템플릿 초안).
발송하지 않는다(Draft-only): 승인하면 감사로그에 남고 .txt로 내려받아 메일 프로그램에 붙여 넣는다.
제외: 신용장(은행 채널) · 선수금 · 파산·사기 신호(사람 처리) · D+45 이후(최고장·추심 위임은 사람이 작성) · 이미 보낸 단계
"""
import pandas as pd
import streamlit as st

import ui
from core import audit as AU
from core import data_io as IO
from core import dunning as DN
from core import guardrails as GR

st.title("⑤ 독촉메일")
st.caption("AI는 초안만 만든다. 가드레일을 모두 통과해야 [승인]이 열리고, 승인해도 메일은 보내지지 않는다(Draft-only).")
L = ui.need_ledger()
if L is None:
    st.stop()
asof = ui.asof()
a = ui.app_settings()
q = DN.queue(L, asof)
with st.expander("독촉 판정표(원장 전체)", expanded=False):
    st.dataframe(q[q["route"] != "NONE"], hide_index=True, height=300)
    st.caption("DRAFT = 초안 대상 · SKIP = 이미 보낸 단계 · HUMAN = 사람 처리(파산·사기·D+45) · NONE = 대상 아님(신용장·단계 아님)")

cand = q[q["route"].isin(["DRAFT", "SKIP"])].copy()
if cand.empty:
    st.info("초안 대상이 없습니다(기준일을 바꿔 보세요).")
    st.stop()
ids = cand["invoice_id"].tolist()
target = st.session_state.get("dunning_target")
idx = ids.index(target) if target in ids else 0
label = cand.set_index("invoice_id").apply(lambda r: f"{r.name} · {r['buyer_id']} · D{int(r['dpd']):+d} · {r['stage_key']} · {r['route']}", axis=1)
inv = st.selectbox("인보이스", ids, index=idx, format_func=lambda i: label[i])
row = L[L["invoice_id"] == inv].iloc[0].to_dict()
c1, c2, c3 = st.columns(3)
row["contact_name"] = c1.text_input("담당자 이름(선택)", value=str(row.get("contact_name", "") or ""))
esc = c2.checkbox("이관 결정됨(escalation_approved = Y)", value=False, disabled=int(row["dpd"]) < 30,
                  help="D+30 이후, 사람이 보험사·추심사 이관을 결정한 건만 이관 사전 통지(T4)")
row["escalation_approved"] = "Y" if esc else ""
recipient = c3.text_input("수신자(본인 플러스 주소로 바꾸기)", value=str(row.get("contact_email", "")))
d = DN.route(row, asof)
if d["route"] == "SKIP":
    st.warning(f"이미 보낸 단계입니다 — {d['reason']}. 중복 발송 방지 규칙상 새 초안을 만들지 않습니다.")
    st.stop()
if d["route"] != "DRAFT":
    st.warning(f"초안 대상이 아닙니다 — {d['reason']}")
    st.stop()
stage = d["stage_key"]
st.markdown(f"**단계 {stage}** · {DN.STAGES[stage][2]} · 판정 이유: {d['reason']} · 등급 {row.get('grade', '')} · "
            f"부보 {row.get('ksure_insured', '')} · 미결 {row.get('currency', '')} {DN.fmt_amount(row.get('open_amount_ccy'), str(row.get('currency', '')))}")

if st.button("초안 만들기", type="primary"):
    templates = DN.load_templates(IO.PROMPTS / "dunning_v1.md")
    cfg = ui.llm_config()
    with st.spinner("초안 작성 중…"):
        dr = DN.generate(row, stage, asof, templates, cfg, a["sender"])
    if dr.tokens_in or dr.tokens_out:
        ui.log_llm(dr.model_alias, dr.model_resolved, dr.tokens_in, dr.tokens_out, f"dunning {stage} {inv}")
    st.session_state["draft"] = {"invoice_id": inv, "stage": stage, "subject": dr.subject, "body": dr.body,
                                 "summary_ko": dr.summary_ko, "banner": dr.banner, "model_alias": dr.model_alias,
                                 "model_resolved": dr.model_resolved, "tokens_in": dr.tokens_in, "tokens_out": dr.tokens_out,
                                 "original": dr.subject + "\n" + dr.body}

dr = st.session_state.get("draft")
if not dr or dr["invoice_id"] != inv:
    st.stop()
st.info(dr["banner"])
subj = st.text_input("제목", value=dr["subject"], key=f"subj_{inv}")
body = st.text_area("본문(영문) — 고쳐도 된다. 고친 내용으로 다시 검사한다", value=dr["body"], height=300, key=f"body_{inv}")
st.markdown(f"**한국어 요약**: {dr['summary_ko']}")
facts = DN.build_facts(row, asof, a["sender"])
res = GR.check_draft(subj, body, stage, facts, recipient, a["recipient_whitelist"], now=ui.now(), tz=a["send_tz"])
st.dataframe(pd.DataFrame([{"검사": r["check"], "결과": "✅" if r["ok"] else "❌", "내용": r["detail"]} for r in res]),
             hide_index=True)
ok = GR.passed(res)
edited = (subj + "\n" + body) != dr["original"]
b1, b2, b3 = st.columns([1, 1, 2])
approver = b3.text_input("승인자", value=a["approver_name"])


def _log(decision: str, reason: str = ""):
    AU.new_entry(st.session_state["audit_log"], learner_id=a["learner_id"], buyer_id=row["buyer_id"], invoice_no=inv,
                 overdue_days=int(row["dpd"]), risk_grade=row.get("grade", ""), template_stage=f"{stage}({DN.STAGES[stage][1]})",
                 model_alias=dr["model_alias"], model_resolved=dr["model_resolved"], prompt_version=DN.PROMPT_VERSION,
                 draft_hash=AU.draft_hash(subj + "\n" + body), guardrail_result=GR.summary_text(res), approver=approver,
                 decision=decision, deny_reason=reason, alert_type="dunning", tokens_in=dr["tokens_in"], tokens_out=dr["tokens_out"])


if b1.button("승인(초안 확정)", type="primary", disabled=not ok or not approver.strip()):
    _log("edit" if edited else "approve")
    st.success("승인 기록됨 — 메일은 보내지 않았습니다. 아래에서 초안을 내려받아 메일 프로그램에 붙여 넣으세요.")
reason = b2.selectbox("반려 사유", AU.DENY_REASONS, label_visibility="collapsed")
if b2.button("반려"):
    _log("deny", reason)
    st.warning(f"반려 기록됨 — {reason}")
if not ok:
    night = any(r["check"].startswith("⑤") and not r["ok"] for r in res)
    st.caption("❌ 항목을 고쳐야 승인할 수 있습니다(규칙 = app/core/guardrails.py)."
               + (" ⑤ 발송 시간창은 수신지 현지 08–21시에만 열린다 — 밤 리허설은 Secrets [app] demo_clock(README §1)." if night else ""))
st.download_button("초안 .txt 내려받기", f"To: {recipient}\nSubject: {subj}\n\n{body}\n".encode("utf-8"),
                   file_name=f"draft_{inv}_{stage}.txt", mime="text/plain", disabled=not ok)
