# # qmsApp_fixed.py
# import streamlit as st
# import os
# import json
# from dotenv import load_dotenv

# from langchain.schema import Document
# from langchain.vectorstores import Chroma
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.chat_models import ChatOpenAI

# # ---------------------------------------------------
# # LOAD ENVIRONMENT
# # ---------------------------------------------------
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# if not OPENAI_API_KEY:
#     st.error("OPENAI_API_KEY not found in environment.")
#     st.stop()

# # ---------------------------------------------------
# # PATH HANDLING
# # ---------------------------------------------------
# DATA_PATH = "qms_projects/data/data.json"
# PERSIST_PATH = "qms_projects/vector_claude"

# # ---------------------------------------------------
# # LOAD JSON SAFELY
# # ---------------------------------------------------
# if not os.path.exists(DATA_PATH):
#     st.error(f"Data file not found at: {DATA_PATH}")
#     st.stop()

# with open(DATA_PATH, "r", encoding="utf-8") as f:
#     iso_data = json.load(f)

# st.write("✅ JSON loaded successfully.")

# # ---------------------------------------------------
# # FLATTEN PROCEDURES (FIXED)
# # ---------------------------------------------------
# def flatten_procedures(data):
#     documents = []
#     sections = data.get("sections", [])

#     for section in sections:
#         section_id = section.get("section_id", "")
#         section_name = section.get("section_name", "")
#         section_desc = section.get("description", "")

#         # Handle sections with subsections
#         for subsection in section.get("subsections", []):
#             subsection_id = subsection.get("subsection_id", "")
#             subsection_name = subsection.get("subsection_name", "")
#             subsection_desc = subsection.get("description", "")

#             for proc in subsection.get("procedures", []):
#                 requirements = proc.get("what_is_required", "")

#                 text = f"""
# Section {section_id} - {section_name}
# Subsection {subsection_id} - {subsection_name}

# Procedure ID: {proc.get("proc_id")}
# Title: {proc.get("title")}

# Description:
# {subsection_desc}

# Requirements:
# {requirements}

# Key Requirements:
# {', '.join(proc.get('key_requirements', []))}

# Implementation Steps:
# {', '.join(proc.get('implementation_steps', []))}

# Responsibilities:
# {', '.join(proc.get('responsibilities', []))}

# Documentation Needed:
# {', '.join(proc.get('documentation_needed', []))}

# Examples:
# {proc.get('examples', '')}

# Regulatory References:
# {', '.join(proc.get('regulatory_references', []))}
# """

#                 documents.append(
#                     Document(
#                         page_content=text.strip(),
#                         metadata={
#                             "proc_id": proc.get("proc_id"),
#                             "section": section_id,
#                             "subsection": subsection_id,
#                             "title": proc.get("title")
#                         }
#                     )
#                 )

#         # Optional: Handle sections with procedures directly (some sections may not have subsections)
#         for proc in section.get("procedures_in_section", []):
#             # Simple placeholder text, since we only have proc IDs in this case
#             text = f"Section {section_id} - {section_name}\nProcedure ID: {proc}"
#             documents.append(
#                 Document(
#                     page_content=text.strip(),
#                     metadata={"proc_id": proc, "section": section_id, "subsection": None, "title": ""}
#                 )
#             )

#     return documents


# documents = flatten_procedures(iso_data)

# if len(documents) == 0:
#     st.error("No documents were created from JSON. Check structure.")
#     st.stop()

# st.write(f"✅ {len(documents)} documents created for RAG.")

# # ---------------------------------------------------
# # EMBEDDINGS
# # ---------------------------------------------------
# embedding = OpenAIEmbeddings()

# # Test embedding
# try:
#     test_vec = embedding.embed_query("ISO test")
# except Exception as e:
#     st.error(f"Embedding failed: {e}")
#     st.stop()

# # ---------------------------------------------------
# # VECTORSTORE (LOAD OR CREATE)
# # ---------------------------------------------------
# if os.path.exists(PERSIST_PATH):
#     vectorstore = Chroma(
#         persist_directory=PERSIST_PATH,
#         embedding_function=embedding
#     )
# else:
#     vectorstore = Chroma.from_documents(
#         documents,
#         embedding,
#         persist_directory=PERSIST_PATH
#     )
#     vectorstore.persist()

# retriever = vectorstore.as_retriever(
#     search_type="mmr",
#     search_kwargs={"k": 5, "fetch_k": 20}
# )

# # ---------------------------------------------------
# # LLM
# # ---------------------------------------------------
# llm = ChatOpenAI(
#     model="gpt-4",
#     temperature=0
# )

# # ---------------------------------------------------
# # QUERY REWRITE
# # ---------------------------------------------------
# def clean_query(user_query):
#     prompt = f"""
# Rewrite this ISO 13485 compliance question clearly and professionally:

# Question:
# {user_query}

# Rewritten:
# """
#     return llm.predict(prompt).strip()

# # ---------------------------------------------------
# # DIRECT SECTION LOOKUP
# # ---------------------------------------------------
# def direct_section_lookup(query):
#     query_lower = query.lower()

#     for section in iso_data.get("sections", []):
#         section_id = section.get("section_id")
#         if section_id and f"section {section_id}" in query_lower:
#             return section

#     return None

# # ---------------------------------------------------
# # GENERATE STRUCTURED ANSWER
# # ---------------------------------------------------
# def generate_answer(query, docs):
#     context = "\n\n".join([doc.page_content for doc in docs])

#     prompt = f"""
# You are an ISO 13485 compliance expert.

# Using the context below, answer professionally.

# Structure your answer:

# 1. Relevant Procedures
# 2. Explanation
# 3. Key Requirements
# 4. Practical Implementation Guidance

# Context:
# {context}

# Question:
# {query}

# Answer:
# """
#     return llm.predict(prompt)

# # ---------------------------------------------------
# # STREAMLIT UI
# # ---------------------------------------------------
# st.title("🧠 Smart ISO 13485 RAG Assistant")

# query = st.text_input("Ask about ISO 13485 procedures")

# if query:
#     with st.spinner("Analyzing..."):

#         cleaned_query = clean_query(query)

#         section_match = direct_section_lookup(cleaned_query)

#         if section_match:
#             st.subheader(f"Section {section_match.get('section_id')} Overview")
#             st.json(section_match)

#         else:
#             docs = retriever.get_relevant_documents(cleaned_query)
#             answer = generate_answer(cleaned_query, docs)
#             st.markdown(answer)

# qmsApp_rag_actionable.py
import streamlit as st
import os
import json
from dotenv import load_dotenv

from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

# ---------------------------------------------------
# LOAD ENVIRONMENT
# ---------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY not found in environment.")
    st.stop()

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
DATA_PATH = "qms_projects/data/data.json"
PERSIST_PATH = "qms_projects/vector_claude"

# ---------------------------------------------------
# LOAD ISO JSON
# ---------------------------------------------------
if not os.path.exists(DATA_PATH):
    st.error(f"Data file not found at: {DATA_PATH}")
    st.stop()

with open(DATA_PATH, "r", encoding="utf-8") as f:
    iso_data = json.load(f)

# ---------------------------------------------------
# FLATTEN PROCEDURES FOR VECTORSTORE
# ---------------------------------------------------
def flatten_procedures(data):
    documents = []
    for section in data.get("sections", []):
        section_id = section.get("section_id", "")
        section_name = section.get("section_name", "")

        for subsection in section.get("subsections", []):
            subsection_id = subsection.get("subsection_id", "")
            subsection_name = subsection.get("subsection_name", "")

            for proc in subsection.get("procedures", []):
                text = f"""
Procedure: {proc.get('title')} ({proc.get('proc_id')})

Section: {section_id} - {section_name}
Subsection: {subsection_id} - {subsection_name}

Requirements:
{proc.get('what_is_required', '')}

Key Requirements:
{', '.join(proc.get('key_requirements', []))}

Implementation Steps:
{', '.join(proc.get('implementation_steps', []))}

Documentation Needed:
{', '.join(proc.get('documentation_needed', []))}

Responsibilities:
{', '.join(proc.get('responsibilities', []))}
"""
                documents.append(
                    Document(
                        page_content=text.strip(),
                        metadata={
                            "proc_id": proc.get("proc_id"),
                            "title": proc.get("title"),
                            "section": section_id,
                            "subsection": subsection_id,
                            "key_requirements": proc.get('key_requirements', []),
                            "implementation_steps": proc.get('implementation_steps', []),
                            "documentation_needed": proc.get('documentation_needed', []),
                            "responsibilities": proc.get('responsibilities', [])
                        }
                    )
                )
    return documents

documents = flatten_procedures(iso_data)
if len(documents) == 0:
    st.error("No procedures found in JSON.")
    st.stop()

# ---------------------------------------------------
# EMBEDDINGS & VECTORSTORE
# ---------------------------------------------------
embedding = OpenAIEmbeddings()

if os.path.exists(PERSIST_PATH):
    vectorstore = Chroma(
        persist_directory=PERSIST_PATH,
        embedding_function=embedding
    )
else:
    vectorstore = Chroma.from_documents(
        documents,
        embedding,
        persist_directory=PERSIST_PATH
    )
    vectorstore.persist()

retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k":5, "fetch_k":20})

# ---------------------------------------------------
# LLM
# ---------------------------------------------------
llm = ChatOpenAI(model="gpt-4", temperature=0)

# ---------------------------------------------------
# QUERY REFORMULATION
# ---------------------------------------------------
def clean_query(user_query):
    prompt = f"""
Rewrite this ISO 13485 question clearly and professionally:

Question:
{user_query}

Rewritten:
"""
    return llm.predict(prompt).strip()

# ---------------------------------------------------
# DIRECT CLAUSE LOOKUP
# ---------------------------------------------------
def direct_clause_lookup(query):
    query_lower = query.lower()
    for section in iso_data.get("sections", []):
        section_id = section.get("section_id", "")
        if f"section {section_id}" in query_lower or section.get("section_name","").lower() in query_lower:
            return section
        for subsection in section.get("subsections", []):
            subsection_id = subsection.get("subsection_id", "")
            if f"{subsection_id}" in query_lower or subsection.get("subsection_name","").lower() in query_lower:
                return subsection
    return None

# ---------------------------------------------------
# STRUCTURED PROCEDURE MATCHING
# ---------------------------------------------------
def extract_procedures_from_docs(docs):
    procedures = []
    for doc in docs:
        procedures.append({
            "title": doc.metadata.get("title"),
            "key_requirements": doc.metadata.get("key_requirements", []),
            "implementation_steps": doc.metadata.get("implementation_steps", []),
            "documentation_needed": doc.metadata.get("documentation_needed", []),
            "responsibilities": doc.metadata.get("responsibilities", [])
        })
    return procedures

# ---------------------------------------------------
# GENERATE ISO-STYLE ANSWER
# ---------------------------------------------------
def generate_actionable_answer(query):
    # 1️⃣ Direct lookup
    clause_match = direct_clause_lookup(query)
    if clause_match:
        if "procedures" in clause_match:
            procedures = clause_match["procedures"]
            st.subheader(f"Direct lookup: {clause_match.get('subsection_name', clause_match.get('section_name',''))}")
            for proc in procedures:
                st.markdown(f"### {proc['title']} ({proc['proc_id']})")
                st.markdown(f"**Requirements:** {proc.get('what_is_required','')}")
                st.markdown("**Key Requirements:**")
                for kr in proc.get('key_requirements', []):
                    st.markdown(f"- {kr}")
                st.markdown("**Implementation Steps:**")
                for step in proc.get('implementation_steps', []):
                    st.markdown(f"- {step}")
                st.markdown("**Documentation Needed:**")
                for doc in proc.get('documentation_needed', []):
                    st.markdown(f"- {doc}")
                st.markdown("**Responsibilities:**")
                for r in proc.get('responsibilities', []):
                    st.markdown(f"- {r}")
                st.markdown("---")
        else:
            st.info("No procedures defined in this clause/subsection.")
        return

    # 2️⃣ Hybrid Retrieval
    docs = retriever.get_relevant_documents(query)
    procedures = extract_procedures_from_docs(docs)
    if len(procedures) == 0:
        st.warning("No procedures found for this query.")
        return

    # 3️⃣ Rerank via LLM reasoning
    context = "\n\n".join([f"{p['title']} - {p['key_requirements']}" for p in procedures])
    prompt = f"""
You are an ISO 13485 expert assistant.

Given the following procedures context:

{context}

User Query:
{query}

Rank and return the **most relevant procedures** for this query along with all actionable steps, required documentation, key requirements, and responsibilities in markdown format.
"""
    answer = llm.predict(prompt)
    st.markdown(answer)

# ---------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------
st.title("🧠 Smart ISO 13485 RAG Procedure Assistant")
user_query = st.text_input("Ask about a procedure or QMS topic:")

if user_query:
    with st.spinner("Processing your request..."):
        cleaned_query = clean_query(user_query)
        generate_actionable_answer(cleaned_query)