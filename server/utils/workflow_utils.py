"""
워크플로우 유틸리티 함수들
persona_classifier, query_generator 등의 간단한 작업을 수행
"""

from typing import Dict, Any
from server.workflow.state import RecommendationState
from server.utils.tools import (
    normalize_slider_inputs,
    extract_keywords,
    create_filters
)


def classify_persona(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """페르소나 분류 로직 제거"""
    vector = normalize_slider_inputs({
        "trust_safety": user_input.get("trust_safety", 50.0),
        "quality_condition": user_input.get("quality_condition", 50.0),
        "remote_transaction": user_input.get("remote_transaction", 50.0),
        "activity_responsiveness": user_input.get("activity_responsiveness", 50.0),
        "price_flexibility": user_input.get("price_flexibility", 50.0),
    })
    return {
        "persona_type": None,
        "confidence": 0.0,
        "vector": vector,
        "matched_prototype": None,
        "reason": "Persona classification disabled",
        "llm_reasoning": ""
    }


def generate_search_query(user_input: Dict[str, Any], persona_classification: Dict[str, Any]) -> Dict[str, Any]:
    """검색 쿼리 생성"""
    original_query = user_input.get("search_query", "")
    persona_type = persona_classification.get("persona_type")

    keywords = extract_keywords(original_query)
    filters = create_filters(user_input)

    return {
        "original_query": original_query,
        "enhanced_query": original_query,
        "keywords": keywords,
        "filters": filters
    }
