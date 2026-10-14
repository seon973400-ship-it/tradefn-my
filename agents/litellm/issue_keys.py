#!/usr/bin/env python
"""LiteLLM 가상 키 일괄 발급(강사용) — config.yaml 아래 표의 키를 /key/generate로 만든다.

사용(키 값은 저장소에 남기지 않는다 — 결과 CSV는 저장소 밖 강사 폴더):
    python agents/litellm/issue_keys.py --dry-run                     # 보낼 내용만 출력(네트워크 없음)
    LITELLM_URL=https://llm.<강사도메인> LITELLM_MASTER_KEY=… \\
    python agents/litellm/issue_keys.py --out ../instructor/day5/keys/litellm_keys.csv
필드 이름(max_budget·budget_duration·rpm_limit·models·duration·key_alias·metadata)은 설치 버전 문서로 D-10에 확인한다.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

FAST = ["fast-default", "fast-backup"]
ALL = FAST + ["quality"]
PLAN = ([(f"L{i:02d}", FAST, 3, 30, "10d", "learner") for i in range(1, 21)]
        + [(f"L{i:02d}", FAST, 3, 30, "10d", "spare") for i in (21, 22)]
        + [("INSTR", ALL, 20, 60, "30d", "instructor"), ("SHARED1", ALL, 10, 60, "10d", "공용"),
           ("SHARED2", ALL, 10, 60, "10d", "공용")])
TEST = [(f"T{i:02d}", FAST, 1, 30, "3d", "test") for i in (1, 2, 3)]


def payload(alias, models, budget, rpm, duration, role) -> dict:
    return {"key_alias": alias, "models": models, "max_budget": budget, "budget_duration": "1d", "rpm_limit": rpm,
            "duration": duration, "metadata": {"role": role, "course": "tradefin-ai-2026"}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test-keys", action="store_true", help="D-10~D-1 시험 키 T01–T03만")
    ap.add_argument("--out", default="../instructor/day5/keys/litellm_keys.csv")
    a = ap.parse_args()
    plan = TEST if a.test_keys else PLAN
    if a.dry_run:
        for p in plan:
            print(json.dumps(payload(*p), ensure_ascii=False))
        return 0
    import requests
    url, mk = os.environ.get("LITELLM_URL", "").rstrip("/"), os.environ.get("LITELLM_MASTER_KEY", "")
    if not url or not mk:
        print("LITELLM_URL · LITELLM_MASTER_KEY 환경변수가 필요합니다", file=sys.stderr)
        return 2
    out = Path(a.out)
    if "tradefin-ai-2026" in str(out.resolve()):
        print("키 CSV를 공개 저장소 안에 쓰지 않습니다 — --out을 저장소 밖으로", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["key_alias", "role", "models", "max_budget_per_day", "rpm", "duration", "key"])
        for p in plan:
            r = requests.post(f"{url}/key/generate", headers={"Authorization": f"Bearer {mk}"}, json=payload(*p), timeout=30)
            r.raise_for_status()
            w.writerow([p[0], p[5], " ".join(p[1]), p[2], p[3], p[4], r.json().get("key", "")])
            print(f"{p[0]} 발급")
    print(f"→ {out} (QR 카드 인쇄용 — 공유 드라이브·단체방에 올리지 않는다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
