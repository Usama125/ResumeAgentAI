from datetime import datetime, timedelta
from typing import Dict, Optional, List
from bson import ObjectId
from app.database import get_database
from app.config import settings
import hashlib
import json
import logging
from dateutil.parser import isoparse

logger = logging.getLogger(__name__)

class AdvancedRateLimiter:
    """
    Advanced rate limiter with enhanced fingerprinting to prevent bypass attempts
    """
    
    def __init__(self):
        # Job matching limits
        self.unauth_job_matching_limit = settings.UNAUTH_DAILY_JOB_MATCHING_LIMIT
        self.auth_job_matching_limit = settings.AUTH_DAILY_JOB_MATCHING_LIMIT
        
        # Chat limits
        self.unauth_chat_limit = settings.UNAUTH_DAILY_CHAT_LIMIT
        self.auth_chat_limit = settings.AUTH_DAILY_CHAT_LIMIT
        
        # Content generation limits
        self.unauth_content_generation_limit = settings.UNAUTH_DAILY_CONTENT_GENERATION_LIMIT
        self.auth_content_generation_limit = settings.AUTH_DAILY_CONTENT_GENERATION_LIMIT

    def _create_device_fingerprint(self, request_data: dict) -> str:
        """
        Create a more robust device fingerprint that's harder to bypass
        """
        # Core identification data
        ip_address = request_data.get('ip_address', 'unknown')
        user_agent = request_data.get('user_agent', 'unknown')
        
        # Additional fingerprinting data
        accept_language = request_data.get('accept_language', '')
        accept_encoding = request_data.get('accept_encoding', '')
        accept = request_data.get('accept', '')
        
        # Screen resolution and timezone (if available from frontend)
        screen_info = request_data.get('screen_info', '')
        timezone = request_data.get('timezone', '')
        
        # Create comprehensive fingerprint
        fingerprint_data = f"{ip_address}:{user_agent}:{accept_language}:{accept_encoding}:{accept}:{screen_info}:{timezone}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def _get_ip_subnet(self, ip_address: str) -> str:
        """
        Get IP subnet to catch users from same network/ISP
        """
        try:
            # For IPv4, use /24 subnet (e.g., 192.168.1.x becomes 192.168.1.0)
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        except:
            pass
        return ip_address

    async def _get_all_client_identifiers(self, request_data: dict) -> List[str]:
        """
        Generate multiple identifiers to track potential bypass attempts
        """
        ip_address = request_data.get('ip_address', 'unknown')
        
        identifiers = []
        
        # 1. Device fingerprint (primary)
        identifiers.append({
            'type': 'fingerprint',
            'id': self._create_device_fingerprint(request_data),
            'weight': 1.0  # Full weight
        })
        
        # 2. IP address only (catches VPN switching with same device)
        identifiers.append({
            'type': 'ip_only',
            'id': hashlib.sha256(ip_address.encode()).hexdigest(),
            'weight': 0.7  # Partial weight
        })
        
        # 3. IP subnet (catches users from same ISP/network)
        subnet = self._get_ip_subnet(ip_address)
        identifiers.append({
            'type': 'subnet',
            'id': hashlib.sha256(subnet.encode()).hexdigest(),
            'weight': 0.3  # Lower weight
        })
        
        return identifiers

    async def _check_multiple_identifiers(self, db, identifiers: List[dict], request_type: str, daily_limit: int) -> Dict[str, any]:
        """
        Check rate limits across multiple identifiers with weighted scoring and rolling window
        """
        now = datetime.utcnow()
        window_hours = settings.RATE_LIMIT_RESET_HOURS
        window_start = now - timedelta(hours=window_hours)
        total_weighted_requests = 0
        soonest_reset_seconds = None
        for identifier_info in identifiers:
            identifier = identifier_info['id']
            weight = identifier_info['weight']
            record = await db.rate_limits.find_one({
                "client_id": identifier,
                "request_type": request_type
            })
            timestamps = []
            if record and "timestamps" in record:
                timestamps = [isoparse(ts) if isinstance(ts, str) else ts for ts in record["timestamps"]]
                timestamps = [ts for ts in timestamps if ts > window_start]
            count = len(timestamps)
            total_weighted_requests += count * weight
            if timestamps:
                oldest = min(timestamps)
                reset_seconds = int((oldest + timedelta(hours=window_hours) - now).total_seconds())
                if soonest_reset_seconds is None or reset_seconds < soonest_reset_seconds:
                    soonest_reset_seconds = reset_seconds
            logger.info(f"Found {count} requests for {identifier_info['type']} (weight: {weight}) in rolling window")
        if total_weighted_requests >= daily_limit:
            # If for some reason soonest_reset_seconds is None (shouldn't happen), default to window_hours*3600
            reset_seconds = soonest_reset_seconds if soonest_reset_seconds is not None else window_hours * 3600
            return {
                "allowed": False,
                "remaining": 0,
                "reset_in_seconds": max(1, reset_seconds),
                "message": self._get_enhanced_limit_message(request_type, daily_limit, total_weighted_requests),
                "is_authenticated": False,
                "detection_method": "multi_identifier"
            }
        return {"allowed": True, "weighted_count": total_weighted_requests}

    async def _increment_all_identifiers(self, db, identifiers: List[dict], request_type: str):
        """
        Increment counters for all identifiers and store timestamps for rolling window
        """
        now = datetime.utcnow()
        window_hours = settings.RATE_LIMIT_RESET_HOURS
        window_start = now - timedelta(hours=window_hours)
        for identifier_info in identifiers:
            identifier = identifier_info['id']
            # Upsert the record and push the new timestamp, also prune old timestamps
            record = await db.rate_limits.find_one({
                "client_id": identifier,
                "request_type": request_type
            })
            timestamps = []
            if record and "timestamps" in record:
                timestamps = [isoparse(ts) if isinstance(ts, str) else ts for ts in record["timestamps"]]
                timestamps = [ts for ts in timestamps if ts > window_start]
            timestamps.append(now)
            # Store as ISO strings
            timestamps_to_store = [ts.isoformat() for ts in timestamps]
            await db.rate_limits.update_one(
                {
                    "client_id": identifier,
                    "request_type": request_type
                },
                {
                    "$set": {"updated_at": now, "timestamps": timestamps_to_store, "identifier_type": identifier_info['type']},
                    "$setOnInsert": {"created_at": now}
                },
                upsert=True
            )

    async def check_job_matching_limit(self, user_id: Optional[str] = None, request_data: dict = None) -> Dict[str, any]:
        """Check job matching rate limit with enhanced tracking"""
        db = await get_database()
        
        if user_id:
            # Authenticated user - use existing logic (already secure)
            return await self._check_authenticated_limit(
                db, user_id, "job_matching", self.auth_job_matching_limit
            )
        else:
            # Unauthenticated user - use enhanced multi-identifier tracking
            identifiers = await self._get_all_client_identifiers(request_data or {})
            
            # Check limits across all identifiers
            result = await self._check_multiple_identifiers(
                db, identifiers, "job_matching", self.unauth_job_matching_limit
            )
            
            if not result["allowed"]:
                return result
            
            # Increment all identifiers
            await self._increment_all_identifiers(db, identifiers, "job_matching")
            
            return {
                "allowed": True,
                "remaining": max(0, self.unauth_job_matching_limit - int(result["weighted_count"]) - 1),
                "reset_in_seconds": None,
                "message": "Request allowed",
                "is_authenticated": False
            }

    async def check_chat_limit(self, user_id: Optional[str] = None, request_data: dict = None) -> Dict[str, any]:
        """Check chat rate limit with enhanced tracking"""
        db = await get_database()
        
        if user_id:
            # Authenticated user - use existing logic (already secure)
            return await self._check_authenticated_limit(
                db, user_id, "chat", self.auth_chat_limit
            )
        else:
            # Unauthenticated user - use enhanced multi-identifier tracking
            identifiers = await self._get_all_client_identifiers(request_data or {})
            
            # Check limits across all identifiers
            result = await self._check_multiple_identifiers(
                db, identifiers, "chat", self.unauth_chat_limit
            )
            
            if not result["allowed"]:
                return result
            
            # Increment all identifiers
            await self._increment_all_identifiers(db, identifiers, "chat")
            
            return {
                "allowed": True,
                "remaining": max(0, self.unauth_chat_limit - int(result["weighted_count"]) - 1),
                "reset_in_seconds": None,
                "message": "Request allowed",
                "is_authenticated": False
            }

    async def check_content_generation_limit(self, user_id: Optional[str] = None, request_data: dict = None) -> Dict[str, any]:
        """Check content generation rate limit with enhanced tracking"""
        db = await get_database()
        
        if user_id:
            # Authenticated user - use existing logic (already secure)
            return await self._check_authenticated_limit(
                db, user_id, "content_generation", self.auth_content_generation_limit
            )
        else:
            # Unauthenticated user - use enhanced multi-identifier tracking
            identifiers = await self._get_all_client_identifiers(request_data or {})
            
            # Check limits across all identifiers
            result = await self._check_multiple_identifiers(
                db, identifiers, "content_generation", self.unauth_content_generation_limit
            )
            
            if not result["allowed"]:
                return result
            
            # Increment all identifiers
            await self._increment_all_identifiers(db, identifiers, "content_generation")
            
            return {
                "allowed": True,
                "remaining": max(0, self.unauth_content_generation_limit - int(result["weighted_count"]) - 1),
                "reset_in_seconds": None,
                "message": "Request allowed",
                "is_authenticated": False
            }

    async def _check_authenticated_limit(self, db, user_id: str, request_type: str, daily_limit: int) -> Dict[str, any]:
        """Check rate limit for authenticated users (SECURE - cannot be bypassed)"""
        user_collection = db.users
        try:
            user = await user_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise Exception("User not found")
        except Exception as e:
            logger.error(f"Error finding user {user_id}: {e}")
            raise Exception("Invalid user ID")
        now = datetime.utcnow()
        window_hours = settings.RATE_LIMIT_RESET_HOURS
        window_start = now - timedelta(hours=window_hours)
        field_name = f"daily_{request_type}_requests"
        reset_field = f"last_{request_type}_reset"
        timestamps_field = f"{request_type}_request_timestamps"
        timestamps = user.get(timestamps_field, [])
        # Parse ISO strings to datetime
        timestamps = [isoparse(ts) if isinstance(ts, str) else ts for ts in timestamps]
        # Only keep timestamps within the window
        timestamps = [ts for ts in timestamps if ts > window_start]
        daily_requests = len(timestamps)
        if daily_requests >= daily_limit:
            oldest = min(timestamps)
            reset_seconds = int((oldest + timedelta(hours=window_hours) - now).total_seconds())
            return {
                "allowed": False,
                "remaining": 0,
                "reset_in_seconds": max(1, reset_seconds),
                "message": self._get_enhanced_limit_message(request_type, daily_limit, daily_requests, True),
                "is_authenticated": True
            }
        # Increment counter and store timestamp
        timestamps.append(now)
        timestamps_to_store = [ts.isoformat() for ts in timestamps]
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {timestamps_field: timestamps_to_store, "updated_at": now}}
        )
        return {
            "allowed": True,
            "remaining": daily_limit - daily_requests - 1,
            "reset_in_seconds": None,
            "message": "Request allowed",
            "is_authenticated": True
        }

    def _get_enhanced_limit_message(self, request_type: str, daily_limit: int, current_count: float, is_authenticated: bool = False) -> str:
        """Generate enhanced limit exceeded messages"""
        user_type = "registered user" if is_authenticated else "guest"
        
        base_messages = {
            "job_matching": f"🎯 Hold up there, search champion! You've reached your daily job matching limit of {daily_limit} requests as a {user_type}. Your dedication to finding the perfect match is admirable! 🚀",
            "chat": f"💬 Whoa there, social butterfly! You've hit your daily chat limit of {daily_limit} conversations as a {user_type}. Your networking game is strong! 🤝",
            "content_generation": f"✨ Wow! You've reached your daily content generation limit of {daily_limit} creations as a {user_type}. Your productivity is impressive! 📝"
        }
        
        if not is_authenticated:
            signup_encouragement = " 🌟 Pro tip: Registered users get higher limits! Why not join our community? ✨"
            detection_notice = " Our smart system detected multiple access patterns to ensure fair usage for everyone. 🛡️"
            return base_messages.get(request_type, "") + signup_encouragement + detection_notice
        
        return base_messages.get(request_type, "") + " Come back tomorrow for more amazing opportunities! 🌅"

# Global instance
advanced_rate_limiter = AdvancedRateLimiter()