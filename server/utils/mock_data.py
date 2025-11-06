"""
테스트용 목업 데이터
각 Agent 테스트에 사용할 수 있는 더미 데이터
"""

from typing import List, Dict, Any
from server.workflow.state import PersonaType, PersonaVector


def get_mock_user_input() -> Dict[str, Any]:
    """기본 사용자 입력 목업 데이터"""
    return {
        "search_query": "아이폰 14 프로",
        "trust_safety": 70.0,
        "quality_condition": 80.0,
        "remote_transaction": 60.0,
        "activity_responsiveness": 75.0,
        "price_flexibility": 50.0,
        "category": "스마트폰",
        "location": "서울",
        "price_min": 500000,
        "price_max": 1500000
    }


def get_mock_sellers_with_products() -> List[Dict[str, Any]]:
    """판매자 + 상품 목업 데이터"""
    sellers = []

    for i in range(1, 6):
        seller = {
            "seller_id": i,
            "seller_name": f"판매자{i}",
            "avg_rating": 4.0 + (i % 5) * 0.2,
            "total_sales": 100 + i * 50,
            "response_time_hours": 12.0 - i * 2,
            "payment_methods": ["안전결제", "직거래"] if i % 2 == 0 else ["직거래"],
            "safety_features": ["인증판매자", "보증서비스"] if i % 2 == 0 else ["인증판매자"],
            "review_count": 50 + i * 10,
            "trust_score": 0.7 + (i % 3) * 0.1,
            "persona_vector": PersonaVector(
                trust_safety=50.0 + i * 5,
                quality_condition=50.0 + i * 5,
                remote_transaction=50.0 + i * 5,
                activity_responsiveness=50.0 + i * 5,
                price_flexibility=50.0 + i * 5
            ),
            "persona_type": "hybrid_trade" if i % 2 == 0 else "trust_safety_pro",
            "characteristics": ["활발한", "신뢰도높음"] if i % 2 == 0 else ["신중한", "안전중시"],
            "products": [
                {
                    "product_id": i * 10 + j,
                    "seller_id": i,
                    "title": f"아이폰 14 프로 {j+1}",
                    "price": 1000000 + j * 100000,
                    "category": "스마트폰",
                    "condition": "새상품" if j == 0 else ("거의새것" if j == 1 else "중고"),
                    "location": "서울",
                    "description": f"테스트용 아이폰 14 프로 상품 {j+1}번입니다. 상태 좋습니다.",
                    "view_count": 100 + j * 50,
                    "like_count": 10 + j * 5
                }
                for j in range(3)
            ]
        }
        sellers.append(seller)

    return sellers


def get_mock_sellers_with_persona() -> List[Dict[str, Any]]:
    """페르소나 매칭용 판매자 목업 데이터"""
    sellers = []

    persona_types = [
        "trust_safety_pro",
        "high_quality_new",
        "fast_shipping_online",
        "local_offline",
        "hybrid_trade"
    ]

    for i in range(1, 6):
        seller = {
            "seller_id": i,
            "seller_name": f"페르소나 판매자{i}",
            "persona_vector": PersonaVector(
                trust_safety=60.0 + i * 6,
                quality_condition=70.0 + i * 4,
                remote_transaction=50.0 + i * 5,
                activity_responsiveness=65.0 + i * 5,
                price_flexibility=55.0 + i * 3
            ),
            "persona_type": persona_types[i % len(persona_types)],
            "characteristics": [
                "신뢰도높음",
                "빠른응답",
                "안전결제" if i % 2 == 0 else "직거래선호"
            ],
            "products": [
                {
                    "product_id": i * 10 + j,
                    "title": f"상품 {j+1}",
                    "price": 500000 + j * 50000,
                    "category": "전자제품",
                    "condition": "중고",
                    "location": "서울",
                    "view_count": 50 + j * 20,
                    "like_count": 5 + j * 2
                }
                for j in range(2)
            ]
        }
        sellers.append(seller)

    return sellers


def get_mock_persona_classification() -> Dict[str, Any]:
    """페르소나 분류 결과 목업 데이터"""
    from server.workflow.state import PERSONA_PROTOTYPES

    return {
        "persona_type": PersonaType.TRUST_SAFETY_PRO,
        "confidence": 0.85,
        "vector": PersonaVector(
            trust_safety=90.0,
            quality_condition=75.0,
            remote_transaction=70.0,
            activity_responsiveness=85.0,
            price_flexibility=50.0
        ),
        "matched_prototype": PERSONA_PROTOTYPES[PersonaType.TRUST_SAFETY_PRO]["vector"],
        "reason": "LLM 기반 판단",
        "llm_reasoning": "사용자가 높은 신뢰도와 안전거래를 중시하는 것으로 판단됩니다."
    }


def get_mock_search_query() -> Dict[str, Any]:
    """검색 쿼리 목업 데이터"""
    return {
        "original_query": "아이폰 14 프로",
        "enhanced_query": "아이폰 14 프로 안전결제 신뢰도높은",
        "keywords": ["아이폰", "14", "프로"],
        "filters": {
            "category": "스마트폰",
            "location": "서울",
            "price_min": 500000,
            "price_max": 1500000
        }
    }


def get_mock_state() -> Dict[str, Any]:
    """전체 RecommendationState 목업 데이터"""
    return {
        "user_input": get_mock_user_input(),
        "search_query": get_mock_search_query(),
        "persona_classification": get_mock_persona_classification(),
        "price_agent_recommendations": None,
        "safety_agent_recommendations": None,
        "persona_matching_recommendations": None,
        "final_seller_recommendations": None,
        "seller_item_scores": None,
        "final_item_scores": None,
        "sql_query": None,
        "ranking_explanation": None,
        "current_step": "start",
        "completed_steps": [],
        "error_message": None,
        "execution_start_time": None,
        "execution_time": None
    }


def get_mock_price_agent_result() -> Dict[str, Any]:
    """가격 에이전트 결과 목업 데이터"""
    return {
        "recommended_sellers": [
            {
                "seller_id": 1,
                "seller_name": "판매자1",
                "price_score": 0.85,
                "price_reasoning": "시세 대비 합리적인 가격",
                "recommended_price_range": {"min": 800000, "max": 1200000},
                "products": get_mock_sellers_with_products()[0]["products"]
            }
        ],
        "market_analysis": {
            "1": {
                "current_price": 1000000,
                "market_avg": 950000,
                "market_median": 920000,
                "market_range": {"min": 800000, "max": 1100000},
                "sample_count": 10
            }
        },
        "reasoning": "가격 관점에서 합리적인 판매자 추천 완료"
    }


def get_mock_safety_agent_result() -> Dict[str, Any]:
    """안전거래 에이전트 결과 목업 데이터"""
    return {
        "recommended_sellers": [
            {
                "seller_id": 2,
                "seller_name": "판매자2",
                "safety_score": 0.90,
                "safety_reasoning": "높은 신뢰도와 안전결제 옵션",
                "safety_features_matched": ["인증판매자", "보증서비스"],
                "trust_level": "high",
                "products": get_mock_sellers_with_products()[1]["products"]
            }
        ],
        "reasoning": "안전거래 관점에서 신뢰할 수 있는 판매자 추천 완료"
    }


def get_mock_persona_matching_result() -> Dict[str, Any]:
    """페르소나 매칭 에이전트 결과 목업 데이터"""
    return {
        "recommended_sellers": [
            {
                "seller_id": 3,
                "seller_name": "판매자3",
                "persona_match_score": 0.88,
                "persona_reasoning": "사용자와 높은 페르소나 호환성",
                "matched_characteristics": ["신뢰도높음", "빠른응답"],
                "compatibility_level": "high",
                "products": get_mock_sellers_with_products()[2]["products"]
            }
        ],
        "reasoning": "페르소나 관점에서 가장 잘 어울리는 판매자 추천 완료"
    }
