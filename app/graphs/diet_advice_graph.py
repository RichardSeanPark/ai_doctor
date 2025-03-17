"""
식단 조언 그래프 구현
"""
from typing import Annotated, Any, Dict, List
import logging
import traceback

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.diet_plan import DietSpecialistResponse
from app.nodes.diet_advice_nodes import provide_diet_advice, provide_diet_specialist_advice, route_diet_request

# 로거 설정
logger = logging.getLogger(__name__)

def create_diet_advice_graph() -> StateGraph:
    """
    식단 조언을 위한 LangGraph 생성
    """
    logger.info("[DIET_GRAPH] 식단 조언 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의 - 딕셔너리 사용
        graph = StateGraph(Dict)
        logger.debug("[DIET_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[DIET_GRAPH] 'route_diet_request' 노드 추가 시작")
        graph.add_node("route_diet_request", route_diet_request)
        logger.debug("[DIET_GRAPH] 'route_diet_request' 노드 추가 완료")
        
        logger.debug("[DIET_GRAPH] 'provide_diet_advice' 노드 추가 시작")
        graph.add_node("provide_diet_advice", provide_diet_advice)
        logger.debug("[DIET_GRAPH] 'provide_diet_advice' 노드 추가 완료")
        
        logger.debug("[DIET_GRAPH] 'provide_diet_specialist_advice' 노드 추가 시작")
        graph.add_node("provide_diet_specialist_advice", provide_diet_specialist_advice)
        logger.debug("[DIET_GRAPH] 'provide_diet_specialist_advice' 노드 추가 완료")
        
        # 라우팅 함수 정의
        def router(state):
            logger.debug(f"[DIET_GRAPH] 라우팅 함수 호출: {state}")
            if "route" in state and state["route"] == "provide_diet_specialist_advice":
                logger.debug("[DIET_GRAPH] 다이어트 전문가 조언으로 라우팅")
                return "provide_diet_specialist_advice"
            else:
                logger.debug("[DIET_GRAPH] 일반 식단 조언으로 라우팅")
                return "provide_diet_advice"
        
        # 엣지 설정
        logger.debug("[DIET_GRAPH] 엣지 설정 시작")
        graph.add_conditional_edges("route_diet_request", router, {
            "provide_diet_advice": "provide_diet_advice",
            "provide_diet_specialist_advice": "provide_diet_specialist_advice"
        })
        
        graph.add_edge("provide_diet_advice", END)
        graph.add_edge("provide_diet_specialist_advice", END)
        logger.debug("[DIET_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[DIET_GRAPH] 시작 노드 설정")
        graph.set_entry_point("route_diet_request")
        
        # 그래프 컴파일
        logger.debug("[DIET_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[DIET_GRAPH] 식단 조언 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[DIET_GRAPH] 식단 조언 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[DIET_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise 