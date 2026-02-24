# 🏗️ ISO 13485 QMS Chatbot - Architecture & Design

## Executive Summary

This is a **Retrieval-Augmented Generation (RAG)** chatbot that helps users understand what content QMS procedures should contain. It combines:

- **Structured Knowledge Base** (JSON) - Your procedures
- **Hybrid Search** (BM25 + TF-IDF) - Smart retrieval  
- **LLM Integration** (OpenAI) - Intelligent responses
- **Web UI** (Streamlit) - User interaction

**Phase 1 Focus:** Content guidance (what should be in procedures)  
**Phase 2 Will Add:** Gap analysis and compliance checking

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     STREAMLIT USER INTERFACE                │
│  • Chat Tab • Full Procedure Browser • Search Demo          │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Chat    │  │ Browse   │  │  Debug   │
    │  Input   │  │Procedure │  │ Search   │
    └─────┬────┘  └────┬─────┘  └────┬─────┘
          │            │             │
          └────────────┼─────────────┘
                       │ User Query
                       ▼
    ┌──────────────────────────────────────┐
    │    HYBRID SEARCH ENGINE              │
    ├──────────────────────────────────────┤
    │ • Split query into tokens            │
    │ • BM25 keyword search (60%)          │
    │ • TF-IDF semantic search (40%)       │
    │ • Combine scores & rank results      │
    └──────────────┬───────────────────────┘
                   │
                   │ Top-K Results
                   │ (default: 5)
                   ▼
    ┌──────────────────────────────────────┐
    │  PROMPT ENGINEERING & CONTEXT BUILD  │
    ├──────────────────────────────────────┤
    │ System Prompt:                       │
    │ "You are an ISO 13485 expert..."     │
    │                                      │
    │ User Message:                        │
    │ "Query: [user question]"             │
    │ "Context: [retrieved sections]"      │
    └──────────────┬───────────────────────┘
                   │
                   │ Formatted prompt
                   ▼
    ┌──────────────────────────────────────┐
    │       OPENAI API (GPT-3.5-turbo)     │
    ├──────────────────────────────────────┤
    │ • Process with LLM                   │
    │ • Generate structured response       │
    │ • Format with markdown               │
    └──────────────┬───────────────────────┘
                   │
                   │ Generated response
                   ▼
    ┌──────────────────────────────────────┐
    │       DISPLAY & SOURCE ATTRIBUTION   │
    ├──────────────────────────────────────┤
    │ • Show main response                 │
    │ • List source documents              │
    │ • Optional: detailed search scores    │
    └──────────────────────────────────────┘
```

---

## 🗄️ Knowledge Base Structure

### File: `procedure_db.json`

```json
{
  "procedure": {
    "id": "DOC-CTRL-001",
    "title": "Control of Documents and Records",
    "version": "1.0",
    "standard": "ISO 13485:2016",
    "purpose": "...",
    "sections": {
      "1": {
        "section_number": "1",
        "section_title": "Purpose",
        "description": "...",
        "must_contain": ["item1", "item2", ...],
        "example_text": "..."
      },
      "2": { ... },
      ...
      "7": {
        "section_title": "Control of Documents",
        "subsections": {
          "7.1": {...},
          "7.2": {...},
          ...
        }
      },
      ...
    },
    "document_control_information": {
      "title": "...",
      "must_contain": [...],
      "example_text": "..."
    },
    "key_explanations": {
      "traceability": "definition...",
      "version_control": "definition...",
      ...
    },
    "common_mistakes": [
      "mistake1",
      "mistake2",
      ...
    ]
  }
}
```

**Why JSON?**
- ✅ Easy to parse and validate
- ✅ Human-readable and editable
- ✅ Hierarchical structure for sections/subsections
- ✅ Can be version controlled in Git
- ✅ Easy to extend with new procedures

---

## 🔍 Hybrid Search Algorithm

### What is Hybrid Search?

Traditional search has trade-offs:

| Type | Pros | Cons |
|------|------|------|
| **Keyword (BM25)** | Fast, precise, technical | Misses synonyms, fragile |
| **Semantic (TF-IDF)** | Smart, flexible, context | Slower, less precise |

**Hybrid combines both** to get best of both worlds.

### Implementation: BM25 + TF-IDF

#### Step 1: Prepare Data
```python
texts = [doc.full_text for doc in knowledge_base]
tokenized = [[word for word in text.split()] for text in texts]
```

#### Step 2: BM25 Scoring
```python
# Probability of relevance based on term frequency
bm25 = BM25Okapi(tokenized_texts)
bm25_scores = bm25.get_scores(query_tokens)

# Result: scores based on keyword matching
# Higher = more relevant keywords
```

**BM25 Formula:**
```
score = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × (|D| / avgdl)))
```

Where:
- `IDF` = how rare the term is
- `f(qi, D)` = frequency of term in document
- `k1, b` = tuning parameters (Okapi defaults)

#### Step 3: TF-IDF Scoring
```python
# Vector representation of text
tfidf = TfidfVectorizer(lowercase=True, stop_words='english')
tfidf_matrix = tfidf.fit_transform(texts)

# Cosine similarity between query and documents
query_tfidf = tfidf.transform([query])
tfidf_scores = cosine_similarity(query_tfidf, tfidf_matrix)[0]

# Result: semantic similarity (0-1)
```

**TF-IDF Formula:**
```
TF-IDF(term, doc) = TF(term, doc) × IDF(term)
TF = (frequency of term in doc) / (total terms in doc)
IDF = log(total docs / docs with term)
```

#### Step 4: Normalize & Combine
```python
# Normalize both to 0-1 range
bm25_norm = (bm25 - min) / (max - min)
tfidf_norm = (tfidf - min) / (max - min)

# Weighted combination (default: 60% keyword, 40% semantic)
hybrid_score = 0.6 × bm25_norm + 0.4 × tfidf_norm

# Rank by hybrid score
top_k = sorted_by_score(hybrid_score)[:k]
```

### Example Search

**Query:** "How should we authorize documents?"

```
Step 1: Tokenize
  → ["how", "should", "we", "authorize", "documents"]

Step 2: BM25 Scores
  Section 7.2 (Approval): 2.15  ← High (has "approve" similar to "authorize")
  Section 5 (Responsibilities): 1.85
  Section 7.1 (Identification): 0.45

Step 3: TF-IDF Scores  
  Section 7.2: 0.78  ← High (semantic similarity)
  Section 5: 0.71
  Section 7.1: 0.32

Step 4: Hybrid (60% BM25 + 40% TF-IDF)
  Section 7.2: 0.6×2.15 + 0.4×0.78 = 1.602 ← Highest!
  Section 5: 0.6×1.85 + 0.4×0.71 = 1.394
  Section 7.1: 0.6×0.45 + 0.4×0.32 = 0.398

Result: Section 7.2 (Approval) ranked first ✓
```

### Why This Works Better

| Query | BM25 Result | TF-IDF Result | Hybrid Result |
|-------|-------------|---------------|--------------|
| "document approval" | Section 7.2 ✓ | Section 7.2 ✓ | Section 7.2 ✓ |
| "how authorize docs" | Section 7.1 ✗ | Section 7.2 ✓ | Section 7.2 ✓ |
| "signature needed" | Section 1 ✗ | Section 7.2 ✓ | Section 7.2 ✓ |

---

## 🧠 RAG (Retrieval Augmented Generation)

### Traditional LLM Problems

```
User: "What should document approval contain?"
LLM generates from training data...
  (May be outdated, generic, hallucinate)
```

### RAG Solution

```
User: "What should document approval contain?"
    ↓
[Search for relevant documents]
    ↓
[Build context: "Here are 5 relevant procedure sections"]
    ↓
[Ask LLM: "Given this context, explain..."]
    ↓
LLM generates from YOUR data + context
  (Accurate, specific, grounded in real procedures)
```

### Benefits of RAG

1. **Accuracy** - Uses your actual procedures, not generic training data
2. **Traceability** - Can cite which section answers were based on
3. **Control** - Easy to update knowledge without retraining
4. **Context** - LLM understands organizational specifics
5. **Freshness** - Automatically reflects latest procedure versions

### Implementation in Code

```python
def generate_response_with_rag(user_query, search_results):
    # Build context from retrieved documents
    context_parts = []
    for result in search_results:
        doc = result['document']
        context_parts.append(f"**{doc['title']}**\n{doc['content']}")
        if doc.get('must_contain'):
            context_parts.append(f"Must contain: {doc['must_contain']}")
    
    context = "\n\n".join(context_parts)
    
    # System prompt establishes role
    system_prompt = """You are an expert in ISO 13485 QMS...
    Focus on: What sections should procedures contain?"""
    
    # User message combines query + context
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context: {context}\n\nQuery: {user_query}"}
    ]
    
    # Generate response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

---

## 🚀 Streamlit UI Architecture

### Session State Management

```python
st.session_state.user_input  # Persist user input across reruns
st.session_state.chat_history  # Could store conversation history
```

### Caching for Performance

```python
@st.cache_resource  # Cache across all sessions
def load_procedure_data():
    return json.load(open('procedure_db.json'))

@st.cache_resource
def initialize_search_indices():
    # BM25 and TF-IDF initialization (expensive)
    return bm25, tfidf, tfidf_matrix
```

First load: ~2 seconds (build indices)  
Subsequent loads: <10ms (cached)

### Tab Structure

```
┌─ CHAT TAB ──────────────────────┐
│ • Input field                    │
│ • Quick-start buttons            │
│ • Response display               │
│ • Source attribution             │
└──────────────────────────────────┘

┌─ PROCEDURE BROWSER ──────────────┐
│ • Full procedure structure        │
│ • Expandable sections            │
│ • All examples & definitions      │
└──────────────────────────────────┘

┌─ SEARCH DEMO ────────────────────┐
│ • Test search directly           │
│ • Adjust weights in real-time    │
│ • View scores & rankings         │
└──────────────────────────────────┘
```

---

## 💾 Data Flow

### Initialization
```
1. Load procedure_db.json
2. Build knowledge base (flatten sections)
3. Initialize BM25 index
4. Initialize TF-IDF vectorizer
5. Cache indices
6. Wait for user input
```

### Per-Query Flow
```
1. User enters question
2. Hybrid search (BM25 + TF-IDF)
   → Returns top 5 documents
3. Build prompt with context
4. Call OpenAI API
5. Stream response to UI
6. Display with sources
```

### State Diagram
```
     ┌─────────────┐
     │   START     │
     └──────┬──────┘
            │
            ▼
     ┌─────────────────┐
     │ Load JSON Data  │
     │ Build Indices   │
     │ Cache Results   │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────────────┐
     │ WAITING FOR USER INPUT  │
     └────────┬────────────────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
    Search      Cache
    Execute     Hit
        │          │
        └─────┬────┘
              ▼
     ┌──────────────────┐
     │ Generate Prompt  │
     │ Call OpenAI API  │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Display Response │
     │ + Sources        │
     └────────┬─────────┘
              │
              ▼
     ┌────────────────────┐
     │ AWAITING NEXT INPUT│
     └────────┬───────────┘
              │
              └──────┐
                     └───→ [Back to Search Execute]
```

---

## 🔧 Configuration Parameters

### Search Parameters

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| BM25 Weight | 0.6 | 0.0-1.0 | Higher = more keyword matching |
| TF-IDF Weight | 0.4 | 0.0-1.0 | Must sum to 1.0 with BM25 |
| Top-K Results | 5 | 1-10 | More results = slower, more context |

### OpenAI Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | gpt-3.5-turbo | Fast, cost-effective |
| Temperature | 0.7 | Balance of creativity & consistency |
| Max Tokens | 1500 | Limit response length |
| Stop Sequences | None | Let model decide ending |

---

## 📊 Extensibility for Phase 2

### Gap Analysis Addition

```
Current (Phase 1):
User: "What should Section 5 contain?"
Bot: "Section 5 should contain A, B, C..."

Phase 2:
User: [Upload their procedure]
Bot: "You have A and B, but missing C, D, E"
Bot: "Your Section 5 is 66% complete"
Bot: "Here's what you need to add..."
```

### Required Changes for Phase 2

1. **File Upload Component**
```python
uploaded_file = st.file_uploader("Upload your procedure")
user_procedure = parse_docx_or_pdf(uploaded_file)
```

2. **Gap Analysis Function**
```python
def analyze_gaps(user_procedure, template_procedure):
    missing_sections = find_missing(user_procedure, template)
    incomplete_content = check_completeness(user_procedure)
    return gap_report
```

3. **Compliance Scoring**
```python
def score_compliance(gaps):
    total_items = count_must_have_items()
    found_items = count_present_items()
    return (found_items / total_items) * 100
```

4. **Recommendation Engine**
```python
def generate_recommendations(gaps, user_context):
    # What's most critical to add?
    # What's regulatory vs best practice?
    # What's quick wins?
```

---

## 🔐 Security Considerations

### API Key Management
- ✅ Stored in `.env` (not in code)
- ✅ Loaded via `python-dotenv`
- ✅ Never logged or exposed in errors
- ✅ Should be rotated regularly

### Data Handling
- ✅ No data stored on server
- ✅ Queries sent to OpenAI (review ToS)
- ✅ Cache only in-memory (session)
- ✅ User procedures (Phase 2) should be treated as confidential

### Input Validation
- ✅ User queries: Limited to text input
- ✅ File uploads (Phase 2): Validate file type & size
- ✅ JSON parsing: Validates schema
- ✅ API responses: Error handling included

---

## 📈 Performance Metrics

### Latency

```
Query Processing:
├─ Search (local): ~100ms
│  ├─ Tokenization: ~10ms
│  ├─ BM25 scoring: ~30ms
│  ├─ TF-IDF scoring: ~50ms
│  └─ Ranking: ~10ms
├─ Prompt building: ~5ms
└─ OpenAI API: ~3-5s (network dependent)

Total: ~3.1-5.1 seconds per query
```

### Memory Usage

```
Indices cached:
├─ BM25 objects: ~2 MB
├─ TF-IDF matrix (sparse): ~1 MB  
├─ Knowledge base (JSON): ~0.5 MB
└─ Streamlit UI: ~50 MB

Total: ~53.5 MB (first load) → ~50 MB (cached)
```

### Cost

```
Per query (using gpt-3.5-turbo):
├─ Input tokens (~500): ~$0.00075
└─ Output tokens (~200): ~$0.0003

Total per query: ~$0.00105
1000 queries: ~$1.05
```

---

## 🎯 Success Metrics

For Phase 1:
- ✅ User gets relevant procedure guidance
- ✅ Response includes required sections
- ✅ Examples provided
- ✅ Sources are accurate

For Phase 2:
- ✅ Accurately identifies missing sections
- ✅ Scores compliance percentage
- ✅ Prioritizes critical gaps
- ✅ Provides actionable recommendations

---

## 📚 References

### Search Algorithms
- BM25: https://en.wikipedia.org/wiki/Okapi_BM25
- TF-IDF: https://en.wikipedia.org/wiki/Tf%E2%80%93idf

### RAG Pattern
- Original Paper: https://arxiv.org/abs/2005.11401
- Implementation Guide: https://python.langchain.com/docs/modules/data_connection/retrieval

### ISO 13485
- Standard: ISO 13485:2016 - Medical devices — Quality management systems
- EU MDR: https://ec.europa.eu/growth/tools-databases/mdr/

---

**Architecture Version:** 1.0  
**Last Updated:** 2025  
**Design Pattern:** RAG (Retrieval Augmented Generation)  
**Search Type:** Hybrid (BM25 + TF-IDF)  
**LLM:** OpenAI GPT-3.5-turbo  
**UI Framework:** Streamlit