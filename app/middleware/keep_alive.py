# Keep-alive middleware to prevent Render free tier from sleeping
# This sends a ping every 10 minutes to keep the server awake

import asyncio
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class KeepAliveMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.last_request_time = asyncio.get_event_loop().time()
        
    async def dispatch(self, request: Request, call_next):
        # Update last request time
        self.last_request_time = asyncio.get_event_loop().time()
        
        # Add keep-alive header
        response = await call_next(request)
        response.headers["Keep-Alive"] = "timeout=300, max=1000"
        
        return response

# Background task to ping the server every 10 minutes
async def keep_alive_ping():
    """Send a ping to keep the server awake on Render free tier"""
    import httpx
    import os
    
    # Only run on Render (not localhost)
    if not os.getenv("RENDER_EXTERNAL_URL"):
        logger.info("Not running on Render, skipping keep-alive ping")
        return
    
    while True:
        try:
            # Wait 10 minutes
            await asyncio.sleep(600)
            
            # Ping the health endpoint
            async with httpx.AsyncClient() as client:
                # Get the current server URL from environment
                server_url = os.getenv("RENDER_EXTERNAL_URL")
                if server_url:
                    await client.get(f"{server_url}/health", timeout=10)
                    logger.info("Keep-alive ping sent successfully")
                
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")
            # Continue trying even if ping fails
