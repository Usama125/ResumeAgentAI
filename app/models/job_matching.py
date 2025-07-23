from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class JobSearchQuery(BaseModel):
    query: str = Field(..., description="Job description or search query")
    location: Optional[str] = Field(None, description="Preferred location")
    experience_level: Optional[str] = Field(None, description="Experience level requirement")
    limit: int = Field(10, ge=1, le=50, description="Number of results to return")
    skip: int = Field(0, ge=0, description="Number of results to skip")

class MatchingCriteria(BaseModel):
    skills_match: float = Field(..., description="Skills matching percentage")
    experience_match: float = Field(..., description="Experience matching percentage")
    location_match: float = Field(..., description="Location matching percentage")
    certification_match: float = Field(..., description="Certification matching percentage")
    overall_match: float = Field(..., description="Overall matching percentage")

class MatchingExplanation(BaseModel):
    strengths: List[str] = Field(..., description="Candidate's strengths for this role")
    gaps: List[str] = Field(..., description="Areas where candidate may need improvement")
    recommendations: List[str] = Field(..., description="Recommendations for the candidate")

class JobMatchResult(BaseModel):
    user_id: str
    name: str
    designation: str
    location: str
    profile_picture: Optional[str]
    experience: str
    summary: str
    skills: List[Dict[str, Any]]
    certifications: List[str]
    matching_score: float = Field(..., description="Overall matching percentage (0-100)")
    matching_criteria: MatchingCriteria
    explanation: MatchingExplanation
    is_looking_for_job: bool
    rating: float

class JobMatchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[JobMatchResult]
    search_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class JobMatchAnalysis(BaseModel):
    candidate_profile: Dict[str, Any]
    job_requirements: str
    matching_score: float
    detailed_analysis: Dict[str, Any]