"""
Unit tests for graph utility functions
"""
import pytest
from src.mongodb_analyst.graph.utils import (
    format_schema_for_prompt,
    clean_query,
    format_results_for_summarization,
    format_results
)


class TestFormatSchemaForPrompt:
    """Tests for format_schema_for_prompt function"""
    
    def test_empty_schema(self):
        """Test with empty schema"""
        result = format_schema_for_prompt({})
        assert "not available" in result
    
    def test_schema_with_error(self):
        """Test with schema containing error"""
        schema = {"error": "Connection failed"}
        result = format_schema_for_prompt(schema)
        assert "not available" in result
    
    def test_valid_schema(self):
        """Test with valid schema"""
        schema = {
            "database_name": "test_db",
            "collections": [
                {
                    "name": "users",
                    "document_count": 100,
                    "sample_fields": [
                        {"field": "name", "type": "str"},
                        {"field": "age", "type": "int"}
                    ],
                    "indexes": [{"name": "idx_name"}]
                }
            ]
        }
        result = format_schema_for_prompt(schema)
        assert "test_db" in result
        assert "users" in result
        assert "name" in result
        assert "age" in result


class TestCleanQuery:
    """Tests for clean_query function"""
    
    def test_query_with_markdown(self):
        """Test cleaning markdown code blocks"""
        query = "```javascript\ndb.users.find({})\n```"
        result = clean_query(query)
        assert "```" not in result
        assert "db.users.find({})" in result
    
    def test_query_with_explanation(self):
        """Test removing explanation text"""
        query = "Here's the query:\ndb.users.find({})\nThis finds all users"
        result = clean_query(query)
        assert "db.users.find({})" in result
    
    def test_simple_query(self):
        """Test simple query without cleaning needed"""
        query = "db.users.find({})"
        result = clean_query(query)
        assert result == "db.users.find({})"


class TestFormatResultsForSummarization:
    """Tests for format_results_for_summarization function"""
    
    def test_empty_results(self):
        """Test with empty list"""
        result = format_results_for_summarization([])
        assert "No results found" in result
    
    def test_list_results(self):
        """Test with list of results"""
        results = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        formatted = format_results_for_summarization(results, max_items=2)
        assert "2 result(s)" in formatted
        assert "John" in formatted
        assert "Jane" in formatted
    
    def test_scalar_result(self):
        """Test with scalar result"""
        result = format_results_for_summarization(42)
        assert "Result: 42" in result
    
    def test_truncation(self):
        """Test result truncation"""
        large_doc = {"data": "x" * 1000}
        results = [large_doc]
        formatted = format_results_for_summarization(results, max_items=1, max_length=100)
        assert "truncated" in formatted.lower()


class TestFormatResults:
    """Tests for format_results function"""
    
    def test_empty_list(self):
        """Test with empty list"""
        result = format_results([], "test question", "db.test.find({})")
        assert "No documents found" in result
    
    def test_list_with_items(self):
        """Test with list containing items"""
        results = [{"id": 1, "name": "Test"}]
        formatted = format_results(results, "test question", "db.test.find({})")
        assert "1 document(s)" in formatted
        assert "test question" in formatted
        assert "db.test.find({})" in formatted
    
    def test_scalar_result(self):
        """Test with scalar result"""
        result = format_results(42, "count", "db.test.count()")
        assert "Result: 42" in result

