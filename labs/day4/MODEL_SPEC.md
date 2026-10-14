# MODEL_SPEC — 바이어별 여신 한도 LP(1쪽)
기준일 2026-09-30 · 단위 USD · 바이어 150(d4_start_scored.csv) · 정책 숫자 d4_params.csv(excel_name으로 찾는다)
기호: g = grade(S/A/B/C) · T = terms_days · 부보 = ksure_insured == "Y" · 신용장 = payment_method ∈ {LC_SIGHT, LC_USANCE}
1. 바이어별 미리 계산
 - LGD_i = 신용장이면 LGD_LC, 아니면 LGD · Cov_i = 부보면 Cov, 아니면 0
 - r_i(할인율) = 무보험: TSOFR3M + Spread_g + PD_g × LGD_i / 부보: TSOFR3M + Spread_g + Prem_g × 365 ÷ T + PD_g × LGD_i × (1 − Cov)
 - Need = monthly_sales_usd × (T + Grace) ÷ 30 · Cap = S: Need, A: Cap_A, B: Cap_B, C: Cap_C_OA
 - Ins = 부보면 ksure_limit_usd, 아니면 0 · Self = Equity_USD × s_g
 - 선적 보류 = bankruptcy_flag == 1 또는 d4_open_inv에서 미결이고 payment_method ∉ {LC_SIGHT, LC_USANCE, TT_ADV}인 인보이스 중 dpd(= 기준일 − due_date) ≥ 30이 1건 이상
 - UB = 0 (payment_method ∈ {LC_SIGHT, LC_USANCE, TT_ADV} 또는 선적 보류), 그 밖에는 MIN(Need, Cap, Ins + Self)
 - LB = strategic_flag == 1이면 MIN(StratMin × current_limit_usd, UB), 아니면 0
 - coef = (UB > 0이고 T > 0)이면 Util × (GM × 365 ÷ T − r_i), 아니면 0
 - elc = Util × PD_g × LGD_i × (1 − Cov_i)
2. 결정변수: L_i(연속, LB_i ≤ L_i ≤ UB_i)
3. 목적: 최대화 Σ coef_i × L_i (연 기대이익 지표)
4. 제약
 ① total_cap: Σ L_i ≤ TotalCap = ROUND(TotalCapShare × Σ UB_i, −5)  (10만 단위, .5는 0에서 먼 쪽)
 ② el_budget: Σ elc_i × L_i ≤ Equity_USD × Alpha
 ③ ctry_{국가}: 국가별 Σ L_i ≤ 국가율 × TotalCap — oecd_crc 비었거나 0–2 → CtryCap_02 · 3 → CtryCap_3 · 4–5 → CtryCap_45 · 6–7 → CtryCap_67
 ④ b_share: Σ(B등급) L_i ≤ ShareCap_B × TotalCap
5. 출력: limits_proposed.xlsx — limits(buyer_id, grade, country_code, ub, lb, coef, elc, current_limit, L, change_pct, approval) · constraints(name, lhs, rhs, slack, shadow_price) · summary(status, objective, total_cap, solver_gap)
   approval = 현행 대비 30% 이상 감액이면 "사람 승인 필요"
