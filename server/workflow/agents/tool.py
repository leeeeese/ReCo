"""
공통 툴: 서브에이전트에서 사용할 수 있는 공통 함수들
PriceAgent, SafetyAgent에서 재사용 가능
"""

from typing import List, Dict, Any, Optional
import re
from sqlalchemy.orm import Session
from server.db.database import SessionLocal
from server.db.models import Seller, Review


def seller_profile_tool(seller_id: int) -> Dict[str, Any]:
    """
    공통 툴: DB에서 판매자 정보와 리뷰를 조회하여
    판매자 신뢰도/리뷰/인기 정도를 정규화된 피처로 반환

    Args:
        seller_id: 판매자 ID

    Returns:
        판매자 프로필 정보 딕셔너리
    """
    db: Session = SessionLocal()

    try:
        # --- 1) DB에서 판매자 정보 조회 ---
        seller = db.query(Seller).filter(Seller.seller_id == seller_id).first()

        if not seller:
            # 판매자 정보 없음 → default low history profile
            return {
                "seller_id": seller_id,
                "seller_trust_score": 50.0,
                "num_items": 0,
                "num_safe_sales": 0,
                "num_customers": 0,
                "account_age_days": None,
                "popularity_index": 0.0,
                "category_top_main": None,
                "review_count": 0,
                "positive_review_ratio": None,
                "review_keywords_positive": [],
                "review_keywords_negative": [],
                "seller_risk_flags": ["NO_SELLER_DATA"],
            }

        # 판매자 데이터 추출
        num_safe_sales = seller.seller_safe_sales or 0
        num_items = seller.seller_items or 0
        num_customers = seller.seller_customs or 0
        account_age_days = None  # created_at이 없으므로 None

        # popularity index: view/like/chat을 정규화
        view = seller.seller_view or 0
        like = seller.seller_like or 0
        chat = seller.seller_chat or 0
        # 정규화: 최대값을 1000으로 가정하고 0~1로 스케일링
        popularity_index = min(
            1.0, (view * 0.2 + like * 0.5 + chat * 0.3) / 1000.0)

        category_top_main = seller.category_top or None

        # --- 2) DB에서 리뷰 조회 및 분석 ---
        reviews = db.query(Review).filter(Review.seller_id == seller_id).all()
        review_count = len(reviews)

        # 리뷰 키워드 분석
        positive_keywords: List[str] = []
        negative_keywords: List[str] = []
        positive_count = 0

        # 긍정/부정 키워드 정의
        positive_keyword_list = [
            "친절", "빠른", "빠르게", "좋은", "좋아", "만족", "감사", "최고",
            "깨끗", "완벽", "신뢰", "안전", "정품", "새상품", "상태 좋"
        ]
        negative_keyword_list = [
            "불만", "느린", "늦은", "나쁜", "불량", "문제", "피해", "사기",
            "가품", "기스", "손상", "불친절", "응답 없"
        ]

        if review_count > 0:
            for review in reviews:
                content = review.review_content or ""
                content_lower = content.lower()

                # 긍정 키워드 확인
                has_positive = any(
                    keyword in content_lower for keyword in positive_keyword_list)
                has_negative = any(
                    keyword in content_lower for keyword in negative_keyword_list)

                if has_positive:
                    positive_count += 1
                    # 키워드 추출
                    for keyword in positive_keyword_list:
                        if keyword in content_lower and keyword not in positive_keywords:
                            positive_keywords.append(keyword)

                if has_negative:
                    # 키워드 추출
                    for keyword in negative_keyword_list:
                        if keyword in content_lower and keyword not in negative_keywords:
                            negative_keywords.append(keyword)

            # 긍정 리뷰 비율 계산
            positive_review_ratio = positive_count / \
                review_count if review_count > 0 else None
        else:
            positive_review_ratio = None

        # --- 3) seller_trust_score & risk_flags ---
        # seller_trust는 이미 0~100 스케일로 저장되어 있음 (445~575 범위를 가정)
        # 0~100 스케일로 정규화 (400~600 범위를 0~100으로)
        base_trust = seller.seller_trust or 0.0
        # 400~600 범위를 0~100으로 정규화
        seller_trust_score = min(100.0, max(0.0, (base_trust - 400) / 2.0))

        risk_flags: List[str] = []

        if num_items < 3:
            risk_flags.append("LOW_HISTORY")
        if num_safe_sales == 0:
            risk_flags.append("NO_SAFE_SALES")
        if review_count == 0:
            risk_flags.append("NO_REVIEWS")
        if seller_trust_score < 30.0:
            risk_flags.append("LOW_TRUST_SCORE")

        return {
            "seller_id": int(seller_id),
            "seller_trust_score": float(seller_trust_score),
            "num_items": int(num_items),
            "num_safe_sales": int(num_safe_sales),
            "num_customers": int(num_customers),
            "account_age_days": account_age_days,
            "popularity_index": float(popularity_index),
            "category_top_main": category_top_main,
            "review_count": int(review_count),
            "positive_review_ratio": positive_review_ratio,
            "review_keywords_positive": positive_keywords[:10],  # 최대 10개
            "review_keywords_negative": negative_keywords[:10],  # 최대 10개
            "seller_risk_flags": risk_flags,
        }

    finally:
        db.close()
