"""
식단 조언 관련 API 라우트
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.db.health_dao import HealthDAO
from app.auth.auth_handler import get_current_user
from app.utils.api_utils import handle_api_error
from app.models.api_models import ApiResponse
from app.models.notification import UserState
from app.models.diet_plan import DietAdviceRequest, DietAdviceResponse, FoodItem
from app.graphs.diet_advice_graph import create_diet_advice_graph

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["diet"])

# 건강 DAO 인스턴스
health_dao = HealthDAO()

# 그래프 인스턴스
logger.info("[DIET_ROUTES] 식단 조언 그래프 인스턴스 생성 시작")
try:
    diet_advice_graph = create_diet_advice_graph()
    logger.info("[DIET_ROUTES] 식단 조언 그래프 인스턴스 생성 완료")
except Exception as e:
    logger.error(f"[DIET_ROUTES] 식단 조언 그래프 인스턴스 생성 오류: {str(e)}")
    logger.error(f"[DIET_ROUTES] 오류 상세: {traceback.format_exc()}")
    raise

@router.post("/advice", response_model=ApiResponse)
async def get_diet_advice(request: DietAdviceRequest, user=Depends(get_current_user)):
    """식단 조언 요청"""
    logger.info(f"[DIET_ROUTES] 식단 조언 요청 시작 - 사용자 ID: {user['user_id']}, 요청 ID: {request.request_id}")
    logger.debug(f"[DIET_ROUTES] 요청 데이터: {json.dumps(request.dict(), ensure_ascii=False, default=str)[:500]}...")
    
    async def _get_diet_advice():
        try:
            # 사용자 프로필 조회
            logger.debug(f"[DIET_ROUTES] 사용자 프로필 조회 시작 - 사용자 ID: {user['user_id']}")
            profile = health_dao.get_complete_health_profile(user["user_id"])
            logger.debug(f"[DIET_ROUTES] 사용자 프로필 조회 완료 - 프로필 키: {list(profile.keys())}")
            
            # UserState 객체 생성
            logger.debug("[DIET_ROUTES] UserState 객체 생성 시작")
            user_state = UserState(
                user_profile=profile,
                user_id=user["user_id"],
                diet_advice_request=request.dict()
            )
            logger.debug("[DIET_ROUTES] UserState 객체 생성 완료")
            
            # 식단 조언 그래프 실행
            logger.info("[DIET_ROUTES] 식단 조언 그래프 실행 시작")
            start_time = datetime.now()
            
            try:
                result = await diet_advice_graph.ainvoke(user_state)
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                logger.info(f"[DIET_ROUTES] 식단 조언 그래프 실행 완료 (소요시간: {elapsed_time:.2f}초)")
            except Exception as e:
                logger.error(f"[DIET_ROUTES] 식단 조언 그래프 실행 오류: {str(e)}")
                logger.error(f"[DIET_ROUTES] 오류 상세: {traceback.format_exc()}")
                raise
            
            # 응답 데이터 준비
            response_data = {}
            logger.debug(f"[DIET_ROUTES] 그래프 결과 타입: {type(result)}")
            
            if isinstance(result, dict):
                logger.debug(f"[DIET_ROUTES] 그래프 결과 키: {list(result.keys())}")
                
                if 'result' in result:
                    # 'result' 키가 있는 경우
                    logger.debug("[DIET_ROUTES] 그래프 결과에 'result' 키가 있음")
                    
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
                        logger.warning(f"[DIET_ROUTES] 'result' 값의 타입({type(result['result'])})을 처리할 수 없습니다")
                        response_data = {
                            "response_id": str(uuid.uuid4()),
                            "request_id": request.request_id,
                            "timestamp": datetime.now().isoformat(),
                            "diet_assessment": "죄송합니다, 현재 식단 평가를 제공할 수 없습니다.",
                            "improvement_suggestions": ["나중에 다시 시도해주세요."],
                            "alternative_foods": [],
                            "health_tips": "데이터 처리 중 오류가 발생했습니다.",
                            "nutrition_analysis": {
                                "protein": "정보 부족",
                                "carbs": "정보 부족",
                                "fat": "정보 부족",
                                "vitamins": "정보 부족",
                                "minerals": "정보 부족",
                                "balance": "정보 부족"
                            }
                        }
                else:
                    # 'result' 키가 없는 경우, diet_advice_response 키가 있는지 확인
                    logger.debug("[DIET_ROUTES] 그래프 결과에 'result' 키가 없음")
                    
                    if 'diet_advice_response' in result:
                        logger.debug("[DIET_ROUTES] 그래프 결과에 'diet_advice_response' 키가 있음")
                        if hasattr(result['diet_advice_response'], 'dict') and callable(result['diet_advice_response'].dict):
                            response_data = result['diet_advice_response'].dict()
                        else:
                            response_data = result['diet_advice_response']
                    else:
                        # UserState 객체 자체가 반환된 경우
                        logger.debug("[DIET_ROUTES] UserState 객체 처리 시도")
                        if hasattr(result, 'diet_advice_response') and result['diet_advice_response'] is not None:
                            if hasattr(result['diet_advice_response'], 'dict') and callable(result['diet_advice_response'].dict):
                                response_data = result['diet_advice_response'].dict()
                            else:
                                response_data = result['diet_advice_response']
                        else:
                            # 기본 응답 생성
                            logger.warning("[DIET_ROUTES] 식단 조언 응답이 없습니다")
                            response_data = {
                                "response_id": str(uuid.uuid4()),
                                "request_id": request.request_id,
                                "timestamp": datetime.now().isoformat(),
                                "diet_assessment": "죄송합니다, 현재 식단 평가를 제공할 수 없습니다.",
                                "improvement_suggestions": ["나중에 다시 시도해주세요."],
                                "alternative_foods": [],
                                "health_tips": "데이터 처리 중 오류가 발생했습니다.",
                                "nutrition_analysis": {
                                    "protein": "정보 부족",
                                    "carbs": "정보 부족",
                                    "fat": "정보 부족",
                                    "vitamins": "정보 부족",
                                    "minerals": "정보 부족",
                                    "balance": "정보 부족"
                                }
                            }
            elif hasattr(result, 'result'):
                # result가 객체이고 result 속성이 있는 경우
                logger.debug("[DIET_ROUTES] 그래프 결과에서 'result' 속성 발견")
                if hasattr(result.result, 'dict') and callable(result.result.dict):
                    response_data = result.result.dict()
                else:
                    response_data = result.result
            else:
                # 그 외의 경우
                logger.warning("[DIET_ROUTES] 식단 조언 응답이 없습니다")
                response_data = {
                    "response_id": str(uuid.uuid4()),
                    "request_id": request.request_id,
                    "timestamp": datetime.now().isoformat(),
                    "diet_assessment": "죄송합니다, 현재 식단 평가를 제공할 수 없습니다.",
                    "improvement_suggestions": ["나중에 다시 시도해주세요."],
                    "alternative_foods": [],
                    "health_tips": "데이터 처리 중 오류가 발생했습니다.",
                    "nutrition_analysis": {
                        "protein": "정보 부족",
                        "carbs": "정보 부족",
                        "fat": "정보 부족",
                        "vitamins": "정보 부족",
                        "minerals": "정보 부족",
                        "balance": "정보 부족"
                    }
                }
            
            logger.debug(f"[DIET_ROUTES] 응답 데이터 키: {list(response_data.keys()) if isinstance(response_data, dict) else 'not a dict'}")
            
            logger.info(f"[DIET_ROUTES] 식단 조언 요청 처리 완료 - 요청 ID: {request.request_id}")
            return response_data
        except Exception as e:
            logger.error(f"[DIET_ROUTES] 식단 조언 요청 오류: {str(e)}")
            logger.error(f"[DIET_ROUTES] 오류 상세: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"식단 조언 요청 중 오류가 발생했습니다: {str(e)}"
            )
    
    return await handle_api_error(
        _get_diet_advice,
        "식단 조언 요청",
        "식단 조언이 생성되었습니다"
    ) 