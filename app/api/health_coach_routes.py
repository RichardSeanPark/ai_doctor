"""
건강 코치 관련 API 라우트
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
from app.models.health_coach_data import HealthCoachRequest, HealthCoachResponse, WeeklyHealthReport, WeeklyReportRequest
from app.graphs.health_coach_graph import create_health_coach_graph, create_weekly_report_graph

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["health_coach"])

# 건강 DAO 인스턴스
health_dao = HealthDAO()

# 그래프 인스턴스
logger.info("[HEALTH_COACH_ROUTES] 건강 코치 그래프 인스턴스 생성 시작")
try:
    health_coach_graph = create_health_coach_graph()
    logger.info("[HEALTH_COACH_ROUTES] 건강 코치 그래프 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"[HEALTH_COACH_ROUTES] 건강 코치 그래프 인스턴스 생성 오류: {str(e)}")
    logger.error(f"[HEALTH_COACH_ROUTES] 오류 상세: {traceback.format_exc()}")
    raise

logger.info("[HEALTH_COACH_ROUTES] 주간 리포트 그래프 인스턴스 생성 시작")
try:
    weekly_report_graph = create_weekly_report_graph()
    logger.info("[HEALTH_COACH_ROUTES] 주간 리포트 그래프 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"[HEALTH_COACH_ROUTES] 주간 리포트 그래프 인스턴스 생성 오류: {str(e)}")
    logger.error(f"[HEALTH_COACH_ROUTES] 오류 상세: {traceback.format_exc()}")
    raise

# 요청 모델
class WeeklyReportRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    week_start_date: Optional[str] = None
    week_end_date: Optional[str] = None

@router.post("/advice", response_model=ApiResponse)
async def get_health_coach_advice(request: HealthCoachRequest, user=Depends(get_current_user)):
    """건강 코치 조언 요청"""
    logger.info(f"[HEALTH_COACH_ROUTES] 건강 코치 조언 요청 시작 - 사용자 ID: {user['user_id']}, 요청 ID: {request.request_id}")
    logger.debug(f"[HEALTH_COACH_ROUTES] 요청 데이터: {json.dumps(request.dict(), ensure_ascii=False, default=str)[:500]}...")
    
    async def _get_health_coach_advice():
        try:
            # 사용자 프로필 조회
            logger.debug(f"[HEALTH_COACH_ROUTES] 사용자 프로필 조회 시작 - 사용자 ID: {user['user_id']}")
            profile = health_dao.get_complete_health_profile(user["user_id"])
            logger.debug(f"[HEALTH_COACH_ROUTES] 사용자 프로필 조회 완료 - 프로필 키: {list(profile.keys())}")
            
            # UserState 객체 생성
            logger.debug("[HEALTH_COACH_ROUTES] UserState 객체 생성 시작")
            user_state = UserState(
                user_profile=profile,
                user_id=user["user_id"],
                health_coach_request=request.dict()
            )
            logger.debug("[HEALTH_COACH_ROUTES] UserState 객체 생성 완료")
            
            # 건강 코치 그래프 실행
            logger.info("[HEALTH_COACH_ROUTES] 건강 코치 그래프 실행 시작")
            start_time = datetime.now()
            
            try:
                result = await health_coach_graph.ainvoke(user_state)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                logger.info(f"[HEALTH_COACH_ROUTES] 건강 코치 그래프 실행 완료 (소요시간: {elapsed_time:.2f}초)")
            except Exception as e:
                logger.error(f"[HEALTH_COACH_ROUTES] 건강 코치 그래프 실행 오류: {str(e)}")
                logger.error(f"[HEALTH_COACH_ROUTES] 오류 상세: {traceback.format_exc()}")
                raise
            
            # 응답 데이터 준비
            response_data = {}
            logger.debug(f"[HEALTH_COACH_ROUTES] 그래프 결과 타입: {type(result)}")
            
            if isinstance(result, dict):
                logger.debug(f"[HEALTH_COACH_ROUTES] 그래프 결과 키: {list(result.keys())}")
                
                if 'result' in result:
                    # 'result' 키가 있는 경우
                    logger.debug("[HEALTH_COACH_ROUTES] 그래프 결과에 'result' 키가 있음")
                    
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
                        logger.warning(f"[HEALTH_COACH_ROUTES] 'result' 값의 타입({type(result['result'])})을 처리할 수 없습니다")
                        response_data = {
                            "advice": "죄송합니다, 현재 건강 조언을 제공할 수 없습니다.",
                            "recommendations": ["나중에 다시 시도해주세요."],
                            "explanation": "데이터 처리 중 오류가 발생했습니다."
                        }
                else:
                    # UserState 객체가 반환된 경우
                    logger.debug("[HEALTH_COACH_ROUTES] UserState 객체 처리 시도")
                    if hasattr(result, 'health_coach_response') and result.health_coach_response is not None:
                        if hasattr(result.health_coach_response, 'dict') and callable(result.health_coach_response.dict):
                            response_data = result.health_coach_response.dict()
                        else:
                            response_data = result.health_coach_response
                    else:
                        # 기본 응답 생성
                        logger.warning("[HEALTH_COACH_ROUTES] 건강 코치 응답이 없습니다")
                        response_data = {
                            "advice": "죄송합니다, 현재 건강 조언을 제공할 수 없습니다.",
                            "recommendations": ["나중에 다시 시도해주세요."],
                            "explanation": "데이터 처리 중 오류가 발생했습니다."
                        }
            elif hasattr(result, 'health_coach_response'):
                # result가 객체이고 health_coach_response 속성이 있는 경우
                logger.debug("[HEALTH_COACH_ROUTES] 그래프 결과에서 'health_coach_response' 속성 발견")
                if hasattr(result.health_coach_response, 'dict') and callable(result.health_coach_response.dict):
                    response_data = result.health_coach_response.dict()
                else:
                    response_data = result.health_coach_response
            else:
                # 그 외의 경우
                logger.warning("[HEALTH_COACH_ROUTES] 건강 코치 응답이 없습니다")
                response_data = {
                    "advice": "죄송합니다, 현재 건강 조언을 제공할 수 없습니다.",
                    "recommendations": ["나중에 다시 시도해주세요."],
                    "explanation": "데이터 처리 중 오류가 발생했습니다."
                }
            
            logger.debug(f"[HEALTH_COACH_ROUTES] 응답 데이터 키: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
            
            logger.info(f"[HEALTH_COACH_ROUTES] 건강 코치 조언 요청 처리 완료 - 요청 ID: {request.request_id}")
            return response_data
        except Exception as e:
            logger.error(f"[HEALTH_COACH_ROUTES] 건강 코치 조언 요청 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH_ROUTES] 오류 상세: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"건강 코치 조언 요청 중 오류가 발생했습니다: {str(e)}"
            )
    
    return await handle_api_error(
        _get_health_coach_advice,
        "건강 코치 조언 요청",
        "건강 코치 조언이 생성되었습니다"
    )

@router.post("/weekly-report", response_model=ApiResponse)
async def get_weekly_health_report(request: WeeklyReportRequest, user=Depends(get_current_user)):
    """주간 건강 리포트 요청"""
    logger.info(f"[HEALTH_COACH_ROUTES] 주간 건강 리포트 요청 시작 - 사용자 ID: {user['user_id']}, 요청 ID: {request.request_id}")
    logger.debug(f"[HEALTH_COACH_ROUTES] 요청 데이터: {json.dumps(request.dict(), ensure_ascii=False, default=str)[:500]}...")
    
    async def _get_weekly_health_report():
        try:
            # 사용자 프로필 조회
            logger.debug(f"[HEALTH_COACH_ROUTES] 사용자 프로필 조회 시작 - 사용자 ID: {user['user_id']}")
            profile = health_dao.get_complete_health_profile(user["user_id"])
            logger.debug(f"[HEALTH_COACH_ROUTES] 사용자 프로필 조회 완료 - 프로필 키: {list(profile.keys())}")
            
            # UserState 객체 생성
            logger.debug("[HEALTH_COACH_ROUTES] UserState 객체 생성 시작")
            user_state = UserState(
                user_profile=profile,
                user_id=user["user_id"],
                weekly_report_request=request.dict()
            )
            logger.debug("[HEALTH_COACH_ROUTES] UserState 객체 생성 완료")
            
            # 주간 리포트 그래프 실행
            logger.info("[HEALTH_COACH_ROUTES] 주간 리포트 그래프 실행 시작")
            start_time = datetime.now()
            
            try:
                result = await weekly_report_graph.ainvoke(user_state)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                logger.info(f"[HEALTH_COACH_ROUTES] 주간 리포트 그래프 실행 완료 (소요시간: {elapsed_time:.2f}초)")
            except Exception as e:
                logger.error(f"[HEALTH_COACH_ROUTES] 주간 리포트 그래프 실행 오류: {str(e)}")
                logger.error(f"[HEALTH_COACH_ROUTES] 오류 상세: {traceback.format_exc()}")
                raise
            
            # 응답 데이터 준비
            response_data = {}
            logger.debug(f"[HEALTH_COACH_ROUTES] 그래프 결과 타입: {type(result)}")
            
            if isinstance(result, dict):
                logger.debug(f"[HEALTH_COACH_ROUTES] 그래프 결과 키: {list(result.keys())}")
                
                if 'result' in result:
                    # 'result' 키가 있는 경우
                    logger.debug("[HEALTH_COACH_ROUTES] 그래프 결과에 'result' 키가 있음")
                    
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
                        logger.warning(f"[HEALTH_COACH_ROUTES] 'result' 값의 타입({type(result['result'])})을 처리할 수 없습니다")
                        response_data = {
                            "summary": "죄송합니다, 현재 주간 건강 리포트를 제공할 수 없습니다.",
                            "health_metrics_summary": "데이터를 처리할 수 없습니다.",
                            "exercise_summary": "데이터를 처리할 수 없습니다.",
                            "diet_summary": "데이터를 처리할 수 없습니다.",
                            "sleep_summary": "데이터를 처리할 수 없습니다.",
                            "recommendations": ["나중에 다시 시도해주세요."]
                        }
                else:
                    # UserState 객체가 반환된 경우
                    logger.debug("[HEALTH_COACH_ROUTES] UserState 객체 처리 시도")
                    if hasattr(result, 'weekly_health_report') and result.weekly_health_report is not None:
                        if hasattr(result.weekly_health_report, 'dict') and callable(result.weekly_health_report.dict):
                            response_data = result.weekly_health_report.dict()
                        else:
                            response_data = result.weekly_health_report
                    else:
                        # 기본 응답 생성
                        logger.warning("[HEALTH_COACH_ROUTES] 주간 건강 리포트 응답이 없습니다")
                        response_data = {
                            "summary": "죄송합니다, 현재 주간 건강 리포트를 제공할 수 없습니다.",
                            "health_metrics_summary": "데이터를 처리할 수 없습니다.",
                            "exercise_summary": "데이터를 처리할 수 없습니다.",
                            "diet_summary": "데이터를 처리할 수 없습니다.",
                            "sleep_summary": "데이터를 처리할 수 없습니다.",
                            "recommendations": ["나중에 다시 시도해주세요."]
                        }
            elif hasattr(result, 'weekly_health_report'):
                # result가 객체이고 weekly_health_report 속성이 있는 경우
                logger.debug("[HEALTH_COACH_ROUTES] 그래프 결과에서 'weekly_health_report' 속성 발견")
                if hasattr(result.weekly_health_report, 'dict') and callable(result.weekly_health_report.dict):
                    response_data = result.weekly_health_report.dict()
                else:
                    response_data = result.weekly_health_report
            else:
                # 그 외의 경우
                logger.warning("[HEALTH_COACH_ROUTES] 주간 건강 리포트 응답이 없습니다")
                response_data = {
                    "summary": "죄송합니다, 현재 주간 건강 리포트를 제공할 수 없습니다.",
                    "health_metrics_summary": "데이터를 처리할 수 없습니다.",
                    "exercise_summary": "데이터를 처리할 수 없습니다.",
                    "diet_summary": "데이터를 처리할 수 없습니다.",
                    "sleep_summary": "데이터를 처리할 수 없습니다.",
                    "recommendations": ["나중에 다시 시도해주세요."]
                }
            
            logger.debug(f"[HEALTH_COACH_ROUTES] 응답 데이터 키: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
            
            logger.info(f"[HEALTH_COACH_ROUTES] 주간 건강 리포트 요청 처리 완료 - 요청 ID: {request.request_id}")
            return response_data
        except Exception as e:
            logger.error(f"[HEALTH_COACH_ROUTES] 주간 건강 리포트 요청 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH_ROUTES] 오류 상세: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"주간 건강 리포트 요청 중 오류가 발생했습니다: {str(e)}"
            )
    
    return await handle_api_error(
        _get_weekly_health_report,
        "주간 건강 리포트 요청",
        "주간 건강 리포트가 생성되었습니다"
    ) 