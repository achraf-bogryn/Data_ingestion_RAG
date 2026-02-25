# # semantic_chunk/procedure_1/app.py

# import os
# import re
# import json
# from pathlib import Path
# from typing import List, Dict, Any, Tuple

# import streamlit as st
# from dotenv import load_dotenv

# from langchain.chat_models import ChatOpenAI
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.vectorstores import Chroma

# from rank_bm25 import BM25Okapi

# # ---------------------------
# # Load .env
# # ---------------------------
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     st.error("OPENAI_API_KEY not found in .env. Put .env next to your project root.")
#     st.stop()
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# # ---------------------------
# # UI
# # ---------------------------
# st.set_page_config(page_title="ISO 13485 QMS RAG", layout="wide")
# st.title("📘 ISO 13485 — QMS Procedure RAG (Chroma + BM25 + MMR)")

# # ---------------------------
# # Defaults / constants
# # ---------------------------
# BASE_DIR = Path(__file__).parent  # ✅ Always resolve relative paths from this file location
# DEFAULT_JSON = str(BASE_DIR / "data_v2.json")
# DEFAULT_PERSIST = str(BASE_DIR / "chroma_qms")
# DEFAULT_COLLECTION = "iso13485_procedures"

# CLAUSE_REGEX = r"\b([4-7]\.\d+(?:\.\d+)*)\b"
# FALLBACK_RESPONSE = "This procedure is not available in the current ISO 13485 clause dataset."

# # ---------------------------
# # Dataset loader (✅ FIXED)
# # ---------------------------
# def load_procedure_dataset(path: str) -> List[Dict[str, Any]]:
#     p = Path(path)
#     if not p.exists():
#         raise FileNotFoundError(f"Dataset JSON not found at: {p.resolve()}")

#     with p.open("r", encoding="utf-8") as f:
#         j = json.load(f)

#     # Case 1: JSON is already a list
#     if isinstance(j, list):
#         if not j:
#             raise ValueError("Dataset JSON is an empty list.")
#         return j

#     # Case 2: JSON is an object with known list keys
#     if isinstance(j, dict):
#         for key in ("entries", "procedures", "data"):
#             if key in j and isinstance(j[key], list) and len(j[key]) > 0:
#                 return j[key]

#     raise ValueError(
#         "JSON structure not recognized.\n"
#         "Expected either:\n"
#         "1) A root list: [ {...}, {...} ]\n"
#         "2) Or an object with one of keys: entries / procedures / data containing a list."
#     )

# # ---------------------------
# # Convert entries -> texts + metadatas
# # ---------------------------
# def entries_to_texts_and_meta(entries: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
#     texts, metas = [], []

#     for i, e in enumerate(entries):
#         retrieval_text = e.get("retrieval_text")
#         if not retrieval_text:
#             retrieval_text = json.dumps(e.get("sections", e), ensure_ascii=False)

#         # clause references can be list or string
#         clause_refs = e.get("clause_references") or e.get("clause_reference") or []
#         if isinstance(clause_refs, str):
#             clause_refs = [clause_refs]

#         procedure_id = e.get("procedure_id") or e.get("id") or f"proc_{i}"
#         procedure_name = e.get("procedure_name") or e.get("title") or f"Procedure {i}"

#         meta = {
#             "procedure_id": procedure_id,
#             "procedure_name": procedure_name,
#             "clause_references": ",".join([c.strip() for c in clause_refs if str(c).strip()]),
#             # store full structured content so LLM can format it
#             "raw_sections": json.dumps(e.get("sections", e), ensure_ascii=False),
#         }

#         texts.append(retrieval_text)
#         metas.append(meta)

#     return texts, metas

# # ---------------------------
# # BM25
# # ---------------------------
# class SimpleBM25:
#     def __init__(self, texts: List[str], metas: List[Dict[str, Any]]):
#         self.docs = texts
#         self.metas = metas
#         tokenized = [self._tokenize(t) for t in texts]
#         self.bm25 = BM25Okapi(tokenized)

#     def _tokenize(self, t: str):
#         return [w.lower() for w in re.findall(r"\w+", t)]

#     def query(self, q: str, k: int = 6):
#         tokens = self._tokenize(q)
#         scores = self.bm25.get_scores(tokens)
#         top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
#         out = []
#         for i in top_idx:
#             out.append({"text": self.docs[i], "meta": self.metas[i], "score": float(scores[i])})
#         return out

# # ---------------------------
# # Build or load Chroma
# # ---------------------------
# def build_or_load_chroma(texts, metas, persist_dir, collection, embeddings) -> Chroma:
#     Path(persist_dir).mkdir(parents=True, exist_ok=True)
#     try:
#         db = Chroma(persist_directory=persist_dir, collection_name=collection, embedding_function=embeddings)
#         # if empty -> build
#         if db._collection.count() == 0:
#             raise Exception("Empty collection")
#         return db
#     except Exception:
#         db = Chroma.from_texts(
#             texts=texts,
#             embedding=embeddings,
#             metadatas=metas,
#             persist_directory=persist_dir,
#             collection_name=collection,
#         )
#         db.persist()
#         return db

# # ---------------------------
# # LLM helpers
# # ---------------------------
# def rewrite_query(llm: ChatOpenAI, q: str) -> str:
#     prompt = (
#         "Rewrite the user question for best retrieval over a QMS procedure dataset. "
#         "Keep clause numbers, procedure names, and key terms. Return ONLY the rewritten query.\n\n"
#         f"User: {q}\nRewrite:"
#     )
#     resp = llm(prompt)
#     return getattr(resp, "content", str(resp)).strip()

# def detect_intent(llm: ChatOpenAI, q: str) -> str:
#     prompt = (
#         "Classify intent into one label only: PROCEDURE_REQUEST, CLAUSE_LOOKUP, GENERAL_QMS_QUESTION.\n\n"
#         f"User: {q}\nLabel:"
#     )
#     resp = llm(prompt)
#     label = getattr(resp, "content", str(resp)).strip().splitlines()[0].strip()
#     if label not in {"PROCEDURE_REQUEST", "CLAUSE_LOOKUP", "GENERAL_QMS_QUESTION"}:
#         return "GENERAL_QMS_QUESTION"
#     return label

# def build_context(cands: List[Dict[str, Any]], max_docs: int = 6) -> str:
#     blocks = []
#     for i, c in enumerate(cands[:max_docs], 1):
#         m = c["meta"]
#         blocks.append(
#             f"[DOC {i}]\n"
#             f"procedure_id: {m.get('procedure_id')}\n"
#             f"procedure_name: {m.get('procedure_name')}\n"
#             f"clause_references: {m.get('clause_references')}\n"
#             f"sections_json: {m.get('raw_sections')}\n"
#             f"text: {c['text'][:3000]}\n"
#         )
#     return "\n\n".join(blocks)

# def generate_report(llm: ChatOpenAI, user_q: str, cands: List[Dict[str, Any]]) -> str:
#     if not cands:
#         return FALLBACK_RESPONSE

#     context = build_context(cands)

#     prompt = f"""
# You are an ISO 13485 QMS compliance assistant specialized in Clauses 4, 5, 6, and 7.
# You MUST use ONLY the provided context. Do NOT invent missing information.
# If the requested procedure is not found in context, output exactly:
# {FALLBACK_RESPONSE}

# Return a single Markdown report with headings and subheadings:
# # Procedure Package
# ## Clause Reference(s)
# ## Procedure Name
# ## Document Control Information
# ## Revision Traceability
# ## Purpose
# ## Scope
# ## References
# ## Definitions
# ## Responsibilities
# ## Process Map
# ## Control of Documents
# ## Control of Records
# ## Training
# ## Monitoring and Improvement
# ## Records
# ## Retention

# Only include sections that exist in the context. If missing, omit (do not guess).

# User question:
# {user_q}

# Context:
# {context}

# Write the report now.
# """
#     resp = llm(prompt)
#     return getattr(resp, "content", str(resp)).strip()

# # ---------------------------
# # Sidebar settings
# # ---------------------------
# with st.sidebar:
#     st.header("⚙️ Settings")
#     dataset_path = st.text_input("Dataset JSON path", value=DEFAULT_JSON)
#     persist_dir = st.text_input("Chroma persist dir", value=DEFAULT_PERSIST)
#     collection = st.text_input("Chroma collection", value=DEFAULT_COLLECTION)

#     model_name = st.selectbox("LLM model", ["gpt-4o-mini", "gpt-4o"], index=0)
#     temperature = st.slider("Temperature", 0.0, 0.6, 0.0, 0.05)

#     rebuild_db = st.button("Rebuild Chroma DB")

# # ---------------------------
# # Init: load dataset, build BM25, load/build Chroma
# # ---------------------------
# st.write("📌 Dataset absolute path:", str(Path(dataset_path).resolve()))

# try:
#     entries = load_procedure_dataset(dataset_path)
# except Exception as e:
#     st.error(f"Failed to load dataset: {e}")
#     st.stop()

# texts, metas = entries_to_texts_and_meta(entries)
# bm25 = SimpleBM25(texts, metas)

# embeddings = OpenAIEmbeddings()
# db = build_or_load_chroma(texts, metas, persist_dir, collection, embeddings)

# if rebuild_db:
#     with st.spinner("Rebuilding Chroma..."):
#         db = Chroma.from_texts(
#             texts=texts,
#             embedding=embeddings,
#             metadatas=metas,
#             persist_directory=persist_dir,
#             collection_name=collection,
#         )
#         db.persist()
#     st.success("✅ Chroma rebuilt.")

# llm = ChatOpenAI(model=model_name, temperature=temperature)

# # ---------------------------
# # Main UI
# # ---------------------------
# q = st.text_area("Ask about a procedure or clause (e.g., 'Procedure for Control of Documents and Records' or '4.2.4')", height=140)
# run = st.button("🔎 Run RAG")

# # ---------------------------
# # Hybrid retrieval (BM25 + Chroma MMR)
# # ---------------------------
# def hybrid_search(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
#     # BM25
#     bm_hits = bm25.query(query, k=top_k * 2)
#     max_b = max((h["score"] for h in bm_hits), default=1.0)

#     # Vector MMR
#     retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": top_k, "fetch_k": max(20, top_k * 4), "lambda_mult": 0.6})
#     vec_docs = retriever.get_relevant_documents(query)

#     combined = {}

#     for h in bm_hits:
#         pid = h["meta"]["procedure_id"]
#         combined.setdefault(pid, {"meta": h["meta"], "text": h["text"], "bm25": 0.0, "vec": 0.0})
#         combined[pid]["bm25"] = (h["score"] / max_b) if max_b else 0.0

#     for d in vec_docs:
#         m = d.metadata
#         pid = m.get("procedure_id") or m.get("procedure_name")
#         combined.setdefault(pid, {"meta": m, "text": d.page_content, "bm25": 0.0, "vec": 0.0})
#         combined[pid]["vec"] = max(combined[pid]["vec"], 0.6)  # presence boost (MMR doesn't return scores)

#     # weights
#     out = []
#     for pid, v in combined.items():
#         score = 0.45 * v["bm25"] + 0.55 * v["vec"]
#         out.append({"meta": v["meta"], "text": v["text"], "score": score})

#     out.sort(key=lambda x: x["score"], reverse=True)
#     return out[:top_k]

# # ---------------------------
# # Run pipeline
# # ---------------------------
# if run and q.strip():
#     with st.spinner("Query rewrite + intent detection..."):
#         rewritten = rewrite_query(llm, q)
#         intent = detect_intent(llm, q)
#         clauses = re.findall(CLAUSE_REGEX, q)

#     st.write({"intent": intent, "rewritten": rewritten, "clauses": clauses})

#     with st.spinner("Hybrid retrieval (BM25 + MMR)..."):
#         hits = hybrid_search(rewritten, top_k=8)

#     # If user asked a specific clause, boost docs containing it
#     if clauses:
#         clause = clauses[0]
#         boosted = [h for h in hits if clause in (h["meta"].get("clause_references") or "")]
#         if boosted:
#             hits = boosted + [h for h in hits if h not in boosted]

#     st.markdown("### 📚 Retrieved candidates")
#     for i, h in enumerate(hits, 1):
#         with st.expander(f"{i}. {h['meta'].get('procedure_name')} (score={h['score']:.3f})"):
#             st.json(h["meta"])
#             st.write(h["text"][:2000] + ("..." if len(h["text"]) > 2000 else ""))

#     with st.spinner("Generating structured report..."):
#         report = generate_report(llm, q, hits[:6])

#     st.markdown("### ✅ Procedure Package Report")
#     st.markdown(report)


# app.py
import os, re, json
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from rank_bm25 import BM25Okapi

# ✅ FIX: proper message type for invoke()
from langchain_core.messages import HumanMessage


# ---------- ENV ----------
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found in .env")
    st.stop()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# ---------- UI ----------
st.set_page_config(page_title="ISO 13485 Procedure Assistant", layout="wide")
st.title("📘 ISO 13485 — Procedure Template + Q&A (Perfect Phase 1)")

BASE_DIR = Path(__file__).parent
DEFAULT_JSON = str(BASE_DIR / "data_v3.json")
DEFAULT_PERSIST = str(BASE_DIR / "chroma_qms")
DEFAULT_COLLECTION = "iso13485_procedures"
FALLBACK_RESPONSE = "This procedure is not available in the current ISO 13485 clause dataset."


# ---------- Load dataset ----------
def load_entries(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {p.resolve()}")
    data = json.loads(p.read_text(encoding="utf-8"))

    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        return data["entries"]
    if isinstance(data, dict) and "procedure_name" in data and "sections" in data:
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("Unsupported JSON format. Use {'entries':[...]}")

# ---------- Build retrieval text + metadata ----------
def entries_to_texts_and_meta(entries: List[Dict[str, Any]]):
    texts, metas = [], []
    for i, e in enumerate(entries):
        proc_id = e.get("procedure_id", f"proc_{i}")
        proc_name = e.get("procedure_name", f"Procedure {i}")
        clause_refs = e.get("clause_references", [])
        if isinstance(clause_refs, str):
            clause_refs = [clause_refs]

        retrieval_text = e.get("retrieval_text") or (proc_name + " " + json.dumps(e.get("sections", {}), ensure_ascii=False))
        meta = {
            "procedure_id": proc_id,
            "procedure_name": proc_name,
            "clause_references": ",".join([c.strip() for c in clause_refs if str(c).strip()]),
            "sections_json": json.dumps(e.get("sections", {}), ensure_ascii=False),
            "template_order": json.dumps(e.get("template_order", []), ensure_ascii=False),
        }
        texts.append(retrieval_text)
        metas.append(meta)
    return texts, metas


# ---------- BM25 ----------
class SimpleBM25:
    def __init__(self, texts, metas):
        self.texts, self.metas = texts, metas
        tok = [self._tok(t) for t in texts]
        self.bm25 = BM25Okapi(tok)

    def _tok(self, t: str):
        return [w.lower() for w in re.findall(r"\w+", t)]

    def search(self, q: str, k: int = 6):
        scores = self.bm25.get_scores(self._tok(q))
        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [{"text": self.texts[i], "meta": self.metas[i], "score": float(scores[i])} for i in idxs]


# ---------- Chroma ----------
def build_or_load_chroma(texts, metas, persist_dir, collection, embeddings):
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    try:
        db = Chroma(persist_directory=persist_dir, collection_name=collection, embedding_function=embeddings)
        if db._collection.count() == 0:
            raise Exception("empty")
        return db
    except Exception:
        db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metas,
            persist_directory=persist_dir,
            collection_name=collection,
        )
        db.persist()
        return db


def hybrid_search(bm25: SimpleBM25, db: Chroma, query: str, top_k: int = 6):
    bm_hits = bm25.search(query, k=top_k * 2)
    max_b = max((h["score"] for h in bm_hits), default=1.0)

    retriever = db.as_retriever(search_type="mmr", search_kwargs={"k": top_k, "fetch_k": max(20, top_k * 4), "lambda_mult": 0.6})
    vec_docs = retriever.get_relevant_documents(query)

    combined = {}
    for h in bm_hits:
        pid = h["meta"]["procedure_id"]
        combined.setdefault(pid, {"meta": h["meta"], "bm25": 0.0, "vec": 0.0})
        combined[pid]["bm25"] = (h["score"] / max_b) if max_b else 0.0

    for d in vec_docs:
        m = d.metadata
        pid = m.get("procedure_id") or m.get("procedure_name")
        combined.setdefault(pid, {"meta": m, "bm25": 0.0, "vec": 0.0})
        combined[pid]["vec"] = 1.0  # presence boost

    out = []
    for pid, v in combined.items():
        score = 0.45 * v["bm25"] + 0.55 * v["vec"]
        out.append({"meta": v["meta"], "score": score})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:top_k]


# ---------- Detect "full procedure" intent ----------
FULL_TRIGGERS = [
    "give me the procedure", "full procedure", "procedure of", "sop", "template",
    "how i can do procedure", "how to do procedure", "process", "all sections"
]
def wants_full(q: str) -> bool:
    ql = q.lower()
    return any(t in ql for t in FULL_TRIGGERS)


# ---------- Deterministic renderer (NO summarizing) ----------
def md_escape_title(s: str) -> str:
    return s.replace("\n", " ").strip()

def render_value(v):
    if v is None:
        return "Not specified in dataset."
    if isinstance(v, str):
        return v.strip() if v.strip() else "Not specified in dataset."
    if isinstance(v, list):
        if not v:
            return "Not specified in dataset."
        lines = []
        for item in v:
            if isinstance(item, dict):
                if "role" in item and "responsibility" in item:
                    lines.append(f"- **{item['role']}**: {item['responsibility']}")
                elif "term" in item and "definition" in item:
                    lines.append(f"- **{item['term']}**: {item['definition']}")
                    if "condition" in item:
                        lines.append(f"  - _Condition_: {item['condition']}")
                else:
                    for k, val in item.items():
                        lines.append(f"- **{k}**: {val}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    if isinstance(v, dict):
        if not v:
            return "Not specified in dataset."
        lines = []
        for k, val in v.items():
            if isinstance(val, (dict, list)):
                lines.append(f"### {k.replace('_',' ').title()}\n{render_value(val)}")
            else:
                lines.append(f"- **{k.replace('_',' ').title()}**: {val}")
        return "\n".join(lines)
    return str(v)

def render_full_procedure(meta: Dict[str, Any]) -> str:
    proc_name = meta.get("procedure_name", "Procedure")
    clause_refs = meta.get("clause_references", "")
    sections = json.loads(meta.get("sections_json", "{}"))
    order = json.loads(meta.get("template_order", "[]"))

    md = [f"# {md_escape_title(proc_name)}", f"## Clause References\n{clause_refs or 'Not specified in dataset.'}\n"]
    for item in order:
        title = item.get("title")
        key = item.get("key")
        sec_no = item.get("section_no")
        md.append(f"## {sec_no}. {md_escape_title(title)}" if sec_no else f"## {md_escape_title(title)}")
        md.append(render_value(sections.get(key)))
        md.append("")
    return "\n".join(md).strip()


# ---------- ✅ FIXED Q&A (LangChain invoke + HumanMessage) ----------
def answer_from_json(llm: ChatOpenAI, user_q: str, meta: Dict[str, Any]) -> str:
    proc_name = meta.get("procedure_name", "")
    clause_refs = meta.get("clause_references", "")
    sections_json = meta.get("sections_json", "{}")

    prompt = f"""
You are an ISO 13485 QMS assistant.
Use ONLY the JSON below (do not invent).
If answer not present, respond exactly:
{FALLBACK_RESPONSE}

Procedure: {proc_name}
Clauses: {clause_refs}

JSON:
{sections_json}

User question:
{user_q}

Return a clear answer in Markdown and mention the section name where you found it.
""".strip()

    # ✅ correct for current LangChain behavior
    resp = llm.invoke([HumanMessage(content=prompt)])
    return getattr(resp, "content", str(resp)).strip()


# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    dataset_path = st.text_input("Dataset JSON path", value=DEFAULT_JSON)
    persist_dir = st.text_input("Chroma persist dir", value=DEFAULT_PERSIST)
    collection = st.text_input("Chroma collection", value=DEFAULT_COLLECTION)
    rebuild = st.button("Rebuild Chroma DB")

# ---------- Init ----------
st.write("📌 Dataset path:", str(Path(dataset_path).resolve()))
entries = load_entries(dataset_path)
texts, metas = entries_to_texts_and_meta(entries)

bm25 = SimpleBM25(texts, metas)
embeddings = OpenAIEmbeddings()
db = build_or_load_chroma(texts, metas, persist_dir, collection, embeddings)

if rebuild:
    with st.spinner("Rebuilding Chroma..."):
        db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metas,
            persist_directory=persist_dir,
            collection_name=collection,
        )
        db.persist()
    st.success("✅ Rebuilt.")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

# ---------- Main ----------
q = st.text_area("Ask (Procedure request OR any question)", height=120)
run = st.button("Run")

if run and q.strip():
    # if only one procedure exists -> always use it (Phase 1 stable)
    if len(metas) == 1:
        best_meta = metas[0]
    else:
        hits = hybrid_search(bm25, db, q, top_k=4)
        if not hits:
            st.markdown(FALLBACK_RESPONSE)
            st.stop()
        best_meta = hits[0]["meta"]

    if wants_full(q):
        st.markdown("### ✅ Full Procedure Template (ALL sections)")
        st.markdown(render_full_procedure(best_meta))
    else:
        st.markdown("### ✅ Answer (only from dataset)")
        st.markdown(answer_from_json(llm, q, best_meta))