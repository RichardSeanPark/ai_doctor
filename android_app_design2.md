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

4. **운동 스케줄 생성**: 운동 일정을 생성하고 알림 설정
   - `POST /api/v1/exercise/schedule`

5. **사용자 스케줄 조회**: 사용자의 모든 운동 스케줄 조회
   - `GET /api/v1/exercise/schedules`

6. **운동 추천별 스케줄 조회**: 특정 운동 추천에 대한 모든 스케줄 조회
   - `GET /api/v1/exercise/recommendation/{recommendation_id}/schedules`

7. **스케줄 업데이트**: 기존 운동 스케줄 정보 수정
   - `PATCH /api/v1/exercise/schedule/{schedule_id}`

8. **스케줄 삭제**: 운동 스케줄 삭제
   - `DELETE /api/v1/exercise/schedule/{schedule_id}`

9. **운동 완료 기록**: 운동 완료 상태 기록
   - `POST /api/v1/exercise/completion`

10. **스케줄별 완료 기록 조회**: 특정 스케줄의 완료 기록 조회
    - `GET /api/v1/exercise/schedule/{schedule_id}/completions`

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

# 4. 운동 스케줄 생성 API

## 엔드포인트

- **URL**: `/api/v1/exercise/schedule`
- **Method**: POST
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 요청 파라미터

### 요청 본문

```json
{
  "recommendation_id": "운동 추천 ID (필수)",
  "day_of_week": 1,
  "time_of_day": "14:00",
  "duration_minutes": 30,
  "notification_enabled": true,
  "notification_minutes_before": 30
}
```

### 필수 파라미터

- **recommendation_id** (String): 운동 추천 ID
- **day_of_week** (Integer): 요일 (0=일요일, 1=월요일, ..., 6=토요일)
- **time_of_day** (String): 시간 (HH:MM 형식)

### 선택 파라미터

- **duration_minutes** (Integer): 운동 시간(분) (기본값: 30, 최소: 5, 최대: 180)
- **notification_enabled** (Boolean): 알림 활성화 여부 (기본값: true)
- **notification_minutes_before** (Integer): 알림을 보낼 시간(분) (기본값: 30, 최소: 5, 최대: 60)

## 응답 구조

```json
{
  "schedule_id": "스케줄 ID",
  "recommendation_id": "운동 추천 ID",
  "user_id": "사용자 ID",
  "day_of_week": 1,
  "time_of_day": "14:00",
  "duration_minutes": 30,
  "notification_enabled": true,
  "notification_minutes_before": 30,
  "is_active": true,
  "created_at": "생성 시간 (ISO 8601 형식)",
  "updated_at": "수정 시간 (ISO 8601 형식)"
}
```

# 5. 사용자 스케줄 조회 API

## 엔드포인트

- **URL**: `/api/v1/exercise/schedules`
- **Method**: GET
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 응답 구조

```json
[
  {
    "schedule_id": "스케줄 ID",
    "recommendation_id": "운동 추천 ID",
    "user_id": "사용자 ID",
    "day_of_week": 1,
    "time_of_day": "14:00",
    "duration_minutes": 30,
    "notification_enabled": true,
    "notification_minutes_before": 30,
    "is_active": true,
    "created_at": "생성 시간 (ISO 8601 형식)",
    "updated_at": "수정 시간 (ISO 8601 형식)"
  },
  // 추가 스케줄...
]
```

# 6. 운동 추천별 스케줄 조회 API

## 엔드포인트

- **URL**: `/api/v1/exercise/recommendation/{recommendation_id}/schedules`
- **Method**: GET
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

### 경로 파라미터

- **recommendation_id** (String, 필수): 조회할 운동 추천의 고유 ID

## 응답 구조

```json
[
  {
    "schedule_id": "스케줄 ID",
    "recommendation_id": "운동 추천 ID",
    "user_id": "사용자 ID",
    "day_of_week": 1,
    "time_of_day": "14:00",
    "duration_minutes": 30,
    "notification_enabled": true,
    "notification_minutes_before": 30,
    "is_active": true,
    "created_at": "생성 시간 (ISO 8601 형식)",
    "updated_at": "수정 시간 (ISO 8601 형식)"
  },
  // 추가 스케줄...
]
```

# 7. 스케줄 업데이트 API

## 엔드포인트

- **URL**: `/api/v1/exercise/schedule/{schedule_id}`
- **Method**: PATCH
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

### 경로 파라미터

- **schedule_id** (String, 필수): 업데이트할 스케줄의 고유 ID

### 요청 본문

```json
{
  "recommendation_id": "운동 추천 ID",
  "day_of_week": 2,
  "time_of_day": "16:00",
  "duration_minutes": 45,
  "notification_enabled": true,
  "notification_minutes_before": 15
}
```

모든 필드는 선택적이며, 변경하려는 필드만 포함시킬 수 있습니다.

## 응답 구조

```json
{
  "schedule_id": "스케줄 ID",
  "recommendation_id": "운동 추천 ID",
  "user_id": "사용자 ID",
  "day_of_week": 2,
  "time_of_day": "16:00",
  "duration_minutes": 45,
  "notification_enabled": true,
  "notification_minutes_before": 15,
  "is_active": true,
  "created_at": "생성 시간 (ISO 8601 형식)",
  "updated_at": "수정 시간 (ISO 8601 형식)"
}
```

# 8. 스케줄 삭제 API

## 엔드포인트

- **URL**: `/api/v1/exercise/schedule/{schedule_id}`
- **Method**: DELETE
- **Authorization**: Bearer Token (JWT)

### 경로 파라미터

- **schedule_id** (String, 필수): 삭제할 스케줄의 고유 ID

## 응답

- **상태 코드**: 204 No Content
- **응답 본문**: 없음

# 9. 운동 완료 기록 API

## 엔드포인트

- **URL**: `/api/v1/exercise/completion`
- **Method**: POST
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

## 요청 파라미터

### 요청 본문

```json
{
  "schedule_id": "스케줄 ID (필수)",
  "recommendation_id": "운동 추천 ID (필수)",
  "satisfaction_rating": 4,
  "feedback": "좋은 운동이었습니다"
}
```

### 필수 파라미터

- **schedule_id** (String): 완료한 운동 스케줄 ID
- **recommendation_id** (String): 관련 운동 추천 ID

### 선택 파라미터

- **satisfaction_rating** (Integer): 만족도 평가(1-5)
- **feedback** (String): 사용자 피드백

## 응답 구조

```json
{
  "completion_id": "완료 기록 ID",
  "schedule_id": "스케줄 ID",
  "recommendation_id": "운동 추천 ID",
  "user_id": "사용자 ID",
  "completed_at": "완료 시간 (ISO 8601 형식)",
  "satisfaction_rating": 4,
  "feedback": "좋은 운동이었습니다",
  "created_at": "생성 시간 (ISO 8601 형식)"
}
```

# 10. 스케줄별 완료 기록 조회 API

## 엔드포인트

- **URL**: `/api/v1/exercise/schedule/{schedule_id}/completions`
- **Method**: GET
- **Content-Type**: application/json
- **Authorization**: Bearer Token (JWT)

### 경로 파라미터

- **schedule_id** (String, 필수): 조회할 스케줄의 고유 ID

### 쿼리 파라미터

- **limit** (Integer, 선택): 반환할 최대 결과 수 (기본값: 10, 최소: 1, 최대: 50)

## 응답 구조

```json
[
  {
    "completion_id": "완료 기록 ID",
    "schedule_id": "스케줄 ID",
    "recommendation_id": "운동 추천 ID",
    "user_id": "사용자 ID",
    "completed_at": "완료 시간 (ISO 8601 형식)",
    "satisfaction_rating": 4,
    "feedback": "좋은 운동이었습니다",
    "created_at": "생성 시간 (ISO 8601 형식)"
  },
  // 추가 완료 기록...
]
```

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
    
    // 4. 운동 스케줄 생성
    @POST("api/v1/exercise/schedule")
    suspend fun createExerciseSchedule(
        @Body request: ExerciseScheduleCreateRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseScheduleResponse>
    
    // 5. 사용자 스케줄 조회
    @GET("api/v1/exercise/schedules")
    suspend fun getUserSchedules(
        @Header("Authorization") authToken: String
    ): Response<List<ExerciseScheduleResponse>>
    
    // 6. 운동 추천별 스케줄 조회
    @GET("api/v1/exercise/recommendation/{recommendationId}/schedules")
    suspend fun getRecommendationSchedules(
        @Path("recommendationId") recommendationId: String,
        @Header("Authorization") authToken: String
    ): Response<List<ExerciseScheduleResponse>>
    
    // 7. 스케줄 업데이트
    @PATCH("api/v1/exercise/schedule/{scheduleId}")
    suspend fun updateExerciseSchedule(
        @Path("scheduleId") scheduleId: String,
        @Body request: ExerciseScheduleCreateRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseScheduleResponse>
    
    // 8. 스케줄 삭제
    @DELETE("api/v1/exercise/schedule/{scheduleId}")
    suspend fun deleteExerciseSchedule(
        @Path("scheduleId") scheduleId: String,
        @Header("Authorization") authToken: String
    ): Response<Unit>
    
    // 9. 운동 완료 기록
    @POST("api/v1/exercise/completion")
    suspend fun recordExerciseCompletion(
        @Body request: ExerciseCompletionCreateRequest,
        @Header("Authorization") authToken: String
    ): Response<ExerciseCompletionResponse>
    
    // 10. 스케줄별 완료 기록 조회
    @GET("api/v1/exercise/schedule/{scheduleId}/completions")
    suspend fun getScheduleCompletions(
        @Path("scheduleId") scheduleId: String,
        @Query("limit") limit: Int = 10,
        @Header("Authorization") authToken: String
    ): Response<List<ExerciseCompletionResponse>>
}

// 요청 모델
data class ExerciseRecommendationRequest(
    val goal: String,
    val fitness_level: String? = null,
    val medical_conditions: List<String>? = null
)

data class ExerciseScheduleCreateRequest(
    val recommendation_id: String,
    val day_of_week: Int,  // 0=일요일, 1=월요일, ..., 6=토요일
    val time_of_day: String,  // HH:MM 형식
    val duration_minutes: Int = 30,
    val notification_enabled: Boolean = true,
    val notification_minutes_before: Int = 30
)

data class ExerciseCompletionCreateRequest(
    val schedule_id: String,
    val recommendation_id: String,
    val satisfaction_rating: Int? = null,
    val feedback: String? = null
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

data class ExerciseScheduleResponse(
    val schedule_id: String,
    val recommendation_id: String,
    val user_id: String,
    val day_of_week: Int,
    val time_of_day: String,
    val duration_minutes: Int,
    val notification_enabled: Boolean,
    val notification_minutes_before: Int,
    val is_active: Boolean,
    val created_at: String,
    val updated_at: String
)

data class ExerciseCompletionResponse(
    val completion_id: String,
    val schedule_id: String,
    val recommendation_id: String,
    val user_id: String,
    val completed_at: String,
    val satisfaction_rating: Int?,
    val feedback: String?,
    val created_at: String
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
    
    // 4. 운동 스케줄 생성
    suspend fun createExerciseSchedule(
        recommendationId: String, 
        dayOfWeek: Int, 
        timeOfDay: String,
        durationMinutes: Int = 30,
        notificationEnabled: Boolean = true,
        notificationMinutesBefore: Int = 30
    ): Result<ExerciseScheduleResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val request = ExerciseScheduleCreateRequest(
                recommendation_id = recommendationId,
                day_of_week = dayOfWeek,
                time_of_day = timeOfDay,
                duration_minutes = durationMinutes,
                notification_enabled = notificationEnabled,
                notification_minutes_before = notificationMinutesBefore
            )
            val response = exerciseApiService.createExerciseSchedule(request, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 스케줄 생성 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 5. 사용자 스케줄 조회
    suspend fun getUserSchedules(): Result<List<ExerciseScheduleResponse>> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val response = exerciseApiService.getUserSchedules(token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("사용자 스케줄 조회 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 6. 운동 추천별 스케줄 조회
    suspend fun getRecommendationSchedules(recommendationId: String): Result<List<ExerciseScheduleResponse>> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val response = exerciseApiService.getRecommendationSchedules(recommendationId, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 추천별 스케줄 조회 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 7. 스케줄 업데이트
    suspend fun updateExerciseSchedule(
        scheduleId: String,
        recommendationId: String, 
        dayOfWeek: Int, 
        timeOfDay: String,
        durationMinutes: Int = 30,
        notificationEnabled: Boolean = true,
        notificationMinutesBefore: Int = 30
    ): Result<ExerciseScheduleResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val request = ExerciseScheduleCreateRequest(
                recommendation_id = recommendationId,
                day_of_week = dayOfWeek,
                time_of_day = timeOfDay,
                duration_minutes = durationMinutes,
                notification_enabled = notificationEnabled,
                notification_minutes_before = notificationMinutesBefore
            )
            val response = exerciseApiService.updateExerciseSchedule(scheduleId, request, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("스케줄 업데이트 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 8. 스케줄 삭제
    suspend fun deleteExerciseSchedule(scheduleId: String): Result<Unit> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val response = exerciseApiService.deleteExerciseSchedule(scheduleId, token)
            
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("스케줄 삭제 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 9. 운동 완료 기록
    suspend fun recordExerciseCompletion(
        scheduleId: String,
        recommendationId: String,
        satisfactionRating: Int? = null,
        feedback: String? = null
    ): Result<ExerciseCompletionResponse> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val request = ExerciseCompletionCreateRequest(
                schedule_id = scheduleId,
                recommendation_id = recommendationId,
                satisfaction_rating = satisfactionRating,
                feedback = feedback
            )
            val response = exerciseApiService.recordExerciseCompletion(request, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("운동 완료 기록 실패: ${response.errorBody()?.string()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // 10. 스케줄별 완료 기록 조회
    suspend fun getScheduleCompletions(scheduleId: String, limit: Int = 10): Result<List<ExerciseCompletionResponse>> {
        return try {
            val token = "Bearer ${authManager.getAccessToken()}"
            val response = exerciseApiService.getScheduleCompletions(scheduleId, limit, token)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("스케줄별 완료 기록 조회 실패: ${response.errorBody()?.string()}"))
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

2. **운동 스케줄 생성**:
   ```kotlin
   viewModelScope.launch {
       when (val result = exerciseRepository.createExerciseSchedule(
           recommendationId = "12345",
           dayOfWeek = 1, // 월요일
           timeOfDay = "18:00",
           durationMinutes = 45
       )) {
           is Result.Success -> {
               val schedule = result.data
               // 스케줄 생성 성공 처리
           }
           is Result.Failure -> {
               // 오류 처리
           }
       }
   }
   ```

3. **운동 완료 기록**:
   ```kotlin
   viewModelScope.launch {
       when (val result = exerciseRepository.recordExerciseCompletion(
           scheduleId = "67890",
           recommendationId = "12345",
           satisfactionRating = 4,
           feedback = "오늘 운동은 정말 효과적이었습니다."
       )) {
           is Result.Success -> {
               // 완료 기록 성공 처리
           }
           is Result.Failure -> {
               // 오류 처리
           }
       }
   }
   ```

4. **사용자 스케줄 조회**:
   ```kotlin
   viewModelScope.launch {
       when (val result = exerciseRepository.getUserSchedules()) {
           is Result.Success -> {
               val schedules = result.data
               // 스케줄 목록 표시
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