# 3일차 데이터 규칙 (d3_rules.md)

Claude Code는 3일차 작업을 시작할 때 이 파일을 먼저 읽고 따른다. 저장소의 `CLAUDE.md` 규칙도 그대로 지킨다.

## 데이터
- `data/checkpoints/`의 3일차 파일(`d3_start_features.csv` · `d3_features_panel.csv` · `d3_start_scoring.csv`)과 `labs/day3/`의 원본은 읽기만 한다. 고칠 것은 `workbench/day3/data/`의 사본으로 한다.
- 정답 열은 `late_30d`다(1 = 기준일 뒤 30일 안에 '결제기일 + 30일' 선을 넘는 미결 인보이스가 생김, 0 = 아님).
- 모르는 열은 `data/data_dictionary.xlsx`의 columns 시트에서 찾는다.

## 특성에서 빼는 열

| 열 | 이유 |
|---|---|
| `buyer_id` · `ref_date` | 식별자 · 날짜 |
| `late_30d` | 정답 |
| `split_suggested` | 학습 · 시험 분할 표시(메타 열) |
| `sample_weight` | 정답으로 계산한 불균형 보정 가중치(메타 열) — 특성으로 넣으면 누수 |

누수 실험(실습 A-1의 4단계)에서만 `sample_weight`를 일부러 넣고, 끝나면 코드를 원래대로 돌린 뒤 diff로 확인한다.

## 분할 · 재현
- 학습 · 시험은 `split_suggested` 열을 그대로 쓴다. 패널의 `burn_in` 행(2024-01~02)은 학습에서 뺀다. 시험셋은 마지막 성적표라 한 번만 본다.
- 무작위 시드는 `random_state = 42`로 고정한다.
- 결과 파일은 `workbench/day3/outputs/`에 저장한다. 재현 메모(시드 · 패키지 버전 · AUC · t · 비용비 근거)는 `workbench/day3/notes.md`에 쓴다.

## 보고
- 숫자는 코드로 계산한 값만 보고하고, 계산한 코드를 함께 남긴다. 모르면 추측하지 말고 '확인 필요'라고 쓴다.
- 회사 실데이터 · 실명은 파일 · 프롬프트 · 커밋 어디에도 넣지 않는다.
