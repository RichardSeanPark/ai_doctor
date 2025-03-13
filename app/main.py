import os
import asyncio
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
import logfire
import logging
import base64
import uuid
import json

from app.models.user_profile import UserProfile, UserGoal, HealthMetrics
from app.models.health_data import SymptomReport, HealthAssessment, DietEntry
from app.models.diet_plan import MealRecommendation, FoodImageData
from app.models.notification import UserState, AndroidNotification, VoiceResponse

from app.graphs.diet_graph import create_diet_analysis_graph, create_food_image_graph
from app.graphs.health_check_graph import create_health_metrics_graph, create_symptom_analysis_graph
from app.graphs.voice_consultation_graph import create_voice_query_graph, create_voice_consultation_graph
from app.graphs.notification_graph import create_notification_graph, create_motivational_notification_graph

from langgraph.graph import END, StateGraph
from app.nodes.health_check_nodes import analyze_health_metrics
from app.config.settings import Settings

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
    
    async def process_voice_query(self, query_text: str, user_id: str = None, context: Dict[str, Any] = None) -> List[str]:
        """
        음성 질의 처리
        
        Args:
            query_text: 처리할 질의 텍스트
            user_id: 사용자 ID (없으면 현재 사용자 ID 사용)
            context: 대화 컨텍스트 정보 (없으면 사용 안함)
        
        Returns:
            음성 응답 텍스트 목록
        """
        self.logger.info(f"음성 질의 처리 시작: {query_text}")
        
        # 빈 쿼리 처리
        if not query_text or query_text.strip() == "":
            self.logger.warning("빈 쿼리가 비어있어 처리할 수 없습니다.")
            return ["죄송합니다. 음성 쿼리가 비어있어 처리할 수 없습니다. 다시 말씀해 주세요."]
            
        # user_id가 제공되면 사용하고, 그렇지 않으면 현재 사용자 ID 사용
        user_id = user_id or self.current_user.user_id
        self.logger.info(f"사용자 ID: {user_id}")
        
        # 사용자 상태 생성
        state = self._create_user_state({
            "voice_input": query_text, 
            "user_id": user_id
        })
        self.logger.info("사용자 상태 객체 생성 완료")
        
        # 대화 컨텍스트가 있으면 상태에 추가
        if context:
            state.conversation_context = context
            self.logger.info(f"대화 컨텍스트 정보 추가됨: {len(context)} 항목")
        
        # 그래프 실행
        try:
            self.logger.info(f"음성 질의 그래프 실행 시작 - 쿼리: '{query_text}'")
            
            try:
                # 상태에 직접 voice_data 설정
                state.voice_data = {"text": query_text}
                self.logger.info(f"상태에 voice_data 설정: {state.voice_data}")
            except Exception as e:
                # voice_data 설정 실패 시 config로 전달
                self.logger.warning(f"상태에 voice_data 설정 실패: {str(e)}")
                config = {
                    "voice_data": {"text": query_text},
                    "conversation_context": context
                }
                self.logger.info(f"대신 config로 전달: {config}")
                result = await self.voice_query_graph.ainvoke(state, config)
                self.logger.info(f"음성 질의 처리 완료 (config 사용) - 결과 타입: {type(result)}")
                
                # 결과가 딕셔너리인 경우 직접 처리
                if isinstance(result, dict):
                    self.logger.info(f"결과 딕셔너리 키: {list(result.keys())}")
                    
                    # 'scripts' 키가 직접 존재하는 경우
                    if 'scripts' in result and result['scripts']:
                        self.logger.info(f"결과에서 'scripts' 키를 직접 찾음: {len(result['scripts'])}개")
                        return result['scripts']
                    
                    # 'segments' 키가 직접 존재하는 경우
                    if 'segments' in result and result['segments']:
                        segments_text = []
                        for segment in result['segments']:
                            if hasattr(segment, 'text'):
                                segments_text.append(segment.text)
                            elif isinstance(segment, dict) and 'text' in segment:
                                segments_text.append(segment['text'])
                            elif isinstance(segment, str):
                                segments_text.append(segment)
                        if segments_text:
                            self.logger.info(f"결과에서 직접 segment 텍스트 추출: {len(segments_text)}개")
                            return segments_text
                
                # 결과가 딕셔너리가 아닌 경우, 기본값 반환
                self.logger.warning(f"알 수 없는 결과 타입: {type(result)}")
                return ["죄송합니다. 응답을 처리하는 중에 오류가 발생했습니다. 다시 시도해주세요."]
                
            # 직접 그래프 실행 (대화 컨텍스트 포함)
            config = {"conversation_context": context} if context else {}
            result = await self.voice_query_graph.ainvoke(state, config)
            self.logger.info(f"음성 질의 처리 완료 - 결과 타입: {type(result)}")
            
            # 결과 형식에 따른 처리
            if isinstance(result, dict):
                self.logger.info(f"결과 딕셔너리 키: {list(result.keys())}")
            
            # voice_segments 추출 함수 호출
            response = self._get_voice_segments(result)
            self.logger.info(f"_get_voice_segments 함수 결과: {len(response)}개")
            
            # 응답 반환
            return response
            
        except Exception as e:
            self.logger.error(f"음성 질의 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return [f"죄송합니다. 음성 질의 처리 중 오류가 발생했습니다: {str(e)}"]
            
    async def process_health_query(self, query_text: str, user_id: str = None, context: Dict[str, Any] = None) -> List[str]:
        """
        건강 상담 쿼리 처리
        
        Args:
            query_text: 처리할 질의 텍스트
            user_id: 사용자 ID (없으면 현재 사용자 ID 사용)
            context: 대화 컨텍스트 정보 (없으면 사용 안함)
        
        Returns:
            건강 상담 응답 텍스트 목록
        """
        self.logger.info(f"건강 상담 쿼리 처리 시작: {query_text}")
        
        # 빈 쿼리 처리
        if not query_text or query_text.strip() == "":
            self.logger.warning("빈 건강 상담 쿼리가 전달되었습니다.")
            return ["죄송합니다. 건강 상담 쿼리가 비어있어 처리할 수 없습니다. 다시 말씀해 주세요."]
            
        # user_id가 제공되면 사용하고, 그렇지 않으면 현재 사용자 ID 사용
        user_id = user_id or self.current_user.user_id
        self.logger.info(f"사용자 ID: {user_id}, 건강 상담 쿼리 시작")
        
        # 사용자 상태 생성
        state = self._create_user_state({
            "voice_input": query_text, 
            "user_id": user_id,
            "query_type": "health"  # 쿼리 타입을 health로 설정
        })
        self.logger.info("건강 상담용 사용자 상태 객체 생성 완료")
        
        # 대화 컨텍스트가 있으면 상태에 추가
        if context:
            state.conversation_context = context
            self.logger.info(f"건강 상담 대화 컨텍스트 정보 추가됨: {len(context)} 항목")
        
        # 그래프 실행
        try:
            self.logger.info(f"건강 상담 그래프(health_metrics_graph) 실행 시작 - 쿼리: '{query_text}'")
            
            # 상태에 voice_data 설정 (health_metrics_graph에서도 이 형식 사용)
            state.voice_data = {"text": query_text}
            self.logger.info(f"상태에 건강 상담 voice_data 설정: {state.voice_data}")
            
            # health_metrics_graph 실행 (대화 컨텍스트 포함)
            config = {"conversation_context": context} if context else {}
            result = await self.health_metrics_graph.ainvoke(state, config)
            self.logger.info(f"건강 상담 그래프 처리 완료 - 결과 타입: {type(result)}")
            
            # 결과 형식에 따른 처리
            if isinstance(result, dict):
                self.logger.info(f"건강 상담 결과 딕셔너리 키: {list(result.keys())}")
                
                # 건강 평가 결과 확인
                if hasattr(result, 'health_assessment') and result.health_assessment:
                    assessment = result.health_assessment
                    self.logger.info(f"건강 평가 결과: {assessment.assessment_summary[:50]}...")
                    
                    # 건강 평가 결과를 텍스트로 변환
                    response_text = [
                        f"건강 평가 결과: {assessment.assessment_summary}",
                        "건강 이슈:",
                    ]
                    
                    # 이슈가 있으면 추가
                    if assessment.issues:
                        for issue in assessment.issues:
                            response_text.append(f"- {issue}")
                    else:
                        response_text.append("- 특별한 건강 이슈가 발견되지 않았습니다.")
                    
                    # 권장 사항 추가
                    response_text.append("권장 사항:")
                    if assessment.recommendations:
                        for rec in assessment.recommendations:
                            response_text.append(f"- {rec}")
                    else:
                        response_text.append("- 특별한 권장 사항이 없습니다.")
                    
                    self.logger.info(f"건강 평가 응답 생성: {len(response_text)}줄")
                    return response_text
            
            # 기본 응답
            self.logger.info("건강 평가 결과를 찾을 수 없어 voice_segments에서 응답 추출 시도")
            
            # voice_segments 추출 함수 호출 (fallback 처리)
            response = self._get_voice_segments(result)
            if response:
                self.logger.info(f"건강 상담 _get_voice_segments 함수 결과: {len(response)}개")
                return response
            
            # 모든 방법이 실패한 경우 기본 응답 반환
            self.logger.warning("건강 상담 결과를 추출할 수 없어 기본 응답 생성")
            return ["건강 상담을 완료했습니다. 특별한 건강 이슈는 발견되지 않았습니다. 정기적인 건강 체크를 권장합니다."]
            
        except Exception as e:
            self.logger.error(f"건강 상담 쿼리 처리 중 오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return [f"죄송합니다. 건강 상담 처리 중 오류가 발생했습니다: {str(e)}"]
    
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
        """알림 목록 출력"""
        print("\n=== 알림 목록 ===")
        for idx, notification in enumerate(notifications, start=1):
            print(f"알림 {idx}: {notification.title}")
            print(f"내용: {notification.body}")
            print(f"우선순위: {notification.priority}")
            print("---")
        print("===============\n")
        
    def _get_voice_segments(self, state) -> List[str]:
        """상태 객체에서 음성 세그먼트 텍스트 추출"""
        # 상태 객체 타입 확인
        self.logger.info(f"_get_voice_segments 실행: state 타입 - {type(state)}")
        
        # LangGraph의 AddableValuesDict 타입 특별 처리
        is_addable_dict = str(type(state)) == "<class 'langgraph.pregel.io.AddableValuesDict'>"
        is_dict_like = isinstance(state, dict) or is_addable_dict
        
        # 상태가 딕셔너리 또는 유사 딕셔너리인 경우(LangGraph 출력 형태)
        if is_dict_like:
            self.logger.info(f"state가 딕셔너리 또는 유사 딕셔너리: 키 - {list(state.keys())}")
            
            # "segments" 키를 통해 직접 접근하는 경우
            if "segments" in state:
                segments = state["segments"]
                self.logger.info(f"state['segments'] 존재 - 갯수: {len(segments)}")
                voice_segments_text = []
                for segment in segments:
                    if hasattr(segment, 'text'):
                        voice_segments_text.append(segment.text)
                    elif isinstance(segment, dict) and 'text' in segment:
                        voice_segments_text.append(segment['text'])
                    elif isinstance(segment, str):
                        voice_segments_text.append(segment)
                if voice_segments_text:
                    self.logger.info(f"음성 세그먼트 텍스트 추출 성공: {len(voice_segments_text)}개")
                    return voice_segments_text
            
            # "scripts" 키를 통해 직접 접근하는 경우
            if "scripts" in state:
                scripts = state["scripts"]
                self.logger.info(f"state['scripts'] 존재 - 갯수: {len(scripts)}")
                if scripts:
                    self.logger.info(f"스크립트 추출 성공: {len(scripts)}개")
                    return scripts
                
            # voice_scripts 키 확인 (LangGraph에서의 상태 변수)
            if "voice_scripts" in state and state["voice_scripts"]:
                voice_scripts = state["voice_scripts"]
                self.logger.info(f"state['voice_scripts'] 존재 - 갯수: {len(voice_scripts)}")
                if voice_scripts:
                    self.logger.info(f"voice_scripts 추출 성공: {len(voice_scripts)}개")
                    return voice_scripts
                
            # voice_segments 키 확인 (LangGraph에서의 상태 변수)
            if "voice_segments" in state and state["voice_segments"]:
                voice_segments = state["voice_segments"]
                self.logger.info(f"state['voice_segments'] 존재 - 갯수: {len(voice_segments)}")
                voice_segments_text = []
                for segment in voice_segments:
                    if hasattr(segment, 'text'):
                        voice_segments_text.append(segment.text)
                    elif isinstance(segment, dict) and 'text' in segment:
                        voice_segments_text.append(segment['text'])
                    elif isinstance(segment, str):
                        voice_segments_text.append(segment)
                if voice_segments_text:
                    self.logger.info(f"voice_segments에서 텍스트 추출 성공: {len(voice_segments_text)}개")
                    return voice_segments_text
                
            # last_response 키 확인 (응답 객체에서 텍스트 추출)
            if "last_response" in state and state["last_response"]:
                last_response = state["last_response"]
                self.logger.info(f"state['last_response'] 존재 - 타입: {type(last_response)}")
                
                # response_text 속성이 있는 경우
                if hasattr(last_response, 'response_text'):
                    self.logger.info(f"last_response.response_text 추출 성공: {len(last_response.response_text)} 글자")
                    return [last_response.response_text]
                # 딕셔너리인 경우
                elif isinstance(last_response, dict) and 'response_text' in last_response:
                    self.logger.info(f"last_response['response_text'] 추출 성공: {len(last_response['response_text'])} 글자")
                    return [last_response['response_text']]
                
            # 이 외의 경우는 기존 로직으로 처리 시도
            self.logger.warning("직접 접근으로 결과를 찾을 수 없어 기존 로직 시도")
                
        # 상태 객체 디버깅 (속성 접근)
        has_last_response = False
        has_voice_segments = False
        has_voice_scripts = False
        
        # 속성 접근 시도
        if hasattr(state, 'last_response') and state.last_response:
            self.logger.info(f"state.last_response 존재 - ID: {getattr(state.last_response, 'response_id', 'ID 없음')}")
            has_last_response = True
        else:
            self.logger.warning("state.last_response 값이 없음")
            
        if hasattr(state, 'voice_segments') and state.voice_segments:
            self.logger.info(f"state.voice_segments 존재 - 갯수: {len(state.voice_segments)}")
            has_voice_segments = True
        else:
            self.logger.warning("state.voice_segments 값이 없음")
            
        if hasattr(state, 'voice_scripts') and state.voice_scripts:
            self.logger.info(f"state.voice_scripts 존재 - 갯수: {len(state.voice_scripts)}")
            has_voice_scripts = True
        else:
            self.logger.warning("state.voice_scripts 값이 없음")
        
        # 음성 스크립트에서 응답 가져오기 (속성 접근)
        if has_voice_scripts:
            self.logger.info(f"음성 스크립트 반환 - 첫 스크립트 처음 50자: {state.voice_scripts[0][:50]}...")
            return state.voice_scripts
        
        # 음성 세그먼트에서 응답 가져오기 (속성 접근)
        if has_voice_segments:
            voice_segments_text = []
            for segment in state.voice_segments:
                if hasattr(segment, 'text'):
                    voice_segments_text.append(segment.text)
                elif isinstance(segment, dict) and 'text' in segment:
                    voice_segments_text.append(segment['text'])
                elif isinstance(segment, str):
                    voice_segments_text.append(segment)
            self.logger.info(f"음성 세그먼트 텍스트 반환 - 첫 세그먼트: {voice_segments_text[0][:50] if voice_segments_text else '없음'}...")
            return voice_segments_text
        
        # last_response에서 응답 가져오기 (속성 접근)
        if has_last_response and hasattr(state.last_response, 'response_text'):
            self.logger.info(f"last_response.response_text 반환: {state.last_response.response_text[:50]}...")
            return [state.last_response.response_text]
        
        # 마지막 수단으로 기본 응답 반환
        self.logger.warning("응답을 찾을 수 없어 기본 응답 반환")
        return ["요청에 대한 응답을 생성할 수 없습니다. 다시 시도해 주세요."]

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
    await app.process_health_query("건강 상담 쿼리 테스트")
    
    # 동기부여 알림 테스트
    await app.send_motivational_notification(sample_progress)

if __name__ == "__main__":
    asyncio.run(main())
