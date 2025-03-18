# 운동 추천 기능 구현 가이드

## API 개요

운동 추천 기능은 사용자의 건강 정보와 목표를 기반으로 개인 맞춤형 운동 계획을 생성해주는 기능입니다. 이 API는 사용자의 운동 목적을 입력받아 AI가 분석한 적절한 운동 계획을 반환합니다. 각 운동에는 YouTube 검색 링크가 포함되어 사용자가 쉽게 운동 방법을 찾아볼 수 있도록 지원합니다.

## API 엔드포인트

- **URL**: `/api/v1/exercise/recommendation`
- **Method**: POST
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 인증 요구사항

이 API는 인증이 필요합니다. 요청 헤더에 다음과 같이 인증 토큰을 포함해야 합니다:

```
Authorization: Bearer <your-jwt-token>
```

JWT 토큰은 로그인 API(`/api/v1/auth/login`)를 통해 획득할 수 있습니다.

## 요청 파라미터

```json
{
  "goal": "운동 목적 텍스트 (필수)",
  "fitness_level": "사용자 피트니스 레벨 (선택, '초보자'/'중급자'/'고급자')",
  "medical_conditions": ["기존 질환 리스트 (선택)"]
}
```

### 필수 파라미터

- **goal** (String): 사용자의 운동 목적을 자연어로 설명합니다. 예: "체중 감량을 위한 홈트레이닝 추천", "근력 강화를 위한 운동 계획 필요"

### 선택 파라미터

- **fitness_level** (String): 사용자의 현재 피트니스 레벨을 지정합니다. 값이 없을 경우 서버에서 자동으로 판단합니다.
- **medical_conditions** (String[]): 사용자의 기존 질환 리스트입니다. 값이 없을 경우 서버에서 사용자 프로필에서 자동으로 가져옵니다.

## 응답 구조

```json
{
  "recommendation_id": "추천 ID",
  "user_id": "사용자 ID",
  "goal": "운동 목적",
  "fitness_level": "피트니스 레벨 (초보자/중급자/고급자)",
  "recommended_frequency": "권장 운동 빈도 (예: 주 3회)",
  "exercise_plans": [
    {
      "name": "운동명",
      "description": "운동 방법 설명",
      "duration": "권장 시간",
      "benefits": "효과",
      "youtube_link": "YouTube 검색 링크"
    },
    // 추가 운동들...
  ],
  "special_instructions": ["특별 지시사항1", "특별 지시사항2", ...],
  "recommendation_summary": "전체 운동 계획 요약",
  "timestamp": "생성 시간 (ISO 8601 형식)"
}
```

### 응답 필드 상세

- **recommendation_id** (String): 추천 결과의 고유 식별자
- **user_id** (String): 요청한 사용자의 ID (토큰에서 자동으로 추출)
- **goal** (String): 사용자가 입력한 운동 목적
- **fitness_level** (String): 추천된 운동의 난이도 수준 ("초보자", "중급자", "고급자" 중 하나)
- **recommended_frequency** (String): 권장 운동 빈도 (예: "주 3회", "매일" 등)
- **exercise_plans** (Array): 추천 운동 목록
  - **name** (String): 운동 이름
  - **description** (String): 운동 방법 상세 설명
  - **duration** (String): 권장 운동 시간 (예: "30분")
  - **benefits** (String): 해당 운동의 효과
  - **youtube_link** (String): 운동 방법을 찾아볼 수 있는 YouTube 검색 URL
- **special_instructions** (Array): 운동 시 주의사항 목록
- **recommendation_summary** (String): 전체 운동 계획에 대한 요약 설명
- **timestamp** (String): 추천 생성 시간 (ISO 8601 형식)

## 에러 응답

```json
{
  "detail": "에러 메시지"
}
```

### 주요 에러 코드

- **401**: 인증 실패 또는 토큰 만료
- **500**: 서버 내부 오류 또는 운동 추천 생성 실패

## 안드로이드 구현 가이드

### 1. Retrofit 인터페이스 설정

```kotlin
interface ExerciseApiService {
    @POST("api/v1/exercise/recommendation")
    suspend fun getExerciseRecommendation(
        @Body request: ExerciseRecommendationRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseRecommendationResponse>
}

data class ExerciseRecommendationRequest(
    val goal: String,
    val fitness_level: String? = null,
    val medical_conditions: List<String>? = null
)

data class ExerciseRecommendationResponse(
    val recommendation_id: String,
    val user_id: String,
    val goal: String,
    val fitness_level: String,
    val recommended_frequency: String,
    val exercise_plans: List<ExercisePlan>,
    val special_instructions: List<String>,
    val recommendation_summary: String,
    val timestamp: String
)

data class ExercisePlan(
    val name: String,
    val description: String,
    val duration: String,
    val benefits: String,
    val youtube_link: String
)

```

## 사용 예시

1. 사용자가 로그인 후 운동 추천 화면으로 이동합니다.
2. 사용자는 운동 목적을 상세하게 입력합니다. (예: "체중 감량과 근력 강화를 위한 홈트레이닝 추천해줘")
3. '운동 추천 받기' 버튼을 누르면 API 호출이 시작됩니다.
4. 로딩 중에는 진행 상태 표시기가 표시됩니다.
5. 응답이 오면 추천 운동 계획과 함께 각 운동별 YouTube 링크가 표시됩니다.
6. 사용자는 운동을 선택하고 YouTube 링크를 통해 운동 방법을 볼 수 있습니다.

## 인증 관련 주의사항

1. API 요청 전 유효한 토큰이 있는지 확인하고, 만료된 경우 사용자를 로그인 화면으로 리디렉션해야 합니다.
2. 토큰 관리를 위해 안전한 저장소(EncryptedSharedPreferences 또는 DataStore with security)를 사용해야 합니다.
3. 백그라운드 작업이나 앱 재시작 후에도 토큰이 유지되도록 설계해야 합니다.

## 기타 주의사항

1. 추천 결과는 5-10초 정도 시간이 소요될 수 있으므로 적절한 로딩 표시가 필요합니다.
2. YouTube 링크 열기는 외부 앱 실행을 요구하므로 인텐트 처리 시 예외 상황에 대한 처리가 필요합니다.
3. 네트워크 오류 및 타임아웃에 대한 적절한 처리가 구현되어야 합니다. 