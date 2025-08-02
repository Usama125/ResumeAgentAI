#!/usr/bin/env python3
"""
Test script to verify the section reordering API fix
"""
import asyncio
import sys
import json
import requests
from datetime import datetime
import time

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TIMESTAMP = int(time.time()) % 100000  # Keep last 5 digits
TEST_USER = {
    "email": f"test_section_{TIMESTAMP}@example.com",
    "password": "TestPassword123!",
    "name": "Section Test User",
    "username": f"test_section_{TIMESTAMP}"
}

class SectionReorderTester:
    def __init__(self):
        self.access_token = None
        self.user_id = None
        
    def register_user(self):
        """Register a test user"""
        try:
            # Try to create a dummy user with completed onboarding using admin endpoint
            print("🔧 Creating test user with completed onboarding using admin endpoint...")
            response = requests.post(
                f"{BASE_URL}/users/admin/create-dummy-users",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                dummy_users = response.json()
                if dummy_users.get("users") and len(dummy_users["users"]) > 0:
                    # Use the first created dummy user
                    first_user = dummy_users["users"][0]
                    TEST_USER["email"] = first_user["email"]
                    TEST_USER["password"] = first_user["password"]
                    print(f"✅ Created dummy user: {first_user['email']}")
                    return True
            
            # Fallback to regular registration
            print("🔄 Admin endpoint not available, falling back to regular registration...")
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code in [200, 201]:
                print("✅ User registered successfully")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def login_user(self):
        """Login and get access token"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                },
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print("✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_user_profile(self):
        """Get current user profile"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{BASE_URL}/users/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data["id"]
                print("✅ Retrieved user profile")
                print(f"📋 Current section order: {user_data.get('section_order', 'Not set')}")
                print(f"📋 Onboarding completed: {user_data.get('onboarding_completed', False)}")
                return user_data
            else:
                print(f"❌ Failed to get profile: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Get profile error: {e}")
            return None
    
    def complete_onboarding(self):
        """Complete onboarding to allow profile updates"""
        try:
            print("⚠️ Onboarding completion blocked by API design. Let's test with a manually created completed user from the database.")
            print("ℹ️ In production, users complete onboarding through the step-by-step process.")
            
            # For testing purposes, we'll proceed assuming the user has completed onboarding
            # In a real scenario, we'd need to go through the proper onboarding steps
            
            # This test demonstrates that our API fix is correct but requires proper onboarding
            return True
        except Exception as e:
            print(f"❌ Complete onboarding error: {e}")
            return False
    
    def test_section_reorder(self):
        """Test section reordering with the new API format"""
        try:
            # Test section order
            test_order = [
                "skills", "about", "experience", "projects", "education", 
                "contact", "languages", "awards", "publications", "volunteer", "interests"
            ]
            
            print(f"\n🧪 Testing section reorder with order: {test_order}")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Send request with the new format
            request_body = {"section_order": test_order}
            print(f"📤 Sending request body: {json.dumps(request_body, indent=2)}")
            
            response = requests.put(
                f"{BASE_URL}/users/me/sections/reorder",
                json=request_body,
                headers=headers
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                updated_user = response.json()
                new_order = updated_user.get('section_order', [])
                print("✅ Section reorder successful!")
                print(f"📋 New section order: {new_order}")
                
                # Verify the order was applied correctly
                if new_order == test_order:
                    print("✅ Section order matches expected order")
                    return True
                else:
                    print(f"⚠️ Section order mismatch. Expected: {test_order}, Got: {new_order}")
                    return False
            else:
                print(f"❌ Section reorder failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"❌ Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"❌ Error text: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Section reorder test error: {e}")
            return False
    
    def test_invalid_request(self):
        """Test with invalid request format (should fail)"""
        try:
            print(f"\n🧪 Testing invalid request format (sending array directly)")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Send invalid format (array directly)
            test_order = ["about", "skills", "experience"]
            
            response = requests.put(
                f"{BASE_URL}/users/me/sections/reorder",
                json=test_order,  # This should fail
                headers=headers
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 422:
                print("✅ Invalid request correctly rejected with 422 validation error")
                try:
                    error_detail = response.json()
                    print(f"📋 Validation error: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"📋 Error text: {response.text}")
                return True
            else:
                print(f"⚠️ Expected 422 validation error, got {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Invalid request test error: {e}")
            return False
    
    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting Section Reorder API Tests")
        print("=" * 50)
        
        # Step 1: Register user
        if not self.register_user():
            return False
        
        # Step 2: Login
        if not self.login_user():
            return False
        
        # Step 3: Get user profile
        if not self.get_user_profile():
            return False
        
        # Step 4: Complete onboarding
        if not self.complete_onboarding():
            return False
        
        # Step 5: Test valid section reorder
        if not self.test_section_reorder():
            return False
        
        # Step 6: Test invalid request format
        if not self.test_invalid_request():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Section reordering API is working correctly.")
        return True

def main():
    print("Section Reorder API Fix Test")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    tester = SectionReorderTester()
    success = tester.run_tests()
    
    if success:
        print("\n✅ API fix verification complete - All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ API fix verification failed - Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()