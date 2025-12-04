"""
공통 유틸리티 Tools
Agent 노드에서 사용할 수 있는 공통 함수들
"""

import re
import numpy as np
from typing import List, Dict, Any, Optional
from server.workflow.state import PersonaVector, PersonaType, MATCHING_WEIGHTS


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


def enhance_query_for_persona(original_query: str, persona_type: PersonaType) -> str:
    """페르소나에 맞게 쿼리 향상"""
    persona_enhancements = {
        PersonaType.TRUST_SAFETY_PRO: "안전결제 신뢰도높은",
        PersonaType.HIGH_QUALITY_NEW: "새상품 미개봉 상태좋은",
        PersonaType.FAST_SHIPPING_ONLINE: "빠른배송 택배",
        PersonaType.LOCAL_OFFLINE: "직거래 동네",
        PersonaType.NEGOTIATION_FRIENDLY: "흥정 협상가능",
        PersonaType.RESPONSIVE_KIND: "친절 응답빠른",
        PersonaType.POWER_SELLER: "활발한 판매자",
        PersonaType.NICHE_SPECIALIST: "전문가 전문상품",
        PersonaType.BALANCED_LOW_ACTIVITY: "신중한 판매자",
        PersonaType.HYBRID_TRADE: "온오프라인"
    }
    enhancement = persona_enhancements.get(persona_type, "")
    return f"{original_query} {enhancement}" if enhancement else original_query


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

def normalize_slider_inputs(user_prefs: Dict[str, Any]) -> PersonaVector:
    """슬라이더 입력을 정규화하여 페르소나 벡터 생성"""
    normalized_vector = {}
    for key in ["trust_safety", "quality_condition", "remote_transaction",
                "activity_responsiveness", "price_flexibility"]:
        value = user_prefs.get(key, 50.0)
        normalized_vector[key] = max(0.0, min(100.0, float(value)))
    return PersonaVector(**normalized_vector)


def calculate_l2_distance(vector1: PersonaVector, vector2: PersonaVector) -> float:
    """두 벡터 간의 L2 거리 계산"""
    keys = ["trust_safety", "quality_condition", "remote_transaction",
            "activity_responsiveness", "price_flexibility"]
    return np.sqrt(sum((vector1[key] - vector2[key]) ** 2 for key in keys))


def calculate_persona_match_score(
    user_vector: PersonaVector,
    seller_vector: PersonaVector
) -> float:
    """사용자와 판매자 간의 페르소나 매칭 점수 계산"""
    score = 0.0
    total_weight = 0.0

    for key, weight in MATCHING_WEIGHTS.items():
        if key in user_vector and key in seller_vector:
            diff = abs(user_vector[key] - seller_vector[key])
            match_score = weight * (1 - diff / 100)
            score += match_score
            total_weight += weight

    return score / total_weight if total_weight > 0 else 0.0


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
    persona_classification: Optional[Dict[str, Any]] = None,
    min_products_per_seller: int = 5,
    max_products_per_seller: int = 10
) -> List[Dict[str, Any]]:
    """
    추천된 판매자들에게 상품을 매칭하는 룰베이스 함수
    
    Args:
        recommended_sellers: 추천된 판매자 리스트 (seller_id 포함)
        user_input: 사용자 입력 (search_query, price_min, price_max 등)
        persona_classification: 페르소나 분류 결과
        min_products_per_seller: 판매자당 희망 최소 상품 수 (기본값: 5, 실제 개수보다 적어도 반환)
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
    seller_ids = [seller.get("seller_id") for seller in recommended_sellers if seller.get("seller_id")]
    
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
        filtered_products = _filter_products_by_user_input(products, user_input)
        
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
                user_input, 
                persona_classification
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
        
        # 실제 상품 개수에 맞춰서 선택 (1개면 1개, 3개면 3개, 10개 이상이면 최대 10개)
        # min_products_per_seller는 "희망 최소 개수"이지 "필수 최소 개수"가 아님
        actual_count = len(scored_products)
        num_products = min(actual_count, max_products_per_seller)
        selected_products = scored_products[:num_products]
        
        # 상품 개수가 희망 최소 개수보다 적은 경우 로깅
        if actual_count < min_products_per_seller:
            logger.info(
                "판매자 상품 개수가 희망 최소 개수보다 적음",
                extra={
                    "seller_id": seller_id,
                    "seller_name": seller.get("seller_name"),
                    "actual_count": actual_count,
                    "min_products_per_seller": min_products_per_seller
                }
            )
        
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
        
        # 검색어 필터 (제목/설명에 포함)
        # 키워드가 여러 개일 경우 모든 키워드가 포함되어야 함 (AND 조건)
        if search_query:
            # 검색어를 키워드로 분리
            keywords = [kw.strip().lower() for kw in search_query.split() if kw.strip()]
            if keywords:
                title = product.get("title", "").lower()
                description = product.get("description", "").lower()
                # 모든 키워드가 제목 또는 설명에 포함되어야 함
                all_keywords_match = all(
                    keyword in title or keyword in description
                    for keyword in keywords
                )
                if not all_keywords_match:
                    continue
        
        filtered.append(product)
    
    return filtered


def _calculate_product_match_score(
    product: Dict[str, Any],
    seller: Dict[str, Any],
    user_input: Dict[str, Any],
    persona_classification: Optional[Dict[str, Any]] = None
) -> float:
    """상품 매칭 점수 계산 (룰베이스)"""
    score = 0.0
    
    # 1. 판매자 최종 점수 (40%)
    seller_score = seller.get("final_score", 0.0)
    score += 0.4 * seller_score
    
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
    
    # 4. 페르소나 기반 보너스 (10%)
    if persona_classification:
        persona_type = persona_classification.get("persona_type", "")
        # 페르소나에 맞는 상품 조건 체크
        if persona_type == "quality_seeker":
            condition = product.get("condition", "")
            if condition in ["새상품", "거의새것"]:
                score += 0.1
        elif persona_type == "price_sensitive":
            # 가격이 낮을수록 보너스
            if price_min and price_max:
                price_ratio = (price - price_min) / (price_max - price_min) if price_max > price_min else 0.5
                score += 0.1 * (1.0 - price_ratio)
    
    return min(score, 1.0)