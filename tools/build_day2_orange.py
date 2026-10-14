#!/usr/bin/env python
"""Day2 Orange 전처리 워크플로 `labs/day2/d2_orange_preprocess.ows`(수강생용)와 강사용 채운 판을 만들고, 다시 열어 실행 검사한다.

(v3 — 이번 과정은 쓰지 않는다) Orange 전처리 워크플로 생성기.
  [File] d2_step1.xlsx · 시트 features(buyer_id = meta · late_30d = target)
   ├ [Column Statistics](옛 이름 Feature Statistics) — 결측 비율
   ├ [Impute (중앙값 · Step 4)] Default = Don't impute · current_ratio · debt_to_equity · dso_buyer · op_margin = Fixed values
   │    ├ [Data Table (중앙값 대체)] · [Distributions (중앙값)](Standard)
   │    ├ [Continuize](One-hot) → [Data Table](보기만) · [Preprocess](Normalize to [0, 1]) → [Data Table](보기만, 저장 안 함)
   │    └ [Save Data (Step 8 · CSV)] — Save Data는 Impute 출력에 잇는다(§0.8 #7, Continuize 뒤 아님)
   └ [Impute (1-NN 비교)] Default = Model-based imputer ← [kNN (k = 1)] → [Data Table (1-NN)] · [Distributions (1-NN)](Standard)
  (선택 · Step 8) [File] d2_news_scored.csv(date = text) → [Select Rows] date 2026-08-02 ~ 2026-08-31(= 창 (AsOf−30, AsOf])
     → [Group by] buyer_id: news_sent_0_10 Mean · Min · Count → [Merge Data](Data = features, buyer_id) → [Data Table]

정하지 않았던 점을 이렇게 정했다(검사로 확인):
- Orange 3.40의 Impute 'Model-based imputer' 기본 모델은 1-NN이 아니라 나무(SimpleTreeLearner)다 → 사양의 '1-NN 비교'가 되도록
  kNN(Number of neighbors = 1)을 Impute의 Learner 입력에 잇는다.
- 수강생용 .ows에는 중앙값을 넣지 않는다(14:45 화면 공개 값) — Fixed values 칸은 Orange 기본값 0 + 캔버스 메모로 '내 check 시트 중앙값으로
  바꾼다'를 알린다. 강사용 채운 판(../instructor/day2/answers/d2_orange_preprocess_filled.ows)에는 기대값 파일의 중앙값을 넣는다.
- 뉴스 창 필터는 date를 text로 읽어 'is between'(ISO 날짜 문자열 비교)으로 한다 — 날짜(QDate) 조건은 .ows에 Qt 객체로 저장돼
  PyQt5/PyQt6 설치판 사이에서 열리지 않을 수 있다.

사용(저장소 루트, Orange 3.40 환경 — tools/orange_ows.py 머리말의 패키지 · 강사 PC에서만: 강사 기대값 파일이 입력이다):
  python tools/build_day2_orange.py          # 수강생용 + 강사용 .ows 생성 → 다시 열기 → 실행 검사(요약 출력)
공개 저장소 파일이다 — 정답 숫자를 코드에 적지 않는다(중앙값은 강사 폴더의 기대값 파일에서 읽어 강사용 판에만 넣는다).
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import orange_ows as ow  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "labs" / "day2" / "d2_orange_preprocess.ows"
ANSWERS = REPO.parent / "instructor" / "day2" / "answers"
OUT_FILLED = ANSWERS / "d2_orange_preprocess_filled.ows"
EXPECTED = ANSWERS / "d2_buyers_features_expected.csv"
GOLDEN_NEWS = ANSWERS / "d2_news_scored_golden.csv"

STEP1 = "d2_step1.xlsx"
NEWS = "d2_news_scored.csv"
# 사이트 Step 4 ③의 features 시트 열(값 붙여넣기) — buyer_id 첫 열 · late_30d 끝 열
FEATURE_COLS = ["buyer_id", "ar_balance_usd", "pct_ar_31p", "late_ratio", "dpd_trend", "current_ratio", "neg_equity",
                "debt_to_equity", "dso_buyer", "op_margin", "fin_missing", "late_30d"]
RATIOS = ["current_ratio", "debt_to_equity", "dso_buyer", "op_margin"]
NEWS_COLS = ["news_id", "buyer_id", "date", "news_sent_0_10", "label", "evidence", "confidence"]  # P2-3 출력 앞 7열
WINDOW = ("2026-08-02", "2026-08-31")  # (AsOf − 30일, AsOf] — AsOf = 2026-08-31

Q = {
    "file": "Orange.widgets.data.owfile.OWFile",
    "stats": "Orange.widgets.data.owfeaturestatistics.OWFeatureStatistics",
    "impute": "Orange.widgets.data.owimpute.OWImpute",
    "knn": "Orange.widgets.model.owknn.OWKNNLearner",
    "table": "Orange.widgets.data.owtable.OWTable",
    "cont": "Orange.widgets.data.owcontinuize.OWContinuize",
    "prep": "Orange.widgets.data.owpreprocess.OWPreprocess",
    "dist": "Orange.widgets.visualize.owdistributions.OWDistributions",
    "save": "Orange.widgets.data.owsave.OWSave",
    "select": "Orange.widgets.data.owselectrows.OWSelectRows",
    "groupby": "Orange.widgets.data.owgroupby.OWGroupBy",
    "merge": "Orange.widgets.data.owmergedata.OWMergeData",
}
T = {
    "file": "File (d2_step1 · features)", "stats": "Column Statistics (결측)",
    "imp": "Impute (중앙값)", "knn": "kNN (k = 1)", "imp_nn": "Impute (1-NN 비교)",
    "t_imp": "Data Table (중앙값 대체)", "t_nn": "Data Table (1-NN)",
    "cont": "Continuize (보기만)", "t_cont": "Data Table (원-핫)",
    "prep": "Preprocess (0–1 · 보기만)", "t_prep": "Data Table (0–1)",
    "d_imp": "Distributions (중앙값)", "d_nn": "Distributions (1-NN)",
    "save": "Save Data (CSV)",
    "fnews": "File (뉴스 점수)", "sel": "Select Rows (뉴스 창)", "gb": "Group by (buyer_id)",
    "merge": "Merge Data (뉴스 붙이기)", "t_merge": "Data Table (뉴스 집계)",
}


def make_inputs(d2: Path) -> dict:
    """수강생 파일을 흉내 낸 입력(강사 기대값에서): d2_step1.xlsx(시트 buyers · features) · d2_news_scored.csv."""
    from openpyxl import Workbook

    exp = pd.read_csv(EXPECTED, encoding="utf-8-sig")
    feat = exp[FEATURE_COLS]
    wb = Workbook()
    ws0 = wb.active
    ws0.title = "buyers"
    ws0.append(["(수강생 작업 시트 — 검사용 자리)"])
    ws = wb.create_sheet("features")
    ws.append(FEATURE_COLS)
    for row in feat.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else v)
                   for v in row])
    wb.save(d2 / STEP1)
    news = pd.read_csv(GOLDEN_NEWS, encoding="utf-8-sig")[NEWS_COLS]
    news.to_csv(d2 / NEWS, index=False, encoding="utf-8-sig")
    med = {c: round(float(feat[c].median()), 4) for c in RATIOS}
    win = news[(news["date"] >= WINDOW[0]) & (news["date"] <= WINDOW[1])]
    return {"medians": med, "missing": {c: int(feat[c].isna().sum()) for c in FEATURE_COLS},
            "news_in_window": int(len(win)), "news_buyers": int(win["buyer_id"].nunique())}


def csv_filter() -> str:
    from Orange.widgets.data.owsave import OWSave

    return next(f for f in OWSave.get_filters() if f.endswith("(*.csv)") and not f.startswith("Compressed"))


def build(d2: Path, fixed: dict[str, float], out: Path, filled: bool) -> Path:
    from Orange.widgets.data.owimpute import Method, StateRole

    fl = ow.Flow("2일차 — 정제 규칙을 Orange로: 결측 대체 · 보기만 분기 · 저장(Orange 3.40)",
                 "DAY2 블록 A Step 4 ④(재무비율 4종만 같은 기준일 중앙값 + 1-NN 비교) · 블록 B Step 8(선택: Orange로 저장 · "
                 "뉴스 집계). 과정 합성 데이터((가상) 한빛정밀). File을 내 D2 폴더의 d2_step1.xlsx(시트 features)로 다시 지정한다.", d2)
    # ---- Step 4 ④: File(features) → 역할
    f = fl.add("file", Q["file"], T["file"], (0, 220),
               {"recent_paths": [ow.recent_path(STEP1, sheet="features")], "source": 0})
    fl.settle()
    ow.set_roles(f, {"buyer_id": "meta", "late_30d": "target"}, {"late_30d": "categorical"})
    fl.settle()
    fl.add("stats", Q["stats"], T["stats"], (200, 60))
    fl.link("file", "data", "stats", "data")
    # Impute(중앙값): Default = Don't impute(Method.Leave) · 재무비율 4종만 Fixed values
    imp = fl.add("imp", Q["impute"], T["imp"], (400, 220), {"_default_method_index": int(Method.Leave),
                                                         "default_numeric_value": 0.0, "autocommit": True})
    fl.link("file", "data", "imp", "data")
    fl.settle()
    names = [v.name for v in imp.varmodel]
    for col in RATIOS:
        idx = imp.varmodel.index(names.index(col))
        imp.varmodel.setData(idx, (int(Method.Default), (float(fixed[col]),)), StateRole)
        imp.update_varview([idx])
    imp._invalidate()
    fl.settle()
    fl.add("t_imp", Q["table"], T["t_imp"], (600, 60))
    fl.link("imp", "data", "t_imp", "data")
    # 비교: kNN(k = 1) → Impute(Model-based) — Orange 기본 모델(나무)이 아니라 '가장 닮은 바이어' 값
    fl.add("knn", Q["knn"], T["knn"], (200, 560), {"n_neighbors": 1, "metric_index": 0, "weight_index": 0,
                                                 "learner_name": "kNN (k = 1)"})
    fl.add("imp_nn", Q["impute"], T["imp_nn"], (400, 560), {"_default_method_index": int(Method.Model),
                                                         "autocommit": True})
    fl.link("file", "data", "imp_nn", "data")
    fl.link("knn", "learner", "imp_nn", "learner")
    fl.add("t_nn", Q["table"], T["t_nn"], (600, 560))
    fl.link("imp_nn", "data", "t_nn", "data")
    # 보기만 분기 — 저장하지 않는다(정규화는 3일차 평가 안에서)
    fl.add("cont", Q["cont"], T["cont"], (600, 180), {"disc_var_hints": {"": 1}, "cont_var_hints": {"": 0},
                                                    "autosend": True})
    fl.link("imp", "data", "cont", "data")
    fl.add("t_cont", Q["table"], T["t_cont"], (800, 180))
    fl.link("cont", "data", "t_cont", "data")
    fl.add("prep", Q["prep"], T["prep"], (600, 300),
           {"storedsettings": {"name": "", "preprocessors": [("orange.preprocess.scale", {"method": 3})]},
            "autocommit": True})
    fl.link("imp", "data", "prep", "data")
    fl.add("t_prep", Q["table"], T["t_prep"], (800, 300))
    fl.link("prep", "preprocessed_data", "t_prep", "data")
    # Standard: 분포 비교(중앙값 vs 1-NN) — current_ratio
    fl.add("d_imp", Q["dist"], T["d_imp"], (800, 60))
    fl.link("imp", "data", "d_imp", "data")
    fl.add("d_nn", Q["dist"], T["d_nn"], (800, 560))
    fl.link("imp_nn", "data", "d_nn", "data")
    # Step 8(선택): Save Data는 Impute 출력에
    fl.add("save", Q["save"], T["save"], (600, 420),
           {"filter": csv_filter(), "stored_name": "d2_end_features_orange.csv", "stored_path": ".",
            "auto_save": False, "add_type_annotations": False})
    fl.link("imp", "data", "save", "data")
    fl.settle(timeout=300)
    for key in ("d_imp", "d_nn"):
        dw = fl.w(key)
        if dw.data is not None:
            dw.var = dw.data.domain["current_ratio"]
            dw._on_var_changed()
    # (선택) 뉴스 집계: File(news, date = text) → Select Rows(창) → Group by → Merge Data
    fn = fl.add("fnews", Q["file"], T["fnews"], (0, 760), {"recent_paths": [ow.recent_path(NEWS)], "source": 0})
    fl.settle()
    ow.set_roles(fn, {}, {"date": "text"})
    fl.settle()
    sel = fl.add("sel", Q["select"], T["sel"], (200, 760), {"purge_attributes": False, "purge_classes": False})
    fl.link("fnews", "data", "sel", "data")
    fl.settle()
    date_var = sel.data.domain["date"]
    from Orange.data.filter import FilterString

    between = [op for op, *_ in sel.Operators[type(date_var)]].index(FilterString.Between)
    sel.remove_all_rows()
    sel.add_row(date_var, between, list(WINDOW))
    sel.conditions_changed()
    sel.commit.now()
    fl.settle()
    gb = fl.add("gb", Q["groupby"], T["gb"], (400, 760))
    fl.link("sel", "matching_data", "gb", "data")
    fl.settle()
    dom = gb.data.domain
    gb.gb_attrs = [dom["buyer_id"]]
    gb.aggregations = {v: set() for v in dom.variables + dom.metas}
    gb.aggregations[dom["news_sent_0_10"]] = {"Mean", "Min. value", "Count"}
    gb._set_gb_selection()
    gb.commit.now()
    fl.settle()
    fl.add("merge", Q["merge"], T["merge"], (600, 760), {"merging": 0, "auto_apply": True})
    fl.link("file", "data", "merge", "data")
    fl.link("gb", "data", "merge", "extra_data")
    fl.add("t_merge", Q["table"], T["t_merge"], (800, 760))
    fl.link("merge", "data", "t_merge", "data")
    fl.settle()
    if len(sel.conditions) != 1:
        raise RuntimeError(f"Select Rows 조건 {len(sel.conditions)}개")

    # ---- 캔버스 메모
    fixed_note = ("강사판 — 기대값 중앙값이 들어 있다(14:45 화면 공개 전 배포 금지)." if filled else
                  "Fixed values 칸의 0은 자리표시다 → 내 check 시트의 중앙값(=MEDIAN)으로 바꾼다.")
    fl.note((-20, -160, 940, 60),
            "2일차 Orange 전처리 — Step 4 ④ 결측 대체(재무비율 4종만) · 보기만 분기 · Step 8(선택) 저장과 뉴스 집계. "
            "처음 열면 File을 내 D2 폴더의 d2_step1.xlsx · Sheet features로 다시 지정 → buyer_id = meta · late_30d = target → Apply.",
            13)
    fl.note((-70, 290, 200, 180), "Step 4 ④ · Column Statistics(옛 이름 Feature Statistics)의 Missing 열로 결측이 많은 열을 "
                                  "본다. 재무비율 4종만 채우고 나머지(pct_ar_31p · dpd_trend 등)는 그대로 둔다 — fin_missing이 표시")
    fl.note((300, -80, 400, 90), "Impute(중앙값) · Default method = Don't impute · current_ratio · debt_to_equity · "
                                 f"dso_buyer · op_margin = Fixed values. {fixed_note}")
    fl.note((130, 630, 460, 60), "비교 · Impute(1-NN) = Model-based imputer + kNN(k = 1). kNN을 잇지 않으면 Orange 기본 모델은 "
                                 "나무(tree)다. 모든 빈칸을 채운다 — 정의되지 않는 값까지 채우는 것이 차이")
    fl.note((900, 170, 240, 130), "보기만 · Continuize(원-핫) · Preprocess(Normalize to [0, 1]) → Data Table. "
                                  "정규화 값은 저장하지 않는다 — 3일차 평가 안에서 학습 데이터 기준으로 한다")
    fl.note((680, 400, 280, 50), "Step 8(선택) · Save Data는 Impute 출력에(Continuize 뒤 아님)")
    fl.note((900, 20, 240, 90), "(Standard) Distributions 두 개(위 · 아래) — current_ratio 분포를 중앙값 vs 1-NN으로 비교한다")
    fl.note((-60, 830, 960, 60), "Step 8(선택) · 뉴스 집계를 Orange로: File(d2_news_scored.csv, date = text) → Select Rows "
                                 f"(date is between {WINDOW[0]} · {WINDOW[1]} = 창 (AsOf−30일, AsOf]) → Group by(buyer_id: Mean · "
                                 "Min · Count) → Merge Data(buyer_id). 뉴스가 없는 바이어는 빈칸 — 5 + no_news_flag는 시트에서 채운다")
    fl.save(out)
    fl.close()
    return out


# ---------------------------------------------------------------- 검사
def check_run(ows: Path, d2: Path, info: dict, filled: bool, workdir: Path) -> dict:
    scheme, w = ow.run_ows(ows, [d2 / STEP1, d2 / NEWS], workdir)
    lv = lambda title, out="data": ow.link_value(scheme, title, out)  # noqa: E731
    problems: list[str] = []
    data = lv(T["file"])
    dom = ow.domain_summary(data)
    if dom["class"] != ["late_30d"] or "buyer_id" not in dom["metas"] or dom["rows"] != 150:
        problems.append(f"File(features) 역할·행 {dom}")
    imp = lv(T["imp"])
    miss = {v.name: int(np.isnan(imp.get_column(v.name).astype(float)).sum()) for v in imp.domain.attributes}
    for c in RATIOS:
        if miss.get(c):
            problems.append(f"Impute(중앙값) {c} 빈칸 {miss[c]}")
    kept = {c: miss.get(c) for c in ("pct_ar_31p", "dpd_trend", "late_ratio")}
    if any(kept[c] != info["missing"][c] for c in kept):
        problems.append(f"Impute(중앙값)이 다른 열까지 채움: {kept}")
    filled_vals = {}
    src = data
    for c in RATIOS:
        was_nan = np.isnan(src.get_column(c).astype(float))
        vals = np.unique(np.round(imp.get_column(c).astype(float)[was_nan], 4))
        filled_vals[c] = vals.tolist()
        want = info["medians"][c] if filled else 0.0
        if len(vals) != 1 or abs(vals[0] - want) > 1e-6:
            problems.append(f"{c} 대체값 {vals.tolist()} ≠ {want}")
    nn = lv(T["imp_nn"])
    nn_left = int(sum(np.isnan(nn.get_column(v.name).astype(float)).sum() for v in nn.domain.attributes))
    learner = w[T["imp_nn"]].learner
    if type(learner).__name__ != "KNNLearner" or getattr(learner, "kwargs", {}).get("n_neighbors") != 1:
        problems.append(f"Impute(1-NN)의 학습기 {learner!r}")
    prep = lv(T["prep"], "preprocessed_data")
    pmax = float(np.nanmax(prep.X)) if prep is not None else None
    pmin = float(np.nanmin(prep.X)) if prep is not None else None
    if prep is None or pmin < -1e-9 or pmax > 1 + 1e-9:
        problems.append(f"Preprocess 0–1 범위 아님 {pmin}–{pmax}")
    saved = {}
    sw = w[T["save"]]
    try:
        sw.do_save()
        fn = Path(sw.filename)
        head = fn.read_text(encoding="utf-8").splitlines()
        saved = {"file": fn.name, "lines": len(head), "header": head[0].split(",")}
        if head[0].startswith(("c#", "d#", "m#", "C#")) or len(head) != 151:
            problems.append(f"저장 CSV 형식 {head[0][:40]} · 줄 {len(head)}")
    except Exception as e:  # noqa: BLE001
        problems.append(f"Save Data 실패 {e!r}")
    sel = lv(T["sel"], "matching_data")
    gbo = lv(T["gb"])
    mer = lv(T["merge"])
    news = {"window_rows": None if sel is None else len(sel), "buyers": None if gbo is None else len(gbo),
            "merged_rows": None if mer is None else len(mer),
            "group_by_columns": None if gbo is None else [v.name for v in gbo.domain.variables + gbo.domain.metas]}
    if news["window_rows"] != info["news_in_window"] or news["buyers"] != info["news_buyers"] or news["merged_rows"] != 150:
        problems.append(f"뉴스 집계 {news} (기대 창 {info['news_in_window']}건 · {info['news_buyers']}개사 · 150행)")
    if len(w[T["sel"]].conditions) != 1:
        problems.append("Select Rows 조건이 1개가 아님")
    dist = {k: getattr(w[T[k]].var, "name", None) for k in ("d_imp", "d_nn")}
    if set(dist.values()) != {"current_ratio"}:
        problems.append(f"Distributions 변수 {dist}")
    out = {"file_roles": dom, "missing_after_median_impute": miss, "fixed_values_used": filled_vals,
           "missing_after_1nn": nn_left, "preprocess_range": [pmin, pmax], "saved_csv": saved, "news_path": news,
           "distributions_var": dist}
    return {"problems": problems, "values": out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--keep", action="store_true", help="임시 폴더를 남긴다(디버그)")
    args = ap.parse_args()
    if not EXPECTED.is_file() or not GOLDEN_NEWS.is_file():
        print(f"강사 기대값 파일이 없습니다: {EXPECTED} · {GOLDEN_NEWS} — 강사 PC에서 실행합니다.")
        return 2
    ow.check_versions()
    tmp = Path(tempfile.mkdtemp(prefix="d2_orange_"))
    rc = 0
    try:
        d2 = tmp / "D2"
        d2.mkdir()
        info = make_inputs(d2)
        print(f"입력(흉내): {STEP1}(features 150행) · {NEWS}(300행) · 창 안 뉴스 {info['news_in_window']}건 · "
              f"{info['news_buyers']}개사")
        for out, fixed, filled in ((OUT, {c: 0.0 for c in RATIOS}, False), (OUT_FILLED, info["medians"], True)):
            path = build(d2, fixed, out, filled)
            loaded = ow.load_check(path)
            where = path.relative_to(REPO) if REPO in path.parents else path
            print(f"생성: {where} ({path.stat().st_size:,} bytes) · 노드 {loaded['nodes']} · 링크 {loaded['links']} · "
                  f"메모 {loaded['annotations']}")
            chk = check_run(path, d2, info, filled, tmp / ("run_filled" if filled else "run_public"))
            v = chk["values"]
            print("  대체값", v["fixed_values_used"], "· 1-NN 뒤 남은 빈칸", v["missing_after_1nn"],
                  "· 0–1 범위", v["preprocess_range"])
            print("  저장 CSV", v["saved_csv"].get("header", [])[:3], "…", v["saved_csv"].get("header", [])[-2:],
                  f"({v['saved_csv'].get('lines')}줄)", "· 뉴스", v["news_path"])
            if chk["problems"]:
                print("  문제:", *chk["problems"], sep="\n   - ")
                rc = 1
        if rc == 0:
            print("검사 통과 — 두 판 모두 설정 복원 · 신호 전달 · 저장까지 문제 없음")
        return rc
    finally:
        if args.keep:
            print("임시 폴더:", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
