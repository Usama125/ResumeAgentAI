"""
Admin routes for managing users, analytics, and system operations
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..utils.api_key_auth import verify_api_key
from ..services.analytics_service import get_analytics_service
from ..models.admin import (
    AdminStats, 
    UserAnalytics, 
    AdminDashboardData, 
    UserAction, 
    CoverLetter, 
    UserFeedback
)
import sys
import os

# Add the parent directory to the path to import the dummy user generator
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

class GenerateUsersRequest(BaseModel):
    count: int = 50
    countries: Optional[list] = None
    
class GenerateUsersResponse(BaseModel):
    message: str
    task_id: str
    count: int
    status: str

# Store background task status
task_status = {}

def verify_admin_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin API key"""
    from ..config import settings
    
    if credentials.credentials != settings.ADMIN_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    
    return credentials.credentials

class AdminLoginRequest(BaseModel):
    admin_key: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    message: str

class BlockUserRequest(BaseModel):
    user_id: str
    block: bool = True

class FeedbackSubmissionRequest(BaseModel):
    message: str
    name: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[int] = None
    page_url: Optional[str] = None

async def generate_users_background(count: int, countries: list = None, task_id: str = None):
    """Background task to generate users"""
    try:
        # Update task status
        task_status[task_id] = {
            "status": "running",
            "progress": 0,
            "total": count,
            "started_at": datetime.now(timezone.utc),
            "message": "Starting user generation..."
        }
        
        # Import the dummy user generator
        from generate_dummy_users import generate_dummy_user
        from motor.motor_asyncio import AsyncIOMotorClient
        from ..config import settings
        
        # Connect to database
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        users_collection = db.users
        
        # Generate users
        users = []
        available_countries = ['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'IT', 'ES', 'IN', 'JP', 'BR', 'MX']
        
        if not countries:
            countries = available_countries
        
        for i in range(count):
            # Update progress
            progress = int((i / count) * 100)
            task_status[task_id].update({
                "progress": progress,
                "message": f"Generated {i}/{count} users..."
            })
            
            # Select country for this user
            country = countries[i % len(countries)]
            user = await generate_dummy_user(country)
            users.append(user)
            
            # Insert in batches of 10
            if len(users) >= 10 or i == count - 1:
                await users_collection.insert_many(users)
                users = []  # Clear the batch
        
        # Update final status
        task_status[task_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Successfully generated {count} users!",
            "completed_at": datetime.now(timezone.utc)
        })
        
        await client.close()
        
    except Exception as e:
        # Update error status
        task_status[task_id].update({
            "status": "error",
            "message": f"Error generating users: {str(e)}",
            "error_at": datetime.now(timezone.utc)
        })
        raise

@router.post("/generate-users", response_model=GenerateUsersResponse)
async def generate_dummy_users_endpoint(
    request: GenerateUsersRequest,
    background_tasks: BackgroundTasks,
    admin_key: str = Depends(verify_admin_access)
):
    """
    Generate dummy users in the background.
    This endpoint creates realistic user profiles without blocking the request.
    """
    if request.count <= 0 or request.count > 1000:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 1000")
    
    # Generate unique task ID
    import uuid
    task_id = str(uuid.uuid4())
    
    # Start background task
    background_tasks.add_task(
        generate_users_background,
        count=request.count,
        countries=request.countries,
        task_id=task_id
    )
    
    # Initialize task status
    task_status[task_id] = {
        "status": "queued",
        "progress": 0,
        "total": request.count,
        "message": "Task queued for execution..."
    }
    
    return GenerateUsersResponse(
        message=f"Started generating {request.count} dummy users in background",
        task_id=task_id,
        count=request.count,
        status="queued"
    )

@router.get("/generate-users/status/{task_id}")
async def get_generation_status(
    task_id: str,
    admin_key: str = Depends(verify_admin_access)
):
    """Get the status of a user generation task"""
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        **task_status[task_id]
    }

@router.get("/generate-users/tasks")
async def list_generation_tasks(
    admin_key: str = Depends(verify_admin_access)
):
    """List all user generation tasks"""
    return {
        "tasks": [
            {"task_id": task_id, **status}
            for task_id, status in task_status.items()
        ]
    }

@router.delete("/users/cleanup")
async def cleanup_dummy_users(
    confirm: bool = Query(False),
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """
    Delete all users with dummy passwords (for testing purposes only).
    Requires confirm=true query parameter.
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Add ?confirm=true to confirm deletion of dummy users"
        )
    
    # Find users created in the last 24 hours with default password
    from datetime import timedelta
    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
    
    result = await db.users.delete_many({
        "created_at": {"$gte": cutoff_date},
        "onboarding_completed": True,
        "daily_requests": 0
    })
    
    return {
        "message": f"Deleted {result.deleted_count} dummy users",
        "deleted_count": result.deleted_count
    }

@router.get("/stats")
async def get_admin_stats(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """Get system statistics (Legacy endpoint - use /dashboard for new stats)"""
    # Count total users
    total_users = await db.users.count_documents({})
    
    # Count users created today
    from datetime import date
    today = datetime.combine(date.today(), datetime.min.time())
    users_today = await db.users.count_documents({
        "created_at": {"$gte": today}
    })
    
    # Count users by profession
    pipeline = [
        {"$match": {"profession": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$profession", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    professions = await db.users.aggregate(pipeline).to_list(length=10)
    
    return {
        "total_users": total_users,
        "users_created_today": users_today,
        "top_professions": professions,
        "active_generation_tasks": len([
            t for t in task_status.values() 
            if t["status"] in ["queued", "running"]
        ])
    }

# ===== NEW ADMIN DASHBOARD ENDPOINTS =====

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(request: AdminLoginRequest):
    """Login as admin with access key"""
    from ..config import settings
    
    if request.admin_key != settings.ADMIN_ACCESS_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    
    # For simplicity, we'll just return the key as token
    # In production, you might want to generate a proper JWT
    return AdminLoginResponse(
        access_token=request.admin_key,
        message="Admin login successful"
    )

@router.get("/dashboard", response_model=AdminDashboardData)
async def get_admin_dashboard(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """Get complete admin dashboard data"""
    analytics = get_analytics_service(db)
    
    # Get all dashboard data
    stats = await analytics.get_admin_stats()
    recent_users = await analytics.get_user_analytics(limit=20)
    recent_actions = await analytics.get_recent_actions(limit=50)
    recent_feedback = await analytics.get_recent_feedback(limit=20)
    recent_cover_letters = await analytics.get_recent_cover_letters(limit=20)
    
    return AdminDashboardData(
        stats=stats,
        recent_users=recent_users,
        recent_actions=recent_actions,
        recent_feedback=recent_feedback,
        recent_cover_letters=recent_cover_letters
    )

@router.get("/users", response_model=List[UserAnalytics])
async def get_admin_users(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """Get users with analytics data"""
    analytics = get_analytics_service(db)
    return await analytics.get_user_analytics(limit=limit, offset=offset, search=search)

@router.post("/users/block")
async def block_unblock_user(
    request: BlockUserRequest,
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """Block or unblock a user"""
    analytics = get_analytics_service(db)
    
    if request.block:
        success = await analytics.block_user(request.user_id)
        action = "blocked"
    else:
        success = await analytics.unblock_user(request.user_id)
        action = "unblocked"
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"User {action} successfully"}

@router.get("/analytics/actions", response_model=List[UserAction])
async def get_user_actions(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(100, le=500)
):
    """Get recent user actions"""
    analytics = get_analytics_service(db)
    return await analytics.get_recent_actions(limit=limit)

@router.get("/analytics/cover-letters", response_model=List[CoverLetter])
async def get_cover_letters(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(50, le=200)
):
    """Get recent cover letters"""
    analytics = get_analytics_service(db)
    return await analytics.get_recent_cover_letters(limit=limit)


@router.delete("/analytics/cover-letters/{letter_id}")
async def delete_cover_letter(
    letter_id: str,
    admin_key: str = Depends(verify_admin_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a single cover letter"""
    try:
        analytics = get_analytics_service(db)
        success = await analytics.delete_cover_letter(letter_id)
        
        if success:
            return {"success": True, "message": "Cover letter deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Cover letter not found")
    
    except Exception as e:
        logger.error(f"Error deleting cover letter {letter_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete cover letter")


@router.delete("/analytics/cover-letters")
async def delete_all_cover_letters(
    admin_key: str = Depends(verify_admin_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete all cover letters"""
    try:
        analytics = get_analytics_service(db)
        deleted_count = await analytics.delete_all_cover_letters()
        
        return {
            "success": True, 
            "message": f"Successfully deleted {deleted_count} cover letters",
            "deleted_count": deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error deleting all cover letters: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete cover letters")


@router.get("/analytics/feedback", response_model=List[UserFeedback])
async def get_feedback(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(50, le=200)
):
    """Get recent feedback"""
    analytics = get_analytics_service(db)
    return await analytics.get_recent_feedback(limit=limit)

# ===== OPTIMIZED STATS ENDPOINTS =====

@router.get("/stats/quick")
async def get_quick_stats(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """Get essential stats quickly - optimized for dashboard cards"""
    try:
        # Use parallel execution for independent queries
        total_users_task = db.users.count_documents({})
        total_profile_views_task = db.user_actions.count_documents({"action_type": "profile_view"})
        total_ai_requests_task = db.user_actions.count_documents({
            "action_type": {"$in": ["ai_chat", "ai_resume_analysis", "ai_content_generation", "cover_letter_generation"]}
        })
        total_cover_letters_task = db.cover_letters.count_documents({})
        total_downloads_task = db.user_actions.count_documents({
            "action_type": {"$in": ["resume_download", "pdf_download"]}
        })
        total_feedback_task = db.user_feedback.count_documents({})
        
        # Execute all queries in parallel
        total_users, total_profile_views, total_ai_requests, total_cover_letters, total_downloads, total_feedback = await asyncio.gather(
            total_users_task,
            total_profile_views_task, 
            total_ai_requests_task,
            total_cover_letters_task,
            total_downloads_task,
            total_feedback_task
        )
        
        return {
            "total_users": total_users,
            "total_profile_views": total_profile_views,
            "total_ai_requests": total_ai_requests,
            "total_cover_letters": total_cover_letters,
            "total_downloads": total_downloads,
            "total_feedback": total_feedback
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quick stats: {str(e)}")

@router.get("/stats/recent-users")
async def get_recent_users_only(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(5, le=20)
):
    """Get only recent users for overview"""
    analytics = get_analytics_service(db)
    return await analytics.get_user_analytics(limit=limit)

@router.get("/stats/top-professions")
async def get_top_professions_only(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(10, le=20)
):
    """Get only top professions - optimized query"""
    try:
        # Optimized aggregation with index hints
        pipeline = [
            {"$match": {"profession": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$profession", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        cursor = db.users.aggregate(pipeline)
        professions = await cursor.to_list(length=limit)
        
        return [
            {"profession": p["_id"], "count": p["count"]} 
            for p in professions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top professions: {str(e)}")

@router.get("/analytics/detailed")
async def get_detailed_analytics(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """Get detailed analytics data including time-based metrics"""
    try:
        from datetime import timedelta
        
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # Get all stats in parallel
        (
            total_users,
            new_users_today,
            new_users_this_week,
            new_users_this_month,
            total_profile_views,
            total_downloads,
            total_ai_requests,
            total_cover_letters,
            total_feedback
        ) = await asyncio.gather(
            db.users.count_documents({}),
            db.users.count_documents({"created_at": {"$gte": today_start}}),
            db.users.count_documents({"created_at": {"$gte": week_start}}),
            db.users.count_documents({"created_at": {"$gte": month_start}}),
            db.user_actions.count_documents({"action_type": "profile_view"}),
            db.user_actions.count_documents({
                "action_type": {"$in": ["resume_download", "pdf_download"]}
            }),
            db.user_actions.count_documents({
                "action_type": {"$in": ["ai_chat", "ai_resume_analysis", "ai_content_generation", "cover_letter_generation"]}
            }),
            db.cover_letters.count_documents({}),
            db.user_feedback.count_documents({})
        )
        
        return {
            "stats": {
                "total_users": total_users,
                "new_users_today": new_users_today,
                "new_users_this_week": new_users_this_week,
                "new_users_this_month": new_users_this_month,
                "total_profile_views": total_profile_views,
                "total_downloads": total_downloads,
                "total_ai_requests": total_ai_requests,
                "total_cover_letters": total_cover_letters,
                "total_feedback": total_feedback
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get detailed analytics: {str(e)}")

@router.get("/feedback", response_model=List[UserFeedback])
async def get_user_feedback(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database),
    limit: int = Query(50, le=200)
):
    """Get user feedback"""
    analytics = get_analytics_service(db)
    return await analytics.get_recent_feedback(limit=limit)

@router.post("/feedback/submit")
async def submit_feedback(
    request: FeedbackSubmissionRequest,
    req: Request,
    db = Depends(get_database)
):
    """Submit user feedback (public endpoint)"""
    analytics = get_analytics_service(db)
    
    feedback_id = await analytics.save_feedback(
        message=request.message,
        name=request.name,
        email=request.email,
        rating=request.rating,
        page_url=request.page_url
    )
    
    return {
        "message": "Feedback submitted successfully",
        "feedback_id": feedback_id
    }


@router.post("/analytics/track")
async def track_frontend_action(
    request: dict,
    req: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Track actions that happen on the frontend side (AI calls, downloads, etc.)
    """
    try:
        analytics = get_analytics_service(db)
        
        # Extract data from request
        action_type_str = request.get("action_type")
        user_id = request.get("user_id")
        username = request.get("username")
        details = request.get("details", {})
        ip_address = request.get("ip_address", "unknown")
        user_agent = request.get("user_agent", "unknown")
        
        # If user_id is null, try to get user info from Authorization header
        if not user_id:
            try:
                from ..utils.analytics_tracker import get_user_info_from_request
                extracted_user_id, extracted_username = get_user_info_from_request(req)
                if extracted_user_id:
                    user_id = extracted_user_id
                    username = extracted_username
            except Exception:
                pass  # Continue with null values if extraction fails
        
        # Convert string action_type to ActionType enum
        try:
            from ..models.admin import ActionType
            action_type = ActionType(action_type_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid action_type: {action_type_str}")
        
        # Create action record
        await analytics.track_action(
            action_type=action_type,
            user_id=user_id,
            username=username,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # For cover letter generation, also save the cover letter
        if action_type == ActionType.COVER_LETTER_GENERATION:
            try:
                # Get the actual cover letter content from the request
                cover_letter_content = request.get("cover_letter_content", "")
                options_used = details.get("options_used", {})
                
                company_name = options_used.get("companyName", "Unknown Company")
                position_title = options_used.get("positionTitle", "Unknown Position")
                
                # Use actual content if available, otherwise create preview
                content_to_save = cover_letter_content if cover_letter_content else f"Cover letter for {position_title} at {company_name}"
                
                await analytics.save_cover_letter(
                    user_id=user_id,
                    username=username,
                    content=content_to_save,
                    position=position_title,
                    company_name=company_name,
                    job_description=options_used.get("jobDescription"),
                    options_used=options_used,
                    word_count=details.get("word_count"),
                    character_count=details.get("character_count")
                )
            except Exception as e:
                print(f"Error saving cover letter: {e}")
        
        return {"success": True, "message": "Action tracked successfully"}
        
    except Exception as e:
        print(f"Error tracking frontend action: {e}")
        return {"success": False, "message": "Failed to track action"}


@router.post("/analytics/save-resume")
async def save_resume_content(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Save generated resume content for admin review
    """
    try:
        analytics = get_analytics_service(db)
        
        username = request.get("username")
        user_data = request.get("user_data")
        processed_data = request.get("processed_data")
        
        if not all([username, user_data, processed_data]):
            return {"success": False, "message": "Missing required fields"}
        
        resume_id = await analytics.save_resume_content(
            username=username,
            user_data=user_data,
            processed_data=processed_data
        )
        
        return {"success": True, "resume_id": resume_id}
        
    except Exception as e:
        print(f"Error saving resume content: {e}")
        return {"success": False, "message": "Failed to save resume content"}


@router.post("/analytics/save-pdf")
async def save_pdf_for_review(
    request: dict,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Save generated PDF for admin review
    """
    try:
        analytics = get_analytics_service(db)
        
        username = request.get("username")
        pdf_type = request.get("pdf_type")
        pdf_data = request.get("pdf_data")
        filename = request.get("filename")
        
        if not all([username, pdf_type, pdf_data, filename]):
            return {"success": False, "message": "Missing required fields"}
        
        pdf_id = await analytics.save_pdf(
            username=username,
            pdf_type=pdf_type,
            pdf_data=pdf_data,
            filename=filename
        )
        
        return {"success": True, "pdf_id": pdf_id}
        
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return {"success": False, "message": "Failed to save PDF"}


@router.get("/resumes")
async def get_generated_resumes(
    admin_key: str = Depends(verify_admin_access),
    db: AsyncIOMotorDatabase = Depends(get_database),
    limit: int = Query(20, le=100)
):
    """Get list of generated resumes"""
    analytics = get_analytics_service(db)
    return await analytics.get_recent_resumes(limit=limit)


@router.get("/resumes/{resume_id}/download")
async def download_resume_pdf(
    resume_id: str,
    admin_key: str = Depends(verify_admin_access),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate and download PDF from saved resume content"""
    try:
        analytics = get_analytics_service(db)
        resume_data = await analytics.get_resume_by_id(resume_id)
        
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # For now, return the resume data - the frontend will handle PDF generation
        # Later we can implement server-side PDF generation if needed
        return {
            "resume_data": resume_data,
            "message": "Resume data retrieved for PDF generation"
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail="Resume not found")

# ===== AI ANALYSIS ADMIN ENDPOINTS =====

@router.get("/ai-analyses")
async def get_ai_analyses(
    admin_key: str = Depends(verify_admin_access),
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0)
):
    """Get all AI analyses for admin review"""
    try:
        from ..services.ai_analysis_cache import AIAnalysisCache
        
        cache = AIAnalysisCache()
        analyses = await cache.get_all_analyses_for_admin(limit=limit, skip=skip)
        
        return {
            "analyses": analyses,
            "total": len(analyses),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI analyses: {str(e)}")

@router.delete("/ai-analyses/user/{user_id}")
async def delete_user_ai_analyses(
    user_id: str,
    admin_key: str = Depends(verify_admin_access)
):
    """Delete all AI analyses for a specific user"""
    try:
        from ..services.ai_analysis_cache import AIAnalysisCache
        
        cache = AIAnalysisCache()
        await cache.invalidate_user_cache(user_id)
        
        return {"message": f"All AI analyses for user {user_id} have been deleted"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete AI analyses: {str(e)}")

@router.get("/ai-analyses/stats")
async def get_ai_analysis_stats(
    admin_key: str = Depends(verify_admin_access),
    db = Depends(get_database)
):
    """Get statistics about AI analyses usage"""
    try:
        # Count total analyses by type
        profile_analysis_count = await db.ai_analysis.count_documents({"analysis_type": "profile"})
        public_analysis_count = await db.ai_analysis.count_documents({"analysis_type": "public"})
        
        # Get recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_analyses = await db.ai_analysis.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        return {
            "total_analyses": profile_analysis_count + public_analysis_count,
            "profile_analyses": profile_analysis_count,
            "public_analyses": public_analysis_count,
            "recent_analyses_7d": recent_analyses
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI analysis stats: {str(e)}")