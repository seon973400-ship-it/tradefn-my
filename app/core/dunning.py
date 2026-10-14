"""⑤ 독촉메일 — 단계 판정(톤 사다리) · 사실값 · 프롬프트 · 모의(템플릿) 초안.

단계: DM3(D-3) · D7 · D15 · D30 · PRE(사람이 이관을 결정한 건)
- C등급은 한 단계 앞당긴다(D+7~14 → D15) [교육용 가정]
- 제외: 신용장(은행 채널) · 선수금 · 파산·사기 신호(사람 처리) · D+45 이후(최고장·추심 위임은 사람이 작성) · 이미 보낸 단계
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import llm as LLM

PROMPT_VERSION = "v1"
STAGES = {  # key: (번호, 템플릿, 한국어 이름)
    "DM3": (0, "T0", "D-3 사전 안내"), "D7": (1, "T1", "D+7 친절한 리마인더"), "D15": (2, "T2", "D+15 단호한 통지"),
    "D30": (3, "T3", "D+30 최종 통지·선적 보류"), "PRE": (4, "T4", "이관 사전 통지(사람 결정 건)")}
LC = ("LC_SIGHT", "LC_USANCE")
DEFAULT_SENDER = {"company_name": "Hanbit Precision Co., Ltd. (fictional)", "sender_name": "Credit Team",
                  "sender_title": "Accounts Receivable", "account_manager": "your account manager"}


def load_templates(path: Path) -> dict[str, str]:
    """dunning_v1.md의 '## T0 …' 절마다 첫 번째 ```text 블록."""
    text = Path(path).read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^## (T\d)\b.*?\n```text\n(.*?)\n```", text, flags=re.S | re.M):
        out[m.group(1)] = m.group(2).strip()
    return out


def _num(v, default=None):
    try:
        if v is None or pd.isna(v):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def route(row, asof) -> dict:
    """원장 한 행 → {route, stage_key, stage_no, template, reason}. route: DRAFT · HUMAN · SKIP · NONE."""
    asof = pd.Timestamp(asof)
    pm = str(row.get("payment_method", ""))
    due = row.get("due_date")
    if pm in LC:
        return {"route": "NONE", "stage_key": None, "stage_no": None, "template": None, "reason": "신용장 — 은행 채널 확인(메일 독촉 안 함)"}
    if pm == "TT_ADV":
        return {"route": "NONE", "stage_key": None, "stage_no": None, "template": None, "reason": "선수금 — 독촉 대상 아님"}
    if due is None or pd.isna(due):
        return {"route": "NONE", "stage_key": None, "stage_no": None, "template": None, "reason": "결제기일 빈칸 — 확인 필요"}
    if int(_num(row.get("bankruptcy_flag"), 0) or 0) == 1 or int(_num(row.get("fraud_flag"), 0) or 0) == 1:
        return {"route": "HUMAN", "stage_key": None, "stage_no": None, "template": None, "reason": "파산·사기 신호 — 사람 처리(AI 초안 금지)"}
    dpd = int((asof - pd.Timestamp(due)).days)
    grade = str(row.get("grade", ""))
    esc = str(row.get("escalation_approved", "")).strip().upper() == "Y"
    key = None
    if dpd >= 30 and esc:
        key = "PRE"
    elif dpd >= 45:
        return {"route": "HUMAN", "stage_key": None, "stage_no": None, "template": None,
                "reason": f"D+{dpd} — D+45 이후 최고장·추심 위임 검토는 사람이 작성"}
    elif dpd >= 30:
        key = "D30"
    elif dpd >= 15:
        key = "D15"
    elif dpd >= 7:
        key = "D15" if grade == "C" else "D7"
    elif -3 <= dpd <= -1:
        key = "DM3"
    if key is None:
        return {"route": "NONE", "stage_key": None, "stage_no": None, "template": None, "reason": f"D{dpd:+d} — 독촉 단계 아님"}
    no, tpl, _ = STAGES[key]
    last = _num(row.get("last_dunning_stage"), None)
    if last is not None and no <= last:
        return {"route": "SKIP", "stage_key": key, "stage_no": no, "template": tpl, "reason": f"이미 보낸 단계(마지막 {int(last)})"}
    why = "C등급 한 단계 앞당김" if (key == "D15" and dpd < 15) else STAGES[key][2]
    return {"route": "DRAFT", "stage_key": key, "stage_no": no, "template": tpl, "reason": why}


def payment_terms_text(method: str, invoice_date, due_date) -> str:
    try:
        days = int((pd.Timestamp(due_date) - pd.Timestamp(invoice_date)).days)
    except Exception:
        days = None
    return {"OA": f"O/A {days} days" if days is not None else "O/A",
            "DA": f"D/A {days} days" if days is not None else "D/A",
            "DP": "D/P at sight", "TT_SPLIT_30_70": "30% T/T in advance, 70% within 30 days after B/L",
            "LC_SIGHT": "L/C at sight", "LC_USANCE": "Usance L/C", "TT_ADV": "T/T in advance"}.get(method, method or "")


def fmt_amount(v, ccy: str) -> str:
    v = _num(v, 0.0) or 0.0
    return f"{v:,.0f}" if ccy == "JPY" else f"{v:,.2f}"


def build_facts(row, asof, sender: dict | None = None) -> dict:
    asof = pd.Timestamp(asof)
    s = {**DEFAULT_SENDER, **(sender or {})}
    dpd = int((asof - pd.Timestamp(row["due_date"])).days)
    ccy = str(row.get("currency", ""))
    amt = row.get("open_amount_ccy")
    if _num(amt) is None:
        amt = row.get("amount_ccy")
    insured = "Y" if str(row.get("ksure_insured", "N")).upper() == "Y" else "N"
    contact = str(row.get("contact_name", "") or "").strip()
    return {
        "company_name": s["company_name"], "sender_name": s["sender_name"], "sender_title": s["sender_title"],
        "account_manager": s["account_manager"],
        "buyer_name": str(row.get("buyer_name", "")), "contact_name": contact or "Accounts Payable Team",
        "invoice_id": str(row["invoice_id"]), "invoice_date": pd.Timestamp(row["invoice_date"]).strftime("%Y-%m-%d"),
        "currency": ccy, "amount_ccy": fmt_amount(amt, ccy),
        "payment_terms": payment_terms_text(str(row.get("payment_method", "")), row["invoice_date"], row["due_date"]),
        "due_date": pd.Timestamp(row["due_date"]).strftime("%Y-%m-%d"), "days_overdue": str(max(dpd, 0)),
        "reply_by_date": (asof + pd.Timedelta(days=5)).strftime("%Y-%m-%d"),
        "hold_effective_date": (asof + pd.Timedelta(days=7)).strftime("%Y-%m-%d"),
        "insured": insured,
        "escalation_partner": "our export credit insurer" if insured == "Y" else "our authorised collection partner",
        "recipient": str(row.get("contact_email", "")),
    }


def render(template: str, facts: dict) -> str:
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: str(facts.get(m.group(1), "")), template)


def mock_email(stage: str, f: dict) -> tuple[str, str, str]:
    """LLM 없이 만드는 초안(가드레일 통과하도록 템플릿 규칙 그대로). 반환: subject, body, summary_ko."""
    sign = f"\n\nKind regards,\n{f['sender_name']}\n{f['sender_title']}, {f['company_name']}"
    bank = "Please use only the bank details on the original invoice."
    amt = f"{f['currency']} {f['amount_ccy']}"
    if stage == "DM3":
        subj = f"Friendly reminder: Invoice {f['invoice_id']} due on {f['due_date']}"
        body = (f"Dear {f['contact_name']},\n\nThis is a friendly reminder that invoice {f['invoice_id']} for {amt} "
                f"is due on {f['due_date']}. {bank}\n\nIf payment has already been arranged, please disregard this message.")
        ko = f"{f['buyer_name']} {f['invoice_id']} {amt} — 결제기일 {f['due_date']} 사전 안내(D-3)."
    elif stage == "D7":
        subj = f"Payment reminder: Invoice {f['invoice_id']}"
        body = (f"Dear {f['contact_name']},\n\nWe may have missed your remittance for invoice {f['invoice_id']} dated "
                f"{f['invoice_date']} ({amt}, terms {f['payment_terms']}, due {f['due_date']}). It is now "
                f"{f['days_overdue']} days past due, and the payment may still be in transit.\n\nCould you please let us know "
                f"the expected payment date or share a remittance copy (e.g., SWIFT MT103)? {bank}\n\n"
                f"If payment has already been made, please disregard this message.")
        ko = f"{f['buyer_name']} {f['invoice_id']} {amt} — {f['days_overdue']}일 지남, 친절한 리마인더(입금 예정일 확인 요청)."
    elif stage == "D15":
        subj = f"Overdue notice: Invoice {f['invoice_id']} ({f['days_overdue']} days)"
        body = (f"Dear {f['contact_name']},\n\nInvoice {f['invoice_id']} dated {f['invoice_date']} for {amt} "
                f"(terms {f['payment_terms']}, due {f['due_date']}) is now {f['days_overdue']} days overdue. "
                f"A friendly reminder was sent earlier.\n\nPlease confirm the payment date in writing by {f['reply_by_date']}. "
                f"We are happy to resend the invoice and a copy of the B/L. If there is any issue with quantity, quality or "
                f"documents, please tell us now so that we can resolve it quickly.\n\nOur account manager, {f['account_manager']}, "
                f"is copied on this email. {bank}")
        ko = f"{f['buyer_name']} {f['invoice_id']} {amt} — {f['days_overdue']}일 연체, {f['reply_by_date']}까지 지급일 서면 회신 요청(영업 담당 참조)."
    elif stage == "D30":
        ins = (" The outstanding amount will be handled in accordance with the terms of our export credit insurance policy."
               if f["insured"] == "Y" else "")
        subj = f"Final notice: Invoice {f['invoice_id']}"
        body = (f"Dear {f['contact_name']},\n\nThis is a final notice for invoice {f['invoice_id']} dated {f['invoice_date']} "
                f"for {amt}, which was due on {f['due_date']} and is now {f['days_overdue']} days overdue. Reminders were sent "
                f"at 7 and 15 days overdue.\n\nUnless payment is received or a written payment plan is agreed by "
                f"{f['reply_by_date']}, further shipments will be placed on hold effective {f['hold_effective_date']}.{ins}\n\n"
                f"Please call or reply today so that we can agree a payment plan. We value our relationship and would like "
                f"to resolve this together. {bank}")
        ko = (f"{f['buyer_name']} {f['invoice_id']} {amt} — {f['days_overdue']}일 연체 최종 통지, {f['hold_effective_date']}부터 "
              f"선적 보류 예고" + (", 보험 약관에 따른 처리 문장 포함." if f["insured"] == "Y" else "."))
    else:  # PRE
        subj = f"Pre-escalation notice: Invoice {f['invoice_id']}"
        body = (f"Dear {f['contact_name']},\n\nInvoice {f['invoice_id']} for {amt}, due on {f['due_date']}, is now "
                f"{f['days_overdue']} days overdue, and shipments to your company are on hold.\n\nUnless full payment or a "
                f"signed payment plan is received by {f['reply_by_date']}, the account will be referred to "
                f"{f['escalation_partner']} for further handling.\n\nIf you dispute any part of this invoice, please reply to "
                f"this email or contact {f['account_manager']} before that date. {bank}")
        ko = f"{f['buyer_name']} {f['invoice_id']} {amt} — 사람이 이관을 결정한 건, {f['reply_by_date']}까지 미지급 시 {f['escalation_partner']} 이관 예고."
    return subj, body + sign, ko


@dataclass
class Draft:
    subject: str
    body: str
    summary_ko: str
    stage: str
    template: str
    used_llm: bool
    model_alias: str
    model_resolved: str
    tokens_in: int
    tokens_out: int
    banner: str


def generate(row, stage: str, asof, templates: dict, llm_cfg: LLM.LLMConfig | None, sender: dict | None = None) -> Draft:
    f = build_facts(row, asof, sender)
    tpl = STAGES[stage][1]
    if llm_cfg is not None and tpl in templates:
        prompt = render(templates[tpl], f)
        res = LLM.chat(llm_cfg, [{"role": "user", "content": prompt}])
        if res.ok:
            obj = LLM.extract_json(res.text)
            if obj and obj.get("subject") and obj.get("body"):
                return Draft(str(obj["subject"]), str(obj["body"]), str(obj.get("summary_ko", "")), stage, tpl, True,
                             res.model_alias, res.model_resolved, res.tokens_in, res.tokens_out,
                             "LLM 초안" + (" (예비 모델)" if res.used_fallback else ""))
            banner = "LLM 응답이 JSON 형식이 아니어서 템플릿 초안으로 바꿨습니다"
        else:
            banner = f"LLM 호출 실패 → 템플릿 초안(LLM 미사용): {res.error[:120]}"
        s, b, k = mock_email(stage, f)
        return Draft(s, b, k, stage, tpl, False, res.model_alias or llm_cfg.default_model, "", res.tokens_in, res.tokens_out, banner)
    s, b, k = mock_email(stage, f)
    return Draft(s, b, k, stage, tpl, False, "mock", "template", 0, 0, "모의 모드 — LLM 미사용 초안(템플릿)")


def queue(ledger: pd.DataFrame, asof) -> pd.DataFrame:
    """원장 전체의 독촉 판정표(앱 ⑤ 목록 · 강사 기대값 대조용)."""
    rows = []
    for _, r in ledger.iterrows():
        d = route(r, asof)
        dpd = int((pd.Timestamp(asof) - pd.Timestamp(r["due_date"])).days) if pd.notna(r.get("due_date")) else None
        rows.append({"invoice_id": r["invoice_id"], "buyer_id": r["buyer_id"], "buyer_name": r.get("buyer_name", ""),
                     "dpd": dpd, "grade": r.get("grade", ""), "payment_method": r.get("payment_method", ""),
                     "last_dunning_stage": r.get("last_dunning_stage"), **d})
    return pd.DataFrame(rows)
