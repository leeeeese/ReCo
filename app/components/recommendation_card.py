"""
추천 결과 카드 컴포넌트
"""

import streamlit as st
from typing import Dict, Any, List
from app.utils.formatters import format_price, format_score, truncate_text


def render_recommendation_card(product: Dict[str, Any], rank: int = None):
    """
    추천 상품 카드 렌더링
    
    Args:
        product: 상품 정보 딕셔너리
        rank: 순위 (선택사항)
    """
    title = product.get("title", "제목 없음")
    price = product.get("price", 0)
    seller_name = product.get("seller_name", "판매자 정보 없음")
    final_score = product.get("final_score", 0)
    ranking_factors = product.get("ranking_factors", {})
    
    # 카드 컨테이너
    with st.container():
        st.markdown("---")
        
        # 순위 표시
        if rank is not None:
            st.markdown(f"### 🏆 {rank}위")
        
        # 상품 정보
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**{title}**")
            st.markdown(f"💰 **{format_price(price)}**")
            st.markdown(f"👤 판매자: {seller_name}")
        
        with col2:
            st.metric("추천 점수", format_score(final_score))
        
        # 랭킹 요인 표시
        if ranking_factors:
            with st.expander("📊 추천 이유 보기"):
                for factor, value in ranking_factors.items():
                    if isinstance(value, (int, float)):
                        st.write(f"- **{factor}**: {format_score(value)}")
                    else:
                        st.write(f"- **{factor}**: {value}")
        
        st.markdown("---")


def render_recommendation_list(products: List[Dict[str, Any]]):
    """
    추천 상품 리스트 렌더링
    
    Args:
        products: 상품 리스트
    """
    if not products:
        st.info("추천 결과가 없습니다.")
        return
    
    st.markdown("### 🎯 추천 상품")
    
    for idx, product in enumerate(products, 1):
        render_recommendation_card(product, rank=idx)


def render_recommendation_summary(result: Dict[str, Any]):
    """
    추천 결과 요약 정보 렌더링
    
    Args:
        result: 추천 결과 딕셔너리
    """
    persona = result.get("persona_classification", {})
    final_items = result.get("final_item_scores", [])
    ranking_explanation = result.get("ranking_explanation", "")
    
    # 페르소나 정보
    if persona:
        persona_type = persona.get("persona_type", "알 수 없음")
        st.info(f"🎭 추천된 페르소나: **{persona_type}**")
    
    # 추천 상품 개수
    if final_items:
        st.success(f"✅ {len(final_items)}개의 상품을 추천했습니다!")
    
    # 랭킹 설명
    if ranking_explanation:
        st.markdown(f"💡 **추천 기준**: {ranking_explanation}")

