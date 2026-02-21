# ISO 13485:2016 RAG Chatbot - Setup & Usage Guide

## 📋 Overview

This is a Retrieval-Augmented Generation (RAG) chatbot built with Streamlit that helps users:
- Search ISO 13485:2016 procedures by keyword or ID
- Ask natural language questions about QMS requirements
- Get AI-assisted answers using OpenAI's API
- Browse all procedures in an organized manner

## 🛠️ Installation & Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Environment Setup

Create a `.env` file in the project root directory:

```bash
touch .env
```

Add your OpenAI API key to the `.env` file:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Note:** You can get your API key from https://platform.openai.com/api-keys

### Step 3: Verify Files

Make sure these files are in the same directory:
- `iso_13485_rag.py` - Main Streamlit application
- `iso_13485_procedures.json` - Procedures database
- `requirements.txt` - Python dependencies
- `.env` - Your API key (keep this private!)

## 🚀 Running the Application

```bash
streamlit run iso_13485_rag.py
```

The app will open in your default browser at `http://localhost:8501`

## 📖 How to Use

### Mode 1: Search Procedures 🔍

**Keyword Search:**
1. Go to "🔍 Search Procedures" tab
2. Select "Keyword" option
3. Enter a search term (e.g., "complaint", "design", "validation")
4. View matching procedures
5. Click "View Full Details" to see complete procedure information

**ID Search:**
1. Go to "🔍 Search Procedures" tab
2. Select "Procedure ID" option
3. Enter exact procedure ID (e.g., "PROC_8_2_2")
4. View the specific procedure

### Mode 2: Ask RAG Assistant 💬

1. Go to "💬 Ask RAG Assistant" tab
2. Enter your question in natural language
3. Examples:
   - "How should the organization handle customer complaints?"
   - "What are the requirements for design control?"
   - "How to validate manufacturing processes?"
   - "What documentation is required?"
4. Click "🔍 Search & Answer"
5. The system will:
   - Search relevant procedures
   - Show retrieved procedures
   - Generate an AI-assisted answer
   - Display detailed procedures

### Mode 3: Browse All 📚

1. Go to "📚 Browse All" tab
2. Filter by section (optional)
3. Sort by ID, Title, or Requirement
4. Explore all procedures
5. Click expanders to view details

### Mode 4: About ℹ️

Learn about the tool, how it works, and database information.

## 🔍 Example Queries

Try these example questions with the RAG Assistant:

### Quality Management System
- "What are the general requirements for a quality management system?"
- "What documentation is required according to ISO 13485?"
- "Explain the document control procedure"

### Product Realization
- "What are the requirements for product planning?"
- "How should product requirements be determined?"
- "What is the design and development process?"

### Monitoring & Improvement
- "How should the organization handle non-conforming products?"
- "What is the corrective action procedure?"
- "How to implement preventive actions?"

### Management
- "What are the responsibilities of top management?"
- "How often should management reviews be conducted?"
- "What should be included in a quality policy?"

## 📊 Database Information

**Total Procedures:** 45
**Sections:** 8
**Coverage:**
- Section 4: Quality Management System
- Section 5: Management Responsibility
- Section 6: Resource Management
- Section 7: Product Realization
- Section 8: Measurement, Analysis & Improvement

## ⚙️ Technical Details

### Architecture

```
User Input
    ↓
Streamlit Interface
    ↓
Keyword Search Algorithm
    ↓
Procedure Database (JSON)
    ↓
Retrieved Procedures
    ↓
OpenAI API (RAG)
    ↓
AI-Generated Answer
    ↓
User Display
```

### Search Algorithm

1. **Tokenization**: Breaks user query into keywords
2. **Multi-field Search**: Searches in:
   - Procedure titles
   - Descriptions
   - Keywords
   - Requirements
3. **Deduplication**: Removes duplicate procedures
4. **Ranking**: Orders by relevance

### RAG Process

1. **Retrieval**: Find relevant procedures from database
2. **Augmentation**: Build context from top 3 procedures
3. **Generation**: Send context + query to OpenAI
4. **Response**: Generate answer based on ISO 13485 context

## 🔐 Security Notes

- **Never commit `.env` file** to version control
- **Keep API key private** - don't share it
- **Limit API calls** - consider implementing usage limits
- **Monitor OpenAI usage** to avoid unexpected charges

## 📝 Procedure JSON Structure

```json
{
  "proc_id": "PROC_8_2_2",
  "title": "Complaint Management and Handling",
  "requirement": "8.2.2",
  "description": "Document procedures for complaint handling...",
  "what_is_required": ["List of requirements"],
  "key_requirements": ["Key points"],
  "implementation_steps": ["Steps to follow"],
  "responsibilities": ["Who is responsible"],
  "documentation_needed": ["Required documents"],
  "examples": "Real-world example",
  "keywords": ["searchable", "keywords"],
  "related_procedures": ["PROC_ID"]
}
```

## 🐛 Troubleshooting

### Issue: "Procedures database not found"
**Solution:** Ensure `iso_13485_procedures.json` is in the same directory as the Python script.

### Issue: OpenAI API Error
**Solution:** 
- Verify your API key in `.env`
- Check API key is valid at https://platform.openai.com/api-keys
- Ensure you have API credits available

### Issue: Slow response time
**Solution:**
- The RAG process takes 2-5 seconds
- OpenAI API calls may be slow depending on server load
- Consider adding caching for frequently asked questions

### Issue: No procedures found
**Solution:**
- Try different keywords
- Use Procedure ID search instead
- Browse all procedures to explore database

## 📈 Performance Tips

1. **Reduce Database Queries**
   - Use keyword search when possible
   - Cache results using Streamlit's `@st.cache_resource`

2. **Optimize API Calls**
   - Limit retrieved procedures to top 3 for context
   - Use shorter prompts for faster responses

3. **Improve Search**
   - Add more keywords to procedures
   - Implement fuzzy matching for typos

## 🔄 API Rate Limits

OpenAI API has rate limits:
- Free tier: Limited calls
- Paid tier: 3,500 RPM / 200,000 TPM

Monitor usage at: https://platform.openai.com/account/usage/overview

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review OpenAI API documentation
3. Check Streamlit documentation
4. Verify your `.env` file setup

## 📚 ISO 13485:2016 Standard

This tool references ISO 13485:2016:
- **Title:** Medical devices — Quality management systems — Requirements for regulatory purposes
- **Edition:** Third edition
- **Publication:** March 1, 2016

For complete standard details, visit ISO: https://www.iso.org/

## 🎯 Future Enhancements

Possible improvements:
1. Add vector embeddings for better search
2. Implement pinecone/vector database for faster retrieval
3. Add advanced filtering options
4. Create user feedback mechanism
5. Add procedure comparison feature
6. Implement persistent chat history
7. Add export functionality

## 📄 License

This tool is for educational and reference purposes.
Ensure compliance with ISO 13485:2016 licensing when used in commercial settings.

## ✨ Version

- **Version:** 1.0
- **Last Updated:** February 2024
- **Status:** Production Ready

---

**Enjoy using the ISO 13485:2016 RAG Chatbot!** 🚀
