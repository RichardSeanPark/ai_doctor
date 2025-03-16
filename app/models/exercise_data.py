from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4

class ExerciseRecommendation(BaseModel):
    """운동 추천 모델"""
    recommendation_id: str = str(uuid4())
    timestamp: datetime = datetime.now()
    time_available: int  # 사용자가 운동에 할애할 수 있는 시간(분)
    location: str  # 운동 장소 (집, 사무실, 헬스장 등)
    intensity: str  # 운동 강도 (낮음, 중간, 높음)
    exercises: List[Dict[str, Any]]  # 추천된 운동 목록
    total_calories: float  # 예상 소모 칼로리
    description: str  # 추천 설명
    tips: List[str]  # 운동 팁
    
class ExerciseRecord(BaseModel):
    """운동 기록 모델"""
    record_id: str = str(uuid4())
    user_id: str
    timestamp: datetime = datetime.now()
    exercise_type: str
    duration_minutes: int
    calories_burned: float
    intensity: str  # 낮음, 중간, 높음
    notes: Optional[str] = None
    
class ExerciseRoutine(BaseModel):
    """운동 루틴 모델"""
    routine_id: str = str(uuid4())
    user_id: str
    name: str
    description: str
    exercises: List[Dict[str, Any]]
    total_duration: int
    estimated_calories: float
    difficulty: str  # 초급, 중급, 고급
    tags: List[str] = []  # 태그 (예: 유산소, 근력, 스트레칭 등) 