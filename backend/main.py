# from dotenv import load_dotenv
# load_dotenv()  # Must be first

# import uuid
# from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# import logging
# from typing import List
# from datetime import datetime, timedelta
# from bson import ObjectId
# import asyncio
# import os
# from config import Config

# from database import (
#     connect_to_mongo, close_mongo_connection, get_database, get_work_update_data,
#     create_temp_work_update, get_temp_work_update, delete_temp_work_update,
#     cleanup_abandoned_temp_updates, get_database_stats, verify_ttl_index
# )
# from ai_service import AIFollowupService
# from rate_limiter import initialize_rate_limiters, get_followup_rate_limiter, get_weekly_report_rate_limiter
# from quality_score import initialize_quality_scorer, get_quality_scorer
# from models import (
#     GenerateQuestionsRequest, GenerateQuestionsResponse, 
#     FollowupAnswersUpdate, AnalysisResponse, TestAIResponse, 
#     ErrorResponse, WorkUpdate, WorkUpdateCreate, FollowupSession, SessionStatus, WorkStatus,
#     QualityAnalysisRequest, QualityAnalysisResponse, WeeklyReportRequest, WeeklyReportResponse,
#     SystemHealthResponse, RateLimiterStatusResponse, CleanupStatusResponse
# )

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Global cleanup task
# cleanup_task = None

# async def scheduled_cleanup_task():
#     """Background task for cleanup (backup to TTL)"""
#     while True:
#         try:
#             logger.info("Running scheduled cleanup (backup to TTL)...")
            
#             ttl_working = await verify_ttl_index()
#             result = await cleanup_abandoned_temp_updates(25 if ttl_working else 24)
            
#             deleted_temp = result.get("deleted_temp_updates", 0)
#             deleted_sessions = result.get("deleted_sessions", 0)
            
#             if deleted_temp > 0 or deleted_sessions > 0:
#                 cleanup_type = "backup" if ttl_working else "primary"
#                 logger.info(f"Scheduled {cleanup_type} cleanup: Removed {deleted_temp} temp updates and {deleted_sessions} sessions")
#             else:
#                 status = "TTL working properly" if ttl_working else "No items found"
#                 logger.info(f"Scheduled cleanup: {status}")
                
#         except Exception as e:
#             logger.error(f"Error in scheduled cleanup: {e}")
        
#         await asyncio.sleep(3600)  # Wait 1 hour

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan manager"""
#     global cleanup_task
    
#     # Startup
#     try:
#         Config.validate_config_simplified()
#         await connect_to_mongo()
        
#         # Initialize rate limiters and quality scorer
#         initialize_rate_limiters()
#         initialize_quality_scorer()
        
#         # Verify TTL index
#         ttl_status = await verify_ttl_index()
#         if ttl_status:
#             logger.info("✅ TTL index verified - automatic cleanup is active")
#         else:
#             logger.warning("⚠️ TTL index not found - relying on manual cleanup")
        
#         # Start background cleanup task
#         cleanup_task = asyncio.create_task(scheduled_cleanup_task())
#         logger.info("Background cleanup task started")
        
#         # Log API key configuration
#         key_summary = Config.get_api_key_summary()
#         logger.info(f"API Keys configured: {key_summary['followup_keys']} followup, 1 weekly report")
        
#         logger.info("Application started successfully with user_id input field")
        
#     except Exception as e:
#         logger.error(f"Failed to start application: {e}")
#         raise
    
#     yield
    
#     # Shutdown
#     if cleanup_task:
#         cleanup_task.cancel()
#         try:
#             await cleanup_task
#         except asyncio.CancelledError:
#             logger.info("Background cleanup task cancelled")
    
#     await close_mongo_connection()
#     logger.info("Application shutdown complete")

# # Create FastAPI app
# app = FastAPI(
#     title="Intern Management AI Service - User ID Input Field",
#     description="AI-powered follow-up generation with quality scoring - Users provide their ID in requests",
#     version="2.3.0",
#     lifespan=lifespan
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE"],  
#     allow_headers=["*"],
# )

# # Dependency to get AI service
# async def get_ai_service() -> AIFollowupService:
#     """Get AI service instance"""
#     try:
#         return AIFollowupService()
#     except Exception as e:
#         logger.error(f"Failed to initialize AI service: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"AI service initialization failed: {str(e)}"
#         )

# @app.get("/")
# async def root():
#     """Root endpoint"""
#     ttl_status = await verify_ttl_index()
#     return {
#         "message": "Intern Management AI Service - User ID Input Field",
#         "version": "2.3.0",
#         "status": "running",
#         "features": {
#             "quality_scoring": "heuristic_based",
#             "multiple_api_keys": "4_followup_1_weekly",
#             "rate_limiting": "enabled",
#             "fallback_questions": "available",
#             "authentication": "user_id_in_request_field",
#             "ttl_cleanup": "active" if ttl_status else "manual_only"
#         },
#         "cleanup_task_status": "running" if cleanup_task and not cleanup_task.done() else "stopped",
#         "usage": {
#             "method": "Include user_id field in all requests",
#             "example_work_update": {
#                 "user_id": "intern123",
#                 "stack": "Backend Development",
#                 "task": "Implemented user authentication API endpoints",
#                 "progress": "Completed OAuth integration and JWT token handling",
#                 "blockers": "Need to review security best practices with senior dev",
#                 "status": "working"
#             },
#             "example_followup_start": {
#                 "user_id": "intern123"
#             }
#         }
#     }

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     try:
#         db = get_database()
#         await db.command("ping")
        
#         ttl_working = await verify_ttl_index()
        
#         followup_limiter = get_followup_rate_limiter()
#         weekly_limiter = get_weekly_report_rate_limiter()
        
#         followup_stats = await followup_limiter.get_stats_summary()
#         weekly_stats = await weekly_limiter.get_stats_summary()
        
#         return {
#             "status": "healthy",
#             "database": "connected",
#             "ttl_index": "active" if ttl_working else "not_found",
#             "automatic_cleanup": "enabled" if ttl_working else "disabled",
#             "cleanup_task_running": cleanup_task and not cleanup_task.done(),
#             "quality_scoring": "enabled",
#             "rate_limiters": {
#                 "followup_keys": followup_stats["total_keys"],
#                 "weekly_keys": weekly_stats["total_keys"],
#                 "total_calls_recorded": followup_stats["total_calls_recorded"] + weekly_stats["total_calls_recorded"]
#             },
#             "authentication": {
#                 "method": "user_id_in_request_field",
#                 "auth_ready": True
#             },
#             "timestamp": datetime.now().isoformat()
#         }
#     except Exception as e:
#         logger.error(f"Health check failed: {e}")
#         return {
#             "status": "unhealthy",
#             "error": str(e),
#             "timestamp": datetime.now().isoformat()
#         }

# # Work Update Creation - Main Entry Point
# @app.post("/api/work-updates")
# async def create_work_update(
#     work_update: WorkUpdateCreate,
#     ai_service: AIFollowupService = Depends(get_ai_service)
# ):
#     """
#     Create work update with automatic quality scoring and intelligent follow-up decision
    
#     User provides: user_id, stack, task, progress (challenges), blockers (plans), status
#     System calculates quality score and decides if follow-up is needed
#     """
#     try:
#         # Extract user ID from request body
#         intern_id = work_update.user_id.strip()
        
#         # Validate work status and task description
#         if work_update.status in [WorkStatus.WORKING, WorkStatus.WFH]:
#             if not work_update.task or not work_update.task.strip():
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Task description is required when status is 'working' or 'wfh'"
#                 )
        
#         db = get_database()
#         today_date = datetime.now().strftime('%Y-%m-%d')
        
#         logger.info(f"Processing work update for user: {intern_id}, status: {work_update.status}")
        
#         if work_update.status == WorkStatus.LEAVE:
#             # ON LEAVE: Save directly to LogBook's DailyRecord collection
#             daily_records = db["dailyrecords"]
#             date_based_query = {"internId": ObjectId(intern_id), "date": today_date}
#             existing_record = await daily_records.find_one(date_based_query)

#             record_dict = {
#                 "internId": ObjectId(intern_id),
#                 "date": today_date,
#                 "stack": work_update.stack,
#                 "task": work_update.task or "On Leave",
#                 "progress": "On Leave",
#                 "blockers": "On Leave",
#                 "status": "leave"
#             }

#             if existing_record:
#                 await daily_records.replace_one({"_id": existing_record["_id"]}, record_dict)
#                 record_id = str(existing_record["_id"])
#                 is_override = True
#             else:
#                 result = await daily_records.insert_one(record_dict)
#                 record_id = str(result.inserted_id)
#                 is_override = False

#             logger.info(f"LEAVE record saved to LogBook for user {intern_id}: {record_id}")
            
#             return {
#                 "success": True,
#                 "message": "Leave status saved successfully to LogBook",
#                 "user_id": intern_id,
#                 "recordId": record_id,
#                 "isOverride": is_override,
#                 "redirectToFollowup": False,
#                 "isOnLeave": True,
#                 "qualityScore": None,
#                 "status": "completed"
#             }
        
#         else:
#             # WORKING/WFH: Apply quality scoring and intelligent follow-up decision
#             logger.info(f"Applying quality scoring to work update for user {intern_id}")
            
#             # Process work update with quality scoring
#             quality_result = await ai_service.process_work_update_with_quality_check(
#                 work_update.task,
#                 intern_id,
#                 today_date
#             )
            
#             quality_score = quality_result.get("quality_score", 0)
#             needs_followup = quality_result.get("needs_followup", False)
#             fallback_used = quality_result.get("fallback_used", False)
            
#             logger.info(f"Quality scoring result for user {intern_id}: score={quality_score}, needs_followup={needs_followup}")
            
#             if needs_followup:
#                 # Low quality - create temporary work update and prepare for follow-up
#                 update_dict = {
#                     "internId": intern_id,
#                     "date": today_date,
#                     "stack": work_update.stack,
#                     "task": work_update.task,
#                     "progress": work_update.progress,
#                     "blockers": work_update.blockers,
#                     "status": work_update.status,
#                     "submittedAt": datetime.now(),
#                     "followupCompleted": False,
#                     "temp_status": "pending_followup",
#                     "qualityScore": quality_score,
#                     "qualityDetails": quality_result.get("score_details", {})
#                 }

#                 temp_work_update_id = await create_temp_work_update(update_dict)
                
#                 return {
#                     "success": True,
#                     "message": f"Work update requires follow-up (Quality Score: {quality_score}/10). Please complete AI follow-up to finalize.",
#                     "user_id": intern_id,
#                     "tempWorkUpdateId": temp_work_update_id,
#                     "redirectToFollowup": True,
#                     "isOnLeave": False,
#                     "qualityScore": quality_score,
#                     "needsFollowup": needs_followup,
#                     "fallbackUsed": fallback_used,
#                     "followupType": quality_result.get("followup_data", {}).get("type", "unknown"),
#                     "ttl_expiry": "24 hours from now",
#                     "status": "pending_followup",
#                     "next_step": "Call /api/followups/start to begin follow-up questions"
#                 }
#             else:
#                 # High quality - save directly to LogBook
#                 daily_records = db["dailyrecords"]
#                 date_based_query = {"internId": ObjectId(intern_id), "date": today_date}
#                 existing_record = await daily_records.find_one(date_based_query)

#                 record_dict = {
#                     "internId": ObjectId(intern_id),
#                     "date": today_date,
#                     "stack": work_update.stack,
#                     "task": work_update.task,
#                     "progress": work_update.progress,
#                     "blockers": work_update.blockers,
#                     "status": work_update.status,
#                     "qualityScore": quality_score,
#                     "followupSkipped": True,
#                     "skipReason": "high_quality"
#                 }

#                 if existing_record:
#                     await daily_records.replace_one({"_id": existing_record["_id"]}, record_dict)
#                     record_id = str(existing_record["_id"])
#                     is_override = True
#                 else:
#                     result = await daily_records.insert_one(record_dict)
#                     record_id = str(result.inserted_id)
#                     is_override = False

#                 logger.info(f"High quality work update saved directly to LogBook for user {intern_id}: {record_id}")
                
#                 return {
#                     "success": True,
#                     "message": f"High quality work update (Score: {quality_score}/10) saved directly to LogBook. No follow-up needed.",
#                     "user_id": intern_id,
#                     "recordId": record_id,
#                     "isOverride": is_override,
#                     "redirectToFollowup": False,
#                     "isOnLeave": False,
#                     "qualityScore": quality_score,
#                     "needsFollowup": False,
#                     "followupSkipped": True,
#                     "status": "completed"
#                 }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error creating work update: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to create work update: {str(e)}"
#         )

# # Start Follow-up Session
# @app.post("/api/followups/start")
# async def start_followup_session(
#     request: GenerateQuestionsRequest,
#     ai_service: AIFollowupService = Depends(get_ai_service)
# ):
#     """Start follow-up session using temporary work update data"""
#     try:
#         intern_id = request.user_id.strip()
        
#         db = get_database()
#         followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]

#         # Find the most recent temp work update for this user
#         temp_collection = db[Config.TEMP_WORK_UPDATES_COLLECTION]
#         temp_work_update = await temp_collection.find_one(
#             {"internId": intern_id, "temp_status": "pending_followup"},
#             sort=[("submittedAt", -1)]
#         )
        
#         if not temp_work_update:
#             raise HTTPException(
#                 status_code=404, 
#                 detail="No pending temporary work update found. Either no work update was submitted or it was auto-deleted after 24 hours."
#             )

#         temp_work_update_id = str(temp_work_update["_id"])
#         today_date = datetime.now().strftime('%Y-%m-%d')
#         session_date_id = f"{intern_id}_{uuid.uuid4().hex}"

#         # Re-run quality scoring to get appropriate questions
#         task_description = temp_work_update.get("task", "")
#         quality_result = await ai_service.process_work_update_with_quality_check(
#             task_description,
#             intern_id,
#             today_date
#         )
        
#         # Get questions from quality result
#         followup_data = quality_result.get("followup_data", {})
#         questions = followup_data.get("questions", ai_service._get_default_questions())
#         question_type = followup_data.get("type", "fallback")
        
#         session_doc = {
#             "_id": session_date_id,
#             "internId": intern_id,
#             "tempWorkUpdateId": temp_work_update_id, 
#             "session_date": today_date,
#             "questions": questions,
#             "answers": [""] * len(questions),
#             "status": SessionStatus.PENDING,
#             "createdAt": datetime.now(),
#             "completedAt": None,
#             "questionType": question_type,
#             "qualityScore": quality_result.get("quality_score", 0),
#             "fallbackUsed": quality_result.get("fallback_used", False)
#         }
#         await followup_collection.replace_one({"_id": session_date_id}, session_doc, upsert=True)

#         logger.info(f"Follow-up session started for user {intern_id} (type: {question_type}, score: {quality_result.get('quality_score')})")

#         return {
#             "success": True,
#             "message": "AI follow-up session started successfully",
#             "user_id": intern_id,
#             "sessionId": session_date_id,
#             "tempWorkUpdateId": temp_work_update_id,
#             "questions": questions,
#             "questionType": question_type,
#             "qualityScore": quality_result.get("quality_score", 0),
#             "fallbackUsed": quality_result.get("fallback_used", False),
#             "reminder": "Complete within 24 hours before auto-deletion",
#             "next_step": f"Submit answers using PUT /api/followup/{session_date_id}/complete"
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error starting follow-up session: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start follow-up session: {str(e)}"
#         )

# # Complete Follow-up Session
# @app.put("/api/followup/{session_id}/complete")
# async def complete_followup_session(
#     session_id: str,
#     answers_update: FollowupAnswersUpdate
# ):
#     """Complete follow-up session and move temp work update to LogBook"""
#     try:
#         intern_id = answers_update.user_id.strip()
        
#         # Validate all answers provided
#         if not answers_update.answers or len(answers_update.answers) != 3:
#             raise HTTPException(
#                 status_code=400,
#                 detail="All 3 questions must be answered"
#             )
        
#         if any(not answer.strip() for answer in answers_update.answers):
#             raise HTTPException(
#                 status_code=400,
#                 detail="All questions must have non-empty answers"
#             )
        
#         db = get_database()
#         followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
#         daily_records = db["dailyrecords"]
        
#         # Get the follow-up session and verify ownership
#         session = await followup_collection.find_one({"_id": session_id})
#         if not session:
#             raise HTTPException(status_code=404, detail="Follow-up session not found")

#         if str(session.get("internId")) != str(intern_id):
#             raise HTTPException(
#                 status_code=403,
#                 detail="Access denied - session belongs to different user"
#             )

#         # Get the temporary work update
#         temp_work_update = await get_temp_work_update(session["tempWorkUpdateId"])
#         if not temp_work_update:
#             raise HTTPException(
#                 status_code=404, 
#                 detail="Temporary work update not found (may have been auto-deleted due to TTL expiry)"
#             )

#         # Complete the follow-up session
#         session_update = {
#             "answers": answers_update.answers,
#             "status": SessionStatus.COMPLETED,
#             "completedAt": datetime.now()
#         }
        
#         await followup_collection.update_one(
#             {"_id": session_id},
#             {"$set": session_update}
#         )

#         # Move temp work update to LogBook's DailyRecord collection
#         daily_record = {
#             "internId": ObjectId(intern_id),
#             "date": temp_work_update["date"],
#             "stack": temp_work_update["stack"],
#             "task": temp_work_update["task"],
#             "progress": temp_work_update.get("progress", "No challenges faced"),
#             "blockers": temp_work_update.get("blockers", "No specific plans"),
#             "status": temp_work_update["status"],
#             "qualityScore": temp_work_update.get("qualityScore", 0),
#             "followupCompleted": True,
#             "questionType": session.get("questionType", "unknown"),
#             "followupAnswers": answers_update.answers
#         }

#         # Check for existing record (override logic)
#         existing_record = await daily_records.find_one({
#             "internId": ObjectId(intern_id),
#             "date": temp_work_update["date"]
#         })
        
#         if existing_record:
#             await daily_records.replace_one({"_id": existing_record["_id"]}, daily_record)
#             final_record_id = str(existing_record["_id"])
#             logger.info(f"Updated existing LogBook record for user {intern_id}: {final_record_id}")
#         else:
#             result = await daily_records.insert_one(daily_record)
#             final_record_id = str(result.inserted_id)
#             logger.info(f"Created new LogBook record for user {intern_id}: {final_record_id}")

#         # Update session with final record ID
#         await followup_collection.update_one(
#             {"_id": session_id},
#             {"$set": {"dailyRecordId": final_record_id}}
#         )

#         # Delete temp work update
#         await delete_temp_work_update(session["tempWorkUpdateId"])

#         logger.info(f"AI follow-up completed for user {intern_id}, LogBook record finalized: {final_record_id}")
        
#         return {
#             "success": True,
#             "message": "AI follow-up completed successfully. Work update saved to LogBook system.",
#             "user_id": intern_id,
#             "sessionId": session_id,
#             "dailyRecordId": final_record_id,
#             "workUpdateCompleted": True,
#             "qualityScore": temp_work_update.get("qualityScore", 0),
#             "status": "completed",
#             "note": "Work update moved to LogBook DailyRecord collection"
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Failed to complete follow-up: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to complete follow-up: {str(e)}"
#         )

# # Quality Score Analysis
# @app.post("/api/quality/analyze", response_model=QualityAnalysisResponse)
# async def analyze_work_quality(request: QualityAnalysisRequest):
#     """Analyze work description quality without creating work update"""
#     try:
#         quality_scorer = get_quality_scorer()
        
#         # Calculate quality score
#         needs_followup, score_details = await quality_scorer.should_trigger_followup(
#             request.work_description, 
#             request.user_id
#         )
        
#         return QualityAnalysisResponse(
#             user_id=request.user_id,
#             quality_score=score_details.get("quality_score", 0),
#             needs_followup=needs_followup,
#             analysis={
#                 "word_count": score_details.get("word_count", 0),
#                 "keyword_found": score_details.get("keyword_found", False),
#                 "sentiment_label": score_details.get("sentiment_label", "neutral"),
#                 "sentiment_polarity": score_details.get("sentiment_polarity", 0),
#                 "is_repetition": score_details.get("is_repetition", False),
#                 "has_structure": score_details.get("has_structure", False),
#                 "flagged": score_details.get("flagged", False),
#                 "flag_reasons": score_details.get("flag_reasons", [])
#             },
#             recommendation="Follow-up recommended" if needs_followup else "Good quality, no follow-up needed",
#             threshold=Config.QUALITY_SCORE_THRESHOLD
#         )
        
#     except Exception as e:
#         logger.error(f"Error analyzing work quality: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to analyze work quality: {str(e)}"
#         )

# # Weekly Report Generation
# @app.post("/api/reports/weekly", response_model=WeeklyReportResponse)
# async def generate_weekly_report(
#     request: WeeklyReportRequest,
#     ai_service: AIFollowupService = Depends(get_ai_service)
# ):
#     """Generate AI-powered weekly report for a user"""
#     try:
#         # Parse dates or use default (last 7 days)
#         if request.start_date and request.end_date:
#             start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
#             end_dt = datetime.strptime(request.end_date, '%Y-%m-%d')
#         else:
#             end_dt = datetime.now()
#             start_dt = end_dt - timedelta(days=7)
        
#         logger.info(f"Generating weekly report for user {request.user_id} from {start_dt.date()} to {end_dt.date()}")
        
#         # Generate the report using dedicated API key
#         report_result = await ai_service.generate_weekly_report(request.user_id, start_dt, end_dt)
        
#         if report_result.get("success"):
#             return WeeklyReportResponse(
#                 success=True,
#                 user_id=request.user_id,
#                 report=report_result["report"],
#                 metadata={
#                     "user_id": request.user_id,
#                     "date_range": {
#                         "start": start_dt.strftime('%Y-%m-%d'),
#                         "end": end_dt.strftime('%Y-%m-%d')
#                     },
#                     "data_summary": report_result.get("data_summary", {}),
#                     "generated_at": datetime.now().isoformat(),
#                     "api_key_type": "dedicated_weekly_report_key"
#                 }
#             )
#         else:
#             return WeeklyReportResponse(
#                 success=False,
#                 user_id=request.user_id,
#                 message=report_result.get("message", "Failed to generate report"),
#                 metadata={
#                     "user_id": request.user_id,
#                     "date_range": {
#                         "start": start_dt.strftime('%Y-%m-%d'),
#                         "end": end_dt.strftime('%Y-%m-%d')
#                     },
#                     "generated_at": datetime.now().isoformat()
#                 }
#             )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error generating weekly report: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to generate weekly report: {str(e)}"
#         )

# # Get Follow-up Sessions for User
# @app.post("/api/followup-sessions/list")
# async def get_followup_sessions(
#     request: GenerateQuestionsRequest,
#     limit: int = 50,
#     skip: int = 0
# ):
#     """Get follow-up sessions for specified user"""
#     try:
#         intern_id = request.user_id.strip()
        
#         db = get_database()
#         followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
#         cursor = followup_collection.find(
#             {"internId": intern_id}
#         ).sort("createdAt", -1).skip(skip).limit(limit)
        
#         sessions = await cursor.to_list(length=limit)
        
#         # Convert ObjectId to string for JSON serialization
#         for session in sessions:
#             if "_id" in session:
#                 session["id"] = str(session["_id"])
#                 session["sessionId"] = session["_id"]
#                 del session["_id"]
        
#         return {
#             "success": True,
#             "user_id": intern_id,
#             "sessions": sessions,
#             "count": len(sessions),
#             "limit": limit,
#             "skip": skip
#         }
        
#     except Exception as e:
#         logger.error(f"Error getting followup sessions: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get followup sessions: {str(e)}"
#         )

# # System Status Endpoints
# @app.get("/api/rate-limiters/status", response_model=RateLimiterStatusResponse)
# async def get_rate_limiter_status():
#     """Get current status of all rate limiters"""
#     try:
#         followup_limiter = get_followup_rate_limiter()
#         weekly_limiter = get_weekly_report_rate_limiter()
        
#         followup_status = await followup_limiter.get_rate_limit_status()
#         weekly_status = await weekly_limiter.get_rate_limit_status()
        
#         followup_stats = await followup_limiter.get_stats_summary()
#         weekly_stats = await weekly_limiter.get_stats_summary()
        
#         return RateLimiterStatusResponse(
#             followup_api_keys={
#                 "status": followup_status,
#                 "stats": followup_stats,
#                 "purpose": "Follow-up question generation"
#             },
#             weekly_report_api_key={
#                 "status": weekly_status,
#                 "stats": weekly_stats,
#                 "purpose": "Weekly report generation"
#             },
#             overall={
#                 "total_keys": followup_stats["total_keys"] + weekly_stats["total_keys"],
#                 "total_calls_recorded": followup_stats["total_calls_recorded"] + weekly_stats["total_calls_recorded"],
#                 "rate_limit_per_minute": Config.RATE_LIMIT_PER_MINUTE
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"Error getting rate limiter status: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get rate limiter status: {str(e)}"
#         )

# @app.get("/api/ai/test", response_model=TestAIResponse)
# async def test_ai_connections():
#     """Test all AI API keys and connections"""
#     try:
#         ai_service = AIFollowupService()
#         test_results = await ai_service.test_ai_connection()
        
#         return TestAIResponse(
#             success=test_results.get("summary", {}).get("overall_status") == "healthy",
#             message="AI connection test completed",
#             test_results={
#                 "timestamp": datetime.now().isoformat(),
#                 "test_results": test_results,
#                 "summary": test_results.get("summary", {})
#             }
#         )
        
#     except Exception as e:
#         logger.error(f"AI connection test failed: {e}")
#         return TestAIResponse(
#             success=False,
#             message="AI connection test failed",
#             test_results={
#                 "timestamp": datetime.now().isoformat(),
#                 "error": str(e),
#                 "summary": {
#                     "overall_status": "error",
#                     "fallback_available": True
#                 }
#             }
#         )

# @app.get("/stats")
# async def get_stats():
#     """Get comprehensive database and system statistics"""
#     try:
#         stats = await get_database_stats()
        
#         ttl_status = await verify_ttl_index()
        
#         followup_limiter = get_followup_rate_limiter()
#         weekly_limiter = get_weekly_report_rate_limiter()
        
#         followup_stats = await followup_limiter.get_stats_summary()
#         weekly_stats = await weekly_limiter.get_stats_summary()
        
#         if stats:
#             stats["cleanup_system"] = {
#                 "ttl_index_active": ttl_status,
#                 "manual_task_running": cleanup_task and not cleanup_task.done(),
#                 "cleanup_frequency": "Every 1 hour (backup to TTL)",
#                 "automatic_deletion": "24 hours via TTL index" if ttl_status else "Manual only"
#             }
#             stats["integration"] = {
#                 "logbook_ready": True,
#                 "daily_records_collection": "dailyrecords",
#                 "authentication": "user_id_in_request_field",
#                 "auth_method": "Simple user_id field in JSON requests"
#             }
#             stats["quality_scoring"] = {
#                 "enabled": True,
#                 "threshold": Config.QUALITY_SCORE_THRESHOLD,
#                 "keywords_count": len(Config().QUALITY_KEYWORDS),
#                 "scoring_components": ["word_count", "keywords", "sentiment", "repetition", "structure"]
#             }
#             stats["api_keys"] = {
#                 "followup_keys": followup_stats["total_keys"],
#                 "weekly_report_keys": weekly_stats["total_keys"],
#                 "total_calls_recorded": followup_stats["total_calls_recorded"] + weekly_stats["total_calls_recorded"],
#                 "rate_limit_per_minute": Config.RATE_LIMIT_PER_MINUTE
#             }
        
#         return stats
#     except Exception as e:
#         logger.error(f"Failed to get stats: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get statistics: {str(e)}"
#         )

# @app.delete("/api/temp-work-updates/cleanup")
# async def cleanup_abandoned_temp_updates_endpoint():
#     """Manually trigger cleanup of temporary work updates (backup to TTL)"""
#     try:
#         ttl_active = await verify_ttl_index()
#         result = await cleanup_abandoned_temp_updates(24)
        
#         deleted_temp = result.get("deleted_temp_updates", 0)
#         deleted_sessions = result.get("deleted_sessions", 0)
        
#         return {
#             "success": True,
#             "message": f"Manual cleanup completed. Cleaned up {deleted_temp} temp updates and {deleted_sessions} sessions",
#             "deleted_temp_updates": deleted_temp,
#             "deleted_sessions": deleted_sessions,
#             "ttl_status": "active" if ttl_active else "inactive",
#             "note": "TTL index handles most cleanup automatically" if ttl_active else "Manual cleanup is primary method"
#         }
        
#     except Exception as e:
#         logger.error(f"Error during manual cleanup: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to cleanup: {str(e)}"
#         )

# @app.get("/api/cleanup/status", response_model=CleanupStatusResponse)
# async def get_cleanup_status():
#     """Get detailed status of the TTL and cleanup system"""
#     ttl_active = await verify_ttl_index()
    
#     return CleanupStatusResponse(
#         ttl_index={
#             "active": ttl_active,
#             "expiry_time": "24 hours",
#             "status": "Automatic deletion enabled" if ttl_active else "TTL index not found"
#         },
#         manual_cleanup={
#             "task_running": cleanup_task and not cleanup_task.done(),
#             "frequency": "Every 1 hour",
#             "purpose": "Backup to TTL + Session cleanup",
#             "age_threshold": "24+ hours"
#         },
#         recommendation="TTL handles most cleanup automatically" if ttl_active else "Relying on manual cleanup only"
#     )

# # Error handlers
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc: HTTPException):
#     """Handle HTTP exceptions"""
#     return {
#         "error": "HTTP_ERROR",
#         "message": exc.detail,
#         "status_code": exc.status_code,
#         "success": False
#     }

# @app.exception_handler(Exception)
# async def general_exception_handler(request, exc: Exception):
#     """Handle general exceptions"""
#     logger.error(f"Unhandled exception: {exc}")
#     return {
#         "error": "INTERNAL_ERROR", 
#         "message": "An internal error occurred",
#         "details": str(exc) if Config.DEBUG else None,
#         "success": False
#     }

# if __name__ == "__main__":
#     import uvicorn
    
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=Config.DEBUG,
#         log_level="info"
#     )


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Or specify ["http://localhost:5500"] etc.
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

from dotenv import load_dotenv
load_dotenv()  # Must be first

import uuid
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
import asyncio
import os
from config import Config

from database import (
    connect_to_mongo, close_mongo_connection, get_database, get_work_update_data,
    create_temp_work_update, get_temp_work_update, delete_temp_work_update,
    cleanup_abandoned_temp_updates, get_database_stats, verify_ttl_index
)
from ai_service import AIFollowupService
from rate_limiter import initialize_rate_limiters, get_followup_rate_limiter, get_weekly_report_rate_limiter
from quality_score import initialize_quality_scorer, get_quality_scorer
from models import (
    GenerateQuestionsRequest, GenerateQuestionsResponse, 
    FollowupAnswersUpdate, AnalysisResponse, TestAIResponse, 
    ErrorResponse, WorkUpdate, WorkUpdateCreate, FollowupSession, SessionStatus, WorkStatus,
    QualityAnalysisRequest, QualityAnalysisResponse, WeeklyReportRequest, WeeklyReportResponse,
    SystemHealthResponse, RateLimiterStatusResponse, CleanupStatusResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global cleanup task
cleanup_task = None

async def scheduled_cleanup_task():
    """Background task for cleanup (backup to TTL)"""
    while True:
        try:
            logger.info("Running scheduled cleanup (backup to TTL)...")
            
            ttl_working = await verify_ttl_index()
            result = await cleanup_abandoned_temp_updates(25 if ttl_working else 24)
            
            deleted_temp = result.get("deleted_temp_updates", 0)
            deleted_sessions = result.get("deleted_sessions", 0)
            
            if deleted_temp > 0 or deleted_sessions > 0:
                cleanup_type = "backup" if ttl_working else "primary"
                logger.info(f"Scheduled {cleanup_type} cleanup: Removed {deleted_temp} temp updates and {deleted_sessions} sessions")
            else:
                status = "TTL working properly" if ttl_working else "No items found"
                logger.info(f"Scheduled cleanup: {status}")
                
        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {e}")
        
        await asyncio.sleep(3600)  # Wait 1 hour

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global cleanup_task
    
    # Startup
    try:
        Config.validate_config_simplified()
        await connect_to_mongo()
        
        # Initialize rate limiters and quality scorer
        initialize_rate_limiters()
        initialize_quality_scorer()
        
        # Verify TTL index
        ttl_status = await verify_ttl_index()
        if ttl_status:
            logger.info("✅ TTL index verified - automatic cleanup is active")
        else:
            logger.warning("⚠️ TTL index not found - relying on manual cleanup")
        
        # Start background cleanup task
        cleanup_task = asyncio.create_task(scheduled_cleanup_task())
        logger.info("Background cleanup task started")
        
        # Log API key configuration
        key_summary = Config.get_api_key_summary()
        logger.info(f"API Keys configured: {key_summary['followup_keys']} followup, 1 weekly report")
        
        logger.info("Application started successfully with user_id input field")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
    
    await close_mongo_connection()
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Intern Management AI Service - User ID Input Field",
    description="AI-powered follow-up generation with quality scoring - Users provide their ID in requests",
    version="2.3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get AI service
async def get_ai_service() -> AIFollowupService:
    """Get AI service instance"""
    try:
        return AIFollowupService()
    except Exception as e:
        logger.error(f"Failed to initialize AI service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI service initialization failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    ttl_status = await verify_ttl_index()
    return {
        "message": "Intern Management AI Service - User ID Input Field",
        "version": "2.3.0",
        "status": "running",
        "features": {
            "quality_scoring": "heuristic_based",
            "multiple_api_keys": "4_followup_1_weekly",
            "rate_limiting": "enabled",
            "fallback_questions": "available",
            "authentication": "user_id_in_request_field",
            "ttl_cleanup": "active" if ttl_status else "manual_only"
        },
        "cleanup_task_status": "running" if cleanup_task and not cleanup_task.done() else "stopped",
        "usage": {
            "method": "Include user_id field in all requests",
            "example_work_update": {
                "user_id": "intern123",
                "stack": "Backend Development",
                "task": "Implemented user authentication API endpoints",
                "progress": "Completed OAuth integration and JWT token handling",
                "blockers": "Need to review security best practices with senior dev",
                "status": "working"
            },
            "example_followup_start": {
                "user_id": "intern123"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        await db.command("ping")
        
        ttl_working = await verify_ttl_index()
        
        followup_limiter = get_followup_rate_limiter()
        weekly_limiter = get_weekly_report_rate_limiter()
        
        followup_stats = await followup_limiter.get_stats_summary()
        weekly_stats = await weekly_limiter.get_stats_summary()
        
        return {
            "status": "healthy",
            "database": "connected",
            "ttl_index": "active" if ttl_working else "not_found",
            "automatic_cleanup": "enabled" if ttl_working else "disabled",
            "cleanup_task_running": cleanup_task and not cleanup_task.done(),
            "quality_scoring": "enabled",
            "rate_limiters": {
                "followup_keys": followup_stats["total_keys"],
                "weekly_keys": weekly_stats["total_keys"],
                "total_calls_recorded": followup_stats["total_calls_recorded"] + weekly_stats["total_calls_recorded"]
            },
            "authentication": {
                "method": "user_id_in_request_field",
                "auth_ready": True
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Work Update Creation - Main Entry Point
@app.post("/api/work-updates")
async def create_work_update(
    work_update: WorkUpdateCreate,
    ai_service: AIFollowupService = Depends(get_ai_service)
):
    """
    Create work update with automatic quality scoring and intelligent follow-up decision
    
    User provides: user_id, stack, task, progress (challenges), blockers (plans), status
    System calculates quality score and decides if follow-up is needed
    """
    try:
        # Extract user ID from request body
        intern_id = work_update.user_id.strip()
        
        # Validate work status and task description
        if work_update.status in [WorkStatus.WORKING, WorkStatus.WFH]:
            if not work_update.task or not work_update.task.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Task description is required when status is 'working' or 'wfh'"
                )
        
        db = get_database()
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Processing work update for user: {intern_id}, status: {work_update.status}")
        
        if work_update.status == WorkStatus.LEAVE:
            # ON LEAVE: Save directly to LogBook's DailyRecord collection
            daily_records = db["dailyrecords"]
            date_based_query = {"internId": intern_id, "date": today_date}  # FIXED: Removed ObjectId()
            existing_record = await daily_records.find_one(date_based_query)

            record_dict = {
                "internId": intern_id,  # FIXED: Removed ObjectId()
                "date": today_date,
                "stack": work_update.stack,
                "task": work_update.task or "On Leave",
                "progress": "On Leave",
                "blockers": "On Leave",
                "status": "leave"
            }

            if existing_record:
                await daily_records.replace_one({"_id": existing_record["_id"]}, record_dict)
                record_id = str(existing_record["_id"])
                is_override = True
            else:
                result = await daily_records.insert_one(record_dict)
                record_id = str(result.inserted_id)
                is_override = False

            logger.info(f"LEAVE record saved to LogBook for user {intern_id}: {record_id}")
            
            return {
                "success": True,
                "message": "Leave status saved successfully to LogBook",
                "user_id": intern_id,
                "recordId": record_id,
                "isOverride": is_override,
                "redirectToFollowup": False,
                "isOnLeave": True,
                "qualityScore": None,
                "status": "completed"
            }
        
        else:
            # WORKING/WFH: Apply quality scoring and intelligent follow-up decision
            logger.info(f"Applying quality scoring to work update for user {intern_id}")
            
            # Process work update with quality scoring
            quality_result = await ai_service.process_work_update_with_quality_check(
                work_update.task,
                intern_id,
                today_date
            )
            
            quality_score = quality_result.get("quality_score", 0)
            needs_followup = quality_result.get("needs_followup", False)
            fallback_used = quality_result.get("fallback_used", False)
            
            logger.info(f"Quality scoring result for user {intern_id}: score={quality_score}, needs_followup={needs_followup}")
            
            if needs_followup:
                # Low quality - create temporary work update and prepare for follow-up
                update_dict = {
                    "internId": intern_id,
                    "date": today_date,
                    "stack": work_update.stack,
                    "task": work_update.task,
                    "progress": work_update.progress,
                    "blockers": work_update.blockers,
                    "status": work_update.status,
                    "submittedAt": datetime.now(),
                    "followupCompleted": False,
                    "temp_status": "pending_followup",
                    "qualityScore": quality_score,
                    "qualityDetails": quality_result.get("score_details", {})
                }

                temp_work_update_id = await create_temp_work_update(update_dict)
                
                return {
                    "success": True,
                    "message": f"Work update requires follow-up (Quality Score: {quality_score}/10). Please complete AI follow-up to finalize.",
                    "user_id": intern_id,
                    "tempWorkUpdateId": temp_work_update_id,
                    "redirectToFollowup": True,
                    "isOnLeave": False,
                    "qualityScore": quality_score,
                    "needsFollowup": needs_followup,
                    "fallbackUsed": fallback_used,
                    "followupType": quality_result.get("followup_data", {}).get("type", "unknown"),
                    "ttl_expiry": "24 hours from now",
                    "status": "pending_followup",
                    "next_step": "Call /api/followups/start to begin follow-up questions"
                }
            else:
                # High quality - save directly to LogBook
                daily_records = db["dailyrecords"]
                date_based_query = {"internId": intern_id, "date": today_date}  # FIXED: Removed ObjectId()
                existing_record = await daily_records.find_one(date_based_query)

                record_dict = {
                    "internId": intern_id,  # FIXED: Removed ObjectId()
                    "date": today_date,
                    "stack": work_update.stack,
                    "task": work_update.task,
                    "progress": work_update.progress,
                    "blockers": work_update.blockers,
                    "status": work_update.status,
                    "qualityScore": quality_score,
                    "followupSkipped": True,
                    "skipReason": "high_quality"
                }

                if existing_record:
                    await daily_records.replace_one({"_id": existing_record["_id"]}, record_dict)
                    record_id = str(existing_record["_id"])
                    is_override = True
                else:
                    result = await daily_records.insert_one(record_dict)
                    record_id = str(result.inserted_id)
                    is_override = False

                logger.info(f"High quality work update saved directly to LogBook for user {intern_id}: {record_id}")
                
                return {
                    "success": True,
                    "message": f"High quality work update (Score: {quality_score}/10) saved directly to LogBook. No follow-up needed.",
                    "user_id": intern_id,
                    "recordId": record_id,
                    "isOverride": is_override,
                    "redirectToFollowup": False,
                    "isOnLeave": False,
                    "qualityScore": quality_score,
                    "needsFollowup": False,
                    "followupSkipped": True,
                    "status": "completed"
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating work update: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create work update: {str(e)}"
        )

# Start Follow-up Session
@app.post("/api/followups/start")
async def start_followup_session(
    request: GenerateQuestionsRequest,
    ai_service: AIFollowupService = Depends(get_ai_service)
):
    """Start follow-up session using temporary work update data"""
    try:
        intern_id = request.user_id.strip()
        
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]

        # Find the most recent temp work update for this user
        temp_collection = db[Config.TEMP_WORK_UPDATES_COLLECTION]
        temp_work_update = await temp_collection.find_one(
            {"internId": intern_id, "temp_status": "pending_followup"},
            sort=[("submittedAt", -1)]
        )
        
        if not temp_work_update:
            raise HTTPException(
                status_code=404, 
                detail="No pending temporary work update found. Either no work update was submitted or it was auto-deleted after 24 hours."
            )

        temp_work_update_id = str(temp_work_update["_id"])
        today_date = datetime.now().strftime('%Y-%m-%d')
        session_date_id = f"{intern_id}_{uuid.uuid4().hex}"

        # Re-run quality scoring to get appropriate questions
        task_description = temp_work_update.get("task", "")
        quality_result = await ai_service.process_work_update_with_quality_check(
            task_description,
            intern_id,
            today_date
        )
        
        # Get questions from quality result
        followup_data = quality_result.get("followup_data", {})
        questions = followup_data.get("questions", ai_service._get_default_questions())
        question_type = followup_data.get("type", "fallback")
        
        session_doc = {
            "_id": session_date_id,
            "internId": intern_id,
            "tempWorkUpdateId": temp_work_update_id, 
            "session_date": today_date,
            "questions": questions,
            "answers": [""] * len(questions),
            "status": SessionStatus.PENDING,
            "createdAt": datetime.now(),
            "completedAt": None,
            "questionType": question_type,
            "qualityScore": quality_result.get("quality_score", 0),
            "fallbackUsed": quality_result.get("fallback_used", False)
        }
        await followup_collection.replace_one({"_id": session_date_id}, session_doc, upsert=True)

        logger.info(f"Follow-up session started for user {intern_id} (type: {question_type}, score: {quality_result.get('quality_score')})")

        return {
            "success": True,
            "message": "AI follow-up session started successfully",
            "user_id": intern_id,
            "sessionId": session_date_id,
            "tempWorkUpdateId": temp_work_update_id,
            "questions": questions,
            "questionType": question_type,
            "qualityScore": quality_result.get("quality_score", 0),
            "fallbackUsed": quality_result.get("fallback_used", False),
            "reminder": "Complete within 24 hours before auto-deletion",
            "next_step": f"Submit answers using PUT /api/followup/{session_date_id}/complete"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting follow-up session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start follow-up session: {str(e)}"
        )

# Complete Follow-up Session
@app.put("/api/followup/{session_id}/complete")
async def complete_followup_session(
    session_id: str,
    answers_update: FollowupAnswersUpdate
):
    """Complete follow-up session and move temp work update to LogBook"""
    try:
        intern_id = answers_update.user_id.strip()
        
        # Validate all answers provided
        if not answers_update.answers or len(answers_update.answers) != 3:
            raise HTTPException(
                status_code=400,
                detail="All 3 questions must be answered"
            )
        
        if any(not answer.strip() for answer in answers_update.answers):
            raise HTTPException(
                status_code=400,
                detail="All questions must have non-empty answers"
            )
        
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        daily_records = db["dailyrecords"]
        
        # Get the follow-up session and verify ownership
        session = await followup_collection.find_one({"_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Follow-up session not found")

        if str(session.get("internId")) != str(intern_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied - session belongs to different user"
            )

        # Get the temporary work update
        temp_work_update = await get_temp_work_update(session["tempWorkUpdateId"])
        if not temp_work_update:
            raise HTTPException(
                status_code=404, 
                detail="Temporary work update not found (may have been auto-deleted due to TTL expiry)"
            )

        # Complete the follow-up session
        session_update = {
            "answers": answers_update.answers,
            "status": SessionStatus.COMPLETED,
            "completedAt": datetime.now()
        }
        
        await followup_collection.update_one(
            {"_id": session_id},
            {"$set": session_update}
        )

        # Move temp work update to LogBook's DailyRecord collection
        daily_record = {
            "internId": intern_id,  # FIXED: Removed ObjectId() - keep as string
            "date": temp_work_update["date"],
            "stack": temp_work_update["stack"],
            "task": temp_work_update["task"],
            "progress": temp_work_update.get("progress", "No challenges faced"),
            "blockers": temp_work_update.get("blockers", "No specific plans"),
            "status": temp_work_update["status"],
            "qualityScore": temp_work_update.get("qualityScore", 0),
            "followupCompleted": True,
            "questionType": session.get("questionType", "unknown"),
            "followupAnswers": answers_update.answers
        }

        # Check for existing record (override logic)
        existing_record = await daily_records.find_one({
            "internId": intern_id,  # FIXED: Removed ObjectId() - keep as string
            "date": temp_work_update["date"]
        })
        
        if existing_record:
            await daily_records.replace_one({"_id": existing_record["_id"]}, daily_record)
            final_record_id = str(existing_record["_id"])
            logger.info(f"Updated existing LogBook record for user {intern_id}: {final_record_id}")
        else:
            result = await daily_records.insert_one(daily_record)
            final_record_id = str(result.inserted_id)
            logger.info(f"Created new LogBook record for user {intern_id}: {final_record_id}")

        # Update session with final record ID
        await followup_collection.update_one(
            {"_id": session_id},
            {"$set": {"dailyRecordId": final_record_id}}
        )

        # Delete temp work update
        await delete_temp_work_update(session["tempWorkUpdateId"])

        logger.info(f"AI follow-up completed for user {intern_id}, LogBook record finalized: {final_record_id}")
        
        return {
            "success": True,
            "message": "AI follow-up completed successfully. Work update saved to LogBook system.",
            "user_id": intern_id,
            "sessionId": session_id,
            "dailyRecordId": final_record_id,
            "workUpdateCompleted": True,
            "qualityScore": temp_work_update.get("qualityScore", 0),
            "status": "completed",
            "note": "Work update moved to LogBook DailyRecord collection"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete follow-up: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete follow-up: {str(e)}"
        )

# Quality Score Analysis
@app.post("/api/quality/analyze", response_model=QualityAnalysisResponse)
async def analyze_work_quality(request: QualityAnalysisRequest):
    """Analyze work description quality without creating work update"""
    try:
        quality_scorer = get_quality_scorer()
        
        # Calculate quality score
        needs_followup, score_details = await quality_scorer.should_trigger_followup(
            request.work_description, 
            request.user_id
        )
        
        return QualityAnalysisResponse(
            user_id=request.user_id,
            quality_score=score_details.get("quality_score", 0),
            needs_followup=needs_followup,
            analysis={
                "word_count": score_details.get("word_count", 0),
                "keyword_found": score_details.get("keyword_found", False),
                "sentiment_label": score_details.get("sentiment_label", "neutral"),
                "sentiment_polarity": score_details.get("sentiment_polarity", 0),
                "is_repetition": score_details.get("is_repetition", False),
                "has_structure": score_details.get("has_structure", False),
                "flagged": score_details.get("flagged", False),
                "flag_reasons": score_details.get("flag_reasons", [])
            },
            recommendation="Follow-up recommended" if needs_followup else "Good quality, no follow-up needed",
            threshold=Config.QUALITY_SCORE_THRESHOLD
        )
        
    except Exception as e:
        logger.error(f"Error analyzing work quality: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze work quality: {str(e)}"
        )

# Weekly Report Generation
@app.post("/api/reports/weekly", response_model=WeeklyReportResponse)
async def generate_weekly_report(
    request: WeeklyReportRequest,
    ai_service: AIFollowupService = Depends(get_ai_service)
):
    """Generate AI-powered weekly report for a user"""
    try:
        # Parse dates or use default (last 7 days)
        if request.start_date and request.end_date:
            start_dt = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(request.end_date, '%Y-%m-%d')
        else:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=7)
        
        logger.info(f"Generating weekly report for user {request.user_id} from {start_dt.date()} to {end_dt.date()}")
        
        # Generate the report using dedicated API key
        report_result = await ai_service.generate_weekly_report(request.user_id, start_dt, end_dt)
        
        if report_result.get("success"):
            return WeeklyReportResponse(
                success=True,
                user_id=request.user_id,
                report=report_result["report"],
                metadata={
                    "user_id": request.user_id,
                    "date_range": {
                        "start": start_dt.strftime('%Y-%m-%d'),
                        "end": end_dt.strftime('%Y-%m-%d')
                    },
                    "data_summary": report_result.get("data_summary", {}),
                    "generated_at": datetime.now().isoformat(),
                    "api_key_type": "dedicated_weekly_report_key"
                }
            )
        else:
            return WeeklyReportResponse(
                success=False,
                user_id=request.user_id,
                message=report_result.get("message", "Failed to generate report"),
                metadata={
                    "user_id": request.user_id,
                    "date_range": {
                        "start": start_dt.strftime('%Y-%m-%d'),
                        "end": end_dt.strftime('%Y-%m-%d')
                    },
                    "generated_at": datetime.now().isoformat()
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate weekly report: {str(e)}"
        )

# Get Follow-up Sessions for User
@app.post("/api/followup-sessions/list")
async def get_followup_sessions(
    request: GenerateQuestionsRequest,
    limit: int = 50,
    skip: int = 0
):
    """Get follow-up sessions for specified user"""
    try:
        intern_id = request.user_id.strip()
        
        db = get_database()
        followup_collection = db[Config.FOLLOWUP_SESSIONS_COLLECTION]
        
        cursor = followup_collection.find(
            {"internId": intern_id}
        ).sort("createdAt", -1).skip(skip).limit(limit)
        
        sessions = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for session in sessions:
            if "_id" in session:
                session["id"] = str(session["_id"])
                session["sessionId"] = session["_id"]
                del session["_id"]
        
        return {
            "success": True,
            "user_id": intern_id,
            "sessions": sessions,
            "count": len(sessions),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Error getting followup sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get followup sessions: {str(e)}"
        )

# System Status Endpoints
@app.get("/api/rate-limiters/status", response_model=RateLimiterStatusResponse)
async def get_rate_limiter_status():
    """Get current status of all rate limiters"""
    try:
        followup_limiter = get_followup_rate_limiter()
        weekly_limiter = get_weekly_report_rate_limiter()
        
        followup_status = await followup_limiter.get_rate_limit_status()
        weekly_status = await weekly_limiter.get_rate_limit_status()
        
        followup_stats = await followup_limiter.get_stats_summary()
        weekly_stats = await weekly_limiter.get_stats_summary()
        
        return RateLimiterStatusResponse(
            followup_api_keys={
                "status": followup_status,
                "stats": followup_stats,
                "purpose": "Follow-up question generation"
            },
            weekly_report_api_key={
                "status": weekly_status,
                "stats": weekly_stats,
                "purpose": "Weekly report generation"
            },
            overall={
                "total_keys": followup_stats["total_keys"] + weekly_stats["total_keys"],
                "total_calls_recorded": followup_stats["total_calls_recorded"] + weekly_stats["total_calls_recorded"],
                "rate_limit_per_minute": Config.RATE_LIMIT_PER_MINUTE
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting rate limiter status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get rate limiter status: {str(e)}"
        )

@app.get("/api/ai/test", response_model=TestAIResponse)
async def test_ai_connections():
    """Test all AI API keys and connections"""
    try:
        ai_service = AIFollowupService()
        test_results = await ai_service.test_ai_connection()
        
        return TestAIResponse(
            success=test_results.get("summary", {}).get("overall_status") == "healthy",
            message="AI connection test completed",
            test_results={
                "timestamp": datetime.now().isoformat(),
                "test_results": test_results,
                "summary": test_results.get("summary", {})
            }
        )
        
    except Exception as e:
        logger.error(f"AI connection test failed: {e}")
        return TestAIResponse(
            success=False,
            message="AI connection test failed",
            test_results={
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "summary": {
                    "overall_status": "error",
                    "fallback_available": True
                }
            }
        )

@app.get("/stats")
async def get_stats():
    """Get comprehensive database and system statistics"""
    try:
        stats = await get_database_stats()
        
        ttl_status = await verify_ttl_index()
        
        followup_limiter = get_followup_rate_limiter()
        weekly_limiter = get_weekly_report_rate_limiter()
        
        followup_stats = await followup_limiter.get_stats_summary()
        weekly_stats = await weekly_limiter.get_stats_summary()
        
        if stats:
            stats["cleanup_system"] = {
                "ttl_index_active": ttl_status,
                "manual_task_running": cleanup_task and not cleanup_task.done(),
                "cleanup_frequency": "Every 1 hour (backup to TTL)",
                "automatic_deletion": "24 hours via TTL index" if ttl_status else "Manual only"
            }
            stats["integration"] = {
                "logbook_ready": True,
                "daily_records_collection": "dailyrecords",
                "authentication": "user_id_in_request_field",
                "auth_method": "Simple user_id field in JSON requests"
            }
            stats["quality_scoring"] = {
                "enabled": True,
                "threshold": Config.QUALITY_SCORE_THRESHOLD,
                "keywords_count": len(Config().QUALITY_KEYWORDS),
                "scoring_components": ["word_count", "keywords", "sentiment", "repetition", "structure"]
            }
            stats["api_keys"] = {
                "followup_keys": followup_stats["total_keys"],
                "weekly_report_keys": weekly_stats["total_keys"],
                "total_calls_recorded": followup_stats["total_calls_recorded"] + weekly_stats["total_calls_recorded"],
                "rate_limit_per_minute": Config.RATE_LIMIT_PER_MINUTE
            }
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@app.delete("/api/temp-work-updates/cleanup")
async def cleanup_abandoned_temp_updates_endpoint():
    """Manually trigger cleanup of temporary work updates (backup to TTL)"""
    try:
        ttl_active = await verify_ttl_index()
        result = await cleanup_abandoned_temp_updates(24)
        
        deleted_temp = result.get("deleted_temp_updates", 0)
        deleted_sessions = result.get("deleted_sessions", 0)
        
        return {
            "success": True,
            "message": f"Manual cleanup completed. Cleaned up {deleted_temp} temp updates and {deleted_sessions} sessions",
            "deleted_temp_updates": deleted_temp,
            "deleted_sessions": deleted_sessions,
            "ttl_status": "active" if ttl_active else "inactive",
            "note": "TTL index handles most cleanup automatically" if ttl_active else "Manual cleanup is primary method"
        }
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup: {str(e)}"
        )

@app.get("/api/cleanup/status", response_model=CleanupStatusResponse)
async def get_cleanup_status():
    """Get detailed status of the TTL and cleanup system"""
    ttl_active = await verify_ttl_index()
    
    return CleanupStatusResponse(
        ttl_index={
            "active": ttl_active,
            "expiry_time": "24 hours",
            "status": "Automatic deletion enabled" if ttl_active else "TTL index not found"
        },
        manual_cleanup={
            "task_running": cleanup_task and not cleanup_task.done(),
            "frequency": "Every 1 hour",
            "purpose": "Backup to TTL + Session cleanup",
            "age_threshold": "24+ hours"
        },
        recommendation="TTL handles most cleanup automatically" if ttl_active else "Relying on manual cleanup only"
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return {
        "error": "HTTP_ERROR",
        "message": exc.detail,
        "status_code": exc.status_code,
        "success": False
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "INTERNAL_ERROR", 
        "message": "An internal error occurred",
        "details": str(exc) if Config.DEBUG else None,
        "success": False
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.DEBUG,
        log_level="info"
    )