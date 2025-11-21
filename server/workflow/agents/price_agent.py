"""
가격 에이전트
LLM 기반으로 실시간 시세와 상품 데이터를 종합 분석하여 
사용자가 합리적이라고 생각할 만한 가격 범위의 상품을 판단
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.workflow.agents.price_updater import PriceUpdater, joongna_search_prices
from server.db.product_service import (
    get_sellers_with_products,
    search_products_by_keywords,
)
from server.workflow.prompts import load_prompt
from server.workflow.agents.tool import (
    item_market_tool,
    price_risk_tool,
    seller_profile_tool,
    review_feature_tool,
)


class PriceAgent:
    """가격 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("price_agent")
        self.price_prompt = load_prompt("price_prompt")

    # ------------------------------------------------------------------
    # 🔥 STEP 1: 각 상품의 시세/시장가 수집
    # ------------------------------------------------------------------
    def _collect_market_data(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """실시간 시세 데이터 수집"""
        market_data = {}

        for product in products[:5]:
            try:
                title = product.get("title", "")
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

    # ------------------------------------------------------------------
    # 🔥 STEP 2: PriceAgent 메인 분석
    # ------------------------------------------------------------------
    def analyze_price_reasonableness(
        self,
        user_input: Dict[str, Any],
        products: List[Dict[str, Any]],
        market_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        LLM 기반으로 가격 합리성 분석
        """

        # (A) 실시간 시세 수집
        market_prices = self._collect_market_data(products)

        # ------------------------------------------------------------------
        # (B) 🔥 item_market_tool / price_risk_tool 적용 (상품별 price feature 생성)
        # ------------------------------------------------------------------
        product_price_features = {}
        for p in products[:10]:
            product_id = p.get("product_id")
            if product_id is None:
                continue

            # 1) 시세 기반 feature
            market_feature = item_market_tool(product_id)

            # 2) 판매자 프로필 (공통 툴)
            seller_id = p.get("seller_id")
            if not seller_id:
                continue
            seller_profile = seller_profile_tool(seller_id)

            # 3) 가격 리스크 feature
            price_feature = price_risk_tool(
                market_features=market_feature,
                seller_profile=seller_profile
            )

            product_price_features[product_id] = {
                "market_feature": market_feature,
                "price_feature": price_feature,
                "seller_profile": seller_profile
            }

        # ------------------------------------------------------------------
        # (C) 🔥 seller_profile_tool / review_feature_tool 적용 (판매자별 seller feature 생성)
        # ------------------------------------------------------------------
        seller_features = {}
        for p in products:
            seller_id = p.get("seller_id")
            if seller_id in seller_features:
                continue
            if not seller_id:
                continue

            seller_features[seller_id] = {
                "seller_profile": seller_profile_tool(seller_id),
                "review_features": review_feature_tool(seller_id),
            }

        # ------------------------------------------------------------------
        # (D) 🔥 LLM에게 넘길 context 구성
        # ------------------------------------------------------------------
        context = {
            "user_price_min": user_input.get("price_min", 0),
            "user_price_max": user_input.get("price_max", float('inf')),
            "user_persona": user_input.get("persona_type"),
            "products": products[:10],

            # 새로 포함된 툴 기반 feature
            "product_price_features": product_price_features,
            "seller_features": seller_features,

            # 기존 실시간 시세
            "market_prices": market_prices,
        }

        # ------------------------------------------------------------------
        # (E) 🔥 LLM 판단 요청
        # ------------------------------------------------------------------
        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.price_prompt,
            format="json"
        )

        return {
            "recommended_sellers_by_price": decision.get("recommended_sellers", []),
            "price_reasoning": decision.get("reasoning", ""),
            "market_analysis": market_prices,
            "recommendation_score": decision.get("confidence", 0.5)
        }

    # ------------------------------------------------------------------
    # 🔥 STEP 3: 노드용 wrapper
    # ------------------------------------------------------------------
    def recommend_sellers_by_price(
        self,
        user_input: Dict[str, Any],
        sellers_with_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        analysis = self.analyze_price_reasonableness(
            user_input,
            [p for seller in sellers_with_products for p in seller.get(
                "products", [])]
        )

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

        recommended_sellers.sort(key=lambda x: x["price_score"], reverse=True)
        return recommended_sellers


# ----------------------------------------------------------------------
# 🔥 그래프 노드 - PriceAgent 실행
# ----------------------------------------------------------------------
def price_agent_node(state: RecommendationState) -> RecommendationState:
    try:
        user_input = state["user_input"]
        search_query = state.get("search_query", {})

        agent = PriceAgent()

        # 1) DB 조회
        if search_query.get("keywords"):
            sellers_with_products = search_products_by_keywords(
                keywords=search_query["keywords"],
                category=user_input.get("category"),
                price_min=user_input.get("price_min"),
                price_max=user_input.get("price_max"),
                limit=50
            )
        else:
            sellers_with_products = get_sellers_with_products(
                search_query=search_query.get("original_query"),
                category=user_input.get("category"),
                category_top=None,
                price_min=user_input.get("price_min"),
                price_max=user_input.get("price_max"),
                limit=50
            )

        if not sellers_with_products:
            raise ValueError("DB에서 상품 데이터를 찾을 수 없습니다.")

        # 2) 가격 분석 실행
        price_recommendations = agent.recommend_sellers_by_price(
            user_input,
            sellers_with_products
        )

        # 3) 상태 저장
        state["price_agent_recommendations"] = {
            "recommended_sellers": price_recommendations,
            "market_analysis": {},
            "reasoning": "가격 관점 분석 완료"
        }
        state["current_step"] = "price_analyzed"
        state["completed_steps"].append("price_analysis")

    except Exception as e:
        state["error_message"] = f"가격 에이전트 오류: {str(e)}"
        state["current_step"] = "error"

    return state
