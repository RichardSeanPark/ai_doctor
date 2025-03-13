from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date

class SymptomReport(BaseModel):
    symptom_name: str
    severity: int  # 1-10 척도
    onset_time: datetime
    description: Optional[str] = None
    
class MedicationIntake(BaseModel):
    medication_name: str
    dosage: str
    time_taken: datetime
    
class HealthMetrics(BaseModel):
    heart_rate: Optional[int] = None
    blood_pressure: Optional[Dict[str, int]] = None  # {"systolic": 120, "diastolic": 80}
    blood_sugar: Optional[float] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[int] = None
    weight: Optional[float] = None
    sleep_hours: Optional[float] = None
    steps: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True

class Symptom(BaseModel):
    symptom_name: str
    severity: int  # 1-10 척도
    onset_time: datetime
    description: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
    
class HealthAssessment(BaseModel):
    assessment_id: str
    timestamp: datetime
    health_status: str  # "양호", "주의", "경고" 등
    concerns: List[str] = []
    recommendations: List[str] = []
    has_concerns: bool = False
    assessment_summary: str  # Renamed from summary
    query_text: Optional[str] = None  # Added for tracking health queries
    
class DietEntry(BaseModel):
    meal_id: str  # 식사 ID
    entry_id: Optional[str] = None  # 추가 식별자
    user_id: Optional[str] = None  # 사용자 ID
    meal_type: str  # "아침", "점심", "저녁", "간식"
    timestamp: datetime
    food_items: List[Any]  # [{"name": "사과", "calories": 95, "amount": "1개"}, ...]
    total_calories: float
    nutrition_data: Optional[Dict[str, float]] = None  # 영양소 데이터
    image_id: Optional[str] = None  # 관련 이미지 ID
    notes: Optional[str] = None  # 추가 메모
    
class DietAnalysis(BaseModel):
    calories_consumed: float
    nutrition_balance: Dict[str, float]  # {"단백질": 0.8, "탄수화물": 0.6, "지방": 0.4}
    improvement_suggestions: List[str]
    
class ExerciseRecord(BaseModel):
    exercise_id: str
    exercise_type: str
    duration_minutes: int
    calories_burned: float
    timestamp: datetime
    intensity: str  # "낮음", "중간", "높음"
    notes: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class UserProfile(BaseModel):
    user_id: str
    name: str
    birth_date: date
    gender: str
    goals: List[Dict[str, Any]] = []
    current_metrics: Dict[str, Any] = {}
    metrics_history: List[Dict[str, Any]] = []
    dietary_restrictions: List[str] = []
    medical_conditions: List[str] = []
    notification_preferences: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class VoiceSegment(BaseModel):
    segment_id: str
    content: str
    segment_type: str  # "greeting", "question", "response", "follow_up", "conclusion"
    timestamp: datetime
    
    class Config:
        arbitrary_types_allowed = True 