"""
Ranker Agent
최종 매칭된 판매자의 상품들을 랭킹
LLM 기반으로 자율적으로 상품 랭킹 판단
"""

from typing import List, Dict, Any
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent


class FusionRanker:
    """융합 랭킹기 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("final_matcher")  # 최종 랭킹도 같은 에이전트 활용

    def rank_products(self,
                      final_seller_recommendations: List[Dict[str, Any]],
                      user_input: Dict[str, Any],
                      persona_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        LLM 기반으로 상품 랭킹

        Args:
            final_seller_recommendations: 최종 매칭된 판매자 추천 결과
            user_input: 사용자 입력
            persona_classification: 페르소나 분류 결과

        Returns:
            랭킹된 상품 리스트
        """
        if not final_seller_recommendations:
            return []

        # 각 판매자의 상품 정보 수집
        all_products = []
        for seller in final_seller_recommendations:
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

        # LLM에게 랭킹 요청
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
            for seller in final_seller_recommendations[:10]
        ]

        context = {
            "user_input": user_input,
            "persona_type": str(persona_classification.get("persona_type", "")),
            "products": all_products[:50],  # 상위 50개만 분석 (토큰 절약)
            "final_seller_scores": seller_scores_list
        }

        decision = self.llm_agent.decide(
            context=context,
            decision_task="최종 매칭된 판매자들의 상품들을 사용자에게 가장 적합한 순서로 랭킹해주세요. "
            "판매자의 가격/안전/페르소나 점수와 상품의 특성을 종합적으로 고려하여 판단하세요.",
            format="json"
        )

        # LLM 결과 파싱 및 적용
        ranked_product_ids = decision.get("ranked_product_ids", [])
        if not ranked_product_ids and decision.get("fallback"):
            # LLM 실패 시 판매자 점수 기반 정렬
            all_products.sort(
                key=lambda x: x["seller_final_score"], reverse=True)
            return all_products

        # LLM이 제시한 순서대로 재정렬
        ranked_products = []
        for product_id in ranked_product_ids:
            product = next((p for p in all_products if p.get(
                "product_id") == product_id), None)
            if product:
                ranked_products.append(product)

        # 랭킹되지 않은 상품들 추가
        ranked_ids = {p.get("product_id") for p in ranked_products}
        for product in all_products:
            if product.get("product_id") not in ranked_ids:
                ranked_products.append(product)

        return ranked_products


def ranker_node(state: RecommendationState) -> RecommendationState:
    """랭킹 노드 - LLM 기반 자율 판단"""
    try:
        final_seller_recommendations = state.get(
            "final_seller_recommendations")
        user_input = state.get("user_input")
        persona_classification = state.get("persona_classification")

        if not final_seller_recommendations:
            raise ValueError("최종 매칭된 판매자가 없습니다.")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        # FusionRanker 인스턴스 생성
        ranker = FusionRanker()

        # LLM 기반 상품 랭킹
        ranked_products = ranker.rank_products(
            final_seller_recommendations,
            user_input,
            persona_classification
        )

        # 결과를 상태에 저장
        state["final_item_scores"] = ranked_products
        state["ranking_explanation"] = "LLM 기반 자율 판단으로 상품 랭킹 완료"
        state["current_step"] = "products_ranked"
        state["completed_steps"].append("ranking")

        print(f"상품 랭킹 완료: {len(ranked_products)}개 상품")
        print(f"LLM 기반 자율 판단으로 랭킹 완료")

        # 상위 5개 결과 출력
        for i, item in enumerate(ranked_products[:5], 1):
            print(
                f"  {i}. {item.get('title', 'N/A')} (판매자: {item.get('seller_name', 'N/A')})")

    except Exception as e:
        state["error_message"] = f"상품 랭킹 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"상품 랭킹 오류: {e}")

    return state
