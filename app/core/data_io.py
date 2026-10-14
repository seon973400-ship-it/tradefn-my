"""경로와 파일 읽기 — 저장소 안의 공개 파일만 읽는다(키·실데이터 없음).

앱은 저장소 전체를 그대로 쓴다(Streamlit Community Cloud도 저장소 전체를 내려받는다).
Day5 원장(d5_start.csv)·Day3 특성표는 그날 아침 공개되므로, 파일이 없으면 화면에서 안내만 한다.
"""
from __future__ import annotations

import io
import json
from datetime import date
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parents[1]
REPO = APP_DIR.parent
DATA = REPO / "data"
CK = DATA / "checkpoints"
RAG_DIR = REPO / "rag"
RAG_CORPUS = RAG_DIR / "corpus"
GOLDSET = RAG_DIR / "goldset_20.csv"
PROMPTS = APP_DIR / "prompts"
SAMPLE_UPLOAD = APP_DIR / "sample_data" / "upload_sample.csv"

DEFAULT_LEDGER = CK / "d5_start.csv"            # Day5 미결 원장(Day5 08:30 공개)
FEATURES_SCORING = CK / "d3_start_scoring.csv"  # 바이어 특성(기준일 2026-09-30, Day3 공개)
FEATURES_PREV = CK / "d3_start_features.csv"    # 직전 기준일(2026-08-31) 특성 — 등급 변화 비교용
FX_DAILY = CK / "fx_krw_daily.csv"              # 최근 300 관측일 원화 환율(FRED H.10 교차)
INVOICE_HISTORY = [CK / "d1_invoices.csv", DATA / "day1" / "d1_invoices.csv"]  # 바이어별 과거 금액(단위 의심 판정)
D4_START = CK / "d4_start_scored.csv"           # (있으면) Day4 시작 파일 — 인수한도·월평균 매출
SCENARIOS = [CK / "d4_scenarios.csv", CK / "scenarios.csv"]   # (있으면) Day4 시나리오 — 없으면 내장 기본값
PARAMS = CK / "d4_params.csv"                   # (있으면) Day4 파라미터(공개 금리 + 회사 가정) — 없으면 내장 기본값

ASOF_DEFAULT = date(2026, 9, 30)


def models_dir() -> Path:
    """모델 폴더: app/models(복사본이 있으면) → 저장소 루트 models/."""
    for p in (APP_DIR / "models", REPO / "models"):
        if (p / "feature_list.json").exists():
            return p
    return REPO / "models"


def read_csv_any(src) -> pd.DataFrame:
    """CSV(경로·업로드 파일·bytes)를 문자열 그대로 읽는다. UTF-8-BOM → UTF-8 → CP949(Excel 한글) 순으로 시도."""
    if hasattr(src, "getvalue"):
        raw = src.getvalue()
    elif isinstance(src, (bytes, bytearray)):
        raw = bytes(src)
    else:
        raw = Path(src).read_bytes()
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc, dtype=str, keep_default_na=False)
        except UnicodeDecodeError as e:  # pragma: no cover - 인코딩별 분기
            last = e
    raise ValueError(f"CSV 인코딩을 읽지 못했습니다: {last}")


def read_csv_typed(path: Path) -> pd.DataFrame:
    """숫자는 숫자로 읽는 일반 읽기(특성표·환율표)."""
    return pd.read_csv(path, encoding="utf-8-sig")


def load_fx() -> pd.DataFrame | None:
    if not FX_DAILY.exists():
        return None
    fx = read_csv_typed(FX_DAILY)
    fx["date"] = pd.to_datetime(fx["date"])
    return fx.sort_values("date").reset_index(drop=True)


def load_history_median() -> pd.Series | None:
    """바이어별 과거 인보이스 금액(USD) 중앙값 — 소수점·단위 오류 탐지 기준."""
    for p in INVOICE_HISTORY:
        if p.exists():
            h = pd.read_csv(p, encoding="utf-8-sig", usecols=["buyer_id", "amount_usd"])
            return h.groupby("buyer_id")["amount_usd"].median()
    return None


def load_invoice_history() -> pd.DataFrame | None:
    for p in INVOICE_HISTORY:
        if p.exists():
            h = pd.read_csv(p, encoding="utf-8-sig", usecols=["buyer_id", "invoice_date", "payment_method", "amount_usd"])
            h["invoice_date"] = pd.to_datetime(h["invoice_date"])
            return h
    return None


def scenarios_path() -> Path | None:
    return next((p for p in SCENARIOS if p.exists()), None)


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def available() -> dict[str, bool]:
    """화면 안내용: 어떤 입력 파일이 지금 저장소에 있나."""
    md = models_dir()
    return {
        "d5_start.csv(Day5 원장)": DEFAULT_LEDGER.exists(),
        "d3_start_scoring.csv(바이어 특성)": FEATURES_SCORING.exists(),
        "models/day3_lgbm(모델)": (md / "day3_lgbm.pkl").exists() or (md / "day3_lgbm.txt").exists(),
        "fx_krw_daily.csv(환율)": FX_DAILY.exists(),
        "rag/corpus(규정)": any(RAG_CORPUS.glob("*.md")),
        "goldset_20.csv(골든셋)": GOLDSET.exists(),
        "d4_start_scored.csv(Day4, 선택)": D4_START.exists(),
    }
