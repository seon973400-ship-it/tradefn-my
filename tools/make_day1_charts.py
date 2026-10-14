#!/usr/bin/env python
"""Day1 실습 가이드용 차트 4종(라이트·다크) + 표 버전 CSV → docs/assets/day1/

사용: python tools/make_day1_charts.py
- 데이터: 정제 150개사 스냅샷(기준일 2026-09-30) + 인보이스 원장(DPD 분포)
- 색: Day1 슬라이드 스타일 킷 토큰(BLUE·ORANGE·PAPER)을 dataviz 검증기로 확인한 값만 사용
  (라이트: 범주 쌍·서열 램프 PASS / 다크: 같은 색상을 다크 면에 맞춰 한 단계 조정 후 PASS)
- 한글 글꼴: tools/fonts/NanumGothic(OFL 1.1)
사이트(MkDocs Material)에서는 `![...](day1_fig1_....png#only-light)` + `![...](..._dark.png#only-dark)`로 쓴다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tf_common import REPO, TOOLS, load_config, write_csv  # noqa: E402

OUT = REPO / "docs" / "assets" / "day1"
FONT_DIR = TOOLS / "fonts"

THEMES = {
    "light": {"surface": "#F6F5F1", "ink": "#13203A", "body": "#3D4656", "muted": "#5B6475", "grid": "#D9D6CC",
              "axis": "#BDB9AD", "blue": "#1F5FD1", "orange": "#C2410C", "current": "#BDB9AD",
              "ramp": ["#EE8A4E", "#D7621F", "#B0440F", "#7A2E0A"], "suffix": ""},
    "dark": {"surface": "#1E2029", "ink": "#F6F5F1", "body": "#C9CDD6", "muted": "#9AA3B5", "grid": "#2E3240",
             "axis": "#454955", "blue": "#3987E5", "orange": "#D95926", "current": "#565B69",
             "ramp": ["#9A3A12", "#C4501C", "#E8743B", "#F6A26E"], "suffix": "_dark"},
}
BUCKETS = ["Current", "1-30", "31-60", "61-90", "91+"]
BUCKET_KO = {"Current": "미연체", "1-30": "1–30일", "31-60": "31–60일", "61-90": "61–90일", "91+": "91일+"}
PM_LABEL = {"TT_ADV": "선수금 TT_ADV", "TT_SPLIT_30_70": "분할 30/70 TT_SPLIT", "LC_SIGHT": "L/C 일람불 LC_SIGHT",
            "LC_USANCE": "L/C 기한부 LC_USANCE", "DP": "D/P", "DA": "D/A", "OA": "O/A"}
LADDER = ["TT_ADV", "TT_SPLIT_30_70", "LC_SIGHT", "LC_USANCE", "DP", "DA", "OA"]  # 수출자 위험 사다리(낮음 → 높음)
SOURCE = "출처: (가상) 한빛정밀(주) 교육용 합성 데이터 · tools/make_day1_charts.py"


def setup_fonts() -> None:
    for f in ["NanumGothic-Regular.ttf", "NanumGothic-Bold.ttf"]:
        font_manager.fontManager.addfont(str(FONT_DIR / f))
    plt.rcParams.update({"font.family": "NanumGothic", "axes.unicode_minus": False, "font.size": 10})


def base(th, w=8.0, h=4.6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=200)
    fig.patch.set_facecolor(th["surface"])
    ax.set_facecolor(th["surface"])
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(th["axis"])
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(colors=th["muted"], labelsize=9, length=0)
    ax.xaxis.grid(True, color=th["grid"], linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)
    return fig, ax


def titles(fig, th, title, subtitle, note=SOURCE):
    fig.text(0.02, 0.965, title, fontsize=14, fontweight="bold", color=th["ink"], va="top", ha="left")
    fig.text(0.02, 0.905, subtitle, fontsize=9, color=th["body"], va="top", ha="left")
    fig.text(0.02, 0.02, note, fontsize=7.5, color=th["muted"], va="bottom", ha="left")


def save(fig, th, stem):
    p = OUT / f"{stem}{th['suffix']}.png"
    fig.savefig(p, facecolor=th["surface"], dpi=200)
    plt.close(fig)
    return p


# ------------------------------------------------------------------ 1. 결제방식 × 에이징
def fig1(clean, th):
    ct = pd.crosstab(clean.payment_method, clean.aging_bucket).reindex(index=LADDER, columns=BUCKETS, fill_value=0)
    n = ct.sum(axis=1)
    share = ct.div(n, axis=0)
    fig, ax = base(th, h=4.9)
    y = np.arange(len(LADDER))[::-1]
    left = np.zeros(len(LADDER))
    colors = [th["current"]] + th["ramp"]
    for b, col in zip(BUCKETS, colors):
        v = share[b].to_numpy()
        ax.barh(y, v, left=left, height=0.56, color=col, edgecolor=th["surface"], linewidth=1.6,
                label=BUCKET_KO[b])
        left += v
    ax.set_yticks(y, [PM_LABEL[m] for m in LADDER], color=th["body"], fontsize=9)
    ax.set_xlim(0, 1.0)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
    ov = 1 - share["Current"]
    for yi, m in zip(y, LADDER):
        txt = f"n={int(n[m])} · 연체 {ov[m] * 100:.1f}%"
        ax.text(1.015, yi, txt, va="center", ha="left", fontsize=8.6, color=th["ink"] if ov[m] > 0 else th["muted"],
                fontweight="bold" if ov[m] > 0 else "normal", clip_on=False)
    leg = ax.legend(ncol=5, loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=8.6,
                    handlelength=1.2, handleheight=0.9, columnspacing=1.2, borderaxespad=0.3)
    for t in leg.get_texts():
        t.set_color(th["body"])
    ax.text(0, -0.13, "← 수출자 위험 낮음(위) · 높음(아래): 결제방식 리스크 사다리", transform=ax.transAxes,
            fontsize=7.8, color=th["muted"], va="top")
    fig.subplots_adjust(left=0.24, right=0.80, top=0.76, bottom=0.17)
    titles(fig, th, "결제방식 × 에이징 구성(행 100%)",
           "정제 150개사 · 기준일 2026-09-30 · 바이어별 최악 연체일 기준 CRF 구간(미연체 / 1–30 / 31–60 / 61–90 / 91일+)")
    tbl = ct.copy()
    tbl.columns = ["n_" + {"Current": "current", "1-30": "1_30", "31-60": "31_60", "61-90": "61_90", "91+": "91p"}[c] for c in tbl.columns]
    tbl["n_total"] = n
    tbl["overdue_share"] = ov.round(4)
    return save(fig, th, "day1_fig1_aging_by_payment_method"), tbl.reset_index().rename(columns={"payment_method": "payment_method"})


# ------------------------------------------------------------------ 2. 국가별 연체 비율 상위 10
def fig2(clean, th):
    g = clean.groupby("country_code").agg(n=("buyer_id", "size"), n_ov=("is_overdue", "sum"), ratio=("is_overdue", "mean"))
    g = g.sort_values(["ratio", "n"], ascending=[False, False]).head(10)
    names = clean.drop_duplicates("country_code").set_index("country_code").country
    ko = {"MEX": "멕시코", "ARE": "UAE", "THA": "태국", "TWN": "대만", "IDN": "인도네시아", "TUR": "튀르키예", "BRA": "브라질",
          "USA": "미국", "DEU": "독일", "POL": "폴란드", "CHN": "중국", "VNM": "베트남", "IND": "인도", "JPN": "일본",
          "GBR": "영국", "NLD": "네덜란드", "MYS": "말레이시아", "SAU": "사우디", "EGY": "이집트", "NGA": "나이지리아"}
    fig, ax = base(th, h=4.9)
    y = np.arange(len(g))[::-1]
    ax.barh(y, g.ratio, height=0.56, color=th["blue"])
    ax.set_yticks(y, [f"{c}  {ko.get(c, names.get(c, ''))}" for c in g.index], color=th["body"], fontsize=9)
    mx = max(0.8, float(g.ratio.max()) + 0.22)
    ax.set_xlim(0, mx)
    ticks = [0, 0.2, 0.4, 0.6, 0.8][: int(mx / 0.2) + 1]
    ax.set_xticks(ticks, [f"{t * 100:.0f}%" for t in ticks])
    for yi, (c, r) in zip(y, g.iterrows()):
        small = "  표본 작음" if r.n < 5 else ""
        ax.text(r.ratio + 0.012, yi, f"{r.ratio * 100:.1f}%  ({int(r.n_ov)}/{int(r.n)}곳){small}", va="center",
                fontsize=8.6, color=th["ink"])
    overall = clean.is_overdue.mean()
    ax.axvline(overall, color=th["muted"], linewidth=0.9)
    ax.text(overall + 0.006, y.max() + 0.62, f"전체 {overall * 100:.1f}%", fontsize=8, color=th["muted"], va="bottom")
    fig.subplots_adjust(left=0.20, right=0.97, top=0.80, bottom=0.12)
    titles(fig, th, "국가별 연체 바이어 비율 상위 10",
           "정제 150개사 · 연체 = 기준일(2026-09-30)에 결제기일이 지난 미결 인보이스 1건 이상 · 동률은 바이어 수 많은 순")
    tbl = g.reset_index().rename(columns={"country_code": "country_code", "n": "buyers", "n_ov": "overdue_buyers", "ratio": "overdue_ratio"})
    tbl["overdue_ratio"] = tbl.overdue_ratio.round(4)
    return save(fig, th, "day1_fig2_overdue_ratio_top10_country"), tbl


# ------------------------------------------------------------------ 3. 권역별 잔액(USD)
def fig3(clean, th, fx_note):
    g = clean.groupby("region").agg(ar=("ar_balance_usd", "sum"), od=("overdue_amount_usd", "sum"))
    g["cur"] = g.ar - g.od
    g = g.sort_values("ar", ascending=False)
    fig, ax = base(th, h=4.6)
    y = np.arange(len(g))[::-1]
    ax.barh(y, g.cur / 1e6, height=0.56, color=th["blue"], edgecolor=th["surface"], linewidth=1.6, label="미연체 잔액")
    ax.barh(y, g.od / 1e6, left=g.cur / 1e6, height=0.56, color=th["orange"], edgecolor=th["surface"], linewidth=1.6,
            label="연체 잔액(결제기일 경과)")
    ax.set_yticks(y, list(g.index), color=th["body"], fontsize=9.5)
    mx = float(g.ar.max() / 1e6) * 1.42
    ax.set_xlim(0, mx)
    step = 0.25 if mx < 1.6 else 0.5
    ticks = np.arange(0, mx + 1e-9, step)
    ax.set_xticks(ticks, [f"{t:.2f}".rstrip("0").rstrip(".") + "M" if t else "0" for t in ticks])
    for yi, (rg, r) in zip(y, g.iterrows()):
        ax.text(r.ar / 1e6 + mx * 0.012, yi, f"USD {r.ar / 1e6:.2f}M · 연체 {r.od / r.ar * 100:.1f}%", va="center",
                fontsize=8.6, color=th["ink"])
    leg = ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=8.6, handlelength=1.2,
                    borderaxespad=0.3)
    for t in leg.get_texts():
        t.set_color(th["body"])
    ax.set_xlabel("매출채권 잔액(USD 백만)", fontsize=8.5, color=th["muted"])
    fig.subplots_adjust(left=0.16, right=0.97, top=0.76, bottom=0.17)
    tot, tod = g.ar.sum(), g.od.sum()
    titles(fig, th, "권역별 매출채권 잔액과 연체 잔액(USD)",
           f"정제 150개사 · 기준일 2026-09-30 · 전체 USD {tot / 1e6:.2f}M 중 연체 {tod / tot * 100:.1f}% · {fx_note}")
    tbl = g.reset_index().rename(columns={"ar": "ar_balance_usd", "od": "overdue_amount_usd", "cur": "current_amount_usd"})
    for c in ["ar_balance_usd", "overdue_amount_usd", "current_amount_usd"]:
        tbl[c] = tbl[c].round(2)
    tbl["overdue_share"] = (tbl.overdue_amount_usd / tbl.ar_balance_usd).round(4)
    return save(fig, th, "day1_fig3_ar_balance_by_region"), tbl


# ------------------------------------------------------------------ 4. DPD 분포(인보이스)
def fig4(inv, th, end):
    late = inv[(inv.dpd_final > 0) & (inv.due_date <= end) & (inv.payment_method != "TT_ADV")].copy()
    d = late.dpd_final.to_numpy()
    edges = list(range(0, 121, 5)) + [10 ** 6]
    counts, _ = np.histogram(d, bins=[e + 0.5 for e in edges])
    labels_x = np.arange(len(counts))
    bk = pd.cut(pd.Series([e + 3 for e in edges[:-1]]), [0, 30, 60, 90, 1e9], labels=BUCKETS[1:])
    color_of = dict(zip(BUCKETS[1:], th["ramp"]))
    fig, ax = base(th, h=4.7)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, color=th["grid"], linewidth=0.6)
    ax.bar(labels_x, counts, width=0.82, color=[color_of[b] for b in bk], edgecolor=th["surface"], linewidth=0.8)
    tick_pos = [0, 6, 12, 18]
    ax.set_xticks([p - 0.5 for p in tick_pos] + [len(counts) - 1], ["0", "30", "60", "90", "121일+"])
    ax.set_xlim(-0.8, len(counts) - 0.2)
    for p in [6, 12, 18]:
        ax.axvline(p - 0.5, color=th["muted"], linewidth=0.9)
    shares = pd.cut(pd.Series(d), [0, 30, 60, 90, 1e9], labels=BUCKETS[1:]).value_counts(normalize=True)
    ymax = counts.max()
    ax.set_ylim(0, ymax * 1.30)
    for (lo, hi), b in zip([(0, 6), (6, 12), (12, 18), (18, len(counts))], BUCKETS[1:]):
        ax.text((lo + hi) / 2 - 0.5, ymax * 1.24, f"{BUCKET_KO[b]}  {shares[b] * 100:.0f}%", ha="center", va="top",
                fontsize=8.8, color=th["ink"], fontweight="bold")
    ax.text(6 - 0.4, ymax * 1.07, "30일: K-SURE 연속수출 면책선\nIFRS 9 '30일 초과' 추정", fontsize=7.6,
            color=th["body"], va="top")
    ax.text(18 - 0.4, ymax * 1.07, "90일: IFRS 9 채무불이행 추정", fontsize=7.6, color=th["body"], va="top")
    ax.set_ylabel("인보이스 수", fontsize=8.5, color=th["muted"])
    ax.set_xlabel("연체일수(DPD, 5일 구간)", fontsize=8.5, color=th["muted"])
    med, p90 = np.median(d), np.percentile(d, 90)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.17)
    titles(fig, th, "연체 인보이스의 연체일(DPD) 분포",
           f"인보이스 원장 2023-10~2026-09 · 연체 {len(d):,}건(미결은 기준일 2026-09-30까지) · 중앙값 {med:.0f}일 · P90 {p90:.0f}일 · 선수금 제외")
    tbl = pd.DataFrame({"dpd_from": [e + 1 for e in edges[:-1]], "dpd_to": [e + 5 if e < 120 else None for e in edges[:-1]],
                        "invoices": counts, "bucket": list(bk.astype(str))})
    return save(fig, th, "day1_fig4_dpd_distribution"), tbl


def main() -> int:
    setup_fonts()
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    from build_checkpoints import Builder  # noqa: E402
    bld = Builder(cfg, answers_dir=REPO / "_unused")
    clean = bld.d1_clean()
    inv = bld.T["invoices"]
    end = pd.Timestamp(cfg["meta"]["end_date"])
    fx = bld.fx.df.loc[end]
    fx_note = f"환산: FRED H.10 교차환율(관측일 {pd.Timestamp(fx.obs_date).date()})"
    made = []
    for name, th in THEMES.items():
        p1, t1 = fig1(clean, th)
        p2, t2 = fig2(clean, th)
        p3, t3 = fig3(clean, th, fx_note)
        p4, t4 = fig4(inv, th, end)
        made += [p1, p2, p3, p4]
    for stem, t in [("day1_fig1_aging_by_payment_method", t1), ("day1_fig2_overdue_ratio_top10_country", t2),
                    ("day1_fig3_ar_balance_by_region", t3), ("day1_fig4_dpd_distribution", t4)]:
        write_csv(t, OUT / f"{stem}.csv")
    for p in made:
        print("→", p.relative_to(REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
