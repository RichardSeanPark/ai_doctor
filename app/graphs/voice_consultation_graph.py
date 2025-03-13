from typing import Annotated, Any, Dict, List

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.voice_data import VoiceQuery, VoiceResponse, ConsultationSummary, VoiceSegment
from app.nodes.voice_consultation_nodes import (
    process_voice_query,
    conduct_voice_consultation,
    create_voice_segments
)

def create_voice_query_graph() -> StateGraph:
    """
    음성 질의 처리를 위한 LangGraph 생성
    """
    from langchain.schema.runnable import RunnablePassthrough
    
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("process_voice_query", process_voice_query)
    
    # create_voice_segments 노드는 process_voice_query의 반환값을 받을 수 있도록 설정
    async def create_voice_segments_wrapper(state, config=None, last_response=None):
        """create_voice_segments 함수를 래핑하여 last_response 매개변수를 전달"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 더 자세한 로깅
        logger.info(f"create_voice_segments_wrapper 호출 - last_response 존재: {last_response is not None}")
        
        if last_response is not None:
            logger.info(f"last_response 타입: {type(last_response)}")
            if hasattr(last_response, 'response_id'):
                logger.info(f"last_response.response_id: {last_response.response_id}")
            else:
                logger.info(f"last_response 속성: {dir(last_response)}")
        
        # config 내용 로깅
        logger.info(f"config 내용: {config}")
        
        # state 객체 검증
        if hasattr(state, 'last_response') and state.last_response is not None:
            logger.info(f"state.last_response 존재: {state.last_response.response_id}")
        
        # create_voice_segments 함수 호출 시 last_response 전달
        result = await create_voice_segments(state, config, last_response)
        logger.info(f"create_voice_segments 함수 결과 타입: {type(result)}")
        if isinstance(result, dict):
            logger.info(f"result 키: {result.keys()}")
            
            # 결과 필드 검증
            for key in ['segments', 'scripts', 'segment_count']:
                if key in result:
                    if key == 'segments':
                        logger.info(f"segments 존재: {len(result['segments'])}개")
                    elif key == 'scripts':
                        logger.info(f"scripts 존재: {len(result['scripts'])}개")
                    elif key == 'segment_count':
                        logger.info(f"segment_count: {result['segment_count']}")
                else:
                    logger.warning(f"결과에 {key} 키가 없습니다")
            
            # segments 또는 scripts가 없는 경우 디버깅
            if 'segments' not in result or 'scripts' not in result:
                logger.warning("result에 필수 필드가 없습니다. 결과 내용:")
                for k, v in result.items():
                    if isinstance(v, list):
                        logger.warning(f"  {k}: (리스트, 길이: {len(v)})")
                    else:
                        logger.warning(f"  {k}: {v}")
        
        # 상태 객체에 스크립트와 세그먼트가 설정되었는지 검증
        if hasattr(state, 'voice_scripts'):
            logger.info(f"state.voice_scripts 길이: {len(state.voice_scripts) if state.voice_scripts else 0}")
        if hasattr(state, 'voice_segments'):
            logger.info(f"state.voice_segments 길이: {len(state.voice_segments) if state.voice_segments else 0}")
        
        # 결과를 반환하기 전 결과 타입 로깅
        logger.info(f"create_voice_segments_wrapper에서 반환하는 결과 타입: {type(result)}")
        
        # LangGraph에서 반환하는 최종 결과
        return result
    
    graph.add_node("create_voice_segments", create_voice_segments_wrapper)
    
    # process_voice_query에서 last_response를 설정하고, 
    # create_voice_segments에서 이를 사용하도록 라우팅합니다.
    def route_to_voice_segments(state: UserState) -> str:
        """라우팅 함수"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 디버깅을 위한 상태 객체 검사
        logger.debug(f"라우팅: 상태 객체 속성: {dir(state)}")
        
        # 상태 변수에서 last_response 확인
        if hasattr(state, 'last_response') and state.last_response is not None:
            response = state.last_response
            logger.info(f"라우팅: last_response 존재함 - ID: {response.response_id}")
            logger.info(f"응답 텍스트 시작 부분: {response.response_text[:50]}...")
        else:
            logger.warning(f"라우팅: state.last_response가 없거나 None 값임")
            # 상태 객체 디버깅 정보
            logger.debug(f"상태 객체 속성: {dir(state)}")
        
        # 항상 create_voice_segments로 이동
        return "create_voice_segments"
    
    # 엣지 설정 - process_voice_query에서 create_voice_segments로 이동
    graph.add_conditional_edges(
        "process_voice_query",
        route_to_voice_segments
    )
    graph.add_edge("create_voice_segments", END)
    
    # 시작 노드 설정
    graph.set_entry_point("process_voice_query")
    
    # 그래프 컴파일
    return graph.compile()

def create_voice_consultation_graph() -> StateGraph:
    """
    음성 상담 세션을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("conduct_voice_consultation", conduct_voice_consultation)
    
    # voice_consultation_node를 수정하여 config에서 직접 consultation_data를 사용하도록 설정
    # 따라서 여기서는 기본적인 엣지와 진입점만 설정합니다
    
    # 엣지 설정
    graph.add_edge("conduct_voice_consultation", END)
    
    # 시작 노드 설정
    graph.set_entry_point("conduct_voice_consultation")
    
    # 그래프 컴파일
    return graph.compile() 