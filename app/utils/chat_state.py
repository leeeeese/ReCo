"""
채팅 상태 관리 유틸리티
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime


def init_chat_state():
    """채팅 상태 초기화"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "current_recommendation" not in st.session_state:
        st.session_state.current_recommendation = None
    
    if "workflow_status" not in st.session_state:
        st.session_state.workflow_status = {
            "current_step": None,
            "completed_steps": [],
            "is_running": False
        }
    
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = {
            "trust_safety": 50.0,
            "quality_condition": 50.0,
            "remote_transaction": 50.0,
            "activity_responsiveness": 50.0,
            "price_flexibility": 50.0,
        }


def add_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
    """메시지 추가"""
    message = {
        "role": role,  # "user" or "assistant"
        "content": content,
        "timestamp": datetime.now(),
        "metadata": metadata or {}
    }
    st.session_state.chat_history.append(message)


def clear_chat():
    """채팅 히스토리 초기화"""
    st.session_state.chat_history = []
    st.session_state.current_recommendation = None
    st.session_state.workflow_status = {
        "current_step": None,
        "completed_steps": [],
        "is_running": False
    }


def update_workflow_status(step: str, completed: List[str] = None, is_running: bool = False):
    """워크플로우 상태 업데이트"""
    st.session_state.workflow_status = {
        "current_step": step,
        "completed_steps": completed or [],
        "is_running": is_running
    }


def set_recommendation(result: Dict[str, Any]):
    """추천 결과 저장"""
    st.session_state.current_recommendation = result


def get_chat_history() -> List[Dict[str, Any]]:
    """채팅 히스토리 조회"""
    return st.session_state.get("chat_history", [])

