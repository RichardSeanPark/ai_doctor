from typing import Dict, Any, List, Union
from uuid import uuid4
from datetime import datetime, timedelta
import logging

from langgraph.graph import END

from app.models.voice_data import VoiceQuery, VoiceResponse, ConsultationSummary, VoiceSegment
from app.models.notification import UserState
from app.agents.agent_config import get_voice_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def process_voice_query(state: UserState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    logger.info("음성 쿼리 처리 시작")
    
    # config에서 voice_data 추출
    if config is None:
        config = {}
    
    voice_data = config.get("voice_data", {})
    
    # voice_data가 문자열인 경우 처리
    if isinstance(voice_data, str):
        query_text = voice_data
    elif isinstance(voice_data, dict):
        # 음성 쿼리 텍스트 (실제로는 음성 인식 결과가 여기 들어갑니다)
        query_text = voice_data.get("text", "")
    else:
        query_text = ""
        logger.warning(f"지원되지 않는 voice_data 형식: {type(voice_data)}")
    
    # 음성 에이전트 생성
    agent = get_voice_agent()
    
    # 사용자 정보 준비
    user_profile = state.user_profile
    user_name = user_profile.get("name", "")
    
    # 건강 지표 정보 준비
    health_metrics = user_profile.get("current_metrics", {})
    metrics_text = ""
    if health_metrics:
        metrics_text = "\n".join([
            f"- {metric}: {value}"
            for metric, value in health_metrics.items()
            if not isinstance(value, dict)  # 중첩된 딕셔너리 제외
        ])
    
    # AI에게 음성 쿼리 처리 요청
    prompt = f"""
    다음 사용자의 음성 쿼리에 응답해주세요:
    
    사용자 정보:
    - 이름: {user_name}
    - 성별: {user_profile.get('gender', '알 수 없음')}
    
    최근 건강 지표:
    {metrics_text if metrics_text else "정보 없음"}
    
    음성 쿼리:
    "{query_text}"
    
    자연스럽고 도움이 되는 응답을 제공해주세요. 응답은 음성으로 전달될 것입니다.
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "response_text": "사용자에게 전달할 응답",
        "requires_followup": true/false,
        "followup_question": "필요한 경우 후속 질문",
        "key_points": ["핵심 포인트 1", "핵심 포인트 2"],
        "recommendations": ["추천사항 1", "추천사항 2"]
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
    
    logger.info(f"음성 쿼리 처리 완료 - 후속 질문 필요: {data.get('requires_followup', False)}")
    
    # 응답 생성
    response = VoiceResponse(
        response_id=str(uuid4()),
        timestamp=datetime.now(),
        query_text=query_text,
        response_text=data["response_text"],
        requires_followup=data.get("requires_followup", False),
        followup_question=data.get("followup_question") if data.get("requires_followup", False) else None,
        key_points=data.get("key_points", ["정보 없음"]),
        recommendations=data.get("recommendations", ["추천사항 없음"])
    )
    
    # 음성 스크립트 저장
    state.voice_scripts.append(data["response_text"])
    
    # 응답을 상태에 저장
    state.last_response = response
    
    # 다음 노드로 전달할 데이터
    return {"response": response}

async def conduct_voice_consultation(state: UserState, config: Dict[str, Any] = None) -> ConsultationSummary:
    logger.info("음성 상담 시작")
    
    # config에서 consultation_data 추출
    if config is None:
        config = {}
    
    consultation_data = config.get("consultation_data", {})
    
    # 실제로는 여기서 음성 인식 및 합성 API를 호출하거나 ML 모델을 사용할 것입니다.
    # 여기서는 간단한 시뮬레이션만 수행합니다.
    
    # 음성 에이전트 생성
    agent = get_voice_agent()
    
    # 상담 데이터 준비
    consultation_topic = consultation_data.get("topic", "일반 건강 상담")
    user_questions = consultation_data.get("questions", [])
    
    # 사용자 정보 준비
    user_profile = state.user_profile
    user_name = user_profile.get("name", "")
    
    # 건강 지표 정보 준비
    health_metrics = user_profile.get("current_metrics", {})
    metrics_text = ""
    if health_metrics:
        metrics_text = "\n".join([
            f"- {metric}: {value}"
            for metric, value in health_metrics.items()
            if not isinstance(value, dict)  # 중첩된 딕셔너리 제외
        ])
    
    # 증상 정보 준비
    symptoms = state.symptoms if state.symptoms else []
    symptoms_text = ""
    if symptoms:
        symptoms_text = "\n".join([
            f"- {symptom.get('description')}: 심각도 {symptom.get('severity')}/10"
            for symptom in symptoms
        ])
    
    # AI에게 상담 진행 요청
    prompt = f"""
    다음 사용자와의 건강 상담을 진행해주세요:
    
    사용자 정보:
    - 이름: {user_name}
    - 성별: {user_profile.get('gender', '알 수 없음')}
    
    최근 건강 지표:
    {metrics_text if metrics_text else "정보 없음"}
    
    증상 정보:
    {symptoms_text if symptoms_text else "정보 없음"}
    
    상담 주제: {consultation_topic}
    
    사용자 질문:
    {chr(10).join([f"- {q}" for q in user_questions]) if user_questions else "질문 없음"}
    
    자연스럽고 도움이 되는 상담을 진행해주세요. 상담 내용은 음성으로 전달될 것입니다.
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "consultation_summary": "상담 내용 요약",
        "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
        "recommendations": ["권장 사항 1", "권장 사항 2", "권장 사항 3"],
        "followup_needed": true/false
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
    
    logger.info(f"음성 상담 완료 - 추가 상담 필요: {data.get('followup_needed', False)}")
    
    # 상담 요약 생성
    summary = ConsultationSummary(
        consultation_id=str(uuid4()),
        timestamp=datetime.now(),
        topic=consultation_topic,
        summary=data["consultation_summary"],
        key_points=data["key_points"],
        recommendations=data["recommendations"],
        followup_needed=data.get("followup_needed", False)
    )
    
    # 음성 스크립트 저장
    voice_script = f"""
    {data["consultation_summary"]}
    
    핵심 사항:
    {chr(10).join([f"- {point}" for point in data["key_points"]])}
    
    권장 사항:
    {chr(10).join([f"- {rec}" for rec in data["recommendations"]])}
    
    {"추가 상담이 필요합니다." if data.get("followup_needed", False) else "오늘 상담은 여기까지입니다. 건강하세요!"}
    """
    
    state.voice_scripts.append(voice_script)
    
    return summary

async def create_voice_segments(state: UserState, response: VoiceResponse = None) -> Dict[str, Any]:
    logger.info("음성 세그먼트 생성 시작")
    
    segments = []
    
    # response 매개변수가 없으면 state에서 가져오기
    if response is None:
        response = state.last_response
    
    if response is None:
        logger.warning("응답이 없어 기본 메시지를 사용합니다")
        # 기본 응답 생성
        default_text = "죄송합니다. 요청을 처리할 수 없습니다."
        segments.append(VoiceSegment(
            segment_id=str(uuid4()),
            text=default_text,
            duration_seconds=2.0,
            segment_type="error"
        ))
        state.voice_segments = segments
        
        # 음성 스크립트도 추가
        state.voice_scripts.append(default_text)
        
        return {"segments": segments, "scripts": [default_text]}
    
    # 인사말 세그먼트
    greeting = "안녕하세요, 건강 관리 AI 주치의입니다."
    segments.append(VoiceSegment(
        segment_id=str(uuid4()),
        text=greeting,
        duration_seconds=2.0,
        segment_type="greeting"
    ))
    
    # 응답 세그먼트
    segments.append(VoiceSegment(
        segment_id=str(uuid4()),
        text=response.response_text,
        duration_seconds=len(response.response_text.split()) * 0.5,  # 단어 수에 따른 대략적인 시간 계산
        segment_type="response"
    ))
    
    # 마무리 세그먼트
    closing_text = "추가 질문이 있으신가요?" if response.requires_followup else "오늘 상담은 여기까지입니다. 건강하세요!"
    segments.append(VoiceSegment(
        segment_id=str(uuid4()),
        text=closing_text,
        duration_seconds=3.0,
        segment_type="closing"
    ))
    
    logger.info(f"음성 세그먼트 생성 완료 - 세그먼트 수: {len(segments)}")
    
    # 상태에 세그먼트 저장
    state.voice_segments = segments
    
    # 음성 스크립트도 추가
    full_script = f"{greeting}\n{response.response_text}\n{closing_text}"
    state.voice_scripts.append(full_script)
    
    return {"segments": segments, "scripts": [full_script]} 