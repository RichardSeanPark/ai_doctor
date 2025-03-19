# 운동 추천 기능 구현 가이드

## API 개요

운동 추천 기능은 사용자의 건강 정보와 목표를 기반으로 개인 맞춤형 운동 계획을 생성해주는 기능입니다. 이 API는 사용자의 운동 목적을 입력받아 AI가 분석한 적절한 운동 계획을 반환합니다. 각 운동에는 YouTube 검색 링크가 포함되어 사용자가 쉽게 운동 방법을 찾아볼 수 있도록 지원합니다.

## API 엔드포인트 목록

1. **운동 추천 생성**: 사용자 목표에 맞는 개인화된 운동 계획 생성
   - `POST /api/v1/exercise/recommendation`

2. **운동 추천 이력 조회**: 사용자의 과거 운동 추천 기록 조회
   - `GET /api/v1/exercise/recommendations_history`

3. **특정 운동 추천 조회**: 특정 ID의 운동 추천 상세 정보 조회
   - `GET /api/v1/exercise/recommendation/{recommendation_id}`

4. **운동 완료 상태 업데이트**: 운동 완료 여부 표시
   - `PATCH /api/v1/exercise/recommendation/{recommendation_id}/completion`

5. **운동 일정 예약**: 운동 일정 예약 시간 설정
   - `PATCH /api/v1/exercise/recommendation/{recommendation_id}/schedule`

## 인증 요구사항

모든 API는 인증이 필요합니다. 요청 헤더에 다음과 같이 인증 토큰을 포함해야 합니다:

```
Authorization: Bearer <your-jwt-token>
```

JWT 토큰은 로그인 API(`/api/v1/auth/login`)를 통해 획득할 수 있습니다.

# 1. 운동 추천 생성 API

## 엔드포인트

- **URL**: `/api/v1/exercise/recommendation`
- **Method**: POST
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

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
  "timestamp": "생성 시간 (ISO 8601 형식)",
  "completed": false,
  "scheduled_time": null
}
```

# 2. 운동 추천 이력 조회 API

## 엔드포인트

- **URL**: `/api/v1/exercise/recommendations_history`
- **Method**: GET
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 요청 파라미터

### 쿼리 파라미터

- **limit** (Integer, 선택): 반환할 최대 결과 수 (기본값: 10, 최소: 1, 최대: 50)
  - 예시: `/api/v1/exercise/recommendations_history?limit=20`

## 응답 구조

```json
[
  {
    "recommendation_id": "추천 ID",
    "user_id": "사용자 ID",
    "goal": "운동 목적",
    "fitness_level": "피트니스 레벨",
    "recommended_frequency": "권장 운동 빈도",
    "exercise_plans": [
      {
        "name": "운동명",
        "description": "운동 방법 설명",
        "duration": "권장 시간",
        "benefits": "효과",
        "youtube_link": "YouTube 검색 링크"
      }
      // 추가 운동들...
    ],
    "special_instructions": ["특별 지시사항1", "특별 지시사항2", ...],
    "recommendation_summary": "전체 운동 계획 요약",
    "timestamp": "생성 시간 (ISO 8601 형식)",
    "completed": false,
    "scheduled_time": null
  },
  // 추가 추천 기록들...
]
```

# 3. 특정 운동 추천 조회 API

## 엔드포인트

- **URL**: `/api/v1/exercise/recommendation/{recommendation_id}`
- **Method**: GET
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 요청 파라미터

### 경로 파라미터

- **recommendation_id** (String, 필수): 조회할 운동 추천의 고유 ID

## 응답 구조

```json
{
  "recommendation_id": "추천 ID",
  "user_id": "사용자 ID",
  "goal": "운동 목적",
  "fitness_level": "피트니스 레벨",
  "recommended_frequency": "권장 운동 빈도",
  "exercise_plans": [
    {
      "name": "운동명",
      "description": "운동 방법 설명",
      "duration": "권장 시간",
      "benefits": "효과",
      "youtube_link": "YouTube 검색 링크"
    }
    // 추가 운동들...
  ],
  "special_instructions": ["특별 지시사항1", "특별 지시사항2", ...],
  "recommendation_summary": "전체 운동 계획 요약",
  "timestamp": "생성 시간 (ISO 8601 형식)",
  "completed": false,
  "scheduled_time": null
}
```

# 4. 운동 완료 상태 업데이트 API

## 엔드포인트

- **URL**: `/api/v1/exercise/recommendation/{recommendation_id}/completion`
- **Method**: PATCH
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 요청 파라미터

### 경로 파라미터

- **recommendation_id** (String, 필수): 업데이트할 운동 추천의 고유 ID

### 요청 본문

```json
{
  "completed": true
}
```

- **completed** (Boolean, 필수): 운동 완료 상태 (true: 완료, false: 미완료)

## 응답 구조

```json
{
  "recommendation_id": "추천 ID",
  "user_id": "사용자 ID",
  "goal": "운동 목적",
  "fitness_level": "피트니스 레벨",
  "recommended_frequency": "권장 운동 빈도",
  "exercise_plans": [
    {
      "name": "운동명",
      "description": "운동 방법 설명",
      "duration": "권장 시간",
      "benefits": "효과",
      "youtube_link": "YouTube 검색 링크"
    }
    // 추가 운동들...
  ],
  "special_instructions": ["특별 지시사항1", "특별 지시사항2", ...],
  "recommendation_summary": "전체 운동 계획 요약",
  "timestamp": "생성 시간 (ISO 8601 형식)",
  "completed": true,
  "scheduled_time": null
}
```

# 5. 운동 일정 예약 API

## 엔드포인트

- **URL**: `/api/v1/exercise/recommendation/{recommendation_id}/schedule`
- **Method**: PATCH
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 요청 파라미터

### 경로 파라미터

- **recommendation_id** (String, 필수): 업데이트할 운동 추천의 고유 ID

### 요청 본문

```json
{
  "scheduled_time": "2025-03-25T14:00:00"
}
```

- **scheduled_time** (String, 필수): 운동 예약 시간 (ISO 8601 형식)

## 응답 구조

```json
{
  "recommendation_id": "추천 ID",
  "user_id": "사용자 ID",
  "goal": "운동 목적",
  "fitness_level": "피트니스 레벨",
  "recommended_frequency": "권장 운동 빈도",
  "exercise_plans": [
    {
      "name": "운동명",
      "description": "운동 방법 설명",
      "duration": "권장 시간",
      "benefits": "효과",
      "youtube_link": "YouTube 검색 링크"
    }
    // 추가 운동들...
  ],
  "special_instructions": ["특별 지시사항1", "특별 지시사항2", ...],
  "recommendation_summary": "전체 운동 계획 요약",
  "timestamp": "생성 시간 (ISO 8601 형식)",
  "completed": false,
  "scheduled_time": "2025-03-25T14:00:00"
}
```

## 응답 필드 상세

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
- **completed** (Boolean): 운동 완료 여부
- **scheduled_time** (String): 예약된 운동 시간 (ISO 8601 형식)

## 에러 응답

```json
{
  "detail": "에러 메시지"
}
```

### 주요 에러 코드

- **401**: 인증 실패 또는 토큰 만료
- **403**: 권한 없음 (다른 사용자의 리소스 접근 시도)
- **404**: 리소스를 찾을 수 없음 (존재하지 않는 추천 ID)
- **500**: 서버 내부 오류

## 안드로이드 구현 가이드

### Retrofit 인터페이스 설정

```kotlin
interface ExerciseApiService {
    // 1. 운동 추천 생성
    @POST("api/v1/exercise/recommendation")
    suspend fun getExerciseRecommendation(
        @Body request: ExerciseRecommendationRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseRecommendationResponse>
    
    // 2. 운동 추천 이력 조회
    @GET("api/v1/exercise/recommendations_history")
    suspend fun getExerciseRecommendationsHistory(
        @Query("limit") limit: Int = 10,
        @Header("Authorization") authToken: String
    ): Response<List<ExerciseRecommendationResponse>>
    
    // 3. 특정 운동 추천 조회
    @GET("api/v1/exercise/recommendation/{recommendationId}")
    suspend fun getSpecificExerciseRecommendation(
        @Path("recommendationId") recommendationId: String,
        @Header("Authorization") authToken: String
    ): Response<ExerciseRecommendationResponse>
    
    // 4. 운동 완료 상태 업데이트
    @PATCH("api/v1/exercise/recommendation/{recommendationId}/completion")
    suspend fun updateExerciseCompletion(
        @Path("recommendationId") recommendationId: String,
        @Body request: ExerciseCompletionRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseRecommendationResponse>
    
    // 5. 운동 일정 예약
    @PATCH("api/v1/exercise/recommendation/{recommendationId}/schedule")
    suspend fun scheduleExercise(
        @Path("recommendationId") recommendationId: String,
        @Body request: ExerciseScheduleRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseRecommendationResponse>
}

// 요청 모델
data class ExerciseRecommendationRequest(
    val goal: String,
    val fitness_level: String? = null,
    val medical_conditions: List<String>? = null
)

data class ExerciseCompletionRequest(
    val completed: Boolean
)

data class ExerciseScheduleRequest(
    val scheduled_time: String // ISO 8601 형식 (예: "2025-03-25T14:00:00")
)

// 응답 모델
data class ExerciseRecommendationResponse(
    val recommendation_id: String,
    val user_id: String,
    val goal: String,
    val fitness_level: String,
    val recommended_frequency: String,
    val exercise_plans: List<ExercisePlan>,
    val special_instructions: List<String>,
    val recommendation_summary: String,
    val timestamp: String,
    val completed: Boolean,
    val scheduled_time: String?
)

data class ExercisePlan(
    val name: String,
    val description: String,
    val duration: String,
    val benefits: String,
    val youtube_link: String
)
```

### Repository 구현 예시

```kotlin
class ExerciseRepository(
    private val exerciseApiService: ExerciseApiService,
    private val authManager: AuthManager
) {
    // 1. 운동 추천 생성
    suspend fun getExerciseRecommendation(goal: String, fitnessLevel: String? = null): Result<ExerciseRecommendationResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val request = ExerciseRecommendationRequest(goal, fitnessLevel)
            val response = exerciseApiService.getExerciseRecommendation(request, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 추천 요청 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 2. 운동 추천 이력 조회
    suspend fun getExerciseRecommendationsHistory(limit: Int = 10): Result<List<ExerciseRecommendationResponse>> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val response = exerciseApiService.getExerciseRecommendationsHistory(limit, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 추천 이력 조회 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 3. 특정 운동 추천 조회
    suspend fun getSpecificExerciseRecommendation(recommendationId: String): Result<ExerciseRecommendationResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val response = exerciseApiService.getSpecificExerciseRecommendation(recommendationId, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("특정 운동 추천 조회 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 4. 운동 완료 상태 업데이트
    suspend fun updateExerciseCompletion(recommendationId: String, completed: Boolean): Result<ExerciseRecommendationResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val request = ExerciseCompletionRequest(completed)
            val response = exerciseApiService.updateExerciseCompletion(recommendationId, request, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 완료 상태 업데이트 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 5. 운동 일정 예약
    suspend fun scheduleExercise(recommendationId: String, scheduledTime: String): Result<ExerciseRecommendationResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val request = ExerciseScheduleRequest(scheduledTime)
            val response = exerciseApiService.scheduleExercise(recommendationId, request, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 일정 예약 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

## 사용 예시

1. **운동 추천 받기**:
   ```kotlin
   viewModelScope.launch {
       when (val result = exerciseRepository.getExerciseRecommendation("체중 감량을 위한 효과적인 운동", "초보자")) {
           is Result.Success -> {
               val recommendation = result.data
               // UI 업데이트
           }
           is Result.Failure -> {
               // 오류 처리
           }
       }
   }
   ```

2. **운동 이력 조회**:
   ```kotlin
   viewModelScope.launch {
       when (val result = exerciseRepository.getExerciseRecommendationsHistory()) {
           is Result.Success -> {
               val recommendations = result.data
               // RecyclerView 업데이트
           }
           is Result.Failure -> {
               // 오류 처리
           }
       }
   }
   ```

3. **운동 완료 표시**:
   ```kotlin
   viewModelScope.launch {
       when (val result = exerciseRepository.updateExerciseCompletion(recommendationId, true)) {
           is Result.Success -> {
               // 완료 상태 UI 업데이트
           }
           is Result.Failure -> {
               // 오류 처리
           }
       }
   }
   ```

4. **운동 일정 예약**:
   ```kotlin
   viewModelScope.launch {
       val isoDateTimeString = "2025-03-25T14:00:00"
       when (val result = exerciseRepository.scheduleExercise(recommendationId, isoDateTimeString)) {
           is Result.Success -> {
               // 일정 추가 성공 메시지 표시
           }
           is Result.Failure -> {
               // 오류 처리
           }
       }
   }
   ```

## 인증 관련 주의사항

1. API 요청 전 유효한 토큰이 있는지 확인하고, 만료된 경우 사용자를 로그인 화면으로 리디렉션해야 합니다.
2. 토큰 관리를 위해 안전한 저장소(EncryptedSharedPreferences 또는 DataStore with security)를 사용해야 합니다.
3. 백그라운드 작업이나 앱 재시작 후에도 토큰이 유지되도록 설계해야 합니다.

## 기타 주의사항

1. 추천 결과는 5-10초 정도 시간이 소요될 수 있으므로 적절한 로딩 표시가 필요합니다.
2. 운동 추천을 하고 나서 사용자에게 무슨 일이 있어도 운동 스케쥴을 업로드 할 수 있게 합니다.
2. YouTube 링크 열기는 외부 앱 실행을 요구하므로 인텐트 처리 시 예외 상황에 대한 처리가 필요합니다.
3. 네트워크 오류 및 타임아웃에 대한 적절한 처리가 구현되어야 합니다.
4. 완료된 운동과 예약된 운동은 UI에서 시각적으로 구분되도록 디자인해야 합니다.
5. 앱 내 알림을 사용하여 예약된 운동 시간이 다가오면 사용자에게 알림을 제공하는 것이 좋습니다.

## 운동 추천 후 알림 설정 프로세스

사용자가 운동 추천을 받은 후 효과적인 운동 습관을 형성할 수 있도록 알림 설정 프로세스를 구현합니다. 이 기능은 사용자가 정기적으로 운동을 수행할 수 있도록 도와줍니다.

### 1. 운동 추천 결과 화면에 알림 설정 유도

운동 추천을 받은 후 표시되는 결과 화면에 알림 설정 섹션을 추가합니다.

### 2. 사용자 경험 개선을 위한 프로세스 흐름

1. **운동 추천 요청 및 결과 수신**
   - 사용자가 운동 추천을 요청
   - 서버가 개인화된 운동 계획 생성
   - 앱에서 운동 계획 표시

2. **알림 설정 유도**
   - 운동 계획 화면 하단에 알림 설정 카드 표시
   - "운동 습관을 형성하려면 정기적인 알림을 설정하세요" 메시지 표시
   - "알림 설정하기" 버튼 제공

3. **스케줄 설정 과정**
   - 사용자가 버튼 클릭 시 알림 설정 다이얼로그 표시
   - 운동 빈도에 따라 권장 요일 미리 선택됨 (예: 주 3회 → 월/수/금)
   - 사용자가 운동 시간과 알림 시간 조정 가능

4. **알림 승인 및 확인**
   - 스케줄 저장 시 성공 메시지 표시
   - 스케줄 목록 화면으로 이동하여 설정된 알림 확인 가능
   - 알림을 설정하지 않은 경우 나중에 설정할 수 있도록 스케줄 화면에서도 추가 버튼 제공

이 구현을 통해 사용자는 운동 추천을 받은 직후 쉽게 알림을 설정할 수 있으며, 운동 빈도에 따라 개인화된 요일 추천을 받아 효과적인 운동 루틴을 형성할 수 있습니다. 