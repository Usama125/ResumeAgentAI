from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Annotated
from datetime import datetime
from bson import ObjectId
from enum import Enum

class Skill(BaseModel):
    name: str
    level: Optional[str] = "Intermediate"  # Default level, no strict validation
    years: Optional[int] = Field(default=0, ge=0, le=50)  # Optional with default
    id: Optional[str] = None  # Optional ID for drag and drop reordering

class Experience(BaseModel):
    company: str
    position: str
    duration: str
    description: Optional[str] = "No description provided"  # Make optional with default
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False

class Project(BaseModel):
    name: str
    description: str = "No description provided"  # Default value to handle missing descriptions
    technologies: List[str] = []  # Default empty list to handle missing technologies
    url: Optional[str] = None
    github_url: Optional[str] = None
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

class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    dribbble: Optional[str] = None
    behance: Optional[str] = None
    medium: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    youtube: Optional[str] = None

class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade: Optional[str] = None
    activities: Optional[str] = None
    description: Optional[str] = None

class Language(BaseModel):
    name: str
    proficiency: Optional[str] = "Intermediate"  # Remove strict pattern validation, use default

class Award(BaseModel):
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None

class Publication(BaseModel):
    title: str
    publisher: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None

class VolunteerExperience(BaseModel):
    organization: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

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
    additional_info: Optional[str] = None
    skills: List[Skill] = []
    experience_details: List[Experience] = []
    projects: List[Project] = []
    certifications: List[str] = []
    work_preferences: Optional[WorkPreferences] = None
    onboarding_progress: Optional[OnboardingProgress] = Field(default_factory=lambda: OnboardingProgress())
    google_id: Optional[str] = None
    # Enhanced fields
    contact_info: Optional[ContactInfo] = Field(default_factory=lambda: ContactInfo())
    education: List[Education] = []
    languages: List[Language] = []
    awards: List[Award] = []
    publications: List[Publication] = []
    volunteer_experience: List[VolunteerExperience] = []
    interests: List[str] = []
    profession: Optional[str] = None  # Auto-detected from resume
    section_order: List[str] = []  # Custom section ordering
    profile_score: int = 0  # Profile completeness and quality score (0-100)
    profile_variant: str = "default"  # Profile view variant (default, compact, advanced)

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
    additional_info: Optional[str] = None
    skills: Optional[List[Skill]] = None
    experience_details: Optional[List[Experience]] = None
    projects: Optional[List[Project]] = None
    certifications: Optional[List[str]] = None
    work_preferences: Optional[WorkPreferences] = None
    onboarding_progress: Optional[OnboardingProgress] = None
    onboarding_completed: Optional[bool] = None
    # Enhanced fields
    contact_info: Optional[ContactInfo] = None
    education: Optional[List[Education]] = None
    languages: Optional[List[Language]] = None
    awards: Optional[List[Award]] = None
    publications: Optional[List[Publication]] = None
    volunteer_experience: Optional[List[VolunteerExperience]] = None
    interests: Optional[List[str]] = None
    profession: Optional[str] = None
    section_order: Optional[List[str]] = None
    profile_score: Optional[int] = None
    profile_variant: Optional[str] = None

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
    # Enhanced fields with defaults for backward compatibility
    contact_info: ContactInfo = Field(default_factory=lambda: ContactInfo())
    education: List[Education] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    volunteer_experience: List[VolunteerExperience] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    profession: Optional[str] = None
    section_order: List[str] = Field(default_factory=list)
    profile_score: int = 0  # Profile completeness and quality score (0-100)
    profile_variant: str = "default"  # Profile view variant

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
    # Enhanced fields
    contact_info: Optional[ContactInfo] = None
    education: List[Education] = []
    languages: List[Language] = []
    awards: List[Award] = []
    publications: List[Publication] = []
    volunteer_experience: List[VolunteerExperience] = []
    interests: List[str] = []
    profession: Optional[str] = None
    profile_score: int = 0

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
    skills: Optional[List[Skill]] = None
    experience_details: Optional[List[Experience]] = None
    projects: Optional[List[Project]] = None
    certifications: Optional[List[str]] = None
    # Enhanced fields for public view
    contact_info: Optional[ContactInfo] = None
    education: Optional[List[Education]] = None
    languages: Optional[List[Language]] = None
    awards: Optional[List[Award]] = None
    publications: Optional[List[Publication]] = None
    volunteer_experience: Optional[List[VolunteerExperience]] = None
    interests: Optional[List[str]] = None
    profession: Optional[str] = None
    # Additional fields that might be needed
    expected_salary: Optional[str] = None
    email: Optional[str] = None
    # Section ordering for public profile display
    section_order: Optional[List[str]] = None
    profile_score: int = 0
    profile_variant: str = "default"  # Profile view variant

class UserListingResponse(BaseModel):
    """Lightweight response model for user listing - only essential fields"""
    id: str
    name: str
    profession: Optional[str] = None
    location: Optional[str] = ""
    profile_picture: Optional[str] = None
    is_looking_for_job: bool = False
    rating: float = 4.5
    profile_score: int = 0