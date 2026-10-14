"""거시 쇼크 손실 시뮬레이터 — 4일차 실습 A 05의 참고 스크립트(시연 2에서 HTML 부분을 뺀 판).

실행(저장소 맨 위 폴더)
    uv run python labs/day4/stress_mc.py
    uv run python labs/day4/stress_mc.py --scenarios workbench/day4/data/d4_scenarios.csv   # 내 시나리오 U1을 더한 사본
    uv run python labs/day4/stress_mc.py --rho 0 0.2 0.4 --out workbench/day4/outputs/rho  # 결과를 다른 폴더에(기본 결과를 덮지 않는다)

읽는 것  data/checkpoints/d4_start_scored.csv (바이어 150곳) · d4_scenarios.csv (시나리오 S0–S4)
         workbench/day4/outputs/limits_proposed.xlsx (있으면 한도 재배정의 절감액도 계산)
쓰는 것  workbench/day4/outputs/stress_results.csv · loss_hist.png · stress_savings.csv (한도안이 있을 때)

계산
  공식 기대손실 EL = Σ 잔액 × min(1, PD × 배수) × LGD × (1 − 보상비율)   (신용사건 바이어는 PD 100%, 신용장은 LGD 0.1)
  몬테카를로 = 난수로 연간 손실을 n번 만들어 평균 · P95 · P99 · ES99(P99를 넘는 손실의 평균)를 잰다
    ρ = 0   바이어끼리 독립 — 바이어마다 난수 하나
    ρ > 0   1-요인 가우스 — 모두가 나눠 받는 충격 z(비중 ρ) + 바이어별 충격 e
  시드를 고정하므로 같은 입력이면 같은 결과가 나온다(난수 방식이 다르면 P99는 ±3% 안팎으로 달라진다).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

# 저장소 맨 위 폴더 = pyproject.toml이 있는 가장 가까운 위 폴더 — scripts/ 로 복사하거나 작업 사본 폴더에서 돌려도 같은 곳을 읽는다
ROOT = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists()), Path(__file__).resolve().parents[2])
DATA = ROOT / "data" / "checkpoints"
OUT = ROOT / "workbench" / "day4" / "outputs"
LC = ["LC_SIGHT", "LC_USANCE"]            # 신용장 — 손실률 LGD_LC(0.1)
NO_LIMIT = LC + ["TT_ADV"]                 # 신용장 · 선수금 = 외상 한도 대상 아님
LGD_LC = 0.1
BASE_LGD = 0.6                             # S0의 손실률 — 절감액의 시나리오 배율 계산에 쓴다


def rel(p: Path) -> str:
    """저장소 맨 위 폴더 기준 경로(밖이면 그대로) — 화면 출력용."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def scenario_vectors(b: pd.DataFrame, s: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """바이어별 (부도확률, 부도 시 손실). 신용사건(bankruptcy_flag = 1)은 PD 100%."""
    pd_eff = np.where(b["bankruptcy_flag"] == 1, 1.0, np.minimum(1.0, b["pd_annual_assumed"] * s["pd_multiplier"]))
    lgd = np.where(b["payment_method"].isin(LC), LGD_LC, s["lgd_scenario"])
    loss_if = b["open_ar_usd"] * lgd * (1 - b["coverage_ratio"])
    return pd_eff, loss_if.to_numpy()


def simulate(p: np.ndarray, loss_if: np.ndarray, n: int, seed: int, rho: float) -> np.ndarray:
    """연간 총손실을 n번 만든다."""
    rng = np.random.default_rng(seed)
    if rho == 0.0:
        u = rng.random((n, len(p)))
        return ((u < p) * loss_if).sum(axis=1)
    z = rng.standard_normal((n, 1))
    e = rng.standard_normal((n, len(p)))
    x = np.sqrt(rho) * z + np.sqrt(1 - rho) * e
    threshold = np.where(p >= 1.0, np.inf, norm.ppf(np.clip(p, 0, 1 - 1e-12)))
    return ((x < threshold) * loss_if).sum(axis=1)


def summarize(loss: np.ndarray) -> dict[str, float]:
    p95, p99 = np.percentile(loss, [95, 99])
    return {"mean": loss.mean(), "p95": p95, "p99": p99, "es99": loss[loss >= p99].mean()}


def savings(b: pd.DataFrame, sc: pd.DataFrame, limits_path: Path) -> pd.DataFrame | None:
    """한도 재배정의 연 기대손실 절감액 = Σ elc × (현행 한도 − 제안 한도), 외상 거래 바이어만.
    elc는 한도안 limits 시트의 열(한도 1달러당 기대손실, S0 기준)이고, 다른 시나리오는 PD 배수 × (손실률 ÷ 0.6)로 키운다."""
    if not limits_path.exists():
        return None
    lim = pd.read_excel(limits_path, sheet_name="limits").set_index("buyer_id")
    credit = ~b.set_index("buyer_id")["payment_method"].isin(NO_LIMIT)
    credit = credit.reindex(lim.index).fillna(False)
    now = float((lim["elc"] * lim["current_limit"])[credit].sum())
    new = float((lim["elc"] * lim["L"])[credit].sum())
    rows = []
    for _, s in sc.iterrows():
        k = s["pd_multiplier"] * s["lgd_scenario"] / BASE_LGD
        rows.append({"scenario_id": s["scenario_id"], "buyers": int(credit.sum()), "el_now_usd": now * k, "el_proposed_usd": new * k,
                     "saving_usd": (now - new) * k})
    return pd.DataFrame(rows)


def draw_hist(path: Path, runs: dict[str, np.ndarray]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    font = ROOT / "tools" / "fonts" / "NanumGothic-Regular.ttf"
    if font.exists():
        font_manager.fontManager.addfont(str(font))
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = {"S0": "#2b6cb0", "S3": "#c05621"}
    for sid, loss in runs.items():
        ax.hist(loss / 1000, bins=60, alpha=0.55, color=colors.get(sid), label=f"{sid} 평균 {loss.mean() / 1000:,.1f}천")
        ax.axvline(np.percentile(loss, 99) / 1000, color=colors.get(sid), linestyle="--", linewidth=1.5)
    ax.set_xlabel("연간 손실(천 달러) — 점선은 P99")
    ax.set_ylabel("횟수")
    ax.set_title("몬테카를로 연간 손실 분포 (바이어끼리 독립)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="거시 쇼크 손실 시뮬레이터(참고 스크립트)")
    ap.add_argument("--scenarios", type=Path, default=DATA / "d4_scenarios.csv", help="시나리오 CSV(row_type이 scenario인 행만 쓴다)")
    ap.add_argument("--n", type=int, default=10_000, help="반복 수")
    ap.add_argument("--seed", type=int, default=42, help="난수 시드")
    ap.add_argument("--rho", type=float, nargs="+", default=[0.0, 0.2], help="공통 요인 비중 ρ(여러 개 가능)")
    ap.add_argument("--out", type=Path, default=OUT, help="결과 폴더")
    ap.add_argument("--limits", type=Path, default=OUT / "limits_proposed.xlsx", help="실습 A 02의 한도안(있으면 절감액 계산)")
    args = ap.parse_args()
    # 상대 경로(예: --out workbench/day4/outputs/u1)는 지금 폴더 기준의 절대 경로로 바꾼다 — 출력 줄에서 경로를 줄일 때 멈추지 않게
    args.scenarios, args.out, args.limits = (p.resolve() for p in (args.scenarios, args.out, args.limits))

    b = pd.read_csv(DATA / "d4_start_scored.csv", encoding="utf-8-sig")
    sc = pd.read_csv(args.scenarios, encoding="utf-8-sig")
    sc = sc[sc["row_type"] == "scenario"].reset_index(drop=True)

    rows, runs = [], {}
    for _, s in sc.iterrows():
        p, loss_if = scenario_vectors(b, s)
        el = float((p * loss_if).sum())
        for rho in args.rho:
            loss = simulate(p, loss_if, args.n, args.seed, rho)
            st = summarize(loss)
            rows.append({"scenario_id": s["scenario_id"], "name_ko": s["name_ko"], "rho": rho, "n_sims": args.n, "seed": args.seed,
                         "el_formula_usd": round(el, 2), "mc_mean_usd": round(st["mean"], 2), "mc_p95_usd": round(st["p95"], 2),
                         "mc_p99_usd": round(st["p99"], 2), "mc_es99_usd": round(st["es99"], 2)})
            if rho == 0.0:
                runs[s["scenario_id"]] = loss
    res = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.out / "stress_results.csv", index=False, encoding="utf-8-sig")

    show = res.assign(**{c: res[c].map("{:,.0f}".format) for c in ("el_formula_usd", "mc_mean_usd", "mc_p95_usd", "mc_p99_usd", "mc_es99_usd")})
    print(f"반복 {args.n:,}회 · 시드 {args.seed}")
    print(show.drop(columns=["name_ko", "n_sims", "seed"]).to_string(index=False))

    draw_hist(args.out / "loss_hist.png", {k: v for k, v in runs.items() if k in ("S0", "S3")})
    print(f"저장: {rel(args.out / 'stress_results.csv')} · {rel(args.out / 'loss_hist.png')}")

    sav = savings(b, sc, args.limits)
    if sav is None:
        print(f"(한도안 {args.limits.name}이 없어 절감액은 건너뜀 — 실습 A 02를 마친 뒤 다시 돌리면 나옵니다)")
    else:
        sav.round(2).to_csv(args.out / "stress_savings.csv", index=False, encoding="utf-8-sig")
        keep = sav[sav["scenario_id"].isin(["S0", "S3"])]
        print("한도 재배정의 연 기대손실 절감액(외상 거래 바이어):", " · ".join(f"{r.scenario_id} {r.saving_usd:,.0f}" for r in keep.itertuples()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
