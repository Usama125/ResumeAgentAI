from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from app.models.chat import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.services.user_service import UserService
from app.utils.secure_auth import verify_secure_request
from app.middleware.advanced_rate_limiting import advanced_rate_limit_chat
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
ai_service = AIService()
user_service = UserService()

@router.post("/{user_id}", response_model=ChatResponse)
@advanced_rate_limit_chat()
async def chat_with_profile(
    user_id: str, 
    chat_request: ChatRequest,
    request: Request
):
    """Chat with a user's profile (public endpoint - no authentication required)"""
    
    try:
        # Get target user profile
        target_user = await user_service.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Generate AI response
        response = await ai_service.generate_chat_response(
            target_user.dict(), 
            chat_request.message
        )
        
        return ChatResponse(
            response=response,
            user_id=user_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_with_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )

@router.get("/suggestions/{user_id}", response_model=List[str])
@advanced_rate_limit_chat()
async def get_chat_suggestions(user_id: str, request: Request):
    """Get contextual chat suggestions for a user profile (public endpoint)"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        suggestions = ai_service.generate_suggestion_chips(user.dict())
        return suggestions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_chat_suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat suggestions"
        )