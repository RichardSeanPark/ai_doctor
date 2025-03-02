from typing import Annotated, Any, Dict, List

from langgraph.graph import StateGraph, END

from app.models.notification import UserState
from app.models.health_data import DietAnalysis, DietEntry
from app.models.diet_plan import MealRecommendation
from app.nodes.diet_nodes import analyze_diet, provide_recommendations, process_food_image
from app.nodes.food_image_nodes import (
    analyze_food_image, 
    calculate_nutrition, 
    generate_diet_feedback,
    create_diet_image_summary
)

def create_diet_analysis_graph() -> StateGraph:
    """
    식단 분석 및 추천을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("analyze_diet", analyze_diet)
    graph.add_node("provide_recommendations", provide_recommendations)
    
    # 엣지 설정 - 항상 analyze_diet에서 provide_recommendations로 이동
    def route_after_analysis(state: UserState) -> str:
        return "provide_recommendations"
    
    # 조건부 엣지 추가
    graph.add_conditional_edges(
        "analyze_diet",
        route_after_analysis
    )
    graph.add_edge("provide_recommendations", END)
    
    # 시작 노드 설정
    graph.set_entry_point("analyze_diet")
    
    # 그래프 컴파일
    return graph.compile()

def create_food_image_graph() -> StateGraph:
    """
    음식 이미지 분석을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("analyze_food_image", analyze_food_image)
    graph.add_node("calculate_nutrition", calculate_nutrition)
    graph.add_node("generate_diet_feedback", generate_diet_feedback)
    graph.add_node("create_diet_image_summary", create_diet_image_summary)
    
    # 이미지 분석 결과 라우팅 함수
    def route_after_image_analysis(state: UserState) -> str:
        if not hasattr(state, 'recognition_result') or state.recognition_result is None:
            return END
        return "calculate_nutrition"
    
    # 영양소 분석 라우팅 함수
    def route_after_nutrition_calculation(state: UserState) -> str:
        if not hasattr(state, 'nutrition_analysis') or state.nutrition_analysis is None:
            return END
        return "generate_diet_feedback"
    
    # 피드백 라우팅 함수
    def route_after_feedback(state: UserState) -> str:
        if not hasattr(state, 'diet_entry') or state.diet_entry is None:
            return END
        return "create_diet_image_summary"
    
    # 조건부 엣지 추가
    graph.add_conditional_edges(
        "analyze_food_image",
        route_after_image_analysis
    )
    
    graph.add_conditional_edges(
        "calculate_nutrition",
        route_after_nutrition_calculation
    )
    
    graph.add_conditional_edges(
        "generate_diet_feedback",
        route_after_feedback
    )
    
    graph.add_edge("create_diet_image_summary", END)
    
    # 시작 노드 설정
    graph.set_entry_point("analyze_food_image")
    
    # 그래프 컴파일
    return graph.compile() 