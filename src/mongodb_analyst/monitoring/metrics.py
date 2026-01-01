"""
Monitoring and observability utilities

Provides metrics, health checks, and performance monitoring.
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime
from ..config.logger import logger


class MetricsCollector:
    """Collects and tracks metrics for the application"""
    
    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "hallucination_detections": 0,
            "query_retries": 0,
            "summary_retries": 0,
            "api_calls": 0,
            "average_query_time": 0.0,
            "total_query_time": 0.0
        }
        self.query_times = []
    
    def record_query(self, success: bool, query_time: float):
        """Record a query execution"""
        self.metrics["total_queries"] += 1
        if success:
            self.metrics["successful_queries"] += 1
        else:
            self.metrics["failed_queries"] += 1
        
        self.query_times.append(query_time)
        self.metrics["total_query_time"] += query_time
        self.metrics["average_query_time"] = (
            self.metrics["total_query_time"] / self.metrics["total_queries"]
        )
    
    def record_hallucination(self, query_type: str = "query"):
        """Record a hallucination detection"""
        self.metrics["hallucination_detections"] += 1
        if query_type == "query":
            self.metrics["query_retries"] += 1
        else:
            self.metrics["summary_retries"] += 1
    
    def record_api_call(self):
        """Record an API call"""
        self.metrics["api_calls"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_queries"] / self.metrics["total_queries"]
                if self.metrics["total_queries"] > 0 else 0.0
            ),
            "failure_rate": (
                self.metrics["failed_queries"] / self.metrics["total_queries"]
                if self.metrics["total_queries"] > 0 else 0.0
            )
        }
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "hallucination_detections": 0,
            "query_retries": 0,
            "summary_retries": 0,
            "api_calls": 0,
            "average_query_time": 0.0,
            "total_query_time": 0.0
        }
        self.query_times = []


class HealthChecker:
    """Health check utilities"""
    
    @staticmethod
    def check_mongodb_connection() -> Dict[str, Any]:
        """Check MongoDB connection health"""
        try:
            from ..mongodb.connection import mongo_connection
            db = mongo_connection.get_database()
            # Try to list collections as a health check
            collections = db.list_collection_names()
            return {
                "status": "healthy",
                "database": db.name,
                "collections_count": len(collections),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @staticmethod
    def check_openai_connection() -> Dict[str, Any]:
        """Check OpenAI API connection health"""
        try:
            from ..config.settings import LLM_API_KEY
            if not LLM_API_KEY:
                return {
                    "status": "unhealthy",
                    "error": "LLM_API_KEY not configured",
                    "timestamp": datetime.now().isoformat()
                }
            return {
                "status": "healthy",
                "api_key_configured": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """Get overall health status"""
        mongodb_health = HealthChecker.check_mongodb_connection()
        openai_health = HealthChecker.check_openai_connection()
        
        overall_status = "healthy" if (
            mongodb_health["status"] == "healthy" and
            openai_health["status"] == "healthy"
        ) else "degraded"
        
        return {
            "status": overall_status,
            "mongodb": mongodb_health,
            "openai": openai_health,
            "timestamp": datetime.now().isoformat()
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()

