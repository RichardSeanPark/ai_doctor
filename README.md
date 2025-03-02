# 건강 관리 AI 에이전트

이 프로젝트는 LangGraph와 PydanticAI를 사용하여 건강 관리를 도와주는 AI 에이전트 시스템입니다. 식단 분석, 건강 지표 모니터링, 증상 분석, 음성 상담, 안드로이드 알림 등의 기능을 제공합니다.

## 주요 기능

- **식단 분석**: 사용자의 식단을 분석하고 영양학적 개선점을 제안
- **건강 지표 모니터링**: 걸음 수, 수면 시간, 심박수 등 건강 지표 분석
- **증상 분석**: 사용자가 보고한 증상을 분석하고 조언 제공
- **음성 상담**: 음성으로 받은 건강 관련 질문에 답변
- **동기부여 알림**: 건강 상태에 따른 맞춤형 동기부여 메시지 전송

## 시스템 요구사항

- Python 3.11 이상
- Anaconda 환경 (권장)
- Google API 키 (Gemini 모델 사용)

## 설치 방법

1. 저장소 클론:
```bash
git clone <repository-url>
cd health-ai-agent
```

2. 환경 설정 (Anaconda 사용):
```bash
conda activate doctor  # 기존 doctor 환경 사용
pip install -r requirements.txt
```

3. 환경 변수 설정:
   `.env` 파일에 Google API 키를 설정:
```
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-1.5-pro
```

## 사용 방법

1. 애플리케이션 실행:
```bash
python run.py
```

2. 테스트 시나리오:
   `run.py` 파일에는 다음과 같은 테스트 시나리오가 포함되어 있습니다:
   - 식단 분석 테스트
   - 건강 지표 확인 테스트
   - 음성 질의 테스트
   - 건강 상담 테스트
   - 동기부여 알림 테스트

## 프로젝트 구조

```
health-ai-agent/
├── .env                  # 환경 변수 파일
├── requirements.txt      # 의존성 정의
├── run.py                # 애플리케이션 실행 파일
└── app/
    ├── main.py           # 메인 애플리케이션 클래스
    ├── agents/           # 에이전트 정의
    ├── models/           # 데이터 모델 정의
    ├── nodes/            # LangGraph 노드
    └── graphs/           # LangGraph 그래프
```

## 커스터마이징

- 식단 분석 로직: `app/nodes/diet_analysis_nodes.py`
- 건강 지표 분석: `app/nodes/health_check_nodes.py`
- 증상 분석: `app/nodes/symptom_analysis_nodes.py`
- 음성 상담: `app/nodes/voice_consultation_nodes.py`
- 알림 시스템: `app/nodes/android_notification_nodes.py`

각 파일에서 해당 기능의 로직을 수정하여 시스템을 커스터마이징할 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 