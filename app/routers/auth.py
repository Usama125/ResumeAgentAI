from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserCreate, UserResponse, UserInDB
from app.services.auth_service import AuthService
from app.services.email_service import email_service
from app.services.google_oauth_service import GoogleOAuthService
from app.utils.security import create_access_token, create_refresh_token, verify_token
from app.utils.username_generator import UsernameGenerator
from app.utils.analytics_tracker import track_user_registration, track_user_login
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()

@router.post("/register", response_model=dict)
async def register(user: UserCreate, request: Request):
    """Register a new user"""
    # Validate username
    is_valid, error_message = UsernameGenerator.validate_username(user.username)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if username is available
    is_available = await UsernameGenerator.is_username_available(user.username)
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )
    
    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = await auth_service.create_user(user)
    
    # Track user registration
    await track_user_registration(request)
    
    # Generate tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(new_user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(new_user.id)}, expires_delta=refresh_token_expires
    )
    
    # Store refresh token JTI in database
    _, refresh_payload = verify_token(refresh_token, "refresh")
    expires_at = datetime.fromtimestamp(refresh_payload["exp"])
    await auth_service.store_refresh_token(
        str(new_user.id), 
        refresh_payload["jti"],
        expires_at
    )
    
    return {
        "user": UserResponse(**new_user.dict()),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=dict)
async def login(login_data: LoginRequest, request: Request):
    """Login user and return JWT token"""
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is blocked
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are blocked by the admin, please contact support"
        )
    
    # Track user login
    await track_user_login(request)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, expires_delta=refresh_token_expires
    )
    
    # Store refresh token JTI in database
    _, refresh_payload = verify_token(refresh_token, "refresh")
    expires_at = datetime.fromtimestamp(refresh_payload["exp"])
    await auth_service.store_refresh_token(
        str(user.id), 
        refresh_payload["jti"],
        expires_at
    )
    
    return {
        "user": UserResponse(**user.dict()),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    user_id, _ = verify_token(token, "access")
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is blocked
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are blocked by the admin, please contact support"
        )
    
    return user

async def get_current_user_optional(request: Request) -> Optional[UserInDB]:
    """Get current user if authenticated, None otherwise"""
    try:
        # Try to get authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        user_id, _ = verify_token(token, "access")
        user = await auth_service.get_user_by_id(user_id)
        return user
    except:
        return None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        user_id, payload = verify_token(refresh_request.refresh_token, "refresh")
        jti = payload.get("jti")
        
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token format"
            )
        
        # Verify refresh token is valid in database
        is_valid = await auth_service.verify_refresh_token(user_id, jti)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or expired"
            )
        
        # Get user
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": UserResponse(**user.dict())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout", response_model=dict)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and revoke refresh token"""
    try:
        # Get user ID from access token
        user_id, _ = verify_token(credentials.credentials, "access")
        
        # Revoke refresh token
        await auth_service.revoke_refresh_token(user_id)
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        # Even if token is invalid, consider logout successful
        return {"message": "Successfully logged out"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email"""
    try:
        logger.info(f"🚀 [FORGOT PASSWORD] Request received for email: {request.email}")
        print(f"🚀 [FORGOT PASSWORD] Request received for email: {request.email}")
        
        # Check if user exists
        user = await auth_service.get_user_by_email(request.email)
        if not user:
            # Don't reveal if email exists for security, but log it
            logger.warning(f"❌ [FORGOT PASSWORD] Password reset requested for non-existent email: {request.email}")
            print(f"❌ [FORGOT PASSWORD] Password reset requested for non-existent email: {request.email}")
            return {"message": "If the email address exists in our system, you will receive a password reset link."}
        
        logger.info(f"✅ [FORGOT PASSWORD] User found for email: {request.email}")
        print(f"✅ [FORGOT PASSWORD] User found for email: {request.email}")
        
        # Create password reset token
        logger.info(f"🔑 [FORGOT PASSWORD] Creating reset token for user: {user.id}")
        print(f"🔑 [FORGOT PASSWORD] Creating reset token for user: {user.id}")
        
        reset_token = await auth_service.create_password_reset_token(str(user.id))
        if not reset_token:
            logger.error(f"❌ [FORGOT PASSWORD] Failed to generate reset token for user: {user.id}")
            print(f"❌ [FORGOT PASSWORD] Failed to generate reset token for user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate reset token"
            )
        
        logger.info(f"✅ [FORGOT PASSWORD] Reset token created: {reset_token[:10]}...")
        print(f"✅ [FORGOT PASSWORD] Reset token created: {reset_token[:10]}...")
        
        # Send password reset email
        logger.info(f"📧 [FORGOT PASSWORD] Attempting to send email to: {user.email}")
        print(f"📧 [FORGOT PASSWORD] Attempting to send email to: {user.email}")
        
        email_sent = await email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            user_name=user.name
        )
        
        if not email_sent:
            logger.error(f"❌ [FORGOT PASSWORD] Failed to send password reset email to {user.email}")
            print(f"❌ [FORGOT PASSWORD] Failed to send password reset email to {user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email"
            )
        
        logger.info(f"✅ [FORGOT PASSWORD] Password reset email sent successfully to {user.email}")
        print(f"✅ [FORGOT PASSWORD] Password reset email sent successfully to {user.email}")
        return {"message": "If the email address exists in our system, you will receive a password reset link."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [FORGOT PASSWORD] Unexpected error: {str(e)}")
        print(f"❌ [FORGOT PASSWORD] Unexpected error: {str(e)}")
        print(f"❌ [FORGOT PASSWORD] Exception type: {type(e).__name__}")
        print(f"❌ [FORGOT PASSWORD] Exception details: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

@router.post("/reset-password", response_model=dict)
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token"""
    try:
        # Verify reset token
        user = await auth_service.verify_password_reset_token(request.token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Reset password
        success = await auth_service.reset_password(str(user.id), request.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
        
        # Send confirmation email
        email_sent = await email_service.send_password_reset_confirmation_email(
            to_email=user.email,
            user_name=user.name
        )
        
        if email_sent:
            logger.info(f"Password reset confirmation email sent to {user.email}")
        else:
            logger.warning(f"Failed to send password reset confirmation email to {user.email}")
        
        logger.info(f"Password successfully reset for user {user.email}")
        return {"message": "Password has been reset successfully. You can now sign in with your new password."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting your password"
        )

class GoogleOAuthRequest(BaseModel):
    id_token: str

@router.post("/google-oauth", response_model=dict)
async def google_oauth(oauth_request: GoogleOAuthRequest):
    """Authenticate user using Google OAuth"""
    try:
        print(f"🚀 [GOOGLE OAUTH] Authentication request received")
        logger.info(f"Google OAuth authentication request received")
        
        # Verify Google ID token
        google_user_info = await GoogleOAuthService.verify_google_token(oauth_request.id_token)
        if not google_user_info:
            print(f"❌ [GOOGLE OAUTH] Invalid Google token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token"
            )
        
        print(f"✅ [GOOGLE OAUTH] Token verified for: {google_user_info['email']}")
        
        # Check if user exists by email
        existing_user = await auth_service.get_user_by_email(google_user_info['email'])
        
        if existing_user:
            # User exists, update Google ID if not set
            print(f"✅ [GOOGLE OAUTH] Existing user found: {existing_user.email}")
            if not hasattr(existing_user, 'google_id') or not existing_user.google_id:
                # Update user with Google ID
                await auth_service.update_user_google_id(str(existing_user.id), google_user_info['google_id'])
                print(f"✅ [GOOGLE OAUTH] Updated existing user with Google ID")
            user = existing_user
        else:
            # Create new user from Google data
            print(f"🆕 [GOOGLE OAUTH] Creating new user for: {google_user_info['email']}")
            
            # Generate unique username from name
            generated_username = await UsernameGenerator.generate_username_from_name(google_user_info['name'])
            print(f"✅ [GOOGLE OAUTH] Generated username: {generated_username}")
            
            # Create user object
            new_user_data = UserCreate(
                email=google_user_info['email'],
                name=google_user_info['name'],
                username=generated_username,
                password="google_oauth_user",  # Placeholder password for OAuth users
                google_id=google_user_info['google_id'],
                profile_picture_url=google_user_info.get('picture', '')
            )
            
            user = await auth_service.create_user(new_user_data)
            print(f"✅ [GOOGLE OAUTH] New user created: {user.email} with username: {generated_username}")
        
        # Generate tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        )
        
        # Store refresh token JTI in database
        _, refresh_payload = verify_token(refresh_token, "refresh")
        expires_at = datetime.fromtimestamp(refresh_payload["exp"])
        await auth_service.store_refresh_token(
            str(user.id), 
            refresh_payload["jti"],
            expires_at
        )
        
        print(f"✅ [GOOGLE OAUTH] Authentication successful for: {user.email}")
        logger.info(f"Google OAuth authentication successful for user: {user.email}")
        
        return {
            "user": UserResponse(**user.dict()),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [GOOGLE OAUTH] Unexpected error: {str(e)}")
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )

class UsernameCheckRequest(BaseModel):
    username: str

@router.post("/check-username", response_model=dict)
async def check_username_availability(request: UsernameCheckRequest):
    """Check if username is available and valid"""
    try:
        # Validate username format
        is_valid, error_message = UsernameGenerator.validate_username(request.username)
        if not is_valid:
            return {
                "available": False,
                "valid": False,
                "message": error_message
            }
        
        # Check availability
        is_available = await UsernameGenerator.is_username_available(request.username)
        
        if is_available:
            return {
                "available": True,
                "valid": True,
                "message": "Username is available"
            }
        else:
            return {
                "available": False,
                "valid": True,
                "message": "Username is already taken"
            }
            
    except Exception as e:
        logger.error(f"Error checking username availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check username availability"
        )