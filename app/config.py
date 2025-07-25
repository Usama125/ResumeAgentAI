from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ai_resume_builder"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "jpg", "jpeg", "png"]
    
    # Rate Limiting - Unauthenticated Users
    UNAUTH_DAILY_JOB_MATCHING_LIMIT: int = 3
    UNAUTH_DAILY_CHAT_LIMIT: int = 10
    
    # Rate Limiting - Authenticated Users
    AUTH_DAILY_JOB_MATCHING_LIMIT: int = 5
    AUTH_DAILY_CHAT_LIMIT: int = 15
    
    # Rate Limiting - Reset Time Configuration
    RATE_LIMIT_RESET_HOURS: int = 24  # Hours until rate limit resets
    
    # Legacy Rate Limiting (deprecated)
    DAILY_REQUEST_LIMIT: int = 10
    DAILY_JOB_MATCHING_LIMIT: int = 3
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Resume Builder API"
    
    # Frontend API Authentication
    FRONTEND_API_KEY: str = "your-frontend-api-key-change-in-production"
    FRONTEND_API_SECRET: str = "your-frontend-api-secret-change-in-production"
    
    # Email - Gmail SMTP
    GMAIL_EMAIL: str = ""  # Your Gmail address
    GMAIL_APP_PASSWORD: str = ""  # Gmail App Password (not your regular password)
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # CORS - Strict Origin Control
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://cvchatter.com", 
        "https://www.cvchatter.com", 
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"

settings = Settings()