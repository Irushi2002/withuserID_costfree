#####with 12 request per each
# import asyncio
# import time
# import random
# import logging
# from typing import List, Dict, Optional, Tuple
# from collections import deque, defaultdict
# from datetime import datetime, timedelta
# from config import Config

# logger = logging.getLogger(__name__)

# class APIRateLimiter:
#     """
#     Rate limiter that manages multiple Gemini API keys with per-minute limits
#     """
    
#     def __init__(self, api_keys: List[str], rate_limit_per_minute: int = 12):
#         self.api_keys = [key for key in api_keys if key]  # Filter out None values
#         self.rate_limit_per_minute = rate_limit_per_minute
        
#         # Track API call timestamps for each key
#         self.call_history: Dict[str, deque] = defaultdict(lambda: deque())
        
#         # Track total calls for debugging
#         self.total_calls_recorded = 0
        
#         # Lock for thread safety
#         self._lock = asyncio.Lock()
        
#         logger.info(f"Rate limiter initialized with {len(self.api_keys)} API keys")
#         logger.info(f"Rate limit: {rate_limit_per_minute} calls per minute per key")
    
#     async def record_api_call(self, api_key: str = None):
#         """
#         Explicitly record an API call - can be called separately from key selection
#         """
#         async with self._lock:
#             current_time = time.time()
            
#             if not api_key:
#                 # If no specific key provided, pick one randomly
#                 if self.api_keys:
#                     api_key = random.choice(self.api_keys)
#                 else:
#                     logger.warning("No API key available to record call")
#                     return
            
#             self.call_history[api_key].append(current_time)
#             self.total_calls_recorded += 1
            
#             logger.info(f"API call recorded for {api_key[:10]}... "
#                        f"(total recorded: {self.total_calls_recorded}, "
#                        f"key calls: {len(self.call_history[api_key])})")
    
#     async def get_available_api_key(self, record_call: bool = True) -> Optional[str]:
#         """
#         Get an available API key that hasn't exceeded rate limits
        
#         Args:
#             record_call: If True, automatically record the call (default behavior)
#         """
#         async with self._lock:
#             current_time = time.time()
            
#             if not self.api_keys:
#                 logger.error("No API keys available")
#                 return None
            
#             # Check each key for availability
#             available_keys = []
            
#             for api_key in self.api_keys:
#                 # Clean old entries (older than 1 minute)
#                 self._clean_old_entries(api_key, current_time)
                
#                 # Check if this key is under the rate limit
#                 current_calls = len(self.call_history[api_key])
#                 if current_calls < self.rate_limit_per_minute:
#                     available_keys.append((api_key, current_calls))
            
#             if not available_keys:
#                 # All keys are at limit - find the one with the oldest call
#                 oldest_call_key = None
#                 oldest_call_time = current_time
                
#                 for api_key in self.api_keys:
#                     if self.call_history[api_key]:
#                         oldest_in_queue = self.call_history[api_key][0]
#                         if oldest_in_queue < oldest_call_time:
#                             oldest_call_time = oldest_in_queue
#                             oldest_call_key = api_key
                
#                 if oldest_call_key:
#                     wait_time = 60 - (current_time - oldest_call_time)
#                     logger.warning(f"All API keys at limit. Next available in {wait_time:.1f} seconds")
#                     return None
#                 else:
#                     # This shouldn't happen, but fallback
#                     selected_key = random.choice(self.api_keys)
#                     if record_call:
#                         self.call_history[selected_key].append(current_time)
#                         self.total_calls_recorded += 1
#                     return selected_key
            
#             # Select API key with least usage (or random if tied)
#             available_keys.sort(key=lambda x: x[1])  # Sort by usage count
#             selected_key = available_keys[0][0]
            
#             # Record this API call if requested
#             if record_call:
#                 self.call_history[selected_key].append(current_time)
#                 self.total_calls_recorded += 1
                
#                 logger.info(f"API key selected and call recorded: {selected_key[:10]}... "
#                            f"(calls in last minute: {len(self.call_history[selected_key])}, "
#                            f"total recorded: {self.total_calls_recorded})")
#             else:
#                 logger.info(f"API key selected (no call recorded): {selected_key[:10]}...")
            
#             return selected_key
    
#     def _clean_old_entries(self, api_key: str, current_time: float):
#         """Remove entries older than 1 minute"""
#         cutoff_time = current_time - 60  # 60 seconds ago
        
#         initial_count = len(self.call_history[api_key])
#         while self.call_history[api_key] and self.call_history[api_key][0] < cutoff_time:
#             self.call_history[api_key].popleft()
        
#         cleaned_count = initial_count - len(self.call_history[api_key])
#         if cleaned_count > 0:
#             logger.debug(f"Cleaned {cleaned_count} old entries for {api_key[:10]}...")
    
#     async def wait_if_needed(self) -> str:
#         """
#         Wait if necessary and return an available API key
#         Note: This method always records a call since it's meant for actual API usage
#         """
#         max_retries = 10
#         retry_count = 0
        
#         while retry_count < max_retries:
#             # Always record call when using this method
#             api_key = await self.get_available_api_key(record_call=True)
            
#             if api_key:
#                 logger.info(f"API key ready for use: {api_key[:10]}...")
#                 return api_key
            
#             # Wait and retry
#             wait_time = 5  # Wait 5 seconds before retrying
#             logger.info(f"Waiting {wait_time}s for API availability (retry {retry_count + 1}/{max_retries})")
#             await asyncio.sleep(wait_time)
#             retry_count += 1
        
#         # Fallback: Still try to record the call even for fallback
#         if self.api_keys:
#             fallback_key = random.choice(self.api_keys)
            
#             # Record the fallback call too
#             async with self._lock:
#                 current_time = time.time()
#                 self.call_history[fallback_key].append(current_time)
#                 self.total_calls_recorded += 1
#                 logger.warning(f"Using fallback API key with call recorded: {fallback_key[:10]}... "
#                              f"(calls: {len(self.call_history[fallback_key])}, "
#                              f"total: {self.total_calls_recorded})")
            
#             return fallback_key
        
#         raise Exception("No API keys available after maximum retries")
    
#     async def get_rate_limit_status(self) -> Dict[str, Dict]:
#         """
#         Get current rate limit status for all API keys
#         """
#         async with self._lock:
#             current_time = time.time()
#             status = {}
            
#             for api_key in self.api_keys:
#                 self._clean_old_entries(api_key, current_time)
#                 current_calls = len(self.call_history[api_key])
                
#                 # Calculate when the oldest call will expire
#                 next_available_in = 0
#                 if current_calls >= self.rate_limit_per_minute and self.call_history[api_key]:
#                     oldest_call = self.call_history[api_key][0]
#                     next_available_in = max(0, 60 - (current_time - oldest_call))
                
#                 status[f"{api_key[:10]}..."] = {
#                     "calls_last_minute": current_calls,
#                     "rate_limit": self.rate_limit_per_minute,
#                     "available": current_calls < self.rate_limit_per_minute,
#                     "next_available_in_seconds": round(next_available_in, 1)
#                 }
            
#             logger.debug(f"Rate limit status requested (total calls recorded: {self.total_calls_recorded})")
#             return status
    
#     async def get_stats_summary(self) -> Dict:
#         """
#         Get summary statistics for debugging
#         """
#         async with self._lock:
#             current_time = time.time()
            
#             total_active_calls = 0
#             active_keys = 0
#             max_calls_per_key = 0
            
#             for api_key in self.api_keys:
#                 self._clean_old_entries(api_key, current_time)
#                 calls = len(self.call_history[api_key])
#                 total_active_calls += calls
                
#                 if calls > 0:
#                     active_keys += 1
                    
#                 max_calls_per_key = max(max_calls_per_key, calls)
            
#             return {
#                 "total_calls_recorded": self.total_calls_recorded,
#                 "total_active_calls": total_active_calls,
#                 "active_keys": active_keys,
#                 "max_calls_per_key": max_calls_per_key,
#                 "total_keys": len(self.api_keys)
#             }
    
#     async def reset_stats(self):
#         """Reset all rate limiting statistics"""
#         async with self._lock:
#             self.call_history.clear()
#             self.total_calls_recorded = 0
#             logger.info("Rate limiter statistics reset")


# # Global rate limiter instances
# followup_rate_limiter: Optional[APIRateLimiter] = None
# weekly_report_rate_limiter: Optional[APIRateLimiter] = None

# def initialize_rate_limiters():
#     """Initialize the global rate limiters"""
#     global followup_rate_limiter, weekly_report_rate_limiter
    
#     config = Config()
    
#     # Initialize followup rate limiter with 4 API keys
#     if not config.GOOGLE_API_KEYS:
#         raise ValueError("No followup API keys configured")
    
#     followup_rate_limiter = APIRateLimiter(
#         api_keys=config.GOOGLE_API_KEYS,
#         rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
#     )
    
#     # Initialize weekly report rate limiter with dedicated API key
#     if not config.WEEKLY_REPORT_API_KEY:
#         raise ValueError("Weekly report API key not configured")
    
#     weekly_report_rate_limiter = APIRateLimiter(
#         api_keys=[config.WEEKLY_REPORT_API_KEY],
#         rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
#     )
    
#     logger.info("Global rate limiters initialized")
#     logger.info(f"Followup keys: {len(config.GOOGLE_API_KEYS)}, Weekly report keys: 1")

# def get_followup_rate_limiter() -> APIRateLimiter:
#     """Get the followup rate limiter instance"""
#     if followup_rate_limiter is None:
#         raise RuntimeError("Followup rate limiter not initialized. Call initialize_rate_limiters() first")
    
#     return followup_rate_limiter

# def get_weekly_report_rate_limiter() -> APIRateLimiter:
#     """Get the weekly report rate limiter instance"""
#     if weekly_report_rate_limiter is None:
#         raise RuntimeError("Weekly report rate limiter not initialized. Call initialize_rate_limiters() first")
    
#     return weekly_report_rate_limiter


#wih th groq hagging part 2

# import asyncio
# import time
# import random
# import logging
# from typing import List, Dict, Optional, Tuple
# from collections import deque, defaultdict
# from datetime import datetime, timedelta
# from config import Config

# logger = logging.getLogger(__name__)

# class MultiProviderRateLimiter:
#     """
#     Rate limiter that manages multiple AI providers (Gemini, Groq, Hugging Face)
#     """
    
#     def __init__(self, providers_config: List[Dict], rate_limit_per_minute: int = 12):
#         self.providers = [p for p in providers_config if p.get('api_key')]  # Filter out None values
#         self.rate_limit_per_minute = rate_limit_per_minute
        
#         # Track API call timestamps for each provider
#         self.call_history: Dict[str, deque] = defaultdict(lambda: deque())
        
#         # Track total calls for debugging
#         self.total_calls_recorded = 0
        
#         # Lock for thread safety
#         self._lock = asyncio.Lock()
        
#         logger.info(f"Multi-provider rate limiter initialized with {len(self.providers)} providers")
#         for provider in self.providers:
#             logger.info(f"Provider: {provider['name']} ({provider['provider']}) - API Key: {'***' + provider['api_key'][-4:] if provider.get('api_key') else 'None'}")
#         logger.info(f"Rate limit: {rate_limit_per_minute} calls per minute per provider")
    
#     async def record_api_call(self, provider_name: str = None):
#         """
#         Explicitly record an API call
#         """
#         async with self._lock:
#             current_time = time.time()
            
#             if not provider_name:
#                 # If no specific provider given, pick one randomly
#                 if self.providers:
#                     provider_name = random.choice(self.providers)['name']
#                 else:
#                     logger.warning("No providers available to record call")
#                     return
            
#             self.call_history[provider_name].append(current_time)
#             self.total_calls_recorded += 1
            
#             logger.info(f"API call recorded for {provider_name} "
#                        f"(total recorded: {self.total_calls_recorded}, "
#                        f"provider calls: {len(self.call_history[provider_name])})")
    
#     async def get_available_provider(self, record_call: bool = True) -> Optional[Dict]:
#         """
#         Get an available provider that hasn't exceeded rate limits
        
#         Args:
#             record_call: If True, automatically record the call
            
#         Returns:
#             Provider configuration dict or None
#         """
#         async with self._lock:
#             current_time = time.time()
            
#             if not self.providers:
#                 logger.error("No providers available")
#                 return None
            
#             # Debug: Log all providers and their current state
#             logger.debug(f"Checking {len(self.providers)} providers for availability")
            
#             # Check each provider for availability
#             available_providers = []
            
#             for provider in self.providers:
#                 provider_name = provider['name']
                
#                 # Clean old entries (older than 1 minute)
#                 self._clean_old_entries(provider_name, current_time)
                
#                 # Check if this provider is under the rate limit
#                 current_calls = len(self.call_history[provider_name])
#                 logger.debug(f"Provider {provider_name}: {current_calls}/{self.rate_limit_per_minute} calls")
                
#                 if current_calls < self.rate_limit_per_minute:
#                     available_providers.append((provider, current_calls))
#                 else:
#                     # Calculate when this provider will be available again
#                     oldest_call = self.call_history[provider_name][0] if self.call_history[provider_name] else current_time
#                     wait_time = 60 - (current_time - oldest_call)
#                     logger.debug(f"Provider {provider_name} at limit, available in {wait_time:.1f}s")
            
#             if not available_providers:
#                 # All providers are at limit
#                 logger.warning("All AI providers at rate limit")
#                 # Log when each will be available
#                 for provider in self.providers:
#                     provider_name = provider['name']
#                     if self.call_history[provider_name]:
#                         oldest_call = self.call_history[provider_name][0]
#                         wait_time = 60 - (current_time - oldest_call)
#                         logger.info(f"  {provider_name} available in {wait_time:.1f}s")
#                 return None
            
#             # Select provider with least usage (or random if tied)
#             available_providers.sort(key=lambda x: x[1])  # Sort by usage count
            
#             # If multiple providers have same usage, randomize selection
#             min_usage = available_providers[0][1]
#             providers_with_min_usage = [p for p in available_providers if p[1] == min_usage]
            
#             if len(providers_with_min_usage) > 1:
#                 selected_provider_tuple = random.choice(providers_with_min_usage)
#                 logger.debug(f"Multiple providers with {min_usage} calls, randomly selected from {len(providers_with_min_usage)} options")
#             else:
#                 selected_provider_tuple = available_providers[0]
            
#             selected_provider = selected_provider_tuple[0]
            
#             # Record this API call if requested
#             if record_call:
#                 self.call_history[selected_provider['name']].append(current_time)
#                 self.total_calls_recorded += 1
                
#                 logger.info(f"Provider selected and call recorded: {selected_provider['name']} "
#                            f"(calls in last minute: {len(self.call_history[selected_provider['name']])}, "
#                            f"total recorded: {self.total_calls_recorded})")
#             else:
#                 logger.info(f"Provider selected (no call recorded): {selected_provider['name']}")
            
#             return selected_provider
    
#     def _clean_old_entries(self, provider_name: str, current_time: float):
#         """Remove entries older than 1 minute"""
#         cutoff_time = current_time - 60  # 60 seconds ago
        
#         initial_count = len(self.call_history[provider_name])
#         while self.call_history[provider_name] and self.call_history[provider_name][0] < cutoff_time:
#             self.call_history[provider_name].popleft()
        
#         cleaned_count = initial_count - len(self.call_history[provider_name])
#         if cleaned_count > 0:
#             logger.debug(f"Cleaned {cleaned_count} old entries for {provider_name}")
    
#     async def wait_if_needed(self) -> Dict:
#         """
#         Wait if necessary and return an available provider
#         """
#         max_retries = 10
#         retry_count = 0
        
#         while retry_count < max_retries:
#             provider = await self.get_available_provider(record_call=True)
            
#             if provider:
#                 logger.info(f"Provider ready for use: {provider['name']}")
#                 return provider
            
#             # Calculate optimal wait time based on when next provider becomes available
#             async with self._lock:
#                 current_time = time.time()
#                 min_wait_time = float('inf')
                
#                 for p in self.providers:
#                     if self.call_history[p['name']]:
#                         oldest_call = self.call_history[p['name']][0]
#                         wait_time = 60 - (current_time - oldest_call)
#                         if wait_time > 0:
#                             min_wait_time = min(min_wait_time, wait_time)
                
#                 # Wait at least 1 second, but not more than 30 seconds
#                 wait_time = max(1, min(30, min_wait_time + 1)) if min_wait_time != float('inf') else 5
            
#             logger.info(f"Waiting {wait_time:.1f}s for provider availability (retry {retry_count + 1}/{max_retries})")
#             await asyncio.sleep(wait_time)
#             retry_count += 1
        
#         # Fallback: Use first provider even if at limit
#         if self.providers:
#             fallback_provider = self.providers[0]
            
#             async with self._lock:
#                 current_time = time.time()
#                 self.call_history[fallback_provider['name']].append(current_time)
#                 self.total_calls_recorded += 1
#                 logger.warning(f"Using fallback provider with call recorded: {fallback_provider['name']}")
            
#             return fallback_provider
        
#         raise Exception("No AI providers available after maximum retries")
    
#     async def get_rate_limit_status(self) -> Dict[str, Dict]:
#         """
#         Get current rate limit status for all providers
#         """
#         async with self._lock:
#             current_time = time.time()
#             status = {}
            
#             for provider in self.providers:
#                 provider_name = provider['name']
#                 self._clean_old_entries(provider_name, current_time)
#                 current_calls = len(self.call_history[provider_name])
                
#                 # Calculate when the oldest call will expire
#                 next_available_in = 0
#                 if current_calls >= self.rate_limit_per_minute and self.call_history[provider_name]:
#                     oldest_call = self.call_history[provider_name][0]
#                     next_available_in = max(0, 60 - (current_time - oldest_call))
                
#                 status[provider_name] = {
#                     "provider_type": provider["provider"],
#                     "calls_last_minute": current_calls,
#                     "rate_limit": self.rate_limit_per_minute,
#                     "available": current_calls < self.rate_limit_per_minute,
#                     "next_available_in_seconds": round(next_available_in, 1),
#                     "model": provider.get("model", "unknown")
#                 }
            
#             logger.debug(f"Rate limit status requested (total calls recorded: {self.total_calls_recorded})")
#             return status
    
#     async def get_stats_summary(self) -> Dict:
#         """
#         Get summary statistics for debugging
#         """
#         async with self._lock:
#             current_time = time.time()
            
#             total_active_calls = 0
#             active_providers = 0
#             max_calls_per_provider = 0
#             provider_types = {}
            
#             for provider in self.providers:
#                 provider_name = provider['name']
#                 provider_type = provider['provider']
                
#                 self._clean_old_entries(provider_name, current_time)
#                 calls = len(self.call_history[provider_name])
#                 total_active_calls += calls
                
#                 if calls > 0:
#                     active_providers += 1
                    
#                 max_calls_per_provider = max(max_calls_per_provider, calls)
                
#                 if provider_type not in provider_types:
#                     provider_types[provider_type] = 0
#                 provider_types[provider_type] += 1
            
#             return {
#                 "total_calls_recorded": self.total_calls_recorded,
#                 "total_active_calls": total_active_calls,
#                 "active_providers": active_providers,
#                 "max_calls_per_provider": max_calls_per_provider,
#                 "total_providers": len(self.providers),
#                 "total_keys": len(self.providers),  # Added missing field
#                 "provider_types": provider_types
#             }

# # Global rate limiter instances
# followup_rate_limiter: Optional[MultiProviderRateLimiter] = None
# weekly_report_rate_limiter: Optional[MultiProviderRateLimiter] = None

# def initialize_rate_limiters():
#     """Initialize the global rate limiters"""
#     global followup_rate_limiter, weekly_report_rate_limiter
    
#     config = Config()
    
#     # Initialize followup rate limiter with multiple providers
#     providers_config = config.AI_PROVIDERS_CONFIG
#     if not providers_config:
#         raise ValueError("No AI providers configured")
    
#     # Debug: Log provider configuration
#     logger.info("Initializing followup rate limiter with providers:")
#     for i, provider in enumerate(providers_config):
#         api_key_info = f"API Key: {'***' + provider['api_key'][-4:] if provider.get('api_key') else 'None'}"
#         logger.info(f"  {i+1}. {provider.get('name', 'Unknown')} ({provider.get('provider', 'Unknown')}) - {api_key_info}")
    
#     followup_rate_limiter = MultiProviderRateLimiter(
#         providers_config=providers_config,
#         rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
#     )
    
#     # Initialize weekly report rate limiter with Gemini only
#     if not config.WEEKLY_REPORT_API_KEY:
#         raise ValueError("Weekly report API key not configured")
    
#     weekly_providers = [{
#         "provider": "gemini",
#         "api_key": config.WEEKLY_REPORT_API_KEY,
#         "model": "gemini-2.0-flash",
#         "name": "Weekly_Gemini"
#     }]
    
#     weekly_report_rate_limiter = MultiProviderRateLimiter(
#         providers_config=weekly_providers,
#         rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
#     )
    
#     logger.info("Global multi-provider rate limiters initialized")
#     logger.info(f"Followup providers: {len([p for p in providers_config if p.get('api_key')])}, Weekly report providers: 1")

# def get_followup_rate_limiter() -> MultiProviderRateLimiter:
#     """Get the followup rate limiter instance"""
#     if followup_rate_limiter is None:
#         raise RuntimeError("Followup rate limiter not initialized. Call initialize_rate_limiters() first")
    
#     return followup_rate_limiter

# def get_weekly_report_rate_limiter() -> MultiProviderRateLimiter:
#     """Get the weekly report rate limiter instance"""
#     if weekly_report_rate_limiter is None:
#         raise RuntimeError("Weekly report rate limiter not initialized. Call initialize_rate_limiters() first")
    
#     return weekly_report_rate_limiter

#####with enhanced request handling
import asyncio
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class MultiProviderRateLimiter:
    """
    Optimized rate limiter that uses different rate limits per provider
    and ensures proper distribution across all available providers
    """
    
    def __init__(self, providers_config: List[Dict], rate_limit_per_minute: int = 12):
        self.providers = [p for p in providers_config if p.get('api_key')]
        self.rate_limit_per_minute = rate_limit_per_minute  # Keep for backward compatibility
        
        # Provider-specific rate limits optimized for each service
        self.provider_rate_limits = {
            "gemini": 15,      # Gemini can handle more requests
            "groq": 30,        # Groq has very high limits
            "huggingface": 10  # HuggingFace more conservative
        }
        
        # Track API call timestamps for each provider
        self.call_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track total calls for debugging
        self.total_calls_recorded = 0
        
        # Provider selection strategy: weighted round-robin based on capacity
        self.provider_weights = {}
        self.current_provider_index = 0
        self.selection_counter = 0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        self._initialize_provider_weights()
        
        logger.info(f"Optimized multi-provider rate limiter initialized with {len(self.providers)} providers")
        self._log_provider_configuration()
    
    def _initialize_provider_weights(self):
        """Initialize provider weights based on their rate limits"""
        for provider in self.providers:
            provider_type = provider['provider']
            rate_limit = self.provider_rate_limits.get(provider_type, self.rate_limit_per_minute)
            self.provider_weights[provider['name']] = rate_limit
            
        total_weight = sum(self.provider_weights.values())
        logger.info(f"Total system capacity: {total_weight} calls/minute")
    
    def _log_provider_configuration(self):
        """Log detailed provider configuration"""
        for i, provider in enumerate(self.providers):
            provider_type = provider['provider']
            rate_limit = self.provider_rate_limits.get(provider_type, self.rate_limit_per_minute)
            api_key_masked = '***' + provider['api_key'][-4:] if provider.get('api_key') else 'None'
            
            logger.info(f"Provider {i}: {provider['name']} ({provider_type}) - "
                       f"{rate_limit} calls/min - API Key: {api_key_masked}")
    
    def _get_provider_rate_limit(self, provider_type: str) -> int:
        """Get provider-specific rate limit"""
        return self.provider_rate_limits.get(provider_type, self.rate_limit_per_minute)
    
    async def record_api_call(self, provider_name: str = None):
        """
        Explicitly record an API call
        """
        async with self._lock:
            current_time = time.time()
            
            if not provider_name:
                if self.providers:
                    provider_name = random.choice(self.providers)['name']
                else:
                    logger.warning("No providers available to record call")
                    return
            
            self.call_history[provider_name].append(current_time)
            self.total_calls_recorded += 1
            
            # Find provider to get its specific rate limit
            provider_rate_limit = self.rate_limit_per_minute  # Default
            for provider in self.providers:
                if provider['name'] == provider_name:
                    provider_rate_limit = self._get_provider_rate_limit(provider['provider'])
                    break
            
            current_calls = len(self.call_history[provider_name])
            logger.info(f"API call recorded for {provider_name} "
                       f"({current_calls}/{provider_rate_limit} calls, "
                       f"total recorded: {self.total_calls_recorded})")
    
    async def get_available_provider(self, record_call: bool = True) -> Optional[Dict]:
        """
        Get available provider using intelligent weighted distribution
        
        Args:
            record_call: If True, automatically record the call
            
        Returns:
            Provider configuration dict or None
        """
        async with self._lock:
            current_time = time.time()
            
            if not self.providers:
                logger.error("No providers available")
                return None
            
            # Clean old entries for all providers first
            for provider in self.providers:
                self._clean_old_entries(provider['name'], current_time)
            
            # Get available providers with their current utilization
            available_providers = self._get_available_providers_with_metrics(current_time)
            
            if not available_providers:
                logger.warning("All AI providers at rate limit")
                self._log_provider_availability_status(current_time)
                return None
            
            # Select provider using intelligent distribution
            selected_provider = self._select_optimal_provider(available_providers)
            
            # Record this API call if requested
            if record_call:
                provider_name = selected_provider['name']
                self.call_history[provider_name].append(current_time)
                self.total_calls_recorded += 1
                
                provider_rate_limit = self._get_provider_rate_limit(selected_provider['provider'])
                current_calls = len(self.call_history[provider_name])
                utilization = (current_calls / provider_rate_limit) * 100
                
                logger.info(f"Provider selected and call recorded: {provider_name} "
                           f"({current_calls}/{provider_rate_limit} calls, {utilization:.1f}% utilized, "
                           f"total recorded: {self.total_calls_recorded})")
            else:
                logger.info(f"Provider selected (no call recorded): {selected_provider['name']}")
            
            return selected_provider
    
    def _get_available_providers_with_metrics(self, current_time: float) -> List[Tuple[Dict, int, int, float]]:
        """Get available providers with their current metrics"""
        available_providers = []
        
        for provider in self.providers:
            provider_name = provider['name']
            provider_type = provider['provider']
            rate_limit = self._get_provider_rate_limit(provider_type)
            current_calls = len(self.call_history[provider_name])
            
            if current_calls < rate_limit:
                utilization = (current_calls / rate_limit) * 100
                capacity_remaining = rate_limit - current_calls
                
                available_providers.append((provider, current_calls, rate_limit, utilization, capacity_remaining))
                
                logger.debug(f"Available: {provider_name} - {current_calls}/{rate_limit} "
                           f"({utilization:.1f}% used, {capacity_remaining} remaining)")
            else:
                # Calculate when this provider will be available again
                oldest_call = self.call_history[provider_name][0] if self.call_history[provider_name] else current_time
                wait_time = 60 - (current_time - oldest_call)
                logger.debug(f"At limit: {provider_name} - {current_calls}/{rate_limit}, "
                           f"available in {wait_time:.1f}s")
        
        return available_providers
    
    def _select_optimal_provider(self, available_providers: List[Tuple[Dict, int, int, float, int]]) -> Dict:
        """Select the optimal provider using intelligent distribution strategy"""
        
        # Strategy 1: If we have providers with low utilization, prefer them
        low_utilization_threshold = 50.0  # 50% utilization
        low_utilization_providers = [p for p in available_providers if p[3] < low_utilization_threshold]
        
        if low_utilization_providers:
            # Among low utilization providers, prefer higher capacity ones
            low_utilization_providers.sort(key=lambda x: (x[3], -x[4]))  # Sort by utilization asc, then capacity desc
            selected = low_utilization_providers[0]
            logger.debug(f"Selected low-utilization provider: {selected[0]['name']} ({selected[3]:.1f}% used)")
            return selected[0]
        
        # Strategy 2: All providers have high utilization, distribute based on remaining capacity
        available_providers.sort(key=lambda x: -x[4])  # Sort by remaining capacity desc
        selected = available_providers[0]
        logger.debug(f"Selected highest-capacity provider: {selected[0]['name']} ({selected[4]} remaining)")
        return selected[0]
    
    def _log_provider_availability_status(self, current_time: float):
        """Log detailed status when all providers are at limit"""
        logger.info("Provider availability status:")
        for provider in self.providers:
            provider_name = provider['name']
            provider_type = provider['provider']
            rate_limit = self._get_provider_rate_limit(provider_type)
            current_calls = len(self.call_history[provider_name])
            
            if self.call_history[provider_name]:
                oldest_call = self.call_history[provider_name][0]
                wait_time = 60 - (current_time - oldest_call)
                logger.info(f"  {provider_name}: {current_calls}/{rate_limit} calls, "
                           f"available in {wait_time:.1f}s")
            else:
                logger.info(f"  {provider_name}: {current_calls}/{rate_limit} calls")
    
    def _clean_old_entries(self, provider_name: str, current_time: float):
        """Remove entries older than 1 minute"""
        cutoff_time = current_time - 60  # 60 seconds ago
        
        initial_count = len(self.call_history[provider_name])
        while self.call_history[provider_name] and self.call_history[provider_name][0] < cutoff_time:
            self.call_history[provider_name].popleft()
        
        cleaned_count = initial_count - len(self.call_history[provider_name])
        if cleaned_count > 0:
            logger.debug(f"Cleaned {cleaned_count} old entries for {provider_name}")
    
    async def wait_if_needed(self) -> Dict:
        """
        Wait if necessary and return an available provider
        """
        max_retries = 20  # Increased for multi-provider setup
        retry_count = 0
        
        while retry_count < max_retries:
            provider = await self.get_available_provider(record_call=True)
            
            if provider:
                logger.info(f"Provider ready for use: {provider['name']} (retry {retry_count})")
                return provider
            
            # Calculate smart wait time
            wait_time = await self._calculate_smart_wait_time()
            
            logger.info(f"Waiting {wait_time:.1f}s for provider availability (retry {retry_count + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
            retry_count += 1
        
        # Fallback: Use provider that will be available soonest
        fallback_provider = await self._get_fallback_provider()
        return fallback_provider
    
    async def _calculate_smart_wait_time(self) -> float:
        """Calculate optimal wait time based on provider-specific limits"""
        async with self._lock:
            current_time = time.time()
            min_wait_times = []
            
            for provider in self.providers:
                provider_name = provider['name']
                provider_type = provider['provider']
                rate_limit = self._get_provider_rate_limit(provider_type)
                current_calls = len(self.call_history[provider_name])
                
                if current_calls >= rate_limit and self.call_history[provider_name]:
                    oldest_call = self.call_history[provider_name][0]
                    wait_time = 60 - (current_time - oldest_call)
                    if wait_time > 0:
                        min_wait_times.append(wait_time)
                elif current_calls < rate_limit:
                    # This provider is available now
                    return 0.1
            
            if not min_wait_times:
                return 2.0  # Default short wait
            
            # Wait for the provider that becomes available soonest
            min_wait = min(min_wait_times)
            return max(0.5, min(15.0, min_wait + 0.5))  # Add buffer, reasonable bounds
    
    async def _get_fallback_provider(self) -> Dict:
        """Get fallback provider when all are at limit"""
        async with self._lock:
            current_time = time.time()
            
            if not self.providers:
                raise Exception("No providers available after maximum retries")
            
            # Find provider that will be available soonest or has highest capacity
            best_provider = None
            shortest_wait = float('inf')
            highest_capacity = 0
            
            for provider in self.providers:
                provider_name = provider['name']
                provider_type = provider['provider']
                rate_limit = self._get_provider_rate_limit(provider_type)
                
                if rate_limit > highest_capacity:
                    highest_capacity = rate_limit
                    best_provider = provider
                
                if self.call_history[provider_name]:
                    oldest_call = self.call_history[provider_name][0]
                    wait_time = 60 - (current_time - oldest_call)
                    
                    if wait_time < shortest_wait:
                        shortest_wait = wait_time
                        if wait_time <= 0:  # Immediately available
                            best_provider = provider
                            break
            
            if not best_provider:
                best_provider = self.providers[0]  # Ultimate fallback
            
            # Record the fallback call
            self.call_history[best_provider['name']].append(current_time)
            self.total_calls_recorded += 1
            
            provider_rate_limit = self._get_provider_rate_limit(best_provider['provider'])
            current_calls = len(self.call_history[best_provider['name']])
            
            logger.warning(f"Using fallback provider: {best_provider['name']} "
                         f"({current_calls}/{provider_rate_limit} - may exceed limit)")
            
            return best_provider
    
    async def get_rate_limit_status(self) -> Dict[str, Dict]:
        """
        Get current rate limit status for all providers
        """
        try:
            async with self._lock:
                current_time = time.time()
                status = {}
                
                for provider in self.providers:
                    try:
                        provider_name = provider['name']
                        provider_type = provider['provider']
                        rate_limit = self._get_provider_rate_limit(provider_type)
                        
                        self._clean_old_entries(provider_name, current_time)
                        current_calls = len(self.call_history[provider_name])
                        
                        # Calculate utilization and availability
                        utilization = (current_calls / rate_limit) * 100 if rate_limit > 0 else 0
                        available = current_calls < rate_limit
                        
                        # Calculate when provider will be available
                        next_available_in = 0
                        if not available and self.call_history[provider_name]:
                            oldest_call = self.call_history[provider_name][0]
                            next_available_in = max(0, 60 - (current_time - oldest_call))
                        
                        status[provider_name] = {
                            "provider_type": provider_type,
                            "calls_last_minute": current_calls,
                            "rate_limit": rate_limit,
                            "utilization_percentage": round(utilization, 1),
                            "available": available,
                            "next_available_in_seconds": round(next_available_in, 1),
                            "model": provider.get("model", "unknown"),
                            "capacity_remaining": rate_limit - current_calls
                        }
                    except Exception as e:
                        logger.error(f"Error processing provider {provider.get('name', 'unknown')}: {e}")
                        provider_name = provider.get('name', f'unknown_{len(status)}')
                        status[provider_name] = {
                            "provider_type": "unknown",
                            "calls_last_minute": 0,
                            "rate_limit": 8,
                            "utilization_percentage": 0.0,
                            "available": True,
                            "next_available_in_seconds": 0.0,
                            "model": "unknown",
                            "capacity_remaining": 8
                        }
                
                logger.debug(f"Rate limit status requested (total calls recorded: {self.total_calls_recorded})")
                return status
                
        except Exception as e:
            logger.error(f"Critical error in get_rate_limit_status: {e}")
            return {}
    
    async def get_stats_summary(self) -> Dict:
        """
        Get summary statistics for debugging
        """
        try:
            async with self._lock:
                current_time = time.time()
                
                total_active_calls = 0
                total_capacity = 0
                active_providers = 0
                max_calls_per_provider = 0
                provider_types = {}
                provider_utilizations = {}
                
                for provider in self.providers:
                    provider_name = provider['name']
                    provider_type = provider['provider']
                    rate_limit = self._get_provider_rate_limit(provider_type)
                    
                    self._clean_old_entries(provider_name, current_time)
                    calls = len(self.call_history[provider_name])
                    
                    total_active_calls += calls
                    total_capacity += rate_limit
                    
                    if calls > 0:
                        active_providers += 1
                        
                    max_calls_per_provider = max(max_calls_per_provider, calls)
                    
                    # Track utilization per provider
                    utilization = (calls / rate_limit) * 100 if rate_limit > 0 else 0
                    provider_utilizations[provider_name] = round(utilization, 1)
                    
                    if provider_type not in provider_types:
                        provider_types[provider_type] = 0
                    provider_types[provider_type] += 1
                
                overall_utilization = (total_active_calls / total_capacity) * 100 if total_capacity > 0 else 0
                
                stats = {
                    "total_calls_recorded": self.total_calls_recorded,
                    "total_active_calls": total_active_calls,
                    "total_capacity": total_capacity,
                    "overall_utilization_percentage": round(overall_utilization, 1),
                    "active_providers": active_providers,
                    "max_calls_per_provider": max_calls_per_provider,
                    "total_providers": len(self.providers),
                    "total_keys": len(self.providers),  # For backward compatibility
                    "provider_types": provider_types,
                    "provider_utilizations": provider_utilizations,
                    "provider_rate_limits": {
                        provider['name']: self._get_provider_rate_limit(provider['provider'])
                        for provider in self.providers
                    }
                }
                
                logger.debug(f"Stats summary generated: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Error generating stats summary: {e}")
            return {
                "total_calls_recorded": 0,
                "total_active_calls": 0,
                "total_capacity": 0,
                "overall_utilization_percentage": 0.0,
                "active_providers": 0,
                "max_calls_per_provider": 0,
                "total_providers": len(self.providers) if hasattr(self, 'providers') else 0,
                "total_keys": len(self.providers) if hasattr(self, 'providers') else 0,
                "provider_types": {},
                "provider_utilizations": {},
                "provider_rate_limits": {}
            }

# Global rate limiter instances
followup_rate_limiter: Optional[MultiProviderRateLimiter] = None
weekly_report_rate_limiter: Optional[MultiProviderRateLimiter] = None

def initialize_rate_limiters():
    """Initialize the global rate limiters"""
    global followup_rate_limiter, weekly_report_rate_limiter
    
    config = Config()
    
    # Initialize followup rate limiter with multiple providers
    providers_config = config.AI_PROVIDERS_CONFIG
    if not providers_config:
        raise ValueError("No AI providers configured")
    
    logger.info("Initializing OPTIMIZED followup rate limiter with provider-specific limits:")
    
    # Calculate total expected capacity
    total_capacity = 0
    for i, provider in enumerate(providers_config):
        provider_type = provider.get('provider', 'unknown')
        if provider_type == 'gemini':
            capacity = 15
        elif provider_type == 'groq':
            capacity = 30
        elif provider_type == 'huggingface':
            capacity = 10
        else:
            capacity = 12
        
        total_capacity += capacity
        api_key_info = f"***{provider['api_key'][-4:]}" if provider.get('api_key') else 'None'
        logger.info(f"  {i+1}. {provider.get('name', 'Unknown')} ({provider_type}) - "
                   f"{capacity}/min - {api_key_info}")
    
    logger.info(f"Total system capacity: {total_capacity} calls/minute")
    
    followup_rate_limiter = MultiProviderRateLimiter(
        providers_config=providers_config,
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
    )
    
    # Initialize weekly report rate limiter with Gemini only
    if not config.WEEKLY_REPORT_API_KEY:
        raise ValueError("Weekly report API key not configured")
    
    weekly_providers = [{
        "provider": "gemini",
        "api_key": config.WEEKLY_REPORT_API_KEY,
        "model": "gemini-2.0-flash",
        "name": "Weekly_Gemini"
    }]
    
    weekly_report_rate_limiter = MultiProviderRateLimiter(
        providers_config=weekly_providers,
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
    )
    
    logger.info("Global optimized multi-provider rate limiters initialized")
    logger.info(f"Followup providers: {len([p for p in providers_config if p.get('api_key')])}, Weekly report providers: 1")

def get_followup_rate_limiter() -> MultiProviderRateLimiter:
    """Get the followup rate limiter instance"""
    if followup_rate_limiter is None:
        raise RuntimeError("Followup rate limiter not initialized. Call initialize_rate_limiters() first")
    
    return followup_rate_limiter

def get_weekly_report_rate_limiter() -> MultiProviderRateLimiter:
    """Get the weekly report rate limiter instance"""
    if weekly_report_rate_limiter is None:
        raise RuntimeError("Weekly report rate limiter not initialized. Call initialize_rate_limiters() first")
    
    return weekly_report_rate_limiter