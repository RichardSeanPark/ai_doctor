"""
건강 데이터 관련 API 라우트
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, validator

from app.db.health_dao import HealthDAO
from app.auth.auth_handler import get_current_user
from app.nodes.health_check_nodes import analyze_health_metrics
from app.utils.api_utils import handle_api_error  # 공통 에러 처리 함수 임포트
from app.models.api_models import ApiResponse  # ApiResponse 모델 임포트
from app.models.notification import UserState  # UserState 모델 임포트

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
        
        # 키와 체중이 있는 경우 BMI 계산 결과를 응답에 포함
        response_data = {"metrics_id": metrics_id}
        weight = metrics_dict.get('weight')
        height = metrics_dict.get('height')
        
        if weight is not None and height is not None and height > 0:
            height_m = height / 100.0
            bmi = round(weight / (height_m * height_m), 1)
            response_data["bmi"] = bmi
            response_data["bmi_calculated"] = True
            
            # BMI 카테고리 추가
            bmi_category = "정보 없음"
            if bmi < 18.5:
                bmi_category = "저체중"
            elif bmi < 23.0:
                bmi_category = "정상"
            elif bmi < 25.0:
                bmi_category = "과체중"
            elif bmi < 30.0:
                bmi_category = "비만(1단계)"
            elif bmi < 35.0:
                bmi_category = "비만(2단계)"
            else:
                bmi_category = "심각한 비만"
                
            response_data["bmi_category"] = bmi_category
        
        return response_data
    
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
async def get_metrics_history(limit: int = 30, user=Depends(get_current_user)):
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
        
        # UserState 객체 생성
        user_state = UserState(
            user_profile=profile,
            query_text=query.query_text,
            health_metrics=profile.get("health_metrics", {}),
            voice_data={"text": query.query_text} if query.query_text else {}
        )
        
        try:
            # gemini_response가 있는 경우 그것을 사용
            if profile.get("gemini_response"):
                logger.info("기존 gemini_response 사용")
                assessment_dict = {
                    "assessment_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "health_status": "분석 완료",
                    "concerns": [],
                    "recommendations": [],
                    "has_concerns": False,
                    "assessment_summary": profile["gemini_response"],
                    "query_text": query.query_text
                }
            else:
                # 새로운 건강 분석 수행
                logger.info("새로운 건강 분석 수행")
                logger.info("analyze_health_metrics 함수 호출 전")
                assessment = await analyze_health_metrics(user_state)
                logger.info("analyze_health_metrics 함수 호출 후")
                
                # 분석 결과를 데이터베이스에 저장
                if hasattr(assessment, "assessment_summary") and assessment.assessment_summary:
                    logger.info("gemini_response 업데이트")
                    # 최신 건강 지표 ID 조회
                    latest_metrics = health_dao.get_latest_health_metrics(user["user_id"])
                    if latest_metrics and "metrics_id" in latest_metrics:
                        # gemini_response 업데이트
                        health_dao.update_gemini_response(
                            latest_metrics["metrics_id"], 
                            assessment.assessment_summary
                        )
                        logger.info(f"metrics_id {latest_metrics['metrics_id']}에 gemini_response 업데이트 완료")
                
                # Pydantic v2에서는 .dict() 대신 .model_dump()를 사용
                # Pydantic v1에서는 .dict()를 사용
                if hasattr(assessment, "model_dump"):
                    assessment_dict = assessment.model_dump()
                elif hasattr(assessment, "dict"):
                    assessment_dict = assessment.dict()
                else:
                    # 객체가 dict 메서드를 가지고 있지 않은 경우 직접 딕셔너리로 변환
                    assessment_dict = {
                        "assessment_id": str(assessment.assessment_id),
                        "timestamp": assessment.timestamp.isoformat(),
                        "health_status": assessment.health_status,
                        "concerns": assessment.concerns,
                        "recommendations": assessment.recommendations,
                        "has_concerns": assessment.has_concerns,
                        "assessment_summary": assessment.assessment_summary,
                        "query_text": assessment.query_text
                    }
            
            return ApiResponse(
                success=True,
                message="건강 분석 완료",
                data={"assessment": assessment_dict}
            )
        except Exception as e:
            logger.error(f"건강 분석 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"건강 분석 중 오류가 발생했습니다: {str(e)}"
            )
    except Exception as e:
        logger.error(f"건강 분석 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"건강 분석 중 오류가 발생했습니다: {str(e)}"
        ) 