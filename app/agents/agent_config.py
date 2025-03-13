import os
from typing import Dict, Optional, Any, List, Callable
import json
import logging

# langchain 관련 임포트 제거하고 모의 클래스 추가
class MockGeminiAgent:
    """Gemini API의 모의 구현"""
    
    def __init__(self, model="gemini-mock", temperature=0.1, **kwargs):
        self.model = model
        self.temperature = temperature
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"MockGeminiAgent 초기화: model={model}, temp={temperature}")
    
    async def ainvoke(self, prompt, **kwargs):
        """비동기 호출 모의 구현"""
        self.logger.info(f"모의 AI 호출: {prompt[:50]}...")
        return {
            "response_text": f"이것은 모의 응답입니다. 실제 Gemini API가 없어 테스트용으로 생성되었습니다.",
            "model": self.model,
            "temperature": self.temperature
        }
    
    def invoke(self, prompt, **kwargs):
        """동기 호출 모의 구현"""
        self.logger.info(f"모의 AI 호출: {prompt[:50]}...")
        return {
            "response_text": f"이것은 모의 응답입니다. 실제 Gemini API가 없어 테스트용으로 생성되었습니다.",
            "model": self.model,
            "temperature": self.temperature
        }

# 환경 설정
API_KEY = os.environ.get("GEMINI_API_KEY", "mock-api-key")
MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-pro")

def get_gemini_agent(temperature: float = 0.1) -> MockGeminiAgent:
    """모의 Gemini AI 모델 에이전트를 생성합니다."""
    return MockGeminiAgent(
        model=MODEL_NAME, 
        temperature=temperature
    )

def get_health_agent() -> MockGeminiAgent:
    """건강 상담을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.2)

def get_diet_agent() -> MockGeminiAgent:
    """식이 상담을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.2)

def get_voice_agent() -> MockGeminiAgent:
    """음성 상담을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.3)

def get_notification_agent() -> MockGeminiAgent:
    """알림 생성을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.3)

def get_diet_analysis_agent() -> MockGeminiAgent:
    """식단 분석을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_symptom_analysis_agent() -> MockGeminiAgent:
    """증상 분석을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_food_image_analysis_agent() -> MockGeminiAgent:
    """음식 이미지 분석을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_voice_query_agent() -> MockGeminiAgent:
    """음성 쿼리 처리를 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.3)

def get_conversation_summary_agent() -> MockGeminiAgent:
    """대화 요약을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_health_entity_extraction_agent() -> MockGeminiAgent:
    """건강 엔티티 추출을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.0)

def get_key_points_extraction_agent() -> MockGeminiAgent:
    """핵심 포인트 추출을 위한 모의 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)