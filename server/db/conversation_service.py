"""
대화 세션 및 메시지 관리 서비스
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from server.db.models import Conversation, Message
from server.db.database import SessionLocal


def create_conversation(user_id: Optional[str] = None) -> Conversation:
    """새 대화 세션 생성"""
    db: Session = SessionLocal()
    try:
        session_id = str(uuid.uuid4())
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    finally:
        db.close()


def get_conversation_by_session_id(session_id: str) -> Optional[Conversation]:
    """세션 ID로 대화 조회"""
    db: Session = SessionLocal()
    try:
        return db.query(Conversation).filter(Conversation.session_id == session_id).first()
    finally:
        db.close()


def get_or_create_conversation(session_id: Optional[str] = None, user_id: Optional[str] = None) -> Conversation:
    """대화 세션 조회 또는 생성"""
    if session_id:
        conversation = get_conversation_by_session_id(session_id)
        if conversation:
            return conversation
    
    return create_conversation(user_id=user_id)


def add_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Message:
    """메시지 추가"""
    db: Session = SessionLocal()
    try:
        # 대화 세션 조회 또는 생성
        conversation = get_or_create_conversation(session_id=session_id)
        
        message = Message(
            conversation_id=conversation.id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    finally:
        db.close()


def get_conversation_messages(session_id: str, limit: int = 50) -> List[Message]:
    """대화 세션의 메시지 목록 조회"""
    db: Session = SessionLocal()
    try:
        return db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).limit(limit).all()
    finally:
        db.close()


def get_conversation_context(session_id: str, limit: int = 10) -> Dict[str, Any]:
    """대화 컨텍스트 추출 (Agent에 전달할 형식)"""
    messages = get_conversation_messages(session_id, limit=limit)
    
    # 최근 N개 메시지만 사용 (토큰 절약)
    recent_messages = messages[-limit:] if len(messages) > limit else messages
    
    context = {
        "previous_messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata or {}
            }
            for msg in recent_messages
        ],
        "total_messages": len(messages),
        "session_id": session_id
    }
    
    # 이전 추천 결과 추출
    previous_recommendations = []
    for msg in recent_messages:
        if msg.role == "assistant" and msg.metadata:
            if "recommendation_result" in msg.metadata:
                previous_recommendations.append(msg.metadata["recommendation_result"])
    
    if previous_recommendations:
        context["previous_recommendations"] = previous_recommendations
    
    return context

