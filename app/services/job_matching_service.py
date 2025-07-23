from typing import List, Dict, Any
from app.database import get_database
from app.models.job_matching import JobMatchResult, MatchingCriteria, MatchingExplanation
from app.services.ai_service import AIService
from app.services.user_service import UserService
from app.utils.job_matching_cache import job_matching_cache
import logging

logger = logging.getLogger(__name__)

class JobMatchingService:
    def __init__(self):
        self.ai_service = AIService()
        self.user_service = UserService()

    async def find_matching_candidates(self, 
                                     query: str, 
                                     location: str = None,
                                     experience_level: str = None,
                                     limit: int = 10, 
                                     skip: int = 0) -> List[JobMatchResult]:
        """
        Find candidates matching a job description with AI-powered percentage matching
        """
        try:
            # Get all active candidates (completed onboarding)
            candidates = await self._get_active_candidates(limit * 3, skip)  # Get more to filter
            
            if not candidates:
                return []
            
            # Analyze each candidate against the job query
            matching_results = []
            
            for candidate in candidates:
                try:
                    # Get full user profile
                    user_profile = await self.user_service.get_user_by_id(candidate["_id"])
                    if not user_profile:
                        continue
                        
                    # Check cache first
                    cached_result = await job_matching_cache.get_cached_result(
                        query, user_profile.dict()
                    )
                    
                    if cached_result:
                        ai_analysis = cached_result
                        logger.info(f"Using cached result for user {user_profile.id}")
                    else:
                        # Analyze job match using AI
                        ai_analysis = self.ai_service.analyze_job_match(
                            user_profile.dict(), 
                            query
                        )
                        
                        # Cache the result
                        await job_matching_cache.cache_result(
                            query, user_profile.dict(), ai_analysis
                        )
                    
                    # Convert to JobMatchResult
                    match_result = self._create_match_result(user_profile, ai_analysis, query)
                    matching_results.append(match_result)
                    
                except Exception as e:
                    logger.error(f"Error analyzing candidate {candidate.get('_id', 'unknown')}: {str(e)}")
                    continue
            
            # Sort by matching score (highest first)
            matching_results.sort(key=lambda x: x.matching_score, reverse=True)
            
            # Apply additional filters
            if location:
                matching_results = [r for r in matching_results 
                                  if location.lower() in r.location.lower()]
            
            # Apply experience level filter if specified
            if experience_level:
                matching_results = self._filter_by_experience_level(matching_results, experience_level)
            
            # Return top matches
            return matching_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in find_matching_candidates: {str(e)}")
            return []

    async def _get_active_candidates(self, limit: int, skip: int) -> List[Dict[str, Any]]:
        """Get active candidates from database"""
        try:
            db = await get_database()
            
            # For now, we'll search all users since onboarding_completed might not be set properly
            # In production, add: {"onboarding_completed": True, "is_looking_for_job": True}
            search_filter = {"is_looking_for_job": True}
            
            cursor = db.users.find(search_filter).skip(skip).limit(limit)
            candidates = await cursor.to_list(length=limit)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error getting active candidates: {str(e)}")
            return []

    def _create_match_result(self, user_profile: Any, ai_analysis: Dict[str, Any], query: str) -> JobMatchResult:
        """Create JobMatchResult from user profile and AI analysis"""
        
        # Extract matching criteria from AI analysis
        matching_criteria = MatchingCriteria(
            skills_match=ai_analysis.get('skills_match', 0.0),
            experience_match=ai_analysis.get('experience_match', 0.0),
            location_match=ai_analysis.get('location_match', 0.0),
            certification_match=ai_analysis.get('certification_match', 0.0),
            overall_match=ai_analysis.get('overall_match', 0.0)
        )
        
        # Create minimal explanation (no detailed text to save tokens)
        explanation = MatchingExplanation(
            strengths=["Available on request"],
            gaps=["Available on request"],
            recommendations=["Available on request"]
        )
        
        # Convert skills to dict format
        skills_dict = []
        for skill in user_profile.skills:
            skills_dict.append({
                "name": skill.name,
                "level": skill.level,
                "years": skill.years
            })
        
        return JobMatchResult(
            user_id=str(user_profile.id),
            name=user_profile.name,
            designation=user_profile.designation or "Not specified",
            location=user_profile.location or "Not specified",
            profile_picture=user_profile.profile_picture,
            experience=user_profile.experience or "Not specified",
            summary=user_profile.summary or "No summary available",
            skills=skills_dict,
            certifications=user_profile.certifications,
            matching_score=ai_analysis.get('overall_match', 0.0),
            matching_criteria=matching_criteria,
            explanation=explanation,
            is_looking_for_job=user_profile.is_looking_for_job,
            rating=user_profile.rating
        )

    def _filter_by_experience_level(self, results: List[JobMatchResult], experience_level: str) -> List[JobMatchResult]:
        """Filter results by experience level"""
        experience_level = experience_level.lower()
        
        if "senior" in experience_level or "lead" in experience_level:
            # Looking for senior candidates (5+ years)
            return [r for r in results if self._extract_years_from_experience(r.experience) >= 5]
        elif "mid" in experience_level or "intermediate" in experience_level:
            # Looking for mid-level candidates (2-5 years)
            years = self._extract_years_from_experience
            return [r for r in results if 2 <= years(r.experience) <= 5]
        elif "junior" in experience_level or "entry" in experience_level:
            # Looking for junior candidates (0-2 years)
            return [r for r in results if self._extract_years_from_experience(r.experience) <= 2]
        
        return results

    def _extract_years_from_experience(self, experience_str: str) -> int:
        """Extract years from experience string"""
        try:
            import re
            # Look for patterns like "5 years", "5+ years", "5-7 years"
            match = re.search(r'(\d+)', experience_str)
            if match:
                return int(match.group(1))
            return 0
        except:
            return 0

    async def get_job_match_summary(self, query: str) -> Dict[str, Any]:
        """Get summary statistics for job matching"""
        try:
            candidates = await self.find_matching_candidates(query, limit=50)
            
            if not candidates:
                return {
                    "total_candidates": 0,
                    "high_match_count": 0,
                    "medium_match_count": 0,
                    "low_match_count": 0,
                    "average_match_score": 0.0
                }
            
            total = len(candidates)
            high_match = len([c for c in candidates if c.matching_score >= 70])
            medium_match = len([c for c in candidates if 40 <= c.matching_score < 70])
            low_match = len([c for c in candidates if c.matching_score < 40])
            avg_score = sum(c.matching_score for c in candidates) / total
            
            return {
                "total_candidates": total,
                "high_match_count": high_match,
                "medium_match_count": medium_match,
                "low_match_count": low_match,
                "average_match_score": round(avg_score, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting job match summary: {str(e)}")
            return {
                "total_candidates": 0,
                "high_match_count": 0,
                "medium_match_count": 0,
                "low_match_count": 0,
                "average_match_score": 0.0
            }