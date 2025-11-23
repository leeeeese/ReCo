"""
채팅 메시지 컴포넌트
"""

import streamlit as st
from typing import Dict, Any
from datetime import datetime


def render_message(message: Dict[str, Any]):
    """
    채팅 메시지 렌더링
    
    Args:
        message: 메시지 딕셔너리
            - role: "user" or "assistant"
            - content: 메시지 내용
            - timestamp: 시간
            - metadata: 추가 메타데이터
    """
    role = message.get("role", "assistant")
    content = message.get("content", "")
    timestamp = message.get("timestamp")
    
    if role == "user":
        # 사용자 메시지 (오른쪽 정렬)
        st.markdown(
            f"""
            <div style="text-align: right; margin: 10px 0;">
                <div style="display: inline-block; background-color: #007bff; color: white; padding: 10px 15px; border-radius: 18px; max-width: 70%;">
                    {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # 봇 메시지 (왼쪽 정렬)
        st.markdown(
            f"""
            <div style="text-align: left; margin: 10px 0;">
                <div style="display: inline-block; background-color: #f0f0f0; color: #333; padding: 10px 15px; border-radius: 18px; max-width: 70%;">
                    {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 타임스탬프 (선택사항)
        if timestamp:
            time_str = timestamp.strftime("%H:%M")
            st.caption(f"🕒 {time_str}")


def render_system_message(content: str, message_type: str = "info"):
    """
    시스템 메시지 렌더링 (워크플로우 진행 상황 등)
    
    Args:
        content: 메시지 내용
        message_type: "info", "success", "warning", "error"
    """
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    icon = icons.get(message_type, "ℹ️")
    
    st.markdown(
        f"""
        <div style="text-align: center; margin: 10px 0; padding: 10px; background-color: #e8f4f8; border-radius: 10px;">
            {icon} {content}
        </div>
        """,
        unsafe_allow_html=True
    )

