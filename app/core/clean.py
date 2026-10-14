"""① 업로드·전처리 — 날짜·통화·금액 표기 통일, 중복·빈칸·단위 의심 점검, USD 환산, 연체일·독촉 단계 파생.

입력은 미결 인보이스 원장(d5_start.csv 형식)이다. 모델·한도 열(grade, pd_30d, limit_usd …)이 없어도 된다 —
② 예측·등급 페이지가 다시 계산한다. 원본은 고치지 않고 정제본과 '정제 리포트'를 따로 돌려준다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

LEDGER_COLS = [
    "invoice_id", "buyer_id", "buyer_name", "contact_email", "country_code", "currency", "amount_ccy", "amount_usd",
    "invoice_date", "due_date", "dpd", "dunning_stage", "payment_method", "ksure_insured", "ksure_notice_deadline",
    "cont_export_risk", "grade", "pd_30d", "limit_usd", "limit_usage_pct", "news_risk_30d", "bankruptcy_flag",
    "fraud_flag", "fraud_type", "term_change_flag", "last_dunning_stage", "last_dunning_date",
    "open_amount_ccy", "open_amount_usd"]
REQUIRED = ["invoice_id", "buyer_id", "currency", "amount_ccy", "invoice_date", "due_date"]
DATE_COLS = ["invoice_date", "due_date", "ksure_notice_deadline", "last_dunning_date"]
AMOUNT_COLS = ["amount_ccy", "amount_usd", "open_amount_ccy", "open_amount_usd"]
LC_METHODS = ("LC_SIGHT", "LC_USANCE")
CCY_ALIAS = {"USD": "USD", "US$": "USD", "$": "USD", "USDOLLAR": "USD", "DOLLAR": "USD", "달러": "USD",
             "EUR": "EUR", "€": "EUR", "EURO": "EUR", "유로": "EUR",
             "JPY": "JPY", "¥": "JPY", "YEN": "JPY", "円": "JPY", "엔": "JPY",
             "CNY": "CNY", "RMB": "CNY", "YUAN": "CNY", "元": "CNY", "위안": "CNY"}
CANON_CCY = ("USD", "EUR", "JPY", "CNY")
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
ISO_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
NUM_RX = re.compile(r"^-?\d+(\.\d+)?$")
UNIT_RATIO = 50.0   # 바이어 과거 중앙값의 50배 초과 또는 1/50 미만이면 '단위 의심' [교육용 가정] — 합성 원장의 정상 금액은 최대 약 30배, 소수점 오류(×100)는 대개 100배 근처

REPORT_ROWS = [  # (code, 유형, 처리 내용) — code는 강사 오염 로그(error_type)와 같은 이름
    ("duplicate", "완전 중복 행", "두 번째 행부터 삭제"),
    ("duplicate_id", "인보이스 번호 중복(내용 다름)", "첫 행만 남기고 확인 목록에 기록"),
    ("ccy_variant", "통화 표기 통일", "usd·US$·€·euro·¥·yen·RMB → USD·EUR·JPY·CNY"),
    ("amount_text", "금액 칸 문자 제거", "콤마·통화 기호·공백·k 단위를 숫자로"),
    ("date_format", "날짜 형식 통일", "일/월/연·연.월.일·영문 월 이름 → YYYY-MM-DD"),
    ("missing", "필수값 빈칸", "확인 필요 표시(통화는 같은 바이어의 다른 행으로 보완)"),
    ("ccy_filled", "통화 빈칸 보완", "같은 바이어 다른 행의 통화로 채움"),
    ("decimal_error", "단위 의심(바이어 과거 중앙값 대비)", "확인 필요 표시 — 자동으로 고치지 않음"),
    ("unparsed", "읽지 못한 값", "확인 필요 표시"),
    ("usd_computed", "USD 금액 계산", "환율표(FRED H.10 교차환율)로 환산"),
]


@dataclass
class CleanResult:
    df: pd.DataFrame
    report: pd.DataFrame
    issues: pd.DataFrame
    counts: dict = field(default_factory=dict)


# ------------------------------------------------------------------------------------------ 값 하나씩
def _blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and np.isnan(v):
        return True
    return str(v).strip().lower() in ("", "nan", "nat", "none", "null")


def parse_date(v) -> pd.Timestamp:
    """여러 표기의 날짜 → Timestamp(못 읽으면 NaT). 슬래시 날짜는 일/월/연으로 읽는다."""
    if _blank(v):
        return pd.NaT
    if isinstance(v, (pd.Timestamp, date)):
        return pd.Timestamp(v).normalize()
    s = str(v).strip()
    if ISO_RX.match(s):
        return pd.Timestamp(s)
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[ T]", s)
    if m:
        return pd.Timestamp(m.group(1))
    m = re.match(r"^(\d{4})\s*[./\-]\s*(\d{1,2})\s*[./\-]\s*(\d{1,2})\.?$", s)
    if m:
        return _ymd(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$", s)
    if m:
        return _ymd(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        return _ymd(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})$", s)
    if m and m.group(1)[:3].lower() in MONTHS:
        return _ymd(int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2)))
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})$", s)
    if m and m.group(2)[:3].lower() in MONTHS:
        return _ymd(int(m.group(3)), MONTHS[m.group(2)[:3].lower()], int(m.group(1)))
    m = re.match(r"^(\d{5})(\.0+)?$", s)
    if m and 30000 < int(m.group(1)) < 60000:  # Excel 날짜 일련번호
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(m.group(1)))
    return pd.NaT


def _ymd(y: int, m: int, d: int) -> pd.Timestamp:
    try:
        return pd.Timestamp(year=y, month=m, day=d)
    except ValueError:
        return pd.NaT


def parse_amount(v) -> float:
    """'USD 12,345' · ' 12345 ' · '12.3k' · '약 1만2천' → 숫자(못 읽으면 NaN)."""
    if _blank(v):
        return np.nan
    if isinstance(v, (int, float, np.integer, np.floating)):
        return float(v)
    s = str(v).strip()
    if NUM_RX.match(s):
        return float(s)
    t = s.upper().replace(",", "").replace(" ", "").replace("약", "").replace("~", "")
    for tok in ("US$", "USD", "EUR", "JPY", "CNY", "RMB", "KRW", "$", "€", "¥", "원"):
        t = t.replace(tok, "")
    if re.search(r"[만천억]", t):
        total, num = 0.0, ""
        for ch in t:
            if ch.isdigit() or ch == ".":
                num += ch
            elif ch in "억만천":
                mult = {"억": 1e8, "만": 1e4, "천": 1e3}[ch]
                total += (float(num) if num else 1.0) * mult
                num = ""
        return total + (float(num) if num else 0.0)
    m = re.match(r"^(-?\d+(?:\.\d+)?)([KMB])?$", t)
    if m:
        mult = {"K": 1e3, "M": 1e6, "B": 1e9}.get(m.group(2) or "", 1.0)
        return float(m.group(1)) * mult
    return np.nan


def normalize_ccy(v) -> str | None:
    if _blank(v):
        return None
    key = str(v).strip().upper().replace(" ", "")
    return CCY_ALIAS.get(key)


def stage_of(dpd) -> float:
    """독촉 단계: 0 = D-3(−3 ≤ dpd < 0) · 1 = D+7(7–14) · 2 = D+15(15–29) · 3 = D+30(≥ 30) · 그 외 빈칸."""
    if dpd is None or (isinstance(dpd, float) and np.isnan(dpd)) or pd.isna(dpd):
        return np.nan
    d = int(dpd)
    if -3 <= d < 0:
        return 0
    if 7 <= d < 15:
        return 1
    if 15 <= d < 30:
        return 2
    if d >= 30:
        return 3
    return np.nan


def add_months(ts: pd.Timestamp, n: int = 1) -> pd.Timestamp:
    return (pd.Timestamp(ts) + pd.DateOffset(months=n)) if not pd.isna(ts) else pd.NaT


# ------------------------------------------------------------------------------------------ 환율
def usd_per_unit(dates, ccys, fx: pd.DataFrame | None) -> np.ndarray:
    """통화 1단위당 USD. 환율표(fx_krw_daily: usd_krw·eur_krw·cny_krw·jpy100_krw)의 그날(없으면 직전 관측일) 값.
    환율표 시작 전 날짜는 첫 관측값을 쓴다. 환율표가 없으면 USD만 1, 나머지 NaN."""
    dates = pd.to_datetime(pd.Series(list(dates)))
    ccys = pd.Series(list(ccys), dtype=object)
    out = np.full(len(dates), np.nan)
    out[(ccys == "USD").to_numpy()] = 1.0
    if fx is None or len(fx) == 0:
        return out
    f = fx.sort_values("date").reset_index(drop=True)
    idx = np.searchsorted(f["date"].to_numpy(), dates.fillna(f["date"].iloc[-1]).to_numpy(), side="right") - 1
    idx = np.clip(idx, 0, len(f) - 1)
    row = f.iloc[idx].reset_index(drop=True)
    krw = {"USD": row["usd_krw"], "EUR": row["eur_krw"], "CNY": row["cny_krw"], "JPY": row["jpy100_krw"] / 100.0}
    for c, s in krw.items():
        m = (ccys == c).to_numpy()
        out[m] = (s / row["usd_krw"]).to_numpy()[m]
    return out


# ------------------------------------------------------------------------------------------ 정제
def _snake(c: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", str(c).strip().lower()).strip("_")


def clean_ledger(raw: pd.DataFrame, asof=None, fx: pd.DataFrame | None = None,
                 hist_median: pd.Series | None = None) -> CleanResult:
    """원장 정제. raw는 문자열로 읽은 표(read_csv_any). 필수 열이 없으면 ValueError."""
    asof = pd.Timestamp(asof or "2026-09-30")
    df = raw.copy()
    df.columns = [_snake(c) for c in df.columns]
    miss_cols = [c for c in REQUIRED if c not in df.columns]
    if miss_cols:
        raise ValueError(f"필수 열이 없습니다: {miss_cols} — 미결 인보이스 원장(d5_start.csv) 형식인지 확인하세요")
    df = df.astype(object).where(pd.notna(df), "")
    df.insert(0, "_row", np.arange(2, len(df) + 2))  # 원본 CSV 줄 번호(머리글 = 1)
    cnt = {code: 0 for code, _, _ in REPORT_ROWS}
    issues: list[dict] = []

    def issue(r, col, problem, raw_v, action):
        issues.append({"csv_row": int(r["_row"]), "invoice_id": str(r.get("invoice_id", "")), "column": col,
                       "problem": problem, "raw_value": str(raw_v), "action": action})

    # 1) 완전 중복 → 같은 번호 중복
    body = df.drop(columns=["_row"]).apply(lambda s: s.astype(str).str.strip())
    dup = body.duplicated(keep="first")
    for _, r in df[dup].iterrows():
        issue(r, "(행 전체)", "완전 중복 행", "", "삭제")
    cnt["duplicate"] = int(dup.sum())
    df = df[~dup].copy()
    did = df["invoice_id"].astype(str).str.strip().duplicated(keep="first")
    for _, r in df[did].iterrows():
        issue(r, "invoice_id", "인보이스 번호 중복(내용 다름)", r["invoice_id"], "첫 행만 남김 — 원본 확인")
    cnt["duplicate_id"] = int(did.sum())
    df = df[~did].copy()
    for c in ("invoice_id", "buyer_id"):
        df[c] = df[c].astype(str).str.strip()

    # 2) 통화
    ccy_out = []
    for _, r in df.iterrows():
        rv = r["currency"]
        code = normalize_ccy(rv)
        if _blank(rv):
            cnt["missing"] += 1
            issue(r, "currency", "필수값 빈칸", rv, "같은 바이어 통화로 보완 시도")
        elif code is None:
            cnt["unparsed"] += 1
            issue(r, "currency", "알 수 없는 통화 표기", rv, "확인 필요")
        elif str(rv) != code:          # 공백만 다른 표기(' USD ')도 고친 것으로 센다
            cnt["ccy_variant"] += 1
        ccy_out.append(code)
    df["currency"] = ccy_out
    if df["currency"].isna().any():
        known = df.dropna(subset=["currency"]).groupby("buyer_id")["currency"].agg(lambda s: s.mode().iloc[0])
        fill = df["buyer_id"].map(known)
        m = df["currency"].isna() & fill.notna()
        cnt["ccy_filled"] = int(m.sum())
        df.loc[m, "currency"] = fill[m]

    # 3) 금액
    for col in [c for c in AMOUNT_COLS if c in df.columns]:
        vals = []
        for _, r in df.iterrows():
            rv = r[col]
            v = parse_amount(rv)
            if _blank(rv):
                if col == "amount_ccy":
                    cnt["missing"] += 1
                    issue(r, col, "필수값 빈칸", rv, "확인 필요")
            elif np.isnan(v):
                cnt["unparsed"] += 1
                issue(r, col, "금액을 읽지 못함", rv, "확인 필요")
            elif not NUM_RX.match(str(rv)):   # 콤마·통화 기호·앞뒤 공백·k 단위
                cnt["amount_text"] += 1
            vals.append(v)
        df[col] = pd.to_numeric(pd.Series(vals, index=df.index), errors="coerce")

    # 4) 날짜
    for col in [c for c in DATE_COLS if c in df.columns]:
        vals = []
        for _, r in df.iterrows():
            rv = r[col]
            v = parse_date(rv)
            if _blank(rv):
                if col in REQUIRED:
                    cnt["missing"] += 1
                    issue(r, col, "필수값 빈칸", rv, "확인 필요 — 독촉·경보에서 제외")
            elif pd.isna(v):
                cnt["unparsed"] += 1
                issue(r, col, "날짜를 읽지 못함", rv, "확인 필요")
            elif not ISO_RX.match(str(rv).strip()):
                cnt["date_format"] += 1
            vals.append(v)
        df[col] = pd.to_datetime(pd.Series(vals, index=df.index), errors="coerce")

    # 5) 빠진 선택 열 기본값
    defaults = {"buyer_name": "", "contact_email": None, "country_code": "", "payment_method": "", "ksure_insured": "N",
                "grade": "", "fraud_type": ""}
    for c, v in defaults.items():
        if c not in df.columns:
            df[c] = v
    df["contact_email"] = [e if not _blank(e) else f"buyer+{b}@example.com" for e, b in zip(df["contact_email"], df["buyer_id"])]
    for c in ("pd_30d", "limit_usd", "limit_usage_pct", "news_risk_30d", "cont_export_risk", "last_dunning_stage"):
        df[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
    for c in ("bankruptcy_flag", "fraud_flag", "term_change_flag"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int) if c in df.columns else 0
    for c in ("payment_method", "ksure_insured", "grade", "fraud_type", "country_code", "buyer_name"):
        df[c] = df[c].astype(str).str.strip().replace({"nan": ""})
    df["ksure_insured"] = df["ksure_insured"].str.upper().replace({"": "N"})
    for c in ("ksure_notice_deadline", "last_dunning_date"):
        if c not in df.columns:
            df[c] = pd.NaT

    # 6) USD 환산(빈칸만 계산)
    upi = usd_per_unit(df["invoice_date"], df["currency"], fx)
    if "amount_usd" not in df.columns:
        df["amount_usd"] = np.nan
    m = df["amount_usd"].isna() & df["amount_ccy"].notna()
    cnt["usd_computed"] = int(m.sum())
    df.loc[m, "amount_usd"] = (df.loc[m, "amount_ccy"] * upi[m.to_numpy()]).round(2)
    if "open_amount_ccy" not in df.columns:
        df["open_amount_ccy"] = df["amount_ccy"]
    df["open_amount_ccy"] = df["open_amount_ccy"].fillna(df["amount_ccy"])
    ua = usd_per_unit([asof] * len(df), df["currency"], fx)
    if "open_amount_usd" not in df.columns:
        df["open_amount_usd"] = np.nan
    m2 = df["open_amount_usd"].isna() & df["open_amount_ccy"].notna()
    df.loc[m2, "open_amount_usd"] = (df.loc[m2, "open_amount_ccy"] * ua[m2.to_numpy()]).round(2)

    # 7) 단위 의심(바이어 과거 중앙값, 없으면 같은 통화 파일 중앙값)
    ref = df["buyer_id"].map(hist_median) if hist_median is not None else pd.Series(np.nan, index=df.index)
    file_med = df.groupby("currency")["amount_usd"].transform("median")
    ref = ref.fillna(file_med)
    ratio = df["amount_usd"] / ref
    sus = (ratio > UNIT_RATIO) | (ratio < 1 / UNIT_RATIO)
    df["unit_suspect"] = sus.fillna(False).astype(int)
    cnt["decimal_error"] = int(df["unit_suspect"].sum())
    for _, r in df[df["unit_suspect"] == 1].iterrows():
        issue(r, "amount_ccy", f"단위 의심(과거 중앙값의 {UNIT_RATIO:.0f}배↑ 또는 1/{UNIT_RATIO:.0f}↓)", r["amount_ccy"], "원본 확인 — 자동 수정 안 함")

    # 8) 파생: 연체일·독촉 단계·사고통지 기한
    df["dpd"] = (asof - df["due_date"]).dt.days.astype("Int64")
    df["dunning_stage"] = [stage_of(v) for v in df["dpd"]]
    df["dunning_stage"] = pd.to_numeric(df["dunning_stage"], errors="coerce").astype("Int64")
    need = df["ksure_notice_deadline"].isna() & (df["ksure_insured"] == "Y") & df["due_date"].notna()
    df.loc[need, "ksure_notice_deadline"] = df.loc[need, "due_date"].map(add_months)
    df["notice_days_left"] = (df["ksure_notice_deadline"] - asof).dt.days.astype("Int64")
    df["is_lc"] = df["payment_method"].isin(LC_METHODS).astype(int)
    df["last_dunning_stage"] = pd.to_numeric(df["last_dunning_stage"], errors="coerce").astype("Int64")
    bad = {i["csv_row"] for i in issues if i["action"] != "삭제" and i["problem"] != "인보이스 번호 중복(내용 다름)"}
    df["needs_review"] = df["_row"].isin(bad).astype(int)
    df.loc[df["due_date"].isna() | df["amount_ccy"].isna() | df["currency"].isna(), "needs_review"] = 1

    order = [c for c in LEDGER_COLS if c in df.columns] + ["unit_suspect", "notice_days_left", "is_lc", "needs_review", "_row"]
    df = df[order].reset_index(drop=True)
    report = pd.DataFrame([{"code": code, "유형": name, "건수": cnt[code], "처리": how} for code, name, how in REPORT_ROWS])
    return CleanResult(df=df, report=report, issues=pd.DataFrame(issues, columns=[
        "csv_row", "invoice_id", "column", "problem", "raw_value", "action"]), counts=cnt)


def to_export(df: pd.DataFrame) -> pd.DataFrame:
    """다운로드용: 날짜는 YYYY-MM-DD 문자열, 보조 열(_row)은 뺀다."""
    out = df.drop(columns=[c for c in ("_row",) if c in df.columns]).copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%d").fillna("")
    return out
