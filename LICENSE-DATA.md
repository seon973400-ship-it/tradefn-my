# 데이터·문서 라이선스 (LICENSE-DATA)

이 저장소는 자료의 종류에 따라 라이선스가 다릅니다.

| 무엇 | 라이선스 | 어디에 적혀 있나 |
|---|---|---|
| 코드 — `tools/`의 스크립트, `labs/`의 노트북, 실습 템플릿 안의 엑셀 수식, 사이트 설정·워크플로(`mkdocs.yml`, `docs/stylesheets/`, `.github/`) | **MIT** | [`LICENSE`](LICENSE) |
| 과정이 만든 데이터·문서 — 아래 1절 | **CC BY 4.0** | 이 파일 |
| 제3자 자료 — 아래 2절 | 각 원본의 조건 | 이 파일 2절 · [`NOTICE.md`](NOTICE.md) |

## 1. CC BY 4.0 — 과정이 만든 데이터·문서

아래 자료는 **크리에이티브 커먼즈 저작자표시 4.0 국제(CC BY 4.0)** 라이선스로 제공합니다. 출처를 밝히면 복제·배포·수정·상업적 이용을 포함해 자유롭게 쓸 수 있습니다.

- **(가상) 한빛정밀(주) 합성 데이터** — `data/day1/`의 바이어 스냅샷(`d1_buyers_raw`)·인보이스 원장(`d1_invoices`), `data/checkpoints/`의 체크포인트 파일, 데이터 사전 `data/data_dictionary.xlsx`
- **Halden 가상 연차보고서** — `data/day1/reports/halden_fictional_annual_report.md`, 같은 폴더의 안내문(`README.md`·`gorman_note.md`)
- **SEC 공시 발췌 파일에서 편집자가 쓴 부분** — 파일 머리의 회사 개요 표, `[E1]` 같은 절 번호, 한국어 소제목·요약(영어 원문 인용은 2절)
- **과정 사이트 원고와 실습 자료** — `docs/`의 글·표·그림, `labs/day1/prompts.md`(프롬프트 원문), `labs/day1/issue_definition_template.md`(현안 정의서 양식)

라이선스 전문: <https://creativecommons.org/licenses/by/4.0/legalcode.ko> · 요약: <https://creativecommons.org/licenses/by/4.0/deed.ko>

**표기 예**: "생성형 AI 기반 무역 금융 리스크 최적화 과정(한태구), CC BY 4.0". 고쳐서 쓰면 고쳤다는 사실을 함께 적습니다.

> (가상) 한빛정밀(주)·Halden과 합성 데이터의 바이어는 교육용 가상 회사이며 실존 기업과 무관합니다. 합성 데이터의 숫자는 실제 거래 기록이 아니고, 이 저장소의 어떤 자료도 투자·여신 판단 자료가 아닙니다.

## 2. CC BY 4.0을 붙이지 않는 것 — 제3자 자료

| 자료 | 이용 조건 |
|---|---|
| **SEC 공시 발췌** — `data/day1/reports/`의 `irobot.md` · `plug_power.md` · `wolfspeed.md` · `big_lots.md` | 미국 SEC EDGAR에 제출된 **공개 공시를 교육 목적으로 일부 발췌**한 것입니다. 영어 원문 인용의 권리와 책임은 각 회사에 있고, 이 저장소의 CC BY 4.0을 원문에 붙이지 않습니다. 원문 전체는 각 파일 머리의 링크와 [데이터 페이지](docs/data.md)의 '보고서 발췌' 표에 있습니다 |
| **SEC 비율표** — `data/day1/real_buyers_ratios.csv`·`.xlsx` | SEC XBRL companyfacts API(data.sec.gov)의 공개 공시 값을 2026-10-01에 추출해 계산한 표입니다. 원래 값의 출처는 각 회사의 공시입니다 |
| **D&B Gorman 샘플 보고서** | **링크만** 제공합니다(`data/day1/reports/gorman_note.md`). PDF에 D&B 저작권 표시가 있으므로 이 저장소·공유 드라이브·단체방에 올리지 않고, 각자 링크에서 받아 개인 실습에만 씁니다 |
| **환율** — `data/external/fred_*.csv`와 합성 데이터의 원화·달러 환산값 | 미국 연준 H.10 환율(FRED 제공) — FRED 시리즈 페이지 표시 "Public Domain: Citation Requested". 인용 방법과 조회일은 [`data/external/ATTRIBUTION.md`](data/external/ATTRIBUTION.md) |
| **글꼴** — `tools/fonts/` | NanumGothic — SIL Open Font License 1.1([`tools/fonts/OFL.txt`](tools/fonts/OFL.txt)) |

## 3. 앞으로 넣을 외부 공개 데이터

UCI 대만 파산 데이터는 `data/external/uci_taiwan_bankruptcy.csv`로 들어 있습니다(CC BY 4.0, [`NOTICE.md`](NOTICE.md)). UCI 폴란드·ECOS·OECD·GDELT 같은 나머지 외부 데이터 캐시는 아직 이 저장소에 없습니다([`data/external/ATTRIBUTION.md`](data/external/ATTRIBUTION.md): "받을 때 이 표에 한 줄씩 추가한다"). 넣을 때는 원본의 라이선스(예: UCI 두 데이터는 CC BY 4.0, 출처 표기 필수)·DOI·조회일을 `ATTRIBUTION.md`와 [`NOTICE.md`](NOTICE.md)에 함께 적고, **원본의 조건이 이 파일보다 우선**합니다.

## 4. 이 저장소에 없는 것

강사 정답지·정답 워크북·결함 기록은 공개하지 않습니다([`README.md`](README.md)의 '공개 범위'). 원천(`data/raw/`, 결함 기록 제외)과 생성기는 과정이 끝난 2026-10-21 19:00에 이 저장소의 `files` 브랜치로 자동 공개되며, 같은 라이선스(코드 MIT · 데이터 CC BY 4.0)를 따릅니다.
