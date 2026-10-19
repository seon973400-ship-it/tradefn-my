#!/usr/bin/env python3
"""ask_claude.py — VS Code 확장에 들어 있는 Claude Code(claude)를 찾아 '질문 하나 → JSON 답 하나'로 부르는 도우미.

4일차 실습 C '메일함 아침 당번 로봇'에서 씁니다. 따로 설치할 것은 없습니다(파이썬 기본 기능만).

쓰는 법 (저장소 맨 위 폴더 · VS Code 터미널):
    uv run python scripts/ask_claude.py --check          # 찾기 · 판 · API 키 · 시험 호출 — 네 줄 확인
    uv run python scripts/ask_claude.py --check --model haiku

코드에서:
    from ask_claude import ask_json                      # scripts/ 안의 다른 파일에서
    answer = ask_json("질문 글", schema={...})            # dict 하나가 돌아온다(--json-schema 모양 그대로)

찾는 순서(먼저 찾은 것을 쓴다 · 확장 폴더는 그중 가장 새 판)
    0) 환경 변수 CLAUDE_BIN(직접 경로를 넣었을 때)
    1) PATH의 claude
    2) ~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude(.exe)   (Windows · Mac · Linux의 VS Code)
    3) ~/.cursor/extensions/…                                                               (Cursor)
    4) ~/.vscode-server/… · ~/.cursor-server/… · ~/.vscode-remote/…                       (WSL · 원격 · Codespaces)
    5) ~/.local/bin/claude · ~/.claude/local/claude                                         (따로 설치한 경우)
못 찾으면: 확장을 설치 · 업데이트하거나, CLAUDE_BIN에 경로를 넣거나, Codespaces에서 하거나, 로봇을 --no-ai로 돌립니다.

부르는 방식(고정): claude -p --output-format json --json-schema <스키마> --tools "" --no-session-persistence --model <모델>
  - 질문은 표준 입력(UTF-8)으로 넣는다 — 한글이 깨지지 않게.
  - 도구는 하나도 주지 않는다(--tools "") — 읽고 답만 한다. 파일 · 명령 · 인터넷을 쓰지 않는다.
  - 작업 폴더는 OS 임시 폴더 — 내 저장소의 CLAUDE.md · 설정을 읽지 않는다.
  - 환경에서 ANTHROPIC_API_KEY · CLAUDECODE · CLAUDE_CODE_*를 지운다 — API 키 청구 없이 내 구독(로그인)으로 돈다.
  - --bare는 쓰지 않는다(그 모드는 로그인을 무시하고 API 키만 쓴다).
이 파일은 실습 자료입니다 — 고치지 않고 그대로 씁니다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WINDOWS = os.name == "nt"
EXE = "claude.exe" if WINDOWS else "claude"
MIN_VERSION = (2, 1, 0)          # --json-schema · --tools ""를 확인한 판(2.1.37 · 2.1.296 · 2.1.301) — 더 옛 판은 건너뛰고 다음 자리를 찾는다
DEFAULT_MODEL = "sonnet"
DEFAULT_TIMEOUT = 180            # 초 — 한 번 부르는 데 보통 5–20초

PING_SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}, "answer": {"type": "string"}},
    "required": ["ok", "answer"],
    "additionalProperties": False,
}
PING_PROMPT = "연결 시험입니다. ok는 true, answer는 영어 소문자 pong 한 단어로 답하세요."


class AskClaudeError(RuntimeError):
    """claude를 부르지 못했거나 답이 JSON이 아닐 때 — kind: notfound · login · limit · timeout · error"""

    def __init__(self, message: str, kind: str = "error"):
        super().__init__(message)
        self.kind = kind


# ---------------------------------------------------------------- 찾기
def _version_key(path: Path) -> tuple[int, ...]:
    """…/anthropic.claude-code-2.1.301-win32-x64/… → (2, 1, 301)"""
    m = re.search(r"anthropic\.claude-code-(\d+)\.(\d+)\.(\d+)", str(path))
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


def _newest_in(ext_root: Path) -> list[Path]:
    if not ext_root.is_dir():
        return []
    found = [d / "resources" / "native-binary" / EXE for d in ext_root.glob("anthropic.claude-code-*")]
    found = [p for p in found if p.is_file()]
    return sorted(found, key=_version_key, reverse=True)


def candidates() -> list[tuple[Path, str]]:
    """(경로, 어디서) — 찾는 순서대로."""
    home = Path.home()
    out: list[tuple[Path, str]] = []
    env = os.environ.get("CLAUDE_BIN", "").strip().strip('"')
    if env:
        out.append((Path(env).expanduser(), "환경 변수 CLAUDE_BIN"))
    on_path = shutil.which(EXE) if WINDOWS else shutil.which("claude")   # Windows는 .exe만(npm의 .cmd 껍데기는 건너뛴다)
    if on_path:
        out.append((Path(on_path), "PATH"))
    groups = [
        ([".vscode", ".vscode-insiders"], "VS Code 확장에 들어 있는 것"),
        ([".cursor"], "Cursor 확장에 들어 있는 것"),
        ([".vscode-server", ".vscode-server-insiders", ".cursor-server", ".vscode-remote"], "원격 · WSL · Codespaces 확장에 들어 있는 것"),
    ]
    for dirs, label in groups:
        for d in dirs:
            out += [(p, label) for p in _newest_in(home / d / "extensions")]
    for p in (home / ".local" / "bin" / EXE, home / ".claude" / "local" / EXE):
        out.append((p, "따로 설치한 것"))
    seen, uniq = set(), []
    for p, where in out:
        key = str(p).lower() if WINDOWS else str(p)
        if key not in seen:
            seen.add(key)
            uniq.append((p, where))
    return uniq


def clean_env() -> dict[str, str]:
    """API 키 · 바깥 Claude Code 세션의 표시를 지운 환경 — 구독으로, 따로 떨어진 한 번의 호출로 돈다."""
    env = {k: v for k, v in os.environ.items()
           if k.upper() != "ANTHROPIC_API_KEY" and k.upper() != "CLAUDECODE" and not k.upper().startswith("CLAUDE_CODE_")}
    env["DISABLE_AUTOUPDATER"] = "1"
    return env


def _run_version(path: Path) -> str | None:
    try:
        r = subprocess.run([str(path), "--version"], capture_output=True, timeout=60, env=clean_env(),
                           cwd=_work_dir(), stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (r.stdout or b"").decode("utf-8", "replace").strip()
    return text if r.returncode == 0 and text else None


def _parse_version(text: str) -> tuple[int, ...]:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)


_FOUND: tuple[Path, str, str] | None = None


def find_claude() -> tuple[Path, str, str]:
    """(경로, 어디서, 판 글자) — 못 찾으면 AskClaudeError(kind='notfound')."""
    global _FOUND
    if _FOUND:
        return _FOUND
    tried = []
    for path, where in candidates():
        if not path.is_file():
            continue
        ver = _run_version(path)
        if ver and _parse_version(ver) >= MIN_VERSION:
            _FOUND = (path, where, ver)
            return _FOUND
        tried.append(f"{path} ({ver or '실행 안 됨'})")
    hint = (" 찾았지만 쓸 수 없는 것: " + "; ".join(tried)) if tried else ""
    raise AskClaudeError("claude를 찾지 못했습니다 — VS Code에서 Claude Code 확장을 설치 · 업데이트하거나, "
                         "환경 변수 CLAUDE_BIN에 claude 경로를 넣으세요. 로봇은 --no-ai로도 돕니다." + hint, "notfound")


def _work_dir() -> str:
    d = Path(tempfile.gettempdir()) / "ask_claude_work"
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


# ---------------------------------------------------------------- 부르기
def _kind_of(text: str) -> str:
    low = (text or "").lower()
    if any(w in low for w in ("log in", "login", "/login", "not logged", "authenticat", "invalid api key", "oauth", "credential")):
        return "login"
    if any(w in low for w in ("usage limit", "limit reached", "rate limit", "quota", "too many requests", "429")):
        return "limit"
    return "error"


def _last_json(text: str) -> dict | None:
    text = (text or "").strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except ValueError:
        pass
    for line in reversed(text.splitlines()):        # 앞에 다른 줄이 섞였으면 마지막 JSON 줄
        line = line.strip()
        if line.startswith("{"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    return obj
            except ValueError:
                continue
    return None


def ask_json(prompt: str, schema: dict, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """질문(prompt) 하나를 보내고 schema 모양의 dict 하나를 받는다. 실패하면 AskClaudeError."""
    path, _, _ = find_claude()
    cmd = [str(path), "-p", "--output-format", "json", "--json-schema", json.dumps(schema, ensure_ascii=True),
           "--tools", "", "--no-session-persistence", "--model", model]
    try:
        r = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True, timeout=timeout,
                           env=clean_env(), cwd=_work_dir())
    except subprocess.TimeoutExpired as e:
        raise AskClaudeError(f"{timeout}초 안에 답이 오지 않았습니다(시간 초과)", "timeout") from e
    except OSError as e:
        raise AskClaudeError(f"claude를 실행하지 못했습니다 — {e}", "error") from e
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    data = _last_json(out)
    if not data:
        msg = (err.strip() or out.strip() or f"종료 코드 {r.returncode}").splitlines()[0][:300]
        raise AskClaudeError(f"답을 읽지 못했습니다 — {msg}", _kind_of(err + out))
    if data.get("is_error") or data.get("subtype") not in (None, "success"):
        msg = str(data.get("result") or data.get("subtype") or "오류")[:300]
        raise AskClaudeError(f"claude가 오류로 답했습니다 — {msg}", _kind_of(msg + err))
    answer = data.get("structured_output")
    if not isinstance(answer, dict):                 # 예전 판: 답 글자에 JSON이 들어 있다
        answer = _last_json(str(data.get("result", "")))
    if not isinstance(answer, dict):
        raise AskClaudeError("답이 JSON 모양이 아닙니다(structured_output 없음)", "error")
    return answer


# ---------------------------------------------------------------- 확인(--check)
def check(model: str) -> int:
    ok_mark, bad_mark = "✓", "✗"
    try:
        path, where, ver = find_claude()
    except AskClaudeError as e:
        print(f"{bad_mark} {e}")
        return 2
    print(f"{ok_mark} claude 찾음 — {path} ({where})")
    print(f"{ok_mark} 판 — {ver}")
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{ok_mark} API 키는 이 도우미가 지우고 부릅니다 — 구독 사용, 추가 청구 없음")
    else:
        print(f"{ok_mark} API 키 없음 — 구독 사용, 추가 청구 없음")
    t0 = time.time()
    try:
        ans = ask_json(PING_PROMPT, PING_SCHEMA, model=model, timeout=120)
    except AskClaudeError as e:
        tip = {"login": " → VS Code의 Claude Code 패널에서 한 번 로그인한 뒤 다시 실행하세요",
               "limit": " → 사용 한도입니다. 풀릴 때까지 로봇은 --no-ai로 돌립니다",
               "timeout": " → 인터넷 연결을 확인하고 한 번 더 실행하세요"}.get(e.kind, "")
        print(f"{bad_mark} 시험 호출 실패 — {e}{tip}")
        return 1
    secs = time.time() - t0
    print(f"{ok_mark} 시험 호출 — {json.dumps(ans, ensure_ascii=False, separators=(',', ':'))} ({secs:.1f}초 · {model})")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):          # Windows 터미널 · 파이프에서도 한글이 깨지지 않게
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="VS Code 확장의 claude를 찾아 JSON 질문 하나를 부르는 도우미")
    ap.add_argument("--check", action="store_true", help="찾기 · 판 · API 키 · 시험 호출을 확인한다")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="모델 별명(기본 sonnet · haiku도 된다)")
    args = ap.parse_args(argv)
    if args.check:
        return check(args.model)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
