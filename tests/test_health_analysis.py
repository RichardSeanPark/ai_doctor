#!/usr/bin/env python
"""
건강 분석 시나리오 테스트

이 스크립트는 건강 분석 시나리오를 모방하여 테스트합니다.
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

class SimpleGeminiAgent:
    """간소화된 Gemini 에이전트"""
    
    def __init__(self, model: str = "gemini-2.0-pro-exp-02-05", temperature: float = 0.2):
        """초기화 함수"""
        self.model_name = model
        self.temperature = temperature
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={"temperature": self.temperature}
        )
        logger.info(f"SimpleGeminiAgent 초기화: model={model}, temp={temperature}")
    
    async def ainvoke(self, input_text: str) -> Any:
        """Gemini API 비동기 호출"""
        try:
            logger.info(f"Gemini API 호출: {input_text[:50]}...")
            
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

# 사용자 상태를 모방한 간단한 클래스
class SimpleUserState:
    """사용자 상태 (UserState)를 모방한 간단한 클래스"""
    
    def __init__(self, user_id: str, query_text: str, health_metrics: Optional[Dict[str, Any]] = None):
        """초기화 함수"""
        self.user_id = user_id
        self.query_text = query_text
        self.health_metrics = health_metrics or {}
        self.health_assessment = None
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"사용자 ID: {self.user_id}, 쿼리: {self.query_text}, 지표 수: {len(self.health_metrics)}"

# 건강 지표 분석 함수
async def analyze_health_metrics(state: SimpleUserState) -> Dict[str, Any]:
    """
    사용자의 건강 지표를 분석하는 함수
    """
    try:
        logger.info(f"건강 지표 분석 시작 - 사용자 ID: {state.user_id}")
        
        if state.query_text:
            logger.info(f"음성 건강 상담 쿼리 감지: '{state.query_text}'")
        
        if not state.health_metrics:
            logger.warning("분석할 건강 지표가 없습니다")
        
        # Gemini 에이전트 초기화
        agent = SimpleGeminiAgent()
        
        # 프롬프트 구성
        prompt = f"""
        다음 사용자의 건강 지표를 분석하고 평가해주세요:
        
        사용자 ID: {state.user_id}
        질문: {state.query_text}
        
        다음 JSON 형식으로만 응답해주세요:
        ```json
        {{
            "health_status": "정상 | 주의 필요 | 경고", 
            "concerns": ["우려사항1", "우려사항2"], 
            "recommendations": ["추천사항1", "추천사항2", "추천사항3"]
        }}
        ```
        """
        
        logger.info("건강 에이전트 API 호출 시작")
        
        # 에이전트 호출
        result = await agent.ainvoke(prompt)
        
        logger.info("건강 에이전트 API 호출 완료")
        logger.info(f"결과 타입: {type(result)}")
        
        # 결과 처리
        assessment = {}
        
        if isinstance(result, tuple) and len(result) >= 2:
            # 튜플인 경우 (일반적으로 (text, data))
            logger.info("결과가 튜플입니다.")
            text_result, data_result = result
            
            # 두 번째 요소가 딕셔너리인지 확인
            if isinstance(data_result, dict):
                assessment = data_result
                logger.info(f"JSON 데이터를 평가 결과로 사용합니다: {json.dumps(assessment, ensure_ascii=False)[:100]}...")
            else:
                logger.warning(f"두 번째 요소가 딕셔너리가 아닙니다: {type(data_result)}")
                # 첫 번째 요소에서 JSON 추출 시도
                try:
                    json_str = extract_json(text_result)
                    if json_str:
                        assessment = json.loads(json_str)
                        logger.info(f"텍스트에서 추출한 JSON을 사용합니다: {json.dumps(assessment, ensure_ascii=False)[:100]}...")
                except Exception as e:
                    logger.error(f"JSON 추출 오류: {e}")
        else:
            # 단일 값인 경우 (일반적으로 text)
            logger.info("결과가 단일 값입니다.")
            try:
                json_str = extract_json(result)
                if json_str:
                    assessment = json.loads(json_str)
                    logger.info(f"텍스트에서 추출한 JSON을 사용합니다: {json.dumps(assessment, ensure_ascii=False)[:100]}...")
            except Exception as e:
                logger.error(f"JSON 추출 오류: {e}")
        
        # 필수 필드 확인
        if not assessment or "health_status" not in assessment:
            logger.warning("건강 상태가 없거나 불완전한 JSON입니다. 기본값 설정")
            assessment = {
                "health_status": "정보 부족",
                "concerns": ["건강 지표 정보 부족으로 인한 평가 불가"],
                "recommendations": ["건강 검진을 통해 건강 지표를 업데이트하세요."]
            }
        
        # 상태 업데이트
        state.health_assessment = assessment
        
        logger.info(f"건강 평가 완료: 상태={assessment.get('health_status')}, 이슈={len(assessment.get('concerns', []))}개")
        
        return assessment
        
    except Exception as e:
        logger.error(f"건강 지표 분석 중 오류 발생: {str(e)}")
        raise

def extract_json(text: str) -> Optional[str]:
    """텍스트에서 JSON 문자열을 추출하는 함수"""
    # JSON 코드 블록 찾기
    json_start = text.find("```json")
    if json_start >= 0:
        logger.info("JSON 코드 블록 찾음")
        json_text_start = text.find("\n", json_start) + 1
        json_text_end = text.find("```", json_text_start)
        if json_text_end > json_text_start:
            json_str = text[json_text_start:json_text_end].strip()
            logger.info(f"파싱할 JSON (처음 100자): {json_str[:100]}...")
            return json_str
    
    # 코드 블록이 없는 경우 일반 JSON 찾기
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    
    if json_start >= 0 and json_end > json_start:
        json_str = text[json_start:json_end]
        logger.info(f"파싱할 JSON (처음 100자): {json_str[:100]}...")
        return json_str
    
    logger.warning("텍스트에서 JSON을 찾을 수 없습니다.")
    return None

# 테스트 함수
async def test_health_analysis():
    """건강 지표 분석 테스트"""
    # 테스트용 사용자 상태 생성
    user_state = SimpleUserState(
        user_id="test-user-123",
        query_text="내 건강 상태는 어떤가요?"
    )
    
    print(f"\n건강 지표 분석 테스트 시작...")
    print(f"사용자 상태: {user_state}")
    
    try:
        # 첫 번째 접근 방식: 직접 반환값 사용
        print("\n[테스트 1] 직접 반환값 사용")
        result = await analyze_health_metrics(user_state)
        print(f"반환값 타입: {type(result)}")
        print(f"반환값: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 두 번째 접근 방식: 언패킹 시도
        print("\n[테스트 2] 언패킹 시도")
        user_state = SimpleUserState(
            user_id="test-user-456",
            query_text="내 혈압이 걱정됩니다"
        )
        
        try:
            print("언패킹 시도 (에러 발생 가능)...")
            content, data = await analyze_health_metrics(user_state)
            print("언패킹 성공!")
            print(f"content: {content[:50]}...")
            print(f"data: {json.dumps(data, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"언패킹 오류: {str(e)}")
            print("안전한 언패킹 방법으로 재시도...")
            
            result = await analyze_health_metrics(user_state)
            if isinstance(result, tuple) and len(result) > 0:
                print(f"첫 번째 요소 사용: {result[0][:50]}...")
            else:
                print(f"단일 값 사용: {result}")
        
        # 세 번째 접근 방식: 래퍼 함수 사용
        print("\n[테스트 3] 래퍼 함수 사용")
        user_state = SimpleUserState(
            user_id="test-user-789",
            query_text="콜레스테롤 수치를 낮추는 방법을 알려주세요"
        )
        
        result = await analyze_health_metrics_wrapper(user_state)
        print(f"래퍼 결과 타입: {type(result)}")
        print(f"래퍼 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {str(e)}")

# 래퍼 함수 추가
async def analyze_health_metrics_wrapper(state: SimpleUserState) -> Dict[str, Any]:
    """
    analyze_health_metrics의 래퍼 함수 - 튜플 반환 오류 해결
    """
    try:
        result = await analyze_health_metrics(state)
        # 결과가 튜플인 경우 첫 번째 요소만 반환
        if isinstance(result, tuple) and len(result) > 0:
            return result[0]
        return result
    except Exception as e:
        logger.error(f"래퍼 함수 오류: {str(e)}")
        raise

# 메인 함수
async def main():
    """메인 함수"""
    print("=== 건강 지표 분석 테스트 시작 ===")
    
    await test_health_analysis()
    
    print("\n=== 테스트 완료 ===")

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(main()) 