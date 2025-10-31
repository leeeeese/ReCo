"""
검색 쿼리 생성 Agent
페르소나와 사용자 입력을 바탕으로 검색 쿼리를 생성합니다.
"""

from typing import Dict, Any
from server.workflow.state import RecommendationState
from server.utils.tools import extract_keywords, enhance_query_for_persona, create_filters


def query_generator_node(state: RecommendationState) -> RecommendationState:
    """검색 쿼리 생성 노드"""
    try:
        user_input = state["user_input"]
        persona_classification = state.get("persona_classification")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        original_query = user_input["search_query"]
        persona_type = persona_classification["persona_type"]

        # 키워드 추출
        keywords = extract_keywords(original_query)

        # 페르소나에 맞게 쿼리 향상
        enhanced_query = enhance_query_for_persona(
            original_query, persona_type)

        # 필터 조건 생성
        filters = create_filters(user_input)

        # 결과를 상태에 저장
        state["search_query"] = {
            "original_query": original_query,
            "enhanced_query": enhanced_query,
            "keywords": keywords,
            "filters": filters
        }

        state["current_step"] = "query_generated"
        state["completed_steps"].append("query_generation")

        print(f"검색 쿼리 생성 완료: {enhanced_query}")
        print(f"추출된 키워드: {keywords}")
        print(f"필터 조건: {filters}")

    except Exception as e:
        state["error_message"] = f"검색 쿼리 생성 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"검색 쿼리 생성 오류: {e}")

    return state
