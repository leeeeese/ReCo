"""
LangGraph 워크플로우 그래프 정의
"""

from langgraph.graph import StateGraph, END
from server.workflow.state import RecommendationState
from server.workflow.agents import (
    price_agent_node,
    safety_agent_node,
    recommendation_orchestrator_node,
)
from server.utils.workflow_utils import classify_persona, generate_search_query


def recommendation_workflow() -> StateGraph:
    """
    추천 시스템 워크플로우 그래프 생성

    Returns:
        StateGraph: LangGraph 워크플로우 그래프
    """

    # State 그래프 생성
    workflow = StateGraph(RecommendationState)

    # 초기화 노드: 페르소나 분류 및 쿼리 생성
    def init_node(state: RecommendationState) -> RecommendationState:
        """초기화: 페르소나 분류 및 검색 쿼리 생성"""
        # 페르소나 분류
        persona_classification = classify_persona(state["user_input"])
        state["persona_classification"] = persona_classification

        # 검색 쿼리 생성
        search_query = generate_search_query(
            state["user_input"], persona_classification)
        state["search_query"] = search_query

        state["current_step"] = "initialized"
        state["completed_steps"].append("initialization")
        return state

    # 2개 서브에이전트
    workflow.add_node("price_agent", price_agent_node)
    workflow.add_node("safety_agent", safety_agent_node)

    # 추천 오케스트레이터 (2개 결과 종합 및 랭킹)
    workflow.add_node("recommendation_orchestrator",
                      recommendation_orchestrator_node)

    # 엣지 추가
    workflow.set_entry_point("init")
    workflow.add_node("init", init_node)

    # 초기화 → 2개 서브에이전트 병렬 실행
    workflow.add_edge("init", "price_agent")
    workflow.add_edge("init", "safety_agent")

    # 2개 서브에이전트 완료 후 오케스트레이터
    workflow.add_edge("price_agent", "recommendation_orchestrator")
    workflow.add_edge("safety_agent", "recommendation_orchestrator")

    # 오케스트레이터 완료
    workflow.add_edge("recommendation_orchestrator", END)

    # 컴파일
    app = workflow.compile()

    return app
