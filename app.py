"""
MongoDB Data Analyst - Streamlit Web Application

A beautiful, modern UI for natural language queries to MongoDB.
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List

from config import MONGODB_URI, MONGODB_DATABASE, LLM_API_URL, LLM_API_KEY

# Check if configuration is valid before importing other modules
CONFIG_VALID = all([MONGODB_URI, MONGODB_DATABASE, LLM_API_URL, LLM_API_KEY])

if CONFIG_VALID:
    from graph import ask_question
    from mongodb_utils import mongo_connection

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="MongoDB Data Analyst",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS Styling
# ============================================================================

st.markdown("""
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Root Variables */
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #111827;
        --bg-card: #1a2234;
        --accent-primary: #10b981;
        --accent-secondary: #06d6a0;
        --accent-glow: rgba(16, 185, 129, 0.3);
        --text-primary: #f3f4f6;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --border-color: #374151;
        --error-color: #ef4444;
        --warning-color: #f59e0b;
        --success-color: #10b981;
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        font-family: 'Outfit', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Custom Header */
    .custom-header {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 214, 160, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .custom-header h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        background: linear-gradient(135deg, #10b981 0%, #06d6a0 50%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .custom-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Card Styles */
    .info-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .info-card h3 {
        color: var(--accent-primary);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Query Input Box */
    .stTextArea textarea {
        background: var(--bg-card) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 1rem !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
        color: #0a0e17 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.75rem 2rem !important;
        border: none !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px var(--accent-glow) !important;
    }
    
    /* Code Block Styles */
    .code-block {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.875rem;
        color: #e6edf3;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-all;
    }
    
    /* Result Card */
    .result-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(6, 214, 160, 0.02) 100%);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    
    /* Error Card */
    .error-card {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    
    .error-card h4 {
        color: var(--error-color);
        margin-bottom: 0.5rem;
    }
    
    /* Schema Card */
    .schema-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    
    .schema-card h4 {
        color: var(--accent-primary);
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }
    
    .schema-card .doc-count {
        color: var(--text-muted);
        font-size: 0.8rem;
    }
    
    .field-list {
        margin-top: 0.5rem;
        padding-left: 1rem;
    }
    
    .field-item {
        color: var(--text-secondary);
        font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
        padding: 0.2rem 0;
    }
    
    .field-type {
        color: var(--text-muted);
        font-size: 0.75rem;
    }
    
    /* Sidebar Styles */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }
    
    /* Status Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .status-connected {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success-color);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-disconnected {
        background: rgba(239, 68, 68, 0.15);
        color: var(--error-color);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Workflow Diagram */
    .workflow-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 1rem;
        background: var(--bg-card);
        border-radius: 12px;
        margin: 1rem 0;
        overflow-x: auto;
    }
    
    .workflow-node {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 214, 160, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 0.8rem;
        color: var(--text-primary);
        white-space: nowrap;
    }
    
    .workflow-node.active {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
        color: #0a0e17;
        font-weight: 600;
    }
    
    .workflow-arrow {
        color: var(--accent-primary);
        font-size: 1.2rem;
    }
    
    /* DataFrame Styles */
    .dataframe {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }
    
    /* Expander Styles */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: 8px !important;
    }
    
    /* Metric Styles */
    [data-testid="stMetricValue"] {
        color: var(--accent-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Chat History */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%);
        border: 1px solid rgba(59, 130, 246, 0.2);
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        margin-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Configuration Check
# ============================================================================

if not CONFIG_VALID:
    st.markdown("""
    <div class="custom-header">
        <h1>🗄️ MongoDB Data Analyst</h1>
        <p>Configuration Required</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.error("⚠️ **Environment variables not configured!**")
    
    st.markdown("""
    ### Setup Instructions
    
    Create a `.env` file in the project root with the following variables:
    
    ```env
    # MongoDB Configuration
    MONGODB_URI=mongodb://localhost:27017
    MONGODB_DATABASE=your_database_name
    
    # LLM API Configuration
    LLM_API_URL=https://your-api-endpoint.com/api/v1/chat
    LLM_API_KEY=your_api_key_here
    ```
    
    ### Missing Variables:
    """)
    
    missing = []
    if not MONGODB_URI:
        missing.append("- `MONGODB_URI` - MongoDB connection string")
    if not MONGODB_DATABASE:
        missing.append("- `MONGODB_DATABASE` - Database name to query")
    if not LLM_API_URL:
        missing.append("- `LLM_API_URL` - LLM API endpoint")
    if not LLM_API_KEY:
        missing.append("- `LLM_API_KEY` - API authentication key")
    
    for m in missing:
        st.markdown(m)
    
    st.info("After creating the `.env` file, restart the Streamlit app.")
    st.stop()

# ============================================================================
# Session State Initialization
# ============================================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "schema_loaded" not in st.session_state:
    st.session_state.schema_loaded = False
    st.session_state.schema_info = None

if "connection_status" not in st.session_state:
    st.session_state.connection_status = "unknown"

# ============================================================================
# Helper Functions
# ============================================================================

def load_schema():
    """Load database schema information"""
    try:
        schema = mongo_connection.get_schema_info()
        st.session_state.schema_info = schema
        st.session_state.schema_loaded = True
        st.session_state.connection_status = "connected"
        return schema
    except Exception as e:
        st.session_state.connection_status = "disconnected"
        st.session_state.schema_info = {"error": str(e), "collections": []}
        return None

def format_results_for_display(results: Any) -> tuple:
    """Format query results for Streamlit display"""
    if isinstance(results, list):
        if len(results) == 0:
            return "empty", None
        # Try to convert to DataFrame
        try:
            df = pd.DataFrame(results)
            return "dataframe", df
        except:
            return "json", results
    elif isinstance(results, (int, float)):
        return "scalar", results
    else:
        return "json", results

def render_workflow_diagram(active_node: str = None):
    """Render the workflow diagram"""
    nodes = ["__start__", "Input Validator", "Exploration Node", "MongoDB", "__end__"]
    
    html = '<div class="workflow-container">'
    for i, node in enumerate(nodes):
        active_class = "active" if node == active_node else ""
        html += f'<div class="workflow-node {active_class}">{node}</div>'
        if i < len(nodes) - 1:
            html += '<span class="workflow-arrow">→</span>'
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)

# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #10b981; margin-bottom: 0.5rem;">🗄️ MongoDB Analyst</h2>
        <p style="color: #9ca3af; font-size: 0.9rem;">Natural Language Queries</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Connection Status
    st.markdown("### 🔌 Connection")
    
    # Load schema on first run
    if not st.session_state.schema_loaded:
        with st.spinner("Connecting to MongoDB..."):
            load_schema()
    
    if st.session_state.connection_status == "connected":
        st.markdown("""
        <div class="status-badge status-connected">
            <span>●</span> Connected
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"**Database:** {MONGODB_DATABASE}")
    else:
        st.markdown("""
        <div class="status-badge status-disconnected">
            <span>●</span> Disconnected
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Retry Connection"):
            load_schema()
            st.rerun()
    
    st.divider()
    
    # Database Schema
    st.markdown("### 📊 Schema")
    
    if st.session_state.schema_info and "collections" in st.session_state.schema_info:
        collections = st.session_state.schema_info.get("collections", [])
        
        if collections:
            for coll in collections:
                with st.expander(f"📁 {coll['name']}", expanded=False):
                    st.caption(f"📄 {coll['document_count']:,} documents")
                    
                    if coll.get("sample_fields"):
                        st.markdown("**Fields:**")
                        for field in coll["sample_fields"][:10]:
                            st.markdown(f"<span class='field-item'>• {field['field']} <span class='field-type'>({field['type']})</span></span>", unsafe_allow_html=True)
                        
                        if len(coll["sample_fields"]) > 10:
                            st.caption(f"... and {len(coll['sample_fields']) - 10} more fields")
        else:
            st.info("No collections found")
    else:
        st.warning("Schema not available")
    
    st.divider()
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Schema"):
        with st.spinner("Refreshing..."):
            load_schema()
        st.rerun()
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Example Questions
    st.markdown("### 💡 Example Questions")
    
    examples = [
        "How many documents are in each collection?",
        "Show me the first 5 documents",
        "What are the unique values in field X?",
        "Find documents where field > value",
        "Count documents grouped by field"
    ]
    
    for example in examples:
        st.caption(f"• {example}")

# ============================================================================
# Main Content
# ============================================================================

# Header
st.markdown("""
<div class="custom-header">
    <h1>🗄️ MongoDB Data Analyst</h1>
    <p>Ask questions about your data in natural language</p>
</div>
""", unsafe_allow_html=True)

# Workflow Diagram
with st.expander("📊 View Workflow Pipeline", expanded=False):
    render_workflow_diagram()
    st.caption("Your question flows through these nodes to generate and execute MongoDB queries.")

# Main Query Section
st.markdown("### 💬 Ask Your Question")

# Query Input
col1, col2 = st.columns([4, 1])

with col1:
    user_question = st.text_area(
        label="Your Question",
        placeholder="E.g., How many documents are in the users collection? Show me all orders from last month...",
        height=100,
        label_visibility="collapsed"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    submit_button = st.button("🚀 Query", use_container_width=True)

# Process Query
if submit_button and user_question:
    # Add to chat history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question,
        "timestamp": datetime.now()
    })
    
    # Show processing status
    with st.status("🔄 Processing your query...", expanded=True) as status:
        st.write("📝 Validating input...")
        
        # Call the LangGraph workflow
        result = ask_question(user_question)
        
        if result["is_valid"]:
            st.write("🔍 Generating MongoDB query...")
            st.write("⚡ Executing query...")
            
            if result["query_success"]:
                status.update(label="✅ Query completed!", state="complete", expanded=False)
            else:
                status.update(label="⚠️ Query had issues", state="error", expanded=False)
        else:
            status.update(label="❌ Validation failed", state="error", expanded=False)
    
    # Add result to chat history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result,
        "timestamp": datetime.now()
    })

# Display Chat History
if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("### 📜 Results")
    
    # Display in reverse order (newest first)
    for i, message in enumerate(reversed(st.session_state.chat_history)):
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>🧑 You</strong> <span style="color: #6b7280; font-size: 0.8rem;">
                    {message["timestamp"].strftime("%H:%M:%S")}
                </span>
                <p style="margin-top: 0.5rem; color: #e5e7eb;">{message["content"]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        elif message["role"] == "assistant":
            result = message["content"]
            
            with st.container():
                # Validation Error
                if not result.get("is_valid", False):
                    st.markdown(f"""
                    <div class="error-card">
                        <h4>❌ Validation Error</h4>
                        <p style="color: #fca5a5;">{result.get("validation_error", "Unknown error")}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Query Generated
                elif result.get("generated_query"):
                    st.markdown("""
                    <div class="result-card">
                    """, unsafe_allow_html=True)
                    
                    # Generated Query
                    st.markdown("**🔍 Generated MongoDB Query:**")
                    st.code(result["generated_query"], language="javascript")
                    
                    # Query Results
                    if result.get("query_success"):
                        st.markdown("**📊 Results:**")
                        
                        results = result.get("query_results")
                        result_type, formatted_data = format_results_for_display(results)
                        
                        if result_type == "empty":
                            st.info("No documents found matching your query.")
                        
                        elif result_type == "dataframe":
                            # Show metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Documents Found", len(formatted_data))
                            with col2:
                                st.metric("Columns", len(formatted_data.columns))
                            with col3:
                                st.metric("Query Status", "✅ Success")
                            
                            # Show dataframe
                            st.dataframe(
                                formatted_data,
                                use_container_width=True,
                                height=400
                            )
                            
                            # Download button
                            csv = formatted_data.to_csv(index=False)
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        
                        elif result_type == "scalar":
                            st.metric("Result", formatted_data)
                        
                        else:
                            # JSON display
                            st.json(formatted_data)
                    
                    else:
                        # Query Error
                        st.error(f"**Query Error:** {result.get('query_error', 'Unknown error')}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

# Empty State
if not st.session_state.chat_history:
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #6b7280;">
        <p style="font-size: 3rem; margin-bottom: 1rem;">💬</p>
        <h3 style="color: #9ca3af;">Start by asking a question</h3>
        <p>Type your question in natural language above and click Query</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p style="font-size: 0.85rem;">
        MongoDB Data Analyst • Powered by LangGraph & GPT
    </p>
</div>
""", unsafe_allow_html=True)

