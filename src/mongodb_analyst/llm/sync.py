"""
LLM utility functions

Handles OpenAI API calls with rate limiting and logging.
"""
from typing import Dict
from openai import OpenAI
from ..config.logger import logger
from ..config.rate_limiter import api_rate_limiter
from ..config.settings import LLM_API_KEY


def gpt_api_call(data: Dict, use_rate_limit: bool = True) -> str:
    """
    Make API call to GPT model using OpenAI client with rate limiting.
    
    Args:
        data: Request payload with messages, temperature, max_tokens, etc.
        use_rate_limit: Whether to apply rate limiting (default: True)
        
    Returns:
        Response content as string
        
    Raises:
        Exception: If API call fails
    """
    if use_rate_limit:
        api_rate_limiter.wait_if_needed()
    
    try:
        client = OpenAI(api_key=LLM_API_KEY)
        
        # Extract parameters from data dict
        messages = data.get("messages", [])
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens", 1000)
        model = data.get("model", "gpt-3.5-turbo")
        
        logger.debug(f"Making OpenAI API call with model: {model}, temperature: {temperature}")
        
        # Make the API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and return the content
        content = response.choices[0].message.content
        logger.debug(f"OpenAI API call successful, response length: {len(content)}")
        
        return content
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
        raise

