"""외부 공개 데이터 캐시 수집 — 네트워크 호출은 이 스크립트만 한다(생성기는 캐시만 읽음).

사용:
    python tools/fetch_external.py fred          # FRED H.10 환율 4종(DEXKOUS·DEXUSEU·DEXCHUS·DEXJPUS)
    python tools/fetch_external.py all

결과: data/external/fred_*.csv (받은 그대로), data/external/_fetch_log.csv (수집 로그)
ECOS·SEC·UCI 등 나머지 대상은 키·이용조건 확인 후 추가 예정.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import sys
import time
import urllib.request

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from tf_common import EXTERNAL, load_config, sha256_file  # noqa: E402

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}&coed={end}"
KST = dt.timezone(dt.timedelta(hours=9))


def _get(url: str, retries: int = 3) -> bytes:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tradefin-ai-2026 fetch_external"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # 네트워크 일시 오류 재시도
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"다운로드 실패: {url} ({last})")


def log_fetch(rows: list[dict]) -> None:
    path = EXTERNAL / "_fetch_log.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8-sig" if new else "utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "url", "fetched_at_kst", "rows", "sha256", "note"])
        if new:
            w.writeheader()
        w.writerows(rows)


def fetch_fred(cfg: dict) -> None:
    start = cfg["external"]["fx_calendar_start"]
    end = cfg["meta"]["end_date"]
    logs = []
    for sid, fname in cfg["external"]["fred_series"].items():
        url = FRED_URL.format(sid=sid, start=start, end=end)
        body = _get(url)
        text = body.decode("utf-8")
        reader = list(csv.reader(io.StringIO(text)))
        if not reader or reader[0][0] != "observation_date":
            raise RuntimeError(f"FRED 응답 형식이 예상과 다름: {sid}")
        out = EXTERNAL / fname
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        n = len(reader) - 1
        last = reader[-1][0] if n else ""
        logs.append({"source": f"FRED {sid}", "url": url,
                     "fetched_at_kst": dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
                     "rows": n, "sha256": sha256_file(out),
                     "note": f"마지막 관측일 {last} (H.10 주간 공표, 이후 날짜는 생성기에서 직전값 채움)"})
        print(f"[fred] {sid}: {n}행, 마지막 {last} → {out.relative_to(EXTERNAL.parents[1])}")
        time.sleep(1)
    log_fetch(logs)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", choices=["fred", "all"])
    ap.add_argument("--config", default=None)
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.target in ("fred", "all"):
        fetch_fred(cfg)


if __name__ == "__main__":
    main()
