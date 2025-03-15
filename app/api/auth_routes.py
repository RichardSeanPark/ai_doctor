"""
인증 관련 API 라우트
회원가입, 로그인 등 인증 기능 제공
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.user_data import UserCreate, UserLogin, UserResponse
from app.models.api_models import ApiResponse
from app.db.user_dao import UserDAO
from app.auth.auth_handler import create_access_token, get_current_user
from app.utils.api_utils import handle_api_error

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 설정
router = APIRouter(tags=["auth"])

# UserDAO 인스턴스
user_dao = UserDAO()

@router.post("/register", response_model=ApiResponse)
async def register_user(user_data: UserCreate):
    """새로운 사용자 등록"""
    async def _register_user():
        # 기존 사용자 확인
        if user_dao.get_user_by_username(user_data.username):
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다.")
        
        if user_data.email and user_dao.get_user_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
        
        # birth_date 검증
        birth_date = None
        if user_data.birth_date:
            try:
                # 날짜 형식 검증만 하고 문자열 그대로 전달
                datetime.strptime(user_data.birth_date, "%Y-%m-%d")
                birth_date = user_data.birth_date
            except ValueError:
                raise HTTPException(status_code=400, detail="생년월일 형식이 올바르지 않습니다. YYYY-MM-DD 형식이어야 합니다.")
        
        # 사용자 생성
        user_id = user_dao.create_user(
            username=user_data.username,
            password=user_data.password,
            name=user_data.full_name,
            birth_date=birth_date,
            gender=user_data.gender,
            email=user_data.email
        )
        
        # 토큰 생성
        token = create_access_token({
            "user_id": user_id,
            "username": user_data.username,
            "email": user_data.email
        })
        
        # 응답 데이터 구성
        return {
            "user_id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
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

@router.get("/profile", response_model=ApiResponse)
async def get_user_profile(current_user=Depends(get_current_user)):
    """
    현재 로그인한 사용자의 프로필 정보를 조회합니다.
    """
    async def _get_user_profile():
        # 사용자 정보 조회
        user = user_dao.get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 민감한 정보 제외
        profile_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "full_name": user["name"],
            "email": user["email"],
            "birth_date": user["birth_date"].isoformat() if user["birth_date"] else None,
            "gender": user["gender"]
        }
        
        return profile_data
    
    return await handle_api_error(
        _get_user_profile,
        "사용자 프로필 조회",
        "사용자 프로필을 성공적으로 조회했습니다."
    ) 