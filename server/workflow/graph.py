"""
LangGraph 워크플로우 그래프 정의
"""

from langgraph.graph import StateGraph, END
from server.workflow.state import RecommendationState
from server.workflow.agents import (
    price_agent_node,
    safety_agent_node,
    orchestrator_agent_node,
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
        # user_input 복사하여 수정 (LangGraph LastValue 채널 중복 write 방지)
        user_input = dict(state["user_input"])
        
        # 페르소나 분류
        persona_classification = classify_persona(user_input)
        state["persona_classification"] = persona_classification
        
        # user_input에 persona_type 추가 (agents에서 사용하기 위해)
        user_input["persona_type"] = persona_classification.get("persona_type")
        state["user_input"] = user_input

        # 검색 쿼리 생성
        search_query = generate_search_query(
            user_input, persona_classification)
        state["search_query"] = search_query

        state["current_step"] = "initialized"
        state["completed_steps"].append("initialization")
        return state

    # 2개 서브에이전트
    workflow.add_node("price_agent", price_agent_node)
    workflow.add_node("safety_agent", safety_agent_node)

    # 추천 오케스트레이터 (2개 결과 종합 및 랭킹)
    workflow.add_node("orchestrator_agent", orchestrator_agent_node)

    # 엣지 추가
    workflow.set_entry_point("init")
    workflow.add_node("init", init_node)

    # 초기화 → 2개 서브에이전트 병렬 실행
    workflow.add_edge("init", "price_agent")
    workflow.add_edge("init", "safety_agent")

    # 2개 서브에이전트 완료 후 오케스트레이터
    workflow.add_edge("price_agent", "orchestrator_agent")
    workflow.add_edge("safety_agent", "orchestrator_agent")

    # 오케스트레이터 완료
    workflow.add_edge("orchestrator_agent", END)

    # 컴파일
    app = workflow.compile()

    return app
