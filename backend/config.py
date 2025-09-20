import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "intern_progress")
    
    # Multiple Google AI API Keys Configuration
    # 4 API keys for regular follow-up generation
    GOOGLE_API_KEY_1 = os.getenv("GOOGLE_API_KEY_1")
    GOOGLE_API_KEY_2 = os.getenv("GOOGLE_API_KEY_2") 
    GOOGLE_API_KEY_3 = os.getenv("GOOGLE_API_KEY_3")
    GOOGLE_API_KEY_4 = os.getenv("GOOGLE_API_KEY_4")
    
    # 1 separate API key for weekly reports
    WEEKLY_REPORT_API_KEY = os.getenv("WEEKLY_REPORT_API_KEY")
    
    # Legacy single API key (for backward compatibility)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Rate limiting configuration
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "12"))
    
    @property
    def GOOGLE_API_KEYS(self) -> List[str]:
        """Get list of all available followup API keys"""
        keys = [
            self.GOOGLE_API_KEY_1,
            self.GOOGLE_API_KEY_2, 
            self.GOOGLE_API_KEY_3,
            self.GOOGLE_API_KEY_4
        ]
        # Filter out None values and return valid keys
        valid_keys = [key for key in keys if key]
        
        # If no multiple keys configured, fall back to single key for backward compatibility
        if not valid_keys and self.GOOGLE_API_KEY:
            valid_keys = [self.GOOGLE_API_KEY]
            
        return valid_keys
    
    # Application Configuration - REMOVED JWT REQUIREMENT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Collections
    WORK_UPDATES_COLLECTION = "work_updates"
    TEMP_WORK_UPDATES_COLLECTION = "temp_work_updates"
    FOLLOWUP_SESSIONS_COLLECTION = "followup_sessions"
    
    # AI Model Configuration
    GEMINI_MODEL = "gemini-2.0-flash"
    
    # Quality Scoring Configuration
    QUALITY_SCORE_THRESHOLD = float(os.getenv("QUALITY_SCORE_THRESHOLD", "6.0"))
    
    # Quality scoring thresholds (tunable)
    WORD_COUNT_WEAK_THRESHOLD = int(os.getenv("WORD_COUNT_WEAK_THRESHOLD", "10"))
    WORD_COUNT_OK_THRESHOLD = int(os.getenv("WORD_COUNT_OK_THRESHOLD", "25"))
    
    # Keyword list for action words 
    DEFAULT_KEYWORDS = [
        "implement", "fix", "test", "deploy", "review", "design", 
        "bug", "ticket", "block", "wip", "refactor", "docs", "complete",
        "debug", "meeting", "plann", "research", "learn",
        "code", "develop", "build", "write", "updat"
    ]
    
    @property
    def QUALITY_KEYWORDS(self) -> List[str]:
        """Get quality keywords from env or use defaults"""
        env_keywords = os.getenv("QUALITY_KEYWORDS")
        if env_keywords:
            return env_keywords.split(",")
        return self.DEFAULT_KEYWORDS
    
    # Sentiment analysis thresholds
    NEGATIVE_SENTIMENT_THRESHOLD = float(os.getenv("NEGATIVE_SENTIMENT_THRESHOLD", "-0.3"))
    POSITIVE_SENTIMENT_THRESHOLD = float(os.getenv("POSITIVE_SENTIMENT_THRESHOLD", "0.2"))
    
    @classmethod
    def validate_config_simplified(cls):
        """Validate required configuration - SIMPLIFIED VERSION (NO JWT REQUIRED)"""
        # Check if we have at least one API key configured
        if not cls().GOOGLE_API_KEYS:
            raise ValueError("At least one Google API key is required (GOOGLE_API_KEY_1-4 or GOOGLE_API_KEY)")
        
        # JWT Secret NO LONGER REQUIRED for user_id input field method
        
        # Check weekly report API key
        if not cls.WEEKLY_REPORT_API_KEY:
            raise ValueError("WEEKLY_REPORT_API_KEY environment variable is required")
            
        return True
    
    @classmethod
    def get_api_key_summary(cls):
        """Get summary of API key configuration for logging"""
        config = cls()
        followup_keys = len(config.GOOGLE_API_KEYS)
        weekly_key = bool(config.WEEKLY_REPORT_API_KEY)
        
        return {
            "followup_keys": followup_keys,
            "weekly_report_key": weekly_key,
            "total_configured": followup_keys + (1 if weekly_key else 0),
            "jwt_required": False,  # NO JWT REQUIRED with user_id field method
            "rate_limit_per_minute": config.RATE_LIMIT_PER_MINUTE,
            "authentication_method": "user_id_in_request_field"
        }