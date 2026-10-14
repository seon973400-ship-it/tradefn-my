"""MkDocs 훅 — 과정 사이트 빌드 보조 (mkdocs.yml의 `hooks:`에 등록돼 있다)

1) 내려받기 파일: MkDocs는 docs/ 안의 모든 .md 파일을 HTML 페이지로 바꾼다. 그런데 docs/downloads/ 아래의
   .md(보고서 발췌 irobot.md, 캔버스 양식 ax_canvas_template.md 등)는 수강생이 내려받아 AI에 올릴
   '원본 파일'이어야 한다. 그런 파일은 페이지로 만들지 않고 이름 그대로 복사한다.
2) 프롬프트 앵커: 제목이 프롬프트 ID로 시작하면(예: "## P1-4 EDA 요약표·차트·코드 공개") 주소 앵커를
   ID만으로 만든다(#p1-4). labs/day1/prompts.md의 제목 글자가 바뀌어도 실습 페이지의 링크가 깨지지 않는다.
   그 밖의 제목은 mkdocs.yml에 적은 대로 한글을 살린 앵커(pymdownx.slugs, 소문자)를 쓴다.
(플러그인 설치 없이 MkDocs 1.4+ 기본 기능인 hooks로 동작)
"""

from __future__ import annotations

import re

from mkdocs.structure.files import File, Files
from pymdownx.slugs import slugify as _make_slugify

DOWNLOAD_PREFIX = "downloads/"

_unicode_slugify = _make_slugify(case="lower")
_PROMPT_ID = re.compile(r"^\s*(P\d+-\d+[a-z]?)(?=[\s(]|$)", re.IGNORECASE)


def prompt_id_slugify(value: str, separator: str) -> str:
    """'P1-1b 두 시점 비교' → 'p1-1b', 그 밖의 제목은 한글을 살린 소문자 앵커."""
    m = _PROMPT_ID.match(value)
    if m:
        return m.group(1).lower()
    return _unicode_slugify(value, separator)


class DownloadFile(File):
    """내려받기용 파일: 확장자가 .md여도 렌더링하지 않고 같은 경로로 그대로 복사한다."""

    def is_documentation_page(self) -> bool:
        return False

    def is_static_page(self) -> bool:
        return False


def on_config(config):
    config.mdx_configs.setdefault("toc", {})["slugify"] = prompt_id_slugify
    return config


def on_files(files: Files, config) -> Files:
    for f in list(files):
        if f.src_uri.startswith(DOWNLOAD_PREFIX) and f.is_documentation_page():
            files.remove(f)
            files.append(
                DownloadFile(
                    f.src_uri,
                    f.src_dir,
                    f.dest_dir,
                    f.use_directory_urls,
                    dest_uri=f.src_uri,
                    inclusion=f.inclusion,
                )
            )
    return files
