"""
워크플로우 State 정의
"""

from typing import TypedDict, List, Dict, Any, Optional


class RecommendationState(TypedDict):
    """추천 워크플로우 상태"""
    # 입력 데이터
    user_input: Dict[str, Any]
    search_query: Optional[Dict[str, Any]]

    # 서브에이전트 결과
    price_agent_recommendations: Optional[Dict[str, Any]]
    safety_agent_recommendations: Optional[Dict[str, Any]]

    # 최종 결과
    final_seller_recommendations: Optional[List[Dict[str, Any]]]
    final_item_scores: Optional[List[Dict[str, Any]]]
    ranking_explanation: Optional[str]

    # 워크플로우 상태
    current_step: str
    completed_steps: List[str]
    error_message: Optional[str]
    execution_start_time: Optional[float]
    execution_time: Optional[float]
