"""⑥ RAG 규정검색 — 조(條) 단위 조각 + TF-IDF(문자 n-gram) 상위 3개 + 인용·기권.

조각 규칙: Markdown의 `## 제N조(제목)` 한 줄 = 조각 하나(별표·부칙 포함). 조각 ID = 문서 머리 + 조 번호(예: HB-27).
LLM이 있으면 P5-1 시스템 프롬프트로 답하고, 없으면(모의 모드) 가장 가까운 항을 그대로 인용한다.
기권: 최고 유사도가 낮거나, 질문의 핵심 낱말이 상위 조각에 거의 없으면 "제공 문서에서 확인되지 않습니다."
검색만으로 기권을 완벽히 가릴 수는 없다 — 골든셋 결과로 한계를 보는 것이 실습 목적이다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ABSTAIN = "제공 문서에서 확인되지 않습니다."
DOC_PREFIX = {"hanbit_credit_policy": ("HB", "가상 규정")}
CIRCLED = {c: i for i, c in enumerate("①②③④⑤⑥⑦⑧⑨⑩", 1)}
SYNONYMS = [(r"k-?sure|케이슈어|무보", " 한국무역보험공사 "), (r"\bl/?c\b|엘씨", " 신용장 "), (r"\bo/?a\b", " 사후송금 "),
            (r"전결", " 전결권 승인 "), (r"chapter\s*11", " 파산신청 회생 "), (r"부보율", " 부보율 보험 ")]
STOP = {"사내", "규정", "규정상", "무엇", "언제", "어떻게", "얼마", "얼마나", "누구", "경우", "해야", "하나", "되나", "있나",
        "인가", "무조건", "관련", "가능", "허용", "되는", "하는", "있는", "어디", "무슨", "알려", "몇", "어느", "같은", "상황",
        "이전", "최근", "전에", "일부", "달라", "늦어", "지나", "인정", "처리", "받기", "등으", "건이", "건도", "내나", "했다",
        "한다", "거래라", "선적한", "늦게", "청구할", "시점", "사유", "연장", "세무상"}
SUFFIXES = sorted(["에서는", "으로는", "에게서", "까지는", "부터는", "이라면", "하기로", "하려면", "해야", "하면", "하는", "했다",
                   "한다", "된다", "되나", "되는", "인데", "이다", "인가", "인지", "해서", "해도", "하고", "하나", "하기", "에서",
                   "에게", "으로", "까지", "부터", "처럼", "보다", "이나", "에는", "에도", "와의", "과의", "라고", "다고", "어야",
                   "아야", "으면", "은", "는", "이", "가", "을", "를", "의", "에", "로", "와", "과", "도", "만", "나", "요", "면",
                   "다", "인", "데", "고", "야", "해", "할", "한", "된", "되", "질", "받", "째"], key=len, reverse=True)
TOKEN_SYN = {"k-sure": "한국무역보험공사", "케이슈어": "한국무역보험공사", "l/c": "신용장", "lc": "신용장", "chapter": "파산신청",
             "o/a": "사후송금"}


@dataclass
class Chunk:
    cid: str
    doc: str
    title: str
    text: str


def _clean_title(t: str) -> str:
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", t).strip()


def split_markdown(text: str, prefix: str, doc: str) -> list[Chunk]:
    chunks, cur, buf = [], None, []

    def flush():
        if cur is not None and buf:
            chunks.append(Chunk(cur[0], doc, cur[1], "\n".join(buf).strip()))

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            title = line[3:].strip()
            m = re.match(r"^제(\d+)조(의\d+)?\s*\(", title)
            a = re.match(r"^별표\s*(\d+)", title)
            if m:
                cid = f"{prefix}-{m.group(1)}{m.group(2) or ''}"
            elif a:
                cid = f"{prefix}-별표{a.group(1)}"
            elif title.startswith("부칙"):
                cid = f"{prefix}-부칙"
            else:
                cid = f"{prefix}-{re.sub(r'[^0-9A-Za-z가-힣]+', '', title)[:12]}"
            cur, buf = (cid, _clean_title(title)), [line]
        elif cur is not None:
            buf.append(line)
    flush()
    return chunks


def load_corpus(folder: Path, extra: list[tuple[str, str, str]] | None = None) -> list[Chunk]:
    """folder의 *.md(README 제외) + extra[(문서명, ID 머리, 본문)] — extra는 수강생이 화면에서 올린 변환본."""
    chunks = []
    for p in sorted(Path(folder).glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        prefix, doc = DOC_PREFIX.get(p.stem, (p.stem[:3].upper(), p.stem))
        chunks += split_markdown(p.read_text(encoding="utf-8"), prefix, doc)
    for doc, prefix, body in extra or []:
        chunks += split_markdown(body, prefix, doc)
    return chunks


def _norm(s: str) -> str:
    s = s.lower()
    for rx, rep in SYNONYMS:
        s = re.sub(rx, lambda m: m.group(0) + rep, s)
    return s


def content_tokens(q: str) -> list[str]:
    """질문의 핵심 낱말(조사·어미를 떼고, 숫자가 든 낱말·의문사·흔한 동사 줄기는 뺀다). 형태소 분석 없이 쓰는 근사."""
    toks = []
    for t in re.findall(r"[0-9A-Za-z가-힣/\-.$,]+", q.lower()):
        t = t.strip(".,-/")
        if re.search(r"\d", t):
            continue
        for _ in range(2):
            for p in SUFFIXES:
                if t.endswith(p) and len(t) - len(p) >= 2:
                    t = t[: -len(p)]
                    break
        t = TOKEN_SYN.get(t, t)
        if len(t) >= 2 and t not in STOP:
            toks.append(t)
    return list(dict.fromkeys(toks))


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        if not chunks:
            raise ValueError("코퍼스 조각이 없습니다 — rag/corpus/*.md 확인")
        self.chunks = chunks
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)
        self.M = self.vec.fit_transform([_norm(c.text) for c in chunks])
        self.corpus_text = _norm(" ".join(c.text for c in chunks))

    def search(self, q: str, k: int = 3) -> list[tuple[Chunk, float]]:
        v = self.vec.transform([_norm(q)])
        sims = (self.M @ v.T).toarray().ravel()
        order = np.argsort(-sims, kind="stable")[:k]
        return [(self.chunks[i], float(sims[i])) for i in order]


def _found(t: str, text: str) -> bool:
    return t in text or (len(t) >= 3 and t[:-1] in text)


def coverage(q: str, hits: list[tuple[Chunk, float]]) -> tuple[float, list[str]]:
    """질문 핵심 낱말 중 상위 조각들에 나오는 비율(낱말 끝 한 글자 차이는 허용)."""
    toks = content_tokens(q)
    if not toks:
        return 0.0, []
    text = _norm(" ".join(c.text for c, _ in hits)).replace(" ", "")
    missing = [t for t in toks if not _found(t.replace(" ", ""), text)]
    return 1 - len(missing) / len(toks), missing


def out_of_corpus(q: str, corpus_text: str) -> list[str]:
    """코퍼스 어디에도 없는 핵심 낱말(영문 약어 3자 이상 또는 한글 4자 이상) — 예: UCP, 보험요율."""
    text = corpus_text.replace(" ", "")
    return [t for t in content_tokens(q)
            if not _found(t, text) and (re.fullmatch(r"[a-z]{3,}", t) or (re.search(r"[가-힣]", t) and len(t) >= 4))]


def decide_abstain(q: str, hits, corpus_text: str = "", min_score: float = 0.08, min_cov: float = 0.5) -> tuple[bool, str]:
    """기권 규칙(모의 모드): ① 최고 유사도 < 0.08 ② 코퍼스에 없는 핵심 낱말 ③ 상위 3개 조각의 핵심 낱말 일치 < 50%."""
    if not hits or hits[0][1] < min_score:
        return True, f"최고 유사도 {hits[0][1] if hits else 0:.2f} < {min_score}"
    oov = out_of_corpus(q, corpus_text) if corpus_text else []
    if oov:
        return True, f"문서에 없는 낱말: {', '.join(oov[:4])}"
    cov, missing = coverage(q, hits)
    if cov < min_cov:
        return True, f"핵심 낱말 일치 {cov:.0%} < {min_cov:.0%} (없음: {', '.join(missing[:5])})"
    return False, f"최고 유사도 {hits[0][1]:.2f} · 핵심 낱말 일치 {cov:.0%}"


def cite_line(chunk: Chunk, q: str) -> tuple[str, str]:
    """조각 안에서 질문과 가장 겹치는 줄과 그 인용 표기([가상 규정 제27조 제2항])."""
    toks = content_tokens(q)
    lines = [ln for ln in chunk.text.splitlines()[1:] if ln.strip() and not ln.startswith("|---")]
    if not lines:
        return "", f"[{chunk.doc} {chunk.title}]"
    best = max(lines, key=lambda ln: (sum(1 for t in toks if t in ln.lower() or (len(t) >= 3 and t[:-1] in ln.lower())), -len(ln)))
    m = re.match(r"^제(\d+)조", chunk.title)
    para = CIRCLED.get(best.strip()[:1])
    where = (f"제{m.group(1)}조" if m else chunk.title) + (f" 제{para}항" if para else "")
    return best.strip(), f"[{chunk.doc} {where}]"


def answer_mock(q: str, hits, corpus_text: str = "") -> tuple[str, bool, str]:
    """LLM 없이: 기권 또는 가장 가까운 줄 인용. 반환: (답, 기권 여부, 판단 이유)."""
    abstain, why = decide_abstain(q, hits, corpus_text)
    if abstain:
        return ABSTAIN, True, why
    top = hits[0][0]
    line, cite = cite_line(top, q)
    body = "\n".join("> " + ln for ln in top.text.splitlines()[1:] if ln.strip())
    if len(body) > 900:
        body = body[:900] + " …"
    others = ", ".join(f"{c.cid}({s:.2f})" for c, s in hits[1:])
    txt = (f"**가장 가까운 근거**: {line} {cite}\n\n**{top.cid} {top.title} 원문**\n{body}\n\n함께 볼 조항: {others}\n\n"
           f"(모의 모드 — LLM 없이 검색 결과만 보여 줍니다. 결론은 사람이 원문을 읽고 판단합니다.)\n\n※ 최종 판단은 담당자·K-SURE 확인")
    return txt, False, why


CITE_RE = re.compile(r"\[[^\]\n]*제\s*\d+\s*조[^\]\n]*\]")


def check_llm_answer(q: str, answer: str, hits, corpus_text: str = "") -> tuple[str, str]:
    """LLM 답 검사(사람이 볼 표시). 반환: (인용 검사, 경고 문구 — 없으면 "").

    인용 검사 = 기권 · 인용 있음 · 인용 없음. 검색 근거가 약한데(모의 모드라면 기권할 질문) LLM이 답했으면 경고를 붙인다."""
    t = answer or ""
    if ABSTAIN in t:
        return "기권", ""
    cited = bool(CITE_RE.search(t))
    weak, why = decide_abstain(q, hits, corpus_text)
    warn = []
    if not cited:
        warn.append("인용이 없다")
    if weak:
        warn.append(f"검색 근거가 약하다({why})")
    msg = ("⚠ " + " · ".join(warn) + " — 원문을 확인하기 전에는 쓰지 않는다") if warn else ""
    return ("인용 있음" if cited else "인용 없음"), msg


def context_block(hits) -> str:
    return "\n\n".join(f"[{c.cid} · {c.doc} {c.title}]\n{c.text}" for c, _ in hits)


def answer_llm(q: str, hits, cfg, system_prompt: str):
    from . import llm as LLM
    msgs = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[컨텍스트]\n{context_block(hits)}\n\n[질문]\n{q}"}]
    return LLM.chat(cfg, msgs)


def load_system_prompt(path: Path) -> str:
    t = Path(path).read_text(encoding="utf-8")
    m = re.search(r"```text\n(.*?)\n```", t, flags=re.S)
    return m.group(1).strip() if m else t


def article_ids(cell: str) -> list[str]:
    return [x.strip() for x in str(cell or "").replace(",", ";").split(";") if x.strip()]


KS = (1, 3, 5)


def prf_at_k(ids: list[str], gold: list[str], k: int) -> tuple[float, float, float]:
    """P@K = 맞힌 조항 수 ÷ K · R@K = 맞힌 조항 수 ÷ 정답 조항 수 · F1@K = 2PR ÷ (P + R) — 과정 사이트 실습 A의 정의."""
    hit = len(set(ids[:k]) & set(gold))
    p = hit / k
    r = hit / len(gold) if gold else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def run_goldset(gold: pd.DataFrame, retr: Retriever, k: int = 5) -> pd.DataFrame:
    """골든셋 일괄 실행(모의 모드 기권 규칙). 검색 지표는 조 단위(gold_articles), 기권(함정) 문항은 검색 지표에서 뺀다.
    지표: Hit@3 · RR(MRR용) · P@K · R@K · F1@K(K = 1·3·5)."""
    rows = []
    for _, g in gold.iterrows():
        hits = retr.search(str(g["question"]), k=k)
        ids = [c.cid for c, _ in hits]
        gold_ids = article_ids(g.get("gold_articles", ""))
        ans, abst, why = answer_mock(str(g["question"]), hits[:3], retr.corpus_text)
        is_trap = str(g.get("eval_type", "")) == "함정"
        rank = next((i + 1 for i, x in enumerate(ids) if x in gold_ids), 0)
        row = {"q_id": g["q_id"], "type": g.get("eval_type", ""), "gold_articles": ";".join(gold_ids),
               **{f"r{i + 1}": (ids[i] if i < len(ids) else "") for i in range(k)},
               "top_score": round(hits[0][1], 3) if hits else 0.0,
               "hit3": None if is_trap else int(0 < rank <= 3), "rr": None if is_trap else (round(1 / rank, 3) if rank else 0.0)}
        for kk in KS:
            pk, rk, fk = (None, None, None) if is_trap else prf_at_k(ids, gold_ids, kk)
            row.update({f"p_at_{kk}": pk, f"r_at_{kk}": rk, f"f1_at_{kk}": fk})
        row.update({"abstained": "Y" if abst else "N", "abstain_ok": (("Y" if abst else "N") if is_trap else ""),
                    "why": why, "answer_text": ans})
        rows.append(row)
    out = pd.DataFrame(rows)
    out["hit3"] = out["hit3"].astype("Int64")      # 함정 문항은 빈칸(검색 지표에서 뺀다)
    for c in ["rr"] + [f"{m}_at_{kk}" for kk in KS for m in ("p", "r", "f1")]:
        out[c] = pd.to_numeric(out[c], errors="coerce").round(3)
    return out


def goldset_summary(res: pd.DataFrame) -> dict:
    norm = res[res["type"] != "함정"]
    trap = res[res["type"] == "함정"]
    mean = lambda c: round(float(pd.to_numeric(norm[c], errors="coerce").mean()), 3) if len(norm) and c in norm else None  # noqa: E731
    out = {"hit_at_3": mean("hit3"), "mrr": mean("rr"),
           "abstain_accuracy": round(float((trap["abstained"] == "Y").mean()), 3) if len(trap) else None,
           "wrong_abstain": int((norm["abstained"] == "Y").sum()), "n": int(len(res))}
    for kk in KS:
        for m in ("p", "r", "f1"):
            out[f"{m}_at_{kk}"] = mean(f"{m}_at_{kk}")
    f1s = {kk: out[f"f1_at_{kk}"] for kk in KS if out.get(f"f1_at_{kk}") is not None}
    out["best_k_f1"] = max(f1s, key=lambda kk: (f1s[kk], -kk)) if f1s else None
    return out
