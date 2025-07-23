import motor.motor_asyncio
from app.config import settings

class Database:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    database: motor.motor_asyncio.AsyncIOMotorDatabase = None

db = Database()

async def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    db.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    db.database = db.client[settings.DATABASE_NAME]
    
    # Create indexes for better performance
    await create_indexes()

async def close_mongo_connection():
    """Close database connection"""
    db.client.close()

async def create_indexes():
    """Create database indexes for optimal performance"""
    users_collection = db.database.users
    
    # Create indexes
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("designation")
    await users_collection.create_index("location")
    await users_collection.create_index("skills.name")
    await users_collection.create_index("is_looking_for_job")
    await users_collection.create_index([("name", "text"), ("designation", "text"), ("summary", "text")])