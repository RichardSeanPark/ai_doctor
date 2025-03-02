"""
안드로이드 앱과의 통신을 담당하는 서비스 모듈
"""

import json
import logging
import asyncio
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, messaging

from app.models.health_data import HealthAssessment
from app.main import HealthAIApplication

# 로깅 설정
logger = logging.getLogger(__name__)

class AndroidServiceError(Exception):
    """안드로이드 서비스 오류"""
    pass


class AndroidCommunicationService:
    """안드로이드 앱과의 통신을 담당하는 서비스 클래스"""
    
    def __init__(self, health_ai_app: HealthAIApplication = None):
        """서비스 초기화"""
        self.health_ai_app = health_ai_app or HealthAIApplication()
        self.firebase_app = None
        self.device_tokens = {}  # 사용자별 FCM 토큰 저장
        
        # Firebase 초기화 시도
        try:
            self._initialize_firebase()
        except Exception as e:
            logger.warning(f"Firebase 초기화 실패: {str(e)}. 알림 기능이 비활성화됩니다.")
    
    def _initialize_firebase(self):
        """Firebase 초기화 (FCM 푸시 알림용)"""
        try:
            # Firebase 초기화
            if not firebase_admin._apps:
                # 실제 환경에서는 환경 변수 또는 안전한 저장소에서 불러오는 것이 좋습니다
                cred_path = "path/to/firebase-credentials.json"
                try:
                    cred = credentials.Certificate(cred_path)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase가 성공적으로 초기화되었습니다.")
                except Exception as e:
                    logger.error(f"Firebase 인증서 로드 실패: {str(e)}")
                    # 개발 모드에서는 기본 앱으로 초기화
                    self.firebase_app = firebase_admin.initialize_app()
        except Exception as e:
            logger.error(f"Firebase 초기화 중 오류 발생: {str(e)}")
            raise
    
    async def process_user_profile_update(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 프로필 업데이트 처리"""
        try:
            user_id = profile_data.get("user_id")
            if not user_id:
                raise AndroidServiceError("사용자 ID가 누락되었습니다")
            
            logger.info(f"사용자 프로필 업데이트 처리: {user_id}")
            
            # 여기에 프로필 저장 로직 구현
            # 실제 환경에서는 데이터베이스에 저장
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "프로필이 성공적으로 업데이트되었습니다."
            }
        except Exception as e:
            logger.error(f"프로필 업데이트 처리 오류: {str(e)}")
            raise AndroidServiceError(f"프로필 업데이트 처리 실패: {str(e)}")
    
    async def process_voice_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """음성 쿼리 처리"""
        try:
            logger.info(f"음성 쿼리 처리: {user_id}, 쿼리: {query}")
            
            # HealthAIApplication을 통한 음성 쿼리 처리
            result = await self.health_ai_app.process_voice_query(query, user_id=user_id)
            
            if not result:
                return {
                    "success": True,
                    "response_text": "질문을 이해하지 못했습니다. 다시 말씀해 주세요.",
                    "voice_segments": [],
                    "voice_scripts": []
                }
            
            return {
                "success": True,
                "response_text": result.get("text", ""),
                "voice_segments": result.get("voice_segments", []),
                "voice_scripts": result.get("voice_scripts", [])
            }
        except Exception as e:
            logger.error(f"음성 쿼리 처리 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_text": "음성 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }
    
    async def process_diet_analysis(
        self, 
        user_id: str, 
        meal_type: str, 
        meal_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """식단 분석 처리"""
        try:
            logger.info(f"식단 분석 처리: {user_id}, 식사 유형: {meal_type}, 항목 수: {len(meal_items)}")
            
            # HealthAIApplication을 통한 식단 분석
            result = await self.health_ai_app.analyze_diet(
                user_id=user_id,
                meal_type=meal_type,
                meal_items=meal_items
            )
            
            # 분석 결과에 음성 스크립트 추가
            voice_script = self._generate_diet_voice_script(result)
            
            return {
                "success": True,
                "analysis_result": result,
                "voice_script": voice_script
            }
        except Exception as e:
            logger.error(f"식단 분석 처리 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "식단 분석 중 오류가 발생했습니다."
            }
    
    def _generate_diet_voice_script(self, diet_analysis: Dict[str, Any]) -> str:
        """식단 분석 결과를 음성 스크립트로 변환"""
        try:
            total_calories = diet_analysis.get("total_calories", 0)
            suggestions = diet_analysis.get("suggestions", [])
            
            script = f"분석 결과, 해당 식사의 총 칼로리는 {total_calories}kcal입니다. "
            
            if suggestions:
                script += f"개선 사항으로는, {suggestions[0]}"
                if len(suggestions) > 1:
                    script += f" 그리고 {suggestions[1]}"
                script += "가 있습니다."
            else:
                script += "전반적으로 균형 잡힌 식사입니다."
                
            return script
        except Exception as e:
            logger.error(f"음성 스크립트 생성 오류: {str(e)}")
            return "식단 분석이 완료되었습니다."
    
    async def process_food_image_analysis(
        self, 
        user_id: str, 
        meal_type: str, 
        image_data: bytes
    ) -> Dict[str, Any]:
        """음식 이미지 분석 처리"""
        try:
            logger.info(f"음식 이미지 분석 처리: {user_id}, 식사 유형: {meal_type}, 이미지 크기: {len(image_data)} bytes")
            
            # HealthAIApplication을 통한 음식 이미지 분석
            result = await self.health_ai_app.analyze_food_image(
                user_id=user_id,
                meal_type=meal_type,
                image_data=image_data
            )
            
            # 이미지 분석 결과에 음성 스크립트 추가
            voice_script = self._generate_food_image_voice_script(result)
            
            return {
                "success": True,
                "analysis_result": result,
                "voice_script": voice_script
            }
        except Exception as e:
            logger.error(f"음식 이미지 분석 처리 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "음식 이미지 분석 중 오류가 발생했습니다."
            }
    
    def _generate_food_image_voice_script(self, food_analysis: Dict[str, Any]) -> str:
        """음식 이미지 분석 결과를 음성 스크립트로 변환"""
        try:
            food_items = food_analysis.get("food_items", [])
            total_calories = food_analysis.get("total_calories", 0)
            
            if not food_items:
                return "이미지에서 음식을 인식하지 못했습니다. 더 밝은 환경에서 다시 시도해 보세요."
            
            food_names = ", ".join([item.get("name", "알 수 없는 음식") for item in food_items[:3]])
            
            script = f"이미지에서 {food_names}"
            
            if len(food_items) > 3:
                script += f" 외 {len(food_items) - 3}개의 음식"
                
            script += f"을 인식했습니다. 총 칼로리는 약 {total_calories}kcal로 추정됩니다."
            
            return script
        except Exception as e:
            logger.error(f"음식 이미지 음성 스크립트 생성 오류: {str(e)}")
            return "음식 이미지 분석이 완료되었습니다."
    
    async def process_health_check(
        self, 
        user_id: str, 
        symptoms: Optional[List[str]] = None,
        health_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """건강 상태 확인 처리"""
        try:
            logger.info(f"건강 상태 확인 처리: {user_id}, 증상 수: {len(symptoms) if symptoms else 0}")
            
            result = {}
            
            # 건강 지표 업데이트 (있는 경우)
            if health_metrics:
                # 여기에 건강 지표 업데이트 로직 추가
                logger.info(f"건강 지표 업데이트: {health_metrics}")
                # 로직 구현...
                result["updated_metrics"] = True
            
            # 증상 분석 (있는 경우)
            if symptoms and len(symptoms) > 0:
                # HealthAIApplication을 통한 증상 분석
                assessment = await self.health_ai_app.analyze_symptoms(
                    user_id=user_id,
                    symptoms=symptoms
                )
                
                result["assessment"] = assessment
                
                # 중요한 건강 문제가 있는 경우 푸시 알림 전송
                if assessment and assessment.get("severity", "low") in ["medium", "high"]:
                    await self._send_health_alert_notification(user_id, assessment)
            
            # 결과가 비어있는 경우
            if not result:
                return {
                    "success": True,
                    "message": "건강 상태 확인을 위한 데이터가 충분하지 않습니다.",
                    "needs_more_data": True
                }
            
            return {
                "success": True,
                "result": result,
                "message": "건강 상태 확인이 완료되었습니다."
            }
        except Exception as e:
            logger.error(f"건강 상태 확인 처리 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "건강 상태 확인 중 오류가 발생했습니다."
            }
    
    async def _send_health_alert_notification(self, user_id: str, assessment: Dict[str, Any]):
        """건강 경고 푸시 알림 전송"""
        try:
            # 사용자의 FCM 토큰 조회
            device_token = self.device_tokens.get(user_id)
            if not device_token:
                logger.warning(f"사용자 {user_id}의 FCM 토큰이 등록되지 않았습니다. 알림을 전송할 수 없습니다.")
                return
            
            # 알림 메시지 구성
            severity = assessment.get("severity", "low")
            summary = assessment.get("summary", "건강 상태에 주의가 필요합니다.")
            
            title = "건강 알림"
            body = summary
            
            if severity == "high":
                title = "⚠️ 긴급 건강 알림"
                body = f"중요: {summary} 전문가와 상담하는 것이 좋습니다."
            elif severity == "medium":
                title = "⚠️ 건강 주의 알림"
            
            # FCM 메시지 생성
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data={
                    "type": "health_alert",
                    "severity": severity,
                    "assessment_id": assessment.get("assessment_id", ""),
                    "timestamp": datetime.now().isoformat()
                },
                token=device_token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        icon="ic_stat_health_alert",
                        color="#f45342",
                        channel_id="health_alerts"
                    )
                )
            )
            
            # FCM으로 알림 전송
            if self.firebase_app:
                response = messaging.send(message)
                logger.info(f"FCM 알림 전송 완료: {response}")
            else:
                logger.warning("Firebase가 초기화되지 않아 알림을 전송할 수 없습니다.")
                
        except Exception as e:
            logger.error(f"건강 알림 전송 오류: {str(e)}")
    
    async def start_voice_consultation(
        self, 
        user_id: str, 
        consultation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """음성 상담 세션 시작"""
        try:
            logger.info(f"음성 상담 세션 시작: {user_id}")
            
            # HealthAIApplication을 통한 음성 상담 수행
            result = await self.health_ai_app.conduct_health_consultation(
                user_id=user_id,
                consultation_data=consultation_data
            )
            
            return {
                "success": True,
                "consultation_id": result.get("consultation_id", ""),
                "voice_segments": result.get("voice_segments", []),
                "voice_scripts": result.get("voice_scripts", []),
                "follow_up_date": result.get("follow_up_date", "")
            }
        except Exception as e:
            logger.error(f"음성 상담 세션 시작 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "음성 상담 세션 시작 중 오류가 발생했습니다."
            }
    
    def register_device_token(self, user_id: str, device_token: str, settings: Dict[str, Any] = None) -> bool:
        """FCM 알림을 위한 디바이스 토큰 등록"""
        try:
            logger.info(f"디바이스 토큰 등록: {user_id}, 토큰: {device_token[:10]}...")
            
            # 사용자 디바이스 토큰 저장
            self.device_tokens[user_id] = device_token
            
            # 설정 저장 (필요한 경우)
            if settings:
                # 구현...
                pass
            
            return True
        except Exception as e:
            logger.error(f"디바이스 토큰 등록 오류: {str(e)}")
            return False
    
    async def send_notification(
        self, 
        user_id: str, 
        title: str, 
        body: str, 
        data: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> bool:
        """사용자에게 푸시 알림 전송"""
        try:
            device_token = self.device_tokens.get(user_id)
            if not device_token:
                logger.warning(f"사용자 {user_id}의 FCM 토큰이 등록되지 않았습니다. 알림을 전송할 수 없습니다.")
                return False
            
            # Firebase 앱이 초기화되지 않은 경우
            if not self.firebase_app:
                logger.warning("Firebase가 초기화되지 않아 알림을 전송할 수 없습니다.")
                return False
            
            # 알림 데이터 기본값 설정
            notification_data = data or {}
            notification_data.update({
                "timestamp": datetime.now().isoformat(),
                "notification_id": str(uuid.uuid4())
            })
            
            # FCM 메시지 생성
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=notification_data,
                token=device_token,
                android=messaging.AndroidConfig(
                    priority="high" if priority == "high" else "normal",
                    notification=messaging.AndroidNotification(
                        icon="ic_stat_notification",
                        color="#4285F4",
                        channel_id="general_notifications" if priority != "high" else "health_alerts"
                    )
                )
            )
            
            # FCM으로 알림 전송
            response = messaging.send(message)
            logger.info(f"FCM 알림 전송 완료: {response}")
            
            return True
        except Exception as e:
            logger.error(f"알림 전송 오류: {str(e)}")
            return False 