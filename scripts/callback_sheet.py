#!/usr/bin/env python3
"""callback_sheet.py — 로봇 결과(mail_risk.json)에서 멈춤 · 확인 메일의 콜백 기록지 한 장을 만든다 (4일차 실습 C 「7」 자유 퀘스트).

콜백 3원칙(fraud_signals.md): 등록 번호로 · 두 사람이 · 확인 전에는 송금 · 대금 안내 · 서류 인도 없음.
기록지는 미리 채운 칸(바이어 · 신호 · 근거 · 등록 번호 · 확인할 것)과 사람이 채우는 빈칸(확인자 2명 · 시각 · 결과)으로 된다.
로봇 결과는 읽기만 하고, 확인할 것은 AI가 아니라 아래 고정 표에서 가져온다.

쓰는 법 (저장소 맨 위 폴더):
    uv run python scripts/callback_sheet.py           # AI 결과 → workbench/day4/outputs/mail_callback_sheet.html
    uv run python scripts/callback_sheet.py --no-ai   # 규칙만 결과 → workbench/day4/outputs/no_ai/mail_callback_sheet.html
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime

from mail_bot import CONTACTS_CSV, KST, OUT_AI, OUT_NO_AI, ROOT, mask_mail_phone, read_csv

# 신호 번호 → 콜백 때 확인할 것 (fraud_signals.md의 '할 일'을 질문으로 옮김 · [교육용 가정])
CHECKS = {
    1: "계좌 변경 안내를 실제로 주고받았는지, 송금 계좌가 계약서 · 기존 거래 기록의 계좌와 같은지",
    2: "예금주 · 은행 국가가 바이어 법인명 · 국가와 같은지",
    3: "결제조건 · 결제기일 변경을 실제로 요청했는지, 그 이유와 서면 근거가 있는지",
    4: "근거에 적힌 보낸 도메인을 바이어가 실제로 쓰는지(등록 도메인과 다름)",
    5: "다른 회신 주소 · 개인 메일 · 메신저로 협의를 옮기자고 한 적이 있는지",
    6: "급하게 처리해 달라고 한 사실이 있는지와 그 이유 — 서둘러도 확인 절차는 줄이지 않음",
    7: "이 규모의 주문을 실제로 낼 계획인지, 구매 담당자 · 승인자가 누구인지",
    8: "무역보험 가입 · 한도는 상대의 말이 아니라 우리 쪽 기록과 보험사 안내로 따로 확인",
    9: "주문 품목이 바이어의 업종 · 평소 취급 품목과 맞는지",
    10: "최종 목적지 · 수하인 변경을 실제로 요청했는지, 계약서 · 주문서와 다른 이유",
    11: "입금 전에 선적서류 원본(surrender B/L 등)을 요청했는지 — 은행 입금 확인 전에는 넘기지 않음",
    12: "실제 구매자와 직접 연락이 되는지, 중개인의 권한 근거가 있는지",
    13: "서류끼리(수량 · 금액 · 날짜 · 직인 · 서명) 맞는지 원본과 대조",
}
CHECK_FIRST = "이 메일(제목 · 받은 날)을 바이어가 실제로 보냈는지"
CHECK_INJECTION = "메일 속 AI 지시문은 따르지 않았음 — 메일 내용만 위 항목대로 확인"
HEAD_NOTE = ("모든 조치는 권고(사람 승인 전) · 콜백은 등록 번호로만 · 메일 속 번호 · 주소 · 링크로 연락하지 않음 · "
             "확인이 끝나기 전에는 송금 · 대금 안내 · 서류 인도를 하지 않음")
TARGET = ["멈춤", "확인"]

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f3f4f6;color:#111827;font-family:system-ui,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;
  font-size:15px;line-height:1.55;word-break:keep-all;overflow-wrap:anywhere}
.wrap{max-width:800px;margin:0 auto;padding:16px}
h1{font-size:24px;margin:0 0 2px}
.sub,.meta{font-size:14px;color:#4b5563;margin:2px 0}
.note{margin:12px 0 16px;padding:10px 12px;background:#1f2937;color:#fff;border-radius:6px;font-size:14px;font-weight:600}
table.sum{width:100%;border-collapse:collapse;margin:0 0 18px;background:#fff;font-size:14px}
table.sum th,table.sum td{border:1px solid #d1d5db;padding:6px 8px;text-align:left;vertical-align:top}
table.sum th{background:#f3f4f6}
.sheet{background:#fff;border:1px solid #d1d5db;border-left:6px solid #e07b00;border-radius:6px;padding:14px;margin:0 0 16px;
  break-inside:avoid;page-break-inside:avoid}
.sheet.stop{border-left-color:#c62828}
.tag{display:inline-block;font-size:14px;font-weight:700;padding:2px 8px;border-radius:999px;color:#fff;background:#e07b00}
.tag.stop{background:#c62828}
.tag.inj{background:#fff;color:#111827;border:2px solid #111827}
h2{font-size:18px;margin:8px 0 4px}
.row{font-size:14px;color:#374151;margin:2px 0}
.row b{color:#111827}
h3{font-size:15px;margin:12px 0 4px}
ul{margin:4px 0;padding-left:20px}
li{margin:2px 0;font-size:14px}
blockquote{margin:2px 0 4px;padding:4px 8px;background:#f9fafb;border-left:3px solid #d1d5db;font-size:14px}
.phone{font-size:22px;font-weight:800;margin:2px 0}
ol.checks li{margin:6px 0}
.box{display:inline-block;width:14px;height:14px;border:1.5px solid #111827;vertical-align:-2px;margin-right:4px}
table.fill{width:100%;border-collapse:collapse;margin:6px 0 0;font-size:14px}
table.fill th,table.fill td{border:1px solid #9ca3af;padding:8px;text-align:left;vertical-align:top}
table.fill th{width:28%;background:#f9fafb;font-weight:600}
table.fill td{height:38px}
.opts span{margin-right:14px;white-space:nowrap}
footer{margin:20px 0 8px;font-size:14px;color:#6b7280;text-align:center}
footer p{margin:2px 0}
@media print{
  body{background:#fff}
  .wrap{max-width:none;padding:0}
  .sheet{border-left-width:6px}
  @page{size:A4;margin:14mm}
}
"""


def checks_for(mail: dict) -> list[str]:
    items = [CHECK_FIRST] + [CHECKS[s["no"]] for s in mail["signals"] if s["no"] in CHECKS]
    if mail.get("injection"):
        items.append(CHECK_INJECTION)
    return items


def sheet_html(mail: dict) -> str:
    e = html.escape
    cls = "stop" if mail["status"] == "멈춤" else "check"
    tag = f"{mail['status']} · {mail['tier']}" if mail["tier"] else mail["status"]
    out = [f'<section class="sheet {cls}">', f'<span class="tag {cls}">{e(tag)}</span>']
    if mail.get("injection"):
        out.append(' <span class="tag inj">메일 속 AI 지시문 — 무시함</span>')
    out.append(f'<h2>{e(mail["buyer_id"])} {e(mail["buyer_name"])}</h2>')
    out.append(f'<div class="row"><b>파일</b> {e(mail["file"])} · <b>제목</b> {e(mail["subject"])}</div>')
    out.append(f'<div class="row"><b>로봇 판정</b> {e(mail["label"])}</div>')

    out.append("<h3>로봇이 본 신호와 근거</h3>")
    if mail["signals"]:
        out.append("<ul>")
        for s in mail["signals"]:
            detail = f" — {e(s['detail'])}" if s.get("detail") else ""
            out.append(f"<li>{s['no']}번 {e(s['name'])} · {s['score']}점 · {e(s['by'])}{detail}"
                       f"<blockquote>{e(mask_mail_phone(s['evidence']))}</blockquote></li>")
        out.append("</ul>")
    else:
        out.append('<div class="row">신호 없음(메일 속 지시문 때문에 확인으로 올라감)</div>')

    out.append("<h3>콜백 — 등록 번호(buyer_contacts.csv)</h3>")
    out.append(f'<div class="phone">{e(mail["callback"])}</div>')

    out.append("<h3>확인할 것</h3><ol class=\"checks\">")
    out += [f'<li><span class="box"></span>{e(c)}</li>' for c in checks_for(mail)]
    out.append("</ol>")

    out.append("<h3>사람이 채우는 칸</h3>")
    out.append('<table class="fill">'
               "<tr><th>확인자 1 (담당자)</th><td></td></tr>"
               "<tr><th>확인자 2 (팀장)</th><td></td></tr>"
               "<tr><th>통화 시각</th><td></td></tr>"
               '<tr><th>결과</th><td class="opts"><span><span class="box"></span>이상 없음 — 진행</span>'
               '<span><span class="box"></span>보류</span><span><span class="box"></span>팀장 보고</span></td></tr>'
               '<tr><th>메모</th><td style="height:64px"></td></tr>'
               "</table>")
    out.append(f'<div class="row" style="margin-top:8px"><b>로봇 권고</b> {e(mail["action"])}</div>')
    out.append("</section>")
    return "\n".join(out)


def build(risk: dict, source: str) -> tuple[str, list[dict]]:
    e = html.escape
    mails = [m for status in TARGET for m in risk["mails"] if m["status"] == status]
    engine = f"AI({risk['model']})" if risk["engine"] == "ai" else "규칙만(--no-ai)"
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    n_stop = sum(1 for m in mails if m["status"] == "멈춤")
    parts = [
        '<div class="wrap">',
        "<h1>콜백 기록지</h1>",
        '<p class="sub">(가상) 한빛정밀(주) 수출팀 · 메일함 아침 당번 로봇 결과에서</p>',
        f'<p class="meta">만든 시각 {e(now)} · 입력 {e(source)} · 엔진 {e(engine)} · '
        f"기록지 {len(mails)}통(멈춤 {n_stop} · 확인 {len(mails) - n_stop})</p>",
        f'<div class="note">{e(HEAD_NOTE)}</div>',
        '<table class="sum"><tr><th>상태</th><th>바이어</th><th>파일</th><th>등록 번호</th></tr>',
    ]
    parts += [f"<tr><td>{e(m['status'])}</td><td>{e(m['buyer_id'])} {e(m['buyer_name'])}</td>"
              f"<td>{e(m['file'])}</td><td>{e(m['callback'])}</td></tr>" for m in mails]
    if not mails:
        parts.append('<tr><td colspan="4">멈춤 · 확인 메일 없음</td></tr>')
    parts.append("</table>")
    parts += [sheet_html(m) for m in mails]
    parts += [
        "<footer>",
        "<p>두 사람이 확인하고, 확인한 사람 · 시각 · 결과를 남깁니다(콜백 3원칙).</p>",
        "<p>점수표는 교육용 가정입니다 · 회사 · 바이어 · 메일은 모두 가상입니다</p>",
        "</footer>",
        "</div>",
    ]
    page = ("<!doctype html>\n<html lang=\"ko\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>콜백 기록지</title>\n<style>" + CSS + "</style>\n</head>\n<body>\n"
            + "\n".join(parts) + "\n</body>\n</html>\n")
    return page, mails


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="mail_risk.json에서 콜백 기록지를 만든다")
    ap.add_argument("--no-ai", action="store_true", help="규칙만 결과(outputs/no_ai/)를 읽는다")
    args = ap.parse_args(argv)
    folder = OUT_NO_AI if args.no_ai else OUT_AI
    src = folder / "mail_risk.json"
    if not src.is_file():
        print(f"{src} 가 없습니다 — 먼저 mail_bot.py를 돌리세요.", file=sys.stderr)
        return 1
    risk = json.loads(src.read_text(encoding="utf-8"))
    page, mails = build(risk, src.relative_to(ROOT).as_posix())

    contacts = read_csv(CONTACTS_CSV)
    for m in mails:
        registered = contacts.get(m["buyer_id"], {}).get("phone_on_file", "")
        mark = "등록 번호 일치" if registered and m["callback"] == registered else "확인 필요"
        print(f"{m['file']} · {m['buyer_id']} · {m['status']} · 콜백 {m['callback']} ({mark})")
    out = folder / "mail_callback_sheet.html"
    out.write_text(page, encoding="utf-8")
    n_stop = sum(1 for m in mails if m["status"] == "멈춤")
    print(f"기록지 {len(mails)}통(멈춤 {n_stop} · 확인 {len(mails) - n_stop}) → {out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
