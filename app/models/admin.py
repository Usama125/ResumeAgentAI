from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ActionType(str, Enum):
    PROFILE_VIEW = "profile_view"
    RESUME_DOWNLOAD = "resume_download"
    PDF_DOWNLOAD = "pdf_download"
    AI_CHAT = "ai_chat"
    AI_RESUME_ANALYSIS = "ai_resume_analysis"
    AI_CONTENT_GENERATION = "ai_content_generation"
    COVER_LETTER_GENERATION = "cover_letter_generation"
    JOB_MATCHING = "job_matching"
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"
    PROFILE_UPDATE = "profile_update"
    ONBOARDING_STEP = "onboarding_step"

class UserAction(BaseModel):
    """Track user actions for analytics"""
    user_id: Optional[str] = None  # None for guest users
    username: Optional[str] = None  # For easier identification
    action_type: ActionType
    details: Optional[Dict[str, Any]] = {}  # Additional action details
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    estimated_tokens: int = 0  # Estimated AI tokens used (if applicable)

class CoverLetter(BaseModel):
    """Store generated cover letters"""
    id: Optional[str] = None
    user_id: Optional[str] = None  # None for guest users
    username: Optional[str] = None
    company_name: str
    position: str
    content: str
    job_description: Optional[str] = None
    options_used: Optional[dict] = None  # User generation options
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_tokens: int = 0

class UserFeedback(BaseModel):
    """Store user feedback"""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: Optional[str] = None  # None for anonymous feedback
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    message: str
    rating: Optional[int] = Field(None, ge=1, le=5)  # 1-5 star rating
    page_url: Optional[str] = None  # Page where feedback was submitted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "new"  # new, reviewed, responded

class GeneratedResume(BaseModel):
    """Store generated resume content for admin review"""
    id: Optional[str] = Field(default=None, alias="_id")
    username: str
    user_data: dict  # Original user profile data
    processed_data: dict  # AI-processed resume data
    download_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_downloaded: Optional[datetime] = None

class AdminStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    total_profile_views: int
    total_downloads: int
    total_ai_requests: int
    total_cover_letters: int
    total_feedback: int
    top_professions: List[Dict[str, Any]]

class UserAnalytics(BaseModel):
    """User-specific analytics data"""
    user_id: str
    username: Optional[str] = None
    name: str
    email: str
    profession: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    last_active: Optional[datetime] = None
    
    # Action counts
    profile_views: int = 0
    resume_downloads: int = 0
    ai_chat_messages: int = 0
    ai_content_generations: int = 0
    cover_letters_generated: int = 0
    job_matches_requested: int = 0
    
    # Token usage
    total_estimated_tokens: int = 0
    
    # Status
    is_active: bool = True
    is_blocked: bool = False
    
    # Profile completion
    profile_completion_score: int = 0

class AdminDashboardData(BaseModel):
    """Complete admin dashboard data"""
    stats: AdminStats
    recent_users: List[UserAnalytics]
    recent_actions: List[UserAction]
    recent_feedback: List[UserFeedback]
    recent_cover_letters: List[CoverLetter]

# Token estimation constants (approximate)
TOKEN_ESTIMATES = {
    ActionType.AI_CHAT: 150,  # Average chat message
    ActionType.AI_RESUME_ANALYSIS: 800,  # Resume analysis
    ActionType.AI_CONTENT_GENERATION: 300,  # Content generation
    ActionType.COVER_LETTER_GENERATION: 600,  # Cover letter
    ActionType.JOB_MATCHING: 200,  # Job matching
}
