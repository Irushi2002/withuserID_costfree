#!/usr/bin/env python3/test file
"""
AI Provider Switching Test - Real-time tracking with proper rate limiter integration

This test specifically monitors:
1. Which AI provider handles each request in real-time
2. How the system switches between providers as rate limits are hit
3. Exact timing of provider switches and fallbacks
4. Rate limiter behavior under rapid requests
5. Proper integration with the MultiProviderRateLimiter
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
import json

@dataclass
class RequestResult:
    """Result of a single request with detailed provider tracking"""
    request_id: int
    timestamp: float
    user_id: str
    quality_score: float
    needs_followup: bool
    provider_used: str
    fallback_used: bool
    success: bool
    response_time: float
    error: str = ""
    questions_sample: str = ""

class ProviderSwitchingTracker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[RequestResult] = []
        
        # Low quality work update to ensure AI generation
        self.base_work_update = {
            "stack": "Backend Development",
            "task": "Fixed some API bugs today",
            "progress": "Made minimal progress",  # Ensure low quality
            "blockers": "Need help",  # Ensure low quality
            "status": "working"
        }

    async def run_switching_test(self, requests_count: int = 20, time_window: int = 60) -> Dict[str, Any]:
        """Run rapid requests to track provider switching"""
        
        print(f"AI Provider Switching Test")
        print(f"Sending {requests_count} requests in {time_window} seconds")
        print("=" * 60)
        print(f"{'ID':<3} {'Time':<8} {'Provider':<18} {'Fallback':<8} {'Score':<6} {'Sample Question'}")
        print("-" * 100)
        
        start_time = time.time()
        connector = aiohttp.TCPConnector(limit=50)
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=20)
        )
        
        try:
            interval = time_window / requests_count
            
            # Send requests at regular intervals
            for i in range(requests_count):
                result = await self.send_tracked_request(session, i, start_time)
                self.results.append(result)
                
                # Real-time display
                self.print_request_result(result)
                
                # Wait for next interval (except last request)
                if i < requests_count - 1:
                    await asyncio.sleep(interval)
                    
                    # Show rate limiter status every 5 requests
                    if (i + 1) % 5 == 0:
                        await self.check_rate_limiter_status(session)
            
            end_time = time.time()
            
            # Comprehensive analysis
            analysis = self.analyze_switching_patterns(start_time, end_time)
            self.print_detailed_analysis(analysis)
            
            return {
                "test_results": [self.result_to_dict(r) for r in self.results],
                "analysis": analysis,
                "test_duration": end_time - start_time
            }
            
        finally:
            await session.close()

    async def send_tracked_request(self, session: aiohttp.ClientSession, request_id: int, start_time: float) -> RequestResult:
        """Send a single request and track which provider handles it"""
        
        request_start = time.time()
        user_id = f"switch_test_{request_id:03d}"
        
        result = RequestResult(
            request_id=request_id,
            timestamp=request_start - start_time,
            user_id=user_id,
            quality_score=0,
            needs_followup=False,
            provider_used="unknown",
            fallback_used=True,
            success=False,
            response_time=0
        )
        
        try:
            # Step 1: Send work update (make it low quality to force followup)
            work_update = self.base_work_update.copy()
            work_update["user_id"] = user_id
            work_update["task"] = f"Fixed bug #{request_id}"  # Vary the task
            
            async with session.post(f"{self.base_url}/api/work-updates", json=work_update) as response:
                work_data = await response.json()
                
                result.response_time = time.time() - request_start
                result.quality_score = work_data.get("qualityScore", 0)
                result.needs_followup = work_data.get("redirectToFollowup", False)
                
                if response.status == 200 and work_data.get("success"):
                    result.success = True
                    
                    if result.needs_followup:
                        # Step 2: Get follow-up questions to identify provider
                        followup_data = await self.get_followup_questions(session, user_id)
                        
                        if followup_data:
                            # Extract provider information from followup response
                            result.provider_used = self.extract_provider_from_followup(followup_data)
                            result.fallback_used = followup_data.get("fallbackUsed", False)
                            
                            questions = followup_data.get("questions", [])
                            if questions:
                                # Get first 50 chars of first question as sample
                                result.questions_sample = questions[0][:50] + "..." if len(questions[0]) > 50 else questions[0]
                            
                            # Also check for provider metadata in the response
                            metadata = followup_data.get("metadata", {})
                            if "provider_name" in metadata:
                                result.provider_used = metadata["provider_name"]
                            elif "selectedProvider" in followup_data:
                                result.provider_used = followup_data["selectedProvider"]
                        else:
                            result.provider_used = "api_error"
                            result.fallback_used = True
                    else:
                        result.provider_used = "high_quality_bypass"
                        result.fallback_used = False
                        result.questions_sample = "No follow-up needed (high quality)"
                else:
                    result.error = f"HTTP {response.status}: {work_data.get('error', 'Unknown error')}"
                    
        except Exception as e:
            result.error = str(e)
            result.response_time = time.time() - request_start
        
        return result

    def extract_provider_from_followup(self, followup_data: Dict[str, Any]) -> str:
        """Extract the actual provider name from followup response"""
        
        # Check various possible fields for provider information
        possible_fields = [
            "provider_name",
            "selectedProvider", 
            "provider",
            "questionType",
            "source",
            "generator"
        ]
        
        for field in possible_fields:
            if field in followup_data:
                provider_value = followup_data[field]
                if provider_value and isinstance(provider_value, str):
                    return provider_value
        
        # Check metadata
        metadata = followup_data.get("metadata", {})
        for field in possible_fields:
            if field in metadata:
                provider_value = metadata[field]
                if provider_value and isinstance(provider_value, str):
                    return provider_value
        
        # Check if there's a provider field in the response structure
        if "response" in followup_data:
            response_data = followup_data["response"]
            if isinstance(response_data, dict):
                for field in possible_fields:
                    if field in response_data:
                        provider_value = response_data[field]
                        if provider_value and isinstance(provider_value, str):
                            return provider_value
        
        # Fallback: try to infer from question style or content
        questions = followup_data.get("questions", [])
        if questions and len(questions) > 0:
            first_question = questions[0].lower()
            
            # Simple heuristics based on typical AI provider response styles
            if "briefly" in first_question and "step" in first_question:
                return "ai_generated_gemini"
            elif "specific" in first_question and "complete" in first_question:
                return "ai_generated_groq"
            elif "describe" in first_question or "explain" in first_question:
                return "ai_generated_huggingface"
        
        return "unknown_provider"

    async def get_followup_questions(self, session: aiohttp.ClientSession, user_id: str) -> Dict[str, Any]:
        """Get follow-up questions and track provider info"""
        try:
            await asyncio.sleep(0.2)  # Small delay for processing
            
            payload = {"user_id": user_id}
            async with session.post(f"{self.base_url}/api/followups/start", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Followup API error: {response.status}")
                    return None
        except Exception as e:
            print(f"Followup request error: {e}")
            return None

    async def check_rate_limiter_status(self, session: aiohttp.ClientSession):
        """Check and display current rate limiter status"""
        try:
            async with session.get(f"{self.base_url}/api/rate-limiters/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    
                    print(f"\n--- Rate Limiter Status Check ---")
                    
                    # Handle both old and new status response formats
                    if "followup_api_keys" in status_data:
                        # Old format
                        followup_keys = status_data.get("followup_api_keys", {}).get("status", {})
                    else:
                        # New format - look for provider status directly
                        followup_keys = {}
                        for key, value in status_data.items():
                            if isinstance(value, dict) and "calls_last_minute" in value:
                                followup_keys[key] = value
                    
                    for provider, status in followup_keys.items():
                        calls = status.get("calls_last_minute", 0)
                        limit = status.get("rate_limit", 8)
                        available = "✓" if status.get("available", True) else "✗"
                        utilization = status.get("utilization_percentage", 0)
                        print(f"   {available} {provider}: {calls}/{limit} calls ({utilization}% used)")
                    print("-" * 100)
                else:
                    print(f"\n--- Rate Limiter Status: HTTP {response.status} ---")
        except Exception as e:
            print(f"\n--- Rate Limiter Status Error: {e} ---")

    def print_request_result(self, result: RequestResult):
        """Print real-time result of each request"""
        
        time_str = f"{result.timestamp:.1f}s"
        provider_display = result.provider_used
        fallback_str = "Yes" if result.fallback_used else "No"
        score_str = f"{result.quality_score:.1f}"
        
        if result.success:
            if result.provider_used == "high_quality_bypass":
                provider_display = "BYPASS"
                fallback_str = "N/A"
            elif result.fallback_used:
                provider_display = f"{provider_display}_FALLBACK"
            
            print(f"{result.request_id:<3} {time_str:<8} {provider_display:<18} {fallback_str:<8} {score_str:<6} {result.questions_sample}")
        else:
            error_msg = result.error[:40] if len(result.error) > 40 else result.error
            print(f"{result.request_id:<3} {time_str:<8} ERROR {error_msg:<12}")

    def analyze_switching_patterns(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """Analyze provider switching patterns and behavior"""
        
        analysis = {
            "test_duration": end_time - start_time,
            "total_requests": len(self.results),
            "successful_requests": sum(1 for r in self.results if r.success),
            "provider_usage": {},
            "switching_timeline": [],
            "rate_limiting_events": [],
            "performance_metrics": {}
        }
        
        # Track provider usage over time
        current_provider = None
        switch_count = 0
        
        for result in self.results:
            if not result.success:
                continue
                
            provider = result.provider_used
            
            # Count provider usage
            if provider not in analysis["provider_usage"]:
                analysis["provider_usage"][provider] = 0
            analysis["provider_usage"][provider] += 1
            
            # Track switches
            if current_provider != provider and provider != "high_quality_bypass":
                if current_provider is not None and current_provider != "high_quality_bypass":
                    switch_count += 1
                    analysis["switching_timeline"].append({
                        "time": result.timestamp,
                        "from": current_provider,
                        "to": provider,
                        "request_id": result.request_id
                    })
                current_provider = provider
            
            # Identify rate limiting events (when fallback starts)
            if result.fallback_used and not result.provider_used == "high_quality_bypass":
                analysis["rate_limiting_events"].append({
                    "time": result.timestamp,
                    "request_id": result.request_id,
                    "provider": result.provider_used
                })
        
        # Calculate performance metrics
        successful_results = [r for r in self.results if r.success]
        if successful_results:
            ai_generated = [r for r in successful_results if r.needs_followup]
            analysis["performance_metrics"] = {
                "success_rate": len(successful_results) / len(self.results) * 100,
                "avg_response_time": sum(r.response_time for r in successful_results) / len(successful_results),
                "provider_switches": switch_count,
                "fallback_rate": sum(1 for r in ai_generated if r.fallback_used) / len(ai_generated) * 100 if ai_generated else 0,
                "ai_generation_rate": len(ai_generated) / len(successful_results) * 100
            }
        
        return analysis

    def print_detailed_analysis(self, analysis: Dict[str, Any]):
        """Print detailed analysis of provider switching"""
        
        print(f"\nDETAILED SWITCHING ANALYSIS")
        print("=" * 60)
        
        metrics = analysis.get("performance_metrics", {})
        
        print(f"\nPERFORMANCE SUMMARY:")
        print(f"  Success Rate: {metrics.get('success_rate', 0):.1f}%")
        print(f"  Avg Response Time: {metrics.get('avg_response_time', 0):.2f}s")
        print(f"  Provider Switches: {metrics.get('provider_switches', 0)}")
        print(f"  Fallback Rate: {metrics.get('fallback_rate', 0):.1f}%")
        print(f"  AI Generation Rate: {metrics.get('ai_generation_rate', 0):.1f}%")
        
        print(f"\nPROVIDER USAGE DISTRIBUTION:")
        total_ai_requests = sum(count for provider, count in analysis["provider_usage"].items() 
                               if provider != "high_quality_bypass")
        
        for provider, count in analysis["provider_usage"].items():
            if total_ai_requests > 0 and provider != "high_quality_bypass":
                percentage = (count / total_ai_requests * 100)
                print(f"  {provider}: {count} requests ({percentage:.1f}%)")
            elif provider == "high_quality_bypass":
                total_percentage = (count / analysis["total_requests"] * 100)
                print(f"  {provider}: {count} requests ({total_percentage:.1f}% of total)")
        
        if analysis["switching_timeline"]:
            print(f"\nPROVIDER SWITCHING TIMELINE:")
            for switch in analysis["switching_timeline"][:10]:  # Show first 10 switches
                print(f"  {switch['time']:.1f}s: {switch['from']} → {switch['to']} (Request #{switch['request_id']})")
            
            if len(analysis["switching_timeline"]) > 10:
                print(f"  ... and {len(analysis['switching_timeline']) - 10} more switches")
        
        # Provider switching effectiveness assessment
        print(f"\nSWITCHING EFFECTIVENESS ASSESSMENT:")
        ai_provider_count = len([p for p in analysis["provider_usage"].keys() 
                                if p not in ["high_quality_bypass", "unknown_provider", "api_error"]])
        
        if ai_provider_count >= 3:
            print("  ✓ Good: Multiple providers are being utilized")
        elif ai_provider_count == 2:
            print("  ⚠ Moderate: Only 2 providers active - consider adding more")
        elif ai_provider_count == 1:
            print("  ✗ Poor: Only 1 provider active - check API keys and configuration")
        else:
            print("  ✗ Critical: No AI providers working - check configuration")
        
        if metrics.get("fallback_rate", 0) < 20:
            print("  ✓ Good: Low fallback rate indicates effective rate limiting")
        elif metrics.get("fallback_rate", 0) < 50:
            print("  ⚠ Moderate: Some fallback usage - monitor under higher load")
        else:
            print("  ✗ High: Excessive fallback usage - increase rate limits or add providers")

    def result_to_dict(self, result: RequestResult) -> Dict[str, Any]:
        """Convert RequestResult to dictionary for JSON serialization"""
        return {
            "request_id": result.request_id,
            "timestamp": result.timestamp,
            "user_id": result.user_id,
            "quality_score": result.quality_score,
            "needs_followup": result.needs_followup,
            "provider_used": result.provider_used,
            "fallback_used": result.fallback_used,
            "success": result.success,
            "response_time": result.response_time,
            "error": result.error,
            "questions_sample": result.questions_sample
        }

    def save_results(self, results: Dict[str, Any]) -> str:
        """Save detailed results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"provider_switching_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return filename


async def main():
    """Run the provider switching test"""
    
    print("Starting AI Provider Switching Test")
    print("This test will show exactly which provider handles each request in real-time")
    print()
    
    tracker = ProviderSwitchingTracker()
    
    # Run test with 15 requests in 60 seconds (one every 4 seconds)
    results = await tracker.run_switching_test(requests_count=15, time_window=60)
    
    # Save detailed results
    filename = tracker.save_results(results)
    print(f"\nDetailed results saved to: {filename}")
    
    print(f"\nTest completed! This shows:")
    print("- Exact provider used for each request")
    print("- When the system switches between providers")
    print("- Rate limiting behavior in real-time")
    print("- Whether your multi-provider setup is working correctly")


if __name__ == "__main__":
    asyncio.run(main())