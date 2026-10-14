# data/external — 외부 공개 데이터 캐시

생성기(`tools/generate_data.py`)는 네트워크를 쓰지 않고 이 폴더의 캐시만 읽는다. 캐시를 새로 받으려면 `python tools/fetch_external.py fred`를 실행한다(수집 기록은 `_fetch_log.csv`).

## 1. 들어 있는 파일

| 파일 | FRED 시리즈 | 단위 | 기간(관측) |
|---|---|---|---|
| `fred_dexkous.csv` | DEXKOUS — South Korean Won to U.S. Dollar Spot Exchange Rate | 1달러당 원 | 2023-09-01 ~ 2026-09-25 |
| `fred_dexuseu.csv` | DEXUSEU — U.S. Dollars to Euro Spot Exchange Rate | 1유로당 달러 | 같음 |
| `fred_dexchus.csv` | DEXCHUS — Chinese Yuan Renminbi to U.S. Dollar Spot Exchange Rate | 1달러당 위안 | 같음 |
| `fred_dexjpus.csv` | DEXJPUS — Japanese Yen to U.S. Dollar Spot Exchange Rate | 1달러당 엔 | 같음 |
| `_fetch_log.csv` | 수집 기록(URL, 조회 시각 KST, 행 수, SHA-256) | | |

- 파일은 FRED가 내려준 CSV를 **그대로** 저장했다(열: `observation_date`, 시리즈 ID). 미국 휴일은 값이 빈칸이다.
- 조회일: 2026-10-01(KST). H.10은 매주 월요일에 지난주 값을 공표하므로, 조회 시점의 마지막 관측일은 **2026-09-25**다. 2026-09-28~30 값은 아직 없다.

## 2. 출처와 이용 조건

- 출처: Board of Governors of the Federal Reserve System (US), *H.10 Foreign Exchange Rates* — retrieved from FRED, Federal Reserve Bank of St. Louis. 시리즈 설명: "Noon buying rates in New York City for cable transfers payable in foreign currencies."
- 이용 조건: 네 시리즈 모두 FRED 시리즈 페이지에 **"Public Domain: Citation Requested"**로 표시돼 있다(2026-10-01 확인). FRED 이용약관(<https://fred.stlouisfed.org/legal/>)에 따라 출처를 밝히고 FRED에서 받았음을 표기한다.
- 인용 예: Board of Governors of the Federal Reserve System (US), South Korean Won to U.S. Dollar Spot Exchange Rate [DEXKOUS], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/DEXKOUS, October 1, 2026.

## 3. 생성기에서 쓰는 방식 (`data/raw/fx_daily_full.csv`)

| 원화 환율 | 계산 |
|---|---|
| `usd_krw` | DEXKOUS |
| `eur_krw` | DEXKOUS × DEXUSEU |
| `cny_krw` | DEXKOUS ÷ DEXCHUS |
| `jpy100_krw` | DEXKOUS ÷ DEXJPUS × 100 (**100엔당** 원 — 1엔이 아님) |

- 달력일 표로 펼치고, 주말·미국 휴일·미공표일(2026-09-26~30)은 직전 관측일 값으로 채운다(`is_ffill=1`, 실제 관측일은 `obs_date`).
- 인보이스 발행일·입금일 환율, 기준일 재평가, 체크포인트의 `fx_at_ref` 시트와 `fx_krw_daily.csv`가 모두 이 값을 쓴다.

## 4. 한국은행 ECOS 매매기준율과의 차이 (수업 소재)

설계 문서의 원/달러 기준은 ECOS 731Y001 매매기준율이다. 이 캐시는 ECOS 인증키를 받기 전이라 FRED 값을 쓴다. 두 출처는 고시 시점과 기준이 달라 값이 조금 다르다.

| 날짜 | ECOS 매매기준율(설계 문서) | FRED DEXKOUS | 차이 |
|---|---|---|---|
| 2026-06-09 | 1,546.5 | 1,529.94 | −1.07% |
| 2026-09-10 | 1,337.9 | 1,345.63 | +0.58% |
| 2026-09-23 | 1,360.0 | 1,366.99 | +0.51% |

`tools/validate_data.py`의 V11이 이 차이가 ±3% 안인지 매번 확인한다. ECOS 키를 확보하면 `fetch_external.py`에 `ecos-fx` 대상을 추가하고 `config.yaml`의 `external.fx_source`를 바꾼다(아직 구현하지 않음).

## 5. 재배포

저장소에 가공 CSV를 함께 둔다(추출 · 가공 CSV + 출처 · 조회일). 의심스러우면 데이터 대신 `fetch_external.py`만 배포하고 각자 받게 한다.
