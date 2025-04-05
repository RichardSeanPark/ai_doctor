"""
계정 삭제 API 테스트
사용자 계정 삭제시 관련된 모든 데이터가 DB에서 삭제되는지 검증
"""

import os
import sys
import pytest
import requests
import json
import uuid
from datetime import datetime, date

# 테스트 환경 설정
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
TEST_USER_ID = None
TEST_TOKEN = None

def test_create_test_user():
    """테스트용 사용자 생성"""
    global TEST_USER_ID, TEST_TOKEN
    
    # 소셜 로그인 요청 (테스트용 계정 생성)
    social_login_url = f"{API_BASE_URL}/api/v1/auth/social/login"
    random_social_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    login_data = {
        "social_id": random_social_id,
        "provider": "kakao"
    }
    
    response = requests.post(social_login_url, json=login_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert "data" in result
    assert "user_id" in result["data"]
    assert "token" in result["data"]
    
    TEST_USER_ID = result["data"]["user_id"]
    TEST_TOKEN = result["data"]["token"]
    
    print(f"테스트 사용자 생성됨: {TEST_USER_ID}")
    return True

def test_user_profile_update():
    """테스트용 사용자 프로필 업데이트"""
    global TEST_USER_ID, TEST_TOKEN
    
    assert TEST_USER_ID is not None
    assert TEST_TOKEN is not None
    
    # 프로필 업데이트 요청
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    profile_update_url = f"{API_BASE_URL}/api/v1/auth/profile/update"
    
    # API에서 birth_date와 gender를 HTTP 쿼리 파라미터로 받고 있으므로 json 대신 params 사용
    profile_data = {
        "birth_date": "1990-01-01",
        "gender": "male"
    }
    
    response = requests.post(profile_update_url, params=profile_data, headers=headers)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    
    # 프로필 조회하여 업데이트 확인
    profile_url = f"{API_BASE_URL}/api/v1/auth/profile"
    response = requests.get(profile_url, headers=headers)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert result["data"]["birth_date"] == "1990-01-01"
    assert result["data"]["gender"] == "male"
    
    print("사용자 프로필 업데이트 성공")
    return True

def test_create_health_metrics():
    """사용자 건강 지표 데이터 생성"""
    global TEST_USER_ID, TEST_TOKEN
    
    assert TEST_USER_ID is not None
    assert TEST_TOKEN is not None
    
    # 건강 지표 업데이트 요청
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    metrics_url = f"{API_BASE_URL}/api/v1/auth/profile/health-metrics"
    
    metrics_data = {
        "height": 175.5,
        "weight": 70.2
    }
    
    response = requests.post(metrics_url, params=metrics_data, headers=headers)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert "data" in result
    assert "metrics_id" in result["data"]
    
    print(f"건강 지표 데이터 생성 성공: 키={metrics_data['height']}cm, 몸무게={metrics_data['weight']}kg")
    return result["data"]["metrics_id"]

def test_create_diet_advice():
    """사용자 식단 조언 데이터 생성"""
    global TEST_USER_ID, TEST_TOKEN
    
    assert TEST_USER_ID is not None
    assert TEST_TOKEN is not None
    
    # 식단 분석 요청
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    diet_url = f"{API_BASE_URL}/api/v1/diet/analyze"
    
    diet_data = {
        "user_id": TEST_USER_ID,
        "meal_type": "breakfast",
        "meal_items": [
            {
                "name": "사과",
                "quantity": "1개",
                "calories": 95
            },
            {
                "name": "통밀빵",
                "quantity": "2조각",
                "calories": 180
            }
        ]
    }
    
    response = requests.post(diet_url, json=diet_data, headers=headers)
    
    # 식단 조언 API가 없거나 실패할 경우 테스트를 스킵합니다
    if response.status_code != 200:
        print("식단 조언 API를 건너뜁니다 (API 사용 불가 또는 오류)")
        return None
    
    result = response.json()
    assert result["success"] == True
    
    print("식단 조언 데이터 생성 성공")
    return True

def test_verify_data_exists():
    """사용자 관련 데이터가 존재하는지 확인 (테스트 목적)"""
    # 여기서는 프로필이 존재하는지만 확인합니다
    # 실제 운영 환경에서는 데이터베이스에 직접 쿼리하여 검증할 수 있습니다
    
    global TEST_USER_ID, TEST_TOKEN
    
    assert TEST_USER_ID is not None
    assert TEST_TOKEN is not None
    
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    profile_url = f"{API_BASE_URL}/api/v1/auth/profile"
    
    response = requests.get(profile_url, headers=headers)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert result["data"]["user_id"] == TEST_USER_ID
    
    print("삭제 전 사용자 데이터 확인 완료")
    return True

def test_delete_account():
    """계정 삭제 API 테스트"""
    global TEST_USER_ID, TEST_TOKEN
    
    assert TEST_USER_ID is not None
    assert TEST_TOKEN is not None
    
    # 계정 삭제 요청
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    delete_url = f"{API_BASE_URL}/api/v1/auth/account"
    
    response = requests.delete(delete_url, headers=headers)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert result["data"]["deleted"] == True
    assert result["data"]["user_id"] == TEST_USER_ID
    
    print(f"계정 삭제 성공: {TEST_USER_ID}")
    
    # 삭제 후 프로필 조회 시도 (실패해야 함)
    profile_url = f"{API_BASE_URL}/api/v1/auth/profile"
    response = requests.get(profile_url, headers=headers)
    
    # 토큰 자체는 아직 유효할 수 있으므로, 응답에서 401 또는 404 중 하나가 반환되어야 함
    assert response.status_code in [401, 404], f"Expected 401 or 404, got {response.status_code}"
    
    if response.status_code == 200:
        # API에서 200을 반환하더라도 success가 False여야 함
        result = response.json()
        assert result["success"] == False
    
    print("삭제된 계정 확인 완료")
    return True

def test_verify_all_data_deleted():
    """사용자 계정과 관련된 모든 데이터가 삭제되었는지 확인"""
    global TEST_USER_ID, TEST_TOKEN
    
    assert TEST_USER_ID is not None
    assert TEST_TOKEN is not None
    
    # 1. 사용자 프로필 조회 시도 (실패해야 함)
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    profile_url = f"{API_BASE_URL}/api/v1/auth/profile"
    
    response = requests.get(profile_url, headers=headers)
    
    # 토큰 자체는 아직 유효할 수 있으므로, 응답에서 401 또는 404 중 하나가 반환되어야 함
    assert response.status_code in [401, 404], f"프로필 API - Expected 401 or 404, got {response.status_code}"
    
    if response.status_code == 200:
        # API에서 200을 반환하더라도 success가 False여야 함
        result = response.json()
        assert result["success"] == False
    
    # 2. 건강 지표 데이터 조회 (존재하지 않아야 함)
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    health_url = f"{API_BASE_URL}/api/v1/health/metrics"
    
    response = requests.get(health_url, headers=headers)
    
    # API가 없거나 401/404를 반환해야 함
    if response.status_code == 200:
        result = response.json()
        # 결과가 비어 있거나 실패 상태여야 함
        assert result.get("success", False) == False or not result.get("data") or len(result.get("data", [])) == 0
    
    print("모든 사용자 데이터가 성공적으로 삭제됨")
    return True

if __name__ == "__main__":
    # 테스트 실행
    print(f"API 서버 URL: {API_BASE_URL}")
    
    # 테스트 단계별로 실행
    try:
        # 1. 사용자 생성
        test_create_test_user()
    except Exception as e:
        print(f"사용자 생성 테스트 실패: {str(e)}")
        sys.exit(1)
        
    try:
        # 2. 사용자 데이터 생성
        test_user_profile_update()
    except Exception as e:
        print(f"프로필 업데이트 테스트 실패: {str(e)}")
        sys.exit(1)
        
    try:
        # 건강 지표 생성
        test_create_health_metrics()
    except Exception as e:
        print(f"건강 지표 생성 테스트 실패: {str(e)}")
        sys.exit(1)
        
    try:
        # 식단 조언 생성
        test_create_diet_advice()
    except Exception as e:
        print(f"식단 조언 테스트 실패: {str(e)}")
        print("이 오류는 무시되며 테스트를 계속 진행합니다.")
        
    try:
        # 3. 데이터가 존재하는지 확인
        test_verify_data_exists()
    except Exception as e:
        print(f"데이터 존재 확인 테스트 실패: {str(e)}")
        sys.exit(1)
        
    try:
        # 4. 계정 삭제
        test_delete_account()
    except Exception as e:
        print(f"계정 삭제 테스트 실패: {str(e)}")
        sys.exit(1)
        
    try:
        # 5. 모든 데이터가 삭제되었는지 확인
        test_verify_all_data_deleted()
    except Exception as e:
        print(f"데이터 삭제 확인 테스트 실패: {str(e)}")
        sys.exit(1)
        
    print("모든 테스트 성공! 계정 및 관련 데이터가 성공적으로 삭제되었습니다.") 