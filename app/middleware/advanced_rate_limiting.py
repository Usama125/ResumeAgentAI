from fastapi import HTTPException, Request, status
from functools import wraps
from typing import Optional, Callable
from app.utils.advanced_rate_limiter import advanced_rate_limiter
from app.routers.auth import get_current_user_optional
import logging

logger = logging.getLogger(__name__)

def get_enhanced_client_info(request: Request) -> dict:
    """
    Extract comprehensive client information for enhanced fingerprinting
    """
    # Get IP address (handles proxies)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "unknown"
    
    # Get browser fingerprinting data
    user_agent = request.headers.get("user-agent", "unknown")
    accept_language = request.headers.get("accept-language", "")
    accept_encoding = request.headers.get("accept-encoding", "")
    accept = request.headers.get("accept", "")
    
    # Additional headers that help with fingerprinting
    dnt = request.headers.get("dnt", "")  # Do Not Track
    upgrade_insecure = request.headers.get("upgrade-insecure-requests", "")
    
    # Check for custom headers from frontend (screen info, timezone, etc.)
    screen_info = request.headers.get("x-screen-info", "")
    timezone = request.headers.get("x-timezone", "")
    canvas_fingerprint = request.headers.get("x-canvas-fp", "")  # If implemented
    
    return {
        "ip_address": ip_address,
        "user_agent": user_agent,
        "accept_language": accept_language,
        "accept_encoding": accept_encoding,
        "accept": accept,
        "dnt": dnt,
        "upgrade_insecure": upgrade_insecure,
        "screen_info": screen_info,
        "timezone": timezone,
        "canvas_fingerprint": canvas_fingerprint
    }

def advanced_rate_limit_job_matching():
    """Enhanced rate limiting decorator for job matching with bypass prevention"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found for rate limiting"
                )
            
            # Try to get current user (optional)
            try:
                current_user = await get_current_user_optional(request)
                user_id = str(current_user.id) if current_user else None
            except:
                user_id = None
            
            # Get enhanced client info
            client_info = get_enhanced_client_info(request)
            
            # Log the attempt for monitoring
            logger.info(f"Job matching request from {'user ' + user_id if user_id else 'anonymous'} - IP: {client_info['ip_address']}")
            
            # Check rate limit with advanced detection
            try:
                rate_limit_result = await advanced_rate_limiter.check_job_matching_limit(
                    user_id=user_id,
                    request_data=client_info
                )
                
                if not rate_limit_result["allowed"]:
                    # Log the rate limit violation
                    detection_method = rate_limit_result.get("detection_method", "standard")
                    logger.warning(f"Rate limit exceeded - Method: {detection_method}, IP: {client_info['ip_address']}, UA: {client_info['user_agent'][:50]}")
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "message": rate_limit_result["message"],
                            "remaining": rate_limit_result["remaining"],
                            "reset_in_seconds": rate_limit_result["reset_in_seconds"],
                            "is_authenticated": rate_limit_result["is_authenticated"],
                            "rate_limit_type": "job_matching",
                            "detection_method": detection_method
                        }
                    )
                
                # Proceed with the request
                response = await func(*args, **kwargs)
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Advanced rate limiting error: {str(e)}")
                # Fallback: continue with request if rate limiting fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def advanced_rate_limit_chat():
    """Enhanced rate limiting decorator for chat with bypass prevention"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found for rate limiting"
                )
            
            # Try to get current user (optional)
            try:
                current_user = await get_current_user_optional(request)
                user_id = str(current_user.id) if current_user else None
            except:
                user_id = None
            
            # Get enhanced client info
            client_info = get_enhanced_client_info(request)
            
            # Log the attempt for monitoring
            logger.info(f"Chat request from {'user ' + user_id if user_id else 'anonymous'} - IP: {client_info['ip_address']}")
            
            # Check rate limit with advanced detection
            try:
                rate_limit_result = await advanced_rate_limiter.check_chat_limit(
                    user_id=user_id,
                    request_data=client_info
                )
                
                if not rate_limit_result["allowed"]:
                    # Log the rate limit violation
                    detection_method = rate_limit_result.get("detection_method", "standard")
                    logger.warning(f"Chat rate limit exceeded - Method: {detection_method}, IP: {client_info['ip_address']}, UA: {client_info['user_agent'][:50]}")
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "message": rate_limit_result["message"],
                            "remaining": rate_limit_result["remaining"],
                            "reset_in_seconds": rate_limit_result["reset_in_seconds"],
                            "is_authenticated": rate_limit_result["is_authenticated"],
                            "rate_limit_type": "chat",
                            "detection_method": detection_method
                        }
                    )
                
                # Proceed with the request
                response = await func(*args, **kwargs)
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Advanced rate limiting error: {str(e)}")
                # Fallback: continue with request if rate limiting fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def advanced_rate_limit_content_generation():
    """Enhanced rate limiting decorator for content generation with bypass prevention"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found for rate limiting"
                )
            
            # Try to get current user (optional)
            try:
                current_user = await get_current_user_optional(request)
                user_id = str(current_user.id) if current_user else None
            except:
                user_id = None
            
            # Get enhanced client info
            client_info = get_enhanced_client_info(request)
            
            # Log the attempt for monitoring
            logger.info(f"Content generation request from {'user ' + user_id if user_id else 'anonymous'} - IP: {client_info['ip_address']}")
            
            # Check rate limit with advanced detection
            try:
                rate_limit_result = await advanced_rate_limiter.check_content_generation_limit(
                    user_id=user_id,
                    request_data=client_info
                )
                
                if not rate_limit_result["allowed"]:
                    # Log the rate limit violation
                    detection_method = rate_limit_result.get("detection_method", "standard")
                    logger.warning(f"Content generation rate limit exceeded - Method: {detection_method}, IP: {client_info['ip_address']}, UA: {client_info['user_agent'][:50]}")
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "message": rate_limit_result["message"],
                            "remaining": rate_limit_result["remaining"],
                            "reset_in_seconds": rate_limit_result["reset_in_seconds"],
                            "is_authenticated": rate_limit_result["is_authenticated"],
                            "rate_limit_type": "content_generation",
                            "detection_method": detection_method
                        }
                    )
                
                # Proceed with the request
                response = await func(*args, **kwargs)
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Advanced rate limiting error: {str(e)}")
                # Fallback: continue with request if rate limiting fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Monitoring function to detect potential abuse patterns
async def detect_abuse_patterns():
    """
    Background task to detect and flag potential abuse patterns
    Can be called periodically to analyze rate limit violations
    """
    try:
        from app.database import get_database
        db = await get_database()
        
        # Find clients with high request counts across different identifiers
        pipeline = [
            {"$match": {"date": datetime.utcnow().date().isoformat()}},
            {"$group": {
                "_id": "$client_id",
                "total_requests": {"$sum": "$count"},
                "identifier_types": {"$addToSet": "$identifier_type"},
                "request_types": {"$addToSet": "$request_type"}
            }},
            {"$match": {"total_requests": {"$gte": 50}}}  # Flag high usage
        ]
        
        suspicious_clients = await db.rate_limits.aggregate(pipeline).to_list(length=100)
        
        if suspicious_clients:
            logger.warning(f"Detected {len(suspicious_clients)} clients with high usage patterns")
            
        return suspicious_clients
        
    except Exception as e:
        logger.error(f"Error in abuse pattern detection: {e}")
        return []