from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime, timedelta
import logging
import json
import re
import traceback

from langgraph.graph import END

from app.models.notification import UserState
from app.models.health_coach_data import HealthCoachResponse, WeeklyHealthReport
from app.agents.agent_config import get_health_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def provide_health_advice(state: UserState) -> UserState:
    """
    사용자에게 건강 조언을 제공하는 함수
    
    Args:
        state: 사용자 상태 객체
        
    Returns:
        UserState: 수정된 사용자 상태 객체
    """
    logger.info(f"[HEALTH_COACH] 건강 조언 제공 시작 - 사용자 ID: {state.user_id}")
    
    try:
        # 사용자 프로필 및 요청 정보 가져오기
        user_profile = state.user_profile
        logger.debug(f"[HEALTH_COACH] 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False, default=str)[:500]}...")
        
        query = state.health_coach_request.get('query', '')
        request_id = state.health_coach_request.get('request_id', str(uuid4()))
        
        logger.info(f"[HEALTH_COACH] 요청 정보 - 요청 ID: {request_id}")
        logger.info(f"[HEALTH_COACH] 사용자 질문: {query}")
        
        # 건강 지표 정보 추출 - health_metrics는 이미 get_latest_health_metrics_by_column 함수를 통해
        # null이 아닌 최신 데이터가 포함되어 있음
        health_metrics = {}
        if 'health_metrics' in user_profile and user_profile['health_metrics']:
            health_metrics = user_profile['health_metrics']
            logger.info(f"[HEALTH_COACH] 건강 지표 정보 추출 성공: 체중={health_metrics.get('weight')}, 키={health_metrics.get('height')}, BMI={health_metrics.get('bmi')}")
            logger.debug(f"[HEALTH_COACH] 전체 건강 지표: {json.dumps(health_metrics, ensure_ascii=False, default=str)}")
        else:
            logger.warning("[HEALTH_COACH] 건강 지표 정보가 없습니다.")
        
        # 건강 에이전트 초기화
        logger.debug("[HEALTH_COACH] 건강 에이전트 초기화 시작")
        agent = get_health_agent()
        logger.debug("[HEALTH_COACH] 건강 에이전트 초기화 완료")
        
        # 나이 계산 - birth_date가 있는 경우
        age = "정보 없음"
        if 'birth_date' in user_profile and user_profile['birth_date']:
            try:
                birth_date = user_profile['birth_date']
                logger.debug(f"[HEALTH_COACH] birth_date 원본 데이터: {birth_date}, 타입: {type(birth_date)}")
                
                if isinstance(birth_date, str):
                    birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                    logger.debug(f"[HEALTH_COACH] birth_date 문자열에서 변환: {birth_date}")
                
                age = str(datetime.now().year - birth_date.year)
                logger.info(f"[HEALTH_COACH] 나이 계산 결과: {age}세")
            except Exception as e:
                logger.error(f"[HEALTH_COACH] 나이 계산 오류: {str(e)}")
                logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
                age = "정보 없음"
        else:
            logger.warning("[HEALTH_COACH] birth_date 정보가 없어 나이를 계산할 수 없습니다.")
        
        # 프롬프트 구성
        logger.debug("[HEALTH_COACH] 프롬프트 구성 시작")
        prompt = f"""
        당신은 전문 건강 코치입니다. 다음 사용자의 건강 관련 질문에 답변해주세요:
        
        사용자 정보:
        - 성별: {user_profile.get('gender', '정보 없음')}
        - 나이: {age}
        - 체중: {health_metrics.get('weight', '정보 없음')} kg
        - 키: {health_metrics.get('height', '정보 없음')} cm
        - BMI: {health_metrics.get('bmi', '정보 없음')}
        - 혈압: {health_metrics.get('blood_pressure_systolic', '정보 없음')}/{health_metrics.get('blood_pressure_diastolic', '정보 없음')} mmHg
        - 심박수: {health_metrics.get('heart_rate', '정보 없음')} bpm
        - 혈당: {health_metrics.get('blood_sugar', '정보 없음')} mg/dL
        
        사용자 질문: {query}
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "advice": "핵심 조언",
            "recommendations": ["추천사항1", "추천사항2", "추천사항3"],
            "explanation": "상세 설명",
            "sources": ["출처1", "출처2"],
            "followup_questions": ["후속 질문1", "후속 질문2"]
        }}
        """
        logger.debug("[HEALTH_COACH] 프롬프트 구성 완료")
        
        # 에이전트 호출
        logger.info("[HEALTH_COACH] 건강 코치 에이전트 호출 시작")
        start_time = datetime.now()
        
        try:
            response = await agent.ainvoke(prompt)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"[HEALTH_COACH] 건강 코치 에이전트 호출 완료 (소요시간: {elapsed_time:.2f}초)")
            
            if hasattr(response, 'content'):
                logger.debug(f"[HEALTH_COACH] 응답 내용 일부: {response.content[:200]}...")
            else:
                logger.warning("[HEALTH_COACH] 응답에 content 필드가 없습니다")
        except Exception as e:
            logger.error(f"[HEALTH_COACH] 에이전트 호출 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 결과 처리
        advice_data = {}
        
        # content 필드에서 JSON 추출
        if hasattr(response, 'content'):
            content = response.content
            
            # JSON 추출
            logger.debug("[HEALTH_COACH] JSON 추출 시작")
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("[HEALTH_COACH] JSON 코드 블록에서 추출 성공")
            else:
                json_str = re.search(r'({.*})', content, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                    logger.debug("[HEALTH_COACH] 정규식으로 JSON 추출 성공")
                else:
                    json_str = content
                    logger.warning("[HEALTH_COACH] JSON 형식을 찾을 수 없어 전체 내용을 사용합니다")
                    
            try:
                logger.debug(f"[HEALTH_COACH] JSON 파싱 시작: {json_str[:100]}...")
                advice_data = json.loads(json_str)
                logger.info(f"[HEALTH_COACH] JSON 파싱 성공: {len(advice_data)} 필드")
                logger.debug(f"[HEALTH_COACH] 파싱된 데이터 키: {list(advice_data.keys())}")
            except Exception as e:
                logger.error(f"[HEALTH_COACH] JSON 파싱 오류: {str(e)}")
                logger.error(f"[HEALTH_COACH] 파싱 시도한 문자열: {json_str[:200]}...")
                logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
                advice_data = {
                    "advice": "죄송합니다, 현재 건강 조언을 제공할 수 없습니다.",
                    "recommendations": ["나중에 다시 시도해주세요."],
                    "explanation": "데이터 처리 중 오류가 발생했습니다.",
                    "sources": [],
                    "followup_questions": []
                }
        else:
            logger.warning("[HEALTH_COACH] 응답에 content 필드가 없습니다")
            advice_data = {
                "advice": "죄송합니다, 현재 건강 조언을 제공할 수 없습니다.",
                "recommendations": ["나중에 다시 시도해주세요."],
                "explanation": "데이터 처리 중 오류가 발생했습니다.",
                "sources": [],
                "followup_questions": []
            }
        
        # HealthCoachResponse 객체 생성
        logger.debug("[HEALTH_COACH] HealthCoachResponse 객체 생성 시작")
        try:
            health_advice = HealthCoachResponse(
                request_id=request_id,
                advice=advice_data.get('advice', ''),
                recommendations=advice_data.get('recommendations', []),
                explanation=advice_data.get('explanation', ''),
                sources=advice_data.get('sources', []),
                followup_questions=advice_data.get('followup_questions', [])
            )
            logger.debug("[HEALTH_COACH] HealthCoachResponse 객체 생성 완료")
        except Exception as e:
            logger.error(f"[HEALTH_COACH] HealthCoachResponse 객체 생성 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 상태 업데이트
        state.health_coach_response = health_advice
        
        logger.info(f"[HEALTH_COACH] 건강 조언 제공 완료 - 요청 ID: {request_id}")
        
        # 수정된 UserState 객체 반환
        return state
        
    except Exception as e:
        logger.error(f"[HEALTH_COACH] 건강 조언 제공 중 예외 발생: {str(e)}")
        logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_response = HealthCoachResponse(
            request_id=str(uuid4()),
            advice="건강 조언 처리 중 오류가 발생했습니다.",
            recommendations=["시스템 오류로 인해 조언을 제공할 수 없습니다. 나중에 다시 시도해주세요."],
            explanation="기술적 문제가 해결된 후 다시 시도해주세요.",
            sources=[],
            followup_questions=[]
        )
        
        # 상태 업데이트
        state.health_coach_response = fallback_response
        
        logger.info(f"[HEALTH_COACH] 건강 조언 제공 완료 (오류 발생) - 요청 ID: {fallback_response.request_id}")
        
        # 수정된 UserState 객체 반환
        return state

async def generate_weekly_report(state: UserState) -> UserState:
    """
    사용자의 주간 건강 리포트를 생성하는 함수
    
    Args:
        state: 사용자 상태 객체
        
    Returns:
        UserState: 수정된 사용자 상태 객체
    """
    logger.info(f"[HEALTH_COACH] 주간 건강 리포트 생성 시작 - 사용자 ID: {state.user_id}")
    
    try:
        # 사용자 프로필 가져오기
        user_profile = state.user_profile
        logger.debug(f"[HEALTH_COACH] 사용자 프로필: {json.dumps(user_profile, ensure_ascii=False, default=str)[:500]}...")
        
        # 날짜 범위 설정 (지난 7일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        logger.info(f"[HEALTH_COACH] 리포트 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # 건강 지표 이력 가져오기
        metrics_history = user_profile.get('metrics_history', [])
        logger.info(f"[HEALTH_COACH] 전체 건강 지표 이력 수: {len(metrics_history)}")
        
        # 지난 7일간의 지표만 필터링
        try:
            recent_metrics = [
                m for m in metrics_history 
                if 'timestamp' in m and datetime.fromisoformat(m['timestamp']) >= start_date
            ]
            logger.info(f"[HEALTH_COACH] 최근 7일간 건강 지표 수: {len(recent_metrics)}")
            logger.debug(f"[HEALTH_COACH] 최근 지표 타임스탬프: {[m.get('timestamp') for m in recent_metrics[:5]]}")
        except Exception as e:
            logger.error(f"[HEALTH_COACH] 최근 지표 필터링 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
            recent_metrics = []
        
        # 나이 계산 - birth_date가 있는 경우
        age = "정보 없음"
        if 'birth_date' in user_profile and user_profile['birth_date']:
            try:
                birth_date = user_profile['birth_date']
                logger.debug(f"[HEALTH_COACH] birth_date 원본 데이터: {birth_date}, 타입: {type(birth_date)}")
                
                if isinstance(birth_date, str):
                    birth_date = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
                    logger.debug(f"[HEALTH_COACH] birth_date 문자열에서 변환: {birth_date}")
                
                age = str(datetime.now().year - birth_date.year)
                logger.info(f"[HEALTH_COACH] 나이 계산 결과: {age}세")
            except Exception as e:
                logger.error(f"[HEALTH_COACH] 나이 계산 오류: {str(e)}")
                logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
                age = "정보 없음"
        else:
            logger.warning("[HEALTH_COACH] birth_date 정보가 없어 나이를 계산할 수 없습니다.")
        
        # 건강 에이전트 초기화
        logger.debug("[HEALTH_COACH] 건강 에이전트 초기화 시작")
        agent = get_health_agent()
        logger.debug("[HEALTH_COACH] 건강 에이전트 초기화 완료")
        
        # 프롬프트 구성
        logger.debug("[HEALTH_COACH] 프롬프트 구성 시작")
        
        # 최근 지표 JSON 문자열 생성
        try:
            recent_metrics_json = json.dumps(recent_metrics, ensure_ascii=False, indent=2)
            logger.debug(f"[HEALTH_COACH] 최근 지표 JSON 생성 완료: {len(recent_metrics_json)} 바이트")
        except Exception as e:
            logger.error(f"[HEALTH_COACH] 최근 지표 JSON 생성 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
            recent_metrics_json = "[]"
        
        prompt = f"""
        당신은 전문 건강 코치입니다. 다음 사용자의 지난 7일간 건강 데이터를 분석하여 주간 건강 리포트를 생성해주세요:
        
        사용자 정보:
        - 성별: {user_profile.get('gender', '정보 없음')}
        - 나이: {age}
        
        지난 7일간 건강 지표:
        {recent_metrics_json}
        
        다음 JSON 형식으로 반드시 응답해주세요:
        {{
            "metrics_summary": {{
                "weight_trend": "증가/감소/유지",
                "blood_pressure_trend": "증가/감소/유지",
                "sleep_quality": "좋음/보통/나쁨",
                "activity_level": "활발/보통/저조"
            }},
            "achievements": ["성취1", "성취2"],
            "challenges": ["도전1", "도전2"],
            "recommendations": ["추천1", "추천2", "추천3"],
            "next_steps": ["다음 단계1", "다음 단계2"],
            "overall_status": "개선/유지/악화"
        }}
        """
        logger.debug("[HEALTH_COACH] 프롬프트 구성 완료")
        
        # 에이전트 호출
        logger.info("[HEALTH_COACH] 주간 리포트 에이전트 호출 시작")
        start_time = datetime.now()
        
        try:
            response = await agent.ainvoke(prompt)
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            logger.info(f"[HEALTH_COACH] 주간 리포트 에이전트 호출 완료 (소요시간: {elapsed_time:.2f}초)")
            
            if hasattr(response, 'content'):
                logger.debug(f"[HEALTH_COACH] 응답 내용 일부: {response.content[:200]}...")
            else:
                logger.warning("[HEALTH_COACH] 응답에 content 필드가 없습니다")
        except Exception as e:
            logger.error(f"[HEALTH_COACH] 에이전트 호출 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 결과 처리
        report_data = {}
        
        # content 필드에서 JSON 추출
        if hasattr(response, 'content'):
            content = response.content
            
            # JSON 추출
            logger.debug("[HEALTH_COACH] JSON 추출 시작")
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("[HEALTH_COACH] JSON 코드 블록에서 추출 성공")
            else:
                json_str = re.search(r'({.*})', content, re.DOTALL)
                if json_str:
                    json_str = json_str.group(1)
                    logger.debug("[HEALTH_COACH] 정규식으로 JSON 추출 성공")
                else:
                    json_str = content
                    logger.warning("[HEALTH_COACH] JSON 형식을 찾을 수 없어 전체 내용을 사용합니다")
                    
            try:
                logger.debug(f"[HEALTH_COACH] JSON 파싱 시작: {json_str[:100]}...")
                report_data = json.loads(json_str)
                logger.info(f"[HEALTH_COACH] JSON 파싱 성공: {len(report_data)} 필드")
                logger.debug(f"[HEALTH_COACH] 파싱된 데이터 키: {list(report_data.keys())}")
            except Exception as e:
                logger.error(f"[HEALTH_COACH] JSON 파싱 오류: {str(e)}")
                logger.error(f"[HEALTH_COACH] 파싱 시도한 문자열: {json_str[:200]}...")
                logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
                report_data = {
                    "metrics_summary": {
                        "weight_trend": "정보 부족",
                        "blood_pressure_trend": "정보 부족",
                        "sleep_quality": "정보 부족",
                        "activity_level": "정보 부족"
                    },
                    "achievements": ["데이터 부족으로 성취 분석 불가"],
                    "challenges": ["충분한 건강 데이터 기록"],
                    "recommendations": ["정기적인 건강 지표 기록", "건강 검진 고려"],
                    "next_steps": ["앱에 건강 데이터 입력 시작"],
                    "overall_status": "정보 부족"
                }
        else:
            logger.warning("[HEALTH_COACH] 응답에 content 필드가 없습니다")
            report_data = {
                "metrics_summary": {
                    "weight_trend": "정보 부족",
                    "blood_pressure_trend": "정보 부족",
                    "sleep_quality": "정보 부족",
                    "activity_level": "정보 부족"
                },
                "achievements": ["데이터 부족으로 성취 분석 불가"],
                "challenges": ["충분한 건강 데이터 기록"],
                "recommendations": ["정기적인 건강 지표 기록", "건강 검진 고려"],
                "next_steps": ["앱에 건강 데이터 입력 시작"],
                "overall_status": "정보 부족"
            }
        
        # WeeklyHealthReport 객체 생성
        logger.debug("[HEALTH_COACH] WeeklyHealthReport 객체 생성 시작")
        try:
            report = WeeklyHealthReport(
                user_id=state.user_id,
                start_date=start_date,
                end_date=end_date,
                metrics_summary=report_data.get('metrics_summary', {}),
                achievements=report_data.get('achievements', []),
                challenges=report_data.get('challenges', []),
                recommendations=report_data.get('recommendations', []),
                next_steps=report_data.get('next_steps', []),
                overall_status=report_data.get('overall_status', '')
            )
            logger.debug("[HEALTH_COACH] WeeklyHealthReport 객체 생성 완료")
        except Exception as e:
            logger.error(f"[HEALTH_COACH] WeeklyHealthReport 객체 생성 오류: {str(e)}")
            logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
            raise
        
        # 상태 업데이트
        state.weekly_health_report = report
        
        logger.info(f"[HEALTH_COACH] 주간 건강 리포트 생성 완료 - 사용자 ID: {state.user_id}")
        
        return state
        
    except Exception as e:
        logger.error(f"[HEALTH_COACH] 주간 건강 리포트 생성 중 예외 발생: {str(e)}")
        logger.error(f"[HEALTH_COACH] 오류 상세: {traceback.format_exc()}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_report = WeeklyHealthReport(
            request_id=str(uuid4()),
            user_id=state.user_id,
            week_start_date=start_date.isoformat() if start_date else None,
            week_end_date=end_date.isoformat() if end_date else None,
            summary="주간 건강 리포트 생성 중 오류가 발생했습니다.",
            health_metrics_summary="데이터를 처리할 수 없습니다.",
            exercise_summary="데이터를 처리할 수 없습니다.",
            diet_summary="데이터를 처리할 수 없습니다.",
            sleep_summary="데이터를 처리할 수 없습니다.",
            recommendations=["시스템 오류로 인해 리포트를 제공할 수 없습니다. 나중에 다시 시도해주세요."],
            next_week_goals=[]
        )
        
        # 상태 업데이트
        state.weekly_health_report = fallback_report
        
        logger.info(f"[HEALTH_COACH] 주간 건강 리포트 생성 완료 (오류 발생) - 요청 ID: {fallback_report.request_id}")
        
        # 수정된 UserState 객체 반환
        return state 