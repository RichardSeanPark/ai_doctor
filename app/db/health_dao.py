from datetime import datetime, date
from typing import Dict, List, Any, Optional
import logging
from app.db.database import Database
from app.models.health_data import HealthMetrics

logger = logging.getLogger(__name__)

class HealthDAO:
    """건강 데이터 액세스 객체"""
    
    def __init__(self):
        self.db = Database()
    
    def add_health_metrics(self, user_id: str, 
                         weight: float = None, height: float = None,
                         blood_pressure_systolic: int = None, blood_pressure_diastolic: int = None,
                         heart_rate: int = None, blood_sugar: float = None,
                         oxygen_saturation: int = None, temperature: float = None,
                         sleep_hours: float = None, steps: int = None) -> int:
        """사용자 건강 지표 추가"""
        # BMI 계산 (가능한 경우)
        bmi = None
        if weight and height and height > 0:
            bmi = weight / ((height/100) ** 2)
        
        query = """
            INSERT INTO health_metrics 
            (user_id, weight, height, bmi, blood_pressure_systolic, blood_pressure_diastolic, 
             heart_rate, blood_sugar, oxygen_saturation, temperature, 
             sleep_hours, steps)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            user_id, weight, height, bmi, blood_pressure_systolic, blood_pressure_diastolic,
            heart_rate, blood_sugar, oxygen_saturation, temperature,
            sleep_hours, steps
        )
        
        return self.db.insert_and_get_id(query, params)
    
    def get_latest_health_metrics(self, user_id: str) -> Optional[Dict]:
        """사용자의 최신 건강 지표 조회"""
        query = """
            SELECT * FROM health_metrics 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        return self.db.fetch_one(query, (user_id,))
    
    def get_health_metrics_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """사용자의 건강 지표 이력 조회"""
        query = """
            SELECT * FROM health_metrics 
            WHERE user_id = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
        """
        return self.db.fetch_all(query, (user_id, limit))
    
    def add_medical_condition(self, user_id: str, condition_name: str, 
                            diagnosis_date: date = None, is_active: bool = True,
                            notes: str = None) -> int:
        """사용자 의료 상태(질병) 추가"""
        query = """
            INSERT INTO medical_conditions 
            (user_id, condition_name, diagnosis_date, is_active, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_id, condition_name, diagnosis_date, is_active, notes)
        
        try:
            condition_id = self.db.insert_and_get_id(query, params)
            logger.info(f"의료 조건 추가: {condition_name} (사용자 ID: {user_id})")
            return condition_id
        except Exception as e:
            logger.error(f"의료 조건 추가 오류: {e}")
            raise
    
    def get_medical_conditions(self, user_id: str, active_only: bool = True) -> List[Dict]:
        """사용자의 의료 상태(질병) 목록 조회"""
        query = """
            SELECT * FROM medical_conditions 
            WHERE user_id = %s
        """
        
        if active_only:
            query += " AND is_active = TRUE"
            
        return self.db.fetch_all(query, (user_id,))
    
    def add_dietary_restriction(self, user_id: str, restriction_type: str,
                              severity: str = None, notes: str = None) -> int:
        """사용자 식이 제한 추가"""
        query = """
            INSERT INTO dietary_restrictions 
            (user_id, restriction_type, severity, notes)
            VALUES (%s, %s, %s, %s)
        """
        params = (user_id, restriction_type, severity, notes)
        
        return self.db.insert_and_get_id(query, params)
    
    def get_dietary_restrictions(self, user_id: str) -> List[Dict]:
        """사용자의 식이 제한 목록 조회"""
        query = """
            SELECT * FROM dietary_restrictions 
            WHERE user_id = %s
        """
        return self.db.fetch_all(query, (user_id,))
    
    def get_complete_health_profile(self, user_id: str) -> Dict[str, Any]:
        """사용자의 완전한 건강 프로필 조회"""
        # 사용자 기본 정보
        user_info = self.db.fetch_one("SELECT * FROM users WHERE user_id = %s", (user_id,))
        
        if not user_info:
            return None
        
        # 최신 건강 지표
        health_metrics = self.get_latest_health_metrics(user_id)
        
        # 활성 의료 상태(질병)
        medical_conditions = self.get_medical_conditions(user_id, active_only=True)
        conditions_list = [cond['condition_name'] for cond in medical_conditions] if medical_conditions else []
        
        # 식이 제한
        dietary_restrictions = self.get_dietary_restrictions(user_id)
        restrictions_list = [rest['restriction_type'] for rest in dietary_restrictions] if dietary_restrictions else []
        
        # 목표 정보
        goals = self.db.fetch_all(
            "SELECT * FROM user_goals WHERE user_id = %s", (user_id,)
        )
        
        # 건강 지표를 적절한 형식으로 변환
        metrics_dict = {}
        if health_metrics:
            for key, value in health_metrics.items():
                if key not in ['metrics_id', 'user_id', 'timestamp'] and value is not None:
                    metrics_dict[key] = value
            
            # 혈압은 별도로 처리
            if health_metrics.get('blood_pressure_systolic') and health_metrics.get('blood_pressure_diastolic'):
                metrics_dict['blood_pressure'] = {
                    'systolic': health_metrics['blood_pressure_systolic'],
                    'diastolic': health_metrics['blood_pressure_diastolic']
                }
                
        return {
            'user_id': user_id,
            'name': user_info.get('name'),
            'birth_date': user_info.get('birth_date'),
            'gender': user_info.get('gender'),
            'current_metrics': metrics_dict,
            'medical_conditions': conditions_list,
            'dietary_restrictions': restrictions_list,
            'goals': goals
        } 