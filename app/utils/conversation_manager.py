"""
대화 세션 및 메시지 관리를 위한 매니저 모듈
"""

import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

from app.db.conversation_dao import ConversationDAO

logger = logging.getLogger(__name__)

class ConversationManager:
    """대화 세션 및 메시지 관리를 위한 매니저 클래스"""
    
    def __init__(self):
        """ConversationManager 초기화"""
        self.conversation_dao = ConversationDAO()
        self.active_sessions = {}  # user_id -> {conversation_id, last_activity, ...}
    
    def get_or_create_session(self, user_id: str, session_type: str = "general") -> Dict[str, Any]:
        """
        사용자의 활성 세션을 가져오거나 없으면 새 세션을 생성합니다.
        
        Args:
            user_id: 사용자 ID
            session_type: 세션 유형 (general, health 등)
            
        Returns:
            세션 정보 (conversation_id 포함)
        """
        # 활성 세션 가져오기
        active_session = self.conversation_dao.get_active_user_session(user_id, session_type)
        
        # 활성 세션이 없으면 새로 생성
        if not active_session:
            conversation_id = self.conversation_dao.create_conversation_session(user_id, session_type)
            active_session = self.conversation_dao.get_session_by_id(conversation_id)
            logger.info(f"새 대화 세션 생성: {conversation_id} (사용자: {user_id}, 유형: {session_type})")
        else:
            # 세션 활동 시간 업데이트
            self.conversation_dao.update_session_activity(active_session['conversation_id'])
            logger.info(f"기존 대화 세션 사용: {active_session['conversation_id']} (사용자: {user_id})")
        
        return active_session
    
    def record_user_message(self, user_id: str, message_text: str, conversation_id: str) -> str:
        """
        사용자 메시지를 기록합니다.
        
        Args:
            user_id: 사용자 ID
            message_text: 메시지 내용
            conversation_id: 대화 세션 ID
            
        Returns:
            메시지 ID
        """
        message_id = self.conversation_dao.add_message(
            conversation_id=conversation_id,
            sender_type="user",
            message_text=message_text,
            metadata={"user_id": user_id}
        )
        logger.info(f"사용자 메시지 기록: {message_id} (세션: {conversation_id})")
        return message_id
    
    def record_assistant_message(self, user_id: str, message_text: str, conversation_id: str, 
                               is_important: bool = False, metadata: Dict[str, Any] = None) -> str:
        """
        어시스턴트 메시지를 기록합니다.
        
        Args:
            user_id: 사용자 ID
            message_text: 메시지 내용
            conversation_id: 대화 세션 ID
            is_important: 중요 메시지 여부
            metadata: 추가 메타데이터
            
        Returns:
            메시지 ID
        """
        # 기본 메타데이터 설정
        meta = metadata or {}
        meta.update({
            "user_id": user_id,
            "is_important": is_important
        })
        
        message_id = self.conversation_dao.add_message(
            conversation_id=conversation_id,
            sender_type="assistant",
            message_text=message_text,
            metadata=meta
        )
        logger.info(f"어시스턴트 메시지 기록: {message_id} (세션: {conversation_id}, 중요: {is_important})")
        return message_id
    
    def get_context_for_llm(self, conversation_id: str, message_limit: int = 10) -> List[Dict[str, Any]]:
        """
        LLM에 제공할 대화 컨텍스트를 가져옵니다.
        
        Args:
            conversation_id: 대화 세션 ID
            message_limit: 가져올 최대 메시지 수
            
        Returns:
            메시지 목록 (시간순)
        """
        messages = self.conversation_dao.get_messages(conversation_id, limit=message_limit)
        
        # LLM에 적합한 형식으로 변환
        context = []
        for msg in messages:
            role = "user" if msg["sender_type"] == "user" else "assistant"
            context.append({
                "role": role,
                "content": msg["message_text"]
            })
        
        return context
    
    def generate_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """
        대화 세션의 요약을 생성합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            생성된 요약 ID
        """
        try:
            # 메시지 가져오기
            messages = self.conversation_dao.get_messages(conversation_id, limit=100)
            if not messages:
                logger.warning(f"요약할 메시지가 없습니다: {conversation_id}")
                return None
            
            # 메시지 텍스트 추출
            conversation_text = ""
            for msg in messages:
                prefix = "사용자: " if msg["sender_type"] == "user" else "어시스턴트: "
                conversation_text += f"{prefix}{msg['message_text']}\n\n"
            
            # 주요 주제 추출
            health_entities = self._extract_health_entities_with_llm(conversation_text)
            
            # 요약 생성
            summary_text = f"이 대화에서는 다음 주제가 논의되었습니다: {', '.join(health_entities.keys())}"
            
            # 요약 저장
            summary_id = self.conversation_dao.add_summary(
                conversation_id=conversation_id,
                summary_text=summary_text,
                metadata={
                    "health_entities": health_entities,
                    "message_count": len(messages)
                }
            )
            
            logger.info(f"대화 요약 생성 완료: {summary_id} (세션: {conversation_id})")
            return summary_id
            
        except Exception as e:
            logger.error(f"대화 요약 생성 오류: {str(e)}")
            return None
    
    def _extract_health_entities_with_llm(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 건강 관련 엔티티를 추출합니다.
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            추출된 엔티티 정보
        """
        # 실제 구현에서는 LLM을 사용하여 엔티티를 추출할 수 있습니다.
        # 현재는 간단히 키워드 기반으로 구현합니다.
        entities = {}
        
        # 건강 관련 키워드 사전
        keywords = {
            "혈압": ["혈압", "blood pressure", "수축기", "이완기", "systolic", "diastolic"],
            "체중": ["체중", "몸무게", "weight", "kg", "킬로그램"],
            "혈당": ["혈당", "당뇨", "blood sugar", "glucose"],
            "심장": ["심장", "heart", "심박수", "heart rate"],
            "식단": ["식단", "음식", "food", "diet", "meal", "nutrition"],
            "운동": ["운동", "exercise", "활동", "걷기", "달리기", "스포츠"],
            "수면": ["수면", "잠", "sleep", "불면증", "insomnia"],
            "약물": ["약", "약물", "medicine", "medication", "drug"]
        }
        
        # 키워드 기반 엔티티 추출
        for category, terms in keywords.items():
            for term in terms:
                if term in text.lower():
                    entities[category] = True
                    break
        
        # 결과 변환
        result = {}
        for category in entities:
            result[category] = {"detected": True, "importance": "medium"}
        
        return result 