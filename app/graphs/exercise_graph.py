from typing import Annotated, Any, Dict, List
import logging
import traceback

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation, ExerciseRecord
from app.nodes.exercise_nodes import recommend_exercise, record_exercise

# 로거 설정
logger = logging.getLogger(__name__)

def create_exercise_recommendation_graph() -> StateGraph:
    """
    운동 추천을 위한 LangGraph 생성
    """
    logger.info("[EXERCISE_GRAPH] 운동 추천 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의
        graph = StateGraph(UserState)
        logger.debug("[EXERCISE_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[EXERCISE_GRAPH] 'recommend_exercise' 노드 추가 시작")
        graph.add_node("recommend_exercise", recommend_exercise)
        logger.debug("[EXERCISE_GRAPH] 'recommend_exercise' 노드 추가 완료")
        
        # 엣지 설정
        logger.debug("[EXERCISE_GRAPH] 엣지 설정 시작")
        graph.add_edge("recommend_exercise", END)
        logger.debug("[EXERCISE_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[EXERCISE_GRAPH] 시작 노드 설정")
        graph.set_entry_point("recommend_exercise")
        
        # 그래프 컴파일
        logger.debug("[EXERCISE_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[EXERCISE_GRAPH] 운동 추천 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[EXERCISE_GRAPH] 운동 추천 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[EXERCISE_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise

def create_exercise_record_graph() -> StateGraph:
    """
    운동 기록을 위한 LangGraph 생성
    """
    logger.info("[EXERCISE_GRAPH] 운동 기록 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의
        graph = StateGraph(UserState)
        logger.debug("[EXERCISE_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[EXERCISE_GRAPH] 'record_exercise' 노드 추가 시작")
        graph.add_node("record_exercise", record_exercise)
        logger.debug("[EXERCISE_GRAPH] 'record_exercise' 노드 추가 완료")
        
        # 엣지 설정
        logger.debug("[EXERCISE_GRAPH] 엣지 설정 시작")
        graph.add_edge("record_exercise", END)
        logger.debug("[EXERCISE_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[EXERCISE_GRAPH] 시작 노드 설정")
        graph.set_entry_point("record_exercise")
        
        # 그래프 컴파일
        logger.debug("[EXERCISE_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[EXERCISE_GRAPH] 운동 기록 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[EXERCISE_GRAPH] 운동 기록 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[EXERCISE_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise 