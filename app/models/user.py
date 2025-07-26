from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Annotated
from datetime import datetime
from bson import ObjectId
from enum import Enum

class Skill(BaseModel):
    name: str
    level: str = Field(..., pattern="^(Expert|Advanced|Intermediate|Beginner)$")
    years: int = Field(..., ge=0, le=50)

class Experience(BaseModel):
    company: str
    position: str
    duration: str
    description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False

class Project(BaseModel):
    name: str
    description: str = "No description provided"  # Default value to handle missing descriptions
    technologies: List[str] = []  # Default empty list to handle missing technologies
    url: Optional[str] = None
    duration: Optional[str] = None

class OnboardingStepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class OnboardingProgress(BaseModel):
    step_1_pdf_upload: OnboardingStepStatus = OnboardingStepStatus.NOT_STARTED
    step_2_profile_info: OnboardingStepStatus = OnboardingStepStatus.NOT_STARTED
    step_3_work_preferences: OnboardingStepStatus = OnboardingStepStatus.NOT_STARTED
    step_4_salary_availability: OnboardingStepStatus = OnboardingStepStatus.NOT_STARTED
    current_step: int = 1
    completed: bool = False

class WorkPreferences(BaseModel):
    current_employment_mode: List[str] = []
    preferred_work_mode: List[str] = []
    preferred_employment_type: List[str] = []
    preferred_location: str = ""
    notice_period: Optional[str] = None
    availability: str = "immediate"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    username: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    profile_picture: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_looking_for_job: bool = True
    expected_salary: Optional[str] = None
    current_salary: Optional[str] = None
    experience: Optional[str] = None
    summary: Optional[str] = None
    skills: List[Skill] = []
    experience_details: List[Experience] = []
    projects: List[Project] = []
    certifications: List[str] = []
    work_preferences: Optional[WorkPreferences] = None
    onboarding_progress: Optional[OnboardingProgress] = Field(default_factory=lambda: OnboardingProgress())
    google_id: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-z0-9_-]+$")

class UserUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    profile_picture: Optional[str] = None
    is_looking_for_job: Optional[bool] = None
    expected_salary: Optional[str] = None
    current_salary: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[Skill]] = None
    experience_details: Optional[List[Experience]] = None
    projects: Optional[List[Project]] = None
    certifications: Optional[List[str]] = None
    work_preferences: Optional[WorkPreferences] = None
    onboarding_progress: Optional[OnboardingProgress] = None
    onboarding_completed: Optional[bool] = None

class UserInDB(UserBase):
    id: Optional[str] = Field(default=None, alias="_id")
    hashed_password: str
    rating: float = 4.5
    onboarding_completed: bool = False
    onboarding_progress: OnboardingProgress = Field(default_factory=lambda: OnboardingProgress())
    daily_requests: int = 0
    last_request_reset: datetime = Field(default_factory=datetime.utcnow)
    job_matching_request_timestamps: Optional[list] = Field(default_factory=list)
    chat_request_timestamps: Optional[list] = Field(default_factory=list)
    refresh_token_jti: Optional[str] = None  # Store current refresh token ID
    refresh_token_expires_at: Optional[datetime] = None
    password_reset_token: Optional[str] = None  # Store password reset token
    password_reset_expires_at: Optional[datetime] = None  # Token expiration
    google_id: Optional[str] = None  # Google OAuth ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class UserResponse(UserBase):
    id: str
    rating: float
    onboarding_completed: bool
    onboarding_progress: OnboardingProgress
    created_at: datetime

class PublicUserResponse(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    designation: Optional[str] = ""
    location: Optional[str] = ""
    profile_picture: Optional[str] = None
    is_looking_for_job: bool = False
    experience: Optional[str] = ""
    rating: float = 4.5
    summary: Optional[str] = ""
    skills: List[Skill] = []
    experience_details: List[Experience] = []
    projects: List[Project] = []
    certifications: List[str] = []