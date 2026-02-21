import streamlit as st
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import re
from typing import List, Dict, Tuple

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="ISO 13485:2016 RAG Chatbot",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5em;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #555;
        font-size: 1.2em;
        margin-bottom: 30px;
    }
    .procedure-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 15px;
    }
    .requirement-box {
        background-color: #e8f4f8;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #ffc107;
        margin-bottom: 10px;
    }
    .success-box {
        background-color: #d4edda;
        padding: 12px;
        border-radius: 6px;
        border-left: 4px solid #28a745;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Load ISO 13485 procedures data
@st.cache_resource
def load_procedures_database():
    """Load procedures from JSON file"""
    try:
        with open('claude_code\iso_13485_procedures.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Procedures database not found. Please ensure iso_13485_procedures.json is in the correct location.")
        return None

# Initialize database
procedures_db = load_procedures_database()

if procedures_db is None:
    st.stop()

def search_procedures_by_keyword(keyword: str, database: Dict) -> List[Dict]:
    """Search procedures by keyword"""
    results = []
    keyword_lower = keyword.lower()
    
    for section in database.get('sections', []):
        if 'procedures' in section:
            for proc in section['procedures']:
                # Search in title, keywords, description
                if (keyword_lower in proc.get('title', '').lower() or
                    keyword_lower in proc.get('description', '').lower() or
                    any(keyword_lower in k.lower() for k in proc.get('keywords', []))):
                    results.append(proc)
        
        # Search in subsections
        if 'subsections' in section:
            for subsection in section['subsections']:
                if 'procedures' in subsection:
                    for proc in subsection['procedures']:
                        if (keyword_lower in proc.get('title', '').lower() or
                            keyword_lower in proc.get('description', '').lower() or
                            any(keyword_lower in k.lower() for k in proc.get('keywords', []))):
                            results.append(proc)
    
    return results

def search_procedures_by_id(proc_id: str, database: Dict) -> Dict :
    """Search procedure by ID"""
    for section in database.get('sections', []):
        if 'procedures' in section:
            for proc in section['procedures']:
                if proc.get('proc_id') == proc_id:
                    return proc
        
        if 'subsections' in section:
            for subsection in section['subsections']:
                if 'procedures' in subsection:
                    for proc in subsection['procedures']:
                        if proc.get('proc_id') == proc_id:
                            return proc
    
    return None

def get_all_procedures(database: Dict) -> List[Dict]:
    """Get all procedures from database"""
    all_procs = []
    
    for section in database.get('sections', []):
        if 'procedures' in section:
            all_procs.extend(section['procedures'])
        
        if 'subsections' in section:
            for subsection in section['subsections']:
                if 'procedures' in subsection:
                    all_procs.extend(subsection['procedures'])
    
    return all_procs

def format_procedure_for_display(proc: Dict) -> str:
    """Format procedure data for display"""
    formatted = f"""
### {proc.get('title', 'N/A')}

**Procedure ID:** {proc.get('proc_id', 'N/A')}

**Requirement:** {proc.get('requirement', 'N/A')}

**Description:** {proc.get('description', 'N/A')}

**What is Required:**
{chr(10).join([f"- {req}" for req in proc.get('what_is_required', [])])}

**Key Requirements:**
{chr(10).join([f"- {req}" for req in proc.get('key_requirements', [])[:5]])}

**Implementation Steps:**
{chr(10).join([f"{step}" for step in proc.get('implementation_steps', [])[:8]])}

**Responsibilities:**
{chr(10).join([f"- {resp}" for resp in proc.get('responsibilities', [])])}

**Documentation Needed:**
{chr(10).join([f"- {doc}" for doc in proc.get('documentation_needed', [])])}

**Keywords:** {', '.join(proc.get('keywords', []))}

**Related Procedures:** {', '.join(proc.get('related_procedures', []))}

**Example:** {proc.get('examples', 'N/A')}
"""
    return formatted

def query_openai_for_rag(user_query: str, retrieved_procedures: List[Dict]) -> str:
    """Use OpenAI to generate answer based on retrieved procedures"""
    
    # Build context from retrieved procedures
    context = "ISO 13485:2016 Procedures Context:\n\n"
    for i, proc in enumerate(retrieved_procedures[:3], 1):
        context += f"\n{i}. {proc.get('title', 'Unknown')}\n"
        context += f"   ID: {proc.get('proc_id', 'N/A')}\n"
        context += f"   Requirement: {proc.get('requirement', 'N/A')}\n"
        context += f"   Description: {proc.get('description', 'N/A')}\n"
        context += f"   Key Points: {', '.join(proc.get('key_requirements', [])[:3])}\n"
    
    # Create message for OpenAI
    messages = [
        {
            "role": "system",
            "content": """You are an expert in ISO 13485:2016 Medical Device Quality Management Systems. 
            You help users understand procedures, requirements, and implementation steps.
            Be precise, clear, and reference specific procedures when answering.
            Use the retrieved procedures context to provide accurate answers."""
        },
        {
            "role": "user",
            "content": f"""Based on the following ISO 13485:2016 procedures context:

{context}

Please answer this question: {user_query}

Provide a clear, structured answer that references the specific procedures."""
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

def display_procedure_list(procedures: List[Dict], title: str = "Found Procedures"):
    """Display list of procedures"""
    if not procedures:
        st.info("No procedures found matching your criteria.")
        return None
    
    st.markdown(f"### {title} ({len(procedures)} found)")
    
    # Create columns for procedure list
    for proc in procedures:
        with st.expander(f"🔹 {proc.get('proc_id', 'Unknown')} - {proc.get('title', 'Unknown')}"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.write(f"**Requirement:** {proc.get('requirement', 'N/A')}")
            
            with col2:
                st.write(f"**Description:** {proc.get('description', 'N/A')[:100]}...")
            
            with col3:
                if st.button("📖 View Full Details", key=f"btn_{proc.get('proc_id')}"):
                    st.session_state.selected_procedure = proc.get('proc_id')
    
    return procedures

# Main App Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="main-title">📋 ISO 13485:2016 RAG Chatbot</div>', unsafe_allow_html=True)

with col2:
    st.markdown("**Medical Device QMS**")

st.markdown('<div class="subtitle">Query procedures, requirements, and implementation guidance</div>', unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    page = st.radio(
        "Select Mode:",
        ["🔍 Search Procedures", "💬 Ask RAG Assistant", "📚 Browse All", "ℹ️ About"]
    )

# Initialize session state
if 'selected_procedure' not in st.session_state:
    st.session_state.selected_procedure = None

# Page: Search Procedures
if page == "🔍 Search Procedures":
    st.markdown("## Search Procedures")
    
    search_type = st.radio("Search by:", ["Keyword", "Procedure ID"])
    
    if search_type == "Keyword":
        search_term = st.text_input(
            "Enter keyword to search:",
            placeholder="e.g., 'complaint', 'design', 'validation'",
            help="Search in procedure titles, descriptions, and keywords"
        )
        
        if search_term:
            results = search_procedures_by_keyword(search_term, procedures_db)
            display_procedure_list(results, f"Search Results for '{search_term}'")
            
            # Show selected procedure details
            if st.session_state.selected_procedure:
                proc = search_procedures_by_id(st.session_state.selected_procedure, procedures_db)
                if proc:
                    st.markdown("---")
                    st.markdown(format_procedure_for_display(proc))
    
    else:  # Procedure ID search
        proc_id = st.text_input(
            "Enter Procedure ID:",
            placeholder="e.g., 'PROC_8_2_2'",
            help="Exact procedure ID"
        )
        
        if proc_id:
            proc = search_procedures_by_id(proc_id, procedures_db)
            if proc:
                st.markdown(format_procedure_for_display(proc))
            else:
                st.error(f"Procedure '{proc_id}' not found.")

# Page: RAG Assistant
elif page == "💬 Ask RAG Assistant":
    st.markdown("## RAG Assistant")
    st.info("Ask questions about ISO 13485:2016 procedures and the assistant will search the database and provide answers using AI.")
    
    user_query = st.text_area(
        "Ask your question:",
        placeholder="e.g., 'How should the organization handle customer complaints?' or 'What are the requirements for design control?'",
        height=100
    )
    
    if st.button("🔍 Search & Answer", use_container_width=True):
        if user_query.strip():
            with st.spinner("Searching procedures and generating answer..."):
                # Step 1: Search for relevant procedures
                st.markdown("### 1️⃣ Searching Procedures...")
                
                # Try multiple search strategies
                keywords_in_query = [word for word in user_query.lower().split() if len(word) > 3]
                all_results = []
                
                for keyword in keywords_in_query[:3]:  # Limit to top 3 keywords
                    results = search_procedures_by_keyword(keyword, procedures_db)
                    all_results.extend(results)
                
                # Remove duplicates
                seen_ids = set()
                unique_results = []
                for proc in all_results:
                    if proc.get('proc_id') not in seen_ids:
                        unique_results.append(proc)
                        seen_ids.add(proc.get('proc_id'))
                
                if unique_results:
                    st.success(f"Found {len(unique_results)} relevant procedures")
                    
                    # Display retrieved procedures
                    with st.expander("📚 Retrieved Procedures", expanded=False):
                        for proc in unique_results[:5]:
                            st.markdown(f"- **{proc.get('proc_id')}**: {proc.get('title')}")
                    
                    # Step 2: Generate answer using OpenAI
                    st.markdown("### 2️⃣ Generating Answer...")
                    answer = query_openai_for_rag(user_query, unique_results)
                    
                    st.markdown("### 📝 Answer")
                    st.markdown(f'<div class="success-box">{answer}</div>', unsafe_allow_html=True)
                    
                    # Step 3: Show detailed procedures
                    st.markdown("### 3️⃣ Detailed Procedures")
                    for proc in unique_results[:3]:
                        with st.expander(f"📖 {proc.get('proc_id')} - {proc.get('title')}"):
                            st.markdown(format_procedure_for_display(proc))
                
                else:
                    st.warning("No relevant procedures found. Try different keywords.")
        else:
            st.warning("Please enter a question.")

# Page: Browse All Procedures
elif page == "📚 Browse All":
    st.markdown("## Browse All Procedures")
    
    all_procedures = get_all_procedures(procedures_db)
    
    # Add filters
    col1, col2 = st.columns(2)
    
    with col1:
        section_filter = st.selectbox(
            "Filter by Section:",
            ["All"] + list(set([proc.get('requirement', '').split('.')[0] 
                               for proc in all_procedures if proc.get('requirement')]))
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by:",
            ["ID", "Title", "Requirement"]
        )
    
    # Filter procedures
    if section_filter != "All":
        filtered = [p for p in all_procedures if p.get('requirement', '').startswith(section_filter)]
    else:
        filtered = all_procedures
    
    # Sort
    if sort_by == "Title":
        filtered.sort(key=lambda x: x.get('title', ''))
    elif sort_by == "Requirement":
        filtered.sort(key=lambda x: x.get('requirement', ''))
    else:
        filtered.sort(key=lambda x: x.get('proc_id', ''))
    
    st.markdown(f"**Total Procedures:** {len(filtered)}")
    st.markdown("---")
    
    # Display procedures
    display_procedure_list(filtered, "All Procedures")
    
    # Show selected procedure
    if st.session_state.selected_procedure:
        proc = search_procedures_by_id(st.session_state.selected_procedure, procedures_db)
        if proc:
            st.markdown("---")
            st.markdown(format_procedure_for_display(proc))

# Page: About
elif page == "ℹ️ About":
    st.markdown("## About ISO 13485:2016 RAG")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📋 ISO 13485:2016
        
        Medical devices — Quality management systems — Requirements for regulatory purposes
        
        **Edition:** Third edition
        **Publication Date:** 2016-03-01
        
        ### 🎯 This Tool
        
        A Retrieval-Augmented Generation (RAG) chatbot that helps you:
        
        - Search procedures by keyword or ID
        - Ask questions about requirements
        - Find implementation guidance
        - Understand relationships between procedures
        - Access complete procedure details
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 How It Works
        
        1. **Search**: Enter keywords or procedure IDs
        2. **Retrieve**: System finds relevant procedures
        3. **Augment**: OpenAI processes the context
        4. **Generate**: Get AI-assisted answers
        
        ### 📊 Database Information
        
        """)
        
        all_procs = get_all_procedures(procedures_db)
        st.info(f"""
        - **Total Procedures:** {len(all_procs)}
        - **Sections:** {len(procedures_db.get('sections', []))}
        - **Database:** ISO 13485:2016 Complete
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🛠️ Features
    
    - **Keyword Search**: Find procedures by topic
    - **ID Search**: Direct access to specific procedures
    - **RAG Assistant**: Ask natural language questions
    - **Full Details**: View complete procedure documentation
    - **Related Procedures**: Understand procedure relationships
    - **Implementation Guidance**: Get practical guidance
    
    ### 💡 Tips
    
    - Use specific keywords for better results
    - Try questions like "How to handle complaints?"
    - Browse all procedures to explore the system
    - Use procedure IDs for exact matches
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div style='text-align: center; color: #999; font-size: 0.8em;'>
    ISO 13485:2016 RAG Chatbot | Powered by OpenAI & Streamlit
    </div>
    """, unsafe_allow_html=True)
