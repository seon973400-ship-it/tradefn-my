"""환경 점검용 한 줄 출력 — `uv sync` 뒤에 `uv run python scripts/hello.py` 로 실행합니다."""
import sys

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas를 찾지 못했습니다. 먼저 터미널에서 `uv sync`를 실행하고, `uv run python scripts/hello.py`로 다시 실행하세요.")

print(f"환경 준비 완료 — Python {sys.version.split()[0]} · pandas {pd.__version__}")
