from fastapi import HTTPException, Header, status
from app.config import settings
import hashlib
import hmac
from typing import Optional

class APIKeyAuth:
    def __init__(self):
        self.api_key = settings.FRONTEND_API_KEY
        self.api_secret = settings.FRONTEND_API_SECRET
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key matches the expected key"""
        return hmac.compare_digest(self.api_key, api_key)
    
    def verify_request_signature(self, signature: str, timestamp: str, request_body: str = "") -> bool:
        """Verify request signature using HMAC"""
        try:
            # Create the string to sign
            string_to_sign = f"{timestamp}:{request_body}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.api_secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

# Global instance
api_key_auth = APIKeyAuth()

def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> bool:
    """Dependency to verify API key"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    if not api_key_auth.verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True

def verify_request_signature(
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp")
) -> bool:
    """Dependency to verify request signature (more secure option)"""
    if not x_signature or not x_timestamp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Request signature and timestamp are required"
        )
    
    if not api_key_auth.verify_request_signature(x_signature, x_timestamp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature"
        )
    
    return True