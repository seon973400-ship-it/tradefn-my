"""1일차: 바이어 원본(d1_buyers_raw.xlsx) 품질 진단 — 읽기 전용, 값을 고치지 않는다.

실행: uv run python scripts/d1_quality_check.py [엑셀 경로]
      (파일 열기가 막히면) cat data/day1/d1_buyers_raw.xlsx | uv run python scripts/d1_quality_check.py -
출력: 진단 수치를 표준출력으로 보인다(보고서 workbench/day1/outputs/d1_quality_report.md의 근거).
"""

import io
import re
import sys
from collections import Counter

import openpyxl
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "data/day1/d1_buyers_raw.xlsx"
BASE_DATE = pd.Timestamp("2026-09-30")  # readme 시트의 기준일

# 원본은 바이트로만 읽는다(수정 없음).
raw = sys.stdin.buffer.read() if SRC == "-" else open(SRC, "rb").read()
df = pd.read_excel(io.BytesIO(raw), sheet_name="buyers", dtype=object)
df.insert(0, "excel_row", df.index + 2)  # 엑셀 행 번호(1행 = 머리글)
ws = openpyxl.load_workbook(io.BytesIO(raw))["buyers"]
cols = [c for c in df.columns if c != "excel_row"]


def section(title):
    print(f"\n## {title}")


# 1) 열별 유형 · 결측
section("열별 셀 유형(openpyxl) · 결측 수 · 고유값 수")
for j, h in enumerate(cols):
    types = Counter(type(r[j].value).__name__ for r in ws.iter_rows(min_row=2))
    blank = df[h].isna().sum() + df[h].map(lambda v: isinstance(v, str) and v.strip() == "").sum()
    print(f"{h}: types={dict(types)} 결측={blank} 고유={df[h].nunique()}")

# 앞뒤 공백 · 대소문자 흔들림
section("앞뒤 공백이 있는 값")
for h in cols:
    s = df[h][df[h].map(lambda v: isinstance(v, str) and v != v.strip())]
    if len(s):
        print(h, len(s), [repr(v) for v in s.head(5)])

# 2) 중복
section("중복")
print("완전 중복 행 수(excel_row 제외):", df.duplicated(subset=cols, keep=False).sum())
for key in ["buyer_id", "buyer_name"]:
    d = df[df.duplicated(subset=[key], keep=False)].sort_values(key)
    print(f"[{key} 중복] {d[key].nunique()}개 값, {len(d)}행")
    for k, g in d.groupby(key):
        diff = [c for c in cols if g[c].astype(str).nunique() > 1]
        print(f"  {k}: 행 {g.excel_row.tolist()} 다른 열={diff}")
        for c in diff:
            print(f"     {c}: {g[c].tolist()}")
print("buyer_id 고유 수:", df.buyer_id.nunique(), "/ 행 수:", len(df))

# 3) 숫자처럼 보이는 글자(숫자 열인데 str로 저장된 셀)
section("숫자 열의 글자 셀")
num_cols = ["ar_balance", "max_dpd_days", "overdue_amount", "pay_score", "oecd_crc",
            "revenue_usd_fy2025", "current_ratio_fy2025", "debt_to_equity_fy2025",
            "dso_fy2025", "op_margin_fy2025"]
for h in num_cols:
    s = df[df[h].map(lambda v: isinstance(v, str))]
    if len(s):
        print(h, Counter(s[h]).most_common())
        for _, r in s.iterrows():
            print(f"   행{r.excel_row} {r.buyer_id} {r[h]!r} 통화={r.ar_currency}")

# 4) 날짜 형식
section("since_date 형식")
pats = {
    "YYYY-MM-DD": r"^\d{4}-\d{2}-\d{2}$",
    "YYYY.M.D": r"^\d{4}\.\d{1,2}\.\d{1,2}$",
    "DD/MM/YYYY 또는 MM/DD/YYYY": r"^\d{2}/\d{2}/\d{4}$",
    "Mon D YYYY": r"^[A-Z][a-z]{2} \d{1,2} \d{4}$",
}
fmt = df.since_date.map(lambda v: next((k for k, p in pats.items() if re.match(p, str(v))), "기타"))
for k, n in fmt.value_counts().items():
    ex = df.since_date[fmt == k].head(3).tolist()
    print(f"{k}: {n} 예={ex}")
sl = df[fmt == "DD/MM/YYYY 또는 MM/DD/YYYY"].since_date.str.split("/", expand=True).astype(int)
print("슬래시형 중 첫 칸>12(일·월 순 확정):", (sl[0] > 12).sum(),
      "둘째 칸>12(월·일 순 확정):", (sl[1] > 12).sum(),
      "둘 다 ≤12(모호):", ((sl[0] <= 12) & (sl[1] <= 12)).sum())
amb = df.loc[sl[(sl[0] <= 12) & (sl[1] <= 12)].index, ["excel_row", "buyer_id", "since_date"]]
print("모호한 예:", amb.head(5).values.tolist())


def parse(v):
    v = str(v)
    for f in ("%Y-%m-%d", "%Y.%m.%d", "%d/%m/%Y", "%b %d %Y"):
        try:
            return pd.to_datetime(v, format=f)
        except ValueError:
            pass
    return pd.NaT


dt = df.since_date.map(parse)
print("해석 실패:", dt.isna().sum(), "범위:", dt.min(), "~", dt.max(),
      "기준일 이후:", (dt > BASE_DATE).sum())

# 5) 코드성 열 값 분포 · 정합성
section("코드성 열 값 분포")
for h in ["country", "country_code", "region", "industry", "segment", "buyer_type",
          "ar_currency", "oecd_crc", "ksure_insured"]:
    print(h, dict(Counter(df[h].map(repr))))

section("country ↔ country_code")
pairs = df.groupby("country_code").country.apply(lambda s: sorted(set(s)))
for code, names in pairs.items():
    if len(names) > 1:
        print(code, names)
print("country_code가 아닌 3글자 대문자 외 값:", df[~df.country_code.str.fullmatch(r"[A-Z]{3}")].country_code.tolist())
print("code → region 다중:", df.groupby("country_code").region.nunique().loc[lambda s: s > 1].to_dict())
print("code → oecd_crc 다중:", df.groupby("country_code").oecd_crc.apply(lambda s: sorted(set(map(str, s)))).loc[lambda s: s.map(len) > 1].to_dict())

section("segment ↔ buyer_type ↔ industry")
print(pd.crosstab(df.segment, df.buyer_type))
print(pd.crosstab(df.industry.fillna("<결측>"), df.segment))
print("industry 결측 행:", df[df.industry.isna()][["excel_row", "buyer_id", "segment", "buyer_type"]].values.tolist())

section("ar_currency ↔ 국가")
print(pd.crosstab(df.country_code, df.ar_currency))


# 6) 금액 · 연체 논리
def to_num(v):
    return v if isinstance(v, (int, float)) and not pd.isna(v) else None


section("금액 · 연체 논리")
ar = df.ar_balance.map(to_num)
od = df.overdue_amount.map(to_num)
dpd = df.max_dpd_days.map(to_num)
m = ar.notna() & od.notna() & (od > ar)
print("overdue > ar_balance:", df[m][["excel_row", "buyer_id", "ar_balance", "overdue_amount", "ar_currency"]].values.tolist())
m = dpd.notna() & od.notna() & (dpd > 0) & (od == 0)
print("dpd>0인데 overdue=0:", df[m][["excel_row", "buyer_id", "max_dpd_days", "overdue_amount"]].values.tolist())
m = dpd.notna() & od.notna() & (dpd == 0) & (od > 0)
print("dpd=0인데 overdue>0:", df[m][["excel_row", "buyer_id", "max_dpd_days", "overdue_amount"]].values.tolist())
m = ar.notna() & (ar == 0) & od.notna() & (od > 0)
print("ar=0인데 overdue>0:", df[m][["excel_row", "buyer_id"]].values.tolist())
print("ar_balance 0 행 수:", (ar == 0).sum())
print("dpd 분포(숫자):", dpd.describe().to_dict())
print("dpd ≥ 91:", df[dpd >= 91][["excel_row", "buyer_id", "max_dpd_days", "overdue_amount"]].values.tolist())
print("ar_balance 통화별 최대:", df.assign(a=ar).groupby("ar_currency").a.max().to_dict())
print("ar_balance 소수점 값:", df[ar.map(lambda v: pd.notna(v) and v != int(v))][["excel_row", "buyer_id", "ar_balance"]].values.tolist())
print("overdue 소수점 값:", df[od.map(lambda v: pd.notna(v) and v != int(v))][["excel_row", "buyer_id", "overdue_amount"]].values.tolist())

section("pay_score")
ps = pd.to_numeric(df.pay_score)
print(ps.describe().to_dict())
print("60 미만:", df[ps < 60][["excel_row", "buyer_id", "pay_score", "max_dpd_days"]].values.tolist())
print("범위(1~100) 밖:", ((ps < 1) | (ps > 100)).sum())

# 7) 재무 열
section("재무 열")
fin = ["revenue_usd_fy2025", "current_ratio_fy2025", "debt_to_equity_fy2025", "dso_fy2025", "op_margin_fy2025"]
for h in fin:
    s = pd.to_numeric(df[h])
    print(h, {k: round(v, 4) for k, v in s.describe().to_dict().items()})
print("debt_to_equity 음수(자본잠식):", df[pd.to_numeric(df.debt_to_equity_fy2025) < 0][["excel_row", "buyer_id", "debt_to_equity_fy2025"]].values.tolist())
print("op_margin |값|>1 (퍼센트로 입력 의심):", (pd.to_numeric(df.op_margin_fy2025).abs() > 1).sum())
all_na = df[fin].isna().all(axis=1)
print("재무 5열 모두 결측:", all_na.sum())
print("  그중 요약문:", Counter(df[all_na].fin_summary_text))
print("revenue 결측인데 다른 재무값 있음:", df[df.revenue_usd_fy2025.isna() & ~all_na][["excel_row", "buyer_id"]].values.tolist())
nd = df.fin_summary_text.str.contains("not disclosed")
print("'not disclosed' 문구:", nd.sum(), "그중 결측 1개 이상:", (df[nd][fin].isna().any(axis=1)).sum())
print("문구 없는데 일부 결측:", df[~nd & ~all_na & df[fin].isna().any(axis=1)][["excel_row", "buyer_id"]].values.tolist())

# 요약문 매출 vs revenue 열 (USD xM 비교)
mm = df.fin_summary_text.str.extract(r"USD ([\d.]+)M")[0].astype(float)
rv = pd.to_numeric(df.revenue_usd_fy2025) / 1e6
bad = df[(mm.notna()) & rv.notna() & ((mm - rv).abs() > 0.1)]
print("요약문 매출 ≠ revenue 열(±0.1M 초과):", bad[["excel_row", "buyer_id", "revenue_usd_fy2025"]].values.tolist(), mm[bad.index].tolist())
