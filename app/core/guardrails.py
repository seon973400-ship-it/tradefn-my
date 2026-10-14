"""독촉 초안 가드레일 — 하나라도 실패하면 [승인] 버튼을 막는다.

① 금지 표현(영·한): 진행하지 않은 법적 절차·국가기관 오인·위협 표현(채권추심법 제9·11조 취지) + 계좌 정보 변경 문구(사기 예방)
② 필수 요소(단계별) ③ 길이 ≤ 180단어 ④ 수신자 화이트리스트 ⑤ 발송 시간창(수신지 현지 08:00–21:00)
시연 5의 에이전트도 같은 검사를 쓴다.
"""
from __future__ import annotations

import fnmatch
import re
from datetime import datetime
from zoneinfo import ZoneInfo

# 금지 표현 정규식(단어 경계로 courtesy·issue 오탐 방지)
BLOCK_EN = re.compile(r"(?i)(legal action|legal proceedings|\bcourt\b|\blawsuit\b|\bsue\b|\bsuing\b|attorney|lawyer|police|"
                      r"criminal|prosecut|\bseiz|garnish|blacklist|credit bureau|report you to|arrest|interpol)")
BLOCK_KO = re.compile(r"(법원|경찰|검찰|형사|고소|소송|압류|체포|신용불량|블랙리스트|법적 조치)")
BANK_CHANGE = re.compile(r"(?i)(new (bank )?account|updated? bank|change[sd]? (of |in |to )?(our |the )?bank|bank (account )?details? (have|has) changed|"
                         r"\biban\b|swift code|account number|routing number)")
MAX_WORDS = 180
DEFAULT_WHITELIST = [r"^buyer\+B\d{3}@example\.com$"]   # 자리표시 주소(가상) — 수업에서는 본인 Gmail 플러스 주소 패턴을 넣는다
SEND_WINDOW = (8, 21)                                     # 08:00 ≤ 현지 시각 < 21:00
COUNTRY_TZ = {"USA": "America/New_York", "MEX": "America/Mexico_City", "BRA": "America/Sao_Paulo", "DEU": "Europe/Berlin",
              "NLD": "Europe/Amsterdam", "GBR": "Europe/London", "POL": "Europe/Warsaw", "TUR": "Europe/Istanbul",
              "CHN": "Asia/Shanghai", "JPN": "Asia/Tokyo", "TWN": "Asia/Taipei", "VNM": "Asia/Ho_Chi_Minh",
              "IND": "Asia/Kolkata", "IDN": "Asia/Jakarta", "THA": "Asia/Bangkok", "MYS": "Asia/Kuala_Lumpur",
              "ARE": "Asia/Dubai", "SAU": "Asia/Riyadh", "EGY": "Africa/Cairo", "NGA": "Africa/Lagos"}


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def blocked_terms(text: str) -> list[str]:
    hits = [m.group(0) for m in BLOCK_EN.finditer(text or "")] + [m.group(0) for m in BLOCK_KO.finditer(text or "")]
    hits += [m.group(0) for m in BANK_CHANGE.finditer(text or "")]
    return sorted(set(hits), key=str.lower)


def required_missing(body: str, stage: str, facts: dict) -> list[str]:
    """단계별 필수 요소(템플릿 T0~T4). 금액은 숫자 부분만 본다(통화 표기 차이 허용)."""
    b = body or ""
    miss = []
    if facts.get("invoice_id") and facts["invoice_id"] not in b:
        miss.append("인보이스 번호")
    amt = str(facts.get("amount_ccy", "")).replace(",", "")
    if amt and amt.replace(".", "").isdigit():
        digits = re.sub(r"[^\d]", "", b)
        core = amt.split(".")[0]
        if core not in digits:
            miss.append("금액")
    if stage in ("DM3", "D7", "D15", "D30") and facts.get("due_date") and facts["due_date"] not in b:
        miss.append("결제기일")
    if stage == "D7" and not re.search(r"(?i)disregard", b):
        miss.append("'이미 지급했으면 무시' 문장")
    if stage in ("D15", "D30", "PRE") and facts.get("reply_by_date") and facts["reply_by_date"] not in b:
        miss.append("회신 기한")
    if stage == "D30" and not re.search(r"(?i)(on hold|hold)", b):
        miss.append("선적 보류 고지")
    if stage == "PRE" and facts.get("escalation_partner") and facts["escalation_partner"] not in b:
        miss.append("이관 대상")
    return miss


def whitelisted(email: str, patterns: list[str] | None = None) -> bool:
    """패턴: 정규식(^로 시작) 또는 와일드카드(*@example.com) 또는 정확한 주소."""
    email = (email or "").strip()
    for p in (patterns or DEFAULT_WHITELIST):
        p = p.strip()
        if not p:
            continue
        if p.startswith("^"):
            if re.match(p, email):
                return True
        elif "*" in p or "?" in p:
            if fnmatch.fnmatch(email.lower(), p.lower()):
                return True
        elif email.lower() == p.lower():
            return True
    return False


def in_send_window(now: datetime | None = None, tz: str = "Asia/Seoul") -> tuple[bool, str]:
    z = ZoneInfo(tz)
    local = (now.astimezone(z) if now and now.tzinfo else (now.replace(tzinfo=z) if now else datetime.now(z)))
    ok = SEND_WINDOW[0] <= local.hour < SEND_WINDOW[1]
    return ok, local.strftime("%Y-%m-%d %H:%M") + f" ({tz})"


def check_draft(subject: str, body: str, stage: str, facts: dict, recipient: str,
                whitelist: list[str] | None = None, now: datetime | None = None, tz: str = "Asia/Seoul") -> list[dict]:
    """가드레일 결과 목록 [{check, ok, detail}]. 모두 ok여야 승인 가능."""
    text = f"{subject}\n{body}"
    bad = blocked_terms(text)
    miss = required_missing(body, stage, facts)
    n = word_count(body)
    wl = whitelisted(recipient, whitelist)
    win, local = in_send_window(now, tz)
    return [
        {"check": "① 금지 표현", "ok": not bad, "detail": ", ".join(bad) if bad else "없음"},
        {"check": "② 필수 요소", "ok": not miss, "detail": ", ".join(miss) if miss else "모두 있음"},
        {"check": f"③ 길이 ≤ {MAX_WORDS}단어", "ok": n <= MAX_WORDS, "detail": f"{n}단어"},
        {"check": "④ 수신자 화이트리스트", "ok": wl, "detail": recipient if wl else f"{recipient} — 허용 목록에 없음"},
        {"check": "⑤ 발송 시간창(현지 08–21시)", "ok": win, "detail": local},
    ]


def passed(results: list[dict]) -> bool:
    return all(r["ok"] for r in results)


def summary_text(results: list[dict]) -> str:
    """감사로그 guardrail_result 칸: pass 또는 fail:①,③ …"""
    fails = [r["check"].split(" ")[0] for r in results if not r["ok"]]
    return "pass" if not fails else "fail:" + ",".join(fails)
