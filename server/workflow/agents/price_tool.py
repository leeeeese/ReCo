"""
PriceAgent 전용 툴
- DB에서 상품 시세 통계와 판매자 프로필 정보를 계산
"""

from typing import Dict, Any, List

import numpy as np
from sqlalchemy.orm import Session

from server.db.database import SessionLocal
from server.db.models import Product


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
