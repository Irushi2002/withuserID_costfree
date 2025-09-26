import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

class Config:
    # MongoDB Configuration
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "intern_progress")
    
    # AI Provider Configuration
    # Gemini API Keys (2 keys)
    GOOGLE_API_KEY_1 = os.getenv("GOOGLE_API_KEY_1")
    GOOGLE_API_KEY_2 = os.getenv("GOOGLE_API_KEY_2")
    
    # Groq API Key (1 key)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Hugging Face API Key (1 key)
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    
    # Weekly Report API Key (keep same - Gemini)
    WEEKLY_REPORT_API_KEY = os.getenv("WEEKLY_REPORT_API_KEY")
    
    # Legacy API Key (for backward compatibility)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Rate limiting configuration
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "12"))
    
    @property
    def AI_PROVIDERS_CONFIG(self) -> List[Dict[str, str]]:
        """Get list of all available AI provider configurations"""
        providers = []
        
        # Add Gemini providers
        if self.GOOGLE_API_KEY_1:
            providers.append({
                "provider": "gemini",
                "api_key": self.GOOGLE_API_KEY_1,
                "model": "gemini-2.0-flash",
                "name": "Gemini_1"
            })
        
        if self.GOOGLE_API_KEY_2:
            providers.append({
                "provider": "gemini",
                "api_key": self.GOOGLE_API_KEY_2,
                "model": "gemini-2.0-flash",
                "name": "Gemini_2"
            })
        
        # Add Groq provider
        if self.GROQ_API_KEY:
            providers.append({
                "provider": "groq",
                "api_key": self.GROQ_API_KEY,
                "model": "llama-3.3-70b-versatile",
                "name": "Groq_Llama3"
            })
        
        # Add Hugging Face provider
        if self.HUGGINGFACE_API_KEY:
            providers.append({
                "provider": "huggingface",
                "api_key": self.HUGGINGFACE_API_KEY,
                "model": "google/flan-t5-large",
                "name": "HuggingFace_FLAN_T5"
            })
        
        # Fallback to legacy if no providers configured
        if not providers and self.GOOGLE_API_KEY:
            providers.append({
                "provider": "gemini",
                "api_key": self.GOOGLE_API_KEY,
                "model": "gemini-2.0-flash",
                "name": "Gemini_Legacy"
            })
            
        return providers
    
    @property
    def GOOGLE_API_KEYS(self) -> List[str]:
        """Get list of Gemini API keys for backward compatibility"""
        keys = [self.GOOGLE_API_KEY_1, self.GOOGLE_API_KEY_2]
        valid_keys = [key for key in keys if key]
        
        if not valid_keys and self.GOOGLE_API_KEY:
            valid_keys = [self.GOOGLE_API_KEY]
            
        return valid_keys
    
    # Application Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Collections
    WORK_UPDATES_COLLECTION = "work_updates"
    TEMP_WORK_UPDATES_COLLECTION = "temp_work_updates"
    FOLLOWUP_SESSIONS_COLLECTION = "followup_sessions"
    DAILY_RECORDS_COLLECTION = "dailyrecords"
    
    # AI Model Configuration
    GEMINI_MODEL = "gemini-2.0-flash"
    GROQ_MODEL = "llama3-70b-8192"
    HUGGINGFACE_MODEL = "google/flan-t5-large"  # Better for questions
    
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
        """Validate required configuration"""
        config = cls()
        
        # Check if we have at least one AI provider configured
        if not config.AI_PROVIDERS_CONFIG:
            raise ValueError("At least one AI provider must be configured (Gemini, Groq, or Hugging Face)")
        
        # Check weekly report API key
        if not cls.WEEKLY_REPORT_API_KEY:
            raise ValueError("WEEKLY_REPORT_API_KEY environment variable is required")
            
        return True
    
    @classmethod
    def get_api_key_summary(cls):
        """Get summary of API key configuration for logging"""
        config = cls()
        providers = config.AI_PROVIDERS_CONFIG
        
        summary = {
            "total_providers": len(providers),
            "providers": {provider["name"]: provider["provider"] for provider in providers},
            "weekly_report_key": bool(config.WEEKLY_REPORT_API_KEY),
            "rate_limit_per_minute": config.RATE_LIMIT_PER_MINUTE,
            "authentication_method": "user_id_in_request_field"
        }
        
        return {
            "followup_keys": len(providers),
            "weekly_report_key": bool(config.WEEKLY_REPORT_API_KEY),
            "total_configured": len(providers) + (1 if config.WEEKLY_REPORT_API_KEY else 0),
            "jwt_required": False,
            "rate_limit_per_minute": config.RATE_LIMIT_PER_MINUTE,
            "authentication_method": "user_id_in_request_field",
            "provider_details": summary
        }