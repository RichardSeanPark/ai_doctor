import asyncio
import base64
import os
import sys
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import HealthAIApplication

async def test_food_image_analysis():
    """
    식품 이미지 분석 기능 테스트
    """
    logger.info("식품 이미지 분석 테스트 시작")
    
    # HealthAIApplication 인스턴스 생성
    app = HealthAIApplication()
    
    # 테스트용 이미지 데이터 (실제로는 파일에서 로드)
    # 이 예제에서는 가상의 Base64 인코딩된 이미지를 사용
    image_base64 = "이미지_데이터_샘플" # 실제 테스트에서는 진짜 이미지 파일을 Base64로 인코딩
    
    # 이미지 데이터 준비
    image_data = {
        "meal_type": "저녁",
        "image_base64": image_base64,
        "location": "집",
        "timestamp": datetime.now()
    }
    
    try:
        # 식품 이미지 분석 실행
        result = await app.analyze_food_image(image_data)
        
        # 결과 출력
        logger.info("식품 이미지 분석 결과:")
        logger.info(f"식사 ID: {result.entry_id}")
        logger.info(f"식사 유형: {result.meal_type}")
        logger.info(f"총 칼로리: {result.total_calories}")
        
        # 인식된 음식 항목 출력
        logger.info("인식된 음식 항목:")
        for i, food_item in enumerate(result.food_items, 1):
            logger.info(f"  {i}. {food_item.name}: {food_item.calories}kcal")
        
        # 영양소 분석 출력
        logger.info("영양소 분석:")
        for nutrient, value in result.nutrition_data.items():
            logger.info(f"  {nutrient}: {value}g")
            
        logger.info("식품 이미지 분석 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        logger.exception(e)
        return False

async def load_and_analyze_image_from_file(file_path, meal_type="아침"):
    """
    파일에서 이미지를 로드하여 분석하는 함수
    
    Args:
        file_path (str): 이미지 파일 경로
        meal_type (str): 식사 유형 (아침, 점심, 저녁, 간식)
    """
    # 파일 존재 확인
    if not os.path.exists(file_path):
        logger.error(f"파일이 존재하지 않습니다: {file_path}")
        return None
    
    try:
        # 파일을 Base64로 인코딩
        with open(file_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
        # HealthAIApplication 인스턴스 생성
        app = HealthAIApplication()
        
        # 이미지 데이터 준비
        image_data = {
            "meal_type": meal_type,
            "image_base64": image_base64,
            "location": "테스트 환경",
            "timestamp": datetime.now(),
            "file_path": file_path  # 디버깅 목적으로 원본 파일 경로 포함
        }
        
        # 식품 이미지 분석 실행
        logger.info(f"이미지 파일 분석 시작: {os.path.basename(file_path)}")
        result = await app.analyze_food_image(image_data)
        
        # 결과 출력
        logger.info("식품 이미지 분석 결과:")
        logger.info(f"식사 ID: {result.entry_id}")
        logger.info(f"식사 유형: {result.meal_type}")
        logger.info(f"총 칼로리: {result.total_calories}")
        
        return result
    
    except Exception as e:
        logger.error(f"이미지 분석 중 오류 발생: {e}")
        logger.exception(e)
        return None

async def main():
    """메인 함수"""
    # 기본 테스트 실행
    success = await test_food_image_analysis()
    
    if success:
        logger.info("기본 이미지 분석 테스트가 성공적으로 완료되었습니다.")
    else:
        logger.warning("기본 이미지 분석 테스트 중 문제가 발생했습니다.")
    
    # 실제 이미지 파일을 테스트하려면 아래 코드의 주석을 해제하고 실제 이미지 경로를 지정
    """
    image_file_path = "test_images/food_sample.jpg"
    result = await load_and_analyze_image_from_file(image_file_path, "점심")
    
    if result:
        logger.info("파일 기반 이미지 분석이 성공적으로 완료되었습니다.")
    else:
        logger.warning("파일 기반 이미지 분석 중 문제가 발생했습니다.")
    """

if __name__ == "__main__":
    asyncio.run(main()) 