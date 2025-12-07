"""
LangGraph 워크플로우 그래프 정의
"""

from langgraph.graph import StateGraph, END
from server.workflow.state import RecommendationState
from server.workflow.agents import (
    product_agent_node,
    reliability_agent_node,
    orchestrator_agent_node,
)
from server.utils.workflow_utils import generate_search_query


def recommendation_workflow() -> StateGraph:
    """
    추천 시스템 워크플로우 그래프 생성

    Returns:
        StateGraph: LangGraph 워크플로우 그래프
    """

    # State 그래프 생성
    workflow = StateGraph(RecommendationState)

    # 초기화 노드: 검색 쿼리 생성
    def init_node(state: RecommendationState) -> RecommendationState:
        """초기화: 검색 쿼리 생성"""
        # user_input 복사하여 수정 (LangGraph LastValue 채널 중복 write 방지)
        user_input = dict(state["user_input"])

        # 검색 쿼리 생성
        search_query = generate_search_query(user_input)

        # 새로운 state 반환 (LangGraph는 immutable state를 요구)
        # completed_steps는 add reducer를 사용하므로 리스트로 반환
        return {
            **state,
            "user_input": user_input,
            "search_query": search_query,
            "current_step": "initialized",
            "completed_steps": ["initialization"],  # add reducer가 기존 리스트와 병합
        }

    # 2개 서브에이전트
    workflow.add_node("product_agent", product_agent_node)
    workflow.add_node("reliability_agent", reliability_agent_node)

    # 추천 오케스트레이터 (2개 결과 종합 및 랭킹)
    workflow.add_node("orchestrator_agent", orchestrator_agent_node)

    # 엣지 추가
    workflow.set_entry_point("init")
    workflow.add_node("init", init_node)

    # 초기화 → 2개 서브에이전트 병렬 실행
    workflow.add_edge("init", "product_agent")
    workflow.add_edge("init", "reliability_agent")

    # 2개 서브에이전트 완료 후 오케스트레이터
    workflow.add_edge("product_agent", "orchestrator_agent")
    workflow.add_edge("reliability_agent", "orchestrator_agent")

    # 오케스트레이터 완료
    workflow.add_edge("orchestrator_agent", END)

    # 컴파일
    app = workflow.compile()

    return app
