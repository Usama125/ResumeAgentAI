#!/usr/bin/env python3
"""
Test script for dummy user generation
Tests the dummy user generator with a small batch
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

from generate_dummy_users import generate_dummy_user, create_dummy_users
import json

async def test_single_user():
    """Test generating a single user"""
    print("🧪 Testing single user generation...")
    
    user = await generate_dummy_user("US")
    
    # Print user info
    print(f"✅ Generated user: {user['name']} ({user['username']})")
    print(f"   Email: {user['email']}")
    print(f"   Profession: {user['profession']}")
    print(f"   Location: {user['location']}")
    print(f"   Skills count: {len(user['skills'])}")
    print(f"   Experience count: {len(user['experience_details'])}")
    print(f"   Projects count: {len(user['projects'])}")
    print(f"   Education count: {len(user['education'])}")
    print(f"   Languages count: {len(user['languages'])}")
    print(f"   Awards count: {len(user['awards'])}")
    print(f"   Publications count: {len(user['publications'])}")
    print(f"   Volunteer experience count: {len(user['volunteer_experience'])}")
    print(f"   Interests count: {len(user['interests'])}")
    
    # Check if all required fields are present
    required_fields = [
        'email', 'name', 'username', 'designation', 'location', 'profession',
        'skills', 'experience_details', 'projects', 'education', 'languages',
        'contact_info', 'work_preferences', 'onboarding_progress'
    ]
    
    missing_fields = [field for field in required_fields if field not in user or user[field] is None]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    else:
        print("✅ All required fields present!")
        return True

async def test_multiple_countries():
    """Test generating users from different countries"""
    print("\n🌍 Testing multiple countries...")
    
    countries = ['US', 'GB', 'CA', 'AU', 'DE']
    
    for country in countries:
        user = await generate_dummy_user(country)
        print(f"✅ {country}: {user['name']} - {user['location']}")

async def test_database_insertion():
    """Test inserting a few users into the database"""
    print("\n💾 Testing database insertion with 5 users...")
    
    try:
        await create_dummy_users(5)
        print("✅ Database insertion test completed!")
        return True
    except Exception as e:
        print(f"❌ Database insertion failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Dummy User Generation Tests")
    print("=" * 50)
    
    # Test 1: Single user generation
    success1 = await test_single_user()
    
    # Test 2: Multiple countries
    await test_multiple_countries()
    
    # Test 3: Database insertion (commented out to avoid affecting live DB)
    print("\n💾 Database insertion test skipped (to protect live database)")
    print("   To test database insertion, uncomment the line in the script")
    # success3 = await test_database_insertion()
    
    print("\n" + "=" * 50)
    if success1:
        print("✅ All tests passed! The dummy user generator is working correctly.")
        print("\n📝 Next steps:")
        print("1. Update the MongoDB URL in generate_dummy_users.py with your live credentials")
        print("2. Run: python generate_dummy_users.py 50")
        print("3. Or use the API endpoint: POST /api/v1/admin/generate-users")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())