"""LiteLLM 프록시(OpenAI 호환 /chat/completions) 호출 — requests만 쓴다(SDK 버전에 묶이지 않게).

Secrets(.streamlit/secrets.toml 또는 Community Cloud Secrets)의 [llm] 칸이 비었거나 자리표시면 None → 모의(템플릿) 모드.
429·5xx·시간 초과면 fallback_models 순서로 다시 시도하고, 전부 실패하면 호출한 쪽이 템플릿 초안으로 바꾼다.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import requests

# 1M 토큰당 USD(입력, 출력). 실제 단가는 프록시 설정·공급자 콘솔에서 D-3에 다시 확인 [교육용 추정]
PRICES = {"fast-default": (0.10, 0.50), "fast-backup": (0.25, 1.50), "quality": (1.00, 5.00)}


@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    default_model: str = "fast-default"
    fallback_models: list = field(default_factory=lambda: ["fast-backup"])
    timeout: float = 30.0
    temperature: float = 0.3
    max_tokens: int = 600


@dataclass
class LLMResult:
    ok: bool
    text: str = ""
    model_alias: str = ""
    model_resolved: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    error: str = ""
    used_fallback: bool = False


def _placeholder(v: str) -> bool:
    v = (v or "").strip()
    return (not v) or ("<" in v) or ("{" in v) or v.endswith("...") or "강사" in v or "가상 키" in v


def from_secrets(secrets) -> LLMConfig | None:
    """st.secrets(또는 dict)에서 [llm] 읽기. 없거나 자리표시면 None(모의 모드)."""
    try:
        s = secrets["llm"]
    except Exception:
        return None
    try:
        base, key = str(s.get("base_url", "")), str(s.get("api_key", ""))
    except Exception:
        return None
    if _placeholder(base) or _placeholder(key):
        return None
    fb = s.get("fallback_models", ["fast-backup"])
    return LLMConfig(base_url=base, api_key=key, default_model=str(s.get("default_model", "fast-default")),
                     fallback_models=list(fb) if isinstance(fb, (list, tuple)) else [str(fb)])


def chat(cfg: LLMConfig, messages: list[dict], model: str | None = None, max_tokens: int | None = None) -> LLMResult:
    models = [model or cfg.default_model] + [m for m in cfg.fallback_models if m != (model or cfg.default_model)]
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    last = ""
    for i, m in enumerate(models):
        try:
            r = requests.post(url, timeout=cfg.timeout,
                              headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
                              json={"model": m, "messages": messages, "temperature": cfg.temperature,
                                    "max_tokens": max_tokens or cfg.max_tokens})
        except requests.RequestException as e:
            last = f"{m}: 연결 실패 {type(e).__name__}"
            continue
        if r.status_code == 200:
            try:
                data = r.json()
                text = data["choices"][0]["message"]["content"] or ""
            except Exception as e:  # 응답 형식이 다르면 다음 모델
                last = f"{m}: 응답 형식 오류 {e}"
                continue
            u = data.get("usage") or {}
            return LLMResult(ok=True, text=text, model_alias=m, model_resolved=str(data.get("model", m)),
                             tokens_in=int(u.get("prompt_tokens", 0) or 0), tokens_out=int(u.get("completion_tokens", 0) or 0),
                             used_fallback=i > 0)
        last = f"{m}: HTTP {r.status_code} {r.text[:160]}"
        if r.status_code in (401, 403):   # 키 문제는 다른 모델로 바꿔도 같다
            break
    return LLMResult(ok=False, error=last)


def extract_json(text: str) -> dict | None:
    """```json 울타리·앞뒤 설명이 섞여도 첫 JSON 객체를 꺼낸다."""
    if not text:
        return None
    t = re.sub(r"```(?:json)?", "", text)
    start = t.find("{")
    while start != -1:
        depth = 0
        for j in range(start, len(t)):
            if t[j] == "{":
                depth += 1
            elif t[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(t[start:j + 1])
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        break
                    break
        start = t.find("{", start + 1)
    return None


def cost_usd(alias: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRICES.get(alias, PRICES["fast-default"])
    return round(tokens_in / 1e6 * pin + tokens_out / 1e6 * pout, 6)
