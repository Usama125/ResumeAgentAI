import hashlib
import hmac
import time
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SecureAPIAuth:
    def __init__(self):
        self.allowed_origins = settings.BACKEND_CORS_ORIGINS
        self.secret_key = settings.FRONTEND_API_SECRET
        self.request_timeout = 300  # 5 minutes
        
    def generate_client_secret(self) -> str:
        """Generate a rotating secret for client-side signing"""
        timestamp = int(time.time())
        # Generate secret that rotates every hour
        hour_seed = timestamp // 3600
        return hashlib.sha256(f"{self.secret_key}:{hour_seed}".encode()).hexdigest()[:32]
    
    def verify_request_signature(self, request: Request) -> bool:
        """Verify request signature with multiple validation layers"""
        try:
            # 1. Check required headers
            timestamp = request.headers.get("X-Timestamp")
            signature = request.headers.get("X-Signature")
            nonce = request.headers.get("X-Nonce")
            
            if not all([timestamp, signature, nonce]):
                logger.warning("Missing required security headers")
                return False
            
            # 2. Verify timestamp (prevent replay attacks)
            try:
                request_time = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - request_time) > self.request_timeout:
                    logger.warning(f"Request timestamp too old: {request_time} vs {current_time}")
                    return False
            except ValueError:
                logger.warning("Invalid timestamp format")
                return False
            
            # 3. Verify origin and referrer
            origin = request.headers.get("Origin")
            referrer = request.headers.get("Referer")
            
            if not self._is_valid_origin(origin, referrer):
                logger.warning(f"Invalid origin: {origin}, referrer: {referrer}")
                return False
            
            # 4. Verify signature
            client_secret = self.generate_client_secret()
            expected_signature = self._generate_signature(
                request.method,
                str(request.url),
                timestamp,
                nonce,
                client_secret
            )
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid request signature")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying request signature: {str(e)}")
            return False
    
    def _is_valid_origin(self, origin: Optional[str], referrer: Optional[str]) -> bool:
        """Validate request origin and referrer"""
        if not origin and not referrer:
            return False
        
        valid_origins = [
            "http://localhost:3000",
            "https://resume-agent-frontend.vercel.app",
            "http://127.0.0.1:3000",
            "https://your-frontend-domain.com",  # Replace with your actual domain
            "https://www.your-frontend-domain.com"
        ]
        
        if origin and origin not in valid_origins:
            return False
        
        if referrer:
            for valid_origin in valid_origins:
                if referrer.startswith(valid_origin):
                    return True
            return False
        
        return True
    
    def _generate_signature(self, method: str, url: str, timestamp: str, nonce: str, secret: str) -> str:
        """Generate HMAC signature for request"""
        # Create signature string
        sig_string = f"{method}:{url}:{timestamp}:{nonce}"
        
        # Generate HMAC
        signature = hmac.new(
            secret.encode('utf-8'),
            sig_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_ip_rate_limit(self, client_ip: str) -> bool:
        """Simple IP-based rate limiting (in production, use Redis)"""
        # This is a basic implementation - in production, use Redis or database
        # For now, we'll just return True and implement proper rate limiting later
        return True

# Global instance
secure_auth = SecureAPIAuth()

async def verify_secure_request(request: Request) -> bool:
    """Dependency to verify secure request"""
    
    # Get client IP
    client_ip = request.client.host
    
    # Check IP rate limit
    if not secure_auth.verify_ip_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Verify request signature and origin
    if not secure_auth.verify_request_signature(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature"
        )
    
    return True

# Client-side JavaScript helper (for frontend integration)
CLIENT_SIDE_JS = '''
class SecureAPIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.clientSecret = null;
        this.lastSecretUpdate = 0;
    }
    
    async updateClientSecret() {
        const now = Date.now();
        // Update secret every hour
        if (!this.clientSecret || now - this.lastSecretUpdate > 3600000) {
            // In production, get this from your backend's public endpoint
            // For now, we'll generate it client-side (less secure but functional)
            const hourSeed = Math.floor(Date.now() / 3600000);
            this.clientSecret = await this.generateSecret(hourSeed);
            this.lastSecretUpdate = now;
        }
    }
    
    async generateSecret(seed) {
        // This should match your backend's secret generation logic
        // In production, get this from a secure endpoint
        const encoder = new TextEncoder();
        const data = encoder.encode(`your-secret-key:${seed}`);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex.substring(0, 32);
    }
    
    generateNonce() {
        return Math.random().toString(36).substring(2, 15) + 
               Math.random().toString(36).substring(2, 15);
    }
    
    async generateSignature(method, url, timestamp, nonce) {
        await this.updateClientSecret();
        
        const sigString = `${method}:${url}:${timestamp}:${nonce}`;
        const encoder = new TextEncoder();
        const keyData = encoder.encode(this.clientSecret);
        const messageData = encoder.encode(sigString);
        
        const key = await crypto.subtle.importKey(
            'raw',
            keyData,
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        
        const signature = await crypto.subtle.sign('HMAC', key, messageData);
        const signatureArray = Array.from(new Uint8Array(signature));
        return signatureArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    
    async secureRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const method = options.method || 'GET';
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const nonce = this.generateNonce();
        
        const signature = await this.generateSignature(method, url, timestamp, nonce);
        
        const headers = {
            'Content-Type': 'application/json',
            'X-Timestamp': timestamp,
            'X-Signature': signature,
            'X-Nonce': nonce,
            ...options.headers
        };
        
        return fetch(url, {
            ...options,
            method,
            headers,
            credentials: 'same-origin'
        });
    }
}

// Usage example:
// const apiClient = new SecureAPIClient('http://localhost:8000/api/v1');
// const response = await apiClient.secureRequest('/job-matching/search?q=React developer');
'''