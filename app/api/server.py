"""
안드로이드 클라이언트와 통신하는 API 서버 구현
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Body, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 앱 모듈 임포트
from app.models.health_data import DietEntry, HealthMetrics, HealthAssessment
from app.models.user_profile import UserProfile, UserGoal
from app.main import HealthAIApplication
from app.api import auth_routes, health_routes, voice_routes, diet_advice_routes, health_coach_routes
from app.api import exercise_routes  # exercise_routes 임포트 추가
from app.api import app_routes  # app_routes 임포트 추가
from app.models.api_models import ApiResponse  # ApiResponse를 직접 정의하지 않고 임포트
from app.models.voice_models import VoiceQueryRequest, VoiceResponse, ConsultationRequest
from app.models.health_data import HealthMetrics, HealthAssessment, DietEntry  # 실제 존재하는 클래스로 대체
from app.models.user_data import UserProfile, UserResponse
from app.models.notification import AndroidNotification  # NotificationSettings 대신 AndroidNotification 사용
from app.config.settings import Settings
from app.utils.conversation_manager import ConversationManager
from app.utils.api_utils import handle_api_error  # api_utils에서 공통 함수 임포트

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="Health AI API", description="안드로이드 앱과 통신하는 건강 관리 AI API")

# CORS 설정 (안드로이드 앱에서의 요청 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 출처만 허용하도록 수정 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증, 건강 및 음성 라우터 연결
app.include_router(auth_routes.router, prefix="/api/v1/auth")  # auth_routes 라우터 복원
app.include_router(health_routes.router, prefix="/api/v1/health")
app.include_router(voice_routes.router, prefix="/api/v1") # voice_routes 추가 (prefix는 /api/v1)
app.include_router(diet_advice_routes.router, prefix="/api/v1/diet") # diet_advice_routes 추가
app.include_router(health_coach_routes.router, prefix="/api/v1/health/coach") # health_coach_routes 추가
app.include_router(exercise_routes.router) # exercise_routes 추가 (prefix는 이미 라우터에 포함됨)
app.include_router(app_routes.router, prefix="/api/v1/app") # app_routes 추가 (앱 버전 정보 등)

# Health AI 애플리케이션 인스턴스
health_ai_app = HealthAIApplication()

# 사용자 세션 캐시 (실제 환경에서는 Redis 등의 외부 캐시 사용 권장)
# TODO: 이 부분은 conversation_dao.py의 세션 관리 기능과 중복될 수 있음
# 추후 리팩토링 시 다음과 같은 방향으로 개선 가능:
# 1. ConversationDAO를 확장하여 임시 세션 정보도 저장하도록 수정
# 2. 별도의 SessionManager 클래스를 만들어 세션 관리 통합
# 3. Redis와 같은 외부 캐시 시스템 도입
user_sessions: Dict[str, Dict[str, Any]] = {}

# 대화 관리자 초기화
conversation_manager = ConversationManager()

# API 요청 모델 정의 (응답 모델은 공통 ApiResponse 사용)
class DietAnalysisRequest(BaseModel):
    user_id: str
    meal_type: str = "breakfast"
    meal_items: List[Dict[str, Any]] = []

class FoodImageAnalysisRequest(BaseModel):
    user_id: str
    meal_type: str = "dinner"
    image_data: Optional[str] = None  # Base64 인코딩된 이미지 데이터

class HealthCheckRequest(BaseModel):
    user_id: str
    symptoms: Optional[List[str]] = None
    health_metrics: Optional[Dict[str, Any]] = None

class NotificationRequest(BaseModel):
    user_id: str
    device_token: str
    notification_settings: Dict[str, Any] = {}

# 사용자 세션 관리 함수
def get_user_session(user_id: str, create_if_missing: bool = True) -> Dict[str, Any]:
    """
    사용자 세션 정보를 조회하거나 생성합니다.
    
    참고: 이 함수는 메모리 내 세션을 관리합니다. 지속성이 필요한 경우 
    conversation_dao.py의 대화 세션 관리 기능을 활용하세요.
    """
    if user_id not in user_sessions and create_if_missing:
        user_sessions[user_id] = {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "context": {}
        }
    elif user_id in user_sessions:
        user_sessions[user_id]["last_activity"] = datetime.now().isoformat()
    
    return user_sessions.get(user_id, {})

@app.get("/")
async def root():
    """API 서버 상태 확인"""
    return {"status": "Health AI API server is running"}

@app.post("/api/v1/user/profile", response_model=ApiResponse)
async def create_or_update_user_profile(profile_data: Dict[str, Any] = Body(...)):
    """사용자 프로필 생성 또는 업데이트"""
    try:
        user_id = profile_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="사용자 ID가 누락되었습니다")
        
        # 사용자 프로필 생성/업데이트 로직
        logger.info(f"사용자 프로필 업데이트: {user_id}")
        
        # 세션 업데이트
        session = get_user_session(user_id)
        session["profile"] = profile_data
        
        return ApiResponse(
            success=True,
            message="사용자 프로필이 업데이트되었습니다",
            data={"user_id": user_id}
        )
    except Exception as e:
        logger.error(f"프로필 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/diet/analyze", response_model=ApiResponse)
async def analyze_diet(request: DietAnalysisRequest):
    """식단 분석"""
    async def _analyze_diet():
        logger.info(f"식단 분석: {request.user_id}, 식사 유형: {request.meal_type}")
        
        # Health AI 애플리케이션을 통한 식단 분석
        return await health_ai_app.analyze_diet(
            user_id=request.user_id,
            meal_type=request.meal_type,
            meal_items=request.meal_items
        )
    
    return await handle_api_error(
        _analyze_diet,
        f"사용자 {request.user_id}의 식단 분석",
        "식단 분석이 완료되었습니다"
    )

@app.post("/api/v1/food/analyze-image", response_model=ApiResponse)
async def analyze_food_image(
    user_id: str = Form(...),
    meal_type: str = Form("dinner"),
    image: UploadFile = File(...)
):
    """음식 이미지 분석"""
    try:
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        logger.info(f"음식 이미지 분석: {user_id}, 식사 유형: {meal_type}, 이미지 크기: {len(image_data)} bytes")
        
        # Health AI 애플리케이션을 통한 음식 이미지 분석
        result = await health_ai_app.analyze_food_image(
            user_id=user_id,
            meal_type=meal_type,
            image_data=image_data
        )
        
        return ApiResponse(
            success=True,
            message="음식 이미지 분석이 완료되었습니다",
            data=result
        )
    except Exception as e:
        logger.error(f"음식 이미지 분석 오류: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"음식 이미지 분석 중 오류가 발생했습니다: {str(e)}",
            data={"error": str(e)}
        )

@app.post("/api/v1/health/check", response_model=ApiResponse)
async def health_check(request: HealthCheckRequest):
    """건강 상태 확인"""
    try:
        user_id = request.user_id
        symptoms = request.symptoms or []
        health_metrics = request.health_metrics or {}
        
        logger.info(f"건강 상태 확인: {user_id}, 증상 수: {len(symptoms)}")
        
        # 건강 지표 업데이트 (있는 경우)
        if health_metrics:
            # 여기에 건강 지표 업데이트 로직 추가
            logger.info(f"건강 지표 업데이트: {health_metrics}")
        
        # 증상 분석 (있는 경우)
        result = None
        if symptoms:
            # Health AI 애플리케이션을 통한 증상 분석
            result = await health_ai_app.analyze_symptoms(
                user_id=user_id,
                symptoms=symptoms
            )
        
        return ApiResponse(
            success=True,
            message="건강 상태 확인이 완료되었습니다",
            data={
                "assessment": result,
                "updated_metrics": health_metrics
            }
        )
    except Exception as e:
        logger.error(f"건강 상태 확인 오류: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"건강 상태 확인 중 오류가 발생했습니다: {str(e)}",
            data={"error": str(e)}
        )

@app.post("/api/v1/notifications/register", response_model=ApiResponse)
async def register_device_for_notifications(request: NotificationRequest):
    """FCM 알림을 위한 디바이스 등록"""
    try:
        user_id = request.user_id
        device_token = request.device_token
        notification_settings = request.notification_settings
        
        logger.info(f"알림 디바이스 등록: {user_id}, 토큰: {device_token[:10]}...")
        
        # 사용자 세션 업데이트
        session = get_user_session(user_id)
        session["device_token"] = device_token
        session["notification_settings"] = notification_settings
        
        # 여기에 실제 FCM 등록 로직 추가
        
        return ApiResponse(
            success=True,
            message="알림 디바이스가 등록되었습니다",
            data={"user_id": user_id}
        )
    except Exception as e:
        logger.error(f"알림 디바이스 등록 오류: {str(e)}")
        return ApiResponse(
            success=False,
            message=f"알림 디바이스 등록 중 오류가 발생했습니다: {str(e)}",
            data={"error": str(e)}
        )

# 서버 실행 함수
def run_server(host: str = "0.0.0.0", port: int = 8000):
    """API 서버 실행"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server() 