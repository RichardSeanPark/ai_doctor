"""
건강 데이터 관련 API 라우트
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator

from app.db.health_dao import HealthDAO
from app.auth.auth_handler import get_current_user
from app.nodes.health_check_nodes import analyze_health_metrics
from app.utils.api_utils import handle_api_error  # 공통 에러 처리 함수 임포트
from app.models.api_models import ApiResponse  # ApiResponse 모델 임포트

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["health"])

# 모델 정의
class HealthMetricsRequest(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    blood_sugar: Optional[float] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[int] = None
    sleep_hours: Optional[float] = None
    steps: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "weight": 70.5,
                "height": 175.0,
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "blood_sugar": 95.5,
                "temperature": 36.5,
                "oxygen_saturation": 98,
                "sleep_hours": 7.5,
                "steps": 8500
            }
        }

class MedicalConditionRequest(BaseModel):
    condition_name: str
    diagnosis_date: Optional[str] = None  # YYYY-MM-DD 형식
    is_active: bool = True
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "condition_name": "고혈압",
                "diagnosis_date": "2023-01-15",
                "is_active": True,
                "notes": "약물 치료 중"
            }
        }

class DietaryRestrictionRequest(BaseModel):
    restriction_type: str  # "알레르기", "종교적", "건강상", "선호도" 등
    description: str
    severity: Optional[str] = None  # "약함", "중간", "강함"
    
    class Config:
        schema_extra = {
            "example": {
                "restriction_type": "알레르기",
                "description": "유제품",
                "severity": "중간"
            }
        }

class HealthQueryRequest(BaseModel):
    query_text: str
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "나의 최근 심박수 변화가 정상인가요?"
            }
        }

# 건강 DAO 인스턴스
health_dao = HealthDAO()

@router.post("/metrics", response_model=ApiResponse)
async def add_health_metrics(metrics: HealthMetricsRequest, user=Depends(get_current_user)):
    """사용자 건강 지표 추가"""
    async def _add_health_metrics():
        metrics_dict = metrics.dict()
        metrics_id = health_dao.add_health_metrics(user["user_id"], metrics_dict)
        return {"metrics_id": metrics_id}
    
    return await handle_api_error(
        _add_health_metrics,
        "건강 지표 추가",
        "건강 지표가 추가되었습니다"
    )

@router.get("/metrics/latest", response_model=ApiResponse)
async def get_latest_metrics(user=Depends(get_current_user)):
    """사용자의 최신 건강 지표 조회"""
    async def _get_latest_metrics():
        metrics = health_dao.get_latest_health_metrics(user["user_id"])
        return {"metrics": metrics}
    
    return await handle_api_error(
        _get_latest_metrics,
        "최신 건강 지표 조회",
        "최신 건강 지표 조회 성공"
    )

@router.get("/metrics/history", response_model=ApiResponse)
async def get_metrics_history(limit: int = 10, user=Depends(get_current_user)):
    """사용자의 건강 지표 이력 조회"""
    try:
        metrics_history = health_dao.get_health_metrics_history(user["user_id"], limit)
        
        return ApiResponse(
            success=True,
            message="건강 지표 이력 조회 성공",
            data={"metrics_history": metrics_history}
        )
    except Exception as e:
        logger.error(f"건강 지표 이력 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"건강 지표 이력 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/medical-conditions", response_model=ApiResponse)
async def add_medical_condition(condition: MedicalConditionRequest, user=Depends(get_current_user)):
    """의학적 상태 추가"""
    try:
        diagnosis_date = None
        if condition.diagnosis_date:
            diagnosis_date = datetime.strptime(condition.diagnosis_date, "%Y-%m-%d").date()
            
        condition_id = health_dao.add_medical_condition(
            user["user_id"],
            condition.condition_name,
            diagnosis_date,
            condition.is_active,
            condition.notes
        )
        
        return ApiResponse(
            success=True,
            message="의학적 상태가 추가되었습니다",
            data={"condition_id": condition_id}
        )
    except Exception as e:
        logger.error(f"의학적 상태 추가 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"의학적 상태 추가 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/medical-conditions", response_model=ApiResponse)
async def get_medical_conditions(active_only: bool = True, user=Depends(get_current_user)):
    """사용자의 의학적 상태 조회"""
    try:
        conditions = health_dao.get_medical_conditions(user["user_id"], active_only)
        
        return ApiResponse(
            success=True,
            message="의학적 상태 조회 성공",
            data={"conditions": conditions}
        )
    except Exception as e:
        logger.error(f"의학적 상태 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"의학적 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/dietary-restrictions", response_model=ApiResponse)
async def add_dietary_restriction(restriction: DietaryRestrictionRequest, user=Depends(get_current_user)):
    """식이 제한 추가"""
    try:
        restriction_id = health_dao.add_dietary_restriction(
            user["user_id"],
            restriction.restriction_type,
            restriction.is_active,
            restriction.notes
        )
        
        return ApiResponse(
            success=True,
            message="식이 제한이 추가되었습니다",
            data={"restriction_id": restriction_id}
        )
    except Exception as e:
        logger.error(f"식이 제한 추가 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"식이 제한 추가 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/dietary-restrictions", response_model=ApiResponse)
async def get_dietary_restrictions(user=Depends(get_current_user)):
    """사용자의 식이 제한 조회"""
    try:
        restrictions = health_dao.get_dietary_restrictions(user["user_id"])
        
        return ApiResponse(
            success=True,
            message="식이 제한 조회 성공",
            data={"restrictions": restrictions}
        )
    except Exception as e:
        logger.error(f"식이 제한 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"식이 제한 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/profile", response_model=ApiResponse)
async def get_health_profile(user=Depends(get_current_user)):
    """사용자의 종합 건강 프로필 조회"""
    try:
        profile = health_dao.get_complete_health_profile(user["user_id"])
        
        return ApiResponse(
            success=True,
            message="건강 프로필 조회 성공",
            data={"profile": profile}
        )
    except Exception as e:
        logger.error(f"건강 프로필 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"건강 프로필 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/analyze", response_model=ApiResponse)
async def analyze_health(query: HealthQueryRequest, user=Depends(get_current_user)):
    """건강 분석 요청"""
    try:
        # 사용자 건강 프로필 조회
        profile = health_dao.get_complete_health_profile(user["user_id"])
        
        # 건강 분석 수행
        assessment = analyze_health_metrics(profile, query.query_text)
        
        return ApiResponse(
            success=True,
            message="건강 분석 완료",
            data={"assessment": assessment.dict()}
        )
    except Exception as e:
        logger.error(f"건강 분석 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"건강 분석 중 오류가 발생했습니다: {str(e)}"
        ) 