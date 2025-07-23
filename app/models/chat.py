from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    timestamp: str = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            from datetime import datetime
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)