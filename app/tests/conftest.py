"""app/tests 공용 — app/ 를 import 경로에 넣고, Day5 원장이 없으면 해당 테스트를 건너뛴다.

실행(저장소 루트): python -m pytest app/tests -q
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

APP = Path(__file__).resolve().parents[1]
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from core import data_io as IO  # noqa: E402

ASOF = pd.Timestamp("2026-09-30")


@pytest.fixture(scope="session")
def d5_raw():
    if not IO.DEFAULT_LEDGER.exists():
        pytest.skip("data/checkpoints/d5_start.csv 없음(Day5 08:30 공개 전) — tools/build_day5.py로 만든다")
    return IO.read_csv_any(IO.DEFAULT_LEDGER)


@pytest.fixture(scope="session")
def ledger(d5_raw):
    from core import clean as CL
    return CL.clean_ledger(d5_raw, asof=ASOF, fx=IO.load_fx(), hist_median=IO.load_history_median()).df
