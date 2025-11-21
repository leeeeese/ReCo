"""
공통 툴: 서브에이전트에서 사용할 수 있는 공통 함수들
PriceAgent, SafetyAgent에서 재사용 가능
"""

from typing import Dict, Any, List

import numpy as np
from sqlalchemy.orm import Session

from server.db.database import SessionLocal
from server.db.models import Product, Seller, Review


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


"""
PriceAgent 전용 툴
- DB에서 상품 시세 통계와 판매자 프로필 정보를 계산
"""


def item_market_tool(product_id: int) -> Dict[str, Any]:
    """
    PriceAgent 전용 툴:
    - DB에서 같은 카테고리/유사 상품들의 가격 분포를 보고
      시세와 현재 가격의 차이를 정량화한다.
    """
    db: Session = SessionLocal()

    def _empty_result(similar_count: int = 0) -> Dict[str, Any]:
        return {
            "item_id": int(product_id),
            "estimated_fair_price": None,
            "price_deviation_ratio": None,
            "price_percentile": None,
            "similar_items_count": int(similar_count),
        }

    try:
        product = (
            db.query(Product).filter(Product.product_id == product_id).first()
        )

        if not product or product.price is None:
            return _empty_result()

        category_top = product.category_top
        category_mid = product.category
        price = float(product.price)

        # --- 1) 유사 아이템 집합 정의 (같은 상/중 카테고리) ---
        similar_query = db.query(Product).filter(
            Product.category_top == category_top,
            Product.category == category_mid,
            Product.price.isnot(None),
        )
        prices: List[float] = [float(p.price) for p in similar_query]
        similar_items_count = len(prices)

        if similar_items_count < 5:
            # 데이터가 너무 적으면 None 처리
            return _empty_result(similar_items_count)

        prices_array = np.array(prices)

        # --- 2) 시세 추정 (median 사용 예시) ---
        fair_price = float(np.median(prices_array))

        if fair_price == 0:
            return _empty_result(similar_items_count)

        # --- 3) 시세 대비 비율, percentile 계산 ---
        price_deviation_ratio = (price - fair_price) / \
            fair_price  # -0.2 → 20% 싸다

        # percentile (분포에서 현재 가격이 몇 분위인지)
        price_percentile = float(np.mean(prices_array <= price))

        return {
            "item_id": int(product_id),
            "estimated_fair_price": fair_price,
            "price_deviation_ratio": price_deviation_ratio,
            "price_percentile": price_percentile,
            "similar_items_count": int(similar_items_count),
        }

    finally:
        db.close()


def price_risk_tool(
    market_features: Dict[str, Any],
    seller_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    PriceAgent 전용 툴:
    - 시세 대비 가격(market_features) + 판매자 신뢰도(seller_profile)를 종합해
      '가격 메리트'를 0~100 점수와 태그로 요약한다.
    """

    fair = market_features.get("estimated_fair_price")
    deviation = market_features.get("price_deviation_ratio")
    percentile = market_features.get("price_percentile")
    seller_trust = seller_profile.get("seller_trust_score", 50.0)

    if fair is None or deviation is None or percentile is None:
        # 정보 부족 → 중립
        return {
            "price_score": 50.0,
            "price_risk_type": "UNKNOWN",
            "price_comment_code": "INSUFFICIENT_MARKET_DATA",
        }

    # 기본 점수: 싸면 +, 비싸면 -
    # deviation = (현재가격 - 시세)/시세 → 음수일수록 싸다
    base = 70.0 - deviation * 100.0  # 예: -0.2 → +20점 느낌
    # 시세보다 80%나 싼 극단치 경우 penalty
    if deviation < -0.5:
        base -= 10.0

    # 판매자 신뢰도가 낮으면, 너무 싼 가격에 페널티
    if deviation < -0.2 and seller_trust < 60:
        base -= 15.0

    # 클리핑
    price_score = max(0.0, min(100.0, base))

    # 태그 지정
    if deviation < -0.4 and seller_trust < 60:
        risk_type = "TOO_CHEAP_RISK"
        comment_code = "SUSPICIOUSLY_CHEAP_WITH_LOW_TRUST"
    elif deviation < -0.15:
        risk_type = "FAIR_CHEAP"
        comment_code = "CHEAPER_THAN_MARKET"
    elif deviation > 0.15:
        risk_type = "OVERPRICED"
        comment_code = "MORE_EXPENSIVE_THAN_MARKET"
    else:
        risk_type = "FAIR"
        comment_code = "CLOSE_TO_MARKET_PRICE"

    return {
        "price_score": float(price_score),
        "price_risk_type": risk_type,
        "price_comment_code": comment_code,
    }


def trade_risk_tool(product_id: int) -> Dict[str, Any]:
    """
    SafetyAgent 전용 툴:
    - 거래 방식, 안전결제 사용 여부, 카테고리 등을 기준으로
      거래 구조의 위험도를 0~100 점수와 태그로 반환한다.
    """

    db: Session = SessionLocal()

    try:
        product = (
            db.query(Product).filter(Product.product_id == product_id).first()
        )

        if not product:
            return {
                "item_id": product_id,
                "trade_risk_score": 50.0,
                "trade_risk_flags": ["NO_ITEM_DATA"],
                "trade_risk_comment_code": "NO_ITEM_DATA",
            }

        sell_method = product.sell_method or ""
        delivery_fee = product.delivery_fee or ""
        is_safe = product.is_safe or ""
        category_top = product.category_top or ""
        price = float(product.price or 0.0)

        risk_score = 0.0
        flags: List[str] = []

        # 1) 안전결제 미사용
        if is_safe != "사용":
            risk_score += 30
            flags.append("NO_SAFE_PAYMENT")

        # 2) 택배만 가능한 거래 (직거래 없음)
        if "직거래" not in sell_method and "택배" in sell_method:
            risk_score += 20
            flags.append("REMOTE_ONLY")

        # 3) 고가 카테고리/전자제품 → 추가 리스크
        high_risk_categories = {"모바일/태블릿", "PC/노트북", "카메라/캠코더"}
        if category_top in high_risk_categories and price > 300000:
            risk_score += 20
            flags.append("HIGH_VALUE_ELECTRONICS")

        # 4) 배송비 선불/무료 등은 나중에 세분화 가능
        if delivery_fee == "없음":
            # 무료배송이라서 무조건 리스크는 아니고, 여기서는 패스
            pass

        # 기본 리스크 baseline
        risk_score = min(100.0, risk_score)

        if risk_score >= 70:
            comment = "HIGH_TRADE_RISK"
        elif risk_score >= 40:
            comment = "MEDIUM_TRADE_RISK"
        else:
            comment = "LOW_TRADE_RISK"

        return {
            "item_id": int(product_id),
            "trade_risk_score": float(risk_score),
            "trade_risk_flags": flags,
            "trade_risk_comment_code": comment,
        }

    finally:
        db.close()


def review_feature_tool(
    seller_id: int,
    max_reviews: int = 20,
) -> Dict[str, Any]:
    """
    SafetyAgent / PriceAgent 공통 툴:
    - 최근 리뷰 내용을 요약해 긍/부정 키워드 및 길이 등을 분석한다.
    """
    db: Session = SessionLocal()

    try:
        # 최신 리뷰 순으로 제한
        reviews = (
            db.query(Review)
            .filter(Review.seller_id == seller_id)
            .order_by(Review.id.desc())
            .limit(max_reviews)
            .all()
        )
        review_count = db.query(Review).filter(
            Review.seller_id == seller_id).count()

        if not reviews:
            return {
                "seller_id": int(seller_id),
                "review_count": int(review_count),
                "used_review_count": 0,
                "avg_review_length": 0.0,
                "joined_reviews": "",
                "positive_keywords": [],
                "negative_keywords": [],
                "positive_hits": 0,
                "negative_hits": 0,
                "has_negative_signal": False,
            }

        contents = [review.review_content or "" for review in reviews]
        used_count = len(contents)
        lengths = [len(c) for c in contents]
        avg_len = float(sum(lengths) / used_count) if used_count > 0 else 0.0
        joined_reviews = "\n".join(contents)

        positive_vocab = [
            "친절", "빠른", "감사", "좋았", "좋네요", "좋습니다",
            "상태 좋", "좋아요", "만족", "정품", "안전", "깨끗"
        ]
        negative_vocab = [
            "사기", "환불", "문제", "불량", "짜증", "최악",
            "다시는", "늦게", "연락이 안", "연락안됨", "가품", "거짓"
        ]

        positive_keywords: List[str] = []
        negative_keywords: List[str] = []
        pos_hits = 0
        neg_hits = 0

        lower_text = joined_reviews.lower()

        for kw in positive_vocab:
            if kw in lower_text:
                positive_keywords.append(kw)
                pos_hits += lower_text.count(kw)

        for kw in negative_vocab:
            if kw in lower_text:
                negative_keywords.append(kw)
                neg_hits += lower_text.count(kw)

        has_negative = neg_hits > 0

        return {
            "seller_id": int(seller_id),
            "review_count": int(review_count),
            "used_review_count": int(used_count),
            "avg_review_length": avg_len,
            "joined_reviews": joined_reviews,
            "positive_keywords": positive_keywords[:10],
            "negative_keywords": negative_keywords[:10],
            "positive_hits": int(pos_hits),
            "negative_hits": int(neg_hits),
            "has_negative_signal": has_negative,
        }
    finally:
        db.close()
