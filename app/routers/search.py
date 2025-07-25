from fastapi import APIRouter, Query, Request
from typing import List, Optional
from app.models.user import PublicUserResponse
from app.services.user_service import UserService
from app.middleware.advanced_rate_limiting import advanced_rate_limit_job_matching

router = APIRouter()
user_service = UserService()

@router.get("/users", response_model=List[PublicUserResponse])
@advanced_rate_limit_job_matching()
async def search_users(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
    skills: Optional[str] = Query(None, description="Comma-separated skills"),
    location: Optional[str] = Query(None, description="Location filter"),
    looking_for_job: Optional[bool] = Query(None, description="Job seeking status"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """Search users with filters"""
    
    # Parse skills
    skills_list = None
    if skills:
        skills_list = [skill.strip() for skill in skills.split(",") if skill.strip()]
    
    users = await user_service.search_users(
        query=q,
        skills=skills_list,
        location=location,
        is_looking_for_job=looking_for_job,
        limit=limit,
        skip=skip
    )
    
    return users