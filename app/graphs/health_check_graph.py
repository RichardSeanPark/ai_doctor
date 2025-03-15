from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.health_data import HealthAssessment
from app.nodes.health_check_nodes import (
    analyze_health_metrics, 
    alert_health_concern,
    analyze_symptoms,
    notify_doctor
)

# 언패킹 오류 해결을 위한 래퍼 함수
async def analyze_health_metrics_wrapper(state: UserState) -> HealthAssessment:
    """
    analyze_health_metrics를 래핑하여 튜플 반환 오류를 해결합니다.
    """
    try:
        result = await analyze_health_metrics(state)
        # 결과가 튜플인 경우 첫 번째 요소만 반환
        if isinstance(result, tuple) and len(result) > 0:
            return result[0]
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"랩퍼 함수 오류: {str(e)}")
        raise e

def create_health_metrics_graph() -> StateGraph:
    """
    건강 지표 분석을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가 (래퍼 함수 사용)
    graph.add_node("analyze_health_metrics", analyze_health_metrics_wrapper)
    graph.add_node("alert_health_concern", alert_health_concern)
    
    # 조건부 엣지 설정
    def route_after_analysis(state: UserState) -> str:
        if state.health_assessment and state.health_assessment.has_concerns:
            return "alert_health_concern"
        else:
            return END
    
    # 엣지 설정
    graph.add_conditional_edges(
        "analyze_health_metrics",
        route_after_analysis
    )
    graph.add_edge("alert_health_concern", END)
    
    # 시작 노드 설정
    graph.set_entry_point("analyze_health_metrics")
    
    # 그래프 컴파일
    return graph.compile()

def create_symptom_analysis_graph() -> StateGraph:
    """
    증상 분석을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("analyze_symptoms", analyze_symptoms)
    graph.add_node("notify_doctor", notify_doctor)
    
    # 조건부 엣지 설정 (간략화된 버전)
    def route_after_symptom_analysis(state: UserState) -> str:
        # 여기서는 증상이 심각하고 의사 알림이 필요한지 확인
        # 실제 구현에서는 더 복잡한 로직이 들어갈 수 있습니다
        if state.health_assessment and state.health_assessment.health_status == "경고" and state.health_assessment.has_concerns:
            return "notify_doctor"
        else:
            return END
    
    # 엣지 설정
    graph.add_conditional_edges(
        "analyze_symptoms",
        route_after_symptom_analysis
    )
    graph.add_edge("notify_doctor", END)
    
    # 시작 노드 설정
    graph.set_entry_point("analyze_symptoms")
    
    # 그래프 컴파일
    return graph.compile() 