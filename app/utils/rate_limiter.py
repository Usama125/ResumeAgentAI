from datetime import datetime, timedelta
from typing import Dict
from bson import ObjectId
from app.database import get_database
from app.config import settings

class RateLimiter:
    def __init__(self):
        self.daily_limit = settings.DAILY_REQUEST_LIMIT

    async def check_rate_limit(self, user_id: str) -> Dict[str, any]:
        """Check if user has exceeded daily rate limit"""
        db = await get_database()
        user_collection = db.users
        
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise Exception("User not found")
        
        now = datetime.utcnow()
        last_reset = user.get("last_request_reset", now)
        
        # Reset counter if it's a new day
        if now.date() > last_reset.date():
            await user_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "daily_requests": 0,
                        "last_request_reset": now
                    }
                }
            )
            daily_requests = 0
        else:
            daily_requests = user.get("daily_requests", 0)
        
        # Check if limit exceeded
        if daily_requests >= self.daily_limit:
            time_until_reset = datetime.combine(now.date() + timedelta(days=1), datetime.min.time()) - now
            return {
                "allowed": False,
                "remaining": 0,
                "reset_in_seconds": int(time_until_reset.total_seconds()),
                "message": "Daily request limit exceeded"
            }
        
        # Increment counter
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"daily_requests": 1}}
        )
        
        return {
            "allowed": True,
            "remaining": self.daily_limit - daily_requests - 1,
            "reset_in_seconds": None,
            "message": "Request allowed"
        }

rate_limiter = RateLimiter()