from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from typing import List, Optional
from app.database import get_database
from app.models.user import PublicUserResponse
from app.services.algolia_service import AlgoliaService
from datetime import datetime
from pydantic import BaseModel
from bson import ObjectId
import json

router = APIRouter()
algolia_service = AlgoliaService()

class AdminUsersResponse(BaseModel):
    users: List[PublicUserResponse]
    total: int
    loaded: int

class BulkDeleteRequest(BaseModel):
    user_ids: List[str]


@router.get("/admin/users", response_model=AdminUsersResponse)
async def get_admin_users(
    limit: int = Query(10, ge=1, le=100, description="Number of users to return"),
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    db = Depends(get_database)
):
    """Get users for admin panel with newest-first sorting and pagination"""
    try:
        # Get total count of users (excluding test users)
        total_count = await db.users.count_documents({"is_test_user": {"$ne": True}})
        
        # Get users sorted by created_at descending (newest first, excluding test users)
        cursor = (
            db.users
            .find({"is_test_user": {"$ne": True}}, {
                "_id": 1,
                "name": 1,
                "username": 1,
                "email": 1,
                "designation": 1,
                "location": 1,
                "profile_picture": 1,
                "is_looking_for_job": 1,
                "rating": 1,
                "created_at": 1
            })
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        
        users = await cursor.to_list(length=limit)
        
        user_responses = [
            PublicUserResponse(
                id=str(user["_id"]),
                name=user.get("name", ""),
                username=user.get("username"),
                designation=user.get("designation") or "",
                location=user.get("location") or "",
                profile_picture=user.get("profile_picture"),
                is_looking_for_job=user.get("is_looking_for_job", False),
                rating=user.get("rating", 4.5),
                email=user.get("email"),
                # Set minimal required fields
                experience="",
                summary="",
                skills=[],
                experience_details=[],
                projects=[],
                certifications=[],
                contact_info=None,
                education=[],
                languages=[],
                awards=[],
                publications=[],
                volunteer_experience=[],
                interests=[],
                profession=None,
                expected_salary=None,
                section_order=[],
                profile_score=0,
                profile_variant="default"
            )
            for user in users
        ]
        
        return AdminUsersResponse(
            users=user_responses,
            total=total_count,
            loaded=skip + len(user_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, db = Depends(get_database)):
    """Delete a specific user from database and Algolia"""
    try:
        # Convert string ID to ObjectId
        try:
            object_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
        
        # Check if user exists
        user = await db.users.find_one({"_id": object_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete from database
        result = await db.users.delete_one({"_id": object_id})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete from Algolia
        try:
            await algolia_service.delete_user_from_algolia(user_id)
        except Exception as algolia_error:
            print(f"Warning: Failed to delete user {user_id} from Algolia: {str(algolia_error)}")
            # Don't fail the entire operation if Algolia deletion fails
        
        return {"message": f"User {user_id} deleted successfully", "success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

@router.post("/admin/users/bulk-delete")
async def bulk_delete_users(request: Request, db = Depends(get_database)):
    """Delete multiple users from database and Algolia"""
    try:
        # Parse the request body manually
        body = await request.body()
        
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No request body provided"
            )
        
        try:
            data = json.loads(body)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in request body"
            )
        
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user IDs provided"
            )
        
        # Convert string IDs to ObjectIds
        object_ids = []
        invalid_ids = []
        for user_id in user_ids:
            try:
                object_id = ObjectId(user_id)
                object_ids.append(object_id)
            except Exception as e:
                invalid_ids.append(user_id)
        
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user ID format: {invalid_ids}"
            )
        
        # Check which users exist
        existing_users = await db.users.find(
            {"_id": {"$in": object_ids}}, 
            {"_id": 1}
        ).to_list(length=None)
        
        existing_object_ids = [user["_id"] for user in existing_users]
        existing_user_ids = [str(oid) for oid in existing_object_ids]
        not_found_ids = [uid for uid in user_ids if uid not in existing_user_ids]
        
        if not existing_object_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found"
            )
        
        # Delete from database
        result = await db.users.delete_many({"_id": {"$in": existing_object_ids}})
        deleted_count = result.deleted_count
        
        # Delete from Algolia
        algolia_success_count = 0
        for user_id in existing_user_ids:
            try:
                await algolia_service.delete_user_from_algolia(user_id)
                algolia_success_count += 1
            except Exception as algolia_error:
                print(f"Warning: Failed to delete user {user_id} from Algolia: {str(algolia_error)}")
        
        response = {
            "message": f"Successfully deleted {deleted_count} users",
            "deleted_count": deleted_count,
            "algolia_deleted_count": algolia_success_count,
            "not_found_ids": not_found_ids,
            "success": True
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete users: {str(e)}"
        )
