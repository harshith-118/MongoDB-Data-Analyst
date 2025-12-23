"""
LangGraph MongoDB Data Analyst Workflow

This module implements the main workflow:
__start__ -> Input Validator -> Exploration Node -> MongoDB Node -> __end__
"""
import json
import re
import requests
from typing import Any, Dict, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from config import LLM_API_URL, LLM_API_KEY
from mongodb_utils import mongo_connection


# ============================================================================
# State Definition
# ============================================================================

class GraphState(TypedDict):
    """State that flows through the graph"""
    # User's original question
    user_question: str
    
    # Validated and cleaned question
    validated_question: Optional[str]
    
    # Validation status
    is_valid: bool
    validation_error: Optional[str]
    
    # Database schema information
    schema_info: Optional[Dict[str, Any]]
    
    # Generated MongoDB query
    generated_query: Optional[str]
    
    # Query execution results
    query_results: Optional[Any]
    query_success: bool
    query_error: Optional[str]
    
    # Final answer for the user
    final_answer: str


# ============================================================================
# LLM API Call
# ============================================================================

def gpt_api_call(data: Dict) -> requests.Response:
    """
    Make API call to GPT model.
    
    Args:
        data: Request payload with messages
        
    Returns:
        API response
    """
    url = LLM_API_URL
    
    payload = json.dumps(data)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LLM_API_KEY}'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    return response


def extract_llm_response(response: requests.Response) -> str:
    """Extract text content from LLM API response"""
    try:
        response_json = response.json()
        # Handle OpenAI-style response format
        if "choices" in response_json:
            return response_json["choices"][0]["message"]["content"]
        # Handle direct content response
        elif "content" in response_json:
            return response_json["content"]
        else:
            return str(response_json)
    except Exception as e:
        return f"Error parsing response: {str(e)}"


# ============================================================================
# Node: Input Validator
# ============================================================================

def input_validator(state: GraphState) -> GraphState:
    """
    Validates and preprocesses the user's input question.
    
    Responsibilities:
    - Check if question is not empty
    - Clean and normalize the question
    - Detect potential injection attempts
    - Validate question is about data querying
    """
    user_question = state.get("user_question", "").strip()
    
    # Check for empty question
    if not user_question:
        return {
            **state,
            "is_valid": False,
            "validation_error": "Question cannot be empty. Please provide a valid question about your data.",
            "final_answer": "Error: No question provided."
        }
    
    # Check minimum length
    if len(user_question) < 5:
        return {
            **state,
            "is_valid": False,
            "validation_error": "Question is too short. Please provide more details.",
            "final_answer": "Error: Question is too short. Please provide more details."
        }
    
    # Check for potential injection patterns (basic security)
    dangerous_patterns = [
        r'\$where\s*:',
        r'function\s*\(',
        r'eval\s*\(',
        r'db\.(drop|remove|delete)',
        r'db\.admin',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, user_question, re.IGNORECASE):
            return {
                **state,
                "is_valid": False,
                "validation_error": "Question contains potentially unsafe content.",
                "final_answer": "Error: Question contains potentially unsafe patterns."
            }
    
    # Clean and normalize the question
    validated_question = " ".join(user_question.split())  # Normalize whitespace
    
    # Get schema information for context
    try:
        schema_info = mongo_connection.get_schema_info()
    except Exception as e:
        schema_info = {"error": str(e), "collections": []}
    
    return {
        **state,
        "validated_question": validated_question,
        "is_valid": True,
        "validation_error": None,
        "schema_info": schema_info
    }


# ============================================================================
# Node: Exploration Node (Query Generator)
# ============================================================================

QUERY_GENERATION_PROMPT = """You are an expert data analyst experienced at using MongoDB.
Your job is to take information about a MongoDB database plus a natural language query and generate a MongoDB shell (mongosh) query to execute to retrieve the information needed to answer the natural language query.

Format the mongosh query in the following structure:

`db.<collection name>.find({/* query */})` or `db.<collection name>.aggregate({/* query */})`

Some general query-authoring tips:

1. Ensure proper use of MongoDB operators ($eq, $gt, $lt, etc.) and data types (ObjectId, ISODate).
2. For complex queries, use aggregation pipeline with proper stages ($match, $group, $lookup, etc.).
3. Consider performance by utilizing available indexes, avoiding $where and full collection scans, and using covered queries where possible.
4. Include sorting (.sort()) and limiting (.limit()) when appropriate for result set management.
5. Handle null values and existence checks explicitly with $exists and $type operators to differentiate between missing fields, null values, and empty arrays.
6. Do not include `null` in results objects in aggregation, e.g. do not include _id: null.
7. For date operations, NEVER use an empty new date object (e.g. `new Date()`). ALWAYS specify the date, such as `new Date("2024-10-24")`. Use the provided 'Latest Date' field to inform dates in queries.
8. For Decimal128 operations, prefer range queries over exact equality.
9. When querying arrays, use appropriate operators like $elemMatch for complex matching, $all to match multiple elements, or $size for array length checks.

DATABASE SCHEMA INFORMATION:
{schema_info}

CURRENT DATE: {current_date}

USER QUESTION:
{question}

Generate ONLY the MongoDB query. Do not include any explanation or additional text. The query should be executable as-is in mongosh.
"""


def exploration_node(state: GraphState) -> GraphState:
    """
    Uses LLM to generate a MongoDB query based on the user's question.
    
    Takes the validated question and schema information to create
    an appropriate MongoDB query.
    """
    if not state.get("is_valid", False):
        return state
    
    question = state.get("validated_question", "")
    schema_info = state.get("schema_info", {})
    
    # Format schema info for the prompt
    schema_text = format_schema_for_prompt(schema_info)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare the prompt
    prompt = QUERY_GENERATION_PROMPT.format(
        schema_info=schema_text,
        current_date=current_date,
        question=question
    )
    
    # Call the LLM API
    try:
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a MongoDB query expert. Generate precise MongoDB queries based on user questions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        response = gpt_api_call(data)
        
        if response.status_code == 200:
            generated_query = extract_llm_response(response)
            # Clean up the query (remove markdown code blocks if present)
            generated_query = clean_query(generated_query)
            
            return {
                **state,
                "generated_query": generated_query
            }
        else:
            error_msg = f"LLM API Error: {response.status_code} - {response.text}"
            return {
                **state,
                "generated_query": None,
                "query_error": error_msg,
                "final_answer": f"Error generating query: {error_msg}"
            }
            
    except Exception as e:
        return {
            **state,
            "generated_query": None,
            "query_error": str(e),
            "final_answer": f"Error calling LLM API: {str(e)}"
        }


def format_schema_for_prompt(schema_info: Dict) -> str:
    """Format schema information for the LLM prompt"""
    if not schema_info or "error" in schema_info:
        return "Schema information not available."
    
    lines = [f"Database: {schema_info.get('database_name', 'unknown')}"]
    lines.append("\nCollections:")
    
    for collection in schema_info.get("collections", []):
        lines.append(f"\n  Collection: {collection['name']}")
        lines.append(f"    Document Count: {collection['document_count']}")
        
        if collection.get("sample_fields"):
            lines.append("    Fields:")
            for field in collection["sample_fields"][:20]:  # Limit fields shown
                lines.append(f"      - {field['field']} ({field['type']})")
        
        if collection.get("indexes"):
            lines.append("    Indexes:")
            for idx in collection["indexes"]:
                lines.append(f"      - {idx}")
    
    return "\n".join(lines)


def clean_query(query: str) -> str:
    """Clean up the generated query string"""
    # Remove markdown code blocks
    query = re.sub(r'```(?:javascript|js|mongo|mongosh)?\n?', '', query)
    query = re.sub(r'```\n?', '', query)
    
    # Remove leading/trailing whitespace
    query = query.strip()
    
    # Remove any explanation text before/after the query
    lines = query.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('db.'):
            # Find the complete query (might span multiple lines)
            query_lines = []
            bracket_count = 0
            started = False
            
            for j in range(i, len(lines)):
                line = lines[j]
                query_lines.append(line)
                
                bracket_count += line.count('(') + line.count('[') + line.count('{')
                bracket_count -= line.count(')') + line.count(']') + line.count('}')
                
                if line.strip().startswith('db.'):
                    started = True
                
                if started and bracket_count <= 0:
                    break
            
            return '\n'.join(query_lines)
    
    return query


# ============================================================================
# Node: MongoDB Execution Node
# ============================================================================

def mongodb_node(state: GraphState) -> GraphState:
    """
    Executes the generated MongoDB query and retrieves results.
    """
    generated_query = state.get("generated_query")
    
    if not generated_query:
        return {
            **state,
            "query_success": False,
            "query_error": "No query was generated",
            "final_answer": "Error: Could not generate a valid query for your question."
        }
    
    try:
        # Execute the query
        success, results = mongo_connection.execute_query(generated_query)
        
        if success:
            # Format results for display
            final_answer = format_results(
                results, 
                state.get("validated_question", ""),
                generated_query
            )
            
            return {
                **state,
                "query_success": True,
                "query_results": results,
                "query_error": None,
                "final_answer": final_answer
            }
        else:
            return {
                **state,
                "query_success": False,
                "query_results": None,
                "query_error": results,  # Error message
                "final_answer": f"Query execution failed: {results}"
            }
            
    except Exception as e:
        return {
            **state,
            "query_success": False,
            "query_results": None,
            "query_error": str(e),
            "final_answer": f"Error executing query: {str(e)}"
        }


def format_results(results: Any, question: str, query: str) -> str:
    """Format query results into a readable answer"""
    output_lines = []
    
    output_lines.append("=" * 60)
    output_lines.append("QUERY RESULTS")
    output_lines.append("=" * 60)
    output_lines.append(f"\n📝 Question: {question}")
    output_lines.append(f"\n🔍 Generated Query:\n{query}")
    output_lines.append("\n" + "-" * 60)
    output_lines.append("📊 Results:\n")
    
    if isinstance(results, list):
        if len(results) == 0:
            output_lines.append("No documents found matching your query.")
        else:
            output_lines.append(f"Found {len(results)} document(s):\n")
            for i, doc in enumerate(results[:50], 1):  # Limit to 50 results
                output_lines.append(f"Document {i}:")
                output_lines.append(json.dumps(doc, indent=2, default=str))
                output_lines.append("")
            
            if len(results) > 50:
                output_lines.append(f"... and {len(results) - 50} more documents")
    elif isinstance(results, (int, float)):
        output_lines.append(f"Result: {results}")
    else:
        output_lines.append(json.dumps(results, indent=2, default=str))
    
    output_lines.append("\n" + "=" * 60)
    
    return "\n".join(output_lines)


# ============================================================================
# Conditional Edge
# ============================================================================

def should_continue(state: GraphState) -> str:
    """
    Determine if we should continue to the next node or end early.
    """
    if not state.get("is_valid", False):
        return "end"
    return "continue"


# ============================================================================
# Graph Builder
# ============================================================================

def build_graph() -> StateGraph:
    """
    Build and return the LangGraph workflow.
    
    Flow:
    __start__ -> input_validator -> exploration_node -> mongodb_node -> __end__
    """
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("input_validator", input_validator)
    workflow.add_node("exploration_node", exploration_node)
    workflow.add_node("mongodb_node", mongodb_node)
    
    # Add edges
    # Start -> Input Validator
    workflow.add_edge(START, "input_validator")
    
    # Input Validator -> Exploration Node (conditional)
    workflow.add_conditional_edges(
        "input_validator",
        should_continue,
        {
            "continue": "exploration_node",
            "end": END
        }
    )
    
    # Exploration Node -> MongoDB Node
    workflow.add_edge("exploration_node", "mongodb_node")
    
    # MongoDB Node -> End
    workflow.add_edge("mongodb_node", END)
    
    return workflow


def create_app():
    """Create and compile the LangGraph application"""
    workflow = build_graph()
    app = workflow.compile()
    return app


# ============================================================================
# Main Query Function
# ============================================================================

def ask_question(question: str) -> Dict[str, Any]:
    """
    Main entry point for asking questions about the database.
    
    Args:
        question: Natural language question about the data
        
    Returns:
        Dictionary with query results and metadata
    """
    app = create_app()
    
    # Initialize state
    initial_state: GraphState = {
        "user_question": question,
        "validated_question": None,
        "is_valid": False,
        "validation_error": None,
        "schema_info": None,
        "generated_query": None,
        "query_results": None,
        "query_success": False,
        "query_error": None,
        "final_answer": ""
    }
    
    # Run the graph
    result = app.invoke(initial_state)
    
    return {
        "question": question,
        "validated_question": result.get("validated_question"),
        "is_valid": result.get("is_valid", False),
        "validation_error": result.get("validation_error"),
        "generated_query": result.get("generated_query"),
        "query_results": result.get("query_results"),
        "query_success": result.get("query_success", False),
        "query_error": result.get("query_error"),
        "final_answer": result.get("final_answer", "No answer generated.")
    }


# For testing the graph structure
if __name__ == "__main__":
    # Build and visualize the graph
    app = create_app()
    print("Graph created successfully!")
    print("\nGraph structure:")
    print("START -> input_validator -> exploration_node -> mongodb_node -> END")

