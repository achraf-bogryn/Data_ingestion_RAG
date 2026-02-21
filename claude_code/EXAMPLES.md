# ISO 13485 RAG Chatbot - Example Usage & Test Cases

## 🎯 Getting Started in 5 Minutes

### Step 1: Setup (2 minutes)
```bash
# Navigate to project directory
cd /path/to/iso13485-rag

# Install dependencies
pip install -r requirements.txt

# Create .env with your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Step 2: Launch App (1 minute)
```bash
streamlit run iso_13485_rag.py
```

### Step 3: Start Using (2 minutes)
- Open browser to http://localhost:8501
- Select a search mode
- Ask your first question!

---

## 📚 Example Scenarios

### Scenario 1: Quality Manager Needs Complaint Handling Procedure

**User Goal:** Understand how to handle customer complaints

**Query Type:** Keyword Search

**Steps:**
1. Go to "🔍 Search Procedures" tab
2. Select "Keyword"
3. Enter: `complaint`
4. View results
5. Click "View Full Details" on PROC_8_2_2

**Expected Results:**
- Complaint Management and Handling procedure
- 7-step handling process
- Required documentation
- Regulatory requirements

---

### Scenario 2: Production Manager Questions Design Control Requirements

**User Goal:** Implement design control process

**Query Type:** RAG Assistant

**Question:** "What are the requirements for design and development control?"

**System Flow:**
```
User Input → Search for "design", "development", "control"
         → Retrieve PROC_7_3_1, PROC_7_3_2, PROC_7_3_3, etc.
         → Build context with top 3 procedures
         → Send to OpenAI with query
         → Generate answer with implementation guidance
         → Display results + detailed procedures
```

**Expected Answer:** 
Would include requirements for planning, input, output, review, verification, validation, and transfer of design.

---

### Scenario 3: New Auditor Preparing for Internal Audit

**User Goal:** Understand internal audit requirements

**Query Type:** Procedure ID Search

**Steps:**
1. Go to "🔍 Search Procedures" tab
2. Select "Procedure ID"
3. Enter: `PROC_8_2_4`
4. View complete Internal Audit Procedure

**Information Retrieved:**
- What is required for internal audits
- Implementation steps
- Audit frequency
- Documentation needed
- Key responsibilities

---

### Scenario 4: Quality Engineer Exploring All Management Procedures

**User Goal:** Get overview of management responsibilities

**Query Type:** Browse All

**Steps:**
1. Go to "📚 Browse All" tab
2. Filter by Section: Select "5"
3. Sort by: "Title"
4. Browse all management procedures
5. Expand individual procedures

**Results:** All 8 management responsibility procedures with details

---

### Scenario 5: Supplier Quality Engineer Asks About Outsourced Process Control

**User Goal:** Understand supplier management requirements

**Query Type:** RAG Assistant

**Question:** "How should we control outsourced manufacturing processes?"

**Response Includes:**
- Procedure: PROC_4_1_5
- Requirements for supplier monitoring
- Quality agreement essentials
- Control elements needed
- Responsibility ownership

---

## 🧪 Test Cases

### Test 1: Basic Keyword Search
```
Input: "training"
Expected: Returns procedures related to personnel competency and training
Procedures: PROC_6_2 (Human Resources)
Status: ✅ Pass
```

### Test 2: Complex Query
```
Input: "How to manage non-conforming products before delivery?"
Expected: Returns PROC_8_3_2 with rework and deviation procedures
Status: ✅ Pass
```

### Test 3: Procedure ID Search
```
Input: "PROC_8_5_2"
Expected: Returns Corrective Action Procedure with full details
Status: ✅ Pass
```

### Test 4: Multi-word Search
```
Input: "document control"
Expected: Returns PROC_4_2_4 with version control details
Status: ✅ Pass
```

### Test 5: Regulatory Query
```
Input: "What are FDA reporting requirements?"
Expected: Returns PROC_8_2_3 (Regulatory Authority Reporting)
Status: ✅ Pass
```

### Test 6: Risk Management Query
```
Input: "risk management"
Expected: Returns PROC_7_1 and related risk procedures
Status: ✅ Pass
```

### Test 7: Null/Empty Search
```
Input: "" (empty)
Expected: Shows info message, no error
Status: ✅ Pass
```

### Test 8: Non-existent ID
```
Input: "PROC_99_99"
Expected: Shows "Procedure not found" error
Status: ✅ Pass
```

---

## 💡 Sample Questions for RAG Assistant

### Category: Quality Management System
```
"What is the fundamental structure of an ISO 13485 QMS?"
"What documentation is required for a quality management system?"
"How should the organization manage QMS processes?"
"What role does risk management play in the QMS?"
```

### Category: Management Responsibility
```
"What are the top management's key responsibilities?"
"How often should management reviews be conducted?"
"What should be included in a quality policy?"
"How should organizational roles be defined?"
```

### Category: Resource Management
```
"What resources are needed for an effective QMS?"
"How should personnel competency be managed?"
"What are infrastructure requirements?"
"How to control the work environment for sterile devices?"
```

### Category: Product Realization
```
"What is the design control process?"
"How should product requirements be determined?"
"What is the supplier management process?"
"How to validate manufacturing processes?"
```

### Category: Monitoring & Improvement
```
"How should customer complaints be handled?"
"What is the internal audit procedure?"
"What are corrective action requirements?"
"How to monitor product quality?"
```

---

## 🔍 Search Strategy Guide

### When to Use Keyword Search
- ✅ Don't know exact procedure ID
- ✅ Want to explore related procedures
- ✅ Learning about a topic
- ✅ Quick reference

### When to Use Procedure ID Search
- ✅ Know exact procedure reference
- ✅ Need specific requirement
- ✅ Regulatory/audit reference
- ✅ Direct implementation

### When to Use RAG Assistant
- ✅ Complex questions
- ✅ Want AI-synthesized answers
- ✅ Need context and guidance
- ✅ Implementation planning

### When to Browse All
- ✅ Audit preparation
- ✅ System overview
- ✅ Training new staff
- ✅ Verification/compliance

---

## 📊 Expected Performance

| Operation | Response Time | Notes |
|-----------|---------------|-------|
| Keyword Search | <1 second | Local database search |
| ID Search | <0.5 seconds | Direct lookup |
| RAG Query | 3-5 seconds | Includes OpenAI API call |
| Browse All | <1 second | Full database load |

---

## 🎓 Training Scenarios

### Scenario 1: New QMS Coordinator Orientation
```
Day 1:
1. Read README and Overview (10 min)
2. Explore "📚 Browse All" to see all procedures (20 min)
3. Search for "quality policy" (10 min)
4. Ask assistant "What are management responsibilities?" (10 min)

Day 2:
1. Search for specific section (e.g., Section 8)
2. Review management review procedures
3. Ask questions about audit process
```

### Scenario 2: Auditor Preparation
```
Before Audit:
1. Search "internal audit" → Review PROC_8_2_4
2. Ask "What should internal audits include?" 
3. Review all measurement and monitoring procedures
4. Browse Section 8 procedures

During Audit:
- Reference specific procedures
- Use exact requirement references
- Cross-check findings against procedures
```

### Scenario 3: Compliance Verification
```
1. Browse specific section (e.g., Section 7)
2. For each procedure:
   - Review requirements
   - Check implementation steps
   - Verify documentation
   - Confirm responsibilities
3. Use RAG for complex questions
4. Export procedures as reference
```

---

## 🐛 Known Limitations

1. **Database Scope**
   - Covers 45 key procedures
   - Not exhaustive (full standard is longer)
   - Tailored for common scenarios

2. **Search Limitations**
   - Keyword search is case-insensitive
   - No fuzzy matching for misspellings
   - Exact phrase matching only

3. **RAG Limitations**
   - Depends on OpenAI API availability
   - Response quality depends on question clarity
   - Context limited to top 3 procedures

4. **Database Updates**
   - Manual updates required
   - No automatic standard version updates
   - Procedure additions need code changes

---

## 🚀 Advanced Usage

### Tip 1: Combine Search Methods
- Start with keyword search to explore
- Use ID for specific reference
- Use RAG for questions and context

### Tip 2: Bookmark Frequently Used Procedures
Keep note of procedures you use often:
- PROC_8_2_2 (Complaint Handling)
- PROC_8_5_2 (Corrective Action)
- PROC_7_2_2 (Requirement Review)

### Tip 3: Use for Audit Trail
- Document procedure references in audits
- Export procedure text for compliance files
- Cross-reference requirements

### Tip 4: Training Material
- Use RAG to create training questions
- Use Browse mode to understand flow
- Use detailed procedures for staff training

---

## ✅ Verification Checklist

After setup, verify everything works:

```
□ Streamlit app launches without errors
□ Keyword search returns results
□ ID search finds specific procedures
□ RAG assistant generates answers
□ All 4 modes accessible
□ No API errors in responses
□ Application is responsive
□ No missing procedures
□ Documentation visible
```

---

## 📞 Support & Feedback

If you encounter issues:

1. **Check Setup**
   - Verify .env file exists
   - Confirm API key is valid
   - Check dependencies installed

2. **Review Logs**
   - Check Streamlit console
   - Review error messages
   - Check OpenAI API status

3. **Try Alternative Search**
   - If keyword search fails, try ID
   - If RAG is slow, use browse mode
   - Clear browser cache if needed

---

## 🎉 Success Indicators

You'll know it's working when:

✅ Streamlit dashboard displays
✅ Procedures appear in search results
✅ RAG assistant generates meaningful answers
✅ All navigation tabs are accessible
✅ No error messages in console
✅ Response times are reasonable
✅ Procedure details display completely

---

**Enjoy using the ISO 13485 RAG Chatbot!** 🚀
