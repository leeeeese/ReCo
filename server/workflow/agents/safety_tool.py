import numpy as np


def item_market_tool(
    item_code: int,
    item_df,   # pd.DataFrame or other data source
) -> Dict[str, Any]:
    """
    PriceAgent 전용 툴:
    - item_detail_data에서 같은 카테고리/유사 상품들의 가격 분포를 보고
      시세와 현재 가격의 차이를 정량화한다.
    """

    row = item_df.loc[item_df["item_code"] == item_code]
    if row.empty:
        return {
            "item_code": item_code,
            "estimated_fair_price": None,
            "price_deviation_ratio": None,
            "price_percentile": None,
            "similar_items_count": 0,
        }

    r = row.iloc[0]
    category_top = r["category_top"]
    category_mid = r["category_mid"]
    price = float(r["item_price"])

    # --- 1) 유사 아이템 집합 정의 (예: 같은 상/중 카테고리) ---
    similar = item_df.loc[
        (item_df["category_top"] == category_top)
        & (item_df["category_mid"] == category_mid)
    ]
    prices = similar["item_price"].astype(float).values
    similar_items_count = len(prices)

    if similar_items_count < 5:
        # 데이터가 너무 적으면 None 처리
        return {
            "item_code": int(item_code),
            "estimated_fair_price": None,
            "price_deviation_ratio": None,
            "price_percentile": None,
            "similar_items_count": int(similar_items_count),
        }

    # --- 2) 시세 추정 (median 사용 예시) ---
    fair_price = float(np.median(prices))

    # --- 3) 시세 대비 비율, percentile 계산 ---
    price_deviation_ratio = (price - fair_price) / fair_price  # -0.2 → 20% 싸다

    # percentile (분포에서 현재 가격이 몇 분위인지)
    price_percentile = float((prices <= price).mean())

    return {
        "item_code": int(item_code),
        "estimated_fair_price": fair_price,
        "price_deviation_ratio": price_deviation_ratio,
        "price_percentile": price_percentile,
        "similar_items_count": int(similar_items_count),
    }


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
