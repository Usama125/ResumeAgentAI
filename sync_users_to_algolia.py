#!/usr/bin/env python3
"""
Sync all users from MongoDB to Algolia
This script will fetch all users from the database and sync them to Algolia search index
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.services.algolia_service import AlgoliaService
from app.models.user import UserInDB
from app.services.profile_scoring_service import ProfileScoringService
from datetime import datetime
import traceback

async def sync_all_users_to_algolia():
    """Sync all users from database to Algolia"""
    
    # Initialize services
    algolia_service = AlgoliaService()
    profile_scoring_service = ProfileScoringService()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    users_collection = db.users
    
    try:
        print("🔄 Starting sync of all users to Algolia...")
        
        # Get all users from database
        users_cursor = users_collection.find({})
        users_list = await users_cursor.to_list(length=None)
        
        print(f"📊 Found {len(users_list)} users in database")
        
        synced_count = 0
        error_count = 0
        
        for user_data in users_list:
            try:
                print(f"\n🔄 Processing user: {user_data.get('name', 'Unknown')} (ID: {user_data.get('_id')})")
                
                # Store the original _id for database updates
                original_id = user_data['_id']
                
                # Convert MongoDB document to UserInDB model
                user_data['id'] = str(user_data['_id'])  # Convert ObjectId to string
                # Remove the original _id field to avoid conflicts
                del user_data['_id']
                
                # Calculate profile score if not exists
                if 'profile_score' not in user_data or user_data.get('profile_score', 0) == 0:
                    print(f"  📈 Calculating profile score...")
                    profile_score = profile_scoring_service.calculate_profile_score(user_data)
                    user_data['profile_score'] = profile_score
                    
                    # Update in database using the original _id
                    await users_collection.update_one(
                        {"_id": original_id}, 
                        {"$set": {"profile_score": profile_score}}
                    )
                    print(f"  ✅ Profile score calculated and saved: {profile_score}")
                else:
                    print(f"  📊 Existing profile score: {user_data.get('profile_score')}")
                
                # Create UserInDB model instance
                try:
                    # Handle missing fields with defaults
                    user_data.setdefault('designation', '')
                    user_data.setdefault('location', '')
                    user_data.setdefault('summary', '')
                    user_data.setdefault('experience', '')
                    user_data.setdefault('skills', [])
                    user_data.setdefault('experience_details', [])
                    user_data.setdefault('projects', [])
                    user_data.setdefault('certifications', [])
                    user_data.setdefault('contact_info', {})
                    user_data.setdefault('education', [])
                    user_data.setdefault('languages', [])
                    user_data.setdefault('awards', [])
                    user_data.setdefault('publications', [])
                    user_data.setdefault('volunteer_experience', [])
                    user_data.setdefault('interests', [])
                    user_data.setdefault('onboarding_completed', True)
                    user_data.setdefault('created_at', datetime.utcnow())
                    user_data.setdefault('updated_at', datetime.utcnow())
                    
                    # Handle profession field
                    if 'profession' not in user_data:
                        user_data['profession'] = user_data.get('designation', '')
                    
                    user = UserInDB(**user_data)
                    
                    # Sync to Algolia
                    print(f"  🔄 Syncing to Algolia...")
                    success = await algolia_service.sync_user_to_algolia(user)
                    
                    if success:
                        synced_count += 1
                        print(f"  ✅ Successfully synced to Algolia")
                    else:
                        error_count += 1
                        print(f"  ❌ Failed to sync to Algolia")
                        
                except Exception as model_error:
                    print(f"  ❌ Error creating UserInDB model: {str(model_error)}")
                    print(f"  📋 User data keys: {list(user_data.keys())}")
                    error_count += 1
                    
            except Exception as user_error:
                print(f"  ❌ Error processing user: {str(user_error)}")
                traceback.print_exc()
                error_count += 1
        
        print(f"\n📊 Sync Summary:")
        print(f"  ✅ Successfully synced: {synced_count}")
        print(f"  ❌ Errors: {error_count}")
        print(f"  📦 Total processed: {len(users_list)}")
        
        if synced_count > 0:
            print(f"\n🎉 Sync completed! {synced_count} users are now searchable in Algolia")
        
    except Exception as e:
        print(f"❌ Error during sync: {str(e)}")
        traceback.print_exc()
        
    finally:
        # Close database connection
        client.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    print("🚀 Starting Algolia sync script...")
    asyncio.run(sync_all_users_to_algolia())