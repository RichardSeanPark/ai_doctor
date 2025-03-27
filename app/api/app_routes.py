import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Optional

from app.models.app_data import AppVersionInfo
from app.db.app_dao import AppDAO
from app.models.response_models import ApiResponse
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()
app_dao = AppDAO()

@router.get("/version", response_model=ApiResponse)
async def get_app_version():
    """
    최신 앱 버전 정보를 조회합니다.
    클라이언트는 이 정보를 통해 업데이트 필요성을 판단할 수 있습니다.
    """
    try:
        version_info = app_dao.get_latest_version()
        
        if not version_info:
            # 버전 정보가 없는 경우, 기본 버전 정보 반환
            return ApiResponse(
                success=True,
                message="기본 앱 버전 정보",
                data={
                    "version_code": 1,
                    "version_name": "1.0.0",
                    "min_api_level": 21,
                    "force_update": False,
                    "change_log": None
                }
            )
        
        # 반환할 버전 정보
        version_data = {
            "version_code": version_info["version_code"],
            "version_name": version_info["version_name"],
            "min_api_level": version_info["min_api_level"],
            "force_update": version_info["force_update"],
            "change_log": version_info["change_log"]
        }
        
        return ApiResponse(
            success=True,
            message="앱 버전 정보 조회 성공",
            data=version_data
        )
    except Exception as e:
        logger.error(f"앱 버전 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"앱 버전 정보 조회 중 오류가 발생했습니다: {str(e)}"
        ) 