from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.database import get_database
from app.models.user import UserInDB, UserUpdate, PublicUserResponse
from datetime import datetime

class UserService:
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            db = await get_database()
            user_data = await db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                return UserInDB(**user_data)
            return None
        except Exception:
            return None

    async def get_public_user(self, user_id: str) -> Optional[PublicUserResponse]:
        """Get public user profile (excludes sensitive data)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        return PublicUserResponse(
            id=str(user.id),
            name=user.name,
            username=user.username,
            designation=user.designation or "",
            location=user.location or "",
            profile_picture=user.profile_picture,
            is_looking_for_job=user.is_looking_for_job or False,
            experience=user.experience or "",
            rating=user.rating or 4.5,
            summary=user.summary or "",
            skills=user.skills or [],
            experience_details=user.experience_details or [],
            projects=user.projects or [],
            certifications=user.certifications or [],
            # Enhanced fields
            contact_info=user.contact_info,
            education=user.education or [],
            languages=user.languages or [],
            awards=user.awards or [],
            publications=user.publications or [],
            volunteer_experience=user.volunteer_experience or [],
            interests=user.interests or [],
            profession=user.profession,
            expected_salary=user.expected_salary,
            email=user.email
        )

    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[UserInDB]:
        """Update user profile with partial updates"""
        db = await get_database()
        
        # Prepare update data - only include fields that are not None
        update_dict = {}
        for key, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                update_dict[key] = value
                if key == "skills":
                    print(f"🎯 [USER_SERVICE] SKILLS DEBUG - Adding to update_dict: {value}")
                    print(f"🎯 [USER_SERVICE] SKILLS DEBUG - Type: {type(value)}, Length: {len(value) if isinstance(value, list) else 'Not a list'}")
                elif key == "experience":
                    print(f"🎯 [USER_SERVICE] EXPERIENCE DEBUG - Adding to update_dict: '{value}' (type: {type(value)})")
        
        # Always update the timestamp
        update_dict["updated_at"] = datetime.utcnow()
        
        # Only update if there are actual changes
        if not update_dict or (len(update_dict) == 1 and "updated_at" in update_dict):
            # No actual changes, just return current user
            return await self.get_user_by_id(user_id)
        
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        if result.matched_count:
            updated_user = await self.get_user_by_id(user_id)
            if updated_user and "skills" in update_dict:
                print(f"🎯 [USER_SERVICE] SKILLS DEBUG - After DB update, user skills: {updated_user.skills}")
                print(f"🎯 [USER_SERVICE] SKILLS DEBUG - Skills length in DB: {len(updated_user.skills) if updated_user.skills else 0}")
            if updated_user and "experience" in update_dict:
                print(f"🎯 [USER_SERVICE] EXPERIENCE DEBUG - After DB update, user experience: '{updated_user.experience}'")
            return updated_user
        return None

    async def search_users(self, 
                          query: Optional[str] = None,
                          skills: Optional[List[str]] = None,
                          location: Optional[str] = None,
                          is_looking_for_job: Optional[bool] = None,
                          limit: int = 20,
                          skip: int = 0) -> List[PublicUserResponse]:
        """Search users with filters"""
        db = await get_database()
        
        # Build search filter
        search_filter = {}
        
        if is_looking_for_job is not None:
            search_filter["is_looking_for_job"] = is_looking_for_job
        
        if location:
            search_filter["location"] = {"$regex": location, "$options": "i"}
        
        if skills:
            search_filter["skills.name"] = {"$in": skills}
        
        if query:
            search_filter["$text"] = {"$search": query}
        
        cursor = db.users.find(search_filter).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        return [
            PublicUserResponse(
                id=str(user["_id"]),
                name=user["name"],
                username=user.get("username"),
                designation=user.get("designation") or "",
                location=user.get("location") or "",
                profile_picture=user.get("profile_picture"),
                is_looking_for_job=user.get("is_looking_for_job", False),
                experience=user.get("experience") or "",
                rating=user.get("rating", 4.5),
                summary=user.get("summary") or "",
                skills=user.get("skills") or [],
                experience_details=user.get("experience_details") or [],
                projects=user.get("projects") or [],
                certifications=user.get("certifications") or [],
                # Enhanced fields
                contact_info=user.get("contact_info"),
                education=user.get("education") or [],
                languages=user.get("languages") or [],
                awards=user.get("awards") or [],
                publications=user.get("publications") or [],
                volunteer_experience=user.get("volunteer_experience") or [],
                interests=user.get("interests") or [],
                profession=user.get("profession"),
                expected_salary=user.get("expected_salary"),
                email=user.get("email")
            )
            for user in users
        ]

    async def get_featured_users(self, limit: int = 12, skip: int = 0) -> List[PublicUserResponse]:
        """Get featured users for homepage"""
        db = await get_database()
        
        cursor = db.users.find({}).sort("rating", -1).skip(skip).limit(limit)
        
        users = await cursor.to_list(length=limit)
        
        return [
            PublicUserResponse(
                id=str(user["_id"]),
                name=user["name"],
                username=user.get("username"),
                designation=user.get("designation") or "",
                location=user.get("location") or "",
                profile_picture=user.get("profile_picture"),
                is_looking_for_job=user.get("is_looking_for_job", False),
                experience=user.get("experience") or "",
                rating=user.get("rating", 4.5),
                summary=user.get("summary") or "",
                skills=user.get("skills") or [],
                experience_details=user.get("experience_details") or [],
                projects=user.get("projects") or [],
                certifications=user.get("certifications") or [],
                # Enhanced fields
                contact_info=user.get("contact_info"),
                education=user.get("education") or [],
                languages=user.get("languages") or [],
                awards=user.get("awards") or [],
                publications=user.get("publications") or [],
                volunteer_experience=user.get("volunteer_experience") or [],
                interests=user.get("interests") or [],
                profession=user.get("profession"),
                expected_salary=user.get("expected_salary"),
                email=user.get("email")
            )
            for user in users
        ]