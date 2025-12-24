"""
MongoDB Data Analyst - Main Application

A LangGraph-powered natural language interface for querying MongoDB databases.
Supports both CLI and Streamlit web UI modes.
"""
import sys
import subprocess
from config import MONGODB_URI, MONGODB_DATABASE, LLM_API_KEY


def check_config():
    """Check if all required environment variables are set"""
    missing = []
    if not MONGODB_URI:
        missing.append("MONGODB_URI")
    if not MONGODB_DATABASE:
        missing.append("MONGODB_DATABASE")
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    
    if missing:
        print("\n❌ Configuration Error!")
        print("=" * 50)
        print("\nMissing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease create a .env file with these variables.")
        print("\nExample .env file:")
        print("-" * 50)
        print("MONGODB_URI=mongodb://localhost:27017")
        print("MONGODB_DATABASE=your_database_name")
        print("LLM_API_KEY=your_openai_api_key_here")
        print("-" * 50)
        return False
    return True


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              🗄️  MongoDB Data Analyst                            ║
║                                                                  ║
║     Natural Language Queries for Your MongoDB Database          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def get_modules():
    """Import modules after config validation"""
    from graph import ask_question, create_app
    from mongodb_utils import mongo_connection
    return ask_question, mongo_connection


def print_connection_info(mongo_connection):
    """Print MongoDB connection information"""
    print(f"\n📌 MongoDB URI: {MONGODB_URI}")
    print(f"📌 Database: {MONGODB_DATABASE}")
    
    try:
        schema = mongo_connection.get_schema_info()
        collections = schema.get("collections", [])
        print(f"📌 Collections: {len(collections)}")
        for coll in collections:
            print(f"   - {coll['name']} ({coll['document_count']} documents)")
    except Exception as e:
        print(f"⚠️  Could not connect to MongoDB: {e}")
        print("   Make sure MongoDB is running and the connection string is correct.")


def interactive_mode(ask_question, mongo_connection):
    """Run the application in interactive mode"""
    print_banner()
    print_connection_info(mongo_connection)
    
    print("\n" + "=" * 60)
    print("Type your questions in natural language.")
    print("Commands: 'quit' or 'exit' to exit, 'schema' to view database schema")
    print("=" * 60 + "\n")
    
    while True:
        try:
            # Get user input
            question = input("\n🔵 Your Question: ").strip()
            
            # Handle special commands
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                mongo_connection.close()
                break
            
            if question.lower() == 'schema':
                try:
                    schema = mongo_connection.get_schema_info()
                    print("\n📊 Database Schema:")
                    print("-" * 40)
                    for coll in schema.get("collections", []):
                        print(f"\nCollection: {coll['name']}")
                        print(f"  Documents: {coll['document_count']}")
                        print("  Fields:")
                        for field in coll.get("sample_fields", [])[:15]:
                            print(f"    - {field['field']} ({field['type']})")
                        if len(coll.get("sample_fields", [])) > 15:
                            print(f"    ... and {len(coll['sample_fields']) - 15} more fields")
                except Exception as e:
                    print(f"Error getting schema: {e}")
                continue
            
            if question.lower() == 'help':
                print("\n📚 Help:")
                print("-" * 40)
                print("Ask questions about your data in natural language.")
                print("\nExamples:")
                print("  - How many documents are in the users collection?")
                print("  - Show me all orders from last month")
                print("  - What is the average price of products?")
                print("  - Find users who signed up in 2024")
                print("\nCommands:")
                print("  schema - View database structure")
                print("  help   - Show this help message")
                print("  quit   - Exit the application")
                continue
            
            if not question:
                continue
            
            # Process the question
            print("\n⏳ Processing your question...")
            
            result = ask_question(question)
            print("\n" + result.get("final_answer", "No answer generated."))
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            mongo_connection.close()
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def single_query_mode(question: str, ask_question, mongo_connection):
    """Run a single query and exit"""
    print(f"\n🔍 Question: {question}")
    print("\n⏳ Processing...")
    
    result = ask_question(question)
    print("\n" + result.get("final_answer", "No answer generated."))
    
    mongo_connection.close()


def run_streamlit():
    """Launch the Streamlit web UI"""
    print("🚀 Starting Streamlit web UI...")
    print("   Open http://localhost:8501 in your browser")
    subprocess.run(["streamlit", "run", "app.py"])


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--web', '-w', 'web', 'ui']:
            # Web UI mode (config check happens in Streamlit)
            run_streamlit()
            return
        elif arg in ['--help', '-h', 'help']:
            print_banner()
            print("\nUsage:")
            print("  python main.py                    - Interactive CLI mode")
            print("  python main.py --web              - Start Streamlit web UI")
            print("  python main.py \"<question>\"       - Single query mode")
            print("\nOr run Streamlit directly:")
            print("  streamlit run app.py")
            return
    
    # Check configuration before running CLI modes
    if not check_config():
        sys.exit(1)
    
    # Import modules after config validation
    ask_question, mongo_connection = get_modules()
    
    if len(sys.argv) > 1:
        # Single query mode
        question = " ".join(sys.argv[1:])
        single_query_mode(question, ask_question, mongo_connection)
    else:
        # Interactive mode
        interactive_mode(ask_question, mongo_connection)


if __name__ == "__main__":
    main()

