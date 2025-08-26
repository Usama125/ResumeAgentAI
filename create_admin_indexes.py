#!/usr/bin/env python3
"""
Create database indexes for admin analytics collections
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def create_admin_indexes():
    """Create indexes for admin collections"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        print("Creating indexes for admin collections...")
        
        # User actions collection indexes
        actions_collection = db.user_actions
        await actions_collection.create_index([("timestamp", -1)])  # Recent actions first
        await actions_collection.create_index([("user_id", 1)])     # User actions lookup
        await actions_collection.create_index([("action_type", 1)]) # Action type filtering
        await actions_collection.create_index([("user_id", 1), ("action_type", 1)])  # Combined lookup
        print("✅ Created indexes for user_actions collection")
        
        # Cover letters collection indexes
        cover_letters_collection = db.cover_letters
        await cover_letters_collection.create_index([("created_at", -1)])  # Recent first
        await cover_letters_collection.create_index([("user_id", 1)])      # User lookup
        await cover_letters_collection.create_index([("username", 1)])     # Username lookup
        print("✅ Created indexes for cover_letters collection")
        
        # User feedback collection indexes
        feedback_collection = db.user_feedback
        await feedback_collection.create_index([("created_at", -1)])  # Recent first
        await feedback_collection.create_index([("status", 1)])       # Status filtering
        await feedback_collection.create_index([("user_id", 1)])      # User lookup
        print("✅ Created indexes for user_feedback collection")
        
        # Users collection additional indexes for admin queries
        users_collection = db.users
        await users_collection.create_index([("created_at", -1)])     # Recent users first
        await users_collection.create_index([("profession", 1)])      # Profession grouping
        await users_collection.create_index([("is_blocked", 1)])      # Block status
        await users_collection.create_index([("username", 1)])        # Username lookup
        print("✅ Created additional indexes for users collection")
        
        print("\n🎉 All admin indexes created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {str(e)}")
    finally:
        await client.close()

def main():
    """Main function"""
    print("Admin Database Index Creator")
    print("=" * 40)
    asyncio.run(create_admin_indexes())

if __name__ == "__main__":
    main()
