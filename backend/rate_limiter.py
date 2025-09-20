import asyncio
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class APIRateLimiter:
    """
    Rate limiter that manages multiple Gemini API keys with per-minute limits
    """
    
    def __init__(self, api_keys: List[str], rate_limit_per_minute: int = 12):
        self.api_keys = [key for key in api_keys if key]  # Filter out None values
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Track API call timestamps for each key
        self.call_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track total calls for debugging
        self.total_calls_recorded = 0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"Rate limiter initialized with {len(self.api_keys)} API keys")
        logger.info(f"Rate limit: {rate_limit_per_minute} calls per minute per key")
    
    async def record_api_call(self, api_key: str = None):
        """
        Explicitly record an API call - can be called separately from key selection
        """
        async with self._lock:
            current_time = time.time()
            
            if not api_key:
                # If no specific key provided, pick one randomly
                if self.api_keys:
                    api_key = random.choice(self.api_keys)
                else:
                    logger.warning("No API key available to record call")
                    return
            
            self.call_history[api_key].append(current_time)
            self.total_calls_recorded += 1
            
            logger.info(f"API call recorded for {api_key[:10]}... "
                       f"(total recorded: {self.total_calls_recorded}, "
                       f"key calls: {len(self.call_history[api_key])})")
    
    async def get_available_api_key(self, record_call: bool = True) -> Optional[str]:
        """
        Get an available API key that hasn't exceeded rate limits
        
        Args:
            record_call: If True, automatically record the call (default behavior)
        """
        async with self._lock:
            current_time = time.time()
            
            if not self.api_keys:
                logger.error("No API keys available")
                return None
            
            # Check each key for availability
            available_keys = []
            
            for api_key in self.api_keys:
                # Clean old entries (older than 1 minute)
                self._clean_old_entries(api_key, current_time)
                
                # Check if this key is under the rate limit
                current_calls = len(self.call_history[api_key])
                if current_calls < self.rate_limit_per_minute:
                    available_keys.append((api_key, current_calls))
            
            if not available_keys:
                # All keys are at limit - find the one with the oldest call
                oldest_call_key = None
                oldest_call_time = current_time
                
                for api_key in self.api_keys:
                    if self.call_history[api_key]:
                        oldest_in_queue = self.call_history[api_key][0]
                        if oldest_in_queue < oldest_call_time:
                            oldest_call_time = oldest_in_queue
                            oldest_call_key = api_key
                
                if oldest_call_key:
                    wait_time = 60 - (current_time - oldest_call_time)
                    logger.warning(f"All API keys at limit. Next available in {wait_time:.1f} seconds")
                    return None
                else:
                    # This shouldn't happen, but fallback
                    selected_key = random.choice(self.api_keys)
                    if record_call:
                        self.call_history[selected_key].append(current_time)
                        self.total_calls_recorded += 1
                    return selected_key
            
            # Select API key with least usage (or random if tied)
            available_keys.sort(key=lambda x: x[1])  # Sort by usage count
            selected_key = available_keys[0][0]
            
            # Record this API call if requested
            if record_call:
                self.call_history[selected_key].append(current_time)
                self.total_calls_recorded += 1
                
                logger.info(f"API key selected and call recorded: {selected_key[:10]}... "
                           f"(calls in last minute: {len(self.call_history[selected_key])}, "
                           f"total recorded: {self.total_calls_recorded})")
            else:
                logger.info(f"API key selected (no call recorded): {selected_key[:10]}...")
            
            return selected_key
    
    def _clean_old_entries(self, api_key: str, current_time: float):
        """Remove entries older than 1 minute"""
        cutoff_time = current_time - 60  # 60 seconds ago
        
        initial_count = len(self.call_history[api_key])
        while self.call_history[api_key] and self.call_history[api_key][0] < cutoff_time:
            self.call_history[api_key].popleft()
        
        cleaned_count = initial_count - len(self.call_history[api_key])
        if cleaned_count > 0:
            logger.debug(f"Cleaned {cleaned_count} old entries for {api_key[:10]}...")
    
    async def wait_if_needed(self) -> str:
        """
        Wait if necessary and return an available API key
        Note: This method always records a call since it's meant for actual API usage
        """
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            # Always record call when using this method
            api_key = await self.get_available_api_key(record_call=True)
            
            if api_key:
                logger.info(f"API key ready for use: {api_key[:10]}...")
                return api_key
            
            # Wait and retry
            wait_time = 5  # Wait 5 seconds before retrying
            logger.info(f"Waiting {wait_time}s for API availability (retry {retry_count + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
            retry_count += 1
        
        # Fallback: Still try to record the call even for fallback
        if self.api_keys:
            fallback_key = random.choice(self.api_keys)
            
            # Record the fallback call too
            async with self._lock:
                current_time = time.time()
                self.call_history[fallback_key].append(current_time)
                self.total_calls_recorded += 1
                logger.warning(f"Using fallback API key with call recorded: {fallback_key[:10]}... "
                             f"(calls: {len(self.call_history[fallback_key])}, "
                             f"total: {self.total_calls_recorded})")
            
            return fallback_key
        
        raise Exception("No API keys available after maximum retries")
    
    async def get_rate_limit_status(self) -> Dict[str, Dict]:
        """
        Get current rate limit status for all API keys
        """
        async with self._lock:
            current_time = time.time()
            status = {}
            
            for api_key in self.api_keys:
                self._clean_old_entries(api_key, current_time)
                current_calls = len(self.call_history[api_key])
                
                # Calculate when the oldest call will expire
                next_available_in = 0
                if current_calls >= self.rate_limit_per_minute and self.call_history[api_key]:
                    oldest_call = self.call_history[api_key][0]
                    next_available_in = max(0, 60 - (current_time - oldest_call))
                
                status[f"{api_key[:10]}..."] = {
                    "calls_last_minute": current_calls,
                    "rate_limit": self.rate_limit_per_minute,
                    "available": current_calls < self.rate_limit_per_minute,
                    "next_available_in_seconds": round(next_available_in, 1)
                }
            
            logger.debug(f"Rate limit status requested (total calls recorded: {self.total_calls_recorded})")
            return status
    
    async def get_stats_summary(self) -> Dict:
        """
        Get summary statistics for debugging
        """
        async with self._lock:
            current_time = time.time()
            
            total_active_calls = 0
            active_keys = 0
            max_calls_per_key = 0
            
            for api_key in self.api_keys:
                self._clean_old_entries(api_key, current_time)
                calls = len(self.call_history[api_key])
                total_active_calls += calls
                
                if calls > 0:
                    active_keys += 1
                    
                max_calls_per_key = max(max_calls_per_key, calls)
            
            return {
                "total_calls_recorded": self.total_calls_recorded,
                "total_active_calls": total_active_calls,
                "active_keys": active_keys,
                "max_calls_per_key": max_calls_per_key,
                "total_keys": len(self.api_keys)
            }
    
    async def reset_stats(self):
        """Reset all rate limiting statistics"""
        async with self._lock:
            self.call_history.clear()
            self.total_calls_recorded = 0
            logger.info("Rate limiter statistics reset")


# Global rate limiter instances
followup_rate_limiter: Optional[APIRateLimiter] = None
weekly_report_rate_limiter: Optional[APIRateLimiter] = None

def initialize_rate_limiters():
    """Initialize the global rate limiters"""
    global followup_rate_limiter, weekly_report_rate_limiter
    
    config = Config()
    
    # Initialize followup rate limiter with 4 API keys
    if not config.GOOGLE_API_KEYS:
        raise ValueError("No followup API keys configured")
    
    followup_rate_limiter = APIRateLimiter(
        api_keys=config.GOOGLE_API_KEYS,
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
    )
    
    # Initialize weekly report rate limiter with dedicated API key
    if not config.WEEKLY_REPORT_API_KEY:
        raise ValueError("Weekly report API key not configured")
    
    weekly_report_rate_limiter = APIRateLimiter(
        api_keys=[config.WEEKLY_REPORT_API_KEY],
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
    )
    
    logger.info("Global rate limiters initialized")
    logger.info(f"Followup keys: {len(config.GOOGLE_API_KEYS)}, Weekly report keys: 1")

def get_followup_rate_limiter() -> APIRateLimiter:
    """Get the followup rate limiter instance"""
    if followup_rate_limiter is None:
        raise RuntimeError("Followup rate limiter not initialized. Call initialize_rate_limiters() first")
    
    return followup_rate_limiter

def get_weekly_report_rate_limiter() -> APIRateLimiter:
    """Get the weekly report rate limiter instance"""
    if weekly_report_rate_limiter is None:
        raise RuntimeError("Weekly report rate limiter not initialized. Call initialize_rate_limiters() first")
    
    return weekly_report_rate_limiter