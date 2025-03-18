#!/usr/bin/env python
"""
RealGeminiAgent 모방 테스트

이 스크립트는 프로젝트의 RealGeminiAgent와 유사한 방식으로 구현하여 테스트합니다.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Union, Tuple, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# Gemini API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

# Gemini API 구성
genai.configure(api_key=GOOGLE_API_KEY)

class TestRealGeminiAgent:
    """RealGeminiAgent를 모방한 테스트 클래스"""
    
    def __init__(self, model: str = "gemini-2.0-pro-exp-02-05", temperature: float = 0.2):
        """초기화 함수"""
        self.model_name = model
        self.temperature = temperature
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"temperature": self.temperature}
        )
        logger.info(f"TestRealGeminiAgent 초기화: model={model}, temp={temperature}")
    
    async def ainvoke(self, input_text: str) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Gemini API 비동기 호출 - RealGeminiAgent.ainvoke 유사 구현
        
        반환:
        - 문자열 또는 (문자열, 딕셔너리) 튜플
        """
        try:
            logger.info(f"실제 Gemini API 호출: {input_text[:50]}...")
            
            # Gemini API 호출
            response = await asyncio.to_thread(self.model.generate_content, input_text)
            
            # 응답 로깅
            if hasattr(response, "text"):
                logger.info(f"Gemini API 응답 수신 (처음 50자): {response.text[:50]}...")
            
            # 응답 처리 - 첫 번째 반환값
            result_text = response.text if hasattr(response, "text") else str(response)
            
            # JSON 형식 추출 시도
            try:
                # JSON 코드 블록 찾기
                json_start = result_text.find("```json")
                if json_start >= 0:
                    json_text_start = result_text.find("\n", json_start) + 1
                    json_text_end = result_text.find("```", json_text_start)
                    if json_text_end > json_text_start:
                        json_str = result_text[json_text_start:json_text_end].strip()
                        data = json.loads(json_str)
                        # 튜플로 반환 (텍스트, JSON 객체)
                        return (result_text, data)
                
                # 코드 블록이 없는 경우 일반 JSON 찾기
                json_start = result_text.find("{")
                json_end = result_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    try:
                        data = json.loads(json_str)
                        # 튜플로 반환 (텍스트, JSON 객체)
                        return (result_text, data)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logger.error(f"JSON 파싱 오류: {e}")
            
            # JSON 변환 실패 시 텍스트만 반환
            return result_text
            
        except Exception as e:
            logger.error(f"Gemini API 호출 오류: {str(e)}")
            raise

# 테스트 함수들
async def test_without_json():
    """일반 텍스트 응답 테스트"""
    agent = TestRealGeminiAgent()
    input_text = "내 건강 상태는 어떤가요?"
    
    print(f"\n일반 텍스트 응답 테스트 시작...")
    print(f"입력: {input_text}")
    
    result = await agent.ainvoke(input_text)
    
    print(f"결과 타입: {type(result)}")
    
    if isinstance(result, tuple):
        print(f"결과는 튜플입니다. 길이: {len(result)}")
        print(f"첫 번째 요소 (텍스트): {result[0][:100]}...")
        print(f"두 번째 요소 (데이터): {json.dumps(result[1], ensure_ascii=False, indent=2)}")
    else:
        print(f"결과는 단일 값입니다.")
        print(f"값: {result[:100]}...")

async def test_with_json_prompt():
    """JSON 응답 요청 테스트"""
    agent = TestRealGeminiAgent()
    input_text = """
    사용자가 "내 건강 상태는 어떤가요?"라고 질문했습니다.
    
    다음 JSON 형식으로만 응답해주세요:
    ```json
    {
        "health_status": "건강 상태 설명", 
        "concerns": ["우려사항1", "우려사항2"], 
        "recommendations": ["추천사항1", "추천사항2"]
    }
    ```
    """
    
    print(f"\nJSON 응답 요청 테스트 시작...")
    print(f"입력: {input_text[:50]}...")
    
    result = await agent.ainvoke(input_text)
    
    print(f"결과 타입: {type(result)}")
    
    if isinstance(result, tuple):
        print(f"결과는 튜플입니다. 길이: {len(result)}")
        print(f"첫 번째 요소 (텍스트) 일부: {result[0][:100]}...")
        print(f"두 번째 요소 (데이터): {json.dumps(result[1], ensure_ascii=False, indent=2)}")
    else:
        print(f"결과는 단일 값입니다.")
        print(f"값: {result[:100]}...")

async def test_unpacking_error():
    """언패킹 오류 시뮬레이션"""
    agent = TestRealGeminiAgent()
    input_text = """
    다음 JSON 형식으로만 응답해주세요:
    ```json
    {
        "health_status": "건강 상태 설명", 
        "concerns": ["우려사항1", "우려사항2"], 
        "recommendations": ["추천사항1", "추천사항2"]
    }
    ```
    """
    
    print(f"\n언패킹 오류 시뮬레이션 시작...")
    
    # 결과 받기
    result = await agent.ainvoke(input_text)
    
    # 결과 타입 출력
    print(f"결과 타입: {type(result)}")
    
    try:
        # 결과 언패킹 시도 - 에러가 발생할 수 있음
        content, data = result
        print(f"언패킹 성공!")
        print(f"content: {content[:50]}...")
        print(f"data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"언패킹 오류 발생: {str(e)}")
        
        # 해결 방법 보여주기
        if isinstance(result, tuple):
            print("해결 방법 (튜플인 경우): 첫 번째 요소만 사용")
            print(f"첫 번째 요소: {result[0][:50]}...")
        else:
            print("해결 방법 (단일 값인 경우): 그대로 사용")
            print(f"값: {result[:50]}...")

# 메인 함수
async def main():
    """메인 함수"""
    print("=== Gemini API 호출 테스트 시작 ===")
    
    # 일반 텍스트 응답 테스트
    await test_without_json()
    
    # JSON 응답 요청 테스트
    await test_with_json_prompt()
    
    # 언패킹 오류 시뮬레이션
    await test_unpacking_error()
    
    print("\n=== 테스트 완료 ===")

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(main()) 