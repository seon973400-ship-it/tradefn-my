"""과정 사이트 훅 — 원시 HTML 부품 안의 `코드`를 <code>로 바꾼다.

점검 시각 `<p class="tf-check">…</p>`와 그림 설명 `<figcaption>…</figcaption>`은 원시 HTML이라
마크다운이 처리되지 않는다. 그 안에 쓴 `data/` · `hello.py` 같은 백틱이 화면에 글자 그대로 보이지 않게
빌드한 HTML에서 백틱 한 쌍을 <code>로 바꾼다. 다른 곳(본문 · 코드 블록)은 건드리지 않는다.
"""
from __future__ import annotations

import re

_BLOCK = re.compile(r'(<p class="tf-check"[^>]*>|<figcaption\b[^>]*>)(.*?)(</p>|</figcaption>)', re.S)
_TICK = re.compile(r"`([^`<>\n]{1,120})`")


def _fix(m: re.Match) -> str:
    body = m.group(2)
    if "`" not in body:
        return m.group(0)
    return m.group(1) + _TICK.sub(lambda t: "<code>" + t.group(1) + "</code>", body) + m.group(3)


def on_page_content(html_text: str, page, config, files):  # noqa: ARG001 — MkDocs 훅 서명
    if "`" not in html_text:
        return html_text
    return _BLOCK.sub(_fix, html_text)
