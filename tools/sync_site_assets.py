#!/usr/bin/env python
"""과정 사이트 '파일 받기' — files 브랜치 색인(_index.json)을 읽어 내려받기 · ZIP · 카드 조각을 만든다.

사용 (저장소 루트에서, 표준 라이브러리만 사용):
    python tools/sync_site_assets.py                        # files 브랜치 작업 트리(_files)의 색인으로 전 일차
    python tools/sync_site_assets.py --day 2                # 2일차만 다시(다른 일차 결과는 그대로)
    python tools/sync_site_assets.py --files-root _files    # CI(.github/workflows/pages.yml)가 두 번째 checkout으로 만든 폴더
    python tools/sync_site_assets.py --check                # 아무것도 바꾸지 않고 상태만(색인의 파일이 빠졌으면 종료코드 1)
    python tools/sync_site_assets.py --check-links site     # 빌드한 site/에서 내려받기 링크가 실제 파일을 가리키는지
    python tools/sync_site_assets.py --now 2026-10-15T07:00:00Z   # 시각을 흉내 내 잠금 · ZIP을 미리 보기(점검용)

원칙
- 무엇을 어느 쪽에 보일지는 색인 하나가 정한다(files 브랜치 _index.json — 강사 PC의 instructor/release/files_build.py가 만든다).
  색인 항목: path · day · where(main = 템플릿에 있는 파일 / files = files 브랜치 / sealed = 봉인 묶음) · badge(필수 · 선택 · 참고 · 완성본 · 비교 기준)
  · practices(실습 구역) · label · desc · dest(받는 이름) · open_at(UTC) · site · zip · placeholder(아직 안 풀린 6일차 자리).
- 열기 시각(open_at)이 남은 파일은 사이트에 복사하되 카드에 data-tf-open(UTC)을 붙인다 — docs/javascripts/tf26.js가 그 시각까지 잠가 보인다
  (소프트 잠금: 수업 흐름을 지키는 장치이지 보안이 아니다). ZIP에는 빌드 시각에 열린 파일만 넣는다 — pages.yml이 각 열기 시각 뒤에 다시 빌드한다.
- 아직 안 풀린 6일차 파일은 링크 없는 잠긴 카드('자동 공개 · 시각')다. 풀리면 d6-release.yml이 사이트를 다시 만든다.
- 정답 원본 · 강사 자료 경로는 색인에 있어도 멈춘다(guard). 링크는 원시 HTML이라 mkdocs --strict가 보지 않는다 → --check-links.

결과물
    docs/downloads/dayN/<dest> · dayN_files.zip · dayN_<구역>.zip    (배포용 사본 — .gitignore)
    docs/_snippets/dayN/files_<구역>_cards.md   실습 쪽 '입력 파일 받기'   (--8<-- "docs/_snippets/dayN/files_lab-a_cards.md")
    docs/_snippets/dayN/files_all_cards.md      일차 개요 '파일 받기'
    docs/_snippets/dayN/files_pdf_cards.md      그날 슬라이드 PDF 카드
    docs/_snippets/dayN/files_all_root_cards.md 루트 쪽(docs/*.md)용 — 링크 접두 downloads/dayN/
    docs/_snippets/dayN/files_all.md · files_all_root.md · files_<구역>.md   예전 표(그대로 쓰는 쪽을 위해)
    docs/_snippets/after/…                      과정 뒤 공개(원천 · 생성기) — 10/21 19:00 뒤 ZIP 카드
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
DL_ROOT = DOCS / "downloads"
SNIP_ROOT = DOCS / "_snippets"
HEADER = "<!-- 자동 생성: tools/sync_site_assets.py — 직접 고치지 말고 스크립트를 다시 돌리세요 -->"
KST = dt.timezone(dt.timedelta(hours=9))
DAY_DATES = {1: (2026, 10, 14), 2: (2026, 10, 15), 3: (2026, 10, 16), 4: (2026, 10, 19), 5: (2026, 10, 20), 6: (2026, 10, 21),
             "after": (2026, 10, 21)}

# 경로에 이 조각이 들어 있으면 수강생용이 아니다 — 색인 실수 방지용 안전장치(빌드를 멈춘다)
FORBIDDEN_PARTS = ("instructor/", "answers/", "_clean", "dirt_log", "dirty_log", "code_table", "golden", "conflicts_answer_key",
                   "ksure_terms", "scorecard", "feedback_template", "us_chapter11", "_private", "release_key", "secrets.toml", "/.env")
# 이름에 정답 냄새가 나는 조각 — '비교 기준'(open_at 있음) · 과정 뒤 파일만 허용
BASELINE_ONLY = ("expected", "answer")
BADGE_RANK = {"필수": 0, "완성본": 1, "선택": 2, "참고": 3, "비교 기준": 4}
CHIP = {"필수": "tf-chip--must", "완성본": "tf-chip--file", "비교 기준": "tf-chip--ref", "선택": "tf-chip--opt", "참고": "tf-chip--opt"}


# ---------------------------------------------------------------- 작은 도구
def human_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB"
    return f"{max(1, round(n / 1024)):,} KB"


def parse_z(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def kst_label(s: str) -> str:
    t = parse_z(s).astimezone(KST)
    return f"{t.month}/{t.day}({'월화수목금토일'[t.weekday()]}) {t:%H:%M}"


def esc(s: str) -> str:
    """원시 HTML 안에서는 마크다운이 돌지 않는다 — 이스케이프하고 `코드`만 <code>로."""
    out = html.escape(str(s), quote=True)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", out)


def ext_of(name: str) -> str:
    e = Path(name).suffix.lower().lstrip(".")
    return e or "file"


def day_label(day) -> str:
    return "과정 뒤" if day == "after" else f"{day}일차"


def day_dir(day) -> str:
    return "after" if day == "after" else f"day{day}"


def zip_root(day) -> str:
    return "tradefin-after-course" if day == "after" else f"D{day}"


# ---------------------------------------------------------------- 색인
class Index:
    def __init__(self, files_root: Path | None):
        self.root = files_root
        p = files_root / "_index.json" if files_root else None
        self.ok = bool(p and p.is_file())
        self.data = json.loads(p.read_text(encoding="utf-8")) if self.ok else {"files": [], "days": {}, "bundles": []}

    def days(self) -> list:
        out = []
        for k in self.data.get("days", {}):
            out.append(int(k) if str(k).isdigit() else k)
        order = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, "after": 7}
        return sorted(out, key=lambda d: order.get(d, 9))

    def meta(self, day) -> dict:
        return self.data.get("days", {}).get(str(day), {"date": "", "practices": {}})

    def entries(self, day) -> list[dict]:
        return [e for e in self.data.get("files", []) if e.get("day") == day]


def guard(e: dict) -> None:
    p = (e.get("path") or "").lower()
    dest = e.get("dest") or ""
    if p:
        bad = [x for x in FORBIDDEN_PARTS if x in "/" + p]
        if bad:
            sys.exit(f"[중단] 수강생에게 나가면 안 되는 경로가 색인에 있습니다: {e.get('path')} (금지 조각: {bad})")
        name = p.rsplit("/", 1)[-1]
        if any(x in name for x in BASELINE_ONLY) and not (e.get("badge") == "비교 기준" or e.get("role") == "after"):
            sys.exit(f"[중단] 이름에 expected/answer가 든 파일은 '비교 기준'으로만 둡니다: {e.get('path')}")
        if p.startswith("data/raw/") and e.get("role") != "after":
            sys.exit(f"[중단] 원천(data/raw/)은 과정 뒤 묶음으로만 나갑니다: {e.get('path')}")
    if not dest or dest.startswith("/") or ".." in Path(dest).parts:
        sys.exit(f"[중단] 받는 이름(dest)이 잘못됐습니다: {dest!r}")


class Item:
    """사이트에 보일 항목 하나(색인 항목 + 원본 위치 · 상태)."""

    def __init__(self, e: dict, idx: Index, now: dt.datetime):
        guard(e)
        self.e = e
        self.dest = e["dest"]
        self.label = e.get("label") or Path(self.dest).name
        self.desc = e.get("desc") or ""
        self.badge = e.get("badge") or "참고"
        self.practices = list(e.get("practices") or [])
        self.placeholder = bool(e.get("placeholder"))
        self.open_at = e.get("open_at")
        self.is_pdf = self.dest.lower().endswith(".pdf")
        # PDF는 기본으로 ZIP에서 뺀다(슬라이드 PDF — files_build.py가 zip: false를 적는다). 선언에 zip: true가 있는 PDF만 넣는다
        # (예: 5일차 채팅 경로의 필수 입력인 규정 PDF)
        self.in_zip = bool(e.get("zip", not self.is_pdf))
        self.timed = bool(self.open_at) and parse_z(self.open_at) > now        # 빌드 시각에 아직 열리지 않았다
        self.src: Path | None = None
        if not self.placeholder and e.get("path"):
            cand = []
            if e.get("where") == "main":
                cand = [REPO / e["path"]] + ([idx.root / e["path"]] if idx.root else [])
            elif idx.root:
                cand = [idx.root / e["path"]]          # files 브랜치에만 있다(main 작업 트리의 .gitignore된 사본은 쓰지 않는다)
            self.src = next((c for c in cand if c.is_file()), None)
        self.size = self.src.stat().st_size if self.src else 0

    @property
    def ready(self) -> bool:
        return self.src is not None

    @property
    def zip_ok(self) -> bool:
        return self.ready and self.in_zip and not self.timed


def build_items(idx: Index, day, now: dt.datetime) -> list[Item]:
    # 과정 뒤 묶음(원천 · 생성기)은 파일마다 카드를 만들지 않고 ZIP 하나로 묶는다 — site 칸과 상관없이 풀린 파일 전부
    keep = ((lambda e: e.get("path") and not e.get("placeholder") and e.get("role") == "after") if day == "after"
            else (lambda e: e.get("site", True) and e.get("role") != "rehearsal"))
    items = [Item(e, idx, now) for e in idx.entries(day) if keep(e)]
    if day == "after":
        for it in items:
            it.dest = it.e["path"]                 # 압축 안에서도 저장소와 같은 자리(data/raw/ · tools/) — 생성기를 그대로 돌릴 수 있게
    items.sort(key=lambda it: (it.placeholder, BADGE_RANK.get(it.badge, 9), it.is_pdf, it.e.get("order", 0)))
    return items


# ---------------------------------------------------------------- 복사 · ZIP
def copy_files(day, items: list[Item], dry: bool) -> list[str]:
    dest_dir = DL_ROOT / day_dir(day)
    problems = []
    expected = {it.dest for it in items if it.ready}
    zips = {f"{day_dir(day)}_files.zip"} | {f"{day_dir(day)}_{k}.zip" for it in items for k in it.practices}
    if day == "after":
        zips = {"after_course_files.zip"}
    if not dry and dest_dir.exists():
        for p in sorted(dest_dir.rglob("*"), reverse=True):
            rel = p.relative_to(dest_dir).as_posix()
            if p.is_file() and rel not in expected and rel not in zips:
                p.unlink()
            elif p.is_dir() and not any(p.iterdir()):
                p.rmdir()
    for it in items:
        if it.placeholder:
            continue
        if not it.ready:
            problems.append(f"{day_label(day)} {it.e.get('path')} — 원본을 찾지 못했다({it.e.get('where')})")
            continue
        if not dry:
            out = dest_dir / it.dest
            out.parent.mkdir(parents=True, exist_ok=True)
            if not out.exists() or out.stat().st_size != it.size or out.read_bytes() != it.src.read_bytes():
                shutil.copy2(it.src, out)
    return problems


def make_zip(day, name: str, items: list[Item], dry: bool) -> int:
    path = DL_ROOT / day_dir(day) / name
    present = [it for it in items if it.zip_ok]
    if not present:
        if path.exists() and not dry:
            path.unlink()
        return 0
    if dry:
        return sum(it.size for it in present)
    y, m, d = DAY_DATES.get(day, (2026, 10, 14))
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        members = [(it.dest, it.src.read_bytes()) for it in sorted(present, key=lambda x: x.dest)]
        if day != "after":                       # 과정 뒤 묶음은 이미 저장소 경로 그대로다
            members.insert(0, ("README.txt", zip_readme(day, present)))
        for name, data in members:
            info = zipfile.ZipInfo(f"{zip_root(day)}/{name}", date_time=(y, m, d, 9, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    return path.stat().st_size


def zip_readme(day, present: list[Item]) -> bytes:
    """ZIP 안 안내문 — 압축 안에서는 파일이 한 폴더에 모여 있으니, 내 저장소의 어느 자리에 두는지(= get_day_files.py가 받는 자리)를 적는다."""
    rows = sorted(((it.dest, it.e.get("path") or it.dest) for it in present), key=lambda r: r[1])
    w = max(len(a) for a, _ in rows)
    lines = [f"{zip_root(day)} — {day_label(day)} 파일 · 압축을 푼 뒤 둘 자리",
             "",
             "내 저장소(VS Code)에서 쓰려면 아래 왼쪽 파일을 오른쪽 자리(저장소 맨 위 폴더 기준)에 그대로 둡니다.",
             f"uv run python tools/get_day_files.py {day} 가 받는 자리와 같아서 프롬프트의 @경로가 그대로 맞습니다.",
             "그 명령이 되면 이 압축 파일은 필요 없습니다. 채팅(ChatGPT · Claude)으로 하는 분은 필요한 파일만 첨부합니다.",
             "이 안내문(README.txt)은 저장소에 넣지 않아도 됩니다.",
             ""]
    lines += [f"{a.ljust(w)}  ->  {b}" for a, b in rows]
    return ("﻿" + "\r\n".join(lines) + "\r\n").encode("utf-8")


# ---------------------------------------------------------------- 카드(§6.8)
def card(it: Item, prefix: str) -> str:
    name = Path(it.dest).name
    ext = ext_of(name)
    chip = f'<span class="tf-chip {CHIP.get(it.badge, "tf-chip--opt")}">{esc(it.badge)}</span>'
    head = f'<span class="tf-dl__ext" data-ext="{esc(ext)}">{esc(ext.upper())}</span><span class="tf-dl__name">{esc(name)}</span>'
    if it.placeholder:
        when = kst_label(it.open_at) if it.open_at else ""
        return (f'<span class="tf-dl__item is-locked is-sealed" data-tf-release="{esc(it.open_at or "")}" data-tf-open-label="{esc(when)}">'
                f'{head}<span class="tf-dl__desc"><span class="tf-chip tf-chip--opt">자동 공개</span><b>{esc(it.label)}</b>'
                f'<span class="tf-dl__when"> · {esc(when)} 자동 공개</span></span></span>')   # 가운뎃점도 when 안에 — JS가 when을 감추면 '데이터 팩 ·'처럼 끝에 점만 남지 않게
    if not it.ready:
        return (f'<span class="tf-dl__item is-locked">{head}<span class="tf-dl__desc">{chip}<b>{esc(it.label)}</b> · '
                f'아직 올라오지 않았습니다 — 화면을 새로 고쳐도 없으면 강사에게 알려 주세요</span></span>')
    desc = f"<b>{esc(it.label)}</b> · {esc(it.desc)} · {human_size(it.size)}" if it.desc else f"<b>{esc(it.label)}</b> · {human_size(it.size)}"
    attrs, when = "", ""
    if it.open_at:
        lab = kst_label(it.open_at)
        attrs = f' data-tf-open="{esc(it.open_at)}" data-tf-open-label="{esc(lab)}"'
        if it.timed:
            when = f'<span class="tf-dl__when">{esc(lab)} 이후 열기</span> '
    cls = "tf-dl__item is-timed" if it.timed else "tf-dl__item"
    return (f'<a class="{cls}" href="{prefix}{esc(it.dest)}" download="{esc(name)}"{attrs}>{head}'
            f'<span class="tf-dl__desc">{chip}{when}{desc}</span></a>')


def zip_card(day, name: str, title: str, size: int, prefix: str, n_timed: int) -> str:
    extra = f" · 시각이 정해진 파일 {n_timed}개는 아래 카드에서 그 시각 뒤에" if n_timed else ""
    return (f'<a class="tf-dl__item tf-dl__item--zip" href="{prefix}{name}" download="{name}"><span class="tf-dl__ext" data-ext="zip">ZIP</span>'
            f'<span class="tf-dl__name">{esc(title)}</span><span class="tf-dl__desc">{name} · {human_size(size)} · 풀면 {zip_root(day)} 폴더{esc(extra)}</span></a>')


def cards_snippet(day, items: list[Item], prefix: str, zip_name: str | None, zip_title: str, zip_size: int) -> str:
    lines = [HEADER, '<div class="tf-dl">']
    if zip_name and zip_size:
        lines.append(zip_card(day, zip_name, zip_title, zip_size, prefix, sum(1 for it in items if it.timed and it.in_zip)))
    lines += [card(it, prefix) for it in items]
    if len(lines) == 2:
        lines.append('<span class="tf-dl__item is-locked"><span class="tf-dl__ext" data-ext="file">–</span>'
                     '<span class="tf-dl__name">파일 없음</span><span class="tf-dl__desc">이 구역에서 받을 파일이 없습니다</span></span>')
    lines.append("</div>")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 예전 표(그대로 쓰는 쪽을 위해)
def link_cell(it: Item, prefix: str) -> str:
    if it.placeholder:
        return f"자동 공개<br>{kst_label(it.open_at)}" if it.open_at else "자동 공개"
    if not it.ready:
        return "아직 없음"
    name = Path(it.dest).name
    attrs = f' data-tf-open="{it.open_at}"' if it.open_at else ""
    tail = f"<br><small>{kst_label(it.open_at)} 이후 열기</small>" if it.timed else ""
    return f'[:material-download: 받기]({prefix}{it.dest}){{ download="{name}"{attrs} }}{tail}'


def table_all(day, items: list[Item], labels: dict, prefix: str, zip_name: str, zip_size: int) -> str:
    lines = [HEADER, "", "| 파일 | 무엇인가 | 쓰는 곳 | 크기 | 받기 |", "|---|---|---|---|---|"]
    if zip_size:
        lines.append(f"| **`{zip_name}`**<br>**한 번에 받기** | 지금 열린 아래 파일을 `{zip_root(day)}` 폴더 하나로 묶은 압축 파일 | 전체 | "
                     f"{human_size(zip_size)} | [:material-folder-download: **받기**]({prefix}{zip_name}){{ download=\"{zip_name}\" }} |")
    for it in items:
        where = " · ".join(labels.get(x, x) for x in it.practices) or "–"
        size = human_size(it.size) if it.ready else "–"
        lines.append(f"| `{Path(it.dest).name}`<br>{it.label} | {it.desc} | {where} {it.badge} | {size} | {link_cell(it, prefix)} |")
    return "\n".join(lines) + "\n"


def table_section(items: list[Item], key: str, prefix: str) -> str:
    lines = [HEADER, "", "| 파일 | 무엇인가 | 구분 | 받기 |", "|---|---|---|---|"]
    for it in items:
        if key in it.practices:
            lines.append(f"| `{Path(it.dest).name}` | {it.desc} | {it.badge} | {link_cell(it, prefix)} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 일차 하나
def sync_day(idx: Index, day, now: dt.datetime, dry: bool) -> tuple[list[str], dict]:
    meta = idx.meta(day)
    labels = dict(meta.get("practices") or {})
    items = build_items(idx, day, now)
    problems = copy_files(day, items, dry)
    dd = day_dir(day)
    page_prefix = f"../downloads/{dd}/"
    root_prefix = f"downloads/{dd}/"
    outputs: dict[str, str] = {}
    stats = {"items": len(items), "ready": sum(it.ready for it in items), "timed": sum(it.timed for it in items),
             "placeholders": sum(it.placeholder for it in items)}
    if day == "after":
        size = make_zip(day, "after_course_files.zip", [it for it in items], dry)
        released = [b for b in idx.data.get("bundles", []) if b.get("kind") == "after"]
        at = released[0]["at"] if released else ""
        if size:
            body = zip_card(day, "after_course_files.zip", "원천 데이터 · 생성기 한 번에 받기", size, "{P}", 0)
        else:
            body = (f'<span class="tf-dl__item is-locked is-sealed" data-tf-release="{at}" data-tf-open-label="{kst_label(at) if at else ""}">'
                    f'<span class="tf-dl__ext" data-ext="zip">ZIP</span><span class="tf-dl__name">원천 데이터 · 생성기</span>'
                    f'<span class="tf-dl__desc"><span class="tf-chip tf-chip--opt">자동 공개</span>'
                    f'<span class="tf-dl__when">{kst_label(at) if at else "과정 뒤"} 자동 공개</span> — data/raw · tools 생성기(MIT · CC BY 4.0)</span></span>')
        for name, pre in (("files_all_cards.md", page_prefix), ("files_all_root_cards.md", root_prefix)):
            outputs[name] = HEADER + "\n" + '<div class="tf-dl">\n' + body.replace("{P}", pre) + "\n</div>\n"
        stats["zip"] = size
    else:
        y = make_zip(day, f"{dd}_files.zip", items, dry)
        stats["zip"] = y
        outputs["files_all_cards.md"] = cards_snippet(day, items, page_prefix, f"{dd}_files.zip", f"{day_label(day)} 파일 한 번에 받기", y)
        outputs["files_all_root_cards.md"] = cards_snippet(day, items, root_prefix, f"{dd}_files.zip", f"{day_label(day)} 파일 한 번에 받기", y)
        outputs["files_pdf_cards.md"] = cards_snippet(day, [it for it in items if it.is_pdf], page_prefix, None, "", 0)
        outputs["files_all.md"] = table_all(day, items, labels, page_prefix, f"{dd}_files.zip", y)
        outputs["files_all_root.md"] = table_all(day, items, labels, root_prefix, f"{dd}_files.zip", y)
        for key, lab in labels.items():
            sub = [it for it in items if key in it.practices]
            zn = f"{dd}_{key}.zip"
            zs = make_zip(day, zn, sub, dry)
            outputs[f"files_{key}_cards.md"] = cards_snippet(day, sub, page_prefix, zn, f"{lab} 파일 한 번에 받기", zs)
            outputs[f"files_{key}.md"] = table_section(items, key, page_prefix)
    if not dry:
        sd = SNIP_ROOT / dd
        sd.mkdir(parents=True, exist_ok=True)
        for p in sd.glob("files_*.md"):
            if p.name not in outputs:
                p.unlink()
        for name, text in outputs.items():
            q = sd / name
            if not q.exists() or q.read_text(encoding="utf-8") != text:
                q.write_text(text, encoding="utf-8")
    stats["snippets"] = sorted(outputs)
    return problems, stats


# ---------------------------------------------------------------- 링크 점검(빌드 뒤)
def check_links(site: Path) -> int:
    bad = []
    n = 0
    for page in site.rglob("*.html"):
        rel = page.relative_to(site).as_posix()
        if rel.startswith(("downloads/", "search/")):
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'href="([^"#?]*downloads/[^"#?]+)"', text):
            href = html.unescape(m.group(1))
            if href.startswith(("http://", "https://")):
                continue
            n += 1
            target = (page.parent / href).resolve()
            if not target.is_file():
                bad.append(f"{rel} → {href}")
    print(f"[check-links] 내려받기 링크 {n}개 중 깨진 링크 {len(bad)}개")
    for b in bad[:100]:
        print("  !", b)
    return 1 if bad else 0


# ---------------------------------------------------------------- 실행
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--files-root", type=Path, default=None, help="files 브랜치 체크아웃 폴더(기본: 저장소의 _files)")
    ap.add_argument("--day", action="append", default=[], help="1–6 또는 after — 이 일차만(여러 번 쓸 수 있다)")
    ap.add_argument("--check", action="store_true", help="아무것도 바꾸지 않고 상태만(빠진 파일이 있으면 종료코드 1)")
    ap.add_argument("--strict", action="store_true", help="빠진 파일이 있으면 종료코드 1(복사는 한다)")
    ap.add_argument("--now", default=None, help="이 시각(UTC ISO)을 '지금'으로 본다 — 잠금 · ZIP 미리 보기용")
    ap.add_argument("--check-links", type=Path, default=None, metavar="SITE", help="빌드한 site 폴더의 내려받기 링크 점검만")
    ap.add_argument("--require-day", type=int, action="append", default=[], help="(폐지 — 무시) 예전 시각 공개용 옵션")
    ap.add_argument("--preview", action="store_true", help="(폐지 — 무시) 공개 여부는 색인이 정한다")
    args = ap.parse_args()
    if args.check_links:
        return check_links(args.check_links)
    root = args.files_root or (REPO / "_files")
    root = root if root.is_absolute() else (Path.cwd() / root)
    idx = Index(root.resolve() if root.exists() else None)
    print(f"[sync_site_assets] 저장소 {REPO} · 색인 {root / '_index.json' if idx.ok else '없음'}")
    if not idx.ok:
        print("  ! files 브랜치 색인(_index.json)을 찾지 못했습니다 — 강사 PC: ../.venv/bin/python ../instructor/release/files_build.py · "
              "CI: pages.yml의 files 브랜치 checkout을 확인")
        return 2
    now = parse_z(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    want = [int(d) if str(d).isdigit() else str(d) for d in args.day] or idx.days()
    problems_all = []
    for day in want:
        if str(day) not in idx.data.get("days", {}):
            print(f"  ! 색인에 {day} 일차가 없습니다")
            continue
        problems, st = sync_day(idx, day, now, dry=args.check)
        problems_all += problems
        print(f"[{day_label(day)}] 카드 {st['items']}개 · 파일 {st['ready']}개 · 시각 전(잠금) {st['timed']}개 · 자동 공개 자리 {st['placeholders']}개 · "
              f"ZIP {human_size(st['zip']) if st.get('zip') else '없음'}")
    for p in problems_all:
        print("  !", p)
    if problems_all and (args.check or args.strict):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
