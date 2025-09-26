#!/usr/bin/env python3/test file
"""
Burst Work Update Test with AI Provider Comparison

This test specifically:
1. Sends multiple work updates within 1 minute to test rate limiting
2. Captures and compares follow-up questions from different AI providers
3. Analyzes question quality and provider behavior under load
4. Validates proper API routing and fallback mechanisms
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

@dataclass
class WorkUpdateTemplate:
    """Template for different quality levels of work updates"""
    stack: str
    task: str
    progress: str
    blockers: str
    status: str = "working"
    expected_quality: str = "low"  # low, medium, high

@dataclass
class AIProviderResult:
    """Results from a specific AI provider"""
    provider_name: str
    questions: List[str]
    response_time: float
    fallback_used: bool
    session_id: str
    quality_score: float
    question_type: str
    generation_successful: bool = True
    error_message: str = ""

@dataclass
class TestResults:
    """Complete test results"""
    test_duration: float = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    high_quality_bypassed: int = 0
    ai_followups_triggered: int = 0
    provider_results: Dict[str, List[AIProviderResult]] = field(default_factory=lambda: defaultdict(list))
    rate_limiting_events: List[Dict] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class BurstWorkUpdateTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = TestResults()
        
        # Different work update templates to trigger AI generation
        self.work_templates = [
            # Low quality - should trigger AI
            WorkUpdateTemplate(
                stack="Backend Development",
                task="Fixed some bugs in the API",
                progress="Good progress",
                blockers="No issues",
                expected_quality="low"
            ),
            WorkUpdateTemplate(
                stack="Frontend Development", 
                task="Updated UI components",
                progress="OK",
                blockers="None",
                expected_quality="low"
            ),
            WorkUpdateTemplate(
                stack="Database",
                task="Did database work",
                progress="Fine",
                blockers="Nothing major",
                expected_quality="low"
            ),
            WorkUpdateTemplate(
                stack="Testing",
                task="Ran some tests",
                progress="Tests passed",
                blockers="No blockers",
                expected_quality="low"
            ),
            WorkUpdateTemplate(
                stack="DevOps",
                task="Updated configuration files",
                progress="Completed the updates",
                blockers="Need review",
                expected_quality="low"
            ),
            # Medium quality - might trigger AI
            WorkUpdateTemplate(
                stack="Full Stack Development",
                task="Implemented user authentication using JWT tokens and bcrypt for password hashing",
                progress="Successfully integrated with existing user model and tested login/logout flow",
                blockers="Need to implement password reset functionality next",
                expected_quality="medium"
            ),
            WorkUpdateTemplate(
                stack="Mobile Development",
                task="Built responsive navigation component with drawer menu and tab navigation",
                progress="Completed iOS testing, Android testing in progress",
                blockers="Need to fix keyboard overlap issue on smaller screens",
                expected_quality="medium"
            ),
            # High quality - should bypass AI
            WorkUpdateTemplate(
                stack="Backend Development",
                task="Implemented comprehensive REST API endpoints for user management including CRUD operations, authentication middleware, input validation, error handling, and rate limiting. Added extensive unit tests covering edge cases and integrated with PostgreSQL database using proper ORM relationships.",
                progress="Successfully completed all planned features including JWT authentication, password hashing with bcrypt, email verification system, and role-based access control. Conducted thorough testing including unit tests, integration tests, and manual API testing using Postman.",
                blockers="Planning to implement caching layer with Redis for improved performance and add API documentation using Swagger/OpenAPI. Need security review from senior developer before production deployment.",
                expected_quality="high"
            )
        ]

    async def run_burst_test(self, num_requests: int = 20, time_window_seconds: int = 60) -> TestResults:
        """Run burst test with specified number of requests in time window"""
        
        print(f"Starting burst test: {num_requests} requests in {time_window_seconds} seconds")
        print("=" * 60)
        
        start_time = time.time()
        self.results = TestResults()
        
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        try:
            # Calculate request intervals
            interval = time_window_seconds / num_requests
            
            tasks = []
            for i in range(num_requests):
                # Select work template (weighted toward low quality for AI testing)
                if i < num_requests * 0.7:  # 70% low quality
                    template = random.choice([t for t in self.work_templates if t.expected_quality == "low"])
                elif i < num_requests * 0.9:  # 20% medium quality  
                    template = random.choice([t for t in self.work_templates if t.expected_quality == "medium"])
                else:  # 10% high quality
                    template = random.choice([t for t in self.work_templates if t.expected_quality == "high"])
                
                user_id = f"burst_test_user_{i:03d}"
                
                # Schedule request
                delay = i * interval
                task = self.send_delayed_request(session, template, user_id, delay)
                tasks.append(task)
            
            # Execute all requests
            await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            self.results.test_duration = end_time - start_time
            
            # Generate comprehensive analysis
            await self.analyze_results()
            
        finally:
            await session.close()
        
        return self.results

    async def send_delayed_request(self, session: aiohttp.ClientSession, template: WorkUpdateTemplate, user_id: str, delay: float):
        """Send a work update request with specified delay"""
        
        await asyncio.sleep(delay)
        request_start = time.time()
        
        try:
            # Create work update payload
            work_update = {
                "user_id": user_id,
                "stack": template.stack,
                "task": template.task,
                "progress": template.progress,
                "blockers": template.blockers,
                "status": template.status
            }
            
            # Send work update
            async with session.post(f"{self.base_url}/api/work-updates", json=work_update) as response:
                response_time = time.time() - request_start
                self.results.response_times.append(response_time)
                self.results.total_requests += 1
                
                if response.status == 200:
                    data = await response.json()
                    self.results.successful_requests += 1
                    
                    if data.get("redirectToFollowup"):
                        # AI follow-up triggered
                        self.results.ai_followups_triggered += 1
                        await self.process_followup_session(session, user_id, template.expected_quality, data.get("qualityScore", 0))
                    else:
                        # High quality - bypassed AI
                        self.results.high_quality_bypassed += 1
                        print(f"✓ {user_id}: High quality bypassed (Score: {data.get('qualityScore', 'N/A')})")
                
                else:
                    self.results.failed_requests += 1
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    self.results.errors.append(error_msg)
                    print(f"✗ {user_id}: Failed - {error_msg}")
                    
        except Exception as e:
            self.results.failed_requests += 1
            self.results.total_requests += 1
            error_msg = f"Exception: {str(e)}"
            self.results.errors.append(error_msg)
            print(f"✗ {user_id}: Error - {error_msg}")

    async def process_followup_session(self, session: aiohttp.ClientSession, user_id: str, expected_quality: str, quality_score: float):
        """Process follow-up session and capture AI provider results"""
        
        try:
            followup_start = time.time()
            
            # Start follow-up session
            payload = {"user_id": user_id}
            async with session.post(f"{self.base_url}/api/followups/start", json=payload) as response:
                
                if response.status == 200:
                    data = await response.json()
                    followup_time = time.time() - followup_start
                    
                    # Create provider result
                    provider_result = AIProviderResult(
                        provider_name=data.get("questionType", "unknown"),
                        questions=data.get("questions", []),
                        response_time=followup_time,
                        fallback_used=data.get("fallbackUsed", False),
                        session_id=data.get("sessionId", ""),
                        quality_score=quality_score,
                        question_type=data.get("questionType", "unknown")
                    )
                    
                    # Store result by provider
                    self.results.provider_results[provider_result.provider_name].append(provider_result)
                    
                    # Log result
                    if provider_result.fallback_used:
                        print(f"⚠ {user_id}: Fallback questions used (Score: {quality_score})")
                    else:
                        print(f"✓ {user_id}: AI questions from {provider_result.provider_name} (Score: {quality_score})")
                        
                        # Display sample question for comparison
                        if provider_result.questions:
                            sample_q = provider_result.questions[0][:80] + "..." if len(provider_result.questions[0]) > 80 else provider_result.questions[0]
                            print(f"  Sample: \"{sample_q}\"")
                
                else:
                    error_msg = f"Follow-up failed: HTTP {response.status}"
                    self.results.errors.append(error_msg)
                    print(f"✗ {user_id}: {error_msg}")
                    
        except Exception as e:
            error_msg = f"Follow-up exception: {str(e)}"
            self.results.errors.append(error_msg)
            print(f"✗ {user_id}: {error_msg}")

    async def analyze_results(self):
        """Analyze and compare results across AI providers"""
        
        print("\n" + "="*60)
        print("DETAILED ANALYSIS")
        print("="*60)
        
        # Basic stats
        success_rate = (self.results.successful_requests / self.results.total_requests * 100) if self.results.total_requests > 0 else 0
        avg_response_time = statistics.mean(self.results.response_times) if self.results.response_times else 0
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Test Duration: {self.results.test_duration:.2f}s")
        print(f"   Total Requests: {self.results.total_requests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Average Response Time: {avg_response_time:.2f}s")
        print(f"   Requests/Second: {self.results.total_requests / self.results.test_duration:.2f}")
        
        print(f"\n🤖 AI GENERATION BREAKDOWN:")
        print(f"   AI Follow-ups Triggered: {self.results.ai_followups_triggered}")
        print(f"   High Quality Bypassed: {self.results.high_quality_bypassed}")
        print(f"   AI Usage Rate: {(self.results.ai_followups_triggered / self.results.total_requests * 100):.1f}%")
        
        # Provider comparison
        if self.results.provider_results:
            print(f"\n🔄 PROVIDER COMPARISON:")
            
            for provider_name, results in self.results.provider_results.items():
                if not results:
                    continue
                    
                total_calls = len(results)
                fallback_count = sum(1 for r in results if r.fallback_used)
                ai_count = total_calls - fallback_count
                
                if ai_count > 0:
                    avg_response_time = statistics.mean([r.response_time for r in results if not r.fallback_used])
                    avg_quality_score = statistics.mean([r.quality_score for r in results])
                    
                    print(f"\n   {provider_name}:")
                    print(f"     Total Calls: {total_calls}")
                    print(f"     AI Generated: {ai_count}")
                    print(f"     Fallback Used: {fallback_count}")
                    print(f"     Avg Response Time: {avg_response_time:.2f}s")
                    print(f"     Avg Quality Score: {avg_quality_score:.1f}")
                    
                    # Show sample questions for comparison
                    ai_results = [r for r in results if not r.fallback_used and r.questions]
                    if ai_results:
                        sample_result = ai_results[0]
                        print(f"     Sample Questions:")
                        for i, q in enumerate(sample_result.questions[:2], 1):
                            short_q = q[:70] + "..." if len(q) > 70 else q
                            print(f"       {i}. {short_q}")
        
        # Question quality analysis
        await self.analyze_question_quality()
        
        # Rate limiting analysis
        self.analyze_rate_limiting()

    async def analyze_question_quality(self):
        """Analyze and compare question quality across providers"""
        
        print(f"\n📝 QUESTION QUALITY ANALYSIS:")
        
        provider_quality = {}
        
        for provider_name, results in self.results.provider_results.items():
            ai_results = [r for r in results if not r.fallback_used and r.questions]
            
            if ai_results:
                all_questions = []
                for result in ai_results:
                    all_questions.extend(result.questions)
                
                if all_questions:
                    # Calculate quality metrics
                    avg_length = statistics.mean(len(q) for q in all_questions)
                    unique_questions = len(set(all_questions))
                    total_questions = len(all_questions)
                    diversity_score = unique_questions / total_questions if total_questions > 0 else 0
                    
                    # Count question words that indicate quality
                    quality_indicators = ["how", "what", "why", "which", "describe", "explain", "steps", "process"]
                    quality_question_count = sum(1 for q in all_questions 
                                               if any(indicator in q.lower() for indicator in quality_indicators))
                    quality_percentage = (quality_question_count / total_questions * 100) if total_questions > 0 else 0
                    
                    provider_quality[provider_name] = {
                        "total_questions": total_questions,
                        "unique_questions": unique_questions,
                        "avg_length": avg_length,
                        "diversity_score": diversity_score,
                        "quality_percentage": quality_percentage,
                        "sample_questions": all_questions[:3]
                    }
        
        # Display quality comparison
        for provider_name, quality in provider_quality.items():
            print(f"\n   {provider_name} Quality Metrics:")
            print(f"     Total Questions: {quality['total_questions']}")
            print(f"     Unique Questions: {quality['unique_questions']}")
            print(f"     Diversity Score: {quality['diversity_score']:.2f}")
            print(f"     Avg Question Length: {quality['avg_length']:.1f} chars")
            print(f"     Quality Indicators: {quality['quality_percentage']:.1f}%")

    def analyze_rate_limiting(self):
        """Analyze rate limiting behavior"""
        
        print(f"\n⚡ RATE LIMITING ANALYSIS:")
        
        fallback_count = sum(len([r for r in results if r.fallback_used]) 
                           for results in self.results.provider_results.values())
        total_ai_attempts = sum(len(results) for results in self.results.provider_results.values())
        
        if total_ai_attempts > 0:
            fallback_rate = (fallback_count / total_ai_attempts * 100)
            print(f"   Fallback Rate: {fallback_rate:.1f}%")
            
            if fallback_rate > 30:
                print("   ⚠️ High fallback rate - providers may be hitting rate limits")
            elif fallback_rate > 10:
                print("   ⚠️ Moderate fallback rate - monitor provider capacity")
            else:
                print("   ✅ Low fallback rate - rate limiting working well")
        
        # Provider distribution
        provider_usage = {name: len(results) for name, results in self.results.provider_results.items()}
        if provider_usage:
            print(f"   Provider Usage Distribution:")
            total_usage = sum(provider_usage.values())
            for provider, usage in provider_usage.items():
                percentage = (usage / total_usage * 100) if total_usage > 0 else 0
                print(f"     {provider}: {usage} calls ({percentage:.1f}%)")

    def save_detailed_results(self) -> str:
        """Save detailed results to JSON file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"burst_test_results_{timestamp}.json"
        
        # Convert results to serializable format
        serializable_results = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_duration": self.results.test_duration,
                "total_requests": self.results.total_requests,
                "test_type": "burst_workupdate_ai_comparison"
            },
            "performance_summary": {
                "successful_requests": self.results.successful_requests,
                "failed_requests": self.results.failed_requests,
                "success_rate": (self.results.successful_requests / self.results.total_requests * 100) if self.results.total_requests > 0 else 0,
                "avg_response_time": statistics.mean(self.results.response_times) if self.results.response_times else 0,
                "requests_per_second": self.results.total_requests / self.results.test_duration if self.results.test_duration > 0 else 0
            },
            "ai_generation_summary": {
                "ai_followups_triggered": self.results.ai_followups_triggered,
                "high_quality_bypassed": self.results.high_quality_bypassed,
                "ai_usage_rate": (self.results.ai_followups_triggered / self.results.total_requests * 100) if self.results.total_requests > 0 else 0
            },
            "provider_results": {},
            "errors": self.results.errors,
            "response_times": self.results.response_times
        }
        
        # Add provider-specific results
        for provider_name, results in self.results.provider_results.items():
            serializable_results["provider_results"][provider_name] = [
                {
                    "questions": result.questions,
                    "response_time": result.response_time,
                    "fallback_used": result.fallback_used,
                    "quality_score": result.quality_score,
                    "question_type": result.question_type,
                    "generation_successful": result.generation_successful
                }
                for result in results
            ]
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        return filename


async def main():
    """Run the burst test with different configurations"""
    
    print("🚀 Burst Work Update Test with AI Provider Comparison")
    print("=" * 60)
    
    test_configs = [
        {"requests": 15, "time_window": 60, "name": "Standard Burst Test"},
        {"requests": 25, "time_window": 60, "name": "High Load Test"},
    ]
    
    tester = BurstWorkUpdateTester()
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"Running {config['name']}: {config['requests']} requests in {config['time_window']}s")
        print(f"{'='*60}")
        
        results = await tester.run_burst_test(
            num_requests=config["requests"],
            time_window_seconds=config["time_window"]
        )
        
        # Save results
        filename = tester.save_detailed_results()
        print(f"\n📁 Detailed results saved to: {filename}")
        
        # Wait between tests
        if config != test_configs[-1]:
            print("\n⏳ Waiting 30 seconds before next test...")
            await asyncio.sleep(30)
    
    print("\n✅ All burst tests completed!")
    print("\nAnalysis Summary:")
    print("- Check the generated JSON files for detailed provider comparisons")
    print("- Look for patterns in question quality across different AI providers")
    print("- Monitor fallback rates to assess rate limiting effectiveness")
    print("- Compare response times and success rates under load")


if __name__ == "__main__":
    asyncio.run(main())