"""
LangGraph MongoDB Data Analyst Workflow

This module implements the main workflow:
__start__ -> Input Validator -> Exploration Node -> MongoDB Node -> __end__
"""
import json
import re
from typing import Any, Dict, Optional, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from openai import OpenAI

from config import LLM_API_KEY
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
    
    # Summarized answer (natural language response)
    summarized_answer: Optional[str]
    
    # Hallucination detection
    query_hallucination_detected: bool
    summary_hallucination_detected: bool
    query_retry_count: int
    summary_retry_count: int
    max_retries: int


# ============================================================================
# LLM API Call
# ============================================================================

def gpt_api_call(data: Dict) -> str:
    """
    Make API call to GPT model using OpenAI client.
    
    Args:
        data: Request payload with messages, temperature, max_tokens, etc.
        
    Returns:
        Response content as string
        
    Raises:
        Exception: If API call fails
    """
    client = OpenAI(api_key=LLM_API_KEY)
    
    # Extract parameters from data dict
    messages = data.get("messages", [])
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 1000)
    model = data.get("model", "gpt-3.5-turbo")
    
    # Make the API call
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # Extract and return the content
    return response.choices[0].message.content


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
    
    # Get current retry count
    retry_count = state.get("query_retry_count", 0)
    
    # Increment retry count if this is a retry (hallucination was detected)
    if state.get("query_hallucination_detected", False):
        retry_count = retry_count + 1
    
    # Format schema info for the prompt
    schema_text = format_schema_for_prompt(schema_info)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare the prompt using string replacement to avoid curly brace conflicts
    prompt = QUERY_GENERATION_PROMPT.replace("{schema_info}", schema_text)
    prompt = prompt.replace("{current_date}", current_date)
    prompt = prompt.replace("{question}", question)
    
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
        
        generated_query = gpt_api_call(data)
        # Clean up the query (remove markdown code blocks if present)
        generated_query = clean_query(generated_query)
        
        return {
            **state,
            "generated_query": generated_query,
            "query_retry_count": retry_count,
            "query_hallucination_detected": False  # Reset for new query
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
            # Store raw results - summarization node will format them
            return {
                **state,
                "query_success": True,
                "query_results": results,
                "query_error": None,
                "final_answer": ""  # Will be set by summarization node
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
# Node: Query Hallucination Detection
# ============================================================================

QUERY_HALLUCINATION_PROMPT = """You are a MongoDB query validator. Your task is to check if the generated MongoDB query contains hallucinations or errors.

DATABASE SCHEMA:
{schema_info}

USER'S QUESTION:
{question}

GENERATED QUERY:
{query}

Check if the query:
1. References collections that exist in the schema
2. Uses field names that exist in the collections
3. Uses valid MongoDB operators and syntax
4. Matches the intent of the user's question

Respond with ONLY "VALID" if the query is correct, or "HALLUCINATION: [reason]" if there are issues."""


def query_hallucination_node(state: GraphState) -> GraphState:
    """
    Detects hallucinations in the generated MongoDB query.
    Returns state with query_hallucination_detected flag.
    """
    generated_query = state.get("generated_query")
    question = state.get("validated_question", "")
    schema_info = state.get("schema_info", {})
    retry_count = state.get("query_retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # If already exceeded max retries, skip detection
    if retry_count >= max_retries:
        return {
            **state,
            "query_hallucination_detected": False  # Accept query after max retries
        }
    
    if not generated_query:
        return {
            **state,
            "query_hallucination_detected": False
        }
    
    try:
        # Format schema for prompt
        schema_text = format_schema_for_prompt(schema_info)
        
        # Prepare hallucination detection prompt
        prompt = QUERY_HALLUCINATION_PROMPT.replace("{schema_info}", schema_text)
        prompt = prompt.replace("{question}", question)
        prompt = prompt.replace("{query}", generated_query)
        
        # Call LLM for hallucination detection
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a MongoDB query validator. Analyze queries for hallucinations and errors."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        validation_response = gpt_api_call(data).strip()
        
        # Check if hallucination detected
        hallucination_detected = not validation_response.upper().startswith("VALID")
        
        return {
            **state,
            "query_hallucination_detected": hallucination_detected
        }
        
    except Exception as e:
        # On error, assume no hallucination to continue flow
        return {
            **state,
            "query_hallucination_detected": False
        }


# ============================================================================
# Node: Summary Hallucination Detection
# ============================================================================

SUMMARY_HALLUCINATION_PROMPT = """You are a fact-checker. Your task is to verify if the summary accurately represents the query results.

USER'S QUESTION:
{question}

QUERY RESULTS:
{results}

GENERATED SUMMARY:
{summary}

Check if the summary:
1. Accurately reflects the data in the results
2. Doesn't make claims not supported by the results
3. Uses correct numbers, names, and facts from the results
4. Doesn't hallucinate information not present in the data

Respond with ONLY "VALID" if the summary is accurate, or "HALLUCINATION: [specific issue]" if there are inaccuracies."""


def summary_hallucination_node(state: GraphState) -> GraphState:
    """
    Detects hallucinations in the generated summary.
    Returns state with summary_hallucination_detected flag.
    """
    summarized_answer = state.get("summarized_answer")
    query_results = state.get("query_results")
    question = state.get("validated_question", "")
    retry_count = state.get("summary_retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # If already exceeded max retries, skip detection
    if retry_count >= max_retries:
        return {
            **state,
            "summary_hallucination_detected": False  # Accept summary after max retries
        }
    
    if not summarized_answer or query_results is None:
        return {
            **state,
            "summary_hallucination_detected": False
        }
    
    try:
        # Format results for prompt
        results_text = format_results_for_summarization(query_results, max_items=10, max_length=2000)
        
        # Prepare hallucination detection prompt
        prompt = SUMMARY_HALLUCINATION_PROMPT.replace("{question}", question)
        prompt = prompt.replace("{results}", results_text)
        prompt = prompt.replace("{summary}", summarized_answer)
        
        # Call LLM for hallucination detection
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a fact-checker. Verify summaries against actual data for accuracy."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        validation_response = gpt_api_call(data).strip()
        
        # Check if hallucination detected
        hallucination_detected = not validation_response.upper().startswith("VALID")
        
        return {
            **state,
            "summary_hallucination_detected": hallucination_detected
        }
        
    except Exception as e:
        # On error, assume no hallucination to continue flow
        return {
            **state,
            "summary_hallucination_detected": False
        }


# ============================================================================
# Node: Summarization Node
# ============================================================================

SUMMARIZATION_PROMPT = """You are a helpful data analyst assistant. Your task is to analyze query results and provide a clear, natural language answer to the user's question.

USER'S QUESTION:
{question}

QUERY RESULTS:
{results}

QUERY USED:
{query}

Based on the query results above, provide a clear and concise answer to the user's question. 
- If the results are empty, explain that no data was found matching the criteria.
- If there are results, summarize the key findings in a natural, conversational way.
- Include specific numbers, names, or data points from the results when relevant.
- Be concise but informative.
- Do not include the raw query or technical details unless specifically asked.

Your answer:"""


def summarization_node(state: GraphState) -> GraphState:
    """
    Summarizes query results into a natural language answer using LLM.
    """
    query_success = state.get("query_success", False)
    query_results = state.get("query_results")
    question = state.get("validated_question", "")
    generated_query = state.get("generated_query", "")
    query_error = state.get("query_error")
    
    # Get current retry count
    retry_count = state.get("summary_retry_count", 0)
    
    # Increment retry count if this is a retry (hallucination was detected)
    if state.get("summary_hallucination_detected", False):
        retry_count = retry_count + 1
    
    # If query failed, return error message without summarization
    if not query_success:
        error_message = query_error or "Query execution failed"
        return {
            **state,
            "summarized_answer": f"I encountered an error while processing your question: {error_message}",
            "final_answer": f"Error: {error_message}"
        }
    
    # If no results, handle empty result case
    if query_results is None:
        return {
            **state,
            "summarized_answer": "I couldn't retrieve any results for your query.",
            "final_answer": "No results found for your query."
        }
    
    # Handle empty list results
    if isinstance(query_results, list) and len(query_results) == 0:
        try:
            # Still try to get a summary from LLM for empty results
            prompt = f"""The user asked: "{question}"

The query executed was: {generated_query}

However, no results were found matching the query criteria.

Provide a helpful, natural language response explaining that no data was found matching their question."""
            
            data = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful data analyst assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }
            
            summarized_answer = gpt_api_call(data)
            
            return {
                **state,
                "summarized_answer": summarized_answer,
                "summary_retry_count": retry_count,
                "summary_hallucination_detected": False,  # Reset for new summary
                "final_answer": f"{summarized_answer}\n\n" + "=" * 60 + "\n📊 Query Details:\n" + "=" * 60 + f"\nQuery: {generated_query}\n\nNo documents found matching your query."
            }
        except Exception as e:
            return {
                **state,
                "summarized_answer": "No results were found matching your query criteria.",
                "final_answer": f"No results found.\n\nQuery: {generated_query}"
            }
    
    try:
        # Format results for the prompt (limit size to avoid token limits)
        results_text = format_results_for_summarization(query_results)
        
        # Prepare the summarization prompt
        prompt = SUMMARIZATION_PROMPT.replace("{question}", question)
        prompt = prompt.replace("{results}", results_text)
        prompt = prompt.replace("{query}", generated_query)
        
        # Call the LLM API for summarization
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful data analyst assistant. Provide clear, natural language summaries of query results."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        summarized_answer = gpt_api_call(data)
        
        # Combine the summary with the detailed results
        final_answer = f"{summarized_answer}\n\n" + "=" * 60 + "\n📊 Detailed Results:\n" + "=" * 60 + "\n" + format_results(
            query_results,
            question,
            generated_query
        )
        
        return {
            **state,
            "summarized_answer": summarized_answer,
            "summary_retry_count": retry_count,
            "summary_hallucination_detected": False,  # Reset for new summary
            "final_answer": final_answer
        }
        
    except Exception as e:
        # If summarization fails, return the original formatted results
        return {
            **state,
            "summarized_answer": None,
            "summary_retry_count": retry_count,
            "summary_hallucination_detected": False,
            "final_answer": state.get("final_answer", f"Error during summarization: {str(e)}")
        }


def format_results_for_summarization(results: Any, max_items: int = 20, max_length: int = 3000) -> str:
    """
    Format query results for LLM summarization (more compact than full display).
    """
    if isinstance(results, list):
        if len(results) == 0:
            return "No results found."
        
        # Limit the number of items shown
        items_to_show = results[:max_items]
        result_text = f"Found {len(results)} result(s). Showing first {len(items_to_show)}:\n\n"
        
        for i, doc in enumerate(items_to_show, 1):
            # Convert to JSON string but keep it compact
            doc_str = json.dumps(doc, indent=2, default=str)
            # Truncate very long documents
            if len(doc_str) > 500:
                doc_str = doc_str[:500] + "... (truncated)"
            result_text += f"Result {i}:\n{doc_str}\n\n"
        
        if len(results) > max_items:
            result_text += f"... and {len(results) - max_items} more results (not shown)\n"
        
        # Truncate if too long
        if len(result_text) > max_length:
            result_text = result_text[:max_length] + "... (truncated for length)"
        
        return result_text
    elif isinstance(results, (int, float)):
        return f"Result: {results}"
    else:
        result_str = json.dumps(results, indent=2, default=str)
        if len(result_str) > max_length:
            result_str = result_str[:max_length] + "... (truncated)"
        return result_str


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


def should_retry_query(state: GraphState) -> str:
    """
    Determine if we should retry query generation due to hallucination.
    """
    hallucination_detected = state.get("query_hallucination_detected", False)
    retry_count = state.get("query_retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if hallucination_detected and retry_count < max_retries:
        return "retry"
    return "continue"


def should_retry_summary(state: GraphState) -> str:
    """
    Determine if we should retry summary generation due to hallucination.
    """
    hallucination_detected = state.get("summary_hallucination_detected", False)
    retry_count = state.get("summary_retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if hallucination_detected and retry_count < max_retries:
        return "retry"
    return "continue"


# ============================================================================
# Graph Builder
# ============================================================================

def build_graph() -> StateGraph:
    """
    Build and return the LangGraph workflow.
    
    Flow:
    __start__ -> input_validator -> exploration_node -> query_hallucination_node -> mongodb_node -> summarization_node -> summary_hallucination_node -> __end__
    """
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("input_validator", input_validator)
    workflow.add_node("exploration_node", exploration_node)
    workflow.add_node("query_hallucination_node", query_hallucination_node)
    workflow.add_node("mongodb_node", mongodb_node)
    workflow.add_node("summarization_node", summarization_node)
    workflow.add_node("summary_hallucination_node", summary_hallucination_node)
    
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
    
    # Exploration Node -> Query Hallucination Detection
    workflow.add_edge("exploration_node", "query_hallucination_node")
    
    # Query Hallucination Node -> MongoDB Node or retry (conditional)
    workflow.add_conditional_edges(
        "query_hallucination_node",
        should_retry_query,
        {
            "retry": "exploration_node",  # Retry query generation
            "continue": "mongodb_node"     # Continue to execution
        }
    )
    
    # MongoDB Node -> Summarization Node
    workflow.add_edge("mongodb_node", "summarization_node")
    
    # Summarization Node -> Summary Hallucination Detection
    workflow.add_edge("summarization_node", "summary_hallucination_node")
    
    # Summary Hallucination Node -> End or retry (conditional)
    workflow.add_conditional_edges(
        "summary_hallucination_node",
        should_retry_summary,
        {
            "retry": "summarization_node",  # Retry summary generation
            "continue": END                  # End workflow
        }
    )
    
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
        "final_answer": "",
        "summarized_answer": None,
        "query_hallucination_detected": False,
        "summary_hallucination_detected": False,
        "query_retry_count": 0,
        "summary_retry_count": 0,
        "max_retries": 3
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
        "final_answer": result.get("final_answer", "No answer generated."),
        "summarized_answer": result.get("summarized_answer")
    }


# For testing the graph structure
if __name__ == "__main__":
    # Build and visualize the graph
    app = create_app()
    print("Graph created successfully!")
    print("\nGraph structure:")
    print("START -> input_validator -> exploration_node -> mongodb_node -> END")

