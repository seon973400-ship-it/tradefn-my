# NOTICE — 제3자 자료와 출처 표기

tradefin-ai-2026 — 생성형 AI 기반 무역 금융 리스크 최적화 과정 실습 저장소
Copyright (c) 2026 Taegu Han

- 코드: MIT License — [`LICENSE`](LICENSE)
- 과정이 만든 데이터·문서((가상) 한빛정밀 합성 데이터, Halden 가상 보고서, 사이트 원고, 실습 템플릿): CC BY 4.0 — [`LICENSE-DATA.md`](LICENSE-DATA.md)

이 저장소는 아래 제3자 자료를 **포함**하거나 **링크로만** 가리킵니다. 제3자 자료에는 이 저장소의 라이선스가 아니라 각 원본의 조건이 적용됩니다.

## 1. 저장소에 포함한 제3자 자료

| 자료 | 위치 | 출처 | 조건 | 조회일 |
|---|---|---|---|---|
| 환율 4종 DEXKOUS · DEXUSEU · DEXCHUS · DEXJPUS | `data/external/fred_*.csv` (합성 데이터의 원화·달러 환산도 이 값으로 계산) | Board of Governors of the Federal Reserve System (US), *H.10 Foreign Exchange Rates*, retrieved from FRED, Federal Reserve Bank of St. Louis | "Public Domain: Citation Requested" · FRED 이용약관 <https://fred.stlouisfed.org/legal/> · 인용 예는 [`data/external/ATTRIBUTION.md`](data/external/ATTRIBUTION.md)·[`data/external/README.md`](data/external/README.md) | 2026-10-01 |
| SEC 공시 발췌 | `data/day1/reports/irobot.md` · `plug_power.md` · `wolfspeed.md` · `big_lots.md` | iRobot Corporation · Plug Power Inc. · Wolfspeed, Inc. · Big Lots, Inc.가 미국 SEC EDGAR에 제출한 Form 10-K · 10-Q | 공개 공시를 교육 목적으로 **일부만** 발췌. 영어 문장은 고치지 않았다(둥근 따옴표만 곧은 따옴표로). 원문의 권리와 책임은 각 회사에 있다. 원문 링크는 각 파일 머리와 [`docs/data.md`](docs/data.md) | 2026-10-01 |
| SEC XBRL 재무 값과 4대 비율 | `data/day1/real_buyers_ratios.csv`·`.xlsx` | SEC companyfacts API(data.sec.gov) — 위 회사들의 공시 값 | 공개 공시 값을 추출해 계산(파일의 `filing_url` 열이 원문) | 2026-10-01 |
| 국가위험등급 | 합성 데이터의 `oecd_crc` 열 | OECD 국가위험분류(Country Risk Classification, 2026-06-26 기준) | 나라마다 등급 값만 옮겨 적음. "-" = 분류 대상 아님(고소득 OECD국) | — |
| 글꼴 NanumGothic | `tools/fonts/` | Copyright (c) 2010, NHN Corporation · Google Fonts 저장소에서 받음 | SIL Open Font License 1.1 — [`tools/fonts/OFL.txt`](tools/fonts/OFL.txt) | 2026-10-01 |

## 2. 링크로만 가리키는 자료(저장소에 없음)

- **D&B 샘플 신용보고서**(가상 기업 "Gorman Manufacturing Company, Inc.") — [`data/day1/reports/gorman_note.md`](data/day1/reports/gorman_note.md)의 링크에서 각자 받습니다. PDF에 D&B 저작권 표시가 있어 이 저장소·공유 드라이브·단체방에 다시 올리지 않습니다.
- **슬라이드·사이트가 인용한 보고서·기사·통계** — 원문 링크와 확인일은 사이트의 [레퍼런스](docs/references.md) 페이지에 있습니다.

## 3. 아직 넣지 않은 외부 데이터

UCI 파산 데이터(대만·폴란드)·ECOS·GDELT·K-SURE 자료 등은 아직 받지 않았습니다([`data/external/ATTRIBUTION.md`](data/external/ATTRIBUTION.md)). 받으면 출처·라이선스·DOI·조회일을 `ATTRIBUTION.md`와 이 파일에 한 줄씩 더합니다.

## 4. 빌드·실행 도구

과정 사이트는 MkDocs와 Material for MkDocs로 만들고, 데이터 도구는 pandas·numpy·openpyxl 등 파이썬 패키지를 씁니다. 이 패키지들은 저장소에 포함하지 않고 설치해서 쓰며(`requirements.txt`·`requirements-docs.txt`), 각자의 라이선스를 따릅니다.

## 5. 이름과 상표

- (가상) 한빛정밀(주), Halden Industrial Supplies Ltd., 합성 데이터의 바이어와 Halden 보고서에 나오는 회사·은행·감사법인·보험사는 모두 교육용 가상 이름이며 실존 기업과 무관합니다.
- 위에 적은 회사·기관 이름과 상표는 출처를 밝히려고 쓴 것이며 각 소유자의 것입니다. 이 과정은 그 회사·기관과 관계가 없고 보증을 받지 않았습니다.

## UCI Machine Learning Repository — Taiwanese Bankruptcy Prediction

`data/external/uci_taiwan_bankruptcy.csv` — Liang, D., Lu, C.-C., Tsai, C.-F., & Shih, G.-A. (2016). Taiwanese Bankruptcy Prediction [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5004D — CC BY 4.0. 열 이름 앞 공백만 제거했고 값은 원본 그대로다(2026-10-07 조회).
