from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import date, datetime

class FoodItem(BaseModel):
    name: str
    calories: float
    protein: float  # 그램 
    carbs: float    # 그램
    fat: float      # 그램
    amount: str     # "100g", "1개" 등
    
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
    
class MealRecommendation(BaseModel):
    recommendation_id: str
    timestamp: datetime
    meal_type: str
    food_items: List[FoodItem]
    total_calories: float
    nutrition_breakdown: Dict[str, float]
    reasoning: str
    alternatives: List[FoodItem] = []
    
    class Config:
        arbitrary_types_allowed = True

# 음식 이미지 분석용 모델
class FoodImageData(BaseModel):
    """음식 이미지 분석을 위한 입력 데이터 모델"""
    image_id: str
    image_url: Optional[str] = None  # 원격 이미지 URL
    image_base64: Optional[str] = None  # Base64 인코딩된 이미지 데이터
    user_id: str
    timestamp: datetime
    meal_type: Optional[str] = None  # "아침", "점심", "저녁", "간식"
    location: Optional[str] = None  # 위치 정보
    
class FoodImageRecognitionResult(BaseModel):
    """음식 이미지 인식 결과 모델"""
    image_id: str
    timestamp: datetime
    recognized_foods: List[Dict[str, float]]  # [{"음식명": 확률}, ...]
    dominant_food: str  # 가장 확률이 높은 음식
    confidence_score: float  # 인식 신뢰도 (0-1)

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
    
class DietEntry(BaseModel):
    """식단 기록 모델"""
    entry_id: str
    user_id: str
    timestamp: datetime
    meal_type: str
    food_items: List[FoodItem]
    total_calories: float
    nutrition_data: Dict[str, float]
    image_id: Optional[str] = None
    notes: Optional[str] = None 