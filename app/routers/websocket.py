from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_progress_update(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
                logger.info(f"Sent progress update to user {user_id}: {message.get('step', 'unknown')}")
            except Exception as e:
                logger.error(f"Error sending WebSocket message to user {user_id}: {str(e)}")
                # Remove disconnected connection
                self.disconnect(user_id)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back or handle keep-alive
            await websocket.send_text(json.dumps({"type": "ping", "message": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Helper function to send progress updates
async def send_progress_update(user_id: str, step: str, progress: int, message: str, details: str = ""):
    """Send progress update to user via WebSocket"""
    import asyncio
    
    update = {
        "type": "progress",
        "step": step,
        "progress": progress,
        "message": message,
        "details": details,
        "timestamp": "now"
    }
    await manager.send_progress_update(user_id, update)
    
    # Add small delay to prevent messages from firing all at once
    await asyncio.sleep(0.5)

# Helper function to send completion update
async def send_completion_update(user_id: str, success: bool, confidence_score: int, missing_sections: list = None):
    """Send completion update with missing sections info"""
    update = {
        "type": "completion",
        "success": success,
        "confidence_score": confidence_score,
        "missing_sections": missing_sections or [],
        "timestamp": "now"
    }
    await manager.send_progress_update(user_id, update)