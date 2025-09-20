#!/usr/bin/env python3
"""
Simple Rate Limit Stress Test
This script sends many requests quickly to test rate limiting behavior
"""

import requests
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"

def send_work_update(request_id, delay=0):
    """Send a single work update request"""
    if delay > 0:
        time.sleep(delay)
    
    start_time = time.time()
    
    payload = {
        "user_id": f"stress_test_{request_id}",
        "stack": "Backend",
        "task": "did some work today",  # Low quality to force AI generation
        "progress": "some progress",
        "blockers": "no blockers",
        "status": "working"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/work-updates",
            json=payload,
            timeout=30
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "request_id": request_id,
                "success": True,
                "status_code": 200,
                "response_time": response_time,
                "quality_score": data.get("qualityScore"),
                "fallback_used": data.get("fallbackUsed", False),
                "followup_type": data.get("followupType", "none"),
                "needs_followup": data.get("redirectToFollowup", False)
            }
        else:
            return {
                "request_id": request_id,
                "success": False,
                "status_code": response.status_code,
                "response_time": response_time,
                "error": response.text[:100]
            }
    except Exception as e:
        return {
            "request_id": request_id,
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time
        }

def stress_test_concurrent(num_requests=20, max_workers=5):
    """Send multiple concurrent requests"""
    print(f"\n{'='*50}")
    print(f"CONCURRENT STRESS TEST")
    print(f"Requests: {num_requests}, Workers: {max_workers}")
    print(f"{'='*50}")
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all requests
        future_to_id = {
            executor.submit(send_work_update, i): i 
            for i in range(num_requests)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_id):
            request_id = future_to_id[future]
            try:
                result = future.result()
                results.append(result)
                
                # Print progress
                status = "SUCCESS" if result["success"] else "FAILED"
                quality = result.get("quality_score", "N/A")
                fallback = result.get("fallback_used", False)
                
                print(f"Request {request_id:2d}: {status:7s} - "
                      f"Score: {quality:4s}, Fallback: {fallback}, "
                      f"Time: {result['response_time']:.2f}s")
                
            except Exception as e:
                print(f"Request {request_id:2d}: ERROR - {e}")
                results.append({
                    "request_id": request_id,
                    "success": False,
                    "error": str(e)
                })
    
    total_time = time.time() - start_time
    
    # Analyze results
    print(f"\n{'='*50}")
    print(f"STRESS TEST RESULTS")
    print(f"{'='*50}")
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    ai_generated = sum(1 for r in results if r.get("success") and not r.get("fallback_used"))
    fallback_used = sum(1 for r in results if r.get("success") and r.get("fallback_used"))
    
    avg_response_time = sum(r["response_time"] for r in results if "response_time" in r) / len(results)
    
    print(f"Total Requests: {num_requests}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"AI Generated: {ai_generated}")
    print(f"Fallback Used: {fallback_used}")
    print(f"Success Rate: {successful/num_requests*100:.1f}%")
    print(f"AI Generation Rate: {ai_generated/num_requests*100:.1f}%")
    print(f"Average Response Time: {avg_response_time:.2f}s")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Request Rate: {num_requests/total_time:.1f} req/s")
    
    return results

def sequential_test(num_requests=15, delay=0.1):
    """Send requests sequentially with small delays"""
    print(f"\n{'='*50}")
    print(f"SEQUENTIAL RATE LIMIT TEST")
    print(f"Requests: {num_requests}, Delay: {delay}s")
    print(f"{'='*50}")
    
    results = []
    start_time = time.time()
    
    for i in range(num_requests):
        result = send_work_update(i, delay)
        results.append(result)
        
        status = "SUCCESS" if result["success"] else "FAILED"
        quality = result.get("quality_score", "N/A")
        fallback = result.get("fallback_used", False)
        
        print(f"Request {i+1:2d}: {status:7s} - "
              f"Score: {quality:4s}, Fallback: {fallback}, "
              f"Time: {result['response_time']:.2f}s")
    
    total_time = time.time() - start_time
    
    # Analysis
    successful = sum(1 for r in results if r["success"])
    ai_generated = sum(1 for r in results if r.get("success") and not r.get("fallback_used"))
    fallback_used = sum(1 for r in results if r.get("success") and r.get("fallback_used"))
    
    print(f"\nSequential Test Results:")
    print(f"Success: {successful}/{num_requests}")
    print(f"AI Generated: {ai_generated}")
    print(f"Fallback Used: {fallback_used}")
    print(f"Total Time: {total_time:.2f}s")
    
    return results

def check_rate_limiter_status():
    """Check current rate limiter status"""
    print(f"\n{'='*50}")
    print(f"RATE LIMITER STATUS")
    print(f"{'='*50}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/rate-limiters/status")
        if response.status_code == 200:
            data = response.json()
            print("Rate Limiter Status:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Rate Limiting Stress Test Tool")
    print("="*30)
    
    # Check initial status
    check_rate_limiter_status()
    
    while True:
        print("\nChoose test type:")
        print("1. Sequential test (15 requests)")
        print("2. Concurrent stress test (20 requests)")
        print("3. Heavy concurrent test (50 requests)")
        print("4. Check rate limiter status")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            sequential_test()
        elif choice == "2":
            stress_test_concurrent(20, 5)
        elif choice == "3":
            stress_test_concurrent(50, 10)
        elif choice == "4":
            check_rate_limiter_status()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()