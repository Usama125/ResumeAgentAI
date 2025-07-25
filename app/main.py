from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, users, onboarding, chat, search, job_matching

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI Resume Builder Backend API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cvchatter.com", "https://www.cvchatter.com", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "pdfs"))
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "profiles"))

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(onboarding.router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["onboarding"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
app.include_router(job_matching.router, prefix=f"{settings.API_V1_STR}/job-matching", tags=["job-matching"])

# Database events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "AI Resume Builder API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}