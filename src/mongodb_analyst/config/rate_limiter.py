"""
Rate limiting utilities for API calls

Provides rate limiting for OpenAI API calls to prevent exceeding rate limits.
"""
import os
import time
from functools import wraps
from typing import Callable, Any
from ratelimit import limits, sleep_and_retry
from dotenv import load_dotenv
from .logger import logger

load_dotenv()

# Rate limits (adjust based on your OpenAI plan)
# Default: 60 requests per minute for free tier
# Pro tier: 500 requests per minute
RATE_LIMIT_CALLS = int(os.getenv("RATE_LIMIT_CALLS", "60"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds


@sleep_and_retry
@limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
def rate_limited_call(func: Callable) -> Callable:
    """
    Decorator to rate limit function calls.
    
    Usage:
        @rate_limited_call
        def my_api_call():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Rate limited call failed: {e}")
            raise
    return wrapper


class RateLimiter:
    """
    Simple token bucket rate limiter for API calls.
    """
    
    def __init__(self, max_calls: int = RATE_LIMIT_CALLS, period: int = RATE_LIMIT_PERIOD):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = False
    
    def acquire(self) -> bool:
        """
        Try to acquire a permit for making a call.
        
        Returns:
            True if permit acquired, False otherwise
        """
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        # Calculate wait time
        oldest_call = min(self.calls)
        wait_time = self.period - (now - oldest_call)
        
        if wait_time > 0:
            logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            self.calls.append(time.time())
            return True
        
        return False
    
    def wait_if_needed(self):
        """Wait if rate limit is reached."""
        if not self.acquire():
            raise Exception("Rate limit exceeded and could not acquire permit")


# Global rate limiter instance
api_rate_limiter = RateLimiter()

