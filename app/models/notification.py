from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.models.voice_data import VoiceSegment

class AndroidNotification(BaseModel):
    title: str
    body: str
    priority: str = "normal"  # "high", "normal", "low"
    data: Optional[Dict[str, Any]] = None
    channel_id: str = "health_ai_channel"
    
class VoiceResponse(BaseModel):
    text: str
    voice_type: str = "female"  # "male", "female"
    speech_speed: float = 1.0
    
class NotificationResult(BaseModel):
    notification_id: str
    timestamp: datetime
    status: str
    message: str
    
class ConsultationSummary(BaseModel):
    consultation_id: str
    timestamp: datetime
    topic: str
    summary: str
    key_points: List[str]
    recommendations: List[str]
    followup_needed: bool = False
    
class UserState(BaseModel):
    user_profile: Dict[str, Any]
    user_id: Optional[str] = None
    query_text: Optional[str] = None
    voice_scripts: List[str] = []
    notifications: List[AndroidNotification] = []
    current_notification: Optional[AndroidNotification] = None
    voice_input: Optional[str] = None
    voice_data: Optional[Dict[str, Any]] = None
    voice_segments: List[VoiceSegment] = []
    recent_meals: Optional[Dict[str, Any]] = None
    progress_data: Optional[Dict[str, Any]] = None
    diet_analysis: Optional[Any] = None
    health_assessment: Optional[Any] = None
    health_metrics: Optional[Dict[str, Any]] = None
    symptoms: Optional[List[Dict[str, Any]]] = None
    last_response: Optional[Any] = None
    
    class Config:
        arbitrary_types_allowed = True 