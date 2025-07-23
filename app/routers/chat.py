from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from app.models.chat import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.services.user_service import UserService
from app.utils.secure_auth import verify_secure_request

router = APIRouter()
ai_service = AIService()
user_service = UserService()

@router.post("/{user_id}", response_model=ChatResponse)
async def chat_with_profile(
    user_id: str, 
    chat_request: ChatRequest
):
    """Chat with a user's profile (public endpoint - no authentication required)"""
    
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

@router.get("/suggestions/{user_id}", response_model=List[str])
async def get_chat_suggestions(user_id: str):
    """Get contextual chat suggestions for a user profile (public endpoint)"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    suggestions = ai_service.generate_suggestion_chips(user.dict())
    return suggestions