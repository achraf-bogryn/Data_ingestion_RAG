import os
import re
import streamlit as st
from dotenv import load_dotenv

from langchain.document_loaders import PyPDFLoader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


# ==========================================
# Load API Key
# ==========================================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY not found in .env file")
    st.stop()


# ==========================================
# Streamlit UI
# ==========================================
st.set_page_config(page_title="ISO RAG Assistant", layout="wide")
st.title("📘 ISO Quality Management RAG Assistant")
st.write("Upload an ISO PDF document and ask questions.")


# ==========================================
# Cleaning Function
# ==========================================
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\.,;:()\-/]", "", text)
    text = re.sub(r"Page\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\d+\s*/\s*\d+", "", text)
    return text.strip()


def load_and_clean_pdf(uploaded_file):
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    loader = PyPDFLoader("temp.pdf")
    documents = loader.load()

    cleaned_docs = []
    for doc in documents:
        cleaned_docs.append(
            Document(
                page_content=clean_text(doc.page_content),
                metadata=doc.metadata
            )
        )

    return cleaned_docs


# ==========================================
# Build RAG System
# ==========================================
def build_rag(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    splits = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.from_documents(
        documents=splits,
        embedding=embeddings
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_template("""
You are an ISO Quality Management expert.

Answer the question using ONLY the provided context.
If the answer is not found, say:
"The requested information is not available in the provided ISO documentation."

Provide:
- A structured paragraph
- Professional tone
- Friendly and formal style

Context:
{context}

Question:
{input}

Answer:
""")

    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    return retrieval_chain


# ==========================================
# File Upload
# ==========================================
uploaded_file = st.file_uploader("Upload ISO PDF", type=["pdf"])

if uploaded_file:

    if "rag_chain" not in st.session_state:
        with st.spinner("Processing document and building RAG system..."):
            documents = load_and_clean_pdf(uploaded_file)
            st.session_state.rag_chain = build_rag(documents)

        st.success("RAG system ready!")

    question = st.text_input("Ask a question about the ISO document:")

    if question:
        with st.spinner("Generating answer..."):
            response = st.session_state.rag_chain.invoke({"input": question})

        st.markdown("### 📌 Answer")
        st.write(response["answer"])
