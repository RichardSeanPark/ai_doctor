import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from app.db.database import Database

logger = logging.getLogger(__name__)

class ConversationDAO:
    """대화 세션 및 메시지 관리를 위한 Data Access Object"""
    
    def __init__(self, db=None):
        """ConversationDAO 초기화"""
        self.db = db or Database()
    
    def create_conversation_session(self, user_id: str, session_type: str = "general", session_name: str = None) -> str:
        """
        새로운 대화 세션을 생성합니다.
        
        Args:
            user_id: 사용자 ID
            session_type: 세션 유형 (general, health, diet 등)
            session_name: 세션 이름 (없으면 자동 생성)
            
        Returns:
            세션 ID
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 현재 시간
            created_at = datetime.now().isoformat()
            
            # 세션 이름이 없으면 자동 생성
            if not session_name:
                session_name = f"{session_type.capitalize()} {created_at[:10]}"
            
            # 세션 생성
            cursor.execute('''
                INSERT INTO conversation_sessions (user_id, session_type, session_name, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (user_id, session_type, session_name, created_at))
            
            # 새로 생성된 세션의 ID 가져오기
            conversation_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"새로운 대화 세션 생성: {conversation_id}, 사용자: {user_id}")
            
            return str(conversation_id)
            
        except Exception as e:
            logger.error(f"대화 세션 생성 중 오류: {str(e)}")
            if conn:
                conn.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_active_sessions(self, user_id: str, session_type: str = None) -> List[Dict[str, Any]]:
        """
        사용자의 활성 대화 세션 목록을 가져옵니다.
        
        Args:
            user_id: 사용자 ID
            session_type: 세션 유형으로 필터링 (선택적)
            
        Returns:
            활성 대화 세션 목록
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            query = '''
                SELECT conversation_id, user_id, session_type, session_name, created_at, updated_at, is_active
                FROM conversation_sessions
                WHERE user_id = ? AND is_active = 1
            '''
            
            params = [user_id]
            
            if session_type:
                query += " AND session_type = ?"
                params.append(session_type)
                
            query += " ORDER BY updated_at DESC, created_at DESC"
            
            cursor.execute(query, params)
            
            sessions = []
            for row in cursor.fetchall():
                session = {
                    'conversation_id': str(row[0]),
                    'user_id': row[1],
                    'session_type': row[2],
                    'session_name': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'is_active': bool(row[6])
                }
                sessions.append(session)
                
            return sessions
            
        except Exception as e:
            logger.error(f"활성 세션 조회 중 오류: {str(e)}")
            return []
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_latest_session(self, user_id: str, session_type: str = None) -> Optional[Dict[str, Any]]:
        """
        사용자의 가장 최근 활성 세션을 가져옵니다.
        
        Args:
            user_id: 사용자 ID
            session_type: 세션 유형 (선택적)
            
        Returns:
            최근 활성 세션 또는 None
        """
        sessions = self.get_active_sessions(user_id, session_type)
        return sessions[0] if sessions else None
    
    def update_session_activity(self, conversation_id: str) -> bool:
        """
        세션의 마지막 활동 시간을 업데이트합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            성공 여부
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 현재 시간
            updated_at = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE conversation_sessions
                SET updated_at = ?
                WHERE conversation_id = ?
            ''', (updated_at, conversation_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"세션 활동 업데이트 중 오류: {str(e)}")
            if conn:
                conn.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def add_message(self, conversation_id: str, user_id: str, sender: str, 
                   message_text: str, is_important: bool = False, entities: Dict = None) -> str:
        """
        대화 메시지를 추가합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            user_id: 사용자 ID
            sender: 발신자 (user/assistant)
            message_text: 메시지 내용
            is_important: 중요 메시지 여부
            entities: 추출된 엔티티
            
        Returns:
            메시지 ID
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 현재 시간
            timestamp = datetime.now().isoformat()
            
            # 엔티티 직렬화
            entities_json = json.dumps(entities) if entities else None
            
            # 메시지 추가
            cursor.execute('''
                INSERT INTO conversation_messages (
                    conversation_id, user_id, sender, message_text, 
                    is_important, entities, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (conversation_id, user_id, sender, message_text, 
                 1 if is_important else 0, entities_json, timestamp))
            
            # 세션 업데이트 시간 갱신
            cursor.execute('''
                UPDATE conversation_sessions
                SET updated_at = ?
                WHERE conversation_id = ?
            ''', (timestamp, conversation_id))
            
            # 새로 생성된 메시지의 ID 가져오기
            message_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"새로운 메시지 추가: {message_id}, 대화: {conversation_id}")
            
            return str(message_id)
            
        except Exception as e:
            logger.error(f"메시지 추가 중 오류: {str(e)}")
            if conn:
                conn.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_messages(self, conversation_id: str, limit: int = 50, offset: int = 0,
                    start_time: str = None, end_time: str = None, important_only: bool = False) -> List[Dict[str, Any]]:
        """
        대화 메시지를 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            limit: 최대 메시지 수
            offset: 시작 위치
            start_time: 시작 시간
            end_time: 종료 시간
            important_only: 중요 메시지만 조회
            
        Returns:
            메시지 목록
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            query = '''
                SELECT message_id, conversation_id, user_id, sender, 
                       message_text, is_important, entities, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
            '''
            
            params = [conversation_id]
            
            if important_only:
                query += " AND is_important = 1"
                
            if start_time:
                query += " AND created_at >= ?"
                params.append(start_time)
                
            if end_time:
                query += " AND created_at <= ?"
                params.append(end_time)
                
            query += " ORDER BY created_at ASC"
            
            if limit > 0:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            messages = []
            for row in cursor.fetchall():
                entities = json.loads(row[6]) if row[6] else None
                
                message = {
                    'message_id': str(row[0]),
                    'conversation_id': str(row[1]),
                    'user_id': row[2],
                    'sender': row[3],
                    'message_text': row[4],
                    'is_important': bool(row[5]),
                    'entities': entities,
                    'created_at': row[7]
                }
                messages.append(message)
                
            return messages
                
        except Exception as e:
            logger.error(f"메시지 조회 중 오류: {str(e)}")
            return []
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        대화 컨텍스트 정보를 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            대화 컨텍스트 정보
        """
        try:
            context = {}
            
            # 세션 정보 가져오기
            session = self.get_session_by_id(conversation_id)
            if not session:
                return context
                
            context['session'] = session
            
            # 최근 메시지 가져오기 (최대 10개)
            messages = self.get_messages(conversation_id, limit=10)
            context['messages'] = messages
            
            # 최신 요약 가져오기
            summary = self.get_latest_summary(conversation_id)
            if summary:
                context['summary'] = summary
                
            return context
                
        except Exception as e:
            logger.error(f"대화 컨텍스트 조회 중 오류: {str(e)}")
            return {}
    
    def add_conversation_summary(self, conversation_id: str, summary_text: str, 
                               key_points: List = None, health_entities: Dict = None) -> str:
        """
        대화 요약을 추가합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            summary_text: 요약 내용
            key_points: 주요 내용 목록
            health_entities: 건강 관련 엔티티
            
        Returns:
            요약 ID
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 현재 시간
            timestamp = datetime.now().isoformat()
            
            # 데이터 직렬화
            key_points_json = json.dumps(key_points) if key_points else json.dumps([])
            health_entities_json = json.dumps(health_entities) if health_entities else json.dumps({})
            
            # 요약 추가
            cursor.execute('''
                INSERT INTO conversation_summaries (
                    conversation_id, summary_text, key_points, 
                    health_entities, created_at
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (conversation_id, summary_text, key_points_json, 
                 health_entities_json, timestamp))
            
            # 새로 생성된 요약의 ID 가져오기
            summary_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"새로운 대화 요약 추가: {summary_id}, 대화: {conversation_id}")
            
            return str(summary_id)
            
        except Exception as e:
            logger.error(f"대화 요약 추가 중 오류: {str(e)}")
            if conn:
                conn.rollback()
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_latest_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        대화의 최신 요약을 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            최신 요약 정보 또는 None
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT summary_id, conversation_id, summary_text, 
                       key_points, health_entities, created_at
                FROM conversation_summaries
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (conversation_id,))
            
            row = cursor.fetchone()
            
            if row:
                summary = {
                    'summary_id': str(row[0]),
                    'conversation_id': str(row[1]),
                    'summary_text': row[2],
                    'key_points': json.loads(row[3]) if row[3] else [],
                    'health_entities': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                }
                return summary
            else:
                return None
                
        except Exception as e:
            logger.error(f"최신 요약 조회 중 오류: {str(e)}")
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_session_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        대화 세션 정보를 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            세션 정보 또는 None
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT conversation_id, user_id, session_type, session_name, created_at, updated_at, is_active
                FROM conversation_sessions
                WHERE conversation_id = ?
            ''', (conversation_id,))
            
            row = cursor.fetchone()
            
            if row:
                session = {
                    'conversation_id': str(row[0]),
                    'user_id': row[1],
                    'session_type': row[2],
                    'session_name': row[3],
                    'created_at': row[4],
                    'updated_at': row[5],
                    'is_active': bool(row[6])
                }
                return session
            else:
                return None
                
        except Exception as e:
            logger.error(f"세션 조회 중 오류: {str(e)}")
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def update_session_status(self, conversation_id: str, is_active: bool = True) -> bool:
        """
        대화 세션의 활성 상태를 업데이트합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            is_active: 활성 상태 여부
            
        Returns:
            업데이트 성공 여부
        """
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 현재 시간
            updated_at = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE conversation_sessions
                SET is_active = ?, updated_at = ?
                WHERE conversation_id = ?
            ''', (1 if is_active else 0, updated_at, conversation_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"세션 상태 업데이트 중 오류: {str(e)}")
            if conn:
                conn.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def close_session(self, conversation_id: str) -> bool:
        """
        대화 세션을 종료 (비활성화)합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            성공 여부
        """
        return self.update_session_status(conversation_id, is_active=False)
    
    async def aget_active_sessions(self, user_id: str, session_type: str = None) -> List[Dict[str, Any]]:
        """
        사용자의 활성 대화 세션 목록을 비동기적으로 가져옵니다.
        
        Args:
            user_id: 사용자 ID
            session_type: 세션 유형으로 필터링 (선택적)
            
        Returns:
            활성 대화 세션 목록
        """
        # 비동기 환경에서도 동기 함수를 사용
        return self.get_active_sessions(user_id, session_type)
    
    async def aget_messages(self, conversation_id: str, limit: int = 50, offset: int = 0,
                    start_time: str = None, end_time: str = None, important_only: bool = False) -> List[Dict[str, Any]]:
        """
        대화 메시지를 비동기적으로 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            limit: 최대 메시지 수
            offset: 시작 위치
            start_time: 시작 시간
            end_time: 종료 시간
            important_only: 중요 메시지만 조회
            
        Returns:
            메시지 목록
        """
        # 비동기 환경에서도 동기 함수를 사용 (실제 비동기 DB 연결이 필요하면 수정 필요)
        return self.get_messages(conversation_id, limit, offset, start_time, end_time, important_only)
    
    async def aget_latest_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        대화의 최신 요약을 비동기적으로 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            최신 요약 정보 또는 None
        """
        # 비동기 환경에서도 동기 함수를 사용
        return self.get_latest_summary(conversation_id)
    
    async def aget_session_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        대화 세션 정보를 비동기적으로 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            세션 정보 또는 None
        """
        # 비동기 환경에서도 동기 함수를 사용
        return self.get_session_by_id(conversation_id)
    
    async def aget_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        대화 컨텍스트 정보를 비동기적으로 조회합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            대화 컨텍스트 정보
        """
        # 비동기 환경에서도 동기 함수를 사용
        return self.get_conversation_context(conversation_id)
    
    async def aadd_conversation_summary(self, conversation_id: str, summary_text: str, 
                                key_points: List = None, health_entities: Dict = None) -> str:
        """
        대화 요약을 비동기적으로 추가합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            summary_text: 요약 내용
            key_points: 주요 내용 목록
            health_entities: 건강 관련 엔티티
            
        Returns:
            요약 ID
        """
        # 비동기 환경에서도 동기 함수를 사용
        return self.add_conversation_summary(conversation_id, summary_text, key_points, health_entities)
    
    async def aclose_session(self, conversation_id: str) -> bool:
        """
        대화 세션을 비동기적으로 종료 (비활성화)합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            
        Returns:
            성공 여부
        """
        # 비동기 환경에서도 동기 함수를 사용
        return self.close_session(conversation_id) 