"""
Async LLM utility functions

Handles async OpenAI API calls with rate limiting and logging.
"""
import asyncio
from typing import Dict
from openai import AsyncOpenAI
from ..config.logger import logger
from ..config.rate_limiter import api_rate_limiter
from ..config.settings import LLM_API_KEY


async def gpt_api_call_async(data: Dict, use_rate_limit: bool = True) -> str:
    """
    Make async API call to GPT model using OpenAI client with rate limiting.
    
    Args:
        data: Request payload with messages, temperature, max_tokens, etc.
        use_rate_limit: Whether to apply rate limiting (default: True)
        
    Returns:
        Response content as string
        
    Raises:
        Exception: If API call fails
    """
    if use_rate_limit:
        # For async, we need to run rate limiter in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, api_rate_limiter.wait_if_needed)
    
    try:
        client = AsyncOpenAI(api_key=LLM_API_KEY)
        
        # Extract parameters from data dict
        messages = data.get("messages", [])
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens", 1000)
        model = data.get("model", "gpt-3.5-turbo")
        
        logger.debug(f"Making async OpenAI API call with model: {model}, temperature: {temperature}")
        
        # Make the async API call
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and return the content
        content = response.choices[0].message.content
        logger.debug(f"Async OpenAI API call successful, response length: {len(content)}")
        
        return content
        
    except Exception as e:
        logger.error(f"Async OpenAI API call failed: {str(e)}", exc_info=True)
        raise


async def batch_gpt_api_calls(requests: list[Dict], max_concurrent: int = 3) -> list[str]:
    """
    Make multiple async API calls with concurrency control.
    
    Args:
        requests: List of request payloads
        max_concurrent: Maximum concurrent requests
        
    Returns:
        List of response contents
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_call(data: Dict) -> str:
        async with semaphore:
            return await gpt_api_call_async(data)
    
    tasks = [bounded_call(data) for data in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Request {i} failed: {result}")
            processed_results.append("")
        else:
            processed_results.append(result)
    
    return processed_results

