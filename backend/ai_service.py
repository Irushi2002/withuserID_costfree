import google.generativeai as genai
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Optional
import logging
import re
import math
from dateutil import parser
from pymongo import DESCENDING

from config import Config
from database import get_database
from models import SessionStatus
from rate_limiter import get_followup_rate_limiter, get_weekly_report_rate_limiter
from quality_score import get_quality_scorer
from ai_client import AIClientWrapper, AIProviderManager

logger = logging.getLogger(__name__)

class AIFollowupService:
    def __init__(self):
        """Initialize AI service with multiple providers and quality scoring"""
        self.db = get_database()
        self.config = Config()
        
        # Get rate limiters for different services
        self.followup_rate_limiter = get_followup_rate_limiter()
        self.weekly_rate_limiter = get_weekly_report_rate_limiter()
        
        # Get quality scorer
        self.quality_scorer = get_quality_scorer()
        
        # Initialize AI provider manager for followup questions
        self.provider_manager = AIProviderManager(self.config.AI_PROVIDERS_CONFIG)
        
        logger.info("AI Followup Service initialized with multiple AI providers")
        
    async def process_work_update_with_quality_check(
        self, 
        work_description: str, 
        intern_id: str, 
        update_date: str = None
    ) -> Dict[str, Any]:
        """
        Main method: Check work quality and decide if follow-up is needed
        
        Returns:
            Dict containing decision, score, and follow-up data if needed
        """
        try:
            # Step 1: Calculate quality score and determine if follow-up needed
            needs_followup, score_details = await self.quality_scorer.should_trigger_followup(
                work_description, intern_id, update_date
            )
            
            result = {
                "needs_followup": needs_followup,
                "quality_score": score_details.get("quality_score", 0),
                "score_details": score_details,
                "followup_data": None,
                "fallback_used": False
            }
            
            if not needs_followup:
                logger.info(f"High quality work update (score: {result['quality_score']}) - no follow-up needed")
                return result
            
            # Step 2: If follow-up needed, try to generate AI questions
            logger.info(f"Low quality work update (score: {result['quality_score']}) - generating follow-up")
            
            # Get available provider
            available_provider = await self.followup_rate_limiter.get_available_provider(record_call=True)
            if available_provider:
                # Generate AI follow-up questions using available provider
                try:
                    questions = await self._generate_ai_followup_questions_multi_provider(
                        intern_id, 
                        work_description, 
                        available_provider
                    )

                    result["followup_data"] = {
                        "questions": questions,
                        "session_id": None,  # Will be set when session is created
                        "type": f"ai_generated_{available_provider['provider']}",
                        "provider_name": available_provider['name']
                    }
                    logger.info(f"AI follow-up questions generated using {available_provider['name']}")
                    
                except Exception as e:
                    logger.error(f"AI question generation failed with {available_provider['name']}: {e}")
                    # Fall back to default questions
                    result["followup_data"] = {
                        "questions": self._get_default_questions(),
                        "session_id": None,
                        "type": "default_fallback",
                        "provider_name": "fallback"
                    }
                    result["fallback_used"] = True
                    logger.info("Using default questions due to AI generation failure")
            else:
                # All providers are rate limited - use default questions
                result["followup_data"] = {
                    "questions": self._get_default_questions(),
                    "session_id": None,
                    "type": "rate_limited_fallback",
                    "provider_name": "fallback"
                }
                result["fallback_used"] = True
                logger.info("Using default questions due to provider rate limits")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing work update with quality check: {e}")
            # Safe fallback
            return {
                "needs_followup": True,  # Err on side of caution
                "quality_score": 0,
                "score_details": {"error": str(e)},
                "followup_data": {
                    "questions": self._get_default_questions(),
                    "session_id": None,
                    "type": "error_fallback",
                    "provider_name": "fallback"
                },
                "fallback_used": True
            }
    
    async def _generate_ai_followup_questions_multi_provider(
        self, 
        intern_id: str, 
        work_description: str,
        provider_config: Dict[str, str]
    ) -> List[str]:
        """
        Generate AI follow-up questions using any available provider
        """
        # Get AI client for the provider
        client = self.provider_manager.get_client(provider_config['name'])
        if not client:
            logger.error(f"No client found for provider: {provider_config['name']}")
            return self._get_default_questions()
        
        # Build work update data for context
        work_update_data = {
            "description": work_description,
            "user_id": intern_id
        }
        
        # Get context and generate questions
        recent_docs = await self._get_recent_work_history(intern_id)
        current_context = self._build_current_work_context(work_update_data)
        history_context = self._build_work_history_context(recent_docs) if recent_docs else ""
        
        prompt = self._build_ai_prompt(current_context, history_context, recent_docs)
        
        logger.info(f"Sending request to {provider_config['name']} ({provider_config['provider']})")
        response_text = await client.generate_content(prompt)
        
        if response_text and response_text.strip():
            questions = self._parse_questions_from_response(response_text)
            if len(questions) >= 3:
                logger.info(f"Successfully generated {len(questions)} AI questions using {provider_config['name']}")
                return questions
            else:
                logger.warning(f"{provider_config['name']} generated only {len(questions)} questions, using defaults")
                return self._get_default_questions()
        else:
            logger.error(f"{provider_config['name']} response was null or empty")
            return self._get_default_questions()
    
    async def generate_weekly_report(
        self, 
        intern_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate AI-powered weekly report using Gemini
        """
        try:
            # Get available provider for weekly reports (Gemini only)
            provider = await self.weekly_rate_limiter.wait_if_needed()
            
            # Configure genai with weekly report API key
            genai.configure(api_key=provider['api_key'])
            model = genai.GenerativeModel(provider['model'])
            
            # Fetch weekly data
            weekly_data = await self._fetch_weekly_data(intern_id, start_date, end_date)
            
            if not weekly_data["work_updates"]:
                return {
                    "success": False,
                    "message": "No work updates found for the specified date range",
                    "report": None
                }
            
            # Build weekly report prompt
            prompt = self._build_weekly_report_prompt(weekly_data, start_date, end_date)
            
            logger.info(f"Generating weekly report for intern {intern_id} using {provider['name']}")
            response = model.generate_content(prompt)
            
            if response.text and response.text.strip():
                return {
                    "success": True,
                    "report": response.text.strip(),
                    "data_summary": {
                        "work_updates_count": len(weekly_data["work_updates"]),
                        "followup_sessions_count": len(weekly_data["followup_sessions"]),
                        "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                        "provider_used": provider['name']
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "AI failed to generate report",
                    "report": None
                }
                
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {
                "success": False,
                "message": f"Failed to generate weekly report: {str(e)}",
                "report": None
            }
    
    async def test_ai_connection(self) -> Dict[str, Any]:
        """Test all AI provider connections"""
        results = {
            "followup_providers": {},
            "weekly_report_provider": {},
            "summary": {}
        }
        
        try:
            # Test followup providers
            followup_results = await self.provider_manager.test_all_connections()
            results["followup_providers"] = followup_results
            
            working_providers = sum(1 for result in followup_results.values() if result.get("status") == "working")
            
            # Test weekly report provider (Gemini)
            try:
                weekly_provider = await self.weekly_rate_limiter.get_available_provider(record_call=False)
                if weekly_provider:
                    genai.configure(api_key=weekly_provider['api_key'])
                    model = genai.GenerativeModel(weekly_provider['model'])
                    response = model.generate_content('Generate a test weekly report header: "Weekly Report Test"')
                    
                    if response.text and "report" in response.text.lower():
                        results["weekly_report_provider"] = {
                            "status": "working",
                            "name": weekly_provider['name'],
                            "response": response.text[:50] + "..."
                        }
                    else:
                        results["weekly_report_provider"] = {
                            "status": "failed",
                            "name": weekly_provider['name'],
                            "error": "Invalid response"
                        }
                else:
                    results["weekly_report_provider"] = {
                        "status": "error",
                        "error": "No weekly report provider available"
                    }
                    
            except Exception as e:
                results["weekly_report_provider"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Summary
            total_followup_providers = len(followup_results)
            weekly_working = results["weekly_report_provider"].get("status") == "working"
            
            results["summary"] = {
                "total_followup_providers": total_followup_providers,
                "working_followup_providers": working_providers,
                "weekly_report_provider_working": weekly_working,
                "overall_status": "healthy" if working_providers > 0 and weekly_working else "degraded",
                "fallback_available": True,
                "provider_types": {
                    "gemini": sum(1 for r in followup_results.values() if r.get("provider") == "gemini"),
                    "groq": sum(1 for r in followup_results.values() if r.get("provider") == "groq"),
                    "huggingface": sum(1 for r in followup_results.values() if r.get("provider") == "huggingface")
                }
            }
            
            logger.info(f"AI Connection Test: {working_providers}/{total_followup_providers} followup providers working, "
                       f"weekly provider: {'working' if weekly_working else 'failed'}")
            
            return results
            
        except Exception as e:
            logger.error(f"AI connection test failed: {e}")
            return {
                "error": str(e),
                "summary": {
                    "overall_status": "error",
                    "fallback_available": True
                }
            }
    
    # CORRECTED: Fetch weekly data from dailyrecords collection
    async def _fetch_weekly_data(
        self, 
        intern_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Fetch all data needed for weekly report generation from correct collections"""
        daily_records_collection = self.db["dailyrecords"]  # Query actual data location
        followup_sessions_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        # Convert to string format for date queries
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch work updates from dailyrecords collection (where data actually is)
        work_updates_query = {
            "internId": intern_id,  # dailyrecords uses internId consistently
            "date": {
                "$gte": start_date_str,
                "$lte": end_date_str
            }
        }
        
        work_updates_cursor = daily_records_collection.find(work_updates_query).sort("date", 1)
        work_updates = await work_updates_cursor.to_list(length=None)
        
        # Fetch followup sessions for the week
        followup_query = {
            "$or": [
                {"userId": intern_id},
                {"internId": intern_id}
            ],
            "createdAt": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        followup_cursor = followup_sessions_collection.find(followup_query).sort("createdAt", 1)
        followup_sessions = await followup_cursor.to_list(length=None)
        
        logger.info(f"Weekly data fetch: Found {len(work_updates)} work updates and {len(followup_sessions)} sessions for intern {intern_id}")
        
        return {
            "work_updates": work_updates,
            "followup_sessions": followup_sessions,
            "intern_id": intern_id,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def _build_weekly_report_prompt(
        self, 
        weekly_data: Dict[str, Any], 
        start_date: datetime, 
        end_date: datetime
    ) -> str:
        """Build AI prompt for weekly report generation"""
        work_updates = weekly_data["work_updates"]
        followup_sessions = weekly_data["followup_sessions"]
        intern_id = weekly_data["intern_id"]
        
        # Format work updates
        work_summary = []
        for i, update in enumerate(work_updates, 1):
            date = update.get("date") or update.get("update_date", "Unknown")
            task = update.get("task") or update.get("description", "No description")
            progress = update.get("progress", "")
            blockers = update.get("blockers", "")
            status = update.get("status", "unknown")
            
            work_summary.append(f"""
Day {i} ({date}):
- Status: {status}
- Tasks: {task}
- Progress: {progress if progress else 'Not specified'}
- Challenges: {blockers if blockers else 'None mentioned'}
""")
        
        # Format followup sessions
        followup_summary = []
        for i, session in enumerate(followup_sessions, 1):
            questions = session.get("questions", [])
            answers = session.get("answers", [])
            status = session.get("status", "unknown")
            created_date = session.get("createdAt", datetime.now()).strftime('%Y-%m-%d')
            
            qa_pairs = []
            for q, a in zip(questions, answers):
                qa_pairs.append(f"Q: {q}\nA: {a if a else 'Not answered'}")
            
            followup_summary.append(f"""
Follow-up Session {i} ({created_date}) - Status: {status}
{chr(10).join(qa_pairs)}
""")
        
        prompt = f"""You are generating a comprehensive weekly report for an intern's progress and performance.

**Intern ID:** {intern_id}
**Week Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}

**WORK UPDATES THIS WEEK:**
{''.join(work_summary)}

**FOLLOW-UP SESSIONS THIS WEEK:**
{''.join(followup_summary) if followup_summary else "No follow-up sessions this week."}

Generate a professional weekly report that includes:

1. **Executive Summary** - Overall performance and progress
2. **Daily Work Breakdown** - What was accomplished each day
3. **Key Achievements** - Major completions and successes
4. **Challenges & Blockers** - Issues faced and how they were addressed
5. **Areas for Improvement** - Constructive feedback based on work quality
6. **Plans for Next Week** - Recommendations and expected outcomes
7. **Manager Notes** - Any concerns or praise worth highlighting

Make the report:
- Professional but supportive in tone
- Specific with examples from the work updates
- Constructive in feedback
- Actionable in recommendations
- Suitable for sharing with managers and the intern

Format the report in clear sections with appropriate headings."""
        
        return prompt
    
    # CORRECTED: Get recent work history from dailyrecords collection
    async def _get_recent_work_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent work updates for context from correct collections"""
        week_ago = datetime.now() - timedelta(days=7)
        week_ago_str = week_ago.strftime('%Y-%m-%d')
        
        daily_records_collection = self.db["dailyrecords"]  # Query actual data location
        temp_updates_collection = self.db[Config.TEMP_WORK_UPDATES_COLLECTION]
        
        # Get from dailyrecords (permanent storage)
        daily_records_query = {
            "internId": user_id,
            "date": {"$gte": week_ago_str}
        }
        
        daily_records_cursor = daily_records_collection.find(daily_records_query)
        daily_records = await daily_records_cursor.to_list(None)
        
        # Get from temp collection
        temp_query = {"internId": user_id}
        temp_cursor = temp_updates_collection.find(temp_query)
        temp_updates = await temp_cursor.to_list(None)
        
        # Filter temp updates by date
        filtered_temp = []
        for doc in temp_updates:
            timestamp = self._extract_timestamp(doc)
            if timestamp and timestamp > week_ago:
                filtered_temp.append(doc)
        
        # Combine and sort
        all_work_updates = daily_records + filtered_temp
        all_work_updates.sort(key=lambda x: self._extract_timestamp(x) or datetime.min, reverse=True)
        
        logger.info(f"Recent work history: Found {len(daily_records)} from dailyrecords, {len(filtered_temp)} from temp for user {user_id}")
        
        return all_work_updates[:10]
    
    async def generate_followup_questions(self, user_id: str, work_update_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """Legacy method - now uses quality-aware processing"""
        try:
            if not work_update_data:
                return self._get_default_questions()
            
            work_description = work_update_data.get('description', '')
            if not work_description:
                return self._get_default_questions()
            
            result = await self.process_work_update_with_quality_check(
                work_description, 
                user_id
            )
            
            if result.get("followup_data"):
                return result["followup_data"]["questions"]
            else:
                return self._get_default_questions()
                
        except Exception as e:
            logger.error(f"Error in legacy generate_followup_questions: {e}")
            return self._get_default_questions()
    
    def _extract_timestamp(self, doc: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from document - handles both temp and dailyrecords formats"""
        timestamp = None
        if 'submittedAt' in doc:
            timestamp = doc['submittedAt']
        elif 'timestamp' in doc:
            timestamp = doc['timestamp']
        elif 'date' in doc:
            date_field = doc['date']
            if isinstance(date_field, datetime):
                timestamp = date_field
            elif isinstance(date_field, str):
                try:
                    # For dailyrecords, date is stored as string YYYY-MM-DD
                    # Convert to datetime for consistent sorting
                    timestamp = parser.parse(date_field + ' 12:00:00')  # Add time for proper sorting
                except Exception:
                    pass
        return timestamp
    
    def _build_current_work_context(self, work_data: Dict[str, Any]) -> str:
        """Build context string from current work update"""
        context_lines = ["CURRENT WORK UPDATE:"]
        
        description = work_data.get('description', '').strip()
        if description:
            context_lines.append(f"Work Description: {description}")
        
        challenges = work_data.get('challenges', '').strip() if work_data.get('challenges') else None
        if challenges:
            context_lines.append(f"Challenges Today: {challenges}")
        
        context_lines.append("---")
        return '\n'.join(context_lines)
    
    def _build_work_history_context(self, docs: List[Dict[str, Any]]) -> str:
        """Build context string from work update history"""
        context_lines = ["RECENT WORK HISTORY:"]
        
        for doc in docs:
            date_time = self._extract_timestamp(doc)
            description = doc.get('description', '').strip() or doc.get('task', '').strip()
            challenges = doc.get('challenges', '').strip() or doc.get('progress', '').strip()
            plans = doc.get('plans', '').strip() or doc.get('blockers', '').strip()
            
            date_str = date_time.strftime('%Y-%m-%d') if date_time else 'Unknown'
            
            context_lines.append(f"Date: {date_str}")
            if description:
                context_lines.append(f"Work: {description}")
            if challenges:
                context_lines.append(f"Challenges: {challenges}")
            if plans:
                context_lines.append(f"Plans: {plans}")
            context_lines.append("---")
        
        return '\n'.join(context_lines)
    
    def _build_ai_prompt(self, current_context: str, history_context: str, recent_docs: List[Dict[str, Any]]) -> str:
        """Build AI prompt for question generation - SAME FOR ALL PROVIDERS"""
        
        today_work_update = current_context
        yesterday_plans = self._extract_yesterday_plans_from_recent_docs(recent_docs)
        current_challenges = self._extract_current_challenges(current_context)
        seven_day_history = history_context

        prompt = f"""You're helping a supervisor create simple, easy-to-answer follow-up questions for an intern's daily work update.

**Today's Work:** {today_work_update}
**What They Planned (from yesterday):** {yesterday_plans}
**Current Challenges:** {current_challenges}
**Recent Work History:** {seven_day_history}

Generate exactly 3 simple questions that:
1. Are easy to answer with 1-2 sentences
2. Sound friendly and conversational to understand progress without being demanding
3. Focus on today's work specifically 
4. When says they completed a task,ask them to describe the steps they followed in a general but specific-enough way, so we can understand how the work was approached and verify it was actually done
7. If {yesterday_plans} exists verify {today_work_update} matches {yesterday_plans} naturally .

Avoid questions about:
- Feelings or emotions
- Complex technical details
- Long explanations

Format your response as:
1. [First simple question] 
2. [Second simple question]
3. [Third simple question]"""

        return prompt
    
    def _extract_yesterday_plans_from_recent_docs(self, recent_docs: List[Dict[str, Any]]) -> str:
        """Extract yesterday's plans from the most recent work update that has plans"""
        if not recent_docs:
            return "No previous plans found"
        
        yesterday = datetime.now().date() - timedelta(days=1)
        
        for doc in recent_docs:
            timestamp = self._extract_timestamp(doc)
            if timestamp and timestamp.date() == yesterday:
                plans = doc.get('plans', '').strip() or doc.get('blockers', '').strip()
                if plans:
                    return plans
        
        today = datetime.now().date()
        
        for doc in recent_docs:
            timestamp = self._extract_timestamp(doc)
            if timestamp and timestamp.date() == today:
                continue
                
            plans = doc.get('plans', '').strip() or doc.get('blockers', '').strip()
            if plans:
                return plans
        
        return "No previous plans found"
    
    def _extract_current_challenges(self, current_context: str) -> str:
        """Extract current challenges from current work context"""
        lines = current_context.split('\n')
        challenges = "No challenges mentioned"
        
        for line in lines:
            if line.strip().startswith('Challenges Today:'):
                challenges = line.replace('Challenges Today:', '').strip()
                break
        
        return challenges
    
    def _parse_questions_from_response(self, response: str) -> List[str]:
        """Parse questions from AI response - WORKS FOR ALL PROVIDERS"""
        questions = []
        
        lines = response.split('\n')
        
        for line in lines:
            trimmed = line.strip()
            if re.match(r'^\d+[.\)]\s*', trimmed):
                question = re.sub(r'^\d+[.\)]\s*', '', trimmed).strip()
                question = re.sub(r'\*\*.*?\*\*:\s*', '', question)
                if question and len(question) > 10:
                    questions.append(question)
        
        if len(questions) < 3:
            for line in lines:
                trimmed = line.strip()
                if not trimmed or trimmed.startswith('#') or trimmed.startswith('**') and not trimmed.endswith('?'):
                    continue
                
                if '?' in trimmed and len(trimmed) > 15:
                    question = re.sub(r'^\d+[.\)]\s*', '', trimmed)
                    question = re.sub(r'\*\*.*?\*\*:\s*', '', question)
                    question = question.strip()
                    
                    if question and not any(q.lower() in question.lower() for q in questions):
                        questions.append(question)
                        
                        if len(questions) >= 3:
                            break
        
        if len(questions) > 3:
            questions = questions[:3]
        elif len(questions) < 3:
            defaults = self._get_default_questions()
            while len(questions) < 3 and len(questions) < len(defaults):
                questions.append(defaults[len(questions)])
        
        return questions
    
    def _get_default_questions(self) -> List[str]:
        """Default questions when AI generation fails or providers are exhausted"""
        return [
            "What specific steps did you take to complete this task?",
            "Did you encounter any technical issues or blockers while working?",
            "What will you focus on next in this project?"
        ]
    
    # Keep existing session management methods
    async def save_followup_session(self, user_id: str, questions: List[str]) -> str:
        """Save follow-up session to MongoDB"""
        try:
            session_id = f"{user_id}_{uuid.uuid4().hex}"
            
            followup_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
            
            session_doc = {
                "_id": session_id,
                "userId": user_id,
                "questions": questions,
                "answers": [""] * len(questions),
                "status": SessionStatus.PENDING,
                "createdAt": datetime.now(),
                "completedAt": None
            }
            
            await followup_collection.replace_one(
                {"_id": session_id}, 
                session_doc, 
                upsert=True
            )
            
            logger.info(f"Follow-up session saved with ID: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to save follow-up session: {e}")
            raise Exception(f"Failed to save follow-up session: {e}")
    
    async def update_followup_answers(self, session_id: str, answers: List[str]) -> None:
        """Update answers for a follow-up session"""
        try:
            followup_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
            
            update_doc = {
                "answers": answers,
                "status": SessionStatus.COMPLETED,
                "completedAt": datetime.now()
            }
            
            result = await followup_collection.update_one(
                {"_id": session_id},
                {"$set": update_doc}
            )
            
            if result.modified_count == 0:
                raise Exception(f"Session {session_id} not found")
            
            logger.info(f"Follow-up answers updated for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to update follow-up answers: {e}")
            raise Exception(f"Failed to update follow-up answers: {e}")
    
    async def get_pending_followup_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get pending follow-up session for user"""
        try:
            followup_collection = self.db[Config.FOLLOWUP_SESSIONS_COLLECTION]
            
            query = {
                "$or": [{"userId": user_id}, {"internId": user_id}],
                "status": SessionStatus.PENDING
            }
            
            cursor = followup_collection.find(query).sort("createdAt", DESCENDING).limit(1)
            sessions = await cursor.to_list(1)
            
            if sessions:
                session = sessions[0]
                session_id = session["_id"]
                logger.info(f"Found pending session: {session_id}")
                
                result = {"sessionId": session_id}
                result.update(session)
                return result
            
            logger.info(f"No pending sessions found for user: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting pending follow-up session: {e}")
            return None