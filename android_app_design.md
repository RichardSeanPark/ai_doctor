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
- **의학적 상태 관리**: 사용자의 기존 질환 관리 (MedicalConditionRequest 모델과 medical-conditions API 엔드포인트 활용)

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
- **음식 이미지 분석**: 카메라를 통한 음식 이미지 촬영 및 자동 분석 (FoodImageData, FoodImageRecognitionResult, FoodNutritionAnalysis 모델 활용)
- **식단 계획**: 식단 계획 생성 및 관리 (DietPlan, Meal 모델 활용)

### 6. 알림 모듈
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

// 의학적 상태 추가 예시
suspend fun addMedicalCondition(condition: MedicalConditionRequest): Result<ApiResponse> {
    return apiService.addMedicalCondition(authManager.getToken(), condition)
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
   - 의학적 상태 및 식이 제한 관리
   - 식단 관리 기능
   - 약물 복용 알림
   - 대화 세션 기록 및 요약 기능

3. **고급 기능 (추후 구현)**
   - 음식 이미지 분석
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