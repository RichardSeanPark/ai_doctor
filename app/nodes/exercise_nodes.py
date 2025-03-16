from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import logging
import json
import re
import traceback

from langgraph.graph import END

from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation, ExerciseRecord
from app.agents.agent_config import get_health_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def recommend_exercise(state: UserState) -> UserState:
    """
    사용자에게 맞춤형 운동을 추천하는 함수
    
    Args:
        state: 사용자 상태 객체
        
    Returns:
        UserState: 수정된 사용자 상태 객체
    """
    logger.info(f"[EXERCISE] 운동 추천 시작 - 사용자 ID: {state.user_id}")
    
    try:
        # 사용자 프로필 및 요청 정보 가져오기
        user_profile = state.user_profile
        logger.debug(f"[EXERCISE] 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False, default=str)[:500]}...")
        
        time_available = state.exercise_request.get('time_available', 30)  # 기본값 30분
        location = state.exercise_request.get('location', '집')  # 기본값 '집'
        intensity = state.exercise_request.get('intensity', '중간')  # 기본값 '중간'
        
        logger.info(f"[EXERCISE] 요청 정보 - 가용 시간: {time_available}분, 장소: {location}, 강도: {intensity}")
        
        # 건강 지표 정보 추출 - health_metrics는 이미 get_latest_health_metrics_by_column 함수를 통해
        # null이 아닌 최신 데이터가 포함되어 있음
        health_metrics = {}
        if 'health_metrics' in user_profile and user_profile['health_metrics']:
            health_metrics = user_profile['health_metrics']
            logger.info(f"[EXERCISE] 건강 지표 정보 추출 성공: 체중={health_metrics.get('weight')}, 키={health_metrics.get('height')}, BMI={health_metrics.get('bmi')}")
            logger.debug(f"[EXERCISE] 전체 건강 지표: {json.dumps(health_metrics, ensure_ascii=False, default=str)}")
        else:
            logger.warning("[EXERCISE] 건강 지표 정보가 없습니다.")
        
        # 운동 이력 정보 추출
        exercise_history = []
        if hasattr(state, 'exercise_history') and state.exercise_history:
            exercise_history = state.exercise_history
            logger.info(f"[EXERCISE] 운동 이력 정보 추출 성공: {len(exercise_history)}개 항목")
            if exercise_history:
                logger.debug(f"[EXERCISE] 최근 운동 이력: {json.dumps(exercise_history[-3:], ensure_ascii=False, default=str)}")
        else:
            logger.warning("[EXERCISE] 운동 이력 정보가 없습니다.")
        
        # 건강 에이전트 초기화
        logger.debug("[EXERCISE] 건강 에이전트 초기화 시작")
        agent = get_health_agent()
        logger.debug("[EXERCISE] 건강 에이전트 초기화 완료")
        
        # 나이 계산 - birth_date가 있는 경우
        age = "정보 없음"
        if 'birth_date' in user_profile and user_profile['birth_date']:
            try:
                birth_date = user_profile['birth_date']
                logger.debug(f"[EXERCISE] birth_date 원본 데이터: {birth_date}, 타입: {type(birth_date)}")
                
                if isinstance(birth_date, str):
                    birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                    logger.debug(f"[EXERCISE] birth_date 문자열에서 변환: {birth_date}")
                
                age = str(datetime.now().year - birth_date.year)
                logger.info(f"[EXERCISE] 나이 계산 결과: {age}세")
            except Exception as e:
                logger.error(f"[EXERCISE] 나이 계산 오류: {str(e)}")
                logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
                age = "정보 없음"
        else:
            logger.warning("[EXERCISE] birth_date 정보가 없어 나이를 계산할 수 없습니다.")
        
        # 운동 이력 문자열 생성
        exercise_history_str = ""
        try:
            if exercise_history:
                exercise_history_str = ', '.join([f"{ex.get('exercise_type')} ({ex.get('duration_minutes')}분)" for ex in exercise_history[-3:]])
                logger.debug(f"[EXERCISE] 운동 이력 문자열 생성 완료: {exercise_history_str}")
            else:
                exercise_history_str = '최근 운동 이력 없음'
        except Exception as e:
            logger.error(f"[EXERCISE] 운동 이력 문자열 생성 오류: {str(e)}")
            logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
            exercise_history_str = '운동 이력 처리 오류'
        
        # 프롬프트 구성
        logger.debug("[EXERCISE] 프롬프트 구성 시작")
        prompt = f"""
        당신은 전문 운동 트레이너입니다. 다음 사용자에게 맞춤형 운동 루틴을 추천해주세요:
        
        사용자 정보:
        - 성별: {user_profile.get('gender', '정보 없음')}
        - 나이: {age}
        - 체중: {health_metrics.get('weight', '정보 없음')} kg
        - 키: {health_metrics.get('height', '정보 없음')} cm
        - BMI: {health_metrics.get('bmi', '정보 없음')}
        
        운동 조건:
        - 가용 시간: {time_available}분
        - 운동 장소: {location}
        - 원하는 강도: {intensity}
        
        최근 운동 이력:
        {exercise_history_str}
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "exercises": [
                {{
                    "name": "운동명",
                    "duration": 분 단위 시간,
                    "calories": 예상 소모 칼로리,
                    "description": "운동 방법 설명",
                    "intensity": "강도 (낮음/중간/높음)"
                }},
                ...
            ],
            "total_calories": 총 예상 소모 칼로리,
            "description": "전체 루틴 설명",
            "tips": ["팁1", "팁2", "팁3"]
        }}
        """
        logger.debug("[EXERCISE] 프롬프트 구성 완료")
        
        # 에이전트 호출
        logger.info("[EXERCISE] 운동 추천 에이전트 호출 시작")
        start_time = datetime.now()
        
        try:
            response = await agent.ainvoke(prompt)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"[EXERCISE] 운동 추천 에이전트 호출 완료 (소요시간: {elapsed_time:.2f}초)")
            
            if hasattr(response, 'content'):
                logger.debug(f"[EXERCISE] 응답 내용 일부: {response.content[:200]}...")
            else:
                logger.warning("[EXERCISE] 응답에 content 필드가 없습니다")
        except Exception as e:
            logger.error(f"[EXERCISE] 에이전트 호출 오류: {str(e)}")
            logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 결과 처리
        recommendation_data = {}
        
        # content 필드에서 JSON 추출
        if hasattr(response, 'content'):
            content = response.content
            
            # JSON 추출
            logger.debug("[EXERCISE] JSON 추출 시작")
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("[EXERCISE] JSON 코드 블록에서 추출 성공")
            else:
                json_str = re.search(r'({.*})', content, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                    logger.debug("[EXERCISE] 정규식으로 JSON 추출 성공")
                else:
                    json_str = content
                    logger.warning("[EXERCISE] JSON 형식을 찾을 수 없어 전체 내용을 사용합니다")
                    
            try:
                logger.debug(f"[EXERCISE] JSON 파싱 시작: {json_str[:100]}...")
                recommendation_data = json.loads(json_str)
                logger.info(f"[EXERCISE] JSON 파싱 성공: {len(recommendation_data)} 필드")
                logger.debug(f"[EXERCISE] 파싱된 데이터 키: {list(recommendation_data.keys())}")
                
                if 'exercises' in recommendation_data:
                    logger.info(f"[EXERCISE] 추천된 운동 수: {len(recommendation_data['exercises'])}")
                    for i, exercise in enumerate(recommendation_data['exercises']):
                        logger.debug(f"[EXERCISE] 추천 운동 {i+1}: {exercise.get('name')}, {exercise.get('duration')}분, {exercise.get('calories')}kcal")
            except Exception as e:
                logger.error(f"[EXERCISE] JSON 파싱 오류: {str(e)}")
                logger.error(f"[EXERCISE] 파싱 시도한 문자열: {json_str[:200]}...")
                logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
                recommendation_data = {
                    "exercises": [],
                    "total_calories": 0,
                    "description": "운동 추천을 생성하는 중 오류가 발생했습니다.",
                    "tips": ["다시 시도해주세요."]
                }
        else:
            logger.warning("[EXERCISE] 응답에 content 필드가 없습니다")
            recommendation_data = {
                "exercises": [],
                "total_calories": 0,
                "description": "운동 추천을 생성하는 중 오류가 발생했습니다.",
                "tips": ["다시 시도해주세요."]
            }
        
        # ExerciseRecommendation 객체 생성
        logger.debug("[EXERCISE] ExerciseRecommendation 객체 생성 시작")
        try:
            recommendation = ExerciseRecommendation(
                time_available=time_available,
                location=location,
                intensity=intensity,
                exercises=recommendation_data.get('exercises', []),
                total_calories=recommendation_data.get('total_calories', 0),
                description=recommendation_data.get('description', ''),
                tips=recommendation_data.get('tips', [])
            )
            logger.debug("[EXERCISE] ExerciseRecommendation 객체 생성 완료")
        except Exception as e:
            logger.error(f"[EXERCISE] ExerciseRecommendation 객체 생성 오류: {str(e)}")
            logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 상태 업데이트
        state.exercise_recommendation = recommendation
        
        logger.info(f"[EXERCISE] 운동 추천 완료: {len(recommendation.exercises)}개 운동 추천됨")
        
        # 수정된 UserState 객체 반환
        return state
        
    except Exception as e:
        logger.error(f"[EXERCISE] 운동 추천 중 예외 발생: {str(e)}")
        logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_recommendation = ExerciseRecommendation(
            time_available=30,
            location="집",
            intensity="중간",
            exercises=[],
            total_calories=0,
            description="운동 추천 처리 중 오류가 발생했습니다.",
            tips=["시스템 오류로 인해 추천을 제공할 수 없습니다. 나중에 다시 시도해주세요."]
        )
        
        # 상태 업데이트
        state.exercise_recommendation = fallback_recommendation
        
        logger.info(f"[EXERCISE] 운동 추천 완료 (오류 발생)")
        
        # 수정된 UserState 객체 반환
        return state

async def record_exercise(state: UserState) -> UserState:
    """
    사용자의 운동 기록을 저장하는 함수
    
    Args:
        state: 사용자 상태 객체
        
    Returns:
        UserState: 수정된 사용자 상태 객체
    """
    logger.info(f"[EXERCISE] 운동 기록 저장 시작 - 사용자 ID: {state.user_id}")
    
    try:
        # 운동 기록 정보 가져오기
        exercise_data = state.exercise_data
        logger.debug(f"[EXERCISE] 운동 기록 데이터: {json.dumps(exercise_data, ensure_ascii=False, default=str)}")
        
        # 필수 필드 검증
        required_fields = ['exercise_type', 'duration_minutes', 'calories_burned', 'intensity']
        for field in required_fields:
            if field not in exercise_data or exercise_data[field] is None:
                logger.warning(f"[EXERCISE] 필수 필드 누락 또는 null: {field}")
        
        # ExerciseRecord 객체 생성
        logger.debug("[EXERCISE] ExerciseRecord 객체 생성 시작")
        try:
            record = ExerciseRecord(
                user_id=state.user_id,
                exercise_type=exercise_data.get('exercise_type', '알 수 없음'),
                duration_minutes=exercise_data.get('duration_minutes', 0),
                calories_burned=exercise_data.get('calories_burned', 0),
                intensity=exercise_data.get('intensity', '중간'),
                notes=exercise_data.get('notes')
            )
            logger.debug("[EXERCISE] ExerciseRecord 객체 생성 완료")
            logger.info(f"[EXERCISE] 운동 기록 생성: {record.exercise_type}, {record.duration_minutes}분, {record.calories_burned}kcal")
        except Exception as e:
            logger.error(f"[EXERCISE] ExerciseRecord 객체 생성 오류: {str(e)}")
            logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 상태 업데이트 (운동 이력에 추가)
        if not hasattr(state, 'exercise_history'):
            logger.debug("[EXERCISE] 운동 이력 초기화")
            state.exercise_history = []
        
        state.exercise_history.append(record)
        logger.info(f"[EXERCISE] 운동 이력에 추가 완료 (현재 이력 수: {len(state.exercise_history)})")
        
        # 상태 업데이트
        state.exercise_record = record
        
        logger.info(f"[EXERCISE] 운동 기록 완료")
        
        # 수정된 UserState 객체 반환
        return state
        
    except Exception as e:
        logger.error(f"[EXERCISE] 운동 기록 중 예외 발생: {str(e)}")
        logger.error(f"[EXERCISE] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_record = ExerciseRecord(
            exercise_id=str(uuid4()),
            user_id=state.user_id,
            exercise_type="알 수 없음",
            duration_minutes=0,
            calories_burned=0,
            intensity="알 수 없음",
            notes="운동 기록 처리 중 오류가 발생했습니다."
        )
        
        # 상태 업데이트
        state.exercise_record = fallback_record
        
        logger.info(f"[EXERCISE] 운동 기록 완료 (오류 발생)")
        
        # 수정된 UserState 객체 반환
        return state 