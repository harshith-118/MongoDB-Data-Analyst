"""
Graph State Definition

Defines the state structure that flows through the LangGraph workflow.
"""
from typing import Any, Dict, Optional, TypedDict


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

