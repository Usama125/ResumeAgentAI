"""
Analytics tracking utility for easy integration across the application
"""

from typing import Optional, Dict, Any
from fastapi import Request
from app.services.analytics_service import get_analytics_service
from app.models.admin import ActionType

def get_user_info_from_request(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract user ID and username from request"""
    try:
        # Try to get user from request state (if authenticated)
        if hasattr(request.state, 'user') and request.state.user:
            user = request.state.user
            return user.get('id'), user.get('username')
        return None, None
    except Exception:
        return None, None

def get_client_info_from_request(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract IP address and user agent from request"""
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
        return ip_address, user_agent
    except Exception:
        return None, None

async def track_action_from_request(
    request: Request,
    action_type: ActionType,
    details: Optional[Dict[str, Any]] = None
):
    """Track user action from a FastAPI request"""
    try:
        # Get database instance directly
        from app.database import db
        analytics = get_analytics_service(db.database)
        
        # Extract user info
        user_id, username = get_user_info_from_request(request)
        ip_address, user_agent = get_client_info_from_request(request)
        
        # Track the action
        await analytics.track_action(
            action_type=action_type,
            user_id=user_id,
            username=username,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't affect user experience
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Analytics tracking failed: {str(e)}")
        pass

# Convenience functions for common actions
async def track_profile_view(request: Request, viewed_user_id: str, viewed_username: str):
    """Track when a user views a profile - attribute to the viewed user, not the viewer"""
    try:
        # Get database instance directly
        from app.database import db
        analytics = get_analytics_service(db.database)
        
        # Get viewer info for context
        viewer_user_id, viewer_username = get_user_info_from_request(request)
        ip_address, user_agent = get_client_info_from_request(request)
        
        # Track the action attributed to the VIEWED user, not the viewer
        await analytics.track_action(
            action_type=ActionType.PROFILE_VIEW,
            user_id=viewed_user_id,  # This is key - attribute to viewed user
            username=viewed_username,
            details={
                "viewer_user_id": viewer_user_id,  # Store viewer info in details
                "viewer_username": viewer_username,
                "viewed_user_id": viewed_user_id,
                "viewed_username": viewed_username
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't affect user experience
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Profile view tracking failed: {str(e)}")
        pass

async def track_resume_download(request: Request, downloaded_user_id: str, downloaded_username: str):
    """Track when a user downloads a resume - attribute to the resume owner, not the downloader"""
    try:
        # Get database instance directly
        from app.database import db
        analytics = get_analytics_service(db.database)
        
        # Get downloader info for context
        downloader_user_id, downloader_username = get_user_info_from_request(request)
        ip_address, user_agent = get_client_info_from_request(request)
        
        # Track the action attributed to the DOWNLOADED user, not the downloader
        await analytics.track_action(
            action_type=ActionType.RESUME_DOWNLOAD,
            user_id=downloaded_user_id,  # Attribute to resume owner
            username=downloaded_username,
            details={
                "downloader_user_id": downloader_user_id,  # Store downloader info in details
                "downloader_username": downloader_username,
                "downloaded_user_id": downloaded_user_id,
                "downloaded_username": downloaded_username
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't affect user experience
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Resume download tracking failed: {str(e)}")
        pass

async def track_pdf_download(request: Request, file_type: str = "resume"):
    """Track when a user downloads a PDF"""
    await track_action_from_request(
        request,
        ActionType.PDF_DOWNLOAD,
        {"file_type": file_type}
    )

async def track_ai_chat(request: Request, message_length: int = 0):
    """Track AI chat interactions"""
    await track_action_from_request(
        request,
        ActionType.AI_CHAT,
        {"message_length": message_length}
    )

async def track_ai_resume_analysis(request: Request):
    """Track AI resume analysis"""
    await track_action_from_request(
        request,
        ActionType.AI_RESUME_ANALYSIS
    )

async def track_ai_content_generation(request: Request, content_type: str = "general"):
    """Track AI content generation"""
    await track_action_from_request(
        request,
        ActionType.AI_CONTENT_GENERATION,
        {"content_type": content_type}
    )

async def track_job_matching(request: Request, job_count: int = 0):
    """Track job matching requests"""
    await track_action_from_request(
        request,
        ActionType.JOB_MATCHING,
        {"job_count": job_count}
    )

async def track_user_registration(request: Request):
    """Track user registration"""
    await track_action_from_request(
        request,
        ActionType.USER_REGISTRATION
    )

async def track_user_login(request: Request):
    """Track user login"""
    await track_action_from_request(
        request,
        ActionType.USER_LOGIN
    )

async def track_profile_update(request: Request, updated_fields: list = None):
    """Track profile updates"""
    await track_action_from_request(
        request,
        ActionType.PROFILE_UPDATE,
        {"updated_fields": updated_fields or []}
    )

async def track_onboarding_step(request: Request, step_number: int, step_name: str):
    """Track onboarding step completion"""
    await track_action_from_request(
        request,
        ActionType.ONBOARDING_STEP,
        {
            "step_number": step_number,
            "step_name": step_name
        }
    )

async def save_cover_letter_and_track(
    request: Request,
    company_name: str,
    position: str,
    content: str,
    job_description: Optional[str] = None
):
    """Save cover letter and track the action"""
    try:
        # Get database instance
        from ..database import get_database
        db_generator = get_database()
        db = await db_generator.__anext__()
        analytics = get_analytics_service(db)
        
        # Extract user info
        user_id, username = get_user_info_from_request(request)
        
        # Save cover letter (this also tracks the action)
        await analytics.save_cover_letter(
            user_id=user_id,
            username=username,
            company_name=company_name,
            position=position,
            content=content,
            job_description=job_description
        )
    except Exception:
        # Silently fail to avoid affecting user experience
        pass
