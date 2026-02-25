"""
신뢰도 분석 에이전트
LLM 기반으로 판매자의 거래 행동 패턴, 리뷰 기반 성향, 신뢰도, 활동성을 종합 분석하여
판매자를 프로파일링하고 사용자와 가장 잘 어울리는 신뢰할 수 있는 판매자를 추천
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.utils import config
from server.workflow.agents.tool import (
    seller_profile_tool,
    review_feature_tool,
    trade_risk_tool,
)
from server.workflow.prompts import load_prompt
from server.utils.logger import get_logger

logger = get_logger(__name__)


class ReliabilityAgent:
    """신뢰도 분석 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        # 서브 에이전트는 Azure GPT-4o-mini deployment 사용 (빠른 응답)
        self.llm_agent = create_agent("reliability_agent", model=config.AOAI_DEPLOY_GPT4O_MINI)
        self.reliability_prompt = load_prompt("reliability_prompt")

    def recommend_sellers_by_reliability(
        self,
        user_input: Dict[str, Any],
        sellers_with_products: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        신뢰도 관점에서 판매자 추천 및 프로파일링

        Args:
            user_input: 사용자 입력 (신뢰도 선호도 포함)
            sellers_with_products: 판매자와 상품 정보

        Returns:
            신뢰도 점수와 함께 판매자 리스트
        """

        # -------------------------------------------------------------
        # 🔥 1) seller_profile_tool / review_feature_tool / trade_risk_tool 적용
        # -------------------------------------------------------------
        seller_reliability_data: List[Dict[str, Any]] = []

        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_name = seller.get("seller_name")
            if not seller_id:
                continue

            # 1-1) 판매자 프로필 (공통 툴)
            seller_profile = seller_profile_tool(seller_id)

            # 1-2) 리뷰 피처 (리뷰 자연어 기반 신호)
            review_features = review_feature_tool(seller_id)

            # 1-3) 이 판매자가 올린 각 상품의 거래 리스크 (거래 방식, 안전결제 등)
            products = seller.get("products", []) or []
            product_trade_risks: Dict[str, Any] = {}

            for p in products:
                product_id = p.get("product_id")
                if product_id is None:
                    continue

                trade_risk = trade_risk_tool(product_id)
                product_trade_risks[str(product_id)] = trade_risk

            seller_reliability_data.append(
                {
                    "seller_id": seller_id,
                    "seller_name": seller_name,
                    "seller_profile": seller_profile,
                    "review_features": review_features,
                    "product_trade_risks": product_trade_risks,
                    "products": products,
                }
            )

        # -------------------------------------------------------------
        # 🔥 2) LLM에게 넘길 context 구성
        # -------------------------------------------------------------
        context = {
            "user_trust_safety_preference": user_input.get("trust_safety", 50),
            "user_remote_transaction_preference": user_input.get("remote_transaction", 50),

            # tools 기반 구조화 피처
            "sellers_reliability_view": seller_reliability_data,
        }

        # -------------------------------------------------------------
        # 🔥 3) LLM에게 판단 요청
        # -------------------------------------------------------------
        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.reliability_prompt,
            format="json",
        )

        # -------------------------------------------------------------
        # 🔥 4) LLM 결과를 기반으로 판매자 점수 계산
        # -------------------------------------------------------------
        raw = decision.get("recommended_sellers", {})

        # normalize to dict[str, dict]
        if isinstance(raw, dict):
            recommended_sellers_result = {
                str(k): v for k, v in raw.items() if isinstance(v, dict)
            }
        elif isinstance(raw, list):
            recommended_sellers_result = {
                str(item.get("seller_id")): item
                for item in raw
                if isinstance(item, dict) and item.get("seller_id") is not None
            }
        else:
            recommended_sellers_result = {}

        recommended_sellers: List[Dict[str, Any]] = []
        for seller in sellers_with_products:
            seller_id = seller.get("seller_id")
            seller_score = recommended_sellers_result.get(str(seller_id), {})

            recommended_sellers.append(
                {
                    "seller_id": seller_id,
                    "seller_name": seller.get("seller_name"),
                    "reliability_score": seller_score.get("score", 0.5),
                    "reliability_reasoning": seller_score.get("reasoning", ""),
                    "seller_profile_summary": seller_score.get("seller_profile_summary", ""),
                    "reliability_features_matched": seller_score.get(
                        "matched_features", []
                    ),
                    "trust_level": seller_score.get("trust_level", "medium"),
                    "products": seller.get("products", []),
                }
            )

        # 신뢰도 점수 기준 정렬
        recommended_sellers.sort(
            key=lambda x: x["reliability_score"], reverse=True)

        return recommended_sellers


def reliability_agent_node(state: RecommendationState) -> dict:
    """신뢰도 분석 에이전트 노드"""
    try:
        user_input = state["user_input"]

        # 신뢰도 분석 에이전트 실행
        agent = ReliabilityAgent()

        # DB에서 조회 (product_agent와 동일한 로직)
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

            # DB에서 조회 (검색어 필터는 사용하지 않음 - 신뢰도 기준으로만 넓게 조회)
            # Orchestrator가 사용자 의도를 파악해서 최종 필터링
            sellers_with_products = get_sellers_with_products(
                search_query=None,  # 검색어 필터 제거
                category=category,
                price_min=price_min,
                price_max=price_max,
                limit=50,
            )

            logger.info(
                "신뢰도 분석용 판매자 조회 완료",
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
            logger.exception("신뢰도 분석 에이전트 DB 조회 실패")
            raise ValueError(f"신뢰도 분석 에이전트 데이터 조회 실패: {str(e)}")

        # 신뢰도 관점에서 판매자 추천
        logger.info(
            "신뢰도 분석 에이전트 LLM 호출 시작",
            extra={"seller_count": len(sellers_with_products)},
        )

        reliability_recommendations = agent.recommend_sellers_by_reliability(
            user_input,
            sellers_with_products,
        )

        # 결과를 상태에 저장 (변경하는 필드만 반환 - user_input은 변경하지 않으므로 제외)
        logger.info(
            "신뢰도 분석 에이전트 분석 완료",
            extra={
                "recommended_sellers": len(reliability_recommendations),
                "has_recommendations": len(reliability_recommendations) > 0,
            },
        )

        # completed_steps는 add reducer를 사용하므로 리스트로 반환
        # current_step은 병렬 실행 중 충돌 방지를 위해 설정하지 않음 (orchestrator에서 설정)
        return {
            "reliability_agent_recommendations": {
                "recommended_sellers": reliability_recommendations,
                "reasoning": "신뢰도 관점에서 신뢰할 수 있는 판매자 프로파일링 및 추천 완료",
            },
            # add reducer가 기존 리스트와 병합
            "completed_steps": ["reliability_analysis"],
        }

    except Exception as e:
        logger.exception("신뢰도 분석 에이전트 오류")
        # 병렬 실행 중 error_message, current_step 충돌 방지: 각 노드의 결과에 에러 정보 포함
        return {
            "reliability_agent_recommendations": {
                "recommended_sellers": [],
                "reasoning": "",
                "error": f"신뢰도 분석 에이전트 오류: {str(e)}",
            },
            "completed_steps": ["reliability_analysis"],
        }
