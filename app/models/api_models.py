"""
API 모델 정의 모듈
표준화된 API 응답 모델과 관련 모델들을 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union, List

class ApiResponse(BaseModel):
    """
    모든 API 엔드포인트에서 일관된 응답 형식을 위한 표준 응답 모델
    """
    success: bool = Field(..., description="API 요청 성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "작업이 성공적으로 완료되었습니다",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "예시 데이터"
                }
            }
        } 