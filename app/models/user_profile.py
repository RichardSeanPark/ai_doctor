from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import date, datetime

class UserGoal(BaseModel):
    goal_type: str  # "체중감량", "근육증가", "건강유지" 등
    target_value: float
    deadline: Optional[date] = None
    
class HealthMetrics(BaseModel):
    weight: float
    height: float
    bmi: float
    body_fat_percentage: Optional[float] = None
    blood_pressure: Optional[Dict[str, float]] = None  # {"systolic": 120, "diastolic": 80}
    heart_rate: Optional[int] = None
    sleep_hours: Optional[float] = None
    
class UserProfile(BaseModel):
    user_id: str
    name: str
    birth_date: date
    gender: str
    goals: List[UserGoal] = []
    current_metrics: HealthMetrics
    metrics_history: List[Dict[str, Any]] = []
    dietary_restrictions: List[str] = []
    medical_conditions: List[str] = []
    notification_preferences: Dict[str, Any] = {
        "android_device_id": "",
        "notification_time": [],
        "voice_preference": {
            "voice_type": "female",
            "speech_speed": 1.0
        }
    }
    
    class Config:
        arbitrary_types_allowed = True 