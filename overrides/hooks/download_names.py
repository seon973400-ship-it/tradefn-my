"""과정 사이트 훅 — 내려받기 단추의 파일 이름을 바로잡는다.

쪽 원고의 `[받기](../downloads/x.xlsx){ .md-button download }`는 attr_list가 `download="download"`로 만든다.
브라우저는 그 값을 저장 이름으로 쓰므로 파일이 확장자 없는 'download'로 저장될 수 있다.
빌드한 HTML에서 그런 링크를 찾아 값을 링크 주소의 파일 이름(x.xlsx)으로 바꾼다. 다른 링크는 건드리지 않는다.
"""
from __future__ import annotations

import posixpath
import re
from urllib.parse import unquote, urlsplit

_A = re.compile(r"<a\b[^>]*>", re.I)
_HREF = re.compile(r'\bhref="([^"]*)"', re.I)


def _fix(tag: str) -> str:
    if 'download="download"' not in tag:
        return tag
    m = _HREF.search(tag)
    if not m:
        return tag
    name = posixpath.basename(unquote(urlsplit(m.group(1)).path))
    if not name or "." not in name:
        return tag
    return tag.replace('download="download"', f'download="{name}"')


def on_page_content(html_text: str, page, config, files):  # noqa: ARG001 — MkDocs 훅 서명
    if 'download="download"' not in html_text:
        return html_text
    return _A.sub(lambda m: _fix(m.group(0)), html_text)
