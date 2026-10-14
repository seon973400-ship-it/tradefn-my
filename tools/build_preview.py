#!/usr/bin/env python
"""Day1 실습 가이드 한 페이지 미리보기(강사 검토용) — 수강생 사이트와 같은 원본 md에서 만든다.

사용 (저장소 루트에서, 먼저 `python tools/sync_site_assets.py`로 파일 표 조각을 만든다):
    python tools/build_preview.py                  # → ../instructor/day1/preview/day1_lab_guide.html (+ 검사)
    python tools/build_preview.py --out 파일.html   # 다른 곳에 쓰기
    python tools/build_preview.py --no-charts      # 부록(정답 차트 4개) 없이 — 강사 폴더 밖에 둘 판
    python tools/build_preview.py --check          # 새로 만들지 않고 이미 있는 파일만 검사

원본: docs/day1/index.md · lab1–3.md · docs/prompts/day1.md(= labs/day1/prompts.md) · docs/ax-project.md ·
      docs/data.md · docs/faq.md · docs/_snippets/day1/*.md(파일 표) · 부록은 docs/assets/day1/*.png(라이트판)·*.csv
마크다운 설정은 mkdocs.yml을 그대로 읽고(프롬프트 앵커 훅 포함) 미리보기에 필요한 것만 바꾼다. 그래서 글은 사이트와 같다.

출력 형식(아티팩트 페이지 규약): <!doctype>·<html>·<head>·<body> 없이 <title> → Google Fonts <link> → <style> 하나 →
본문 → <script>. 색은 :root 토큰(라이트) + 다크 두 블록. 외부 자원은 글꼴 스타일시트 하나, 차트는 data: URI.
받기 링크는 넣지 않고 파일 경로와 '과정 사이트에서 받기'만 적는다.
검사(매번): 태그 짝 · id 중복 · 내부 링크 대상 · 금지 태그 · 외부 자원 · 라이브러리 프롬프트 전부 포함 · 복사 버튼 수.
"""
from __future__ import annotations

import argparse
import base64
import collections
import csv
import datetime as dt
import hashlib
import html
import itertools
import logging
import posixpath
import re
import sys
import xml.etree.ElementTree as etree
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
PROMPTS_SRC = REPO / "labs" / "day1" / "prompts.md"
SNIPPETS = DOCS / "_snippets" / "day1"
CHART_DIR = DOCS / "assets" / "day1"
INSTRUCTOR_DAY1 = REPO.parent / "instructor" / "day1"
DEFAULT_OUT = INSTRUCTOR_DAY1 / "preview" / "day1_lab_guide.html"

PAGE_TITLE = "Day1 실습 가이드"
FONTS_HREF = ("https://fonts.googleapis.com/css2?family=Nanum+Gothic+Coding:wght@400;700"
              "&family=Noto+Sans+KR:wght@400;500;700&display=swap")

# (키, docs/ 기준 경로, 목차 묶음) — 순서가 곧 페이지 순서
PAGES = [
    ("day1", "day1/index.md", "실습"),
    ("lab1", "day1/lab1.md", "실습"),
    ("lab2", "day1/lab2.md", "실습"),
    ("lab3", "day1/lab3.md", "실습"),
    ("prompts", "prompts/day1.md", "참고"),
    ("ax", "ax-project.md", "참고"),
    ("data", "data.md", "참고"),
    ("faq", "faq.md", "참고"),
]
PAGE_KEYS = {rel: key for key, rel, _ in PAGES}
APPENDIX_ID = "answer-charts"

TRACKS = {"Basic": "basic", "Standard": "standard", "Challenge": "challenge"}
TRACK_EMOJI = {"\U0001F7E2": "Basic", "\U0001F535": "Standard", "\U0001F7E3": "Challenge"}  # 🟢 🔵 🟣
EMOJI_RE = re.compile("[\U0001F7E2\U0001F535\U0001F7E3]️?\\s*")
SAFE_ID = re.compile(r"^[A-Za-z0-9._~-]+$")
KIND_KO = {"note": "참고", "abstract": "요약", "info": "안내", "tip": "팁", "success": "핵심", "question": "질문",
           "warning": "주의", "danger": "위험", "failure": "실패", "bug": "버그", "example": "예시", "quote": "인용"}
ADM_DEFAULT_TITLES = {k.capitalize() for k in KIND_KO}

# 부록 차트 — 숫자는 쓰지 않는다(숫자는 만들 때 CSV에서 읽어 표로만 넣는다)
CHARTS = [
    ("day1_fig1_aging_by_payment_method", "결제방식 × 에이징 구성(행 100%)",
     "가로 100% 누적 막대 차트. 결제방식 7종을 수출자 위험이 낮은 순서(선수금 → O/A)로 놓고, 바이어별 최악 연체일 구간"
     "(미연체 · 1–30일 · 31–60일 · 61–90일 · 91일 이상)이 차지하는 비율과 결제방식별 바이어 수를 보여 준다.",
     "Lab2 피벗①과 100% 누적 막대 차트를 견줄 때 봅니다."),
    ("day1_fig2_overdue_ratio_top10_country", "국가별 연체 바이어 비율 상위 10",
     "가로 막대 차트. 연체 바이어 비율이 높은 10개국을 위에서부터 놓고, 나라마다 연체 바이어 수와 전체 바이어 수, 전체 평균선을 보여 준다.",
     "Lab2 피벗②(국가별 상위 10)를 견줄 때 봅니다."),
    ("day1_fig3_ar_balance_by_region", "권역별 매출채권 잔액과 연체 잔액(USD)",
     "가로 누적 막대 차트. 권역 6곳의 매출채권 잔액을 미연체 잔액과 연체 잔액으로 나눠 달러로 환산해 보여 준다.",
     "수강생 실습에는 같은 차트가 없습니다. Day1에는 통화가 섞여 있어 금액을 합하지 않습니다(P1-3·P1-4 경고)."),
    ("day1_fig4_dpd_distribution", "연체 인보이스의 연체일(DPD) 분포",
     "막대 그래프. 연체된 인보이스를 연체일 5일 구간으로 세고, 30·60·90일 경계와 구간별 비중을 표시한다.",
     "Lab2 Challenge B-3(연체일 분포)을 견줄 때 봅니다."),
]
CHART_COLS = {
    "payment_method": "결제방식", "n_current": "미연체", "n_1_30": "1–30일", "n_31_60": "31–60일", "n_61_90": "61–90일",
    "n_91p": "91일+", "n_total": "바이어 수", "overdue_share": "연체 비율", "country_code": "국가코드", "buyers": "바이어 수",
    "overdue_buyers": "연체 바이어", "overdue_ratio": "연체 비율", "region": "권역", "ar_balance_usd": "매출채권 잔액(USD)",
    "overdue_amount_usd": "연체 잔액(USD)", "current_amount_usd": "미연체 잔액(USD)", "dpd_from": "연체일(부터)",
    "dpd_to": "연체일(까지)", "invoices": "인보이스 수", "bucket": "구간",
}
PCT_COLS = {"overdue_share", "overdue_ratio"}
MONEY_COLS = {"ar_balance_usd", "overdue_amount_usd", "current_amount_usd"}


# ---------------------------------------------------------------- 원본 읽기
def load_site_config():
    """mkdocs.yml의 마크다운 확장·설정과 nav를 그대로 읽는다(훅의 프롬프트 앵커 규칙 포함)."""
    logging.getLogger("mkdocs").setLevel(logging.ERROR)
    from mkdocs.config import load_config

    sys.path.insert(0, str(REPO / "tools"))
    from mkdocs_hooks import prompt_id_slugify

    cfg = load_config(str(REPO / "mkdocs.yml"))
    exts = list(cfg["markdown_extensions"])
    conf = {k: dict(v) for k, v in cfg["mdx_configs"].items()}
    conf.setdefault("toc", {})["slugify"] = prompt_id_slugify          # 사이트 빌드의 on_config와 같게
    conf.setdefault("pymdownx.highlight", {})["anchor_linenums"] = False
    conf["pymdownx.snippets"] = {**conf.get("pymdownx.snippets", {}), "base_path": [str(REPO)], "check_paths": True}
    conf["pymdownx.tasklist"] = {"custom_checkbox": False, "clickable_checkbox": True}
    return cfg, exts, conf


def nav_titles(nav) -> dict[str, str]:
    """mkdocs nav에서 '경로 → 메뉴 이름'. 제목 없는 항목(섹션 첫 페이지)은 섹션 이름을 쓴다."""
    out: dict[str, str] = {}

    def walk(items, section=None):
        for item in items or []:
            if isinstance(item, str):
                out.setdefault(item, section or item)
            elif isinstance(item, dict):
                for title, val in item.items():
                    if isinstance(val, str):
                        out[val] = title
                    elif isinstance(val, list):
                        walk(val, title)

    walk(nav)
    return out


def library_prompts() -> dict[str, dict]:
    """labs/day1/prompts.md의 스니펫 구역(<!-- --8<-- [start:이름] -->) → {이름: {pid, title, label, body}}."""
    text = PROMPTS_SRC.read_text(encoding="utf-8")
    pat = re.compile(r"<!--\s*--8<--\s*\[start:(?P<name>[\w-]+)\]\s*-->\s*\n```[^\n]*\n(?P<body>.*?)\n```\s*\n"
                     r"<!--\s*--8<--\s*\[end:(?P=name)\]\s*-->", re.S)
    out = {}
    for m in pat.finditer(text):
        heads = re.findall(r"^## (P\d+-\d+[a-z]?)\s+(.+?)\s*$", text[: m.start()], re.M)
        pid, title = heads[-1] if heads else (m.group("name").upper(), "")
        name = m.group("name")
        rest = name[len(pid):].strip("-") if name.lower().startswith(pid.lower()) else ""
        label = f"{pid} 변형({rest.upper()})" if rest else f"{pid} {title}"
        out[name] = {"pid": pid, "title": title, "label": label, "body": norm_code(m.group("body"))}
    if not out:
        raise SystemExit(f"[build_preview] {PROMPTS_SRC}에서 프롬프트 스니펫을 찾지 못했습니다.")
    return out


def norm_code(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip("\n").splitlines())


def abstract_rows(md_text: str) -> dict[str, str]:
    """실습 페이지 맨 위 '한눈에 보기' 표 → {항목: 내용(마크다운)}."""
    m = re.search(r"^!!! abstract[^\n]*\n((?:[ ]{4}.*\n?)+)", md_text, re.M)
    rows: dict[str, str] = {}
    for line in (m.group(1).splitlines() if m else []):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] not in ("항목",) and not set(cells[0]) <= set("-: "):
            rows[cells[0]] = cells[1]
    return rows


def inline_md(text: str) -> str:
    out = markdown.markdown(text or "")
    return re.sub(r"^<p>|</p>$", "", out.strip())


def strip_track_emoji(text: str) -> str:
    return re.sub(r"\s{2,}", " ", EMOJI_RE.sub("", text)).strip()


def scoped_id(key: str, raw: str | None) -> str:
    """페이지마다 id 앞에 키를 붙여 한 문서 안에서 겹치지 않게 한다. 한글 id는 짧은 영문 해시로 바꾼다."""
    raw = unquote(raw or "").strip()
    if not raw:
        return key
    if SAFE_ID.match(raw):
        return f"{key}-{raw}"
    return f"{key}-s" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------- 코드 블록(모든 펜스) → 복사 버튼이 달린 상자
def make_fence(prompts: dict[str, dict]):
    by_body = {p["body"]: p for p in prompts.values()}

    def fence(src, language, class_name, options, md, **kwargs):
        body = norm_code(src)
        hit = by_body.get(body)
        if hit:
            kind, label = "prompt", f"프롬프트 · {hit['label']}"
        elif body.lstrip().startswith("="):
            kind, label = "formula", "엑셀 수식"
        else:
            kind, label = "text", "텍스트"
        attrs = f' data-prompt="{html.escape(hit["pid"])}"' if hit else ""
        return (f'<div class="codeblock" data-kind="{kind}"{attrs}><div class="codebar">'
                f'<span class="codelabel">{html.escape(label)}</span>'
                f'<button type="button" class="copy-btn" data-label="{html.escape(label)}" '
                f'aria-label="{html.escape(label)} 복사">복사</button></div>'
                f'<pre tabindex="0"><code>{html.escape(body, quote=False)}</code></pre></div>')

    return fence


# ---------------------------------------------------------------- 페이지 트리 다듬기(마크다운 트리 단계)
class PageCtx:
    def __init__(self, key: str, rel: str, titles: dict[str, str]):
        self.key, self.rel, self.titles = key, rel, titles
        self.counter = itertools.count(1)
        self.notes: list[str] = []

    # -- 진입점
    def transform(self, root: etree.Element) -> None:
        self.drop_title(root)
        self.headings(root)
        self.ids(root)
        self.links(root)
        self.tabs(root)
        self.boxes(root)
        self.tables(root)
        self.stages(root)

    @staticmethod
    def parents(root):
        return {c: p for p in root.iter() for c in p}

    @staticmethod
    def classes(el) -> list[str]:
        return (el.get("class") or "").split()

    def drop_title(self, root):
        h1 = next((el for el in root if el.tag == "h1"), None)
        if h1 is not None:
            root.remove(h1)

    def headings(self, root):
        for el in root.iter():
            if el.tag in ("h2", "h3", "h4", "h5"):
                el.tag = f"h{int(el.tag[1]) + 1}"

    def ids(self, root):
        for el in root.iter():
            if el.get("id"):
                el.set("id", scoped_id(self.key, el.get("id")))

    def links(self, root):
        for a in list(root.iter("a")):
            href = a.get("href")
            if href is None:
                continue
            if "headerlink" in self.classes(a):
                a.set("href", "#" + scoped_id(self.key, href.lstrip("#")))
                a.set("title", "이 절의 주소")
                a.set("aria-label", "이 절의 주소")
                a.text = "#"
                continue
            parts = urlsplit(href)
            if parts.scheme in ("http", "https"):
                a.set("target", "_blank")
                a.set("rel", "noopener")
                continue
            if parts.scheme or href.startswith("//"):
                continue
            if not parts.path:
                a.set("href", "#" + scoped_id(self.key, parts.fragment))
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(self.rel), unquote(parts.path)))
            if target.startswith("downloads/"):
                self.download_chip(a, target)
            elif target in PAGE_KEYS:
                k = PAGE_KEYS[target]
                a.attrib.pop("download", None)
                a.set("href", "#" + (scoped_id(k, parts.fragment) if parts.fragment else k))
            else:
                self.site_ref(a, target, parts.fragment)

    def download_chip(self, a, path):
        for ch in list(a):
            a.remove(ch)
        a.tag, a.text = "span", None
        a.attrib.clear()
        a.set("class", "dl")
        lab = etree.SubElement(a, "span", {"class": "dl-label"})
        lab.text = "과정 사이트에서 받기"
        code = etree.SubElement(a, "code", {"class": "dl-path"})
        code.text = path

    def site_ref(self, a, target, fragment):
        name = self.titles.get(target, target)
        a.tag = "span"
        a.attrib.clear()
        a.set("class", "xref")
        a.set("title", f"과정 사이트 · {name}" + (f" (#{unquote(fragment)})" if fragment else ""))
        tag = etree.SubElement(a, "span", {"class": "xref-tag"})
        tag.text = "사이트"

    def tabs(self, root):
        parents = self.parents(root)
        for ts in [el for el in root.iter("div") if "tabbed-set" in self.classes(el)]:
            labels_box = next((c for c in ts if "tabbed-labels" in self.classes(c)), None)
            content = next((c for c in ts if "tabbed-content" in self.classes(c)), None)
            if labels_box is None or content is None:
                continue
            names = [strip_track_emoji("".join(lab.itertext())) for lab in labels_box]
            blocks = [b for b in content if "tabbed-block" in self.classes(b)]
            track = bool(names) and all(n in TRACKS for n in names)
            group = "track" if track else "cards"
            wrap = etree.Element("div", {"class": f"tabs tabs-{group}", "data-group": group})
            tl = etree.SubElement(wrap, "div", {"class": "tablist", "role": "tablist",
                                                "aria-label": "트랙 고르기" if track else "카드 고르기"})
            for i, (name, block) in enumerate(zip(names, blocks)):
                n = next(self.counter)
                tid, pid = f"{self.key}-tab{n}", f"{self.key}-panel{n}"
                btn = etree.SubElement(tl, "button", {
                    "type": "button", "role": "tab", "id": tid, "aria-controls": pid,
                    "aria-selected": "true" if i == 0 else "false", "tabindex": "0" if i == 0 else "-1",
                    "class": f"tab tab-{TRACKS[name]}" if track else "tab"})
                if track:
                    btn.set("data-track", TRACKS[name])
                btn.text = name
                panel = etree.SubElement(wrap, "section", {"class": "tabpanel", "role": "tabpanel", "id": pid,
                                                           "aria-labelledby": tid, "tabindex": "0"})
                if track:
                    panel.set("data-track", TRACKS[name])
                label = etree.SubElement(panel, "p", {"class": "panel-label"})
                if track:
                    pill = etree.SubElement(label, "span", {"class": f"trk trk-{TRACKS[name]}"})
                    pill.text, pill.tail = name, " 트랙"
                else:
                    label.text = name
                label.tail = block.text
                for child in list(block):
                    panel.append(child)
            parent = parents[ts]
            idx = list(parent).index(ts)
            parent.remove(ts)
            wrap.tail = ts.tail
            parent.insert(idx, wrap)

    @staticmethod
    def prepend_kind(el, label):
        span = etree.Element("span", {"class": "adm-kind"})
        span.text = label
        span.tail = " " + (el.text or "").lstrip()
        el.text = None
        el.insert(0, span)

    def boxes(self, root):
        for d in root.iter("details"):
            summary = d.find("summary")
            text = "".join(summary.itertext()) if summary is not None else ""
            kinds = self.classes(d)
            if self.key.startswith("lab") and "펼쳐서 복사" in text:
                d.set("class", " ".join(kinds + ["prompt-box"]))   # 사이트처럼 접어 둔다(라이브러리에 펼친 원문)
                label = "프롬프트"
            else:
                d.set("open", "open")
                label = KIND_KO.get(kinds[0] if kinds else "", "")
            if summary is not None and label:
                self.prepend_kind(summary, label)
        for div in root.iter("div"):
            cls = self.classes(div)
            if "admonition" not in cls:
                continue
            kind = next((c for c in cls if c != "admonition"), "note")
            title = next((c for c in div if c.tag == "p" and "admonition-title" in self.classes(c)), None)
            if title is not None and (title.text or "").strip() in ADM_DEFAULT_TITLES and not len(title):
                title.text = KIND_KO.get(kind, "참고")
            elif title is not None and kind != "abstract":
                self.prepend_kind(title, KIND_KO.get(kind, "참고"))
            if kind not in ("abstract", "quote"):
                div.set("role", "note")

    def tables(self, root):
        parents = self.parents(root)
        for t in list(root.iter("table")):
            heads = ["".join(th.itertext()).strip() for th in t.iter("th")]
            first = next(t.iter("tr"), None)
            ncols = len(list(first)) if first is not None else 0
            t.set("class", f"cols-{ncols}")
            label = "표: " + " · ".join(h for h in heads if h)[:80] if heads else "표"
            wrap = etree.Element("div", {"class": "table-wrap", "role": "region", "tabindex": "0", "aria-label": label})
            parent = parents[t]
            idx = list(parent).index(t)
            parent.remove(t)
            wrap.tail, t.tail = t.tail, None
            wrap.append(t)
            parent.insert(idx, wrap)

    def stages(self, root):
        """'**1단계 — …**'처럼 굵은 글씨만 있는 문단 → 단계 머리(class=stage)."""
        for p in root.iter("p"):
            kids = list(p)
            if (len(kids) == 1 and kids[0].tag == "strong" and not (p.text or "").strip()
                    and not (kids[0].tail or "").strip() and not p.get("class")):
                p.set("class", "stage")


class _PreviewTree(Treeprocessor):
    def __init__(self, md, ctx):
        super().__init__(md)
        self.ctx = ctx

    def run(self, root):
        self.ctx.transform(root)


class PreviewExtension(Extension):
    def __init__(self, ctx, **kwargs):
        self.ctx = ctx
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # toc(5)·tab_slugs(4)가 id를 정한 뒤, unescape(0) 전에 돈다
        md.treeprocessors.register(_PreviewTree(md, self.ctx), "preview", 2)


# ---------------------------------------------------------------- 렌더된 HTML 다듬기(문자열 단계)
def pill(name: str) -> str:
    return f'<span class="trk trk-{TRACKS[name]}">{name}</span>'


def post_html(text: str, key: str) -> tuple[str, int]:
    text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.S)                      # 자동 생성 주석
    counter = itertools.count(1)

    def task(m):  # pymdownx.tasklist는 체크박스를 원문 HTML로 넣는다 → id와 <label>을 붙인다
        cid = f"{key}-check{next(counter)}"
        checked = " checked" if m.group(1) else ""
        return (f'<li class="task-list-item"><input type="checkbox" id="{cid}"{checked}>'
                f'<label for="{cid}">{m.group(2).strip()}</label></li>')

    text = re.sub(r'<li class="task-list-item"><input type="checkbox"( checked)?\s*/?>(.*?)</li>', task, text, flags=re.S)
    text = re.sub(r"<h([1-6])\b([^>]*)>(.*?)</h\1>",                           # 제목 안의 트랙 이모지는 지운다
                  lambda m: f"<h{m.group(1)}{m.group(2)}>{EMOJI_RE.sub('', m.group(3))}</h{m.group(1)}>",
                  text, flags=re.S)
    for emo, name in TRACK_EMOJI.items():                                      # 나머지는 슬라이드와 같은 트랙 알약
        text = re.sub(re.escape(emo) + r"️?\s*(?:<strong>" + name + r"</strong>|" + name + r"(?![A-Za-z]))",
                      pill(name), text)
        text = re.sub(re.escape(emo) + r"️?", pill(name), text)
    text, todo = re.subn(r"\[([^\[\]<>\n]{0,60}강사 입력[^\[\]<>\n]{0,30})\]",
                         r'<mark class="todo">[\1]</mark>', text)
    return text, todo


# ---------------------------------------------------------------- 페이지 하나 렌더
class Page:
    def __init__(self, key, rel, group, html_body, title, sections, src):
        self.key, self.rel, self.group = key, rel, group
        self.body, self.title, self.sections, self.src = html_body, title, sections, src


def render_pages(exts, conf, titles, prompts) -> tuple[list[Page], int]:
    conf = {**conf, "pymdownx.superfences": {**conf.get("pymdownx.superfences", {}), "custom_fences": [
        {"name": "*", "class": "codeblock", "format": make_fence(prompts)}]}}
    pages, todo_total = [], 0
    for key, rel, group in PAGES:
        src = (DOCS / rel).read_text(encoding="utf-8")
        ctx = PageCtx(key, rel, titles)
        md = markdown.Markdown(extensions=exts + [PreviewExtension(ctx)], extension_configs=conf)
        try:
            body = md.convert(src)
        except Exception as exc:  # 스니펫 파일이 없을 때가 대부분
            raise SystemExit(f"[build_preview] {rel} 변환 실패: {exc}\n"
                             f"  → 먼저 `python tools/sync_site_assets.py`로 docs/_snippets/day1/을 만드세요.") from exc
        body, todo = post_html(body, key)
        todo_total += todo
        h1 = next((t for t in md.toc_tokens if t.get("level") == 1), None)
        title = strip_track_emoji(html.unescape(h1["name"])) if h1 else titles.get(rel, key)
        sections = [(scoped_id(key, t["id"]), strip_track_emoji(html.unescape(t["name"])))
                    for t in (h1["children"] if h1 else md.toc_tokens) if t.get("level") == 2]
        pages.append(Page(key, rel, group, body, title, sections, src))
    return pages, todo_total


# ---------------------------------------------------------------- 부록: 정답 차트(강사 전용)
def chart_figures() -> tuple[str, list[Path]]:
    figs, used = [], []
    for i, (stem, title, alt, use) in enumerate(CHARTS, 1):
        png, data = CHART_DIR / f"{stem}.png", CHART_DIR / f"{stem}.csv"
        if not png.exists():
            print(f"[build_preview] 경고: {png.relative_to(REPO)} 없음 — 이 차트는 건너뜁니다")
            continue
        used += [png] + ([data] if data.exists() else [])
        raw = png.read_bytes()
        w, h = int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
        uri = "data:image/png;base64," + base64.b64encode(raw).decode("ascii")
        table = chart_table(data, title) if data.exists() else ""
        figs.append(
            f'<figure class="chart" id="{APPENDIX_ID}-fig{i}">'
            f'<img src="{uri}" width="{w}" height="{h}" alt="{html.escape(alt)}" decoding="async">'
            f'<figcaption><p class="chart-title"><span class="chart-no">차트 {i}</span>{html.escape(title)}</p>'
            f'<p class="chart-use">{html.escape(use)}</p>{table}</figcaption></figure>')
    return "\n".join(figs), used


def chart_table(path: Path, title: str) -> str:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return ""
    cols = list(rows[0].keys())

    def cell(col, val):
        val = (val or "").strip()
        if col in PCT_COLS and val:
            return f'<td class="num">{float(val) * 100:.1f}%</td>'
        if col in MONEY_COLS and val:
            return f'<td class="num">{float(val):,.0f}</td>'
        if col == "dpd_to" and not val:
            return '<td class="num">이상</td>'
        if re.fullmatch(r"-?\d+(\.0+)?", val):
            return f'<td class="num">{int(float(val)):,}</td>'
        return f"<td>{html.escape(val)}</td>"

    text_cols = ("payment_method", "country_code", "region", "bucket")
    num_attr = ' class="num"'
    head = "".join(f'<th{"" if c in text_cols else num_attr}>{html.escape(CHART_COLS.get(c, c))}</th>' for c in cols)
    body = "".join("<tr>" + "".join(cell(c, r.get(c)) for c in cols) + "</tr>" for r in rows)
    return (f'<details class="chart-data"><summary>표로 보기</summary>'
            f'<div class="table-wrap" role="region" tabindex="0" aria-label="표: {html.escape(title)}">'
            f'<table class="cols-{len(cols)}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></details>')


# ---------------------------------------------------------------- 조립
def build(out: Path, with_charts: bool) -> Path:
    cfg, exts, conf = load_site_config()
    titles = nav_titles(cfg["nav"])
    prompts = library_prompts()
    pages, todo = render_pages(exts, conf, titles, prompts)
    figures, chart_files = chart_figures() if with_charts and CHART_DIR.exists() else ("", [])
    if with_charts and not figures:
        print("[build_preview] 경고: 정답 차트가 없어 부록 없이 만듭니다(공개 저장소 복제본이면 정상)")

    sources = [DOCS / rel for _, rel, _ in PAGES] + [PROMPTS_SRC] + sorted(SNIPPETS.glob("*.md")) + chart_files
    digest = hashlib.sha256()
    for p in sources:
        digest.update(p.read_bytes())
    site_name = cfg["site_name"]

    # 오후 실습 흐름(실습 페이지의 '한눈에 보기' 표에서 읽는다)
    flow, eyebrows = [], {"day1": "개요", "prompts": "프롬프트", "ax": "참고", "data": "참고", "faq": "참고"}
    for pg in pages:
        if not pg.key.startswith("lab"):
            continue
        rows = abstract_rows(pg.src)
        nav = titles.get(pg.rel, pg.key)
        head, _, rest = nav.partition(" ")
        time_html = inline_md(rows.get("시간", ""))
        eyebrows[pg.key] = "실습 · " + html.unescape(re.sub(r"<[^>]+>", "", time_html))
        flow.append(f'<li><a href="#{pg.key}"><span class="flow-key">{html.escape(head)}</span>'
                    f'<span class="flow-title">{html.escape(rest or nav)}</span>'
                    f'<span class="flow-time">{time_html}</span>'
                    f'<span class="flow-out">{inline_md(rows.get("산출물", ""))}</span></a></li>')

    # 목차
    toc = ['<nav class="toc" id="toc" aria-label="목차"><p class="toc-title">목차</p>']
    groups = collections.OrderedDict()
    for pg in pages:
        groups.setdefault(pg.group, []).append(pg)
    for gname, items in groups.items():
        toc.append(f'<div class="toc-group"><p class="toc-group-title">{gname}</p><ol class="toc-pages">')
        for pg in items:
            label = html.escape(strip_track_emoji(titles.get(pg.rel, pg.title)))
            subs = "".join(f'<li><a href="#{sid}">{html.escape(name)}</a></li>' for sid, name in pg.sections)
            toc.append(f'<li><a href="#{pg.key}">{label}</a>'
                       + (f'<ol class="toc-sections">{subs}</ol>' if subs else "") + "</li>")
        toc.append("</ol></div>")
    if figures:
        toc.append('<div class="toc-group"><p class="toc-group-title">강사 전용</p><ol class="toc-pages">'
                   f'<li><a href="#{APPENDIX_ID}">부록 · Day1 정답 차트</a></li></ol></div>')
    toc.append("</nav>")

    # 본문
    main = ['<main class="guide" id="main">']
    for pg in pages:
        main.append(f'<section class="doc" id="{pg.key}" aria-labelledby="{pg.key}--title">'
                    f'<header class="doc-head"><p class="eyebrow">{html.escape(eyebrows.get(pg.key, ""))}</p>'
                    f'<h2 class="doc-title" id="{pg.key}--title">{html.escape(pg.title)}</h2></header>')
        main.append(pg.body)
        main.append('<p class="back"><a href="#toc">목차로</a></p></section>')
    if figures:
        main.append(
            f'<section class="doc appendix" id="{APPENDIX_ID}" aria-labelledby="{APPENDIX_ID}--title">'
            '<header class="doc-head"><p class="eyebrow">강사 전용 · 수강생 사이트에 없음</p>'
            f'<h2 class="doc-title" id="{APPENDIX_ID}--title">부록 · Day1 정답 차트</h2></header>'
            '<div class="admonition warning" role="note"><p class="admonition-title"><span class="adm-kind">주의</span> '
            '실습 전에 공개하지 않는 차트입니다</p>'
            '<p>이 차트 4개는 <code>docs/assets/day1/</code>에 있고, 사이트 빌드(<code>mkdocs.yml</code>의 '
            '<code>exclude_docs</code>)와 공개 저장소(<code>.gitignore</code>)에서 빠져 있습니다. 차트 1–3은 정제한 '
            '150개사 기준이라, 원천 153행으로 만든 수강생 피벗과 숫자가 다를 수 있습니다. 차트 4는 인보이스 원장 기준입니다.</p>'
            '</div>' + figures + '<p class="back"><a href="#toc">목차로</a></p></section>')
    main.append("</main>")

    notes = [
        f'<li>트랙 탭({pill("Basic")} {pill("Standard")} {pill("Challenge")})은 한 곳에서 고르면 모든 실습이 같은 트랙으로 '
        "바뀝니다(사이트와 같습니다). 키보드로는 ←·→ 키로 옮깁니다.</li>",
        "<li>실습 안의 '펼쳐서 복사' 상자는 사이트처럼 접혀 있습니다. 같은 프롬프트가 프롬프트 라이브러리에 펼쳐져 있습니다.</li>",
        "<li>파일 받기 버튼 자리에는 파일 경로를 적었습니다. 파일은 과정 사이트에서 받습니다.</li>",
        '<li><span class="xref-tag">사이트</span> 표시가 붙은 말은 이 미리보기에 없는 사이트 페이지(사전 준비 · 레퍼런스)로 가는 '
        "링크입니다.</li>",
    ]
    if todo:
        notes.append(f'<li><mark class="todo">노란 표시</mark>는 강사가 채울 자리입니다({todo}곳).</li>')
    if figures:
        notes.append(f'<li>부록의 <a href="#{APPENDIX_ID}">정답 차트 4개</a>에는 정답 숫자가 있습니다. '
                     "이 페이지는 수강생에게 공유하지 않습니다.</li>")

    n_src = len([p for p in sources if p.suffix == ".md"])
    masthead = (
        '<header class="masthead">'
        f'<p class="eyebrow">{html.escape(site_name)} · 강사 검토용</p>'
        f"<h1>{PAGE_TITLE}</h1>"
        f'<p class="lede">수강생 사이트의 Day1 페이지 {len(pages)}개(개요 · Lab1–3 · 프롬프트 라이브러리 · 내 AX 프로젝트 · '
        "데이터 · FAQ)를 한 페이지로 모았습니다. 사이트와 같은 원본 md에서 만들어서 글이 같습니다.</p>"
        f'<ol class="flow" aria-label="오후 실습 순서">{"".join(flow)}</ol>'
        '<div class="toolbar"><button type="button" class="btn-toggle" id="expand-all" aria-pressed="false">'
        '모두 펼쳐 보기</button><p class="toolbar-note">세 트랙과 접힌 상자를 한꺼번에 엽니다. 한 번 더 누르면 돌아갑니다.</p></div>'
        f'<ul class="notes">{"".join(notes)}</ul>'
        f'<p class="meta">만든 날 {dt.date.today().isoformat()} · 원본 md {n_src}개 · 원본 해시 '
        f"<code>{digest.hexdigest()[:10]}</code></p></header>")
    colophon = ('<footer class="colophon"><p><code>tools/build_preview.py</code>가 사이트 원본(docs/day1 · docs/prompts · '
                "docs/ax-project.md · docs/data.md · docs/faq.md · docs/_snippets/day1의 파일 표)으로 만듭니다. 원본을 고친 뒤 "
                "<code>python tools/sync_site_assets.py</code> → <code>python tools/build_preview.py</code> 순서로 다시 만듭니다."
                "</p></footer>")

    doc = "\n".join([
        f"<title>{PAGE_TITLE}</title>",
        f'<link rel="stylesheet" href="{html.escape(FONTS_HREF)}">',
        f"<style>{CSS}</style>",
        "<script>document.documentElement.classList.add('js');</script>",
        '<div class="page">',
        '<a class="skip" href="#main">본문으로 건너뛰기</a>',
        masthead,
        '<div class="layout">',
        "".join(toc),
        "\n".join(main),
        "</div>",
        colophon,
        "</div>",
        '<div class="visually-hidden" id="live" aria-live="polite"></div>',
        f"<script>{JS}</script>",
        "",
    ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    return out


# ---------------------------------------------------------------- 검사
class _Checker(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.errors: list[str] = []
        self.ids: collections.Counter = collections.Counter()
        self.hrefs: list[str] = []
        self.tags: collections.Counter = collections.Counter()
        self.resources: list[tuple[str, str]] = []
        self.code_blocks: list[tuple[str | None, str]] = []   # (페이지 키, 코드 글자)
        self._capture: list[str] | None = None
        self._section: list[tuple[int, str]] = []

    def handle_decl(self, decl):
        self.errors.append(f"선언문 금지: <!{decl}>")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags[tag] += 1
        if tag in ("html", "head", "body"):
            self.errors.append(f"<{tag}> 태그 금지 {self.getpos()}")
        if "download" in a:
            self.errors.append(f"download 속성 금지 {self.getpos()}")
        if a.get("id"):
            self.ids[a["id"]] += 1
        if tag in ("input", "select", "textarea") and not a.get("id"):
            self.errors.append(f"id 없는 <{tag}> {self.getpos()}")
        if tag == "button" and a.get("type") != "button":
            self.errors.append(f'type="button" 없는 <button> {self.getpos()}')
        if tag == "a" and a.get("href") is not None:
            self.hrefs.append(a["href"])
        if tag == "link":
            self.resources.append(("link", a.get("href") or ""))
        if tag in ("script", "img", "iframe", "source", "video", "audio", "embed", "object") and (a.get("src") or a.get("data")):
            self.resources.append((tag, a.get("src") or a.get("data") or ""))
        if tag == "section" and "doc" in (a.get("class") or "").split():
            self._section.append((len(self.stack), a.get("id") or ""))
        if tag == "code" and self.stack and self.stack[-1][0] == "pre":
            self._capture = []
        if tag not in self.VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if tag == "code" and self._capture is not None:
            sec = self._section[-1][1] if self._section else None
            self.code_blocks.append((sec, "".join(self._capture)))
            self._capture = None
        if not self.stack:
            self.errors.append(f"짝 없는 </{tag}> {self.getpos()}")
            return
        if self.stack[-1][0] != tag:
            self.errors.append(f"</{tag}>가 <{self.stack[-1][0]}> {self.stack[-1][1]}를 닫음 {self.getpos()}")
            names = [t for t, _ in self.stack]
            if tag in names:
                while self.stack and self.stack[-1][0] != tag:
                    self.stack.pop()
            else:
                return
        self.stack.pop()
        while self._section and self._section[-1][0] >= len(self.stack):
            self._section.pop()

    def handle_data(self, data):
        if self._capture is not None:
            self._capture.append(data)


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    if not text.startswith(f"<title>{PAGE_TITLE}</title>"):
        problems.append(f"파일이 <title>{PAGE_TITLE}</title>로 시작하지 않음")
    ck = _Checker()
    ck.feed(text)
    ck.close()
    problems += ck.errors
    if ck.stack:
        problems.append("닫히지 않은 태그: " + ", ".join(f"<{t}> {pos}" for t, pos in ck.stack[:8]))
    if ck.tags["style"] != 1:
        problems.append(f"<style>이 {ck.tags['style']}개(1개여야 함)")
    if ck.tags["title"] != 1:
        problems.append(f"<title>이 {ck.tags['title']}개")
    for kind, url in ck.resources:
        if kind == "link" and not url.startswith("https://fonts.googleapis.com/"):
            problems.append(f"허용되지 않은 <link>: {url[:80]}")
        if kind != "link" and not url.startswith("data:"):
            problems.append(f"외부 자원 금지: <{kind}> {url[:80]}")
    dup = [i for i, n in ck.ids.items() if n > 1]
    if dup:
        problems.append(f"id 중복 {len(dup)}개: {', '.join(dup[:8])}")
    internal = [h[1:] for h in ck.hrefs if h.startswith("#")]
    missing = sorted({unquote(h) for h in internal if unquote(h) not in ck.ids})
    if missing:
        problems.append(f"대상 없는 내부 링크 {len(missing)}개: {', '.join(missing[:10])}")
    if any("downloads/" in h for h in ck.hrefs):
        problems.append("받기 링크(downloads/)가 남아 있음")
    if re.search("[\U0001F7E2\U0001F535\U0001F7E3]", text):
        problems.append("트랙 이모지(🟢🔵🟣)가 남아 있음")
    if "\x02" in text or "\x03" in text or "wzxhzdk" in text:
        problems.append("마크다운 임시 자리표시(htmlStash)가 남아 있음")
    if "--8<--" in text:
        problems.append("스니펫 표시(--8<--)가 남아 있음")
    n_copy = text.count('class="copy-btn"')
    if n_copy != len(ck.code_blocks):
        problems.append(f"코드 블록 {len(ck.code_blocks)}개 · 복사 버튼 {n_copy}개 — 수가 다름")
    prompts = library_prompts()
    in_lib = {norm_code(c) for sec, c in ck.code_blocks if sec == "prompts"}
    anywhere = {norm_code(c) for _, c in ck.code_blocks}
    lost = [n for n, p in prompts.items() if p["body"] not in anywhere]
    not_lib = [n for n, p in prompts.items() if p["body"] not in in_lib]
    if lost:
        problems.append(f"라이브러리 프롬프트가 빠짐: {', '.join(lost)}")
    if not_lib:
        problems.append(f"프롬프트 라이브러리 절에 없는 프롬프트: {', '.join(not_lib)}")
    size = path.stat().st_size
    if size > 16 * 1024 * 1024:
        problems.append(f"파일이 16MB를 넘음({size / 1e6:.1f}MB)")
    summary = (f"태그 {sum(ck.tags.values())}개 · id {len(ck.ids)}개 · 내부 링크 {len(internal)}개 · "
               f"코드 블록 {len(ck.code_blocks)}개(복사 버튼 {n_copy}개) · 라이브러리 프롬프트 "
               f"{len(prompts) - len(not_lib)}/{len(prompts)} · 이미지 {ck.tags['img']}개 · {size / 1024:,.0f} KB")
    print(f"[build_preview] 검사: {summary}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Day1 실습 가이드 한 페이지 미리보기(강사 검토용)")
    ap.add_argument("--out", type=Path, default=None, help=f"출력 경로(기본: {DEFAULT_OUT})")
    ap.add_argument("--no-charts", action="store_true", help="부록(정답 차트) 없이 만든다")
    ap.add_argument("--check", action="store_true", help="새로 만들지 않고 이미 있는 파일만 검사한다")
    args = ap.parse_args(argv)
    out = args.out
    if out is None:
        if not INSTRUCTOR_DAY1.exists():
            print(f"[build_preview] {INSTRUCTOR_DAY1}가 없습니다. --out으로 출력 경로를 지정하세요.")
            return 2
        out = DEFAULT_OUT
    out = out.resolve()
    if not args.check:
        build(out, with_charts=not args.no_charts)
        print(f"[build_preview] 만듦: {out}")
    elif not out.exists():
        print(f"[build_preview] 검사할 파일이 없습니다: {out}")
        return 2
    problems = check(out)
    for p in problems:
        print(f"  ✘ {p}")
    print("[build_preview] " + ("통과" if not problems else f"실패 {len(problems)}건"))
    return 0 if not problems else 1


# ---------------------------------------------------------------- 스타일(토큰 → 컴포넌트)
CSS = r"""
/* 배치: 종이 업무 문서 — 넓은 화면은 왼쪽에 따라 내려오는 목차, 오른쪽에 읽기 칼럼 하나 · 좁은 화면은 한 칼럼 */
:root {
  --bg: #F6F5F1; --sheet: #FFFDF8; --sunk: #ECEAE3; --fg: #13203A; --muted: #5B6475;
  --line: #D9D6CC; --line-strong: #BDB9AD;
  --accent: #1F5FD1; --accent-ink: #16469E; --accent-soft: #EEF3FC; --accent-line: #C5D6F6; --on-accent: #FFFFFF;
  --warn: #C2410C; --warn-soft: #FBF0E9; --warn-line: #EBC7B2; --on-warn: #FFFFFF;
  --code-bg: #FFFDF8; --todo-bg: #FDEBA6;
  --trk-basic-bg: #ECEAE3; --trk-basic-fg: #13203A; --trk-basic-line: #D9D6CC;
  --trk-std-bg: #D6E4FB; --trk-std-fg: #13203A; --trk-std-line: #B7CDF5;
  --trk-chl-bg: #13203A; --trk-chl-fg: #F6F5F1; --trk-chl-line: #13203A;
  --font-text: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-code: "Nanum Gothic Coding", "D2Coding", ui-monospace, "SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #11161F; --sheet: #171D29; --sunk: #222A38; --fg: #ECEAE3; --muted: #A2AABA;
    --line: #2C3444; --line-strong: #465066;
    --accent: #7FAAF6; --accent-ink: #B9D0FA; --accent-soft: #172440; --accent-line: #2C4572; --on-accent: #0D1320;
    --warn: #F2945F; --warn-soft: #2A1C16; --warn-line: #6A3B25; --on-warn: #160E0A;
    --code-bg: #141A25; --todo-bg: #4D3F12;
    --trk-basic-bg: #262E3D; --trk-basic-fg: #ECEAE3; --trk-basic-line: #3B4558;
    --trk-std-bg: #1E3560; --trk-std-fg: #E4EDFE; --trk-std-line: #2D4C85;
    --trk-chl-bg: #ECEAE3; --trk-chl-fg: #13203A; --trk-chl-line: #ECEAE3;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #11161F; --sheet: #171D29; --sunk: #222A38; --fg: #ECEAE3; --muted: #A2AABA;
  --line: #2C3444; --line-strong: #465066;
  --accent: #7FAAF6; --accent-ink: #B9D0FA; --accent-soft: #172440; --accent-line: #2C4572; --on-accent: #0D1320;
  --warn: #F2945F; --warn-soft: #2A1C16; --warn-line: #6A3B25; --on-warn: #160E0A;
  --code-bg: #141A25; --todo-bg: #4D3F12;
  --trk-basic-bg: #262E3D; --trk-basic-fg: #ECEAE3; --trk-basic-line: #3B4558;
  --trk-std-bg: #1E3560; --trk-std-fg: #E4EDFE; --trk-std-line: #2D4C85;
  --trk-chl-bg: #ECEAE3; --trk-chl-fg: #13203A; --trk-chl-line: #ECEAE3;
  color-scheme: dark;
}

[hidden] { display: none !important; }
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--font-text); font-size: 1rem; line-height: 1.75; }
.page { padding-inline: clamp(1rem, 3.2vw, 2.5rem); padding-block: 1.25rem 4rem; }
.masthead, .layout, .colophon { max-width: 74rem; margin-inline: auto; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
a { color: var(--accent); text-decoration-line: underline; text-decoration-thickness: 1px; text-underline-offset: .22em; }
a:hover { text-decoration-thickness: 2px; }
[id] { scroll-margin-top: 1rem; }
.skip { position: absolute; left: 1rem; top: 0; z-index: 10; transform: translateY(-120%); padding: .5rem .9rem;
  border-radius: 0 0 6px 6px; background: var(--fg); color: var(--bg); font-weight: 700; text-decoration: none; }
.skip:focus { transform: none; }
.visually-hidden { position: absolute !important; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0;
  overflow: hidden; clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
.eyebrow { margin: 0; font-size: .78rem; font-weight: 700; letter-spacing: .06em; color: var(--muted); }

/* 머리말 */
.masthead { padding-block: .5rem 2rem; margin-bottom: 2rem; border-bottom: 1px solid var(--line); word-break: keep-all; overflow-wrap: break-word; }
.masthead h1 { margin: .35rem 0 .6rem; font-size: clamp(2rem, 1.4rem + 2.4vw, 3rem); line-height: 1.15;
  letter-spacing: -0.02em; font-weight: 700; color: var(--fg); text-wrap: balance; }
.lede { margin: 0 0 1.5rem; max-width: 46rem; font-size: 1.06rem; }
.flow { list-style: none; margin: 0 0 1.5rem; padding: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: 1px;
  background: var(--line); border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }
@media (min-width: 46rem) { .flow { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
.flow li { background: var(--sheet); min-width: 0; }
.flow a { display: grid; align-content: start; gap: .15rem; height: 100%; box-sizing: border-box; padding: .85rem 1rem 1rem;
  color: var(--fg); text-decoration: none; }
.flow a:hover .flow-title { text-decoration: underline; text-underline-offset: .2em; }
.flow-key { font-size: .75rem; font-weight: 700; letter-spacing: .08em; color: var(--accent); }
.flow-title { font-weight: 700; font-size: 1.02rem; }
.flow-time { font-size: .9rem; font-variant-numeric: tabular-nums; }
.flow-out { font-size: .82rem; color: var(--muted); }
.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem 1rem; margin-bottom: 1rem; }
.btn-toggle { font: inherit; font-size: .92rem; font-weight: 700; min-height: 2.5rem; padding: .45rem 1rem; border-radius: 6px;
  border: 1px solid var(--fg); background: transparent; color: var(--fg); cursor: pointer; }
.btn-toggle:hover { background: var(--sunk); }
.btn-toggle[aria-pressed="true"] { background: var(--fg); color: var(--bg); }
.toolbar-note { margin: 0; font-size: .86rem; color: var(--muted); }
.notes { margin: 0 0 1rem; padding-left: 1.15rem; max-width: 52rem; font-size: .9rem; color: var(--muted); }
.notes li { margin-block: .25rem; }
.meta { margin: 0; font-size: .8rem; color: var(--muted); }

/* 배치 */
.layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: 2rem 3rem; align-items: start; }
.guide { min-width: 0; max-width: 52rem; word-break: keep-all; overflow-wrap: break-word; }
.toc { min-width: 0; font-size: .88rem; line-height: 1.5; word-break: keep-all; }
.toc-title { margin: 0 0 .5rem; font-weight: 700; font-size: .95rem; }
.toc-group + .toc-group { margin-top: 1rem; }
.toc-group-title { margin: 0 0 .25rem; font-size: .72rem; font-weight: 700; letter-spacing: .08em; color: var(--muted); }
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc a { display: block; padding: .28rem .55rem; border-radius: 4px; color: var(--fg); text-decoration: none; }
.toc a:hover { background: var(--sunk); }
.toc-pages > li > a { font-weight: 700; }
.toc-sections { margin: .1rem 0 .45rem; }
.toc-sections a { padding-left: 1.1rem; font-size: .84rem; color: var(--muted); }
.toc a.is-current-page { color: var(--accent-ink); }
.toc a[aria-current] { background: var(--accent-soft); color: var(--accent-ink); font-weight: 700; }
@media (min-width: 70rem) {
  .layout { grid-template-columns: 15rem minmax(0, 1fr); }
  .toc { position: sticky; top: env(safe-area-inset-top, 0px); max-height: calc(100vh - env(safe-area-inset-top, 0px));
    overflow-y: auto; overscroll-behavior: contain; box-sizing: border-box; padding-block: .5rem 2rem; }
}
@media (max-width: 69.99rem) {
  .toc { padding: .85rem 1rem; border: 1px solid var(--line); border-radius: 6px; background: var(--sheet); }
  .toc-sections { display: none; }
  .toc-pages { display: grid; grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr)); gap: .1rem .5rem; }
}

/* 페이지 머리와 제목 */
.doc { margin-bottom: 4.5rem; }
.doc-head { margin-bottom: 1.5rem; padding-top: 1.1rem; border-top: 3px solid var(--fg); }
.doc-title { margin: .4rem 0 0; font-size: clamp(1.45rem, 1.2rem + 1vw, 1.9rem); line-height: 1.3; letter-spacing: -0.01em; text-wrap: balance; }
.guide h3, .guide h4, .guide h5, .guide h6 { color: var(--fg); line-height: 1.4; font-weight: 700; text-wrap: balance; }
.guide h3 { margin: 2.75rem 0 .9rem; font-size: 1.32rem; }
.guide h4 { margin: 2rem 0 .6rem; font-size: 1.1rem; }
.guide h5 { margin: 1.5rem 0 .5rem; font-size: 1rem; }
.headerlink { margin-left: .4rem; color: var(--line-strong); font-weight: 400; text-decoration: none; opacity: 0; }
.guide :is(h3, h4, h5):hover .headerlink, .headerlink:focus-visible { opacity: 1; }
.back { margin: 2rem 0 0; font-size: .85rem; }
.back a { color: var(--muted); }

/* 본문 요소 */
.guide p, .guide ul, .guide ol, .guide dl { margin: 0 0 1rem; }
.guide ul, .guide ol { padding-left: 1.6rem; }
.guide li { margin-block: .35rem; }
.guide li > p { margin-bottom: .5rem; }
.guide ol > li::marker { font-weight: 700; color: var(--muted); font-variant-numeric: tabular-nums; }
.guide ul > li::marker { color: var(--line-strong); }
.guide strong { font-weight: 700; }
.guide hr { margin: 2.5rem 0; border: 0; border-top: 1px solid var(--line); }
.guide blockquote { margin: 1.25rem 0; padding: .1rem 0 .1rem 1rem; border-left: 3px solid var(--line-strong); color: var(--muted); }
.guide blockquote > :last-child { margin-bottom: 0; }
.guide p.stage { margin: 1.75rem 0 .6rem; }
.stage > strong { font-size: 1.04rem; }
.guide .tabpanel p.stage { padding-top: 1rem; border-top: 1px solid var(--line); }
.guide .tabpanel p.panel-label + p.stage { margin-top: .25rem; padding-top: 0; border-top: 0; }
.guide .admonition p.stage { margin-top: .75rem; }
code, pre, kbd { font-family: var(--font-code); font-variant-ligatures: none; font-feature-settings: "liga" 0, "calt" 0; }
:not(pre) > code { padding: .1em .38em; border-radius: 4px; background: var(--sunk); color: var(--fg); font-size: .86em; overflow-wrap: anywhere; }
td code { word-break: break-all; }
kbd { padding: .05em .42em; border: 1px solid var(--line-strong); border-bottom-width: 2px; border-radius: 4px;
  background: var(--sheet); color: var(--fg); font-size: .8em; white-space: nowrap; }
.keys { white-space: nowrap; }
.keys > span { padding-inline: .1em; color: var(--muted); }
.twemoji { display: inline-flex; vertical-align: -0.15em; }
.twemoji svg { width: 1.1em; height: 1.1em; fill: currentColor; }
mark.todo { padding: 0 .2em; border-radius: 2px; background: var(--todo-bg); color: var(--fg); box-shadow: inset 0 -2px 0 var(--warn); }
.xref { text-decoration: underline dotted var(--line-strong); text-underline-offset: .22em; }
.xref-tag { display: inline-block; margin-left: .3em; padding: 0 .35em; border: 1px solid var(--line-strong); border-radius: 3px;
  font-size: .68em; font-weight: 700; line-height: 1.5; color: var(--muted); vertical-align: .12em; white-space: nowrap; }
.dl { display: inline-flex; flex-direction: column; align-items: flex-start; gap: .15rem; }
.dl-label { font-size: .76rem; font-weight: 700; color: var(--muted); white-space: nowrap; }
.guide code.dl-path { font-size: .76rem; }

/* 트랙 표시 — 슬라이드 D1-37~39의 알약과 같은 색 */
.trk { display: inline-block; padding: 0 .6em; border: 1px solid transparent; border-radius: 999px; font-size: .78em;
  font-weight: 700; line-height: 1.65; white-space: nowrap; vertical-align: .06em; }
.trk-basic { background: var(--trk-basic-bg); color: var(--trk-basic-fg); border-color: var(--trk-basic-line); }
.trk-standard { background: var(--trk-std-bg); color: var(--trk-std-fg); border-color: var(--trk-std-line); }
.trk-challenge { background: var(--trk-chl-bg); color: var(--trk-chl-fg); border-color: var(--trk-chl-line); }

/* 탭(트랙·페르소나) */
.tabs { margin: 1.25rem 0 2rem; }
.tablist { display: none; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; padding-bottom: .85rem; border-bottom: 1px solid var(--line); }
.js .tablist { display: flex; }
.tab { font: inherit; font-size: .95rem; font-weight: 700; min-height: 2.5rem; padding: .35rem 1.1rem; border-radius: 999px;
  border: 1px solid var(--line-strong); background: transparent; color: var(--muted); cursor: pointer; }
.tab:hover { border-color: var(--fg); color: var(--fg); }
.tab[aria-selected="true"] { background: var(--sunk); border-color: var(--line-strong); color: var(--fg); }
.tab-basic[aria-selected="true"] { background: var(--trk-basic-bg); border-color: var(--trk-basic-line); color: var(--trk-basic-fg); }
.tab-standard[aria-selected="true"] { background: var(--trk-std-bg); border-color: var(--trk-std-line); color: var(--trk-std-fg); }
.tab-challenge[aria-selected="true"] { background: var(--trk-chl-bg); border-color: var(--trk-chl-line); color: var(--trk-chl-fg); }
.guide p.panel-label { display: flex; align-items: center; gap: .45rem; margin: 1.75rem 0 .75rem; padding-top: .9rem;
  border-top: 2px solid var(--line); font-size: .9rem; font-weight: 700; color: var(--muted); }
.guide .tabpanel:first-of-type > p.panel-label { margin-top: .5rem; }
.js .guide p.panel-label { display: none; }
.js .tabs:not([data-ready]) > .tabpanel ~ .tabpanel { display: none; }
.js .guide.is-expanded p.panel-label { display: flex; }
.js .guide.is-expanded .tablist { display: none; }

/* 상자: 안내·주의·접는 상자 */
.admonition, .guide details { margin: 1.25rem 0; padding: .9rem 1.1rem; border: 1px solid var(--line); border-radius: 6px; background: var(--sheet); }
.admonition > :last-child, .guide details > :last-child { margin-bottom: 0; }
.guide p.admonition-title { display: flex; flex-wrap: wrap; align-items: baseline; gap: .25rem .55rem; margin: 0 0 .55rem; font-weight: 700; line-height: 1.5; }
.adm-kind { display: inline-block; padding: .02rem .45rem; border-radius: 4px; background: var(--sunk); color: var(--muted);
  font-size: .72rem; font-weight: 700; letter-spacing: .04em; line-height: 1.6; white-space: nowrap; }
.admonition:is(.tip, .info, .question) { background: var(--accent-soft); border-color: var(--accent-line); }
.admonition:is(.tip, .info, .question) .adm-kind { background: var(--accent); color: var(--on-accent); }
.admonition:is(.warning, .danger) { background: var(--warn-soft); border-color: var(--warn-line); }
.admonition:is(.warning, .danger) .adm-kind { background: var(--warn); color: var(--on-warn); }
.admonition.success { border-color: var(--fg); }
.admonition.success .adm-kind { background: var(--fg); color: var(--bg); }
.admonition.quote { background: transparent; }
.guide details > summary { display: flex; flex-wrap: wrap; align-items: center; gap: .25rem .55rem; cursor: pointer; font-weight: 700; line-height: 1.5; list-style: none; }
.guide details > summary::-webkit-details-marker { display: none; }
.guide details > summary::before { content: ""; flex: none; width: .42rem; height: .42rem; margin-right: .15rem;
  border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted); transform: rotate(-45deg); transition: transform .15s ease; }
.guide details[open] > summary::before { transform: rotate(45deg); }
.guide details[open] > summary { margin-bottom: .75rem; }
.guide details.prompt-box { border-color: var(--line-strong); }
.guide details.prompt-box > summary .adm-kind { background: var(--fg); color: var(--bg); }

/* 표 */
.table-wrap { margin: 1rem 0 1.25rem; overflow-x: auto; border: 1px solid var(--line); border-radius: 6px; background: var(--sheet); }
.table-wrap table { width: 100%; border-collapse: collapse; font-size: .9rem; line-height: 1.6; }
.table-wrap table.cols-4 { min-width: 38rem; }
.table-wrap table:is(.cols-5, .cols-6, .cols-7, .cols-8, .cols-9) { min-width: 44rem; }
.table-wrap th, .table-wrap td { padding: .5rem .75rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
.table-wrap th { background: var(--sunk); color: var(--fg); font-weight: 700; white-space: nowrap; }
.table-wrap tr:last-child > td { border-bottom: 0; }
.table-wrap :is(th, td).num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.admonition .table-wrap { background: var(--sheet); }

/* 코드·프롬프트 */
.codeblock { margin: .75rem 0 1.1rem; overflow: hidden; border: 1px solid var(--line); border-radius: 6px; background: var(--code-bg); }
.codebar { display: flex; align-items: center; justify-content: space-between; gap: .75rem; padding: .3rem .4rem .3rem .85rem;
  border-bottom: 1px solid var(--line); background: var(--sunk); }
.codelabel { min-width: 0; font-size: .78rem; font-weight: 700; color: var(--muted); }
.copy-btn { flex: none; font: inherit; font-size: .8rem; font-weight: 700; min-height: 2rem; padding: .2rem .85rem; border-radius: 4px;
  border: 1px solid var(--line-strong); background: var(--sheet); color: var(--fg); cursor: pointer; }
.copy-btn:hover { border-color: var(--accent); color: var(--accent); }
.copy-btn[data-state="ok"] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
.copy-btn[data-state="select"] { background: var(--warn-soft); border-color: var(--warn); color: var(--fg); }
.codeblock pre { margin: 0; padding: .85rem 1rem; overflow-x: auto; background: transparent; color: var(--fg); font-size: .88rem; line-height: 1.7;
  white-space: pre-wrap; word-break: normal; overflow-wrap: anywhere; tab-size: 4; }
.codeblock[data-kind="formula"] pre { white-space: pre; overflow-wrap: normal; }
.codeblock pre code { padding: 0; background: none; font-size: inherit; }

/* 할 일 목록 */
.guide .task-list { list-style: none; padding-left: 0; }
.task-list-item { display: flex; align-items: flex-start; gap: .6rem; }
.task-list-item input { flex: none; width: 1.05rem; height: 1.05rem; margin: .38rem 0 0; accent-color: var(--accent); }
.task-list-item label { min-width: 0; cursor: pointer; }

/* 부록 차트 */
.chart { margin: 1.75rem 0 2.75rem; }
.chart img { display: block; width: 100%; max-width: 100%; height: auto; border: 1px solid var(--line); border-radius: 6px; }
.chart figcaption { margin-top: .75rem; }
.guide p.chart-title { margin: 0 0 .2rem; font-weight: 700; }
.chart-no { margin-right: .5rem; font-size: .75rem; letter-spacing: .06em; color: var(--accent); }
.guide p.chart-use { margin: 0 0 .5rem; font-size: .9rem; color: var(--muted); }

.colophon { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: .82rem; color: var(--muted); word-break: keep-all; }
.colophon p { margin: 0; max-width: 52rem; }

@media (prefers-reduced-motion: reduce) {
  .guide details > summary::before { transition: none; }
}
@media print {
  .toc, .toolbar, .copy-btn, .skip, .back, .tablist { display: none !important; }
  .layout { display: block; }
  .tabpanel[hidden], .js .tabs > .tabpanel { display: block !important; }
  .js .panel-label { display: flex !important; }
}
"""

# ---------------------------------------------------------------- 동작(탭·펼치기·복사·목차 위치)
JS = r"""
(() => {
  'use strict';
  const root = document.documentElement;
  root.classList.add('js');
  const guide = document.getElementById('main');
  const live = document.getElementById('live');
  const store = {
    get(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* 저장소를 쓸 수 없는 창 */ } }
  };
  const KEY_TRACK = 'd1-guide-track';
  const KEY_EXPAND = 'd1-guide-expanded';
  const sets = Array.from(document.querySelectorAll('.tabs'));
  const tabsOf = (set) => Array.from(set.querySelector('.tablist').querySelectorAll('[role="tab"]'));
  const panelsOf = (set) => Array.from(set.children).filter((el) => el.getAttribute('role') === 'tabpanel');
  let expanded = false;

  function activate(set, index, focus) {
    const tabs = tabsOf(set);
    const panels = panelsOf(set);
    if (!(index >= 0 && index < tabs.length)) index = 0;
    tabs.forEach((tab, i) => {
      const on = i === index;
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      tab.tabIndex = on ? 0 : -1;
      if (on && focus) tab.focus();
    });
    panels.forEach((panel, i) => { panel.hidden = !expanded && i !== index; });
    set.dataset.active = String(index);
    set.dataset.ready = '1';
  }
  function selectTrack(track, origin, focus) {
    let found = false;
    sets.forEach((set) => {
      if (set.dataset.group !== 'track') return;
      const i = tabsOf(set).findIndex((t) => t.dataset.track === track);
      if (i >= 0) { found = true; activate(set, i, focus && set === origin); }
    });
    if (found) store.set(KEY_TRACK, track);
  }
  sets.forEach((set) => {
    const tabs = tabsOf(set);
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => {
        if (set.dataset.group === 'track') selectTrack(tab.dataset.track, set, false);
        else activate(set, i, false);
      });
      tab.addEventListener('keydown', (ev) => {
        const last = tabs.length - 1;
        let j = null;
        if (ev.key === 'ArrowRight') j = i === last ? 0 : i + 1;
        else if (ev.key === 'ArrowLeft') j = i === 0 ? last : i - 1;
        else if (ev.key === 'Home') j = 0;
        else if (ev.key === 'End') j = last;
        if (j === null) return;
        ev.preventDefault();
        if (set.dataset.group === 'track') selectTrack(tabs[j].dataset.track, set, true);
        else activate(set, j, true);
      });
    });
    activate(set, 0, false);
  });
  const savedTrack = store.get(KEY_TRACK);
  if (savedTrack) selectTrack(savedTrack, null, false);

  const toggle = document.getElementById('expand-all');
  function setExpanded(on, save) {
    expanded = on;
    guide.classList.toggle('is-expanded', on);
    if (toggle) toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
    guide.querySelectorAll('details').forEach((d) => {
      if (on) {
        if (d.dataset.was === undefined) d.dataset.was = d.open ? '1' : '0';
        d.open = true;
      } else if (d.dataset.was !== undefined) {
        d.open = d.dataset.was === '1';
        delete d.dataset.was;
      }
    });
    sets.forEach((set) => activate(set, Number(set.dataset.active || 0), false));
    if (save) store.set(KEY_EXPAND, on ? '1' : '0');
  }
  if (toggle) toggle.addEventListener('click', () => setExpanded(!expanded, true));
  if (store.get(KEY_EXPAND) === '1') setExpanded(true, false);

  function selectNode(node) {
    const sel = window.getSelection();
    if (!sel) return;
    const range = document.createRange();
    range.selectNodeContents(node);
    sel.removeAllRanges();
    sel.addRange(range);
  }
  function report(btn, text, state) {
    btn.textContent = text;
    btn.dataset.state = state;
    if (live) live.textContent = (btn.dataset.label || '코드') + ': ' + text;
    window.clearTimeout(btn._timer);
    btn._timer = window.setTimeout(() => { btn.textContent = '복사'; delete btn.dataset.state; }, 2500);
  }
  document.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.copy-btn');
    if (!btn) return;
    const code = btn.closest('.codeblock').querySelector('pre code');
    const text = code.textContent;
    const fallback = () => {
      selectNode(code);
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      report(btn, ok ? '복사됨' : '선택됨 · Ctrl+C', ok ? 'ok' : 'select');
    };
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      navigator.clipboard.writeText(text).then(() => report(btn, '복사됨', 'ok'), fallback);
    } else {
      fallback();
    }
  });

  const idFromHash = (hash) => {
    const raw = (hash || '').replace(/^#/, '');
    try { return decodeURIComponent(raw); } catch (e) { return raw; }
  };
  function reveal(id) {
    const el = id ? document.getElementById(id) : null;
    if (!el) return;
    const panel = el.closest('[role="tabpanel"]');
    if (panel && panel.hidden) {
      const set = panel.closest('.tabs');
      const i = panelsOf(set).indexOf(panel);
      if (set.dataset.group === 'track') selectTrack(tabsOf(set)[i].dataset.track, null, false);
      else activate(set, i, false);
    }
    let d = el.closest('details');
    while (d) { d.open = true; d = d.parentElement ? d.parentElement.closest('details') : null; }
  }
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('a[href^="#"]');
    if (a) reveal(idFromHash(a.getAttribute('href')));
  });
  window.addEventListener('hashchange', () => reveal(idFromHash(location.hash)));
  if (location.hash) {
    const id = idFromHash(location.hash);
    reveal(id);
    const target = document.getElementById(id);
    if (target) target.scrollIntoView();
  }

  const toc = document.getElementById('toc');
  const links = new Map();
  if (toc) toc.querySelectorAll('a[href^="#"]').forEach((a) => links.set(idFromHash(a.getAttribute('href')), a));
  const targets = Array.from(links.keys()).map((id) => document.getElementById(id)).filter(Boolean);
  let current = null;
  function markCurrent() {
    const limit = window.innerHeight * 0.25;
    let pick = null;
    for (const t of targets) {
      if (t.getBoundingClientRect().top <= limit) pick = t; else break;
    }
    const id = pick ? pick.id : null;
    if (id === current) return;
    current = id;
    links.forEach((a, key) => {
      if (key === id) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
    });
    toc.querySelectorAll('.is-current-page').forEach((x) => x.classList.remove('is-current-page'));
    const a = id ? links.get(id) : null;
    const pageLink = a ? a.closest('.toc-pages > li') : null;
    if (pageLink && pageLink.firstElementChild) pageLink.firstElementChild.classList.add('is-current-page');
    if (a && getComputedStyle(toc).position === 'sticky') {
      const y = a.offsetTop;
      if (y < toc.scrollTop + 24 || y > toc.scrollTop + toc.clientHeight - 48) toc.scrollTop = Math.max(0, y - toc.clientHeight / 3);
    }
  }
  if (toc && targets.length) {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => { ticking = false; markCurrent(); });
    }, { passive: true });
    markCurrent();
  }
})();
"""

if __name__ == "__main__":
    sys.exit(main())
