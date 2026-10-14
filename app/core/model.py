"""② 예측·등급 — Day3 강사 모델(LightGBM)로 30일 연체확률(pd_30d)을 다시 계산하고 S/A/B/C 등급을 붙인다.

모델 파일: models/day3_lgbm.pkl(joblib) — 실패하면 같은 모델의 네이티브 텍스트판 day3_lgbm.txt(라이브러리 버전 의존이 적다).
특성 정의: models/feature_list.json(숫자 열 + 이진 2 + 결제방식 원-핫), 등급 경계: models/grade_cutoffs.json(t/4·t/2·t).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

GRADES = ["S", "A", "B", "C"]
PREV_REF_DATE = "2026-08-31"   # 직전 기준일(등급 변화 비교)


@dataclass
class ModelBundle:
    features: list
    spec: dict
    cutoffs: dict
    kind: str            # "pkl" | "txt"
    version: str
    _model: object

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.kind == "pkl":
            return self._model.predict_proba(X[self.features])[:, 1]
        return self._model.predict(X[self.features])

    def contrib(self, X: pd.DataFrame) -> np.ndarray:
        """특성별 기여(로그오즈, + = 위험↑). 마지막 열은 기준값(bias). LightGBM pred_contrib = TreeSHAP."""
        booster = self._model.booster_ if self.kind == "pkl" else self._model
        return booster.predict(X[self.features], pred_contrib=True)


def load_model(models_dir: Path) -> ModelBundle:
    models_dir = Path(models_dir)
    spec = json.loads((models_dir / "feature_list.json").read_text(encoding="utf-8"))
    cut = json.loads((models_dir / "grade_cutoffs.json").read_text(encoding="utf-8"))
    model, kind = None, ""
    pkl = models_dir / "day3_lgbm.pkl"
    if pkl.exists():
        try:
            import joblib
            model, kind = joblib.load(pkl), "pkl"
        except Exception:  # 버전 차이로 역직렬화 실패 → 텍스트 모델
            model = None
    if model is None:
        import lightgbm as lgb
        model, kind = lgb.Booster(model_file=str(models_dir / "day3_lgbm.txt")), "txt"
    return ModelBundle(features=list(spec["features"]), spec=spec, cutoffs=cut, kind=kind,
                       version=spec.get("model_version", "unknown"), _model=model)


def design(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """특성표 → 모델 입력 행렬(train_day3_model.design과 같은 규칙). 없는 숫자 열은 빈칸(NaN)."""
    X = pd.DataFrame(index=df.index)
    for c in spec["numeric_features"]:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan
    for name, b in spec["binary_features"].items():
        col = df[b["column"]].astype(str) if b["column"] in df.columns else pd.Series("", index=df.index)
        X[name] = (col == b["equals"]).astype(float)
    oh = spec["onehot"]
    col = df[oh["column"]].astype(str) if oh["column"] in df.columns else pd.Series("", index=df.index)
    for lv in oh["levels"]:
        X[oh["prefix"] + lv] = (col == lv).astype(float)
    return X[spec["features"]].astype(float)


def grade_from_pd(p, cutoffs: dict) -> np.ndarray:
    """grade_cutoffs.json의 [하한, 상한) 구간. 기본 규칙 S < t/4 ≤ A < t/2 ≤ B < t ≤ C."""
    p = np.asarray(p, dtype=float)
    c = cutoffs["cutoffs"]
    return np.select([p >= c["C"][0], p >= c["B"][0], p >= c["A"][0]], ["C", "B", "A"], "S")


def grade_quantile(p) -> np.ndarray:
    """🔵 대안: 위험 순위 백분위 15/35/35/15(rank_pct ≥ 0.85 C · ≥ 0.50 B · ≥ 0.15 A)."""
    r = pd.Series(p).rank(pct=True, method="average").to_numpy()
    return np.select([r >= 0.85, r >= 0.50, r >= 0.15], ["C", "B", "A"], "S")


def update_from_ledger(features: pd.DataFrame, ledger: pd.DataFrame, asof) -> pd.DataFrame:
    """업로드 원장으로 '지금 연체' 특성 4개를 다시 계산한다(원장에 있는 바이어만).
    oldest_open_days · ksure_30d_flag · overdue_amount_usd · open_ar_usd. 나머지 이력·재무·뉴스 특성은 그대로."""
    asof = pd.Timestamp(asof)
    f = features.copy().set_index("buyer_id")
    L = ledger[ledger["due_date"].notna()].copy()
    L["dpd_now"] = (asof - L["due_date"]).dt.days
    amt = L["open_amount_usd"].fillna(L.get("amount_usd"))
    L["_amt"] = amt
    nonlc = ~L["payment_method"].isin(["LC_SIGHT", "LC_USANCE", "TT_ADV"])
    g = L.groupby("buyer_id")
    upd = pd.DataFrame({
        "oldest_open_days": g["dpd_now"].max().clip(lower=0),
        "open_ar_usd": g["_amt"].sum().round(2),
        "overdue_amount_usd": L[L["dpd_now"] > 0].groupby("buyer_id")["_amt"].sum().round(2),
        "ksure_30d_flag": L[nonlc & (L["dpd_now"] > 30)].groupby("buyer_id").size().gt(0).astype(int),
    })
    upd["overdue_amount_usd"] = upd["overdue_amount_usd"].fillna(0.0)
    upd["ksure_30d_flag"] = upd["ksure_30d_flag"].fillna(0).astype(int)
    common = f.index.intersection(upd.index)
    for c in upd.columns:
        f.loc[common, c] = upd.loc[common, c]
    return f.reset_index()


def score(features: pd.DataFrame, bundle: ModelBundle, top_k: int = 3) -> pd.DataFrame:
    """바이어 특성표 → buyer_id · pd_30d · grade · grade_quantile · rank_pct · 상위 기여 3개(한국어)."""
    X = design(features, bundle.spec)
    p = bundle.predict(X)
    cont = bundle.contrib(X)[:, :-1]
    ko = bundle.spec.get("labels_ko", {})
    out = pd.DataFrame({"buyer_id": features["buyer_id"].to_numpy(), "pd_30d": np.round(p, 5)})
    out["grade"] = grade_from_pd(p, bundle.cutoffs)
    out["grade_quantile"] = grade_quantile(p)
    out["rank_pct"] = pd.Series(p).rank(pct=True, method="average").round(4).to_numpy()
    feats = bundle.features
    reasons, tops = [], []
    for i in range(len(X)):
        order = np.argsort(-np.abs(cont[i]))[:top_k]
        tops.append([feats[j] for j in order])
        reasons.append(" · ".join(f"{ko.get(feats[j], feats[j])}({cont[i, j]:+.2f})" for j in order))
    for k in range(top_k):
        out[f"top_feature_{k + 1}"] = [t[k] for t in tops]
    out["top_reasons_ko"] = reasons
    out["model_version"] = bundle.version
    return out


def grade_change(cur: pd.Series, prev: pd.Series) -> pd.Series:
    """등급 변화: 하락(위험↑) = 'down', 상승 = 'up', 같음 = 'same', 비교 불가 = ''."""
    rank = {g: i for i, g in enumerate(GRADES)}
    out = []
    for a, b in zip(cur, prev):
        if a not in rank or b not in rank:
            out.append("")
        elif rank[a] > rank[b]:
            out.append("down")
        elif rank[a] < rank[b]:
            out.append("up")
        else:
            out.append("same")
    return pd.Series(out, index=cur.index)


def score_table(features: pd.DataFrame, bundle: ModelBundle, prev_features: pd.DataFrame | None = None,
                quantile: bool = False) -> pd.DataFrame:
    """② 점수표 = score() + grade_prev(직전 기준일 등급) · grade_change(down·up·same) · news_risk_30d.

    quantile=True면 등급을 분위수(15/35/35/15)로 바꾼다(직전 기준일도 같은 규칙). ④ P4 경보가 이 표를 쓴다."""
    sc = score(features, bundle)
    if quantile:
        sc["grade"] = sc["grade_quantile"]
    prev = pd.DataFrame(columns=["buyer_id", "grade_prev"])
    if prev_features is not None and "ref_date" in prev_features.columns:
        pv = prev_features[prev_features["ref_date"].astype(str) == PREV_REF_DATE]
        if len(pv):
            ps = score(pv, bundle)
            prev = pd.DataFrame({"buyer_id": ps["buyer_id"], "grade_prev": ps["grade_quantile"] if quantile else ps["grade"]})
    sc = sc.merge(prev, on="buyer_id", how="left")
    sc["grade_prev"] = sc["grade_prev"].fillna("")
    sc["grade_change"] = grade_change(sc["grade"], sc["grade_prev"])
    if "news_risk_30d" in features.columns:
        sc["news_risk_30d"] = sc["buyer_id"].map(features.set_index("buyer_id")["news_risk_30d"])
    return sc
