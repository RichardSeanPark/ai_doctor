# 건강 AI 안드로이드 앱 설계 문서

## 개요
이 문서는 건강 AI API 서버와 연동하여 작동하는 안드로이드 앱의 설계 가이드를 제공합니다. 서버 API 구조를 기반으로 최적의 앱 구조와 기능을 정의합니다.

## 앱 아키텍처

안드로이드 앱은 현대적인 아키텍처 패턴을 따릅니다:
- **MVVM (Model-View-ViewModel)** 패턴 사용
- **Clean Architecture** 원칙 적용
- **Jetpack Components** 활용 (ViewModel, LiveData, Room, Navigation)
- **Kotlin Coroutines** 및 **Flow**를 사용한 비동기 처리
- **Dagger Hilt** 또는 **Koin**을 통한 의존성 주입

## 주요 모듈

### 1. 인증 모듈
- **로그인 화면**: 사용자명과 비밀번호 입력
- **회원가입 화면**: 사용자 기본 정보 및 건강 정보 입력
- **인증 관리**: 토큰 관리 및 자동 로그인 기능
- **프로필 관리**: 사용자 정보 조회 및 수정

### 2. 건강 대시보드 모듈
- **메인 대시보드**: 핵심 건강 지표 및 최근 분석 요약 표시
- **건강 지표 입력**: 체중, 혈압, 심박수 등 건강 지표 입력 폼
- **건강 차트**: 시간에 따른 건강 지표 변화 그래프
- **건강 상태 요약**: 현재 건강 상태 및 주의사항 표시

### 3. 건강 데이터 관리 모듈
- **의학적 상태 관리**: 사용자의 기존 질환 관리
- **약물 복용 관리**: 복용 중인 약물 등록 및 리마인더
- **식이 제한 관리**: 알레르기 등 식이 제한 사항 관리
- **목표 설정**: 건강 목표 설정 및 진행 상황 추적

### 4. 음성 인터페이스 모듈
- **음성 비서 화면**: 마이크 아이콘과 음성 입력 UI
- **음성 응답 표시**: 음성 텍스트와 함께 시각적 피드백 제공
- **음성 상담 기록**: 이전 음성 상담 내용 저장 및 조회
- **음성 타입 선택**: 일반 질문 또는 건강 상담 모드 선택

### 5. 식단 관리 모듈
- **식단 입력**: 식사 종류 및 음식 항목 입력
- **식단 분석**: 입력된 식단의 영양소 분석 결과 표시
- **식단 기록**: 이전 식단 기록 저장 및 조회
- **음식 이미지 분석**: 카메라를 통한 음식 이미지 촬영 및 자동 분석

### 6. 알림 모듈
- **알림 설정**: 알림 시간, 유형 등 설정
- **알림 이력**: 받은 알림 이력 표시
- **FCM 연동**: Firebase Cloud Messaging을 통한 푸시 알림 수신

## 데이터 흐름 및 상태 관리

### 1. 인증 흐름
1. 사용자 로그인 → 서버에서 토큰 발급 → 로컬 저장
2. 토큰 만료 시 자동 갱신 또는 재로그인 요청
3. 로그아웃 시 토큰 폐기 및 로컬 데이터 삭제

### 2. 건강 데이터 흐름
1. 로컬 캐싱과 서버 동기화 전략 사용
2. 오프라인 모드 지원: 연결 없이 데이터 입력 가능, 연결 시 자동 동기화
3. 건강 지표 변화에 따른 실시간 분석 및 알림

### 3. 음성 처리 흐름
1. 음성 입력 → 텍스트 변환 → 서버 전송 → 응답 수신 → 화면 표시/음성 출력
2. 대화 세션 상태 관리: 이전 대화 맥락 유지

## API 연동

### 인증 API 연동
```kotlin
// 로그인 예시
suspend fun login(username: String, password: String): Result<TokenResponse> {
    return apiService.login(UserLoginRequest(username, password))
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
```

### 음성 쿼리 API 연동
```kotlin
// 음성 쿼리 처리 예시
suspend fun processVoiceQuery(query: String, type: String): Result<VoiceResponse> {
    return apiService.processVoiceQuery(
        VoiceQueryRequest(
            userManager.getUserId(),
            query,
            sessionManager.getCurrentSessionId(),
            type
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

### 3. 상호작용 패턴
- **음성과 터치의 병행**: 모든 음성 기능은 터치로도 접근 가능
- **컨텍스트 인식**: 사용자 상황에 맞는 UI 요소 제공
- **점진적 공개**: 복잡한 기능은 필요에 따라 단계적으로 노출

## 기술 스택 권장사항

### 데이터 저장
- **Room**: 로컬 데이터베이스
- **DataStore**: 사용자 설정 및 토큰 저장
- **WorkManager**: 백그라운드 동기화 작업

### 분석 및 모니터링
- **Firebase Analytics**: 사용자 행동 분석
- **Firebase Crashlytics**: 오류 보고
- **Performance Monitoring**: 앱 성능 모니터링

## 구현 우선순위

1. **필수 구현 사항**
   - 사용자 인증 시스템
   - 기본 건강 지표 입력 및 조회
   - 음성 인터페이스 기본 기능
   - 건강 분석 요청 및 결과 표시

2. **2차 구현 사항**
   - 상세 건강 차트 및 분석
   - 식단 관리 기능
   - 약물 복용 알림
   - 오프라인 모드 지원

3. **고급 기능 (추후 구현)**
   - 음식 이미지 분석
   - 건강 목표에 따른 맞춤형 조언
   - 다른 건강 기기와 연동
   - 고급 음성 상담 기능

## 보안 고려사항

- **토큰 관리**: 안전한 저장 및 갱신
- **민감 정보 보호**: 건강 데이터 암호화
- **네트워크 보안**: HTTPS 통신, 인증서 피닝
- **접근 제어**: 바이오메트릭 인증 옵션 제공

## 결론

이 설계 문서는 현재 API 서버 구조에 최적화된 안드로이드 앱의 구현 가이드를 제공합니다. 추가적인 서버 기능이 개발됨에 따라 앱 설계도 점진적으로 확장할 수 있습니다. 모든 구현은 사용자 중심 설계를 바탕으로 직관적인 인터페이스와 안정적인 성능을 제공하는 것을 목표로 합니다. 