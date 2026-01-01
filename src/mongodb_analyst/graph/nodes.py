"""
Graph Nodes

Contains all the node functions for the LangGraph workflow.
Each node processes the state and returns updated state.
"""
import re
from datetime import datetime
from typing import Dict, Any

from ..config.logger import logger
from ..monitoring.metrics import metrics_collector
from .state import GraphState
from .utils import (
    format_schema_for_prompt,
    clean_query,
    format_results_for_summarization,
    format_results
)
from ..llm.sync import gpt_api_call
from ..prompts import (
    QUERY_GENERATION_PROMPT,
    SUMMARIZATION_PROMPT,
    QUERY_HALLUCINATION_PROMPT,
    SUMMARY_HALLUCINATION_PROMPT
)
from ..mongodb.connection import mongo_connection


def input_validator(state: GraphState) -> GraphState:
    """
    Validates and preprocesses the user's input question.
    
    Responsibilities:
    - Check if question is not empty
    - Clean and normalize the question
    - Detect potential injection attempts
    - Validate question is about data querying
    """
    logger.info("Starting input validation")
    user_question = state.get("user_question", "").strip()
    
    # Check for empty question
    if not user_question:
        logger.warning("Empty question provided")
        return {
            **state,
            "is_valid": False,
            "validation_error": "Question cannot be empty. Please provide a valid question about your data.",
            "final_answer": "Error: No question provided."
        }
    
    # Check minimum length
    if len(user_question) < 5:
        logger.warning(f"Question too short: {len(user_question)} characters")
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
            logger.warning(f"Potentially unsafe pattern detected: {pattern}")
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
        logger.debug("Fetching database schema")
        schema_info = mongo_connection.get_schema_info()
        logger.info(f"Schema retrieved: {len(schema_info.get('collections', []))} collections")
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
        schema_info = {"error": str(e), "collections": []}
    
    logger.info("Input validation successful")
    return {
        **state,
        "validated_question": validated_question,
        "is_valid": True,
        "validation_error": None,
        "schema_info": schema_info
    }


def exploration_node(state: GraphState) -> GraphState:
    """
    Uses LLM to generate a MongoDB query based on the user's question.
    
    Takes the validated question and schema information to create
    an appropriate MongoDB query.
    """
    if not state.get("is_valid", False):
        return state
    
    logger.info("Starting query generation")
    question = state.get("validated_question", "")
    schema_info = state.get("schema_info", {})
    
    # Get current retry count
    retry_count = state.get("query_retry_count", 0)
    
    # Increment retry count if this is a retry (hallucination was detected)
    if state.get("query_hallucination_detected", False):
        retry_count = retry_count + 1
        logger.warning(f"Retrying query generation (attempt {retry_count})")
    
    # Format schema info for the prompt
    schema_text = format_schema_for_prompt(schema_info)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare the prompt using string replacement to avoid curly brace conflicts
    prompt = QUERY_GENERATION_PROMPT.replace("{schema_info}", schema_text)
    prompt = prompt.replace("{current_date}", current_date)
    prompt = prompt.replace("{question}", question)
    
    # Call the LLM API
    try:
        metrics_collector.record_api_call()
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
        
        logger.info(f"Query generated successfully: {generated_query[:100]}...")
        
        return {
            **state,
            "generated_query": generated_query,
            "query_retry_count": retry_count,
            "query_hallucination_detected": False  # Reset for new query
        }
            
    except Exception as e:
        logger.error(f"Error generating query: {e}", exc_info=True)
        return {
            **state,
            "generated_query": None,
            "query_error": str(e),
            "final_answer": f"Error calling LLM API: {str(e)}"
        }


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
        logger.warning(f"Max retries ({max_retries}) reached for query, accepting query")
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
        logger.debug("Checking query for hallucinations")
        # Format schema for prompt
        schema_text = format_schema_for_prompt(schema_info)
        
        # Prepare hallucination detection prompt
        prompt = QUERY_HALLUCINATION_PROMPT.replace("{schema_info}", schema_text)
        prompt = prompt.replace("{question}", question)
        prompt = prompt.replace("{query}", generated_query)
        
        # Call LLM for hallucination detection
        metrics_collector.record_api_call()
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
        
        if hallucination_detected:
            logger.warning(f"Query hallucination detected: {validation_response}")
            metrics_collector.record_hallucination("query")
        else:
            logger.debug("Query validation passed")
        
        return {
            **state,
            "query_hallucination_detected": hallucination_detected
        }
        
    except Exception as e:
        logger.error(f"Error in hallucination detection: {e}", exc_info=True)
        # On error, assume no hallucination to continue flow
        return {
            **state,
            "query_hallucination_detected": False
        }


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
        logger.info("Executing MongoDB query")
        start_time = datetime.now()
        
        # Execute the query
        success, results = mongo_connection.execute_query(generated_query)
        
        query_time = (datetime.now() - start_time).total_seconds()
        metrics_collector.record_query(success, query_time)
        
        if success:
            logger.info(f"Query executed successfully in {query_time:.2f}s, {len(results) if isinstance(results, list) else 1} results")
            # Store raw results - summarization node will format them
            return {
                **state,
                "query_success": True,
                "query_results": results,
                "query_error": None,
                "final_answer": ""  # Will be set by summarization node
            }
        else:
            logger.error(f"Query execution failed: {results}")
            return {
                **state,
                "query_success": False,
                "query_results": None,
                "query_error": results,  # Error message
                "final_answer": f"Query execution failed: {results}"
            }
            
    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        metrics_collector.record_query(False, 0.0)
        return {
            **state,
            "query_success": False,
            "query_results": None,
            "query_error": str(e),
            "final_answer": f"Error executing query: {str(e)}"
        }


def summarization_node(state: GraphState) -> GraphState:
    """
    Summarizes query results into a natural language answer using LLM.
    """
    query_success = state.get("query_success", False)
    query_results = state.get("query_results")
    question = state.get("validated_question", "")
    generated_query = state.get("generated_query", "")
    query_error = state.get("query_error")
    
    # If query failed, return error message without summarization
    if not query_success:
        error_message = query_error or "Query execution failed"
        logger.warning(f"Query failed, skipping summarization: {error_message}")
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
    
    # Get current retry count
    retry_count = state.get("summary_retry_count", 0)
    
    # Increment retry count if this is a retry (hallucination was detected)
    if state.get("summary_hallucination_detected", False):
        retry_count = retry_count + 1
        logger.warning(f"Retrying summary generation (attempt {retry_count})")
    
    # Handle empty list results
    if isinstance(query_results, list) and len(query_results) == 0:
        try:
            # Still try to get a summary from LLM for empty results
            prompt = f"""The user asked: "{question}"

The query executed was: {generated_query}

However, no results were found matching the query criteria.

Provide a helpful, natural language response explaining that no data was found matching their question."""
            
            metrics_collector.record_api_call()
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
            logger.error(f"Error generating empty result summary: {e}")
            return {
                **state,
                "summarized_answer": "No results were found matching your query criteria.",
                "summary_retry_count": retry_count,
                "summary_hallucination_detected": False,
                "final_answer": f"No results found.\n\nQuery: {generated_query}"
            }
    
    try:
        logger.info("Generating summary from query results")
        # Format results for the prompt (limit size to avoid token limits)
        results_text = format_results_for_summarization(query_results)
        
        # Prepare the summarization prompt
        prompt = SUMMARIZATION_PROMPT.replace("{question}", question)
        prompt = prompt.replace("{results}", results_text)
        prompt = prompt.replace("{query}", generated_query)
        
        # Call the LLM API for summarization
        metrics_collector.record_api_call()
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
        
        logger.info("Summary generated successfully")
        
        return {
            **state,
            "summarized_answer": summarized_answer,
            "summary_retry_count": retry_count,
            "summary_hallucination_detected": False,  # Reset for new summary
            "final_answer": final_answer
        }
        
    except Exception as e:
        logger.error(f"Error during summarization: {e}", exc_info=True)
        # If summarization fails, return the original formatted results
        return {
            **state,
            "summarized_answer": None,
            "summary_retry_count": retry_count,
            "summary_hallucination_detected": False,
            "final_answer": state.get("final_answer", f"Error during summarization: {str(e)}")
        }


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
        logger.warning(f"Max retries ({max_retries}) reached for summary, accepting summary")
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
        logger.debug("Checking summary for hallucinations")
        # Format results for prompt
        results_text = format_results_for_summarization(query_results, max_items=10, max_length=2000)
        
        # Prepare hallucination detection prompt
        prompt = SUMMARY_HALLUCINATION_PROMPT.replace("{question}", question)
        prompt = prompt.replace("{results}", results_text)
        prompt = prompt.replace("{summary}", summarized_answer)
        
        # Call LLM for hallucination detection
        metrics_collector.record_api_call()
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
        
        if hallucination_detected:
            logger.warning(f"Summary hallucination detected: {validation_response}")
            metrics_collector.record_hallucination("summary")
        else:
            logger.debug("Summary validation passed")
        
        return {
            **state,
            "summary_hallucination_detected": hallucination_detected
        }
        
    except Exception as e:
        logger.error(f"Error in summary hallucination detection: {e}", exc_info=True)
        # On error, assume no hallucination to continue flow
        return {
            **state,
            "summary_hallucination_detected": False
        }

