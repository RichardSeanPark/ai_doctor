"""
인증 관련 API 라우트
회원가입, 로그인 등 인증 기능 제공
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional

from app.models.user_data import UserCreate, UserLogin, UserResponse
from app.models.api_models import ApiResponse
from app.db.user_dao import UserDAO
from app.auth.auth_handler import create_access_token
from app.utils.api_utils import handle_api_error

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 설정
router = APIRouter(tags=["auth"])

# UserDAO 인스턴스
user_dao = UserDAO()

@router.post("/register", response_model=ApiResponse)
async def register_user(user_data: UserCreate):
    """
    새 사용자 등록 (회원가입)
    """
    async def _register_user():
        # 사용자 아이디 중복 확인
        existing_user = user_dao.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자 이름입니다."
            )
        
        # 이메일 중복 확인
        if user_data.email:
            existing_email = user_dao.get_user_by_email(user_data.email)
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 이메일입니다."
                )
        
        # 사용자 생성
        logger.info(f"새 사용자 등록: {user_data.username}")
        user_id = user_dao.create_user(
            username=user_data.username,
            password=user_data.password,
            name=user_data.full_name,
            email=user_data.email
        )
        
        # 사용자 정보 조회
        user = user_dao.get_user_by_id(user_id)
        
        # 토큰 생성
        token = create_access_token({
            "user_id": user_id,
            "username": user["username"],
            "email": user.get("email")
        })
        
        # 응답 데이터 구성
        return {
            "user_id": user_id,
            "username": user["username"],
            "email": user.get("email"),
            "full_name": user.get("name"),
            "token": token
        }
    
    return await handle_api_error(
        _register_user,
        "사용자 등록",
        "회원가입이 완료되었습니다."
    )
    
@router.post("/login", response_model=ApiResponse)
async def login_user(login_data: UserLogin):
    """
    사용자 로그인
    """
    async def _login_user():
        # 사용자 인증
        user = user_dao.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 사용자 이름 또는 비밀번호입니다."
            )
        
        # 토큰 생성
        token = create_access_token({
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user.get("email")
        })
        
        # 응답 데이터 구성
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user.get("email"),
            "full_name": user.get("name"),
            "token": token
        }
    
    return await handle_api_error(
        _login_user,
        "사용자 로그인",
        "로그인이 완료되었습니다."
    ) 