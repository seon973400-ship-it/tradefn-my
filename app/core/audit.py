"""⑦ 감사로그 — 필드 21개.

Community Cloud 저장소는 휘발성이라 로그는 세션에만 있다 → 세션이 끝나기 전에 CSV로 내려받는다.
"""
from __future__ import annotations

import hashlib
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

AUDIT_FIELDS = ["log_id", "timestamp_kst", "learner_id", "buyer_id", "invoice_no", "overdue_days", "risk_grade",
                "template_stage", "model_alias", "model_resolved", "prompt_version", "draft_hash", "guardrail_result",
                "approver", "decision", "deny_reason", "sent_at", "message_id", "alert_type", "tokens_in", "tokens_out"]
DENY_REASONS = ["금액 오류", "톤 부적절", "이미 입금", "분쟁 확인 중", "기타"]


def draft_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")


def new_entry(log: list[dict], learner_id: str = "", **kw) -> dict:
    e = {k: "" for k in AUDIT_FIELDS}
    e.update({"log_id": f"{learner_id or 'L00'}-{len(log) + 1:04d}", "timestamp_kst": now_kst(), "learner_id": learner_id,
              "sent_at": "NA(Draft-only)", "message_id": "NA"})
    for k, v in kw.items():
        if k in e:
            e[k] = v
    log.append(e)
    return e


def to_frame(log: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(log, columns=AUDIT_FIELDS)


def to_csv_bytes(log: list[dict]) -> bytes:
    buf = io.StringIO()
    to_frame(log).to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode("utf-8-sig")
