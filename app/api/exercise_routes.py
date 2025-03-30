from typing import Dict, Any, List, Optional
import logging
from uuid import uuid4
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path
from pydantic import BaseModel, Field

from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation, ExerciseCompletion
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
    # 추가 세부 정보
    exercise_location: Optional[str] = Field(None, description="운동 장소 (예: 집, 헬스장, 야외, 공원 등)")
    preferred_exercise_type: Optional[str] = Field(None, description="선호 운동 유형 (예: 유산소, 무산소, 근력 운동, 유연성 등)")
    available_equipment: Optional[List[str]] = Field(None, description="사용 가능한 장비 목록 (예: 덤벨, 러닝머신, 요가 매트 등)")
    time_per_session: Optional[int] = Field(None, ge=5, le=180, description="세션당 가능한 운동 시간(분)")
    experience_level: Optional[str] = Field(None, description="운동 경험 수준 (예: 초보자, 중급자, 전문가)")
    intensity_preference: Optional[str] = Field(None, description="선호하는 운동 강도 (예: 저강도, 중강도, 고강도)")
    exercise_constraints: Optional[List[str]] = Field(None, description="운동 제약사항 (예: 관절 통증, 임신, 부상 등)")

# 응답 모델
class ExerciseRecommendationResponse(BaseModel):
    recommendation_id: str
    user_id: str
    goal: str
    fitness_level: Optional[str] = None
    recommended_frequency: Optional[str] = None
    exercise_plans: List[Dict[str, Any]] = []
    special_instructions: Optional[List[str]] = []
    recommendation_summary: str
    timestamp: datetime
    completed: bool = False
    scheduled_time: Optional[datetime] = None
    # 운동 환경 및 선호도 정보
    exercise_location: Optional[str] = None
    preferred_exercise_type: Optional[str] = None
    available_equipment: Optional[List[str]] = []
    time_per_session: Optional[int] = None
    experience_level: Optional[str] = None
    intensity_preference: Optional[str] = None
    exercise_constraints: Optional[List[str]] = []

# 운동 완료 요청 모델
class ExerciseCompletionCreateRequest(BaseModel):
    recommendation_id: str
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="만족도 평가(1-5)")
    feedback: Optional[str] = None

# 운동 완료 응답 모델
class ExerciseCompletionResponse(BaseModel):
    completion_id: str
    recommendation_id: str
    user_id: str
    completed_at: datetime
    satisfaction_rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime

@router.post("/recommendation", response_model=ExerciseRecommendationResponse)
async def get_exercise_recommendation(
    request: ExerciseRecommendationRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    사용자의 운동 목적에 맞는 운동 계획을 추천합니다.
    사용자 ID를 통해 자동으로 사용자 정보(나이, 성별, 체중, 키 등)를 조회합니다.
    추가 세부 정보(운동 장소, 선호 운동 유형, 사용 가능한 장비 등)를 활용하여 보다 맞춤화된 운동 계획을 제공합니다.
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
        
        # 추가 세부 정보 포함
        if request.exercise_location:
            user_profile["exercise_location"] = request.exercise_location
            logger.info(f"[EXERCISE_API] 운동 장소 정보 추가: {request.exercise_location}")
        
        if request.preferred_exercise_type:
            user_profile["preferred_exercise_type"] = request.preferred_exercise_type
            logger.info(f"[EXERCISE_API] 선호 운동 유형 추가: {request.preferred_exercise_type}")
        
        if request.available_equipment:
            user_profile["available_equipment"] = request.available_equipment
            logger.info(f"[EXERCISE_API] 사용 가능한 장비 추가: {', '.join(request.available_equipment)}")
        
        if request.time_per_session:
            user_profile["time_per_session"] = request.time_per_session
            logger.info(f"[EXERCISE_API] 세션당 운동 시간 추가: {request.time_per_session}분")
        
        if request.experience_level:
            user_profile["experience_level"] = request.experience_level
            logger.info(f"[EXERCISE_API] 운동 경험 수준 추가: {request.experience_level}")
        
        if request.intensity_preference:
            user_profile["intensity_preference"] = request.intensity_preference
            logger.info(f"[EXERCISE_API] 선호 운동 강도 추가: {request.intensity_preference}")
        
        if request.exercise_constraints:
            user_profile["exercise_constraints"] = request.exercise_constraints
            logger.info(f"[EXERCISE_API] 운동 제약사항 추가: {', '.join(request.exercise_constraints)}")
        
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
        
        # DB에 저장
        health_dao = HealthDAO()
        save_success = health_dao.save_exercise_recommendation(recommendation)
        
        if not save_success:
            logger.warning(f"[EXERCISE_API] 운동 추천 정보 DB 저장 실패: {recommendation.recommendation_id}")
        else:
            logger.info(f"[EXERCISE_API] 운동 추천 정보 DB 저장 성공: {recommendation.recommendation_id}")
        
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
            timestamp=recommendation.timestamp,
            completed=recommendation.completed,
            scheduled_time=recommendation.scheduled_time,
            exercise_location=recommendation.exercise_location,
            preferred_exercise_type=recommendation.preferred_exercise_type,
            available_equipment=recommendation.available_equipment,
            time_per_session=recommendation.time_per_session,
            experience_level=recommendation.experience_level,
            intensity_preference=recommendation.intensity_preference,
            exercise_constraints=recommendation.exercise_constraints
        )
    
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 추천 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 추천 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/recommendations_history", response_model=List[ExerciseRecommendationResponse])
async def get_user_exercise_recommendations(
    limit: int = Query(10, ge=1, le=50, description="반환할 최대 결과 수"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    사용자의 운동 추천 이력을 조회합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 사용자 운동 추천 이력 조회 요청 - 사용자 ID: {user_id}")
        
        health_dao = HealthDAO()
        recommendations = health_dao.get_user_exercise_recommendations(user_id, limit)
        
        logger.info(f"[EXERCISE_API] 사용자 운동 추천 이력 조회 완료 - {len(recommendations)}개 결과")
        
        # 응답용 객체로 변환
        response = []
        for rec in recommendations:
            response.append(ExerciseRecommendationResponse(
                recommendation_id=rec.recommendation_id,
                user_id=rec.user_id,
                goal=rec.goal,
                fitness_level=rec.fitness_level or "초보자",
                recommended_frequency=rec.recommended_frequency or "주 3회",
                exercise_plans=rec.exercise_plans,
                special_instructions=rec.special_instructions,
                recommendation_summary=rec.recommendation_summary,
                timestamp=rec.timestamp,
                completed=rec.completed,
                scheduled_time=rec.scheduled_time,
                exercise_location=rec.exercise_location,
                preferred_exercise_type=rec.preferred_exercise_type,
                available_equipment=rec.available_equipment,
                time_per_session=rec.time_per_session,
                experience_level=rec.experience_level,
                intensity_preference=rec.intensity_preference,
                exercise_constraints=rec.exercise_constraints
            ))
        
        return response
    
    except Exception as e:
        logger.error(f"[EXERCISE_API] 사용자 운동 추천 이력 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 추천 이력 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/recommendation/{recommendation_id}", response_model=ExerciseRecommendationResponse)
async def get_specific_exercise_recommendation(
    recommendation_id: str = Path(..., description="조회할 운동 추천 ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    특정 ID의 운동 추천 정보를 조회합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 특정 운동 추천 조회 요청 - 사용자 ID: {user_id}, 추천 ID: {recommendation_id}")
        
        health_dao = HealthDAO()
        recommendation = health_dao.get_exercise_recommendation(recommendation_id)
        
        if not recommendation:
            logger.warning(f"[EXERCISE_API] 운동 추천을 찾을 수 없음 - 추천 ID: {recommendation_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 추천을 찾을 수 없습니다")
        
        # 권한 검증 - 다른 사용자의 추천은 접근 불가
        if recommendation.user_id != user_id:
            logger.warning(f"[EXERCISE_API] 권한 없음 - 사용자 ID: {user_id}, 추천 소유자: {recommendation.user_id}")
            raise HTTPException(status_code=403, detail="이 운동 추천에 접근할 권한이 없습니다")
        
        logger.info(f"[EXERCISE_API] 운동 추천 조회 성공 - 추천 ID: {recommendation_id}")
        
        # 응답 반환
        return ExerciseRecommendationResponse(
            recommendation_id=recommendation.recommendation_id,
            user_id=recommendation.user_id,
            goal=recommendation.goal,
            fitness_level=recommendation.fitness_level or "초보자",
            recommended_frequency=recommendation.recommended_frequency or "주 3회",
            exercise_plans=recommendation.exercise_plans,
            special_instructions=recommendation.special_instructions,
            recommendation_summary=recommendation.recommendation_summary,
            timestamp=recommendation.timestamp,
            completed=recommendation.completed,
            scheduled_time=recommendation.scheduled_time,
            exercise_location=recommendation.exercise_location,
            preferred_exercise_type=recommendation.preferred_exercise_type,
            available_equipment=recommendation.available_equipment,
            time_per_session=recommendation.time_per_session,
            experience_level=recommendation.experience_level,
            intensity_preference=recommendation.intensity_preference,
            exercise_constraints=recommendation.exercise_constraints
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 추천 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 추천 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/completion", response_model=ExerciseCompletionResponse)
async def record_exercise_completion(
    request: ExerciseCompletionCreateRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    운동 완료 기록을 생성합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 운동 완료 기록 생성 요청 - 사용자 ID: {user_id}")
        
        health_dao = HealthDAO()
        
        recommendation = health_dao.get_exercise_recommendation(request.recommendation_id)
        
        if not recommendation:
            logger.warning(f"[EXERCISE_API] 운동 추천을 찾을 수 없음 - 추천 ID: {request.recommendation_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 추천을 찾을 수 없습니다")
            
        # 권한 검증
        if recommendation.user_id != user_id:
            logger.warning(f"[EXERCISE_API] 권한 없음 - 사용자 ID: {user_id}, 완료하려는 추천 소유자: {recommendation.user_id}")
            raise HTTPException(status_code=403, detail="이 운동 추천을 완료할 권한이 없습니다")
        
        # 운동 완료 기록 생성
        completion = ExerciseCompletion(
            completion_id=str(uuid4()),
            recommendation_id=request.recommendation_id,
            user_id=user_id,
            completed_at=datetime.now(),
            satisfaction_rating=request.satisfaction_rating,
            feedback=request.feedback
        )
        
        success = health_dao.save_exercise_completion(completion)
        
        if not success:
            logger.error(f"[EXERCISE_API] 운동 완료 기록 생성 실패")
            raise HTTPException(status_code=500, detail="운동 완료 기록 생성에 실패했습니다")
        
        logger.info(f"[EXERCISE_API] 운동 완료 기록 생성 성공 - 완료 ID: {completion.completion_id}")
        
        # 응답 반환
        return ExerciseCompletionResponse(
            completion_id=completion.completion_id,
            recommendation_id=completion.recommendation_id,
            user_id=completion.user_id,
            completed_at=completion.completed_at,
            satisfaction_rating=completion.satisfaction_rating,
            feedback=completion.feedback,
            created_at=completion.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 완료 기록 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 완료 기록 생성 중 오류가 발생했습니다: {str(e)}") 