from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from uuid import uuid4

class FoodItem(BaseModel):
    """음식 항목 모델"""
    name: str
    amount: str = "1인분"
    calories: float
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    
class Meal(BaseModel):
    meal_type: str  # "아침", "점심", "저녁", "간식"
    food_items: List[FoodItem]
    total_calories: float
    nutrition_breakdown: Dict[str, float]  # {"단백질": 25.0, "탄수화물": 50.0, "지방": 15.0}
    
class DietPlan(BaseModel):
    plan_id: str
    user_id: str
    start_date: date
    end_date: date
    daily_calorie_target: float
    daily_meals: Dict[str, List[Meal]]  # {"월요일": [Meal, Meal, Meal], "화요일": [...]}
    dietary_restrictions: List[str]
    nutritional_goals: Dict[str, float]  # {"단백질": 25, "탄수화물": 50, "지방": 25} (%)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
class DietEntry(BaseModel):
    """식단 기록 모델"""
    entry_id: str = str(uuid4())
    user_id: Optional[str] = None
    timestamp: datetime = datetime.now()
    meal_type: str  # 아침, 점심, 저녁, 간식 등
    food_items: List[FoodItem]
    total_calories: float
    image_url: Optional[str] = None
    meal_id: Optional[str] = None
    
class MealRecommendation(BaseModel):
    """식사 추천 모델"""
    recommendation_id: str = str(uuid4())
    user_id: Optional[str] = None
    timestamp: datetime = datetime.now()
    meal_type: str
    food_items: List[Dict[str, Any]]
    total_calories: float
    nutrients: Dict[str, float]
    description: str
    
class FoodImageData(BaseModel):
    """음식 이미지 데이터 모델"""
    image_id: str = str(uuid4())
    user_id: str
    meal_type: str
    image_data: str  # Base64 인코딩된 이미지 데이터
    timestamp: datetime = datetime.now()
    
class FoodImageRecognitionResult(BaseModel):
    """음식 이미지 인식 결과 모델"""
    recognition_id: str = str(uuid4())
    image_id: str
    timestamp: datetime = datetime.now()
    recognized_foods: List[Dict[str, float]]  # 음식 이름과 확률
    confidence_score: float
    
class FoodNutritionAnalysis(BaseModel):
    """음식 영양소 분석 모델"""
    analysis_id: str = str(uuid4())
    recognition_id: str
    timestamp: datetime = datetime.now()
    recognized_foods: List[FoodItem]
    estimated_total_calories: float
    estimated_nutrition: Dict[str, float]  # 단백질, 탄수화물, 지방 등
    nutrition_percentage: Dict[str, float]  # 영양소 비율 (%)
    meal_quality_score: float  # 1-10 점수
    
class DietAdviceRequest(BaseModel):
    """식단 조언 요청 모델"""
    request_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    user_id: str
    current_diet: List[Dict[str, Any]]
    dietary_restrictions: Optional[List[str]] = None
    health_goals: Optional[List[str]] = None
    specific_concerns: Optional[str] = None
    
class DietSpecialistResponse(BaseModel):
    """다이어트 전문 조언 응답 모델"""
    response_id: str = str(uuid4())
    request_id: str
    timestamp: datetime = datetime.now()
    advice: str  # 모든 다이어트 조언을 포함하는 단일 필드

class DietAnalysis(BaseModel):
    """식단 분석 결과 모델"""
    analysis_id: str
    user_id: str
    timestamp: datetime
    calories_consumed: float
    nutrition_balance: Dict[str, float]  # {"단백질": 15.0, "탄수화물": 55.0, "지방": 30.0} (%)
    improvement_suggestions: List[str]
    food_recommendations: List[FoodItem] = []
    
class FoodNutritionAnalysis(BaseModel):
    """인식된 음식의 영양소 분석 결과 모델"""
    image_id: str
    timestamp: datetime
    recognized_foods: List[FoodItem]  # 인식된 음식 항목들
    estimated_total_calories: float
    estimated_nutrition: Dict[str, float]  # {"단백질": 25.0, "탄수화물": 50.0, "지방": 15.0} (그램)
    nutrition_percentage: Dict[str, float]  # {"단백질": 20, "탄수화물": 50, "지방": 30} (%)
    meal_quality_score: float  # 식사 품질 점수 (0-10)
    
class DietAnalysis(BaseModel):
    """식단 분석 결과 모델"""
    analysis_id: str
    user_id: str
    timestamp: datetime
    calories_consumed: float
    nutrition_balance: Dict[str, float]  # {"단백질": 15.0, "탄수화물": 55.0, "지방": 30.0} (%)
    improvement_suggestions: List[str]
    food_recommendations: List[FoodItem] = [] 