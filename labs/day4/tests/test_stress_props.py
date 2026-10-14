"""스트레스 시뮬레이터 결과의 '속성 테스트' — 답이 얼마인지가 아니라, 어떤 시뮬레이션이든 지켜야 할 성질을 검사한다.

실행(저장소 맨 위 폴더)   uv run pytest labs/day4/tests/test_stress_props.py -q
먼저 시뮬레이터를 돌려 결과 파일을 만든다   uv run python labs/day4/stress_mc.py
검사하는 파일   workbench/day4/outputs/stress_results.csv

열(내가 만든 시뮬레이터도 이 열 이름을 쓰면 같은 테스트로 볼 수 있다)
  scenario_id · rho · n_sims · el_formula_usd(공식 기대손실) · mc_mean_usd · mc_p95_usd · mc_p99_usd · mc_es99_usd

- 순서: 시나리오 S0 < S1 < … < S4 로 갈수록 공식 기대손실이 커진다
- 일치: 시뮬레이션 평균은 공식 기대손실의 ±3% 안이다(반복 1만 회 이상일 때)
- 꼬리: ES99 ≥ P99 ≥ P95 ≥ 평균
- 상관: 같은 시나리오에서 ρ = 0.2의 P99는 ρ = 0의 P99보다 크다(평균은 같고 꼬리만 두꺼워진다)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / "workbench" / "day4" / "outputs" / "stress_results.csv"
ORDER = ["S0", "S1", "S2", "S3", "S4"]


@pytest.fixture(scope="module")
def res(request) -> pd.DataFrame:
    opt = request.config.getoption("--stress")
    path = (Path(opt) if Path(opt).is_absolute() else ROOT / opt) if opt else DEFAULT
    if not path.exists():
        pytest.fail(f"결과 파일이 없다 — 먼저 시뮬레이터를 돌린다: uv run python labs/day4/stress_mc.py  (찾은 곳: {path})")
    df = pd.read_csv(path, encoding="utf-8-sig")
    need = {"scenario_id", "rho", "n_sims", "el_formula_usd", "mc_mean_usd", "mc_p95_usd", "mc_p99_usd", "mc_es99_usd"}
    assert need <= set(df.columns), f"빠진 열: {sorted(need - set(df.columns))}"
    return df


def test_01_expected_loss_rises_with_the_scenario(res):
    el = res[res["scenario_id"].isin(ORDER)].groupby("scenario_id")["el_formula_usd"].first().reindex(ORDER)
    assert el.notna().all(), f"S0–S4가 모두 있어야 한다(있는 것: {list(res['scenario_id'].unique())})"
    assert el.is_monotonic_increasing and el.nunique() == 5, f"공식 기대손실이 S0 < … < S4 순이 아니다: {el.round(0).tolist()}"


def test_02_simulation_mean_matches_the_formula_within_3_percent(res):
    big = res[res["n_sims"] >= 10_000]
    assert not big.empty, "반복 1만 회 이상인 행이 없다"
    off = big[(big["mc_mean_usd"] / big["el_formula_usd"] - 1).abs() > 0.03]
    assert off.empty, f"평균이 공식 기대손실의 ±3%를 벗어난 행: {off[['scenario_id', 'rho', 'mc_mean_usd', 'el_formula_usd']].round(0).to_dict('records')}"


def test_03_tail_ordering(res):
    bad = res[~((res["mc_es99_usd"] >= res["mc_p99_usd"]) & (res["mc_p99_usd"] >= res["mc_p95_usd"]) & (res["mc_p95_usd"] >= res["mc_mean_usd"]))]
    assert bad.empty, f"ES99 ≥ P99 ≥ P95 ≥ 평균이 아닌 행: {bad[['scenario_id', 'rho']].to_dict('records')}"


def test_04_correlation_fattens_the_tail(res):
    pairs = res.pivot_table(index="scenario_id", columns="rho", values="mc_p99_usd")
    assert {0.0, 0.2} <= set(pairs.columns), f"ρ 0과 0.2가 모두 있어야 한다(있는 것: {list(pairs.columns)})"
    weak = pairs[pairs[0.2] <= pairs[0.0]]
    assert weak.empty, f"ρ 0.2의 P99가 ρ 0보다 크지 않은 시나리오: {list(weak.index)}"
