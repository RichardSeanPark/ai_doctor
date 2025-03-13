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

async def analyze_health_metrics(health_profile: Dict[str, Any], query_text: str = None) -> HealthAssessment:
    """
    사용자의 건강 지표를 분석하여 건강 평가를 수행하는 함수
    
    Args:
        health_profile: 사용자의 건강 프로필 정보(DB에서 로드된 정보)
        query_text: 사용자 질문 텍스트 (선택적)
    
    Returns:
        HealthAssessment: 건강 평가 결과
    """
    # 사용자 ID 로그
    user_info = health_profile.get('user_info', {})
    user_id = user_info.get('user_id', 'unknown')
    logger.info(f"건강 지표 분석 시작 - 사용자 ID: {user_id}")
    
    # 쿼리 텍스트 로깅
    if query_text:
        logger.info(f"건강 상담 쿼리: '{query_text}'")
    
    # 건강 지표 준비
    health_metrics = health_profile.get('latest_metrics', {})
    if not health_metrics:
        logger.warning("분석할 건강 지표가 없습니다")
        health_metrics = {}  # 빈 딕셔너리 초기화 (오류 방지)
    
    # 건강 에이전트 생성
    agent = get_health_agent()
    
    # 건강 지표 문자열로 변환
    metrics_lines = []
    for key, value in health_metrics.items():
        # BMI 계산이 있으면 특별 처리
        if key == 'bmi' and value is not None:
            bmi_value = value
            if bmi_value < 18.5:
                bmi_category = "저체중"
            elif bmi_value < 23:
                bmi_category = "정상"
            elif bmi_value < 25:
                bmi_category = "과체중"
            elif bmi_value < 30:
                bmi_category = "경도 비만"
            else:
                bmi_category = "중등도 이상 비만"
            metrics_lines.append(f"- BMI: {bmi_value:.1f} ({bmi_category})")
        # 혈압 처리
        elif key == 'blood_pressure_systolic' and 'blood_pressure_diastolic' in health_metrics:
            sys_value = value
            dia_value = health_metrics.get('blood_pressure_diastolic')
            if sys_value is not None and dia_value is not None:
                metrics_lines.append(f"- 혈압: {sys_value}/{dia_value} mmHg")
        elif key == 'blood_pressure_diastolic':
            continue  # 이미 수축기 혈압에서 처리함
        # 기타 지표 처리
        elif value is not None:
            # 각 지표별 단위 설정
            unit = ""
            if key == 'weight':
                unit = "kg"
            elif key == 'height':
                unit = "cm"
            elif key == 'heart_rate':
                unit = "bpm"
            elif key == 'blood_sugar':
                unit = "mg/dL"
            elif key == 'temperature':
                unit = "°C"
            elif key == 'oxygen_saturation':
                unit = "%"
            elif key == 'sleep_hours':
                unit = "시간"
            elif key == 'steps':
                unit = "걸음"
            
            metrics_lines.append(f"- {key.replace('_', ' ').title()}: {value} {unit}")
    
    metrics_data = "\n".join(metrics_lines) if metrics_lines else "건강 지표 정보 없음"
    
    # 사용자 정보 준비
    name = user_info.get('name', '사용자')
    birth_date = user_info.get('birth_date')
    gender = user_info.get('gender', '알 수 없음')
    
    # 나이 계산
    age = "알 수 없음"
    if birth_date:
        try:
            birth_year = birth_date.year if hasattr(birth_date, 'year') else int(str(birth_date).split('-')[0])
            current_year = datetime.now().year
            age = current_year - birth_year
        except:
            pass
    
    # 의학적 상태 정보
    medical_conditions = health_profile.get('medical_conditions', [])
    conditions_text = "없음"
    if medical_conditions:
        condition_items = []
        for condition in medical_conditions:
            condition_name = condition.get('condition_name', '')
            diagnosis_date = condition.get('diagnosis_date', '')
            if diagnosis_date:
                condition_items.append(f"{condition_name} (진단: {diagnosis_date})")
            else:
                condition_items.append(condition_name)
        conditions_text = ", ".join(condition_items)
    
    # 식이 제한 정보
    dietary_restrictions = health_profile.get('dietary_restrictions', [])
    restrictions_text = "없음"
    if dietary_restrictions:
        restriction_items = []
        for restriction in dietary_restrictions:
            restriction_items.append(restriction.get('restriction_type', ''))
        restrictions_text = ", ".join(restriction_items)
    
    # AI에게 건강 지표 분석 요청
    prompt = f"""
    다음 사용자의 건강 지표를 분석하고 평가해주세요:
    
    사용자 정보:
    - 이름: {name}
    - 나이: {age}세
    - 성별: {gender}
    - 기존 질환: {conditions_text}
    - 식이 제한: {restrictions_text}
    
    건강 지표:
    {metrics_data}
    
    {f"사용자 질문: {query_text}" if query_text else ""}
    
    위 정보를 바탕으로 건강 상태를 분석하고, 다음 형식으로 응답해주세요:
    1. 전반적인 건강 상태 (건강함, 주의 필요, 우려됨 중 하나)
    2. 발견된 잠재적 건강 이슈 (발견 시)
    3. 건강 개선을 위한 구체적인 권장 사항
    4. 건강 상태에 대한 간략한 요약
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "health_status": "건강 상태",
        "concerns": ["잠재적 건강 이슈 1", "잠재적 건강 이슈 2"],
        "recommendations": ["권장 사항 1", "권장 사항 2", "권장 사항 3"],
        "assessment_summary": "건강 상태 요약"
    }}
    """
    
    # 에이전트 실행 및 결과 파싱
    try:
        logger.info("건강 에이전트 API 호출 시작")
        result = await agent.ainvoke({"input": prompt})
        
        # 결과 로깅
        logger.info("건강 에이전트 API 호출 완료")
        
        # AIMessage 객체에서 content 추출
        if hasattr(result, 'content'):
            output = result.content
            logger.info("건강 에이전트 응답 content 속성 존재")
        else:
            output = str(result)
            logger.info("건강 에이전트 응답 content 속성 없음, 결과를 문자열로 변환")
        
        # 디버깅을 위해 응답 처음 200자 로깅
        logger.info(f"건강 에이전트 응답 (처음 200자): {output[:200]}...")
        
        # JSON 문자열 추출 및 파싱
        import json
        import re
        
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.info("JSON 코드 블록 찾음")
            else:
                json_pattern = re.search(r'{.*}', output, re.DOTALL)
                if json_pattern:
                    json_str = json_pattern.group(0)
                    logger.info("중괄호로 둘러싸인 JSON 데이터 찾음")
                else:
                    logger.error("JSON 형식의 응답을 찾을 수 없음")
                    raise ValueError("JSON 형식의 응답을 찾을 수 없습니다.")
            
            logger.info(f"파싱할 JSON (처음 100자): {json_str[:100]}...")
            data = json.loads(json_str)
            
            # 응답 생성
            assessment = HealthAssessment(
                assessment_id=str(uuid4()),
                timestamp=datetime.now(),
                health_status=data.get("health_status", "알 수 없음"),
                has_concerns=bool(data.get("concerns", [])),
                concerns=data.get("concerns", []),
                recommendations=data.get("recommendations", ["권장 사항 없음"]),
                assessment_summary=data.get("assessment_summary", "요약 정보 없음"),
                query_text=query_text   # 쿼리 텍스트도 저장 (추적 목적)
            )
            
            # 건강 평가 결과 로깅
            status = assessment.health_status
            concern_count = len(assessment.concerns)
            logger.info(f"건강 평가 완료: 상태={status}, 이슈={concern_count}개")
            
            return assessment
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"건강 평가 응답 처리 중 오류 발생: {str(e)}")
            
            # 오류 발생 시 기본 평가 생성
            default_assessment = HealthAssessment(
                assessment_id=str(uuid4()),
                timestamp=datetime.now(),
                health_status="분석 오류",
                has_concerns=True,
                concerns=["건강 지표 분석 중 오류가 발생했습니다."],
                recommendations=["의사와 상담하세요.", "추가 건강 검진을 받으세요."],
                assessment_summary=f"건강 지표 분석 중 오류: {str(e)}. 만약 건강 문제가 있다면 의사와 상담하세요.",
                query_text=query_text
            )
            
            return default_assessment
    
    except Exception as e:
        logger.error(f"건강 평가 처리 중 오류 발생: {str(e)}")
        
        # 오류 발생 시 기본 평가 생성
        error_assessment = HealthAssessment(
            assessment_id=str(uuid4()),
            timestamp=datetime.now(),
            health_status="처리 오류",
            has_concerns=True,
            concerns=["시스템 오류로 건강 지표를 평가할 수 없습니다."],
            recommendations=["나중에 다시 시도하세요.", "지속적인 문제 발생 시 의사와 상담하세요."],
            assessment_summary=f"시스템 오류: {str(e)}. 건강에 즉각적인 우려가 있으면 의사와 상담하세요.",
            query_text=query_text
        )
        
        return error_assessment

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