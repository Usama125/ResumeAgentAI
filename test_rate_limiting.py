#!/usr/bin/env python3
"""
Rate Limiting Test Script for AI Resume Builder

This script tests the enhanced rate limiting functionality with different scenarios:
1. Unauthenticated users (job matching and chat)
2. Authenticated users (job matching and chat)
3. Rate limit exceed scenarios
4. Reset functionality

Usage:
    python test_rate_limiting.py
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class RateLimitTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "RateLimitTester/1.0"
        }
    
    async def setup(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def cleanup(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
    
    async def register_test_user(self) -> bool:
        """Register a test user for authenticated tests"""
        try:
            data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "name": "Test User"
            }
            
            async with self.session.post(
                f"{BASE_URL}/auth/register",
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    print(f"✅ Test user registered successfully")
                    return True
                elif response.status == 400:
                    # User might already exist, try to login
                    return await self.login_test_user()
                else:
                    print(f"❌ Failed to register test user: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error registering test user: {e}")
            return False
    
    async def login_test_user(self) -> bool:
        """Login test user"""
        try:
            data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(
                f"{BASE_URL}/auth/login",
                headers=self.headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    print(f"✅ Test user logged in successfully")
                    return True
                else:
                    print(f"❌ Failed to login test user: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error logging in test user: {e}")
            return False
    
    async def test_job_matching_unauthenticated(self):
        """Test job matching rate limiting for unauthenticated users"""
        print("\n🔍 Testing Job Matching - Unauthenticated Users")
        print("=" * 50)
        
        # Try to make requests until rate limit is hit
        for i in range(5):  # Try 5 requests (limit is 3)
            try:
                data = {
                    "query": f"Python developer test {i}",
                    "location": None,
                    "experience_level": None,
                    "limit": 10,
                    "skip": 0
                }
                
                async with self.session.post(
                    f"{BASE_URL}/job-matching/search",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        print(f"✅ Request {i+1}: Success")
                    elif response.status == 429:
                        result = await response.json()
                        print(f"🚫 Request {i+1}: Rate limited")
                        print(f"   Message: {result.get('detail', {}).get('message', 'N/A')}")
                        print(f"   Reset in: {result.get('detail', {}).get('reset_in_seconds', 'N/A')} seconds")
                        print(f"   Is authenticated: {result.get('detail', {}).get('is_authenticated', 'N/A')}")
                        break
                    else:
                        print(f"❌ Request {i+1}: Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Request {i+1}: Exception {e}")
    
    async def test_job_matching_authenticated(self):
        """Test job matching rate limiting for authenticated users"""
        print("\n🔍 Testing Job Matching - Authenticated Users")
        print("=" * 50)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return
        
        auth_headers = {
            **self.headers,
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        # Try to make requests until rate limit is hit
        for i in range(7):  # Try 7 requests (limit is 5)
            try:
                data = {
                    "query": f"Python developer authenticated test {i}",
                    "location": None,
                    "experience_level": None,
                    "limit": 10,
                    "skip": 0
                }
                
                async with self.session.post(
                    f"{BASE_URL}/job-matching/search",
                    headers=auth_headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        print(f"✅ Request {i+1}: Success")
                    elif response.status == 429:
                        result = await response.json()
                        print(f"🚫 Request {i+1}: Rate limited")
                        print(f"   Message: {result.get('detail', {}).get('message', 'N/A')}")
                        print(f"   Reset in: {result.get('detail', {}).get('reset_in_seconds', 'N/A')} seconds")
                        print(f"   Is authenticated: {result.get('detail', {}).get('is_authenticated', 'N/A')}")
                        break
                    else:
                        print(f"❌ Request {i+1}: Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Request {i+1}: Exception {e}")
    
    async def test_chat_unauthenticated(self):
        """Test chat rate limiting for unauthenticated users"""
        print("\n💬 Testing Chat - Unauthenticated Users")
        print("=" * 50)
        
        # Use a dummy user ID for testing
        test_user_id = "507f1f77bcf86cd799439011"
        
        # Try to make requests until rate limit is hit
        for i in range(12):  # Try 12 requests (limit is 10)
            try:
                data = {
                    "message": f"Hello, this is test message {i+1}"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/chat/{test_user_id}",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        print(f"✅ Request {i+1}: Success")
                    elif response.status == 429:
                        result = await response.json()
                        print(f"🚫 Request {i+1}: Rate limited")
                        print(f"   Message: {result.get('detail', {}).get('message', 'N/A')}")
                        print(f"   Reset in: {result.get('detail', {}).get('reset_in_seconds', 'N/A')} seconds")
                        print(f"   Is authenticated: {result.get('detail', {}).get('is_authenticated', 'N/A')}")
                        break
                    elif response.status == 404:
                        print(f"⚠️  Request {i+1}: User not found (expected for dummy ID)")
                    else:
                        print(f"❌ Request {i+1}: Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Request {i+1}: Exception {e}")
    
    async def test_chat_authenticated(self):
        """Test chat rate limiting for authenticated users"""
        print("\n💬 Testing Chat - Authenticated Users")
        print("=" * 50)
        
        if not self.auth_token:
            print("❌ No auth token available")
            return
        
        auth_headers = {
            **self.headers,
            "Authorization": f"Bearer {self.auth_token}"
        }
        
        # Use a dummy user ID for testing
        test_user_id = "507f1f77bcf86cd799439011"
        
        # Try to make requests until rate limit is hit
        for i in range(17):  # Try 17 requests (limit is 15)
            try:
                data = {
                    "message": f"Hello authenticated, this is test message {i+1}"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/chat/{test_user_id}",
                    headers=auth_headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        print(f"✅ Request {i+1}: Success")
                    elif response.status == 429:
                        result = await response.json()
                        print(f"🚫 Request {i+1}: Rate limited")
                        print(f"   Message: {result.get('detail', {}).get('message', 'N/A')}")
                        print(f"   Reset in: {result.get('detail', {}).get('reset_in_seconds', 'N/A')} seconds")
                        print(f"   Is authenticated: {result.get('detail', {}).get('is_authenticated', 'N/A')}")
                        break
                    elif response.status == 404:
                        print(f"⚠️  Request {i+1}: User not found (expected for dummy ID)")
                    else:
                        print(f"❌ Request {i+1}: Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Request {i+1}: Exception {e}")
    
    async def run_all_tests(self):
        """Run all rate limiting tests"""
        print("🚀 Starting Rate Limiting Tests")
        print("=" * 50)
        print(f"Base URL: {BASE_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print(f"Timestamp: {datetime.now()}")
        
        # Setup
        await self.setup()
        
        try:
            # Register/login test user
            await self.register_test_user()
            
            # Run tests
            await self.test_job_matching_unauthenticated()
            await self.test_job_matching_authenticated()
            await self.test_chat_unauthenticated()
            await self.test_chat_authenticated()
            
            print("\n✅ All tests completed!")
            
        finally:
            await self.cleanup()

async def main():
    """Main function"""
    tester = RateLimitTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())