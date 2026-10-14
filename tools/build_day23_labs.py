#!/usr/bin/env python
"""Day2·Day3 실습 양식 4종을 만들고 검사한다(v4 — Orange 워크플로·Challenge 노트북은 쓰지 않는다. 옛 생성기 build_day2/3_orange.py · build_day2/3_notebook.py는 v3용).

만드는 파일(수강생용 = 공개 저장소, 정답 없음)
  labs/day2/news_warmup_10.txt          실습 B 워밍업 뉴스 10건(한 4 · 영 6) — d2_news.csv 앞쪽 행 그대로, 점수 없음(채팅 경로 형식 시험용)
  labs/day2/byod_anonymize_template.xlsx 자사 엑셀 익명화 점검표 + 가상 예시 변환 수식(사이트 setup.md#byod)
  labs/day3/d3_grade_banding.xlsx       등급 매칭 시트(실습 B-1): pred(붙여넣기 칸 — grade 열은 비워 두고 IFS를 직접 쓴다) · 이름 t(빈칸) · 기준·분포 · 단조성
  labs/day3/d3_shap_report_template.md / .docx  근거 메모 1장(실습 B-2) — 메모 프롬프트(B4) 출력 5칸 + 그림 2칸(같은 내용 두 형식)
강사용(저장소 밖 ../instructor/day3/answers/)
  d3_grade_banding_filled.xlsx — 강사 정답 모델(d3_end_scored.csv)의 pd_30d + models/grade_cutoffs.json의 t + 검증 예측
  (d3_oot_predictions.csv)으로 채운 판(grade 열 IFS 포함). --check가 pycel로 다시 계산해 정답표(d3_cutoffs.csv)의 등급 수 · 검증 연체율과 대조한다.

사용(저장소 루트):
  python tools/build_day23_labs.py           # 생성 + 검사
  python tools/build_day23_labs.py --check   # 생성 없이 검사만
필요 패키지: pandas · openpyxl · python-docx · pycel(검사). 입력: data/checkpoints/d2_news.csv · d3_end_scored.csv ·
models/grade_cutoffs.json · ../instructor/day3/answers/(d3_oot_predictions.csv · d3_cutoffs.csv) — 강사 PC에서 돈다.
공개 저장소 파일이다 — 정답 숫자를 코드에 적지 않는다(t·등급 수는 정답 파일에서 읽어 강사용 판·검사에만 쓴다).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CK = REPO / "data" / "checkpoints"
LAB2 = REPO / "labs" / "day2"
LAB3 = REPO / "labs" / "day3"
ANS3 = REPO.parent / "instructor" / "day3" / "answers"

WARMUP = LAB2 / "news_warmup_10.txt"
BYOD = LAB2 / "byod_anonymize_template.xlsx"
BANDING = LAB3 / "d3_grade_banding.xlsx"
BANDING_FILLED = ANS3 / "d3_grade_banding_filled.xlsx"
SHAP_MD = LAB3 / "d3_shap_report_template.md"
SHAP_DOCX = LAB3 / "d3_shap_report_template.docx"

PRED_ROWS = 150          # 예측 대상 바이어 수(d3_start_scoring.csv)
MONO_ROWS = 1200         # 단조성 시트 붙여넣기 칸(수강생 시험셋 88행 · 강사 검증 1,084행)
REF_DATE = (2026, 9, 30)

FONT = "맑은 고딕"
BLUE, YELLOW, GRAY, RED = "DDEBF7", "FFF2CC", "EDEDED", "C00000"


# ---------------------------------------------------------------- 1) 워밍업 10건
def build_warmup() -> Path:
    news = pd.read_csv(CK / "d2_news.csv", encoding="utf-8-sig", dtype=str)
    first = news.head(100)
    en = first[first["lang"] == "en"].head(6)
    ko = first[first["lang"] == "ko"].head(4)
    pick = pd.concat([en, ko]).sort_index()                       # 파일 순서(최신순) 그대로
    assert len(pick) == 10 and pick.index.max() < 50, "워밍업은 배치 1(앞 50행) 안에서 고른다"
    cols = ["news_id", "buyer_id", "date", "headline", "body_short"]
    for c in cols:
        assert not pick[c].str.contains("\t|\n", regex=True).any(), f"{c}에 탭·줄바꿈"
    lines = [
        "2일차 실습 B 워밍업 — 뉴스 10건(한국어 4 · 영어 6)",
        "",
        "- 과정 제작 합성 뉴스입니다(가상 바이어 · d2_news.csv 앞쪽 행과 같은 문장). 점수는 들어 있지 않습니다.",
        "- 언제 쓰나: **웹 채팅 경로**에서 50행을 붙여 넣기 전에 먼저 10건으로 형식을 시험할 때. 채팅창에 workbench/day2/prompts/news_score_v1.md의 내용을 붙이고, 이 파일의 '복사 시작'과 '복사 끝' 사이(머리글 + 10행)를 아래에 붙여 보냅니다(탭 구분). Claude Code로 하는 기본 경로에서는 쓰지 않아도 됩니다.",
        "- 이 10건은 앞 50행에 다시 들어 있습니다 — 같은 뉴스의 점수가 워밍업 때와 같은지 보면 일관성을 확인할 수 있습니다.",
        "- 척도는 0–10(0–5 부정·위험, 6–10 긍정·중립)이고, 점수 경계는 news_score_v1.md의 [척도]를 따릅니다.",
        "- 과정 제작 합성 뉴스 · CC BY 4.0. 회사 실명·실데이터가 아닙니다.",
        "",
        "===== 복사 시작 =====",
        "\t".join(cols),
        *("\t".join(r) for r in pick[cols].itertuples(index=False)),
        "===== 복사 끝 =====",
        "",
    ]
    WARMUP.write_text("\n".join(lines), encoding="utf-8")
    return WARMUP


# ---------------------------------------------------------------- xlsx 공통
def _wb_style(wb):
    from openpyxl.styles import Font

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None and c.font.name != FONT:
                    f = c.font
                    c.font = Font(name=FONT, size=f.size or 10, bold=f.bold, italic=f.italic, color=f.color)


def _fill(hex_):
    from openpyxl.styles import PatternFill

    return PatternFill("solid", start_color=hex_, end_color=hex_)


def _head(ws, row, values, color=BLUE, col0=1):
    from openpyxl.styles import Alignment, Border, Font, Side

    thin = Side(style="thin", color="999999")
    for j, v in enumerate(values):
        c = ws.cell(row=row, column=col0 + j, value=v)
        c.font = Font(name=FONT, bold=True, size=10)
        c.fill = _fill(color)
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = Border(bottom=thin, top=thin, left=thin, right=thin)


def _text_sheet(ws, title, lines, width=110):
    from openpyxl.styles import Alignment, Font

    ws["A1"] = title
    ws["A1"].font = Font(name=FONT, bold=True, size=14)
    for i, line in enumerate(lines, start=3):
        c = ws.cell(row=i, column=1, value=line)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if line.startswith("■"):
            c.font = Font(name=FONT, bold=True, size=11)
    ws.column_dimensions["A"].width = width


# ---------------------------------------------------------------- 2) BYOD 익명화 점검표
BYOD_RULES = [  # (원본 칸, 처리 규칙, 예(가상)) — 사이트 setup.md#byod
    ("바이어명 · 담당자명 · 이메일 · 전화", "지우고 BUYER_### 코드로 바꾼다. 코드 ↔ 실제 이름 대응표는 내 PC의 별도 파일(…_private.xlsx)에만 둔다",
     "(가상) Alpha Trading GmbH → BUYER_001"),
    ("국가", "그 나라 바이어가 3곳 미만이면 권역으로 올린다", "KEN(1곳) → 사하라 이남 아프리카"),
    ("금액", "파일마다 비밀 계수 k(0.5~2.0 사이 아무 수)를 곱하거나 구간으로 바꾼다", "123,400 × k(1.37) → 169,100 · 또는 '5만~20만'"),
    ("날짜", "바이어별로 같은 날수(0~90일)만큼 옮긴다 — 연체일 · 결제기간 같은 '간격'은 그대로", "2025-03-02 → 2025-04-11(+40일)"),
    ("인보이스 · L/C · B/L 번호", "1, 2, 3 … 순번으로 새로 매긴다", "INV-2025-0383 → INV-0001"),
    ("메모 · 메일 본문 같은 자유 서술", "지우거나 분류 코드로 바꾼다(분쟁 사유 = 품질 / 수량 / 서류 / 가격)", "\"customer claims damaged goods\" → DISPUTE_QUALITY"),
    ("은행 · 계좌 정보", "완전히 지운다(코드로도 남기지 않는다)", "— (열 삭제)"),
]
BYOD_FINAL = [
    "파일 안에서 회사 이름 · 이메일 도메인을 검색(Ctrl+F)해 0건이다",
    "한 행만 보고 어느 회사인지 알 수 없다(국가 + 업종 + 금액 조합으로도)",
    "회사 보안 규정 · NDA(비밀유지계약)에 어긋나지 않는다",
    "쓰려는 AI 서비스의 학습 설정을 껐다(무료 소비자 AI에는 원본을 넣지 않는다)",
]
BYOD_EXAMPLE = [  # 가상 예시 8행 — 실명·실계좌 아님(example 도메인 · 0으로 채운 계좌)
    ("(가상) Alpha Trading GmbH", "kim@alpha.example", "DEU", "INV-2025-0383", (2025, 3, 2), 123400, "partial payment, rest next month", "XX00 0000 0000 0001"),
    ("(가상) Alpha Trading GmbH", "kim@alpha.example", "DEU", "INV-2025-0391", (2025, 3, 18), 45800, "", "XX00 0000 0000 0001"),
    ("(가상) Beta Instruments Ltd", "ops@beta.example", "KEN", "INV-2025-0402", (2025, 4, 1), 18900, "customer claims damaged goods", "XX00 0000 0000 0002"),
    ("(가상) Gamma Industrial Co.", "buy@gamma.example", "VNM", "INV-2025-0410", (2025, 4, 9), 76250, "short shipment 2 boxes", "XX00 0000 0000 0003"),
    ("(가상) Gamma Industrial Co.", "buy@gamma.example", "VNM", "INV-2025-0433", (2025, 5, 6), 9800, "", "XX00 0000 0000 0003"),
    ("(가상) Delta Supplies S.A.", "pay@delta.example", "MEX", "INV-2025-0440", (2025, 5, 14), 212000, "invoice price disputed", "XX00 0000 0000 0004"),
    ("(가상) Epsilon Tech Kft.", "hu@eps.example", "DEU", "INV-2025-0452", (2025, 6, 3), 33300, "B/L copy missing", "XX00 0000 0000 0005"),
    ("(가상) Delta Supplies S.A.", "pay@delta.example", "MEX", "INV-2025-0460", (2025, 6, 20), 58100, "", "XX00 0000 0000 0004"),
]
BYOD_MEMO = {"partial payment, rest next month": "PAYMENT_PARTIAL", "customer claims damaged goods": "DISPUTE_QUALITY",
             "short shipment 2 boxes": "DISPUTE_QUANTITY", "invoice price disputed": "DISPUTE_PRICE",
             "B/L copy missing": "DISPUTE_DOCS", "": ""}
BYOD_KEY = [("(가상) Alpha Trading GmbH", "BUYER_001", 40), ("(가상) Beta Instruments Ltd", "BUYER_002", 12),
            ("(가상) Gamma Industrial Co.", "BUYER_003", 73), ("(가상) Delta Supplies S.A.", "BUYER_004", 5),
            ("(가상) Epsilon Tech Kft.", "BUYER_005", 61)]
BYOD_REGION = [("KEN", "사하라 이남 아프리카"), ("NGA", "사하라 이남 아프리카"), ("VNM", "동남아"), ("IDN", "동남아"),
               ("THA", "동남아"), ("MEX", "중남미"), ("BRA", "중남미"), ("DEU", "서유럽"), ("NLD", "서유럽"),
               ("POL", "중동부 유럽"), ("TUR", "중동"), ("SAU", "중동"), ("ARE", "중동"), ("EGY", "중동·북아프리카")]
BYOD_K = 1.37


def build_byod() -> Path:
    from datetime import date

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws0 = wb.active
    ws0.title = "00_사용법"
    _text_sheet(ws0, "자사 엑셀 익명화(BYOD) 점검표 — 내 업무 숫자를 다루기 전 · 6일차 기획서", [
        "■ 원칙 — 구조만 내 것, 값은 비식별",
        "원본은 내 PC의 엑셀에서만 연다. 익명화본도 GitHub(개인 저장소 · fork)와 과정의 AI 도구(ChatGPT · Claude · Claude Code)에는 넣지 않는다 — 내 PC의 엑셀 · 스크립트로만 다룬다(과정 뒤에는 회사가 허용한 AI 도구에서 같은 기준).",
        "■ 순서",
        "① 01_규칙표의 7행마다 '내 파일의 열 이름'을 적고, 처리했으면 '처리함'을 예로 바꾼다(해당 열이 없으면 '해당 없음').",
        "② 03_대응표_private 시트처럼 코드 · 날짜 이동 · 권역 · 비밀 계수 k를 만든다 → 이 시트는 별도 파일(예: byod_key_private.xlsx)로 옮겨 내 PC에만 둔다.",
        "③ 02_변환예시의 수식처럼 내 파일에 변환 열을 만든다(원본 열은 고치지 않는다).",
        "④ 변환 열만 '값 붙여넣기'로 새 통합 문서에 옮겨 저장한다(예: 내파일_anon.xlsx) — 원본 열 · 대응표 · k가 남지 않게.",
        "⑤ 01_규칙표 아래 '마지막 확인 4가지'가 모두 예이고, 판정 칸이 '통과'일 때만 실습에 쓴다.",
        "■ 파일 이름",
        "대응표 · 비밀 계수 파일 이름에는 _private를 넣는다(예: byod_key_private.xlsx) — 과정 저장소의 .gitignore가 git 커밋을 막는다. "
        "GitHub 웹의 'Upload files'는 .gitignore와 관계없이 올라가므로 올리기 전에 파일을 직접 확인한다.",
        "■ 근거와 한계",
        "규칙은 과정 사이트 '사전 준비 → 익명화 체크리스트'와 같다. 법률 자문이 아니다 — 회사 보안 규정 · NDA가 먼저다.",
        "실수로 실데이터를 올렸다면: 그 대화를 바로 삭제 → 강사 · 도우미에게 알림(비난하지 않고 기록만) → 가상 데이터로 계속.",
    ])
    # ---- 01_규칙표
    ws = wb.create_sheet("01_규칙표")
    ws["A1"] = "익명화 규칙 7가지 + 마지막 확인 4가지"
    ws["A1"].font = Font(name=FONT, bold=True, size=13)
    _head(ws, 2, ["#", "원본 칸", "이렇게 바꾼다", "예(가상)", "내 파일의 열 이름", "처리함", "메모"])
    for i, (src, rule, ex) in enumerate(BYOD_RULES, start=1):
        r = 2 + i
        for j, v in enumerate([i, src, rule, ex, None, None, None], start=1):
            c = ws.cell(row=r, column=j, value=v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(row=r, column=5).fill = _fill(YELLOW)
        ws.cell(row=r, column=6).fill = _fill(YELLOW)
    r0 = 2 + len(BYOD_RULES) + 2                      # 12
    _head(ws, r0, ["#", "마지막 확인", "", "", "", "예/아니오", "메모"])
    for i, txt in enumerate(BYOD_FINAL, start=1):
        r = r0 + i
        ws.cell(row=r, column=1, value=f"확인 {i}")
        c = ws.cell(row=r, column=2, value=txt)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        ws.cell(row=r, column=6).fill = _fill(YELLOW)
    rule_rng = f"F3:F{2 + len(BYOD_RULES)}"
    fin_rng = f"F{r0 + 1}:F{r0 + len(BYOD_FINAL)}"
    rj = r0 + len(BYOD_FINAL) + 2
    ws.cell(row=rj, column=2, value="판정").font = Font(name=FONT, bold=True)
    ws.cell(row=rj, column=3, value=(   # 규칙 7행이 모두 예/해당 없음 + 마지막 확인 4행이 모두 예일 때만 통과
        f'=IF(AND(COUNTIF({rule_rng},"예")+COUNTIF({rule_rng},"해당 없음")={len(BYOD_RULES)},'
        f'COUNTIF({fin_rng},"예")={len(BYOD_FINAL)}),"통과 — 실습에 써도 된다","미통과 — 아직 쓰지 않는다")'))
    ws.cell(row=rj, column=3).font = Font(name=FONT, bold=True, color=RED)
    dv1 = DataValidation(type="list", formula1='"예,아니오,해당 없음"', allow_blank=True)
    dv2 = DataValidation(type="list", formula1='"예,아니오"', allow_blank=True)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    dv1.add(rule_rng)
    dv2.add(fin_rng)
    for col, wdt in zip("ABCDEFG", (6, 24, 52, 36, 20, 11, 24)):
        ws.column_dimensions[col].width = wdt
    # ---- 03_대응표_private (먼저 만들어 두고 02가 참조)
    wk = wb.create_sheet("03_대응표_private")
    wk["A1"] = "이 시트는 공유 파일에 넣지 않는다 — 별도 파일(…_private.xlsx)로 옮겨 내 PC에만 둔다"
    wk["A1"].font = Font(name=FONT, bold=True, size=12, color=RED)
    _head(wk, 3, ["원본 바이어명", "코드", "날짜 이동(일)"])
    for i, (name, code, off) in enumerate(BYOD_KEY, start=4):
        wk.cell(row=i, column=1, value=name)
        wk.cell(row=i, column=2, value=code)
        wk.cell(row=i, column=3, value=off)
    _head(wk, 3, ["국가 코드", "권역"], col0=5)
    for i, (cc, reg) in enumerate(BYOD_REGION, start=4):
        wk.cell(row=i, column=5, value=cc)
        wk.cell(row=i, column=6, value=reg)
    wk["A22"] = "금액 비밀 계수 k(0.5~2.0) — 내 값으로 바꾸고 아무에게도 알리지 않는다"
    wk["A22"].font = Font(name=FONT, bold=True)
    wk["B23"] = BYOD_K
    wk["B23"].fill = _fill(YELLOW)
    wk["A23"] = "k ="
    for col, wdt in zip("ABCDEF", (30, 14, 14, 3, 12, 22)):
        wk.column_dimensions[col].width = wdt
    # ---- 02_변환예시
    we = wb.create_sheet("02_변환예시", 2)
    we["A1"] = "가상 예시 8행 — 왼쪽 원본(회색), 오른쪽 변환(파랑). 내 파일에서는 같은 수식을 내 열 이름 · 행 범위에 맞춰 쓴다"
    we["A1"].font = Font(name=FONT, bold=True, size=11)
    src_cols = ["buyer_name", "contact_email", "country", "invoice_no", "invoice_date", "amount_usd", "memo", "bank_account"]
    out_cols = ["buyer_code", "country_out", "invoice_seq", "invoice_date_out", "amount_out", "amount_band", "memo_code"]
    _head(we, 2, src_cols, color=GRAY)
    _head(we, 2, out_cols, color=BLUE, col0=10)
    n = len(BYOD_EXAMPLE)
    last = 2 + n
    key = "'03_대응표_private'!$A$4:$C$20"
    reg = "'03_대응표_private'!$E$4:$F$40"
    for i, (nm, em, cc, inv, d, amt, memo, bank) in enumerate(BYOD_EXAMPLE, start=3):
        for j, v in enumerate([nm, em, cc, inv, date(*d), amt, memo, bank], start=1):
            c = we.cell(row=i, column=j, value=v)
            if j == 5:
                c.number_format = "yyyy-mm-dd"
            if j == 6:
                c.number_format = "#,##0"
        we.cell(row=i, column=10, value=f'=IFERROR(VLOOKUP(A{i},{key},2,FALSE),"대응표에 없음")')
        we.cell(row=i, column=11, value=f'=IF(COUNTIF($C$3:$C${last},C{i})<3,IFERROR(VLOOKUP(C{i},{reg},2,FALSE),"기타 권역"),C{i})')
        we.cell(row=i, column=12, value='="INV-"&TEXT(ROW()-2,"0000")')
        c = we.cell(row=i, column=13, value=f"=E{i}+VLOOKUP(A{i},{key},3,FALSE)")
        c.number_format = "yyyy-mm-dd"
        c = we.cell(row=i, column=14, value=f"=ROUND(F{i}*'03_대응표_private'!$B$23,-2)")
        c.number_format = "#,##0"
        we.cell(row=i, column=15, value=(f'=IF(F{i}<10000,"1만 달러 미만",IF(F{i}<50000,"1만~5만",'
                                         f'IF(F{i}<200000,"5만~20만","20만 이상")))'))
        we.cell(row=i, column=16, value=BYOD_MEMO[memo])
    notes = [
        "buyer_code: 대응표에서 코드를 찾는다(VLOOKUP). 이메일 · 담당자 열은 변환하지 않고 지운다.",
        "country_out: 같은 나라가 3곳(행) 미만이면 권역으로 올린다 — 실제 파일에서는 '바이어 수'로 센다.",
        "invoice_seq: 행 순서대로 새 번호. 원래 번호는 남기지 않는다.",
        "invoice_date_out: 바이어별 같은 날수를 더한다 → 연체일 · 결제기간 같은 간격은 그대로다.",
        "amount_out / amount_band: 비밀 계수 k를 곱해 100단위로 반올림하거나, 구간으로 바꾼다(둘 중 하나만 공유).",
        "memo_code: 사람이 읽고 분류한다(품질 · 수량 · 서류 · 가격 · 지급). 자유 서술은 남기지 않는다. bank_account: 지운다.",
        "공유할 때는 파랑 열만 '값 붙여넣기'로 새 파일에 옮긴다.",
    ]
    for i, t in enumerate(notes, start=last + 2):
        we.cell(row=i, column=1, value=t).alignment = Alignment(wrap_text=False)
    for j, wdt in enumerate([28, 20, 8, 15, 12, 11, 30, 20, 3, 13, 22, 11, 15, 11, 13, 18], start=1):
        we.column_dimensions[chr(64 + j)].width = wdt
    _wb_style(wb)
    wb.save(BYOD)
    return BYOD


# ---------------------------------------------------------------- 3) 등급 매칭 시트
def build_banding(path: Path, filled: dict | None = None) -> Path:
    """v4 실습 B-1 등급 매칭 시트. 수강생판은 pred의 grade 열을 비워 두고(IFS를 직접 쓰고 채우기 핸들로 끈다),
    강사판(filled)은 grade 열에 IFS까지 넣고 값도 채운다."""

    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Font
    from openpyxl.workbook.defined_name import DefinedName
    from openpyxl.worksheet.table import Table, TableStyleInfo

    wb = Workbook()
    ws0 = wb.active
    ws0.title = "00_사용법"
    title = ("3일차 실습 B-1 — S/A/B/C 등급 매칭 시트" if filled else
             "3일차 실습 B-1 — S/A/B/C 등급 매칭 시트(빈 양식 · 선택) — 수업 시간에는 완성본 d3_grade_banding_example.xlsx를 쓰고, "
             "이 양식은 엑셀로 직접 해 보고 싶을 때(수업 뒤) 쓴다")
    _text_sheet(ws0, title, [
        "■ 규칙(C부터 검사) — C: pd_30d ≥ t · B: ≥ t/2 · A: ≥ t/4 · 나머지 S",
        "t = 실습 A-2에서 정한 임계값(비용 5:1이면 이론값 1 ÷ 6 ≈ 0.17). 등급은 회사 내부 관리 등급이며 무역보험의 공식 등급이 아니다.",
        "■ 순서",
        "① 기준 시트의 노란 칸(이름 t)에 내 t를 넣는다 — 경계값 t/4 · t/2 · t가 저절로 계산된다.",
        "② d3_scores.csv(buyer_id · ref_date · pd_30d, 150행)를 열어 데이터 3열을 복사해 pred 시트 A2부터 '값 붙여넣기' 한다(머리글은 이미 있다).",
        "③ pred 시트 D2에 IFS 수식을 쓰고 채우기 핸들(칸 오른쪽 아래의 작은 사각형)을 두 번 클릭하거나 150행까지 끌어 내린다:",
        '   =IFS(C2>=t,"C",C2>=t/2,"B",C2>=t/4,"A",TRUE,"S")   — 가장 위험한 C부터 검사한다(순서를 바꿔 A를 먼저 검사하면 B · C 행까지 A가 된다).',
        '   IFS가 없는 엑셀(2016 이하)이면 =IF(C2>=t,"C",IF(C2>=t/2,"B",IF(C2>=t/4,"A","S"))) 를 쓴다(뜻이 같다). 모두 같은 등급이면 이름 t가 비었거나 칸 이름이 다른지 본다.',
        "④ 조건부 서식: grade 열을 선택 → 홈 › 조건부 서식 › 셀 강조 규칙 › 같음 → C는 빨강, B는 주황(글자도 함께). 피벗 테이블로 등급별 바이어 수를 센다(기준 시트의 분포 표와 같아야 한다).",
        "⑤ 단조성: 실습 A의 d3_test_pred.csv(buyer_id · ref_date · late_30d · pd_30d, 88행) 데이터 4열을 단조성 시트 A2부터 붙인다 → 등급별 실제 연체율이 S < A < B < C 쪽으로 오르는지 본다.",
        "   시험셋 연체가 4건뿐이라 A · B는 행이 0~몇 개뿐이다 — 연체율이 0% 또는 100%로 뛰는 것은 표본 탓이니 건수와 함께 읽고, S와 C를 먼저 비교한다.",
        ("⑥ pred 시트(buyer_id · ref_date · pd_30d · grade)를 파일 › 다른 이름으로 저장 › CSV UTF-8(쉼표로 분리)로 workbench/day3/outputs/d3_grade_excel.csv에 저장한다. 최종 d3_end_scored.csv(6열)는 Claude Code가 같은 규칙으로 만들고 이 파일과 견준다." if filled else
         "⑥ 결과가 완성본(labs/day3/d3_grade_banding_example.xlsx)의 등급 분포 · 단조성 표와 같은지 본다. 다르면 t 값 · 붙여 넣은 행 수 · 수식 순서(C부터 검사)를 확인한다."),
        "■ 등급 → 결제조건 [교육용 가정]",
        "S · A: O/A 유지 · B: 결제기간 단축 · 부보 검토 · C: 선수금 · L/C만(신규 O/A 금지), 조건 변경은 사람이 승인한다.",
        "■ 주의",
        "예측 대상 150곳은 정답이 없다 — 모델 성능은 실습 A의 시험셋(88행) 숫자로만 말한다. 이 시트의 등급 분포는 '일을 매기는 방법'이지 성능이 아니다.",
    ])
    # ---- 기준
    wt = wb.create_sheet("기준")
    wt["A1"] = "임계값 t와 등급 경계"
    wt["A1"].font = Font(name=FONT, bold=True, size=13)
    wt["A3"] = "t (실습 A-2)"
    wt["A3"].font = Font(name=FONT, bold=True)
    wt["B3"] = filled["t"] if filled else None
    wt["B3"].fill = _fill(YELLOW)
    wt["B3"].number_format = "0.0000"
    wt["C3"] = "← 노란 칸에 내 t(예: 0.17)를 넣는다"
    wb.defined_names["t"] = DefinedName("t", attr_text="'기준'!$B$3")
    _head(wt, 5, ["등급", "조건", "경계값", "뜻", "결제조건 [교육용 가정]"])
    rows = [("C", "pd_30d ≥ t", '=IF(t="","",t)', "30일 내 연체 예상", "선수금 · L/C만(신규 O/A 금지)"),
            ("B", "t/2 ≤ pd_30d < t", '=IF(t="","",t/2)', "관찰", "결제기간 단축 · 부보 검토"),
            ("A", "t/4 ≤ pd_30d < t/2", '=IF(t="","",t/4)', "낮음", "O/A 유지"),
            ("S", "pd_30d < t/4", "", "매우 낮음", "O/A 유지")]
    for i, r in enumerate(rows, start=6):
        for j, v in enumerate(r, start=1):
            c = wt.cell(row=i, column=j, value=v)
            if j == 3:
                c.number_format = "0.0000"
    _head(wt, 11, ["등급", "바이어 수", "비율"])
    for i, g in enumerate("SABC", start=12):
        wt.cell(row=i, column=1, value=g)
        wt.cell(row=i, column=2, value=f'=COUNTIF(pred!$D$2:$D${PRED_ROWS + 1},"{g}")')
        c = wt.cell(row=i, column=3, value=f'=IF($B$16=0,"",B{i}/$B$16)')
        c.number_format = "0.0%"
    wt["A16"] = "합계"
    wt["B16"] = "=SUM(B12:B15)"
    for col, wdt in zip("ABCDE", (16, 20, 12, 18, 34)):
        wt.column_dimensions[col].width = wdt
    # ---- pred : A buyer_id · B ref_date · C pd_30d 는 d3_scores.csv 그대로(붙여넣기), D grade 는 수강생이 IFS를 쓴다
    wp = wb.create_sheet("pred", 1)
    head = ["buyer_id", "ref_date", "pd_30d", "grade"]
    _head(wp, 1, head)
    for k in range(PRED_ROWS):
        r = k + 2
        if filled:
            wp.cell(row=r, column=1, value=filled["pred"][k][0])
            wp.cell(row=r, column=2, value=f"{REF_DATE[0]}-{REF_DATE[1]:02d}-{REF_DATE[2]:02d}")
            wp.cell(row=r, column=3, value=filled["pred"][k][1])
            wp.cell(row=r, column=4, value=(f'=IF(OR(C{r}="",t=""),"",_xlfn.IFS(C{r}>=t,"C",C{r}>=t/2,"B",'
                                            f'C{r}>=t/4,"A",TRUE,"S"))'))
        else:
            for col in (1, 2, 3):
                wp.cell(row=r, column=col).fill = _fill(YELLOW)
        wp.cell(row=r, column=3).number_format = "0.0000"
    tab = Table(displayName="pred", ref=f"A1:D{PRED_ROWS + 1}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    wp.add_table(tab)
    wp.freeze_panes = "A2"
    for col, wdt in zip("ABCD", (12, 12, 10, 8)):
        wp.column_dimensions[col].width = wdt
    if filled:   # 강사판은 보기 좋게 서식까지
        wp.conditional_formatting.add(f"D2:D{PRED_ROWS + 1}", CellIsRule(operator="equal", formula=['"C"'], fill=_fill("F4B6B6")))
        wp.conditional_formatting.add(f"D2:D{PRED_ROWS + 1}", CellIsRule(operator="equal", formula=['"B"'], fill=_fill("F8CBAD")))
    # ---- 단조성 : A buyer_id · B ref_date · C late_30d · D pd_30d 는 d3_test_pred.csv 그대로, E grade 는 미리 들어 있다
    wm = wb.create_sheet("단조성")
    _head(wm, 1, ["buyer_id", "ref_date", "late_30d", "pd_30d", "grade"])
    mono = filled["mono"] if filled else []
    for k in range(MONO_ROWS):
        r = k + 2
        if k < len(mono):
            wm.cell(row=r, column=1, value=mono[k][0])
            wm.cell(row=r, column=2, value=mono[k][1])
            wm.cell(row=r, column=3, value=mono[k][3])
            wm.cell(row=r, column=4, value=mono[k][2])
        wm.cell(row=r, column=5, value=(f'=IF(OR(D{r}="",t=""),"",_xlfn.IFS(D{r}>=t,"C",D{r}>=t/2,"B",'
                                        f'D{r}>=t/4,"A",TRUE,"S"))'))
    _head(wm, 1, ["등급", "행 수", "연체 수", "실제 연체율"], col0=7)
    last = MONO_ROWS + 1
    for i, g in enumerate("SABC", start=2):
        wm.cell(row=i, column=7, value=g)
        wm.cell(row=i, column=8, value=f'=COUNTIF($E$2:$E${last},"{g}")')
        wm.cell(row=i, column=9, value=f'=COUNTIFS($E$2:$E${last},"{g}",$C$2:$C${last},1)')
        c = wm.cell(row=i, column=10, value=f'=IF(H{i}=0,"",I{i}/H{i})')
        c.number_format = "0.0%"
    wm["G7"] = "단조성"
    wm["G7"].font = Font(name=FONT, bold=True)
    wm["H7"] = ('=IF(OR(H2=0,H5=0),"",IF(AND(J2<=J5,OR(H4=0,AND(J2<=J4,J4<=J5))),'
                '"S ≤ B ≤ C — 순서대로 오른다","순서가 뒤집혔다 — t와 수식 순서를 다시 본다"))')
    wm["G9"] = "붙여넣기: d3_test_pred.csv의 4열(buyer_id · ref_date · late_30d · pd_30d)을 A2부터. 건수가 적은 A · B는 흔들릴 수 있다 — S와 C를 먼저 본다."
    wm["G9"].alignment = Alignment(wrap_text=False)
    for col, wdt in zip("ABCDEFGHIJ", (12, 12, 9, 10, 8, 3, 8, 9, 9, 12)):
        wm.column_dimensions[col].width = wdt
    wm.freeze_panes = "A2"
    _wb_style(wb)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def banding_filled_inputs() -> dict:
    cut = json.loads((REPO / "models" / "grade_cutoffs.json").read_text(encoding="utf-8"))
    sc = pd.read_csv(CK / "d3_end_scored.csv", encoding="utf-8-sig")
    oot = pd.read_csv(ANS3 / "d3_oot_predictions.csv", encoding="utf-8-sig")
    assert len(sc) == PRED_ROWS and len(oot) <= MONO_ROWS
    return {"t": float(cut["threshold"]), "model_version": str(cut["model_version"]),
            "pred": [(b, float(p)) for b, p in zip(sc["buyer_id"], sc["pd_30d"])],
            "mono": [(b, str(d), float(p), int(y)) for b, d, p, y in zip(oot["buyer_id"], oot["ref_date"], oot["pd_30d"], oot["late_30d"])]}


# ---------------------------------------------------------------- 4) SHAP 해석서 양식
SHAP_TITLE = "근거 메모 — 바이어 1곳의 등급 이유(3일차 실습 B-2)"
SHAP_INFO = [("바이어", "buyer_id:"), ("pd_30d / 등급 / 임계값 t", "pd_30d:        등급:        t:"),
             ("모델", "예: day3_my_v1(내 LightGBM)"), ("전역 상위 특성", "평균 SHAP 절댓값 상위 8개의 한글 이름"),
             ("작성 · 사람 확인", "작성:            확인:")]
SHAP_SECTIONS = [
    ("① 결론 1문장", "현행 유지 / 조건 강화 / 신규 O/A 중단 검토 중 하나만. AI 초안을 내 말로 고친다.", None),
    ("② 위험을 올린 요인 3", "+ 기여만, 절댓값이 큰 순서. 숫자는 기여 표 그대로(한글명 – 값 – 기여 – 업무 해석).", ("한글명", "이 바이어의 값", "기여(+)", "업무 해석(1줄)", 3)),
    ("③ 위험을 낮춘 요인 2", "− 기여만, 절댓값이 큰 순서.", ("한글명", "이 바이어의 값", "기여(−)", "업무 해석(1줄)", 2)),
    ("④ 사람이 확인할 것 3", "데이터 원천 · 최신성 · 조작 가능성 — 예: 재무제표 감사인 실존 여부, 최근 결제 이력의 원장 대조. AI 초안을 사람이 고친다.", 3),
    ("⑤ 한계 3줄", "(a) SHAP은 모델이 어떻게 판단했는지이지 원인이 아니다 (b) 합성 데이터 150곳이다 (c) 신규 바이어 · 조작된 재무제표에는 모델이 늦게 반응한다.", 3),
]
SHAP_CAPTURES = [("그림 1 — 전역 설명", "평균 |SHAP| 상위 10 막대(전역 그림 PNG)"),
                 ("그림 2 — 개별 설명", "이 바이어의 워터폴(기준값 → 특성별 기여 → 최종 확률 PNG)")]
SHAP_FOOT = "사람 승인 전 초안 — 등급과 권고는 여신위원회가 확정한다."
SHAP_FOOT_KEY = "사람 승인 전 초안"
SHAP_LEAD = ("파일 이름 d3_shap_memo.md(이 양식을 쓰면 .docx) · A4 1장. 메모 프롬프트(B4)가 준 5칸을 칸별로 옮기고 ① · ④ · ⑤는 내 말로 고친다. "
             "오늘 파일은 합성 데이터라 AI에 올려도 되지만, 회사 실데이터는 어떤 AI 도구에도 넣지 않는다.")


def build_shap_md() -> Path:
    out = [f"# {SHAP_TITLE}", "", f"> {SHAP_LEAD}", "", "| 항목 | 값 |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in SHAP_INFO]
    for title, guide, spec in SHAP_SECTIONS:
        out += ["", f"## {title}", "", f"*{guide}*", ""]
        if spec is None:
            out += ["(1문장)"]
        elif isinstance(spec, tuple):
            *cols, n = spec
            out += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
            out += ["| " + " | ".join([" "] * len(cols)) + " |" for _ in range(n)]
        else:
            out += [f"{i}. " for i in range(1, spec + 1)]
    for title, guide in SHAP_CAPTURES:
        out += ["", f"## {title}", "", f"*{guide}* — 그림을 붙인다(워드는 Ctrl+V)."]
    out += ["", "---", "", SHAP_FOOT, ""]
    SHAP_MD.write_text("\n".join(out), encoding="utf-8")
    return SHAP_MD


def build_shap_docx() -> Path:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(1.8))
    sec.top_margin = sec.bottom_margin = Cm(1.5)
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for name in ("Heading 1", "Heading 2"):
        s = doc.styles[name]
        s.font.name = FONT
        s.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        s.font.color.rgb = RGBColor(0x1F, 0x3A, 0x68)
    doc.styles["Heading 1"].font.size = Pt(15)
    doc.styles["Heading 2"].font.size = Pt(12)

    def gray(p, text):
        r = p.add_run(text)
        r.italic = True
        r.font.color.rgb = RGBColor(0x76, 0x76, 0x76)
        r.font.size = Pt(9)
        return r

    doc.add_heading(SHAP_TITLE, level=1)
    gray(doc.add_paragraph(), SHAP_LEAD)
    t = doc.add_table(rows=len(SHAP_INFO), cols=2)
    t.style = "Table Grid"
    for i, (k, v) in enumerate(SHAP_INFO):
        t.cell(i, 0).text = k
        t.cell(i, 0).paragraphs[0].runs[0].bold = True
        t.cell(i, 0).width = Cm(4.2)
        gray(t.cell(i, 1).paragraphs[0], v)
    for title, guide, spec in SHAP_SECTIONS:
        doc.add_heading(title, level=2)
        gray(doc.add_paragraph(), guide)
        if spec is None:
            doc.add_paragraph("")
        elif isinstance(spec, tuple):
            *cols, n = spec
            tb = doc.add_table(rows=n + 1, cols=len(cols))
            tb.style = "Table Grid"
            tb.alignment = WD_TABLE_ALIGNMENT.CENTER
            for j, c in enumerate(cols):
                tb.cell(0, j).text = c
                tb.cell(0, j).paragraphs[0].runs[0].bold = True
        else:
            for i in range(1, spec + 1):
                doc.add_paragraph(f"{i}. ")
    for title, guide in SHAP_CAPTURES:
        doc.add_heading(title, level=2)
        box = doc.add_table(rows=1, cols=1)
        box.style = "Table Grid"
        cell = box.cell(0, 0)
        gray(cell.paragraphs[0], f"{guide} — 그림을 여기에 붙인다(Ctrl+V)")
        tr = box.rows[0]._tr
        trpr = tr.get_or_add_trPr()
        from docx.oxml import OxmlElement

        h = OxmlElement("w:trHeight")
        h.set(qn("w:val"), str(int(Cm(4.6).twips if hasattr(Cm(4.6), "twips") else 2608)))
        h.set(qn("w:hRule"), "atLeast")
        trpr.append(h)
    p = doc.add_paragraph()
    r = p.add_run(SHAP_FOOT)
    r.bold = True
    doc.core_properties.title = SHAP_TITLE
    doc.core_properties.author = "tradefin-ai-2026"
    doc.core_properties.comments = "3일차 실습 B-2 양식 — 근거 메모 5칸 + 그림 2칸"
    doc.save(SHAP_DOCX)
    return SHAP_DOCX


# ---------------------------------------------------------------- 검사
def _pycel():
    """pycel 1.0b30 + openpyxl 3.1: 이름 정의(DefinedNameDict) 읽기 보정 — build_day4_workbook.py와 같은 방식."""
    from pycel import ExcelCompiler
    from pycel.excelwrapper import ExcelOpxWrapper

    def _dn(self):
        if self.workbook is not None and self._defined_names is None:
            self._defined_names = {}
            for nm, d in self.workbook.defined_names.items():
                dest = [(alias, w) for w, alias in d.destinations if w in self.workbook]
                if dest:
                    self._defined_names[str(nm)] = dest
        return self._defined_names
    ExcelOpxWrapper.defined_names = property(_dn)
    return ExcelCompiler


def check() -> list[str]:
    import re

    probs: list[str] = []
    # 1) 워밍업 — 언어는 글자(한글 유무)로 센다. 원문 대조는 d2_news.csv가 있을 때(강사 PC · Day2 08:30 이후)만
    txt = WARMUP.read_text(encoding="utf-8").splitlines()
    a, b = txt.index("===== 복사 시작 ====="), txt.index("===== 복사 끝 =====")
    head, rows = txt[a + 1].split("\t"), [ln.split("\t") for ln in txt[a + 2:b]]
    langs = ["ko" if re.search("[가-힣]", r[3] + r[4]) else "en" for r in rows]
    if head != ["news_id", "buyer_id", "date", "headline", "body_short"] or any(len(r) != 5 for r in rows):
        probs.append("워밍업 머리글·열 수가 P2-2 입력(5열)과 다르다")
    if len(rows) != 10 or langs.count("ko") != 4 or langs.count("en") != 6:
        probs.append(f"워밍업 10건 · 한 4 · 영 6이 아님: {len(rows)}건 {langs}")
    if (CK / "d2_news.csv").is_file():
        news = pd.read_csv(CK / "d2_news.csv", encoding="utf-8-sig", dtype=str).set_index("news_id")
        for r in rows:
            src = news.loc[r[0]]
            if [src["buyer_id"], src["date"], src["headline"], src["body_short"]] != r[1:]:
                probs.append(f"워밍업 {r[0]}이 d2_news.csv와 다름")
        if max(list(news.index).index(r[0]) for r in rows) >= 50:
            probs.append("워밍업 행이 배치 1(앞 50행) 밖")
    else:
        print("  (건너뜀) 워밍업 원문 대조 — data/checkpoints/d2_news.csv 없음")
    # 2) BYOD — pycel로 가상 예시 변환을 다시 계산
    try:
        ExcelCompiler = _pycel()
    except ImportError:
        print("  (건너뜀) 수식 검산 — pycel 없음(pip install pycel)")
        return probs + _check_shap()

    xc = ExcelCompiler(filename=str(BYOD))
    exp_code = {nm: code for nm, code, _ in BYOD_KEY}
    off = {nm: o for nm, _, o in BYOD_KEY}
    cnt = pd.Series([r[2] for r in BYOD_EXAMPLE]).value_counts()
    regmap = dict(BYOD_REGION)
    for i, (nm, _, cc, _, d, amt, _, _) in enumerate(BYOD_EXAMPLE, start=3):
        got = [xc.evaluate(f"'02_변환예시'!{c}{i}") for c in ("J", "K", "L", "N", "O")]
        want = [exp_code[nm], (regmap.get(cc, "기타 권역") if cnt[cc] < 3 else cc), f"INV-{i - 2:04d}",
                round(amt * BYOD_K, -2), ("1만 달러 미만" if amt < 10000 else "1만~5만" if amt < 50000 else
                                          "5만~20만" if amt < 200000 else "20만 이상")]
        norm = lambda v: round(float(v), 2) if isinstance(v, (int, float)) else str(v)  # noqa: E731
        if [norm(g) for g in got] != [norm(w) for w in want]:
            probs.append(f"BYOD 변환 {i}행 {got} ≠ {want}")
        dd = xc.evaluate(f"'02_변환예시'!M{i}")
        from datetime import date as _d

        want_serial = (_d(*d) - _d(1899, 12, 30)).days + off[nm]
        if int(dd) != want_serial:
            probs.append(f"BYOD 날짜 이동 {i}행 {dd} ≠ {want_serial}")
    verdict = xc.evaluate(f"'01_규칙표'!C{2 + len(BYOD_RULES) + 2 + len(BYOD_FINAL) + 2}")
    if "미통과" not in str(verdict):
        probs.append(f"빈 점검표 판정이 '미통과'가 아님: {verdict}")
    # 3) 등급 매칭 — 빈 양식은 t·입력이 비어 있어야 하고, 강사판은 정답표와 같아야 한다
    from openpyxl import load_workbook

    wb = load_workbook(BANDING)
    if wb["기준"]["B3"].value is not None or any(wb["pred"].cell(row=r, column=c).value for r in range(2, PRED_ROWS + 2) for c in (1, 2, 3, 4)):
        probs.append("수강생용 등급 시트에 t · 확률 · grade 수식이 들어 있다(grade 열은 수강생이 IFS를 쓴다)")
    if wb.sheetnames != ["00_사용법", "pred", "기준", "단조성"]:
        probs.append(f"등급 시트 시트 이름이 v4와 다르다: {wb.sheetnames}")
    if "t" not in wb.defined_names:
        probs.append("이름 t가 없다")
    if BANDING_FILLED.is_file() and (ANS3 / "d3_cutoffs.csv").is_file():
        xf = ExcelCompiler(filename=str(BANDING_FILLED))
        cuts = pd.read_csv(ANS3 / "d3_cutoffs.csv", encoding="utf-8-sig").set_index("grade")
        dist = {g: int(xf.evaluate(f"'기준'!B{12 + i}")) for i, g in enumerate("SABC")}
        want_d = {g: int(cuts.loc[g, "count_2026_09_30"]) for g in "SABC"}
        if dist != want_d:
            probs.append(f"강사판 등급 분포 {dist} ≠ 정답 {want_d}")
        mono = {g: (int(xf.evaluate(f"'단조성'!H{2 + i}")), xf.evaluate(f"'단조성'!J{2 + i}")) for i, g in enumerate("SABC")}
        for g in "SABC":
            n_ok = mono[g][0] == int(cuts.loc[g, "valid_rows_2026"])
            r_ok = abs(float(mono[g][1] or 0) - float(cuts.loc[g, "valid_late_rate_2026"])) < 5e-5
            if not (n_ok and r_ok):
                probs.append(f"강사판 단조성 {g} {mono[g]} ≠ 정답 ({cuts.loc[g, 'valid_rows_2026']}, {cuts.loc[g, 'valid_late_rate_2026']})")
        mono_msg = xf.evaluate("'단조성'!H7")
        if "순서대로" not in str(mono_msg):
            probs.append(f"강사판 단조성 판정 {mono_msg}")
        first = [xf.evaluate(f"'pred'!{c}2") for c in "ABCD"]
        if first[0] in ("", None) or first[3] not in tuple("SABC"):
            probs.append(f"pred 첫 행 {first}")
    else:
        print("  (건너뜀) 강사판 등급 시트 대조 — ../instructor/day3/answers 없음(강사 PC에서만)")
    return probs + _check_shap()


def _check_shap() -> list[str]:
    """근거 메모 양식 — md · docx 칸 이름이 메모 프롬프트 B4(labs/day3/prompts.md)의 출력 5칸과 같은가."""
    probs: list[str] = []
    md = SHAP_MD.read_text(encoding="utf-8")
    from docx import Document

    heads = [p.text for p in Document(str(SHAP_DOCX)).paragraphs if p.style.name.startswith("Heading 2")]
    want_h = [s[0] for s in SHAP_SECTIONS] + [c[0] for c in SHAP_CAPTURES]
    if heads != want_h or any(f"## {h}" not in md for h in want_h):
        probs.append(f"근거 메모 양식 칸 이름 불일치: {heads}")
    b4 = (LAB3 / "prompts.md").read_text(encoding="utf-8")
    for key in ("① 결론 1문장", "② 위험을 올린 요인 3", "③ 위험을 낮춘 요인 2", "④ 사람이 확인할 것 3", "⑤ 한계 3줄", SHAP_FOOT_KEY):
        if key not in b4:
            probs.append(f"메모 프롬프트(B4)에 없는 칸 이름: {key}")
    return probs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="생성하지 않고 검사만")
    a = ap.parse_args()
    if not a.check:
        print("썼음:", build_warmup().relative_to(REPO))
        print("썼음:", build_byod().relative_to(REPO))
        print("썼음:", build_banding(BANDING).relative_to(REPO))
        if ANS3.is_dir() and (ANS3 / "d3_oot_predictions.csv").is_file():
            print("썼음:", build_banding(BANDING_FILLED, banding_filled_inputs()))
        print("썼음:", build_shap_md().relative_to(REPO))
        print("썼음:", build_shap_docx().relative_to(REPO))
    probs = check()
    if probs:
        print("검사 실패:", *probs, sep="\n  - ")
        return 1
    print("검사 통과 — 워밍업(한 4 · 영 6 · 원문 일치) · BYOD 변환 수식 · 등급 시트(강사판 = 정답표) · 근거 메모 양식 5칸 + 그림 2칸")
    return 0


if __name__ == "__main__":
    sys.exit(main())
