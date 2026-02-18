# qmsApp.py
import streamlit as st
import os
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# --------------------------
# 1. Load environment variables
# --------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please add it to your .env file as OPENAI_API_KEY.")
    st.stop()

# --------------------------
# 2. Initialize embeddings
# --------------------------
# Use the same embeddings as when the vector store was created
embeddings_model = OpenAIEmbeddings(
    openai_api_key=OPENAI_API_KEY
)  # default model -> text-embedding-3-small (1536-dim)

# --------------------------
# 3. Load Chroma vector store
# --------------------------
persist_directory = "qms_projects/outpot_db"

vectorstore = Chroma(
    persist_directory=persist_directory,
    collection_name="rag_collection",
    embedding_function=embeddings_model
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # return top 3 relevant chunks
)

# --------------------------
# 4. Create prompt template
# --------------------------
# system_prompt = """
# You are an assistant for question-answering tasks about ISO 13485 and QMS.
# Use the following context to answer the question.
# If you don't know the answer, just say you don't know.
# Answer in concise form, using bullet points or numbered list if relevant.
# Limit the answer to 3 sentences maximum.

# Context: {context}
# """

system_prompt = """
You are an assistant for question-answering tasks about ISO 13485 and QMS.
Use the following context to answer the question.
If you don't know the answer, just say you don't know.
Answer in a clear, detailed, and structured way.
Use numbered points (1, 2, 3, 4…) to organize the answer if relevant.
Provide full explanation and context so the user can understand, not just short phrases.

Context: {context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# --------------------------
# 5. Create LLM and RAG chain
# --------------------------
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

# Create document chain
from langchain.chains.combine_documents import create_stuff_documents_chain
document_chain = create_stuff_documents_chain(llm, prompt)

# Create the RAG chain
rag_chain = create_retrieval_chain(retriever, document_chain)

# --------------------------
# 6. Streamlit UI
# --------------------------
st.title("QMS ISO 13485 RAG QA Chatbot")

user_question = st.text_input("Ask a question about ISO 13485 QMS:")

if user_question:
    with st.spinner("Retrieving answer..."):
        result = rag_chain.invoke({"input": user_question})
        answer = result.get("answer", "No answer found.")

    st.subheader("Answer:")
    st.write(answer)

    # Optional: show retrieved context
    # if st.checkbox("Show retrieved context"):
    #     st.subheader("Retrieved Chunks:")
    #     for i, doc in enumerate(result.get("context", [])):
    #         st.markdown(f"**Chunk {i+1}:**")
    #         st.text(doc.page_content)
