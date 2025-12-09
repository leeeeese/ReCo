"""
공통 유틸리티 Tools
Agent 노드에서 사용할 수 있는 공통 함수들
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional


# ==================== 텍스트 처리 Tools ====================

def extract_keywords(query: str) -> List[str]:
    """검색 쿼리에서 키워드 추출 (한글 포함)"""
    if not query:
        return []

    # 한글, 영문, 숫자를 포함한 키워드 추출
    # \w는 한글을 포함하지 않을 수 있으므로 명시적으로 패턴 정의
    keywords = re.findall(r'[가-힣a-zA-Z0-9]+', query.lower())
    stop_words = {'의', '을', '를', '이', '가', '은', '는', '에',
                  '에서', '로', '으로', '와', '과', '도', '만', '까지', '부터'}
    # 1글자 키워드도 허용 (예: '아이폰' 같은 경우)
    keywords = [kw for kw in keywords if kw not in stop_words and len(kw) >= 1]
    return keywords if keywords else [query.strip()]  # 키워드가 없으면 원본 쿼리 반환


def create_filters(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 입력에서 필터 조건 생성"""
    filters = {}
    if user_input.get("price_min"):
        filters["price_min"] = user_input["price_min"]
    if user_input.get("price_max"):
        filters["price_max"] = user_input["price_max"]
    if user_input.get("category"):
        filters["category"] = user_input["category"]
    if user_input.get("location"):
        filters["location"] = user_input["location"]
    return filters


# ==================== 벡터 및 점수 계산 Tools ====================

def normalize_slider_inputs(user_prefs: Dict[str, Any]) -> Dict[str, float]:
    """슬라이더 입력을 정규화"""
    normalized_vector = {}
    for key in ["trust_safety", "quality_condition", "remote_transaction",
                "activity_responsiveness", "price_flexibility"]:
        value = user_prefs.get(key, 50.0)
        normalized_vector[key] = max(0.0, min(100.0, float(value)))
    return normalized_vector


def calculate_seller_quality_score(seller: Dict[str, Any]) -> float:
    """판매자 품질 점수 계산"""
    rating_score = min(seller.get("avg_rating", 0) / 5.0, 1.0)
    sales_score = min(seller.get("total_sales", 0) / 1000.0, 1.0)
    response_score = max(
        0, 1 - (seller.get("response_time_hours", 24.0) / 24.0))
    return 0.5 * rating_score + 0.3 * sales_score + 0.2 * response_score


def calculate_product_feature_score(product: Dict[str, Any]) -> float:
    """상품 피처 점수 계산"""
    view_score = min(product.get("view_count", 0) / 1000.0, 1.0)
    like_score = min(product.get("like_count", 0) / 100.0, 1.0)

    condition_scores = {
        "새상품": 1.0,
        "거의새것": 0.8,
        "중고": 0.6,
        "사용감있음": 0.4
    }
    condition_score = condition_scores.get(product.get("condition", "중고"), 0.5)

    return 0.4 * view_score + 0.3 * like_score + 0.3 * condition_score


def normalize_scores(scores: List[float]) -> List[float]:
    """점수 리스트를 0-1 범위로 정규화 (Min-Max)"""
    if not scores or max(scores) == min(scores):
        return [0.5] * len(scores)
    return [(score - min(scores)) / (max(scores) - min(scores)) for score in scores]


def calculate_diversity_score(items: List[Dict[str, Any]], key: str) -> float:
    """다양성 점수 계산 (카테고리, 판매자 등)"""
    if not items:
        return 0.0
    unique_count = len(set(item.get(key) for item in items if key in item))
    return unique_count / len(items) if items else 0.0


# ==================== 상품 매칭 룰베이스 ====================

def match_products_to_sellers(
    recommended_sellers: List[Dict[str, Any]],
    user_input: Dict[str, Any],
    max_products_per_seller: int = 5
) -> List[Dict[str, Any]]:
    """
    추천된 판매자들에게 상품을 매칭하는 룰베이스 함수

    Args:
        recommended_sellers: 추천된 판매자 리스트 (seller_id 포함)
        user_input: 사용자 입력 (search_query, price_min, price_max 등)
        max_products_per_seller: 판매자당 최대 상품 수 (기본값: 10)

    Returns:
        판매자 정보와 매칭된 상품 리스트가 포함된 딕셔너리 리스트
        (상품이 없는 판매자는 제외됨)
    """
    from server.db.product_service import get_products_by_seller_ids
    from server.utils.logger import get_logger

    logger = get_logger(__name__)

    if not recommended_sellers:
        return []

    # 판매자 ID 추출
    seller_ids = [seller.get("seller_id")
                  for seller in recommended_sellers if seller.get("seller_id")]

    if not seller_ids:
        return []

    # DB에서 상품 조회 (필터링을 위해 더 많이 조회)
    sellers_with_products = get_products_by_seller_ids(
        seller_ids=seller_ids,
        limit=max_products_per_seller * 2  # 필터링 후에도 충분한 상품 확보
    )

    # 판매자 ID로 인덱싱
    sellers_dict = {str(seller["seller_id"]): seller for seller in sellers_with_products}

    # 중복 상품 추적 (여러 판매자에게 나타나는 상품 제거)
    seen_product_ids = set()

    # 추천된 판매자 순서대로 정렬하고 상품 매칭
    matched_results = []
    sellers_without_products = []

    for seller in recommended_sellers:
        seller_id = seller.get("seller_id")
        seller_id_str = str(seller_id)

        # DB에서 조회한 판매자 정보 가져오기
        seller_data = sellers_dict.get(seller_id_str, {})

        # 상품 필터링 (사용자 입력 조건에 맞는 상품만)
        products = seller_data.get("products", [])
        filtered_products = _filter_products_by_user_input(
            products, user_input)

        # 중복 상품 제거 (이미 다른 판매자에게 나타난 상품 제외)
        unique_products = []
        for product in filtered_products:
            product_id = product.get("product_id")
            if product_id and product_id not in seen_product_ids:
                unique_products.append(product)
                seen_product_ids.add(product_id)

        # 상품이 없는 경우 예외 처리
        if not unique_products:
            sellers_without_products.append({
                "seller_id": seller_id,
                "seller_name": seller.get("seller_name")
            })
            logger.warning(
                "판매자에게 매칭된 상품이 없음",
                extra={
                    "seller_id": seller_id,
                    "seller_name": seller.get("seller_name"),
                    "total_products_in_db": len(products),
                    "filtered_products": len(filtered_products)
                }
            )
            continue  # 상품이 없는 판매자는 결과에서 제외

        # 상품 점수 계산 및 정렬
        scored_products = []
        for product in unique_products:
            product_score = _calculate_product_match_score(
                product,
                seller,
                user_input
            )
            scored_products.append({
                **product,
                "match_score": product_score,
                "seller_id": seller_id,
                "seller_name": seller.get("seller_name"),
                "seller_price_score": seller.get("price_score", 0.0),
                "seller_safety_score": seller.get("safety_score", 0.0),
                "seller_final_score": seller.get("final_score", 0.0),
            })

        # 점수 순으로 정렬
        scored_products.sort(key=lambda x: x["match_score"], reverse=True)

        # 실제 상품 개수에 맞춰서 선택 (1개면 1개, 3개면 3개, 최대 10개)
        num_products = min(len(scored_products), max_products_per_seller)
        selected_products = scored_products[:num_products]

        matched_results.append({
            **seller,
            "products": selected_products,
        })

    # 상품이 없는 판매자 요약 로깅
    if sellers_without_products:
        logger.warning(
            "상품이 없는 판매자 제외",
            extra={
                "excluded_count": len(sellers_without_products),
                "excluded_sellers": sellers_without_products[:10]  # 최대 10개만 로깅
            }
        )

    return matched_results


def _filter_products_by_user_input(
    products: List[Dict[str, Any]],
    user_input: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """사용자 입력 조건에 맞는 상품만 필터링"""
    filtered = []

    price_min = user_input.get("price_min")
    price_max = user_input.get("price_max")
    category = user_input.get("category")
    search_query = user_input.get("search_query", "")

    for product in products:
        # 가격 필터
        if price_min is not None and product.get("price", 0) < price_min:
            continue
        if price_max is not None and product.get("price", 0) > price_max:
            continue

        # 카테고리 필터
        if category and product.get("category") != category:
            continue

        # 검색어 필터 제거: Orchestrator가 이미 적절한 판매자를 선택했으므로
        # 그 판매자의 모든 상품을 보여주는 것이 올바름
        # (LLM이 "아이폰 14" 원하는 사용자에게 아이폰 판매자를 선택했다면,
        #  그 판매자의 모든 아이폰 상품을 보여주어야 함)

        filtered.append(product)

    return filtered


def _calculate_product_match_score(
    product: Dict[str, Any],
    seller: Dict[str, Any],
    user_input: Dict[str, Any]
) -> float:
    """상품 매칭 점수 계산 (룰베이스)"""
    score = 0.0

    # 1. 판매자 최종 점수 (50%)
    seller_score = seller.get("final_score", 0.0)
    score += 0.5 * seller_score

    # 2. 상품 피처 점수 (30%)
    product_feature_score = calculate_product_feature_score(product)
    score += 0.3 * product_feature_score

    # 3. 가격 적합성 (20%)
    price = product.get("price", 0)
    price_min = user_input.get("price_min")
    price_max = user_input.get("price_max")

    if price_min is not None and price_max is not None:
        price_range = price_max - price_min
        if price_range > 0:
            # 가격 범위 중간값에 가까울수록 높은 점수
            mid_price = (price_min + price_max) / 2
            price_distance = abs(price - mid_price) / price_range
            price_score = 1.0 - min(price_distance, 1.0)
        else:
            price_score = 1.0 if price_min <= price <= price_max else 0.0
    else:
        price_score = 0.5  # 가격 범위가 없으면 중간 점수

    score += 0.2 * price_score

    return min(score, 1.0)
