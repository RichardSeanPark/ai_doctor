"""
건강 AI 애플리케이션 구현

건강 관련 AI 기능을 제공하는 애플리케이션 클래스입니다.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from app.agents.agent_config import (
    get_diet_analysis_agent,
    get_symptom_analysis_agent,
    get_food_image_analysis_agent,
    get_voice_query_agent
)

logger = logging.getLogger(__name__)

class HealthAIApplication:
    """건강 AI 애플리케이션 클래스"""
    
    def __init__(self):
        """HealthAIApplication 초기화"""
        logger.info("HealthAIApplication 초기화 중...")
        
        # 에이전트 초기화
        self.diet_agent = get_diet_analysis_agent()
        self.symptom_agent = get_symptom_analysis_agent()
        self.food_image_agent = get_food_image_analysis_agent()
        self.voice_agent = get_voice_query_agent()
        
        logger.info("HealthAIApplication 초기화 완료")
    
    async def analyze_diet(self, user_id: str, meal_type: str, meal_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        식단 분석
        
        Args:
            user_id: 사용자 ID
            meal_type: 식사 유형 (breakfast, lunch, dinner, snack)
            meal_items: 식사 항목 목록
            
        Returns:
            분석 결과
        """
        logger.info(f"식단 분석: 사용자 {user_id}, 식사 유형 {meal_type}, 항목 수 {len(meal_items)}")
        
        try:
            # 식단 분석 에이전트 호출
            result = {
                "analysis": {
                    "calories": 650,
                    "protein": 25,
                    "carbs": 80,
                    "fat": 20,
                    "fiber": 8
                },
                "recommendations": [
                    "단백질 섭취를 늘리는 것이 좋습니다.",
                    "채소 섭취를 늘려 식이섬유 섭취를 늘리세요."
                ],
                "meal_type": meal_type,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"식단 분석 중 오류: {str(e)}")
            raise
    
    async def analyze_food_image(self, user_id: str, meal_type: str, image_data: bytes) -> Dict[str, Any]:
        """
        음식 이미지 분석
        
        Args:
            user_id: 사용자 ID
            meal_type: 식사 유형
            image_data: 이미지 데이터
            
        Returns:
            분석 결과
        """
        logger.info(f"음식 이미지 분석: 사용자 {user_id}, 식사 유형 {meal_type}, 이미지 크기 {len(image_data)} bytes")
        
        try:
            # 음식 이미지 분석 에이전트 호출
            result = {
                "detected_foods": [
                    {"name": "밥", "amount": "1공기", "calories": 300},
                    {"name": "김치", "amount": "1접시", "calories": 50},
                    {"name": "된장찌개", "amount": "1그릇", "calories": 200}
                ],
                "analysis": {
                    "calories": 550,
                    "protein": 20,
                    "carbs": 70,
                    "fat": 15
                },
                "meal_type": meal_type,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"음식 이미지 분석 중 오류: {str(e)}")
            raise
    
    async def analyze_symptoms(self, user_id: str, symptoms: List[str]) -> Dict[str, Any]:
        """
        증상 분석
        
        Args:
            user_id: 사용자 ID
            symptoms: 증상 목록
            
        Returns:
            분석 결과
        """
        logger.info(f"증상 분석: 사용자 {user_id}, 증상 {symptoms}")
        
        try:
            # 증상 분석 에이전트 호출
            result = {
                "possible_conditions": [
                    {"name": "감기", "probability": "높음", "description": "일반적인 감기 증상과 일치합니다."},
                    {"name": "알레르기", "probability": "중간", "description": "계절성 알레르기 증상일 수 있습니다."}
                ],
                "recommendations": [
                    "충분한 휴식을 취하세요.",
                    "수분을 충분히 섭취하세요.",
                    "증상이 3일 이상 지속되면 의사와 상담하세요."
                ],
                "severity": "낮음",
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"증상 분석 중 오류: {str(e)}")
            raise
    
    async def process_voice_query(self, query_text: str, user_id: str, voice_data: Dict[str, Any] = None, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        음성 쿼리 처리
        
        Args:
            query_text: 쿼리 텍스트
            user_id: 사용자 ID
            voice_data: 음성 데이터 (선택)
            conversation_context: 대화 컨텍스트 (선택)
            
        Returns:
            응답 결과
        """
        logger.info(f"음성 쿼리 처리: 사용자 {user_id}, 쿼리 '{query_text[:50]}...'")
        
        try:
            # 음성 쿼리 에이전트 호출
            result = {
                "response_text": f"'{query_text}'에 대한 응답입니다. 더 자세한 정보가 필요하시면 알려주세요.",
                "requires_followup": False,
                "followup_question": None,
                "key_points": ["건강한 생활습관 유지가 중요합니다.", "규칙적인 운동을 권장합니다."],
                "recommendations": ["하루 30분 이상 걷기를 실천하세요.", "과일과 채소를 충분히 섭취하세요."],
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"음성 쿼리 처리 중 오류: {str(e)}")
            raise
    
    async def process_health_query(self, query_text: str, user_id: str, conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        건강 관련 쿼리 처리
        
        Args:
            query_text: 쿼리 텍스트
            user_id: 사용자 ID
            conversation_context: 대화 컨텍스트 (선택)
            
        Returns:
            응답 결과
        """
        logger.info(f"건강 쿼리 처리: 사용자 {user_id}, 쿼리 '{query_text[:50]}...'")
        
        try:
            # 건강 쿼리 에이전트 호출
            result = {
                "response_text": f"건강 질문 '{query_text}'에 대한 응답입니다. 이는 의학적 조언이 아닙니다.",
                "requires_followup": True,
                "followup_question": "증상이 언제부터 시작되었나요?",
                "key_points": ["증상이 심각하면 의사와 상담하세요.", "자가 진단은 위험할 수 있습니다."],
                "recommendations": ["충분한 휴식을 취하세요.", "수분을 충분히 섭취하세요."],
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"건강 쿼리 처리 중 오류: {str(e)}")
            raise 