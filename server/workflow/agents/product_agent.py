"""
상품 특성 분석 에이전트
LLM 기반으로 판매자의 상품 품질 패턴, 시세 대비 가격 전략, 판매자 성향을 종합 분석하여
상품 특성 관점에서 사용자와 가장 잘 어울리는 판매자를 추천
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.workflow.agents.tool import (
    seller_profile_tool,
    item_market_tool,
    price_risk_tool,
    review_feature_tool,
)
from server.workflow.prompts import load_prompt
from server.utils.logger import get_logger

logger = get_logger(__name__)


class ProductAgent:
    """상품 특성 분석 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        # 서브 에이전트는 gpt-4o-mini 사용 (빠른 응답)
        self.llm_agent = create_agent("product_agent", model="gpt-4o-mini")
        self.product_prompt = load_prompt("product_prompt")

    def recommend_sellers_by_product_characteristics(
        self,
        user_input: Dict[str, Any],
        sellers_with_products: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        상품 특성 관점에서 판매자 추천 및 프로파일링

        Args:
            user_input: 사용자 입력 (가격 범위 등)
            sellers_with_products: 판매자와 상품 정보

        Returns:
            상품 특성 점수와 함께 판매자 리스트
        """

        # -------------------------------------------------------------
        # 🔥 1) 각 판매자의 상품들에 대해 툴 적용
        # -------------------------------------------------------------
        seller_product_data: List[Dict[str, Any]] = []

        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_name = seller.get("seller_name")
            products = seller.get("products", []) or []

            if not seller_id or not products:
                continue

            # 1-1) 판매자 프로필 (공통 툴)
            seller_profile = seller_profile_tool(seller_id)

            # 1-2) 리뷰 피처
            review_features = review_feature_tool(seller_id)

            # 1-3) 각 상품의 시세 분석 및 가격 리스크 분석
            product_features: Dict[str, Any] = {}
            market_prices: Dict[str, Any] = {}

            for p in products:
                product_id = p.get("product_id")
                if product_id is None:
                    continue

                # 시세 분석
                market_feature = item_market_tool(product_id)
                product_features[str(product_id)] = {
                    "market_feature": market_feature,
                    "price_feature": price_risk_tool(market_feature, seller_profile),
                    "seller_profile": seller_profile,
                    "product_info": {
                        "title": p.get("title", ""),
                        "description": p.get("description", ""),
                        "price": p.get("price"),
                        "condition": p.get("condition", ""),
                        "category": p.get("category", ""),
                    },
                }

                # 시세 정보
                if market_feature.get("estimated_fair_price") is not None:
                    market_prices[str(product_id)] = {
                        "current_price": p.get("price"),
                        "market_avg": market_feature.get("estimated_fair_price"),
                        "market_median": market_feature.get("estimated_fair_price"),
                        "market_range": {
                            "min": market_feature.get("estimated_fair_price", 0) * 0.8,
                            "max": market_feature.get("estimated_fair_price", 0) * 1.2,
                        },
                        "sample_count": market_feature.get("similar_items_count", 0),
                    }

            seller_product_data.append(
                {
                    "seller_id": seller_id,
                    "seller_name": seller_name,
                    "products": products,
                    "product_features": product_features,
                    "market_prices": market_prices,
                    "seller_profile": seller_profile,
                    "review_features": review_features,
                }
            )

        # -------------------------------------------------------------
        # 🔥 2) LLM에게 넘길 context 구성
        # -------------------------------------------------------------
        # -------------------------------------------------------------
        # 🔥 (NEW) seller_id 기반 매핑 생성 — zip() 제거
        # -------------------------------------------------------------
        # seller_product_data 내부는 seller_id 포함된 dict 리스트
        seller_data_map = {
            str(item["seller_id"]): item
            for item in seller_product_data
        }

        # -------------------------------------------------------------
        # 🔥 context 구성 (zip → seller_id 매핑 방식으로 변경)
        # -------------------------------------------------------------
        context = {
            "user_price_min": user_input.get("price_min", 0),
            "user_price_max": user_input.get("price_max", 1e9),

            # 모든 상품 flat list 형태
            "products": [
                {
                    "product_id": p.get("product_id"),
                    "seller_id": seller.get("seller_id"),
                    "title": p.get("title", ""),
                    "price": p.get("price"),
                    "condition": p.get("condition", ""),
                    "description": p.get("description", ""),
                    "category": p.get("category", ""),
                }
                for seller in sellers_with_products
                for p in seller.get("products", [])
            ],

            # 각 seller_id별 상품 feature 매핑
            "product_features": {
                str(seller["seller_id"]): seller_data_map.get(
                    str(seller["seller_id"]), {}
                ).get("product_features", {})
                for seller in sellers_with_products
            },

            # seller profile + review feature 매핑
            "seller_features": {
                str(seller["seller_id"]): {
                    "seller_profile": seller_data_map.get(
                        str(seller["seller_id"]), {}
                    ).get("seller_profile", {}),
                    "review_features": seller_data_map.get(
                        str(seller["seller_id"]), {}
                    ).get("review_features", {}),
                }
                for seller in sellers_with_products
            },

            # 시장가격 정보 매핑
            "market_prices": {
                str(seller["seller_id"]): seller_data_map.get(
                    str(seller["seller_id"]), {}
                ).get("market_prices", {})
                for seller in sellers_with_products
            },
        }

        # -------------------------------------------------------------
        # 🔥 3) LLM에게 판단 요청
        # -------------------------------------------------------------
        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.product_prompt,
            format="json",
        )

        # -------------------------------------------------------------
        # 🔥 4) LLM 결과를 기반으로 판매자 점수 계산
        # -------------------------------------------------------------
        recommended_sellers_result = decision.get("recommended_sellers", [])

        # seller_id를 키로 하는 딕셔너리 생성
        seller_scores: Dict[str, Dict[str, Any]] = {
            str(rec.get("seller_id")): rec for rec in recommended_sellers_result
        }

        recommended_sellers: List[Dict[str, Any]] = []
        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_score_data = seller_scores.get(str(seller_id), {})

            recommended_sellers.append(
                {
                    "seller_id": seller_id,
                    "seller_name": seller.get("seller_name"),
                    "product_score": seller_score_data.get("score", 0.5),
                    "product_reasoning": seller_score_data.get("reasoning", ""),
                    "seller_characteristics": seller_score_data.get(
                        "seller_characteristics", ""
                    ),
                    "recommended_price_range": seller_score_data.get(
                        "price_range", {"min": 0, "max": 0}
                    ),
                    "products": seller.get("products", []),
                }
            )

        # 상품 특성 점수 기준 정렬
        recommended_sellers.sort(
            key=lambda x: x["product_score"], reverse=True)

        return recommended_sellers


def product_agent_node(state: RecommendationState) -> dict:
    """상품 특성 분석 에이전트 노드"""
    try:
        user_input = state["user_input"]

        # 상품 특성 분석 에이전트 실행
        agent = ProductAgent()

        # DB에서 조회
        from server.db.product_service import (
            get_sellers_with_products,
            search_products_by_keywords,
        )

        search_query = state.get("search_query", {})

        try:
            # 검색 쿼리 파싱
            search_query_obj = search_query.get("original_query") or search_query.get(
                "enhanced_query", ""
            )
            keywords = search_query.get("keywords", [])

            # 사용자 입력에서 필터 추출
            category = user_input.get("category")
            price_min = user_input.get("price_min")
            price_max = user_input.get("price_max")

            # DB에서 조회 (검색어 필터는 사용하지 않음 - 가격/할인율 기준으로만 넓게 조회)
            # Orchestrator가 사용자 의도를 파악해서 최종 필터링
            sellers_with_products = get_sellers_with_products(
                search_query=None,  # 검색어 필터 제거
                category=category,
                price_min=price_min,
                price_max=price_max,
                limit=50,
            )

            logger.info(
                "상품 특성 분석용 판매자 조회 완료",
                extra={
                    "seller_count": len(sellers_with_products) if sellers_with_products else 0,
                    "has_keywords": bool(keywords),
                    "search_query": search_query_obj if not keywords else None,
                }
            )

            if not sellers_with_products:
                # DB에 상품이 있는지 확인
                from server.db.database import SessionLocal
                from server.db.models import Product
                db = SessionLocal()
                try:
                    total_count = db.query(Product).count()
                    if total_count == 0:
                        raise ValueError(
                            "DB에 상품 데이터가 없습니다. CSV 파일을 먼저 마이그레이션해주세요.")
                    else:
                        raise ValueError(
                            f"필터 조건에 맞는 상품이 없습니다. (DB에 총 {total_count}개 상품 존재)")
                finally:
                    db.close()
        except Exception as e:
            logger.exception("상품 특성 분석 에이전트 DB 조회 실패")
            raise ValueError(f"상품 특성 분석 에이전트 데이터 조회 실패: {str(e)}")

        # 상품 특성 관점에서 판매자 추천
        logger.info(
            "상품 특성 분석 에이전트 LLM 호출 시작",
            extra={"seller_count": len(sellers_with_products)},
        )

        product_recommendations = agent.recommend_sellers_by_product_characteristics(
            user_input,
            sellers_with_products,
        )

        # 결과를 상태에 저장
        logger.info(
            "상품 특성 분석 에이전트 분석 완료",
            extra={
                "recommended_sellers": len(product_recommendations),
                "has_recommendations": len(product_recommendations) > 0,
            },
        )

        return {
            "product_agent_recommendations": {
                "recommended_sellers": product_recommendations,
                "reasoning": "상품 특성 관점에서 판매자 프로파일링 및 추천 완료",
                "confidence": 0.8,
            },
            "completed_steps": ["product_analysis"],
        }

    except Exception as e:
        logger.exception("상품 특성 분석 에이전트 오류")
        return {
            "product_agent_recommendations": {
                "recommended_sellers": [],
                "reasoning": "",
                "confidence": 0.0,
                "error": f"상품 특성 분석 에이전트 오류: {str(e)}",
            },
            "completed_steps": ["product_analysis"],
        }
