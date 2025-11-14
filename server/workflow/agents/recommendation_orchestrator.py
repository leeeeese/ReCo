"""
추천 오케스트레이터
3개 서브에이전트(가격, 안전거래, 페르소나) 결과를 종합하여
최종 판매자 추천 및 상품 랭킹을 수행
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.workflow.prompts import load_prompt


class RecommendationOrchestrator:
    """추천 오케스트레이터 - LLM 기반 종합 판단 및 랭킹"""

    def __init__(self):
        self.llm_agent = create_agent("final_matcher")
        # 프롬프트 로드
        self.combine_sellers_prompt = load_prompt(
            "orchestrator_combine_sellers")
        self.rank_products_prompt = load_prompt("orchestrator_rank_products")

    def combine_and_rank(self,
                         price_results: Dict[str, Any],
                         safety_results: Dict[str, Any],
                         persona_results: Dict[str, Any],
                         user_input: Dict[str, Any],
                         persona_classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        3개 서브에이전트 결과를 종합하여 최종 추천 및 랭킹

        Returns:
            최종 추천 판매자 및 랭킹된 상품 리스트
        """
        # 1. 3개 서브에이전트 결과 종합하여 판매자 추천
        final_sellers = self._combine_sub_agent_results(
            price_results, safety_results, persona_results)

        # 2. 추천된 판매자의 상품들을 랭킹
        ranked_products = self._rank_products(
            final_sellers, user_input, persona_classification)

        return {
            "final_seller_recommendations": final_sellers,
            "ranked_products": ranked_products
        }

    def _combine_sub_agent_results(self,
                                   price_results: Dict[str, Any],
                                   safety_results: Dict[str, Any],
                                   persona_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """3개 서브에이전트 결과 종합"""
        decision = self.llm_agent.analyze_and_combine(
            sub_agent_results=[
                {"agent": "price", "results": price_results},
                {"agent": "safety", "results": safety_results},
                {"agent": "persona", "results": persona_results}
            ],
            combination_task=self.combine_sellers_prompt
        )

        # 각 서브에이전트 결과를 병합
        all_sellers = {}

        # 가격 에이전트 결과 병합
        self._merge_seller_results(
            all_sellers,
            price_results.get("recommended_sellers", []),
            "price_score", "price_reasoning", "price_score"
        )

        # 안전거래 에이전트 결과 병합
        self._merge_seller_results(
            all_sellers,
            safety_results.get("recommended_sellers", []),
            "safety_score", "safety_reasoning", "safety_score"
        )

        # 페르소나 에이전트 결과 병합
        self._merge_seller_results(
            all_sellers,
            persona_results.get("recommended_sellers", []),
            "persona_score", "persona_reasoning", "persona_match_score",
            include_products=True
        )

        # LLM 종합 점수 적용
        final_recommendations_data = decision.get("final_recommendations", {})
        recommended_seller_ids = final_recommendations_data.get(
            "seller_ids", [])
        scores_data = final_recommendations_data.get("scores", {})
        final_recommendations = []

        for seller_id in recommended_seller_ids:
            seller_id_str = str(seller_id)
            if seller_id_str in all_sellers:
                seller = all_sellers[seller_id_str]
                final_score_data = scores_data.get(seller_id_str, {})

                final_recommendations.append({
                    "seller_id": seller["seller_id"],
                    "seller_name": seller["seller_name"],
                    "price_score": seller.get("price_score", 0),
                    "safety_score": seller.get("safety_score", 0),
                    "persona_score": seller.get("persona_score", 0),
                    "final_score": final_score_data.get("score", 0),
                    "final_reasoning": final_score_data.get("reasoning", ""),
                    "combination_explanation": decision.get("reasoning", ""),
                    "products": seller.get("products", [])
                })

        final_recommendations.sort(
            key=lambda x: x["final_score"], reverse=True)
        return final_recommendations

    def _merge_seller_results(self,
                              all_sellers: Dict[str, Any],
                              sellers: List[Dict[str, Any]],
                              score_key: str,
                              reasoning_key: str,
                              source_score_key: str,
                              include_products: bool = False) -> None:
        """서브에이전트 결과를 all_sellers에 병합하는 공통 로직"""
        for seller in sellers:
            seller_id = str(seller.get("seller_id"))
            if seller_id not in all_sellers:
                all_sellers[seller_id] = {
                    "seller_id": seller_id,
                    "seller_name": seller.get("seller_name")
                }
            all_sellers[seller_id][score_key] = seller.get(source_score_key, 0)
            all_sellers[seller_id][reasoning_key] = seller.get(
                reasoning_key, "")
            if include_products:
                all_sellers[seller_id]["products"] = seller.get("products", [])

    def _rank_products(self,
                       final_sellers: List[Dict[str, Any]],
                       user_input: Dict[str, Any],
                       persona_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """상품 랭킹"""
        if not final_sellers:
            return []

        # 각 판매자의 상품 정보 수집
        all_products = []
        for seller in final_sellers:
            seller_id = seller.get("seller_id")
            seller_name = seller.get("seller_name")
            products = seller.get("products", [])

            for product in products:
                all_products.append({
                    **product,
                    "seller_id": seller_id,
                    "seller_name": seller_name,
                    "seller_price_score": seller.get("price_score", 0),
                    "seller_safety_score": seller.get("safety_score", 0),
                    "seller_persona_score": seller.get("persona_score", 0),
                    "seller_final_score": seller.get("final_score", 0)
                })

        if not all_products:
            return []

        # 판매자 점수 정보를 리스트로 구성
        seller_scores_list = [
            {
                "seller_id": seller.get("seller_id"),
                "seller_name": seller.get("seller_name"),
                "price": seller.get("price_score", 0),
                "safety": seller.get("safety_score", 0),
                "persona": seller.get("persona_score", 0),
                "final": seller.get("final_score", 0)
            }
            for seller in final_sellers[:10]
        ]

        context = {
            "user_input": user_input,
            "persona_type": str(persona_classification.get("persona_type", "")),
            "products": all_products[:50],
            "final_seller_scores": seller_scores_list
        }

        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.rank_products_prompt,
            format="json"
        )

        # LLM 결과 파싱 및 적용
        ranked_product_ids = decision.get("ranked_product_ids", [])
        if not ranked_product_ids and decision.get("fallback"):
            all_products.sort(
                key=lambda x: x["seller_final_score"], reverse=True)
            return all_products

        # 상품을 product_id로 인덱싱하여 빠른 조회
        products_by_id = {p.get("product_id"): p for p in all_products}

        # LLM이 제시한 순서대로 재정렬
        ranked_products = []
        ranked_ids = set()
        for product_id in ranked_product_ids:
            product = products_by_id.get(product_id)
            if product:
                ranked_products.append(product)
                ranked_ids.add(product_id)

        # 랭킹되지 않은 상품들 추가
        for product in all_products:
            product_id = product.get("product_id")
            if product_id not in ranked_ids:
                ranked_products.append(product)

        return ranked_products


def recommendation_orchestrator_node(state: RecommendationState) -> RecommendationState:
    """추천 오케스트레이터 노드"""
    try:
        # 3개 서브에이전트 결과 가져오기
        price_results = state.get("price_agent_recommendations", {})
        safety_results = state.get("safety_agent_recommendations", {})
        persona_results = state.get("persona_matching_recommendations", {})

        if not price_results or not safety_results or not persona_results:
            raise ValueError("서브에이전트 결과가 완료되지 않았습니다.")

        user_input = state.get("user_input")
        persona_classification = state.get("persona_classification")

        # 오케스트레이터 실행
        orchestrator = RecommendationOrchestrator()
        result = orchestrator.combine_and_rank(
            price_results,
            safety_results,
            persona_results,
            user_input,
            persona_classification
        )

        # 결과를 상태에 저장
        state["final_seller_recommendations"] = result["final_seller_recommendations"]
        state["final_item_scores"] = result["ranked_products"]
        state["ranking_explanation"] = "LLM 기반 자율 판단으로 최종 추천 및 랭킹 완료"
        state["current_step"] = "recommendation_completed"
        state["completed_steps"].append("recommendation")

        print(
            f"최종 추천 완료: {len(result['final_seller_recommendations'])}개 판매자, {len(result['ranked_products'])}개 상품")

        # 상위 5개 결과 출력
        for i, seller in enumerate(result["final_seller_recommendations"][:5], 1):
            print(
                f"  {i}. {seller['seller_name']} (최종점수: {seller['final_score']:.3f})")

    except Exception as e:
        state["error_message"] = f"추천 오케스트레이터 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"추천 오케스트레이터 오류: {e}")

    return state
