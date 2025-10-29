"""
Pydantic 스키마 정의
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class UserInput(BaseModel):
    """사용자 입력"""
    search_query: str
    trust_safety: float = 50.0
    quality_condition: float = 50.0
    remote_transaction: float = 50.0
    activity_responsiveness: float = 50.0
    price_flexibility: float = 50.0
    category: Optional[str] = None
    location: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None


class RecommendationResult(BaseModel):
    """추천 결과"""
    product_id: int
    seller_id: int
    title: str
    price: float
    final_score: float
    ranking_factors: Dict[str, Any]
    seller_name: str
    category: str
    condition: str
    location: str


class HistoryRequest(BaseModel):
    """히스토리 저장 요청"""
    user_input: UserInput
    search_query: str
    persona_type: str
    results: List[RecommendationResult]


class HistoryResponse(BaseModel):
    """히스토리 조회 응답"""
    id: int
    user_input: Dict[str, Any]
    search_query: str
    persona_type: str
    results: List[Dict[str, Any]]
    created_at: datetime
