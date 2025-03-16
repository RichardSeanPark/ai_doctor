from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import logging
import json
import re
import traceback

from langgraph.graph import END

from app.models.notification import UserState
from app.models.diet_plan import DietAdviceResponse, FoodItem
from app.agents.agent_config import get_diet_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def provide_diet_advice(state: UserState) -> UserState:
    """
    사용자에게 식단 조언을 제공하는 함수
    
    Args:
        state: 사용자 상태 객체
        
    Returns:
        UserState: 수정된 사용자 상태 객체
    """
    logger.info(f"[DIET_ADVICE] 식단 조언 제공 시작 - 사용자 ID: {state.user_id}")
    
    try:
        # 사용자 프로필 및 요청 정보 가져오기
        user_profile = state.user_profile
        logger.debug(f"[DIET_ADVICE] 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False, default=str)[:500]}...")
        
        food_items = state.diet_advice_request.get('food_items', [])
        meal_type = state.diet_advice_request.get('meal_type', '식사')
        request_id = state.diet_advice_request.get('request_id', str(uuid4()))
        health_goals = state.diet_advice_request.get('health_goals', [])
        
        logger.info(f"[DIET_ADVICE] 요청 정보 - 요청 ID: {request_id}, 식사 유형: {meal_type}, 음식 항목 수: {len(food_items)}")
        logger.info(f"[DIET_ADVICE] 건강 목표: {health_goals}")
        
        # 건강 지표 정보 추출 - health_metrics는 이미 get_latest_health_metrics_by_column 함수를 통해
        # null이 아닌 최신 데이터가 포함되어 있음
        health_metrics = {}
        if 'health_metrics' in user_profile and user_profile['health_metrics']:
            health_metrics = user_profile['health_metrics']
            logger.info(f"[DIET_ADVICE] 건강 지표 정보 추출 성공: 체중={health_metrics.get('weight')}, 키={health_metrics.get('height')}, BMI={health_metrics.get('bmi')}")
            logger.debug(f"[DIET_ADVICE] 전체 건강 지표: {json.dumps(health_metrics, ensure_ascii=False, default=str)}")
        else:
            logger.warning("[DIET_ADVICE] 건강 지표 정보가 없습니다.")
        
        # 식이 제한 정보 추출
        dietary_restrictions = user_profile.get('dietary_restrictions', [])
        logger.info(f"[DIET_ADVICE] 식이 제한 정보: {dietary_restrictions}")
        
        # 식단 에이전트 초기화
        logger.debug("[DIET_ADVICE] 식단 에이전트 초기화 시작")
        agent = get_diet_agent()
        logger.debug("[DIET_ADVICE] 식단 에이전트 초기화 완료")
        
        # 음식 항목 정보 정리
        try:
            food_items_str = "\n".join([
                f"- {item.name}: {item.amount}, {item.calories}kcal" 
                for item in food_items
            ])
            logger.debug(f"[DIET_ADVICE] 음식 항목 정보 정리 완료: {len(food_items)}개 항목")
        except Exception as e:
            logger.error(f"[DIET_ADVICE] 음식 항목 정보 정리 오류: {str(e)}")
            logger.error(f"[DIET_ADVICE] 음식 항목 데이터: {food_items}")
            food_items_str = "음식 항목 정보 없음"
        
        # 총 칼로리 계산
        try:
            total_calories = sum(item.calories for item in food_items)
            logger.info(f"[DIET_ADVICE] 총 칼로리: {total_calories}kcal")
        except Exception as e:
            logger.error(f"[DIET_ADVICE] 총 칼로리 계산 오류: {str(e)}")
            total_calories = 0
        
        # 나이 계산 - birth_date가 있는 경우
        age = "정보 없음"
        if 'birth_date' in user_profile and user_profile['birth_date']:
            try:
                birth_date = user_profile['birth_date']
                logger.debug(f"[DIET_ADVICE] birth_date 원본 데이터: {birth_date}, 타입: {type(birth_date)}")
                
                if isinstance(birth_date, str):
                    birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                    logger.debug(f"[DIET_ADVICE] birth_date 문자열에서 변환: {birth_date}")
                
                age = str(datetime.now().year - birth_date.year)
                logger.info(f"[DIET_ADVICE] 나이 계산 결과: {age}세")
            except Exception as e:
                logger.error(f"[DIET_ADVICE] 나이 계산 오류: {str(e)}")
                logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
                age = "정보 없음"
        else:
            logger.warning("[DIET_ADVICE] birth_date 정보가 없어 나이를 계산할 수 없습니다.")
        
        # 프롬프트 구성
        logger.debug("[DIET_ADVICE] 프롬프트 구성 시작")
        prompt = f"""
        당신은 전문 영양사입니다. 다음 사용자의 식단에 대한 조언을 제공해주세요:
        
        사용자 정보:
        - 성별: {user_profile.get('gender', '정보 없음')}
        - 나이: {age}
        - 체중: {health_metrics.get('weight', '정보 없음')} kg
        - 키: {health_metrics.get('height', '정보 없음')} cm
        - BMI: {health_metrics.get('bmi', '정보 없음')}
        - 식이 제한: {', '.join(dietary_restrictions) if dietary_restrictions else '없음'}
        - 건강 목표: {', '.join(health_goals) if health_goals else '정보 없음'}
        
        식단 정보 ({meal_type}):
        {food_items_str}
        총 칼로리: {total_calories}kcal
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "diet_assessment": "식단 평가 내용",
            "improvement_suggestions": ["제안1", "제안2", "제안3"],
            "alternative_foods": ["대체 식품1", "대체 식품2"],
            "health_tips": "건강 목표 달성 팁",
            "nutrition_analysis": {{
                "protein": "단백질 평가",
                "carbs": "탄수화물 평가",
                "fat": "지방 평가",
                "vitamins": "비타민 평가",
                "minerals": "미네랄 평가",
                "balance": "전체 균형 평가"
            }}
        }}
        """
        logger.debug("[DIET_ADVICE] 프롬프트 구성 완료")
        
        # 에이전트 호출
        logger.info("[DIET_ADVICE] 식단 조언 에이전트 호출 시작")
        start_time = datetime.now()
        
        try:
            response = await agent.ainvoke(prompt)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"[DIET_ADVICE] 식단 조언 에이전트 호출 완료 (소요시간: {elapsed_time:.2f}초)")
            
            # 응답 로깅
            if isinstance(response, dict) and 'content' in response:
                logger.debug(f"[DIET_ADVICE] 응답 내용 일부: {response['content'][:200]}...")
            else:
                logger.warning("[DIET_ADVICE] 응답에 content 필드가 없습니다")
        except Exception as e:
            logger.error(f"[DIET_ADVICE] 에이전트 호출 오류: {str(e)}")
            logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 결과 처리
        advice_data = {}
        
        # content 필드에서 JSON 추출
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
            
            # JSON 추출
            logger.debug("[DIET_ADVICE] JSON 추출 시작")
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("[DIET_ADVICE] JSON 코드 블록에서 추출 성공")
            else:
                json_str = re.search(r'({.*})', content, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                    logger.debug("[DIET_ADVICE] 정규식으로 JSON 추출 성공")
                else:
                    json_str = content
                    logger.warning("[DIET_ADVICE] JSON 형식을 찾을 수 없어 전체 내용을 사용합니다")
                    
            try:
                logger.debug(f"[DIET_ADVICE] JSON 파싱 시작: {json_str[:100]}...")
                advice_data = json.loads(json_str)
                logger.info(f"[DIET_ADVICE] JSON 파싱 성공: {len(advice_data)} 필드")
                logger.debug(f"[DIET_ADVICE] 파싱된 데이터 키: {list(advice_data.keys())}")
            except Exception as e:
                logger.error(f"[DIET_ADVICE] JSON 파싱 오류: {str(e)}")
                logger.error(f"[DIET_ADVICE] 파싱 시도한 문자열: {json_str[:200]}...")
                logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
                advice_data = {
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
            logger.warning("[DIET_ADVICE] 응답에 content 필드가 없습니다")
            advice_data = {
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
        
        # DietAdviceResponse 객체 생성
        logger.debug("[DIET_ADVICE] DietAdviceResponse 객체 생성 시작")
        try:
            # alternative_foods 형식 변환 (문자열 리스트 -> 딕셔너리 리스트)
            alternative_foods = advice_data.get('alternative_foods', [])
            formatted_alternative_foods = []
            
            for item in alternative_foods:
                if isinstance(item, str):
                    # "A -> B" 형식의 문자열을 딕셔너리로 변환
                    parts = item.split("->")
                    if len(parts) == 2:
                        formatted_alternative_foods.append({
                            "original": parts[0].strip(),
                            "alternative": parts[1].strip()
                        })
                    else:
                        formatted_alternative_foods.append({
                            "suggestion": item.strip()
                        })
                elif isinstance(item, dict):
                    # 이미 딕셔너리 형태인 경우 그대로 사용
                    formatted_alternative_foods.append(item)
            
            diet_advice = DietAdviceResponse(
                request_id=request_id,
                diet_assessment=advice_data.get('diet_assessment', ''),
                improvement_suggestions=advice_data.get('improvement_suggestions', []),
                alternative_foods=formatted_alternative_foods,
                health_tips=advice_data.get('health_tips', ''),
                nutrition_analysis=advice_data.get('nutrition_analysis', {})
            )
            logger.debug("[DIET_ADVICE] DietAdviceResponse 객체 생성 완료")
        except Exception as e:
            logger.error(f"[DIET_ADVICE] DietAdviceResponse 객체 생성 오류: {str(e)}")
            logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 상태 업데이트
        state.diet_advice_response = diet_advice
        
        logger.info(f"[DIET_ADVICE] 식단 조언 제공 완료 - 요청 ID: {request_id}")
        
        # 수정된 UserState 객체 반환
        return state
        
    except Exception as e:
        logger.error(f"[DIET_ADVICE] 식단 조언 제공 중 예외 발생: {str(e)}")
        logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_response = DietAdviceResponse(
            request_id=str(uuid4()),
            diet_assessment="식단 조언 처리 중 오류가 발생했습니다.",
            improvement_suggestions=["시스템 오류로 인해 조언을 제공할 수 없습니다. 나중에 다시 시도해주세요."],
            alternative_foods=[],
            health_tips="기술적 문제가 해결된 후 다시 시도해주세요.",
            nutrition_analysis={
                "protein": "오류 발생",
                "carbs": "오류 발생",
                "fat": "오류 발생",
                "vitamins": "오류 발생",
                "minerals": "오류 발생",
                "balance": "오류 발생"
            }
        )
        
        # 상태 업데이트
        state.diet_advice_response = fallback_response
        
        logger.info(f"[DIET_ADVICE] 식단 조언 제공 완료 - 요청 ID: {fallback_response.request_id}")
        
        # 수정된 UserState 객체 반환
        return state 