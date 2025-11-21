"""
추천 오케스트레이터
2개 서브에이전트(가격, 안전거래) 결과를 종합하여
최종 판매자 추천 및 상품 랭킹을 수행
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.workflow.prompts import load_prompt


class OrchestratorAgent:
    """추천 오케스트레이터 - LLM 기반 종합 판단 및 랭킹"""

    def __init__(self):
        self.llm_agent = create_agent("final_matcher")
        # 프롬프트 로드
        self.combine_sellers_prompt = load_prompt(
            "orchestrator_recommendation_prompt"
        )
        self.rank_products_prompt = load_prompt(
            "orchestrator_ranking_prompt"
        )

    def combine_and_rank(
        self,
        price_results: Dict[str, Any],
        safety_results: Dict[str, Any],
        user_input: Dict[str, Any],
        persona_classification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        2개 서브에이전트 결과를 종합하여 최종 추천 및 랭킹
        """

        # user_input / persona 맥락을 서브에이전트 결과에 태워서 전달 (LLM이 trade-off 판단하기 좋게)
        price_results_with_ctx = {
            **price_results,
            "user_input": user_input,
            "persona_classification": persona_classification,
        }
        safety_results_with_ctx = {
            **safety_results,
            "user_input": user_input,
            "persona_classification": persona_classification,
        }

        # 1. 2개 서브에이전트 결과 종합하여 판매자 추천
        final_sellers = self._combine_sub_agent_results(
            price_results_with_ctx, safety_results_with_ctx
        )

        # 2. 추천된 판매자의 상품들을 랭킹
        ranked_products = self._rank_products(
            final_sellers, user_input, persona_classification
        )

        return {
            "final_seller_recommendations": final_sellers,
            "ranked_products": ranked_products,
        }

    def _combine_sub_agent_results(
        self,
        price_results: Dict[str, Any],
        safety_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        2개 서브에이전트 결과 종합

        - 1차: LLM(final_matcher)의 analyze_and_combine 결과 사용
        - 2차: LLM 출력이 없거나 비정상일 경우, 가격/안전 점수를 단순 결합한 fallback 사용
        """

        # 1) LLM에 서브에이전트 결과 전달
        decision = self.llm_agent.analyze_and_combine(
            sub_agent_results=[
                {"agent": "price", "results": price_results},
                {"agent": "safety", "results": safety_results},
            ],
            combination_task=self.combine_sellers_prompt,
        )

        # 2) 각 서브에이전트 결과를 병합하여 기본 seller dict 구성
        all_sellers: Dict[str, Dict[str, Any]] = {}

        self._merge_seller_results(
            all_sellers,
            price_results.get("recommended_sellers", []),
            score_key="price_score",
            reasoning_key="price_reasoning",
            source_score_key="price_score",
            include_products=False,
        )

        self._merge_seller_results(
            all_sellers,
            safety_results.get("recommended_sellers", []),
            score_key="safety_score",
            reasoning_key="safety_reasoning",
            source_score_key="safety_score",
            include_products=True,  # safety 쪽에 products가 붙어 있는 구조라면 여기서 채움
        )

        # 3) LLM 결합 결과 파싱
        final_recommendations: List[Dict[str, Any]] = []

        final_recommendations_data = (decision or {}).get(
            "final_recommendations", {})
        recommended_seller_ids = final_recommendations_data.get(
            "seller_ids", [])
        scores_data = final_recommendations_data.get("scores", {})

        # LLM이 정상적으로 seller_ids를 줬을 때
        if recommended_seller_ids:
            for seller_id in recommended_seller_ids:
                seller_id_str = str(seller_id)
                if seller_id_str not in all_sellers:
                    continue

                seller = all_sellers[seller_id_str]
                final_score_data = scores_data.get(seller_id_str, {})

                final_recommendations.append(
                    {
                        "seller_id": seller["seller_id"],
                        "seller_name": seller["seller_name"],
                        "price_score": seller.get("price_score", 0.0),
                        "safety_score": seller.get("safety_score", 0.0),
                        "final_score": final_score_data.get("score", 0.0),
                        "final_reasoning": final_score_data.get("reasoning", ""),
                        "combination_explanation": decision.get("reasoning", ""),
                        "products": seller.get("products", []),
                    }
                )

            final_recommendations.sort(
                key=lambda x: x["final_score"], reverse=True)
            if final_recommendations:
                return final_recommendations

        # 4) 🔥 Fallback: LLM 결합 결과가 비었거나 이상한 경우
        #    → 가격/안전 점수를 단순 결합해서 final_score 산출
        fallback_recommendations: List[Dict[str, Any]] = []

        for seller_id_str, seller in all_sellers.items():
            price_score = float(seller.get("price_score", 0.0))
            safety_score = float(seller.get("safety_score", 0.0))

            # 기본은 단순 평균 (원하면 나중에 가중치 추가 가능)
            final_score = (price_score + safety_score) / 2.0

            fallback_recommendations.append(
                {
                    "seller_id": seller["seller_id"],
                    "seller_name": seller.get("seller_name"),
                    "price_score": price_score,
                    "safety_score": safety_score,
                    "final_score": final_score,
                    "final_reasoning": "LLM 결합 결과가 없거나 비정상이라 가격/안전 점수를 단순 결합하여 산출된 최종 점수입니다.",
                    "combination_explanation": "",
                    "products": seller.get("products", []),
                }
            )

        fallback_recommendations.sort(
            key=lambda x: x["final_score"], reverse=True)
        return fallback_recommendations

    def _merge_seller_results(
        self,
        all_sellers: Dict[str, Any],
        sellers: List[Dict[str, Any]],
        score_key: str,
        reasoning_key: str,
        source_score_key: str,
        include_products: bool = False,
    ) -> None:
        """서브에이전트 결과를 all_sellers에 병합하는 공통 로직"""

        for seller in sellers:
            seller_id = seller.get("seller_id")
            if seller_id is None:
                continue

            seller_id_str = str(seller_id)

            if seller_id_str not in all_sellers:
                all_sellers[seller_id_str] = {
                    "seller_id": seller_id,
                    "seller_name": seller.get("seller_name"),
                }

            all_sellers[seller_id_str][score_key] = seller.get(
                source_score_key, 0.0)
            all_sellers[seller_id_str][reasoning_key] = seller.get(
                reasoning_key, "")

            if include_products:
                # safety 쪽에서 더 풍부한 products를 내려주는 경우, 여기서 붙이기
                all_sellers[seller_id_str]["products"] = seller.get(
                    "products", [])

    def _rank_products(
        self,
        final_sellers: List[Dict[str, Any]],
        user_input: Dict[str, Any],
        persona_classification: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """상품 랭킹"""

        if not final_sellers:
            return []

        # 각 판매자의 상품 정보 수집
        all_products: List[Dict[str, Any]] = []
        for seller in final_sellers:
            seller_id = seller.get("seller_id")
            seller_name = seller.get("seller_name")
            products = seller.get("products", []) or []

            for product in products:
                all_products.append(
                    {
                        **product,
                        "seller_id": seller_id,
                        "seller_name": seller_name,
                        "seller_price_score": seller.get("price_score", 0.0),
                        "seller_safety_score": seller.get("safety_score", 0.0),
                        "seller_final_score": seller.get("final_score", 0.0),
                    }
                )

        if not all_products:
            return []

        # 판매자 점수 정보를 리스트로 구성
        seller_scores_list = [
            {
                "seller_id": seller.get("seller_id"),
                "seller_name": seller.get("seller_name"),
                "price": seller.get("price_score", 0.0),
                "safety": seller.get("safety_score", 0.0),
                "final": seller.get("final_score", 0.0),
            }
            for seller in final_sellers[:10]
        ]

        context = {
            "user_input": user_input,
            "persona_type": str(persona_classification.get("persona_type", "")),
            "products": all_products[:50],
            "final_seller_scores": seller_scores_list,
        }

        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.rank_products_prompt,
            format="json",
        )

        ranked_product_ids = decision.get("ranked_product_ids", [])

        # 🔥 fallback: LLM이 상품 순서를 안 줬으면 seller_final_score 기준 정렬
        if not ranked_product_ids and decision.get("fallback"):
            all_products.sort(
                key=lambda x: x["seller_final_score"], reverse=True)
            return all_products

        # 상품을 product_id로 인덱싱
        products_by_id = {p.get("product_id"): p for p in all_products}

        ranked_products: List[Dict[str, Any]] = []
        ranked_ids = set()

        for product_id in ranked_product_ids:
            product = products_by_id.get(product_id)
            if product:
                ranked_products.append(product)
                ranked_ids.add(product_id)

        # 랭킹되지 않은 상품들 추가 (순서는 기존 seller_final_score 순)
        for product in all_products:
            pid = product.get("product_id")
            if pid not in ranked_ids:
                ranked_products.append(product)

        return ranked_products


def orchestrator_agent_node(state: RecommendationState) -> RecommendationState:
    """추천 오케스트레이터 노드"""
    try:
        price_results = state.get("price_agent_recommendations", {})
        safety_results = state.get("safety_agent_recommendations", {})

        if not price_results or not safety_results:
            raise ValueError("서브에이전트 결과가 완료되지 않았습니다.")

        user_input = state.get("user_input")
        persona_classification = state.get("persona_classification", {})

        orchestrator = OrchestratorAgent()
        result = orchestrator.combine_and_rank(
            price_results,
            safety_results,
            user_input,
            persona_classification,
        )

        state["final_seller_recommendations"] = result["final_seller_recommendations"]
        state["final_item_scores"] = result["ranked_products"]
        state["ranking_explanation"] = "LLM 기반 자율 판단으로 최종 추천 및 랭킹 완료"
        state["current_step"] = "recommendation_completed"
        state.setdefault("completed_steps", []).append("recommendation")

        print(
            f"최종 추천 완료: {len(result['final_seller_recommendations'])}개 판매자, {len(result['ranked_products'])}개 상품"
        )

        for i, seller in enumerate(
            result["final_seller_recommendations"][:5], 1
        ):
            print(
                f"  {i}. {seller['seller_name']} (최종점수: {seller['final_score']:.3f})")

    except Exception as e:
        state["error_message"] = f"추천 오케스트레이터 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"추천 오케스트레이터 오류: {e}")

    return state
