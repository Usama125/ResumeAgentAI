import re
import secrets
import hashlib
from typing import Optional
from app.database import get_database

class UsernameGenerator:
    """Utility class for generating unique usernames"""
    
    @staticmethod
    def normalize_name(full_name: str) -> str:
        """Convert full name to username format (lowercase, no spaces, alphanumeric only)"""
        # Remove extra spaces and convert to lowercase
        normalized = full_name.strip().lower()
        
        # Remove special characters and keep only alphanumeric characters and spaces
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Replace spaces with underscores
        normalized = re.sub(r'\s+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        return normalized
    
    @staticmethod
    def generate_unique_suffix() -> str:
        """Generate a unique 4-character suffix that's memorable"""
        # Use a combination of timestamp and random data for uniqueness
        import time
        timestamp = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
        random_part = secrets.token_hex(2)  # 4 character hex string
        
        # Mix them to create a 4-character suffix
        combined = timestamp + random_part
        hash_obj = hashlib.md5(combined.encode())
        hex_hash = hash_obj.hexdigest()
        
        # Take first 4 characters of hash
        return hex_hash[:4]
    
    @staticmethod
    async def generate_username_from_name(full_name: str, max_attempts: int = 10) -> str:
        """Generate a unique username from full name with automatic suffix if needed"""
        db = await get_database()
        
        # Normalize the name
        base_username = UsernameGenerator.normalize_name(full_name)
        
        # If base username is empty or too short, use a default
        if not base_username or len(base_username) < 3:
            base_username = "user"
        
        # Limit base username to 26 characters to leave room for suffix
        if len(base_username) > 26:
            base_username = base_username[:26]
        
        # First, try the base username without suffix
        if await UsernameGenerator.is_username_available(base_username):
            return base_username
        
        # If base is taken, try with unique suffixes
        for attempt in range(max_attempts):
            suffix = UsernameGenerator.generate_unique_suffix()
            candidate = f"{base_username}_{suffix}"
            
            if await UsernameGenerator.is_username_available(candidate):
                return candidate
        
        # Fallback: use timestamp-based username
        import time
        timestamp_suffix = str(int(time.time()))[-6:]  # Last 6 digits
        fallback_username = f"user_{timestamp_suffix}"
        
        return fallback_username
    
    @staticmethod
    async def is_username_available(username: str) -> bool:
        """Check if username is available in database"""
        try:
            db = await get_database()
            existing_user = await db.users.find_one({"username": username})
            return existing_user is None
        except Exception:
            # If there's any error, assume username is not available for safety
            return False
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, Optional[str]]:
        """Validate username format and return (is_valid, error_message)"""
        if not username:
            return False, "Username is required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 30:
            return False, "Username must be no more than 30 characters long"
        
        # Check if username contains only allowed characters
        if not re.match(r'^[a-z0-9_-]+$', username):
            return False, "Username can only contain lowercase letters, numbers, underscores, and hyphens"
        
        # Check if username starts and ends with alphanumeric character
        if not re.match(r'^[a-z0-9].*[a-z0-9]$', username):
            if len(username) == 1:
                if not re.match(r'^[a-z0-9]$', username):
                    return False, "Username must start with a letter or number"
            else:
                return False, "Username must start and end with a letter or number"
        
        # Check for reserved usernames
        reserved_usernames = {
            'admin', 'root', 'api', 'www', 'ftp', 'mail', 'email', 'user', 'test',
            'support', 'help', 'info', 'contact', 'about', 'privacy', 'terms',
            'login', 'register', 'signin', 'signup', 'auth', 'oauth', 'profile',
            'dashboard', 'home', 'index', 'search', 'blog', 'news', 'system'
        }
        
        if username.lower() in reserved_usernames:
            return False, "This username is reserved and cannot be used"
        
        return True, None