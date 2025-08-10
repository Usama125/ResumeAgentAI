from fastapi import HTTPException, Request, status
from functools import wraps
from typing import Optional, Callable
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def debug_rate_limit_job_matching():
    """Debug version of rate limiting decorator"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            print("🔍 DEBUG: Rate limiting decorator called!")
            
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                print("❌ DEBUG: No request object found")
                return await func(*args, **kwargs)
            
            print(f"🔍 DEBUG: Request found - {request.method} {request.url}")
            
            # Get client info
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            print(f"🔍 DEBUG: Client info - IP: {ip_address}, UA: {user_agent[:50]}")
            
            # Try to get current user (optional)
            try:
                from app.routers.auth import get_current_user_optional
                current_user = await get_current_user_optional(request)
                user_id = str(current_user.id) if current_user else None
                is_authenticated = user_id is not None
                print(f"🔍 DEBUG: User authentication - {'Authenticated' if is_authenticated else 'Anonymous'}{f' (ID: {user_id})' if user_id else ''}")
            except:
                user_id = None
                is_authenticated = False
                print("🔍 DEBUG: User authentication - Anonymous (detection failed)")
            
            # Simple counter-based rate limiting for debugging
            try:
                # Try to import and use a simple in-memory counter for now
                import datetime
                from collections import defaultdict
                
                # Simple in-memory rate limiting (resets when server restarts)
                if not hasattr(debug_rate_limit_job_matching, '_requests'):
                    debug_rate_limit_job_matching._requests = defaultdict(list)
                
                # Use user_id for authenticated users, IP+UA for anonymous
                if is_authenticated:
                    client_key = f"user:{user_id}"
                    limit = 3000  # Authenticated job matching limit
                else:
                    client_key = f"{ip_address}:{user_agent}"
                    limit = 3000  # Unauthenticated limit
                
                now = datetime.datetime.now()
                
                # Clean old requests (older than 24 hours)
                cutoff = now - datetime.timedelta(hours=24)
                debug_rate_limit_job_matching._requests[client_key] = [
                    req_time for req_time in debug_rate_limit_job_matching._requests[client_key] 
                    if req_time > cutoff
                ]
                
                # Check if limit exceeded
                request_count = len(debug_rate_limit_job_matching._requests[client_key])
                
                print(f"🔍 DEBUG: Request count for {client_key}: {request_count}/{limit}")
                
                if request_count >= limit:
                    print(f"🚫 DEBUG: Rate limit exceeded!")
                    user_type = "registered user" if is_authenticated else "guest"
                    message = f"🎯 Hold up there, search champion! You've reached your daily job matching limit of {limit} requests as a {user_type}. Your dedication to finding the perfect match is admirable! 🚀 Come back tomorrow to discover more amazing opportunities. In the meantime, why not perfect your profile? ✨"
                    
                    if not is_authenticated:
                        message += " 🌟 Pro tip: Registered users get 5 requests per day! Why not join our community? ✨"
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "message": message,
                            "remaining": 0,
                            "reset_in_seconds": settings.RATE_LIMIT_RESET_HOURS * 3600,  # Convert hours to seconds
                            "is_authenticated": is_authenticated,
                            "rate_limit_type": "job_matching"
                        }
                    )
                
                # Add this request to the counter
                debug_rate_limit_job_matching._requests[client_key].append(now)
                print(f"✅ DEBUG: Request allowed. Count now: {request_count + 1}/{limit}")
                
                # Proceed with the request
                response = await func(*args, **kwargs)
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"❌ DEBUG: Error in rate limiting: {e}")
                import traceback
                traceback.print_exc()
                # Still allow request but log the error
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def debug_rate_limit_chat():
    """Debug version of chat rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            print("🔍 DEBUG: Chat rate limiting decorator called!")
            
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                print("❌ DEBUG: No request object found")
                return await func(*args, **kwargs)
            
            print(f"🔍 DEBUG: Chat request found - {request.method} {request.url}")
            
            # Get client info
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            print(f"🔍 DEBUG: Client info - IP: {ip_address}, UA: {user_agent[:50]}")
            
            # Try to get current user (optional)
            try:
                from app.routers.auth import get_current_user_optional
                current_user = await get_current_user_optional(request)
                user_id = str(current_user.id) if current_user else None
                is_authenticated = user_id is not None
                print(f"🔍 DEBUG: User authentication - {'Authenticated' if is_authenticated else 'Anonymous'}{f' (ID: {user_id})' if user_id else ''}")
            except:
                user_id = None
                is_authenticated = False
                print("🔍 DEBUG: User authentication - Anonymous (detection failed)")
            
            # Simple counter-based rate limiting for debugging
            try:
                import datetime
                from collections import defaultdict
                
                # Simple in-memory rate limiting
                if not hasattr(debug_rate_limit_chat, '_requests'):
                    debug_rate_limit_chat._requests = defaultdict(list)
                
                # Use user_id for authenticated users, IP+UA for anonymous
                if is_authenticated:
                    client_key = f"user:{user_id}"
                    limit = 15  # Authenticated chat limit
                else:
                    client_key = f"{ip_address}:{user_agent}"
                    limit = 10  # Unauthenticated limit
                
                now = datetime.datetime.now()
                
                # Clean old requests (older than 24 hours)
                cutoff = now - datetime.timedelta(hours=24)
                debug_rate_limit_chat._requests[client_key] = [
                    req_time for req_time in debug_rate_limit_chat._requests[client_key] 
                    if req_time > cutoff
                ]
                
                # Check if limit exceeded
                request_count = len(debug_rate_limit_chat._requests[client_key])
                
                print(f"🔍 DEBUG: Chat request count for {client_key}: {request_count}/{limit}")
                
                if request_count >= limit:
                    print(f"🚫 DEBUG: Chat rate limit exceeded!")
                    user_type = "registered user" if is_authenticated else "guest"
                    message = f"💬 Whoa there, conversation master! You've reached your daily chat limit of {limit} requests as a {user_type}. Your curiosity is impressive! 🎉 Take a breather and come back tomorrow for more engaging conversations. ✨"
                    
                    if not is_authenticated:
                        message += " 🌟 Pro tip: Registered users get 15 chat requests per day! Why not join our community? 🚀"
                    
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "message": message,
                            "remaining": 0,
                            "reset_in_seconds": settings.RATE_LIMIT_RESET_HOURS * 3600,  # Convert hours to seconds
                            "is_authenticated": is_authenticated,
                            "rate_limit_type": "chat"
                        }
                    )
                
                # Add this request to the counter
                debug_rate_limit_chat._requests[client_key].append(now)
                print(f"✅ DEBUG: Chat request allowed. Count now: {request_count + 1}/{limit}")
                
                # Proceed with the request
                response = await func(*args, **kwargs)
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"❌ DEBUG: Error in chat rate limiting: {e}")
                import traceback
                traceback.print_exc()
                # Still allow request but log the error
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator