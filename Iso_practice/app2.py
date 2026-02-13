# app_modern_rag_word_final.py
import streamlit as st
import os
from dotenv import load_dotenv

# LangChain imports
from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 0️⃣ Load .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env")

# 1️⃣ Streamlit UI
st.set_page_config(page_title="Modern RAG Word", layout="wide")
st.title("📄 Modern RAG - Word (.docx) Question Answering")

uploaded_file = st.file_uploader("Upload Word Document (.docx)", type=["docx"])

if uploaded_file:

    # Save uploaded file temporarily
    with open("temp.docx", "wb") as f:
        f.write(uploaded_file.read())

    st.info("Loading Word document...")

    # 2️⃣ Load DOCX
    loader = UnstructuredWordDocumentLoader("temp.docx")
    documents = loader.load()
    st.success(f"Loaded {len(documents)} document chunks")

    # 3️⃣ Split text recursively
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    docs_split = text_splitter.split_documents(documents)
    st.success(f"Split into {len(docs_split)} chunks for embeddings")

    # 4️⃣ Create embeddings + Chroma vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        docs_split,
        embeddings,
        persist_directory="./chroma_db"
    )
    vectorstore.persist()
    st.success("ChromaDB vectorstore created and persisted!")

    # 5️⃣ Build Retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # 6️⃣ Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 7️⃣ Create ChatPromptTemplate for your QMS/ISO 13485 project
    system_prompt = """You are an assistant for question-answering tasks on Quality Management Systems (QMS) and ISO 13485:2016. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Use three sentences maximum and keep the answer concise.

Context: {context}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    # 8️⃣ Create stuff_documents_chain with the ChatPromptTemplate
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt
    )

    # 9️⃣ Modern RAG retrieval chain
    rag_chain = create_retrieval_chain(
        retriever,
        document_chain
    )

    # 10️⃣ Query input
    query = st.text_input("Ask a question about the Word document:")

    if query:
        # Modern chain returns a string directly
        response = rag_chain.invoke({"input": query})
        st.markdown("### 📌 Answer")
        st.write(response["answer"])
