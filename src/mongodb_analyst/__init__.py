"""
MongoDB Data Analyst Package

A LangGraph-powered natural language interface for querying MongoDB databases.
"""

__version__ = "2.0.0"

from .graph.graph import ask_question, create_app, build_graph
from .mongodb.connection import mongo_connection
from .config.settings import (
    MONGODB_URI,
    MONGODB_DATABASE,
    LLM_API_KEY,
    validate_config
)
from .monitoring.metrics import metrics_collector, HealthChecker

__all__ = [
    "ask_question",
    "create_app",
    "build_graph",
    "mongo_connection",
    "MONGODB_URI",
    "MONGODB_DATABASE",
    "LLM_API_KEY",
    "validate_config",
    "metrics_collector",
    "HealthChecker",
]

