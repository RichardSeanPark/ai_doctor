from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import logging
import os

from langgraph.graph import END

from app.models.notification import UserState, AndroidNotification, NotificationResult
from app.agents.agent_config import get_notification_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def send_android_notification(state: UserState) -> NotificationResult:
    logger.info("안드로이드 알림 전송 시작")
    
    # 알림 데이터 가져오기
    notification = state.current_notification
    if not notification:
        logger.warning("전송할 알림이 없습니다")
        return END(NotificationResult(
            notification_id=str(uuid4()),
            timestamp=datetime.now(),
            status="failed",
            message="전송할 알림이 없습니다."
        ))
    
    # 실제로는 여기서 FCM 또는 다른 푸시 알림 서비스 API를 호출할 것입니다.
    # 여기서는 간단한 시뮬레이션만 수행합니다.
    
    user_id = state.user_profile.get("user_id", "unknown")
    device_token = state.user_profile.get("device_token", "")
    
    if not device_token:
        logger.warning(f"사용자 기기 토큰이 없습니다 - 사용자 ID: {user_id}")
        return END(NotificationResult(
            notification_id=str(uuid4()),
            timestamp=datetime.now(),
            status="failed",
            message="사용자 기기 토큰이 없습니다."
        ))
    
    # 알림 전송 시뮬레이션
    logger.info(f"알림 전송 성공 - 사용자 ID: {user_id}, 제목: {notification.title}")
    
    # 결과 생성
    result = NotificationResult(
        notification_id=str(uuid4()),
        timestamp=datetime.now(),
        status="success",
        message="알림이 성공적으로 전송되었습니다."
    )
    
    return END(result)

async def schedule_notification(state: UserState, schedule_data: Dict[str, Any]) -> AndroidNotification:
    logger.info("알림 스케줄링 시작")
    
    # 스케줄 데이터 확인
    schedule_time = schedule_data.get("schedule_time")
    notification_type = schedule_data.get("notification_type", "reminder")
    
    if not schedule_time:
        logger.warning("스케줄 시간이 지정되지 않았습니다")
        return END(AndroidNotification(
            title="스케줄링 오류",
            body="알림 스케줄링에 필요한 시간 정보가 없습니다.",
            priority="normal"
        ))
    
    # 알림 에이전트 생성
    agent = get_notification_agent()
    
    # 사용자 정보 준비
    user_profile = state.user_profile
    user_name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}"
    
    # 알림 내용 생성 요청
    prompt = f"""
    다음 사용자를 위한 {notification_type} 알림을 생성해주세요:
    
    사용자 정보:
    - 이름: {user_name}
    - 나이: {user_profile.get('age', '알 수 없음')}
    - 성별: {user_profile.get('gender', '알 수 없음')}
    
    알림 유형: {notification_type}
    예약 시간: {schedule_time}
    
    알림 제목과 내용을 생성해주세요. 내용은 간결하고 동기부여가 되어야 합니다.
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "title": "알림 제목",
        "body": "알림 내용",
        "priority": "normal 또는 high"
    }}
    """
    
    # 에이전트 실행 및 결과 파싱
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 문자열 추출 및 파싱
    import json
    import re
    
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"알림 생성 완료 - 제목: {data['title']}")
    
    # 알림 생성
    notification = AndroidNotification(
        title=data["title"],
        body=data["body"],
        priority=data["priority"]
    )
    
    # 알림 저장
    state.notifications.append(notification)
    state.current_notification = notification
    
    return END(notification)

async def create_motivational_notification(state: UserState) -> AndroidNotification:
    logger.info("동기부여 알림 생성 시작")
    
    # 알림 에이전트 생성
    agent = get_notification_agent()
    
    # 사용자 정보 준비
    user_profile = state.user_profile
    user_name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}"
    
    # 사용자 목표 정보 준비
    goals = user_profile.get("goals", [])
    goal_str = "건강 관리" if not goals else f"{goals[0].get('goal_type')} (목표값: {goals[0].get('target_value')})"
    
    # 진행 상황 정보 준비
    progress = state.progress_data
    progress_percentage = progress.get("percentage", 0) if progress else 0
    recent_activities = progress.get("recent_activities", []) if progress else []
    activities_str = "없음" if not recent_activities else ", ".join(recent_activities[:3])
    
    # 알림 내용 생성 요청
    prompt = f"""
    다음 사용자를 위한 동기부여 알림을 생성해주세요:
    
    사용자 정보:
    - 이름: {user_name}
    - 목표: {goal_str}
    - 현재 진행률: {progress_percentage}%
    - 최근 활동: {activities_str}
    
    동기부여가 되는 알림 제목과 내용을 생성해주세요. 내용은 간결하고 긍정적이어야 합니다.
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "title": "알림 제목",
        "body": "알림 내용",
        "priority": "normal"
    }}
    """
    
    # 에이전트 실행 및 결과 파싱
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 문자열 추출 및 파싱
    import json
    import re
    
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"동기부여 알림 생성 완료 - 제목: {data['title']}")
    
    # 알림 생성
    notification = AndroidNotification(
        title=data["title"],
        body=data["body"],
        priority=data["priority"]
    )
    
    # 알림 저장
    state.notifications.append(notification)
    state.current_notification = notification
    
    return END(notification) 