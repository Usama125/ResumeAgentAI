#!/usr/bin/env python3
"""
Debug script to test rate limiting functionality
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def debug_rate_limiting():
    print("🔍 Debugging Rate Limiting Issues...")
    
    # Test 1: Check imports
    print("\n1. Testing imports...")
    try:
        from app.utils.advanced_rate_limiter import advanced_rate_limiter
        print("✅ advanced_rate_limiter imported successfully")
    except Exception as e:
        print(f"❌ Failed to import advanced_rate_limiter: {e}")
        return False
    
    # Test 2: Check configuration
    print("\n2. Testing configuration...")
    try:
        from app.config import settings
        print(f"✅ UNAUTH_DAILY_JOB_MATCHING_LIMIT: {settings.UNAUTH_DAILY_JOB_MATCHING_LIMIT}")
        print(f"✅ AUTH_DAILY_JOB_MATCHING_LIMIT: {settings.AUTH_DAILY_JOB_MATCHING_LIMIT}")
        print(f"✅ UNAUTH_DAILY_CHAT_LIMIT: {settings.UNAUTH_DAILY_CHAT_LIMIT}")
        print(f"✅ AUTH_DAILY_CHAT_LIMIT: {settings.AUTH_DAILY_CHAT_LIMIT}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test 3: Check database connection
    print("\n3. Testing database connection...")
    try:
        from app.database import get_database
        db = await get_database()
        print("✅ Database connection successful")
        
        # Test collection access
        users_collection = db.users
        rate_limits_collection = db.rate_limits
        print("✅ Collections accessible")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("This is likely why rate limiting isn't working!")
        return False
    
    # Test 4: Test rate limiter methods
    print("\n4. Testing rate limiter methods...")
    try:
        test_request_data = {
            'ip_address': '127.0.0.1',
            'user_agent': 'Test-Agent/1.0',
            'accept_language': 'en-US',
            'accept_encoding': 'gzip',
            'accept': 'text/html',
            'screen_info': '1920x1080x24',
            'timezone': 'UTC'
        }
        
        # Test fingerprint creation
        fingerprint = advanced_rate_limiter._create_device_fingerprint(test_request_data)
        print(f"✅ Fingerprint created: {fingerprint[:16]}...")
        
        # Test identifier generation
        identifiers = await advanced_rate_limiter._get_all_client_identifiers(test_request_data)
        print(f"✅ Generated {len(identifiers)} identifiers")
        
        # Test actual rate limit check
        result = await advanced_rate_limiter.check_job_matching_limit(
            user_id=None,
            request_data=test_request_data
        )
        print(f"✅ Rate limit check result: {result}")
        
    except Exception as e:
        print(f"❌ Rate limiter method failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ All tests passed! Rate limiting should be working.")
    return True

async def main():
    success = await debug_rate_limiting()
    if not success:
        print("\n❌ Rate limiting has issues. Check the errors above.")
    else:
        print("\n🎉 Rate limiting is configured correctly!")

if __name__ == "__main__":
    asyncio.run(main())