"""
워크플로우 유틸리티 함수들
persona_classifier, query_generator 등의 간단한 작업을 수행
"""

from typing import Dict, Any
from server.utils.tools import (
    normalize_slider_inputs,
    extract_keywords,
    create_filters
)
from server.workflow.state import PersonaType


def classify_persona(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """페르소나 분류 (이전 대화 컨텍스트 활용하여 선호도 벡터 생성)"""
    # 이전 대화에서 선호도 정보 추출
    conversation_context = user_input.get("conversation_context", {})
    previous_messages = conversation_context.get("previous_messages", [])
    
    # 이전 대화에서 선호도 정보 누적
    accumulated_prefs = {
        "trust_safety": [],
        "quality_condition": [],
        "remote_transaction": [],
        "activity_responsiveness": [],
        "price_flexibility": [],
    }
    
    for msg in previous_messages:
        if msg.get("role") == "user" and msg.get("metadata"):
            user_input_prev = msg["metadata"].get("user_input", {})
            for key in accumulated_prefs.keys():
                if key in user_input_prev:
                    accumulated_prefs[key].append(user_input_prev[key])
    
    # 현재 입력과 이전 대화의 평균값 사용
    prefs = {}
    for key in accumulated_prefs.keys():
        values = accumulated_prefs[key]
        current_value = user_input.get(key, 50.0)
        if values:
            # 이전 값들의 평균과 현재 값을 가중 평균 (최근 대화에 더 가중치)
            avg_prev = sum(values) / len(values)
            prefs[key] = (avg_prev * 0.3 + current_value * 0.7)
        else:
            prefs[key] = current_value
    
    vector = normalize_slider_inputs(prefs)
    
    # user_input에 persona_type 추가 (agents에서 사용하기 위해)
    # 벡터 기반으로 간단한 페르소나 타입 추정
    persona_type: PersonaType
    if prefs.get("trust_safety", 50) > 70:
        persona_type = PersonaType.TRUST_SAFETY_PRO
    elif prefs.get("price_flexibility", 50) > 70:
        persona_type = PersonaType.PRICE_SENSITIVE
    elif prefs.get("quality_condition", 50) > 70:
        persona_type = PersonaType.QUALITY_SEEKER
    else:
        persona_type = PersonaType.BALANCED
    
    return {
        "persona_type": persona_type.value if isinstance(persona_type, PersonaType) else str(persona_type),
        "confidence": 0.5,  # 간단한 추정이므로 낮은 신뢰도
        "vector": vector,
        "matched_prototype": None,
        "reason": f"이전 {len(previous_messages)}개 대화를 참고하여 선호도 분석",
    }


def generate_search_query(user_input: Dict[str, Any], persona_classification: Dict[str, Any]) -> Dict[str, Any]:
    """검색 쿼리 생성 (이전 대화 컨텍스트 활용)"""
    original_query = user_input.get("search_query", "")
    
    # 이전 대화에서 검색 쿼리 추출
    conversation_context = user_input.get("conversation_context", {})
    previous_messages = conversation_context.get("previous_messages", [])
    
    # 이전 대화의 검색 쿼리들을 키워드로 활용
    previous_queries = []
    for msg in previous_messages:
        if msg.get("role") == "user":
            prev_query = msg.get("content", "")
            if prev_query and prev_query != original_query:
                previous_queries.append(prev_query)
    
    # 현재 쿼리와 이전 쿼리들을 결합하여 키워드 추출
    all_queries = [original_query] + previous_queries[-3:]  # 최근 3개만 사용
    combined_text = " ".join(all_queries)
    
    keywords = extract_keywords(combined_text)
    
    # 필터 정보 추출
    filters = create_filters(user_input)
    
    # enhanced_query: 이전 대화의 키워드를 포함하여 향상된 쿼리 생성
    enhanced_query = original_query
    if previous_queries:
        # 이전 대화의 주요 키워드만 추출하여 추가
        prev_keywords = extract_keywords(" ".join(previous_queries[-2:]))  # 최근 2개만
        # 중복 제거하고 현재 쿼리에 없는 키워드만 추가
        new_keywords = [kw for kw in prev_keywords if kw not in keywords[:3]]  # 상위 3개 키워드와 중복 체크
        if new_keywords:
            enhanced_query = f"{original_query} {' '.join(new_keywords[:2])}"  # 최대 2개만 추가

    return {
        "original_query": original_query,
        "enhanced_query": enhanced_query,
        "keywords": keywords,
        "filters": filters,
        "context_queries": previous_queries[-3:] if previous_queries else []
    }
