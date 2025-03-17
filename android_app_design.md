# 건강 AI 안드로이드 앱 설계 문서

## 개요
이 문서는 건강 AI API 서버와 연동하여 작동하는 안드로이드 앱의 설계 가이드를 제공합니다. 서버 API 구조를 기반으로 최적의 앱 구조와 기능을 정의합니다. 이 문서는 API 서버에 구현된 실제 기능을 기반으로 작성되었습니다.

## 앱 아키텍처

안드로이드 앱은 현대적인 아키텍처 패턴을 따릅니다:
- **MVVM (Model-View-ViewModel)** 패턴 사용
- **Clean Architecture** 원칙 적용
- **Jetpack Components** 활용 (ViewModel, LiveData, Room, Navigation)
- **Kotlin Coroutines** 및 **Flow**를 사용한 비동기 처리
- **Dagger Hilt** 또는 **Koin**을 통한 의존성 주입
- **Firebase Cloud Messaging**을 통한 푸시 알림 수신 구현

## 주요 모듈

### 1. 인증 모듈
- **로그인 화면**: 사용자명과 비밀번호 입력
- **회원가입 화면**: 사용자 기본 정보 및 건강 정보 입력 (UserCreate 모델 활용)
- **인증 관리**: JWT 토큰 관리 및 자동 로그인 기능 (auth_handler를 통한 인증)
- **프로필 관리**: 사용자 정보 조회 및 수정 (UserProfile 모델 활용)

### 2. 건강 대시보드 모듈
- **메인 대시보드**: 핵심 건강 지표 및 최근 분석 요약 표시
- **건강 지표 입력**: 체중, 혈압, 심박수 등 건강 지표 입력 폼 (HealthMetricsRequest 모델 활용)
- **건강 차트**: 시간에 따른 건강 지표 변화 그래프 (metrics/history API 엔드포인트 활용)
- **건강 상태 요약**: 현재 건강 상태 및 주의사항 표시 (HealthAssessment 모델 활용)

### 3. 건강 데이터 관리 모듈
- **약물 복용 관리**: 복용 중인 약물 등록 및 리마인더 (MedicationIntake 모델 활용)
- **식이 제한 관리**: 알레르기 등 식이 제한 사항 관리 (DietaryRestrictionRequest 모델과 dietary-restrictions API 엔드포인트 활용)
- **건강 프로필 조회**: 종합적인 건강 프로필 정보 조회 (health/profile API 엔드포인트 활용)
- **증상 기록**: 증상 입력 및 기록 (Symptom 모델 활용)

### 4. 음성 인터페이스 모듈
- **음성 비서 화면**: 마이크 아이콘과 음성 입력 UI
- **음성 응답 표시**: 음성 텍스트와 함께 시각적 피드백 제공 (VoiceResponse 모델 활용)
- **음성 상담 기록**: 이전 음성 상담 내용 저장 및 조회 (voice/conversations API 엔드포인트 활용)
- **음성 타입 선택**: 일반 질문 또는 건강 상담 모드 선택 (QueryType 활용)
- **대화 세션 관리**: 대화 세션 시작, 종료 및 기록 관리 (voice/end-conversation API 엔드포인트 활용)
- **대화 컨텍스트 유지**: 대화 맥락을 유지하는 세션 관리 (conversation_id 활용)

### 5. 식단 관리 모듈
- **식단 입력**: 식사 종류 및 음식 항목 입력 (DietEntry, FoodItem 모델 활용)
- **식단 분석**: 입력된 식단의 영양소 분석 결과 표시 (DietAnalysis 모델 활용)
- **식단 기록**: 이전 식단 기록 저장 및 조회
- **직장인 맞춤형 식단 조언**: 사용자가 섭취한/섭취 예정인 음식 내용과 양을 입력하면 건강 상태에 맞는 조언 제공 (Gemini AI 활용)
  - **간편 식단 입력**: 외식, 배달, 편의점 음식 등 실제 섭취 가능한 음식 위주의 간편한 입력 인터페이스
  - **영양 밸런스 분석**: 입력된 식단의 영양 밸런스 분석 및 부족한 영양소 보충 방법 제안
  - **식사량 최적화**: 사용자의 건강 목표(체중 감량, 근육 증가 등)에 맞는 적정 섭취량 조언
  - **대체 음식 추천**: 더 건강한 대체 음식 또는 추가 섭취 권장 음식 추천
  - **식사 시간 조언**: 최적의 식사 시간 및 간격 제안
- **음식 이미지 분석**: 카메라를 통한 음식 이미지 촬영 및 자동 분석 (FoodImageData, FoodImageRecognitionResult, FoodNutritionAnalysis 모델 활용)
- **식단 계획**: 식단 계획 생성 및 관리 (DietPlan, Meal 모델 활용)

### 6. 운동 관리 모듈
- **맞춤형 운동 추천**: 사용자의 건강 상태, 목표, 생활 패턴에 맞는 운동 추천 (Gemini AI 활용)
  - **바쁜 직장인을 위한 시간 효율적 운동**: 짧은 시간에 효과적인 운동 루틴 제공
  - **장소 제약 없는 운동**: 사무실, 집, 출퇴근 시간 등 다양한 환경에서 가능한 운동 제안
  - **강도 조절**: 사용자의 체력 수준과 건강 상태에 맞는 운동 강도 조절
  - **진행 상황 추적**: 운동 기록 및 효과 분석을 통한 동기 부여
  - **운동 영상 연동**: 추천된 운동에 대한 가이드 영상 제공
  - **일정 통합**: 사용자의 일정에 맞춰 최적의 운동 시간 제안

### 7. 건강 관리 전문가 모듈
- **AI 건강 코치**: Gemini AI를 활용한 개인 맞춤형 건강 관리 코치 기능
  - **건강 데이터 통합 분석**: 사용자의 건강 지표, 식단, 운동, 수면 패턴 등을 종합적으로 분석
  - **맞춤형 건강 조언**: 사용자의 생활 패턴과 건강 상태에 맞는 구체적인 조언 제공
  - **목표 설정 및 관리**: 현실적인 건강 목표 설정 및 달성 과정 관리
  - **정기적 건강 리포트**: 주간/월간 건강 상태 변화 및 개선점 리포트 제공
  - **생활 습관 개선 제안**: 작은 변화부터 시작하는 건강한 생활 습관 형성 가이드
  - **스트레스 관리**: 직장인의 스트레스 수준 모니터링 및 관리 방법 제안
- **건강 질문 응답**: 건강 관련 질문에 대한 신뢰할 수 있는 정보 제공
  - **증상 분석**: 사용자가 입력한 증상에 대한 초기 분석 및 조언
  - **건강 지식 제공**: 건강, 질병, 영양에 관한 최신 정보 제공
  - **의학 용어 설명**: 복잡한 의학 용어를 이해하기 쉽게 설명

### 8. 알림 모듈
- **알림 설정**: 알림 시간, 유형 등 설정
- **알림 이력**: 받은 알림 이력 표시
- **FCM 연동**: Firebase Cloud Messaging을 통한 푸시 알림 수신 (AndroidNotification 모델 활용)
- **알림 우선순위**: 건강 경고에 대한 우선순위 높은 알림 전송
- **상담 요약 알림**: 건강 상담 요약 및 권장사항 알림 (ConsultationSummary 모델 활용)

## 데이터 흐름 및 상태 관리

### 1. 인증 흐름
1. 사용자 로그인 → 서버에서 JWT 토큰 발급 → 로컬 저장
2. 토큰 만료 시 자동 갱신 또는 재로그인 요청
3. 로그아웃 시 토큰 폐기 및 로컬 데이터 삭제
4. 모든 API 요청에 Authorization 헤더로 토큰 전달 (get_current_user 의존성 활용)

### 2. 건강 데이터 흐름
1. 로컬 캐싱과 서버 동기화 전략 사용
2. 오프라인 모드 지원: 연결 없이 데이터 입력 가능, 연결 시 자동 동기화
3. 건강 지표 변화에 따른 실시간 분석 및 알림
4. 의미 있는 변화에 대한 자동 분석 요청 구현

### 3. 음성 처리 흐름
1. 음성 입력 → 텍스트 변환 → 서버 전송 → 응답 수신 → 화면 표시/음성 출력
2. 대화 세션 상태 관리: 이전 대화 맥락 유지 및 세션 종료 시 요약 생성
3. 대화 유형에 따른 전문화된 응답 생성 (건강 상담, 일반 질문 구분)
4. 중요한 정보에 대한 별도 저장 및 하이라이트 기능

### 4. 건강 관리 전문가 흐름
1. 사용자 건강 데이터 수집 → Gemini AI 분석 요청 → 맞춤형 조언 생성 → 사용자에게 제공
2. 사용자 피드백 수집 → 조언 품질 개선 → 더 정확한 맞춤형 조언 제공
3. 정기적인 건강 상태 평가 및 목표 달성 진행 상황 업데이트

## API 연동

### 인증 API 연동
```kotlin
// 로그인 예시
suspend fun login(username: String, password: String): Result<TokenResponse> {
    return apiService.login(UserLoginRequest(username, password))
}

// 사용자 정보 조회 예시
suspend fun getUserProfile(): Result<UserProfile> {
    return apiService.getUserProfile(authManager.getToken())
}
```

### 건강 데이터 API 연동
```kotlin
// 건강 지표 추가 예시
suspend fun addHealthMetrics(metrics: HealthMetricsRequest): Result<ApiResponse> {
    return apiService.addHealthMetrics(authManager.getToken(), metrics)
}

// 건강 분석 요청 예시
suspend fun analyzeHealth(query: String): Result<ApiResponse> {
    return apiService.analyzeHealth(authManager.getToken(), HealthQueryRequest(query))
}

// 식이 제한 추가 예시
suspend fun addDietaryRestriction(restriction: DietaryRestrictionRequest): Result<ApiResponse> {
    return apiService.addDietaryRestriction(authManager.getToken(), restriction)
}
```

### 음성 쿼리 API 연동
```kotlin
// 음성 쿼리 처리 예시
suspend fun processVoiceQuery(query: String, type: QueryType): Result<ApiResponse> {
    return apiService.processVoiceQuery(
        VoiceQueryRequest(
            userManager.getUserId(),
            query,
            sessionManager.getCurrentSessionId(),
            type
        )
    )
}

// 대화 세션 종료 예시
suspend fun endConversation(conversationId: String): Result<ApiResponse> {
    return apiService.endConversation(
        authManager.getToken(),
        conversationId
    )
}

// 대화 이력 조회 예시
suspend fun getConversationHistory(conversationId: String): Result<ApiResponse> {
    return apiService.getConversationDetail(
        authManager.getToken(),
        conversationId
    )
}
```

### 식단 관리 API 연동
```kotlin
// 식단 분석 요청 예시
suspend fun analyzeDiet(dietEntry: DietEntry): Result<ApiResponse> {
    return apiService.analyzeDiet(
        authManager.getToken(),
        dietEntry
    )
}

// 직장인 맞춤형 식단 조언 요청 예시
suspend fun getDietAdvice(foodItems: List<FoodItem>, mealType: String): Result<ApiResponse> {
    return apiService.getDietAdvice(
        authManager.getToken(),
        DietAdviceRequest(
            userManager.getUserId(),
            foodItems,
            mealType
        )
    )
}

// 음식 이미지 분석 예시
suspend fun analyzeFoodImage(imageData: ByteArray, mealType: String): Result<ApiResponse> {
    return apiService.analyzeFoodImage(
        authManager.getToken(),
        FoodImageRequest(
            userManager.getUserId(),
            mealType,
            Base64.encodeToString(imageData, Base64.DEFAULT)
        )
    )
}
```

### 운동 관리 API 연동
```kotlin
// 맞춤형 운동 추천 요청 예시
suspend fun getExerciseRecommendation(timeAvailable: Int, location: String, intensity: String): Result<ApiResponse> {
    return apiService.getExerciseRecommendation(
        authManager.getToken(),
        ExerciseRecommendationRequest(
            userManager.getUserId(),
            timeAvailable,
            location,
            intensity
        )
    )
}
```

### 건강 관리 전문가 API 연동
```kotlin
// AI 건강 코치 상담 요청 예시
suspend fun getHealthCoachAdvice(query: String): Result<ApiResponse> {
    return apiService.getHealthCoachAdvice(
        authManager.getToken(),
        HealthCoachRequest(
            userManager.getUserId(),
            query
        )
    )
}

// 주간 건강 리포트 요청 예시
suspend fun getWeeklyHealthReport(): Result<ApiResponse> {
    return apiService.getWeeklyHealthReport(
        authManager.getToken(),
        userManager.getUserId()
    )
}
```

### 알림 API 연동
```kotlin
// FCM 토큰 등록 예시
suspend fun registerDeviceToken(token: String, settings: NotificationSettings): Result<ApiResponse> {
    return apiService.registerDeviceToken(
        authManager.getToken(),
        DeviceTokenRequest(
            userManager.getUserId(),
            token,
            settings
        )
    )
}
```

## API 엔드포인트 상세 명세

### 식단 조언 API (Diet Advice API)

#### 엔드포인트: `/api/v1/diet/advice`

#### 메소드: POST

#### 인증: Bearer Token 필요

#### 요청 파라미터 (Request Body)

```json
{
  "request_id": "20250317055817",  // 선택적, 제공하지 않으면 서버에서 자동 생성 (현재 시간 기반)
  "user_id": "0b3d8b66-70ff-4cb8-bdcf-a9b7b14c70d8",  // 필수, 사용자 ID
  "current_diet": [  // 필수, 현재 식단 정보 (배열)
    {
      "meal_type": "아침",  // 식사 유형 (아침, 점심, 저녁, 간식 등)
      "food_items": [  // 음식 항목 배열
        {
          "name": "계란",  // 음식 이름
          "amount": "2개"  // 섭취량
        },
        {
          "name": "토스트",
          "amount": "2조각"
        },
        {
          "name": "우유",
          "amount": "1잔"
        }
      ]
    }
  ],
  "dietary_restrictions": ["글루텐", "유당"],  // 선택적, 식이 제한 사항 (알레르기 등)
  "health_goals": ["체중 감량", "근육 증가"],  // 선택적, 건강 목표
  "specific_concerns": "단백질 섭취량을 늘리고 싶습니다."  // 선택적, 특정 관심사 또는 우려사항
}
```

#### 응답 형식 (Response)

```json
{
  "success": true,  // API 요청 성공 여부
  "message": "식단 조언이 생성되었습니다",  // 응답 메시지
  "data": {  // 응답 데이터
    "response_id": "41b70cb1-6e75-4dd4-89b6-71a4cf975e77",  // 응답 ID (UUID)
    "request_id": "20250317044439",  // 요청 ID
    "timestamp": "2025-03-17T04:44:56.145872",  // 응답 생성 시간
    "diet_assessment": "현재 식단은 단백질이 부족하고 탄수화물 비율이 높습니다. 총 칼로리는 450kcal로 아침 식사로는 적절하나, 영양 균형을 개선할 필요가 있습니다.",  // 식단 평가
    "improvement_suggestions": [  // 개선 제안 (배열)
      "단백질 섭취를 늘리기 위해 계란 흰자를 추가하거나 그릭 요거트를 간식으로 섭취하세요.",
      "토스트 대신 통곡물 빵을 선택하여 복합 탄수화물 섭취를 늘리세요.",
      "건강한 지방 섭취를 위해 아보카도나 견과류를 추가하세요."
    ],
    "alternative_foods": [  // 대체 식품 제안 (배열)
      {
        "original": "흰 토스트",
        "alternative": "통밀빵"
      },
      {
        "original": "우유",
        "alternative": "무가당 두유 또는 아몬드 밀크"
      }
    ],
    "health_tips": "체중 감량과 근육 증가를 동시에 이루기 위해서는 단백질 섭취를 우선시하고, 적절한 운동과 함께 균형 잡힌 식단을 유지하는 것이 중요합니다. 하루 총 칼로리는 약간 제한하되, 단백질은 체중 1kg당 1.6-2.2g을 목표로 하세요.",  // 건강 팁
    "nutrition_analysis": {  // 영양소 분석
      "protein": "현재 식단의 단백질 함량은 약 20g으로, 목표치(약 40-50g)에 비해 부족합니다.",
      "carbs": "탄수화물 비율이 65%로 다소 높습니다. 50% 이하로 줄이는 것이 좋습니다.",
      "fat": "지방 함량이 15%로 낮은 편입니다. 건강한 지방을 25-30%까지 늘리는 것이 좋습니다.",
      "vitamins": "비타민 D와 비타민 C가 부족할 수 있습니다. 과일이나 채소를 추가하세요.",
      "minerals": "칼슘은 충분하나 마그네슘과 철분이 부족할 수 있습니다.",
      "balance": "전체적으로 탄수화물 비중이 높고 단백질과 건강한 지방이 부족합니다."
    }
  }
}
```

#### 안드로이드 앱 연동 예시

```kotlin
// 식단 조언 요청 예시
suspend fun getDietAdvice(
    currentDiet: List<MealData>,
    healthGoals: List<String>? = null,
    dietaryRestrictions: List<String>? = null,
    specificConcerns: String? = null
): Result<ApiResponse> {
    return apiService.getDietAdvice(
        authManager.getToken(),
        DietAdviceRequest(
            user_id = userManager.getUserId(),
            current_diet = currentDiet,
            health_goals = healthGoals,
            dietary_restrictions = dietaryRestrictions,
            specific_concerns = specificConcerns
        )
    )
}

// 식단 조언 요청 모델
data class DietAdviceRequest(
    val user_id: String,
    val current_diet: List<MealData>,
    val dietary_restrictions: List<String>? = null,
    val health_goals: List<String>? = null,
    val specific_concerns: String? = null,
    val request_id: String = SimpleDateFormat("yyyyMMddHHmmss", Locale.getDefault()).format(Date())
)

// 식사 데이터 모델
data class MealData(
    val meal_type: String,
    val food_items: List<FoodItem>
)

// 음식 항목 모델
data class FoodItem(
    val name: String,
    val amount: String
)

// 식단 조언 응답 처리 예시
viewModelScope.launch {
    val result = dietRepository.getDietAdvice(
        currentDiet = listOf(
            MealData(
                meal_type = "아침",
                food_items = listOf(
                    FoodItem("계란", "2개"),
                    FoodItem("토스트", "2조각"),
                    FoodItem("우유", "1잔")
                )
            )
        ),
        healthGoals = listOf("체중 감량", "근육 증가"),
        specificConcerns = "단백질 섭취량을 늘리고 싶습니다."
    )
    
    when (result) {
        is Result.Success -> {
            val dietAdvice = result.data.data
            // UI 업데이트
            _dietAssessment.value = dietAdvice["diet_assessment"] as String
            _improvementSuggestions.value = dietAdvice["improvement_suggestions"] as List<String>
            _alternativeFoods.value = dietAdvice["alternative_foods"] as List<Map<String, String>>
            _healthTips.value = dietAdvice["health_tips"] as String
            _nutritionAnalysis.value = dietAdvice["nutrition_analysis"] as Map<String, String>
        }
        is Result.Error -> {
            // 오류 처리
            _errorMessage.value = "식단 조언을 가져오는 중 오류가 발생했습니다: ${result.exception.message}"
        }
    }
}
```

#### 주요 UI 구성 요소

1. **식단 입력 화면**
   - 식사 유형 선택 (아침, 점심, 저녁, 간식)
   - 음식 항목 추가 기능 (이름, 양, 칼로리)
   - 자주 먹는 음식 빠른 추가 기능
   - 건강 목표 및 식이 제한 선택 옵션
   - 특정 관심사 입력 텍스트 필드

2. **식단 조언 결과 화면**
   - 식단 평가 요약 섹션
   - 개선 제안 목록 (카드 형태로 표시)
   - 대체 식품 추천 섹션 (원본 → 대체 형태로 표시)
   - 건강 팁 섹션
   - 영양소 분석 차트 및 상세 설명

3. **식단 기록 및 추적 화면**
   - 이전 식단 기록 목록
   - 식단 조언 이력
   - 시간에 따른 식단 개선 추적 그래프

### 식단 전문가 조언 API (Diet Specialist Advice API)

#### 엔드포인트: `/api/v1/diet/specialist-advice`

#### 메소드: POST

#### 인증: Bearer Token 필요

#### 요청 파라미터 (Request Body)

```json
{
  "request_id": "20250317055817",  // 선택적, 제공하지 않으면 서버에서 자동 생성 (현재 시간 기반)
  "user_id": "0b3d8b66-70ff-4cb8-bdcf-a9b7b14c70d8",  // 필수, 사용자 ID
  "current_diet": [  // 필수, 현재 식단 정보 (배열)
    {
      "meal_type": "아침",  // 식사 유형 (아침, 점심, 저녁, 간식 등)
      "food_items": [  // 음식 항목 배열
        {
          "name": "흰 쌀밥",  // 음식 이름
          "amount": "1공기"  // 섭취량
        },
        {
          "name": "계란 프라이",
          "amount": "1개"
        },
        {
          "name": "김치",
          "amount": "1접시"
        }
      ]
    }
  ],
  "dietary_restrictions": ["고혈압"],  // 선택적, 식이 제한 사항 (알레르기, 질환 등)
  "health_goals": ["체중 감량", "균형 잡힌 식단"],  // 선택적, 건강 목표
  "specific_concerns": "체중을 줄이면서 영양 균형을 맞추고 싶습니다."  // 선택적, 특정 관심사 또는 우려사항
}
```

#### 응답 형식 (Response)

```json
{
  "success": true,  // API 요청 성공 여부
  "message": "식단 조언이 생성되었습니다",  // 응답 메시지
  "data": {  // 응답 데이터
    "advice": "안녕하세요. 51세 남성분의 식단에 대한 전문적인 영양 조언을 제공합니다. 현재 체중과 키를 고려했을 때 BMI가 33.7로 비만 범주에 속하며, 건강 목표가 균형 잡힌 식단이므로 체중 관리와 전반적인 건강 증진을 위한 식단 개선이 필요합니다. \n\n**1. 현재 식단 평가:**\n현재 아침 식단은 흰 쌀밥, 계란 프라이, 김치로 구성되어 있습니다. 탄수화물 위주의 식단이며, 단백질과 식이섬유 섭취량이 부족합니다. 흰 쌀밥은 혈당을 빠르게 상승시킬 수 있으며, 계란 프라이는 조리 방식에 따라 지방 함량이 높아질 수 있습니다. 김치는 발효 식품으로 유산균 섭취에 도움이 되지만, 나트륨 함량이 높을 수 있습니다. 전반적으로 영양 불균형이 우려됩니다.\n\n**2. 개선 제안:**\n* **탄수화물 종류 변경:** 흰 쌀밥 대신 현미, 잡곡, 통밀빵 등 정제되지 않은 곡물을 섭취하여 혈당 조절과 포만감을 높이는 것이 좋습니다. 밥의 양도 줄여서 섭취량을 조절하는 것이 필요합니다.\n* **단백질 섭취량 증가:** 계란 프라이 외에 닭가슴살, 생선, 두부, 콩 등 다양한 단백질 식품을 추가하여 근육 유지 및 성장에 도움을 주어야 합니다. 계란 조리 방식은 삶거나 찌는 방식으로 변경하여 지방 섭취를 줄이는 것이 좋습니다.\n* **식이섬유 섭취량 증가:** 채소와 과일을 충분히 섭취하여 식이섬유 섭취량을 늘려야 합니다. 식이섬유는 포만감을 높이고, 혈당 조절 및 배변 활동에 도움을 줍니다.\n* **나트륨 섭취량 감소:** 김치 섭취량을 줄이거나, 덜 짜게 담근 김치를 선택하는 것이 좋습니다. 국이나 찌개 섭취 시 국물은 최대한 적게 먹는 것이 좋습니다.\n* **균형 잡힌 식단 구성:** 아침, 점심, 저녁 식사 모두 탄수화물, 단백질, 지방, 비타민, 미네랄을 골고루 섭취하는 것이 중요합니다.\n\n**3. 대체 식품 추천:**\n* **흰 쌀밥 → 현미밥, 잡곡밥, 통밀빵, 고구마, 귀리**\n* **계란 프라이 → 삶은 계란, 찐 계란, 두부, 닭가슴살, 생선**\n* **김치 → 샐러드, 브로콜리, 시금치, 오이, 파프리카 등 다양한 채소**\n* **간식 → 과일, 견과류, 요거트**\n\n**4. 건강 목표 달성을 위한 팁:**\n* **규칙적인 식사:** 정해진 시간에 규칙적으로 식사하는 것이 중요합니다.\n* **천천히 식사:** 음식을 천천히 꼭꼭 씹어 먹으면 포만감을 느끼기 쉽고, 소화에도 도움이 됩니다.\n* **충분한 수분 섭취:** 하루 8잔 이상의 물을 마셔 수분 섭취량을 늘려야 합니다.\n* **꾸준한 운동:** 규칙적인 운동은 체중 관리 및 건강 증진에 필수적입니다.\n* **식단 기록:** 식단 기록을 통해 자신의 식습관을 파악하고 개선하는 데 도움이 됩니다.\n\n**5. 영양소 분석 (추정치, 아침 식단 기준):**\n* **단백질:** 약 7-8g (계란 1개 기준)\n* **탄수화물:** 약 60-70g (흰 쌀밥 1공기 기준)\n* **지방:** 약 10-15g (계란 프라이 조리 방식에 따라 다름)\n* **비타민:** 비타민 B군 (계란), 비타민 C (김치)\n* **미네랄:** 칼륨, 칼슘 (김치), 철분 (계란)\n* **전체 균형:** 탄수화물 비중이 높고, 단백질과 식이섬유 비율이 낮아 불균형합니다. 나트륨 함량도 높을 수 있습니다.\n\n**종합적으로,** 현재 식단은 개선이 필요하며, 위에 제시된 제안들을 바탕으로 균형 잡힌 식단을 구성하는 것이 중요합니다. 꾸준한 노력과 건강한 식습관을 통해 건강 목표를 달성하시길 바랍니다. 필요하다면 전문 영양사와 상담하여 개인 맞춤형 식단 계획을 세우는 것을 추천합니다."
  }
}
```

#### 안드로이드 앱 연동 예시

```kotlin
// 식단 전문가 조언 요청 예시
suspend fun getDietSpecialistAdvice(
    currentDiet: List<MealData>,
    healthGoals: List<String>? = null,
    dietaryRestrictions: List<String>? = null,
    specificConcerns: String? = null
): Result<ApiResponse> {
    return apiService.getDietSpecialistAdvice(
        authManager.getToken(),
        DietAdviceRequest(
            user_id = userManager.getUserId(),
            current_diet = currentDiet,
            health_goals = healthGoals,
            dietary_restrictions = dietaryRestrictions,
            specific_concerns = specificConcerns
        )
    )
}

// 식단 전문가 조언 응답 처리 예시
viewModelScope.launch {
    val result = dietRepository.getDietSpecialistAdvice(
        currentDiet = listOf(
            MealData(
                meal_type = "아침",
                food_items = listOf(
                    FoodItem("흰 쌀밥", "1공기"),
                    FoodItem("계란 프라이", "1개"),
                    FoodItem("김치", "1접시")
                )
            )
        ),
        healthGoals = listOf("체중 감량", "균형 잡힌 식단"),
        specificConcerns = "체중을 줄이면서 영양 균형을 맞추고 싶습니다."
    )
    
    when (result) {
        is Result.Success -> {
            val dietAdvice = result.data.data
            // UI 업데이트
            _specialistAdvice.value = dietAdvice["advice"] as String
        }
        is Result.Error -> {
            // 오류 처리
            _errorMessage.value = "식단 전문가 조언을 가져오는 중 오류가 발생했습니다: ${result.exception.message}"
        }
    }
}
```

#### 주요 UI 구성 요소

1. **식단 전문가 조언 화면**
   - 식단 입력 섹션 (식사 유형, 음식 항목 추가)
   - 건강 목표 및 식이 제한 선택 옵션
   - 특정 관심사 입력 텍스트 필드
   - 전문가 조언 결과 표시 영역 (마크다운 형식 지원)
   - 조언 저장 및 공유 기능

## UI/UX 가이드라인

### 1. 디자인 시스템
- **Material Design 3** 적용: 동적 색상 시스템 활용
- 다크 모드 지원
- 접근성 고려: 글꼴 크기 조정, 대비, 스크린 리더 지원

### 2. 주요 화면 레이아웃
- **홈 화면**: 건강 상태 요약, 최근 측정값, 빠른 작업 버튼
- **건강 입력 화면**: 직관적인 입력 폼, 이전 값 참조 기능
- **분석 결과 화면**: 시각적 요약과 상세 텍스트 분석 병행
- **음성 인터페이스**: 음성 입력 중 시각적 피드백, 텍스트 전환 기능
- **대화 기록 화면**: 과거 대화 내용과 중요 시점 하이라이트 표시
- **식단 분석 화면**: 영양소 그래프와 권장사항 표시
- **운동 추천 화면**: 시간별, 장소별 맞춤형 운동 카드 형태로 제공
- **건강 코치 화면**: 대화형 인터페이스와 주요 건강 조언 카드 형태로 제공

### 3. 상호작용 패턴
- **음성과 터치의 병행**: 모든 음성 기능은 터치로도 접근 가능
- **컨텍스트 인식**: 사용자 상황에 맞는 UI 요소 제공
- **점진적 공개**: 복잡한 기능은 필요에 따라 단계적으로 노출
- **실시간 피드백**: 데이터 입력과 처리 상태에 대한 시각적 피드백

## 기술 스택 권장사항

### 기본 구성
### 데이터 저장
- **Room**: 로컬 데이터베이스
- **DataStore**: 사용자 설정 및 토큰 저장
- **WorkManager**: 백그라운드 동기화 작업

### 음성 및 이미지 처리
- **ML Kit Speech Recognition**: 음성 인식 기능
- **CameraX**: 최신 카메라 API로 음식 이미지 촬영
- **Glide/Coil**: 이미지 로딩 및 캐싱

### 분석 및 모니터링
- **Firebase Analytics**: 사용자 행동 분석
- **Firebase Crashlytics**: 오류 보고
- **Performance Monitoring**: 앱 성능 모니터링

## 구현 우선순위

1. **필수 구현 사항**
   - 사용자 인증 시스템 (JWT 토큰 관리)
   - 기본 건강 지표 입력 및 조회
   - 음성 인터페이스 기본 기능
   - 건강 분석 요청 및 결과 표시
   - FCM 알림 수신 구현

2. **2차 구현 사항**
   - 상세 건강 차트 및 분석
   - 식이 제한 관리
   - 직장인 맞춤형 식단 조언 기능
   - 바쁜 직장인을 위한 맞춤형 운동 추천
   - 약물 복용 알림
   - 대화 세션 기록 및 요약 기능

3. **고급 기능 (추후 구현)**
   - 음식 이미지 분석
   - AI 건강 코치 기능
   - 건강 목표에 따른 맞춤형 조언
   - 다른 건강 기기와 연동
   - 오프라인 모드 지원
   - 고급 음성 상담 기능

## 보안 고려사항

- **토큰 관리**: JWT 토큰의 안전한 저장 및 갱신
- **민감 정보 보호**: 건강 데이터 암호화
- **네트워크 보안**: HTTPS 통신, 인증서 피닝
- **접근 제어**: 바이오메트릭 인증 옵션 제공
- **데이터 백업**: 사용자 데이터의 안전한 백업 및 복원 기능

## 결론

이 설계 문서는 현재 API 서버 구조에 최적화된 안드로이드 앱의 구현 가이드를 제공합니다. 현재 구현된 API 엔드포인트, 데이터 모델 및 기능을 기반으로 안드로이드 앱이 건강 AI 서비스의 기능을 최대한 활용할 수 있도록 설계되었습니다. 실제 API 구현을 기반으로 하는 이 문서는 개발자가 서버와 클라이언트 사이의 일관된 통합을 구현할 수 있도록 도와줍니다.

이 앱은 사용자 중심 설계를 바탕으로 직관적인 인터페이스와 안정적인 성능을 제공하는 것을 목표로 합니다. API 서버의 기능이 확장됨에 따라 앱의 기능도 점진적으로 확장할 수 있습니다. 