"""1일차: 바이어 원본 → 분석용 표(메모리) 정리 규칙 — 원본 파일은 읽기만 하고 저장하지 않는다.

근거: workbench/day1/outputs/d1_quality_report.md(진단) · d1_code_table.csv(결제조건 코드표)
사용: from scripts.d1_clean_rules import build_analysis_table
      df, log = build_analysis_table()

규칙 요약
- 중복: 완전 중복 행 삭제 → 같은 buyer_id가 남으면 처음 나온 행만 남긴다(B094 · B114, 상호 표기만 다름)
- max_dpd_days: '90일' · '381 days'처럼 숫자 + 단위면 숫자만, '-' · '확인중'은 빈칸 + dpd_확인필요 플래그(0으로 채우지 않음)
- 연체: is_overdue = max_dpd_days > 0, dpd가 빈칸이면 빈칸(비율 분모에서 뺀다)
- 국가: country_code로 묶고, 표시 이름은 그 코드에서 가장 많이 쓴 표기
- 결제방식: payment_terms_raw 원래 표기를 d1_code_table.csv에서 그대로 조회 → pay_method
- 금액: 쉼표 · 'USD ' · 'k' · '만/천' 표기를 숫자로, 'k' · '약'은 금액_근사치 플래그
- 통화: usd · US$ → USD, € → EUR, ¥ → JPY(¥는 위안일 수도 있어 통화_확인필요 플래그)
- since_date: 4형식 해석, 슬래시형은 DD/MM 가정(일 · 월 둘 다 12 이하면 날짜_모호 플래그)
"""

import re

import pandas as pd

RAW_PATH = "data/day1/d1_buyers_raw.xlsx"
CODE_TABLE_PATH = "workbench/day1/outputs/d1_code_table.csv"

CURRENCY_MAP = {"USD": "USD", "usd": "USD", "US$": "USD", "EUR": "EUR", "€": "EUR",
                "JPY": "JPY", "¥": "JPY", "CNY": "CNY"}
DATE_FORMATS = ("%Y-%m-%d", "%Y.%m.%d", "%d/%m/%Y", "%b %d %Y")


def parse_amount(v):
    """금액 셀 → (숫자, 근사치 여부). 해석할 수 없으면 (None, False)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None, False
    if isinstance(v, (int, float)):
        return float(v), False
    s = str(v).strip()
    approx = s.startswith("약")
    s = re.sub(r"^(약|USD|US\$)\s*", "", s).replace(",", "").strip()
    if m := re.fullmatch(r"([\d.]+)k", s, re.I):
        return float(m.group(1)) * 1_000, True
    if m := re.fullmatch(r"(?:(\d+)만)?\s*(?:(\d+)천)?", s):
        if m.group(1) or m.group(2):
            return float(m.group(1) or 0) * 10_000 + float(m.group(2) or 0) * 1_000, True
    if re.fullmatch(r"[\d.]+", s):
        return float(s), approx
    return None, False


def parse_dpd(v):
    """연체일수 셀 → 숫자 또는 None('-' · '확인중' 등)."""
    if isinstance(v, (int, float)) and not pd.isna(v):
        return float(v)
    m = re.fullmatch(r"\s*(\d+)\s*(일|days?)?\s*", str(v))
    return float(m.group(1)) if m else None


def parse_date(v):
    for f in DATE_FORMATS:
        try:
            return pd.to_datetime(str(v), format=f)
        except ValueError:
            pass
    return pd.NaT


def build_analysis_table(raw_path=RAW_PATH, code_table_path=CODE_TABLE_PATH):
    """분석용 표와 정리 기록(dict)을 돌려준다. 파일은 쓰지 않는다."""
    raw = pd.read_excel(raw_path, sheet_name="buyers", dtype=object)
    log = {"원본 행": len(raw)}

    df = raw.drop_duplicates()
    log["완전 중복 삭제"] = len(raw) - len(df)
    n = len(df)
    df = df.drop_duplicates(subset="buyer_id", keep="first").copy()
    log["buyer_id 중복(첫 행 유지) 삭제"] = n - len(df)
    log["분석 행"] = len(df)

    # 연체
    df["max_dpd_days_raw"] = df["max_dpd_days"]
    df["max_dpd_days"] = df["max_dpd_days_raw"].map(parse_dpd).astype(float)
    df["dpd_확인필요"] = df["max_dpd_days"].isna()
    df["is_overdue"] = (df["max_dpd_days"] > 0).astype("boolean").mask(df["dpd_확인필요"])
    log["dpd 확인필요(빈칸 처리)"] = int(df["dpd_확인필요"].sum())

    # 국가: 코드별 최빈 표기를 표시 이름으로
    names = df.groupby("country_code")["country"].agg(lambda s: s.value_counts().index[0])
    df["country_raw"] = df["country"]
    df["country"] = df["country_code"].map(names)

    # 결제방식
    codes = pd.read_csv(code_table_path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    lookup = dict(zip(codes["원래 표기"], codes["표준 코드"]))
    df["pay_method"] = df["payment_terms_raw"].map(lookup)
    log["결제방식 코드표에 없음"] = int(df["pay_method"].isna().sum())
    log["결제방식 검토 필요"] = int((df["pay_method"] == "검토 필요").sum())

    # 금액 · 통화
    for col in ["ar_balance", "overdue_amount"]:
        parsed = df[col].map(parse_amount)
        df[col + "_raw"] = df[col]
        df[col] = parsed.map(lambda t: t[0]).astype(float)
        df[col + "_근사치"] = parsed.map(lambda t: t[1])
    df["ar_currency_raw"] = df["ar_currency"]
    df["ar_currency"] = df["ar_currency_raw"].map(CURRENCY_MAP)
    df["통화_확인필요"] = df["ar_currency_raw"].eq("¥")

    # 날짜
    df["since_date_raw"] = df["since_date"]
    df["since_date"] = df["since_date_raw"].map(parse_date)
    sl = df["since_date_raw"].str.extract(r"^(\d{2})/(\d{2})/\d{4}$").astype(float)
    df["날짜_모호"] = (sl[0] <= 12) & (sl[1] <= 12)

    # 그 밖의 표기
    df["oecd_crc_해당없음"] = df["oecd_crc"].eq("-")
    df["oecd_crc"] = pd.to_numeric(df["oecd_crc"].mask(df["oecd_crc_해당없음"]))
    df["pay_score"] = pd.to_numeric(df["pay_score"])
    df["industry"] = df["industry"].fillna("unknown")

    return df.reset_index(drop=True), log


def to_markdown_table(frame):
    """tabulate 없이 DataFrame → Markdown 표."""
    cols = list(frame.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, r in frame.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)
