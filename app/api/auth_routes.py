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
                status_code=status.HTTP_401_UNAUTHORIZED,
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

# 소셜 로그인 엔드포인트
@router.post("/social/login", response_model=ApiResponse)
async def social_login(login_request: SocialLoginRequest):
    """
    소셜 로그인/회원가입 처리
    
    소셜 ID와 provider(kakao 또는 google)를 사용하여 소셜 로그인을 처리합니다.
    """
    async def _process_social_login():
        social_id = login_request.social_id
        provider = login_request.provider
        
        if not social_id:
            raise HTTPException(status_code=400, detail="소셜 ID가 제공되지 않았습니다.")
        
        if provider not in ["kakao", "google"]:
            raise HTTPException(status_code=400, detail="지원하지 않는 provider입니다. kakao 또는 google만 지원합니다.")
        
        # 기존 소셜 계정 확인
        user = user_dao.get_social_account(social_id, provider)
        
        user_id = None
        is_new_user = False
        
        if user:
            # 기존 사용자
            user_id = user["user_id"]
        else:
            # 새 사용자 생성
            is_new_user = True
            user_id = user_dao.create_user(social_id=social_id, provider=provider)
        
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
        _process_social_login,
        "소셜 로그인 처리",
        f"{login_request.provider} 로그인이 완료되었습니다."
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

# 사용자 프로필 업데이트 엔드포인트 (생년월일, 성별)
@router.post("/profile/update", response_model=ApiResponse)
async def update_user_profile(birth_date: Optional[str] = None, gender: Optional[str] = None, current_user=Depends(get_current_user)):
    """
    사용자의 생년월일과 성별을 업데이트합니다.
    생년월일과 성별 모두 social_accounts 테이블에 저장됩니다.
    """
    async def _update_user_profile():
        user_id = current_user["user_id"]
        updated_fields = {}
        
        if birth_date is None and gender is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="생년월일 또는 성별 중 최소한 하나는 제공해야 합니다."
            )
            
        # 1. 생년월일 업데이트 (제공된 경우)
        if birth_date is not None:
            try:
                # 날짜 형식 확인
                parsed_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
                
                # social_accounts 테이블에 생년월일 업데이트
                birth_date_updated = user_dao.update_user(user_id, birth_date=parsed_date)
                
                if birth_date_updated:
                    updated_fields["birth_date"] = birth_date
                    logger.info(f"사용자 {user_id}의 생년월일이 업데이트되었습니다: {birth_date}")
                else:
                    logger.warning(f"사용자 {user_id}의 생년월일 업데이트 실패")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요."
                )
        
        # 2. 성별 업데이트 (제공된 경우)
        if gender is not None:
            # 성별 값 검증 (male 또는 female만 허용)
            if gender not in ["male", "female"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 성별입니다. 'male' 또는 'female'로 입력해주세요."
                )
                
            # social_accounts 테이블에 성별 업데이트
            gender_updated = user_dao.update_user(user_id, gender=gender)
            
            if gender_updated:
                updated_fields["gender"] = gender
                logger.info(f"사용자 {user_id}의 성별이 업데이트되었습니다: {gender}")
            else:
                logger.warning(f"사용자 {user_id}의 성별 업데이트 실패")
        
        # 응답 데이터 구성
        response_data = {
            "user_id": user_id,
            "updated_fields": updated_fields
        }
            
        if not updated_fields:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="프로필 업데이트 중 오류가 발생했습니다."
            )
            
        return response_data
    
    return await handle_api_error(
        _update_user_profile,
        "사용자 프로필 업데이트",
        "사용자 프로필이 성공적으로 업데이트되었습니다."
    )

# 계정 삭제 엔드포인트
@router.delete("/account", response_model=ApiResponse)
async def delete_account(current_user=Depends(get_current_user)):
    """
    현재 로그인한 사용자의 계정을 삭제합니다.
    모든 관련 데이터(세션, 건강 지표, 식단 기록 등)가 함께 삭제됩니다.
    """
    async def _delete_account():
        user_id = current_user["user_id"]
        
        # 사용자 존재 여부 확인
        user = user_dao.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        # 사용자 계정 삭제 (관련된 모든 데이터는 CASCADE로 삭제됨)
        success = user_dao.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="계정 삭제 중 오류가 발생했습니다."
            )
        
        return {
            "user_id": user_id,
            "deleted": True
        }
    
    return await handle_api_error(
        _delete_account,
        "계정 삭제",
        "계정이 성공적으로 삭제되었습니다."
    ) 