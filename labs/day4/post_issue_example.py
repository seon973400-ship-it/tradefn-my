#!/usr/bin/env python3
"""조기경보 결과를 GitHub 이슈로 알리는 참고 스크립트(4일차 실습 B 02) - 엔진(ews.py · ews_example.py) 다음에 실행한다.

    uv run python labs/day4/post_issue_example.py             # Actions 러너에서 - 이슈를 만들거나 댓글을 단다
    uv run python labs/day4/post_issue_example.py --dry-run   # 아무것도 올리지 않고 본문만 출력(내 PC에서는 이 모드로 본문을 미리 본다)

- 제목은 "[조기경보] {기준일} 기준". 같은 제목의 열린 이슈가 있으면 댓글로 갱신하고, 없으면 새로 만든다.
  -> 몇 번을 돌려도 이슈는 하나, 댓글만 는다(멱등).
- 결과가 지난번과 같으면(요약 해시 동일) 댓글에 '결과 동일'이라 적고, 달라졌으면 이슈 본문도 새 결과로 고친다.
- GitHub CLI(gh)를 쓴다. 러너에는 이미 있고 토큰은 GH_TOKEN(워크플로의 github.token)으로 받는다 - 키를 코드에 적지 않는다.
- 문장은 모두 '권고(사람 승인 전)'. 이 스크립트도 메일 · 선적 · 송금 같은 실행은 하지 않는다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 저장소 맨 위 폴더 = pyproject.toml이 있는 가장 가까운 위 폴더 — scripts/ 로 복사하거나 작업 사본 폴더에서 돌려도 같은 곳을 읽는다
ROOT = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists()), Path(__file__).resolve().parents[2])
KST = timezone(timedelta(hours=9))
RECO = "권고(사람 승인 전)"
LABEL = {"R-CREDIT-EVENT": "신용사건", "R-FRAUD-ACCOUNT": "계좌 변경 요청", "R-D30-HOLD": "선적 보류(D+30)",
         "R-KSURE-NOTICE-SOON": "사고발생통지 임박", "R-KSURE-NOTICE-OVERDUE": "통지 기한 경과",
         "R-TERMS-CHANGE": "결제조건 변경", "R-PD-WATCH": "연체 확률 높음"}
MARK = re.compile(r"<!-- ews:v1 asof=(\S+) sha=(\w+) -->")


def money(x: float) -> str:
    return f"{x:,.0f}"


# --------------------------------------------------------------------------- 실행 정보(Actions 환경변수)
def cron_to_kst(cron: str) -> str:
    """'47 9 8 10 *' (UTC) -> '18:47 KST'. 분 · 시가 숫자가 아니면 cron 글자를 그대로 쓴다."""
    parts = cron.split()
    if len(parts) == 5 and parts[0].isdigit() and parts[1].isdigit():
        mins = (int(parts[1]) * 60 + int(parts[0]) + 9 * 60) % (24 * 60)
        return f"{mins // 60:02d}:{mins % 60:02d} KST"
    return cron


def run_info(out: Path) -> dict:
    env = os.environ
    event = env.get("GITHUB_EVENT_NAME", "local")
    repo = env.get("GITHUB_REPOSITORY", "")
    run_id = env.get("GITHUB_RUN_ID", "")
    url = f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run_id}" if repo and run_id else ""
    cron = ""
    if event == "schedule" and env.get("GITHUB_EVENT_PATH"):
        try:
            cron = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")).get("schedule", "")
        except (OSError, ValueError):
            pass
    run_at = ""
    log = out / "run_log.jsonl"
    if log.exists() and log.read_text(encoding="utf-8").strip():
        run_at = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[-1]).get("run_at", "")
    when = datetime.fromisoformat(run_at).astimezone(KST) if run_at else datetime.now(KST)
    return {"event": event, "repo": repo, "run_id": run_id, "url": url, "cron": cron,
            "scheduled": cron_to_kst(cron) if cron else "", "at": when.strftime("%Y-%m-%d %H:%M KST"), "hm": when.strftime("%H:%M")}


# --------------------------------------------------------------------------- 글
def run_link(info: dict) -> str:
    return f"[#{info['run_id']}]({info['url']})" if info["url"] else "로컬 실행"


def render_body(s: dict, info: dict, sha: str) -> str:
    rows = ["| 등급 | 규칙 | 건수 |", "|---|---|---:|"]
    for rid, r in sorted(s["rules"].items(), key=lambda kv: kv[1]["tier"]):  # 같은 등급 안에서는 규칙 파일의 순서
        n = f"{r['alerts']}곳" if r["scope"] == "buyer" else f"{r['alerts']}건"
        if r["scope"] == "invoice" and rid in s["ship_hold"]["rules"]:
            n += f" · {r['buyers']}곳"
        rows.append(f"| {r['tier']} {s['tiers'][r['tier']]['meaning']} | {LABEL.get(rid, rid)} | {n} |")
    st = " · ".join(f"{k} {v['count']}건 {money(v['amount_usd'])}" for k, v in s["stages"].items())
    hold = s["ship_hold"]
    return "\n".join([
        f"**기준일 {s['asof']}** · 미결 {s['open_invoices']}건 · 바이어 {s['buyers']}곳",
        f"아래는 모두 **{RECO}** 입니다.", "결정과 실행은 담당자가 합니다.", "",
        *rows, "",
        f"**연체 단계(USD)** {st}", "",
        f"**선적 보류 {RECO} {hold['count']}곳**", " · ".join(hold["buyers"]) or "해당 없음", "",
        f"**사고발생통지** 임박 {s['notice']['soon_invoices']}건 · 경과 {s['notice']['overdue_invoices']}건", "보험 가입 건만 · 기한 = 결제기일 + 1개월", "",
        f"실행 {run_link(info)} · 이벤트 `{info['event']}` · {info['hm']} KST · 결과 파일은 아티팩트 `alerts`",
        f"<!-- ews:v1 asof={s['asof']} sha={sha} -->", ""])


def render_comment(info: dict, n: int, same: bool, s: dict, sha: str) -> str:
    head = "예약 실행" if info["event"] == "schedule" else "다시 실행"
    verdict = f"결과 동일(해시 `{sha}`)" if same else f"**결과가 달라져** 이슈 본문을 새 결과로 고쳤습니다(해시 `{sha}`)"
    lines = [f"**{head} {n}회째** · {verdict}"]
    if info["event"] == "schedule":
        lines += [f"예약 {info['scheduled']}(cron `{info['cron']}`, UTC) → 실제 실행 {info['hm']} KST",
                  f"실행 {run_link(info)} · 사람이 누른 버튼 없음"]
    else:
        lines += ["이슈는 하나로 두고 댓글만 더합니다." if same else "이슈는 하나로 두고 본문과 댓글을 갱신합니다.",
                  f"이벤트 `{info['event']}` · 실행 {run_link(info)} · {info['hm']} KST"]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- gh
class GH:
    def __init__(self, repo: str, dry: bool):
        self.repo, self.dry = repo, dry

    def _run(self, args: list[str], text: str | None = None) -> str:
        cmd = ["gh", *args] + (["-R", self.repo] if self.repo else [])
        r = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            sys.exit(f"gh {' '.join(args[:2])} 실패 (종료 {r.returncode}): {r.stderr.strip()}")
        return r.stdout.strip()

    def find(self, title: str) -> dict | None:
        out = self._run(["issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,body,comments"])
        for it in json.loads(out or "[]"):
            if it["title"] == title:
                return it
        return None

    def create(self, title: str, body: str) -> str:
        return self._run(["issue", "create", "--title", title, "--body-file", "-"], body)

    def edit(self, number: int, body: str) -> None:
        self._run(["issue", "edit", str(number), "--body-file", "-"], body)

    def comment(self, number: int, body: str) -> None:
        self._run(["issue", "comment", str(number), "--body-file", "-"], body)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "workbench/day4/outputs"))
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""), help="owner/repo (Actions에서는 자동)")
    ap.add_argument("--dry-run", action="store_true", help="이슈를 만들지 않고 본문 · 댓글만 출력")
    a = ap.parse_args(argv)

    out = Path(a.out)
    raw = (out / "alert_summary.json").read_bytes()
    s = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()[:8]
    info = run_info(out)
    title = f"[조기경보] {s['asof']} 기준"
    gh = GH(a.repo, a.dry_run)

    found = None if a.dry_run and not a.repo else gh.find(title)
    if found is None:
        body = render_body(s, info, sha)
        if a.dry_run:
            print(f"[dry-run] 새 이슈 만들기: {title}\n\n{body}")
        else:
            print(f"이슈 만들기: {gh.create(title, body)}")
        return 0

    m = MARK.search(found["body"] or "")
    same = bool(m and m.group(2) == sha)
    n = len(found["comments"]) + 2  # 이슈를 만든 실행이 1회째, 댓글마다 한 번 더
    if not same:
        body = render_body(s, info, sha)
        if a.dry_run:
            print(f"[dry-run] 이슈 #{found['number']} 본문 고치기\n\n{body}")
        else:
            gh.edit(found["number"], body)
    comment = render_comment(info, n, same, s, sha)
    if a.dry_run:
        print(f"[dry-run] 이슈 #{found['number']} 에 댓글\n\n{comment}")
    else:
        gh.comment(found["number"], comment)
        print(f"이슈 #{found['number']} 에 댓글 {n - 1}번째 - 결과 {'동일' if same else '달라짐(본문 갱신)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
