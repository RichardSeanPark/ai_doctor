from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from uuid import uuid4

class ExerciseRecommendation(BaseModel):
    """운동 추천 모델"""
    recommendation_id: str = str(uuid4())
    user_id: str
    goal: str  # 근력 강화, 유산소, 체중 감량, 유연성 향상 등
    exercise_plans: List[Dict[str, Any]] = []  # [{"name": "운동명", "description": "설명", "duration": "30분", "youtube_link": "URL"}]
    fitness_level: Optional[str] = None  # 초보자, 중급자, 고급자
    recommended_frequency: Optional[str] = None  # 주 3회, 매일 등
    special_instructions: Optional[List[str]] = []  # 특별 지시사항
    timestamp: datetime = datetime.now()
    recommendation_summary: str  # 운동 추천 요약

    class Config:
        arbitrary_types_allowed = True 