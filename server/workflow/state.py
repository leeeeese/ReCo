"""
워크플로우 State 정의
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from enum import Enum


class PersonaType(str, Enum):
    """페르소나 타입"""
    TRUST_SAFETY_PRO = "trust_safety_pro"
    HIGH_QUALITY_NEW = "high_quality_new"
    FAST_SHIPPING_ONLINE = "fast_shipping_online"
    LOCAL_OFFLINE = "local_offline"
    NEGOTIATION_FRIENDLY = "negotiation_friendly"
    POWER_SELLER = "power_seller"
    RESPONSIVE_KIND = "responsive_kind"
    NICHE_SPECIALIST = "niche_specialist"
    BALANCED_LOW_ACTIVITY = "balanced_low_activity"
    HYBRID_TRADE = "hybrid_trade"


class PersonaVector(TypedDict):
    """페르소나 벡터"""
    trust_safety: float
    quality_condition: float
    remote_transaction: float
    activity_responsiveness: float
    price_flexibility: float


# 페르소나 프로토타입
PERSONA_PROTOTYPES = {
    PersonaType.TRUST_SAFETY_PRO: {
        "vector": PersonaVector(
            trust_safety=90,
            quality_condition=75,
            remote_transaction=70,
            activity_responsiveness=85,
            price_flexibility=50
        )
    },
    PersonaType.HIGH_QUALITY_NEW: {
        "vector": PersonaVector(
            trust_safety=75,
            quality_condition=95,
            remote_transaction=60,
            activity_responsiveness=70,
            price_flexibility=40
        )
    },
    # ... 나머지 페르소나 정의
}


# 매칭 가중치
MATCHING_WEIGHTS = {
    "trust_safety": 0.25,
    "quality_condition": 0.20,
    "remote_transaction": 0.15,
    "activity_responsiveness": 0.20,
    "price_flexibility": 0.20,
}


class RecommendationState(TypedDict):
    """추천 워크플로우 상태"""
    user_input: Dict[str, Any]
    search_query: Optional[Dict[str, Any]]
    persona_classification: Optional[Dict[str, Any]]
    seller_item_scores: Optional[List[Dict[str, Any]]]
    final_item_scores: Optional[List[Dict[str, Any]]]
    sql_query: Optional[Dict[str, Any]]
    ranking_explanation: Optional[str]
    current_step: str
    completed_steps: List[str]
    error_message: Optional[str]
    execution_start_time: Optional[float]
    execution_time: Optional[float]
