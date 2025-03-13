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
    """
    음성 질의를 처리하고 적절한 응답을 생성합니다.
    """
    logger.info("process_voice_query 함수 시작")
    logger.info(f"config 파라미터: {config}")
    
    # config 기본값 설정
    if config is None:
        config = {}
    
    # 1. voice_data 가져오기 (상태 객체와 config 모두 확인)
    # 상태 객체에서 voice_data 접근 시도
    voice_data = None
    
    # 1) 상태 객체에서 voice_data 확인
    if hasattr(state, 'voice_data') and state.voice_data is not None:
        voice_data = state.voice_data
        logger.info(f"상태 객체에서 voice_data 가져옴: {voice_data}")
    # 2) config에서 voice_data 확인
    elif "voice_data" in config:
        voice_data = config.get("voice_data")
        logger.info(f"config에서 voice_data 가져옴: {voice_data}")
    else:
        logger.warning("voice_data를 찾을 수 없음")
        voice_data = {}
    
    # voice_data가 딕셔너리인지 문자열인지 확인
    if isinstance(voice_data, str):
        logger.info("voice_data가 문자열, 딕셔너리로 변환")
        query_text = voice_data
    elif isinstance(voice_data, dict) and 'text' in voice_data:
        logger.info("voice_data가 딕셔너리, text 추출")
        query_text = voice_data['text']
    else:
        logger.warning(f"voice_data 형식을 인식할 수 없음: {type(voice_data)}")
        query_text = ""
    
    # 쿼리 텍스트가 비어있는 경우 state.voice_input에서 가져오기 시도
    if not query_text:
        logger.warning("쿼리 텍스트가 비어있음, state.voice_input에서 가져오기 시도")
        query_text = getattr(state, 'voice_input', '')
        logger.info(f"state.voice_input에서 가져온 쿼리: '{query_text}'")
    
    # 그래도 쿼리가 비어있으면 경고 로그 출력 후 기본 응답 반환
    if not query_text:
        logger.error("쿼리 텍스트를 찾을 수 없음")
        response = VoiceResponse(
            response_id=str(uuid4()),
            timestamp=datetime.now(),
            query_text="",
            response_text="죄송합니다. 음성 쿼리를 인식할 수 없습니다. 다시 말씀해주세요.",
            requires_followup=False,
            followup_question=None,
            key_points=["쿼리 인식 실패"],
            recommendations=["다시 시도하세요"]
        )
        # 상태에 응답을 명시적으로 저장
        state.last_response = response
        logger.info(f"빈 쿼리로 인한 기본 응답 생성, 상태에 저장: {state.last_response is not None}")
        
        # 변경된 상태 검증
        logger.info(f"상태를 통한 last_response: {getattr(state, 'last_response', None) is not None}")
        if hasattr(state, 'last_response'):
            logger.info(f"상태에 저장된 last_response ID: {state.last_response.response_id}")
            
        return {
            "last_response": response,  # create_voice_segments에 매개변수로 전달됨
            "response": response,       # 이전 버전과의 호환성 유지
            "__arg:last_response": response  # LangGraph에서 명시적으로 인식할 수 있는 형식
        }
    
    # 음성 에이전트 생성
    agent = get_voice_agent()
    
    # 사용자 정보 준비
    user_profile = state.user_profile
    user_name = user_profile.get("name", "")
    
    # AI에게 음성 쿼리 처리 요청
    prompt = f"""
    다음 사용자의 음성 쿼리에 응답해주세요:
    
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
    try:
        logger.info(f"Gemini API 호출 시작 - 쿼리: '{query_text}'")
        result = await agent.ainvoke({"input": prompt})
        
        # 결과 로깅
        logger.info("Gemini API 호출 완료")
        
        # AIMessage 객체에서 content 추출
        if hasattr(result, 'content'):
            output = result.content
            logger.info(f"Gemini 응답 content 속성 존재")
        else:
            output = str(result)
            logger.info(f"Gemini 응답 content 속성 없음, 결과를 문자열로 변환")
        
        # 디버깅을 위해 응답 처음 200자 로깅
        logger.info(f"Gemini 응답 (처음 200자): {output[:200]}...")
        
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
            logger.info(f"JSON 파싱 성공: {list(data.keys())}")
            
            # 반드시 필요한 필드 검증
            if "response_text" not in data:
                data["response_text"] = "음성 응답을 생성할 수 없습니다. 다시 시도해주세요."
            
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
            logger.info(f"응답을 상태에 저장 성공: {state.last_response is not None}")
            logger.info(f"응답 ID: {response.response_id}, 텍스트 길이: {len(response.response_text)}")
            
            # 다음 노드로 전달할 데이터 (상태 변경사항 명시적 반환)
            logger.info("상태 업데이트 및 last_response 전달")
            
            # 변경된 상태 검증
            logger.info(f"상태를 통한 last_response: {getattr(state, 'last_response', None) is not None}")
            if hasattr(state, 'last_response'):
                logger.info(f"상태에 저장된 last_response ID: {state.last_response.response_id}")
            
            # 반환 값은 두 가지 목적으로 사용됨:
            # 1. 직접 매개변수로 전달 - next_node(state, last_response=response)
            # 2. 상태 업데이트 - state.last_response = response
            logger.info("명확한 매개변수 이름으로 응답 반환")
            return {
                "last_response": response,  # create_voice_segments에 매개변수로 전달됨
                "response": response,       # 이전 버전과의 호환성 유지
                "__arg:last_response": response  # LangGraph에서 명시적으로 인식할 수 있는 형식
            }
        
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"응답 처리 중 오류 발생: {str(e)}")
            
            # 오류 발생 시 기본 응답 생성
            fallback_response = VoiceResponse(
                response_id=str(uuid4()),
                timestamp=datetime.now(),
                query_text=query_text,
                response_text="죄송합니다. 응답을 처리하는 중 오류가 발생했습니다. 다시 시도해주세요.",
                requires_followup=False,
                followup_question=None,
                key_points=["오류 발생"],
                recommendations=["다시 시도하세요"]
            )
            
            # 상태에 응답을 명시적으로 저장
            state.last_response = fallback_response
            logger.info(f"오류 발생으로 인한 대체 응답 생성, 상태에 저장: {state.last_response is not None}")
            
            # 상태 변경사항 명시적 반환
            return {
                "last_response": fallback_response,  # create_voice_segments에 매개변수로 전달됨
                "response": fallback_response,       # 이전 버전과의 호환성 유지
                "__arg:last_response": fallback_response  # LangGraph에서 명시적으로 인식할 수 있는 형식
            }
    
    except Exception as e:
        logger.error(f"음성 쿼리 처리 중 오류 발생: {str(e)}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_response = VoiceResponse(
            response_id=str(uuid4()),
            timestamp=datetime.now(),
            query_text=query_text,
            response_text="음성 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
            requires_followup=False,
            key_points=["오류 발생"],
            recommendations=["다시 시도해보세요"]
        )
        
        # 상태에 저장
        state.last_response = fallback_response
        logger.info(f"오류 발생으로 인한 기본 응답 생성, 상태에 저장: {state.last_response is not None}")
        
        # 상태 변경사항 명시적 반환
        return {
            "last_response": fallback_response,  # create_voice_segments에 매개변수로 전달됨
            "response": fallback_response,       # 이전 버전과의 호환성 유지
            "__arg:last_response": fallback_response  # LangGraph에서 명시적으로 인식할 수 있는 형식
        }

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
    
    # AI에게 상담 진행 요청
    prompt = f"""
    다음 사용자와의 건강 상담을 진행해주세요:
    
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
    
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_pattern = re.search(r'{.*}', output, re.DOTALL)
            if json_pattern:
                json_str = json_pattern.group(0)
            else:
                raise ValueError("JSON 형식의 응답을 찾을 수 없습니다.")
        
        data = json.loads(json_str)
        
        # 필수 필드 검증
        required_fields = ["consultation_summary", "key_points", "recommendations"]
        for field in required_fields:
            if field not in data:
                if field == "consultation_summary":
                    data[field] = "상담 정보를 생성할 수 없습니다."
                elif field == "key_points":
                    data[field] = ["정보 없음"]
                elif field == "recommendations":
                    data[field] = ["추천사항 없음"]
        
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
    
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error(f"상담 응답 처리 중 오류 발생: {str(e)}")
        
        # 오류 발생 시 기본 응답 생성
        fallback_summary = ConsultationSummary(
            consultation_id=str(uuid4()),
            timestamp=datetime.now(),
            topic=consultation_topic,
            summary="상담 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
            key_points=["오류 발생"],
            recommendations=["다시 시도해보세요"],
            followup_needed=False
        )
        
        # 음성 스크립트 저장
        error_script = "상담 처리 중 오류가 발생했습니다. 다시 시도해주세요."
        state.voice_scripts.append(error_script)
        
        return fallback_summary

async def create_voice_segments(state: UserState, config: Dict[str, Any] = None, last_response: Any = None) -> Dict[str, Any]:
    """
    음성 응답을 세그먼트로 변환합니다.
    """
    logger.info("음성 세그먼트 생성 시작")
    
    segments = []
    scripts = []
    
    # 1. process_voice_query에서 명시적으로 전달된 last_response 확인
    if last_response is not None:
        response = last_response
        logger.info(f"last_response 매개변수 사용 - ID: {response.response_id}, 타입: {type(response)}")
    # 2. 없으면 state에서 가져오기 시도
    else:
        response = getattr(state, 'last_response', None)
        
        # last_response 디버깅 정보
        if response:
            logger.info(f"state.last_response 찾음 - ID: {response.response_id}, 타입: {type(response)}")
            logger.info(f"응답 텍스트 길이: {len(response.response_text)}")
        else:
            logger.warning("last_response 매개변수와 state.last_response 모두 None입니다")
            # 로깅을 위해 상태 객체의 모든 속성 출력
            logger.debug(f"상태 객체 속성: {dir(state)}")
    
    if response is None:
        logger.warning("응답이 없어 기본 메시지를 사용합니다")
        # 기본 응답 생성
        default_text = "죄송합니다. 요청에 대한 응답을 생성할 수 없습니다."
        segments.append(VoiceSegment(
            segment_id=str(uuid4()),
            text=default_text,
            duration_seconds=2.0,
            segment_type="error"
        ))
        scripts.append(default_text)
        state.voice_segments = segments
        
        # 음성 스크립트도 추가
        state.voice_scripts.append(default_text)
        logger.info("기본 오류 메시지로 세그먼트 생성 완료")
        
        return {"segments": segments, "scripts": [default_text]}
    
    # 인사말 세그먼트
    greeting = "안녕하세요, 건강 관리 AI 주치의입니다."
    segments.append(VoiceSegment(
        segment_id=str(uuid4()),
        text=greeting,
        duration_seconds=2.0,
        segment_type="greeting"
    ))
    
    try:
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
        
        # 음성 스크립트 생성 및 추가
        full_script = f"{greeting}\n{response.response_text}\n{closing_text}"
        scripts.append(full_script)
        state.voice_scripts = scripts
        
        # 딕셔너리 형태로 명확하게 반환
        result = {
            "segments": segments,
            "scripts": scripts,
            "segment_count": len(segments)
        }
        logger.info(f"create_voice_segments 함수 반환 - 결과 타입: {type(result)}")
        return result
        
    except AttributeError as e:
        logger.error(f"응답 객체에서 속성 접근 중 오류 발생: {str(e)}")
        
        # 오류 메시지 세그먼트
        error_text = "죄송합니다. 음성 응답을 처리하는 중 오류가 발생했습니다."
        segments.append(VoiceSegment(
            segment_id=str(uuid4()),
            text=error_text,
            duration_seconds=2.5,
            segment_type="error"
        ))
        
        # 상태에 세그먼트 저장
        state.voice_segments = segments
        
        # 음성 스크립트 생성 및 추가
        error_script = f"{greeting}\n{error_text}"
        scripts.append(error_script)
        state.voice_scripts = scripts
        
        # 딕셔너리 형태로 명확하게 반환
        result = {
            "segments": segments,
            "scripts": scripts,
            "segment_count": len(segments),
            "error": str(e)
        }
        logger.info(f"create_voice_segments 함수 오류 반환 - 결과 타입: {type(result)}")
        return result 