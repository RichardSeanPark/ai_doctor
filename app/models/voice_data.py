from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class VoiceQuery(BaseModel):
    query_id: str
    timestamp: datetime
    query_text: str
    user_id: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class VoiceResponse(BaseModel):
    response_id: str
    timestamp: datetime
    query_text: str
    response_text: str
    requires_followup: bool = False
    followup_question: Optional[str] = None
    key_points: List[str] = []
    recommendations: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True

class ConsultationSummary(BaseModel):
    consultation_id: str
    timestamp: datetime
    summary: str
    key_points: List[str]
    recommendations: List[str]
    followup_needed: bool = False
    
    class Config:
        arbitrary_types_allowed = True

class VoiceSegment(BaseModel):
    segment_id: str
    text: str
    duration_seconds: float
    segment_type: str  # "greeting", "response", "closing" 등
    
    class Config:
        arbitrary_types_allowed = True 