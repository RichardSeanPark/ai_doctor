from fastapi import APIRouter, Depends, HTTPException, Body, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import json

from app.auth.auth_handler import get_current_user, UserInfo
from app.models.api_models import ApiResponse
from app.models.voice_models import VoiceQuery, VoiceResponse, QueryType
from app.agents.health_ai_app import HealthAIApplication
from app.utils.conversation_manager import ConversationManager
from app.utils.api_utils import handle_api_error  # 공통 에러 처리 함수 임포트

# 라우터 설정
router = APIRouter(prefix="/voice", tags=["voice"])

# 로깅 설정
logger = logging.getLogger(__name__)

# Health AI 어플리케이션 인스턴스
health_ai_app = HealthAIApplication()

# 대화 관리자 인스턴스
conversation_manager = ConversationManager()

@router.post("/query", response_model=ApiResponse)
async def process_voice_query(
    query: VoiceQuery,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    음성 쿼리를 처리합니다.
    
    음성 인식 결과를 분석하고 적절한 응답을 생성합니다.
    """
    async def _process_query():
        user_id = current_user.user_id
        logger.info(f"사용자 {user_id}로부터 음성 쿼리 수신: {query.query_text[:50]}...")
        
        # 세션 관리
        session_type = query.query_type.value if query.query_type else "general"
        if query.conversation_id:
            conversation_id = query.conversation_id
            logger.info(f"기존 대화 세션 사용: {conversation_id}")
        else:
            # 새 세션 생성 또는 활성 세션 가져오기
            session = conversation_manager.get_or_create_session(user_id, session_type)
            conversation_id = session['conversation_id']
            logger.info(f"대화 세션 생성/조회: {conversation_id}")
        
        # 사용자 메시지 기록
        conversation_manager.record_user_message(
            user_id=user_id,
            message_text=query.query_text,
            conversation_id=conversation_id
        )
        
        # 대화 컨텍스트 가져오기
        conversation_context = conversation_manager.get_context_for_llm(conversation_id)
        
        # 쿼리 유형에 따라 처리
        if query.query_type == QueryType.HEALTH:
            # 건강 쿼리 처리
            result = await health_ai_app.process_health_query(
                query_text=query.query_text,
                user_id=user_id,
                conversation_context=conversation_context
            )
        else:
            # 일반 음성 쿼리 처리
            result = await health_ai_app.process_voice_query(
                query_text=query.query_text,
                user_id=user_id,
                voice_data=query.voice_data or {},
                conversation_context=conversation_context
            )
        
        # 응답 형식 확인 및 변환
        if isinstance(result, str):
            response_data = VoiceResponse(
                response_text=result,
                conversation_id=conversation_id
            )
        elif isinstance(result, dict):
            # 기존 dict 응답 처리
            response_text = result.get('response_text', '') or result.get('text', '')
            response_data = VoiceResponse(
                response_text=response_text,
                requires_followup=result.get('requires_followup', False),
                followup_question=result.get('followup_question', ''),
                recommendations=result.get('recommendations', []),
                key_points=result.get('key_points', []),
                conversation_id=conversation_id
            )
        else:
            # 다른 형식의 응답 처리
            response_data = VoiceResponse(
                response_text=str(result),
                conversation_id=conversation_id
            )
        
        # 어시스턴트 메시지 기록
        if response_data.response_text:
            # 응답이 중요한지 여부 판단 (권장사항이나 후속 질문이 있으면 중요)
            is_important = bool(response_data.recommendations or response_data.followup_question)
            
            # 메시지 기록
            conversation_manager.record_assistant_message(
                user_id=user_id,
                message_text=response_data.response_text,
                conversation_id=conversation_id,
                is_important=is_important
            )
            
            # 일정 길이 이상의 대화가 있으면 요약 생성
            try:
                messages = conversation_manager.conversation_dao.get_messages(conversation_id)
                if len(messages) >= 5:  # 5개 이상의 메시지가 있으면 요약 생성
                    # generate_conversation_summary는 동기 메서드이므로 await 없이 호출
                    conversation_manager.generate_conversation_summary(conversation_id)
            except Exception as e:
                logger.error(f"대화 요약 생성 중 오류: {str(e)}")
        
        # 성공 응답 반환
        return ApiResponse(
            success=True,
            message="음성 쿼리 처리 완료",
            data=response_data.dict()
        )
    
    return await handle_api_error(
        _process_query,
        "음성 쿼리 처리",
        "음성 쿼리가 성공적으로 처리되었습니다"
    )

@router.post("/end-conversation", response_model=ApiResponse)
async def end_conversation(
    conversation_id: str = Body(..., embed=True),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    대화 세션을 종료합니다.
    """
    async def _end_conversation():
        user_id = current_user.user_id
        logger.info(f"사용자 {user_id}가 대화 세션 {conversation_id} 종료 요청")
        
        # 세션 정보 확인
        session = conversation_manager.conversation_dao.get_session_by_id(conversation_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대화 세션을 찾을 수 없습니다."
            )
            
        # 사용자 권한 확인
        if session['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 대화 세션에 대한 권한이 없습니다."
            )
        
        # 세션 종료 (비활성화)
        success = conversation_manager.conversation_dao.update_session_status(
            conversation_id=conversation_id,
            is_active=False
        )
        
        # 최종 요약 생성
        try:
            # generate_conversation_summary는 동기 메서드이므로 await 없이 호출
            conversation_manager.generate_conversation_summary(conversation_id)
            summary = conversation_manager.conversation_dao.get_latest_summary(conversation_id)
            summary_text = summary['summary_text'] if summary else "대화 요약이 생성되지 않았습니다."
        except Exception as e:
            logger.error(f"최종 요약 생성 중 오류: {str(e)}")
            summary_text = "대화 요약 생성 중 오류가 발생했습니다."
        
        # 성공 응답 반환
        return ApiResponse(
            success=success,
            message="대화 세션이 종료되었습니다.",
            data={
                "conversation_id": conversation_id,
                "summary": summary_text
            }
        )
    
    return await handle_api_error(
        _end_conversation,
        "대화 세션 종료",
        "대화 세션이 성공적으로 종료되었습니다"
    )

@router.get("/conversations", response_model=ApiResponse)
async def get_user_conversations(
    current_user: UserInfo = Depends(get_current_user),
    limit: int = 10,
    active_only: bool = True
):
    """
    사용자의 대화 세션 목록을 조회합니다.
    """
    async def _get_user_conversations():
        user_id = current_user.user_id
        logger.info(f"사용자 {user_id}의 대화 세션 목록 조회 요청")
        
        # 활성 세션 또는 모든 세션 조회
        sessions = conversation_manager.conversation_dao.get_active_sessions(user_id)
        
        # 각 세션에 대한 요약 정보 추가
        session_list = []
        for session in sessions:
            # 최신 요약 조회
            summary = conversation_manager.conversation_dao.get_latest_summary(session['conversation_id'])
            
            # 세션 정보 구성
            session_info = {
                "conversation_id": session['conversation_id'],
                "session_type": session['session_type'],
                "created_at": session['created_at'],
                "updated_at": session['updated_at'],
                "is_active": session['is_active'],
                "summary": summary['summary_text'] if summary else "요약 없음"
            }
            session_list.append(session_info)
        
        # 성공 응답 반환
        return ApiResponse(
            success=True,
            message=f"{len(session_list)}개의 대화 세션을 찾았습니다.",
            data={
                "conversations": session_list
            }
        )
    
    return await handle_api_error(
        _get_user_conversations,
        "대화 세션 목록 조회",
        "사용자의 대화 세션 목록을 성공적으로 조회했습니다"
    )

@router.get("/conversation/{conversation_id}", response_model=ApiResponse)
async def get_conversation_detail(
    conversation_id: str,
    current_user: UserInfo = Depends(get_current_user),
    message_limit: int = 50
):
    """
    특정 대화 세션의 상세 정보를 조회합니다.
    """
    async def _get_conversation_detail():
        user_id = current_user.user_id
        logger.info(f"사용자 {user_id}의 대화 세션 {conversation_id} 상세 조회 요청")
        
        # 세션 정보 확인
        session = conversation_manager.conversation_dao.get_session_by_id(conversation_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대화 세션을 찾을 수 없습니다."
            )
            
        # 사용자 권한 확인
        if session['user_id'] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 대화 세션에 대한 권한이 없습니다."
            )
        
        # 메시지 조회
        messages = conversation_manager.conversation_dao.get_messages(
            conversation_id=conversation_id,
            limit=message_limit
        )
        
        # 최신 요약 조회
        summary = conversation_manager.conversation_dao.get_latest_summary(conversation_id)
        
        # 응답 데이터 구성
        conversation_data = {
            "session": {
                "conversation_id": session['conversation_id'],
                "session_type": session['session_type'],
                "created_at": session['created_at'],
                "updated_at": session['updated_at'],
                "is_active": session['is_active']
            },
            "messages": messages,
            "summary": summary if summary else None,
            "message_count": len(messages)
        }
        
        # 성공 응답 반환
        return ApiResponse(
            success=True,
            message=f"대화 세션 {conversation_id}의 상세 정보를 조회했습니다.",
            data=conversation_data
        )
    
    return await handle_api_error(
        _get_conversation_detail,
        "대화 세션 상세 조회",
        "특정 대화 세션의 상세 정보를 성공적으로 조회했습니다"
    ) 