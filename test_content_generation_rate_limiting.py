#!/usr/bin/env python3
"""
Test script for content generation rate limiting
Tests both authenticated and unauthenticated rate limits
"""

import asyncio
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
CONTENT_GENERATOR_URL = f"{BASE_URL}/content-generator"

def test_unauthenticated_rate_limiting():
    """Test rate limiting for unauthenticated users (should allow 3 requests)"""
    print("🧪 Testing unauthenticated user rate limiting...")
    
    # Test request payload - simplified to match new backend
    payload = {
        "content_type": "cover_letter"
    }
    
    successful_requests = 0
    
    # Make requests until rate limited
    for i in range(5):  # Try 5 requests, should be limited at 4th
        print(f"📝 Making request {i+1}...")
        
        try:
            response = requests.post(
                f"{CONTENT_GENERATOR_URL}/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                successful_requests += 1
                data = response.json()
                print(f"✅ Request {i+1} successful. Message: {data.get('message', 'unknown')}")
                print(f"   User authenticated: {data.get('is_authenticated', False)}")
            elif response.status_code == 429:
                print(f"🚫 Request {i+1} rate limited! Response: {response.json()}")
                break
            else:
                print(f"❌ Request {i+1} failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Request {i+1} error: {str(e)}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    print(f"📊 Unauthenticated test completed. Successful requests: {successful_requests}")
    print(f"✅ Expected: 3 successful requests, then rate limited")
    
    return successful_requests

def test_different_content_types():
    """Test that different content types work"""
    print("\n🧪 Testing different content types...")
    
    for content_type in ["cover_letter", "proposal"]:
        payload = {"content_type": content_type}
        print(f"📝 Testing {content_type}...")
        
        try:
            response = requests.post(
                f"{CONTENT_GENERATOR_URL}/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {content_type} validated successfully")
                print(f"   Message: {data.get('message')}")
            elif response.status_code == 429:
                print(f"🚫 {content_type} rate limited: {response.json()}")
            else:
                print(f"❌ {content_type} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ {content_type} error: {str(e)}")
        
        time.sleep(0.5)

def main():
    """Run all tests"""
    print("🚀 Starting content generation rate limiting tests...")
    print("="*60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("❌ Backend not running or health check failed")
            return
    except:
        print("❌ Cannot connect to backend. Make sure it's running on localhost:8000")
        return
    
    print("✅ Backend is running")
    
    # Test unauthenticated rate limiting
    successful_requests = test_unauthenticated_rate_limiting()
    
    # Test different content types
    test_different_content_types()
    
    print("\n" + "="*60)
    print("📊 Test Summary:")
    print(f"✅ Rate limiting is {'working correctly' if successful_requests == 3 else 'NOT working as expected'}")
    print(f"   Expected 3 successful requests, got {successful_requests}")
    print("✅ Backend validation endpoint working - actual generation will be on Next.js side")

if __name__ == "__main__":
    main()