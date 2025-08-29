from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.database import get_database
from app.models.user import UserInDB, UserUpdate, PublicUserResponse
from app.services.profile_scoring_service import ProfileScoringService
from app.services.algolia_service import AlgoliaService
from datetime import datetime

class UserService:
    def __init__(self):
        self.profile_scoring_service = ProfileScoringService()
        self.algolia_service = AlgoliaService()
    
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
            email=user.email,
            # Include section order for consistent display
            section_order=user.section_order or [],
            profile_score=user.profile_score or 0,
            profile_variant=user.profile_variant or "default"
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
            
            # Calculate and update profile score after any profile update
            if updated_user:
                profile_score = self.profile_scoring_service.calculate_profile_score(updated_user)
                
                # Update profile score in database if it has changed
                if profile_score != getattr(updated_user, 'profile_score', 0):
                    await db.users.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": {"profile_score": profile_score}}
                    )
                    # Refresh user data to get the updated score
                    updated_user = await self.get_user_by_id(user_id)
                
                # Sync to Algolia after profile update (async, don't block user)
                try:
                    print(f"🔄 [USER_SERVICE] Starting Algolia sync for user {user_id}")
                    sync_success = await self.algolia_service.sync_user_to_algolia(updated_user)
                    if sync_success:
                        print(f"✅ [USER_SERVICE] Algolia sync completed successfully for user {user_id}")
                    else:
                        print(f"❌ [USER_SERVICE] Algolia sync failed for user {user_id}")
                except Exception as algolia_error:
                    print(f"⚠️ [USER_SERVICE] Algolia sync exception for user {user_id}: {str(algolia_error)}")
                    import traceback
                    traceback.print_exc()
                
                # Invalidate AI analysis cache since profile was updated
                try:
                    from app.services.ai_analysis_cache import AIAnalysisCache
                    cache = AIAnalysisCache()
                    await cache.invalidate_user_cache(user_id)
                    print(f"✅ [USER_SERVICE] AI analysis cache invalidated for user {user_id}")
                except Exception as cache_error:
                    print(f"⚠️ [USER_SERVICE] AI analysis cache invalidation failed: {str(cache_error)}")
            
            if updated_user and "skills" in update_dict:
                print(f"🎯 [USER_SERVICE] SKILLS DEBUG - After DB update, user skills: {updated_user.skills}")
                print(f"🎯 [USER_SERVICE] SKILLS DEBUG - Skills length in DB: {len(updated_user.skills) if updated_user.skills else 0}")
            if updated_user and "experience" in update_dict:
                print(f"🎯 [USER_SERVICE] EXPERIENCE DEBUG - After DB update, user experience: '{updated_user.experience}'")
            return updated_user
        return None
    
    async def get_profile_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed profile analysis with strengths and weaknesses - Now uses OpenAI + caching"""
        try:
            print(f"🚀 [USER_SERVICE] Getting profile analysis for user {user_id}")
            user = await self.get_user_by_id(user_id)
            if not user:
                print(f"❌ [USER_SERVICE] User {user_id} not found")
                return None
            
            print(f"✅ [USER_SERVICE] User found, last updated: {user.updated_at}")
            
            # Use AI analysis cache for OpenAI-powered analysis
            from app.services.ai_analysis_cache import AIAnalysisCache
            cache = AIAnalysisCache()
            
            print(f"🤖 [USER_SERVICE] Calling AI analysis cache for user {user_id}")
            analysis = await cache.get_or_generate_profile_analysis(user_id, user.updated_at)
            
            if analysis:
                print(f"✅ [USER_SERVICE] Got analysis from cache service with keys: {list(analysis.keys())}")
                return analysis
            else:
                print(f"❌ [USER_SERVICE] AI analysis cache returned None, using fallback")
            
            # Fallback to old scoring method
            fallback_analysis = self.profile_scoring_service.get_profile_analysis(user)
            print(f"🔄 [USER_SERVICE] Using fallback analysis with keys: {list(fallback_analysis.keys())}")
            return fallback_analysis
            
        except Exception as e:
            print(f"💥 [USER_SERVICE] Error in get_profile_analysis: {str(e)}")
            import traceback
            print(f"💥 [USER_SERVICE] Traceback: {traceback.format_exc()}")
            # Fallback to old method
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            return self.profile_scoring_service.get_profile_analysis(user)

    async def get_professional_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get professional fit analysis for employers and recruiters - Now uses caching"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Use AI analysis cache for public analysis
            from app.services.ai_analysis_cache import AIAnalysisCache
            cache = AIAnalysisCache()
            
            analysis = await cache.get_or_generate_public_analysis(user_id, user.updated_at)
            if analysis:
                return analysis
            
            # Fallback to direct AI service call
            from app.services.ai_service import AIService
            ai_service = AIService()
            analysis = await ai_service.analyze_professional_fit(user.dict())
            return analysis
            
        except Exception as e:
            print(f"Error in get_professional_analysis: {str(e)}")
            return None

    async def search_users(self, 
                          query: Optional[str] = None,
                          skills: Optional[List[str]] = None,
                          location: Optional[str] = None,
                          is_looking_for_job: Optional[bool] = None,
                          limit: int = 20,
                          skip: int = 0,
                          listing_only: bool = False) -> List[PublicUserResponse]:
        """Search users with filters"""
        db = await get_database()
        
        search_filter = {}
        
        # Exclude users who haven't completed first step of onboarding
        search_filter["$or"] = [
            {"onboarding_progress.step_1_pdf_upload": {"$ne": "not_started"}},
            {"onboarding_progress": {"$exists": False}},
            {"onboarding_completed": True}
        ]
        
        if is_looking_for_job is not None:
            search_filter["is_looking_for_job"] = is_looking_for_job
        
        if location:
            search_filter["location"] = {"$regex": location, "$options": "i"}
        
        if skills:
            search_filter["skills.name"] = {"$in": skills}
        
        if query:
            # Enhanced search: case insensitive partial matching for name, email, username
            search_terms = [term.strip() for term in query.split() if term.strip()]
            
            if search_terms:
                # Create regex patterns for each search term
                term_queries = []
                for term in search_terms:
                    escaped_term = term.replace('\\', '\\\\').replace('.', '\\.')
                    term_regex = {"$regex": escaped_term, "$options": "i"}
                    
                    # Search in name (split by spaces), email, username, designation
                    term_queries.append({
                        "$or": [
                            {"name": term_regex},
                            {"email": term_regex},
                            {"username": term_regex},
                            {"designation": term_regex}
                        ]
                    })
                
                # All terms must match at least one field
                search_filter["$and"] = term_queries
        
        # Define projection based on listing_only flag
        if listing_only:
            projection = {
                "_id": 1,
                "name": 1,
                "username": 1,
                "designation": 1,
                "profession": 1,
                "location": 1,
                "profile_picture": 1,
                "is_looking_for_job": 1,
                "rating": 1,
                "email": 1,
                "skills": 1
            }
        else:
            projection = None
        
        cursor = db.users.find(search_filter, projection).skip(skip).limit(limit)
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
                experience=user.get("experience") or "" if not listing_only else None,
                rating=user.get("rating", 4.5),
                summary=user.get("summary") or "" if not listing_only else None,
                skills=user.get("skills") or [],
                experience_details=user.get("experience_details") or [] if not listing_only else None,
                projects=user.get("projects") or [] if not listing_only else None,
                certifications=user.get("certifications") or [] if not listing_only else None,
                # Enhanced fields
                contact_info=user.get("contact_info") if not listing_only else None,
                education=user.get("education") or [] if not listing_only else None,
                languages=user.get("languages") or [] if not listing_only else None,
                awards=user.get("awards") or [] if not listing_only else None,
                publications=user.get("publications") or [] if not listing_only else None,
                volunteer_experience=user.get("volunteer_experience") or [] if not listing_only else None,
                interests=user.get("interests") or [] if not listing_only else None,
                profession=user.get("profession"),
                expected_salary=user.get("expected_salary") if not listing_only else None,
                email=user.get("email"),
                section_order=user.get("section_order") or [] if not listing_only else None
            )
            for user in users
        ]

    async def get_featured_users(self, limit: int = 12, skip: int = 0, listing_only: bool = False) -> List[PublicUserResponse]:
        """Get featured users for homepage"""
        db = await get_database()
        
        # Filter to exclude users who haven't completed first step of onboarding
        filter_query = {
            "$or": [
                {"onboarding_progress.step_1_pdf_upload": {"$ne": "not_started"}},
                {"onboarding_progress": {"$exists": False}},
                {"onboarding_completed": True}
            ]
        }
        
        # Define projection based on listing_only flag
        if listing_only:
            projection = {
                "_id": 1,
                "name": 1,
                "username": 1,
                "designation": 1,
                "profession": 1,
                "location": 1,
                "profile_picture": 1,
                "is_looking_for_job": 1,
                "rating": 1,
                "email": 1,
                "skills": 1
            }
        else:
            projection = None
        
        cursor = db.users.find(filter_query, projection).sort("rating", -1).skip(skip).limit(limit)
        
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
                experience=user.get("experience") or "" if not listing_only else None,
                rating=user.get("rating", 4.5),
                summary=user.get("summary") or "" if not listing_only else None,
                skills=user.get("skills") or [],
                experience_details=user.get("experience_details") or [] if not listing_only else None,
                projects=user.get("projects") or [] if not listing_only else None,
                certifications=user.get("certifications") or [] if not listing_only else None,
                # Enhanced fields
                contact_info=user.get("contact_info") if not listing_only else None,
                education=user.get("education") or [] if not listing_only else None,
                languages=user.get("languages") or [] if not listing_only else None,
                awards=user.get("awards") or [] if not listing_only else None,
                publications=user.get("publications") or [] if not listing_only else None,
                volunteer_experience=user.get("volunteer_experience") or [] if not listing_only else None,
                interests=user.get("interests") or [] if not listing_only else None,
                profession=user.get("profession"),
                expected_salary=user.get("expected_salary") if not listing_only else None,
                email=user.get("email"),
                section_order=user.get("section_order") or [] if not listing_only else None
            )
            for user in users
        ]