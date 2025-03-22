"""
인증 관련 API 라우트
소셜 로그인 등 인증 기능 제공
"""

import logging
import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.user_data import UserResponse, SocialLoginRequest
from app.models.api_models import ApiResponse
from app.db.user_dao import UserDAO
from app.auth.auth_handler import create_access_token, get_current_user
from app.utils.api_utils import handle_api_error
from app.config.settings import get_settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 설정 로드
settings = get_settings()

# 라우터 설정
router = APIRouter(tags=["auth"])

# UserDAO 인스턴스
user_dao = UserDAO()

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
        
        # 프로필 데이터 구성
        profile_data = {
            "user_id": user["user_id"],
            "birth_date": user["birth_date"].isoformat() if user["birth_date"] else None,
            "gender": user["gender"]
        }
        
        # 최신 건강 지표 조회 (키, 몸무게)
        latest_metrics_query = """
            SELECT height, weight FROM health_metrics 
            WHERE user_id = %s 
            ORDER BY timestamp DESC LIMIT 1
        """
        latest_metrics = user_dao.db.fetch_one(latest_metrics_query, (user["user_id"],))
        
        if latest_metrics:
            profile_data["height"] = latest_metrics.get("height")
            profile_data["weight"] = latest_metrics.get("weight")
        
        return profile_data
    
    return await handle_api_error(
        _get_user_profile,
        "사용자 프로필 조회",
        "사용자 프로필을 성공적으로 조회했습니다."
    )

# 카카오 소셜 로그인 엔드포인트
@router.post("/social/login", response_model=ApiResponse)
async def kakao_login(login_request: SocialLoginRequest):
    """
    카카오 ID를 이용한 소셜 로그인/회원가입 처리
    
    카카오 ID만 사용하여 소셜 로그인을 처리합니다.
    """
    async def _process_kakao_login():
        social_id = login_request.social_id
        
        if not social_id:
            raise HTTPException(status_code=400, detail="카카오 ID가 제공되지 않았습니다.")
        
        # 기존 소셜 계정 확인
        user = user_dao.get_social_account(social_id, "kakao")
        
        user_id = None
        is_new_user = False
        
        if user:
            # 기존 사용자
            user_id = user["user_id"]
        else:
            # 새 사용자 생성
            is_new_user = True
            user_id = user_dao.create_user(social_id=social_id, provider="kakao")
        
        # JWT 토큰 생성
        token = create_access_token({
            "user_id": user_id
        })
        
        # 응답 데이터 구성
        return {
            "user_id": user_id,
            "token": token,
            "is_new_user": is_new_user
        }
    
    return await handle_api_error(
        _process_kakao_login,
        "카카오 로그인 처리",
        "카카오 로그인이 완료되었습니다."
    )

# 건강 지표 업데이트 엔드포인트
@router.post("/profile/health-metrics", response_model=ApiResponse)
async def update_health_metrics(height: Optional[float] = None, weight: Optional[float] = None, current_user=Depends(get_current_user)):
    """
    사용자의 건강 지표를 업데이트합니다.
    현재는 키와 몸무게만 지원합니다.
    """
    async def _update_health_metrics():
        if height is None and weight is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="최소한 하나 이상의 건강 지표를 제공해야 합니다."
            )
        
        # 건강 지표 저장
        metrics_id = user_dao.update_health_metrics(
            user_id=current_user["user_id"],
            height=height,
            weight=weight
        )
        
        if not metrics_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="건강 지표 저장 중 오류가 발생했습니다."
            )
        
        return {
            "metrics_id": metrics_id,
            "height": height,
            "weight": weight
        }
    
    return await handle_api_error(
        _update_health_metrics,
        "건강 지표 업데이트",
        "건강 지표가 성공적으로 업데이트되었습니다."
    ) 