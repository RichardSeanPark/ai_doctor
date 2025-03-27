from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AppVersionInfo(BaseModel):
    """안드로이드 앱 버전 정보 모델"""
    version_code: int = Field(..., description="앱 버전 코드 (숫자)")
    version_name: str = Field(..., description="앱 버전 이름 (예: 1.0.0)")
    min_api_level: int = Field(21, description="최소 지원 안드로이드 API 레벨")
    force_update: bool = Field(False, description="강제 업데이트 여부")
    change_log: Optional[str] = Field(None, description="변경 사항 설명")
    
    class Config:
        schema_extra = {
            "example": {
                "version_code": 10,
                "version_name": "1.0.0",
                "min_api_level": 21,
                "force_update": False,
                "change_log": "- 버그 수정\n- 성능 개선"
            }
        } 