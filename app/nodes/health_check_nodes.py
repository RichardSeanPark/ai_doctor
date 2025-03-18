from typing import Dict, Any, List, Union, Optional
from uuid import uuid4
from datetime import datetime, timedelta
import logging
import json
import re

from langgraph.graph import END

from app.models.health_data import HealthAssessment, HealthMetrics, Symptom
from app.models.notification import UserState, AndroidNotification
from app.agents.agent_config import get_health_agent, RealGeminiAgent

# 로거 설정
logger = logging.getLogger(__name__)

async def analyze_health_metrics(state: UserState) -> HealthAssessment:
    """
    사용자의 건강 지표 분석
    
    Args:
        state: 사용자 상태 객체 (건강 지표 포함)
        
    Returns:
        HealthAssessment: 건강 평가 결과
    """
    try:
        logger.info(f"건강 지표 분석 시작 - 사용자 ID: {state.user_id}")
        
        # 음성 쿼리 처리
        if state.query_text:
            logger.info(f"음성 건강 상담 쿼리 감지: '{state.query_text}'")
        
        # 건강 지표 정보 추출
        health_metrics = {}
        
        # UserState에서 건강 지표 데이터 추출
        if hasattr(state, 'user_profile') and state.user_profile:
            if 'health_metrics' in state.user_profile and state.user_profile['health_metrics']:
                # health_metrics 딕셔너리에서 각 항목 추출
                metrics = state.user_profile['health_metrics']
                
                # 필수 건강 지표 항목 추출
                for key in ['weight', 'height', 'heart_rate', 'blood_sugar', 
                           'oxygen_saturation', 'sleep_hours', 'steps', 'bmi', 'temperature']:
                    if key in metrics and metrics[key] is not None:
                        health_metrics[key] = metrics[key]
                
                # 혈압 처리 (다양한 포맷 지원)
                if 'blood_pressure' in metrics and isinstance(metrics['blood_pressure'], dict):
                    bp = metrics['blood_pressure']
                    if 'systolic' in bp and 'diastolic' in bp and bp['systolic'] is not None and bp['diastolic'] is not None:
                        health_metrics['blood_pressure'] = {
                            'systolic': bp['systolic'],
                            'diastolic': bp['diastolic']
                        }
                elif 'blood_pressure_systolic' in metrics and 'blood_pressure_diastolic' in metrics:
                    if metrics['blood_pressure_systolic'] is not None and metrics['blood_pressure_diastolic'] is not None:
                        health_metrics['blood_pressure'] = {
                            'systolic': metrics['blood_pressure_systolic'],
                            'diastolic': metrics['blood_pressure_diastolic']
                        }
        
        # 건강 지표가 없는 경우 로그
        if not health_metrics:
            logger.warning("분석할 건강 지표가 없습니다")
            # 건강 지표가 없을 경우 바로 정보 부족 상태 반환
            assessment = HealthAssessment(
                assessment_id=str(uuid4()),
                user_id=state.user_id,
                health_status="정보 부족",
                concerns=["건강 지표 정보가 제공되지 않았습니다.", "현재 건강 상태를 평가할 수 있는 데이터가 없습니다."],
                recommendations=["혈압, 혈당, 콜레스테롤 수치 등 기본적인 건강 지표를 측정해주세요.",
                               "최근 건강 검진 결과를 확인해주세요.",
                               "의사와 상담하여 건강 상태를 평가받고 필요한 조치를 취해주세요."],
                timestamp=datetime.now(),
                assessment_summary="제공된 건강 지표가 없어 현재 건강 상태를 평가할 수 없습니다. 건강 지표 측정을 권장합니다.",
                has_concerns=True
            )
            return assessment
        else:
            logger.info(f"분석할 건강 지표: {len(health_metrics)}개 항목 - {', '.join(health_metrics.keys())}")
        
        # 건강 에이전트 초기화
        agent = get_health_agent()
        
        # 프롬프트 구성 - 응답 형식을 명확히 지정
        prompt = f"""
        당신은 세계에서 가장 유명하고 친절한 의사 입니다. 다음 사용자의 건강 지표를 분석하고 진단 및 조언을 제공해주세요.:
        
        사용자 ID: {state.user_id}
        질문: {state.query_text}
        건강 지표: {json.dumps(health_metrics, ensure_ascii=False, indent=2)}
        
        매우 중요: 반드시 아래 JSON 형식으로만 응답해주세요. 다른 텍스트나 설명은 추가하지 마세요.
        
        {{
            "health_status": "정상" 또는 "주의 필요" 또는 "경고" 또는 "정보 부족" 중 하나,
            "concerns": ["우려사항1", "우려사항2"], 
            "recommendations": ["추천사항1", "추천사항2", "추천사항3"],
            "assessment_summary": "건강 상태에 대한 진단 및 조언. 조언에 대해 의사 상담 방법, 음식, 운동 등 카테고리를 선정하고 해당 카테코리에 맞게 설명해주세요."
        }}
        
        응답은 반드시 유효한 JSON 형식이어야 합니다. 중괄호, 따옴표, 콤마를 정확히 사용하세요.
        정보가 부족하면 "정보 부족"을 반환하고, 비어있는 건강 지표에 대한 정보를 concerns에 추가해주세요.
        """
        
        logger.info("건강 에이전트 API 호출 시작")
        
        # 에이전트 호출
        response = await agent.ainvoke(prompt)
        logger.info(f"응답 타입: {type(response)}")
        
        if isinstance(response, dict):
            logger.info(f"응답 필드: {response.keys()}")
        else:
            logger.info(f"응답이 dict 형식이 아닙니다: {type(response)}")
        
        # 결과 처리
        assessment_data = {}
        
        # content 필드에서 JSON 추출
        if isinstance(response, dict) and 'content' in response:
            logger.info("응답에서 content 필드 찾음")
            content = response['content']
            
            try:
                # JSON 코드 블록 추출 시도
                json_str = extract_json(content)
                if json_str:
                    logger.info(f"JSON 데이터 추출 성공 (처음 100자): {json_str[:100]}")
                    assessment_data = json.loads(json_str)
                else:
                    logger.warning("JSON 데이터를 추출할 수 없습니다")
            except Exception as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
        else:
            # 직접 응답이 올 경우 처리
            try:
                if isinstance(response, str):
                    json_str = extract_json(response)
                    if json_str:
                        assessment_data = json.loads(json_str)
                elif isinstance(response, dict):
                    # 이미 dictionary 형태로 반환된 경우
                    assessment_data = response
            except Exception as e:
                logger.error(f"응답 처리 오류: {str(e)}")
                logger.warning(f"응답에 content 필드가 없거나 응답이 dict가 아닙니다: {response}")
        
        # 필수 필드 확인
        if not assessment_data or "health_status" not in assessment_data:
            logger.warning("건강 상태가 없거나 불완전한 JSON입니다. 기본값 설정")
            assessment_data = {
                "health_status": "정보 부족",
                "concerns": ["건강 지표 정보 부족으로 인한 평가 불가"],
                "recommendations": ["건강 검진을 통해 건강 지표를 업데이트하세요."],
                "assessment_summary": "건강 상태를 평가할 수 있는 충분한 정보가 없습니다."
            }
        
        # 필드가 비어 있으면 기본값 설정
        if "concerns" not in assessment_data:
            # 건강 지표가 충분한지 확인 (최소 5개 이상의 건강 지표가 있으면 충분하다고 판단)
            if len(health_metrics) < 5:
                assessment_data["concerns"] = ["건강 지표 정보 부족으로 인한 평가 불가"]
            else:
                assessment_data["concerns"] = []
            
        if "recommendations" not in assessment_data or not assessment_data["recommendations"]:
            assessment_data["recommendations"] = ["건강 검진을 통해 건강 지표를 업데이트하세요."]
            
        if "assessment_summary" not in assessment_data or not assessment_data["assessment_summary"]:
            assessment_data["assessment_summary"] = f"건강 상태: {assessment_data.get('health_status', '정보 부족')}"
        
        # HealthAssessment 객체 생성
        assessment = HealthAssessment(
            assessment_id=str(uuid4()),
            user_id=state.user_id,
            health_status=assessment_data.get('health_status', '정보 부족'),
            concerns=assessment_data.get('concerns', []),
            recommendations=assessment_data.get('recommendations', []),
            timestamp=datetime.now(),
            assessment_summary=assessment_data.get('assessment_summary', ''),
            has_concerns=bool(assessment_data.get('concerns', []))
        )
        
        # 상태 업데이트
        state.health_assessment = assessment
        
        logger.info(f"건강 평가 완료: 상태={assessment.health_status}, 이슈={len(assessment.concerns)}개")
        
        return assessment
        
    except Exception as e:
        logger.error(f"건강 지표 분석 중 오류 발생: {str(e)}")
        raise

def extract_json(text: str) -> Optional[str]:
    """텍스트에서 JSON 문자열을 추출하는 함수"""
    try:
        # JSON 코드 블록 찾기 (```json ... ``` 형식)
        json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        json_blocks = re.findall(json_block_pattern, text)
        
        if json_blocks:
            logger.info("JSON 코드 블록 찾음")
            return json_blocks[0].strip()
        
        # 중괄호 기반 JSON 찾기
        json_pattern = r"(\{[\s\S]*\})"
        json_matches = re.findall(json_pattern, text)
        
        if json_matches:
            # 가장 긴 JSON 문자열을 선택 (완전한 JSON 객체일 가능성이 높음)
            logger.info("중괄호 기반 JSON 찾음")
            return max(json_matches, key=len).strip()
        
        logger.warning("텍스트에서 JSON을 찾을 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"JSON 추출 중 오류: {str(e)}")
        return None

async def alert_health_concern(state: UserState, assessment: HealthAssessment) -> AndroidNotification:
    logger.info(f"건강 우려 사항 알림 생성 - 상태: {assessment.health_status}")
    
    # 알림 생성
    concerns_text = "\n".join([f"- {concern}" for concern in assessment.concerns])
    recommendations_text = "\n".join([f"- {rec}" for rec in assessment.recommendations])
    
    notification_title = f"건강 주의 알림: {assessment.health_status}"
    notification_body = f"""
    건강 지표에 주의가 필요합니다.
    
    우려 사항:
    {concerns_text}
    
    권장 사항:
    {recommendations_text}
    """
    
    notification = AndroidNotification(
        title=notification_title,
        body=notification_body,
        priority="high" if assessment.health_status == "경고" else "normal"
    )
    
    # 알림 저장
    state.notifications.append(notification)
    
    return notification

async def analyze_symptoms(state: UserState) -> HealthAssessment:
    # 사용자의 증상 분석
    logger.info(f"증상 분석 시작 - 사용자 ID: {state.user_profile.get('user_id', 'unknown')}")
    
    symptoms = state.symptoms
    if not symptoms:
        logger.warning("분석할 증상이 없습니다")
        return HealthAssessment(
            assessment_id=str(uuid4()),
            timestamp=datetime.now(),
            health_status="정보 없음",
            has_concerns=False,
            concerns=[],
            recommendations=["증상 정보를 입력해주세요."],
            assessment_summary="증상 정보 없음"
        )
    
    # 건강 에이전트 생성
    agent = get_health_agent()
    
    # 사용자 증상 데이터 준비
    symptoms_data = "\n".join([
        f"- {symptom.get('description')}: 심각도 {symptom.get('severity')}/10, " +
        f"시작 시간: {symptom.get('onset_time').strftime('%Y-%m-%d %H:%M')}"
        for symptom in symptoms
    ])
    
    user_profile = state.user_profile
    age = user_profile.get("age", "알 수 없음")
    gender = user_profile.get("gender", "알 수 없음")
    medical_conditions = user_profile.get("medical_conditions", [])
    conditions_str = "없음" if not medical_conditions else ", ".join(medical_conditions)
    
    # AI에게 증상 분석 요청
    prompt = f"""
    다음 사용자의 증상을 분석하고 평가해주세요:
    
    사용자 정보:
    - 나이: {age}
    - 성별: {gender}
    - 기존 질환: {conditions_str}
    
    증상:
    {symptoms_data}
    
    분석 결과를 제공해주세요:
    1. 전반적인 건강 상태 (정상, 주의, 경고 중 하나)
    2. 우려 사항이 있는지 여부 (있음/없음)
    3. 가능한 원인 (3가지)
    4. 권장 조치 (3가지)
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "health_status": "정상/주의/경고",
        "has_concerns": true/false,
        "concerns": ["가능한 원인 1", "가능한 원인 2", "가능한 원인 3"],
        "recommendations": ["권장 조치 1", "권장 조치 2", "권장 조치 3"]
    }}
    """
    
    # 에이전트 실행 및 결과 파싱
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 문자열 추출 및 파싱
    import re
    
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"증상 분석 완료 - 상태: {data['health_status']}, 우려 사항: {data['has_concerns']}")
    
    # 분석 결과 생성
    assessment = HealthAssessment(
        assessment_id=str(uuid4()),
        timestamp=datetime.now(),
        health_status=data["health_status"],
        has_concerns=data["has_concerns"],
        concerns=data["concerns"],
        recommendations=data["recommendations"],
        assessment_summary="증상 분석 결과"
    )
    
    # 분석 결과를 상태에 저장
    state.health_assessment = assessment
    
    # 음성 응답을 위한 스크립트 생성
    voice_script = f"증상 분석 결과입니다. 현재 건강 상태는 {data['health_status']}입니다."
    if data["has_concerns"]:
        voice_script += f" 가능한 원인은 {data['concerns'][0]}입니다."
    state.voice_scripts.append(voice_script)
    
    return assessment

async def notify_doctor(state: UserState, assessment: HealthAssessment) -> Dict[str, Any]:
    logger.info(f"의사 알림 생성 - 상태: {assessment.health_status}")
    
    # 실제로는 여기서 의사에게 메시지를 보내는 API를 호출할 것입니다.
    # 여기서는 간단한 시뮬레이션만 수행합니다.
    
    user_profile = state.user_profile
    user_name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}"
    
    # 증상 정보 수집
    symptoms_data = "\n".join([
        f"- {symptom.get('description')}: 심각도 {symptom.get('severity')}/10, " +
        f"시작 시간: {symptom.get('onset_time').strftime('%Y-%m-%d %H:%M')}"
        for symptom in state.symptoms
    ])
    
    # 의사 알림 메시지 생성
    doctor_message = f"""
    환자 정보:
    - 이름: {user_name}
    - 나이: {user_profile.get('age', '알 수 없음')}
    - 성별: {user_profile.get('gender', '알 수 없음')}
    - 기존 질환: {', '.join(user_profile.get('medical_conditions', ['없음']))}
    
    증상:
    {symptoms_data}
    
    분석 결과:
    - 상태: {assessment.health_status}
    - 우려 사항: {', '.join(assessment.concerns)}
    
    권장 조치:
    {', '.join(assessment.recommendations)}
    """
    
    # 알림 결과 생성
    notification_result = {
        "doctor_notified": True,
        "timestamp": datetime.now().isoformat(),
        "message": doctor_message
    }
    
    # 음성 스크립트 생성
    voice_script = "의사에게 귀하의 증상 정보가 전송되었습니다. 곧 연락이 올 것입니다."
    state.voice_scripts.append(voice_script)
    
    # 알림 생성
    notification = AndroidNotification(
        title="의사 알림 전송됨",
        body="귀하의 증상 정보가 의사에게 전송되었습니다. 곧 연락이 올 것입니다.",
        priority="high"
    )
    state.notifications.append(notification)
    
    return notification_result 