"""2일차: 뉴스 점수 파일 검사 — workbench/day2/prompts/news_score_v1.md [척도] · [규칙] 2·5 · [출력]을 확인한다.

실행: uv run python scripts/validate_scores.py
입력(읽기만): workbench/day2/outputs/news_scored.jsonl · data/checkpoints/d2_news.csv (1–100행)
출력: 위반 행 목록(콘솔). 위반이 있으면 종료 코드 1.

검사
- 줄 수: 100줄
- 점수: news_sent_0_10이 0–10 정수(bool 제외)
- 라벨: 0–2 severe · 3–4 high · 5 watch · 6–10 low
- evidence: 같은 news_id 원문의 headline 또는 body_short 안에 글자 그대로 있음
"""

import csv
import json
import sys
from pathlib import Path

SCORED = Path("workbench/day2/outputs/news_scored.jsonl")
NEWS = Path("data/checkpoints/d2_news.csv")
N_ROWS = 100


def band(score):
    if score <= 2:
        return "severe"
    if score <= 4:
        return "high"
    if score == 5:
        return "watch"
    return "low"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with NEWS.open(encoding="utf-8-sig", newline="") as f:
        news = {r["news_id"]: r for r in list(csv.DictReader(f))[:N_ROWS]}
    lines = SCORED.read_text(encoding="utf-8").splitlines()

    problems = []
    if len(lines) != N_ROWS:
        problems.append((0, "-", f"줄 수 {len(lines)} ≠ {N_ROWS}"))

    for i, line in enumerate(lines, 1):
        try:
            o = json.loads(line)
        except json.JSONDecodeError as e:
            problems.append((i, "-", f"JSON 아님: {e}"))
            continue
        nid = o.get("news_id", "-")
        src = news.get(nid)
        if src is None:
            problems.append((i, nid, "원문 1–100행에 없는 news_id"))
            continue

        s = o.get("news_sent_0_10")
        score_ok = isinstance(s, int) and not isinstance(s, bool) and 0 <= s <= 10
        if not score_ok:
            problems.append((i, nid, f"점수가 0–10 정수가 아님: {s!r}"))
        elif o.get("label") != band(s):
            problems.append((i, nid, f"라벨 {o.get('label')!r} ≠ 점수 {s}의 대역 {band(s)!r}"))

        ev = o.get("evidence")
        if not isinstance(ev, str) or not ev or (ev not in src["headline"] and ev not in src["body_short"]):
            problems.append((i, nid, f"evidence가 원문에 그대로 없음: {ev!r}"))

    for i, nid, msg in problems:
        print(f"{i}행 {nid}: {msg}")
    print(f"검사 {len(lines)}줄 · 위반 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
