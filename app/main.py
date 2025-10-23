from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, users, onboarding, chat, search, job_matching, websocket, admin, dummy_users, content_generator, admin_users
from app.middleware.keep_alive import KeepAliveMiddleware, keep_alive_ping

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI Resume Builder Backend API"
)

# CORS middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cvchatter.com", "https://www.cvchatter.com", "http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep-alive middleware (prevents Render free tier from sleeping)
app.add_middleware(KeepAliveMiddleware)

# Add caching middleware for profile endpoints
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add cache headers for profile endpoints (only for GET requests)
    # Don't cache PUT/POST/DELETE requests to ensure fresh data after updates
    if (request.method == "GET" and 
        (request.url.path.startswith("/api/v1/users/username/") or 
         request.url.path.startswith("/api/v1/users/")) and
        not request.url.path.endswith("/me") and  # Don't cache current user's profile
        not request.url.path.endswith("/ai-analysis") and  # Don't cache AI analysis
        not request.url.path.endswith("/professional-analysis")):
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
        response.headers["ETag"] = f'"{hash(request.url.path)}"'
    
    # Ensure profile update endpoints don't get cached
    elif (request.method in ["PUT", "POST", "DELETE"] and 
          request.url.path.startswith("/api/v1/users/")):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response

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
app.include_router(websocket.router, prefix=f"{settings.API_V1_STR}", tags=["websocket"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}", tags=["admin"])
app.include_router(admin_users.router, prefix=f"{settings.API_V1_STR}", tags=["admin-users"])
app.include_router(dummy_users.router, tags=["dummy-users"])
app.include_router(content_generator.router, prefix=f"{settings.API_V1_STR}", tags=["content-generator"])

# Database events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    # Start keep-alive ping task for Render free tier
    asyncio.create_task(keep_alive_ping())

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "AI Resume Builder API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}