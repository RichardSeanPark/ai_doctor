"""
식단 조언 관련 API 라우트
"""
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.db.health_dao import HealthDAO
from app.auth.auth_handler import get_current_user
from app.utils.api_utils import handle_api_error
from app.models.api_models import ApiResponse
from app.models.notification import UserState
from app.models.diet_plan import DietAdviceRequest, FoodItem
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
            
            # 상태 딕셔너리 생성
            logger.debug("[DIET_ROUTES] 상태 딕셔너리 생성 시작")
            user_state = {
                "user_profile": profile,
                "user_id": user["user_id"],
                "diet_advice_request": request.dict()
            }
            logger.debug("[DIET_ROUTES] 상태 딕셔너리 생성 완료")
            
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
                if "diet_response" in result:
                    logger.debug("[DIET_ROUTES] 그래프 결과에서 diet_response 키 발견")
                    response_data = result["diet_response"]
                else:
                    logger.debug("[DIET_ROUTES] 그래프 결과에 diet_response 키가 없음, 전체 결과 반환")
                    response_data = result
            else:
                # 기본 응답 생성
                logger.warning("[DIET_ROUTES] 식단 조언 응답이 없습니다")
                response_data = {
                    "advice": "죄송합니다, 현재 식단 평가를 제공할 수 없습니다. 나중에 다시 시도해주세요."
                }
            
            # 식단 조언 기록 저장
            try:
                # 현재 날짜 가져오기
                current_date = datetime.now().date().isoformat()
                
                # 첫 번째 식사 정보 가져오기 (현재는 한 번에 하나의 식사만 처리)
                meal = request.current_diet[0]
                
                # 식단 조언 저장
                success = health_dao.save_diet_advice(
                    user_id=user["user_id"],
                    request_id=request.request_id,
                    meal_date=current_date,
                    meal_type=meal["meal_type"],
                    food_items=meal["food_items"],
                    dietary_restrictions=request.dietary_restrictions,
                    health_goals=request.health_goals,
                    specific_concerns=request.specific_concerns,
                    advice_text=response_data.get("advice", "")
                )
                
                if success:
                    logger.info(f"[DIET_ROUTES] 식단 조언 기록 저장 완료 - 사용자 ID: {user['user_id']}")
                else:
                    logger.error(f"[DIET_ROUTES] 식단 조언 기록 저장 실패 - 사용자 ID: {user['user_id']}")
            except Exception as e:
                logger.error(f"[DIET_ROUTES] 식단 조언 기록 저장 중 오류 발생: {str(e)}")
                logger.error(f"[DIET_ROUTES] 오류 상세: {traceback.format_exc()}")
            
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

@router.get("/history", response_model=ApiResponse)
async def get_diet_advice_history(
    start_date: Optional[str] = Query(None, description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료 날짜 (YYYY-MM-DD)"),
    user=Depends(get_current_user)
):
    """사용자의 식단 조언 히스토리 조회"""
    logger.info(f"[DIET_ROUTES] 식단 조언 히스토리 조회 시작 - 사용자 ID: {user['user_id']}")
    
    async def _get_diet_advice_history():
        try:
            # 식단 조언 히스토리 조회
            history = health_dao.get_diet_advice_history(
                user_id=user["user_id"],
                start_date=start_date,
                end_date=end_date
            )
            
            # dietary_restrictions와 specific_concerns 필드 제외
            filtered_history = []
            for record in history:
                filtered_record = {
                    "advice_id": record["advice_id"],
                    "request_id": record["request_id"],
                    "meal_date": record["meal_date"].isoformat() if hasattr(record["meal_date"], "isoformat") else record["meal_date"],
                    "meal_type": record["meal_type"],
                    "food_items": record["food_items"],
                    "health_goals": record["health_goals"],
                    "advice_text": record["advice_text"],
                    "created_at": record["created_at"].isoformat() if hasattr(record["created_at"], "isoformat") else record["created_at"],
                    "updated_at": record["updated_at"].isoformat() if hasattr(record["updated_at"], "isoformat") else record["updated_at"]
                }
                filtered_history.append(filtered_record)
            
            logger.info(f"[DIET_ROUTES] 식단 조언 히스토리 조회 완료 - 사용자 ID: {user['user_id']}, 레코드 수: {len(filtered_history)}")
            return {"history": filtered_history}
            
        except Exception as e:
            logger.error(f"[DIET_ROUTES] 식단 조언 히스토리 조회 오류: {str(e)}")
            logger.error(f"[DIET_ROUTES] 오류 상세: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"식단 조언 히스토리 조회 중 오류가 발생했습니다: {str(e)}"
            )
    
    return await handle_api_error(
        _get_diet_advice_history,
        "식단 조언 히스토리 조회",
        "식단 조언 히스토리가 조회되었습니다"
    ) 