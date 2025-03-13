import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from app.db.conversation_dao import ConversationDAO
from app.db.health_dao import HealthDAO
from app.db.user_dao import UserDAO
from app.agents.agent_config import (
    get_conversation_summary_agent,
    get_health_entity_extraction_agent,
    get_key_points_extraction_agent
)

logger = logging.getLogger(__name__)

class ConversationManager:
    """대화 관리 유틸리티 클래스"""
    
    def __init__(self):
        """ConversationManager 초기화"""
        self.conversation_dao = ConversationDAO()
        self.health_dao = HealthDAO()
        self.user_dao = UserDAO()
        
        # LLM 에이전트 초기화
        self.summary_agent = get_conversation_summary_agent()
        self.entity_agent = get_health_entity_extraction_agent()
        self.key_points_agent = get_key_points_extraction_agent()
    
    def get_or_create_session(self, user_id: str, session_type: str = "general") -> Dict[str, Any]:
        """
        사용자의 활성 세션을 가져오거나 새로 생성합니다.
        
        Args:
            user_id: 사용자 ID
            session_type: 세션 유형
            
        Returns:
            세션 정보
        """
        # 최근 활성 세션 검색
        session = self.conversation_dao.get_latest_session(user_id, session_type)
        
        # 없으면 새로 생성
        if not session:
            conversation_id = self.conversation_dao.create_conversation_session(user_id, session_type)
            session = self.conversation_dao.get_session_by_id(conversation_id)
            
        return session
    
    def record_user_message(self, user_id: str, message_text: str, 
                          conversation_id: str = None, session_type: str = "general") -> Tuple[str, str]:
        """
        사용자 메시지를 기록합니다.
        
        Args:
            user_id: 사용자 ID
            message_text: 메시지 내용
            conversation_id: 대화 세션 ID (없으면 최근 세션 또는 새 세션 사용)
            session_type: 세션 유형 (새 세션 생성 시 사용)
            
        Returns:
            (대화 세션 ID, 메시지 ID)
        """
        # 세션 ID가 없으면 활성 세션 가져오거나 새로 생성
        if not conversation_id:
            session = self.get_or_create_session(user_id, session_type)
            conversation_id = session['conversation_id']
        
        # 메시지 추가
        message_id = self.conversation_dao.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            sender='user',
            message_text=message_text
        )
        
        return conversation_id, message_id
    
    def record_assistant_message(self, user_id: str, message_text: str, conversation_id: str,
                               is_important: bool = False, entities: Dict = None) -> str:
        """
        어시스턴트 메시지를 기록합니다.
        
        Args:
            user_id: 사용자 ID
            message_text: 메시지 내용
            conversation_id: 대화 세션 ID
            is_important: 중요 메시지 여부
            entities: 추출된 엔티티
            
        Returns:
            메시지 ID
        """
        # 메시지 엔티티가 없으면 LLM으로 추출 시도
        if entities is None and len(message_text) > 20:
            try:
                entities = self._extract_health_entities_with_llm(message_text)
                logger.info(f"LLM을 통한 건강 엔티티 추출 완료: {len(entities)} 항목")
            except Exception as e:
                logger.error(f"LLM 엔티티 추출 오류: {str(e)}")
                entities = {}
        
        # 메시지 추가
        message_id = self.conversation_dao.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            sender='assistant',
            message_text=message_text,
            is_important=is_important,
            entities=entities
        )
        
        return message_id
    
    def generate_conversation_summary(self, conversation_id: str, recent_message_count: int = 10) -> Optional[str]:
        """
        대화 요약을 생성합니다. (동기 버전)
        
        주의: 이 메서드는 동기 메서드이며, 비동기 컨텍스트에서 호출할 때는 
        await 없이 호출하거나 별도 스레드에서 실행해야 합니다.
        
        참고: 고급 요약이 필요한 경우 _generate_summary_with_llm 메서드를 
        비동기 컨텍스트에서 사용할 수 있습니다. 현재 구현에서는 간단한 요약만 생성합니다.
        
        Args:
            conversation_id: 대화 세션 ID
            recent_message_count: 요약에 포함할 최근 메시지 수
            
        Returns:
            생성된 요약 ID 또는 None
        """
        # 세션 정보 가져오기
        session = self.conversation_dao.get_session_by_id(conversation_id)
        if not session:
            logger.error(f"세션 ID {conversation_id}를 찾을 수 없음")
            return None
            
        # 최근 메시지 가져오기
        messages = self.conversation_dao.get_messages(conversation_id, limit=recent_message_count)
        if not messages:
            logger.warning(f"세션 {conversation_id}에 요약할 메시지가 없음")
            return None
        
        # 대화 내용 텍스트로 변환
        conversation_content = "\n".join([f"{msg['sender']}: {msg['message_text']}" for msg in messages])
        
        try:
            # 간단한 요약 생성 (LLM 없이)
            summary_text = f"이 대화에서는 {len(messages)}개의 메시지가 교환되었습니다."
            
            # 주요 내용 추출
            key_points = self._extract_key_points(messages, use_llm=False)
            
            # 건강 관련 엔티티 추출 - 모든 메시지에서 추출
            health_entities = {}
            for msg in messages:
                if msg['sender'] == 'assistant' and msg['message_text']:
                    try:
                        # 개별 메시지에서 추출
                        msg_entities = self._extract_health_entities_with_llm(msg['message_text'])
                        # 기존 엔티티에 병합
                        for category, items in msg_entities.items():
                            if category not in health_entities:
                                health_entities[category] = []
                            if isinstance(items, list):
                                health_entities[category].extend(items)
                            elif isinstance(items, dict):
                                if category not in health_entities:
                                    health_entities[category] = {}
                                health_entities[category].update(items)
                    except Exception as e:
                        logger.error(f"메시지 엔티티 추출 오류: {str(e)}")
            
            # 요약 저장
            summary_id = self.conversation_dao.add_conversation_summary(
                conversation_id=conversation_id,
                summary_text=summary_text,
                key_points=key_points,
                health_entities=health_entities
            )
            
            logger.info(f"대화 요약 생성 완료 (동기): {summary_id}")
            return summary_id
            
        except Exception as e:
            logger.error(f"대화 요약 생성 중 오류 (동기): {str(e)}")
            return None
    
    async def _generate_summary_with_llm(self, conversation_text: str) -> Dict[str, Any]:
        """
        LLM을 사용하여 대화 요약을 생성합니다. (비동기 버전)
        
        참고: 이 메서드는 generate_conversation_summary에서 직접 호출되지는 않지만,
        필요한 경우 비동기 컨텍스트에서 더 고급화된 요약 생성을 위해 호출할 수 있습니다.
        
        Args:
            conversation_text: 대화 내용 텍스트
            
        Returns:
            요약 정보 딕셔너리
        """
        try:
            logger.info("LLM을 통한 대화 요약 생성 시작")
            
            # 프롬프트 구성
            prompt = f"""
            다음 대화 내용을 분석하고 요약해주세요:
            
            {conversation_text}
            
            대화의 주요 내용, 건강 관련 우려사항, 권장사항, 향후 논의 주제 등을 포함해 요약해주세요.
            """
            
            # LLM 호출
            result = await self.summary_agent.ainvoke({"input": prompt})
            
            # 결과 파싱
            if hasattr(result, 'content'):
                output = result.content
            else:
                output = str(result)
            
            # JSON 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.warning("JSON 형식 응답을 찾을 수 없음")
                    return {'summary_text': '대화 요약을 생성할 수 없습니다.'}
            
            # JSON 파싱
            summary_data = json.loads(json_str)
            logger.info(f"LLM 요약 생성 완료: {summary_data.get('summary_text', '')[:50]}...")
            
            return summary_data
            
        except Exception as e:
            logger.error(f"LLM 요약 생성 중 오류: {str(e)}")
            return {'summary_text': f'대화 요약 생성 중 오류 발생: {str(e)}'}
    
    def _extract_health_entities_with_llm(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 건강 관련 엔티티를 추출합니다. (동기 버전)
        
        참고: 현재 구현에서는 LLM을 실제로 호출하지 않고 키워드 기반 추출을 사용합니다.
        향후 실제 LLM 호출로 교체할 수 있습니다.
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            추출된 건강 엔티티
        """
        try:
            logger.info("건강 엔티티 추출 시작 (동기 버전)")
            
            # 현재 구현에서는 기본 키워드 기반 추출 사용
            health_terms = ['혈압', '당뇨', '두통', '피로', '알레르기', '체중', '키', '온도', '맥박']
            health_entities = {
                'symptoms': [],
                'conditions': [],
                'medications': [],
                'biometrics': {},
                'diet': [],
                'exercise': [],
                'lifestyle': []
            }
            
            # 간단한 규칙 기반 추출
            text_lower = text.lower()
            
            # 증상 카테고리
            if '두통' in text_lower or '머리가 아프' in text_lower:
                health_entities['symptoms'].append('두통')
            if '피로' in text_lower or '피곤' in text_lower:
                health_entities['symptoms'].append('피로감')
            
            # 질병 카테고리
            if '당뇨' in text_lower:
                health_entities['conditions'].append('당뇨병')
            if '고혈압' in text_lower:
                health_entities['conditions'].append('고혈압')
            
            # 생체지표 카테고리
            if '혈압' in text_lower:
                health_entities['biometrics']['혈압'] = '측정 필요'
            if '체중' in text_lower:
                health_entities['biometrics']['체중'] = '언급됨'
                
            logger.info(f"엔티티 추출 완료: {len(health_entities)} 카테고리")
            return health_entities
            
        except Exception as e:
            logger.error(f"건강 엔티티 추출 중 오류: {str(e)}")
            return {}
    
    async def _extract_key_points_with_llm(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        LLM을 사용하여 메시지에서 주요 내용을 추출합니다. (비동기 버전)
        
        Args:
            messages: 메시지 목록
            
        Returns:
            추출된 주요 내용 목록
        """
        try:
            logger.info("LLM을 통한 주요 내용 추출 시작")
            
            # 메시지 내용 결합
            conversation_text = "\n".join([f"{msg['sender']}: {msg['message_text']}" for msg in messages])
            
            # 프롬프트 구성
            prompt = f"""
            다음 대화에서 주요 내용과 핵심 포인트를 추출해주세요:
            
            {conversation_text}
            """
            
            # LLM 호출
            result = await self.key_points_agent.ainvoke({"input": prompt})
            
            # 결과 파싱
            if hasattr(result, 'content'):
                output = result.content
            else:
                output = str(result)
            
            # JSON 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.warning("JSON 형식 응답을 찾을 수 없음")
                    return []
            
            # JSON 파싱
            key_points_data = json.loads(json_str)
            
            # 주요 내용 추출
            key_points = key_points_data.get('key_points', [])
            logger.info(f"LLM 주요 내용 추출 완료: {len(key_points)} 항목")
            
            return key_points
            
        except Exception as e:
            logger.error(f"LLM 주요 내용 추출 중 오류: {str(e)}")
            return []
    
    def _extract_key_points(self, messages: List[Dict[str, Any]], use_llm: bool = False) -> List[str]:
        """
        메시지에서 주요 내용을 추출합니다.
        
        Args:
            messages: 메시지 목록
            use_llm: LLM을 사용하여 고급 추출을 수행할지 여부 (비동기 컨텍스트에서만 True 사용 가능)
            
        Returns:
            추출된 주요 내용 목록
        """
        # use_llm이 True이면 경고 로그 (비동기 컨텍스트에서만 사용 가능)
        if use_llm:
            logger.warning("LLM 기반 키포인트 추출은 비동기 컨텍스트에서만 사용할 수 있습니다. "
                           "간단한 규칙 기반 추출로 대체합니다.")
        
        # 간단한 키 포인트 추출 (LLM 호출 없이 기본 제공)
        key_points = []
        
        for msg in messages:
            if len(msg['message_text']) > 100 and '?' in msg['message_text']:
                key_points.append(f"질문: {msg['message_text'][:50]}...")
            
            # 권장사항 추출
            if msg['sender'] == 'assistant' and ('권장' in msg['message_text'] or '추천' in msg['message_text']):
                sentences = msg['message_text'].split('.')
                for sentence in sentences:
                    if '권장' in sentence or '추천' in sentence:
                        key_points.append(f"권장사항: {sentence.strip()}.")
            
            # 주의사항 추출
            if msg['sender'] == 'assistant' and ('주의' in msg['message_text'] or '경고' in msg['message_text']):
                sentences = msg['message_text'].split('.')
                for sentence in sentences:
                    if '주의' in sentence or '경고' in sentence:
                        key_points.append(f"주의사항: {sentence.strip()}.")
                
        return key_points
    
    def get_context_for_llm(self, conversation_id: str, include_health_profile: bool = True) -> Dict[str, Any]:
        """
        LLM에 제공할 대화 컨텍스트를 가져옵니다.
        
        Args:
            conversation_id: 대화 세션 ID
            include_health_profile: 건강 프로필 포함 여부
            
        Returns:
            LLM 컨텍스트 정보
        """
        # 기본 대화 컨텍스트 가져오기
        context = self.conversation_dao.get_conversation_context(conversation_id)
        if not context:
            return {}
            
        # 사용자 정보 추가
        user_id = context['session']['user_id']
        user = self.user_dao.get_user_by_id(user_id)
        if user:
            context['user'] = {
                'user_id': user['user_id'],
                'name': user['name'],
                'gender': user['gender'],
                'age': self._calculate_age(user['birth_date']) if 'birth_date' in user else None
            }
        
        # 건강 프로필 추가 (옵션)
        if include_health_profile and user:
            try:
                health_profile = self.health_dao.get_complete_health_profile(user_id)
                if health_profile:
                    context['health_profile'] = health_profile
            except Exception as e:
                logger.error(f"건강 프로필 가져오기 오류: {str(e)}")
        
        return context
    
    def _calculate_age(self, birth_date) -> Optional[int]:
        """
        생년월일로부터 나이를 계산합니다.
        
        Args:
            birth_date: 생년월일
            
        Returns:
            나이 또는 None
        """
        if not birth_date:
            return None
            
        try:
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
                
            today = datetime.now().date()
            age = today.year - birth_date.year
            
            # 생일이 지나지 않았으면 1 빼기
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1
                
            return age
        except Exception as e:
            logger.error(f"나이 계산 오류: {str(e)}")
            return None 