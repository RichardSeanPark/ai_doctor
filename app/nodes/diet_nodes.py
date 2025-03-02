from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime, timedelta
import logging

from langgraph.graph import END

from app.models.health_data import DietAnalysis, DietEntry
from app.models.diet_plan import MealRecommendation, FoodItem
from app.models.notification import UserState, AndroidNotification
from app.agents.agent_config import get_diet_agent

# 로거 설정
logger = logging.getLogger(__name__)

async def analyze_diet(state: UserState) -> DietAnalysis:
    # 사용자의 식단 정보 분석
    logger.info(f"식단 분석 시작 - 사용자 ID: {state.user_profile.get('user_id', 'unknown')}")
    
    recent_meals = state.recent_meals
    if not recent_meals:
        logger.warning("분석할 식단 정보가 없습니다")
        return DietAnalysis(
            calories_consumed=0.0,
            nutrition_balance={"단백질": 0.0, "탄수화물": 0.0, "지방": 0.0},
            improvement_suggestions=["식단 정보를 입력해주세요."]
        )
    
    # 다이어트 에이전트 생성
    agent = get_diet_agent()
    
    # 사용자 식단 데이터 준비
    meals_data = "\n".join([
        f"- {meal.get('meal_type')}: " + 
        ", ".join([f"{food.get('name')} ({food.get('amount', '1개')})" for food in meal.get('food_items', [])])
        for meal in recent_meals.get('meals', [])
    ])
    
    user_goals = state.user_profile.get("goals", [])
    goal_str = "특별한 목표 없음" if not user_goals else f"{user_goals[0].get('goal_type')} (목표값: {user_goals[0].get('target_value')})"
    
    dietary_restrictions = state.user_profile.get("dietary_restrictions", [])
    restrictions_str = "없음" if not dietary_restrictions else ", ".join(dietary_restrictions)
    
    # AI에게 식단 분석 요청
    prompt = f"""
    다음 사용자의 식단을 분석하고 영양 균형을 평가해주세요:
    
    사용자 정보:
    - 건강 목표: {goal_str}
    - 식이 제한: {restrictions_str}
    
    오늘의 식단:
    {meals_data}
    
    분석 결과를 제공해주세요:
    1. 총 섭취 칼로리
    2. 영양소 균형 (단백질, 탄수화물, 지방의 비율)
    3. 개선 제안 (3가지)
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "calories": 숫자,
        "nutrition_balance": {{"단백질": 소수점, "탄수화물": 소수점, "지방": 소수점}},
        "suggestions": ["개선 제안 1", "개선 제안 2", "개선 제안 3"]
    }}
    """
    
    # 에이전트 실행 및 결과 파싱
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 문자열 추출 및 파싱
    import json
    import re
    
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"식단 분석 완료 - 칼로리: {data['calories']}")
    
    # 분석 결과 생성
    analysis = DietAnalysis(
        calories_consumed=data["calories"],
        nutrition_balance=data["nutrition_balance"],
        improvement_suggestions=data["suggestions"]
    )
    
    # 분석 결과를 상태에 저장
    state.diet_analysis = analysis
    
    # 음성 응답을 위한 스크립트 생성
    voice_script = f"오늘 식단 분석 결과입니다. 섭취 칼로리는 {data['calories']}kcal이며, {data['suggestions'][0]}"
    state.voice_scripts.append(voice_script)
    
    return analysis

async def provide_recommendations(state: UserState) -> MealRecommendation:
    # 상태에서 분석 결과 가져오기
    analysis = state.diet_analysis
    if not analysis:
        logger.warning("식단 분석 결과가 없습니다")
        return MealRecommendation(
            recommendation_id=str(uuid4()),
            timestamp=datetime.now(),
            meal_type="간식",
            food_items=[],
            total_calories=0,
            nutrition_breakdown={"단백질": 0.0, "탄수화물": 0.0, "지방": 0.0},
            reasoning="식단 분석 결과가 없어 추천할 수 없습니다."
        )
    
    logger.info(f"식단 추천 시작 - 칼로리: {analysis.calories_consumed}")
    
    # 식단 추천 에이전트 생성
    agent = get_diet_agent()
    
    user_profile = state.user_profile
    dietary_restrictions = user_profile.get("dietary_restrictions", [])
    goals = user_profile.get("goals", [])
    
    # 다음 식사 시간 결정 (현재 시간 기준)
    now = datetime.now()
    hour = now.hour
    
    if hour < 10:
        next_meal = "아침"
    elif hour < 14:
        next_meal = "점심"
    elif hour < 18:
        next_meal = "저녁"
    else:
        next_meal = "간식"
    
    # 목표 칼로리 계산 (간단한 예시)
    if goals and goals[0].get("goal_type") == "체중감량":
        target_calories = 400 if next_meal == "아침" else 600 if next_meal == "점심" else 500 if next_meal == "저녁" else 200
    else:
        target_calories = 600 if next_meal == "아침" else 800 if next_meal == "점심" else 700 if next_meal == "저녁" else 300
    
    # 영양 균형 계산
    current_balance = analysis.nutrition_balance
    needs_more_protein = current_balance.get("단백질", 0) < 0.25
    needs_more_carbs = current_balance.get("탄수화물", 0) < 0.45
    needs_more_fat = current_balance.get("지방", 0) < 0.2
    
    nutrient_focus = []
    if needs_more_protein:
        nutrient_focus.append("단백질")
    if needs_more_carbs:
        nutrient_focus.append("탄수화물")
    if needs_more_fat:
        nutrient_focus.append("지방")
    
    nutrient_focus_str = ", ".join(nutrient_focus) if nutrient_focus else "균형잡힌 영양소"
    
    # 식단 추천 요청
    prompt = f"""
    사용자를 위한 다음 식사({next_meal}) 추천을 해주세요.
    
    사용자 정보:
    - 식이 제한: {', '.join(dietary_restrictions) if dietary_restrictions else '없음'}
    - 보충이 필요한 영양소: {nutrient_focus_str}
    - 목표 칼로리: {target_calories}kcal
    
    오늘의 현재 섭취 상황:
    - 총 섭취 칼로리: {analysis.calories_consumed}kcal
    - 영양소 균형: 단백질 {current_balance.get('단백질', 0)*100:.1f}%, 탄수화물 {current_balance.get('탄수화물', 0)*100:.1f}%, 지방 {current_balance.get('지방', 0)*100:.1f}%
    
    다음 정보를 JSON 형식으로 제공해주세요:
    1. 추천 음식 목록 (이름, 양, 예상 칼로리)
    2. 이 식사의 영양소 구성
    3. 식사 설명 및 추천 이유
    
    JSON 예시:
    {
        "meal_items": [
            {"name": "음식1", "amount": "100g", "calories": 150},
            {"name": "음식2", "amount": "1인분", "calories": 200}
        ],
        "nutrients": {"단백질": 0.3, "탄수화물": 0.5, "지방": 0.2},
        "description": "이 식단을 추천한 이유에 대한 설명"
    }
    """
    
    # 에이전트 호출 및 결과 처리
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 추출
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"식단 추천 완료 - 식사 유형: {data['meal_type']}, 칼로리: {data['total_calories']}")
    
    # 식품 항목 변환
    food_items = []
    for item_data in data["food_items"]:
        food_items.append(FoodItem(
            name=item_data["name"],
            calories=item_data["calories"],
            protein=item_data["protein"],
            carbs=item_data["carbs"],
            fat=item_data["fat"],
            amount=item_data["amount"]
        ))
    
    # 대체 식품 변환
    alternatives = []
    if "alternatives" in data and data["alternatives"]:
        for alt_data in data["alternatives"]:
            alternatives.append(FoodItem(
                name=alt_data["name"],
                calories=alt_data["calories"],
                protein=alt_data["protein"],
                carbs=alt_data["carbs"],
                fat=alt_data["fat"],
                amount=alt_data["amount"]
            ))
    
    # 추천 결과 생성
    recommendation = MealRecommendation(
        recommendation_id=str(uuid4()),
        timestamp=datetime.now(),
        meal_type=data["meal_type"],
        food_items=food_items,
        total_calories=data["total_calories"],
        nutrition_breakdown=data["nutrition_breakdown"],
        reasoning=data["reasoning"],
        alternatives=alternatives
    )
    
    # 음성 스크립트 생성
    voice_script = f"{next_meal}으로 추천해 드리는 식단입니다: {', '.join([item.name for item in food_items])}. 총 {data['total_calories']}kcal입니다."
    state.voice_scripts.append(voice_script)
    
    # 알림 생성
    notification = AndroidNotification(
        title=f"{next_meal} 식단 추천",
        body=f"오늘의 {next_meal} 추천: {', '.join([item.name for item in food_items[:3]])} {'외 여러 항목' if len(food_items) > 3 else ''}",
        priority="normal"
    )
    state.notifications.append(notification)
    
    return END(recommendation)

async def process_food_image(state: UserState, image_data: Dict[str, Any]) -> DietEntry:
    logger.info("음식 이미지 처리 시작")
    
    # 실제로는 여기서 이미지 분석 API를 호출하거나 ML 모델을 사용할 것입니다.
    # 여기서는 간단한 시뮬레이션만 수행합니다.
    
    # 다이어트 에이전트 생성
    agent = get_diet_agent()
    
    # 샘플 이미지 설명 (실제로는 이미지 분석 결과가 여기 들어갑니다)
    image_description = image_data.get("description", "음식 접시")
    
    prompt = f"""
    다음 음식 이미지에 대한 설명을 분석하고 식단 기록을 생성해주세요:
    
    이미지 설명: {image_description}
    
    JSON 형식으로 다음 정보를 포함하여 응답해주세요:
    {{
        "meal_type": "추정되는 식사 유형 (아침/점심/저녁/간식)",
        "food_items": [
            {{"name": "음식명", "calories": 숫자, "amount": "양"}},
            // 추가 음식...
        ],
        "total_calories": 숫자
    }}
    """
    
    # 에이전트 실행 및 결과 파싱
    result = await agent.ainvoke({"input": prompt})
    
    # AIMessage 객체에서 content 추출
    if hasattr(result, 'content'):
        output = result.content
    else:
        output = str(result)
    
    # JSON 문자열 추출 및 파싱
    import json
    import re
    
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = re.search(r'{.*}', output, re.DOTALL).group(0)
    
    data = json.loads(json_str)
    
    logger.info(f"음식 이미지 처리 완료 - 식사 유형: {data['meal_type']}, 칼로리: {data['total_calories']}")
    
    # 식품 항목 변환
    food_items = []
    for item_data in data["food_items"]:
        food_items.append(FoodItem(
            name=item_data["name"],
            calories=item_data["calories"],
            amount=item_data["amount"]
        ))
    
    # 식단 기록 생성
    diet_entry = DietEntry(
        entry_id=str(uuid4()),
        timestamp=datetime.now(),
        meal_type=data["meal_type"],
        food_items=food_items,
        total_calories=data["total_calories"],
        image_url=image_data.get("url", "")
    )
    
    # 음성 스크립트 생성
    voice_script = f"음식 이미지를 분석했습니다. {data['meal_type']}으로 {', '.join([item.name for item in food_items])}이(가) 감지되었습니다. 총 {data['total_calories']}kcal입니다."
    state.voice_scripts.append(voice_script)
    
    return END(diet_entry) 