from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.models.user import UserCreate, UserInDB
from app.utils.security import get_password_hash, verify_password
from datetime import datetime, timedelta
import secrets

class AuthService:
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        db = await get_database()
        user_data = await db.users.find_one({"email": email})
        if user_data:
            user_data["_id"] = str(user_data["_id"])
            return UserInDB(**user_data)
        return None

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

    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        db = await get_database()
        user_data = await db.users.find_one({"username": username})
        if user_data:
            user_data["_id"] = str(user_data["_id"])
            return UserInDB(**user_data)
        return None

    async def create_user(self, user: UserCreate) -> UserInDB:
        """Create new user"""
        db = await get_database()
        
        # Hash password
        hashed_password = get_password_hash(user.password)
        
        # Create user document
        user_dict = user.dict()
        del user_dict["password"]
        user_dict["hashed_password"] = hashed_password
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        user_dict["onboarding_completed"] = False
        user_dict["onboarding_skipped"] = False
        user_dict["daily_requests"] = 0
        user_dict["last_request_reset"] = datetime.utcnow()
        user_dict["rating"] = 4.5
        user_dict["job_matching_request_timestamps"] = []
        user_dict["chat_request_timestamps"] = []
        
        result = await db.users.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        
        return UserInDB(**user_dict)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def store_refresh_token(self, user_id: str, jti: str, expires_at: datetime) -> bool:
        """Store refresh token JTI for user"""
        try:
            db = await get_database()
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "refresh_token_jti": jti,
                        "refresh_token_expires_at": expires_at,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def verify_refresh_token(self, user_id: str, jti: str) -> bool:
        """Verify if refresh token JTI is valid for user"""
        try:
            db = await get_database()
            user_data = await db.users.find_one({
                "_id": ObjectId(user_id),
                "refresh_token_jti": jti,
                "refresh_token_expires_at": {"$gt": datetime.utcnow()}
            })
            return user_data is not None
        except Exception:
            return False
    
    async def revoke_refresh_token(self, user_id: str) -> bool:
        """Revoke refresh token for user"""
        try:
            db = await get_database()
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$unset": {
                        "refresh_token_jti": "",
                        "refresh_token_expires_at": ""
                    },
                    "$set": {
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def create_password_reset_token(self, user_id: str) -> Optional[str]:
        """Create and store password reset token for user"""
        try:
            # Generate secure random token
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
            
            db = await get_database()
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_reset_token": reset_token,
                        "password_reset_expires_at": expires_at,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                return reset_token
            return None
        except Exception:
            return None
    
    async def verify_password_reset_token(self, token: str) -> Optional[UserInDB]:
        """Verify password reset token and return user if valid"""
        try:
            db = await get_database()
            user_data = await db.users.find_one({
                "password_reset_token": token,
                "password_reset_expires_at": {"$gt": datetime.utcnow()}
            })
            
            if user_data:
                user_data["_id"] = str(user_data["_id"])
                return UserInDB(**user_data)
            return None
        except Exception:
            return None
    
    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """Reset user password and clear reset token"""
        try:
            # Hash new password
            hashed_password = get_password_hash(new_password)
            
            db = await get_database()
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "password_reset_token": "",
                        "password_reset_expires_at": "",
                        "refresh_token_jti": "",  # Invalidate existing sessions
                        "refresh_token_expires_at": ""
                    }
                }
            )
            
            return result.modified_count > 0
        except Exception:
            return False
    
    async def update_user_google_id(self, user_id: str, google_id: str) -> bool:
        """Update user's Google ID"""
        try:
            db = await get_database()
            result = await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "google_id": google_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception:
            return False