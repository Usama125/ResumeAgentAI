#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify auth error handling
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login_error():
    """Test login with wrong credentials"""
    print("🧪 Testing login with wrong credentials...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Incorrect email or password"
    print("✅ Login error test passed!")

def test_register_validation_error():
    """Test register with validation errors"""
    print("\n🧪 Testing register with validation errors...")
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": "invalid-email", "password": "short", "name": ""}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) >= 2  # Should have email and password errors
    print("✅ Register validation error test passed!")

def test_forgot_password_success():
    """Test forgot password (should always return success message)"""
    print("\n🧪 Testing forgot password...")
    
    response = requests.post(
        f"{BASE_URL}/auth/forgot-password",
        json={"email": "nonexistent@example.com"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "receive a password reset link" in data["message"]
    print("✅ Forgot password test passed!")

def test_reset_password_invalid_token():
    """Test reset password with invalid token"""
    print("\n🧪 Testing reset password with invalid token...")
    
    response = requests.post(
        f"{BASE_URL}/auth/reset-password",
        json={"token": "invalid_token", "new_password": "newpassword123"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Should return error for invalid token
    assert response.status_code in [400, 401, 422]
    data = response.json()
    assert "detail" in data
    print("✅ Reset password invalid token test passed!")

if __name__ == "__main__":
    print("🚀 Starting auth error handling tests...\n")
    
    try:
        test_login_error()
        test_register_validation_error()
        test_forgot_password_success()
        test_reset_password_invalid_token()
        
        print("\n🎉 All auth error tests passed!")
        print("✅ Backend error handling is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("💡 Please check your backend server is running on http://localhost:8000")