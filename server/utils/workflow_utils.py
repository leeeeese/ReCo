"""
워크플로우 유틸리티 함수들
query_generator 등의 간단한 작업을 수행
"""

from typing import Dict, Any
from server.utils.tools import (
    extract_keywords,
    create_filters
)


def generate_search_query(user_input: Dict[str, Any]) -> Dict[str, Any]:
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
        prev_keywords = extract_keywords(
            " ".join(previous_queries[-2:]))  # 최근 2개만
        # 중복 제거하고 현재 쿼리에 없는 키워드만 추가
        # 상위 3개 키워드와 중복 체크
        new_keywords = [kw for kw in prev_keywords if kw not in keywords[:3]]
        if new_keywords:
            # 최대 2개만 추가
            enhanced_query = f"{original_query} {' '.join(new_keywords[:2])}"

    return {
        "original_query": original_query,
        "enhanced_query": enhanced_query,
        "keywords": keywords,
        "filters": filters,
        "context_queries": previous_queries[-3:] if previous_queries else []
    }
