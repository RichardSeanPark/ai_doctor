import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
import json

from app.db.database import Database
from app.models.exercise_data import ExerciseRecommendation, ExerciseSchedule, ExerciseCompletion

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
    
    def get_three_months_health_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 최근 3개월간 건강 지표 데이터 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            각 컬럼별 최신 데이터와 3개월치 시계열 데이터가 포함된 딕셔너리
        """
        try:
            # 모든 건강 지표 컬럼 목록
            columns = [
                'weight', 'height', 'heart_rate', 
                'blood_pressure_systolic', 'blood_pressure_diastolic',
                'blood_sugar', 'temperature', 'oxygen_saturation',
                'sleep_hours', 'steps'
            ]
            
            # 최신 데이터를 저장할 딕셔너리
            latest_metrics = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # 시계열 데이터를 저장할 딕셔너리
            time_series_metrics = {column: [] for column in columns}
            
            # 3개월 전 날짜 계산
            three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            # 새로운 연결 생성
            conn = self.db.connect()
            
            # 기존 연결을 닫고 새로 연결하여 최신 데이터 확인
            if hasattr(conn, 'ping'):
                conn.ping(reconnect=True)
            
            # 각 컬럼별로 최신 null이 아닌 값 조회
            for column in columns:
                # 최신 값 조회
                latest_query = f"""
                    SELECT {column}, timestamp FROM health_metrics
                    WHERE user_id = %s AND {column} IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(latest_query, (user_id,))
                    latest_result = cursor.fetchone()
                
                if latest_result and latest_result[column] is not None:
                    latest_metrics[column] = latest_result[column]
                    logger.debug(f"컬럼 {column}의 최신 데이터 조회: {latest_result[column]} (날짜: {latest_result['timestamp']})")
                
                # 1년치 시계열 데이터 조회
                time_series_query = f"""
                    SELECT {column}, timestamp FROM health_metrics
                    WHERE user_id = %s 
                    AND {column} IS NOT NULL 
                    AND timestamp >= %s
                    ORDER BY timestamp ASC
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(time_series_query, (user_id, three_months_ago))
                    time_series_results = cursor.fetchall()
                
                # 시계열 데이터 가공
                for result in time_series_results:
                    if result and result[column] is not None:
                        time_series_metrics[column].append({
                            'value': result[column],
                            'timestamp': result['timestamp'].isoformat() if isinstance(result['timestamp'], datetime) else result['timestamp']
                        })
            
            # 명시적으로 커밋하여 트랜잭션 완료
            conn.commit()
            
            # BMI 자동 계산 (키와 체중이 있는 경우)
            if 'weight' in latest_metrics and 'height' in latest_metrics and latest_metrics['height'] > 0:
                weight = latest_metrics['weight']
                height_m = latest_metrics['height'] / 100.0
                bmi = round(weight / (height_m * height_m), 1)
                latest_metrics['bmi'] = bmi
                logger.info(f"BMI 자동 계산: {bmi} (체중: {weight}kg, 키: {latest_metrics['height']}cm)")
            
            # 혈압 데이터가 있는 경우 blood_pressure 객체 추가
            if 'blood_pressure_systolic' in latest_metrics and 'blood_pressure_diastolic' in latest_metrics:
                latest_metrics['blood_pressure'] = {
                    'systolic': latest_metrics['blood_pressure_systolic'],
                    'diastolic': latest_metrics['blood_pressure_diastolic']
                }
            
            # 시계열 데이터에 BMI 계산 추가
            time_series_metrics['bmi'] = []
            
            # weight와 height의 시간별 데이터를 저장할 딕셔너리
            weight_by_time = {}
            height_by_time = {}
            
            # weight와 height 데이터를 timestamp별로 정리
            for weight_data in time_series_metrics['weight']:
                weight_by_time[weight_data['timestamp']] = weight_data['value']
            
            for height_data in time_series_metrics['height']:
                height_by_time[height_data['timestamp']] = height_data['value']
            
            # 모든 타임스탬프 가져오기
            all_timestamps = set(weight_by_time.keys()) | set(height_by_time.keys())
            
            # 각 타임스탬프에 대해 weight와 height 데이터가 모두 있는 경우 BMI 계산
            for timestamp in all_timestamps:
                if timestamp in weight_by_time and timestamp in height_by_time:
                    weight = weight_by_time[timestamp]
                    height = height_by_time[timestamp]
                    
                    if height > 0:
                        height_m = height / 100.0
                        bmi = round(weight / (height_m * height_m), 1)
                        time_series_metrics['bmi'].append({
                            'value': bmi,
                            'timestamp': timestamp
                        })
                        logger.debug(f"시계열 BMI 계산: {timestamp}, BMI: {bmi}")
            
            # bmi 시계열 데이터를 시간 순으로 정렬
            time_series_metrics['bmi'].sort(key=lambda x: x['timestamp'])
            
            # 최종 결과 집계
            result = {
                'latest': latest_metrics,
                'time_series': time_series_metrics
            }
            
            logger.info(f"사용자 {user_id}의 1년치 건강 지표 조회 완료")
            return result
            
        except Exception as e:
            logger.error(f"1년치 건강 지표 조회 오류: {str(e)}")
            return {'user_id': user_id, 'latest': {}, 'time_series': {}}
    
    def get_health_metrics_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """사용자의 건강 지표 이력 조회"""
        query = """
            SELECT * FROM health_metrics
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        params = (user_id, limit)
        
        try:
            results = self.db.fetch_all(query, params)
            # 날짜/시간 형식 처리
            for result in results:
                if 'timestamp' in result and result['timestamp']:
                    result['timestamp'] = result['timestamp'].isoformat()
            
            logger.info(f"건강 지표 이력 조회 성공: 사용자 {user_id}, {len(results)}개 레코드")
            return results
        except Exception as e:
            logger.error(f"건강 지표 이력 조회 오류: {str(e)}")
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
        """사용자의 식이 제한 사항 조회"""
        query = """
        SELECT restriction_type, description, severity
        FROM dietary_restrictions
        WHERE user_id = %s
        """
        return self.db.execute_query(query, (user_id,))
    
    def save_diet_advice(self, user_id: str, request_id: str, meal_date: str, 
                        meal_type: str, food_items: List[Dict[str, Any]], 
                        dietary_restrictions: List[str], health_goals: List[str],
                        specific_concerns: str, advice_text: str) -> bool:
        """식단 조언 기록 저장"""
        try:
            # JSON 데이터 변환
            food_items_json = json.dumps(food_items, ensure_ascii=False)
            dietary_restrictions_json = json.dumps(dietary_restrictions, ensure_ascii=False) if dietary_restrictions else None
            health_goals_json = json.dumps(health_goals, ensure_ascii=False) if health_goals else None
            
            # 같은 날짜, 같은 식사 유형의 기록이 있는지 확인
            check_query = """
            SELECT advice_id FROM diet_advice_history 
            WHERE user_id = %s AND meal_date = %s AND meal_type = %s
            """
            existing_record = self.db.execute_query(check_query, (user_id, meal_date, meal_type))
            
            if existing_record:
                # 기존 기록 업데이트
                update_query = """
                UPDATE diet_advice_history 
                SET food_items = %s,
                    dietary_restrictions = %s,
                    health_goals = %s,
                    specific_concerns = %s,
                    advice_text = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND meal_date = %s AND meal_type = %s
                """
                self.db.execute_query(update_query, (
                    food_items_json,
                    dietary_restrictions_json,
                    health_goals_json,
                    specific_concerns,
                    advice_text,
                    user_id,
                    meal_date,
                    meal_type
                ))
            else:
                # 새 기록 생성
                insert_query = """
                INSERT INTO diet_advice_history (
                    advice_id, user_id, request_id, meal_date, meal_type,
                    food_items, dietary_restrictions, health_goals,
                    specific_concerns, advice_text
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                advice_id = str(uuid.uuid4())
                self.db.execute_query(insert_query, (
                    advice_id,
                    user_id,
                    request_id,
                    meal_date,
                    meal_type,
                    food_items_json,
                    dietary_restrictions_json,
                    health_goals_json,
                    specific_concerns,
                    advice_text
                ))
            
            return True
        except Exception as e:
            logger.error(f"식단 조언 기록 저장 중 오류 발생: {str(e)}")
            return False
    
    def get_diet_advice_history(self, user_id: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """사용자의 식단 조언 기록 조회"""
        try:
            query = """
            SELECT 
                advice_id,
                request_id,
                meal_date,
                meal_type,
                food_items,
                dietary_restrictions,
                health_goals,
                specific_concerns,
                advice_text,
                created_at,
                updated_at
            FROM diet_advice_history
            WHERE user_id = %s
            """
            params = [user_id]
            
            if start_date:
                query += " AND meal_date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND meal_date <= %s"
                params.append(end_date)
            
            query += " ORDER BY meal_date DESC, meal_type"
            
            # 쿼리와 파라미터 로깅
            logger.info(f"[HEALTH_DAO] 식단 조언 히스토리 조회 쿼리: {query}")
            logger.info(f"[HEALTH_DAO] 쿼리 파라미터: {params}")
            
            results = self.db.fetch_all(query, tuple(params))
            
            # JSON 문자열을 파이썬 객체로 변환
            for result in results:
                result['food_items'] = json.loads(result['food_items'])
                if result['dietary_restrictions']:
                    result['dietary_restrictions'] = json.loads(result['dietary_restrictions'])
                if result['health_goals']:
                    result['health_goals'] = json.loads(result['health_goals'])
            
            return results
        except Exception as e:
            logger.error(f"식단 조언 기록 조회 중 오류 발생: {str(e)}")
            return []
    
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
            # 건강 지표 조회 (최신 및 3개월치 시계열 데이터)
            metrics_data = self.get_three_months_health_metrics(user_id)
            
            # 사용자 기본 정보 조회 (생년월일 포함)
            conn = None
            user_info = {}
            try:
                # 새로운 연결 생성
                conn = self.db.connect()
                
                # 기존 연결을 닫고 새로 연결하여 최신 데이터 확인
                if hasattr(conn, 'ping'):
                    conn.ping(reconnect=True)
                
                # 사용자 정보 조회 쿼리 (생년월일 포함)
                user_query = """
                    SELECT user_id, social_id, provider, gender, birth_date, created_at
                    FROM social_accounts
                    WHERE user_id = %s
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(user_query, (user_id,))
                    user_result = cursor.fetchone()
                    
                    if user_result:
                        user_info = {
                            'user_id': user_result['user_id'],
                            'social_id': user_result['social_id'],
                            'provider': user_result['provider'],
                            'gender': user_result['gender'],
                            'birth_date': user_result['birth_date'],
                            'created_at': user_result['created_at']
                        }
                        logger.info(f"사용자 정보 조회 완료: {user_id}, 생년월일: {user_result['birth_date']}")
                
                # 최신 gemini_response 조회
                gemini_query = """
                    SELECT gemini_response
                    FROM health_metrics
                    WHERE user_id = %s AND gemini_response IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                
                with conn.cursor() as cursor:
                    cursor.execute(gemini_query, (user_id,))
                    result = cursor.fetchone()
                
                # 명시적으로 커밋하여 트랜잭션 완료
                conn.commit()
                
                latest_gemini_response = result['gemini_response'] if result else None
                logger.info(f"최신 gemini_response 조회 완료: {latest_gemini_response is not None}")
            finally:
                # 연결 종료는 Database 클래스에서 관리
                pass
            
            # 식이 제한 조회
            dietary_restrictions = self.get_dietary_restrictions(user_id)
            
            # 통합 프로필 구성
            profile = {
                'user_id': user_id,
                'health_metrics': metrics_data.get('latest', {}),
                'health_metrics_history': metrics_data.get('time_series', {}),
                'dietary_restrictions': dietary_restrictions or [],
                'gemini_response': latest_gemini_response,
                'last_updated': datetime.now().isoformat()
            }
            
            # 사용자 정보 추가
            if user_info:
                profile.update(user_info)
            
            logger.info(f"종합 건강 프로필 조회 성공: 사용자 {user_id}")
            return profile
        except Exception as e:
            logger.error(f"종합 건강 프로필 조회 오류: {str(e)}")
            raise
    
    def save_exercise_recommendation(self, recommendation: ExerciseRecommendation) -> bool:
        """
        운동 추천 정보 저장
        
        Args:
            recommendation: ExerciseRecommendation 모델
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            logger.info(f"[HealthDAO] 운동 추천 정보 저장 시작: {recommendation.recommendation_id}")
            
            # JSON 필드 직렬화
            exercise_plans_json = json.dumps(recommendation.exercise_plans, ensure_ascii=False)
            special_instructions_json = json.dumps(recommendation.special_instructions, ensure_ascii=False)
            available_equipment_json = json.dumps(recommendation.available_equipment, ensure_ascii=False)
            exercise_constraints_json = json.dumps(recommendation.exercise_constraints, ensure_ascii=False)
            
            logger.debug(f"[HealthDAO] JSON 필드 직렬화 완료")
            
            # 동일 날짜에 기존 레코드가 있는지 확인
            check_query = """
            SELECT recommendation_id FROM exercise_recommendations
            WHERE user_id = %s AND DATE(timestamp) = DATE(%s)
            """
            
            existing_record = self.db.fetch_one(check_query, (recommendation.user_id, recommendation.timestamp))
            
            if existing_record:
                # 기존 레코드가 있으면 업데이트
                logger.info(f"[HealthDAO] 동일 날짜의 기존 운동 추천 레코드 발견: {existing_record['recommendation_id']}, 업데이트 수행")
                
                update_query = """
                UPDATE exercise_recommendations SET
                    goal = %s,
                    fitness_level = %s,
                    recommended_frequency = %s,
                    exercise_plans = %s,
                    special_instructions = %s,
                    recommendation_summary = %s,
                    timestamp = %s,
                    exercise_location = %s,
                    preferred_exercise_type = %s,
                    available_equipment = %s,
                    time_per_session = %s,
                    experience_level = %s,
                    intensity_preference = %s,
                    exercise_constraints = %s
                WHERE recommendation_id = %s
                """
                
                params = (
                    recommendation.goal,
                    recommendation.fitness_level,
                    recommendation.recommended_frequency,
                    exercise_plans_json,
                    special_instructions_json,
                    recommendation.recommendation_summary,
                    recommendation.timestamp,
                    recommendation.exercise_location,
                    recommendation.preferred_exercise_type,
                    available_equipment_json,
                    recommendation.time_per_session,
                    recommendation.experience_level,
                    recommendation.intensity_preference,
                    exercise_constraints_json,
                    existing_record['recommendation_id']
                )
                
                affected_rows = self.db.execute_query(update_query, params)
                
                # 추천 ID를 기존 ID로 업데이트 (일관성 유지)
                recommendation.recommendation_id = existing_record['recommendation_id']
                
                logger.info(f"[HealthDAO] 운동 추천 정보 업데이트 성공: {existing_record['recommendation_id']}, 영향 받은 행: {affected_rows}")
            else:
                # 기존 레코드가 없으면 새로 삽입
                logger.info(f"[HealthDAO] 새 운동 추천 정보 삽입: {recommendation.recommendation_id}")
                
                insert_query = """
                INSERT INTO exercise_recommendations (
                    recommendation_id, user_id, goal, fitness_level, recommended_frequency,
                    exercise_plans, special_instructions, recommendation_summary, timestamp,
                    exercise_location, preferred_exercise_type, available_equipment,
                    time_per_session, experience_level, intensity_preference, exercise_constraints
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                params = (
                    recommendation.recommendation_id,
                    recommendation.user_id,
                    recommendation.goal,
                    recommendation.fitness_level,
                    recommendation.recommended_frequency,
                    exercise_plans_json,
                    special_instructions_json,
                    recommendation.recommendation_summary,
                    recommendation.timestamp,
                    recommendation.exercise_location,
                    recommendation.preferred_exercise_type,
                    available_equipment_json,
                    recommendation.time_per_session,
                    recommendation.experience_level,
                    recommendation.intensity_preference,
                    exercise_constraints_json
                )
                
                affected_rows = self.db.execute_query(insert_query, params)
                logger.info(f"[HealthDAO] 새 운동 추천 정보 저장 성공: {recommendation.recommendation_id}, 영향 받은 행: {affected_rows}")
            
            return True
        except Exception as e:
            logger.error(f"[HealthDAO] 운동 추천 정보 저장 중 오류: {str(e)}")
            logger.exception("[HealthDAO] 상세 오류 정보:")
            return False
    
    def get_exercise_recommendation(self, recommendation_id: str) -> Optional[ExerciseRecommendation]:
        """
        특정 운동 추천 정보 조회
        
        Args:
            recommendation_id: 운동 추천 ID
            
        Returns:
            Optional[ExerciseRecommendation]: 운동 추천 정보
        """
        try:
            sql = """
            SELECT recommendation_id, user_id, goal, fitness_level, recommended_frequency,
                   exercise_plans, special_instructions, recommendation_summary, timestamp,
                   exercise_location, preferred_exercise_type, available_equipment,
                   time_per_session, experience_level, intensity_preference, exercise_constraints
            FROM exercise_recommendations
            WHERE recommendation_id = %s
            """
            
            result = self.db.fetch_one(sql, (recommendation_id,))
            
            if not result:
                return None
            
            # JSON 필드 파싱
            exercise_plans = json.loads(result['exercise_plans']) if result['exercise_plans'] else []
            special_instructions = json.loads(result['special_instructions']) if result['special_instructions'] else []
            available_equipment = json.loads(result['available_equipment']) if result['available_equipment'] else []
            exercise_constraints = json.loads(result['exercise_constraints']) if result['exercise_constraints'] else []
            
            # 운동 완료 여부 확인
            completed = self.check_exercise_completion(recommendation_id)
            
            # ExerciseRecommendation 객체 생성
            recommendation = ExerciseRecommendation(
                recommendation_id=result['recommendation_id'],
                user_id=result['user_id'],
                goal=result['goal'],
                exercise_plans=exercise_plans,
                fitness_level=result['fitness_level'],
                recommended_frequency=result['recommended_frequency'],
                special_instructions=special_instructions,
                recommendation_summary=result['recommendation_summary'],
                timestamp=result['timestamp'],
                exercise_location=result['exercise_location'],
                preferred_exercise_type=result['preferred_exercise_type'],
                available_equipment=available_equipment,
                time_per_session=result['time_per_session'],
                experience_level=result['experience_level'],
                intensity_preference=result['intensity_preference'],
                exercise_constraints=exercise_constraints,
                completed=completed
            )
            
            logger.info(f"[HealthDAO] 운동 추천 정보 조회 성공: {recommendation_id}")
            return recommendation
        except Exception as e:
            logger.error(f"[HealthDAO] 운동 추천 정보 조회 중 오류: {str(e)}")
            return None
            
    def get_user_exercise_recommendations(self, user_id: str, limit: int = 10) -> List[ExerciseRecommendation]:
        """
        사용자 운동 추천 목록 조회
        
        Args:
            user_id: 사용자 ID
            limit: 조회 개수 제한
            
        Returns:
            List[ExerciseRecommendation]: 운동 추천 목록
        """
        try:
            sql = """
            SELECT recommendation_id, user_id, goal, fitness_level, recommended_frequency,
                   exercise_plans, special_instructions, recommendation_summary, timestamp,
                   exercise_location, preferred_exercise_type, available_equipment,
                   time_per_session, experience_level, intensity_preference, exercise_constraints
            FROM exercise_recommendations
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """
            
            results = self.db.fetch_all(sql, (user_id, limit))
            
            recommendations = []
            for result in results:
                # JSON 필드 파싱
                exercise_plans = json.loads(result['exercise_plans']) if result['exercise_plans'] else []
                special_instructions = json.loads(result['special_instructions']) if result['special_instructions'] else []
                available_equipment = json.loads(result['available_equipment']) if result['available_equipment'] else []
                exercise_constraints = json.loads(result['exercise_constraints']) if result['exercise_constraints'] else []
                
                # 운동 완료 여부 확인
                completed = self.check_exercise_completion(result['recommendation_id'])
                
                # ExerciseRecommendation 객체 생성
                recommendation = ExerciseRecommendation(
                    recommendation_id=result['recommendation_id'],
                    user_id=result['user_id'],
                    goal=result['goal'],
                    exercise_plans=exercise_plans,
                    fitness_level=result['fitness_level'],
                    recommended_frequency=result['recommended_frequency'],
                    special_instructions=special_instructions,
                    recommendation_summary=result['recommendation_summary'],
                    timestamp=result['timestamp'],
                    exercise_location=result['exercise_location'],
                    preferred_exercise_type=result['preferred_exercise_type'],
                    available_equipment=available_equipment,
                    time_per_session=result['time_per_session'],
                    experience_level=result['experience_level'],
                    intensity_preference=result['intensity_preference'],
                    exercise_constraints=exercise_constraints,
                    completed=completed
                )
                recommendations.append(recommendation)
            
            logger.info(f"[HealthDAO] 최근 1달 내 사용자 운동 추천 목록 조회 성공: 사용자 {user_id}, {len(recommendations)}개 결과")
            return recommendations
        except Exception as e:
            logger.error(f"[HealthDAO] 사용자 운동 추천 목록 조회 중 오류: {str(e)}")
            return []
    
    def update_exercise_completion(self, recommendation_id: str, completed: bool) -> bool:
        """운동 완료 상태를 업데이트한다.
        
        Args:
            recommendation_id: 업데이트할 운동 추천 ID
            completed: 완료 여부
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            update_query = """
            UPDATE exercise_recommendations 
            SET completed = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE recommendation_id = %s
            """
            affected_rows = self.db.execute_query(update_query, (completed, recommendation_id))
            
            if affected_rows > 0:
                logger.info(f"운동 완료 상태 업데이트 성공: ID {recommendation_id}, 완료 상태: {completed}")
                return True
            else:
                logger.warning(f"운동 추천 정보를 찾을 수 없음: ID {recommendation_id}")
                return False
        except Exception as e:
            logger.error(f"운동 완료 상태 업데이트 중 오류 발생: {str(e)}")
            return False
    
    def schedule_exercise(self, recommendation_id: str, scheduled_time: datetime) -> bool:
        """운동 시간을 예약한다.
        
        Args:
            recommendation_id: 업데이트할 운동 추천 ID
            scheduled_time: 예약 시간
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            update_query = """
            UPDATE exercise_recommendations 
            SET scheduled_time = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE recommendation_id = %s
            """
            affected_rows = self.db.execute_query(update_query, (scheduled_time, recommendation_id))
            
            if affected_rows > 0:
                logger.info(f"운동 시간 예약 성공: ID {recommendation_id}, 예약 시간: {scheduled_time}")
                return True
            else:
                logger.warning(f"운동 추천 정보를 찾을 수 없음: ID {recommendation_id}")
                return False
        except Exception as e:
            logger.error(f"운동 시간 예약 중 오류 발생: {str(e)}")
            return False
    
    def save_exercise_schedule(self, schedule: ExerciseSchedule) -> bool:
        """
        운동 스케줄을 저장합니다.
        
        Args:
            schedule: 저장할 운동 스케줄 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 이미 동일한 요일, 시간에 스케줄이 있는지 확인
            check_query = """
            SELECT schedule_id FROM exercise_schedules
            WHERE user_id = %s AND day_of_week = %s AND time_of_day = %s AND is_active = TRUE
            """
            existing_record = self.db.fetch_one(check_query, (
                schedule.user_id, 
                schedule.day_of_week, 
                schedule.time_of_day.strftime('%H:%M:%S')
            ))
            
            if existing_record:
                # 기존 레코드가 있으면 업데이트
                logger.info(f"동일한 요일과 시간에 기존 스케줄을 발견하여 업데이트합니다. 기존 ID: {existing_record['schedule_id']}")
                
                update_query = """
                UPDATE exercise_schedules
                SET 
                    recommendation_id = %s,
                    duration_minutes = %s,
                    notification_enabled = %s,
                    notification_minutes_before = %s,
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE schedule_id = %s
                """
                
                self.db.execute_query(update_query, (
                    schedule.recommendation_id,
                    schedule.duration_minutes,
                    schedule.notification_enabled,
                    schedule.notification_minutes_before,
                    schedule.is_active,
                    existing_record['schedule_id']
                ))
                
                logger.info(f"운동 스케줄 업데이트 성공: ID {existing_record['schedule_id']}")
                
                # schedule 객체의 ID를 기존 ID로 업데이트 (일관성 유지)
                schedule.schedule_id = existing_record['schedule_id']
                
                return True
            else:
                # 새 레코드 삽입
                insert_query = """
                INSERT INTO exercise_schedules (
                    schedule_id, recommendation_id, user_id, day_of_week, time_of_day,
                    duration_minutes, notification_enabled, notification_minutes_before,
                    is_active, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                self.db.execute_query(insert_query, (
                    schedule.schedule_id,
                    schedule.recommendation_id,
                    schedule.user_id,
                    schedule.day_of_week,
                    schedule.time_of_day.strftime('%H:%M:%S'),
                    schedule.duration_minutes,
                    schedule.notification_enabled,
                    schedule.notification_minutes_before,
                    schedule.is_active
                ))
                
                logger.info(f"새 운동 스케줄 저장 성공: ID {schedule.schedule_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"운동 스케줄 저장 중 오류 발생: {str(e)}")
            return False
    
    def get_exercise_schedules_by_recommendation(self, recommendation_id: str) -> List[ExerciseSchedule]:
        """
        특정 운동 추천의 스케줄 목록을 조회합니다.
        
        Args:
            recommendation_id: 조회할 운동 추천 ID
            
        Returns:
            List[ExerciseSchedule]: 운동 스케줄 목록
        """
        try:
            query = """
            SELECT * FROM exercise_schedules
            WHERE recommendation_id = %s AND is_active = TRUE
            ORDER BY day_of_week, time_of_day
            """
            results = self.db.fetch_all(query, (recommendation_id,))
            
            schedules = []
            for result in results:
                schedule = ExerciseSchedule(
                    schedule_id=result['schedule_id'],
                    recommendation_id=result['recommendation_id'],
                    user_id=result['user_id'],
                    day_of_week=result['day_of_week'],
                    time_of_day=datetime.strptime(str(result['time_of_day']), '%H:%M:%S').time(),
                    duration_minutes=result['duration_minutes'],
                    notification_enabled=result['notification_enabled'],
                    notification_minutes_before=result['notification_minutes_before'],
                    is_active=result['is_active'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at']
                )
                schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            logger.error(f"운동 스케줄 목록 조회 중 오류 발생: {str(e)}")
            return []
    
    def get_user_exercise_schedules(self, user_id: str) -> List[ExerciseSchedule]:
        """
        사용자의 모든 운동 스케줄을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            List[ExerciseSchedule]: 운동 스케줄 목록
        """
        try:
            query = """
            SELECT * FROM exercise_schedules
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY day_of_week, time_of_day
            """
            results = self.db.fetch_all(query, (user_id,))
            
            schedules = []
            for result in results:
                schedule = ExerciseSchedule(
                    schedule_id=result['schedule_id'],
                    recommendation_id=result['recommendation_id'],
                    user_id=result['user_id'],
                    day_of_week=result['day_of_week'],
                    time_of_day=datetime.strptime(str(result['time_of_day']), '%H:%M:%S').time(),
                    duration_minutes=result['duration_minutes'],
                    notification_enabled=result['notification_enabled'],
                    notification_minutes_before=result['notification_minutes_before'],
                    is_active=result['is_active'],
                    created_at=result['created_at'],
                    updated_at=result['updated_at']
                )
                schedules.append(schedule)
            
            return schedules
            
        except Exception as e:
            logger.error(f"사용자 운동 스케줄 목록 조회 중 오류 발생: {str(e)}")
            return []
    
    def get_recent_diet_advice_history(self, user_id: str, months: int = 1) -> List[Dict[str, Any]]:
        """
        사용자의 최근 식단 조언 기록을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            months: 가져올 기간(월 단위, 기본값 1)
            
        Returns:
            List[Dict[str, Any]]: 최근 식단 조언 기록 목록
        """
        try:
            # months 개월 전 날짜 계산
            months_ago = (datetime.now() - timedelta(days=30 * months)).strftime('%Y-%m-%d')
            
            query = """
            SELECT meal_date, meal_type, 
                   food_items, dietary_restrictions, created_at
            FROM diet_advice_history
            WHERE user_id = %s AND meal_date >= %s
            ORDER BY meal_date DESC, created_at DESC
            """
            
            results = self.db.fetch_all(query, (user_id, months_ago))
            
            diet_history = []
            for result in results:
                # JSON 필드 파싱
                food_items = json.loads(result['food_items']) if result['food_items'] else []
                dietary_restrictions = json.loads(result['dietary_restrictions']) if result['dietary_restrictions'] else []
                
                record = {
                    'meal_date': result['meal_date'],
                    'meal_type': result['meal_type'],
                    'food_items': food_items,
                    'dietary_restrictions': dietary_restrictions,
                    'created_at': result['created_at']
                }
                diet_history.append(record)
            
            logger.info(f"최근 {months}개월 식단 조언 기록 {len(diet_history)}개 조회 성공: 사용자 {user_id}")
            return diet_history
            
        except Exception as e:
            logger.error(f"최근 식단 조언 기록 조회 중 오류 발생: {str(e)}")
            return []
    
    def save_exercise_completion(self, completion: ExerciseCompletion) -> bool:
        """
        운동 완료 기록을 저장합니다.
        
        Args:
            completion: 저장할 운동 완료 기록 객체
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            insert_query = """
            INSERT INTO exercise_completions (
                completion_id, schedule_id, recommendation_id, user_id,
                completed_at, satisfaction_rating, feedback, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """
            
            self.db.execute_query(insert_query, (
                completion.completion_id,
                completion.schedule_id,
                completion.recommendation_id,
                completion.user_id,
                completion.completed_at,
                completion.satisfaction_rating,
                completion.feedback
            ))
            
            logger.info(f"운동 완료 기록 저장 성공: ID {completion.completion_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"운동 완료 기록 저장 중 오류 발생: {str(e)}")
            return False
    
    def get_exercise_completions_by_schedule(self, schedule_id: str, limit: int = 10) -> List[ExerciseCompletion]:
        """
        특정 스케줄의 완료 기록을 조회합니다.
        
        Args:
            schedule_id: 조회할 스케줄 ID
            limit: 최대 반환 결과 수
            
        Returns:
            List[ExerciseCompletion]: 운동 완료 기록 목록
        """
        try:
            query = """
            SELECT * FROM exercise_completions
            WHERE schedule_id = %s
            ORDER BY completed_at DESC
            LIMIT %s
            """
            results = self.db.fetch_all(query, (schedule_id, limit))
            
            completions = []
            for result in results:
                completion = ExerciseCompletion(
                    completion_id=result['completion_id'],
                    schedule_id=result['schedule_id'],
                    recommendation_id=result['recommendation_id'],
                    user_id=result['user_id'],
                    completed_at=result['completed_at'],
                    satisfaction_rating=result['satisfaction_rating'],
                    feedback=result['feedback'],
                    created_at=result['created_at']
                )
                completions.append(completion)
            
            return completions
            
        except Exception as e:
            logger.error(f"운동 완료 기록 조회 중 오류 발생: {str(e)}")
            return []
    
    def check_exercise_completion(self, recommendation_id: str) -> bool:
        """
        특정 운동 추천에 대한 완료 기록이 있는지 확인합니다.
        
        Args:
            recommendation_id: 확인할 운동 추천 ID
            
        Returns:
            bool: 완료 기록이 있으면 True, 없으면 False
        """
        try:
            query = """
            SELECT COUNT(*) as completion_count 
            FROM exercise_completions
            WHERE recommendation_id = %s
            """
            result = self.db.fetch_one(query, (recommendation_id,))
            
            if result and result['completion_count'] > 0:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"운동 완료 여부 확인 중 오류 발생: {str(e)}")
            return False
    
    def get_today_schedules_for_notification(self, minutes_threshold: int = 30) -> List[Dict[str, Any]]:
        """
        오늘 알림이 필요한 운동 스케줄을 조회합니다.
        
        Args:
            minutes_threshold: 현재 시간으로부터 몇 분 후의 스케줄을 가져올지 설정
            
        Returns:
            List[Dict]: 알림이 필요한 스케줄 정보 목록 (사용자 정보 포함)
        """
        try:
            # 현재 요일 및 시간 계산
            now = datetime.now()
            day_of_week = now.weekday()  # 월요일=0, 일요일=6
            if day_of_week == 6:  # 일요일이면 0으로 변환
                day_of_week = 0
            else:  # 그 외에는 월요일이 1, 화요일이 2, ... 토요일이 6이 되도록 +1
                day_of_week += 1
            
            # 현재 시간 + minutes_threshold 분 후의 시간 계산
            notification_time = (now + timedelta(minutes=minutes_threshold)).time()
            
            query = """
            SELECT es.*, sa.social_id, sa.provider, sa.gender, er.goal, er.recommendation_summary
            FROM exercise_schedules es
            JOIN social_accounts sa ON es.user_id = sa.user_id
            JOIN exercise_recommendations er ON es.recommendation_id = er.recommendation_id
            WHERE es.day_of_week = %s
            AND es.time_of_day BETWEEN %s AND DATE_ADD(%s, INTERVAL 5 MINUTE)
            AND es.is_active = TRUE
            AND es.notification_enabled = TRUE
            """
            
            time_str = notification_time.strftime('%H:%M:%S')
            results = self.db.fetch_all(query, (day_of_week, time_str, time_str))
            
            notification_schedules = []
            for result in results:
                notification_schedules.append({
                    'schedule_id': result['schedule_id'],
                    'recommendation_id': result['recommendation_id'],
                    'user_id': result['user_id'],
                    'social_id': result['social_id'],
                    'provider': result['provider'],
                    'gender': result['gender'],
                    'day_of_week': result['day_of_week'],
                    'time_of_day': str(result['time_of_day']),
                    'duration_minutes': result['duration_minutes'],
                    'goal': result['goal'],
                    'recommendation_summary': result['recommendation_summary']
                })
            
            return notification_schedules
            
        except Exception as e:
            logger.error(f"알림이 필요한 스케줄 조회 중 오류 발생: {str(e)}")
            return [] 