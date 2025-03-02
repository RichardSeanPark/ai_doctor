import os
import asyncio
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
import logfire
import logging
import base64
import uuid

from app.models.user_profile import UserProfile, UserGoal, HealthMetrics
from app.models.health_data import SymptomReport, HealthAssessment, DietEntry
from app.models.diet_plan import MealRecommendation, FoodImageData
from app.models.notification import UserState, AndroidNotification, VoiceResponse

from app.graphs.diet_graph import create_diet_analysis_graph, create_food_image_graph
from app.graphs.health_check_graph import create_health_metrics_graph, create_symptom_analysis_graph
from app.graphs.voice_consultation_graph import create_voice_query_graph, create_voice_consultation_graph
from app.graphs.notification_graph import create_notification_graph, create_motivational_notification_graph

from langgraph.graph import END

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HealthAIApplication:
    """건강 관리 AI 애플리케이션의 메인 클래스"""
    
    def __init__(self):
        self.logger = logger
        self.logger.info("건강 관리 AI 애플리케이션 초기화 중...")
        
        # 그래프 초기화
        self.diet_analysis_graph = create_diet_analysis_graph()
        self.food_image_graph = create_food_image_graph()
        self.health_metrics_graph = create_health_metrics_graph()
        self.symptom_analysis_graph = create_symptom_analysis_graph()
        self.voice_query_graph = create_voice_query_graph()
        self.voice_consultation_graph = create_voice_consultation_graph()
        self.notification_graph = create_notification_graph()
        self.motivational_notification_graph = create_motivational_notification_graph()
        
        # 샘플 사용자 생성 (실제로는 DB에서 로드)
        self.current_user = self._create_sample_user()
        
        self.logger.info("건강 관리 AI 애플리케이션 초기화 완료")
    
    def _create_sample_user(self) -> UserProfile:
        """샘플 사용자 프로필 생성"""
        return UserProfile(
            user_id="user123",
            name="홍길동",
            birth_date=date(1985, 5, 15),
            gender="남성",
            goals=[
                UserGoal(
                    goal_type="체중감량",
                    target_value=75.0,
                    deadline=date(2023, 12, 31)
                )
            ],
            current_metrics=HealthMetrics(
                weight=82.5,
                height=178.0,
                bmi=26.0,
                body_fat_percentage=25.0,
                blood_pressure={"systolic": 130, "diastolic": 85},
                heart_rate=72,
                sleep_hours=6.5
            ),
            dietary_restrictions=["고당류 제한"],
            medical_conditions=["경도 고혈압"]
        )
    
    def _create_user_state(self, additional_data: Optional[Dict] = None) -> UserState:
        """사용자 상태 객체 생성"""
        user_data = self.current_user.dict()
        
        state = UserState(
            user_profile=user_data,
            voice_scripts=[],
            notifications=[],
            voice_segments=[]
        )
        
        if additional_data:
            for key, value in additional_data.items():
                setattr(state, key, value)
        
        return state
    
    async def analyze_diet(self, meals_data: Dict) -> MealRecommendation:
        """식단 분석 및 추천 수행"""
        self.logger.info("식단 분석 시작")
        
        # 사용자 상태 생성
        state = self._create_user_state({"recent_meals": meals_data})
        
        # 그래프 실행
        result = await self.diet_analysis_graph.ainvoke(state)
        
        self.logger.info("식단 분석 완료")
        self._print_voice_scripts(state.voice_scripts)
        self._print_notifications(state.notifications)
        
        return result
    
    async def analyze_food_image(self, image_data: Dict) -> DietEntry:
        """음식 이미지 분석 수행"""
        self.logger.info("음식 이미지 분석 시작")
        
        # 이미지 데이터 검증
        if not image_data:
            self.logger.error("이미지 데이터가 없습니다")
            raise ValueError("이미지 데이터가 필요합니다")
        
        # 이미지 ID 생성 및 기본 데이터 설정
        image_id = str(uuid.uuid4())
        user_id = self.current_user.user_id
        
        # FoodImageData 객체 생성 (필요시)
        if "image_object" not in image_data:
            food_image_data = FoodImageData(
                image_id=image_id,
                user_id=user_id,
                timestamp=datetime.now(),
                image_base64=image_data.get("image_base64"),
                image_url=image_data.get("image_url"),
                meal_type=image_data.get("meal_type", "식사"),
                location=image_data.get("location")
            )
            image_data["image_object"] = food_image_data
        
        # 사용자 상태 생성
        state = self._create_user_state()
        
        # 그래프 실행
        self.logger.info(f"음식 이미지 분석 그래프 실행 - 식사 유형: {image_data.get('meal_type', '알 수 없음')}")
        result = await self.food_image_graph.ainvoke(state, {"image_data": image_data})
        
        self.logger.info("음식 이미지 분석 완료")
        self._print_voice_scripts(state.voice_scripts)
        
        # 음식 이미지 분석 결과가 DietEntry 객체인지 확인
        if hasattr(result, 'entry_id'):
            return result
        else:
            self.logger.warning("이미지 분석에서 식단 정보를 추출할 수 없습니다")
            # 기본 DietEntry 생성 (실제 구현에서는 더 적절한 처리 필요)
            meal_id = str(uuid.uuid4())
            entry_id = str(uuid.uuid4())
            return DietEntry(
                meal_id=meal_id,
                entry_id=entry_id,
                user_id=user_id,
                timestamp=datetime.now(),
                meal_type=image_data.get("meal_type", "식사"),
                food_items=[],
                total_calories=0.0,
                nutrition_data={},
                image_id=image_id,
                notes="이미지에서 식단 정보를 추출할 수 없습니다."
            )
    
    async def check_health_metrics(self) -> HealthAssessment:
        """건강 지표 분석 수행"""
        self.logger.info("건강 지표 분석 시작")
        
        # 사용자 상태 생성
        state = self._create_user_state()
        
        # 그래프 실행
        result = await self.health_metrics_graph.ainvoke(state)
        
        self.logger.info("건강 지표 분석 완료")
        self._print_voice_scripts(state.voice_scripts)
        self._print_notifications(state.notifications)
        
        return result
    
    async def analyze_symptoms(self, symptoms_data: Dict) -> HealthAssessment:
        """증상 분석 수행"""
        self.logger.info("증상 분석 시작")
        
        # 사용자 상태 생성
        state = self._create_user_state()
        
        # 그래프 실행
        result = await self.symptom_analysis_graph.ainvoke(state, {"symptoms_data": symptoms_data})
        
        self.logger.info("증상 분석 완료")
        self._print_voice_scripts(state.voice_scripts)
        self._print_notifications(state.notifications)
        
        return result
    
    async def process_voice_query(self, query_text: str, user_id: str = None) -> List[str]:
        """음성 질의 처리"""
        self.logger.info(f"음성 질의 처리 시작: {query_text}")
        
        # user_id가 제공되면 사용하고, 그렇지 않으면 현재 사용자 ID 사용
        user_id = user_id or self.current_user.user_id
        
        # 사용자 상태 생성
        state = self._create_user_state({"voice_input": query_text, "user_id": user_id})
        
        # 그래프 실행
        try:
            result = await self.voice_query_graph.ainvoke(state, {"voice_data": {"text": query_text}})
            
            self.logger.info("음성 질의 처리 완료")
            
            # 음성 스크립트에서 응답 가져오기
            if state.voice_scripts:
                return state.voice_scripts
            
            # 음성 세그먼트에서 응답 가져오기
            if state.voice_segments:
                voice_segments_text = []
                for segment in state.voice_segments:
                    if hasattr(segment, 'text'):
                        voice_segments_text.append(segment.text)
                    elif isinstance(segment, dict) and 'text' in segment:
                        voice_segments_text.append(segment['text'])
                    elif isinstance(segment, str):
                        voice_segments_text.append(segment)
                return voice_segments_text
            
            # last_response에서 응답 가져오기
            if state.last_response and hasattr(state.last_response, 'response_text'):
                return [state.last_response.response_text]
            
            # 마지막 수단으로 기본 응답 반환
            return ["요청에 대한 응답을 생성할 수 없습니다."]
        except Exception as e:
            self.logger.error(f"음성 질의 처리 중 오류 발생: {e}")
            self.logger.exception(e)  # 디버깅용 스택 트레이스 출력
            return ["음성 질의 처리 중 오류가 발생했습니다."]
    
    async def conduct_health_consultation(self, progress_data: Dict) -> List[str]:
        """건강 상담 세션 수행"""
        self.logger.info("건강 상담 세션 시작")
        
        # 사용자 상태 생성
        state = self._create_user_state({"progress_data": progress_data})
        
        try:
            # 그래프 실행
            result = await self.voice_consultation_graph.ainvoke(state, {"consultation_data": progress_data})
            
            self.logger.info("건강 상담 세션 완료")
            
            # 음성 세그먼트 처리
            voice_segments_text = []
            for segment in state.voice_segments:
                if hasattr(segment, 'text'):
                    voice_segments_text.append(segment.text)
                elif isinstance(segment, dict) and 'text' in segment:
                    voice_segments_text.append(segment['text'])
                elif isinstance(segment, str):
                    voice_segments_text.append(segment)
            
            return voice_segments_text
        except Exception as e:
            self.logger.error(f"건강 상담 세션 중 오류 발생: {e}")
            return ["건강 상담 세션 중 오류가 발생했습니다."]
    
    async def send_motivational_notification(self, progress_data: Dict) -> AndroidNotification:
        """동기부여 알림 생성 및 전송"""
        self.logger.info("동기부여 알림 생성 시작")
        
        # 사용자 상태 생성
        state = self._create_user_state({"progress_data": progress_data})
        
        # 그래프 실행
        result = await self.motivational_notification_graph.ainvoke(state)
        
        self.logger.info("동기부여 알림 전송 완료")
        
        return result
    
    def _print_voice_scripts(self, scripts: List[str]) -> None:
        """음성 스크립트 출력 (디버깅용)"""
        if not scripts:
            return
        
        self.logger.info("음성 스크립트:")
        for i, script in enumerate(scripts, 1):
            self.logger.info(f"  {i}. {script}")
    
    def _print_notifications(self, notifications: List[AndroidNotification]) -> None:
        """알림 출력 (디버깅용)"""
        if not notifications:
            return
        
        self.logger.info("알림:")
        for i, notification in enumerate(notifications, 1):
            self.logger.info(f"  {i}. [{notification.priority}] {notification.title}: {notification.body}")

async def main():
    """메인 함수"""
    app = HealthAIApplication()
    
    # 샘플 식단 데이터
    sample_meals = {
        "meals": [
            {
                "meal_type": "아침",
                "food_items": [
                    {"name": "통밀빵", "amount": "2쪽", "calories": 150},
                    {"name": "스크램블 에그", "amount": "1인분", "calories": 220},
                    {"name": "오렌지 주스", "amount": "1잔", "calories": 110}
                ]
            },
            {
                "meal_type": "점심",
                "food_items": [
                    {"name": "비빔밥", "amount": "1인분", "calories": 550},
                    {"name": "미역국", "amount": "1공기", "calories": 100}
                ]
            }
        ]
    }
    
    # 샘플 이미지 데이터 (실제로는 이미지 파일을 Base64로 인코딩)
    sample_image_data = {
        "meal_type": "점심",
        "image_base64": "샘플_이미지_Base64_문자열",  # 실제 구현에서는 진짜 이미지 데이터
        "location": "집"
    }
    
    # 샘플 증상 데이터
    sample_symptoms = {
        "symptoms": [
            {
                "symptom_name": "두통",
                "severity": 6,
                "onset_time": datetime.now()
            },
            {
                "symptom_name": "어지러움",
                "severity": 4,
                "onset_time": datetime.now()
            }
        ]
    }
    
    # 샘플 진행 데이터
    sample_progress = {
        "percentage": 65,
        "recent_activities": ["매일 걷기 30분", "식단 조절", "수면 개선"]
    }
    
    # 건강 체크 테스트
    await app.check_health_metrics()
    
    # 식단 분석 테스트
    await app.analyze_diet(sample_meals)
    
    # 식품 이미지 분석 테스트
    await app.analyze_food_image(sample_image_data)
    
    # 증상 분석 테스트
    await app.analyze_symptoms(sample_symptoms)
    
    # 음성 질의 테스트
    await app.process_voice_query("매일 할 수 있는 간단한 운동 추천해줘")
    
    # 건강 상담 테스트
    await app.conduct_health_consultation(sample_progress)
    
    # 동기부여 알림 테스트
    await app.send_motivational_notification(sample_progress)

if __name__ == "__main__":
    asyncio.run(main())
