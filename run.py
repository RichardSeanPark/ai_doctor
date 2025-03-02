#!/usr/bin/env python
import asyncio
import logging
import os
import sys
import traceback
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
import argparse

from app.main import HealthAIApplication
from app.models.health_data import DietEntry, HealthAssessment, UserProfile, VoiceSegment

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

async def run_diet_analysis_test(mock=False):
    """
    식단 분석 테스트
    """
    logger.info("식단 분석 테스트 시작")
    
    app = HealthAIApplication()
    
    # 샘플 식단 데이터
    sample_meals = {
        "meals": [
            {
                "meal_type": "아침",
                "food_items": [
                    {"name": "현미밥", "amount": "1공기", "calories": 200},
                    {"name": "된장국", "amount": "1공기", "calories": 100},
                    {"name": "김치", "amount": "1접시", "calories": 30},
                    {"name": "계란말이", "amount": "1개", "calories": 120}
                ]
            },
            {
                "meal_type": "점심",
                "food_items": [
                    {"name": "샐러드", "amount": "1접시", "calories": 150},
                    {"name": "닭가슴살", "amount": "100g", "calories": 165},
                    {"name": "통밀빵", "amount": "2쪽", "calories": 130}
                ]
            },
            {
                "meal_type": "저녁",
                "food_items": [
                    {"name": "잡곡밥", "amount": "1공기", "calories": 230},
                    {"name": "불고기", "amount": "150g", "calories": 350},
                    {"name": "나물", "amount": "1접시", "calories": 50},
                    {"name": "요구르트", "amount": "1개", "calories": 100}
                ]
            }
        ]
    }
    
    # 식단 분석 실행
    if mock:
        logger.info("모의 식단 분석 결과 생성")
        # 모의 결과 생성
        user_profile = UserProfile(
            user_id="user123",
            name="홍길동",
            birth_date=datetime(1985, 5, 15).date(),
            gender="남성"
        )
        result = {
            "user_profile": user_profile,
            "voice_scripts": [],
            "notifications": [],
            "voice_segments": [],
            "recent_meals": sample_meals
        }
    else:
        result = await app.analyze_diet(sample_meals)
    
    logger.info(f"식단 분석 결과: {result}")
    
    return result

async def run_food_image_test(mock=False):
    """
    식품 이미지 분석 테스트
    """
    logger.info("식품 이미지 분석 테스트 시작")
    
    app = HealthAIApplication()
    
    # 샘플 이미지 데이터 (실제로는 이미지 파일을 Base64로 인코딩)
    meal_id = str(uuid.uuid4())
    entry_id = str(uuid.uuid4())
    sample_image_data = {
        "meal_type": "점심",
        "image_base64": "샘플_이미지_Base64_문자열",  # 실제 구현에서는 진짜
        "location": "식당",
        "image_id": str(uuid.uuid4())
    }
    
    # 식품 이미지 분석 실행
    try:
        if mock:
            logger.info("모의 식품 이미지 분석 결과 생성")
            # 모의 결과 생성
            result = DietEntry(
                meal_id=meal_id,
                entry_id=entry_id,
                meal_type="점심",
                food_items=[
                    {"name": "비빔밥", "amount": "1공기", "calories": 650},
                    {"name": "김치", "amount": "1접시", "calories": 30}
                ],
                total_calories=680.0,
                timestamp=datetime.now(),
                location="식당",
                image_id=sample_image_data["image_id"]
            )
        else:
            result = await app.analyze_food_image(sample_image_data)
            
        logger.info(f"식품 이미지 분석 결과:")
        logger.info(f"식사 ID: {result.meal_id}")
        logger.info(f"식사 유형: {result.meal_type}")
        logger.info(f"총 칼로리: {result.total_calories}kcal")
        
        return result
    except Exception as e:
        logger.error(f"식품 이미지 분석 중 오류 발생: {e}")
        logger.exception(e)
        return None

async def run_health_metrics_test(mock=False):
    """
    건강 지표 분석 테스트
    """
    logger.info("건강 지표 분석 테스트 시작")
    
    app = HealthAIApplication()
    
    # 건강 지표 분석 실행
    if mock:
        logger.info("모의 건강 지표 분석 결과 생성")
        # 모의 결과 생성
        user_profile = UserProfile(
            user_id="user123",
            name="홍길동",
            birth_date=datetime(1985, 5, 15).date(),
            gender="남성"
        )
        result = {
            "user_profile": user_profile,
            "voice_scripts": [],
            "notifications": [],
            "voice_segments": []
        }
    else:
        result = await app.check_health_metrics()
    
    logger.info(f"건강 지표 분석 결과: {result}")
    
    return result

async def run_voice_query_test(mock=False):
    """
    음성 질의 테스트
    """
    logger.info("음성 질의 테스트 시작")
    
    app = HealthAIApplication()
    
    # 샘플 음성 질의
    query = "요즘 잠을 잘 못 자고 피로감이 있어요. 어떻게 하면 좋을까요?"
    
    # 음성 질의 처리 실행
    if mock:
        logger.info("모의 음성 질의 결과 생성")
        # 모의 결과 생성
        result = [
            VoiceSegment(
                segment_id=str(uuid.uuid4()),
                content="수면 문제와 피로감에 대해 말씀해 주셨네요. 수면의 질을 개선하기 위한 몇 가지 방법을 알려드리겠습니다.",
                segment_type="response",
                timestamp=datetime.now()
            )
        ]
    else:
        result = await app.process_voice_query(query)
    
    logger.info(f"음성 질의 결과: {result}")
    
    return result

async def run_health_consultation_test(mock=False):
    """
    건강 상담 세션 테스트
    """
    logger.info("건강 상담 세션 테스트 시작")
    
    app = HealthAIApplication()
    
    # 샘플 진행 데이터
    progress_data = {
        "percentage": 65,
        "recent_activities": ["매일 걷기 30분", "식단 조절", "수면 개선"]
    }
    
    # 건강 상담 세션 실행
    if mock:
        logger.info("모의 건강 상담 세션 결과 생성")
        # 모의 결과 생성
        result = {
            "consultation_id": str(uuid.uuid4()),
            "summary": "건강 목표를 향해 잘 진행 중입니다. 걷기와 식단 조절을 꾸준히 유지하세요.",
            "recommendations": [
                "수면 시간을 7-8시간으로 늘려보세요",
                "스트레스 관리를 위한 명상을 시도해보세요"
            ],
            "next_steps": [
                "일주일에 3회 근력 운동 추가",
                "물 섭취량 늘리기"
            ]
        }
    else:
        result = await app.conduct_health_consultation(progress_data)
    
    logger.info(f"건강 상담 세션 결과: {result}")
    
    return result

async def main():
    """
    메인 함수
    """
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='건강 AI 애플리케이션 실행')
    parser.add_argument('--mock', action='store_true', help='API 호출 없이 모의 데이터로 테스트')
    args = parser.parse_args()
    
    mock_mode = args.mock
    if mock_mode:
        logger.info("모의 모드로 실행 중 - 실제 API 호출 없음")
    
    logger.info("HealthAIApplication 초기화 시작")
    
    # HealthAIApplication 초기화
    app = HealthAIApplication()
    
    logger.info("HealthAIApplication 초기화 완료")
    logger.info("건강 AI 시스템 테스트 시작")
    
    # 식단 분석 테스트
    await run_diet_analysis_test(mock=mock_mode)
    
    # 식품 이미지 분석 테스트
    await run_food_image_test(mock=mock_mode)
    
    # 건강 지표 분석 테스트
    await run_health_metrics_test(mock=mock_mode)
    
    # 음성 질의 테스트
    await run_voice_query_test(mock=mock_mode)
    
    # 건강 상담 세션 테스트
    await run_health_consultation_test(mock=mock_mode)
    
    logger.info("모든 테스트 완료")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}")
        logger.exception(e)
        sys.exit(1) 