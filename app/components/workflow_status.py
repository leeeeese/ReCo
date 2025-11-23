"""
워크플로우 진행 상황 컴포넌트
"""

import streamlit as st
from typing import Dict, Any


def render_workflow_status(status: Dict[str, Any]):
    """
    워크플로우 진행 상황 표시
    
    Args:
        status: 워크플로우 상태 딕셔너리
    """
    if not status or not status.get("is_running"):
        return
    
    current_step = status.get("current_step")
    completed_steps = status.get("completed_steps", [])
    
    # 단계 정의
    steps = [
        ("initialization", "초기화", "🔍"),
        ("price_analysis", "가격 분석", "💰"),
        ("safety_analysis", "안전거래 분석", "🔒"),
        ("recommendation", "최종 추천", "✨"),
    ]
    
    st.markdown("### ⚙️ 분석 진행 상황")
    
    # 진행 바
    total_steps = len(steps)
    completed_count = len(completed_steps)
    progress = completed_count / total_steps if total_steps > 0 else 0
    st.progress(progress)
    
    # 단계별 상태 표시
    cols = st.columns(len(steps))
    
    for idx, (step_key, step_name, icon) in enumerate(steps):
        with cols[idx]:
            if step_key in completed_steps:
                st.success(f"{icon} {step_name}")
            elif current_step == step_key:
                st.info(f"{icon} {step_name} 중...")
            else:
                st.write(f"{icon} {step_name}")

