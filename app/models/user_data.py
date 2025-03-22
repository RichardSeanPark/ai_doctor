"""
사용자 데이터 관련 모델 정의
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime

class UserCreate(BaseModel):
    """사용자 생성 모델"""
    username: str
    password: str
    email: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "username": "user123",
                "password": "securepassword",
                "email": "user@example.com"
            }
        }

class UserLogin(BaseModel):
    """사용자 로그인 모델"""
    username: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "user123",
                "password": "securepassword"
            }
        }

class SocialLoginRequest(BaseModel):
    """
    안드로이드 앱에서 소셜 로그인 요청 모델 (카카오용)
    앱에서 이미 소셜 인증이 완료된 후 서버로 전송되는 정보
    """
    social_id: str  # 카카오 ID
    
    class Config:
        schema_extra = {
            "example": {
                "social_id": "12345678"
            }
        }

class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    user_id: str
    social_id: str
    provider: str = "kakao"
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "user_id": "user123",
                "social_id": "12345678",
                "provider": "kakao",
                "birth_date": "1990-01-01",
                "gender": "male",
                "height": 175.0,
                "weight": 70.5
            }
        }

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    user_id: str
    token: Optional[str] = None
    is_new_user: Optional[bool] = False
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "is_new_user": False
            }
        }

class HealthMetricsUpdate(BaseModel):
    """건강 지표 업데이트 요청 모델"""
    height: Optional[float] = None
    weight: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "height": 175.0,
                "weight": 70.5
            }
        } 