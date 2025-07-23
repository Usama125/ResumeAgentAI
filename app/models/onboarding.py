from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.models.user import OnboardingStepStatus

class PDFProcessingRequest(BaseModel):
    filename: str

class PDFProcessingResponse(BaseModel):
    success: bool
    extracted_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_text_length: Optional[int] = None

class OnboardingCompleteRequest(BaseModel):
    extracted_data: Dict[str, Any] = {}
    additional_info: str = ""
    is_looking_for_job: bool = True
    current_employment_mode: str = ""
    preferred_work_mode: str = ""
    preferred_employment_type: str = ""
    preferred_location: str = ""
    current_salary: str = ""
    expected_salary: str = ""
    notice_period: str = ""
    availability: str = "immediate"

class Step1PDFUploadRequest(BaseModel):
    extracted_data: Dict[str, Any]

class Step2ProfileInfoRequest(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    is_looking_for_job: bool = True
    additional_info: Optional[str] = None

class Step3WorkPreferencesRequest(BaseModel):
    current_employment_mode: List[str] = []
    preferred_work_mode: List[str] = []
    preferred_employment_type: List[str] = []
    preferred_location: str = ""
    notice_period: Optional[str] = None
    availability: str = "immediate"

class Step4SalaryAvailabilityRequest(BaseModel):
    current_salary: Optional[str] = None
    expected_salary: Optional[str] = None
    availability: str = "immediate"
    notice_period: Optional[str] = None

class OnboardingStatusResponse(BaseModel):
    current_step: int
    completed: bool
    step_1_pdf_upload: OnboardingStepStatus
    step_2_profile_info: OnboardingStepStatus
    step_3_work_preferences: OnboardingStepStatus
    step_4_salary_availability: OnboardingStepStatus

class StepCompletionResponse(BaseModel):
    success: bool
    next_step: Optional[int] = None
    message: str
    onboarding_completed: bool = False