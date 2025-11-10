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
    """검색 쿼리에서 키워드 추출"""
    keywords = re.findall(r'\b\w+\b', query.lower())
    stop_words = {'의', '을', '를', '이', '가', '은', '는', '에',
                  '에서', '로', '으로', '와', '과', '도', '만', '까지', '부터'}
    keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 1]
    return keywords


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
