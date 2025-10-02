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
    Optimized rate limiter with TRUE round-robin distribution
    """
    
    def __init__(self, providers_config: List[Dict], rate_limit_per_minute: int = 12):
        self.providers = [p for p in providers_config if p.get('api_key')]
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Provider-specific rate limits
        self.provider_rate_limits = {
            "gemini": 15,
            "groq": 30,
            "huggingface": 10
        }
        
        # Track API call timestamps for each provider
        self.call_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track total calls
        self.total_calls_recorded = 0
        
        # FIXED: True round-robin counter
        self.round_robin_index = 0
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        self._initialize_provider_weights()
        
        logger.info(f"Rate limiter initialized with {len(self.providers)} providers")
        self._log_provider_configuration()
    
    def _initialize_provider_weights(self):
        """Initialize provider weights based on their rate limits"""
        for provider in self.providers:
            provider_type = provider['provider']
            rate_limit = self.provider_rate_limits.get(provider_type, self.rate_limit_per_minute)
            logger.info(f"{provider['name']} capacity: {rate_limit}/min")
    
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
        """Record an API call"""
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
            
            provider_rate_limit = self.rate_limit_per_minute
            for provider in self.providers:
                if provider['name'] == provider_name:
                    provider_rate_limit = self._get_provider_rate_limit(provider['provider'])
                    break
            
            current_calls = len(self.call_history[provider_name])
            logger.info(f"API call recorded for {provider_name} "
                       f"({current_calls}/{provider_rate_limit} calls)")
    
    async def get_available_provider(self, record_call: bool = True) -> Optional[Dict]:
        """
        FIXED: Get available provider using TRUE round-robin distribution
        """
        async with self._lock:
            current_time = time.time()
            
            if not self.providers:
                logger.error("No providers available")
                return None
            
            # Clean old entries for all providers
            for provider in self.providers:
                self._clean_old_entries(provider['name'], current_time)
            
            # Get available providers
            available_providers = []
            for provider in self.providers:
                provider_name = provider['name']
                provider_type = provider['provider']
                rate_limit = self._get_provider_rate_limit(provider_type)
                current_calls = len(self.call_history[provider_name])
                
                if current_calls < rate_limit:
                    utilization = (current_calls / rate_limit) * 100
                    available_providers.append({
                        'provider': provider,
                        'calls': current_calls,
                        'limit': rate_limit,
                        'utilization': utilization,
                        'remaining': rate_limit - current_calls
                    })
            
            if not available_providers:
                logger.warning("All AI providers at rate limit")
                return None
            
            # FIXED: Use true round-robin with skip-if-full logic
            attempts = 0
            max_attempts = len(self.providers) * 2  # Try all providers twice
            
            while attempts < max_attempts:
                # Get current provider in round-robin
                current_index = self.round_robin_index % len(self.providers)
                candidate_provider = self.providers[current_index]
                
                # Move to next provider for next call
                self.round_robin_index = (self.round_robin_index + 1) % len(self.providers)
                attempts += 1
                
                # Check if this provider is available
                provider_name = candidate_provider['name']
                provider_type = candidate_provider['provider']
                rate_limit = self._get_provider_rate_limit(provider_type)
                current_calls = len(self.call_history[provider_name])
                
                if current_calls < rate_limit:
                    # This provider is available!
                    selected = candidate_provider
                    
                    # Record the call if requested
                    if record_call:
                        self.call_history[provider_name].append(current_time)
                        self.total_calls_recorded += 1
                        
                        utilization = ((current_calls + 1) / rate_limit) * 100
                        
                        logger.info(f"✅ Provider selected (round-robin): {provider_name} "
                                   f"({current_calls + 1}/{rate_limit} calls, {utilization:.1f}% utilized)")
                    
                    return selected
                else:
                    logger.debug(f"⏭️ Skipping {provider_name} (at limit: {current_calls}/{rate_limit})")
            
            # All providers exhausted
            logger.warning("All providers at limit after round-robin attempts")
            return None
    
    def _clean_old_entries(self, provider_name: str, current_time: float):
        """Remove entries older than 1 minute"""
        cutoff_time = current_time - 60
        
        initial_count = len(self.call_history[provider_name])
        while self.call_history[provider_name] and self.call_history[provider_name][0] < cutoff_time:
            self.call_history[provider_name].popleft()
        
        cleaned_count = initial_count - len(self.call_history[provider_name])
        if cleaned_count > 0:
            logger.debug(f"Cleaned {cleaned_count} old entries for {provider_name}")
    
    async def wait_if_needed(self) -> Dict:
        """Wait if necessary and return an available provider"""
        max_retries = 20
        retry_count = 0
        
        while retry_count < max_retries:
            provider = await self.get_available_provider(record_call=True)
            
            if provider:
                logger.info(f"Provider ready: {provider['name']}")
                return provider
            
            wait_time = await self._calculate_smart_wait_time()
            
            logger.info(f"Waiting {wait_time:.1f}s for availability (retry {retry_count + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
            retry_count += 1
        
        # Fallback
        fallback_provider = await self._get_fallback_provider()
        return fallback_provider
    
    async def _calculate_smart_wait_time(self) -> float:
        """Calculate optimal wait time"""
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
                    return 0.1
            
            if not min_wait_times:
                return 2.0
            
            min_wait = min(min_wait_times)
            return max(0.5, min(15.0, min_wait + 0.5))
    
    async def _get_fallback_provider(self) -> Dict:
        """Get fallback provider"""
        async with self._lock:
            current_time = time.time()
            
            if not self.providers:
                raise Exception("No providers available")
            
            best_provider = self.providers[0]
            
            self.call_history[best_provider['name']].append(current_time)
            self.total_calls_recorded += 1
            
            logger.warning(f"Using fallback provider: {best_provider['name']}")
            
            return best_provider
    
    async def get_rate_limit_status(self) -> Dict[str, Dict]:
        """Get current rate limit status for all providers"""
        try:
            async with self._lock:
                current_time = time.time()
                status = {}
                
                for provider in self.providers:
                    provider_name = provider['name']
                    provider_type = provider['provider']
                    rate_limit = self._get_provider_rate_limit(provider_type)
                    
                    self._clean_old_entries(provider_name, current_time)
                    current_calls = len(self.call_history[provider_name])
                    
                    utilization = (current_calls / rate_limit) * 100 if rate_limit > 0 else 0
                    available = current_calls < rate_limit
                    
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
                
                return status
                
        except Exception as e:
            logger.error(f"Error in get_rate_limit_status: {e}")
            return {}
    
    async def get_stats_summary(self) -> Dict:
        """Get summary statistics"""
        try:
            async with self._lock:
                current_time = time.time()
                
                total_active_calls = 0
                total_capacity = 0
                provider_utilizations = {}
                
                for provider in self.providers:
                    provider_name = provider['name']
                    provider_type = provider['provider']
                    rate_limit = self._get_provider_rate_limit(provider_type)
                    
                    self._clean_old_entries(provider_name, current_time)
                    calls = len(self.call_history[provider_name])
                    
                    total_active_calls += calls
                    total_capacity += rate_limit
                    
                    utilization = (calls / rate_limit) * 100 if rate_limit > 0 else 0
                    provider_utilizations[provider_name] = round(utilization, 1)
                
                overall_utilization = (total_active_calls / total_capacity) * 100 if total_capacity > 0 else 0
                
                return {
                    "total_calls_recorded": self.total_calls_recorded,
                    "total_active_calls": total_active_calls,
                    "total_capacity": total_capacity,
                    "overall_utilization_percentage": round(overall_utilization, 1),
                    "total_providers": len(self.providers),
                    "total_keys": len(self.providers),
                    "provider_utilizations": provider_utilizations,
                    "round_robin_position": self.round_robin_index % len(self.providers) if self.providers else 0
                }
                
        except Exception as e:
            logger.error(f"Error in get_stats_summary: {e}")
            return {
                "total_calls_recorded": 0,
                "total_active_calls": 0,
                "total_capacity": 0,
                "overall_utilization_percentage": 0.0,
                "total_providers": 0,
                "total_keys": 0,
                "provider_utilizations": {},
                "round_robin_position": 0
            }

# Global instances
followup_rate_limiter: Optional[MultiProviderRateLimiter] = None
weekly_report_rate_limiter: Optional[MultiProviderRateLimiter] = None

def initialize_rate_limiters():
    """Initialize the global rate limiters"""
    global followup_rate_limiter, weekly_report_rate_limiter
    
    config = Config()
    
    providers_config = config.AI_PROVIDERS_CONFIG
    if not providers_config:
        raise ValueError("No AI providers configured")
    
    logger.info("Initializing followup rate limiter with TRUE round-robin:")
    
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
        
        logger.info(f"  {i+1}. {provider.get('name')} ({provider_type}) - {capacity}/min")
    
    followup_rate_limiter = MultiProviderRateLimiter(
        providers_config=providers_config,
        rate_limit_per_minute=config.RATE_LIMIT_PER_MINUTE
    )
    
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
    
    logger.info("✅ Rate limiters initialized with round-robin distribution")

def get_followup_rate_limiter() -> MultiProviderRateLimiter:
    if followup_rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized")
    return followup_rate_limiter

def get_weekly_report_rate_limiter() -> MultiProviderRateLimiter:
    if weekly_report_rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized")
    return weekly_report_rate_limiter