import os
from typing import Dict, Optional, Any, List, Callable
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Gemini API를 위한 실제 클래스
class RealGeminiAgent:
    """실제 Google Gemini API 구현"""
    
    def __init__(self, model="gemini-1.5-pro", temperature=0.1, **kwargs):
        self.model = model
        self.temperature = temperature
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)
        
        # Google API 키 설정
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            self.logger.error("GOOGLE_API_KEY가 환경 변수에 설정되지 않았습니다.")
            raise ValueError("GOOGLE_API_KEY가 필요합니다.")
        
        # Gemini API 설정
        genai.configure(api_key=api_key)
        self.logger.info(f"RealGeminiAgent 초기화: model={model}, temp={temperature}")
    
    async def ainvoke(self, prompt, **kwargs):
        """비동기 호출 실제 구현"""
        try:
            self.logger.info(f"실제 Gemini API 호출: {str(prompt)[:50]}...")
            
            # 프롬프트에서 입력 텍스트 추출
            input_text = prompt
            if isinstance(prompt, dict) and "input" in prompt:
                input_text = prompt["input"]
            
            # Gemini 모델 생성
            model = genai.GenerativeModel(self.model)
            
            # 모델 구성 설정
            generation_config = {
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # API 호출 및 응답 처리
            response = await model.generate_content_async(
                input_text,
                generation_config=generation_config
            )
            
            # 응답 텍스트 추출
            response_text = response.text
            
            self.logger.info(f"Gemini API 응답 수신 (처음 50자): {response_text[:50]}...")
            
            # 응답 객체 생성
            return {
                "content": response_text,
                "model": self.model,
                "temperature": self.temperature
            }
            
        except Exception as e:
            self.logger.error(f"Gemini API 호출 오류: {str(e)}")
            # 오류 발생 시 기본 응답 반환
            return {
                "content": f"오류 발생: {str(e)}",
                "model": self.model,
                "temperature": self.temperature
            }
    
    def invoke(self, prompt, **kwargs):
        """동기 호출 실제 구현 (주의: 동기 버전은 비동기 함수를 실행하지 않고 간단한 버전으로 구현)"""
        try:
            self.logger.info(f"실제 Gemini API 호출(동기): {str(prompt)[:50]}...")
            
            # 프롬프트에서 입력 텍스트 추출
            input_text = prompt
            if isinstance(prompt, dict) and "input" in prompt:
                input_text = prompt["input"]
            
            # Gemini 모델 생성
            model = genai.GenerativeModel(self.model)
            
            # 모델 구성 설정
            generation_config = {
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # API 호출 및 응답 처리
            response = model.generate_content(
                input_text,
                generation_config=generation_config
            )
            
            # 응답 텍스트 추출
            response_text = response.text
            
            self.logger.info(f"Gemini API 응답 수신 (처음 50자): {response_text[:50]}...")
            
            # 응답 객체 생성
            return {
                "content": response_text,
                "model": self.model,
                "temperature": self.temperature
            }
            
        except Exception as e:
            self.logger.error(f"Gemini API 호출 오류: {str(e)}")
            # 오류 발생 시 기본 응답 반환
            return {
                "content": f"오류 발생: {str(e)}",
                "model": self.model,
                "temperature": self.temperature
            }

# 환경 설정
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

def get_gemini_agent(temperature: float = 0.1) -> RealGeminiAgent:
    """실제 Gemini AI 모델 에이전트를 생성합니다."""
    return RealGeminiAgent(
        model=MODEL_NAME, 
        temperature=temperature
    )

def get_health_agent() -> RealGeminiAgent:
    """건강 상담을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.2)

def get_diet_agent() -> RealGeminiAgent:
    """식이 상담을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.2)

def get_voice_agent() -> RealGeminiAgent:
    """음성 상담을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.3)

def get_notification_agent() -> RealGeminiAgent:
    """알림 생성을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.3)

def get_diet_analysis_agent() -> RealGeminiAgent:
    """식단 분석을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_symptom_analysis_agent() -> RealGeminiAgent:
    """증상 분석을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_food_image_analysis_agent() -> RealGeminiAgent:
    """음식 이미지 분석을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_voice_query_agent() -> RealGeminiAgent:
    """음성 쿼리 처리를 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.3)

def get_conversation_summary_agent() -> RealGeminiAgent:
    """대화 요약을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)

def get_health_entity_extraction_agent() -> RealGeminiAgent:
    """건강 엔티티 추출을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.0)

def get_key_points_extraction_agent() -> RealGeminiAgent:
    """핵심 포인트 추출을 위한 실제 Gemini AI 에이전트를 생성합니다."""
    # 에이전트 생성
    return get_gemini_agent(temperature=0.1)