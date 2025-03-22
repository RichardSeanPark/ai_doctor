"""
설정 관리 모듈

환경 변수와 기본 설정값을 관리합니다.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# 환경 변수 로드
load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 서버 설정
    API_HOST: str = Field(default="0.0.0.0", description="API 서버 호스트")
    API_PORT: int = Field(default=8080, description="API 서버 포트")
    
    # 구글 API 설정
    GOOGLE_API_KEY: str = Field(
        default=os.getenv("GOOGLE_API_KEY", ""), 
        description="Google API 키"
    )
    GEMINI_MODEL: str = Field(
        default=os.getenv("GEMINI_MODEL", "gemini-2.0-pro-exp-02-05"), 
        description="Gemini 모델명"
    )
    
    # OAuth 소셜 로그인 설정 - 안드로이드 앱용
    # Google OAuth 설정
    GOOGLE_CLIENT_ID: str = Field(
        default=os.getenv("GOOGLE_CLIENT_ID", ""), 
        description="Google OAuth 클라이언트 ID"
    )
    
    # Kakao OAuth 설정
    KAKAO_CLIENT_ID: str = Field(
        default=os.getenv("KAKAO_CLIENT_ID", ""), 
        description="Kakao OAuth 클라이언트 ID"
    )
    
    # 서버측 ID 검증용 (토큰 검증 시 사용, 선택적)
    GOOGLE_CLIENT_SECRET: str = Field(
        default=os.getenv("GOOGLE_CLIENT_SECRET", ""), 
        description="Google OAuth 서버측 검증용 시크릿 (선택적)"
    )
    KAKAO_CLIENT_SECRET: str = Field(
        default=os.getenv("KAKAO_CLIENT_SECRET", ""), 
        description="Kakao OAuth 서버측 검증용 시크릿 (선택적)"
    )
    
    # 의료 데이터 관련 설정
    MAX_HEALTH_HISTORY_DAYS: int = Field(
        default=int(os.getenv("MAX_HEALTH_HISTORY_DAYS", 365)), 
        description="건강 기록 최대 보관 일수"
    )
    
    # 알림 설정
    DEFAULT_NOTIFICATION_PRIORITY: str = Field(
        default=os.getenv("DEFAULT_NOTIFICATION_PRIORITY", "normal"),
        description="기본 알림 우선순위"
    )
    
    # 데이터베이스 연결 설정
    DB_HOST: str = Field(
        default=os.getenv("DB_HOST", "localhost"), 
        description="데이터베이스 호스트"
    )
    DB_USER: str = Field(
        default=os.getenv("DB_USER", ""), 
        description="데이터베이스 사용자"
    )
    DB_PASSWORD: str = Field(
        default=os.getenv("DB_PASSWORD", ""), 
        description="데이터베이스 비밀번호"
    )
    DB_NAME: str = Field(
        default=os.getenv("DB_NAME", "healthai_db"), 
        description="데이터베이스 이름"
    )
    DB_PORT: int = Field(
        default=int(os.getenv("DB_PORT", 3306)), 
        description="데이터베이스 포트"
    )
    DB_CHARSET: str = Field(
        default=os.getenv("DB_CHARSET", "utf8mb4"), 
        description="데이터베이스 문자 인코딩"
    )
    
    # JWT 인증 설정
    JWT_SECRET: str = Field(
        default=os.getenv("JWT_SECRET", "health_ai_secret_key"), 
        description="JWT 시크릿 키"
    )
    JWT_ALGORITHM: str = Field(
        default=os.getenv("JWT_ALGORITHM", "HS256"), 
        description="JWT 알고리즘"
    )
    JWT_EXPIRATION: int = Field(
        default=int(os.getenv("JWT_EXPIRATION", 86400)), 
        description="JWT 토큰 만료 시간(초)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 설정 인스턴스 생성
settings = Settings()

def get_settings() -> Settings:
    """설정 인스턴스 반환"""
    return settings

def get_db_url() -> str:
    """데이터베이스 연결 URL 반환"""
    return f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset={settings.DB_CHARSET}" 