"""
ReCo Streamlit UI
중고거래 추천 시스템 프론트엔드
"""

import streamlit as st
import requests
from typing import Dict, Any

# 페이지 설정
st.set_page_config(
    page_title="ReCo - 중고거래 추천",
    page_icon="🛍️",
    layout="wide"
)

# 스타일
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """메인 페이지"""

    # 헤더
    st.markdown('<p class="main-header">🛍️ ReCo - 중고거래 추천 시스템</p>',
                unsafe_allow_html=True)
    st.markdown("---")

    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")

        st.subheader("검색 조건")
        search_query = st.text_input("상품명", placeholder="예: 아이폰 14 프로")

        st.subheader("카테고리")
        category = st.selectbox(
            "카테고리 선택",
            ["전체", "스마트폰", "노트북", "가전제품", "의류", "기타"]
        )

        st.subheader("가격 범위")
        price_min = st.number_input("최소 가격 (원)", value=0, step=10000)
        price_max = st.number_input("최대 가격 (원)", value=10000000, step=10000)

        st.subheader("위치")
        location = st.text_input("지역", placeholder="예: 서울")

    # 메인 컨텐츠
    st.header("🎯 사용자 선호도 설정")
    st.markdown("슬라이더를 조정하여 원하는 판매자 유형을 선택하세요.")

    col1, col2, col3 = st.columns(3)

    with col1:
        trust_safety = st.slider(
            "신뢰·안전 🔒",
            0, 100, 50,
            help="신뢰할 수 있는 판매자인가요?"
        )
        quality_condition = st.slider(
            "품질·상태 📦",
            0, 100, 50,
            help="상품의 품질이 중요한가요?"
        )

    with col2:
        remote_transaction = st.slider(
            "원격거래성향 📱",
            0, 100, 50,
            help="온라인 거래를 선호하시나요?"
        )
        activity_responsiveness = st.slider(
            "활동·응답 📬",
            0, 100, 50,
            help="빠른 응답을 원하시나요?"
        )

    with col3:
        price_flexibility = st.slider(
            "가격유연성 💰",
            0, 100, 50,
            help="가격 흥정이 가능한가요?"
        )

    st.markdown("---")

    # 추천 버튼
    if st.button("🚀 추천 시작", type="primary", use_container_width=True):
        if not search_query:
            st.error("상품명을 입력해주세요!")
            return

        with st.spinner("추천 시스템이 실행 중입니다..."):
            try:
                # API 호출
                payload = {
                    "search_query": search_query,
                    "trust_safety": trust_safety,
                    "quality_condition": quality_condition,
                    "remote_transaction": remote_transaction,
                    "activity_responsiveness": activity_responsiveness,
                    "price_flexibility": price_flexibility,
                    "category": category if category != "전체" else None,
                    "location": location,
                    "price_min": price_min if price_min > 0 else None,
                    "price_max": price_max if price_max < 10000000 else None,
                }

                # TODO: 실제 API 호출
                # response = requests.post("http://localhost:8000/api/v1/recommend", json=payload)

                st.success("추천 시스템 준비 중입니다!")
                st.json(payload)

            except Exception as e:
                st.error(f"오류 발생: {str(e)}")


if __name__ == "__main__":
    main()
