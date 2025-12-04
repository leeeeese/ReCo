"""
Pydantic 스키마 정의
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import html


class UserInput(BaseModel):
    """사용자 입력"""
    search_query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="검색 쿼리 (1-500자)"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="대화 세션 ID (멀티 턴 대화용)"
    )
    trust_safety: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="신뢰도/안전성 선호도 (0-100)"
    )
    quality_condition: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="품질/상태 선호도 (0-100)"
    )
    remote_transaction: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="원격 거래 선호도 (0-100)"
    )
    activity_responsiveness: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="활동성/응답성 선호도 (0-100)"
    )
    price_flexibility: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="가격 유연성 선호도 (0-100)"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=100,
        description="카테고리"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=100,
        description="지역"
    )
    price_min: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="최소 가격 (0 이상)"
    )
    price_max: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="최대 가격 (0 이상)"
    )

    @field_validator('search_query')
    @classmethod
    def validate_search_query(cls, v: str) -> str:
        """검색 쿼리 검증 및 XSS 방지"""
        if not v or not v.strip():
            raise ValueError('검색 쿼리는 비어있을 수 없습니다.')
        # XSS 방지를 위해 HTML 이스케이프 (백엔드에서 기본적으로 처리)
        # 실제 렌더링은 프론트엔드에서 처리하므로 여기서는 길이와 기본 검증만 수행
        v = v.strip()
        if len(v) < 1:
            raise ValueError('검색 쿼리는 최소 1자 이상이어야 합니다.')
        if len(v) > 500:
            raise ValueError('검색 쿼리는 최대 500자까지 입력 가능합니다.')
        return v

    @field_validator('category', 'location')
    @classmethod
    def validate_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        """선택적 문자열 필드 검증"""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            # XSS 방지: HTML 특수문자 검증
            if '<' in v or '>' in v or '&' in v:
                # HTML 이스케이프 처리
                v = html.escape(v)
        return v

    @model_validator(mode='after')
    def validate_price_range(self) -> 'UserInput':
        """가격 범위 검증"""
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise ValueError('최소 가격은 최대 가격보다 작거나 같아야 합니다.')
        return self


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


class ConversationCreate(BaseModel):
    """대화 세션 생성"""
    user_id: Optional[str] = None


class ConversationResponse(BaseModel):
    """대화 세션 응답"""
    id: int
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class MessageCreate(BaseModel):
    """메시지 생성"""
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """메시지 응답"""
    id: int
    conversation_id: int
    session_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


class ConversationWithMessages(BaseModel):
    """대화 세션과 메시지 목록"""
    conversation: ConversationResponse
    messages: List[MessageResponse]
