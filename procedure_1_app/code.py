import streamlit as st
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="ISO 13485 QMS Procedure Guide",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD PROCEDURE DATA
# ============================================================================
@st.cache_resource
def load_procedure_data():
    """Load the JSON procedure database"""
    with open('procedure_1_app\data.json', 'r') as f:
        return json.load(f)

procedure_data = load_procedure_data()
procedure = procedure_data['procedure']

# ============================================================================
# BUILD SEARCHABLE KNOWLEDGE BASE
# ============================================================================
@st.cache_resource
def build_knowledge_base():
    """Create searchable index from procedure data"""
    knowledge_base = []
    
    # Add procedure overview
    knowledge_base.append({
        "id": "overview",
        "type": "overview",
        "title": procedure['title'],
        "content": f"Purpose: {procedure['purpose']}",
        "full_text": f"{procedure['title']}. {procedure['purpose']}"
    })
    
    # Add each section
    for section_num, section_data in procedure['sections'].items():
        content = f"{section_data.get('description', '')}"
        must_contain = ". ".join(section_data.get('must_contain', []))
        example = section_data.get('example_text', '')
        
        knowledge_base.append({
            "id": f"section_{section_num}",
            "type": "section",
            "title": f"Section {section_num}: {section_data['section_title']}",
            "content": content,
            "must_contain": must_contain,
            "example": example,
            "full_text": f"{section_data['section_title']}. {content}. {must_contain}. {example}"
        })
        
        # Add subsections if they exist
        if 'subsections' in section_data:
            for sub_id, subsection_data in section_data['subsections'].items():
                sub_content = subsection_data.get('description', '')
                sub_must_contain = ". ".join(subsection_data.get('must_contain', []))
                sub_example = subsection_data.get('example_text', '')
                
                knowledge_base.append({
                    "id": f"subsection_{sub_id}",
                    "type": "subsection",
                    "title": f"Section {sub_id}: {subsection_data['title']}",
                    "content": sub_content,
                    "must_contain": sub_must_contain,
                    "example": sub_example,
                    "full_text": f"{subsection_data['title']}. {sub_content}. {sub_must_contain}. {sub_example}"
                })
    
    # Add key explanations
    for term, explanation in procedure.get('key_explanations', {}).items():
        knowledge_base.append({
            "id": f"definition_{term}",
            "type": "definition",
            "title": term.replace('_', ' ').title(),
            "content": explanation,
            "full_text": f"{term}. {explanation}"
        })
    
    # Add common mistakes
    for idx, mistake in enumerate(procedure.get('common_mistakes', [])):
        knowledge_base.append({
            "id": f"mistake_{idx}",
            "type": "common_mistake",
            "title": f"Common Mistake {idx + 1}",
            "content": mistake,
            "full_text": mistake
        })
    
    return knowledge_base

knowledge_base = build_knowledge_base()

# ============================================================================
# HYBRID SEARCH IMPLEMENTATION
# ============================================================================
@st.cache_resource
def initialize_search_indices():
    """Initialize BM25 and TF-IDF search indices"""
    texts = [doc['full_text'].lower() for doc in knowledge_base]
    
    # BM25 initialization
    tokenized_texts = [text.split() for text in texts]
    bm25 = BM25Okapi(tokenized_texts)
    
    # TF-IDF initialization
    tfidf = TfidfVectorizer(lowercase=True, stop_words='english')
    tfidf_matrix = tfidf.fit_transform(texts)
    
    return bm25, tfidf, tfidf_matrix, texts

bm25, tfidf, tfidf_matrix, texts = initialize_search_indices()

def hybrid_search(query, top_k=5, bm25_weight=0.6, tfidf_weight=0.4):
    """
    Hybrid search combining BM25 (keyword) and TF-IDF (semantic) search
    
    Args:
        query: User's search query
        top_k: Number of results to return
        bm25_weight: Weight for BM25 results (0-1)
        tfidf_weight: Weight for TF-IDF results (0-1)
    
    Returns:
        List of top k search results with scores
    """
    query_lower = query.lower()
    
    # BM25 search
    tokenized_query = query_lower.split()
    bm25_scores = bm25.get_scores(tokenized_query)
    
    # TF-IDF search
    query_tfidf = tfidf.transform([query_lower])
    tfidf_scores = cosine_similarity(query_tfidf, tfidf_matrix)[0]
    
    # Normalize scores to 0-1 range
    bm25_scores_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-8)
    tfidf_scores_norm = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min() + 1e-8)
    
    # Hybrid score
    hybrid_scores = bm25_weight * bm25_scores_norm + tfidf_weight * tfidf_scores_norm
    
    # Get top k results
    top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
    results = []
    
    for idx in top_indices:
        if hybrid_scores[idx] > 0:  # Only include if score > 0
            results.append({
                "index": int(idx),
                "document": knowledge_base[idx],
                "score": float(hybrid_scores[idx]),
                "bm25_score": float(bm25_scores[idx]),
                "tfidf_score": float(tfidf_scores[idx])
            })
    
    return results

# ============================================================================
# OPENAI GENERATION
# ============================================================================
def generate_response_with_rag(user_query, search_results):
    """
    Generate chatbot response using RAG (Retrieval Augmented Generation)
    
    Args:
        user_query: User's question
        search_results: Retrieved context from hybrid search
    
    Returns:
        Generated response from OpenAI
    """
    # Build context from search results
    context_parts = []
    for result in search_results:
        doc = result['document']
        context_parts.append(f"**{doc['title']}**\n{doc.get('content', '')}")
        if doc.get('must_contain'):
            context_parts.append(f"Must contain: {doc['must_contain']}")
        if doc.get('example'):
            context_parts.append(f"Example: {doc['example']}")
    
    context = "\n\n".join(context_parts)
    
    # System prompt for the chatbot
    system_prompt = """You are an expert in ISO 13485 Quality Management Systems and QMS procedures. 
Your role is to help users understand what content and sections should be included in QMS procedures.
When a user asks about a specific procedure, provide clear, structured guidance on:
1. What sections it should contain
2. What content each section must have
3. Examples and best practices
4. Common mistakes to avoid

Always reference the provided knowledge base when available.
Be precise, professional, and practical in your recommendations.
Focus on Phase 1: Explaining what a procedure should contain."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Based on this procedure knowledge: {context}\n\nUser question: {user_query}"}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}. Please check your OpenAI API key in .env file."

# ============================================================================
# UI LAYOUT
# ============================================================================

st.title("📋 ISO 13485 QMS Procedure Guide - Phase 1")
st.markdown("**Chatbot to explain what sections and content QMS procedures should contain**")
st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    search_weight_bm25 = st.slider("BM25 Keyword Weight", 0.0, 1.0, 0.6, help="Higher = more keyword matching")
    search_weight_tfidf = 1.0 - search_weight_bm25
    top_k = st.slider("Number of Search Results", 1, 10, 5, help="How many documents to retrieve")
    show_search_details = st.checkbox("Show Search Details", False, help="Display search scores and retrieved documents")
    
    st.divider()
    st.subheader("📚 Procedure Overview")
    st.info(f"**Procedure:** {procedure['title']}\n\n**Standard:** {procedure['standard']}\n\n**Sections:** 12")

# Main content area
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📖 Full Procedure", "⚙️ Hybrid Search Demo"])

# ============================================================================
# TAB 1: CHAT
# ============================================================================
with tab1:
    st.subheader("Ask About Procedure Content")
    
    # Example questions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What should Section 1 (Purpose) contain?"):
            st.session_state.user_input = "What should a Purpose section contain in a QMS procedure?"
    with col2:
        if st.button("What are common mistakes in document control?"):
            st.session_state.user_input = "What are common mistakes in document control procedures?"
    with col3:
        if st.button("What is revision traceability?"):
            st.session_state.user_input = "Explain revision traceability in document control"
    
    # User input
    user_input = st.text_input(
        "Your question:",
        value=st.session_state.get('user_input', ''),
        placeholder="E.g., 'What should a document approval process contain?'",
        key="chat_input"
    )
    
    if user_input:
        # Clear the session state input
        st.session_state.user_input = ""
        
        with st.spinner("🔍 Searching knowledge base..."):
            # Perform hybrid search
            search_results = hybrid_search(user_input, top_k=top_k, 
                                          bm25_weight=search_weight_bm25, 
                                          tfidf_weight=search_weight_tfidf)
        
        if search_results:
            # Show search results if requested
            if show_search_details:
                st.subheader("📊 Retrieved Documents")
                for i, result in enumerate(search_results, 1):
                    with st.expander(f"{i}. {result['document']['title']} (Score: {result['score']:.3f})"):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Hybrid Score", f"{result['score']:.3f}")
                        col2.metric("BM25 Score", f"{result['bm25_score']:.3f}")
                        col3.metric("TF-IDF Score", f"{result['tfidf_score']:.3f}")
                        
                        st.write(f"**Type:** {result['document']['type']}")
                        st.write(result['document'].get('content', 'N/A'))
            
            # Generate response
            with st.spinner("✨ Generating response with OpenAI..."):
                response = generate_response_with_rag(user_input, search_results)
            
            st.subheader("💡 Response")
            st.markdown(response)
            
            # Show sources
            st.subheader("📚 Sources")
            for i, result in enumerate(search_results[:3], 1):
                st.caption(f"{i}. {result['document']['title']}")
        else:
            st.warning("No relevant documents found for your query. Try different keywords.")

# ============================================================================
# TAB 2: FULL PROCEDURE
# ============================================================================
with tab2:
    st.subheader(procedure['title'])
    st.markdown(f"**Standard:** {procedure['standard']}")
    st.markdown(f"**Document ID:** {procedure['id']}")
    st.divider()
    
    # Document Control Information
    with st.expander("📌 Document Control Information (Mandatory Header)", expanded=True):
        st.write("**Every controlled document must include this on its first page:**")
        dci = procedure['document_control_information']
        for item in dci['must_contain']:
            st.write(f"- {item}")
        st.info(dci['example_text'])
    
    # All sections
    for section_num in sorted(procedure['sections'].keys()):
        section = procedure['sections'][section_num]
        with st.expander(f"Section {section_num}: {section['section_title']}", expanded=False):
            st.write(f"**Description:** {section.get('description', 'N/A')}")
            
            st.write("**Must Contain:**")
            for item in section.get('must_contain', []):
                st.write(f"- {item}")
            
            if 'example_text' in section:
                st.info(f"**Example:** {section['example_text']}")
            
            # Show subsections if exist
            if 'subsections' in section:
                st.write("**Subsections:**")
                for sub_id, subsection in section['subsections'].items():
                    with st.expander(f"{sub_id}: {subsection['title']}", expanded=False):
                        for item in subsection.get('must_contain', []):
                            st.write(f"- {item}")
                        if 'example_text' in subsection:
                            st.info(subsection['example_text'])
    
    st.divider()
    
    # Key Explanations
    with st.expander("📖 Key Terms and Explanations", expanded=False):
        for term, explanation in procedure['key_explanations'].items():
            st.write(f"**{term.replace('_', ' ').title()}:** {explanation}")
    
    # Common Mistakes
    with st.expander("⚠️ Common Mistakes", expanded=False):
        for i, mistake in enumerate(procedure['common_mistakes'], 1):
            st.write(f"{i}. {mistake}")

# ============================================================================
# TAB 3: SEARCH DEMO
# ============================================================================
with tab3:
    st.subheader("🔍 Hybrid Search Demonstration")
    st.write("Test the hybrid search functionality with different queries to understand how BM25 and TF-IDF combine.")
    
    demo_query = st.text_input("Enter search query:", value="document approval process")
    
    if demo_query:
        results = hybrid_search(demo_query, top_k=top_k, 
                               bm25_weight=search_weight_bm25, 
                               tfidf_weight=search_weight_tfidf)
        
        st.subheader("Results")
        if results:
            # Create a visual comparison
            data_for_display = []
            for result in results:
                data_for_display.append({
                    "Title": result['document']['title'],
                    "Type": result['document']['type'],
                    "Hybrid Score": round(result['score'], 3),
                    "BM25": round(result['bm25_score'], 3),
                    "TF-IDF": round(result['tfidf_score'], 3)
                })
            
            st.dataframe(data_for_display, use_container_width=True)
            
            # Detailed view
            st.subheader("Detailed Results")
            for i, result in enumerate(results, 1):
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{i}. {result['document']['title']}**")
                    col2.metric("Score", f"{result['score']:.3f}")
                    
                    st.caption(f"Type: {result['document']['type']}")
                    st.write(result['document'].get('content', 'No content'))
                    
                    if result['document'].get('must_contain'):
                        with st.expander("Must Contain"):
                            st.write(result['document']['must_contain'])
        else:
            st.warning("No results found")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    <p>ISO 13485 QMS Procedure Guide - Phase 1: Content Structure Guidance</p>
    <p>Hybrid Search: BM25 (Keyword) + TF-IDF (Semantic) | LLM: OpenAI GPT-3.5-turbo</p>
</div>
""", unsafe_allow_html=True)