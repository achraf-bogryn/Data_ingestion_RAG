# # app_rag_streamlit.py
# import os
# import streamlit as st
# from dotenv import load_dotenv
# from langchain_community.vectorstores import Chroma
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain.chains import create_retrieval_chain
# from langchain_core.prompts import ChatPromptTemplate

# # -------------------------
# # 1️⃣ Load .env and API Keys safely
# # -------------------------
# load_dotenv()  # Loads keys from .env

# openai_key = os.getenv("OPENAI_API_KEY")
# groq_key = os.getenv("GROQ_API_KEY")

# if openai_key is None:
#     raise ValueError("OPENAI_API_KEY is missing in your .env file.")
# if groq_key is None:
#     raise ValueError("GROQ_API_KEY is missing in your .env file.")

# # Set environment variables for libraries
# os.environ["OPENAI_API_KEY"] = openai_key
# os.environ["GROQ_API_KEY"] = groq_key

# st.success("✅ API keys loaded successfully.")

# # -------------------------
# # 2️⃣ Load existing Chroma vector store
# # -------------------------
# persist_directory = ".././chroma_db"
# embeddings = OpenAIEmbeddings()

# try:
#     vectorstore = Chroma(
#         persist_directory=persist_directory,
#         embedding_function=embeddings,
#         collection_name="rag_collection"
#     )
#     st.success(f"Vector store loaded with {vectorstore._collection.count()} vectors!")
# except Exception as e:
#     st.error(f"Error loading vector store: {e}")
#     st.stop()

# # -------------------------
# # 3️⃣ Initialize LLM
# # -------------------------
# llm = ChatOpenAI(model="gpt-4o", temperature=0)

# # -------------------------
# # 4️⃣ Define expanded ISO 13485 system prompt
# # -------------------------
# system_prompt = """
# You are a regulatory compliance assistant specialized in ISO 13485:2016 and Quality Management Systems (QMS).

# You must answer strictly based on the retrieved context provided below.

# Rules:
# - Use ONLY the information found in the context.
# - Do NOT add external knowledge.
# - Do NOT assume missing information.
# - If the answer is not explicitly available in the context, say:
#   "The requested information is not available in the provided ISO 13485 context."
# - Clearly reference the relevant ISO 13485 clause number in your answer.
# - Use professional regulatory and compliance language suitable for regulatory documentation.
# - Organize the answer in numbered points (1-, 2-, 3-, etc.).
# - When appropriate, group information under clear headings (e.g., Summary, Requirements, Required Documents, Required Records, Responsibilities).
# - Provide detailed explanations for each point to enhance understanding, but remain strictly within the context.
# - Where possible, elaborate on implications, steps, or conditions described in the context, without introducing external knowledge.
# - Highlight any critical compliance obligations, mandatory actions, or key considerations indicated in the context.
# - Ensure that the answer is comprehensive, clear, and suitable for inclusion in QMS compliance reports.
# - Expand on each relevant point sufficiently to help the reader fully understand the requirement or procedure.

# Retrieved Context:
# {context}
# """

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "{input}")
# ])

# # -------------------------
# # 5️⃣ Create document chain
# # -------------------------
# document_chain = create_stuff_documents_chain(llm, prompt)

# # -------------------------
# # 6️⃣ Create RAG chain
# # -------------------------
# retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
# rag_chain = create_retrieval_chain(retriever, document_chain)

# # -------------------------
# # 7️⃣ Streamlit UI
# # -------------------------
# st.title("ISO 13485 QMS Assistant (RAG)")

# user_question = st.text_input("Ask your question about ISO 13485:")

# if user_question:
#     with st.spinner("Searching and generating answer..."):
#         result = rag_chain.invoke({"input": user_question})
#         st.subheader("Answer:")
#         st.write(result["output"])


# # procedeur.py
# import os
# import streamlit as st
# from dotenv import load_dotenv
# from langchain_community.vectorstores import Chroma
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain.chains import create_retrieval_chain
# from langchain_core.prompts import ChatPromptTemplate

# # -------------------------
# # 1️⃣ Load .env and API keys safely
# # -------------------------
# load_dotenv()

# openai_key = os.getenv("OPENAI_API_KEY")
# groq_key = os.getenv("GROQ_API_KEY")

# if openai_key is None:
#     raise ValueError("OPENAI_API_KEY is missing in your .env file.")
# if groq_key is None:
#     raise ValueError("GROQ_API_KEY is missing in your .env file.")

# os.environ["OPENAI_API_KEY"] = openai_key
# os.environ["GROQ_API_KEY"] = groq_key

# st.success("✅ API keys loaded successfully.")

# # -------------------------
# # 2️⃣ Load existing Chroma vector store
# # -------------------------
# persist_directory = os.path.join(os.path.dirname(__file__), "chroma_db")
# embeddings = OpenAIEmbeddings()

# if not os.path.exists(persist_directory):
#     st.error(f"Vector store folder not found at {persist_directory}.")
#     st.stop()

# vectorstore = Chroma(
#     persist_directory=persist_directory,
#     embedding_function=embeddings,
#     collection_name="rag_collection"
# )

# vector_count = vectorstore._collection.count()
# st.write(f"🎯 Total vectors in vector store: {vector_count}")

# if vector_count == 0:
#     st.warning("Vector store is empty. Please make sure it was persisted correctly.")
#     st.stop()

# # -------------------------
# # 3️⃣ Initialize LLM
# # -------------------------
# llm = ChatOpenAI(model="gpt-4o", temperature=0)

# # -------------------------
# # 4️⃣ Define ISO 13485 system prompt
# # -------------------------
# system_prompt = """
# You are a regulatory compliance assistant specialized in ISO 13485:2016 and Quality Management Systems (QMS).

# You must answer strictly based on the retrieved context provided below.

# Rules:
# - Use ONLY the information found in the context.
# - Do NOT add external knowledge.
# - Do NOT assume missing information.
# - If the answer is not explicitly available in the context, say:
#   "The requested information is not available in the provided ISO 13485 context."
# - Clearly reference the relevant ISO 13485 clause number in your answer.
# - Use professional regulatory and compliance language suitable for regulatory documentation.
# - Organize the answer in numbered points (1-, 2-, 3-, etc.).
# - When appropriate, group information under clear headings (e.g., Summary, Requirements, Required Documents, Required Records, Responsibilities).
# - Provide detailed explanations for each point to enhance understanding, but remain strictly within the context.
# - Where possible, elaborate on implications, steps, or conditions described in the context, without introducing external knowledge.
# - Highlight any critical compliance obligations, mandatory actions, or key considerations indicated in the context.
# - Ensure that the answer is comprehensive, clear, and suitable for inclusion in QMS compliance reports.
# - Expand on each relevant point sufficiently to help the reader fully understand the requirement or procedure.

# Retrieved Context:
# {context}
# """

# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     ("human", "{input}")
# ])

# # -------------------------
# # 5️⃣ Create document chain
# # -------------------------
# document_chain = create_stuff_documents_chain(llm, prompt)

# # -------------------------
# # 6️⃣ Create RAG chain using retriever only
# # -------------------------
# retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
# rag_chain = create_retrieval_chain(retriever, document_chain)

# # -------------------------
# # 7️⃣ Streamlit UI
# # -------------------------
# st.title("ISO 13485 QMS Assistant (RAG)")

# user_question = st.text_input("Ask your question about ISO 13485:")

# if user_question:
#     with st.spinner("Searching and generating answer..."):
#         result = rag_chain.invoke({"input": user_question})

#         # LangChain 1.2.9 invoke() may return a string directly or dict
#         if isinstance(result, dict) and "output" in result:
#             answer = result["output"]
#         else:
#             answer = result

#         st.subheader("Answer:")
#         st.write(answer)

# procedeur_clean_text.py
import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# -------------------------
# 1️⃣ Load .env API keys
# -------------------------
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

if not openai_key:
    raise ValueError("OPENAI_API_KEY missing in .env")
if not groq_key:
    raise ValueError("GROQ_API_KEY missing in .env")

os.environ["OPENAI_API_KEY"] = openai_key
os.environ["GROQ_API_KEY"] = groq_key

st.success("✅ API keys loaded successfully.")

# -------------------------
# 2️⃣ Load existing Chroma vector store
# -------------------------
persist_directory = os.path.join(os.path.dirname(__file__), "chroma_db")
embeddings = OpenAIEmbeddings()

if not os.path.exists(persist_directory):
    st.error(f"Vector store folder not found at {persist_directory}")
    st.stop()

try:
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name="rag_collection"
    )
    vector_count = vectorstore._collection.count()
    st.write(f"🎯 Total vectors in vector store: {vector_count}")
    if vector_count == 0:
        st.warning("Vector store is empty. Please ensure it was persisted correctly.")
        st.stop()
except Exception as e:
    st.error(f"Error loading vector store: {e}")
    st.stop()

# -------------------------
# 3️⃣ Initialize LLM
# -------------------------
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_key)

# -------------------------
# 4️⃣ Define QMS prompt (clean readable text, numbered paragraphs)
# -------------------------
system_prompt = """
You are a regulatory compliance assistant specialized in ISO 13485:2016 and Quality Management Systems (QMS).

Rules:
- Answer strictly based on the retrieved context.
- Organize the answer in **clear numbered sections or paragraphs  as section start by .**.
- Each section should be a readable paragraph explaining the concept in full sentences.
- Include subsections when appropriate (e.g., Purpose, Scope, Definitions).
- Do not include any metadata, JSON, or code formatting in your answer.
- If information is not found in context, respond: 
  "The requested information is not available in the provided ISO 13485 context."

Context:
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# -------------------------
# 5️⃣ Create document chain
# -------------------------
document_chain = create_stuff_documents_chain(llm, prompt)

# -------------------------
# 6️⃣ Create RAG chain using retriever only
# -------------------------
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
rag_chain = create_retrieval_chain(retriever, document_chain)

# -------------------------
# 7️⃣ Streamlit UI
# -------------------------
st.title("ISO 13485 QMS Assistant (Clean Text Output)")

user_question = st.text_input("Ask your question about ISO 13485:")

if user_question:
    with st.spinner("Retrieving relevant documents and generating answer..."):
        result = rag_chain.invoke({"input": user_question})

        # Get plain text answer only
        if isinstance(result, dict):
            answer = result.get("answer") or result.get("output") or str(result)
        else:
            answer = str(result)

        # Display as readable markdown (numbered paragraphs)
        st.subheader("Answer:")
        st.markdown(answer)
