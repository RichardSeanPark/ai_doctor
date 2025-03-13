"""
API 응답에 사용되는 공통 모델 정의
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union

class ApiResponse(BaseModel):
    """
    모든 API 응답에 사용되는 표준 응답 모델
    
    Attributes:
        success (bool): API 호출 성공 여부
        message (str): 응답 메시지
        data (Dict[str, Any]): 응답 데이터 (성공 시 결과, 실패 시 오류 정보)
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorDetail(BaseModel):
    """
    오류 상세 정보 모델
    
    Attributes:
        code (str): 오류 코드
        message (str): 오류 메시지
        field (Optional[str]): 오류가 발생한 필드명 (유효성 검사 오류 시)
    """
    code: str
    message: str
    field: Optional[str] = None

class PaginatedResponse(BaseModel):
    """
    페이징된 응답 결과를 위한 모델
    
    Attributes:
        total (int): 전체 항목 수
        page (int): 현재 페이지 번호
        per_page (int): 페이지당 항목 수
        items (List[Any]): 현재 페이지의 항목들
    """
    total: int
    page: int
    per_page: int
    items: List[Any] 