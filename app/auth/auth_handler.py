"""
JWT 인증 처리 모듈

JWT 토큰 생성, 검증 및 사용자 인증을 처리합니다.
"""

import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.config.settings import Settings, get_settings

# OAuth2 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
settings = get_settings()

# 모델 정의
class UserInfo(BaseModel):
    """사용자 정보 모델"""
    user_id: str
    role: str = "user"

def create_access_token(user_data: Dict) -> str:
    """액세스 토큰 생성"""
    # 페이로드에 만료 시간 추가
    expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION)
    payload = {
        "sub": user_data["user_id"],
        "role": user_data.get("role", "user"),
        "exp": expire.timestamp()
    }
    
    # JWT 토큰 생성
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token

def decode_token(token: str) -> Dict:
    """토큰 디코딩 및 검증"""
    try:
        # 토큰 디코딩
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # 만료 시간 확인
        if "exp" in payload and payload["exp"] < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    현재 인증된 사용자 정보 조회
    
    참고: 프로덕션 환경에서는 데이터베이스에서 사용자 정보를 조회하는 코드를 추가해야 합니다.
    """
    try:
        # 토큰 디코딩
        payload = decode_token(token)
        
        # 사용자 정보를 사전 형태로 반환
        user_info = {
            "user_id": payload["sub"],
            "role": payload.get("role", "user")
        }
        
        return user_info
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증에 실패했습니다",
            headers={"WWW-Authenticate": "Bearer"}
        ) 