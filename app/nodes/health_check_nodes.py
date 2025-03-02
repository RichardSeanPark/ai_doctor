from typing import Dict, Any, List, Union
from uuid import uuid4
from datetime import datetime, timedelta
import logging

from langgraph.graph import END

from app.models.health_data import HealthAssessment, HealthMetrics, Symptom
from app.models.notification import UserState, AndroidNotification
from app.agents.agent_config import get_health_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def analyze_health_metrics(state: UserState) -> HealthAssessment:
    # 사용자의 건강 지표 분석
    logger.info(f"건강 지표 분석 시작 - 사용자 ID: {state.user_profile.get('user_id', 'unknown')}")
    
    health_metrics = state.health_metrics
    if not health_metrics:
        logger.warning("분석할 건강 지표가 없습니다")
        return HealthAssessment(
            assessment_id=str(uuid4()),
            timestamp=datetime.now(),
            health_status="정보 없음",
            has_concerns=False,
            concerns=[],
            recommendations=["건강 지표를 입력해주세요."],
            summary="건강 지표 정보 없음"
        )
    
    # 건강 에이전트 생성
    agent = get_health_agent()
    
    # 사용자 건강 데이터 준비
    metrics_data = "\n".join([
        f"- {metric}: {value} {unit}"
        for metric, (value, unit) in health_metrics.items()
    ])
    
    user_profile = state.user_profile
    age = user_profile.get("age", "알 수 없음")
    gender = user_profile.get("gender", "알 수 없음")
    medical_conditions = user_profile.get("medical_conditions", [])
    conditions_str = "없음" if not medical_conditions else ", ".join(medical_conditions)
    
    # AI에게 건강 지표 분석 요청
    prompt = f"""
    다음 사용자의 건강 지표를 분석하고 평가해주세요:
    
    사용자 정보:
    - 나이: {age}
    - 성별: {gender}
    - 기존 질환: {conditions_str}
    
    건강 지표:
    {metrics_data}
    
    분석 결과를 제공해주세요:
    1. 전반적인 건강 상태 (정상, 주의, 경고 중 하나)
    2. 우려 사항이 있는지 여부 (있음/없음)
    3. 구체적인 우려 사항 (있는 경우)
    4. 개선을 위한 권장 사항 (3가지)
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "health_status": "정상/주의/경고",
        "has_concerns": true/false,
        "concerns": ["우려 사항 1", "우려 사항 2", ...],
        "recommendations": ["권장 사항 1", "권장 사항 2", "권장 사항 3"]
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
    import json
    import re
    
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"건강 지표 분석 완료 - 상태: {data['health_status']}, 우려 사항: {data['has_concerns']}")
    
    # 분석 결과 생성
    assessment = HealthAssessment(
        assessment_id=str(uuid4()),
        timestamp=datetime.now(),
        health_status=data["health_status"],
        has_concerns=data["has_concerns"],
        concerns=data["concerns"],
        recommendations=data["recommendations"],
        summary="건강 지표 분석 결과"
    )
    
    # 분석 결과를 상태에 저장
    state.health_assessment = assessment
    
    # 음성 응답을 위한 스크립트 생성
    voice_script = f"건강 지표 분석 결과입니다. 현재 건강 상태는 {data['health_status']}입니다."
    if data["has_concerns"]:
        voice_script += f" 주의할 점은 {data['concerns'][0]}입니다."
    state.voice_scripts.append(voice_script)
    
    return assessment

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
            summary="증상 정보 없음"
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
    import json
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
        summary="증상 분석 결과"
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