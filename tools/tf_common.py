"""공용 유틸: 경로·설정·난수 스트림·환율·파일 쓰기.

tools/ 아래 모든 스크립트가 이 모듈을 import 한다(네트워크 호출 없음).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
DATA = REPO / "data"
RAW = DATA / "raw"
EXTERNAL = DATA / "external"
CHECKPOINTS = DATA / "checkpoints"

# 난수 스트림 이름 — 순서를 바꾸지 말 것(새 스트림은 맨 뒤에만 추가). 테이블별로 독립 → 한 테이블을 고쳐도 다른 테이블 난수는 그대로.
STREAM_NAMES = [
    "buyers", "names", "payment", "volume", "amounts", "late", "default",
    "financials", "news", "events", "scenarios", "bonds", "dirt_d1", "dirt_d2", "misc",
]

XLSX_CREATED = dt.datetime(2026, 10, 1, 0, 0, 0)  # xlsx 메타데이터 고정 → 같은 입력이면 같은 해시


def load_config(path: str | Path | None = None) -> dict:
    path = Path(path) if path else TOOLS / "config.yaml"
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_path"] = str(path)
    cfg["_sha256"] = sha256_file(path)
    return cfg


def make_streams(seed: int) -> dict[str, np.random.Generator]:
    root = np.random.Generator(np.random.PCG64(seed))
    children = root.spawn(len(STREAM_NAMES))
    return dict(zip(STREAM_NAMES, children))


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ts(x) -> pd.Timestamp:
    return pd.Timestamp(x)


# ---------------------------------------------------------------- 환율
def load_fx(cfg: dict) -> pd.DataFrame:
    """FRED 캐시 4종 → 달력일 환율표(원화 교차환율 포함).

    반환 컬럼: date, usd_krw, eur_krw, cny_krw, jpy100_krw, eurusd, usdcny, usdjpy, is_ffill, obs_date
    - 주말·미국 휴일·미공표일은 직전 관측일 값으로 채우고 is_ffill=1, obs_date = 실제 관측일
    """
    ext = cfg["external"]
    frames = []
    for sid, fname in ext["fred_series"].items():
        p = EXTERNAL / fname
        if not p.exists():
            raise FileNotFoundError(
                f"외부 캐시 없음: {p} — 먼저 `python tools/fetch_external.py fred` 실행")
        df = pd.read_csv(p)
        df.columns = ["date", sid]
        df["date"] = pd.to_datetime(df["date"])
        df[sid] = pd.to_numeric(df[sid], errors="coerce")  # 휴일 공란 → NaN
        frames.append(df.set_index("date"))
    raw = pd.concat(frames, axis=1).sort_index()
    raw = raw.dropna(how="any")  # 4개 시리즈가 모두 있는 날만 '관측일'
    start = ts(ext["fx_calendar_start"])
    end = ts(cfg["meta"]["end_date"])
    cal = pd.DataFrame(index=pd.date_range(start, end, freq="D"))
    cal.index.name = "date"
    obs = raw.loc[(raw.index >= start) & (raw.index <= end)].copy()
    obs["obs_date"] = obs.index
    cal = cal.join(obs)
    cal["is_ffill"] = cal["DEXKOUS"].isna().astype(int)
    cal = cal.ffill()
    if cal["DEXKOUS"].isna().any():
        raise ValueError("환율 달력 앞부분에 관측값이 없음 — fx_calendar_start 확인")
    out = pd.DataFrame(index=cal.index)
    out["usd_krw"] = cal["DEXKOUS"].round(2)
    out["eur_krw"] = (cal["DEXKOUS"] * cal["DEXUSEU"]).round(2)
    out["cny_krw"] = (cal["DEXKOUS"] / cal["DEXCHUS"]).round(2)
    out["jpy100_krw"] = (cal["DEXKOUS"] / cal["DEXJPUS"] * 100).round(2)
    out["eurusd"] = cal["DEXUSEU"]
    out["usdcny"] = cal["DEXCHUS"]
    out["usdjpy"] = cal["DEXJPUS"]
    out["is_ffill"] = cal["is_ffill"].astype(int)
    out["obs_date"] = cal["obs_date"]
    return out.reset_index()


class FX:
    """날짜 → 통화별 환율 조회(달력일 기준, 휴일은 직전 관측일 값)."""

    def __init__(self, fx: pd.DataFrame):
        self.df = fx.set_index("date")
        self.start = self.df.index.min()
        self.end = self.df.index.max()

    def _idx(self, dates) -> pd.DatetimeIndex:
        d = pd.to_datetime(pd.Series(dates)).clip(lower=self.start, upper=self.end)
        return pd.DatetimeIndex(d)

    def krw_per_unit(self, dates, ccy) -> np.ndarray:
        """통화 1단위당 원화(JPY도 1엔 기준). ccy는 스칼라 또는 배열."""
        idx = self._idx(dates)
        sub = self.df.loc[idx]
        ccy = np.broadcast_to(np.asarray(ccy, dtype=object), (len(idx),))
        out = np.full(len(idx), np.nan)
        for c, col, div in [("USD", "usd_krw", 1), ("EUR", "eur_krw", 1),
                            ("CNY", "cny_krw", 1), ("JPY", "jpy100_krw", 100)]:
            m = ccy == c
            out[m] = sub[col].to_numpy()[m] / div
        return out

    def usd_per_unit(self, dates, ccy) -> np.ndarray:
        idx = self._idx(dates)
        return self.krw_per_unit(dates, ccy) / self.df.loc[idx, "usd_krw"].to_numpy()


# ---------------------------------------------------------------- 파일 쓰기
def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """UTF-8-BOM CSV(Excel 한글 깨짐 방지)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")
    return path


def _excel_width(series: pd.Series, header: str) -> float:
    def w(s: str) -> float:
        # 한글·기호는 폭 2, ASCII는 1로 근사
        return sum(2 if ord(ch) > 0x2E7F else 1 for ch in s)
    sample = series.dropna().astype(str).head(400)
    m = max([w(header)] + [w(s) for s in sample]) if len(sample) else w(header)
    return float(min(max(m + 2, 8), 60))


def write_xlsx(sheets: dict[str, pd.DataFrame], path: str | Path,
               notes: dict[str, list[str]] | None = None,
               freeze: bool = True) -> Path:
    """여러 시트를 xlsx로 저장(머리글 굵게·틀 고정·자동 필터·열 너비). 메타데이터 고정으로 재현 가능.

    notes: {시트명: [설명 줄, ...]} — 표 위에 설명을 넣고 싶을 때(표는 그 아래부터 시작)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    notes = notes or {}
    with pd.ExcelWriter(path, engine="xlsxwriter", date_format="yyyy-mm-dd", datetime_format="yyyy-mm-dd",
                        engine_kwargs={"options": {"strings_to_numbers": False,
                                                   "strings_to_formulas": False,
                                                   "strings_to_urls": False}}) as xw:
        book = xw.book
        book.set_properties({"created": XLSX_CREATED, "author": "tradefin-ai-2026 tools",
                             "title": path.stem,
                             "comments": "(가상) 한빛정밀(주) 교육용 합성 데이터 — 실존 기업과 무관"})
        hdr = book.add_format({"bold": True, "bg_color": "#ECEAE3", "border": 1,
                               "font_name": "Malgun Gothic"})
        note_fmt = book.add_format({"italic": True, "font_color": "#5B6475"})
        for name, df in sheets.items():
            start = len(notes.get(name, []))
            df.to_excel(xw, sheet_name=name, index=False, startrow=start)
            ws = xw.sheets[name]
            for i, line in enumerate(notes.get(name, [])):
                ws.write(i, 0, line, note_fmt)
            for j, col in enumerate(df.columns):
                ws.write(start, j, col, hdr)
                ws.set_column(j, j, _excel_width(df[col], str(col)))
            if freeze and len(df.columns):
                ws.freeze_panes(start + 1, 0)
                if len(df):
                    ws.autofilter(start, 0, start + len(df), len(df.columns) - 1)
    return path


README_INDEX_MARKER = "## 0. 색인"


def keep_readme_index(path: str | Path, new_text: str, marker: str = README_INDEX_MARKER) -> str:
    """정답 README(instructor/dayN/answers/README.md)를 다시 쓸 때 강사 키트가 손으로 넣은 '## 0. 색인' 절을 보존한다.

    기존 파일에 marker로 시작하는 2단계 제목이 있으면 그 절(다음 '## ' 제목 앞까지)을 new_text의
    첫 '## ' 제목 바로 앞(= 제목·머리말 블록 다음)에 끼워 넣은 본문을 돌려준다. 파일이 없거나 절이 없으면,
    또는 new_text에 이미 같은 절이 있으면 new_text를 그대로 돌려준다. 호출 쪽은 돌려받은 본문을 쓴다."""
    p = Path(path)
    if marker in new_text or not p.exists():
        return new_text
    old_lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, line in enumerate(old_lines) if line.startswith(marker)), None)
    if start is None:
        return new_text
    end = next((i for i in range(start + 1, len(old_lines)) if old_lines[i].startswith("## ")), len(old_lines))
    section = "".join(old_lines[start:end]).rstrip("\n") + "\n\n"
    new_lines = new_text.splitlines(keepends=True)
    ins = next((i for i, line in enumerate(new_lines) if line.startswith("## ")), len(new_lines))
    head = "".join(new_lines[:ins])
    if head and not head.endswith("\n\n"):
        head = head.rstrip("\n") + "\n\n"
    return head + section + "".join(new_lines[ins:])


def write_json(obj, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    return path


# ---------------------------------------------------------------- 텍스트 정규화
def excel_upper_trim(s: str) -> str:
    """Excel UPPER(TRIM(x))와 같은 결과(앞뒤 공백 제거 + 연속 공백 1칸 + 대문자)."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    return re.sub(r" +", " ", str(s).strip(" ")).upper()


def paydex_from_days(days: np.ndarray, key: list[list[float]]) -> np.ndarray:
    """금액가중 평균 지연일 → PAYDEX형 점수(D&B 키 선형 보간, 120일 초과는 20 고정)."""
    xs = np.array([k[0] for k in key], dtype=float)
    ys = np.array([k[1] for k in key], dtype=float)
    return np.interp(np.clip(days, 0, None), xs, ys)
