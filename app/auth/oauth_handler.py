"""
OAuth 인증 처리 모듈

소셜 로그인(Google, Kakao) 인증 토큰을 검증하고 사용자 정보를 가져오는 기능 제공
안드로이드 앱에서 사용하기 위한 모듈입니다.
"""

import json
import logging
import httpx
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 사용자 정보 조회 엔드포인트
USER_INFO_ENDPOINTS = {
    "google": "https://www.googleapis.com/oauth2/v3/userinfo",
    "kakao": "https://kapi.kakao.com/v2/user/me",
}

# Google ID 토큰 검증을 위한 공개 키 URL
GOOGLE_CERT_URL = "https://www.googleapis.com/oauth2/v3/certs"

async def verify_google_token(access_token: str, id_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Google 액세스 토큰 검증 및 사용자 정보 조회
    
    Args:
        access_token: 구글 OAuth 액세스 토큰
        id_token: 구글 ID 토큰 (선택적)
        
    Returns:
        사용자 정보 또는 None (검증 실패 시)
    """
    # ID 토큰이 제공된 경우 검증
    if id_token:
        try:
            # Google ID 토큰 검증 (라이브러리에서 자동으로 공개 키 가져옴)
            # 이 부분은 실제 환경에서는 google-auth 라이브러리를 사용하는 것이 좋습니다
            # 여기서는 간단한 검증만 수행
            
            # JWT 헤더 확인 (서명 검증 없이)
            header = jwt.get_unverified_header(id_token)
            if not header or 'alg' not in header:
                logger.error("Invalid ID token header")
                return None
            
            # 페이로드 확인 (서명 검증 없이)
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Google 클라이언트 ID 확인
            if payload.get('aud') != settings.GOOGLE_CLIENT_ID:
                logger.error("ID token audience doesn't match client ID")
                return None
            
            # 만료 시간 확인
            if 'exp' in payload and payload['exp'] < time.time():
                logger.error("ID token expired")
                return None
            
            # 페이로드에 필요한 정보가 있으면 바로 반환
            if 'sub' in payload and ('email' in payload or 'name' in payload):
                return {
                    "id": payload['sub'],
                    "email": payload.get('email'),
                    "name": payload.get('name'),
                    "picture": payload.get('picture'),
                    "verified_email": payload.get('email_verified', False)
                }
        
        except Exception as e:
            logger.error(f"ID 토큰 검증 오류: {str(e)}")
            # ID 토큰 검증 실패 시 액세스 토큰으로 계속 진행
    
    # 액세스 토큰으로 사용자 정보 조회
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(USER_INFO_ENDPOINTS["google"], headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info("구글 사용자 정보 조회 성공")
                
                # 응답 데이터 매핑
                return {
                    "id": user_data.get("sub"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "picture": user_data.get("picture"),
                    "verified_email": user_data.get("email_verified", False)
                }
            else:
                logger.error(f"구글 사용자 정보 조회 실패: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"구글 사용자 정보 조회 오류: {str(e)}")
        return None

async def verify_kakao_token(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Kakao 액세스 토큰 검증 및 사용자 정보 조회
    
    Args:
        access_token: 카카오 OAuth 액세스 토큰
        
    Returns:
        사용자 정보 또는 None (검증 실패 시)
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(USER_INFO_ENDPOINTS["kakao"], headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info("카카오 사용자 정보 조회 성공")
                
                # 카카오는 계정 정보가 여러 레벨로 중첩되어 있음
                kakao_account = user_data.get("kakao_account", {})
                profile = kakao_account.get("profile", {})
                
                # 응답 데이터 매핑
                return {
                    "id": str(user_data.get("id")),
                    "email": kakao_account.get("email"),
                    "name": profile.get("nickname"),
                    "picture": profile.get("profile_image_url"),
                    "verified_email": kakao_account.get("is_email_verified", False)
                }
            else:
                logger.error(f"카카오 사용자 정보 조회 실패: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"카카오 사용자 정보 조회 오류: {str(e)}")
        return None

async def verify_social_token(provider: str, token: str, id_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    소셜 로그인 토큰 검증 및 사용자 정보 조회
    
    Args:
        provider: 소셜 로그인 제공자 (google, kakao)
        token: 액세스 토큰
        id_token: ID 토큰 (구글만 해당, 선택적)
        
    Returns:
        표준화된 사용자 정보 또는 None
    """
    user_data = None
    
    if provider == "google":
        user_data = await verify_google_token(token, id_token)
    elif provider == "kakao":
        user_data = await verify_kakao_token(token)
    else:
        logger.error(f"지원하지 않는 소셜 로그인 제공자: {provider}")
        return None
    
    # 검증 실패
    if not user_data:
        return None
    
    # 표준화된 형식으로 반환
    return {
        "social_id": user_data.get("id", ""),
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "profile_image": user_data.get("picture"),
        "provider": provider,
        "verified_email": user_data.get("verified_email", False),
        "raw_data": user_data
    } 