"""4일차 테스트 공통 옵션 — 아무것도 주지 않으면 '기준' 값(원본 정책 값 · 기준 규칙 파일 · scripts/의 엔진 · workbench/day4/outputs/의 결과)을 검사한다.

정책 실험(실험 카드) · 버그 카드의 결과도 같은 테스트로 볼 수 있다 — 정책 값 파일과 결과 파일의 경로를 준다:
    uv run pytest labs/day4/tests/test_limits_props.py --params workbench/day4/data/d4_params.csv --result workbench/day4/outputs/exp/limits_proposed.xlsx
스트레스 시뮬레이터 결과는 --stress 로 바꿔 준다(내 시나리오 U1을 더한 결과 · 내가 만든 시뮬레이터):
    uv run pytest labs/day4/tests/test_stress_props.py --stress workbench/day4/outputs/stress_results.csv
경보 엔진 테스트는 엔진 파일과 규칙 파일을 바꿔 줄 수 있다(내 규칙을 더한 판 · 참고 엔진 확인):
    uv run pytest labs/day4/tests/test_ews_props.py --rules workbench/day4/rules/alert_rules.yml --engine labs/day4/ews_example.py
경로는 저장소 맨 위 폴더 기준이다.
"""


def pytest_addoption(parser):
    parser.addoption("--params", default=None, help="정책 값 CSV (기본: data/checkpoints/d4_params.csv)")
    parser.addoption("--result", default=None, help="한도 엔진 결과 xlsx (기본: workbench/day4/outputs/limits_proposed.xlsx)")
    parser.addoption("--stress", default=None, help="스트레스 결과 CSV (기본: workbench/day4/outputs/stress_results.csv)")
    parser.addoption("--rules", default=None, help="경보 규칙 YAML (기본: labs/day4/alert_rules.yml)")
    parser.addoption("--engine", default=None, help="경보 엔진 파이썬 파일 (기본: scripts/ews.py)")
