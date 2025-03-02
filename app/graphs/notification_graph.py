from typing import Annotated, Any, Dict, List

from langgraph.graph import StateGraph, END

from app.models.notification import UserState, AndroidNotification, NotificationResult
from app.nodes.android_notification_nodes import (
    send_android_notification,
    schedule_notification,
    create_motivational_notification
)

def create_notification_graph() -> StateGraph:
    """
    안드로이드 알림 전송을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("send_android_notification", send_android_notification)
    
    # 엣지 설정
    graph.add_edge("send_android_notification", END)
    
    # 시작 노드 설정
    graph.set_entry_point("send_android_notification")
    
    # 그래프 컴파일
    return graph.compile()

def create_schedule_notification_graph() -> StateGraph:
    """
    알림 스케줄링을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("schedule_notification", schedule_notification)
    
    # 엣지 설정
    graph.add_edge("schedule_notification", END)
    
    # 시작 노드 설정
    graph.set_entry_point("schedule_notification")
    
    # 그래프 컴파일
    return graph.compile()

def create_motivational_notification_graph() -> StateGraph:
    """
    동기부여 알림 생성을 위한 LangGraph 생성
    """
    # 그래프의 상태 정의
    graph = StateGraph(UserState)
    
    # 노드 추가
    graph.add_node("create_motivational_notification", create_motivational_notification)
    graph.add_node("send_android_notification", send_android_notification)
    
    # 엣지 설정
    graph.add_edge("create_motivational_notification", "send_android_notification")
    graph.add_edge("send_android_notification", END)
    
    # 시작 노드 설정
    graph.set_entry_point("create_motivational_notification")
    
    # 그래프 컴파일
    return graph.compile() 