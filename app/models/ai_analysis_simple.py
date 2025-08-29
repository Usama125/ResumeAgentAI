from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class AIAnalysis(BaseModel):
    """Simple AI Analysis model for caching"""
    id: Optional[str] = Field(alias="_id", default=None)
    user_id: str
    analysis_type: str  # "profile" or "public" 
    analysis_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}