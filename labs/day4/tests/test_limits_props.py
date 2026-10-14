"""한도 엔진 결과의 '속성 테스트' 8개 — 답이 얼마인지가 아니라, 어떤 답이든 지켜야 할 규칙을 검사한다.

실행(저장소 맨 위 폴더)   uv run pytest labs/day4/tests/test_limits_props.py -q
먼저 엔진을 돌려 결과 파일을 만든다   uv run python scripts/limits_lp.py
검사하는 파일   workbench/day4/outputs/limits_proposed.xlsx  (시트 limits · constraints · summary)

정책 숫자는 data/checkpoints/d4_params.csv 에서 읽는다. 선적 보류 · 국가 비율은 결과 파일을 믿지 않고 원본 CSV 에서 다시 계산해 대조한다.
금액 비교의 허용 오차는 1달러다 — 결과를 센트 단위로 반올림하거나 1달러 단위로 내려도 통과하고, 1달러가 넘는 위반만 실패로 본다.
정책 실험 · 버그 카드의 결과를 검사하려면 --params 와 --result 로 경로를 준다(conftest.py 참고).

엔진이 이 테스트를 통과하려면 limits 시트에 buyer_id · grade · country_code · ub · lb · elc · L 열이,
constraints 시트에 name · lhs · rhs · slack · shadow_price 열이, summary 시트에 status · total_cap · solver_gap 열이 있어야 한다
(열의 뜻은 labs/day4/MODEL_SPEC.md 5절).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "checkpoints"
DEFAULT_RESULT = ROOT / "workbench" / "day4" / "outputs" / "limits_proposed.xlsx"
NO_LIMIT = {"LC_SIGHT", "LC_USANCE", "TT_ADV"}   # 신용장 · 선수금 = 한도 대상 아님
TOL = 1.0   # 금액 허용 오차 1달러 — 센트 단위 반올림 · 1달러 내림은 통과, 1달러 넘는 위반은 실패


def pick(option: str | None, default: Path) -> Path:
    """--params · --result 로 받은 경로(저장소 맨 위 폴더 기준)를 쓰고, 없으면 기본 경로."""
    if not option:
        return default
    p = Path(option)
    return p if p.is_absolute() else ROOT / p


def round_half_away(x: float, ndigits: int) -> float:
    """엑셀 ROUND 와 같은 반올림(.5는 0에서 먼 쪽). ndigits=-5 → 10만 단위."""
    q = Decimal(1).scaleb(-ndigits)
    return float((Decimal(str(x)) / q).quantize(Decimal(1), rounding=ROUND_HALF_UP) * q)


@pytest.fixture(scope="module")
def params(request) -> dict[str, float]:
    p = pd.read_csv(pick(request.config.getoption("--params"), DATA / "d4_params.csv"), encoding="utf-8-sig")
    return {str(k): float(v) for k, v in zip(p["excel_name"], p["value"])}


@pytest.fixture(scope="module")
def buyers() -> pd.DataFrame:
    return pd.read_csv(DATA / "d4_start_scored.csv", encoding="utf-8-sig")


@pytest.fixture(scope="module")
def invoices() -> pd.DataFrame:
    return pd.read_csv(DATA / "d4_open_inv.csv", encoding="utf-8-sig")


@pytest.fixture(scope="module")
def result(request) -> dict[str, pd.DataFrame]:
    path = pick(request.config.getoption("--result"), DEFAULT_RESULT)
    if not path.exists():
        pytest.fail(f"결과 파일이 없다 — 먼저 엔진을 돌린다: uv run python scripts/limits_lp.py  (찾은 곳: {path})")
    sheets = pd.read_excel(path, sheet_name=None)
    for need in ("limits", "constraints", "summary"):
        assert need in sheets, f"시트 '{need}' 가 없다(있는 시트: {list(sheets)})"
    return sheets


@pytest.fixture(scope="module")
def limits(result, buyers) -> pd.DataFrame:
    lim = result["limits"].copy()
    assert len(lim) == len(buyers) == 150, f"limits 시트는 바이어 150곳이어야 한다(지금 {len(lim)}행)"
    assert set(lim["buyer_id"]) == set(buyers["buyer_id"]), "limits 시트의 buyer_id 가 d4_start_scored.csv 와 다르다"
    return lim


@pytest.fixture(scope="module")
def summary(result) -> pd.Series:
    return result["summary"].iloc[0]


def country_rate(crc, P: dict[str, float]) -> float:
    """국가위험등급(oecd_crc) → 총허용익스포저 대비 국가 비율(규정 제17조 ②)"""
    if pd.isna(crc) or crc <= 2:
        return P["CtryCap_02"]
    if crc == 3:
        return P["CtryCap_3"]
    if crc <= 5:
        return P["CtryCap_45"]
    return P["CtryCap_67"]


def shipment_hold(buyers: pd.DataFrame, invoices: pd.DataFrame) -> set[str]:
    """선적 보류 = 부도 인지 또는 (미결 · 신용장/선수금 아님 · 연체 30일 이상) 인보이스가 1건 이상"""
    ref = pd.Timestamp(buyers["ref_date"].iloc[0])
    open_ = invoices[(invoices["paid"] == "N") & (~invoices["payment_method"].isin(NO_LIMIT))]
    dpd = (ref - pd.to_datetime(open_["due_date"])).dt.days
    late = set(open_.loc[dpd >= 30, "buyer_id"])
    return set(buyers.loc[buyers["bankruptcy_flag"] == 1, "buyer_id"]) | late


# ① 풀이 상태 ---------------------------------------------------------------------------------
def test_01_status_is_optimal(summary):
    assert str(summary["status"]) == "Optimal", f"풀이 상태가 Optimal 이 아니다: {summary['status']}"


# ② 모든 한도가 [하한, 상한] 안 -------------------------------------------------------------------
def test_02_every_limit_within_bounds(limits):
    below = limits[limits["L"] < limits["lb"] - TOL]
    above = limits[limits["L"] > limits["ub"] + TOL]
    assert below.empty and above.empty, f"하한 미달 {list(below['buyer_id'])[:5]} · 상한 초과 {list(above['buyer_id'])[:5]}"


# ③ 총액: 합계 ≤ 총허용익스포저, 그 값은 (상한 합 × 비율)을 10만 달러 단위로 반올림 ---------------------------
def test_03_total_cap_rounded_and_respected(limits, summary, params):
    expected = round_half_away(params["TotalCapShare"] * limits["ub"].sum(), -5)
    assert abs(float(summary["total_cap"]) - expected) <= 1.0, (
        f"total_cap {summary['total_cap']:,.0f} ≠ ROUND(비율 × 상한 합, -5) = {expected:,.0f}")
    assert limits["L"].sum() <= float(summary["total_cap"]) + 1.0, "한도 합계가 총허용익스포저를 넘었다"


# ④ 미부보 기대손실 예산 ---------------------------------------------------------------------------
def test_04_expected_loss_budget(limits, params):
    use = float((limits["elc"] * limits["L"]).sum())
    budget = params["Equity_USD"] * params["Alpha"]
    assert use <= budget + TOL, f"기대손실 사용 {use:,.0f} > 예산 {budget:,.0f}"


# ⑤ 국가별 합계 ≤ 국가 비율 × 총허용익스포저 ---------------------------------------------------------
def test_05_country_caps(limits, buyers, summary, params):
    crc = buyers.groupby("country_code")["oecd_crc"].agg(lambda s: s.iloc[0])
    total_cap = float(summary["total_cap"])
    over = []
    for ctry, grp in limits.groupby("country_code"):
        cap = country_rate(crc[ctry], params) * total_cap
        if grp["L"].sum() > cap + TOL:
            over.append((ctry, round(grp["L"].sum()), round(cap)))
    assert not over, f"국가 한도 초과(국가, 합계, 한도): {over}"


# ⑥ B등급 합계 비중 ---------------------------------------------------------------------------------
def test_06_b_grade_share(limits, summary, params):
    b_sum = float(limits.loc[limits["grade"] == "B", "L"].sum())
    cap = params["ShareCap_B"] * float(summary["total_cap"])
    assert b_sum <= cap + TOL, f"B등급 합계 {b_sum:,.0f} > {cap:,.0f}"


# ⑦ 선적 보류 · 신용장 · 선수금 바이어는 한도 0 ------------------------------------------------------
def test_07_held_lc_and_advance_buyers_get_zero(limits, buyers, invoices):
    blocked = shipment_hold(buyers, invoices) | set(buyers.loc[buyers["payment_method"].isin(NO_LIMIT), "buyer_id"])
    got = limits[limits["buyer_id"].isin(blocked) & (limits["L"] > TOL)]
    assert got.empty, f"한도가 0이어야 하는 바이어에 한도가 있다: {list(got['buyer_id'])[:8]}"


# ⑧ 솔버 두 개의 목적함수 차이(PuLP 대 HiGHS) < 0.01% -------------------------------------------------
def test_08_two_solvers_agree(summary):
    gap = float(summary["solver_gap"])
    assert gap < 1e-4, f"PuLP 와 HiGHS 목적함수 차이 {gap:.2e} ≥ 1e-4(0.01%)"
