#!/usr/bin/env python3
"""
Optimize MongoDB indexes for admin dashboard performance
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import settings

async def create_optimized_indexes():
    """Create optimized indexes for admin dashboard queries"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    try:
        print("Creating optimized indexes for admin dashboard...")
        
        # 1. Users collection indexes
        print("1. Optimizing users collection...")
        
        # Index for counting users by created_at (for new users stats)
        await db.users.create_index([("created_at", 1)])
        print("   ✓ Created index on created_at")
        
        # Index for profession aggregation (for top professions)
        await db.users.create_index([("profession", 1)])
        print("   ✓ Created index on profession")
        
        # Compound index for active users filtering
        await db.users.create_index([("created_at", 1), ("profession", 1)])
        print("   ✓ Created compound index on created_at + profession")
        
        # 2. User actions collection indexes
        print("2. Optimizing user_actions collection...")
        
        # Index for action type queries (most frequent)
        await db.user_actions.create_index([("action_type", 1)])
        print("   ✓ Created index on action_type")
        
        # Index for timestamp queries (for active users)
        await db.user_actions.create_index([("timestamp", 1)])
        print("   ✓ Created index on timestamp")
        
        # Compound index for user-specific action queries
        await db.user_actions.create_index([("user_id", 1), ("action_type", 1)])
        print("   ✓ Created compound index on user_id + action_type")
        
        # Compound index for time-based action filtering
        await db.user_actions.create_index([("timestamp", 1), ("action_type", 1)])
        print("   ✓ Created compound index on timestamp + action_type")
        
        # Compound index for active users distinct query optimization
        await db.user_actions.create_index([("timestamp", 1), ("user_id", 1)])
        print("   ✓ Created compound index on timestamp + user_id")
        
        # 3. Cover letters collection indexes
        print("3. Optimizing cover_letters collection...")
        
        # Index for recent cover letters queries
        await db.cover_letters.create_index([("created_at", -1)])
        print("   ✓ Created index on created_at (descending)")
        
        # Index for user-specific cover letters
        await db.cover_letters.create_index([("user_id", 1), ("created_at", -1)])
        print("   ✓ Created compound index on user_id + created_at")
        
        # 4. User feedback collection indexes
        print("4. Optimizing user_feedback collection...")
        
        # Index for recent feedback queries
        await db.user_feedback.create_index([("created_at", -1)])
        print("   ✓ Created index on created_at (descending)")
        
        # Index for user-specific feedback
        await db.user_feedback.create_index([("user_id", 1), ("created_at", -1)])
        print("   ✓ Created compound index on user_id + created_at")
        
        print("\n🚀 All indexes created successfully!")
        print("\nAdmin dashboard queries should now be significantly faster!")
        
        # Show index statistics
        print("\n📊 Index Statistics:")
        collections = ['users', 'user_actions', 'cover_letters', 'user_feedback']
        
        for collection_name in collections:
            collection = db[collection_name]
            indexes = await collection.list_indexes().to_list(length=None)
            print(f"\n{collection_name}: {len(indexes)} indexes")
            for idx in indexes:
                keys = list(idx.get('key', {}).keys())
                print(f"  - {', '.join(keys)}")
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        return False
    
    finally:
        client.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(create_optimized_indexes())
    sys.exit(0 if success else 1)
