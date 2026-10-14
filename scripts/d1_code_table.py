"""1일차: payment_terms_raw 표기 → 표준 결제조건 코드 7종 매핑표 만들기 — 원본은 읽기만 한다.

실행: uv run python scripts/d1_code_table.py [엑셀 경로]
      (파일 열기가 막히면) cat data/day1/d1_buyers_raw.xlsx | uv run python scripts/d1_code_table.py -
출력: workbench/day1/outputs/d1_code_table.csv (utf-8-sig, 엑셀에서 한글 유지)

판단은 공백 제거 · 대문자로 바꾼 표기에 아래 규칙을 위에서부터 차례로 적용한다.
코드 정의는 data/data_dictionary.xlsx 시트 codes(payment_method)를 따른다.
어느 규칙에도 확실히 맞지 않으면 '검토 필요'로 두고 추측하지 않는다.
"""

import io
import re
import sys

import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/day1/d1_buyers_raw.xlsx"
OUT = "workbench/day1/outputs/d1_code_table.csv"
REVIEW = "검토 필요"

# (정규식, 표준 코드, 판단 근거, 확신) — 위에서부터 첫 번째로 맞는 규칙을 쓴다.
RULES = [
    # 분할: 비율이 30/70이 아니면 표준 코드에 맞지 않는다.
    (r"10% T/T ADVANCE \+ 90% O/A", REVIEW,
     "'10% T/T advance' + '90% O/A' — 선수 10%·잔금 90%로 TT_SPLIT_30_70(30/70)과 비율이 다름", "낮음"),
    (r"30% T/T ADVANCE, 70%", "TT_SPLIT_30_70",
     "'30% T/T advance' + '70% within 30 days after B/L' — codes 정의 문구와 같음", "높음"),
    (r"^T/T 30[/:]70$", "TT_SPLIT_30_70", "'T/T' + 비율 '30/70'(30:70) — 분할 송금 30/70", "높음"),
    # 선수금
    (r"IN ADVANCE|BEFORE SHIPMENT", "TT_ADV", "'in advance' / 'before shipment' — 선적 전 송금", "높음"),
    # 신용장
    (r"신용장 일람불", "LC_SIGHT", "'신용장'(L/C) + '일람불'(at sight)", "높음"),
    (r"L/?C AT SIGHT", "LC_SIGHT", "'L/C' + 'at sight'", "높음"),
    (r"USANCE L/C", "LC_USANCE", "'Usance L/C' — 기한부 신용장", "높음"),
    (r"^L/C \d+ DAYS$", "LC_USANCE",
     "'L/C' + 일수 — 'usance' 단어는 없지만 일수가 붙어 기한부로 판단", "낮음"),
    # 추심
    (r"^D/?P\b", "DP", "'D/P' — Documents against payment", "높음"),
    (r"^D/?A ?\d|DOCUMENTS AGAINST ACCEPTANCE", "DA", "'D/A' / 'Documents against acceptance'", "높음"),
    # 사후송금
    (r"\bO/?A(\b|\d)|OPEN ACC(OUN)?T", "OA", "'O/A' / 'OA' / 'Open account'", "높음"),
    (r"^NET \d+", "OA", "'Net N' — codes 시트 OA 설명에 'Net N' 포함", "높음"),
    (r"^T/T \d+ ?DAYS", "OA", "'T/T' + 일수 — codes 시트 OA 설명: 'T/T + 일수 표기는 사후송금 = O/A'", "높음"),
    # 시기 정보가 없는 송금
    (r"^TT$", REVIEW, "'TT'만 있음 — 선적 전(선수금)인지 선적 후(O/A)인지 알 수 없음", "낮음"),
]


def classify(raw):
    key = re.sub(r"\s+", " ", raw.strip().upper())
    for pat, code, why, conf in RULES:
        if re.search(pat, key):
            return code, why, conf
    return REVIEW, "맞는 규칙 없음", "낮음"


raw = sys.stdin.buffer.read() if SRC == "-" else open(SRC, "rb").read()
df = pd.read_excel(io.BytesIO(raw), sheet_name="buyers", dtype=object)
terms = sorted(df["payment_terms_raw"].dropna().unique(), key=lambda s: (s.strip().upper(), s))

rows = [(t, *classify(t)) for t in terms]
out = pd.DataFrame(rows, columns=["원래 표기", "표준 코드", "판단 근거(어느 단어로)", "확신(높음/낮음)"])
out.to_csv(OUT, index=False, encoding="utf-8-sig")

n = df["payment_terms_raw"].value_counts()
print(f"표기 {len(out)}종 → {OUT}")
print(out.assign(행수=out["원래 표기"].map(n)).groupby("표준 코드")["행수"].agg(["count", "sum"])
      .rename(columns={"count": "표기 수", "sum": "행 수"}).to_string())
print(out.groupby("확신(높음/낮음)").size().to_string())
