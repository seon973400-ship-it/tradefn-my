"""과정 사이트 훅 — 강사만 아는 주소를 mkdocs.yml 한 곳(extra.course_links)에서 쪽마다 채운다.

쪽에서 쓰는 법(마크다운 안의 원시 HTML 한 줄):

    <span data-tf-link="open_chat">오픈채팅 들어가기</span>
    <span data-tf-link="team_form" data-tf-empty="수업 중 화면 · 오픈채팅 공지로 받은 주소">팀 제출 폼</span>

- 값이 http(s)://… 이면 → 새 탭 링크 `<a class="tf-link">오픈채팅 들어가기</a>`
- 값이 글자(예: 강의장 이름)면 → 그 글자
- 값이 비었거나 키가 없으면 → 점선 알약에 '이름(주소를 실제로 받는 곳)'. data-tf-empty가 있으면 그 글만 쓴다.
    개강 전 항목(open_chat · pre_survey · venue) → '설문 열기(과정 안내 메시지(문자 · 메일)로 받은 주소)'
    수업 중 항목(그 밖의 키 · 모르는 키)         → '제출 폼(수업 중 화면 · 오픈채팅 공지로 받은 주소)'
    6일차 post_survey · peer_form               → 위 글 + '· 안 열리면 종이 양식 post_assessment.md'(peer_feedback_form.md)
  이름이 없으면(예: 강의장) 받는 곳만 쓴다.

쪽의 문장은 링크가 있을 때와 비었을 때 모두 맞아야 한다 — '홈에 있다' · '이 쪽에 있다'처럼 링크가 생겨야만 맞는 말은 쓰지 않는다.
값을 넣고 main에 push하면 다음 배포부터 모든 쪽이 바뀐다. 빌드는 깨지지 않는다.
"""
from __future__ import annotations

import html
import logging
import re

log = logging.getLogger("mkdocs.hooks.course_links")

_SPAN = re.compile(
    r'<span\b(?P<attrs>[^>]*?\bdata-tf-link="(?P<key>[A-Za-z0-9_-]+)"[^>]*)>(?P<text>.*?)</span>',
    re.S,
)
_EMPTY = re.compile(r'\bdata-tf-empty="(?P<v>[^"]*)"')
_URL = re.compile(r"^(https?://|mailto:)", re.I)

# 주소가 비어 있을 때 '실제로 어디서 받는가' — 개강 전 항목은 과정 안내 메시지, 수업 중 항목은 수업 화면 · 오픈채팅 공지
PRE_COURSE = frozenset({"open_chat", "pre_survey", "venue"})
PRE_COURSE_WHERE = "과정 안내 메시지(문자 · 메일)로 받은 주소"
IN_CLASS_WHERE = "수업 중 화면 · 오픈채팅 공지로 받은 주소"
PAPER_FORM = {"post_survey": "post_assessment.md", "peer_form": "peer_feedback_form.md"}   # 6일차 종이 양식(labs/day6/)


def empty_where(key: str) -> str:
    """링크가 비었을 때 이름 뒤 괄호에 붙는 글 — 주소를 실제로 받는 곳."""
    if key in PRE_COURSE:
        return PRE_COURSE_WHERE
    if key in PAPER_FORM:
        return f"{IN_CLASS_WHERE} · 안 열리면 종이 양식 {PAPER_FORM[key]}"
    return IN_CLASS_WHERE


def empty_title(key: str) -> str:
    """점선 알약에 마우스를 올리면 보이는 설명."""
    if key in PRE_COURSE:
        return "개강 전에 과정 안내 메시지(문자 · 메일)로 보내 드린 주소를 씁니다"
    if key in PAPER_FORM:
        return f"수업 중 화면과 오픈채팅 공지로 알려 드리는 주소를 씁니다. 폼이 안 열리면 종이 양식({PAPER_FORM[key]})에 씁니다"
    return "수업 중 화면과 오픈채팅 공지로 알려 드리는 주소를 씁니다"


def _links(config) -> dict:
    extra = config.get("extra") or {}
    links = extra.get("course_links") or {}
    return links if isinstance(links, dict) else {}


def render(html_text: str, links: dict, page_name: str = "") -> str:
    def repl(m: re.Match) -> str:
        key, attrs, text = m.group("key"), m.group("attrs"), m.group("text").strip()
        value = str(links.get(key) or "").strip()
        if key not in links:
            log.info("course_links: '%s'에 모르는 키 '%s' — 수업 중 항목의 안내 글로 둡니다", page_name, key)
        if not value:
            e = _EMPTY.search(attrs)
            if e and e.group("v"):
                fallback = html.escape(e.group("v"))
            elif text and "<" not in text:
                # 이름을 살려 둔다 — 'PR 링크를 제출 폼(수업 중 화면 · 오픈채팅 공지로 받은 주소)에 붙입니다'
                fallback = f"{text}({empty_where(key)})"
            else:
                fallback = empty_where(key)
            return (f'<span class="tf-link tf-link--pending" data-tf-link-key="{key}" '
                    f'title="{empty_title(key)}">{fallback}</span>')
        if _URL.match(value):
            label = text or "열기"
            return (f'<a class="tf-link" data-tf-link-key="{key}" href="{html.escape(value, quote=True)}" '
                    f'target="_blank" rel="noopener">{label}</a>')
        return f'<span class="tf-link tf-link--text" data-tf-link-key="{key}">{html.escape(value)}</span>'

    return _SPAN.sub(repl, html_text)


def on_page_content(html_text, page, config, files):  # noqa: D401 — MkDocs 훅 이름
    if "data-tf-link=" not in html_text:
        return html_text
    return render(html_text, _links(config), getattr(getattr(page, "file", None), "src_uri", ""))
