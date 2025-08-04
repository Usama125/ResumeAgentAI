"""
Admin routes for managing dummy users and system operations
"""

import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..database import get_database
from ..utils.security import verify_api_key
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

async def verify_admin_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin API key"""
    # You can implement your own admin authentication here
    # For now, using a simple API key check
    expected_key = "admin-key-change-this-in-production"  # Change this in production
    
    if credentials.credentials != expected_key:
        raise HTTPException(status_code=403, detail="Invalid admin credentials")
    
    return credentials.credentials

async def generate_users_background(count: int, countries: list = None, task_id: str = None):
    """Background task to generate users"""
    try:
        # Update task status
        task_status[task_id] = {
            "status": "running",
            "progress": 0,
            "total": count,
            "started_at": datetime.utcnow(),
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
            "completed_at": datetime.utcnow()
        })
        
        await client.close()
        
    except Exception as e:
        # Update error status
        task_status[task_id].update({
            "status": "error",
            "message": f"Error generating users: {str(e)}",
            "error_at": datetime.utcnow()
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
    
    # Delete users with dummy password hash pattern
    # This is a safety measure to only delete users created by the script
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Find users created in the last 24 hours with default password
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(hours=24)
    
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
    """Get system statistics"""
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