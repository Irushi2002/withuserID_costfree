#!/usr/bin/env python3
"""
Rate Limiting Test Script for Intern Management API

This script tests the rate limiting functionality by sending multiple requests
to verify that API keys rotate properly when limits are reached.
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import List, Dict, Any

API_BASE = "http://localhost:8000"

class RateLimitTester:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_request(self, endpoint: str, method: str = "POST", data: dict = None) -> Dict[str, Any]:
        """Send a single request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "POST":
                async with self.session.post(url, json=data) as response:
                    return {
                        "status": response.status,
                        "data": await response.json(),
                        "timestamp": datetime.now().isoformat(),
                        "response_time": time.time()
                    }
            elif method == "GET":
                async with self.session.get(url) as response:
                    return {
                        "status": response.status,
                        "data": await response.json(),
                        "timestamp": datetime.now().isoformat(),
                        "response_time": time.time()
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "response_time": time.time()
            }
    
    async def test_quality_analysis_burst(self, num_requests: int = 15) -> List[Dict]:
        """Test quality analysis endpoint with burst requests"""
        print(f"\n🧪 Testing Quality Analysis Endpoint with {num_requests} rapid requests")
        print("=" * 60)
        
        # Prepare test data
        test_data = {
            "user_id": "rate_test_user",
            "work_description": "Fixed some bugs and wrote code for the project"
        }
        
        # Send requests rapidly
        start_time = time.time()
        tasks = []
        
        for i in range(num_requests):
            task = self.send_request("/api/quality/analyze", "POST", test_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Average time per request: {(end_time - start_time) / num_requests:.3f} seconds")
        
        success_count = sum(1 for r in results if r.get("status") == 200)
        error_count = len(results) - success_count
        
        print(f"✅ Successful requests: {success_count}")
        print(f"❌ Failed requests: {error_count}")
        
        # Show first few results
        print("\n📊 Sample Results:")
        for i, result in enumerate(results[:5]):
            status = result.get("status", "unknown")
            if status == 200:
                quality_score = result.get("data", {}).get("quality_score", "N/A")
                print(f"Request {i+1}: Status {status}, Quality Score: {quality_score}")
            else:
                error = result.get("data", {}).get("detail", result.get("error", "Unknown error"))
                print(f"Request {i+1}: Status {status}, Error: {error}")
        
        return results
    
    async def test_work_update_burst(self, num_requests: int = 10) -> List[Dict]:
        """Test work update submission with burst requests"""
        print(f"\n🚀 Testing Work Update Endpoint with {num_requests} requests")
        print("=" * 60)
        
        start_time = time.time()
        tasks = []
        
        for i in range(num_requests):
            test_data = {
                "user_id": f"rate_test_user_{i}",
                "stack": "Backend Development",
                "task": f"Test work update {i+1} - implemented some features",
                "progress": "Making good progress",
                "blockers": "No major blockers",
                "status": "working"
            }
            
            task = self.send_request("/api/work-updates", "POST", test_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"Total time: {end_time - start_time:.2f} seconds")
        
        success_count = sum(1 for r in results if r.get("status") == 200)
        followup_needed = sum(1 for r in results if r.get("status") == 200 and 
                            r.get("data", {}).get("redirectToFollowup", False))
        
        print(f"✅ Successful submissions: {success_count}")
        print(f"🔄 Requiring follow-up: {followup_needed}")
        
        return results
    
    async def test_api_key_rotation(self, num_requests: int = 20) -> Dict:
        """Test API key rotation by checking rate limiter status"""
        print(f"\n🔑 Testing API Key Rotation with {num_requests} requests")
        print("=" * 60)
        
        # Get initial rate limiter status
        initial_status = await self.send_request("/api/rate-limiters/status", "GET")
        print("Initial Rate Limiter Status:")
        if initial_status.get("status") == 200:
            followup_stats = initial_status["data"]["followup_api_keys"]["stats"]
            print(f"  Total API Keys: {followup_stats['total_keys']}")
            print(f"  Total Calls Recorded: {followup_stats['total_calls_recorded']}")
        
        # Send burst of requests that will trigger AI generation
        test_data = {
            "user_id": "rotation_test_user",
            "work_description": "did stuff"  # Low quality to trigger AI
        }
        
        print(f"\nSending {num_requests} quality analysis requests...")
        start_time = time.time()
        
        # Send requests in batches to better observe rotation
        batch_size = 5
        all_results = []
        
        for batch in range(0, num_requests, batch_size):
            batch_end = min(batch + batch_size, num_requests)
            batch_tasks = []
            
            for i in range(batch, batch_end):
                task = self.send_request("/api/quality/analyze", "POST", test_data)
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)
            
            # Short delay between batches to see rate limiting effects
            await asyncio.sleep(1)
            print(f"Completed batch {batch//batch_size + 1}")
        
        end_time = time.time()
        
        # Get final rate limiter status
        final_status = await self.send_request("/api/rate-limiters/status", "GET")
        
        print(f"\nTest completed in {end_time - start_time:.2f} seconds")
        
        if final_status.get("status") == 200:
            final_stats = final_status["data"]["followup_api_keys"]["stats"]
            print(f"Final Total Calls Recorded: {final_stats['total_calls_recorded']}")
            
            # Calculate calls made during test
            if initial_status.get("status") == 200:
                initial_calls = initial_status["data"]["followup_api_keys"]["stats"]["total_calls_recorded"]
                calls_during_test = final_stats["total_calls_recorded"] - initial_calls
                print(f"Calls made during test: {calls_during_test}")
        
        # Analyze success/failure patterns
        success_count = sum(1 for r in all_results if r.get("status") == 200)
        print(f"✅ Successful requests: {success_count}/{num_requests}")
        
        return {
            "total_requests": num_requests,
            "successful_requests": success_count,
            "initial_status": initial_status,
            "final_status": final_status,
            "results": all_results
        }
    
    async def test_weekly_report_api_key(self) -> Dict:
        """Test the dedicated weekly report API key"""
        print(f"\n📊 Testing Weekly Report API Key")
        print("=" * 40)
        
        test_data = {
            "user_id": "weekly_test_user",
            "start_date": "2025-09-14",
            "end_date": "2025-09-20"
        }
        
        result = await self.send_request("/api/reports/weekly", "POST", test_data)
        
        if result.get("status") == 200:
            print("✅ Weekly report API key working")
            print(f"Report length: {len(result['data'].get('report', ''))}")
        else:
            print("❌ Weekly report API key failed")
            print(f"Error: {result.get('data', {}).get('detail', 'Unknown error')}")
        
        return result
    
    async def monitor_system_during_load(self, duration: int = 60) -> List[Dict]:
        """Monitor system status during load testing"""
        print(f"\n📈 Monitoring System Status for {duration} seconds")
        print("=" * 50)
        
        monitoring_data = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Get system stats
            stats = await self.send_request("/stats", "GET")
            health = await self.send_request("/health", "GET")
            
            monitoring_data.append({
                "timestamp": datetime.now().isoformat(),
                "elapsed": time.time() - start_time,
                "stats": stats,
                "health": health
            })
            
            # Print current status
            if stats.get("status") == 200 and health.get("status") == 200:
                pending_followups = stats["data"].get("temp_work_updates", {}).get("pending", 0)
                api_calls = health["data"].get("rate_limiters", {}).get("total_calls_recorded", 0)
                print(f"Time: {time.time() - start_time:.1f}s, Pending: {pending_followups}, API Calls: {api_calls}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        return monitoring_data

async def run_comprehensive_test():
    """Run comprehensive rate limiting tests"""
    print("🎯 Starting Comprehensive Rate Limiting Test")
    print("=" * 80)
    
    async with RateLimitTester() as tester:
        # Test 1: Quality Analysis Burst (should use followup API keys)
        await tester.test_quality_analysis_burst(15)
        
        # Wait a bit between tests
        print("\n⏳ Waiting 10 seconds between tests...")
        await asyncio.sleep(10)
        
        # Test 2: Work Update Burst (mixed quality)
        await tester.test_work_update_burst(8)
        
        # Wait a bit
        print("\n⏳ Waiting 10 seconds...")
        await asyncio.sleep(10)
        
        # Test 3: API Key Rotation Test
        rotation_results = await tester.test_api_key_rotation(25)
        
        # Wait a bit
        print("\n⏳ Waiting 10 seconds...")
        await asyncio.sleep(10)
        
        # Test 4: Weekly Report API Key
        await tester.test_weekly_report_api_key()
        
        # Test 5: System stress test
        print(f"\n🔥 Starting stress test with rapid requests...")
        stress_tasks = []
        
        # Quality analysis stress
        for i in range(10):
            stress_tasks.append(tester.test_quality_analysis_burst(5))
        
        stress_results = await asyncio.gather(*stress_tasks)
        
        total_stress_requests = sum(len(result) for result in stress_results)
        total_stress_success = sum(
            sum(1 for r in result if r.get("status") == 200) 
            for result in stress_results
        )
        
        print(f"\n🔥 Stress Test Results:")
        print(f"Total requests sent: {total_stress_requests}")
        print(f"Successful requests: {total_stress_success}")
        print(f"Success rate: {(total_stress_success/total_stress_requests*100):.1f}%")
    
    print(f"\n✅ Comprehensive test completed!")
    print("Check your API logs to see key rotation in action")

async def run_simple_burst_test():
    """Run a simple burst test"""
    print("⚡ Running Simple Burst Test (20 requests in rapid succession)")
    print("=" * 60)
    
    async with RateLimitTester() as tester:
        results = await tester.test_quality_analysis_burst(20)
        
        # Get final rate limiter status
        status = await tester.send_request("/api/rate-limiters/status", "GET")
        
        if status.get("status") == 200:
            print("\n📊 Final Rate Limiter Status:")
            followup_data = status["data"]["followup_api_keys"]
            print(f"Total API Keys: {followup_data['stats']['total_keys']}")
            print(f"Total Calls: {followup_data['stats']['total_calls_recorded']}")
            
            print("\nPer-key status:")
            for key, info in followup_data["status"].items():
                available = "✅" if info["available"] else "❌"
                print(f"  {key}: {available} ({info['calls_last_minute']}/{info['rate_limit']})")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        asyncio.run(run_simple_burst_test())
    else:
        asyncio.run(run_comprehensive_test())