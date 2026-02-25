"""
ReCo Streamlit UI - 메인 진입점 (레거시)
중고거래 추천 시스템 프론트엔드

신규 앱: streamlit_app/app.py
실행: streamlit run streamlit_app/app.py
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# 페이지 설정
st.set_page_config(
    page_title="ReCo - 중고거래 추천",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    padding: 2rem;
}
.menu-card {
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s;
    cursor: pointer;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
}
.menu-card:hover {
    transform: translateY(-5px);
}
</style>
""", unsafe_allow_html=True)


def main():
    """메인 페이지"""
    st.markdown('<p class="main-header">🛍️ ReCo - 중고거래 추천 시스템</p>',
                unsafe_allow_html=True)
    st.markdown("---")

    st.info(
        "💡 **새 버전의 Streamlit 앱이 준비되어 있습니다.**  \n"
        "더 완성도 높은 추천 UI를 사용하려면 아래 명령을 실행하세요:  \n"
        "`streamlit run streamlit_app/app.py`"
    )

    st.markdown("### 🎯 서비스 선택")
    st.markdown("원하시는 서비스를 선택해주세요.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="menu-card">
            <h2>🔍 상품 추천</h2>
            <p>AI 에이전트가 분석한<br>중고거래 상품 추천 받기</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("추천 시작", key="rec_btn", use_container_width=True, type="primary"):
            st.switch_page("streamlit_app/app.py")

    with col2:
        st.markdown("""
        <div style="padding: 2rem; border-radius: 15px; background-color: #f0f0f0; text-align: center;">
            <h2>📦 상품 조회</h2>
            <p>준비 중입니다</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("상품 조회", key="products_btn", use_container_width=True, disabled=True)

    with col3:
        st.markdown("""
        <div style="padding: 2rem; border-radius: 15px; background-color: #f0f0f0; text-align: center;">
            <h2>👤 마이페이지</h2>
            <p>준비 중입니다</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("마이페이지", key="mypage_btn", use_container_width=True, disabled=True)

    st.markdown("---")
    st.caption(f"백엔드: {BACKEND_URL} | Azure OpenAI 기반")


if __name__ == "__main__":
    main()
