#!/usr/bin/env python
"""Day5 에이전트 파일 — n8n 독촉 워크플로 JSON · Dify RAG 앱 DSL을 한 원문(app/prompts/*.md · agents/n8n/code/*.js)에서 만든다.
(v3 — 5일차 v4에서는 쓰지 않는다. 돌리면 agents/n8n · agents/dify가 되살아난다. 사본: instructor/day5/lab_v3_archive/agents_v3/)

사용(저장소 루트):
    python tools/build_day5_agents.py            # agents/n8n/dunning_workflow_v1.json · agents/dify/hanbit_policy_rag_v1.yml 생성 + 검사
    python tools/build_day5_agents.py --check    # 생성하지 않고 검사만(Node.js가 있으면 Code 노드 JS를 실제로 돌려 앱 규칙과 대조)
(v3 — 이번 과정은 쓰지 않는다) n8n 노드 15 · Dify KB · Chatflow · 화이트리스트 · 금지 문구 · 발송 시간 · C등급 앞당김 · 템플릿 4종.
- 프롬프트 원문은 app/prompts/dunning_v1.md(T0~T4) · rag_system_v1.md(P5-1) 하나다 → 앱과 n8n·Dify가 같은 문장을 쓴다.
- 자격증명(Google Sheets·Gmail·OpenAI 호환)은 넣지 않는다 — 가져온 뒤 각자 연결한다(agents/README.md).
- 노드 id는 이름에서 만든 고정 UUID(uuid5)라 다시 만들어도 같은 파일이 나온다.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
APP = REPO / "app"
AG = REPO / "agents"
N8N_OUT = AG / "n8n" / "dunning_workflow_v1.json"
DIFY_OUT = AG / "dify" / "hanbit_policy_rag_v1.yml"
NS = uuid.UUID("6f1c2d8e-5d0a-4c7e-9a52-2f3b8c1d0e5a")
SHEET_DOC = {"__rl": True, "value": "", "mode": "list", "cachedResultName": "TF_AR_Ledger"}
AUDIT_FIELDS = ["log_id", "timestamp_kst", "learner_id", "buyer_id", "invoice_no", "overdue_days", "risk_grade",
                "template_stage", "model_alias", "model_resolved", "prompt_version", "draft_hash", "guardrail_result",
                "approver", "decision", "deny_reason", "sent_at", "message_id", "alert_type", "tokens_in", "tokens_out"]
STAGES = [("PRE", "T4", "T4 이관 사전 통지"), ("D30", "T3", "T3 D+30 최종 통지"), ("D15", "T2", "T2 D+15 단호한 통지"),
          ("D7", "T1", "T1 D+7 리마인더"), ("DM3", "T0", "T0 D-3 사전 안내")]


def nid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def templates() -> dict[str, str]:
    text = (APP / "prompts" / "dunning_v1.md").read_text(encoding="utf-8")
    out = {m.group(1): m.group(2).strip() for m in re.finditer(r"^## (T\d)\b.*?\n```text\n(.*?)\n```", text, flags=re.S | re.M)}
    assert set(out) == {"T0", "T1", "T2", "T3", "T4"}, out.keys()
    return out


def rag_prompt() -> str:
    t = (APP / "prompts" / "rag_system_v1.md").read_text(encoding="utf-8")
    return re.search(r"```text\n(.*?)\n```", t, flags=re.S).group(1).strip()


def n8n_expr(tpl: str) -> str:
    """{{buyer_name}} → {{ $json.facts.buyer_name }} (n8n 식). 맨 앞 '=' = 식 모드."""
    return "=" + re.sub(r"\{\{\s*(\w+)\s*\}\}", r"{{ $json.facts.\1 }}", tpl)


def cond(left: str, op_type: str, op: str, right=None, cid: str = "c") -> dict:
    c = {"id": nid(cid), "leftValue": left, "operator": {"type": op_type, "operation": op}}
    if op_type == "boolean":
        c["operator"]["singleValue"] = True
    else:
        c["rightValue"] = right
    return c


def if_node(name: str, conditions: list[dict], pos, combinator: str = "and") -> dict:
    return {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                          "conditions": conditions, "combinator": combinator}, "options": {}},
            "id": nid(name), "name": name, "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": pos}


def sheets_read(name: str, sheet: str, pos, execute_once: bool = False) -> dict:
    n = {"parameters": {"operation": "read", "documentId": SHEET_DOC,
                        "sheetName": {"__rl": True, "value": sheet, "mode": "name"}, "options": {}},
         "id": nid(name), "name": name, "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": pos}
    if execute_once:
        n["executeOnce"] = True
    return n


def audit_append(name: str, decision: str, pos, src: str = "가드레일", extra: dict | None = None) -> dict:
    """Audit_Log 탭에 03 Part1 §7.7 21필드 한 줄."""
    j = f"$('{src}').item.json"
    val = {
        "log_id": "={{ $execution.id }}-" + "{{ " + j + ".invoice_id || " + j + ".buyer_id }}",
        "timestamp_kst": "={{ $now.setZone('Asia/Seoul').toFormat('yyyy-LL-dd HH:mm:ss') }}",
        "learner_id": "={{ " + j + ".learner_id }}", "buyer_id": "={{ " + j + ".buyer_id }}",
        "invoice_no": "={{ " + j + ".invoice_id || " + j + ".invoices }}", "overdue_days": "={{ " + j + ".dpd ?? '' }}",
        "risk_grade": "={{ " + j + ".grade ?? '' }}", "template_stage": "={{ " + j + ".stage_key ?? 'HUMAN' }}",
        "model_alias": "={{ " + j + ".model_alias }}", "model_resolved": "",
        "prompt_version": "={{ " + j + ".prompt_version }}-{{ " + j + ".template ?? '' }}",
        "draft_hash": "={{ " + j + ".draft_hash ?? '' }}", "guardrail_result": "={{ " + j + ".guardrail_result ?? '' }}",
        "approver": "={{ " + j + ".approver_email }}", "decision": decision, "deny_reason": "", "sent_at": "",
        "message_id": "", "alert_type": "dunning", "tokens_in": "", "tokens_out": ""}
    val.update(extra or {})
    schema = [{"id": f, "displayName": f, "required": False, "defaultMatch": False, "display": True, "type": "string",
               "canBeUsedToMatch": True} for f in AUDIT_FIELDS]
    return {"parameters": {"operation": "append", "documentId": SHEET_DOC,
                           "sheetName": {"__rl": True, "value": "Audit_Log", "mode": "name"},
                           "columns": {"mappingMode": "defineBelow", "value": val, "matchingColumns": [], "schema": schema},
                           "options": {}},
            "id": nid(name), "name": name, "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": pos}


def gmail_send(name: str, to: str, subject: str, message: str, pos) -> dict:
    return {"parameters": {"sendTo": to, "subject": subject, "emailType": "text", "message": message,
                           "options": {"appendAttribution": False}},
            "id": nid(name), "name": name, "type": "n8n-nodes-base.gmail", "typeVersion": 2.1, "position": pos,
            "webhookId": nid(name + "-hook")}


def sticky(name: str, content: str, pos, w=380, h=220, color=7) -> dict:
    return {"parameters": {"content": content, "width": w, "height": h, "color": color}, "id": nid(name), "name": name,
            "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": pos}


def build_n8n() -> dict:
    T = templates()
    stage_js = (AG / "n8n" / "code" / "stage_logic.js").read_text(encoding="utf-8")
    guard_js = (AG / "n8n" / "code" / "guardrail.js").read_text(encoding="utf-8")
    G = "$('가드레일').item.json"
    nodes = [
        sticky("메모: 이 워크플로는", "## 한빛 독촉 워크플로 v1 (Draft-only)\n가져온 뒤: ① Google Sheets·Gmail 자격증명 연결 ② `TF_AR_Ledger` 시트 선택(노드 4개) "
               "③ 'LLM 모델' 노드 5개에 LiteLLM 가상 키(OpenAI 호환 자격증명, Base URL) 또는 Gateway credits ④ Settings → Timezone = Asia/Seoul.\n"
               "**메일은 바이어에게 가지 않는다** — 승인 요청은 Config approver_email(본인)에게, 승인 뒤에는 Gmail **임시보관함 초안**만 만든다.",
               [-80, -420], w=560, h=230, color=4),
        {"parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * 1-5"}]}},
         "id": nid("평일 09:00"), "name": "평일 09:00", "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2,
         "position": [0, -120]},
        {"parameters": {}, "id": nid("수동 실행(수업)"), "name": "수동 실행(수업)", "type": "n8n-nodes-base.manualTrigger",
         "typeVersion": 1, "position": [0, 80]},
        sheets_read("Config 읽기", "Config", [240, 0]),
        sheets_read("AR_Ledger 읽기", "AR_Ledger", [480, 0], execute_once=True),
        {"parameters": {"mode": "runOnceForAllItems", "jsCode": stage_js}, "id": nid("단계 판정"), "name": "단계 판정",
         "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [720, 0]},
        if_node("사람 처리?", [cond("={{ $json.route }}", "string", "equals", "HUMAN", "c-human")], [960, 0]),
        gmail_send("사람 처리 알림(내부)", "={{ $json.approver_email }}",
                   "=[사람 처리] {{ $json.buyer_id }} {{ $json.buyer_name }}",
                   "=AI 독촉 초안을 만들지 않은 바이어입니다 — 담당자가 직접 처리하세요.\n바이어: {{ $json.buyer_id }} {{ $json.buyer_name }}\n"
                   "이유: {{ $json.reason }}\n신호: {{ $json.fraud_type }}\n인보이스: {{ $json.invoices }}\n"
                   "파산·부도: 신규 선적 중단 · 사고발생통지·보험금 청구 검토 / 사기 신호: 입금 계좌 변경 금지 · 기존 연락처로 전화 확인", [1200, -260]),
        audit_append("감사로그: 사람 처리", "human_required", [1440, -260], src="단계 판정"),
        if_node("화이트리스트?", [cond("={{ $json.whitelist_ok }}", "boolean", "true", None, "c-wl")], [1200, 60]),
        audit_append("감사로그: 수신자 차단", "blocked_whitelist", [1440, 260], src="단계 판정"),
        {"parameters": {"rules": {"values": [
            {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 2},
                            "conditions": [cond("={{ $json.stage_key }}", "string", "equals", key, f"c-sw-{key}")], "combinator": "and"},
             "renameOutput": True, "outputKey": key} for key, _, _ in STAGES]},
            "options": {"fallbackOutput": "extra", "renameFallbackOutput": "대상 아님"}},
         "id": nid("단계 분기"), "name": "단계 분기", "type": "n8n-nodes-base.switch", "typeVersion": 3.2, "position": [1440, 40]},
    ]
    conns = {
        "평일 09:00": {"main": [[{"node": "Config 읽기", "type": "main", "index": 0}]]},
        "수동 실행(수업)": {"main": [[{"node": "Config 읽기", "type": "main", "index": 0}]]},
        "Config 읽기": {"main": [[{"node": "AR_Ledger 읽기", "type": "main", "index": 0}]]},
        "AR_Ledger 읽기": {"main": [[{"node": "단계 판정", "type": "main", "index": 0}]]},
        "단계 판정": {"main": [[{"node": "사람 처리?", "type": "main", "index": 0}]]},
        "사람 처리?": {"main": [[{"node": "사람 처리 알림(내부)", "type": "main", "index": 0}],
                             [{"node": "화이트리스트?", "type": "main", "index": 0}]]},
        "사람 처리 알림(내부)": {"main": [[{"node": "감사로그: 사람 처리", "type": "main", "index": 0}]]},
        "화이트리스트?": {"main": [[{"node": "단계 분기", "type": "main", "index": 0}],
                               [{"node": "감사로그: 수신자 차단", "type": "main", "index": 0}]]},
        "단계 분기": {"main": []},
    }
    y0 = -360
    for i, (key, tpl, title) in enumerate(STAGES):
        y = y0 + i * 190
        chain = f"초안 {title}"
        model = f"LLM 모델 {key}"
        nodes.append({"parameters": {"promptType": "define", "text": n8n_expr(T[tpl]), "hasOutputParser": False},
                      "id": nid(chain), "name": chain, "type": "@n8n/n8n-nodes-langchain.chainLlm", "typeVersion": 1.5,
                      "position": [1720, y]})
        nodes.append({"parameters": {"model": {"__rl": True, "value": "={{ $json.model_alias }}", "mode": "id"},
                                     "options": {"baseURL": "https://<강사 LiteLLM 주소>/v1", "temperature": 0.3, "maxTokens": 600,
                                                 "timeout": 30000, "maxRetries": 1}},
                      "id": nid(model), "name": model, "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2,
                      "position": [1720, y + 150]})
        conns["단계 분기"]["main"].append([{"node": chain, "type": "main", "index": 0}])
        conns[chain] = {"main": [[{"node": "가드레일", "type": "main", "index": 0}]]}
        conns[model] = {"ai_languageModel": [[{"node": chain, "type": "ai_languageModel", "index": 0}]]}
    nodes.append({"parameters": {}, "id": nid("대상 아님"), "name": "대상 아님", "type": "n8n-nodes-base.noOp", "typeVersion": 1,
                  "position": [1720, y0 + 5 * 190]})
    conns["단계 분기"]["main"].append([{"node": "대상 아님", "type": "main", "index": 0}])
    nodes += [
        {"parameters": {"mode": "runOnceForEachItem", "jsCode": guard_js}, "id": nid("가드레일"), "name": "가드레일",
         "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [2040, 0]},
        if_node("가드레일 통과?", [cond("={{ $json.guardrail_pass }}", "boolean", "true", None, "c-guard")], [2280, 0]),
        audit_append("감사로그: 금지 문구·요소 차단", "blocked_guardrail", [2520, 260]),
        gmail_send("재작성 필요 알림(내부)", "={{ $('가드레일').item.json.approver_email }}",
                   "=[재작성 필요] {{ $('가드레일').item.json.stage_key }} {{ $('가드레일').item.json.invoice_id }}",
                   "=가드레일에 걸린 초안입니다(발송 경로 중단).\n{{ $('가드레일').item.json.checks_text }}\n\n제목: {{ $('가드레일').item.json.subject }}\n\n"
                   "{{ $('가드레일').item.json.body }}", [2760, 260]),
        if_node("발송 시간창?", [cond("={{ $json.in_window }}", "boolean", "true", None, "c-window")], [2520, -40]),
        {"parameters": {"resume": "specificTime",
                        "dateTime": "={{ $now.setZone($json.send_tz).plus({days: $now.setZone($json.send_tz).hour >= 21 ? 1 : 0})"
                                    ".set({hour: 8, minute: 0, second: 0}) }}"},
         "id": nid("08:00까지 대기"), "name": "08:00까지 대기", "type": "n8n-nodes-base.wait", "typeVersion": 1.1,
         "position": [2760, 100], "webhookId": nid("wait-hook")},
        {"parameters": {"action": "hash", "type": "SHA256", "value": "={{ $('가드레일').item.json.body }}", "dataPropertyName": "draft_hash"},
         "id": nid("초안 해시"), "name": "초안 해시", "type": "n8n-nodes-base.crypto", "typeVersion": 1, "position": [3000, -40]},
        {"parameters": {"operation": "sendAndWait", "sendTo": f"={{{{ {G}.approver_email }}}}",
                        "subject": f"=[승인요청] {{{{ {G}.stage_key }}}} {{{{ {G}.invoice_id }}}} {{{{ {G}.buyer_id }}}}",
                        "message": f"=바이어: {{{{ {G}.buyer_id }}}} {{{{ {G}.buyer_name }}}} · 등급 {{{{ {G}.grade }}}} · D+{{{{ {G}.dpd }}}} · "
                                   f"미결 {{{{ {G}.facts.currency }}}} {{{{ {G}.facts.amount_ccy }}}} · 부보 {{{{ {G}.insured }}}}\n"
                                   f"사고발생통지 기한: {{{{ {G}.ksure_notice_deadline || '해당 없음' }}}} (D-{{{{ {G}.notice_days_left ?? '-' }}}})\n"
                                   f"수신자(초안): {{{{ {G}.recipient }}}}\n가드레일:\n{{{{ {G}.checks_text }}}}\n\n"
                                   f"한국어 요약: {{{{ {G}.summary_ko }}}}\n\n제목: {{{{ {G}.subject }}}}\n\n{{{{ {G}.body }}}}\n\n"
                                   "승인하면 Gmail 임시보관함에 초안만 만든다(보내지 않음).",
                        "approvalOptions": {"values": {"approvalType": "double", "approveLabel": "승인(초안 생성)",
                                                       "disapproveLabel": "반려"}},
                        "options": {"limitWaitTime": {"values": {"limitType": "afterTimeInterval", "resumeAmount": 1, "resumeUnit": "days"}}}},
         "id": nid("승인 요청 메일(검토자)"), "name": "승인 요청 메일(검토자)", "type": "n8n-nodes-base.gmail", "typeVersion": 2.1,
         "position": [3240, -40], "webhookId": nid("approve-hook")},
        if_node("승인?", [cond("={{ $json.data.approved }}", "boolean", "true", None, "c-approved")], [3480, -40]),
        {"parameters": {"resource": "draft", "operation": "create", "subject": f"={{{{ {G}.subject }}}}", "emailType": "text",
                        "message": f"={{{{ {G}.body }}}}", "options": {"sendTo": f"={{{{ {G}.recipient }}}}"}},
         "id": nid("Gmail 초안 만들기"), "name": "Gmail 초안 만들기", "type": "n8n-nodes-base.gmail", "typeVersion": 2.1,
         "position": [3720, -140]},
        audit_append("감사로그: 승인", "approve", [3960, -140],
                     extra={"draft_hash": "={{ $('초안 해시').item.json.draft_hash }}", "message_id": "={{ $json.id }}"}),
        {"parameters": {"operation": "update", "documentId": SHEET_DOC, "sheetName": {"__rl": True, "value": "AR_Ledger", "mode": "name"},
                        "columns": {"mappingMode": "defineBelow",
                                    "value": {"invoice_id": f"={{{{ {G}.invoice_id }}}}",
                                              "last_dunning_stage": f"={{{{ {G}.stage_no >= 4 ? 3 : {G}.stage_no }}}}",
                                              "last_dunning_date": f"={{{{ {G}.as_of }}}}",
                                              "ship_hold": f"={{{{ {G}.stage_key === 'D30' || {G}.stage_key === 'PRE' ? 'Y' : '' }}}}"},
                                    "matchingColumns": ["invoice_id"],
                                    "schema": [{"id": c, "displayName": c, "required": False, "defaultMatch": c == "invoice_id",
                                                "display": True, "type": "string", "canBeUsedToMatch": True}
                                               for c in ("invoice_id", "last_dunning_stage", "last_dunning_date", "ship_hold")]},
                        "options": {}},
         "id": nid("원장 갱신"), "name": "원장 갱신", "type": "n8n-nodes-base.googleSheets", "typeVersion": 4.5, "position": [4200, -140]},
        if_node("D+30?", [cond(f"={{{{ {G}.stage_key }}}}", "string", "equals", "D30", "c-d30")], [4440, -140]),
        gmail_send("에스컬레이션 알림(내부)", f"={{{{ {G}.approver_email }}}}",
                   f"=[D+30 에스컬레이션] {{{{ {G}.buyer_id }}}} {{{{ {G}.invoice_id }}}}",
                   f"=D+30 최종 통지 초안 승인 · 선적 보류(ship_hold = Y) · 한도 동결 제안(사람 검토).\n"
                   f"K-SURE 사고발생통지 기한 = 결제기일 + 1개월: {{{{ {G}.ksure_notice_deadline || '부보 아님' }}}} — 통지 여부는 사람이 결정한다.\n"
                   f"바이어: {{{{ {G}.buyer_id }}}} {{{{ {G}.buyer_name }}}} · D+{{{{ {G}.dpd }}}}", [4680, -140]),
        audit_append("감사로그: 반려", "deny", [3720, 120]),
        sticky("메모: 가드레일", "### 가드레일(앱 core/guardrails.py와 같은 규칙)\n① 금지 표현(법적 절차·국가기관·위협, 계좌 변경 문구) ② 필수 요소 ③ 180단어 "
               "④ 수신자 화이트리스트(Config whitelist_regex) → 하나라도 실패하면 발송 경로 중단 + 감사로그.\n"
               "⑤ 발송 시간창(현지 08–21시) 밖이면 08:00까지 대기.", [2000, -420], w=520, h=200, color=6),
    ]
    conns.update({
        "가드레일": {"main": [[{"node": "가드레일 통과?", "type": "main", "index": 0}]]},
        "가드레일 통과?": {"main": [[{"node": "발송 시간창?", "type": "main", "index": 0}],
                               [{"node": "감사로그: 금지 문구·요소 차단", "type": "main", "index": 0}]]},
        "감사로그: 금지 문구·요소 차단": {"main": [[{"node": "재작성 필요 알림(내부)", "type": "main", "index": 0}]]},
        "발송 시간창?": {"main": [[{"node": "초안 해시", "type": "main", "index": 0}],
                              [{"node": "08:00까지 대기", "type": "main", "index": 0}]]},
        "08:00까지 대기": {"main": [[{"node": "초안 해시", "type": "main", "index": 0}]]},
        "초안 해시": {"main": [[{"node": "승인 요청 메일(검토자)", "type": "main", "index": 0}]]},
        "승인 요청 메일(검토자)": {"main": [[{"node": "승인?", "type": "main", "index": 0}]]},
        "승인?": {"main": [[{"node": "Gmail 초안 만들기", "type": "main", "index": 0}],
                         [{"node": "감사로그: 반려", "type": "main", "index": 0}]]},
        "Gmail 초안 만들기": {"main": [[{"node": "감사로그: 승인", "type": "main", "index": 0}]]},
        "감사로그: 승인": {"main": [[{"node": "원장 갱신", "type": "main", "index": 0}]]},
        "원장 갱신": {"main": [[{"node": "D+30?", "type": "main", "index": 0}]]},
        "D+30?": {"main": [[{"node": "에스컬레이션 알림(내부)", "type": "main", "index": 0}], []]},
    })
    return {"name": "한빛 독촉 워크플로 v1 (Draft-only)", "nodes": nodes, "connections": conns, "pinData": {},
            "settings": {"executionOrder": "v1", "timezone": "Asia/Seoul", "saveManualExecutions": True,
                         "callerPolicy": "workflowsFromSameOwner"},
            "active": False, "meta": {"templateCredsSetupCompleted": False}, "tags": []}


# ------------------------------------------------------------------------------------------------ Dify
def build_dify() -> str:
    """Dify Chatflow(advanced-chat) DSL. 지식베이스(청킹·검색 설정)는 DSL에 들어가지 않는다 → 머리 주석과 agents/README.md 절차로 만든 뒤 연결."""
    start, kr, ifn, llm, ans, abst = "1729000000001", "1729000000002", "1729000000003", "1729000000004", "1729000000005", "1729000000006"
    sysp = rag_prompt() + "\n\n[컨텍스트]\n{{#context#}}"

    def node(i, x, y, data, h=98):
        return {"id": i, "type": "custom", "data": {**data, "selected": False, "desc": data.get("desc", "")},
                "position": {"x": x, "y": y}, "positionAbsolute": {"x": x, "y": y}, "width": 244, "height": h,
                "sourcePosition": "right", "targetPosition": "left", "selected": False}

    def edge(s, t, st, tt, handle="source"):
        return {"id": f"{s}-{handle}-{t}-target", "source": s, "sourceHandle": handle, "target": t, "targetHandle": "target",
                "type": "custom", "zIndex": 0, "data": {"sourceType": st, "targetType": tt, "isInIteration": False}}

    dsl = {
        "app": {"name": "한빛 여신규정 도우미", "mode": "advanced-chat", "icon": "📚", "icon_background": "#E4FBCC",
                "description": "(가상) 한빛정밀 여신관리규정 + K-SURE 약관 + 법령 — 조항 인용 강제·기권·규정 충돌 표시(Day5 RAG)",
                "use_icon_as_answer_icon": False},
        "kind": "app", "version": "0.3.0", "dependencies": [],
        "workflow": {
            "conversation_variables": [], "environment_variables": [],
            "features": {
                "file_upload": {"enabled": False},
                "opening_statement": "규정·약관 질문을 입력하세요. 근거 조항을 [문서 제N조 제M항]으로 붙이고, 문서에 없으면 '제공 문서에서 확인되지 않습니다.'라고 답합니다.",
                "retriever_resource": {"enabled": True},
                "sensitive_word_avoidance": {"enabled": False},
                "speech_to_text": {"enabled": False},
                "suggested_questions": ["사내 규정상 C등급 바이어에게 허용되는 결제조건은?",
                                        "사내 규정상 연체 40일 바이어에게 영업본부장 승인으로 선적해도 되나?",
                                        "결제기일이 2026-09-15인 O/A 건이 미결제다. 사고발생통지 기한은?"],
                "suggested_questions_after_answer": {"enabled": False},
                "text_to_speech": {"enabled": False}},
            "graph": {
                "nodes": [
                    node(start, 30, 280, {"type": "start", "title": "시작", "variables": []}, 54),
                    node(kr, 330, 280, {
                        "type": "knowledge-retrieval", "title": "지식 검색(조 단위)",
                        "desc": "가져온 뒤 지식베이스 3개(hanbit_policy · ksure_terms · laws)를 다시 연결하고 Rerank 모델을 고른다",
                        "dataset_ids": [], "query_variable_selector": [start, "sys.query"], "retrieval_mode": "multiple",
                        "multiple_retrieval_config": {
                            "top_k": 3, "score_threshold": 0.5, "reranking_enable": True, "reranking_mode": "reranking_model",
                            "reranking_model": {"provider": "", "model": ""}}}),
                    node(ifn, 630, 280, {
                        "type": "if-else", "title": "검색 결과 있음?",
                        "cases": [{"case_id": "true", "id": "true", "logical_operator": "and",
                                   "conditions": [{"id": "c1", "variable_selector": [kr, "result"], "comparison_operator": "not empty",
                                                   "value": "", "varType": "array[object]"}]}]}, 126),
                    node(llm, 930, 200, {
                        "type": "llm", "title": "답변(인용 강제·기권·충돌 표시)",
                        "model": {"provider": "langgenius/openai_api_compatible/openai_api_compatible", "name": "fast-default",
                                  "mode": "chat", "completion_params": {"temperature": 0.1, "max_tokens": 800}},
                        "prompt_template": [{"id": "sys-p5-1", "role": "system", "text": sysp},
                                            {"id": "user-q", "role": "user", "text": "{{#sys.query#}}"}],
                        "context": {"enabled": True, "variable_selector": [kr, "result"]},
                        "memory": {"window": {"enabled": False, "size": 10}, "query_prompt_template": "{{#sys.query#}}",
                                   "role_prefix": {"user": "", "assistant": ""}},
                        "vision": {"enabled": False}, "variables": []}),
                    node(ans, 1230, 200, {"type": "answer", "title": "답", "answer": "{{#" + llm + ".text#}}", "variables": []}, 105),
                    node(abst, 930, 420, {"type": "answer", "title": "기권(고정 문구)", "answer": "제공 문서에서 확인되지 않습니다.",
                                          "variables": []}, 105),
                ],
                "edges": [edge(start, kr, "start", "knowledge-retrieval"), edge(kr, ifn, "knowledge-retrieval", "if-else"),
                          edge(ifn, llm, "if-else", "llm", "true"), edge(ifn, abst, "if-else", "answer", "false"),
                          edge(llm, ans, "llm", "answer")],
                "viewport": {"x": 0, "y": 0, "zoom": 0.8}}}}
    head = """# Dify DSL — 한빛 여신규정 도우미(Chatflow) · Day5 RAG (03 Part1 §8.2 · 03 Part2 §5.6)
# 가져오기: Studio → Import DSL file → 이 파일. 버전 경고가 뜨면 '계속'(DSL 0.3.0 기준으로 썼다).
# 지식베이스(KB)는 DSL에 들어가지 않는다 → 먼저 KB 3개를 만들고, 가져온 앱의 '지식 검색' 노드에 다시 연결한다.
#   KB 설정(정본): Index = High Quality · Chunk mode = Parent-child
#     Parent: Paragraph, 구분자 \\n\\n, 최대 1,000 tokens(부모 = 조) · Child: 구분자 \\n, 최대 200 tokens(자식 = 항·호)
#     전처리: '연속 공백·줄바꿈·탭 치환' 끔 · 'URL·이메일 삭제' 끔
#     검색: Hybrid Search(의미 + 키워드) → Rerank 켬(모델 선택) → Top K 3 → Score Threshold 0.5
#     (Top K·Threshold는 Rerank를 켜야 적용된다 — 비교 실험 E1~E4는 rag/eval_sheet_template.xlsx experiments 탭)
#   KB 3개: hanbit_policy(rag/corpus/hanbit_credit_policy.md) · ksure_terms(각자 받은 약관 PDF 또는 P5-2 변환본) · laws(law.go.kr 조문 복사)
# 모델: LLM 노드 = 'OpenAI-API-compatible' 공급자 + 강사 LiteLLM(가상 키, 모델 fast-default). 크레딧 모델을 쓰려면 노드에서 모델만 바꾼다.
# 기능: Citations and Attributions(retriever_resource) 켜짐 · 시스템 프롬프트 = P5-1(app/prompts/rag_system_v1.md와 같은 원문)
"""
    return head + yaml.safe_dump(dsl, allow_unicode=True, sort_keys=False, width=1000)


# ------------------------------------------------------------------------------------------------ 검사
def structural_check(w: dict) -> list[str]:
    probs = []
    names = [n["name"] for n in w["nodes"]]
    if len(names) != len(set(names)):
        probs.append("노드 이름 중복")
    ids = [n["id"] for n in w["nodes"]]
    if len(ids) != len(set(ids)):
        probs.append("노드 id 중복")
    for src, outs in w["connections"].items():
        if src not in names:
            probs.append(f"연결 출발 없음 {src}")
        for kind, branches in outs.items():
            for br in branches:
                for e in br:
                    if e["node"] not in names:
                        probs.append(f"연결 대상 없음 {e['node']}")
    targets = {e["node"] for o in w["connections"].values() for b in o.values() for br in b for e in br}
    sources = set(w["connections"])
    for n in w["nodes"]:
        if n["type"].endswith("stickyNote") or n["type"].endswith("Trigger") or n["type"].endswith("manualTrigger"):
            continue
        if n["name"] not in targets and n["name"] not in sources:
            probs.append(f"고립 노드 {n['name']}")
    for n in w["nodes"]:
        if n["type"] == "n8n-nodes-base.gmail" and n["parameters"].get("operation") in (None, "send"):
            to = n["parameters"].get("sendTo", "")
            if "recipient" in to or "contact_email" in to:
                probs.append(f"{n['name']}: 바이어에게 바로 보내는 Send 노드(Draft-only 위반)")
    return probs


def node_check(rows_csv: Path) -> list[str]:
    """Node.js로 Code 노드 JS를 실제로 돌려 앱 규칙(app/core/dunning.route · guardrails)과 대조."""
    node = shutil.which("node")
    if not node:
        return ["(건너뜀) node 없음"]
    import pandas as pd
    sys.path.insert(0, str(APP))
    from core import clean as CL, dunning as DN, guardrails as GR  # noqa: E402
    raw = pd.read_csv(rows_csv, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    cfg_rows = [{"key": "as_of", "value": "2026-09-30"}, {"key": "approver_email", "value": "reviewer@example.com"},
                {"key": "whitelist_regex", "value": r"^buyer\+B\d{3}@example\.com$"}, {"key": "model_alias", "value": "fast-default"},
                {"key": "prompt_version", "value": "v1"}, {"key": "send_tz", "value": "Asia/Seoul"}]
    rows = raw.to_dict("records")
    for r in rows:
        r["status"] = "open"
    probs = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "rows.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        (td / "cfg.json").write_text(json.dumps(cfg_rows), encoding="utf-8")
        harness = r"""
const fs = require('fs');
const [codePath, rowsPath, cfgPath] = process.argv.slice(2);
const code = fs.readFileSync(codePath, 'utf8');
const rows = JSON.parse(fs.readFileSync(rowsPath, 'utf8'));
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
const $ = (name) => ({ all: () => cfg.map((j) => ({ json: j })) });
const $input = { all: () => rows.map((j) => ({ json: j })) };
const out = new Function('$', '$input', code)($, $input);
process.stdout.write(JSON.stringify(out.map((o) => o.json)));
"""
        (td / "h.js").write_text(harness, encoding="utf-8")
        res = subprocess.run([node, str(td / "h.js"), str(AG / "n8n" / "code" / "stage_logic.js"), str(td / "rows.json"),
                              str(td / "cfg.json")], capture_output=True, text=True, timeout=60)
        if res.returncode:
            return [f"stage_logic.js 실행 오류: {res.stderr[:300]}"]
        js = json.loads(res.stdout)
        drafts_js = {(o["invoice_id"], o["stage_key"]) for o in js if o["route"] == "DRAFT"}
        human_js = {o["buyer_id"] for o in js if o["route"] == "HUMAN"}
        led = CL.clean_ledger(raw, asof="2026-09-30").df
        q = DN.queue(led, "2026-09-30")
        drafts_py = {(r.invoice_id, r.stage_key) for r in q[q.route == "DRAFT"].itertuples()}
        hum = q[(q.route == "HUMAN") & (q.dpd >= -3)]
        if drafts_js != drafts_py:
            probs.append(f"DRAFT 불일치 JS-Py {sorted(drafts_js - drafts_py)[:3]} Py-JS {sorted(drafts_py - drafts_js)[:3]}")
        if human_js != set(hum.buyer_id):
            probs.append(f"HUMAN 바이어 불일치 {sorted(human_js ^ set(hum.buyer_id))}")
        # 가드레일: 앱 모의 초안 → JS 가드레일 통과, 금지어 넣으면 실패
        gh = r"""
const fs = require('fs');
const [codePath, rowPath, llmPath] = process.argv.slice(2);
const code = fs.readFileSync(codePath, 'utf8');
const row = JSON.parse(fs.readFileSync(rowPath, 'utf8'));
const llm = JSON.parse(fs.readFileSync(llmPath, 'utf8'));
const $ = (name) => ({ item: { json: row } });
const out = new Function('$', '$json', code)($, llm);
process.stdout.write(JSON.stringify(out.json));
"""
        (td / "g.js").write_text(gh, encoding="utf-8")
        n_ok = 0
        for o in [o for o in js if o["route"] == "DRAFT"]:
            r = led[led.invoice_id == o["invoice_id"]].iloc[0].to_dict()
            s, b, k = DN.mock_email(o["stage_key"], DN.build_facts(r, "2026-09-30"))
            for variant, expect in ((b, True), (b + "\nOtherwise our lawyer will file a lawsuit.", False)):
                (td / "row.json").write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
                (td / "llm.json").write_text(json.dumps({"text": "```json\n" + json.dumps({"subject": s, "body": variant, "summary_ko": k},
                                                                                           ensure_ascii=False) + "\n```"}), encoding="utf-8")
                g = subprocess.run([node, str(td / "g.js"), str(AG / "n8n" / "code" / "guardrail.js"), str(td / "row.json"),
                                    str(td / "llm.json")], capture_output=True, text=True, timeout=60)
                if g.returncode:
                    return probs + [f"guardrail.js 실행 오류: {g.stderr[:300]}"]
                gj = json.loads(g.stdout)
                py_ok = GR.passed(GR.check_draft(s, variant, o["stage_key"], DN.build_facts(r, "2026-09-30"), o["recipient"])[:4])
                if gj["guardrail_pass"] != expect or py_ok != expect:
                    probs.append(f"가드레일 {o['invoice_id']} {o['stage_key']} 기대 {expect} JS {gj['guardrail_pass']} Py {py_ok} {gj['checks_text']}")
                n_ok += 1
        if not probs:
            probs.append(f"(통과) DRAFT {len(drafts_js)}건 · HUMAN 바이어 {len(human_js)}곳 앱과 일치 · 가드레일 {n_ok}건 JS = Python")
    return probs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not args.check:
        w = build_n8n()
        N8N_OUT.parent.mkdir(parents=True, exist_ok=True)
        N8N_OUT.write_text(json.dumps(w, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        DIFY_OUT.parent.mkdir(parents=True, exist_ok=True)
        DIFY_OUT.write_text(build_dify(), encoding="utf-8")
        print(f"→ {N8N_OUT.relative_to(REPO)}(노드 {len(w['nodes'])}) · {DIFY_OUT.relative_to(REPO)}")
    w = json.loads(N8N_OUT.read_text(encoding="utf-8"))
    probs = structural_check(w)
    d = yaml.safe_load(DIFY_OUT.read_text(encoding="utf-8"))
    ids = {n["id"] for n in d["workflow"]["graph"]["nodes"]}
    probs += [f"Dify 엣지 노드 없음 {e['id']}" for e in d["workflow"]["graph"]["edges"] if e["source"] not in ids or e["target"] not in ids]
    d5 = REPO / "data" / "checkpoints" / "d5_start.csv"
    notes = node_check(d5) if d5.exists() else ["(건너뜀) d5_start.csv 없음"]
    hard = [p for p in probs]
    hard += [n for n in notes if not n.startswith("(")]
    for n in notes:
        print("  ", n)
    if hard:
        print("문제:", hard)
        return 1
    print("구조 검사 통과(n8n 연결·노드 · Dify 그래프)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
