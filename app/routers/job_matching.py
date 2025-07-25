from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from typing import List, Optional
from app.models.job_matching import JobSearchQuery, JobMatchResponse, JobMatchResult
from app.services.job_matching_service import JobMatchingService
from app.routers.auth import get_current_user
from app.utils.secure_auth import verify_secure_request
from app.middleware.advanced_rate_limiting import advanced_rate_limit_job_matching
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
job_matching_service = JobMatchingService()

@router.post("/search", response_model=JobMatchResponse)
@advanced_rate_limit_job_matching()
async def search_matching_candidates(
    search_query: JobSearchQuery,
    request: Request,
    secure_verified: bool = Depends(verify_secure_request)
):
    """
    Search for candidates matching a job description or requirements.
    Uses AI to analyze profiles and provide matching percentages.
    Requires secure request verification for access.
    """
    try:
        
        # Find matching candidates
        matching_candidates = await job_matching_service.find_matching_candidates(
            query=search_query.query,
            location=search_query.location,
            experience_level=search_query.experience_level,
            limit=search_query.limit,
            skip=search_query.skip
        )
        
        return JobMatchResponse(
            query=search_query.query,
            total_matches=len(matching_candidates),
            results=matching_candidates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_matching_candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while searching for matching candidates"
        )

@router.get("/search", response_model=JobMatchResponse)
@advanced_rate_limit_job_matching()
async def search_candidates_by_query(
    request: Request,
    q: str = Query(..., description="Job description or search query"),
    location: Optional[str] = Query(None, description="Preferred location"),
    experience_level: Optional[str] = Query(None, description="Experience level (junior, mid, senior)"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    secure_verified: bool = Depends(verify_secure_request)
):
    """
    Search for candidates using query parameters.
    Alternative endpoint for simple searches.
    Requires secure request verification for access.
    """
    try:
        
        # Create search query object
        search_query = JobSearchQuery(
            query=q,
            location=location,
            experience_level=experience_level,
            limit=limit,
            skip=skip
        )
        
        # Find matching candidates
        matching_candidates = await job_matching_service.find_matching_candidates(
            query=search_query.query,
            location=search_query.location,
            experience_level=search_query.experience_level,
            limit=search_query.limit,
            skip=search_query.skip
        )
        
        return JobMatchResponse(
            query=search_query.query,
            total_matches=len(matching_candidates),
            results=matching_candidates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_candidates_by_query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while searching for candidates"
        )

@router.get("/summary")
@advanced_rate_limit_job_matching()
async def get_job_match_summary(
    request: Request,
    q: str = Query(..., description="Job description or search query"),
    secure_verified: bool = Depends(verify_secure_request)
):
    """
    Get summary statistics for job matching results.
    Shows distribution of matching scores.
    Requires secure request verification for access.
    """
    try:
        
        summary = await job_matching_service.get_job_match_summary(q)
        
        return {
            "query": q,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_job_match_summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while generating summary"
        )

@router.get("/analyze/{user_id}")
@advanced_rate_limit_job_matching()
async def analyze_candidate_for_job(
    user_id: str,
    request: Request,
    q: str = Query(..., description="Job description or search query"),
    secure_verified: bool = Depends(verify_secure_request)
):
    """
    Analyze a specific candidate against a job description.
    Returns detailed matching analysis.
    Requires secure request verification for access.
    """
    try:
        
        # Get user profile
        from app.services.user_service import UserService
        user_service = UserService()
        user_profile = await user_service.get_user_by_id(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Analyze job match
        from app.services.ai_service import AIService
        ai_service = AIService()
        analysis = ai_service.analyze_job_match(user_profile.dict(), q)
        
        return {
            "user_id": user_id,
            "candidate_name": user_profile.name,
            "job_query": q,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_candidate_for_job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while analyzing candidate"
        )