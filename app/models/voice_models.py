"""
음성 관련 데이터 모델 정의
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class QueryType(str, Enum):
    """쿼리 유형 열거형"""
    GENERAL = "general"
    HEALTH = "health"
    DIET = "diet"
    EXERCISE = "exercise"
    MEDICATION = "medication"

class VoiceQuery(BaseModel):
    """음성 쿼리 모델"""
    query_text: str
    user_id: str
    conversation_id: Optional[str] = None
    query_type: Optional[QueryType] = QueryType.GENERAL
    voice_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

class VoiceResponse(BaseModel):
    """음성 응답 모델"""
    response_text: str
    conversation_id: str
    requires_followup: bool = False
    followup_question: Optional[str] = None
    key_points: List[str] = []
    recommendations: List[str] = []
    timestamp: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True

class VoiceQueryRequest(BaseModel):
    """음성 쿼리 요청 모델"""
    user_id: str
    query_text: str
    conversation_id: Optional[str] = None
    query_type: Optional[str] = "general"
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "query_text": "오늘 두통이 있어요",
                "conversation_id": "conv_abc123",
                "query_type": "health"
            }
        }

class ConsultationRequest(BaseModel):
    """상담 요청 모델"""
    user_id: str
    initial_query: str
    health_context: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "initial_query": "건강 상담을 받고 싶어요",
                "health_context": {
                    "recent_symptoms": ["두통", "피로감"],
                    "chronic_conditions": ["고혈압"]
                }
            }
        } 