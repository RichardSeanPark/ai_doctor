from typing import Dict, Any, List, Union, Optional
from uuid import uuid4
from datetime import datetime, timedelta
import logging
import json
import re
import urllib.parse

from langgraph.graph import END

from app.models.notification import UserState, AndroidNotification
from app.models.exercise_data import ExerciseRecommendation
from app.agents.agent_config import get_gemini_agent, RealGeminiAgent
from app.db.health_dao import HealthDAO

# 로거 설정
logger = logging.getLogger(__name__)

async def recommend_exercise_plan(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자의 목적에 맞는 운동 계획 추천
    
    Args:
        state: 사용자 상태 객체 (사용자 정보 및 운동 목적 포함)
        
    Returns:
        Dict[str, Any]: 운동 추천 정보가 포함된 상태 업데이트
    """
    try:
        user_id = state["user_id"]
        logger.info(f"[EXERCISE_NODE] 운동 계획 추천 시작 - 사용자 ID: {user_id}")
        
        # 사용자 운동 목적 추출
        exercise_goal = ""
        if "query_text" in state and state["query_text"]:
            exercise_goal = state["query_text"]
            logger.info(f"[EXERCISE_NODE] 운동 목적 쿼리: '{exercise_goal}'")
        
        # 사용자 정보 조회
        health_dao = HealthDAO()
        
        # DAO를 통해 사용자 완전한 건강 프로필 조회 (사용자 기본 정보 포함)
        logger.info(f"[EXERCISE_NODE] 사용자 건강 프로필 조회 시작 - 사용자 ID: {user_id}")
        user_health_profile = health_dao.get_complete_health_profile(user_id)
        
        # 최근 1달간의 식단 데이터 조회
        logger.info(f"[EXERCISE_NODE] 사용자 최근 식단 데이터 조회 시작 - 사용자 ID: {user_id}")
        recent_diet_history = health_dao.get_recent_diet_advice_history(user_id, months=1)
        diet_history_data = []
        
        if recent_diet_history:
            logger.info(f"[EXERCISE_NODE] 최근 식단 데이터 {len(recent_diet_history)}개 조회 성공")
            # 필요한 필드만 추출하여 정리
            for diet_entry in recent_diet_history:
                diet_data = {
                    "meal_date": diet_entry.get("meal_date", "").strftime("%Y-%m-%d") if hasattr(diet_entry.get("meal_date", ""), "strftime") else diet_entry.get("meal_date", ""),
                    "meal_type": diet_entry.get("meal_type", ""),
                    "food_items": diet_entry.get("food_items", []),
                    "created_at": diet_entry.get("created_at", "").strftime("%Y-%m-%d %H:%M:%S") if hasattr(diet_entry.get("created_at", ""), "strftime") else diet_entry.get("created_at", "")
                }
                diet_history_data.append(diet_data)
        else:
            logger.info(f"[EXERCISE_NODE] 최근 식단 데이터 없음")
        
        # 최근 운동 추천 데이터 조회
        logger.info(f"[EXERCISE_NODE] 사용자 최근 운동 추천 데이터 조회 시작 - 사용자 ID: {user_id}")
        recent_exercise_recommendations = health_dao.get_user_exercise_recommendations(user_id, limit=1)
        exercise_history_data = []
        
        if recent_exercise_recommendations:
            logger.info(f"[EXERCISE_NODE] 최근 운동 추천 데이터 {len(recent_exercise_recommendations)}개 조회 성공")
            # 필요한 필드만 추출하여 정리
            for recommendation in recent_exercise_recommendations:
                lst_exercise_plans = []
                for plan in recommendation.exercise_plans:
                    exercise_name = plan.get("name", "")
                    lst_exercise_plans.append(exercise_name)
                exercise_data = {
                    "exercise_plans": lst_exercise_plans
                }
                exercise_history_data.append(exercise_data)
        else:
            logger.info(f"[EXERCISE_NODE] 최근 운동 추천 데이터 없음")
        
        # 사용자 정보 병합
        user_profile = state.get("user_profile", {}) if isinstance(state, dict) else {}
        
        # 건강 프로필 데이터 통합
        if user_health_profile:
            logger.info(f"[EXERCISE_NODE] 건강 프로필 정보 통합 - 사용자 ID: {user_id}")
            
            # 건강 지표에서 키, 체중 정보 가져오기
            if 'health_metrics' in user_health_profile:
                health_metrics = user_health_profile['health_metrics']
                
                # 키, 체중 정보 추출
                height = health_metrics.get('height')
                weight = health_metrics.get('weight')
                
                if height:
                    user_profile['height'] = height
                    logger.info(f"[EXERCISE_NODE] 키 정보 추가: {height}cm")
                
                if weight:
                    user_profile['weight'] = weight
                    logger.info(f"[EXERCISE_NODE] 체중 정보 추가: {weight}kg")
                
                # 기타 건강 정보 추가
                user_profile['health_metrics'] = health_metrics
            
            # 건강 지표 시계열 데이터 추출
            health_metrics_history = {}
            if 'health_metrics_history' in user_health_profile:
                health_metrics_history = user_health_profile['health_metrics_history']
                logger.info(f"[EXERCISE_NODE] 건강 지표 시계열 데이터 추출: {', '.join(health_metrics_history.keys())}")
                # 시계열 데이터를 사용자 프로필에 추가
                user_profile['health_metrics_history'] = health_metrics_history
            
            # 기본 정보 통합 (성별)
            if 'gender' in user_health_profile and user_health_profile['gender']:
                user_profile['gender'] = user_health_profile['gender']
                logger.info(f"[EXERCISE_NODE] 성별 정보 추가: {user_health_profile['gender']}")
            
            # 나이 계산 (생년월일이 있는 경우)
            if 'birth_date' in user_health_profile and user_health_profile['birth_date']:
                birth_date = user_health_profile['birth_date']
                today = datetime.now().date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                user_profile['age'] = age
                logger.info(f"[EXERCISE_NODE] 나이 정보 추가: {age}세")
        
        # 최종 사용자 정보 로깅
        age = user_profile.get("age", "알 수 없음")
        gender = user_profile.get("gender", "알 수 없음")
        height = user_profile.get("height", "알 수 없음")
        weight = user_profile.get("weight", "알 수 없음")
        
        # 추가된 세부 정보 추출
        exercise_location = user_profile.get("exercise_location", "정보 없음")
        preferred_exercise_type = user_profile.get("preferred_exercise_type", "정보 없음")
        available_equipment = user_profile.get("available_equipment", [])
        time_per_session = user_profile.get("time_per_session", "정보 없음")
        experience_level = user_profile.get("experience_level", user_profile.get("fitness_level", "정보 없음"))
        intensity_preference = user_profile.get("intensity_preference", "정보 없음")
        exercise_constraints = user_profile.get("exercise_constraints", [])
        
        # 추가 정보 로깅
        logger.info(f"[EXERCISE_NODE] 운동 장소: {exercise_location}")
        logger.info(f"[EXERCISE_NODE] 선호 운동 유형: {preferred_exercise_type}")
        logger.info(f"[EXERCISE_NODE] 사용 가능한 장비: {', '.join(available_equipment) if available_equipment else '없음'}")
        logger.info(f"[EXERCISE_NODE] 세션당 운동 시간: {time_per_session}분")
        logger.info(f"[EXERCISE_NODE] 운동 경험/피트니스 레벨: {experience_level}")
        logger.info(f"[EXERCISE_NODE] 선호 운동 강도: {intensity_preference}")
        logger.info(f"[EXERCISE_NODE] 운동 제약사항: {', '.join(exercise_constraints) if exercise_constraints else '없음'}")
        
        logger.info(f"[EXERCISE_NODE] 최종 사용자 정보 - 나이: {age}, 성별: {gender}, 키: {height}, 체중: {weight}")
        
        # 건강 상태 정보 추출
        health_conditions = user_profile.get("medical_conditions", [])
        conditions_str = "없음" if not health_conditions else ", ".join(health_conditions)
        
        # Gemini 에이전트 초기화
        agent = get_gemini_agent(temperature=0.7)
        
        logger.info(f"[EXERCISE_NODE] 운동 전문가 AI 호출 준비")
        
        # 장비 정보 문자열
        equipment_str = "없음" if not available_equipment else ", ".join(available_equipment)
        
        # 제약사항 문자열
        constraints_str = "없음" if not exercise_constraints else ", ".join(exercise_constraints)
        
        # 프롬프트 구성
        prompt = f"""
        당신은 세계적인 운동 전문가로서 개인의 상황과 환경에 맞는 최적화된 운동 계획을 제공합니다. 다음 사용자에게 상세한 정보를 기반으로 맞춤형 운동 계획을 제안해주세요:
        
        ### 사용자 기본 정보:
        - 나이: {age}
        - 성별: {gender}
        - 키: {height}
        - 체중: {weight}
        - 건강 상태: {conditions_str}
        
        ### 건강 지표 시계열 데이터:
        {json.dumps(health_metrics_history, ensure_ascii=False, indent=2)}
        
        ### 최근 1달간 식단 정보:
        {json.dumps(diet_history_data, ensure_ascii=False, indent=2)}
        
        ### 최근 운동 추천 기록:
        {json.dumps(exercise_history_data, ensure_ascii=False, indent=2)}
        
        ### 운동 환경 및 선호도:
        - 운동 장소: {exercise_location}
        - 선호하는 운동 유형: {preferred_exercise_type}
        - 사용 가능한 장비: {equipment_str}
        - 세션당 가능한 운동 시간: {time_per_session}분
        - 운동 경험 수준: {experience_level}
        - 선호하는 운동 강도: {intensity_preference}
        - 운동 제약사항/주의사항: {constraints_str}
        
        ### 운동 목적:
        {exercise_goal}
        
        다음 형식에 맞게 정확히 JSON 문자열만 응답해주세요. 설명이나 다른 텍스트는 포함하지 마세요:
        
        {{
            "fitness_level": "초보자/중급자/고급자 중 하나",
            "recommended_frequency": "주 3회, 매일 등 권장 빈도",
            "exercise_plans": [
                {{
                    "name": "운동명 (예: 조깅, 스쿼트 등)",
                    "description": "해당 장소와 장비를 고려한 세부 운동 방법",
                    "duration": "권장 시간 (예: 30분)",
                    "benefits": "효과"
                }},
                // 3-5개 정도의 추천 운동
            ],
            "special_instructions": ["주의사항1", "주의사항2"],
            "recommendation_summary": "전체적인 운동 계획 요약"
        }}
        
        특별한 고려사항:
        1. 사용자가 제공한 운동 장소(집, 헬스장, 야외 등)에 적합한 운동만 추천하세요.
        2. 사용 가능한 장비가 제한적이라면 그에 맞는 운동을 제안하세요.
        3. 사용자의 운동 경험 수준에 맞는 난이도로 운동을 구성하세요.
        4. 건강 상태나 제약사항을 고려하여 안전한 운동을 권장하세요.
        5. 선호하는 운동 유형과 강도를 반영한 계획을 제시하세요.
        6. 총 모든 운동을 완료하는데 걸리는 시간이 1시간 이하로 구성하세요.
        7. 최근 조언한 운동 계획을 참고하여 운동 계획을 구성하세요. 가급적 가장 최근에 추천한 운동은 추천하지 마세요.
        """
        
        logger.info(f"[EXERCISE_NODE] Gemini API 호출 시작")
        
        # AI 호출
        response = await agent.ainvoke(prompt)
        
        logger.info(f"[EXERCISE_NODE] Gemini API 응답 수신")
        
        # 결과 파싱
        try:
            # 응답 JSON 추출
            if isinstance(response, dict) and 'content' in response:
                content = response['content']
                exercise_data = extract_json(content)
            else:
                exercise_data = extract_json(str(response))
            
            if not exercise_data:
                logger.warning("[EXERCISE_NODE] 응답에서 JSON 추출 실패")
                exercise_data = {
                    "fitness_level": "초보자",
                    "recommended_frequency": "주 3회",
                    "exercise_plans": [
                        {
                            "name": "걷기",
                            "description": "평지에서 빠른 걸음으로 걷기",
                            "duration": "30분",
                            "benefits": "심폐 건강 향상, 체중 관리"
                        }
                    ],
                    "special_instructions": ["무리하지 말고 천천히 시작하세요."],
                    "recommendation_summary": "가벼운 걷기로 시작하여 점차 운동 강도를 높이는 것을 추천합니다."
                }
        except Exception as e:
            logger.error(f"[EXERCISE_NODE] JSON 파싱 오류: {str(e)}")
            exercise_data = {
                "fitness_level": "초보자",
                "recommended_frequency": "주 3회",
                "exercise_plans": [
                    {
                        "name": "걷기",
                        "description": "평지에서 빠른 걸음으로 걷기",
                        "duration": "30분",
                        "benefits": "심폐 건강 향상, 체중 관리"
                    }
                ],
                "special_instructions": ["무리하지 말고 천천히 시작하세요."],
                "recommendation_summary": "가벼운 걷기로 시작하여 점차 운동 강도를 높이는 것을 추천합니다."
            }
        
        logger.info(f"[EXERCISE_NODE] 운동 계획 구성 시작")
        
        # YouTube 링크 생성
        updated_exercise_plans = []
        for plan in exercise_data.get("exercise_plans", []):
            exercise_name = plan.get("name", "")
            if exercise_name:
                # YouTube 검색 링크 생성
                search_query = f"{exercise_name} 운동 방법"
                youtube_link = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
                plan["youtube_link"] = youtube_link
            updated_exercise_plans.append(plan)
        
        # 추천 데이터 업데이트
        exercise_data["exercise_plans"] = updated_exercise_plans
        
        # ExerciseRecommendation 객체 생성
        recommendation = ExerciseRecommendation(
            user_id=user_id,
            goal=exercise_goal,
            exercise_plans=exercise_data.get("exercise_plans", []),
            fitness_level=exercise_data.get("fitness_level", "초보자"),
            recommended_frequency=exercise_data.get("recommended_frequency", "주 3회"),
            special_instructions=exercise_data.get("special_instructions", []),
            recommendation_summary=exercise_data.get("recommendation_summary", ""),
            # 운동 환경 및 선호도 정보 추가
            exercise_location=exercise_location,
            preferred_exercise_type=preferred_exercise_type,
            available_equipment=available_equipment,
            time_per_session=time_per_session if time_per_session != "정보 없음" else None,
            experience_level=experience_level if experience_level != "정보 없음" else None,
            intensity_preference=intensity_preference if intensity_preference != "정보 없음" else None,
            exercise_constraints=exercise_constraints
        )
        
        # 알림 메시지 생성
        notification_title = "맞춤 운동 계획이 준비되었습니다"
        notification_body = f"{recommendation.recommendation_summary}"
        
        logger.info(f"[EXERCISE_NODE] 운동 계획 추천 완료: {len(recommendation.exercise_plans)}개 운동 추천")
        
        # 딕셔너리 형태로 결과 반환 (LangGraph 상태 업데이트용)
        return {
            "user_id": user_id,
            "user_profile": user_profile,
            "query_text": exercise_goal,
            "exercise_recommendation": recommendation
        }
        
    except Exception as e:
        logger.error(f"[EXERCISE_NODE] 운동 계획 추천 중 오류 발생: {str(e)}")
        raise

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """텍스트에서 JSON 데이터를 추출하는 함수"""
    try:
        # JSON 코드 블록 찾기 (```json ... ``` 형식)
        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        json_blocks = re.findall(json_block_pattern, text)
        
        if json_blocks:
            logger.info("[EXERCISE_NODE] JSON 코드 블록 찾음")
            json_str = json_blocks[0].strip()
            return json.loads(json_str)
        
        # 중괄호 기반 JSON 찾기
        json_pattern = r"(\{[\s\S]*\})"
        json_matches = re.findall(json_pattern, text)
        
        if json_matches:
            # 가장 긴 JSON 문자열을 선택 (완전한 JSON 객체일 가능성이 높음)
            logger.info("[EXERCISE_NODE] 중괄호 기반 JSON 찾음")
            json_str = max(json_matches, key=len).strip()
            return json.loads(json_str)
        
        logger.warning("[EXERCISE_NODE] 텍스트에서 JSON을 찾을 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"[EXERCISE_NODE] JSON 추출 중 오류: {str(e)}")
        return None 