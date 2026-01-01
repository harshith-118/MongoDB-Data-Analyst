"""
LangGraph MongoDB Data Analyst Workflow

This module implements the main workflow with hallucination detection:
__start__ -> Input Validator -> Exploration Node -> Query Hallucination Node 
-> MongoDB Node -> Summarization Node -> Summary Hallucination Node -> __end__
"""
from langgraph.graph import StateGraph, START, END
from logger_config import logger

from graph_state import GraphState
from graph_nodes import (
    input_validator,
    exploration_node,
    query_hallucination_node,
    mongodb_node,
    summarization_node,
    summary_hallucination_node
)


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


def build_graph() -> StateGraph:
    """
    Build and return the LangGraph workflow.
    
    Flow:
    __start__ -> input_validator -> exploration_node -> query_hallucination_node 
    -> mongodb_node -> summarization_node -> summary_hallucination_node -> __end__
    """
    logger.info("Building LangGraph workflow")
    
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
    
    logger.info("Workflow built successfully")
    return workflow


def create_app():
    """Create and compile the LangGraph application"""
    workflow = build_graph()
    app = workflow.compile()
    return app


def ask_question(question: str) -> dict:
    """
    Main entry point for asking questions about the database.
    
    Args:
        question: Natural language question about the data
        
    Returns:
        Dictionary with query results and metadata
    """
    logger.info(f"Processing question: {question[:100]}...")
    
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
    
    logger.info("Question processing completed")
    
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
    print("START -> input_validator -> exploration_node -> query_hallucination_node")
    print("-> mongodb_node -> summarization_node -> summary_hallucination_node -> END")

