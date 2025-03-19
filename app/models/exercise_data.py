from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date, time
from uuid import uuid4

class ExerciseRecommendation(BaseModel):
    """운동 추천 정보 모델"""
    recommendation_id: str = str(uuid4())
    user_id: str
    goal: str  # 근력 강화, 유산소, 체중 감량, 유연성 향상 등
    exercise_plans: List[Dict[str, Any]] = []  # [{"name": "운동명", "description": "설명", "duration": "30분", "youtube_link": "URL"}]
    fitness_level: Optional[str] = None  # 초보자, 중급자, 고급자
    recommended_frequency: Optional[str] = None  # 주 3회, 매일 등
    special_instructions: Optional[List[str]] = []  # 특별 지시사항
    recommendation_summary: str  # 운동 추천 요약
    timestamp: datetime = Field(default_factory=datetime.now)

class ExerciseSchedule(BaseModel):
    """운동 스케줄 모델"""
    schedule_id: str = str(uuid4())
    recommendation_id: str
    user_id: str
    day_of_week: int  # 0=일요일, 1=월요일, ..., 6=토요일
    time_of_day: time
    duration_minutes: int = 30
    notification_enabled: bool = True
    notification_minutes_before: int = 30
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ExerciseCompletion(BaseModel):
    """운동 완료 기록 모델"""
    completion_id: str = str(uuid4())
    schedule_id: str
    recommendation_id: str
    user_id: str
    completed_at: datetime = Field(default_factory=datetime.now)
    satisfaction_rating: Optional[int] = None  # 1-5 평점
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True 