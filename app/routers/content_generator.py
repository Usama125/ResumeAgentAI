from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel
from typing import Optional
from app.middleware.advanced_rate_limiting import advanced_rate_limit_content_generation
from app.routers.auth import get_current_user_optional
from app.models.user import UserInDB
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-generator", tags=["content-generator"])

class ContentGenerationRequest(BaseModel):
    """Request payload for content generation - only for rate limiting validation"""
    content_type: str  # Just for logging purposes
    pass

@router.post("/generate", response_model=dict)
@advanced_rate_limit_content_generation()
async def validate_content_generation(
    content_request: ContentGenerationRequest,
    request: Request,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """Validate content generation rate limit (same pattern as chat)"""
    try:
        # If we reach here, rate limiting validation passed
        # Return success response - actual generation happens on Next.js side
        return {
            "success": True,
            "message": "Content generation validated successfully",
            "user_id": str(current_user.id) if current_user else None,
            "is_authenticated": bool(current_user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in content generation rate limit check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process rate limit check"
        )