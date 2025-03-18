from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4

class HealthCoachRequest(BaseModel):
    """건강 코치 요청 모델"""
    request_id: str = str(uuid4())
    user_id: str
    query: str
    timestamp: datetime = datetime.now()
    context: Optional[Dict[str, Any]] = None

class HealthCoachResponse(BaseModel):
    """건강 코치 응답 모델"""
    response_id: str = str(uuid4())
    request_id: str
    timestamp: datetime = datetime.now()
    advice: str
    recommendations: List[str]
    explanation: str
    sources: Optional[List[str]] = None
    followup_questions: Optional[List[str]] = None

class HealthGoal(BaseModel):
    """건강 목표 모델"""
    goal_id: str = str(uuid4())
    user_id: str
    goal_type: str  # 체중 감량, 근육 증가, 건강 개선 등
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    start_date: datetime = datetime.now()
    target_date: Optional[datetime] = None
    progress: float = 0.0  # 0.0 ~ 1.0
    status: str = "진행 중"  # 진행 중, 달성, 포기 등
    
class WeeklyHealthReport(BaseModel):
    """주간 건강 리포트 모델"""
    report_id: str = str(uuid4())
    user_id: str
    start_date: datetime
    end_date: datetime
    metrics_summary: Dict[str, Any]
    achievements: List[str]
    challenges: List[str]
    recommendations: List[str]
    next_steps: List[str]
    overall_status: str  # 개선, 유지, 악화 등 

class WeeklyReportRequest(BaseModel):
    """주간 건강 리포트 요청 모델"""
    request_id: str = str(uuid4())
    user_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_metrics: bool = True
    include_activities: bool = True
    include_diet: bool = True
    timestamp: datetime = datetime.now() 