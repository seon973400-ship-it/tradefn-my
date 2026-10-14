"""LiteLLM(OpenAI 호환) 경로 — 가짜 로컬 서버로 호출·예비 모델 전환·JSON 추출·Secrets 자리표시 처리를 확인한다(네트워크 없음)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conftest import ASOF
from core import data_io as IO
from core import dunning as DN
from core import llm as LLM

CALLS = []


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append((body["model"], self.headers.get("Authorization")))
        if body["model"] == "fast-default":                      # 기본 모델은 한도 초과 → 예비 모델로 넘어가야 한다
            self.send_response(429)
            self.end_headers()
            self.wfile.write(b'{"error":"budget exceeded"}')
            return
        content = ("```json\n" + json.dumps({"subject": "Payment reminder", "body": "Dear team, invoice {INV} ...",
                                              "summary_ko": "요약"}) + "\n```")
        out = {"model": "gemini/gemini-flash-lite-test", "choices": [{"message": {"content": content}}],
               "usage": {"prompt_tokens": 321, "completion_tokens": 77}}
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture(scope="module")
def server():
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1"
    srv.shutdown()


def test_placeholder_secrets_mean_mock():
    assert LLM.from_secrets({}) is None
    assert LLM.from_secrets({"llm": {"base_url": "https://llm.<강사도메인>/v1", "api_key": "<가상 키>"}}) is None
    cfg = LLM.from_secrets({"llm": {"base_url": "https://llm.example.org/v1", "api_key": "test-key-123",
                                    "fallback_models": ["fast-backup"]}})
    assert cfg and cfg.default_model == "fast-default" and cfg.fallback_models == ["fast-backup"]


def test_fallback_and_json(server):
    cfg = LLM.LLMConfig(base_url=server, api_key="test-key-123")
    r = LLM.chat(cfg, [{"role": "user", "content": "hi"}])
    assert r.ok and r.used_fallback and r.model_alias == "fast-backup" and r.tokens_in == 321
    assert [m for m, _ in CALLS[-2:]] == ["fast-default", "fast-backup"]
    assert CALLS[-1][1] == "Bearer test-key-123"
    assert LLM.extract_json(r.text)["subject"] == "Payment reminder"


def test_generate_uses_llm(server, ledger):
    q = DN.queue(ledger, ASOF)
    inv = q[q.route == "DRAFT"].iloc[0]
    row = ledger[ledger.invoice_id == inv.invoice_id].iloc[0].to_dict()
    tpl = DN.load_templates(IO.PROMPTS / "dunning_v1.md")
    d = DN.generate(row, inv.stage_key, ASOF, tpl, LLM.LLMConfig(base_url=server, api_key="test-key-123"))
    assert d.used_llm and d.subject == "Payment reminder" and d.tokens_out == 77


def test_unreachable_falls_back_to_template(ledger):
    q = DN.queue(ledger, ASOF)
    inv = q[q.route == "DRAFT"].iloc[0]
    row = ledger[ledger.invoice_id == inv.invoice_id].iloc[0].to_dict()
    tpl = DN.load_templates(IO.PROMPTS / "dunning_v1.md")
    cfg = LLM.LLMConfig(base_url="http://127.0.0.1:9/v1", api_key="x-key", timeout=2)
    d = DN.generate(row, inv.stage_key, ASOF, tpl, cfg)
    assert not d.used_llm and "템플릿" in d.banner and inv.invoice_id in d.body
