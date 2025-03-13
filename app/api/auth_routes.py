"""
사용자 인증 관련 API 라우트
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator

from app.db.user_dao import UserDAO

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["auth"])

# 모델 정의
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    birth_date: str  # YYYY-MM-DD 형식
    gender: str = Field(..., pattern="^(male|female|other)$")
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("날짜 형식은 YYYY-MM-DD여야 합니다")

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    name: str

class ApiResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[Dict[str, Any]] = None

# 사용자 DAO 인스턴스
user_dao = UserDAO()

@router.post("/register", response_model=ApiResponse)
async def register_user(user_data: UserRegisterRequest):
    """새 사용자 등록"""
    try:
        # 사용자명 중복 확인
        existing_user = user_dao.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 사용자명입니다"
            )
        
        # 이메일 중복 확인 (실제 구현 시 추가)
        
        # 사용자 생성
        birth_date = datetime.strptime(user_data.birth_date, "%Y-%m-%d").date()
        
        user_id = user_dao.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            birth_date=birth_date,
            gender=user_data.gender
        )
        
        return ApiResponse(
            success=True,
            message="사용자 등록 성공",
            data={"user_id": user_id}
        )
    except HTTPException as e:
        logger.error(f"사용자 등록 오류: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"사용자 등록 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 등록 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLoginRequest):
    """사용자 로그인 및 세션 토큰 발급"""
    try:
        # 사용자 인증
        user_id = user_dao.authenticate_user(login_data.username, login_data.password)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 사용자명 또는 비밀번호"
            )
        
        # 사용자 정보 조회
        user = user_dao.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 정보를 찾을 수 없습니다"
            )
        
        # 세션 생성 (24시간 유효)
        session_id = user_dao.create_session(
            user_id, 
            datetime.now() + timedelta(days=1)
        )
        
        return TokenResponse(
            access_token=session_id,
            user_id=user_id,
            username=user["username"],
            name=user["name"]
        )
    except HTTPException as e:
        logger.error(f"로그인 오류: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"로그인 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/logout", response_model=ApiResponse)
async def logout_user(token: str):
    """사용자 로그아웃 (세션 종료)"""
    try:
        # 세션 삭제
        success = user_dao.delete_session(token)
        
        if not success:
            return ApiResponse(
                success=False,
                message="로그아웃 중 오류가 발생했습니다"
            )
        
        return ApiResponse(
            success=True,
            message="성공적으로 로그아웃되었습니다"
        )
    except Exception as e:
        logger.error(f"로그아웃 오류: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"로그아웃 중 오류가 발생했습니다: {str(e)}"
        ) 