from typing import Dict, Any, List, Optional
import logging
from uuid import uuid4
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path
from pydantic import BaseModel, Field

from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation, ExerciseSchedule, ExerciseCompletion
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
    completed: bool = False
    scheduled_time: Optional[datetime] = None

# 운동 스케줄 요청 모델
class ExerciseScheduleCreateRequest(BaseModel):
    recommendation_id: str
    day_of_week: int = Field(..., ge=0, le=6, description="0=일요일, 1=월요일, ..., 6=토요일")
    time_of_day: str = Field(..., description="HH:MM 형식의 시간")
    duration_minutes: int = Field(30, ge=5, le=180, description="운동 시간(분)")
    notification_enabled: bool = True
    notification_minutes_before: int = Field(30, ge=5, le=60, description="알림을 보낼 시간(분)")

# 운동 완료 요청 모델
class ExerciseCompletionCreateRequest(BaseModel):
    schedule_id: str
    recommendation_id: str
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="만족도 평가(1-5)")
    feedback: Optional[str] = None

# 운동 스케줄 응답 모델
class ExerciseScheduleResponse(BaseModel):
    schedule_id: str
    recommendation_id: str
    user_id: str
    day_of_week: int
    time_of_day: str
    duration_minutes: int
    notification_enabled: bool
    notification_minutes_before: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

# 운동 완료 응답 모델
class ExerciseCompletionResponse(BaseModel):
    completion_id: str
    schedule_id: str
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
            scheduled_time=recommendation.scheduled_time
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
                scheduled_time=rec.scheduled_time
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
            scheduled_time=recommendation.scheduled_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 추천 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 추천 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/schedule", response_model=ExerciseScheduleResponse)
async def create_exercise_schedule(
    request: ExerciseScheduleCreateRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    운동 스케줄을 생성합니다.
    특정 요일과 시간에 정기적으로 반복되는 운동 일정을 설정합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 운동 스케줄 생성 요청 - 사용자 ID: {user_id}")
        
        health_dao = HealthDAO()
        
        # 운동 추천이 존재하는지 확인 및 권한 검증
        recommendation = health_dao.get_exercise_recommendation(request.recommendation_id)
        
        if not recommendation:
            logger.warning(f"[EXERCISE_API] 운동 추천을 찾을 수 없음 - 추천 ID: {request.recommendation_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 추천을 찾을 수 없습니다")
        
        # 권한 검증 - 다른 사용자의 추천은 접근 불가
        if recommendation.user_id != user_id:
            logger.warning(f"[EXERCISE_API] 권한 없음 - 사용자 ID: {user_id}, 추천 소유자: {recommendation.user_id}")
            raise HTTPException(status_code=403, detail="이 운동 추천에 접근할 권한이 없습니다")
        
        # 스케줄 생성
        try:
            time_obj = datetime.strptime(request.time_of_day, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="시간 형식이 잘못되었습니다. HH:MM 형식을 사용하세요.")
        
        schedule = ExerciseSchedule(
            schedule_id=str(uuid4()),
            recommendation_id=request.recommendation_id,
            user_id=user_id,
            day_of_week=request.day_of_week,
            time_of_day=time_obj,
            duration_minutes=request.duration_minutes,
            notification_enabled=request.notification_enabled,
            notification_minutes_before=request.notification_minutes_before,
            is_active=True
        )
        
        success = health_dao.save_exercise_schedule(schedule)
        
        if not success:
            logger.error(f"[EXERCISE_API] 운동 스케줄 생성 실패")
            raise HTTPException(status_code=500, detail="운동 스케줄 생성에 실패했습니다")
        
        logger.info(f"[EXERCISE_API] 운동 스케줄 생성 성공 - 스케줄 ID: {schedule.schedule_id}")
        
        # 응답 반환
        return ExerciseScheduleResponse(
            schedule_id=schedule.schedule_id,
            recommendation_id=schedule.recommendation_id,
            user_id=schedule.user_id,
            day_of_week=schedule.day_of_week,
            time_of_day=schedule.time_of_day.strftime("%H:%M"),
            duration_minutes=schedule.duration_minutes,
            notification_enabled=schedule.notification_enabled,
            notification_minutes_before=schedule.notification_minutes_before,
            is_active=schedule.is_active,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 스케줄 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 스케줄 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/schedules", response_model=List[ExerciseScheduleResponse])
async def get_user_schedules(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    사용자의 모든 운동 스케줄을 조회합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 사용자 운동 스케줄 조회 요청 - 사용자 ID: {user_id}")
        
        health_dao = HealthDAO()
        schedules = health_dao.get_user_exercise_schedules(user_id)
        
        logger.info(f"[EXERCISE_API] 사용자 운동 스케줄 조회 완료 - {len(schedules)}개 결과")
        
        # 응답용 객체로 변환
        response = []
        for schedule in schedules:
            response.append(ExerciseScheduleResponse(
                schedule_id=schedule.schedule_id,
                recommendation_id=schedule.recommendation_id,
                user_id=schedule.user_id,
                day_of_week=schedule.day_of_week,
                time_of_day=schedule.time_of_day.strftime("%H:%M"),
                duration_minutes=schedule.duration_minutes,
                notification_enabled=schedule.notification_enabled,
                notification_minutes_before=schedule.notification_minutes_before,
                is_active=schedule.is_active,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at
            ))
        
        return response
    
    except Exception as e:
        logger.error(f"[EXERCISE_API] 사용자 운동 스케줄 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 스케줄 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/recommendation/{recommendation_id}/schedules", response_model=List[ExerciseScheduleResponse])
async def get_recommendation_schedules(
    recommendation_id: str = Path(..., description="조회할 운동 추천 ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    특정 운동 추천의 모든 스케줄을 조회합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 운동 추천 스케줄 조회 요청 - 사용자 ID: {user_id}, 추천 ID: {recommendation_id}")
        
        health_dao = HealthDAO()
        
        # 운동 추천이 존재하는지 확인 및 권한 검증
        recommendation = health_dao.get_exercise_recommendation(recommendation_id)
        
        if not recommendation:
            logger.warning(f"[EXERCISE_API] 운동 추천을 찾을 수 없음 - 추천 ID: {recommendation_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 추천을 찾을 수 없습니다")
        
        # 권한 검증 - 다른 사용자의 추천은 접근 불가
        if recommendation.user_id != user_id:
            logger.warning(f"[EXERCISE_API] 권한 없음 - 사용자 ID: {user_id}, 추천 소유자: {recommendation.user_id}")
            raise HTTPException(status_code=403, detail="이 운동 추천에 접근할 권한이 없습니다")
        
        schedules = health_dao.get_exercise_schedules_by_recommendation(recommendation_id)
        
        logger.info(f"[EXERCISE_API] 운동 추천 스케줄 조회 완료 - {len(schedules)}개 결과")
        
        # 응답용 객체로 변환
        response = []
        for schedule in schedules:
            response.append(ExerciseScheduleResponse(
                schedule_id=schedule.schedule_id,
                recommendation_id=schedule.recommendation_id,
                user_id=schedule.user_id,
                day_of_week=schedule.day_of_week,
                time_of_day=schedule.time_of_day.strftime("%H:%M"),
                duration_minutes=schedule.duration_minutes,
                notification_enabled=schedule.notification_enabled,
                notification_minutes_before=schedule.notification_minutes_before,
                is_active=schedule.is_active,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at
            ))
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 추천 스케줄 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 추천 스케줄 조회 중 오류가 발생했습니다: {str(e)}")

@router.patch("/schedule/{schedule_id}", response_model=ExerciseScheduleResponse)
async def update_exercise_schedule(
    schedule_id: str = Path(..., description="업데이트할 스케줄 ID"),
    request: ExerciseScheduleCreateRequest = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    운동 스케줄을 업데이트합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 운동 스케줄 업데이트 요청 - 사용자 ID: {user_id}, 스케줄 ID: {schedule_id}")
        
        health_dao = HealthDAO()
        
        # TODO: 이 메소드는 아직 HealthDAO에 구현되어 있지 않습니다. 필요시 구현해야 합니다.
        # 스케줄이 존재하는지 확인 및 권한 검증
        schedules = health_dao.get_user_exercise_schedules(user_id)
        schedule = next((s for s in schedules if s.schedule_id == schedule_id), None)
        
        if not schedule:
            logger.warning(f"[EXERCISE_API] 운동 스케줄을 찾을 수 없음 - 스케줄 ID: {schedule_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 스케줄을 찾을 수 없습니다")
        
        # 스케줄 업데이트
        try:
            time_obj = datetime.strptime(request.time_of_day, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="시간 형식이 잘못되었습니다. HH:MM 형식을 사용하세요.")
        
        # 기존 스케줄 비활성화
        schedule.is_active = False
        health_dao.save_exercise_schedule(schedule)
        
        # 새 스케줄 생성
        new_schedule = ExerciseSchedule(
            schedule_id=str(uuid4()),
            recommendation_id=request.recommendation_id,
            user_id=user_id,
            day_of_week=request.day_of_week,
            time_of_day=time_obj,
            duration_minutes=request.duration_minutes,
            notification_enabled=request.notification_enabled,
            notification_minutes_before=request.notification_minutes_before,
            is_active=True
        )
        
        success = health_dao.save_exercise_schedule(new_schedule)
        
        if not success:
            logger.error(f"[EXERCISE_API] 운동 스케줄 업데이트 실패")
            raise HTTPException(status_code=500, detail="운동 스케줄 업데이트에 실패했습니다")
        
        logger.info(f"[EXERCISE_API] 운동 스케줄 업데이트 성공 - 신규 스케줄 ID: {new_schedule.schedule_id}")
        
        # 응답 반환
        return ExerciseScheduleResponse(
            schedule_id=new_schedule.schedule_id,
            recommendation_id=new_schedule.recommendation_id,
            user_id=new_schedule.user_id,
            day_of_week=new_schedule.day_of_week,
            time_of_day=new_schedule.time_of_day.strftime("%H:%M"),
            duration_minutes=new_schedule.duration_minutes,
            notification_enabled=new_schedule.notification_enabled,
            notification_minutes_before=new_schedule.notification_minutes_before,
            is_active=new_schedule.is_active,
            created_at=new_schedule.created_at,
            updated_at=new_schedule.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 스케줄 업데이트 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 스케줄 업데이트 중 오류가 발생했습니다: {str(e)}")

@router.delete("/schedule/{schedule_id}", status_code=204)
async def delete_exercise_schedule(
    schedule_id: str = Path(..., description="삭제할 스케줄 ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    운동 스케줄을 삭제합니다 (비활성화).
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 운동 스케줄 삭제 요청 - 사용자 ID: {user_id}, 스케줄 ID: {schedule_id}")
        
        health_dao = HealthDAO()
        
        # 스케줄이 존재하는지 확인 및 권한 검증
        schedules = health_dao.get_user_exercise_schedules(user_id)
        schedule = next((s for s in schedules if s.schedule_id == schedule_id), None)
        
        if not schedule:
            logger.warning(f"[EXERCISE_API] 운동 스케줄을 찾을 수 없음 - 스케줄 ID: {schedule_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 스케줄을 찾을 수 없습니다")
        
        # 스케줄 비활성화
        schedule.is_active = False
        success = health_dao.save_exercise_schedule(schedule)
        
        if not success:
            logger.error(f"[EXERCISE_API] 운동 스케줄 삭제 실패")
            raise HTTPException(status_code=500, detail="운동 스케줄 삭제에 실패했습니다")
        
        logger.info(f"[EXERCISE_API] 운동 스케줄 삭제 성공 - 스케줄 ID: {schedule_id}")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 운동 스케줄 삭제 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"운동 스케줄 삭제 중 오류가 발생했습니다: {str(e)}")

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
        
        # 스케줄과 추천이 존재하는지 확인
        schedules = health_dao.get_user_exercise_schedules(user_id)
        schedule = next((s for s in schedules if s.schedule_id == request.schedule_id), None)
        
        if not schedule:
            logger.warning(f"[EXERCISE_API] 운동 스케줄을 찾을 수 없음 - 스케줄 ID: {request.schedule_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 스케줄을 찾을 수 없습니다")
        
        recommendation = health_dao.get_exercise_recommendation(request.recommendation_id)
        
        if not recommendation:
            logger.warning(f"[EXERCISE_API] 운동 추천을 찾을 수 없음 - 추천 ID: {request.recommendation_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 추천을 찾을 수 없습니다")
        
        # 운동 완료 기록 생성
        completion = ExerciseCompletion(
            completion_id=str(uuid4()),
            schedule_id=request.schedule_id,
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
            schedule_id=completion.schedule_id,
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

@router.get("/schedule/{schedule_id}/completions", response_model=List[ExerciseCompletionResponse])
async def get_schedule_completions(
    schedule_id: str = Path(..., description="조회할 스케줄 ID"),
    limit: int = Query(10, ge=1, le=50, description="반환할 최대 결과 수"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    특정 스케줄의 완료 기록 목록을 조회합니다.
    """
    try:
        user_id = current_user["user_id"]
        logger.info(f"[EXERCISE_API] 스케줄 완료 기록 조회 요청 - 사용자 ID: {user_id}, 스케줄 ID: {schedule_id}")
        
        health_dao = HealthDAO()
        
        # 스케줄이 존재하는지 확인 및 권한 검증
        schedules = health_dao.get_user_exercise_schedules(user_id)
        schedule = next((s for s in schedules if s.schedule_id == schedule_id), None)
        
        if not schedule:
            logger.warning(f"[EXERCISE_API] 운동 스케줄을 찾을 수 없음 - 스케줄 ID: {schedule_id}")
            raise HTTPException(status_code=404, detail="해당 ID의 운동 스케줄을 찾을 수 없습니다")
        
        # 완료 기록 조회
        completions = health_dao.get_exercise_completions_by_schedule(schedule_id, limit)
        
        logger.info(f"[EXERCISE_API] 스케줄 완료 기록 조회 완료 - {len(completions)}개 결과")
        
        # 응답용 객체로 변환
        response = []
        for completion in completions:
            response.append(ExerciseCompletionResponse(
                completion_id=completion.completion_id,
                schedule_id=completion.schedule_id,
                recommendation_id=completion.recommendation_id,
                user_id=completion.user_id,
                completed_at=completion.completed_at,
                satisfaction_rating=completion.satisfaction_rating,
                feedback=completion.feedback,
                created_at=completion.created_at
            ))
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXERCISE_API] 스케줄 완료 기록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"스케줄 완료 기록 조회 중 오류가 발생했습니다: {str(e)}") 