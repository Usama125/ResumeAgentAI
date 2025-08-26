"""
Analytics service for tracking user actions and generating admin insights
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from ..models.admin import (
    UserAction, 
    ActionType, 
    CoverLetter, 
    UserFeedback, 
    AdminStats, 
    UserAnalytics,
    AdminDashboardData,
    TOKEN_ESTIMATES
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.actions_collection = db.user_actions
        self.cover_letters_collection = db.cover_letters
        self.feedback_collection = db.user_feedback
        self.users_collection = db.users

    async def track_action(
        self, 
        action_type: ActionType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Track user action asynchronously without blocking the main request
        """
        try:
            # Estimate tokens used for AI actions
            estimated_tokens = TOKEN_ESTIMATES.get(action_type, 0)
            
            action = UserAction(
                user_id=user_id,
                username=username,
                action_type=action_type,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                estimated_tokens=estimated_tokens
            )
            
            # Insert asynchronously in background
            task = asyncio.create_task(
                self._insert_action(action.dict())
            )
            # Store task reference to prevent garbage collection
            self._background_tasks = getattr(self, '_background_tasks', set())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            
        except Exception as e:
            # Log error but don't raise to avoid affecting user experience
            logger.error(f"Failed to track action {action_type}: {str(e)}")

    async def _insert_action(self, action_data: Dict[str, Any]) -> None:
        """Internal method to insert action data"""
        try:
            await self.actions_collection.insert_one(action_data)
        except Exception as e:
            logger.error(f"Failed to insert action data: {str(e)}")

    async def save_cover_letter(
        self,
        user_id: Optional[str],
        username: Optional[str],
        company_name: str,
        position: str,
        content: str,
        job_description: Optional[str] = None,
        options_used: Optional[dict] = None,
        word_count: Optional[int] = None,
        character_count: Optional[int] = None
    ) -> None:
        """Save generated cover letter"""
        try:
            cover_letter = CoverLetter(
                user_id=user_id,
                username=username,
                company_name=company_name,
                position=position,
                content=content,
                job_description=job_description,
                options_used=options_used,
                word_count=word_count,
                character_count=character_count,
                estimated_tokens=TOKEN_ESTIMATES[ActionType.COVER_LETTER_GENERATION]
            )
            
            task = asyncio.create_task(
                self.cover_letters_collection.insert_one(cover_letter.dict())
            )
            # Store task reference to prevent garbage collection
            self._background_tasks = getattr(self, '_background_tasks', set())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            
            # Also track as an action
            await self.track_action(
                ActionType.COVER_LETTER_GENERATION,
                user_id=user_id,
                username=username,
                details={
                    "company_name": company_name,
                    "position": position
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to save cover letter: {str(e)}")

    async def save_feedback(
        self,
        message: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        rating: Optional[int] = None,
        page_url: Optional[str] = None
    ) -> str:
        """Save user feedback and return feedback ID"""
        try:
            feedback = UserFeedback(
                user_id=user_id,
                username=username,
                name=name,
                email=email,
                message=message,
                rating=rating,
                page_url=page_url
            )
            
            result = await self.feedback_collection.insert_one(feedback.dict())
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save feedback: {str(e)}")
            raise

    async def get_admin_stats(self) -> AdminStats:
        """Get comprehensive admin statistics"""
        try:
            now = datetime.now(timezone.utc)
            today_start = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
            week_start = today_start - timedelta(days=7)
            month_start = today_start - timedelta(days=30)

            # Total users
            total_users = await self.users_collection.count_documents({})
            
            # New users by time period
            new_users_today = await self.users_collection.count_documents({
                "created_at": {"$gte": today_start}
            })
            
            new_users_this_week = await self.users_collection.count_documents({
                "created_at": {"$gte": week_start}
            })
            
            new_users_this_month = await self.users_collection.count_documents({
                "created_at": {"$gte": month_start}
            })

            # Action counts
            total_profile_views = await self.actions_collection.count_documents({
                "action_type": ActionType.PROFILE_VIEW
            })
            
            total_downloads = await self.actions_collection.count_documents({
                "action_type": {"$in": [ActionType.RESUME_DOWNLOAD, ActionType.PDF_DOWNLOAD]}
            })
            
            total_ai_requests = await self.actions_collection.count_documents({
                "action_type": {"$in": [
                    ActionType.AI_CHAT,
                    ActionType.AI_RESUME_ANALYSIS,
                    ActionType.AI_CONTENT_GENERATION,
                    ActionType.COVER_LETTER_GENERATION
                ]}
            })
            
            total_cover_letters = await self.cover_letters_collection.count_documents({})
            total_feedback = await self.feedback_collection.count_documents({})

            # Top professions
            match_stage = {"$match": {"profession": {"$exists": True, "$ne": None, "$ne": ""}}}
            group_stage = {"$group": {"_id": "$profession", "count": {"$sum": 1}}}
            sort_stage = {"$sort": {"count": -1}}
            limit_stage = {"$limit": 10}
            
            profession_pipeline = [match_stage, group_stage, sort_stage, limit_stage]
            
            professions_cursor = self.users_collection.aggregate(profession_pipeline)
            top_professions = await professions_cursor.to_list(length=10)
            
            return AdminStats(
                total_users=total_users,
                new_users_today=new_users_today,
                new_users_this_week=new_users_this_week,
                new_users_this_month=new_users_this_month,
                total_profile_views=total_profile_views,
                total_downloads=total_downloads,
                total_ai_requests=total_ai_requests,
                total_cover_letters=total_cover_letters,
                total_feedback=total_feedback,
                top_professions=[
                    {"profession": p["_id"], "count": p["count"]} 
                    for p in top_professions
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to get admin stats: {str(e)}")
            raise

    async def get_user_analytics(
        self, 
        limit: int = 50, 
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[UserAnalytics]:
        """Get user analytics with action counts"""
        try:
            # Build user query
            user_query = {}
            if search:
                regex_pattern = {"$regex": search, "$options": "i"}
                user_query["$or"] = [
                    {"name": regex_pattern},
                    {"email": regex_pattern},
                    {"username": regex_pattern},
                    {"profession": regex_pattern}
                ]

            # Get users with pagination, sorted by creation date (newest first)
            users_cursor = self.users_collection.find(user_query).sort("created_at", -1).skip(offset).limit(limit)
            users = await users_cursor.to_list(length=limit)
            
            user_analytics = []
            
            for user in users:
                user_id = str(user["_id"])
                
                # Get action counts for this user
                action_counts = await self._get_user_action_counts(user_id)
                
                # Get last activity
                last_action = await self.actions_collection.find_one(
                    {"user_id": user_id},
                    sort=[("timestamp", -1)]
                )
                
                user_analytics.append(UserAnalytics(
                    user_id=user_id,
                    username=user.get("username"),
                    name=user.get("name", ""),
                    email=user.get("email", ""),
                    profession=user.get("profession"),
                    location=user.get("location"),
                    created_at=user.get("created_at"),
                    last_active=last_action["timestamp"] if last_action else None,
                    profile_views=action_counts.get(ActionType.PROFILE_VIEW, 0),
                    resume_downloads=action_counts.get(ActionType.RESUME_DOWNLOAD, 0) + 
                                   action_counts.get(ActionType.PDF_DOWNLOAD, 0),
                    ai_chat_messages=action_counts.get(ActionType.AI_CHAT, 0),
                    ai_content_generations=action_counts.get(ActionType.AI_CONTENT_GENERATION, 0),
                    cover_letters_generated=action_counts.get(ActionType.COVER_LETTER_GENERATION, 0),
                    job_matches_requested=action_counts.get(ActionType.JOB_MATCHING, 0),
                    total_estimated_tokens=await self._get_user_token_usage(user_id),
                    profile_completion_score=user.get("profile_score", 0),
                    is_active=True,
                    is_blocked=user.get("is_blocked", False)
                ))
            
            return user_analytics
            
        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            raise

    async def _get_user_action_counts(self, user_id: str) -> Dict[ActionType, int]:
        """Get action counts for a specific user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$action_type", "count": {"$sum": 1}}}
        ]
        
        results = await self.actions_collection.aggregate(pipeline).to_list(length=None)
        
        return {
            ActionType(result["_id"]): result["count"] 
            for result in results
            if result["_id"] in [e.value for e in ActionType]
        }

    async def _get_user_token_usage(self, user_id: str) -> int:
        """Get estimated token usage for a user"""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total_tokens": {"$sum": "$estimated_tokens"}}}
        ]
        
        result = await self.actions_collection.aggregate(pipeline).to_list(length=1)
        return result[0]["total_tokens"] if result else 0

    async def get_recent_actions(self, limit: int = 100) -> List[UserAction]:
        """Get recent user actions"""
        try:
            actions_cursor = self.actions_collection.find().sort("timestamp", -1).limit(limit)
            actions_data = await actions_cursor.to_list(length=limit)
            
            # Convert ObjectId to string for Pydantic models
            for action in actions_data:
                if '_id' in action:
                    del action['_id']  # UserAction doesn't have an id field
            
            return [UserAction(**action) for action in actions_data]
            
        except Exception as e:
            logger.error(f"Failed to get recent actions: {str(e)}")
            raise

    async def get_recent_cover_letters(self, limit: int = 50) -> List[CoverLetter]:
        """Get recently generated cover letters"""
        try:
            cover_letters_cursor = self.cover_letters_collection.find().sort("created_at", -1).limit(limit)
            cover_letters_data = await cover_letters_cursor.to_list(length=limit)
            
            # Convert ObjectId to string for Pydantic models
            for cl in cover_letters_data:
                if '_id' in cl:
                    cl['id'] = str(cl['_id'])
                    del cl['_id']
            
            return [CoverLetter(**cl) for cl in cover_letters_data]
            
        except Exception as e:
            logger.error(f"Failed to get recent cover letters: {str(e)}")
            raise

    async def delete_cover_letter(self, letter_id: str) -> bool:
        """Delete a single cover letter by ID"""
        try:
            from bson import ObjectId
            result = await self.cover_letters_collection.delete_one({"_id": ObjectId(letter_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete cover letter {letter_id}: {str(e)}")
            return False
    
    async def delete_all_cover_letters(self) -> int:
        """Delete all cover letters and return count of deleted items"""
        try:
            result = await self.cover_letters_collection.delete_many({})
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete all cover letters: {str(e)}")
            return 0

    async def get_recent_feedback(self, limit: int = 50) -> List[UserFeedback]:
        """Get recent user feedback"""
        try:
            feedback_cursor = self.feedback_collection.find().sort("created_at", -1).limit(limit)
            feedback_data = await feedback_cursor.to_list(length=limit)
            
            # Convert ObjectId to string for Pydantic models
            for fb in feedback_data:
                if '_id' in fb:
                    fb['id'] = str(fb['_id'])
                    del fb['_id']
            
            return [UserFeedback(**fb) for fb in feedback_data]
            
        except Exception as e:
            logger.error(f"Failed to get recent feedback: {str(e)}")
            raise

    async def block_user(self, user_id: str) -> bool:
        """Block a user"""
        try:
            from bson import ObjectId
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_blocked": True, "updated_at": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to block user {user_id}: {str(e)}")
            raise

    async def unblock_user(self, user_id: str) -> bool:
        """Unblock a user"""
        try:
            from bson import ObjectId
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_blocked": False, "updated_at": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to unblock user {user_id}: {str(e)}")
            raise

    async def save_resume_content(self, username: str, user_data: dict, processed_data: dict) -> str:
        """Save generated resume content for admin review"""
        try:
            # Check if resume already exists for this user
            existing = await self.db.generated_resumes.find_one({"username": username})
            
            if existing:
                # Update existing resume
                result = await self.db.generated_resumes.update_one(
                    {"username": username},
                    {
                        "$set": {
                            "user_data": user_data,
                            "processed_data": processed_data,
                            "created_at": datetime.now(timezone.utc)
                        },
                        "$inc": {"download_count": 1},
                        "$set": {"last_downloaded": datetime.now(timezone.utc)}
                    }
                )
                return str(existing["_id"])
            else:
                # Create new resume record
                resume_record = {
                    "username": username,
                    "user_data": user_data,
                    "processed_data": processed_data,
                    "download_count": 1,
                    "created_at": datetime.now(timezone.utc),
                    "last_downloaded": datetime.now(timezone.utc)
                }
                
                result = await self.db.generated_resumes.insert_one(resume_record)
                return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving resume content: {e}")
            raise
    
    async def get_recent_resumes(self, limit: int = 20) -> List[dict]:
        """Get recently generated resumes"""
        try:
            cursor = self.db.generated_resumes.find().sort("created_at", -1).limit(limit)
            resumes = []
            
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                resumes.append(doc)
            
            return resumes
            
        except Exception as e:
            logger.error(f"Error getting recent resumes: {e}")
            return []
    
    async def get_resume_by_id(self, resume_id: str) -> dict:
        """Get resume content by ID"""
        try:
            from bson import ObjectId
            
            resume = await self.db.generated_resumes.find_one({"_id": ObjectId(resume_id)})
            if resume:
                resume["id"] = str(resume["_id"])
                del resume["_id"]
                return resume
            return None
            
        except Exception as e:
            logger.error(f"Error getting resume: {e}")
            raise

# Singleton instance to be used across the application
analytics_service: Optional[AnalyticsService] = None

def get_analytics_service(db: AsyncIOMotorDatabase) -> AnalyticsService:
    """Get or create analytics service instance"""
    global analytics_service
    if analytics_service is None:
        analytics_service = AnalyticsService(db)
    return analytics_service
