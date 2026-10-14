#!/usr/bin/env python3
"""정한 시각이 된 봉인 묶음을 풀어 files 브랜치 작업 트리에 놓는다 — .github/workflows/d6-release.yml이 돌린다.

봉인 묶음 = files 브랜치의 sealed/<id>.tgz.enc(openssl AES-256-CBC · PBKDF2 60만 회 · 무작위 384비트 키 = 저장소 시크릿 RELEASE_KEY).
공개 로그에는 파일 이름 · 내용을 찍지 않는다 — 묶음 번호와 개수 · 해시 OK/NG만.

    python tools/release_due.py --files-root _files                 # 실제 공개: 때가 된 묶음(곧 될 묶음은 그 시각까지 기다렸다가)
    python tools/release_due.py --files-root _files --verify-all    # 사전 점검(dry-run): 아직 안 풀린 묶음을 모두 풀어 해시만 확인 — 쓰지 않음
    python tools/release_due.py --files-root _files --dry-run --now 2026-10-21T00:30:00Z   # 그 시각이면 무엇이 풀리나(쓰지 않음)
    python tools/release_due.py --files-root _files --force --only r2   # 고른 묶음을 지금 공개(수동 버튼 · 비상)
    옵션  --arm-min 20(곧 때가 될 묶음을 기다리는 최대 분) · --offset-min N(아직 안 나간 묶음 전체를 N분 늦춘다)

결과는 $GITHUB_OUTPUT: changed=true|false, ids=r1,r2. 같은 묶음은 두 번 풀지 않는다(sealed/released.json).
시각 전 묶음은 --force 없이 절대 풀지 않는다. 표준 라이브러리 + openssl 명령만 쓴다(ubuntu 러너 기본 포함).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ITER = "600000"
SAFE = re.compile(r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9_./\-가-힣 ]+$")
SPECIAL = ("SHA256SUMS", "_index_part.json")


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def iso(t: dt.datetime) -> str:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def say(msg: str) -> None:
    print(msg, flush=True)


def out(k: str, v: str) -> None:
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"{k}={v}\n")


def decrypt(enc: bytes) -> bytes:
    r = subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", ITER, "-md", "sha256", "-pass", "env:RELEASE_KEY"],
                       input=enc, capture_output=True, env=os.environ)
    if r.returncode:
        raise RuntimeError("복호화 실패 — RELEASE_KEY가 묶음을 봉인한 키와 같은지 확인")
    return r.stdout


def unpack(tgz: bytes) -> tuple[dict[str, bytes], dict]:
    """(파일 {경로: 내용}, 색인 조각). 이름 · 종류 · 해시를 모두 메모리에서 확인한 뒤에야 돌려준다."""
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(tgz), mode="r:gz") as tf:
        for m in tf.getmembers():
            if not m.isreg() or not SAFE.match(m.name):
                raise RuntimeError("묶음에 허용되지 않는 항목이 있다(이름 · 종류)")
            files[m.name] = tf.extractfile(m).read()
    sums = files.pop("SHA256SUMS", None)
    if sums is None:
        raise RuntimeError("SHA256SUMS 없음")
    want = {}
    for line in sums.decode().splitlines():
        h, _, name = line.partition("  ")
        want[name] = h
    if set(want) != set(files):
        raise RuntimeError("SHA256SUMS와 묶음 내용의 파일 목록이 다르다")
    for name, data in files.items():
        if hashlib.sha256(data).hexdigest() != want[name]:
            raise RuntimeError("해시 불일치")
    part = json.loads(files.pop("_index_part.json").decode("utf-8")) if "_index_part.json" in files else {"files": []}
    return files, part


def day_of(path: str):
    m = re.search(r"/d(\d)_|labs/day(\d)/|handouts/day(\d)_", "/" + path)
    return int(next(g for g in m.groups() if g)) if m else None


def apply_release(root: Path, m: dict, files: dict[str, bytes], part: dict, stamp: str) -> None:
    """평문을 쓰고 색인(_index.json) · released.json을 고친다(다른 묶음 · 일차 항목은 그대로)."""
    for name, data in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    idx_p = root / "_index.json"
    idx = json.loads(idx_p.read_text(encoding="utf-8")) if idx_p.exists() else {"v": 2, "files": [], "bundles": []}
    meta = {e["path"]: e for e in part.get("files", []) if e.get("path")}
    new_paths = set(files)
    kept = [e for e in idx.get("files", [])
            if not (e.get("bundle") == m["id"] and e.get("placeholder")) and e.get("path") not in new_paths]
    for name, data in sorted(files.items()):
        e = dict(meta.get(name) or {"path": name, "day": day_of(name), "role": "surprise", "badge": "참고", "practices": [],
                                    "label": Path(name).name, "desc": "", "dest": Path(name).name, "site": False, "zip": True})
        e.update(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest(), bundle=m["id"], where="sealed")
        e.pop("placeholder", None)
        kept.append(e)
    order = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, "after": 7}
    kept.sort(key=lambda x: (order.get(x.get("day"), 9), x.get("order", 0), x.get("path") or ""))
    idx["files"] = kept
    for b in idx.get("bundles", []):
        if b.get("id") == m["id"]:
            b["released"] = stamp
    idx["updated"] = stamp
    idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rel_p = root / "sealed" / "released.json"
    rel = json.loads(rel_p.read_text(encoding="utf-8")) if rel_p.exists() else {}
    rel[m["id"]] = {"at": m["at"], "released": stamp, "n": len(files)}
    rel_p.write_text(json.dumps(rel, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files-root", required=True, type=Path)
    ap.add_argument("--verify-all", action="store_true", help="dry-run: 아직 안 풀린 묶음을 모두 풀어 해시만 확인(쓰지 않음)")
    ap.add_argument("--dry-run", action="store_true", help="무엇이 풀릴지 보기만(쓰지 않음)")
    ap.add_argument("--now", default=None, help="(dry-run · verify-all 전용) 이 시각을 지금으로 본다")
    ap.add_argument("--arm-min", type=int, default=20)
    ap.add_argument("--offset-min", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    root: Path = a.files_root
    key_ok = bool(os.environ.get("RELEASE_KEY"))
    mp = root / "sealed" / "manifest.json"
    if not mp.exists():
        say("[release] sealed/manifest.json 없음 — 할 일 없음")
        out("changed", "false")
        return 0
    manifest = json.loads(mp.read_text(encoding="utf-8"))["items"]
    rel_path = root / "sealed" / "released.json"
    released = json.loads(rel_path.read_text(encoding="utf-8")) if rel_path.exists() else {}
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    unknown = only - {m["id"] for m in manifest}
    if unknown:
        raise SystemExit(f"--only에 없는 묶음 번호: {sorted(unknown)}")
    safe_mode = a.verify_all or a.dry_run
    if a.now and not safe_mode:
        raise SystemExit("--now는 --dry-run · --verify-all에서만 쓴다")
    if a.force and not only:
        raise SystemExit("--force는 --only와 함께만 쓴다(예: --only r2 --force)")
    now = parse(a.now) if a.now else now_utc()
    off = dt.timedelta(minutes=a.offset_min)
    todo = [m for m in manifest if m["id"] not in released and (not only or m["id"] in only)]
    say(f"[release] 지금 {iso(now)} · 봉인 {len(manifest)}개 · 공개됨 {len(released)}개 · 대기 {len(todo)}개"
        + (f" · 시각 밀기 {a.offset_min}분" if a.offset_min else ""))

    if a.verify_all:
        if not key_ok:
            raise SystemExit("RELEASE_KEY 없음 — 저장소 Settings → Secrets → Actions에 RELEASE_KEY가 있는지 확인")
        bad = 0
        for m in todo:
            enc = (root / m["enc"]).read_bytes()
            ok_hash = hashlib.sha256(enc).hexdigest() == m["enc_sha256"]
            try:
                files, part = unpack(decrypt(enc))
                say(f"  {m['id']}: 암호문 해시 {'OK' if ok_hash else 'NG'} · 풀림 OK · 파일 {len(files)}개 · 공개 시각 {m['at']}")
                bad += (not ok_hash)
            except Exception as e:  # noqa: BLE001
                say(f"  {m['id']}: NG — {e}")
                bad += 1
        out("changed", "false")
        say(f"[release] 사전 점검 {'통과' if not bad else f'실패 {bad}개'}")
        return 1 if bad else 0

    def due_at(m):
        return parse(m["at"]) + off

    soon = todo if a.force else [m for m in todo if (due_at(m) - now).total_seconds() <= a.arm_min * 60]
    if not soon:
        nxt = min((due_at(m) for m in todo), default=None)
        say("[release] 지금 할 일 없음" + (f" · 다음 {iso(nxt)}" if nxt else ""))
        out("changed", "false")
        return 0
    if not key_ok:
        raise SystemExit("RELEASE_KEY 없음")
    first = min(due_at(m) for m in soon)
    wait = (first - now).total_seconds()
    if wait > 0 and not (safe_mode or a.force):
        say(f"[release] 대기: 다음 묶음까지 {int(wait)}초 — 그 시각까지 기다린 뒤 공개한다(예약 지연 대비)")
        while True:
            left = (first - now_utc()).total_seconds()
            if left <= 0:
                break
            time.sleep(min(5, left))
        now = now_utc()
    ids = []
    for m in sorted(soon, key=due_at):
        if due_at(m) > now and not a.force:          # 하드 가드: 시각 전 묶음은(force 없이) 풀지 않는다
            continue
        enc = (root / m["enc"]).read_bytes()
        if hashlib.sha256(enc).hexdigest() != m["enc_sha256"]:
            raise SystemExit(f"{m['id']}: 묶음 파일이 manifest와 다르다")
        files, part = unpack(decrypt(enc))
        say(f"[release] {m['id']}: 풀림 · 파일 {len(files)}개{' (dry-run: 쓰지 않음)' if safe_mode else ''}")
        if safe_mode:
            continue
        apply_release(root, m, files, part, iso(now_utc()))
        ids.append(m["id"])
    out("changed", "true" if ids else "false")
    out("ids", ",".join(ids))
    say(f"[release] 공개 {len(ids)}개: {','.join(ids) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
