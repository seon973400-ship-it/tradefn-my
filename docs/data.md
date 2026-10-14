---
title: 데이터
---

<div class="tf-hero" markdown>
<span class="tf-eyebrow">시작하기 · 6일 동안 쓰는 데이터</span>

# 데이터

6일 동안 **같은 가상 회사의 데이터**로 실습합니다. 회사 이름도 숫자도 과정을 위해 만든 **합성 데이터**이며 실존 기업과 무관합니다. 어제의 결과 파일이 오늘의 입력이 되고, 열의 정확한 뜻은 **데이터 사전**(`data_dictionary.xlsx`)에 있습니다.

<div class="tf-buttons" markdown>
[파일 체인](#chain){ .md-button .md-button--primary }
[일차별 파일 받기](#files){ .md-button }
[바이어 컬럼](#buyers){ .md-button }
[결제방식 코드](#codes){ .md-button }
</div>
</div>

## 시나리오 — (가상) 한빛정밀(주) {#scenario}

<div class="tf-facts" markdown>

회사
:   대전 소재 정밀부품 · 산업용 센서 수출 중소기업(가상)

규모
:   바이어 **150**곳 · **20**개국 · **36**개월 · 인보이스 약 **5,000**건

결제조건
:   송금(선수금 · 사후송금) 약 70%, 신용장 6~8%, 나머지 D/A · D/P

고민
:   미수금이 늘고, 연체를 늦게 안다

기준일
:   1일차 바이어 스냅샷 **2026-09-30**

</div>

결제조건 비중은 실제 한국 수출과 닮게 만들었습니다 — 한국 수출 결제는 송금 70.7%, 신용장 약 6%입니다(2024, 업계 집계 · 원통계 미표기).
무역금융 판단은 여러분이 전문가입니다. 이 시나리오는 방법을 연습하는 무대입니다.

## 파일 체인 — 1일차 → 6일차 {#chain}

6일 동안 **어제의 결과 파일이 오늘의 입력**이 됩니다. 실습을 다 못 끝냈거나 결석했어도, 그날 아침 `uv run python tools/get_day_files.py N`으로 받는 **시작 파일**(강사 기준본)로 그날 실습에 바로 합류합니다.

| 일차 | 시작 파일(강사 공개) | 내가 만들어 내는 것(제출) | 다음 날 시작 파일 |
|---|---|---|---|
| [1일차](day1/index.md) · 10/14(수) | 내 저장소의 `data/day1/` — `d1_buyers_raw.xlsx`/`.csv`(153행) · 보고서 발췌 `reports/` · `real_buyers_ratios.csv` · `d1_invoices.csv`(5,033행) | 내 저장소 `workbench/day1/outputs/`의 결과 파일 9종 — 변수 정의서 · EDA 노트북 · 현안 정의서 등(push) | `d2_start.xlsx` |
| [2일차](day2/index.md) · 10/15(목) | `d2_start.xlsx` · `fx_krw_daily.csv` · `d2_news.csv` · 15:35 `d2_news_answer.csv` — `uv run python tools/get_day_files.py 2` | 내 저장소 `workbench/day2/outputs/d2_end_features.csv`(150행) · 정제 표 · 품질 보고서 · 뉴스 점수 · 평가 · 이슈 1개 · PR 2개(push) | `d3_start_features.csv` + `d3_start_scoring.csv` |
| [3일차](day3/index.md) · 10/16(금) | `d3_start_features.csv`(300행) · `d3_start_scoring.csv`(150행) · `d3_features_panel.csv`(패널 4,017행) · 오늘의 규칙 `workbench/day3/rules/d3_rules.md` — `uv run python tools/get_day_files.py 3` · 18:00 강사 기준 `d3_end_scored.csv` | 내 저장소 `workbench/day3/outputs/d3_end_scored.csv`(150행 · 6열) · 데이터 카드 · 평가 · 임계값 기록 · 근거 메모 · 환율 구간 · `workbench/day3/notes.md` · PR 1개(push) | `d4_start_scored.csv`(월요일 — 모두 같은 3일차 기준 등급 파일) |
| [4일차](day4/index.md) · 10/19(월) | `d4_start_scored.csv`(150행) · `d4_params.csv`(정책 숫자 65행) · `d4_scenarios.csv` · `d4_open_inv.csv`(300건) · 한도 워크북 `d4_limit_model.xlsx` · 15:00 `d4_report_input.json` — `uv run python tools/get_day_files.py 4` · 18:00 강사 정답 요약 `d4_end_limits.xlsx` | 내 저장소 `workbench/day4/outputs/`의 한도안 `limits_proposed.xlsx` · `model_card.md` · 스트레스 표 · 보고 파일 · `number_trace.csv` · `redteam.md` + `workbench/day4/experiments.md` · 경보 워크플로와 자동 이슈 · PR 3개(push) | `d5_start.csv` |
| [5일차](day5/index.md) · 10/20(화) | `d5_start.csv`(300행 이하) — `uv run python tools/get_day_files.py 5` · 규정 PDF · 골든셋 · 질문 목록 · 평가 시트(`rag/`) · 요구사항 카드 · 톤 표(`labs/day5/`)는 이미 저장소에 있음 | 내 저장소 `workbench/day5/outputs/`의 `baseline.md` · `rag_report.md` · `rag_eval.csv` · `f1_at_k.png` · `scripts/rag_lab/` · 환율 타일 · 톤 표 · `receivables.db`(커밋 제외) + `links.md` · 배포한 앱 주소 · PR 3개(push) · 21:00 `plan_draft__T{조}-{번호}.docx`(비공개 폼) | `d6_crisis_pack.xlsx` |
| [6일차](day6/index.md) · 10/21(수) | `d6_crisis_pack.xlsx` · 위기 카드 · 양식(SOP · ROI · 기획서) | 팀: 저장소 `tradefin-kit-T{조}` **`v1.0` 릴리스** / 개인: `d6_plan__T{조}-{번호}.docx` · `d6_roi__T{조}-{번호}.xlsx` · 사후 진단(비공개 폼) | – |

- **제출 파일 이름 규칙**: `{파일}__T{조}-{번호}.{확장자}` — 밑줄 두 개, 대문자 T, 번호는 두 자리(예: 2조 7번 → `plan_draft__T2-07.docx` — 1–5일차 실습 결과는 내 저장소에 push · PR하므로 이 이름을 쓰지 않고, 비공개 폼으로 내는 기획서만 이 이름을 씁니다).
- 각 일차의 받을 파일은 그날 쪽의 **파일 받기** 카드에 있습니다. 정답이 담긴 비교 기준 파일은 정한 시각 전까지 잠금 표시(<span class="tf-chip tf-chip--lock">15:35 공개</span>)로 보이고, 시각이 지나면 저절로 받기 단추로 바뀝니다 → [자료는 언제 열리나](course.md#release).

### 시작 파일의 주요 열 {#checkpoint-columns}

| 파일 | 행 | 주요 열 |
|---|---|---|
| `d2_start.xlsx` | `buyers` 150 · `buyer_features_raw` 300 · `invoices_raw` 1,902 | 시트 `buyers`(실습 A의 입력 — 150곳 × 28열, 기준일 2026-08-31, 일부러 지저분한 표기 · 결측 · 단위 오류 포함) · `buyer_features_raw`(150개사 × 기준일 2개: `buyer_id` · `ref_date` · 결제방식 · 누적 거래 횟수 · 연체·분쟁 지표 · 미결 잔액 · 재무비율 4종 · `pay_score` · `late_30d`) · `fx_at_ref`(기준일 환율) · `invoices_raw`(더 하기) · `dirty_list` · `map_ccy` · `map_country` · `dictionary`(열 설명) |
| `d2_news.csv` | 300 | `news_id` · `buyer_id` · `ref_window` · `date` · `lang` · `headline` · `body_short` · `source_type`(합성 · 과정 제작) — 실습 B는 앞 100행 |
| `d2_end_features.csv` | 150 · 32열 | 내가 만드는 융합 특성표(`workbench/day2/outputs/`) — 정제한 특성 25열(결측 표시 `fin_missing` · `neg_equity` 포함) + `overdue_usd` · `cum_dpd_days` + 뉴스 지표(`news_cnt_30d` · `news_sent_0_10_30d` · `news_sent_min_30d` · `news_risk_30d` · `no_news_flag`), `buyer_id` 첫 열 · `late_30d` 끝 열 |
| `d3_start_features.csv` · `d3_start_scoring.csv` | 300 · 150 | 2일차 특성(강사본) + `sample_weight`(불균형 보정) · `split_suggested`(바이어 단위 70/30 분할 제안 — 패널은 시간 분할) / 예측 대상은 기준일 2026-09-30, 레이블 없음 |
| `d3_end_scored.csv` | 150 | 내가 만드는 파일은 6열 — `buyer_id` · `ref_date` · `pd_30d`(30일 이내 연체 확률) · `grade`(S/A/B/C) · `threshold_used` · `model_version`. 18:00에 열리는 강사 기준 파일(17열)은 여기에 `pred_late` · `grade_rule` · `rank_pct` · 상위 사유 열이 더 있다 |
| `d4_start_scored.csv` | 150 · 35열 | 3일차 기준 등급 파일(`pd_30d` · `grade` · `grade_quantile` · 상위 사유 · `threshold_used`) + 한도 계산 열(`terms_days` · `ksure_insured` · `ksure_limit_usd` · `monthly_sales_usd` · `open_ar_usd` · `overdue_amount_usd` · `current_limit_usd` · `oecd_crc`) + 가정 열(`pd_annual_assumed` · `lgd_assumed` · `coverage_ratio`) + 전략 · 신용사건 표시(`strategic_flag` · `bankruptcy_flag`) |
| `d4_params.csv` | 65 | 정책 숫자 표 — `excel_name`(코드가 찾는 이름) · `value`(값, 비율은 소수) · `unit` · `status`(확인 · 계산 · 가정 · 교육용 가정) · `as_of` · `note`. 총액 비율(`TotalCapShare`) · EL 예산(`Alpha`) · 국가 캡(`CtryCap_*`) · 등급별 PD · 가산금리 · 보험료 같은 값이 든다. 금리 · 환율 값은 교육용 기준일의 공개 값을 옮긴 것이고 거래용이 아니다 |
| `d4_scenarios.csv` | 6 | 시나리오 S0 기준 · S1 경미 · S2 중간 · S3 심각 · S4 극단(`pd_multiplier` · `lgd_scenario` · `usd_krw_level` · `rate_shock_bp`)과 2026년 실제 원/달러 경로 참고 행(`row_type`이 `reference`). PD 배수 · LGD는 교육용 가정 |
| `d4_open_inv.csv` | 300 · 14열 | 기준일 미결 인보이스 — `invoice_id` · `buyer_id` · `payment_method` · `ksure_insured` · `due_date` · `amount_usd` · `paid` · `terms_change_date` · `bank_change_request`(원장 기준 0건이 정상 — 경보 규칙의 입력) |
| `d4_report_input.json` | – | 15:00에 열림 — 보고서 지표 JSON(포트폴리오 · 한도 · 시나리오 · 경보 · 주의 바이어 5곳 · 절감액 · 기준 · 승인 주체). 문장 속 숫자를 대조하는 기준 |
| `d4_end_limits.xlsx` | – | 18:00에 열리는 강사 정답 요약 — 시트 `limits`(바이어별 제안 한도) · `portfolio` · `constraints` · `scenario_results` · `early_warning` · `report_input` · `report_draft` 등. `get_day_files.py 4` 또는 4일차 '파일 받기'에서 받는다 |
| `d5_start.csv` | 300 이하 · 29열 | 2026-09-30 미결 인보이스: `invoice_id` · `buyer_id` · 금액 · 결제기일 · `dpd` · 독촉 단계 · 사고통지 기한 · `grade` · `pd_30d` · 한도 · 경보 표시(메일 주소는 가상) |
| `d6_crisis_pack.xlsx` | – | 시트 `cards`(카드별 영향 바이어·시나리오) · `buyer_changes`(결제조건·단가·PD 배수·송금 지연 변경) 등 |

열의 정확한 이름 · 뜻 · 단위는 **데이터 사전**(`data_dictionary.xlsx`)의 `columns` 시트에 있습니다.

## 일차별 파일 받기 {#files}

1일차 파일은 내 저장소의 `data/day1/`에 **이미 들어 있습니다**. 저장소 없이 채팅 경로로 하는 분과 2–6일차 파일은 각 일차 쪽의 **파일 받기**에서 받습니다(ZIP 한 번에 · 파일별).

<div class="grid cards tf-cols-3" markdown>

-   **1일차** · 바이어 스냅샷 · 인보이스 · 보고서 발췌

    [1일차 파일 받기](day1/index.md#files)

-   **2일차** · `d2_start.xlsx` · 뉴스 · 환율

    [2일차 파일 받기](day2/index.md#files)

-   **3일차** · 특성 · 점수 대상 · 패널

    [3일차 파일 받기](day3/index.md#files)

-   **4일차** · 등급 · 정책 숫자 · 시나리오 · 미결

    [4일차 파일 받기](day4/index.md#files)

-   **5일차** · 미결 인보이스 · 규정 · 골든셋

    [5일차 파일 받기](day5/index.md#files)

-   **6일차** · 위기 카드 · 데이터 팩 · 양식

    [6일차 파일 받기](day6/index.md#files)

</div>

모든 컬럼의 뜻 · 단위는 **데이터 사전**(`data_dictionary.xlsx`)의 `columns` 시트에 있습니다.

## 바이어 스냅샷 `d1_buyers_raw` 핵심 컬럼 {#buyers}

153행 · 23열 · 시트 `buyers`(안내는 `readme` 시트). ★는 1일차 실습 B에서 직접 쓰는 컬럼입니다.

!!! warning "원천 입력 오류가 섞여 있습니다"
    실무 대장처럼 담당자가 입력한 그대로의 데이터입니다. **무엇이 이상한지는 1일차 실습 B-1에서 직접 찾습니다** — 오늘은 진단만, 정제는 2일차입니다.

| 컬럼 | 한글명 | 뜻 | 단위 |
|---|---|---|---|
| `buyer_id` ★ | 바이어 ID | B001~B150 형식의 가명 식별자 | – |
| `buyer_name` | 바이어명(가상) | 가상 상호(실존 기업과 무관) | – |
| `country` | 국가명(원천 표기) | 담당자가 입력한 국가명 그대로 | – |
| `country_code` ★ | 국가코드 | ISO 3166-1 alpha-3 세 글자 코드(예: USA, DEU) | – |
| `region` ★ | 권역 | 북미·중남미 / 서유럽 / 중동부유럽 / 동아시아 / 동남아·남아 / 중동·아프리카 | – |
| `industry` | 업종 | `oem_manufacturer`(완제품 제조사) · `distributor`(유통·대리점) · `retail`(소매) · `epc_contractor`(EPC·설치 시공) · `utility`(유틸리티) · `public_agency`(공공기관) | – |
| `segment` | 고객 구분 | private(민간) / public(공공) | – |
| `buyer_type` | 공공 유형 | PRIVATE / UN(UN 계열 기구) / MDB(다자개발은행 재원 사업) / EM_GOV(신흥국 정부) / DM_GOV(선진국 정부) | – |
| `payment_terms_raw` ★ | 결제조건(원천 표기) | 담당자가 입력한 결제조건 그대로. 실습 B-1 · 03에서 [코드 7종](#codes)으로 나눈다 | – |
| `ar_balance` | 매출채권 잔액 | 기준일 미결제 잔액(청구 통화 기준) | 통화 |
| `ar_currency` | 잔액 통화(원천 표기) | 청구 통화 | – |
| `max_dpd_days` ★ | 연체일수(최악) | 기준일에 남은 미결 인보이스 중 결제기일을 가장 오래 넘긴 날수(0 = 연체 없음) | 일 |
| `overdue_amount` | 미납 결제 금액 | 결제기일이 지난 미결 잔액(청구 통화 기준) | 통화 |
| `pay_score` | 바이어 신용도 점수 | 결제 이력으로 만든 1~100점(PAYDEX형) | 점 |
| `oecd_crc` | 국가위험등급 | OECD 국가위험분류 0~7(높을수록 위험), "-" = 분류 대상 아님(고소득 OECD국) | 등급 |
| `ksure_insured` ★ | K-SURE 부보 여부 | 바이어 단위 단기수출보험 가입 여부 | Y/N |
| `since_date` | 거래 시작일 | 첫 거래일 | 날짜 |
| `fin_summary_text` | 재무 요약문 | 재무 상태를 요약한 영문 1~2문장 | – |
| `revenue_usd_fy2025` | 매출액 | 바이어의 FY2025 매출 | USD |
| `current_ratio_fy2025` | 유동비율 | 유동자산 ÷ 유동부채 | 배 |
| `debt_to_equity_fy2025` | 부채비율 | 총부채 ÷ 자기자본 | 배 |
| `dso_fy2025` | 매출채권회전일(DSO) | 매출채권 ÷ 매출 × 365 | 일 |
| `op_margin_fy2025` | 영업이익률 | 영업이익 ÷ 매출(소수: 0.08 = 8%) | 비율 |

1일차 실습 B-2 · 02의 완성본 엑셀(`d1_pivot_check.xlsx`)에는 이 표에 열 2개가 더 있습니다: `표준코드`(코드표로 찾은 결제방식 — [코드 7종](#codes)) · `연체`(연체일수 > 0이면 1, 아니면 0). 결제방식별로 센 표와 차트가 함께 있어 AI 노트북의 숫자와 견줍니다 → [실습 B-2 · 02](day1/lab-b.md#b2-check).

## 결제방식 코드 7종 {#codes}

| 코드 | 뜻 | 대금 받는 시점 | 위험을 지는 쪽 |
|---|---|---|---|
| `TT_ADV` | 선수금 송금(T/T in advance, cash in advance) | 선적 전 | 수출자 위험은 거의 없음 |
| `TT_SPLIT_30_70` | 분할 송금 — 30% 선수금 + 70% 선적 후 송금 | 30% 선적 전 · 70% 선적 후 | 잔금 70%는 수출자 |
| `OA` | 사후송금(Open Account, T/T after shipment) | 선적 후 30·60·90일 | 수출자 전부 |
| `DA` | 인수인도조건 추심(Documents against Acceptance) | 수입자가 어음을 인수한 뒤 만기 | 수출자(추심은행은 지급을 보증하지 않음) |
| `DP` | 지급인도조건 추심(Documents against Payment) | 대금을 내야 서류를 내줌 | 수출자(안 내면 물품 반송·재판매) |
| `LC_SIGHT` | 일람불 신용장(Sight L/C) | 서류 제시·심사 후 | 개설은행·국가(서류 하자는 수출자) |
| `LC_USANCE` | 기한부 신용장(Usance L/C) | 만기 | 개설은행·국가 |

## 연체 구간(에이징) {#aging}

| 구간 | 뜻 |
|---|---|
| Current | 연체 없음(결제기일 전·당일, 연체일 ≤ 0) |
| 1-30 | 1~30일 연체 |
| 31-60 | 31~60일 연체 |
| 61-90 | 61~90일 연체 |
| 91+ | 91일 이상 연체 |
| 확인필요 | 연체일이 숫자가 아니라 구간을 정할 수 없음 |

구간은 바이어마다 **가장 오래 연체된 인보이스(최악 연체일)** 기준입니다.

## 인보이스 원장 `d1_invoices` {#invoices}

5,033행(36개월) · 시트 `invoices`. 바이어 한 줄 요약이 아니라 인보이스 하나하나가 들어 있습니다.

| 컬럼 | 뜻 |
|---|---|
| `invoice_id` · `buyer_id` · `country_code` | 인보이스 번호 · 바이어 ID · 국가코드 |
| `invoice_date` · `due_date` · `settled_date` | 발행일(= 선적일로 가정) · 결제기일 · 완납일(2026-09-30까지 다 받지 못했으면 빈칸) |
| `payment_method` · `terms_days` | 결제방식 코드 7종 · 선적 후 결제기일까지 날수 |
| `currency` · `amount_ccy` · `amount_usd` | 청구 통화 · 원통화 금액 · 달러 환산 금액 |
| `status` | 2026-09-30 기준 상태: paid(완납) / open(미결) / default(부도 바이어 미회수) / written_off(대손 처리). 데이터 사전의 returned(D/P 서류 반송)는 Day1 원장에 없습니다 |
| `ksure_insured` · `dispute_flag` · `dispute_type` | 보험 가입 여부 · 분쟁 여부 · 분쟁 유형(QUALITY 품질 · QUANTITY 수량 · DOCS 서류 · PRICE 가격, 분쟁이 없으면 빈칸) |

나머지 컬럼(환율·원화 금액·환차손익 등)은 데이터 사전 `columns` 시트를 보세요.

## SEC 추출 비율표 `real_buyers_ratios` {#ratios}

1일차 실습 A-2에서 쓰는 보고서 발췌 4개사의 재무 원값과 4대 비율을 미국 SEC의 XBRL 공시 데이터(companyfacts API)에서 뽑은 표입니다(9행: 발췌와 같은 기간 + 비교 기간).

| 컬럼 | 뜻 |
|---|---|
| `company` · `form` · `fiscal_period_end` · `row_role` | 회사 · 공시 종류 · 기준일 · 그 행의 용도(발췌와 같은 기간인지 등) |
| `current_assets` … `operating_income` | 유동자산·유동부채·총부채·자기자본·매출채권·매출·영업이익 — 모두 **달러 원 단위**(발췌 재무표는 천 달러) |
| `current_ratio` · `debt_to_equity` · `dso_days` · `op_margin_pct` | 유동비율 · 부채비율(자본잠식이면 빈칸, `negative_equity_flag` = 1) · DSO(일) · 영업이익률(%) |
| `xbrl_tags_used` · `data_note` · `filing_url` | 어떤 계정 태그에서 뽑았나 · 주의 사항 · 원문 공시 주소 |
| `going_concern_flag` · `later_event` … | 이후 경과 — **실습이 끝난 뒤** 봅니다 |

## 보고서 발췌 {#reports}

| 파일 | 원문 | 단위 |
|---|---|---|
| `halden_fictional_annual_report.md` | **가상** 연차보고서(강사 창작, FY2026) — SEC 공시 아님 | 천 파운드 |
| `irobot.md` | [iRobot Form 10-K FY2024](https://www.sec.gov/Archives/edgar/data/1159167/000115916725000011/irbt-20241228.htm) (2025-03-12 접수) | 천 달러 |
| `plug_power.md` | [PART A 10-Q 2023년 3분기](https://www.sec.gov/Archives/edgar/data/1093691/000155837023018601/plug-20230930x10q.htm) · [PART B 10-K FY2023](https://www.sec.gov/Archives/edgar/data/1093691/000155837024002178/plug-20231231x10k.htm) · [PART C 10-K FY2024](https://www.sec.gov/Archives/edgar/data/1093691/000155837025002049/plug-20241231x10k.htm) | 천 달러 |
| `wolfspeed.md` | [Wolfspeed Form 10-Q (2025-03-30 분기)](https://www.sec.gov/Archives/edgar/data/895419/000089541925000071/wolf-20250330.htm) | 백만 달러 |
| `big_lots.md` | [Big Lots Form 10-Q (2024-05-04 분기)](https://www.sec.gov/Archives/edgar/data/768835/000076883524000049/big-20240504.htm) | 천 달러 |
| `gorman_note.md` | D&B 샘플 보고서(가상 기업) **링크와 읽기 안내만** | 달러 |

SEC 발췌는 영어 원문을 고치지 않았고(둥근 따옴표만 곧은 따옴표로 바꿈), `[E1]` 같은 번호와 한국어 소제목은 편집자가 붙인 것입니다.

## 라이선스와 이용 조건 {#license}

라이선스 전문은 과정 저장소 맨 위 폴더의 `LICENSE`(코드 · MIT) · `LICENSE-DATA.md`(데이터·문서 · CC BY 4.0과 제3자 자료의 이용 조건)에, 제3자 자료의 표기는 `NOTICE.md`에 있습니다(© 2026 Taegu Han).

| 대상 | 조건 |
|---|---|
| (가상) 한빛정밀 합성 데이터 · Halden 가상 보고서 · 이 사이트의 글 | **CC BY 4.0** — 저작자를 밝히면 자유롭게 쓸 수 있습니다 |
| 실습 코드(노트북·도구) | MIT |
| SEC 공시 발췌(iRobot · Plug Power · Wolfspeed · Big Lots) | 미국 SEC EDGAR에 제출된 **공개 공시를 교육 목적으로 일부 발췌**한 것입니다. 원문의 저작권과 책임은 각 회사에 있고, 원문 전체는 위 링크에서 봅니다 |
| SEC 비율표 | SEC XBRL companyfacts API(data.sec.gov)에서 2026-10-01에 추출·계산 |
| D&B Gorman 샘플 | **링크만** 제공합니다. PDF에 D&B 저작권 표시가 있으므로 저장소·공유 드라이브·단체방에 올리지 않고 각자 링크에서 받아 개인 실습에만 씁니다 |
| 환율(데이터 안의 원화 환산) | 미국 연준 FRED H.10 기준 교차환율 — 한국은행 매매기준율과 소폭(약 ±1%) 다를 수 있습니다 |
| 글꼴(차트·노트북의 한글) | NanumGothic — SIL Open Font License 1.1 |

이 사이트의 어떤 자료도 투자·여신 판단 자료가 아닙니다.

### 과정이 끝난 뒤 — 원천 데이터와 생성기 {#after}

합성 데이터의 원천(`data/raw/`)과 과정 데이터를 만든 생성 코드는 과정이 끝나는 **10/21(수) 19:00에 자동으로 공개**됩니다. 그때 아래 카드가 받기 단추로 바뀝니다(1–3분 뒤 새로 고침).

--8<-- "docs/_snippets/after/files_all_root_cards.md"

## 데이터 위생 {#hygiene}

!!! warning "AI 대화창은 외부 채널입니다"

    과정 데이터는 전부 가상이거나 공개 공시입니다. 회사 실데이터를 쓰려면 [데이터 위생 5원칙](setup.md#hygiene)과 [익명화 체크리스트](setup.md#byod)를 먼저 확인하세요.
