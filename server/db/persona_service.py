"""
판매자 페르소나 계산 및 조회 서비스
Persona Matching Agent에서 사용
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from server.db.database import SessionLocal
from server.db.models import Seller, Review, Product
from server.workflow.state import PersonaVector


def calculate_seller_persona_vector(seller: Seller, reviews: List[Review]) -> PersonaVector:
    """
    판매자 데이터와 리뷰를 분석하여 페르소나 벡터 계산

    Args:
        seller: 판매자 정보
        reviews: 판매자 리뷰 리스트

    Returns:
        계산된 페르소나 벡터
    """
    # 1. trust_safety 계산
    # seller_trust 점수를 0-100 스케일로 변환 (445-575 범위를 가정)
    trust_base = min(max((seller.seller_trust - 400) / 2, 0),
                     100) if seller.seller_trust else 50.0

    # seller_safe_sales가 있으면 trust_safety 증가
    safe_sales_bonus = min(seller.seller_safe_sales * 5,
                           20) if seller.seller_safe_sales else 0

    # 리뷰에서 신뢰 관련 키워드 확인
    trust_keywords = ["신뢰", "믿음", "안전", "보증", "정품", "인증"]
    trust_review_bonus = 0
    if reviews:
        trust_review_count = sum(1 for review in reviews
                                 if any(keyword in review.review_content for keyword in trust_keywords))
        trust_review_bonus = min(trust_review_count * 2, 15)

    trust_safety = min(trust_base + safe_sales_bonus + trust_review_bonus, 100)

    # 2. quality_condition 계산
    # seller_customs (거래 건수)가 많으면 품질 신뢰도 높음
    quality_base = min(seller.seller_customs / 10,
                       50) if seller.seller_customs else 50.0

    # 리뷰에서 품질 관련 키워드
    quality_keywords = ["상태 좋", "새상품", "깨끗", "완벽", "품질", "좋은 제품"]
    quality_review_bonus = 0
    if reviews:
        quality_review_count = sum(1 for review in reviews
                                   if any(keyword in review.review_content for keyword in quality_keywords))
        quality_review_bonus = min(quality_review_count * 3, 30)

    quality_condition = min(quality_base + quality_review_bonus, 100)

    # 3. remote_transaction 계산
    # sell_method에 "택배"가 있으면 remote_transaction 높음
    remote_base = 50.0
    if seller.sell_method:
        if "택배" in seller.sell_method:
            remote_base = 80.0
        elif "직거래" in seller.sell_method and "택배" not in seller.sell_method:
            remote_base = 30.0

    # 리뷰에서 배송 관련 키워드
    shipping_keywords = ["배송", "택배", "빠른 배송", "포장"]
    shipping_bonus = 0
    if reviews:
        shipping_review_count = sum(1 for review in reviews
                                    if any(keyword in review.review_content for keyword in shipping_keywords))
        shipping_bonus = min(shipping_review_count * 2, 20)

    remote_transaction = min(remote_base + shipping_bonus, 100)

    # 4. activity_responsiveness 계산
    # seller_customs, seller_items, seller_chat이 많으면 활동성 높음
    activity_base = 50.0
    if seller.seller_customs:
        activity_base += min(seller.seller_customs / 5, 20)
    if seller.seller_items:
        activity_base += min(seller.seller_items * 2, 15)
    if seller.seller_chat:
        activity_base += min(seller.seller_chat * 3, 15)
    activity_base = min(activity_base, 100)

    # 리뷰에서 응답 관련 키워드
    response_keywords = ["빠른", "빠르게", "응답", "친절", "소통"]
    response_bonus = 0
    if reviews:
        response_review_count = sum(1 for review in reviews
                                    if any(keyword in review.review_content for keyword in response_keywords))
        response_bonus = min(response_review_count * 3, 25)

    activity_responsiveness = min(activity_base + response_bonus, 100)

    # 5. price_flexibility 계산
    # seller_customs가 많으면 가격 협상 경험 많음 → 유연성 높음
    price_base = 50.0
    if seller.seller_customs:
        price_base += min(seller.seller_customs / 10, 30)

    # 리뷰에서 협상 관련 키워드
    negotiation_keywords = ["협상", "할인", "가격", "저렴", "합리"]
    negotiation_bonus = 0
    if reviews:
        negotiation_review_count = sum(1 for review in reviews
                                       if any(keyword in review.review_content for keyword in negotiation_keywords))
        negotiation_bonus = min(negotiation_review_count * 2, 20)

    price_flexibility = min(price_base + negotiation_bonus, 100)

    return PersonaVector(
        trust_safety=round(trust_safety, 2),
        quality_condition=round(quality_condition, 2),
        remote_transaction=round(remote_transaction, 2),
        activity_responsiveness=round(activity_responsiveness, 2),
        price_flexibility=round(price_flexibility, 2)
    )


def get_sellers_with_persona(
    limit: int = 50,
    min_reviews: int = 0
) -> List[Dict[str, Any]]:
    """
    판매자와 페르소나 정보를 함께 조회 (Persona Matching Agent용)

    Args:
        limit: 최대 조회 개수
        min_reviews: 최소 리뷰 수 (필터링)

    Returns:
        페르소나 벡터가 포함된 판매자 리스트
    """
    db: Session = SessionLocal()

    try:
        # 리뷰가 있는 판매자만 조회
        sellers_with_reviews = db.query(
            Seller.seller_id,
            func.count(Review.id).label('review_count')
        ).join(
            Review, Seller.seller_id == Review.seller_id
        ).group_by(
            Seller.seller_id
        ).having(
            func.count(Review.id) >= min_reviews
        ).limit(limit).all()

        seller_ids = [s[0] for s in sellers_with_reviews]

        if not seller_ids:
            # 리뷰가 없는 경우 모든 판매자 조회
            sellers = db.query(Seller).limit(limit).all()
            seller_ids = [s.seller_id for s in sellers]

        # 판매자별로 페르소나 계산
        sellers_with_persona = []

        for seller_id in seller_ids:
            seller = db.query(Seller).filter(
                Seller.seller_id == seller_id).first()
            if not seller:
                continue

            # 판매자의 리뷰 조회
            reviews = db.query(Review).filter(
                Review.seller_id == seller_id).all()

            # 페르소나 벡터 계산
            persona_vector = calculate_seller_persona_vector(seller, reviews)

            # 판매자의 상품 조회 (최대 5개)
            products = db.query(Product).filter(
                Product.seller_id == seller_id
            ).order_by(Product.view_count.desc()).limit(5).all()

            sellers_with_persona.append({
                "seller_id": seller.seller_id,
                "seller_name": seller.seller_name,
                "seller_trust": seller.seller_trust,
                "seller_safe_sales": seller.seller_safe_sales,
                "seller_customs": seller.seller_customs,
                "seller_items": seller.seller_items,
                "sell_method": seller.sell_method,
                "persona_vector": persona_vector,
                "persona_type": None,  # 나중에 분류 가능
                "review_count": len(reviews),
                "avg_rating": seller.avg_rating,
                "products": [
                    {
                        "product_id": p.product_id,
                        "title": p.title,
                        "price": p.price,
                        "category": p.category,
                        "condition": p.condition
                    }
                    for p in products
                ]
            })

        return sellers_with_persona

    finally:
        db.close()
