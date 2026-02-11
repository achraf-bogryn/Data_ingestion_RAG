import os
import streamlit as st
from dotenv import load_dotenv

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


# =====================================================
# 1️⃣ Load Environment
# =====================================================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found in .env file")
    st.stop()


# =====================================================
# 2️⃣ Professional Light CSS Styling
# =====================================================
st.markdown("""
<style>
.main-title {
    font-size: 38px;
    font-weight: 700;
    color: #1f4e79;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 18px;
    color: #4a4a4a;
    margin-bottom: 25px;
}

.answer-box {
    background-color: #f4f7fb;
    padding: 25px;
    border-radius: 10px;
    border-left: 5px solid #1f4e79;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
    font-size: 16px;
    line-height: 1.7;
}

.stTextArea textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3️⃣ Header
# =====================================================
st.markdown('<div class="main-title">AI Expert Document Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Advanced Retrieval-Augmented Analysis using ChromaDB</div>', unsafe_allow_html=True)


# =====================================================
# 4️⃣ Load Existing Chroma DB
# =====================================================
@st.cache_resource
def load_vectorstore():
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    return vectorstore


vectorstore = load_vectorstore()

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)


# =====================================================
# 5️⃣ LLM
# =====================================================
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2
)


# =====================================================
# 6️⃣ AI Expert Prompt
# =====================================================
prompt = ChatPromptTemplate.from_template("""
You are an Expert AI Systems Architect and Intelligent Document Analysis Specialist.

You specialize in:
- Retrieval-Augmented Generation (RAG)
- Regulatory and structured documentation analysis
- Risk and compliance reasoning
- Executive-level technical reporting

Your mission:
Deliver a precise, analytical, and structured response based strictly on the provided context.

Instructions:

1. Use ONLY the information available in the context.
2. Do NOT fabricate or assume missing information.
3. If the answer is not contained in the context, respond clearly:
   "The requested information is not available in the provided documentation."
4. Think critically and synthesize insights instead of copying text.
5. Structure your answer using:

### 1. Core Analysis
Provide a concise explanation of the relevant concepts.

### 2. Technical or Operational Implications
Explain impact, risks, or system considerations.

### 3. Strategic Insight
Provide higher-level reasoning or architectural implications when applicable.

Tone:
- Professional
- Analytical
- Structured
- Clear and precise

Context:
{context}

Question:
{input}

Answer:
""")


# =====================================================
# 7️⃣ Chains
# =====================================================
document_chain = create_stuff_documents_chain(llm, prompt)

retrieval_chain = create_retrieval_chain(
    retriever,
    document_chain
)


# =====================================================
# 8️⃣ Question Input
# =====================================================
question = st.text_area("Ask a technical or strategic question:")

if question:
    with st.spinner("Generating expert analysis..."):
        response = retrieval_chain.invoke({"input": question})

    st.markdown("### 📌 Expert Analysis")
    st.markdown(f'<div class="answer-box">{response["answer"]}</div>', unsafe_allow_html=True)
