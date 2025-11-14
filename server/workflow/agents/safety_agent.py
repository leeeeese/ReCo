"""
안전거래 에이전트
LLM 기반으로 거래 방식, 결제 안전도, 판매자 신뢰도를 종합하여
사용자와 가장 잘 어울리는 안전한 판매자를 추천
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent


class SafetyAgent:
    """안전거래 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("safety_agent")

    def recommend_sellers_by_safety(self,
                                    user_input: Dict[str, Any],
                                    sellers_with_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        안전거래 관점에서 판매자 추천

        Args:
            user_input: 사용자 입력 (안전거래 선호도 포함)
            sellers_with_products: 판매자와 상품 정보

        Returns:
            안전거래 점수와 함께 판매자 리스트
        """
        # 판매자 안전거래 정보 구성
        seller_safety_data = []
        for seller in sellers_with_products:
            seller_safety_data.append({
                "seller_id": seller.get("seller_id"),
                "seller_name": seller.get("seller_name"),
                "avg_rating": seller.get("avg_rating", 0),
                "total_sales": seller.get("total_sales", 0),
                "response_time_hours": seller.get("response_time_hours", 24),
                "payment_methods": seller.get("payment_methods", []),
                "safety_features": seller.get("safety_features", []),
                "review_count": seller.get("review_count", 0),
                "trust_score": seller.get("trust_score", 0)
            })

        # LLM에게 판단 요청
        context = {
            "user_trust_safety_preference": user_input.get("trust_safety", 50),
            "user_remote_transaction_preference": user_input.get("remote_transaction", 50),
            "sellers": seller_safety_data[:20],  # 상위 20개만 분석
            "user_persona": user_input.get("persona_type")
        }

        decision = self.llm_agent.decide(
            context=context,
            decision_task="다음 판매자들 중에서 사용자가 안전하게 거래할 수 있는 판매자를 추천해주세요. "
            "결제 안전도, 판매자 신뢰도, 거래 방식 등 안전거래에 영향을 미치는 복합적인 요소를 종합 고려하세요.",
            format="json"
        )

        # LLM 결과를 기반으로 판매자 점수 계산
        recommended_sellers = []
        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_score = decision.get(
                "recommended_sellers", {}).get(str(seller_id), {})

            recommended_sellers.append({
                "seller_id": seller_id,
                "seller_name": seller.get("seller_name"),
                "safety_score": seller_score.get("score", 0.5),
                "safety_reasoning": seller_score.get("reasoning", ""),
                "safety_features_matched": seller_score.get("matched_features", []),
                "trust_level": seller_score.get("trust_level", "medium"),
                "products": seller.get("products", [])
            })

        # 안전거래 점수 기준 정렬
        recommended_sellers.sort(key=lambda x: x["safety_score"], reverse=True)

        return recommended_sellers


def safety_agent_node(state: RecommendationState) -> RecommendationState:
    """안전거래 에이전트 노드"""
    try:
        user_input = state["user_input"]

        # 안전거래 에이전트 실행
        agent = SafetyAgent()

        # DB에서 조회 (price_agent와 동일한 로직)
        from server.db.product_service import get_sellers_with_products, search_products_by_keywords

        search_query = state.get("search_query", {})

        try:
            # 검색 쿼리 파싱
            search_query_obj = search_query.get(
                "original_query") or search_query.get("enhanced_query", "")
            keywords = search_query.get("keywords", [])

            # 사용자 입력에서 필터 추출
            category = user_input.get("category")
            price_min = user_input.get("price_min")
            price_max = user_input.get("price_max")

            # DB에서 조회
            if keywords:
                sellers_with_products = search_products_by_keywords(
                    keywords=keywords,
                    category=category,
                    price_min=price_min,
                    price_max=price_max,
                    limit=50
                )
            else:
                sellers_with_products = get_sellers_with_products(
                    search_query=search_query_obj if search_query_obj else None,
                    category=category,
                    price_min=price_min,
                    price_max=price_max,
                    limit=50
                )

            if not sellers_with_products:
                raise ValueError("DB에서 상품 데이터를 찾을 수 없습니다.")

            print(f"DB에서 {len(sellers_with_products)}개 판매자 조회 완료 (안전거래 분석용)")
        except Exception as e:
            raise ValueError(f"안전거래 에이전트 데이터 조회 실패: {e}")

        # 안전거래 관점에서 판매자 추천
        safety_recommendations = agent.recommend_sellers_by_safety(
            user_input,
            sellers_with_products
        )

        # 결과를 상태에 저장
        state["safety_agent_recommendations"] = {
            "recommended_sellers": safety_recommendations,
            "reasoning": "안전거래 관점에서 신뢰할 수 있는 판매자 추천 완료"
        }
        state["current_step"] = "safety_analyzed"
        state["completed_steps"].append("safety_analysis")

        print(f"안전거래 에이전트 분석 완료: {len(safety_recommendations)}개 판매자 추천")

    except Exception as e:
        state["error_message"] = f"안전거래 에이전트 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"안전거래 에이전트 오류: {e}")

    return state
