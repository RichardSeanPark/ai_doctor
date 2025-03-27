from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import logging
import json
import re
import traceback

from langgraph.graph import END

from app.models.notification import UserState
from app.models.diet_plan import DietSpecialistResponse, FoodItem
from app.agents.agent_config import get_diet_agent, get_diet_specialist_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def route_diet_request(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자의 건강 목표에 따라 적절한 다이어트 조언 노드로 라우팅하는 함수
    라우팅 결정은 Gemini 에이전트에게 맡깁니다.
    
    Args:
        state: 상태 딕셔너리
        
    Returns:
        Dict[str, Any]: 다음 노드 이름을 포함하는 딕셔너리
    """
    user_id = state.get("user_id")
    logger.info(f"[DIET_ROUTER] 식단 조언 라우팅 시작 - 사용자 ID: {user_id}")
    
    try:
        # 사용자 프로필 및 요청 정보 가져오기
        user_profile = state.get("user_profile", {})
        diet_advice_request = state.get("diet_advice_request", {})
        
        # 요청 데이터 파싱
        request_id = diet_advice_request.get('request_id', str(uuid4()))
        current_diet = diet_advice_request.get('current_diet', [])
        health_goals = diet_advice_request.get('health_goals', [])
        dietary_restrictions_req = diet_advice_request.get('dietary_restrictions', [])
        specific_concerns = diet_advice_request.get('specific_concerns')
        
        logger.info(f"[DIET_ROUTER] 건강 목표: {health_goals}")
        
        # 라우팅 에이전트 초기화
        logger.debug("[DIET_ROUTER] 라우팅 에이전트 초기화 시작")
        agent = get_diet_agent()
        logger.debug("[DIET_ROUTER] 라우팅 에이전트 초기화 완료")
        
        # 현재 식단에서 모든 식사 정보 추출
        all_meals_info = []
        
        for meal in current_diet:
            meal_type = meal.get('meal_type', '식사')
            food_items = meal.get('food_items', [])
            
            food_items_str = "\n".join([
                f"- {item['name']}: {item['amount']}" 
                for item in food_items
            ])
            
            all_meals_info.append(f"[{meal_type}]\n{food_items_str}")
        
        meals_str = "\n\n".join(all_meals_info) if all_meals_info else "식단 정보 없음"
        
        # 프롬프트 구성
        logger.debug("[DIET_ROUTER] 프롬프트 구성 시작")
        prompt = f"""
        당신은 사용자의 건강 목표와 식단 정보를 분석하여 적절한 조언 서비스로 라우팅하는 전문가입니다.
        
        사용자 정보:
        - 성별: {user_profile.get('gender', '정보 없음')}
        - 건강 목표: {', '.join(health_goals) if health_goals else '정보 없음'}
        - 식이 제한: {', '.join(dietary_restrictions_req) if dietary_restrictions_req else '없음'}
        - 특정 관심사: {specific_concerns if specific_concerns else '없음'}
        
        현재 식단 정보:
        {meals_str}
        
        다음 두 가지 서비스 중 하나로 라우팅해야 합니다:
        1. 다이어트 전문 조언 서비스: 체중 감량, 다이어트, 체중 관리 등이 주요 목표인 경우
        2. 일반 식단 조언 서비스: 균형 잡힌 영양, 건강한 식단, 영양소 균형 등이 주요 목표인 경우
        
        사용자의 건강 목표와 식단 정보를 분석하여 어떤 서비스가 더 적합한지 결정해주세요.
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "service": "diet_specialist" 또는 "diet_advice",
        }}
        """
        logger.debug("[DIET_ROUTER] 프롬프트 구성 완료")
        
        # 에이전트 호출
        logger.info("[DIET_ROUTER] 라우팅 에이전트 호출 시작")
        start_time = datetime.now()
        
        try:
            response = await agent.ainvoke(prompt)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"[DIET_ROUTER] 라우팅 에이전트 호출 완료 (소요시간: {elapsed_time:.2f}초)")
            
            # 응답 로깅
            if isinstance(response, dict) and 'content' in response:
                logger.debug(f"[DIET_ROUTER] 응답 내용 일부: {response['content'][:200]}...")
            else:
                logger.warning("[DIET_ROUTER] 응답에 content 필드가 없습니다")
        except Exception as e:
            logger.error(f"[DIET_ROUTER] 에이전트 호출 오류: {str(e)}")
            logger.error(f"[DIET_ROUTER] 오류 상세: {traceback.format_exc()}")
            # 오류 발생 시 기본 식단 조언으로 라우팅
            state["route"] = "provide_diet_advice"
            return state
        
        # 결과 처리
        routing_data = {}
        
        # content 필드에서 JSON 추출
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
            
            # JSON 추출
            logger.debug("[DIET_ROUTER] JSON 추출 시작")
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("[DIET_ROUTER] JSON 코드 블록에서 추출 성공")
            else:
                json_str = re.search(r'({.*})', content, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                    logger.debug("[DIET_ROUTER] 정규식으로 JSON 추출 성공")
                else:
                    json_str = content
                    logger.warning("[DIET_ROUTER] JSON 형식을 찾을 수 없어 전체 내용을 사용합니다")
                    
            try:
                logger.debug(f"[DIET_ROUTER] JSON 파싱 시작: {json_str[:100]}...")
                routing_data = json.loads(json_str)
                logger.info(f"[DIET_ROUTER] JSON 파싱 성공: {routing_data}")
            except Exception as e:
                logger.error(f"[DIET_ROUTER] JSON 파싱 오류: {str(e)}")
                logger.error(f"[DIET_ROUTER] 파싱 시도한 문자열: {json_str[:200]}...")
                logger.error(f"[DIET_ROUTER] 오류 상세: {traceback.format_exc()}")
                # 오류 발생 시 기본 식단 조언으로 라우팅
                state["route"] = "provide_diet_advice"
                return state
        else:
            logger.warning("[DIET_ROUTER] 응답에 content 필드가 없습니다")
            # 응답이 없는 경우 기본 식단 조언으로 라우팅
            state["route"] = "provide_diet_advice"
            return state
        
        # 라우팅 결정
        service = routing_data.get('service', 'diet_advice')
        
        if service == 'diet_specialist':
            logger.info(f"[DIET_ROUTER] 다이어트 전문 조언으로 라우팅")
            # 상태 딕셔너리에 라우팅 정보 추가
            state["route"] = "provide_diet_specialist_advice"
            return state
        else:
            logger.info(f"[DIET_ROUTER] 일반 식단 조언으로 라우팅")
            # 상태 딕셔너리에 라우팅 정보 추가
            state["route"] = "provide_diet_advice"
            return state
            
    except Exception as e:
        logger.error(f"[DIET_ROUTER] 라우팅 중 오류 발생: {str(e)}")
        logger.error(f"[DIET_ROUTER] 오류 상세: {traceback.format_exc()}")
        # 오류 발생 시 기본 식단 조언으로 라우팅
        state["route"] = "provide_diet_advice"
        return state

async def provide_diet_specialist_advice(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자에게 다이어트 전문 조언을 제공하는 함수
    
    Args:
        state: 상태 딕셔너리
        
    Returns:
        Dict[str, Any]: 수정된 상태 딕셔너리
    """
    user_id = state.get("user_id")
    logger.info(f"[DIET_SPECIALIST] 다이어트 전문 조언 제공 시작 - 사용자 ID: {user_id}")
    
    try:
        # 사용자 프로필 및 요청 정보 가져오기
        user_profile = state.get("user_profile", {})
        diet_advice_request = state.get("diet_advice_request", {})
        logger.debug(f"[DIET_SPECIALIST] 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False, default=str)[:500]}...")
        
        # 요청 데이터 파싱
        request_id = diet_advice_request.get('request_id', str(uuid4()))
        current_diet = diet_advice_request.get('current_diet', [])
        health_goals = diet_advice_request.get('health_goals', [])
        dietary_restrictions_req = diet_advice_request.get('dietary_restrictions', [])
        specific_concerns = diet_advice_request.get('specific_concerns')
        
        # 현재 식단에서 모든 식사 정보 추출
        all_meals_info = []
        
        for meal in current_diet:
            meal_type = meal.get('meal_type', '식사')
            food_items = meal.get('food_items', [])
            
            food_items_str = "\n".join([
                f"- {item['name']}: {item['amount']}" 
                for item in food_items
            ])
            
            all_meals_info.append(f"[{meal_type}]\n{food_items_str}")
        
        meals_str = "\n\n".join(all_meals_info) if all_meals_info else "식단 정보 없음"
        
        logger.info(f"[DIET_SPECIALIST] 요청 정보 - 요청 ID: {request_id}, 식사 수: {len(current_diet)}")
        logger.info(f"[DIET_SPECIALIST] 건강 목표: {health_goals}")
        logger.info(f"[DIET_SPECIALIST] 식이 제한(요청): {dietary_restrictions_req}")
        logger.info(f"[DIET_SPECIALIST] 특정 관심사: {specific_concerns}")
        
        # 건강 지표 정보 추출
        health_metrics = {}
        if 'health_metrics' in user_profile and user_profile['health_metrics']:
            health_metrics = user_profile['health_metrics']
            logger.info(f"[DIET_SPECIALIST] 건강 지표 정보 추출 성공: 체중={health_metrics.get('weight')}, 키={health_metrics.get('height')}, BMI={health_metrics.get('bmi')}")
        else:
            logger.warning("[DIET_SPECIALIST] 건강 지표 정보가 없습니다.")
        
        # 식이 제한 정보 추출
        dietary_restrictions = user_profile.get('dietary_restrictions', [])
        logger.info(f"[DIET_SPECIALIST] 식이 제한 정보: {dietary_restrictions}")
        
        # 나이 계산 - birth_date가 있는 경우
        age = "정보 없음"
        if 'birth_date' in user_profile and user_profile['birth_date']:
            try:
                birth_date = user_profile['birth_date']
                
                if isinstance(birth_date, str):
                    birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                
                age = str(datetime.now().year - birth_date.year)
                logger.info(f"[DIET_SPECIALIST] 나이 계산 결과: {age}세")
            except Exception as e:
                logger.error(f"[DIET_SPECIALIST] 나이 계산 오류: {str(e)}")
                age = "정보 없음"
        else:
            logger.warning("[DIET_SPECIALIST] birth_date 정보가 없어 나이를 계산할 수 없습니다.")
        
        # 다이어트 전문 에이전트 초기화
        logger.debug("[DIET_SPECIALIST] 다이어트 전문 에이전트 초기화 시작")
        agent = get_diet_specialist_agent()
        logger.debug("[DIET_SPECIALIST] 다이어트 전문 에이전트 초기화 완료")
        
        # 프롬프트 구성
        logger.debug("[DIET_SPECIALIST] 프롬프트 구성 시작")
        prompt = f"""
        당신은 세계적으로 가장 유명한 다이어트와 체중 관리 전문가입니다. 다음 사용자의 식단과 건강 목표를 분석하여 효과적인 다이어트 조언을 제공해주세요:
        직장인일 수 있으므로 직장인에 맞게 조언을 제공해주세요. 제공된 음식에 맞게 조언을 제공해주세요.(예시. 양 조절, 금지 음식, 추가 음식)
        운동 조언은 하지 않습니다.
        사용자 정보:
        - 성별: {user_profile.get('gender', '정보 없음')}
        - 나이: {age}
        - 체중: {health_metrics.get('weight', '정보 없음')} kg
        - 키: {health_metrics.get('height', '정보 없음')} cm
        - BMI: {health_metrics.get('bmi', '정보 없음')}
        - 식이 제한(프로필): {', '.join(dietary_restrictions) if dietary_restrictions else '없음'}
        - 식이 제한(요청): {', '.join(dietary_restrictions_req) if dietary_restrictions_req else '없음'}
        - 건강 목표: {', '.join(health_goals) if health_goals else '정보 없음'}
        - 특정 관심사: {specific_concerns if specific_concerns else '없음'}
        
        현재 식단 정보:
        {meals_str}
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "advice": "식단에 대한 당신의 전문가적인 소견을 상세히 작성해 주세요. 직작인이라는 단어 사용 금지. 제어 문자 사용 금지. 형식을 구조화하여 조언을 제공해주세요."
        }}
        """
        logger.debug("[DIET_SPECIALIST] 프롬프트 구성 완료")
        
        # 에이전트 호출
        logger.info("[DIET_SPECIALIST] 다이어트 전문 에이전트 호출 시작")
        start_time = datetime.now()
        
        try:
            response = await agent.ainvoke(prompt)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"[DIET_SPECIALIST] 다이어트 전문 에이전트 호출 완료 (소요시간: {elapsed_time:.2f}초)")
            
            # 응답 로깅
            if isinstance(response, dict) and 'content' in response:
                logger.debug(f"[DIET_SPECIALIST] 응답 내용 일부: {response['content'][:200]}...")
            else:
                logger.warning("[DIET_SPECIALIST] 응답에 content 필드가 없습니다")
        except Exception as e:
            logger.error(f"[DIET_SPECIALIST] 에이전트 호출 오류: {str(e)}")
            logger.error(f"[DIET_SPECIALIST] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 결과 처리
        advice_data = {}
        
        # content 필드에서 JSON 추출
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
            
            # JSON 추출
            logger.debug("[DIET_SPECIALIST] JSON 추출 시작")
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("[DIET_SPECIALIST] JSON 코드 블록에서 추출 성공")
            else:
                json_str = re.search(r'({.*})', content, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                    logger.debug("[DIET_SPECIALIST] 정규식으로 JSON 추출 성공")
                else:
                    json_str = content
                    logger.warning("[DIET_SPECIALIST] JSON 형식을 찾을 수 없어 전체 내용을 사용합니다")
                    
            try:
                logger.debug(f"[DIET_SPECIALIST] JSON 파싱 시작: {json_str[:100]}...")
                advice_data = json.loads(json_str)
                logger.info(f"[DIET_SPECIALIST] JSON 파싱 성공: {len(advice_data)} 필드")
                logger.debug(f"[DIET_SPECIALIST] 파싱된 데이터 키: {list(advice_data.keys())}")
            except Exception as e:
                logger.error(f"[DIET_SPECIALIST] JSON 파싱 오류: {str(e)}")
                logger.error(f"[DIET_SPECIALIST] 파싱 시도한 문자열: {json_str[:200]}...")
                logger.error(f"[DIET_SPECIALIST] 오류 상세: {traceback.format_exc()}")
                advice_data = {
                    "advice": "죄송합니다, 현재 다이어트 조언을 제공할 수 없습니다. 나중에 다시 시도해주세요."
                }
        else:
            logger.warning("[DIET_SPECIALIST] 응답에 content 필드가 없습니다")
            advice_data = {
                "advice": "죄송합니다, 현재 다이어트 조언을 제공할 수 없습니다. 나중에 다시 시도해주세요."
            }
        
        # 결과 저장
        logger.debug("[DIET_SPECIALIST] 결과 저장 시작")
        try:
            # advice_data를 상태 딕셔너리에 저장
            state["diet_response"] = advice_data
            logger.debug("[DIET_SPECIALIST] advice_data를 상태 딕셔너리에 저장 완료")
            
            logger.info(f"[DIET_SPECIALIST] 다이어트 전문 조언 제공 완료 - 요청 ID: {request_id}")
            
            # 수정된 상태 딕셔너리 반환
            return state
        except Exception as e:
            logger.error(f"[DIET_SPECIALIST] 결과 저장 오류: {str(e)}")
            logger.error(f"[DIET_SPECIALIST] 오류 상세: {traceback.format_exc()}")
            raise
        
    except Exception as e:
        logger.error(f"[DIET_SPECIALIST] 다이어트 전문 조언 제공 중 예외 발생: {str(e)}")
        logger.error(f"[DIET_SPECIALIST] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_response = {
            "advice": "다이어트 조언 처리 중 오류가 발생했습니다. 기술적 문제가 해결된 후 다시 시도해주세요."
        }
        
        # 상태 업데이트
        state["diet_response"] = fallback_response
        
        logger.info("[DIET_SPECIALIST] 다이어트 전문 조언 제공 완료 (오류 발생)")
        
        # 수정된 상태 딕셔너리 반환
        return state

async def provide_diet_advice(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자에게 식단 조언을 제공하는 함수
    
    Args:
        state: 상태 딕셔너리
        
    Returns:
        Dict[str, Any]: 수정된 상태 딕셔너리
    """
    user_id = state.get("user_id")
    logger.info(f"[DIET_ADVICE] 식단 조언 제공 시작 - 사용자 ID: {user_id}")
    
    try:
        # 사용자 프로필 및 요청 정보 가져오기
        user_profile = state.get("user_profile", {})
        diet_advice_request = state.get("diet_advice_request", {})
        logger.debug(f"[DIET_ADVICE] 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False, default=str)[:500]}...")
        
        # 요청 데이터 파싱
        request_id = diet_advice_request.get('request_id', str(uuid4()))
        current_diet = diet_advice_request.get('current_diet', [])
        health_goals = diet_advice_request.get('health_goals', [])
        dietary_restrictions_req = diet_advice_request.get('dietary_restrictions', [])
        specific_concerns = diet_advice_request.get('specific_concerns')
        
        # 현재 식단에서 첫 번째 식사 정보 추출 (기본적으로 첫 번째 식사 항목 사용)
        food_items = []
        meal_type = '식사'
        
        if current_diet and len(current_diet) > 0:
            first_meal = current_diet[0]
            meal_type = first_meal.get('meal_type', '식사')
            food_items = first_meal.get('food_items', [])
        
        logger.info(f"[DIET_ADVICE] 요청 정보 - 요청 ID: {request_id}, 식사 유형: {meal_type}, 음식 항목 수: {len(food_items)}")
        logger.info(f"[DIET_ADVICE] 건강 목표: {health_goals}")
        logger.info(f"[DIET_ADVICE] 식이 제한(요청): {dietary_restrictions_req}")
        logger.info(f"[DIET_ADVICE] 특정 관심사: {specific_concerns}")
        
        # 건강 지표 정보 추출 - health_metrics는 이미 get_yearly_health_metrics 함수를 통해
        # 최신 데이터와 1년치 시계열 데이터가 포함되어 있음
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
                f"- {item['name']}: {item['amount']}" 
                for item in food_items
            ])
            logger.debug(f"[DIET_ADVICE] 음식 항목 정보 정리 완료: {len(food_items)}개 항목")
        except Exception as e:
            logger.error(f"[DIET_ADVICE] 음식 항목 정보 정리 오류: {str(e)}")
            logger.error(f"[DIET_ADVICE] 음식 항목 데이터: {food_items}")
            food_items_str = "음식 항목 정보 없음"
        
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
        - 식이 제한(프로필): {', '.join(dietary_restrictions) if dietary_restrictions else '없음'}
        - 식이 제한(요청): {', '.join(dietary_restrictions_req) if dietary_restrictions_req else '없음'}
        - 건강 목표: {', '.join(health_goals) if health_goals else '정보 없음'}
        - 특정 관심사: {specific_concerns if specific_concerns else '없음'}
        
        식단 정보 ({meal_type}):
        {food_items_str}
        
        다음 내용을 포함한 종합적인 식단 조언을 제공해주세요:
        1. 현재 식단 평가
        2. 개선 제안
        3. 대체 식품 추천
        4. 건강 목표 달성을 위한 팁
        5. 영양소 분석 (단백질, 탄수화물, 지방, 비타민, 미네랄, 전체 균형)
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "advice": "여기에 모든 식단 조언을 하나의 텍스트로 작성해주세요. 제어 문자 사용 금지. 형식을 구조화하여 조언을 제공해주세요."
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
                    "advice": "죄송합니다, 현재 식단 평가를 제공할 수 없습니다. 나중에 다시 시도해주세요."
                }
        else:
            logger.warning("[DIET_ADVICE] 응답에 content 필드가 없습니다")
            advice_data = {
                "advice": "죄송합니다, 현재 식단 평가를 제공할 수 없습니다. 나중에 다시 시도해주세요."
            }
        
        # 결과 저장
        logger.debug("[DIET_ADVICE] 결과 저장 시작")
        try:
            # advice_data를 상태 딕셔너리에 저장
            state["diet_response"] = advice_data
            logger.debug("[DIET_ADVICE] advice_data를 상태 딕셔너리에 저장 완료")
            
            logger.info(f"[DIET_ADVICE] 식단 조언 제공 완료 - 요청 ID: {request_id}")
            
            # 수정된 상태 딕셔너리 반환
            return state
        except Exception as e:
            logger.error(f"[DIET_ADVICE] 결과 저장 오류: {str(e)}")
            logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
            raise
        
    except Exception as e:
        logger.error(f"[DIET_ADVICE] 식단 조언 제공 중 예외 발생: {str(e)}")
        logger.error(f"[DIET_ADVICE] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_response = {
            "advice": "식단 조언 처리 중 오류가 발생했습니다. 기술적 문제가 해결된 후 다시 시도해주세요."
        }
        
        # 상태 업데이트
        state["diet_response"] = fallback_response
        
        logger.info("[DIET_ADVICE] 식단 조언 제공 완료 (오류 발생)")
        
        # 수정된 상태 딕셔너리 반환
        return state 