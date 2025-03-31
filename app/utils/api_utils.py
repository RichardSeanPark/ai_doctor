"""
API 유틸리티 함수들을 제공하는 모듈
"""

import logging
from typing import Dict, Any, Optional, Callable, TypeVar
from fastapi import HTTPException
from app.models.api_models import ApiResponse

logger = logging.getLogger(__name__)

# 타입 변수 정의
T = TypeVar('T')

async def handle_api_error(func: Callable[..., T], log_prefix: str, success_message: str, *args, **kwargs) -> ApiResponse:
    """
    API 엔드포인트 함수의 에러를 일관되게 처리하는 유틸리티 함수
    
    Args:
        func: 실행할 함수
        log_prefix: 로그 메시지 접두사
        success_message: 성공 시 반환할 메시지
        args, kwargs: func에 전달할 인자들
        
    Returns:
        ApiResponse: 표준화된 API 응답
        
    Raises:
        HTTPException: FastAPI HTTP 예외는 그대로 전파되어 적절한 상태 코드 응답이 됩니다.
    """
    try:
        result = await func(*args, **kwargs)
        logger.info(f"{log_prefix} 완료")
        return ApiResponse(
            success=True,
            message=success_message,
            data=result
        )
    except HTTPException:
        # HTTP 예외는 그대로 전파하여 적절한 상태 코드가 반환되도록 함
        logger.error(f"{log_prefix} 중 HTTP 예외 발생")
        raise
    except Exception as e:
        error_msg = f"{log_prefix} 중 오류: {str(e)}"
        logger.error(error_msg)
        return ApiResponse(
            success=False,
            message=error_msg,
            data={"error": str(e)}
        ) 