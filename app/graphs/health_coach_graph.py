from typing import Annotated, Any, Dict, List
import logging
import traceback

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.health_coach_data import HealthCoachResponse, WeeklyHealthReport
from app.nodes.health_coach_nodes import provide_health_advice, generate_weekly_report

# 로거 설정
logger = logging.getLogger(__name__)

def create_health_coach_graph() -> StateGraph:
    """
    건강 코치 조언을 위한 LangGraph 생성
    """
    logger.info("[HEALTH_COACH_GRAPH] 건강 코치 조언 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의
        graph = StateGraph(UserState)
        logger.debug("[HEALTH_COACH_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[HEALTH_COACH_GRAPH] 'provide_health_advice' 노드 추가 시작")
        graph.add_node("provide_health_advice", provide_health_advice)
        logger.debug("[HEALTH_COACH_GRAPH] 'provide_health_advice' 노드 추가 완료")
        
        # 엣지 설정
        logger.debug("[HEALTH_COACH_GRAPH] 엣지 설정 시작")
        graph.add_edge("provide_health_advice", END)
        logger.debug("[HEALTH_COACH_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[HEALTH_COACH_GRAPH] 시작 노드 설정")
        graph.set_entry_point("provide_health_advice")
        
        # 그래프 컴파일
        logger.debug("[HEALTH_COACH_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[HEALTH_COACH_GRAPH] 건강 코치 조언 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[HEALTH_COACH_GRAPH] 건강 코치 조언 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[HEALTH_COACH_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise

def create_weekly_report_graph() -> StateGraph:
    """
    주간 건강 리포트 생성을 위한 LangGraph 생성
    """
    logger.info("[HEALTH_COACH_GRAPH] 주간 건강 리포트 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의
        graph = StateGraph(UserState)
        logger.debug("[HEALTH_COACH_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[HEALTH_COACH_GRAPH] 'generate_weekly_report' 노드 추가 시작")
        graph.add_node("generate_weekly_report", generate_weekly_report)
        logger.debug("[HEALTH_COACH_GRAPH] 'generate_weekly_report' 노드 추가 완료")
        
        # 엣지 설정
        logger.debug("[HEALTH_COACH_GRAPH] 엣지 설정 시작")
        graph.add_edge("generate_weekly_report", END)
        logger.debug("[HEALTH_COACH_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[HEALTH_COACH_GRAPH] 시작 노드 설정")
        graph.set_entry_point("generate_weekly_report")
        
        # 그래프 컴파일
        logger.debug("[HEALTH_COACH_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[HEALTH_COACH_GRAPH] 주간 건강 리포트 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[HEALTH_COACH_GRAPH] 주간 건강 리포트 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[HEALTH_COACH_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise 