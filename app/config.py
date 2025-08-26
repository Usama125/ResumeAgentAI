from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb+srv://Usama125:yabwj7sYtLD0FifC@cluster0.tfx2doy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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
    UNAUTH_DAILY_JOB_MATCHING_LIMIT: int = 3000
    UNAUTH_DAILY_CHAT_LIMIT: int = 10
    UNAUTH_DAILY_CONTENT_GENERATION_LIMIT: int = 3
    
    # Rate Limiting - Authenticated Users
    AUTH_DAILY_JOB_MATCHING_LIMIT: int = 3000
    AUTH_DAILY_CHAT_LIMIT: int = 15
    AUTH_DAILY_CONTENT_GENERATION_LIMIT: int = 5
    
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
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    
    # Algolia Configuration
    ALGOLIA_APPLICATION_ID: str = "NIQXR0065F"
    ALGOLIA_API_KEY: str = "565d9aca1108bd03da1acff52209f4c3"
    ALGOLIA_SEARCH_KEY: str = "35e6909c47fc60a52be842d593de7967"
    ALGOLIA_INDEX_NAME: str = "users"
    
    # Admin Configuration
    ADMIN_ACCESS_KEY: str = "admin-secure-key-change-in-production"
    
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