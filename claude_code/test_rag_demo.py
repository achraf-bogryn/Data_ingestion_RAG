import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load procedures database
def load_database():
    """Load procedures from JSON file"""
    try:
        with open('/home/claude/iso_13485_procedures.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: iso_13485_procedures.json not found!")
        return None

def search_procedures_by_keyword(keyword: str, database: Dict) -> List[Dict]:
    """Search procedures by keyword"""
    results = []
    keyword_lower = keyword.lower()
    
    for section in database.get('sections', []):
        if 'procedures' in section:
            for proc in section['procedures']:
                if (keyword_lower in proc.get('title', '').lower() or
                    keyword_lower in proc.get('description', '').lower() or
                    any(keyword_lower in k.lower() for k in proc.get('keywords', []))):
                    results.append(proc)
        
        if 'subsections' in section:
            for subsection in section['subsections']:
                if 'procedures' in subsection:
                    for proc in subsection['procedures']:
                        if (keyword_lower in proc.get('title', '').lower() or
                            keyword_lower in proc.get('description', '').lower() or
                            any(keyword_lower in k.lower() for k in proc.get('keywords', []))):
                            results.append(proc)
    
    return results

def search_procedures_by_id(proc_id: str, database: Dict) -> Dict:
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

def display_procedure(proc: Dict):
    """Display full procedure details"""
    print("\n" + "="*80)
    print(f"📋 PROCEDURE: {proc.get('title', 'Unknown')}")
    print("="*80)
    print(f"\n🔹 ID: {proc.get('proc_id', 'N/A')}")
    print(f"🔹 Requirement: {proc.get('requirement', 'N/A')}")
    print(f"\n📝 Description:")
    print(f"   {proc.get('description', 'N/A')}")
    
    print(f"\n✅ What is Required:")
    for req in proc.get('what_is_required', [])[:5]:
        print(f"   • {req}")
    
    print(f"\n🎯 Key Requirements:")
    for req in proc.get('key_requirements', [])[:5]:
        print(f"   • {req}")
    
    print(f"\n📋 Implementation Steps:")
    for i, step in enumerate(proc.get('implementation_steps', [])[:6], 1):
        print(f"   {step}")
    
    print(f"\n👥 Responsibilities:")
    for resp in proc.get('responsibilities', []):
        print(f"   • {resp}")
    
    print(f"\n📑 Documentation Needed:")
    for doc in proc.get('documentation_needed', []):
        print(f"   • {doc}")
    
    print(f"\n💡 Example:")
    print(f"   {proc.get('examples', 'N/A')}")
    
    print(f"\n🔑 Keywords: {', '.join(proc.get('keywords', []))}")
    print(f"\n🔗 Related Procedures: {', '.join(proc.get('related_procedures', []))}")
    print("\n" + "="*80 + "\n")

def display_summary_list(procedures: List[Dict], title: str):
    """Display summary list of procedures"""
    print(f"\n{'='*80}")
    print(f"📚 {title} ({len(procedures)} procedures)")
    print(f"{'='*80}\n")
    
    for i, proc in enumerate(procedures, 1):
        print(f"{i}. {proc.get('proc_id', 'Unknown')} - {proc.get('title', 'Unknown')}")
        print(f"   Requirement: {proc.get('requirement', 'N/A')}")
        print(f"   Description: {proc.get('description', 'N/A')[:80]}...")
        print()

def interactive_mode(database: Dict):
    """Interactive command-line interface"""
    print("\n" + "="*80)
    print("🤖 ISO 13485:2016 RAG Chatbot - Interactive Mode")
    print("="*80)
    print("\nCommands:")
    print("  'search <keyword>' - Search by keyword (e.g., 'search complaint')")
    print("  'find <proc_id>'   - Find by procedure ID (e.g., 'find PROC_8_2_2')")
    print("  'ask <question>'   - Ask RAG assistant (e.g., 'ask How to handle complaints?')")
    print("  'browse'           - List all procedures")
    print("  'section <num>'    - Show procedures in section (e.g., 'section 8')")
    print("  'help'             - Show help")
    print("  'exit'             - Exit program")
    print("="*80 + "\n")
    
    while True:
        try:
            user_input = input("🔍 Enter command (or 'help' for options): ").strip()
            
            if not user_input:
                continue
            
            # Parse command
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            # Execute commands
            if command == 'exit':
                print("\n👋 Goodbye!\n")
                break
            
            elif command == 'help':
                print("\n📖 Available Commands:")
                print("  search <keyword>   - Search procedures by keyword")
                print("  find <proc_id>     - Get specific procedure by ID")
                print("  ask <question>     - Ask RAG assistant a question")
                print("  browse             - List all procedures")
                print("  section <num>      - Show procedures by section number")
                print("  examples           - Show example queries")
                print("  exit               - Exit the program\n")
            
            elif command == 'search':
                if not arg:
                    print("❌ Please provide a keyword to search")
                    continue
                
                print(f"\n🔍 Searching for: '{arg}'...")
                results = search_procedures_by_keyword(arg, database)
                
                if results:
                    display_summary_list(results, f"Search Results for '{arg}'")
                    
                    # Ask if user wants details
                    view = input("📖 View full details of a procedure? Enter ID (or 'no'): ").strip()
                    if view.lower() != 'no' and view:
                        proc = search_procedures_by_id(view, database)
                        if proc:
                            display_procedure(proc)
                        else:
                            print(f"❌ Procedure '{view}' not found")
                else:
                    print(f"❌ No procedures found for keyword '{arg}'")
            
            elif command == 'find':
                if not arg:
                    print("❌ Please provide a procedure ID")
                    continue
                
                print(f"\n🔍 Finding procedure: {arg}...")
                proc = search_procedures_by_id(arg, database)
                
                if proc:
                    display_procedure(proc)
                else:
                    print(f"❌ Procedure '{arg}' not found")
            
            elif command == 'ask':
                if not arg:
                    print("❌ Please provide a question")
                    continue
                
                print(f"\n💬 Your question: {arg}")
                print("\n⏳ Searching procedures and generating answer...")
                
                # Search for relevant procedures
                keywords = [word for word in arg.lower().split() if len(word) > 3]
                all_results = []
                
                for keyword in keywords[:3]:
                    results = search_procedures_by_keyword(keyword, database)
                    all_results.extend(results)
                
                # Remove duplicates
                seen_ids = set()
                unique_results = []
                for proc in all_results:
                    if proc.get('proc_id') not in seen_ids:
                        unique_results.append(proc)
                        seen_ids.add(proc.get('proc_id'))
                
                if unique_results:
                    print(f"\n✅ Found {len(unique_results)} relevant procedures:")
                    for proc in unique_results[:3]:
                        print(f"   • {proc.get('proc_id')}: {proc.get('title')}")
                    
                    print("\n⏳ Generating answer from OpenAI...")
                    answer = query_openai_for_rag(arg, unique_results)
                    
                    print("\n" + "="*80)
                    print("📝 ANSWER:")
                    print("="*80)
                    print(f"\n{answer}\n")
                    
                    # Show detailed procedures
                    view = input("📖 View detailed procedures? (yes/no): ").strip().lower()
                    if view == 'yes':
                        for proc in unique_results[:3]:
                            display_procedure(proc)
                else:
                    print(f"❌ No relevant procedures found for your question")
            
            elif command == 'browse':
                all_procs = get_all_procedures(database)
                display_summary_list(all_procs, "All Procedures")
                
                # Option to view specific procedure
                proc_id = input("📖 View full details? Enter procedure ID (or 'no'): ").strip()
                if proc_id.lower() != 'no' and proc_id:
                    proc = search_procedures_by_id(proc_id, database)
                    if proc:
                        display_procedure(proc)
                    else:
                        print(f"❌ Procedure '{proc_id}' not found")
            
            elif command == 'section':
                if not arg:
                    print("❌ Please provide a section number (e.g., '8')")
                    continue
                
                all_procs = get_all_procedures(database)
                section_procs = [p for p in all_procs if p.get('requirement', '').startswith(arg)]
                
                if section_procs:
                    display_summary_list(section_procs, f"Procedures in Section {arg}")
                else:
                    print(f"❌ No procedures found in section '{arg}'")
            
            elif command == 'examples':
                print("\n📌 Example Queries:")
                examples = [
                    "search complaint",
                    "find PROC_8_2_2",
                    "ask How to handle customer complaints?",
                    "ask What are the requirements for design control?",
                    "ask What documentation is required?",
                    "section 8",
                    "browse"
                ]
                for example in examples:
                    print(f"   > {example}")
                print()
            
            else:
                print(f"❌ Unknown command: '{command}'. Type 'help' for options.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            continue

def demo_mode(database: Dict):
    """Automated demo showing RAG capabilities"""
    print("\n" + "="*80)
    print("🚀 ISO 13485:2016 RAG Chatbot - Demo Mode")
    print("="*80)
    
    demo_queries = [
        ("search", "complaint"),
        ("find", "PROC_8_2_2"),
        ("ask", "How to handle customer complaints?")
    ]
    
    for i, (cmd_type, query) in enumerate(demo_queries, 1):
        print(f"\n{'─'*80}")
        print(f"📍 Demo {i}: {cmd_type.upper()} - {query}")
        print(f"{'─'*80}")
        
        if cmd_type == "search":
            results = search_procedures_by_keyword(query, database)
            if results:
                print(f"✅ Found {len(results)} procedures:")
                display_summary_list(results, f"Search Results")
        
        elif cmd_type == "find":
            proc = search_procedures_by_id(query, database)
            if proc:
                display_procedure(proc)
        
        elif cmd_type == "ask":
            print(f"💬 Question: {query}")
            keywords = [word for word in query.lower().split() if len(word) > 3]
            all_results = []
            for keyword in keywords[:3]:
                results = search_procedures_by_keyword(keyword, database)
                all_results.extend(results)
            
            seen_ids = set()
            unique_results = []
            for proc in all_results:
                if proc.get('proc_id') not in seen_ids:
                    unique_results.append(proc)
                    seen_ids.add(proc.get('proc_id'))
            
            if unique_results:
                print(f"✅ Found {len(unique_results)} relevant procedures")
                print("\n⏳ Calling OpenAI API...")
                answer = query_openai_for_rag(query, unique_results)
                print(f"\n📝 Answer:\n{answer}")
    
    print(f"\n{'='*80}")
    print("✨ Demo Complete!")
    print(f"{'='*80}\n")

def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🤖 ISO 13485:2016 Retrieval-Augmented Generation (RAG) Chatbot")
    print("="*80)
    
    # Load database
    print("\n📂 Loading procedures database...")
    database = load_database()
    
    if not database:
        return
    
    all_procs = get_all_procedures(database)
    print(f"✅ Loaded {len(all_procs)} procedures from {len(database.get('sections', []))} sections")
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY not found in environment")
        print("   Set it in your .env file to use RAG features")
    else:
        print("✅ OpenAI API key configured")
    
    # Choose mode
    print("\n" + "="*80)
    print("Select Mode:")
    print("1. Interactive Mode (explore and ask questions)")
    print("2. Demo Mode (see examples)")
    print("="*80)
    
    mode = input("\nEnter your choice (1 or 2, or press Enter for interactive): ").strip()
    
    if mode == "2":
        demo_mode(database)
    else:
        interactive_mode(database)

if __name__ == "__main__":
    main()
