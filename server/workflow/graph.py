"""
LangGraph 워크플로우 그래프 정의
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from server.workflow.state import RecommendationState
from server.workflow.agents import (
    persona_classifier_node,
    query_generator_node,
    product_matching_node,
    ranker_node,
    router_node,
    should_continue,
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
    workflow.add_node("product_matching", product_matching_node)
    workflow.add_node("ranker", ranker_node)
    workflow.add_node("router", router_node)
    workflow.add_node("sql_generator", lambda state: state)  # TODO: 구현

    # 엣지 추가
    workflow.set_entry_point("persona_classifier")

    workflow.add_edge("persona_classifier", "query_generator")
    workflow.add_edge("query_generator", "product_matching")
    workflow.add_edge("product_matching", "ranker")
    workflow.add_edge("ranker", "router")

    # 조건부 엣지
    workflow.add_conditional_edges(
        "router",
        should_continue,
        {
            "continue": "sql_generator",
            "end": END
        }
    )

    # 컴파일
    app = workflow.compile()

    return app
