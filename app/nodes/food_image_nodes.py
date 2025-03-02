import logging
from typing import Dict, Any, List, Union
from uuid import uuid4
from datetime import datetime
import json
import re

from langgraph.graph import END

from app.models.notification import UserState
from app.models.diet_plan import (
    FoodItem, 
    FoodImageData, 
    FoodImageRecognitionResult, 
    FoodNutritionAnalysis,
    DietEntry
)
from app.agents.agent_config import get_diet_agent

# 로거 설정
logger = logging.getLogger(__name__)

# 영양소 데이터베이스 (실제로는 더 광범위한 DB나 API를 사용)
NUTRITION_DB = {
    "밥 (공기)": {"calories": 300, "protein": 5.0, "carbs": 65, "fat": 0.5},
    "김치": {"calories": 30, "protein": 2.5, "carbs": 4.5, "fat": 0.5},
    "된장찌개": {"calories": 150, "protein": 10, "carbs": 10, "fat": 7},
    "삼겹살 (100g)": {"calories": 480, "protein": 17, "carbs": 0, "fat": 45},
    "계란프라이": {"calories": 120, "protein": 7, "carbs": 1, "fat": 10},
    "사과": {"calories": 80, "protein": 0.5, "carbs": 21, "fat": 0.3},
    "바나나": {"calories": 105, "protein": 1.2, "carbs": 27, "fat": 0.4},
    "닭가슴살 (100g)": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.5},
    "두부 (100g)": {"calories": 80, "protein": 8, "carbs": 2, "fat": 4.5},
    "시금치": {"calories": 25, "protein": 3, "carbs": 3.5, "fat": 0.4},
    "고구마": {"calories": 115, "protein": 2, "carbs": 27, "fat": 0.1},
    "우유 (200ml)": {"calories": 120, "protein": 6.5, "carbs": 9.5, "fat": 6.5},
    "요거트 (100g)": {"calories": 60, "protein": 5, "carbs": 4, "fat": 3},
    "치즈 (30g)": {"calories": 110, "protein": 7, "carbs": 0.5, "fat": 9},
    "감자": {"calories": 85, "protein": 2, "carbs": 20, "fat": 0.1},
    "오렌지": {"calories": 65, "protein": 1.3, "carbs": 16, "fat": 0.2},
    "샐러드 (1인분)": {"calories": 50, "protein": 2, "carbs": 5, "fat": 2},
    "피자 (1조각)": {"calories": 300, "protein": 12, "carbs": 35, "fat": 12},
    "라면": {"calories": 550, "protein": 10, "carbs": 72, "fat": 22},
    "비빔밥": {"calories": 550, "protein": 15, "carbs": 85, "fat": 14},
}

async def analyze_food_image(state: UserState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    음식 이미지를 분석하여 식품을 인식하는 함수
    """
    logger.info("음식 이미지 분석 시작")
    
    if config is None:
        config = {}
    
    # 이미지 데이터 추출
    image_data = config.get("image_data", {})
    
    if not image_data:
        logger.warning("이미지 데이터가 없습니다")
        return {"error": "이미지 데이터가 없습니다"}
    
    # 이미지 ID 생성 (실제로는 이미지 저장 시 생성된 ID를 사용)
    image_id = str(uuid4())
    user_id = state.user_profile.get("user_id", "unknown_user")
    
    # 실제 구현에서는 여기서 이미지 인식 API나 모델을 호출
    # 예: Google Cloud Vision API, Amazon Rekognition 등
    # 여기서는 시뮬레이션
    
    # 식품 인식 결과 생성 (실제로는 AI 모델의 결과)
    # 시뮬레이션: 한식 식사 인식 결과
    recognized_foods = [
        {"밥 (공기)": 0.95},
        {"김치": 0.92},
        {"된장찌개": 0.87},
        {"계란프라이": 0.65}
    ]
    
    dominant_food = "한식 식사"
    confidence_score = 0.85
    
    # 이미지 인식 결과를 UserState에 저장
    recognition_result = FoodImageRecognitionResult(
        image_id=image_id,
        timestamp=datetime.now(),
        recognized_foods=recognized_foods,
        dominant_food=dominant_food,
        confidence_score=confidence_score
    )
    
    # 결과 반환
    state.recognition_result = recognition_result
    
    logger.info(f"음식 이미지 인식 완료 - 주요 음식: {dominant_food}, 신뢰도: {confidence_score:.2f}")
    
    return {"recognition_result": recognition_result.__dict__}

async def calculate_nutrition(state: UserState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    인식된 음식의 영양소를 계산하는 함수
    """
    logger.info("음식 영양소 계산 시작")
    
    # 인식 결과 가져오기
    recognition_result = state.recognition_result
    
    if not recognition_result:
        logger.warning("인식 결과가 없습니다")
        return {"error": "인식 결과가 없습니다"}
    
    # 인식된 음식들을 FoodItem으로 변환
    food_items = []
    estimated_calories = 0
    estimated_nutrition = {"protein": 0, "carbs": 0, "fat": 0}
    
    for food_dict in recognition_result.recognized_foods:
        for food_name, probability in food_dict.items():
            # 영양소 데이터베이스에서 정보 가져오기
            if food_name in NUTRITION_DB:
                nutrition = NUTRITION_DB[food_name]
                
                # FoodItem 생성
                food_item = FoodItem(
                    name=food_name,
                    calories=nutrition["calories"],
                    protein=nutrition["protein"],
                    carbs=nutrition["carbs"],
                    fat=nutrition["fat"],
                    amount="1인분"  # 기본값, 실제로는 이미지 분석으로 양 추정 필요
                )
                
                food_items.append(food_item)
                
                # 총 칼로리 및 영양소 계산
                estimated_calories += nutrition["calories"]
                estimated_nutrition["protein"] += nutrition["protein"]
                estimated_nutrition["carbs"] += nutrition["carbs"]
                estimated_nutrition["fat"] += nutrition["fat"]
    
    # 총 열량 계산 (g 단위)
    total_nutrition_weight = sum(estimated_nutrition.values())
    
    # 영양소 비율 계산 (%)
    nutrition_percentage = {}
    if total_nutrition_weight > 0:
        for nutrient, value in estimated_nutrition.items():
            nutrition_percentage[nutrient] = round((value / total_nutrition_weight) * 100, 1)
    
    # 식사 품질 점수 계산 (간단한 알고리즘)
    # 이상적인 영양소 비율: 단백질 20%, 탄수화물 50%, 지방 30%
    ideal_ratio = {"protein": 20, "carbs": 50, "fat": 30}
    
    # 차이 계산
    ratio_diff = 0
    for nutrient, ideal in ideal_ratio.items():
        actual = nutrition_percentage.get(nutrient, 0)
        ratio_diff += abs(ideal - actual)
    
    # 점수 계산 (100점 만점, 차이가 클수록 점수 낮음)
    meal_quality_score = max(0, 10 - (ratio_diff / 10))
    
    # 영양소 분석 결과 생성
    nutrition_analysis = FoodNutritionAnalysis(
        image_id=recognition_result.image_id,
        timestamp=datetime.now(),
        recognized_foods=food_items,
        estimated_total_calories=estimated_calories,
        estimated_nutrition=estimated_nutrition,
        nutrition_percentage=nutrition_percentage,
        meal_quality_score=meal_quality_score
    )
    
    # 상태에 저장
    state.nutrition_analysis = nutrition_analysis
    
    logger.info(f"음식 영양소 계산 완료 - 총 칼로리: {estimated_calories}kcal, 품질 점수: {meal_quality_score:.1f}/10")
    
    return {"nutrition_analysis": nutrition_analysis.__dict__}

async def generate_diet_feedback(state: UserState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    식단 분석 결과를 바탕으로 피드백 생성
    """
    logger.info("식단 피드백 생성 시작")
    
    # 영양소 분석 결과 가져오기
    nutrition_analysis = state.nutrition_analysis
    
    if not nutrition_analysis:
        logger.warning("영양소 분석 결과가 없습니다")
        return {"error": "영양소 분석 결과가 없습니다"}
    
    # 사용자 정보 가져오기
    user_profile = state.user_profile
    user_id = user_profile.get("user_id", "unknown_user")
    
    # 식이 제한 사항 확인
    dietary_restrictions = user_profile.get("dietary_restrictions", [])
    
    # 식단 에이전트 생성
    agent = get_diet_agent()
    
    # 건강 지표
    health_metrics = user_profile.get("current_metrics", {})
    
    # 현재 식단 정보 정리
    recognized_foods = [food.name for food in nutrition_analysis.recognized_foods]
    
    # 프롬프트 생성
    prompt = f"""
    다음 사용자의 식단을 분석하고 맞춤형 피드백과 개선 제안을 제공해주세요:
    
    사용자 정보:
    - 이름: {user_profile.get('name', '사용자')}
    - 성별: {user_profile.get('gender', '정보 없음')}
    - 나이: {datetime.now().year - user_profile.get('birth_date', datetime.now()).year if 'birth_date' in user_profile else '정보 없음'}
    - 현재 체중: {health_metrics.get('weight', '정보 없음')} kg
    - 현재 BMI: {health_metrics.get('bmi', '정보 없음')}
    - 식이 제한사항: {', '.join(dietary_restrictions) if dietary_restrictions else '없음'}
    
    인식된 식단:
    - 음식 항목: {', '.join(recognized_foods)}
    - 총 칼로리: {nutrition_analysis.estimated_total_calories} kcal
    - 단백질: {nutrition_analysis.estimated_nutrition.get('protein', 0)}g ({nutrition_analysis.nutrition_percentage.get('protein', 0)}%)
    - 탄수화물: {nutrition_analysis.estimated_nutrition.get('carbs', 0)}g ({nutrition_analysis.nutrition_percentage.get('carbs', 0)}%)
    - 지방: {nutrition_analysis.estimated_nutrition.get('fat', 0)}g ({nutrition_analysis.nutrition_percentage.get('fat', 0)}%)
    - 식사 품질 점수: {nutrition_analysis.meal_quality_score}/10
    
    다음 항목을 포함한 JSON 형식으로 응답해주세요:
    1. 식단 평가
    2. 개선 제안 (최소 3가지)
    3. 추천 대체 식품 (2-3가지)
    4. 건강 목표 달성을 위한 팁
    
    JSON 형식:
    {
        "diet_assessment": "식단 평가 내용",
        "improvement_suggestions": ["제안1", "제안2", "제안3"],
        "alternative_foods": ["대체 식품1", "대체 식품2"],
        "health_tips": "건강 목표 달성 팁"
    }
    """
    
    # 에이전트 실행
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 문자열 추출 및 파싱
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        logger.error("JSON 파싱 오류")
        data = {
            "diet_assessment": "식단 분석 중 오류가 발생했습니다.",
            "improvement_suggestions": ["더 많은 단백질 섭취 권장", "채소 섭취량 증가", "가공식품 줄이기"],
            "alternative_foods": ["닭가슴살", "두부", "견과류"],
            "health_tips": "규칙적인 식사와 충분한 수분 섭취를 유지하세요."
        }
    
    # DietEntry 생성
    entry_id = str(uuid4())
    meal_id = str(uuid4())
    diet_entry = DietEntry(
        entry_id=entry_id,
        meal_id=meal_id,
        user_id=user_id,
        timestamp=datetime.now(),
        meal_type=config.get("meal_type", "식사") if config else "식사",
        food_items=nutrition_analysis.recognized_foods,
        total_calories=nutrition_analysis.estimated_total_calories,
        nutrition_data=nutrition_analysis.estimated_nutrition,
        image_id=nutrition_analysis.image_id,
        notes=data.get("diet_assessment", "")
    )
    
    # 상태에 저장
    state.diet_entry = diet_entry
    
    # 음성 스크립트 생성
    voice_script = f"""
    식단 분석 결과입니다.
    
    총 {nutrition_analysis.estimated_total_calories} 칼로리를 섭취하셨고, 식사 품질 점수는 10점 만점에 {nutrition_analysis.meal_quality_score:.1f}점입니다.
    
    {data.get('diet_assessment', '')}
    
    개선 제안:
    {'. '.join(data.get('improvement_suggestions', []))}
    
    추천 대체 식품으로는 {', '.join(data.get('alternative_foods', []))} 등이 있습니다.
    
    {data.get('health_tips', '')}
    """
    
    # 음성 스크립트 저장
    state.voice_scripts.append(voice_script)
    
    logger.info("식단 피드백 생성 완료")
    
    return {"diet_entry": diet_entry.__dict__, "feedback": data}

async def create_diet_image_summary(state: UserState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    식단 이미지 분석 결과를 요약하는 함수
    """
    logger.info("식단 이미지 요약 생성 시작")
    
    # 필요한 상태 데이터 가져오기
    diet_entry = state.diet_entry
    nutrition_analysis = state.nutrition_analysis
    
    if not diet_entry or not nutrition_analysis:
        logger.warning("식단 분석 데이터가 부족합니다")
        return {"error": "필요한 데이터가 없습니다"}
    
    # meal_id가 없으면 추가
    if not hasattr(diet_entry, 'meal_id') or diet_entry.meal_id is None:
        diet_entry.meal_id = str(uuid4())
        logger.info(f"식단 항목에 meal_id 추가: {diet_entry.meal_id}")
    
    # END 노드를 위한 결과 생성
    result = diet_entry.__dict__
    
    # 상태 데이터 정리 (필요 시)
    # 실제 구현에서는 여기서 데이터베이스에 저장하거나 다른 처리 수행
    
    logger.info(f"식단 이미지 요약 생성 완료 - 식사: {diet_entry.meal_type}, 칼로리: {diet_entry.total_calories}")
    
    return {"result": END(result)} 