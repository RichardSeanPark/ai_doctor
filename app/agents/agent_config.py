import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# 환경 변수 로드
load_dotenv()

# Google API 키 가져오기
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

# Gemini 모델 이름 가져오기
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

def get_gemini_agent():
    """
    Gemini Pro 모델을 사용하는 간단한 체인을 생성합니다.
    """
    # Gemini Pro 모델 설정
    gemini_pro = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        top_p=0.8,
        convert_system_message_to_human=True
    )
    
    # 프롬프트 템플릿 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 건강 관리 AI 주치의입니다."),
        ("human", "{input}")
    ])
    
    # 체인 생성
    chain = prompt | gemini_pro
    
    return chain

def get_health_agent():
    """
    건강 관련 상담을 위한 특화된 체인을 생성합니다.
    """
    # 건강 관련 프롬프트 지정
    health_system_prompt = """
    당신은 건강 관리 AI 주치의입니다. 사용자의 건강 데이터를 분석하고, 
    건강한 생활 습관과 영양 섭취에 대한 과학적 근거 기반의 조언을 제공합니다.
    
    항상 의학적으로 정확한 정보를 제공하되, 의사의 전문적인 진단을 대체하지 않는다는 점을 명시하세요.
    심각한 건강 문제가 의심될 경우 즉시 의사와 상담할 것을 권고하세요.
    
    사용자에게 친절하고 명확하게 대화하세요. 전문 용어를 사용할 때는 쉬운 설명을 함께 제공하세요.
    """
    
    # Gemini Pro 모델 설정 (건강 상담용 파라미터 조정)
    gemini_health = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,  # 더 정확한 응답을 위해 온도 낮춤
        top_p=0.95,
        convert_system_message_to_human=True
    )
    
    # 프롬프트 템플릿 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", health_system_prompt),
        ("human", "{input}")
    ])
    
    # 체인 생성
    chain = prompt | gemini_health
    
    return chain

def get_diet_agent():
    """
    다이어트 관리를 위한 특화된 체인을 생성합니다.
    """
    # 다이어트 관련 프롬프트 지정
    diet_system_prompt = """
    당신은 다이어트 및 영양 관리 AI 주치의입니다. 사용자의 식단을 분석하고, 
    영양 균형과 칼로리 관리에 대한 과학적 근거 기반의 조언을 제공합니다.
    
    다음 지침을 따르세요:
    1. 사용자의 건강 목표와 식이 제한을 고려하여 맞춤형 조언을 제공하세요.
    2. 영양소 균형을 강조하고, 건강한 식습관을 장려하세요.
    3. 급격한 다이어트보다 지속 가능한 식습관 개선을 권장하세요.
    4. 단순히 칼로리만 제한하는 것이 아닌 영양가 있는 식품 선택을 강조하세요.
    
    사용자에게 친절하고 격려하는 태도로 대화하세요.
    """
    
    # Gemini Pro 모델 설정 (다이어트 상담용 파라미터)
    gemini_diet = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        top_p=0.9,
        convert_system_message_to_human=True
    )
    
    # 프롬프트 템플릿 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", diet_system_prompt),
        ("human", "{input}")
    ])
    
    # 체인 생성
    chain = prompt | gemini_diet
    
    return chain

def get_voice_agent():
    """
    음성 상담을 위한 특화된 체인을 생성합니다.
    """
    # 음성 상담 관련 프롬프트 지정
    voice_system_prompt = """
    당신은 건강 관리 AI 주치의의 음성 비서입니다. 사용자의 음성 질의에 대해
    명확하고 자연스러운 응답을 제공합니다.
    
    다음 지침을 따르세요:
    1. 간결하고 명확하게 대답하세요. 음성으로 전달되므로 너무 길지 않게 유지하세요.
    2. 의학적으로 정확한 정보를 제공하되, 전문 용어는 쉽게 설명하세요.
    3. 사용자가 추가 질문을 할 수 있도록 대화를 열어두세요.
    4. 심각한 건강 문제에 대해서는 의사 상담을 권고하세요.
    
    사용자에게 친절하고 도움이 되는 태도로 대화하세요.
    """
    
    # Gemini Pro 모델 설정 (음성 상담용 파라미터)
    gemini_voice = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        top_p=0.9,
        convert_system_message_to_human=True
    )
    
    # 프롬프트 템플릿 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", voice_system_prompt),
        ("human", "{input}")
    ])
    
    # 체인 생성
    chain = prompt | gemini_voice
    
    return chain

def get_notification_agent():
    """
    알림 생성을 위한 특화된 체인을 생성합니다.
    """
    # 알림 관련 프롬프트 지정
    notification_system_prompt = """
    당신은 건강 관리 AI 주치의의 알림 시스템입니다. 사용자에게 전달할
    알림 메시지를 생성합니다.
    
    다음 지침을 따르세요:
    1. 간결하고 명확한 알림 메시지를 작성하세요.
    2. 사용자의 건강 목표와 진행 상황을 고려하여 맞춤형 메시지를 제공하세요.
    3. 동기부여가 되는 긍정적인 메시지를 작성하세요.
    4. 중요한 건강 알림의 경우 명확한 행동 지침을 포함하세요.
    
    사용자에게 도움이 되고 행동을 유도하는 알림을 작성하세요.
    """
    
    # Gemini Pro 모델 설정 (알림 생성용 파라미터)
    gemini_notification = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.4,
        top_p=0.9,
        convert_system_message_to_human=True
    )
    
    # 프롬프트 템플릿 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", notification_system_prompt),
        ("human", "{input}")
    ])
    
    # 체인 생성
    chain = prompt | gemini_notification
    
    return chain 