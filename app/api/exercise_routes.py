"""
운동 추천 관련 API 라우트
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.db.health_dao import HealthDAO
from app.auth.auth_handler import get_current_user
from app.utils.api_utils import handle_api_error
from app.models.api_models import ApiResponse
from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation, ExerciseRecord
from app.graphs.exercise_graph import create_exercise_recommendation_graph, create_exercise_record_graph

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["exercise"])

# 건강 DAO 인스턴스
health_dao = HealthDAO()

# 그래프 인스턴스
logger.info("[EXERCISE_ROUTES] 운동 추천 그래프 인스턴스 생성 시작")
try:
    exercise_recommendation_graph = create_exercise_recommendation_graph()
    logger.info("[EXERCISE_ROUTES] 운동 추천 그래프 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"[EXERCISE_ROUTES] 운동 추천 그래프 인스턴스 생성 오류: {str(e)}")
    logger.error(f"[EXERCISE_ROUTES] 오류 상세: {traceback.format_exc()}")
    raise

logger.info("[EXERCISE_ROUTES] 운동 기록 그래프 인스턴스 생성 시작")
try:
    exercise_record_graph = create_exercise_record_graph()
    logger.info("[EXERCISE_ROUTES] 운동 기록 그래프 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"[EXERCISE_ROUTES] 운동 기록 그래프 인스턴스 생성 오류: {str(e)}")
    logger.error(f"[EXERCISE_ROUTES] 오류 상세: {traceback.format_exc()}")
    raise

# 요청 모델
class ExerciseRecommendationRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_available: int
    location: str
    intensity: str
    
class ExerciseRecordRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exercise_type: str
    duration_minutes: int
    calories_burned: float
    intensity: str
    notes: Optional[str] = None

@router.post("/recommend", response_model=ApiResponse)
async def recommend_exercise(request: ExerciseRecommendationRequest, user=Depends(get_current_user)):
    """운동 추천 요청"""
    logger.info(f"[EXERCISE_ROUTES] 운동 추천 요청 시작 - 사용자 ID: {user['user_id']}, 요청 ID: {request.request_id}")
    logger.debug(f"[EXERCISE_ROUTES] 요청 데이터: {json.dumps(request.dict(), ensure_ascii=False, default=str)[:500]}...")
    
    async def _recommend_exercise():
        try:
            # 사용자 프로필 조회
            logger.debug(f"[EXERCISE_ROUTES] 사용자 프로필 조회 시작 - 사용자 ID: {user['user_id']}")
            profile = health_dao.get_complete_health_profile(user["user_id"])
            logger.debug(f"[EXERCISE_ROUTES] 사용자 프로필 조회 완료 - 프로필 키: {list(profile.keys())}")
            
            # UserState 객체 생성
            logger.debug("[EXERCISE_ROUTES] UserState 객체 생성 시작")
            user_state = UserState(
                user_profile=profile,
                user_id=user["user_id"],
                exercise_request={
                    "time_available": request.time_available,
                    "location": request.location,
                    "intensity": request.intensity
                }
            )
            logger.debug("[EXERCISE_ROUTES] UserState 객체 생성 완료")
            
            # 운동 추천 그래프 실행
            logger.info("[EXERCISE_ROUTES] 운동 추천 그래프 실행 시작")
            start_time = datetime.now()
            
            try:
                result = await exercise_recommendation_graph.ainvoke(user_state)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                logger.info(f"[EXERCISE_ROUTES] 운동 추천 그래프 실행 완료 (소요시간: {elapsed_time:.2f}초)")
            except Exception as e:
                logger.error(f"[EXERCISE_ROUTES] 운동 추천 그래프 실행 오류: {str(e)}")
                logger.error(f"[EXERCISE_ROUTES] 오류 상세: {traceback.format_exc()}")
                raise
            
            # 응답 데이터 준비
            response_data = {}
            logger.debug(f"[EXERCISE_ROUTES] 그래프 결과 타입: {type(result)}")
            
            if isinstance(result, dict):
                logger.debug(f"[EXERCISE_ROUTES] 그래프 결과 키: {list(result.keys())}")
                
                if 'result' in result:
                    # 'result' 키가 있는 경우
                    logger.debug("[EXERCISE_ROUTES] 그래프 결과에 'result' 키가 있음")
                    
                    if isinstance(result['result'], dict):
                        # result['result']가 딕셔너리인 경우
                        response_data = result['result']
                    elif hasattr(result['result'], '__dict__'):
                        # result['result']가 객체인 경우 (dict 메서드가 있는지 확인)
                        response_data = result['result'].__dict__
                    elif hasattr(result['result'], 'dict') and callable(result['result'].dict):
                        # result['result']가 Pydantic 모델인 경우 (dict 메서드가 있는지 확인)
                        response_data = result['result'].dict()
                    else:
                        # 그 외의 경우
                        logger.warning(f"[EXERCISE_ROUTES] 'result' 값의 타입({type(result['result'])})을 처리할 수 없습니다")
                        response_data = {
                            "response_id": str(uuid.uuid4()),
                            "request_id": request.request_id,
                            "exercises": [],
                            "total_calories": 0,
                            "description": "죄송합니다, 현재 운동 추천을 제공할 수 없습니다.",
                            "tips": ["나중에 다시 시도해주세요."]
                        }
                else:
                    # UserState 객체가 반환된 경우
                    logger.debug("[EXERCISE_ROUTES] UserState 객체 처리 시도")
                    if hasattr(result, 'exercise_recommendation') and result.exercise_recommendation is not None:
                        if hasattr(result.exercise_recommendation, 'dict') and callable(result.exercise_recommendation.dict):
                            response_data = result.exercise_recommendation.dict()
                        else:
                            response_data = result.exercise_recommendation
                    else:
                        # 기본 응답 생성
                        logger.warning("[EXERCISE_ROUTES] 운동 추천 응답이 없습니다")
                        response_data = {
                            "response_id": str(uuid.uuid4()),
                            "request_id": request.request_id,
                            "exercises": [],
                            "total_calories": 0,
                            "description": "죄송합니다, 현재 운동 추천을 제공할 수 없습니다.",
                            "tips": ["나중에 다시 시도해주세요."]
                        }
            elif hasattr(result, 'result'):
                # result가 객체이고 result 속성이 있는 경우
                logger.debug("[EXERCISE_ROUTES] 그래프 결과에서 'result' 속성 발견")
                if hasattr(result.result, 'dict') and callable(result.result.dict):
                    response_data = result.result.dict()
                else:
                    response_data = result.result
            else:
                # 그 외의 경우
                logger.warning("[EXERCISE_ROUTES] 운동 추천 응답이 없습니다")
                response_data = {
                    "response_id": str(uuid.uuid4()),
                    "request_id": request.request_id,
                    "exercises": [],
                    "total_calories": 0,
                    "description": "죄송합니다, 현재 운동 추천을 제공할 수 없습니다.",
                    "tips": ["나중에 다시 시도해주세요."]
                }
            
            logger.debug(f"[EXERCISE_ROUTES] 응답 데이터 키: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
            
            logger.info(f"[EXERCISE_ROUTES] 운동 추천 요청 처리 완료 - 요청 ID: {request.request_id}")
            return response_data
        except Exception as e:
            logger.error(f"[EXERCISE_ROUTES] 운동 추천 요청 오류: {str(e)}")
            logger.error(f"[EXERCISE_ROUTES] 오류 상세: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"운동 추천 요청 중 오류가 발생했습니다: {str(e)}"
            )
    
    return await handle_api_error(
        _recommend_exercise,
        "운동 추천 요청",
        "운동 추천이 생성되었습니다"
    )

@router.post("/record", response_model=ApiResponse)
async def record_exercise(request: ExerciseRecordRequest, user=Depends(get_current_user)):
    """운동 기록 저장"""
    logger.info(f"[EXERCISE_ROUTES] 운동 기록 저장 요청 시작 - 사용자 ID: {user['user_id']}, 요청 ID: {request.request_id}")
    logger.debug(f"[EXERCISE_ROUTES] 요청 데이터: {json.dumps(request.dict(), ensure_ascii=False, default=str)[:500]}...")
    
    async def _record_exercise():
        try:
            # 사용자 프로필 조회
            logger.debug(f"[EXERCISE_ROUTES] 사용자 프로필 조회 시작 - 사용자 ID: {user['user_id']}")
            profile = health_dao.get_complete_health_profile(user["user_id"])
            logger.debug(f"[EXERCISE_ROUTES] 사용자 프로필 조회 완료 - 프로필 키: {list(profile.keys())}")
            
            # UserState 객체 생성
            logger.debug("[EXERCISE_ROUTES] UserState 객체 생성 시작")
            user_state = UserState(
                user_profile=profile,
                user_id=user["user_id"],
                exercise_data={
                    "exercise_type": request.exercise_type,
                    "duration_minutes": request.duration_minutes,
                    "calories_burned": request.calories_burned,
                    "intensity": request.intensity,
                    "notes": request.notes
                }
            )
            logger.debug("[EXERCISE_ROUTES] UserState 객체 생성 완료")
            
            # 운동 기록 그래프 실행
            logger.info("[EXERCISE_ROUTES] 운동 기록 그래프 실행 시작")
            start_time = datetime.now()
            
            try:
                result = await exercise_record_graph.ainvoke(user_state)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                logger.info(f"[EXERCISE_ROUTES] 운동 기록 그래프 실행 완료 (소요시간: {elapsed_time:.2f}초)")
            except Exception as e:
                logger.error(f"[EXERCISE_ROUTES] 운동 기록 그래프 실행 오류: {str(e)}")
                logger.error(f"[EXERCISE_ROUTES] 오류 상세: {traceback.format_exc()}")
                raise
            
            # 응답 데이터 준비
            response_data = {}
            logger.debug(f"[EXERCISE_ROUTES] 그래프 결과 타입: {type(result)}")
            
            if isinstance(result, dict):
                logger.debug(f"[EXERCISE_ROUTES] 그래프 결과 키: {list(result.keys())}")
                
                if 'result' in result:
                    # 'result' 키가 있는 경우
                    logger.debug("[EXERCISE_ROUTES] 그래프 결과에 'result' 키가 있음")
                    
                    if isinstance(result['result'], dict):
                        # result['result']가 딕셔너리인 경우
                        response_data = result['result']
                    elif hasattr(result['result'], '__dict__'):
                        # result['result']가 객체인 경우 (dict 메서드가 있는지 확인)
                        response_data = result['result'].__dict__
                    elif hasattr(result['result'], 'dict') and callable(result['result'].dict):
                        # result['result']가 Pydantic 모델인 경우 (dict 메서드가 있는지 확인)
                        response_data = result['result'].dict()
                    else:
                        # 그 외의 경우
                        logger.warning(f"[EXERCISE_ROUTES] 'result' 값의 타입({type(result['result'])})을 처리할 수 없습니다")
                        response_data = {
                            "exercise_id": str(uuid.uuid4()),
                            "user_id": user["user_id"],
                            "exercise_type": "알 수 없음",
                            "duration_minutes": 0,
                            "calories_burned": 0,
                            "intensity": "알 수 없음",
                            "notes": "운동 기록 처리 중 오류가 발생했습니다."
                        }
                else:
                    # UserState 객체가 반환된 경우
                    logger.debug("[EXERCISE_ROUTES] UserState 객체 처리 시도")
                    if hasattr(result, 'exercise_record') and result.exercise_record is not None:
                        if hasattr(result.exercise_record, 'dict') and callable(result.exercise_record.dict):
                            response_data = result.exercise_record.dict()
                        else:
                            response_data = result.exercise_record
                    else:
                        # 기본 응답 생성
                        logger.warning("[EXERCISE_ROUTES] 운동 기록 응답이 없습니다")
                        response_data = {
                            "exercise_id": str(uuid.uuid4()),
                            "user_id": user["user_id"],
                            "exercise_type": "알 수 없음",
                            "duration_minutes": 0,
                            "calories_burned": 0,
                            "intensity": "알 수 없음",
                            "notes": "운동 기록 처리 중 오류가 발생했습니다."
                        }
            elif hasattr(result, 'result'):
                # result가 객체이고 result 속성이 있는 경우
                logger.debug("[EXERCISE_ROUTES] 그래프 결과에서 'result' 속성 발견")
                if hasattr(result.result, 'dict') and callable(result.result.dict):
                    response_data = result.result.dict()
                else:
                    response_data = result.result
            else:
                # 그 외의 경우
                logger.warning("[EXERCISE_ROUTES] 운동 기록 응답이 없습니다")
                response_data = {
                    "exercise_id": str(uuid.uuid4()),
                    "user_id": user["user_id"],
                    "exercise_type": "알 수 없음",
                    "duration_minutes": 0,
                    "calories_burned": 0,
                    "intensity": "알 수 없음",
                    "notes": "운동 기록 처리 중 오류가 발생했습니다."
                }
            
            logger.debug(f"[EXERCISE_ROUTES] 응답 데이터 키: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
            
            logger.info(f"[EXERCISE_ROUTES] 운동 기록 저장 요청 처리 완료 - 요청 ID: {request.request_id}")
            return response_data
        except Exception as e:
            logger.error(f"[EXERCISE_ROUTES] 운동 기록 저장 요청 오류: {str(e)}")
            logger.error(f"[EXERCISE_ROUTES] 오류 상세: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"운동 기록 저장 중 오류가 발생했습니다: {str(e)}"
            )
    
    return await handle_api_error(
        _record_exercise,
        "운동 기록 저장",
        "운동 기록이 저장되었습니다"
    ) 