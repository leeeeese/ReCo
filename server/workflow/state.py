"""
워크플로우 State 정의
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add


# ==================== 워크플로우 State ====================

class RecommendationState(TypedDict, total=False):
    """추천 워크플로우 상태 - total=False로 모든 필드가 선택적"""
    # 입력 데이터
    user_input: Dict[str, Any]
    search_query: Optional[Dict[str, Any]]

    # 서브에이전트 결과
    product_agent_recommendations: Optional[Dict[str, Any]]
    reliability_agent_recommendations: Optional[Dict[str, Any]]

    # 최종 결과
    final_seller_recommendations: Optional[List[Dict[str, Any]]]
    final_item_scores: Optional[List[Dict[str, Any]]]
    ranking_explanation: Optional[str]

    # 워크플로우 상태
    current_step: str
    # LangGraph add reducer 사용 (리스트 병합)
    completed_steps: Annotated[List[str], add]
    error_message: Optional[str]
    execution_start_time: Optional[float]
    execution_time: Optional[float]
