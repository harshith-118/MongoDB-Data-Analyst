"""
Configuration settings for MongoDB Data Analyst

All settings are loaded from environment variables.
Create a .env file in the project root with your settings.
See .env.example for the required variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# LLM API Configuration
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Validation
def validate_config():
    """Validate that all required environment variables are set"""
    missing = []
    
    if not MONGODB_URI:
        missing.append("MONGODB_URI")
    if not MONGODB_DATABASE:
        missing.append("MONGODB_DATABASE")
    if not LLM_API_URL:
        missing.append("LLM_API_URL")
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please create a .env file with these variables. See .env.example for reference."
        )

