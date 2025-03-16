import uuid
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union

from app.db.database import Database

logger = logging.getLogger(__name__)

class HealthDAO:
    """건강 데이터 액세스 객체"""
    
    def __init__(self):
        self.db = Database()
    
    def add_health_metrics(self, user_id: str, metrics: Dict[str, Any]) -> str:
        """사용자 건강 지표 추가"""
        metrics_id = str(uuid.uuid4())
        now = datetime.now()
        
        # 필수 필드가 없으면 None으로 설정
        weight = metrics.get('weight')
        height = metrics.get('height')
        heart_rate = metrics.get('heart_rate')
        blood_pressure_systolic = metrics.get('blood_pressure_systolic')
        blood_pressure_diastolic = metrics.get('blood_pressure_diastolic')
        blood_sugar = metrics.get('blood_sugar')
        temperature = metrics.get('temperature')
        oxygen_saturation = metrics.get('oxygen_saturation')
        sleep_hours = metrics.get('sleep_hours')
        steps = metrics.get('steps')
        
        # BMI 자동 계산 (키와 체중이 모두 제공된 경우)
        bmi = None
        if weight is not None and height is not None and height > 0:
            # 키(cm)를 미터로 변환하여 BMI 계산
            height_m = height / 100.0
            bmi = round(weight / (height_m * height_m), 1)
            logger.info(f"BMI 자동 계산: {bmi} (체중: {weight}kg, 키: {height}cm)")
        
        # BMI 필드 추가
        query = """
            INSERT INTO health_metrics (
                metrics_id, user_id, timestamp,
                weight, height, heart_rate,
                blood_pressure_systolic, blood_pressure_diastolic,
                blood_sugar, temperature, oxygen_saturation,
                sleep_hours, steps, bmi
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            metrics_id, user_id, now,
            weight, height, heart_rate,
            blood_pressure_systolic, blood_pressure_diastolic,
            blood_sugar, temperature, oxygen_saturation,
            sleep_hours, steps, bmi
        )
        
        try:
            self.db.execute_query(query, params)
            logger.info(f"건강 지표 추가 성공: 사용자 {user_id}, 지표 ID {metrics_id}")
            return metrics_id
        except Exception as e:
            logger.error(f"건강 지표 추가 오류: {str(e)}")
            raise
    
    def get_latest_health_metrics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자의 최신 건강 지표 조회"""
        conn = None
        try:
            # 새로운 연결 생성
            conn = self.db.connect()
            
            # 기존 연결을 닫고 새로 연결하여 최신 데이터 확인
            if hasattr(conn, 'ping'):
                conn.ping(reconnect=True)
            
            query = """
                SELECT * FROM health_metrics
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()
            
            # 명시적으로 커밋하여 트랜잭션 완료
            conn.commit()
            
            if result:
                logger.info(f"최신 건강 지표 조회 성공: 사용자 {user_id}")
                return dict(result)
            else:
                logger.info(f"최신 건강 지표 없음: 사용자 {user_id}")
                return None
        except Exception as e:
            logger.error(f"최신 건강 지표 조회 오류: {str(e)}")
            return None
    
    def get_latest_health_metrics_by_column(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 각 건강 지표 컬럼별로 null이 아닌 최신 데이터 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            각 컬럼별 최신 데이터가 포함된 딕셔너리
        """
        try:
            # 모든 건강 지표 컬럼 목록
            columns = [
                'weight', 'height', 'heart_rate', 
                'blood_pressure_systolic', 'blood_pressure_diastolic',
                'blood_sugar', 'temperature', 'oxygen_saturation',
                'sleep_hours', 'steps'
            ]
            
            combined_metrics = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # 새로운 연결 생성
            conn = self.db.connect()
            
            # 기존 연결을 닫고 새로 연결하여 최신 데이터 확인
            if hasattr(conn, 'ping'):
                conn.ping(reconnect=True)
            
            # 각 컬럼별로 최신 null이 아닌 값 조회
            for column in columns:
                query = f"""
                    SELECT {column}, timestamp FROM health_metrics
                    WHERE user_id = %s AND {column} IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                
                if result and result[column] is not None:
                    combined_metrics[column] = result[column]
                    logger.debug(f"컬럼 {column}의 최신 데이터 조회: {result[column]} (날짜: {result['timestamp']})")
            
            # 명시적으로 커밋하여 트랜잭션 완료
            conn.commit()
            
            # BMI 자동 계산 (키와 체중이 있는 경우)
            if 'weight' in combined_metrics and 'height' in combined_metrics and combined_metrics['height'] > 0:
                weight = combined_metrics['weight']
                height_m = combined_metrics['height'] / 100.0
                bmi = round(weight / (height_m * height_m), 1)
                combined_metrics['bmi'] = bmi
                logger.info(f"컬럼별 BMI 자동 계산: {bmi} (체중: {weight}kg, 키: {combined_metrics['height']}cm)")
            
            # 혈압 데이터가 있는 경우 blood_pressure 객체 추가
            if 'blood_pressure_systolic' in combined_metrics and 'blood_pressure_diastolic' in combined_metrics:
                combined_metrics['blood_pressure'] = {
                    'systolic': combined_metrics['blood_pressure_systolic'],
                    'diastolic': combined_metrics['blood_pressure_diastolic']
                }
            
            logger.info(f"사용자 {user_id}의 컬럼별 최신 건강 지표 조회 완료: {len(combined_metrics) - 2}개 항목")
            return combined_metrics
            
        except Exception as e:
            logger.error(f"컬럼별 최신 건강 지표 조회 오류: {str(e)}")
            return {'user_id': user_id}
    
    def get_health_metrics_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """사용자의 건강 지표 이력 조회"""
        query = """
            SELECT * FROM health_metrics
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        try:
            results = self.db.fetch_all(query, (user_id, limit))
            # 날짜/시간 형식 처리
            for result in results:
                if 'timestamp' in result and result['timestamp']:
                    result['timestamp'] = result['timestamp'].isoformat()
            
            logger.info(f"건강 지표 이력 조회 성공: 사용자 {user_id}, {len(results)}개 레코드")
            return results
        except Exception as e:
            logger.error(f"건강 지표 이력 조회 오류: {str(e)}")
            raise
    
    def add_medical_condition(self, 
                             user_id: str, 
                             condition_name: str,
                             diagnosis_date: Optional[date] = None,
                             is_active: bool = True,
                             notes: Optional[str] = None) -> str:
        """의학적 상태 추가"""
        condition_id = str(uuid.uuid4())
        now = datetime.now()
        
        query = """
            INSERT INTO medical_conditions (
                condition_id, user_id, condition_name,
                diagnosis_date, is_active, notes,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            condition_id, user_id, condition_name,
            diagnosis_date, is_active, notes,
            now, now
        )
        
        try:
            self.db.execute_query(query, params)
            logger.info(f"의학적 상태 추가 성공: 사용자 {user_id}, 상태 '{condition_name}'")
            return condition_id
        except Exception as e:
            logger.error(f"의학적 상태 추가 오류: {str(e)}")
            raise
    
    def get_medical_conditions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """사용자의 의학적 상태 조회"""
        if active_only:
            query = """
                SELECT * FROM medical_conditions
                WHERE user_id = %s AND is_active = 1
                ORDER BY created_at DESC
            """
            params = (user_id,)
        else:
            query = """
                SELECT * FROM medical_conditions
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            params = (user_id,)
        
        try:
            results = self.db.fetch_all(query, params)
            # 날짜/시간 형식 처리
            for result in results:
                if 'diagnosis_date' in result and result['diagnosis_date']:
                    result['diagnosis_date'] = result['diagnosis_date'].isoformat()
                if 'created_at' in result and result['created_at']:
                    result['created_at'] = result['created_at'].isoformat()
                if 'updated_at' in result and result['updated_at']:
                    result['updated_at'] = result['updated_at'].isoformat()
            
            logger.info(f"의학적 상태 조회 성공: 사용자 {user_id}, {len(results)}개 레코드")
            return results
        except Exception as e:
            logger.error(f"의학적 상태 조회 오류: {str(e)}")
            raise
    
    def add_dietary_restriction(self, 
                              user_id: str, 
                              restriction_type: str,
                              is_active: bool = True,
                              notes: Optional[str] = None) -> str:
        """식이 제한 추가"""
        restriction_id = str(uuid.uuid4())
        now = datetime.now()
        
        query = """
            INSERT INTO dietary_restrictions (
                restriction_id, user_id, restriction_type,
                is_active, notes, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            restriction_id, user_id, restriction_type,
            is_active, notes, now
        )
        
        try:
            self.db.execute_query(query, params)
            logger.info(f"식이 제한 추가 성공: 사용자 {user_id}, 유형 '{restriction_type}'")
            return restriction_id
        except Exception as e:
            logger.error(f"식이 제한 추가 오류: {str(e)}")
            raise
    
    def get_dietary_restrictions(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 식이 제한 조회"""
        query = """
            SELECT * FROM dietary_restrictions
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        
        try:
            results = self.db.fetch_all(query, (user_id,))
            # 날짜/시간 형식 처리
            for result in results:
                if 'created_at' in result and result['created_at']:
                    result['created_at'] = result['created_at'].isoformat()
            
            logger.info(f"식이 제한 조회 성공: 사용자 {user_id}, {len(results)}개 레코드")
            return results
        except Exception as e:
            logger.error(f"식이 제한 조회 오류: {str(e)}")
            raise
    
    def update_gemini_response(self, metrics_id: str, gemini_response: str) -> bool:
        """건강 지표의 gemini_response 필드 업데이트"""
        conn = None
        try:
            # 새로운 연결 생성
            conn = self.db.connect()
            
            query = """
                UPDATE health_metrics
                SET gemini_response = %s
                WHERE metrics_id = %s
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query, (gemini_response, metrics_id))
            
            # 명시적으로 커밋
            conn.commit()
            
            logger.info(f"gemini_response 업데이트 성공: 지표 ID {metrics_id}")
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"gemini_response 업데이트 오류: {str(e)}")
            return False
    
    def get_complete_health_profile(self, user_id: str) -> Dict[str, Any]:
        """사용자의 종합 건강 프로필 조회"""
        try:
            # 최신 건강 지표 조회
            latest_metrics = self.get_latest_health_metrics_by_column(user_id)
            
            # 최신 gemini_response 조회 - 캐싱 문제 해결을 위해 직접 연결 사용
            conn = None
            try:
                # 새로운 연결 생성
                conn = self.db.connect()
                
                # 기존 연결을 닫고 새로 연결하여 최신 데이터 확인
                if hasattr(conn, 'ping'):
                    conn.ping(reconnect=True)
                
                query = """
                    SELECT gemini_response
                    FROM health_metrics
                    WHERE user_id = %s AND gemini_response IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                
                # 명시적으로 커밋하여 트랜잭션 완료
                conn.commit()
                
                latest_gemini_response = result['gemini_response'] if result else None
                logger.info(f"최신 gemini_response 조회 완료: {latest_gemini_response is not None}")
            finally:
                # 연결 종료는 Database 클래스에서 관리
                pass
            
            # 의학적 상태 조회 (활성 상태만)
            medical_conditions = self.get_medical_conditions(user_id, active_only=True)
            
            # 식이 제한 조회
            dietary_restrictions = self.get_dietary_restrictions(user_id)
            
            # 통합 프로필 구성
            profile = {
                'user_id': user_id,
                'health_metrics': latest_metrics or {},
                'medical_conditions': medical_conditions or [],
                'dietary_restrictions': dietary_restrictions or [],
                'gemini_response': latest_gemini_response,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"종합 건강 프로필 조회 성공: 사용자 {user_id}")
            return profile
        except Exception as e:
            logger.error(f"종합 건강 프로필 조회 오류: {str(e)}")
            raise 