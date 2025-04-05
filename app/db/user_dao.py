from datetime import datetime, date, timedelta
import uuid
import hashlib
import os
import json
from typing import Dict, List, Any, Optional, Union
import logging
from app.db.database import Database
from app.models.user_profile import UserProfile, UserGoal, HealthMetrics

logger = logging.getLogger(__name__)

class UserDAO:
    """사용자 데이터 액세스 객체"""
    
    def __init__(self):
        self.db = Database()
    
    def create_user(self, social_id: str, provider: str = "kakao", birth_date: date = None, gender: str = None) -> str:
        """
        새 사용자 생성 (소셜 로그인용)
        
        Parameters:
            social_id: 소셜 ID (카카오 ID 등)
            provider: 제공자 (기본값: kakao)
            birth_date: 생년월일 (선택)
            gender: 성별 (선택)
            
        Returns:
            str: 생성된 사용자 ID
        """
        # 사용자 ID 생성
        user_id = str(uuid.uuid4())
        
        # 사용자 정보 저장 (소셜 계정 테이블에 직접 저장)
        query = """
            INSERT INTO social_accounts 
            (user_id, social_id, provider, birth_date, gender)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, social_id, provider, birth_date, gender)
        
        try:
            self.db.execute_query(query, params)
            logger.info(f"새 사용자 생성: {user_id} (소셜 ID: {social_id}, 제공자: {provider})")
            return user_id
        except Exception as e:
            logger.error(f"사용자 생성 오류: {e}")
            raise
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """사용자 ID로 사용자 정보 조회"""
        query = "SELECT * FROM social_accounts WHERE user_id = %s"
        return self.db.fetch_one(query, (user_id,))
    
    def get_social_account(self, social_id: str, provider: str) -> Optional[Dict[str, Any]]:
        """소셜 ID와 제공자로 사용자 정보 조회"""
        query = """
            SELECT * FROM social_accounts 
            WHERE social_id = %s AND provider = %s
        """
        return self.db.fetch_one(query, (social_id, provider))
    
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
    
    def update_user(self, user_id: str, **fields) -> bool:
        """
        사용자 정보 업데이트
        
        Parameters:
            user_id (str): 업데이트할 사용자의 ID
            **fields: 업데이트할 필드 (birth_date, gender 등)
        
        Returns:
            bool: 업데이트 성공 여부
        """
        if not fields:
            logger.warning(f"업데이트할 필드가 제공되지 않았습니다: {user_id}")
            return False
            
        # 필드 검증 (허용된 필드만 업데이트)
        allowed_fields = {'birth_date', 'gender'}
        update_fields = {k: v for k, v in fields.items() if k in allowed_fields}
        
        if not update_fields:
            logger.warning(f"업데이트할 유효한 필드가 없습니다: {user_id}")
            return False
            
        # 업데이트 쿼리 생성
        set_clause = ", ".join([f"{field} = %s" for field in update_fields.keys()])
        query = f"UPDATE social_accounts SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s"
        
        # 파라미터 준비 (업데이트 필드 값 + 사용자 ID)
        params = list(update_fields.values())
        params.append(user_id)
        
        try:
            rows = self.db.execute_query(query, tuple(params))
            success = rows > 0
            if success:
                logger.info(f"사용자 정보 업데이트 성공: {user_id}, 필드: {list(update_fields.keys())}")
            else:
                logger.warning(f"사용자 정보 업데이트 실패 (영향받은 행 없음): {user_id}")
            return success
        except Exception as e:
            logger.error(f"사용자 정보 업데이트 오류: {e}")
            return False
            
    def update_health_metrics(self, user_id: str, height: float = None, weight: float = None, **metrics) -> str:
        """
        사용자 건강 지표 업데이트
        
        Parameters:
            user_id (str): 사용자 ID
            height (float): 키 (cm)
            weight (float): 몸무게 (kg)
            **metrics: 기타 건강 지표 (heart_rate, blood_pressure_systolic 등)
            
        Returns:
            str: 생성된 지표 ID
        """
        metrics_id = str(uuid.uuid4())
        
        # 기본 필드 설정
        all_metrics = {
            'height': height,
            'weight': weight
        }
        
        # 추가 지표 병합
        all_metrics.update(metrics)
        
        # NULL이 아닌 필드 필터링
        valid_metrics = {k: v for k, v in all_metrics.items() if v is not None}
        
        if not valid_metrics:
            logger.warning(f"업데이트할 건강 지표가 제공되지 않았습니다: {user_id}")
            return None
            
        # 쿼리 생성
        fields = list(valid_metrics.keys())
        placeholders = ", ".join(["%s"] * (len(fields) + 2))  # user_id와 metrics_id용 플레이스홀더 추가
        field_str = "metrics_id, user_id, " + ", ".join(fields)
        
        query = f"INSERT INTO health_metrics ({field_str}) VALUES ({placeholders})"
        
        # 파라미터 준비
        params = [metrics_id, user_id] + list(valid_metrics.values())
        
        try:
            self.db.execute_query(query, tuple(params))
            logger.info(f"건강 지표 업데이트 성공: {user_id}, 지표: {list(valid_metrics.keys())}")
            return metrics_id
        except Exception as e:
            logger.error(f"건강 지표 업데이트 오류: {e}")
            return None
    
    def delete_user(self, user_id: str) -> bool:
        """
        사용자 계정 삭제
        
        데이터베이스에 ON DELETE CASCADE 제약 조건이 설정되어 있으므로 
        social_accounts 테이블에서 사용자를 삭제하면 관련된 모든 데이터가 함께 삭제됩니다.
        다음 테이블의 사용자 관련 데이터가 모두 삭제됩니다:
        - sessions: 사용자 세션 정보
        - health_metrics: 키, 몸무게 등 건강 지표
        - dietary_restrictions: 식이 제한 정보
        - diet_advice_history: 식단 조언 기록
        - exercise_recommendations: 운동 추천 정보
        - exercise_completions: 운동 완료 기록
        
        Parameters:
            user_id (str): 삭제할 사용자의 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 사용자 계정 삭제 쿼리
            query = "DELETE FROM social_accounts WHERE user_id = %s"
            rows = self.db.execute_query(query, (user_id,))
            
            success = rows > 0
            if success:
                logger.info(f"사용자 계정 및 모든 관련 데이터 삭제 성공: {user_id}")
            else:
                logger.warning(f"사용자 계정 삭제 실패 (사용자를 찾을 수 없음): {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"사용자 계정 삭제 오류: {e}")
            return False 