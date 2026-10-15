"""2일차: buyers 시트 정제 — workbench/day2/rules/정제규칙.md 1–7칸을 그대로 옮긴 스크립트.

실행: uv run python scripts/clean_buyers.py
입력(읽기만): data/checkpoints/d2_start.xlsx (buyers · fx_at_ref) · data/checkpoints/fx_krw_daily.csv
출력: workbench/day2/outputs/d2_buyers_clean.csv (150행 × 25열)
      workbench/day2/outputs/dq_report.md (전·후 비교)
"""

import io
import re
from pathlib import Path

import pandas as pd

SRC = Path("data/checkpoints/d2_start.xlsx")
FX_DAILY = Path("data/checkpoints/fx_krw_daily.csv")
OUT = Path("workbench/day2/outputs")
AS_OF = pd.Timestamp("2026-08-31")

AMT_COLS = ["ar_balance", "ar_current", "ar_1_30", "ar_31_60", "ar_61_90", "ar_91p"]
BUCKETS = AMT_COLS[1:]
FIN5 = ["current_assets", "current_liabilities", "total_liabilities", "equity", "revenue"]
RATIOS = ["current_ratio", "debt_to_equity", "dso_buyer", "op_margin"]

# 1칸 통화: 앞뒤 공백 제거 + 대소문자 무시 후 매핑
CCY_MAP = {"usd": "USD", "us$": "USD", "eur": "EUR", "euro": "EUR",
           "jpy": "JPY", "yen": "JPY", "cny": "CNY", "rmb": "CNY"}
# fx 표의 통화 코드(JPY는 100엔 단위)와 일별 파일의 열 이름
FX_CODE = {"USD": "USD", "EUR": "EUR", "CNY": "CNY", "JPY": "JPY100"}
FX_UNIT = {"USD": 1, "EUR": 1, "CNY": 1, "JPY": 100}
DAILY_COL = {"USD": "usd_krw", "EUR": "eur_krw", "CNY": "cny_krw", "JPY": "jpy100_krw"}

# 원본은 바이트로 한 번만 읽는다(파일을 열어 두거나 쓰지 않는다).
raw_bytes = SRC.read_bytes()
raw = pd.read_excel(io.BytesIO(raw_bytes), sheet_name="buyers", dtype=object)
fx_ref = pd.read_excel(io.BytesIO(raw_bytes), sheet_name="fx_at_ref")
daily = pd.read_csv(FX_DAILY, encoding="utf-8-sig", parse_dates=["date"]).sort_values("date")
assert len(raw) == 150 and raw.buyer_id.is_unique

df = raw.copy()


# 1칸 통화
def map_ccy(v):
    key = str(v).strip().lower()
    if key not in CCY_MAP:
        raise ValueError(f"매핑에 없는 통화 표기: {v!r}")
    return CCY_MAP[key]


df["ccy_clean"] = df.currency.map(map_ccy)


# 2칸 숫자 변환: 공백 · 콤마 · 통화 글자 제거, 끝 k는 ×1,000
def to_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return float("nan")
    if not isinstance(v, str):
        return float(v)
    s = v.strip()
    mult = 1000 if s.lower().endswith("k") else 1
    s = re.sub(r"(?i)US\$|USD|EUR|CNY|JPY|k$", "", s).replace(",", "").strip()
    try:
        return float(s) * mult
    except ValueError:
        print(f"[변환 실패] {v!r} → 빈칸")
        return float("nan")


for c in AMT_COLS:
    df[c + "_num"] = df[c].map(to_num)

# 7칸 환율: 기준일 2026-08-31 행만 쓴다(2026-09-30 행은 기준일 뒤라 쓰지 않음)
ref = fx_ref[fx_ref.ref_date == AS_OF].set_index("ccy")
assert len(ref) == 4, "fx_at_ref에 기준일 행이 4개(통화별)가 아니다"
usd_krw = ref.loc["USD", "krw_close"]
to_usd = {c: ref.loc[FX_CODE[c], "krw_close"] / FX_UNIT[c] / usd_krw for c in FX_CODE}
df["fx_to_usd"] = df.ccy_clean.map(to_usd)
df["fx_chg_30d"] = df.ccy_clean.map(lambda c: ref.loc[FX_CODE[c], "chg_30d"])


def rate_on(col, day):
    """일별 환율에서 day 당일(없으면 직전 관측일) 값."""
    s = daily[daily.date <= day]
    return s[col].iloc[-1], s.date.iloc[-1]


d30, d60 = AS_OF - pd.Timedelta(days=30), AS_OF - pd.Timedelta(days=60)
lag30, fx_check = {}, []
for c, col in DAILY_COL.items():
    p0, o0 = rate_on(col, AS_OF)
    p30, o30 = rate_on(col, d30)
    p60, o60 = rate_on(col, d60)
    lag30[c] = p30 / p60 - 1
    fx_check.append((c, o0.date(), o30.date(), o60.date(), p0 / p30 - 1,
                     ref.loc[FX_CODE[c], "chg_30d"], lag30[c]))
df["fx_chg_30d_lag30"] = df.ccy_clean.map(lag30)

# 4칸 단위 의심: USD 환산 잔액 > 한도 × 10 → unit_flag = 1, 잔액 ÷1,000
usd_before = df.ar_balance_num * df.fx_to_usd
df["unit_flag"] = (usd_before > df.credit_limit_usd.astype(float) * 10).astype(int)
df["amt_num"] = df.ar_balance_num.where(df.unit_flag == 0, df.ar_balance_num / 1000)
df["ar_balance_usd"] = (df.amt_num * df.fx_to_usd).round(2)

# 잔액 비중: 분모는 버킷 합(미결 잔액). 0이면 빈칸
bsum = df[[c + "_num" for c in BUCKETS]].sum(axis=1)
den = bsum.where(bsum != 0)
df["pct_current"] = df.ar_current_num / den
df["pct_ar_31p"] = (df.ar_31_60_num + df.ar_61_90_num + df.ar_91p_num) / den
df["pct_91plus"] = df.ar_91p_num / den

# 행동 열: 빈칸은 채우지 않는다(3칸 — 구조적 결측)
inv = df.invoices_12m.astype(float).where(lambda s: s > 0)
df["avg_days_late"] = df.avg_days_late_12m.astype(float)
df["late_ratio"] = df.late_invoices_12m.astype(float) / inv
df["dispute_ratio"] = df.dispute_cnt_12m.astype(float) / inv
df["dpd_trend"] = df.avg_dpd_last3m.astype(float) - df.avg_dpd_prev3m.astype(float)

# 3칸 결측 · 5칸 자본잠식: 플래그 → 비율 계산 → 비율 열만 중위수 대체
fin = df[FIN5 + ["accounts_receivable", "operating_income"]].astype(float)
df["fin_missing"] = fin[FIN5].isna().any(axis=1).astype(int)
df["neg_equity"] = (fin.equity <= 0).astype(int)
df["current_ratio"] = fin.current_assets / fin.current_liabilities
df["debt_to_equity"] = (fin.total_liabilities / fin.equity).where(df.neg_equity == 0)
df["dso_buyer"] = fin.accounts_receivable / fin.revenue * 365
df["op_margin"] = fin.operating_income / fin.revenue
ratio_na_before = df[RATIOS].isna().sum()
medians = df[RATIOS].median()  # 대체 전 150행의 그 열 중위수(빈칸 제외)
for c in RATIOS:
    fill = df[c].isna() & ~((c == "debt_to_equity") & (df.neg_equity == 1))
    df.loc[fill, c] = medians[c]

# 6칸 국가위험
crc = df.oecd_crc.map(lambda v: None if pd.isna(v) or str(v).strip() in ("-", "") else int(v))
df["crc_unclassified"] = crc.isna().astype(int)
df["country_risk"] = crc.fillna(0).astype(int)

COLS = ["buyer_id", "payment_method", "ccy_clean", "amt_num", "ar_balance_usd",
        "pct_current", "pct_ar_31p", "pct_91plus", "max_dpd", "avg_days_late",
        "late_ratio", "dpd_trend", "dispute_ratio", "current_ratio", "debt_to_equity",
        "dso_buyer", "op_margin", "fin_missing", "neg_equity", "country_risk",
        "crc_unclassified", "unit_flag", "fx_chg_30d", "fx_chg_30d_lag30", "late_30d"]
out = df[COLS]
assert out.shape == (150, 25) and out.columns[0] == "buyer_id" and out.columns[-1] == "late_30d"
OUT.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT / "d2_buyers_clean.csv", index=False, encoding="utf-8")

# ---------- 전·후 비교 보고서 ----------
is_text = lambda s: s.map(lambda v: isinstance(v, str)).sum()  # noqa: E731
row = lambda b: f"{int(df.index[df.buyer_id == b][0]) + 2}행 {b}"  # noqa: E731
L = ["# buyers 정제 전·후 비교 — 2일차", "",
     f"- 입력(읽기만): `{SRC.as_posix()}` buyers · fx_at_ref, `{FX_DAILY.as_posix()}`",
     "- 규칙: `workbench/day2/rules/정제규칙.md` 1–7칸 · 코드: `scripts/clean_buyers.py`",
     f"- 결과: `workbench/day2/outputs/d2_buyers_clean.csv` ({out.shape[0]}행 × {out.shape[1]}열)",
     "- 이 문서의 숫자는 모두 위 스크립트가 출력한 값이다.", "",
     "## 전·후 건수", "", "| 항목 | 정제 전 | 정제 후 | 칸 |", "|---|---|---|---|",
     f"| 통화 표기 종류 | {raw.currency.nunique()}종 | {df.ccy_clean.nunique()}종 | 1 |"]
for c in AMT_COLS:
    L.append(f"| `{c}` 글자 셀 | {is_text(raw[c])} | {int(df[c + '_num'].isna().sum())}(변환 실패) | 2 |")
for c in RATIOS:
    L.append(f"| `{c}` 빈칸 | {ratio_na_before[c]} | {int(df[c].isna().sum())} | 3 |")
L += [f"| `fin_missing` = 1 | – | {df.fin_missing.sum()} | 3 |",
      f"| 행동 열 빈칸(avg_days_late · dpd_trend · late_ratio) | – | {int(df.avg_days_late.isna().sum())} · {int(df.dpd_trend.isna().sum())} · {int(df.late_ratio.isna().sum())}(채우지 않음) | 3 |",
      f"| 단위 의심(USD 잔액 > 한도 × 10) | {int(df.unit_flag.sum())} | 0(÷1,000 후 {int((df.ar_balance_usd > df.credit_limit_usd.astype(float) * 10).sum())}) | 4 |",
      f"| 자기자본 ≤ 0 | {int(df.neg_equity.sum())} | D/E 빈칸 {int(df.debt_to_equity.isna().sum())} | 5 |",
      f"| oecd_crc `\"-\"` | {int((raw.oecd_crc.astype(str).str.strip() == '-').sum())} | `crc_unclassified` = 1: {df.crc_unclassified.sum()} | 6 |",
      "", "## 통화별 바이어 수(정제 후)", "", "| 통화 | 바이어 수 | 원천 표기 |", "|---|---|---|"]
for c, g in df.groupby("ccy_clean"):
    L.append(f"| {c} | {len(g)} | {' · '.join(f'{k} {v}' for k, v in g.currency.value_counts().items())} |")
L += ["", "## 값이 바뀐 행", "", "| 행 | 열 | 원천 | 정제 후 |", "|---|---|---|---|"]
for c in AMT_COLS:
    for i in df.index[raw[c].map(lambda v: isinstance(v, (str, float)) and not pd.isna(v))]:
        L.append(f"| {i + 2}행 {df.buyer_id[i]} | `{c}` | `{raw[c][i]!r}` | {df[c + '_num'][i]:,.2f} |")
for i in df.index[df.unit_flag == 1]:
    L.append(f"| {i + 2}행 {df.buyer_id[i]} | `amt_num` (unit_flag) | {df.ar_balance_num[i]:,.0f} {df.currency[i]} "
             f"= USD {usd_before[i]:,.2f}, 한도 {df.credit_limit_usd[i]:,} | {df.amt_num[i]:,.2f} → USD {df.ar_balance_usd[i]:,.2f} |")
L += ["", "## 중위수 대체값(대체 전 150행, 빈칸 제외)", "", "| 열 | 중위수 | 채운 칸 |", "|---|---|---|"]
for c in RATIOS:
    L.append(f"| `{c}` | {medians[c]:.4f} | {ratio_na_before[c] - int(df[c].isna().sum())} |")
L += ["", f"`neg_equity` = 1: {', '.join(row(b) for b in df.buyer_id[df.neg_equity == 1])} — debt_to_equity는 빈칸으로 둠.",
      "", "## 환율(기준일 2026-08-31)", "",
      "| 통화 | 기준 관측일 | 30일 전 관측일 | 60일 전 관측일 | 일별로 다시 낸 30일 변화 | fx_at_ref chg_30d | fx_chg_30d_lag30 |",
      "|---|---|---|---|---|---|---|"]
for c, o0, o30, o60, chk, chg, lg in fx_check:
    L.append(f"| {c} | {o0} | {o30} | {o60} | {chk:.4f} | {chg:.4f} | {lg:.4f} |")
L += ["", "USD 환산율(1 단위 통화 → USD): " + " · ".join(f"{c} {v:.6f}" for c, v in to_usd.items()),
      "", "## 잔액 ≠ 버킷 합(보조 점검)", "", "| 행 | amt_num | 버킷 합 | 차이 |", "|---|---|---|---|"]
for i in df.index[(df.amt_num - bsum).abs() > 0.5]:
    L.append(f"| {i + 2}행 {df.buyer_id[i]} | {df.amt_num[i]:,.2f} | {bsum[i]:,.2f} | {df.amt_num[i] - bsum[i]:,.2f} |")
L += ["", "## 열 정의(규칙 문서에 없는 열 — 스크립트가 정한 것)", "",
      "- `amt_num` = 잔액 숫자 변환값(청구 통화). unit_flag 행은 ÷1,000 한 값.",
      "- `pct_*` 분모 = 버킷 5개 합(미결 잔액). 0이면 빈칸. `pct_ar_31p` = (31–60 + 61–90 + 91+) ÷ 합.",
      "- `avg_days_late` = `avg_days_late_12m` 그대로(빈칸 유지).",
      "- `late_ratio` = late_invoices_12m ÷ invoices_12m, `dispute_ratio` = dispute_cnt_12m ÷ invoices_12m. 인보이스 0건이면 빈칸.",
      "- `dpd_trend` = avg_dpd_last3m − avg_dpd_prev3m(+면 악화). 어느 한쪽이 빈칸이면 빈칸."]
(OUT / "dq_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")

print(f"저장: {OUT / 'd2_buyers_clean.csv'} {out.shape}")
print(f"저장: {OUT / 'dq_report.md'}")
print("통화별:", df.ccy_clean.value_counts().to_dict())
print("B001 · B009 · B072 ar_balance_usd:", df.set_index("buyer_id").loc[["B001", "B009", "B072"], "ar_balance_usd"].to_dict())
print("unit_flag:", df.buyer_id[df.unit_flag == 1].tolist(), "neg_equity:", df.buyer_id[df.neg_equity == 1].tolist())
print("fin_missing 합:", df.fin_missing.sum(), "중위수:", medians.round(4).to_dict())
for r in fx_check:
    print("fx", r)
