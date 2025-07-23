import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.database import get_database
import logging

logger = logging.getLogger(__name__)

class JobMatchingCache:
    def __init__(self, cache_duration_hours: int = 24):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.collection_name = "job_matching_cache"

    def _generate_cache_key(self, job_query: str, user_profile: Dict[str, Any]) -> str:
        """Generate a unique cache key for job query + user profile combination"""
        # Create a simplified profile hash (only relevant fields)
        profile_key = {
            'skills': user_profile.get('skills', []),
            'experience': user_profile.get('experience', ''),
            'certifications': user_profile.get('certifications', []),
            'location': user_profile.get('location', ''),
            'designation': user_profile.get('designation', ''),
            'summary': user_profile.get('summary', '')
        }
        
        # Combine query and profile
        cache_data = {
            'query': job_query.lower().strip(),
            'profile': profile_key
        }
        
        # Generate hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def get_cached_result(self, job_query: str, user_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached job matching result if available and not expired"""
        try:
            cache_key = self._generate_cache_key(job_query, user_profile)
            
            db = await get_database()
            cache_collection = db[self.collection_name]
            
            cached_item = await cache_collection.find_one({"cache_key": cache_key})
            
            if cached_item:
                # Check if cache is still valid
                cached_time = cached_item.get('created_at')
                if datetime.utcnow() - cached_time < self.cache_duration:
                    logger.info(f"Cache hit for key: {cache_key}")
                    return cached_item.get('result')
                else:
                    # Cache expired, remove it
                    await cache_collection.delete_one({"cache_key": cache_key})
                    logger.info(f"Cache expired for key: {cache_key}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    async def cache_result(self, job_query: str, user_profile: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Cache job matching result"""
        try:
            cache_key = self._generate_cache_key(job_query, user_profile)
            
            db = await get_database()
            cache_collection = db[self.collection_name]
            
            cache_item = {
                "cache_key": cache_key,
                "job_query": job_query,
                "user_id": str(user_profile.get('id', '')),
                "result": result,
                "created_at": datetime.utcnow()
            }
            
            # Upsert the cache item
            await cache_collection.update_one(
                {"cache_key": cache_key},
                {"$set": cache_item},
                upsert=True
            )
            
            logger.info(f"Cached result for key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")
            return False

    async def clear_expired_cache(self) -> int:
        """Clear expired cache entries"""
        try:
            db = await get_database()
            cache_collection = db[self.collection_name]
            
            expiry_time = datetime.utcnow() - self.cache_duration
            
            result = await cache_collection.delete_many({
                "created_at": {"$lt": expiry_time}
            })
            
            logger.info(f"Cleared {result.deleted_count} expired cache entries")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error clearing expired cache: {str(e)}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            db = await get_database()
            cache_collection = db[self.collection_name]
            
            total_entries = await cache_collection.count_documents({})
            
            # Count recent entries (last 24 hours)
            recent_time = datetime.utcnow() - timedelta(hours=24)
            recent_entries = await cache_collection.count_documents({
                "created_at": {"$gte": recent_time}
            })
            
            return {
                "total_entries": total_entries,
                "recent_entries": recent_entries,
                "cache_duration_hours": self.cache_duration.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "total_entries": 0,
                "recent_entries": 0,
                "cache_duration_hours": 24
            }

# Global cache instance
job_matching_cache = JobMatchingCache()