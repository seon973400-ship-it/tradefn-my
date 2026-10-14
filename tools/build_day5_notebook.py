#!/usr/bin/env python
"""Day5 Challenge 노트북 `labs/day5/d5_rag_eval.ipynb` — 골든셋으로 RAG 검색 정확도를 코드로 잰다(출력 없는 수강생용).
(v3 — 5일차 v4에서는 쓰지 않는다. 돌리면 labs/day5/d5_rag_eval.ipynb가 되살아난다. 사본: instructor/day5/lab_v3_archive/)

사용(저장소 루트):
    python tools/build_day5_notebook.py                 # 생성 + 규칙 점검
    python tools/build_day5_notebook.py --execute       # 저장소 안에서 위→아래로 실행해 앱(app/core/rag.py) 지표와 대조
    python tools/build_day5_notebook.py --org myorg     # Colab 배지·RAW_BASE의 GitHub 조직 이름(기본 brainini)
지표 정의는 과정 사이트 5일차 실습 A와 같다: P@K = 맞힌 조항 ÷ K · R@K = 맞힌 조항 ÷ 정답 조항 · F1@K = 2PR ÷ (P + R), K = 1·3·5.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "labs" / "day5" / "d5_rag_eval.ipynb"


def md(cid, text):
    c = new_markdown_cell(text.strip("\n"))
    c["id"] = cid
    return c


def code(cid, text):
    c = new_code_cell(text.strip("\n"))
    c["id"] = cid
    return c


def build(org: str):
    badge = f"https://colab.research.google.com/github/{org}/tradefin-ai-2026/blob/main/labs/day5/d5_rag_eval.ipynb"
    cells = [
        md("title", f"""
# Day5 Challenge 노트북 — RAG 검색 정확도를 코드로 재기(골든셋 20문항)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({badge})

Dify·Gemini Notebook에서 손으로 기록한 검색 결과를 **코드로 다시 재고**, 청킹(조 단위 vs 고정 길이)과 검색기(TF-IDF vs BM25), Top-K를 바꿔 가며 비교합니다.

| 절 | 시간 | 하는 일 | 평가 시트 연결 |
|---|---|---|---|
| 0 준비 | 5분 | 버전 · 글꼴 · 데이터(골든셋 · 가상 규정) | — |
| A 조 단위 청킹 | 5분 | `## 제N조(제목)` 한 줄 = 조각 하나 | goldset 탭 gold_articles |
| B 검색기 2종 | 10분 | TF-IDF(문자 n-gram) · BM25(낱말) | — |
| C 지표 | 10분 | P@K · R@K · F1@K(K = 1·3·5) · Hit@3 · MRR | eval V~AD열 · summary |
| D 청킹 비교 | 10분 | 조 단위 vs 고정 길이 300자 | experiments 탭(E1·E2) |
| E Top-K 고르기 | 5분 | F1@K가 가장 높은 K | summary 'F1 최고 K' |
| F·G (선택) | 남는 시간 | 내 약관 변환본 추가 · LLM 답변과 인용 검사 | run_app 탭 |

**Colab에서 여는 법**: 위 배지 → **파일 → Drive에 사본 저장** → 셀을 위에서 아래로 **Shift+Enter**.

> **데이터 위생** — (가상) 한빛정밀 규정과 공개 법령·공식 링크에서 받은 약관만 씁니다. 회사 실규정·실데이터는 넣지 않습니다. LLM 키는 화면에서 입력받고 파일에 저장하지 않습니다.
"""),
        md("s0", """
## 0. 준비 (5분)

1. **0-1 버전** — Colab 기본 라이브러리(pandas · numpy · scikit-learn)만 씁니다. 따로 설치할 것이 없습니다.
2. **0-2 한글 글꼴** — 그래프 한글이 □로 깨지지 않게 합니다.
3. **0-3 데이터** — ① 내 컴퓨터의 과정 저장소 폴더 → ② 과정 저장소 웹 주소(`RAW_BASE`) → ③ 직접 업로드 순서로 찾습니다.
"""),
        code("c01", """
# 0-1. 파이썬·라이브러리 버전 확인(설치 없음)
import sys, re, json, math
import numpy as np
import pandas as pd
import sklearn
print("Python", sys.version.split()[0], "| pandas", pd.__version__, "| numpy", np.__version__, "| scikit-learn", sklearn.__version__)
pd.set_option("display.max_colwidth", 80)
pd.set_option("display.width", 160)
"""),
        code("c02", """
# 0-2. 그래프 한글이 깨지지 않게 나눔고딕 글꼴을 등록한다(Colab은 한 번 내려받는다)
import urllib.request
from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"

def find_upwards(rel):
    \"\"\"지금 폴더와 위쪽 폴더(3단계까지)에서 rel 파일을 찾는다. 없으면 None.\"\"\"
    here = Path.cwd().resolve()
    for base in [here, *here.parents][:4]:
        if (base / rel).is_file():
            return base / rel
    return None

font_file = find_upwards("tools/fonts/NanumGothic-Regular.ttf") or Path("NanumGothic-Regular.ttf")
try:
    if not font_file.is_file():
        urllib.request.urlretrieve(FONT_URL, font_file.with_suffix(".part"))
        font_file.with_suffix(".part").rename(font_file)
    font_manager.fontManager.addfont(str(font_file))
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font_file)).get_name()
except Exception as e:
    print("글꼴 등록 실패 — 그래프 한글이 □로 보일 수 있지만 계산은 그대로 됩니다:", e)
plt.rcParams.update({"axes.unicode_minus": False, "figure.dpi": 100, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#E6E6E6", "axes.axisbelow": True})
print("글꼴:", plt.rcParams["font.family"])
"""),
        code("c03", f"""
# 0-3. 데이터 — 골든셋(rag/goldset_20.csv)과 (가상) 한빛정밀 여신관리규정(rag/corpus/hanbit_credit_policy.md)
RAW_BASE = "https://raw.githubusercontent.com/{org}/tradefin-ai-2026/main"   # <org>가 남아 있으면 강사가 알려 준 이름으로 바꾼다

def get_file(rel):
    found = find_upwards(rel) or find_upwards(Path(rel).name)
    if found:
        return found
    target = Path(rel)
    if "<org>" not in RAW_BASE:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(f"{{RAW_BASE}}/{{rel}}", target)
            return target
        except Exception as e:
            print("내려받기 실패(공개 전이면 정상):", e)
    try:
        from google.colab import files
    except ImportError:
        raise FileNotFoundError(f"{{rel}} 을(를) 찾지 못했습니다. 과정 저장소 폴더에서 실행하거나 RAW_BASE를 확인하세요.") from None
    print(f"'{{target.name}}' 파일을 골라 올려 주세요.")
    return Path(next(iter(files.upload())))

gold = pd.read_csv(get_file("rag/goldset_20.csv"), encoding="utf-8-sig", dtype=str, keep_default_na=False)
policy = get_file("rag/corpus/hanbit_credit_policy.md").read_text(encoding="utf-8")
print(f"골든셋 {{len(gold)}}문항 · 유형 {{gold['type'].value_counts().to_dict()}} · 규정 {{len(policy):,}}자")
gold[["q_id", "question", "gold_articles", "eval_type"]].head(8)
"""),
        md("sA", """
## A. 조 단위 청킹 (5분)

규정·약관은 `제N조 → 항(①②) → 호(1. 2.)` 구조입니다. **`## 제N조(제목)` 한 줄부터 다음 `##` 전까지를 조각 하나**로 자르면, 검색 결과의 첫 줄이 곧 조항 번호가 되어 평가가 쉽고 인용도 정확해집니다(Dify Parent-child의 '부모 = 조'와 같은 단위).
"""),
        code("cA1", """
# A-1. Markdown을 조 단위 조각으로 자른다 → id(HB-27 등) · 제목 · 본문
def split_articles(text, prefix="HB", doc="가상 규정"):
    rows, cur, buf = [], None, []
    def flush():
        if cur is not None:
            rows.append({"id": cur[0], "doc": doc, "title": cur[1], "text": "\\n".join(buf).strip()})
    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            title = re.sub(r"\\s*\\[[^\\]]*\\]\\s*$", "", line[3:].strip())
            m, a = re.match(r"^제(\\d+)조(의\\d+)?\\s*\\(", title), re.match(r"^별표\\s*(\\d+)", title)
            cid = f"{prefix}-{m.group(1)}{m.group(2) or ''}" if m else (f"{prefix}-별표{a.group(1)}" if a else f"{prefix}-{title[:6]}")
            cur, buf = (cid, title), [line]
        elif cur is not None:
            buf.append(line)
    flush()
    return pd.DataFrame(rows)

chunks = split_articles(policy)
print(f"조각 {len(chunks)}개(조 {chunks['id'].str.match(r'^HB-\\d+$').sum()} + 별표·부칙)")
chunks.assign(chars=chunks.text.str.len())[["id", "title", "chars"]].head(10)
"""),
        md("sB", """
## B. 검색기 2종 (10분)

| 검색기 | 무엇을 맞추나 | 장점 | 약점 |
|---|---|---|---|
| **TF-IDF(문자 2~4글자)** | 글자 조각이 겹치는 정도 | 한국어 조사·어미가 붙어도 잘 맞는다 | 흔한 낱말(결제기일 등)에 끌려간다 |
| **BM25(낱말)** | 낱말이 나오는 횟수 + 문서 길이 보정 | 'L/C'·'D/A'처럼 정확한 용어에 강하다 | 띄어쓰기·조사에 약하다 |

Dify의 **Hybrid**는 의미(임베딩) 검색과 키워드 검색을 섞습니다. 여기서는 임베딩 없이 키워드 쪽 두 가지를 비교합니다.
"""),
        code("cB1", """
# B-1. 검색기 두 가지 — 같은 사용법: search(질문, k) → [(조각 id, 점수), ...]
from sklearn.feature_extraction.text import TfidfVectorizer

SYN = [(r"k-?sure|케이슈어|무보", " 한국무역보험공사 "), (r"\\bl/?c\\b", " 신용장 "), (r"\\bo/?a\\b", " 사후송금 "),
       (r"전결", " 전결권 승인 "), (r"chapter\\s*11", " 파산신청 회생 "), (r"부보율", " 부보율 보험 ")]

def norm(s):
    s = s.lower()
    for rx, rep in SYN:                                   # 질문의 줄임말을 규정 용어로 넓힌다(앱 ⑥과 같은 표)
        s = re.sub(rx, lambda m: m.group(0) + rep, s)
    return s

class TfidfSearch:
    name = "TF-IDF(문자 2~4)"
    def __init__(self, df):
        self.df = df.reset_index(drop=True)
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)
        self.M = self.vec.fit_transform([norm(t) for t in self.df.text])
    def search(self, q, k=5):
        s = (self.M @ self.vec.transform([norm(q)]).T).toarray().ravel()
        o = np.argsort(-s, kind="stable")[:k]
        return [(self.df.id[i], float(s[i])) for i in o]

def words(s):
    return re.findall(r"[0-9a-z가-힣/$]+", norm(s))

class BM25Search:
    name = "BM25(낱말)"
    def __init__(self, df, k1=1.5, b=0.75):
        self.df = df.reset_index(drop=True)
        self.docs = [words(t) for t in self.df.text]
        self.avg = np.mean([len(d) for d in self.docs])
        self.k1, self.b = k1, b
        N = len(self.docs)
        df_ = {}
        for d in self.docs:
            for w in set(d):
                df_[w] = df_.get(w, 0) + 1
        self.idf = {w: math.log(1 + (N - n + 0.5) / (n + 0.5)) for w, n in df_.items()}
    def search(self, q, k=5):
        qs = words(q)
        sc = []
        for d in self.docs:
            tf = {}
            for w in d:
                tf[w] = tf.get(w, 0) + 1
            s = 0.0
            for w in qs:
                if w in tf:
                    f = tf[w]
                    s += self.idf.get(w, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            sc.append(s)
        sc = np.array(sc)
        o = np.argsort(-sc, kind="stable")[:k]
        return [(self.df.id[i], float(sc[i])) for i in o]

tfidf, bm25 = TfidfSearch(chunks), BM25Search(chunks)
q = "사내 규정상 연체 40일 바이어에게 영업본부장 승인으로 선적해도 되나?"
print("TF-IDF:", tfidf.search(q, 3))
print("BM25  :", bm25.search(q, 3))
"""),
        md("sC", """
## C. 지표 — P@K · R@K · F1@K · Hit@3 · MRR (10분)

질문마다 정답 조항 집합 **G**(조 단위, 1~2개)와 상위 K개 검색 결과 **R**을 비교합니다. 기권(함정) 문항은 검색 지표에서 뺍니다.

- **P@K** = 맞힌 조항 수 ÷ K — 결과 중 쓸모 있는 비율(잡음이 적을수록 높다)
- **R@K** = 맞힌 조항 수 ÷ 정답 조항 수 — 정답을 놓치지 않은 비율
- **F1@K** = 2 × P × R ÷ (P + R) — 둘의 조화평균
- 보조: **Hit@3**(상위 3개 안에 정답이 하나라도) · **MRR**(첫 정답 순위의 역수 평균)
"""),
        code("cC1", """
# C-1. 한 검색기로 골든셋 20문항을 돌려 문항별 지표를 만든다
KS = (1, 3, 5)

def evaluate(searcher, gold, k=5):
    rows = []
    for _, g in gold.iterrows():
        res = searcher.search(g.question, k)
        ids = [i for i, _ in res]
        G = [x for x in g.gold_articles.split(";") if x]
        row = {"q_id": g.q_id, "type": g.eval_type, "gold": ";".join(G), **{f"r{i + 1}": ids[i] for i in range(k)}}
        if g.eval_type != "함정":
            rank = next((i + 1 for i, x in enumerate(ids) if x in G), 0)
            row.update({"hit3": int(0 < rank <= 3), "rr": 1 / rank if rank else 0.0})
            for K in KS:
                h = len(set(ids[:K]) & set(G))
                p, r = h / K, h / len(G)
                row.update({f"P@{K}": p, f"R@{K}": r, f"F1@{K}": 2 * p * r / (p + r) if p + r else 0.0})
        rows.append(row)
    return pd.DataFrame(rows)

def summary(res):
    s = res[res.type != "함정"]
    out = {"Hit@3": s.hit3.mean(), "MRR": s.rr.mean()}
    for K in KS:
        out.update({f"P@{K}": s[f"P@{K}"].mean(), f"R@{K}": s[f"R@{K}"].mean(), f"F1@{K}": s[f"F1@{K}"].mean()})
    return pd.Series(out).round(3)

res_tfidf, res_bm25 = evaluate(tfidf, gold), evaluate(bm25, gold)
table = pd.DataFrame({tfidf.name: summary(res_tfidf), bm25.name: summary(res_bm25)})
table
"""),
        code("cC2", """
# C-2. 어디서 놓쳤나 — 정상·충돌 문항 중 상위 3개에 정답이 없는 것(가상 규정만 넣었다면 K-SURE 문항은 놓치는 게 정상)
miss = res_tfidf[(res_tfidf.type != "함정") & (res_tfidf.hit3 == 0)][["q_id", "gold", "r1", "r2", "r3"]]
print(f"TF-IDF가 상위 3개에서 놓친 문항 {len(miss)}개 — gold가 KS-로 시작하면 코퍼스에 약관이 없어서다(F절에서 추가)")
miss.merge(gold[["q_id", "question"]], on="q_id")
"""),
        md("sD", """
## D. 청킹 비교 — 조 단위 vs 고정 길이 (10분)

Dify 'General' 청킹(구분자 + 최대 길이)처럼 **글자 수로 자르면** 조 경계가 무너져 한 조각에 두 조가 섞이거나 한 조가 둘로 나뉩니다. 고정 길이 조각은 시작 위치가 속한 조의 id를 붙여 같은 지표로 잽니다(평가 시트 experiments 탭 E1 vs E2).
"""),
        code("cD1", """
# D-1. 고정 길이(300자, 겹침 50자) 조각 → 조각마다 '시작 위치가 속한 조' id를 붙인다
def fixed_chunks(df, size=300, overlap=50):
    full, spans, pos = "", [], 0
    for _, r in df.iterrows():
        t = r.text + "\\n\\n"
        spans.append((pos, pos + len(t), r.id))
        full += t
        pos += len(t)
    rows, start, n = [], 0, 0
    while start < len(full):
        piece = full[start:start + size]
        owner = next(i for a, b, i in spans if a <= start < b)
        rows.append({"id": owner, "title": f"조각{n}", "text": piece})
        start += size - overlap
        n += 1
    return pd.DataFrame(rows)

class Dedup:
    \"\"\"같은 조의 조각이 여러 개 걸리면 한 번만 센다(상위 K개 = 서로 다른 조 K개).\"\"\"
    def __init__(self, inner):
        self.inner, self.name = inner, inner.name + " · 고정 300자"
    def search(self, q, k=5):
        out, seen = [], set()
        for i, s in self.inner.search(q, k * 6):
            if i not in seen:
                seen.add(i)
                out.append((i, s))
            if len(out) == k:
                break
        return out

fx = fixed_chunks(chunks)
res_fixed = evaluate(Dedup(TfidfSearch(fx)), gold)
comp = pd.DataFrame({"조 단위 · TF-IDF": summary(res_tfidf), "고정 300자 · TF-IDF": summary(res_fixed),
                     "조 단위 · BM25": summary(res_bm25)})
print(f"고정 길이 조각 {len(fx)}개(조 단위 {len(chunks)}개)")
comp
"""),
        code("cD2", """
# D-2. 그림 — K별 F1(높을수록 좋음)
ax = comp.loc[["F1@1", "F1@3", "F1@5"]].plot(kind="bar", figsize=(7, 3.6), color=["#1F5FD1", "#C2410C", "#666666"], rot=0)
ax.set_title("청킹·검색기별 F1@K — 골든셋(함정 제외)")
ax.set_ylabel("F1@K")
ax.set_ylim(0, max(0.6, float(comp.loc[['F1@1', 'F1@3', 'F1@5']].max().max()) + 0.1))
plt.tight_layout()
plt.show()
"""),
        md("sE", """
## E. Top-K 고르기 (5분)

K를 늘리면 **R@K(놓치지 않음)** 는 오르지만 **P@K(잡음 없음)** 는 내려갑니다. 두 값의 조화평균 F1@K가 가장 높은 K를 고르는 것이 이 과정의 'Top-K 최적화'입니다. 같은 값이면 작은 K(LLM에 넘기는 조각이 적어 비용·혼동이 준다).
"""),
        code("cE1", """
# E-1. 설정별 F1이 가장 높은 K
best = {c: int(max(KS, key=lambda K: (comp.loc[f"F1@{K}", c], -K))) for c in comp.columns}
for c, K in best.items():
    print(f"{c:22s} → Top-K = {K}  (F1 {comp.loc[f'F1@{K}', c]:.3f} · P {comp.loc[f'P@{K}', c]:.3f} · R {comp.loc[f'R@{K}', c]:.3f})")
CHECK = {"n_chunks": int(len(chunks)), "tfidf": summary(res_tfidf).to_dict(), "bm25": summary(res_bm25).to_dict(),
         "fixed": summary(res_fixed).to_dict(), "best_k": best}
print(json.dumps({"CHECK": CHECK}, ensure_ascii=False))
"""),
        md("sF", """
## F. (선택) 내 약관 변환본을 넣고 다시 재기

K-SURE 약관 PDF를 프롬프트 **P5-2**로 `## 제N조(제목)` Markdown으로 바꿨다면(각자 받은 원문으로, 공유 금지) 아래 셀에서 올리고 다시 잽니다. 골든셋 K-SURE 문항(Q01~Q14)의 R@K가 오르는지 보세요.
"""),
        code("cF1", """
# F-1. MY_DOC = True로 바꾸고 실행 → 파일 선택(.md). ID 머리는 KS(약관).
MY_DOC = False
if MY_DOC:
    try:
        from google.colab import files
        up = files.upload()
        body = next(iter(up.values())).decode("utf-8")
    except ImportError:
        body = Path(input("Markdown 파일 경로: ")).read_text(encoding="utf-8")
    ks = split_articles(body, prefix="KS", doc="K-SURE 약관")
    both = pd.concat([chunks, ks], ignore_index=True)
    print(f"약관 조각 {len(ks)}개 추가 → 전체 {len(both)}개")
    display(pd.DataFrame({"규정만": summary(res_tfidf), "규정 + 약관": summary(evaluate(TfidfSearch(both), gold))}))
"""),
        md("sG", """
## G. (선택) LLM 답변과 인용·기권 검사

강사 LiteLLM 주소와 내 가상 키로 상위 3개 조각만 근거로 답하게 하고(P5-1), ① 답에 정답 조항이 인용됐는지 ② 함정 문항(Q19·Q20)에서 "제공 문서에서 확인되지 않습니다"라고 기권했는지 봅니다. 키는 화면에서만 입력합니다(파일·노트북에 남기지 않는다).
"""),
        code("cG1", """
# G-1. USE_LLM = True로 바꾸고 실행
USE_LLM = False
P51 = ("너는 (가상) 한빛정밀(주) 여신관리팀의 규정 검색 도우미다. 반드시 컨텍스트만 근거로 답하고, 모든 문장 끝에 [문서명 제N조 제M항]을 붙인다. "
       "근거가 없으면 정확히 \\"제공 문서에서 확인되지 않습니다.\\"라고만 답한다. 사내 규정과 약관이 다르면 두 조항을 모두 인용하고 "
       "\\"[규정 충돌] 담당자 확인 필요\\"라고 표시한다. 마지막 줄: \\"※ 최종 판단은 담당자·K-SURE 확인\\"")
if USE_LLM:
    import getpass, requests
    base = input("LiteLLM 주소(…/v1): ").rstrip("/")
    key = getpass.getpass("가상 키: ")
    out = []
    for qid in ["Q07", "Q15", "Q16", "Q19", "Q20"]:
        g = gold[gold.q_id == qid].iloc[0]
        ctx = "\\n\\n".join(f"[{i}] " + chunks.set_index("id").text[i] for i, _ in tfidf.search(g.question, 3))
        r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}"}, timeout=30,
                          json={"model": "fast-default", "temperature": 0.1, "max_tokens": 500,
                                "messages": [{"role": "system", "content": P51},
                                             {"role": "user", "content": f"[컨텍스트]\\n{ctx}\\n\\n[질문]\\n{g.question}"}]})
        ans = r.json()["choices"][0]["message"]["content"] if r.ok else f"오류 {r.status_code}"
        arts = [a for a in g.gold_articles.split(";") if a]
        cited = any(f"제{a.split('-')[1]}조" in ans for a in arts if a.startswith("HB-"))
        out.append({"q_id": qid, "type": g.eval_type, "기권": "제공 문서에서 확인되지 않습니다" in ans, "정답 조항 인용": cited, "답": ans[:160]})
    display(pd.DataFrame(out))
"""),
        md("sH", """
## H. AI와 함께 확장 · 셀프 체크

- **확장 프롬프트 예**: "이 노트북의 BM25Search에 한국어 조사 떼기(은·는·이·가·을·를·의·에서…)를 넣고, 조 단위 TF-IDF와 점수를 0.5:0.5로 섞는 HybridSearch 클래스를 추가해 줘. 기존 함수 이름은 바꾸지 말고, C-1의 evaluate로 비교할 수 있게 해 줘."
- **셀프 체크**
    1. 고정 길이 청킹의 F1@K가 조 단위보다 낮은 이유를 '조 경계'로 한 문장 설명할 수 있다.
    2. K를 3에서 5로 늘리면 P@K와 R@K가 각각 어떻게 움직이는지 표에서 확인했다.
    3. 가상 규정만 넣었을 때 K-SURE 문항을 놓치는 것은 검색기 탓이 아니라 **코퍼스에 문서가 없어서**임을 안다.
    4. 검색 지표가 좋아도 답이 틀릴 수 있다 — 답 품질(정답·인용·기권)은 평가 시트 P~U열에서 사람이 채점한다.
"""),
    ]
    nb = new_notebook(cells=cells, metadata={"colab": {"provenance": [], "toc_visible": True},
                                             "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                             "language_info": {"name": "python"}})
    nbformat.validate(nb)
    return nb


def lint(nb) -> list[str]:
    probs = []
    src = "\n".join(c.source for c in nb.cells)
    # 회사명(한글 3자 · 영문 7자)은 공개 저장소에 글자로 남기지 않게 코드포인트로 적는다
    org = ("".join(map(chr, (0xC634, 0xB2C8, 0xCF58))), "".join(map(chr, (111, 109, 110, 105, 113, 111, 110))))
    if any(n in src.lower() for n in org):
        probs.append("금지 문자열(회사명)")
    for bad in ("sk-", "api_key ="):
        if bad in src:
            probs.append(f"금지 문자열 {bad!r}")
    if any(c.get("outputs") for c in nb.cells if c.cell_type == "code"):
        probs.append("출력이 남아 있음")
    return probs


def execute(nb) -> dict:
    from nbclient import NotebookClient
    work = REPO / "labs" / "day5"
    client = NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(work)}})
    client.execute()
    for c in nb.cells:
        for o in c.get("outputs", []):
            t = o.get("text", "")
            if '{"CHECK"' in t:
                return json.loads(t[t.index('{"CHECK"'):].splitlines()[0])["CHECK"]
    raise RuntimeError("CHECK 출력이 없습니다")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--org", default="brainini")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()
    nb = build(a.org)
    probs = lint(nb)
    if probs:
        print("문제:", probs)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(nbformat.writes(nb) + "\n", encoding="utf-8")
    print(f"→ {OUT.relative_to(REPO)} (셀 {len(nb.cells)})")
    if a.execute:
        import copy
        chk = execute(copy.deepcopy(nb))
        sys.path.insert(0, str(REPO / "app"))
        import pandas as pd
        from core import data_io as IO, rag as RG
        app = RG.goldset_summary(RG.run_goldset(pd.read_csv(IO.GOLDSET, encoding="utf-8-sig", dtype=str, keep_default_na=False),
                                                RG.Retriever(RG.load_corpus(IO.RAG_CORPUS))))
        t = chk["tfidf"]
        pairs = [("Hit@3", "hit_at_3"), ("MRR", "mrr")] + [(f"{m.upper() if m != 'f1' else 'F1'}@{k}", f"{m}_at_{k}")
                                                          for k in (1, 3, 5) for m in ("p", "r", "f1")]
        diff = [(nbk, t[nbk], app[ak]) for nbk, ak in pairs if abs(t[nbk] - app[ak]) > 0.002]
        print("노트북 실행 통과 · 조각", chk["n_chunks"], "· TF-IDF", {k: t[k] for k in ("Hit@3", "MRR", "F1@1", "F1@3", "F1@5")},
              "· 최적 K", chk["best_k"])
        if diff:
            print("앱(app/core/rag.py)과 TF-IDF 지표가 다르다:", diff)
            return 1
        print("앱 ⑥ 골든셋 지표와 일치")
    return 0


if __name__ == "__main__":
    sys.exit(main())
