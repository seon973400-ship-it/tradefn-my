# 차트용 한글 글꼴

- `NanumGothic-Regular.ttf`, `NanumGothic-Bold.ttf` — 출처: Google Fonts 저장소 <https://github.com/google/fonts/tree/main/ofl/nanumgothic> (2026-10-01 내려받음)
- 라이선스: SIL Open Font License 1.1 (`OFL.txt`). 재배포·동봉 가능. 글꼴을 고쳐 배포할 때는 예약 이름(Nanum, NanumGothic 등)을 쓰지 않는다.
- 쓰는 곳: `tools/make_day1_charts.py`(matplotlib `font_manager.addfont`). Challenge 노트북(`labs/day1/d1_challenge.ipynb`, `tools/build_day1_notebook.py`가 만든다)은 저장소 안에서 실행하면 이 폴더의 `NanumGothic-Regular.ttf`를 등록하고, 파일이 없는 Colab에서는 같은 파일을 위 Google Fonts 저장소에서 한 번 받아 등록한다.
