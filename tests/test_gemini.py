#!/usr/bin/env python
"""
Gemini API 직접 호출 테스트

이 스크립트는 Gemini API를 직접 호출하여 응답 구조를 확인합니다.
"""

import os
import asyncio
import json
from dotenv import load_dotenv
import google.generativeai as genai

# .env 파일 로드
load_dotenv()

# Gemini API 키 설정
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

# Gemini API 구성
genai.configure(api_key=GOOGLE_API_KEY)

async def test_gemini_direct():
    """Gemini API를 직접 호출하여 응답 구조 확인"""
    try:
        print("Gemini API 직접 호출 테스트 시작...")
        
        # 모델 설정
        model_name = "gemini-2.0-pro-exp-02-05"
        model = genai.GenerativeModel(model_name=model_name, generation_config={"temperature": 0.2})
        
        # 간단한 쿼리
        query = "내 건강 상태는 어떤가요?"
        
        # 비동기 호출
        response = await asyncio.to_thread(model.generate_content, query)
        
        # 응답 타입 확인
        print(f"응답 타입: {type(response)}")
        print(f"응답 속성: {dir(response)}")
        
        # 응답 내용 확인
        print("\n응답 텍스트:")
        print(response.text)
        
        # 응답이 튜플인지 확인
        if isinstance(response, tuple):
            print(f"\n응답은 튜플입니다. 길이: {len(response)}")
            for i, item in enumerate(response):
                print(f"항목 {i+1} 타입: {type(item)}")
        else:
            print("\n응답은 튜플이 아닙니다.")
            
            # 응답을 JSON으로 변환 시도
            try:
                if hasattr(response, "text"):
                    json_start = response.text.find("{")
                    json_end = response.text.rfind("}") + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = response.text[json_start:json_end]
                        data = json.loads(json_str)
                        print("\nJSON 파싱 결과:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"JSON 파싱 실패: {e}")
        
        return response
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        raise

async def test_gemini_prompt_with_json():
    """JSON 형식 응답을 요청하는 프롬프트로 Gemini API 호출"""
    try:
        print("\nJSON 형식 응답 요청 테스트 시작...")
        
        # 모델 설정
        model_name = "gemini-2.0-pro-exp-02-05"
        model = genai.GenerativeModel(model_name=model_name, generation_config={"temperature": 0.2})
        
        # JSON 응답을 요청하는 프롬프트
        prompt = """
        사용자가 "내 건강 상태는 어떤가요?"라고 질문했습니다.
        
        다음 JSON 형식으로 응답해주세요:
        ```json
        {
            "health_status": "건강 상태 설명", 
            "concerns": ["우려사항1", "우려사항2"], 
            "recommendations": ["추천사항1", "추천사항2"]
        }
        ```
        
        다른 텍스트는 포함하지 말고, 위 JSON 형식만 정확히 반환해주세요.
        """
        
        # 비동기 호출
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        # 응답 타입 확인
        print(f"응답 타입: {type(response)}")
        
        # 응답 내용 확인
        print("\n응답 텍스트:")
        print(response.text)
        
        # JSON 파싱 시도
        try:
            code_block_start = response.text.find("```json")
            if code_block_start >= 0:
                json_text_start = response.text.find("\n", code_block_start) + 1
                json_text_end = response.text.find("```", json_text_start)
                if json_text_end > json_text_start:
                    json_str = response.text[json_text_start:json_text_end].strip()
                    data = json.loads(json_str)
                    print("\nJSON 파싱 결과:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                # 코드 블록이 없는 경우 전체 텍스트에서 JSON 찾기
                json_start = response.text.find("{")
                json_end = response.text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response.text[json_start:json_end]
                    data = json.loads(json_str)
                    print("\nJSON 파싱 결과:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"JSON 파싱 실패: {e}")
        
        return response
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        raise

# 메인 함수
async def main():
    """메인 함수"""
    # 직접 호출 테스트
    await test_gemini_direct()
    
    # JSON 응답 요청 테스트
    await test_gemini_prompt_with_json()

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(main()) 