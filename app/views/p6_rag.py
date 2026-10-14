"""⑥ RAG 규정검색 — (가상) 한빛정밀 여신관리규정을 조(條) 단위로 찾아 인용과 함께 답한다. 근거가 없으면 기권한다.

검색: TF-IDF(문자 2~4글자 n-gram) 상위 3개 조각. 조각 = Markdown `## 제N조(제목)` 한 줄부터 다음 `##` 전까지.
답: LLM이 있으면 P5-1 시스템 프롬프트(인용 강제·기권·충돌 표시) + 인용·근거 검사 표시, 없으면 모의 모드(가장 가까운 조항 원문 인용).
K-SURE 약관은 저장소에 없다(링크만) — 각자 변환한 Markdown을 아래에서 올리면 이 세션에서만 함께 찾는다.
"""
import pandas as pd
import streamlit as st

import ui
from core import data_io as IO
from core import rag as RG

st.title("⑥ RAG 규정검색")
st.caption("근거 조항을 [문서 제N조 제M항]으로 붙이고, 문서에서 찾지 못하면 '제공 문서에서 확인되지 않습니다.'라고 답한다.")
ss = st.session_state

with st.expander("문서 추가(선택) — K-SURE 약관 조문 Markdown 등. 서버에 저장하지 않는다"):
    up = st.file_uploader("Markdown·텍스트(.md · .txt), `## 제N조(제목)` 형식", type=["md", "txt"])
    c1, c2 = st.columns(2)
    prefix = c1.selectbox("조항 ID 머리", ["KS", "LAW-TIA", "LAW-FTA", "LAW-CIT", "DOC"],
                          help="KS = K-SURE 약관 · LAW-TIA = 무역보험법 · LAW-FTA = 대외무역법 · LAW-CIT = 법인세법 시행령")
    docname = c2.text_input("문서 이름", value="K-SURE 약관" if prefix == "KS" else "법령")
    if st.button("이 문서 추가") and up is not None:
        body = up.getvalue().decode("utf-8", errors="replace")
        n = len(RG.split_markdown(body, prefix, docname))
        if n == 0:
            st.error("`## 제N조(제목)` 머리가 없어 조각을 만들지 못했습니다 — 프롬프트 P5-2로 변환하세요.")
        else:
            ss["rag_extra"] = ss["rag_extra"] + [(docname, prefix, body)]
            st.success(f"{docname}: 조각 {n}개 추가")
    if ss["rag_extra"]:
        st.write("추가한 문서: " + ", ".join(f"{d}({p})" for d, p, _ in ss["rag_extra"]))
        if st.button("추가 문서 모두 빼기"):
            ss["rag_extra"] = []

retr = ui.retriever(ss["rag_extra"])
cfg = ui.llm_config()
system_prompt = RG.load_system_prompt(IO.PROMPTS / "rag_system_v1.md")
st.caption(f"코퍼스 조각 {len(retr.chunks)}개 · {'LLM 답변' if cfg else '모의 모드(검색 결과 인용)'}")

for h in ss["rag_history"][-6:]:
    with st.chat_message("user"):
        st.write(h["q"])
    with st.chat_message("assistant"):
        st.markdown(h["a"])
        st.caption(h["meta"])

q = st.chat_input("규정에 대해 물어보세요 — 예: 사내 규정상 C등급 바이어에게 허용되는 결제조건은?")
if q:
    hits = retr.search(q, k=3)
    if cfg:
        res = RG.answer_llm(q, hits, cfg, system_prompt)
        if res.ok:
            chk, warn = RG.check_llm_answer(q, res.text, hits, retr.corpus_text)   # 인용·근거 검사(사람이 보는 표시)
            ans = (f"> {warn}\n\n" if warn else "") + res.text
            meta = f"LLM {res.model_alias} · 토큰 {res.tokens_in}/{res.tokens_out} · 인용 검사: {chk}"
            ui.log_llm(res.model_alias, res.model_resolved, res.tokens_in, res.tokens_out, "rag")
        else:
            ans, _, why = RG.answer_mock(q, hits, retr.corpus_text)
            meta = f"LLM 실패 → 모의 답변 · {res.error[:80]}"
    else:
        ans, _, why = RG.answer_mock(q, hits, retr.corpus_text)
        meta = f"모의 모드 · {why}"
    meta += " · 검색: " + ", ".join(f"{c.cid}({s:.2f})" for c, s in hits)
    ss["rag_history"].append({"q": q, "a": ans, "meta": meta, "hits": [(c.cid, round(s, 3)) for c, s in hits]})
    st.rerun()

if ss["rag_history"]:
    last = ss["rag_history"][-1]
    with st.expander("마지막 질문의 상위 3개 조각(Hit@3 기록용)"):
        for cid, s in last["hits"]:
            ch = next(c for c in retr.chunks if c.cid == cid)
            st.markdown(f"**{cid}** · {ch.doc} {ch.title} · 유사도 {s:.3f}")
            st.code(ch.text[:800], language=None)

st.divider()
st.subheader("골든셋 20문항 일괄 실행(모의 모드 기권 규칙)")
st.caption("앱 안의 참고 계산이다 — 실습 A의 평가 시트(rag/eval_sheet_template.xlsx의 eval · eval_B 탭)와 정의가 달라 숫자가 다를 수 있어 실습 기록에는 쓰지 않는다. 가상 규정만 있으면 K-SURE 문항은 기권이 정상이다.")
if st.button("골든셋 실행"):
    gold = pd.read_csv(IO.GOLDSET, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    ss["goldset_run"] = RG.run_goldset(gold, retr)
gr = ss.get("goldset_run")
if gr is not None:
    s = RG.goldset_summary(gr)
    m = st.columns(5)
    m[0].metric("Hit@3(함정 제외)", f"{s['hit_at_3']:.2f}")
    m[1].metric("MRR", f"{s['mrr']:.2f}")
    bk = s["best_k_f1"]
    m[2].metric(f"F1@K 최고 K = {bk}", f"{s['f1_at_' + str(bk)]:.2f}")
    m[3].metric("기권 정확도(함정 2)", f"{s['abstain_accuracy']:.0%}")
    m[4].metric("오기권(정상 문항)", s["wrong_abstain"])
    st.dataframe(pd.DataFrame([{"K": k, "P@K": s[f"p_at_{k}"], "R@K": s[f"r_at_{k}"], "F1@K": s[f"f1_at_{k}"]} for k in (1, 3, 5)]),
                 hide_index=True)
    st.caption("P@K = 맞힌 조항 수 ÷ K · R@K = 맞힌 조항 수 ÷ 정답 조항 수 · F1@K = 2PR ÷ (P + R) — K를 늘리면 놓치는 것은 줄지만 잡음이 는다.")
    st.dataframe(gr.drop(columns=["answer_text"]), hide_index=True, height=300)
    export = gr[["q_id", "r1", "r2", "r3", "r4", "r5", "abstained", "top_score", "answer_text"]]
    st.download_button("결과 CSV 받기(참고용)", export.to_csv(index=False).encode("utf-8-sig"), file_name="goldset_app_run.csv", mime="text/csv")
