"""
식단 조언 그래프 구현
"""
from typing import Annotated, Any, Dict, List
import logging
import traceback

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.diet_plan import DietAdviceResponse
from app.nodes.diet_advice_nodes import provide_diet_advice

# 로거 설정
logger = logging.getLogger(__name__)

def create_diet_advice_graph() -> StateGraph:
    """
    식단 조언을 위한 LangGraph 생성
    """
    logger.info("[DIET_GRAPH] 식단 조언 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의
        graph = StateGraph(UserState)
        logger.debug("[DIET_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[DIET_GRAPH] 'provide_diet_advice' 노드 추가 시작")
        graph.add_node("provide_diet_advice", provide_diet_advice)
        logger.debug("[DIET_GRAPH] 'provide_diet_advice' 노드 추가 완료")
        
        # 엣지 설정
        logger.debug("[DIET_GRAPH] 엣지 설정 시작")
        graph.add_edge("provide_diet_advice", END)
        logger.debug("[DIET_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[DIET_GRAPH] 시작 노드 설정")
        graph.set_entry_point("provide_diet_advice")
        
        # 그래프 컴파일
        logger.debug("[DIET_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[DIET_GRAPH] 식단 조언 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[DIET_GRAPH] 식단 조언 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[DIET_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise 