"""
Graph utility functions

Helper functions for query formatting, cleaning, and result processing.
"""
import json
import re
from typing import Any, Dict


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

