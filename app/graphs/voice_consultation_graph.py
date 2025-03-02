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
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("process_voice_query", process_voice_query)
    graph.add_node("create_voice_segments", create_voice_segments)
    
    # process_voice_query에서 last_response를 설정하고, create_voice_segments에서 이를 사용하도록 함
    def route_to_voice_segments(state: UserState) -> str:
        # state.last_response를 사용하여 create_voice_segments 함수 호출
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