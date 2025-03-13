from datetime import datetime, date, timedelta
import uuid
import hashlib
import os
from typing import Dict, List, Any, Optional
import logging
from app.db.database import Database
from app.models.user_profile import UserProfile, UserGoal, HealthMetrics

logger = logging.getLogger(__name__)

class UserDAO:
    """사용자 데이터 액세스 객체"""
    
    def __init__(self):
        self.db = Database()
    
    def create_user(self, username: str, password: str, name: str = None, 
                   birth_date: date = None, gender: str = None, 
                   email: str = None, phone: str = None) -> str:
        """새 사용자 생성"""
        # 사용자 ID 생성
        user_id = str(uuid.uuid4())
        
        # 비밀번호 해싱
        salt = os.urandom(32)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        ).hex()
        
        # 비밀번호 해시 + 솔트 저장
        password_storage = f"{password_hash}:{salt.hex()}"
        
        # 사용자 정보 저장
        query = """
            INSERT INTO users 
            (user_id, username, password_hash, name, birth_date, gender, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (user_id, username, password_storage, name, birth_date, gender, email, phone)
        
        try:
            self.db.execute_query(query, params)
            logger.info(f"새 사용자 생성: {username} (ID: {user_id})")
            return user_id
        except Exception as e:
            logger.error(f"사용자 생성 오류: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """사용자 ID로 사용자 정보 조회"""
        query = "SELECT * FROM users WHERE user_id = %s"
        return self.db.fetch_one(query, (user_id,))
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """사용자명으로 사용자 정보 조회"""
        query = "SELECT * FROM users WHERE username = %s"
        return self.db.fetch_one(query, (username,))
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 정보 조회"""
        query = "SELECT * FROM users WHERE email = %s"
        return self.db.fetch_one(query, (email,))
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """사용자 인증 및 사용자 정보 반환"""
        user = self.get_user_by_username(username)
        
        if not user:
            logger.warning(f"인증 실패: 사용자 없음 - {username}")
            return None
        
        # 저장된 해시 및 솔트 분리
        stored_password = user['password_hash']
        password_hash, salt_hex = stored_password.split(':')
        salt = bytes.fromhex(salt_hex)
        
        # 입력된 비밀번호 해싱
        input_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt, 
            100000
        ).hex()
        
        # 해시 비교
        if input_hash == password_hash:
            logger.info(f"사용자 인증 성공: {username}")
            return user  # 전체 사용자 정보 반환
        else:
            logger.warning(f"인증 실패: 비밀번호 불일치 - {username}")
            return None
    
    def create_session(self, user_id: str) -> str:
        """사용자 세션 생성"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)  # 세션 7일 유효
        
        query = """
            INSERT INTO sessions (session_id, user_id, expires_at)
            VALUES (%s, %s, %s)
        """
        params = (session_id, user_id, expires_at)
        
        self.db.execute_query(query, params)
        logger.info(f"세션 생성: {session_id} (사용자 ID: {user_id})")
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """세션 유효성 검사 및 사용자 ID 반환"""
        query = """
            SELECT user_id FROM sessions 
            WHERE session_id = %s AND expires_at > NOW()
        """
        result = self.db.fetch_one(query, (session_id,))
        
        if result:
            return result['user_id']
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제 (로그아웃)"""
        query = "DELETE FROM sessions WHERE session_id = %s"
        rows = self.db.execute_query(query, (session_id,))
        return rows > 0 