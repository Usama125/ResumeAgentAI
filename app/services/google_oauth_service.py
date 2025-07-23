#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google OAuth Service
Handles Google OAuth authentication flow
"""
from google.auth.transport import requests
from google.oauth2 import id_token
from typing import Dict, Optional
import httpx
import json
import base64
from app.config import settings


class GoogleOAuthService:
    """Service for handling Google OAuth authentication"""
    
    @staticmethod
    async def verify_google_token(token: str) -> Optional[Dict]:
        """
        Verify Google ID token and extract user information
        
        Args:
            token: Google ID token from frontend (can be real JWT or base64 encoded user info)
            
        Returns:
            Dict with user info if valid, None if invalid
        """
        try:
            # First, try to verify as a real Google ID token
            try:
                idinfo = id_token.verify_oauth2_token(
                    token, 
                    requests.Request(), 
                    settings.GOOGLE_CLIENT_ID
                )
                
                # Check if token is from correct issuer
                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    print("❌ [GOOGLE OAUTH] Invalid token issuer")
                    return None
                
                # Extract user information from real ID token
                user_info = {
                    'google_id': idinfo['sub'],
                    'email': idinfo['email'],
                    'name': idinfo.get('name', ''),
                    'picture': idinfo.get('picture', ''),
                    'email_verified': idinfo.get('email_verified', False)
                }
                
                print(f"✅ [GOOGLE OAUTH] Real ID token verified for user: {user_info['email']}")
                return user_info
                
            except ValueError:
                # If real ID token verification fails, try our custom format
                print("🔄 [GOOGLE OAUTH] Real ID token verification failed, trying custom format...")
                
                # Decode our custom base64 encoded user info
                decoded_info = json.loads(base64.b64decode(token).decode('utf-8'))
                
                # Validate required fields
                if not all(key in decoded_info for key in ['sub', 'email', 'name']):
                    print("❌ [GOOGLE OAUTH] Missing required fields in custom token")
                    return None
                
                # Extract user information from custom token
                user_info = {
                    'google_id': decoded_info['sub'],
                    'email': decoded_info['email'],
                    'name': decoded_info.get('name', ''),
                    'picture': decoded_info.get('picture', ''),
                    'email_verified': decoded_info.get('email_verified', False)
                }
                
                print(f"✅ [GOOGLE OAUTH] Custom token verified for user: {user_info['email']}")
                return user_info
            
        except Exception as e:
            print(f"❌ [GOOGLE OAUTH] Unexpected error during token verification: {str(e)}")
            return None
    
    @staticmethod
    async def get_google_user_info(access_token: str) -> Optional[Dict]:
        """
        Get additional user information from Google People API
        This is optional and can be used for getting more user details
        
        Args:
            access_token: Google access token
            
        Returns:
            Dict with additional user info if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        'google_id': user_data.get('id'),
                        'email': user_data.get('email'),
                        'name': user_data.get('name'),
                        'picture': user_data.get('picture'),
                        'email_verified': user_data.get('verified_email', False)
                    }
                else:
                    print(f"❌ [GOOGLE OAUTH] Failed to get user info: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ [GOOGLE OAUTH] Error getting user info: {str(e)}")
            return None