from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from app.db.user_dao import UserDAO

security = HTTPBearer()
user_dao = UserDAO()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """사용자 인증 및 정보 반환"""
    token = credentials.credentials
    
    # 세션 유효성 검사
    user_id = user_dao.validate_session(token)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 인증 정보"
        )
    
    # 사용자 정보 조회
    user = user_dao.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return user 