# buyers 시트 진단 — 2일차

- 입력: `data/checkpoints/d2_start.xlsx` 시트 `buyers` (150행 × 28열, 1행 = 머리글)
- 방식: 읽기 전용 진단. 값은 고치지 않았다.
- 행 번호는 엑셀 행 번호(머리글 = 1행)다.

## 열별 진단

| 열 | 셀 타입(openpyxl) | 결측 | 표기 종류 | 의심 값 (엑셀 행 · ID) |
|---|---|---|---|---|
| buyer_id | str 150 | 0 | B001–B150 | 중복 0 (dirty_list 8번의 기대와 같음) |
| country_code | str 150 | 0 | ISO3 20종 | 없음. 사전에 나오는 자유표기 `country` 열은 이 시트에 **없다** |
| region | str 150 | 0 | 6종 | 국가와 권역이 1:1이고 흔들림 없음 |
| payment_method | str 150 | 0 | 7종 코드(OA 88 · DA 24 · TT_ADV 12 · LC_SIGHT 10 · TT_SPLIT_30_70 8 · DP 4 · LC_USANCE 4) | 없음 |
| oecd_crc | str 57 · int 93 | 0 (`"-"` 57) | `"-"` · 2–6 | `"-"` = 미분류(USA · DEU · JPN · GBR · NLD · POL). 숫자와 글자가 한 열에 섞여 있음 |
| currency | str 150 | 0 | **9종**: USD 81 · EUR 18 · US$ 15 · usd 14 · JPY 8 · CNY 5 · euro 5 · RMB 2 · yen 2 | 통화 4종을 여러 표기로 씀. `map_ccy` 시트는 비어 있음 |
| ar_balance | int 140 · str 9 · float 1 | 0 | 숫자 · `"7,680"` · `"CNY 317,000"` · `"155,200 CNY"` · `"EUR 143,620"` · `"47.0k"` · 앞뒤 공백 `" 195900 "` · 소수(float) 60187.68 | 글자 셀: 6 B005 · 10 B009 · 16 B015 · 35 B034 · 44 B043 · 84 B083 · 87 B086 · 115 B114 · 142 B141, float 셀: 30 B029. **73 B072 = 8,320,000 euro**: 버킷 합 8,320의 1000배이고, USD 환산 약 9.67M은 한도 10,000의 약 967배 → 단위 의심 |
| ar_current | int 148 · str 2 | 0 | 콤마 들어간 글자 | 77 B076 `"51,970"` · 92 B091 `"7,980"` |
| ar_1_30 | int 148 · str 2 | 0 | 콤마 들어간 글자 | 9 B008 `"6,850"` · 73 B072 `"8,320"` |
| ar_31_60 | int 149 · float 1 | 0 | 숫자 | 30 B029 21007.68 (센트 단위. 다른 행은 정수) |
| ar_61_90 · ar_91p | int 150 | 0 | 숫자 | 없음 (ar_91p > 0인데 max_dpd < 91인 행 0) |
| max_dpd | int 150 | 0 | 0–351 | 없음 (잔액이 0인데 dpd > 0인 행 0) |
| avg_days_late_12m | float 47 · int 92 · None 11 | 11 | 숫자 | 결측 11행은 모두 invoices_12m = 0 (구조적 결측) |
| invoices_12m · late_invoices_12m · dispute_cnt_12m | int 150 | 0 | 숫자 | late > invoices인 행 0 |
| avg_dpd_last3m | 숫자 · None 33 | 33 | 숫자 | 해당 창에 결제기일이 든 건이 없어서로 보이지만 확인 필요 |
| avg_dpd_prev3m | 숫자 · None 42 | 42 | 숫자 | 위와 같음, 확인 필요 |
| current_assets · total_liabilities · revenue | int 132 · None 18 | 18 | 숫자(USD) | 이 18행은 재무 7항목이 **모두** 빈칸 |
| current_liabilities | int 111 · None 39 | 39 | 숫자 | |
| equity | int 116 · None 34 | 34 | 숫자 | **음수 2**: 14 B013 −15,126,000 · 49 B048 −37,662,000 (자본잠식) |
| accounts_receivable | int 111 · None 39 | 39 | 숫자 | |
| operating_income | int 113 · None 37 | 37 | 숫자 | 음수 19 (영업손실. 사전상 허용) |
| credit_limit_usd | int 150 | 0 | 10,000–250,000 | 없음 |
| late_30d | int 150 | 0 | 0 137 · 1 13 | 라벨이므로 특성 계산에 쓰지 않음 |

## 추가 관찰

- 재무 결측(유동자산 · 유동부채 · 총부채 · 자기자본 · 매출 중 하나라도 빈칸)은 47행이다. CRC별로 보면 `-` 10/57 · 2 7/35 · 3 20/40 · 4 3/4 · 5 4/7 · 6 3/7로, 신흥국 쪽 결측 비율이 높다(dirty_list 5번 비고와 같음).
- 잔액과 버킷 합이 다른 행: B072(1000배), B141(`47.0k`는 47,000이고 버킷 합은 47,030이라 k 표기 때문에 30이 빠짐).
- 단위 의심 기준(USD 환산 잔액 > 한도 × 10)에 걸리는 행은 B072 하나다. 2위 B034는 5.8배다.
  - 환산에는 `fx_at_ref` 시트의 2026-08-31 환율을 썼다. JPY는 100엔 단위(856.55원)이고, 비율은 통화 원화값 ÷ USD 원화값(1,368.25)이다.
- TT_ADV 12개사는 잔액이 모두 0이다(정상).

## 근거

- 수치는 이 세션에서 pandas · openpyxl로 원본 바이트를 읽어 계산했다. 진단 코드는 아직 `scripts/`에 파일로 남기지 않았다. 다시 만들려면 `scripts/d1_quality_check.py` 구조를 따라 `scripts/d2_buyers_check.py`로 옮겨야 한다.
- 위 숫자 해석은 진단용 임시 해석이다(콤마 · 공백 · 통화 글자 제거, `k` = ×1000). 정제 규칙이 아니다.
