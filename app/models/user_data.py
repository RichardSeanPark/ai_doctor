"""
사용자 데이터 관련 모델 정의
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    """사용자 생성 요청 모델"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "username": "user123",
                "email": "user@example.com",
                "password": "securepassword",
                "full_name": "홍길동"
            }
        }

class UserLogin(BaseModel):
    """사용자 로그인 요청 모델"""
    username: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "username": "user123",
                "password": "securepassword"
            }
        }

class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    user_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
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
                "username": "user123",
                "email": "user@example.com",
                "full_name": "홍길동",
                "birth_date": "1990-01-01",
                "gender": "male",
                "height": 175.0,
                "weight": 70.5
            }
        }

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    user_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    token: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "username": "user123",
                "email": "user@example.com",
                "full_name": "홍길동",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        } 