"""
가격 에이전트
LLM 기반으로 실시간 시세와 상품 데이터를 종합 분석하여 
사용자가 합리적이라고 생각할 만한 가격 범위의 상품을 판단
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.workflow.agents.price_updater import PriceUpdater, joongna_search_prices
from server.db.product_service import get_sellers_with_products, search_products_by_keywords


class PriceAgent:
    """가격 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("price_agent")
        # PriceUpdater는 필요시 인스턴스 생성

    def analyze_price_reasonableness(self,
                                     user_input: Dict[str, Any],
                                     products: List[Dict[str, Any]],
                                     market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        LLM 기반으로 가격 합리성 분석

        Args:
            user_input: 사용자 입력 (가격 선호도 포함)
            products: 후보 상품 리스트
            market_data: 실시간 시세 데이터

        Returns:
            가격 관점에서 합리적인 상품과 판매자 추천 결과
        """
        # 실시간 시세 수집
        market_prices = self._collect_market_data(products)

        # LLM에게 판단 요청
        context = {
            "user_price_preference": user_input.get("price_min", 0),
            "user_price_max": user_input.get("price_max", float('inf')),
            "products": products[:10],  # LLM 토큰 절약을 위해 상위 10개만
            "market_prices": market_prices,
            "user_persona": user_input.get("persona_type")
        }

        decision = self.llm_agent.decide(
            context=context,
            decision_task="다음 상품들 중에서 사용자가 합리적이라고 판단할 만한 가격의 상품과 판매자를 추천해주세요. "
            "실시간 시세, 상품 상태, 거래 방식 등 복합적인 요소를 종합 고려하세요.",
            format="json"
        )

        return {
            "recommended_sellers_by_price": decision.get("recommended_sellers", []),
            "price_reasoning": decision.get("reasoning", ""),
            "market_analysis": market_prices,
            "recommendation_score": decision.get("confidence", 0.5)
        }

    def _collect_market_data(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """실시간 시세 데이터 수집"""
        market_data = {}

        for product in products[:5]:  # 샘플만 수집
            try:
                title = product.get("title", "")
                # 실시간 시세 조회
                prices = joongna_search_prices(title)

                if prices:
                    market_data[product.get("product_id")] = {
                        "current_price": product.get("price"),
                        "market_avg": sum(prices) / len(prices),
                        "market_median": sorted(prices)[len(prices)//2],
                        "market_range": {"min": min(prices), "max": max(prices)},
                        "sample_count": len(prices)
                    }
            except Exception as e:
                print(f"시세 조회 실패: {e}")
                continue

        return market_data

    def recommend_sellers_by_price(self,
                                   user_input: Dict[str, Any],
                                   sellers_with_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        가격 관점에서 판매자 추천

        Returns:
            가격 합리성 점수와 함께 판매자 리스트
        """
        analysis = self.analyze_price_reasonableness(
            user_input,
            [p for seller in sellers_with_products for p in seller.get(
                "products", [])]
        )

        # LLM 추천 결과를 기반으로 판매자 점수 계산
        recommended_sellers = []
        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_score = analysis.get(
                "recommended_sellers_by_price", {}).get(str(seller_id), {})

            recommended_sellers.append({
                "seller_id": seller_id,
                "seller_name": seller.get("seller_name"),
                "price_score": seller_score.get("score", 0.5),
                "price_reasoning": seller_score.get("reasoning", ""),
                "recommended_price_range": seller_score.get("price_range"),
                "products": seller.get("products", [])
            })

        # 가격 점수 기준 정렬
        recommended_sellers.sort(key=lambda x: x["price_score"], reverse=True)

        return recommended_sellers


def price_agent_node(state: RecommendationState) -> RecommendationState:
    """가격 에이전트 노드"""
    try:
        user_input = state["user_input"]
        search_query = state.get("search_query", {})

        # 가격 에이전트 실행
        agent = PriceAgent()

        # DB에서 조회
        try:
            # 검색 쿼리 파싱
            search_query_obj = search_query.get(
                "original_query") or search_query.get("enhanced_query", "")
            keywords = search_query.get("keywords", [])

            # 사용자 입력에서 필터 추출
            category = user_input.get("category")
            category_top = None  # 필요시 추가
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
                    category_top=category_top,
                    price_min=price_min,
                    price_max=price_max,
                    limit=50
                )

            if not sellers_with_products:
                raise ValueError("DB에서 상품 데이터를 찾을 수 없습니다.")
            
            print(f"DB에서 {len(sellers_with_products)}개 판매자 조회 완료")
        except Exception as e:
            raise ValueError(f"가격 에이전트 데이터 조회 실패: {e}")

        # 가격 관점에서 판매자 추천
        price_recommendations = agent.recommend_sellers_by_price(
            user_input,
            sellers_with_products
        )

        # 결과를 상태에 저장
        state["price_agent_recommendations"] = {
            "recommended_sellers": price_recommendations,
            "market_analysis": {},
            "reasoning": "가격 관점에서 합리적인 판매자 추천 완료"
        }
        state["current_step"] = "price_analyzed"
        state["completed_steps"].append("price_analysis")

        print(f"가격 에이전트 분석 완료: {len(price_recommendations)}개 판매자 추천")

    except Exception as e:
        state["error_message"] = f"가격 에이전트 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"가격 에이전트 오류: {e}")

    return state
