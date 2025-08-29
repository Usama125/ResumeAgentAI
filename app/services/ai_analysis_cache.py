from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.models.ai_analysis_simple import AIAnalysis
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

class AIAnalysisCache:
    """Simple AI Analysis caching service"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    async def get_or_generate_profile_analysis(self, user_id: str, user_updated_at: datetime) -> Optional[Dict[str, Any]]:
        """Get or generate profile analysis for /profile page (with OpenAI)"""
        return await self._get_or_generate_analysis(user_id, "profile", user_updated_at, self._generate_profile_analysis)
    
    async def get_or_generate_public_analysis(self, user_id: str, user_updated_at: datetime) -> Optional[Dict[str, Any]]:
        """Get or generate public analysis for /profile/[username] page"""
        return await self._get_or_generate_analysis(user_id, "public", user_updated_at, self._generate_public_analysis)
    
    async def _get_or_generate_analysis(
        self, 
        user_id: str, 
        analysis_type: str, 
        user_updated_at: datetime,
        generator_func
    ) -> Optional[Dict[str, Any]]:
        """Core method to get cached analysis or generate new one"""
        try:
            db = await get_database()
            logger.info(f"🔍 Checking cache for user {user_id}, type {analysis_type}")
            
            # Check if we have cached analysis
            cached_analysis = await db.ai_analysis.find_one({
                "user_id": user_id,
                "analysis_type": analysis_type
            })
            
            # If cached analysis exists and user hasn't updated profile since analysis was created
            if cached_analysis:
                cached_created_at = cached_analysis.get("created_at", datetime.min)
                logger.info(f"📅 Found cached analysis created at: {cached_created_at}")
                logger.info(f"📅 User last updated at: {user_updated_at}")
                
                if user_updated_at <= cached_created_at:
                    logger.info(f"✅ Serving cached {analysis_type} analysis for user {user_id}")
                    return cached_analysis["analysis_data"]
                else:
                    logger.info(f"🔄 Cache is outdated, generating new analysis")
            else:
                logger.info(f"💫 No cached analysis found, generating new analysis")
            
            # Generate new analysis
            logger.info(f"🤖 Generating new {analysis_type} analysis for user {user_id}")
            analysis_data = await generator_func(user_id)
            
            if not analysis_data:
                logger.error(f"❌ Failed to generate analysis data for user {user_id}")
                return None
            
            logger.info(f"✅ Generated analysis data with keys: {list(analysis_data.keys())}")
            
            # Save to database (upsert to ensure max 2 analyses per user)
            logger.info(f"💾 Saving analysis to database for user {user_id}")
            result = await db.ai_analysis.update_one(
                {"user_id": user_id, "analysis_type": analysis_type},
                {
                    "$set": {
                        "user_id": user_id,
                        "analysis_type": analysis_type,
                        "analysis_data": analysis_data,
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Successfully saved {analysis_type} analysis for user {user_id}")
            else:
                logger.error(f"❌ Failed to save analysis to database for user {user_id}")
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"💥 Error in AI analysis cache for user {user_id}: {str(e)}")
            import traceback
            logger.error(f"💥 Traceback: {traceback.format_exc()}")
            return None
    
    async def _generate_profile_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Generate profile analysis using OpenAI for /profile page"""
        try:
            logger.info(f"🤖 [AI_CACHE] Starting profile analysis generation for user {user_id}")
            
            # TEMPORARY: Check if OpenAI is disabled due to quota issues
            import os
            if os.getenv("DISABLE_OPENAI_CALLS", "false").lower() == "true":
                logger.info(f"⚠️ [AI_CACHE] OpenAI calls disabled, using enhanced fallback for user {user_id}")
                return await self._generate_enhanced_fallback_analysis(user_id)
            
            # Get user data directly from database to avoid circular imports
            db = await get_database()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user_doc:
                logger.error(f"❌ [AI_CACHE] User {user_id} not found in database")
                return None
            
            logger.info(f"✅ [AI_CACHE] User data retrieved for {user_doc.get('name', 'Unknown')}")
            
            # Create enhanced OpenAI prompt for profile improvement
            system_prompt = f"""You are an expert career coach analyzing a user's profile. Provide actionable advice to help them improve their profile and stand out to employers.

User Profile:
- Name: {user_doc.get('name', 'Not specified')}
- Role: {user_doc.get('designation', 'Not specified')}
- Experience: {user_doc.get('experience', 'Not specified')}
- Skills: {len(user_doc.get('skills', []))} skills listed
- Projects: {len(user_doc.get('projects', []))} projects
- Work Experience: {len(user_doc.get('experience_details', []))} positions
- Education: {len(user_doc.get('education', []))} entries

Provide detailed analysis focusing on:
1. **Profile Strengths**: What makes this profile stand out (3-4 points)
2. **Areas for Improvement**: Specific weaknesses that need attention (3-4 points)  
3. **Actionable Recommendations**: Concrete steps to improve the profile (4-5 points)
4. **Profile Completeness Score**: Rate 1-100 based on completeness and quality

Return JSON format:
{{
    "profile_score": 85,
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2", "weakness3"],
    "recommendations": ["rec1", "rec2", "rec3", "rec4"],
    "overall_assessment": "2-3 sentence summary of the profile quality and potential"
}}"""
            
            logger.info(f"🚀 [AI_CACHE] Making OpenAI API call for user {user_id}")
            
            response = self.ai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Changed from gpt-4 to avoid quota issues
                messages=[
                    {"role": "system", "content": "You are an expert career coach providing profile analysis."},
                    {"role": "user", "content": system_prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            result = response.choices[0].message.content
            logger.info(f"✅ [AI_CACHE] Received OpenAI response for user {user_id}")
            
            analysis = self.ai_service._parse_json_response(result, {
                "profile_score": 50,
                "strengths": ["Analysis temporarily unavailable"],
                "weaknesses": ["Analysis temporarily unavailable"],
                "recommendations": ["Please try again later"],
                "overall_assessment": "Profile analysis could not be completed at this time"
            })
            
            logger.info(f"✅ [AI_CACHE] Parsed OpenAI response with keys: {list(analysis.keys())}")
            return analysis
            
        except Exception as e:
            logger.error(f"💥 [AI_CACHE] Error generating profile analysis: {str(e)}")
            import traceback
            logger.error(f"💥 [AI_CACHE] Traceback: {traceback.format_exc()}")
            
            # If OpenAI fails, use enhanced fallback
            logger.info(f"🔄 [AI_CACHE] OpenAI failed, using enhanced fallback for user {user_id}")
            return await self._generate_enhanced_fallback_analysis(user_id)
    
    async def _generate_enhanced_fallback_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Generate enhanced fallback analysis when OpenAI is unavailable"""
        try:
            # Get user data from database
            db = await get_database()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user_doc:
                return None
            
            # Use the existing profile scoring service for basic analysis
            from app.services.user_service import UserService
            from app.models.user import UserInDB
            
            # Convert user doc to UserInDB model
            user_service = UserService()
            user = await user_service.get_user_by_id(user_id)
            
            if not user:
                return None
            
            # Get basic scoring analysis
            basic_analysis = user_service.profile_scoring_service.get_profile_analysis(user)
            
            # Enhance it with better format for new UI
            enhanced_analysis = {
                "profile_score": basic_analysis.get("score", 50),
                "overall_assessment": f"Your profile shows {basic_analysis.get('score', 50)}% completeness. " + 
                                    ("You have a strong foundation with room for strategic improvements." if basic_analysis.get('score', 0) > 60 
                                     else "Focus on adding more detailed information to make your profile stand out."),
                "strengths": basic_analysis.get("strengths", ["Profile information is structured and organized"]),
                "weaknesses": basic_analysis.get("weaknesses", ["Consider adding more detailed information"]),
                "recommendations": [
                    "Add a compelling professional summary highlighting your key achievements",
                    "Include specific metrics and numbers in your experience descriptions", 
                    "Ensure all contact information is complete and professional",
                    "Consider adding relevant certifications for your field",
                    "Include links to your best work or portfolio projects"
                ],
                "section_scores": basic_analysis.get("section_scores", {}),
                "analysis_type": "enhanced_fallback"
            }
            
            logger.info(f"✅ [AI_CACHE] Generated enhanced fallback analysis for user {user_id}")
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"💥 [AI_CACHE] Error generating enhanced fallback: {str(e)}")
            return None
    
    async def _generate_public_analysis(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Generate public analysis using existing professional fit analysis"""
        try:
            logger.info(f"🤖 [AI_CACHE] Starting public analysis generation for user {user_id}")
            
            # Get user data directly from database to avoid circular imports
            db = await get_database()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            
            if not user_doc:
                logger.error(f"❌ [AI_CACHE] User {user_id} not found in database")
                return None
            
            logger.info(f"✅ [AI_CACHE] User data retrieved for {user_doc.get('name', 'Unknown')}")
            
            # Use existing professional fit analysis directly
            analysis = await self.ai_service.analyze_professional_fit(user_doc)
            
            if analysis:
                logger.info(f"✅ [AI_CACHE] Generated public analysis with keys: {list(analysis.keys())}")
            else:
                logger.error(f"❌ [AI_CACHE] Failed to generate public analysis")
            
            return analysis
            
        except Exception as e:
            logger.error(f"💥 [AI_CACHE] Error generating public analysis: {str(e)}")
            import traceback
            logger.error(f"💥 [AI_CACHE] Traceback: {traceback.format_exc()}")
            return None
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cached analyses for a user"""
        try:
            db = await get_database()
            result = await db.ai_analysis.delete_many({"user_id": user_id})
            logger.info(f"Invalidated {result.deleted_count} cached analyses for user {user_id}")
        except Exception as e:
            logger.error(f"Error invalidating cache for user {user_id}: {str(e)}")
    
    async def get_all_analyses_for_admin(self, limit: int = 50, skip: int = 0):
        """Get all analyses for admin panel"""
        try:
            db = await get_database()
            
            pipeline = [
                {
                    "$lookup": {
                        "from": "users",
                        "let": {"user_id": {"$toObjectId": "$user_id"}},
                        "pipeline": [
                            {"$match": {"$expr": {"$eq": ["$_id", "$$user_id"]}}},
                            {"$project": {"name": 1, "email": 1, "designation": 1}}
                        ],
                        "as": "user_info"
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$skip": skip},
                {"$limit": limit}
            ]
            
            analyses = await db.ai_analysis.aggregate(pipeline).to_list(length=limit)
            
            result = []
            for analysis in analyses:
                user_info = analysis.get("user_info", [{}])[0]
                result.append({
                    "id": str(analysis["_id"]),
                    "user_id": analysis["user_id"],
                    "user_name": user_info.get("name", "Unknown"),
                    "user_email": user_info.get("email", "Unknown"),
                    "analysis_type": analysis["analysis_type"],
                    "created_at": analysis["created_at"],
                    "has_data": bool(analysis.get("analysis_data"))
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching analyses for admin: {str(e)}")
            return []