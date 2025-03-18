from typing import Annotated, Any, Dict, List, TypedDict
import logging
import traceback

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.exercise_data import ExerciseRecommendation
from app.nodes.exercise_nodes import recommend_exercise_plan

# 로거 설정
logger = logging.getLogger(__name__)

# 상태 타입 정의
class GraphState(TypedDict):
    user_id: str
    user_profile: Dict[str, Any]
    query_text: str
    exercise_recommendation: ExerciseRecommendation

def create_exercise_recommendation_graph() -> StateGraph:
    """
    운동 추천을 위한 LangGraph 생성
    """
    logger.info("[EXERCISE_GRAPH] 운동 추천 그래프 생성 시작")
    
    try:
        # 그래프의 상태 정의
        graph = StateGraph(GraphState)
        logger.debug("[EXERCISE_GRAPH] 상태 그래프 초기화 완료")
        
        # 노드 추가
        logger.debug("[EXERCISE_GRAPH] 'recommend_exercise_plan' 노드 추가 시작")
        graph.add_node("recommend_exercise_plan", recommend_exercise_plan)
        logger.debug("[EXERCISE_GRAPH] 'recommend_exercise_plan' 노드 추가 완료")
        
        # 엣지 설정
        logger.debug("[EXERCISE_GRAPH] 엣지 설정 시작")
        graph.add_edge("recommend_exercise_plan", END)
        logger.debug("[EXERCISE_GRAPH] 엣지 설정 완료")
        
        # 시작 노드 설정
        logger.debug("[EXERCISE_GRAPH] 시작 노드 설정")
        graph.set_entry_point("recommend_exercise_plan")
        
        # 그래프 컴파일
        logger.debug("[EXERCISE_GRAPH] 그래프 컴파일 시작")
        compiled_graph = graph.compile()
        logger.info("[EXERCISE_GRAPH] 운동 추천 그래프 생성 완료")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"[EXERCISE_GRAPH] 운동 추천 그래프 생성 중 오류 발생: {str(e)}")
        logger.error(f"[EXERCISE_GRAPH] 오류 상세: {traceback.format_exc()}")
        raise 