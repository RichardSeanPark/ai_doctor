import unittest
from fastapi.testclient import TestClient
import sys
import os

# 루트 디렉토리 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.server import app

class TestPrivacyPolicyRoutes(unittest.TestCase):
    """개인정보 처리방침 페이지 라우트 테스트"""
    
    def setUp(self):
        """테스트 클라이언트 설정"""
        self.client = TestClient(app)
    
    def test_privacy_policy_page(self):
        """전체 개인정보 처리방침 페이지 테스트"""
        response = self.client.get("/privacy-policy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("개인정보 처리방침", response.text)
        self.assertIn("최종 업데이트", response.text)
        self.assertIn("개인정보 보호책임자", response.text)
    
    def test_privacy_policy_simple_page(self):
        """간소화된 개인정보 처리방침 페이지 테스트"""
        response = self.client.get("/privacy")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Google Play 스토어 등록정보", response.text)
        self.assertIn("개인 식별 요청 방법", response.text)
        self.assertIn("데이터 보관 기간", response.text)

if __name__ == "__main__":
    unittest.main() 