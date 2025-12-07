"""
상품 특성 분석 에이전트
LLM 기반으로 판매자가 판매하는 상품들의 모든 특성(가격, 상태, 중고/새상품, 품질 등)을 종합 분석하여
이 판매자가 어떤 특성의 상품을 파는 사람인지를 판단하고, 사용자와의 매칭 적합성을 평가
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
from server.utils.logger import get_logger

logger = get_logger(__name__)


class ProductAgent:
    """상품 특성 분석 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("product_agent")
        self.product_prompt = load_prompt("product_prompt")

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
                logger.warning("시세 조회 실패", exc_info=e,
                               extra={"product": product})
                continue

        return market_data

    # ------------------------------------------------------------------
    # 🔥 STEP 2: ProductAgent 메인 분석
    # ------------------------------------------------------------------
    def analyze_product_characteristics(
        self,
        user_input: Dict[str, Any],
        products: List[Dict[str, Any]],
        market_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        LLM 기반으로 판매자가 판매하는 상품들의 모든 특성을 종합 분석
        - 가격 (시세 대비 저렴/적정/비쌈)
        - 상태 (새상품/중고/사용감 있음 등)
        - 품질 (구성품 완비, 정품 인증 등)
        - 거래 방식 (직거래/택배/안전결제 등)
        등 모든 특성을 고려하여 판매자의 특성을 파악
        """

        # (A) 실시간 시세 수집
        market_prices = self._collect_market_data(products)

        # ------------------------------------------------------------------
        # (B) 🔥 item_market_tool / price_risk_tool 적용 (상품별 feature 생성)
        # ------------------------------------------------------------------
        product_features = {}
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

            product_features[product_id] = {
                "market_feature": market_feature,
                "price_feature": price_feature,
                "seller_profile": seller_profile,
                # 상품 자체 정보도 포함 (상태, 설명 등)
                "product_info": {
                    "title": p.get("title", ""),
                    "description": p.get("description", ""),
                    "price": p.get("price"),
                    "condition": p.get("condition", ""),
                    "category": p.get("category", ""),
                }
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
            "products": products[:10],  # 상품의 모든 정보 포함 (가격, 상태, 설명 등)

            # 새로 포함된 툴 기반 feature
            "product_features": product_features,
            "seller_features": seller_features,

            # 기존 실시간 시세
            "market_prices": market_prices,
        }

        # ------------------------------------------------------------------
        # (E) 🔥 LLM 판단 요청
        # ------------------------------------------------------------------
        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.product_prompt,
            format="json"
        )

        # LLM 결과를 dict 형태로 변환 (seller_id를 key로 사용)
        recommended_sellers_raw = decision.get("recommended_sellers", {})
        if isinstance(recommended_sellers_raw, list):
            # list 형태인 경우 dict로 변환
            recommended_sellers_dict = {}
            for item in recommended_sellers_raw:
                seller_id = item.get("seller_id")
                if seller_id:
                    recommended_sellers_dict[str(seller_id)] = item
            recommended_sellers_by_product = recommended_sellers_dict
        else:
            # 이미 dict 형태인 경우 그대로 사용
            recommended_sellers_by_product = recommended_sellers_raw if isinstance(
                recommended_sellers_raw, dict) else {}

        return {
            "recommended_sellers_by_product": recommended_sellers_by_product,
            "product_reasoning": decision.get("reasoning", ""),
            "market_analysis": market_prices,
            "recommendation_score": decision.get("confidence", 0.5)
        }

    # ------------------------------------------------------------------
    # 🔥 STEP 3: 노드용 wrapper
    # ------------------------------------------------------------------
    def recommend_sellers_by_product_characteristics(
        self,
        user_input: Dict[str, Any],
        sellers_with_products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        analysis = self.analyze_product_characteristics(
            user_input,
            [p for seller in sellers_with_products for p in seller.get(
                "products", [])]
        )

        recommended_sellers = []
        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_score = analysis.get(
                "recommended_sellers_by_product", {}).get(str(seller_id), {})

            recommended_sellers.append({
                "seller_id": seller_id,
                "seller_name": seller.get("seller_name"),
                "product_score": seller_score.get("score", 0.5),
                "product_reasoning": seller_score.get("reasoning", ""),
                "seller_characteristics": seller_score.get("seller_characteristics", ""),
                "recommended_price_range": seller_score.get("price_range"),
                "products": seller.get("products", [])
            })

        recommended_sellers.sort(
            key=lambda x: x["product_score"], reverse=True)
        return recommended_sellers


# ----------------------------------------------------------------------
# 🔥 그래프 노드 - ProductAgent 실행
# ----------------------------------------------------------------------
def product_agent_node(state: RecommendationState) -> RecommendationState:
    try:
        user_input = state["user_input"]
        search_query = state.get("search_query", {})

        agent = ProductAgent()

        # 1) DB 조회
        try:
            if search_query.get("keywords"):
                sellers_with_products = search_products_by_keywords(
                    keywords=search_query["keywords"],
                    category=user_input.get("category"),
                    price_min=user_input.get("price_min"),
                    price_max=user_input.get("price_max"),
                    limit=50
                )
            else:
                # 검색 쿼리가 없으면 모든 상품 조회 (필터만 적용)
                search_query_str = search_query.get(
                    "original_query") or search_query.get("enhanced_query")
                sellers_with_products = get_sellers_with_products(
                    search_query=search_query_str,
                    category=user_input.get("category"),
                    category_top=None,
                    price_min=user_input.get("price_min"),
                    price_max=user_input.get("price_max"),
                    limit=50
                )

            logger.info(
                "상품 특성 분석용 판매자 조회 완료",
                extra={
                    "seller_count": len(sellers_with_products) if sellers_with_products else 0,
                    "has_keywords": bool(search_query.get("keywords")),
                    "search_query": search_query_str if not search_query.get("keywords") else None,
                }
            )

            if not sellers_with_products:
                # 필터를 완화하여 재시도
                logger.warning(
                    "검색 조건으로 상품을 찾지 못해 필터를 완화하여 재시도",
                    extra={
                        "original_keywords": search_query.get("keywords"),
                        "original_search_query": search_query.get("original_query"),
                    }
                )
                sellers_with_products = get_sellers_with_products(
                    search_query=None,  # 검색어 제거
                    category=None,  # 카테고리 제거
                    category_top=None,
                    price_min=None,  # 가격 필터 제거
                    price_max=None,
                    limit=50
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
                                f"검색 조건이 너무 엄격합니다. (DB에 총 {total_count}개 상품 존재)")
                    finally:
                        db.close()
        except Exception as e:
            logger.exception("상품 특성 분석 에이전트 DB 조회 실패")
            raise ValueError(f"상품 특성 분석 에이전트 데이터 조회 실패: {str(e)}")

        # 2) 상품 특성 분석 실행
        product_recommendations = agent.recommend_sellers_by_product_characteristics(
            user_input,
            sellers_with_products
        )

        # 3) 상태 저장 (변경하는 필드만 반환 - user_input은 변경하지 않으므로 제외)
        # completed_steps는 add reducer를 사용하므로 리스트로 반환
        # current_step은 병렬 실행 중 충돌 방지를 위해 설정하지 않음 (orchestrator에서 설정)
        return {
            "product_agent_recommendations": {
                "recommended_sellers": product_recommendations,
                "market_analysis": {},
                "reasoning": "상품 특성 관점 분석 완료"
            },
            "completed_steps": ["product_analysis"],  # add reducer가 기존 리스트와 병합
        }

    except Exception as e:
        logger.exception("상품 특성 분석 에이전트 오류")
        # 병렬 실행 중 error_message, current_step 충돌 방지: 각 노드의 결과에 에러 정보 포함
        return {
            "product_agent_recommendations": {
                "recommended_sellers": [],
                "reasoning": "",
                "error": f"상품 특성 분석 에이전트 오류: {str(e)}",
            },
            "completed_steps": ["product_analysis"],
        }
