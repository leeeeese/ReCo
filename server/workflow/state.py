"""
워크플로우 State 정의
"""

from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


# ==================== 페르소나 타입 정의 ====================

class PersonaType(str, Enum):
    """페르소나 타입 Enum"""
    TRUST_SAFETY_PRO = "trust_safety_pro"
    HIGH_QUALITY_NEW = "high_quality_new"
    FAST_SHIPPING_ONLINE = "fast_shipping_online"
    LOCAL_OFFLINE = "local_offline"
    NEGOTIATION_FRIENDLY = "negotiation_friendly"
    RESPONSIVE_KIND = "responsive_kind"
    POWER_SELLER = "power_seller"
    NICHE_SPECIALIST = "niche_specialist"
    BALANCED_LOW_ACTIVITY = "balanced_low_activity"
    HYBRID_TRADE = "hybrid_trade"
    PRICE_SENSITIVE = "price_sensitive"
    QUALITY_SEEKER = "quality_seeker"
    BALANCED = "balanced"


class PersonaVector(TypedDict):
    """페르소나 벡터 (선호도 값들)"""
    trust_safety: float
    quality_condition: float
    remote_transaction: float
    activity_responsiveness: float
    price_flexibility: float


# 페르소나 매칭 가중치
MATCHING_WEIGHTS = {
    "trust_safety": 0.25,
    "quality_condition": 0.20,
    "remote_transaction": 0.15,
    "activity_responsiveness": 0.20,
    "price_flexibility": 0.20,
}


# ==================== 워크플로우 State ====================

class RecommendationState(TypedDict):
    """추천 워크플로우 상태"""
    # 입력 데이터
    user_input: Dict[str, Any]
    search_query: Optional[Dict[str, Any]]
    persona_classification: Optional[Dict[str, Any]]

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
