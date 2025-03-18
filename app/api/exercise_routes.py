from typing import Dict, Any, List, Optional
import logging
from uuid import uuid4
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path
from pydantic import BaseModel, Field

from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation
from app.graphs.exercise_recommendation_graph import create_exercise_recommendation_graph
from app.db.health_dao import HealthDAO
from app.auth.auth_handler import get_current_user

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 설정
router = APIRouter(
    prefix="/api/v1/exercise",
    tags=["exercise"],
)

# 요청 모델 (user_id 필드 제거)
class ExerciseRecommendationRequest(BaseModel):
    goal: str
    # 필수적인 정보가 아닌 경우 선택적으로 제공
    fitness_level: Optional[str] = None
    medical_conditions: Optional[List[str]] = None

# 응답 모델
class ExerciseRecommendationResponse(BaseModel):
    recommendation_id: str
    user_id: str
    goal: str
    fitness_level: str
    recommended_frequency: str
    exercise_plans: List[Dict[str, Any]]
    special_instructions: List[str]
    recommendation_summary: str
    timestamp: datetime

@router.post("/recommendation", response_model=ExerciseRecommendationResponse)
async def get_exercise_recommendation(
    request: ExerciseRecommendationRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    사용자의 운동 목적에 맞는 운동 계획을 추천합니다.
    사용자 ID를 통해 자동으로 사용자 정보(나이, 성별, 체중, 키 등)를 조회합니다.
    """
    try:
        # 토큰에서 사용자 ID 추출
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 운동 추천 요청 수신 - 사용자 ID: {user_id}, 목적: {request.goal}")
        
        # 초기 사용자 프로필 생성 - 기본 정보만 포함
        user_profile = {
            "user_id": user_id
        }
        
        # 요청에서 제공된 선택적 정보 추가
        if request.fitness_level:
            user_profile["fitness_level"] = request.fitness_level
            logger.info(f"[EXERCISE_API] 요청에서 피트니스 레벨 추가: {request.fitness_level}")
        
        if request.medical_conditions:
            user_profile["medical_conditions"] = request.medical_conditions
            logger.info(f"[EXERCISE_API] 요청에서 의학적 조건 추가: {len(request.medical_conditions)}개 항목")
        
        # UserState 객체 생성 - 사용자 데이터는 노드에서 자동으로 조회됨
        state = UserState(
            user_id=user_id,
            user_profile=user_profile,
            query_text=request.goal  # 운동 목적을 query_text에 설정
        )
        
        logger.info(f"[EXERCISE_API] 운동 추천 그래프 생성")
        
        # 운동 추천 그래프 생성
        exercise_graph = create_exercise_recommendation_graph()
        
        logger.info(f"[EXERCISE_API] 운동 추천 그래프 실행 시작")
        
        # 그래프 실행 - 딕셔너리로 상태 전달
        initial_state = {
            "user_id": user_id,
            "user_profile": user_profile,
            "query_text": request.goal
        }
        result = await exercise_graph.ainvoke(initial_state)
        
        logger.info(f"[EXERCISE_API] 운동 추천 그래프 실행 완료")
        logger.info(f"[EXERCISE_API] 결과 타입: {type(result)}")
        
        # 결과에서 운동 추천 데이터 추출
        recommendation = None
        
        # 결과가 딕셔너리인 경우 (LangGraph가 노드의 딕셔너리 반환값을 그대로 전달)
        if isinstance(result, dict) and 'exercise_recommendation' in result:
            recommendation = result['exercise_recommendation']
            logger.info(f"[EXERCISE_API] 딕셔너리에서 exercise_recommendation 추출 성공")
        # 결과가 UserState 객체인 경우
        elif hasattr(result, 'exercise_recommendation') and result.exercise_recommendation:
            recommendation = result.exercise_recommendation
            logger.info(f"[EXERCISE_API] UserState 객체에서 exercise_recommendation 추출 성공")
        else:
            logger.warning(f"[EXERCISE_API] exercise_recommendation을 찾을 수 없음. 결과 타입: {type(result)}")
            # 디버깅을 위한 추가 정보
            if isinstance(result, dict):
                logger.info(f"[EXERCISE_API] 결과 딕셔너리 키: {result.keys()}")
            else:
                logger.info(f"[EXERCISE_API] 결과 속성: {dir(result)}")
        
        if not recommendation:
            logger.error("[EXERCISE_API] 운동 추천 결과가 없습니다")
            raise HTTPException(status_code=500, detail="운동 추천 생성에 실패했습니다")
        
        logger.info(f"[EXERCISE_API] 운동 추천 응답 준비 완료 - 추천 ID: {recommendation.recommendation_id}")
        
        # 응답 반환
        return ExerciseRecommendationResponse(
            recommendation_id=recommendation.recommendation_id,
            user_id=user_id,  # current_user에서 가져온 ID를 사용
            goal=recommendation.goal,
            fitness_level=recommendation.fitness_level or "초보자",
            recommended_frequency=recommendation.recommended_frequency or "주 3회",
            exercise_plans=recommendation.exercise_plans,
            special_instructions=recommendation.special_instructions,
            recommendation_summary=recommendation.recommendation_summary,
            timestamp=recommendation.timestamp
        )
    
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 추천 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 추천 처리 중 오류가 발생했습니다: {str(e)}") 