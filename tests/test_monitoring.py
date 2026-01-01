"""
Unit tests for monitoring and metrics
"""
import pytest
from monitoring import MetricsCollector, HealthChecker


class TestMetricsCollector:
    """Tests for MetricsCollector class"""
    
    def test_initial_state(self):
        """Test initial metrics state"""
        collector = MetricsCollector()
        metrics = collector.get_metrics()
        assert metrics["total_queries"] == 0
        assert metrics["successful_queries"] == 0
        assert metrics["failed_queries"] == 0
    
    def test_record_successful_query(self):
        """Test recording successful query"""
        collector = MetricsCollector()
        collector.record_query(True, 1.5)
        metrics = collector.get_metrics()
        assert metrics["total_queries"] == 1
        assert metrics["successful_queries"] == 1
        assert metrics["failed_queries"] == 0
        assert metrics["average_query_time"] == 1.5
    
    def test_record_failed_query(self):
        """Test recording failed query"""
        collector = MetricsCollector()
        collector.record_query(False, 0.5)
        metrics = collector.get_metrics()
        assert metrics["total_queries"] == 1
        assert metrics["successful_queries"] == 0
        assert metrics["failed_queries"] == 1
    
    def test_record_hallucination(self):
        """Test recording hallucination"""
        collector = MetricsCollector()
        collector.record_hallucination("query")
        metrics = collector.get_metrics()
        assert metrics["hallucination_detections"] == 1
        assert metrics["query_retries"] == 1
    
    def test_record_api_call(self):
        """Test recording API call"""
        collector = MetricsCollector()
        collector.record_api_call()
        metrics = collector.get_metrics()
        assert metrics["api_calls"] == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        collector = MetricsCollector()
        collector.record_query(True, 1.0)
        collector.record_query(True, 1.0)
        collector.record_query(False, 1.0)
        metrics = collector.get_metrics()
        assert metrics["success_rate"] == pytest.approx(2/3, 0.01)
        assert metrics["failure_rate"] == pytest.approx(1/3, 0.01)
    
    def test_reset(self):
        """Test resetting metrics"""
        collector = MetricsCollector()
        collector.record_query(True, 1.0)
        collector.reset()
        metrics = collector.get_metrics()
        assert metrics["total_queries"] == 0


class TestHealthChecker:
    """Tests for HealthChecker class"""
    
    def test_get_health_status_structure(self):
        """Test health status structure"""
        health = HealthChecker.get_health_status()
        assert "status" in health
        assert "mongodb" in health
        assert "openai" in health
        assert "timestamp" in health

