"""
LangGraph 워크플로우 그래프 정의
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from server.workflow.state import RecommendationState
from server.workflow.agents import (
    persona_classifier_node,
    query_generator_node,
    price_agent_node,
    safety_agent_node,
    persona_matching_agent_node,
    final_matcher_node,
    ranker_node,
)


def recommendation_workflow() -> StateGraph:
    """
    추천 시스템 워크플로우 그래프 생성

    Returns:
        StateGraph: LangGraph 워크플로우 그래프
    """

    # State 그래프 생성
    workflow = StateGraph(RecommendationState)

    # 노드 추가
    workflow.add_node("persona_classifier", persona_classifier_node)
    workflow.add_node("query_generator", query_generator_node)

    # 3개 서브에이전트 (병렬 실행)
    workflow.add_node("price_agent", price_agent_node)
    workflow.add_node("safety_agent", safety_agent_node)
    workflow.add_node("persona_matching_agent", persona_matching_agent_node)

    # 최종 매칭 에이전트
    workflow.add_node("final_matcher", final_matcher_node)

    # 랭킹 및 SQL 생성
    workflow.add_node("ranker", ranker_node)

    # 엣지 추가
    workflow.set_entry_point("persona_classifier")

    # 페르소나 분류 → 검색 쿼리 생성
    workflow.add_edge("persona_classifier", "query_generator")

    # 검색 쿼리 생성 후 3개 서브에이전트 병렬 실행
    workflow.add_edge("query_generator", "price_agent")
    workflow.add_edge("query_generator", "safety_agent")
    workflow.add_edge("query_generator", "persona_matching_agent")

    # 3개 서브에이전트 완료 후 최종 매칭
    # Note: LangGraph의 add_edge는 순차적 실행이므로,
    #       병렬 실행을 원하면 조건부 엣지나 다른 방식을 사용해야 합니다.
    #       현재는 모든 노드가 완료될 때까지 대기하는 방식으로 구현 필요

    # 임시로 하나의 경로만 설정 (실제 병렬 실행은 LangGraph의 조건부 엣지 활용)
    # TODO: LangGraph의 병렬 실행 패턴 적용
    workflow.add_edge("price_agent", "final_matcher")
    workflow.add_edge("safety_agent", "final_matcher")
    workflow.add_edge("persona_matching_agent", "final_matcher")

    # 최종 매칭 → 랭킹
    workflow.add_edge("final_matcher", "ranker")
    workflow.add_edge("ranker", END)

    # 컴파일
    app = workflow.compile()

    return app
