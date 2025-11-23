"""
챗봇 페이지
에이전트 기반 추천 시스템과 대화형 인터페이스
"""

import streamlit as st
import re
from typing import Dict, Any, Optional
from app.utils.chat_state import (
    init_chat_state,
    add_message,
    get_chat_history,
    update_workflow_status,
    set_recommendation,
    clear_chat
)
from app.utils.api_client import api_client
from app.components.chat_message import render_message, render_system_message
from app.components.recommendation_card import (
    render_recommendation_list,
    render_recommendation_summary
)
from app.components.workflow_status import render_workflow_status


# 페이지 설정
st.set_page_config(
    page_title="ReCo 챗봇",
    page_icon="💬",
    layout="wide"
)

# 상태 초기화
init_chat_state()

# 스타일
st.markdown("""
    <style>
    .chat-container {
        height: 600px;
        overflow-y: auto;
        padding: 20px;
        background-color: #f9f9f9;
        border-radius: 10px;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)


def extract_user_preferences(user_message: str) -> Dict[str, float]:
    """
    사용자 메시지에서 선호도 추출 (간단한 키워드 기반)
    실제로는 LLM을 사용하여 추출하는 것이 좋음
    """
    preferences = {
        "trust_safety": 50.0,
        "quality_condition": 50.0,
        "remote_transaction": 50.0,
        "activity_responsiveness": 50.0,
        "price_flexibility": 50.0,
    }
    
    message_lower = user_message.lower()
    
    # 가격 관련 키워드
    if any(word in message_lower for word in ["가격", "저렴", "싸게", "비싸", "할인"]):
        preferences["price_flexibility"] = 70.0
    
    # 신뢰/안전 관련 키워드
    if any(word in message_lower for word in ["신뢰", "안전", "믿을", "검증", "리뷰"]):
        preferences["trust_safety"] = 70.0
    
    # 품질 관련 키워드
    if any(word in message_lower for word in ["품질", "상태", "깨끗", "새것", "A급"]):
        preferences["quality_condition"] = 70.0
    
    # 원격거래 관련 키워드
    if any(word in message_lower for word in ["택배", "온라인", "배송", "직거래"]):
        preferences["remote_transaction"] = 70.0
    
    return preferences


def parse_search_query(user_message: str) -> Optional[str]:
    """
    사용자 메시지에서 검색 쿼리 추출
    """
    # 간단한 추출 로직 (실제로는 더 정교한 NLP 필요)
    # "아이폰 14 프로 찾고 있어요" -> "아이폰 14 프로"
    
    # 일반적인 패턴 제거
    patterns = [
        r"찾고\s+있",
        r"찾아",
        r"추천",
        r"알려",
        r"보여",
        r"줘",
        r"해줘",
    ]
    
    query = user_message
    for pattern in patterns:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE)
    
    query = query.strip()
    return query if query else None


def build_user_input(user_message: str) -> Dict[str, Any]:
    """
    사용자 메시지를 UserInput 스키마에 맞게 변환
    """
    search_query = parse_search_query(user_message)
    if not search_query:
        search_query = user_message  # 전체 메시지를 검색 쿼리로 사용
    
    preferences = extract_user_preferences(user_message)
    
    return {
        "search_query": search_query,
        **preferences,
        "category": None,
        "location": None,
        "price_min": None,
        "price_max": None,
    }


def handle_recommendation_request(user_message: str):
    """
    추천 요청 처리
    
    🔧 수정 포인트:
    - 141줄: 챗봇 응답 메시지 변경 가능
    - 144줄: 워크플로우 단계명 변경 가능
    - 148줄: user_input 생성 전 추가 로직 삽입 가능
    - 163-178줄: API 응답 처리 로직 수정 가능
    """
    # 사용자 메시지 추가
    add_message("user", user_message)
    
    # 🔧 수정 가능: 챗봇 응답 메시지 변경
    add_message("assistant", "네, 찾아드릴게요! 잠시만 기다려주세요...")
    
    # 🔧 수정 가능: 워크플로우 단계명 변경
    update_workflow_status("initialization", [], is_running=True)
    
    try:
        # 🔧 수정 가능: UserInput 생성 전 추가 로직 (검증, 전처리 등)
        user_input = build_user_input(user_message)
        
        # 🔧 수정 가능: spinner 메시지 변경
        with st.spinner("추천 시스템이 분석 중입니다..."):
            result = api_client.recommend_products(user_input)
        
        # 워크플로우 상태 업데이트
        update_workflow_status("recommendation", 
                             ["initialization", "price_analysis", "safety_analysis", "recommendation"],
                             is_running=False)
        
        # 추천 결과 저장
        set_recommendation(result)
        
        # 🔧 수정 가능: API 응답 처리 로직 변경
        status = result.get("status", "success")
        
        if status == "success":
            # RecommendationState 구조 또는 간단한 응답 구조 모두 처리
            final_items = result.get("final_item_scores") or result.get("ranked_products", [])
            
            if final_items:
                # 🔧 수정 가능: 성공 메시지 변경
                st.session_state.chat_history[-1]["content"] = f"추천 결과를 찾았어요! {len(final_items)}개의 상품을 추천드립니다."
            else:
                # 🔧 수정 가능: 결과 없을 때 메시지 변경
                message = result.get("message", "추천 시스템이 준비 중입니다.")
                st.session_state.chat_history[-1]["content"] = f"{message} (시스템 준비 중)"
        else:
            # 🔧 수정 가능: 에러 메시지 처리 방식 변경
            error_msg = result.get("error_message") or result.get("message", "알 수 없는 오류")
            st.session_state.chat_history[-1]["content"] = f"추천 중 오류가 발생했어요: {error_msg}"
    
    except Exception as e:
        update_workflow_status(None, [], is_running=False)
        error_msg = f"오류가 발생했습니다: {str(e)}"
        st.session_state.chat_history[-1]["content"] = error_msg
        st.error(error_msg)


def main():
    """메인 페이지"""
    
    # 헤더
    st.title("💬 ReCo 챗봇")
    st.markdown("에이전트 기반 중고거래 추천 시스템과 대화해보세요!")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 채팅 초기화 버튼
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            clear_chat()
            st.rerun()
        
        st.markdown("---")
        
        # API 상태 확인
        st.subheader("🔌 연결 상태")
        if api_client.health_check():
            st.success("✅ 서버 연결됨")
        else:
            st.error("❌ 서버 연결 실패")
            st.info(f"서버 URL: {api_client.base_url}")
        
        st.markdown("---")
        
        # 사용 가이드
        st.subheader("📖 사용 가이드")
        st.markdown("""
        **예시 질문:**
        - "아이폰 14 프로 찾고 있어요"
        - "가격이 중요해요"
        - "신뢰할 수 있는 판매자 추천해줘"
        - "노트북 추천해주세요"
        """)
    
    # 🔧 수정 가능: 레이아웃 비율 변경 (예: [3, 1] 또는 [1, 1])
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 🔧 수정 가능: 헤더 텍스트 변경
        st.subheader("💬 대화")
        
        chat_history = get_chat_history()
        
        if not chat_history:
            st.info("👋 안녕하세요! 찾고 계신 상품을 말씀해주세요.")
            st.markdown("""
            **예시:**
            - "아이폰 14 프로 찾고 있어요"
            - "가격이 중요해요"
            - "신뢰할 수 있는 판매자 추천해줘"
            """)
        else:
            # 채팅 메시지 표시
            for message in chat_history:
                render_message(message)
        
        # 워크플로우 진행 상황
        workflow_status = st.session_state.get("workflow_status", {})
        if workflow_status.get("is_running"):
            render_workflow_status(workflow_status)
        
        # 🔧 수정 가능: 입력 필드 변경 (text_input → text_area 등)
        st.markdown("---")
        user_input = st.text_input(
            "메시지 입력",
            placeholder="예: 아이폰 14 프로 찾고 있어요",
            key="chat_input"
        )
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("📤 전송", type="primary", use_container_width=True):
                if user_input.strip():
                    handle_recommendation_request(user_input.strip())
                    st.rerun()
        
        with col_btn2:
            if st.button("🔄 새로고침", use_container_width=True):
                st.rerun()
    
    with col2:
        # 추천 결과
        st.subheader("🎯 추천 결과")
        
        current_recommendation = st.session_state.get("current_recommendation")
        
        if current_recommendation:
            # 요약 정보
            render_recommendation_summary(current_recommendation)
            
            # 추천 상품 리스트 (여러 가능한 키 확인)
            final_items = (
                current_recommendation.get("final_item_scores") or 
                current_recommendation.get("ranked_products") or 
                []
            )
            
            if final_items:
                # 🔧 수정 가능: 표시 개수 변경 또는 다른 컴포넌트 사용
                render_recommendation_list(final_items[:10])  # 상위 10개만 표시
            else:
                # 🔧 수정 가능: 결과 없을 때 표시 방식 변경
                if current_recommendation.get("message"):
                    st.info(current_recommendation.get("message"))
                else:
                    st.info("추천 결과가 없습니다.")
        else:
            st.info("대화를 시작하면 추천 결과가 여기에 표시됩니다.")


if __name__ == "__main__":
    main()

