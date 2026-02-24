import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import streamlit as st
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from rank_bm25 import BM25Okapi

# ---------------------------
# Load .env
# ---------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found in .env. Put it in a file named .env in your project root.")
    st.stop()
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ---------------------------
# UI
# ---------------------------
st.set_page_config(page_title="ISO 13485 QMS RAG", layout="wide")
st.title("📘 ISO 13485 — QMS Procedure RAG (Chroma + BM25 + MMR)")

BASE_DIR = Path(__file__).parent
DEFAULT_JSON = str(BASE_DIR / "data.json")
DEFAULT_PERSIST = str(BASE_DIR / "chroma_qms")
DEFAULT_COLLECTION = "iso13485_procedures"

CLAUSE_REGEX = r"\b([4-7]\.\d+(?:\.\d+)*)\b"
FALLBACK_RESPONSE = "This procedure is not available in the current ISO 13485 clause dataset."

# ---------------------------
# Dataset loader (expects {"entries":[...]} but also supports list/single object)
# ---------------------------
def load_procedure_dataset(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset JSON not found at: {p.resolve()}")

    with p.open("r", encoding="utf-8") as f:
        j = json.load(f)

    # Root list
    if isinstance(j, list) and len(j) > 0:
        return j

    # Root dict
    if isinstance(j, dict):
        for key in ("entries", "procedures", "data"):
            if key in j and isinstance(j[key], list) and len(j[key]) > 0:
                return j[key]

        # Single procedure object -> wrap
        if "procedure_name" in j and ("sections" in j or "retrieval_text" in j):
            return [j]

    raise ValueError(
        "JSON structure not recognized.\n"
        "Expected either:\n"
        "- A root list: [ {...}, {...} ]\n"
        "- Or an object with key entries/procedures/data containing a list\n"
        "- Or a single procedure object with procedure_name + sections/retrieval_text"
    )

# ---------------------------
# Convert entries -> texts + metadatas
# ---------------------------
def entries_to_texts_and_meta(entries: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    texts, metas = [], []

    for i, e in enumerate(entries):
        retrieval_text = e.get("retrieval_text")
        if not retrieval_text:
            retrieval_text = json.dumps(e.get("sections", e), ensure_ascii=False)

        clause_refs = e.get("clause_references") or e.get("clause_reference") or []
        if isinstance(clause_refs, str):
            clause_refs = [clause_refs]

        procedure_id = e.get("procedure_id") or e.get("id") or f"proc_{i}"
        procedure_name = e.get("procedure_name") or e.get("title") or f"Procedure {i}"

        meta_block = {
            "procedure_id": procedure_id,
            "procedure_name": procedure_name,
            "clause_references": ",".join([str(c).strip() for c in clause_refs if str(c).strip()]),
            "raw_sections": json.dumps(e.get("sections", e), ensure_ascii=False),
        }

        # include extra metadata if present
        md = e.get("metadata") or {}
        for k in ("domain", "process_area", "language", "output_mode"):
            if k in md:
                meta_block[k] = md[k]

        texts.append(retrieval_text)
        metas.append(meta_block)

    return texts, metas

# ---------------------------
# BM25
# ---------------------------
class SimpleBM25:
    def __init__(self, texts: List[str], metas: List[Dict[str, Any]]):
        self.docs = texts
        self.metas = metas
        tokenized = [self._tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(tokenized)

    def _tokenize(self, t: str):
        return [w.lower() for w in re.findall(r"\w+", t)]

    def query(self, q: str, k: int = 6):
        tokens = self._tokenize(q)
        scores = self.bm25.get_scores(tokens)
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        out = []
        for i in top_idx:
            out.append({"text": self.docs[i], "meta": self.metas[i], "score": float(scores[i])})
        return out

# ---------------------------
# Chroma load/build
# ---------------------------
def build_or_load_chroma(texts, metas, persist_dir, collection, embeddings) -> Chroma:
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    try:
        db = Chroma(
            persist_directory=persist_dir,
            collection_name=collection,
            embedding_function=embeddings,
        )
        if db._collection.count() == 0:
            raise Exception("Empty collection")
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

# ---------------------------
# LLM helpers
# ---------------------------
def rewrite_query(llm: ChatOpenAI, q: str) -> str:
    prompt = (
        "Rewrite the user question for best retrieval over a QMS procedure dataset. "
        "Keep clause numbers, procedure names, and key terms. Return ONLY the rewritten query.\n\n"
        f"User: {q}\nRewrite:"
    )
    resp = llm(prompt)
    return getattr(resp, "content", str(resp)).strip()

def detect_intent(llm: ChatOpenAI, q: str) -> str:
    prompt = (
        "Classify intent into one label only: PROCEDURE_REQUEST, CLAUSE_LOOKUP, GENERAL_QMS_QUESTION.\n\n"
        f"User: {q}\nLabel:"
    )
    resp = llm(prompt)
    label = getattr(resp, "content", str(resp)).strip().splitlines()[0].strip()
    if label not in {"PROCEDURE_REQUEST", "CLAUSE_LOOKUP", "GENERAL_QMS_QUESTION"}:
        return "GENERAL_QMS_QUESTION"
    return label

def build_context(cands: List[Dict[str, Any]], max_docs: int = 6) -> str:
    blocks = []
    for i, c in enumerate(cands[:max_docs], 1):
        m = c["meta"]
        blocks.append(
            f"[DOC {i}]\n"
            f"procedure_id: {m.get('procedure_id')}\n"
            f"procedure_name: {m.get('procedure_name')}\n"
            f"clause_references: {m.get('clause_references')}\n"
            f"sections_json: {m.get('raw_sections')}\n"
            f"text: {c['text'][:3000]}\n"
        )
    return "\n\n".join(blocks)

def generate_report(llm: ChatOpenAI, user_q: str, cands: List[Dict[str, Any]]) -> str:
    if not cands:
        return FALLBACK_RESPONSE

    context = build_context(cands)

    prompt = f"""
You are an ISO 13485 QMS compliance assistant specialized in Clauses 4, 5, 6, and 7.
You MUST use ONLY the provided context. Do NOT invent missing information.
If the requested procedure is not found in context, output exactly:
{FALLBACK_RESPONSE}

Return a single Markdown report with headings and subheadings:
# Procedure Package
## Clause Reference(s)
## Procedure Name
## Document Control Information
## Revision Traceability
## Purpose
## Scope
## References
## Definitions
## Responsibilities
## Process Map
## Control of Documents
## Control of Records
## Training
## Monitoring and Improvement
## Records
## Retention

Only include sections that exist in the context. If missing, omit (do not guess).

User question:
{user_q}

Context:
{context}

Write the report now.
"""
    resp = llm(prompt)
    return getattr(resp, "content", str(resp)).strip()

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    dataset_path = st.text_input("Dataset JSON path", value=DEFAULT_JSON)
    persist_dir = st.text_input("Chroma persist dir", value=DEFAULT_PERSIST)
    collection = st.text_input("Chroma collection", value=DEFAULT_COLLECTION)

    model_name = st.selectbox("LLM model", ["gpt-4o-mini", "gpt-4o"], index=0)
    temperature = st.slider("Temperature", 0.0, 0.6, 0.0, 0.05)

    rebuild_db = st.button("Rebuild Chroma DB")

# ---------------------------
# Init
# ---------------------------
st.write("📌 Dataset absolute path:", str(Path(dataset_path).resolve()))

try:
    entries = load_procedure_dataset(dataset_path)
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

texts, metas = entries_to_texts_and_meta(entries)
bm25 = SimpleBM25(texts, metas)

embeddings = OpenAIEmbeddings()
db = build_or_load_chroma(texts, metas, persist_dir, collection, embeddings)

if rebuild_db:
    with st.spinner("Rebuilding Chroma..."):
        db = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metas,
            persist_directory=persist_dir,
            collection_name=collection,
        )
        db.persist()
    st.success("✅ Chroma rebuilt.")

llm = ChatOpenAI(model=model_name, temperature=temperature)

# ---------------------------
# Hybrid search
# ---------------------------
def hybrid_search(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    # BM25
    bm_hits = bm25.query(query, k=top_k * 2)
    max_b = max((h["score"] for h in bm_hits), default=1.0)

    # Vector MMR
    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": top_k, "fetch_k": max(20, top_k * 4), "lambda_mult": 0.6},
    )
    vec_docs = retriever.get_relevant_documents(query)

    combined = {}

    for h in bm_hits:
        pid = h["meta"]["procedure_id"]
        combined.setdefault(pid, {"meta": h["meta"], "text": h["text"], "bm25": 0.0, "vec": 0.0})
        combined[pid]["bm25"] = (h["score"] / max_b) if max_b else 0.0

    for d in vec_docs:
        m = d.metadata
        pid = m.get("procedure_id") or m.get("procedure_name")
        combined.setdefault(pid, {"meta": m, "text": d.page_content, "bm25": 0.0, "vec": 0.0})
        combined[pid]["vec"] = max(combined[pid]["vec"], 0.6)  # MMR retriever doesn't return score

    out = []
    for pid, v in combined.items():
        score = 0.45 * v["bm25"] + 0.55 * v["vec"]
        out.append({"meta": v["meta"], "text": v["text"], "score": score})

    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:top_k]

# ---------------------------
# Main UI
# ---------------------------
q = st.text_area("Ask about a procedure or clause (e.g., 'Procedure for Control of Documents and Records' or '4.2.4')", height=140)
run = st.button("🔎 Run RAG")

if run and q.strip():
    with st.spinner("Query rewrite + intent detection..."):
        rewritten = rewrite_query(llm, q)
        intent = detect_intent(llm, q)
        clauses = re.findall(CLAUSE_REGEX, q)

    st.write({"intent": intent, "rewritten": rewritten, "clauses": clauses})

    with st.spinner("Hybrid retrieval (BM25 + MMR)..."):
        hits = hybrid_search(rewritten, top_k=8)

    if clauses:
        clause = clauses[0]
        boosted = [h for h in hits if clause in (h["meta"].get("clause_references") or "")]
        if boosted:
            hits = boosted + [h for h in hits if h not in boosted]

    st.markdown("### 📚 Retrieved candidates")
    for i, h in enumerate(hits, 1):
        with st.expander(f"{i}. {h['meta'].get('procedure_name')} (score={h['score']:.3f})"):
            st.json(h["meta"])
            st.write(h["text"][:2000] + ("..." if len(h["text"]) > 2000 else ""))

    with st.spinner("Generating structured report..."):
        report = generate_report(llm, q, hits[:6])

    st.markdown("### ✅ Procedure Package Report")
    st.markdown(report)