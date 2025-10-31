"""
최종 매칭 에이전트
가격, 안전거래, 페르소나 매칭 3개 서브에이전트의 결과를 종합하여
사용자와 가장 잘 어울리는 판매자를 최종 추천
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent


class FinalMatcher:
    """최종 매칭 에이전트 - LLM 기반 종합 판단"""

    def __init__(self):
        self.llm_agent = create_agent("final_matcher")

    def combine_sub_agent_results(self,
                                  price_results: Dict[str, Any],
                                  safety_results: Dict[str, Any],
                                  persona_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        3개 서브에이전트 결과를 종합하여 최종 추천

        Args:
            price_results: 가격 에이전트 결과
            safety_results: 안전거래 에이전트 결과
            persona_results: 페르소나 매칭 에이전트 결과

        Returns:
            최종 추천 판매자 리스트
        """
        # 종합 분석을 위한 컨텍스트 구성
        context = {
            "price_agent_recommendations": price_results.get("recommended_sellers", []),
            "price_reasoning": price_results.get("reasoning", ""),
            "safety_agent_recommendations": safety_results.get("recommended_sellers", []),
            "safety_reasoning": safety_results.get("reasoning", ""),
            "persona_agent_recommendations": persona_results.get("recommended_sellers", []),
            "persona_reasoning": persona_results.get("reasoning", "")
        }

        # LLM에게 종합 판단 요청
        decision = self.llm_agent.analyze_and_combine(
            sub_agent_results=[
                {"agent": "price", "results": price_results},
                {"agent": "safety", "results": safety_results},
                {"agent": "persona", "results": persona_results}
            ],
            combination_task="3개 서브에이전트의 판단을 종합하여 사용자에게 가장 적합한 판매자를 최종 추천해주세요. "
            "각 에이전트의 추천 이유와 점수를 종합적으로 고려하여 최종 판단을 내려주세요."
        )

        # 최종 추천 결과 구성
        final_recommendations = []
        recommended_seller_ids = decision.get(
            "final_recommendations", {}).get("seller_ids", [])

        # 각 서브에이전트 결과를 병합
        all_sellers = {}

        # 가격 에이전트 결과 병합
        for seller in price_results.get("recommended_sellers", []):
            seller_id = seller.get("seller_id")
            if seller_id not in all_sellers:
                all_sellers[seller_id] = {
                    "seller_id": seller_id, "seller_name": seller.get("seller_name")}
            all_sellers[seller_id]["price_score"] = seller.get(
                "price_score", 0)
            all_sellers[seller_id]["price_reasoning"] = seller.get(
                "price_reasoning", "")

        # 안전거래 에이전트 결과 병합
        for seller in safety_results.get("recommended_sellers", []):
            seller_id = seller.get("seller_id")
            if seller_id not in all_sellers:
                all_sellers[seller_id] = {
                    "seller_id": seller_id, "seller_name": seller.get("seller_name")}
            all_sellers[seller_id]["safety_score"] = seller.get(
                "safety_score", 0)
            all_sellers[seller_id]["safety_reasoning"] = seller.get(
                "safety_reasoning", "")

        # 페르소나 매칭 에이전트 결과 병합
        for seller in persona_results.get("recommended_sellers", []):
            seller_id = seller.get("seller_id")
            if seller_id not in all_sellers:
                all_sellers[seller_id] = {
                    "seller_id": seller_id, "seller_name": seller.get("seller_name")}
            all_sellers[seller_id]["persona_score"] = seller.get(
                "persona_match_score", 0)
            all_sellers[seller_id]["persona_reasoning"] = seller.get(
                "persona_reasoning", "")

        # LLM 종합 점수 적용
        for seller_id in recommended_seller_ids:
            if str(seller_id) in all_sellers:
                seller = all_sellers[str(seller_id)]

                # LLM이 계산한 최종 점수
                final_score_data = decision.get("final_recommendations", {}).get(
                    "scores", {}).get(str(seller_id), {})

                final_recommendations.append({
                    "seller_id": seller["seller_id"],
                    "seller_name": seller["seller_name"],
                    "price_score": seller.get("price_score", 0),
                    "safety_score": seller.get("safety_score", 0),
                    "persona_score": seller.get("persona_score", 0),
                    "final_score": final_score_data.get("score", 0),
                    "final_reasoning": final_score_data.get("reasoning", ""),
                    "combination_explanation": decision.get("reasoning", "")
                })

        # 최종 점수 기준 정렬
        final_recommendations.sort(
            key=lambda x: x["final_score"], reverse=True)

        return final_recommendations


def final_matcher_node(state: RecommendationState) -> RecommendationState:
    """최종 매칭 에이전트 노드"""
    try:
        # 3개 서브에이전트 결과 가져오기
        price_results = state.get("price_agent_recommendations", {})
        safety_results = state.get("safety_agent_recommendations", {})
        persona_results = state.get("persona_matching_recommendations", {})

        if not price_results or not safety_results or not persona_results:
            raise ValueError("서브에이전트 결과가 완료되지 않았습니다.")

        # 최종 매칭 에이전트 실행
        matcher = FinalMatcher()

        # 3개 결과 종합
        final_recommendations = matcher.combine_sub_agent_results(
            price_results,
            safety_results,
            persona_results
        )

        # 결과를 상태에 저장
        state["final_seller_recommendations"] = final_recommendations
        state["current_step"] = "final_matched"
        state["completed_steps"].append("final_matching")

        print(f"최종 매칭 완료: {len(final_recommendations)}개 판매자 추천")

        # 상위 5개 출력
        for i, seller in enumerate(final_recommendations[:5], 1):
            print(
                f"  {i}. {seller['seller_name']} (최종점수: {seller['final_score']:.3f})")
            print(f"     가격: {seller['price_score']:.3f}, "
                  f"안전: {seller['safety_score']:.3f}, "
                  f"페르소나: {seller['persona_score']:.3f}")

    except Exception as e:
        state["error_message"] = f"최종 매칭 에이전트 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"최종 매칭 에이전트 오류: {e}")

    return state
