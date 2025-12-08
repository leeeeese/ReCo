"""
최종 통합 및 랭킹 에이전트
ProductAgent와 ReliabilityAgent의 결과를 통합하여
최종 판매자 랭킹 생성
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState
from server.utils.llm_agent import create_agent
from server.workflow.prompts import load_prompt
from server.utils.logger import get_logger
from server.utils.tools import match_products_to_sellers as rule_based_match

logger = get_logger(__name__)


class OrchestratorAgent:
    """최종 통합 및 랭킹 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("final_matcher")
        self.orchestrator_prompt = load_prompt(
            "orchestrator_recommendation_prompt")

    def finalize_recommendations(
        self,
        user_input: Dict[str, Any],
        product_agent_results: Dict[str, Any],
        reliability_agent_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        최종 추천 생성

        Args:
            user_input: 사용자 입력
            product_agent_results: ProductAgent 결과
            reliability_agent_results: ReliabilityAgent 결과

        Returns:
            최종 추천 결과
        """

        # -------------------------------------------------------------
        # 🔥 1) LLM에게 넘길 context 구성
        # -------------------------------------------------------------
        sub_agent_results = [
            {
                "agent": "product",
                "results": {
                    **product_agent_results,
                    "user_input": user_input,
                },
            },
            {
                "agent": "reliability",
                "results": {
                    **reliability_agent_results,
                    "user_input": user_input,
                },
            },
        ]

        context = {
            "sub_agent_results": sub_agent_results,
            "user_input": user_input,
        }

        # -------------------------------------------------------------
        # 🔥 2) LLM에게 판단 요청
        # -------------------------------------------------------------
        decision = self.llm_agent.decide(
            context=context,
            decision_task=self.orchestrator_prompt,
            format="json",
        )

        # -------------------------------------------------------------
        # 🔥 3) LLM 결과 파싱 및 상품 매칭
        # -------------------------------------------------------------
        final_recommendations = decision.get("final_recommendations", {})
        seller_ids = final_recommendations.get("seller_ids", [])
        scores = final_recommendations.get("scores", {})

        # 판매자 ID를 정수로 변환
        recommended_seller_ids = []
        for seller_id in seller_ids:
            try:
                recommended_seller_ids.append(int(seller_id))
            except (ValueError, TypeError):
                try:
                    recommended_seller_ids.append(int(str(seller_id)))
                except:
                    logger.warning(f"판매자 ID 변환 실패: {seller_id}")
                    continue

        # 판매자 정보 통합 (ProductAgent와 ReliabilityAgent 결과 병합)
        all_sellers = {}
        for seller in product_agent_results.get("recommended_sellers", []):
            seller_id = seller.get("seller_id")
            if seller_id:
                all_sellers[seller_id] = seller
        for seller in reliability_agent_results.get("recommended_sellers", []):
            seller_id = seller.get("seller_id")
            if seller_id and seller_id not in all_sellers:
                all_sellers[seller_id] = seller

        # 최종 추천된 판매자만 필터링
        recommended_sellers_list = [
            {"seller_id": sid, **all_sellers.get(sid, {})}
            for sid in recommended_seller_ids
            if sid in all_sellers
        ]

        # 룰베이스 기반 상품 매칭
        matched_sellers = rule_based_match(
            recommended_sellers_list,
            user_input,
        )

        # 최종 점수와 추론 정보 추가
        for matched_seller in matched_sellers:
            seller_id_str = str(matched_seller["seller_id"])
            if seller_id_str in scores:
                matched_seller["final_score"] = scores[seller_id_str].get(
                    "score", 0.5)
                matched_seller["final_reasoning"] = scores[seller_id_str].get(
                    "reasoning", "")
                matched_seller["match_explanation"] = scores[seller_id_str].get(
                    "match_explanation", "")
            else:
                # LLM 결과에 없으면 기본값 사용
                matched_seller["final_score"] = (
                    matched_seller["product_score"] * 0.5 +
                    matched_seller["reliability_score"] * 0.5
                )
                matched_seller["final_reasoning"] = "상품 특성과 신뢰도를 종합하여 추천합니다."
                matched_seller["match_explanation"] = "균형 잡힌 선택을 원하는 사용자에게 적합합니다."

        # 최종 점수 기준 정렬
        matched_sellers.sort(key=lambda x: x.get(
            "final_score", 0.5), reverse=True)

        return {
            "recommended_sellers": matched_sellers,
            "reasoning": decision.get("reasoning", "최종 추천 완료"),
        }


def orchestrator_agent_node(state: RecommendationState) -> RecommendationState:
    """최종 통합 및 랭킹 에이전트 노드"""
    try:
        user_input = state["user_input"]
        product_agent_results = state.get("product_agent_recommendations", {})
        reliability_agent_results = state.get(
            "reliability_agent_recommendations", {})

        # 최종 통합 에이전트 실행
        agent = OrchestratorAgent()

        # 최종 추천 생성
        final_results = agent.finalize_recommendations(
            user_input,
            product_agent_results,
            reliability_agent_results,
        )

        logger.info(
            "최종 통합 에이전트 분석 완료",
            extra={"recommended_sellers": len(
                final_results.get("recommended_sellers", []))},
        )

        return {
            "final_recommendations": final_results,
            "current_step": "completed",
            "completed_steps": ["orchestration"],
        }

    except Exception as e:
        logger.exception("최종 통합 에이전트 오류")
        # Fallback: 단순 결합 로직
        try:
            product_sellers = product_agent_results.get(
                "recommended_sellers", [])
            reliability_sellers = reliability_agent_results.get(
                "recommended_sellers", [])

            # 판매자 ID 수집
            seller_ids = set()
            for seller in product_sellers:
                seller_ids.add(seller.get("seller_id"))
            for seller in reliability_sellers:
                seller_ids.add(seller.get("seller_id"))

            # 단순 결합
            seller_dict = {}
            for seller in product_sellers:
                seller_id = seller.get("seller_id")
                seller_dict[seller_id] = {
                    **seller,
                    "reliability_score": 0.5,
                }
            for seller in reliability_sellers:
                seller_id = seller.get("seller_id")
                if seller_id in seller_dict:
                    seller_dict[seller_id]["reliability_score"] = seller.get(
                        "reliability_score", 0.5)
                else:
                    seller_dict[seller_id] = {
                        **seller,
                        "product_score": 0.5,
                    }

            # 최종 점수 계산 (기본 가중치: 50:50)
            fallback_sellers = []
            for seller_id, seller_data in seller_dict.items():
                product_score = seller_data.get("product_score", 0.5)
                reliability_score = seller_data.get("reliability_score", 0.5)
                final_score = product_score * 0.5 + reliability_score * 0.5

                fallback_sellers.append({
                    "seller_id": seller_id,
                    "seller_name": seller_data.get("seller_name", ""),
                    "products": seller_data.get("products", []),
                    "final_score": final_score,
                    "product_score": product_score,
                    "reliability_score": reliability_score,
                    "final_reasoning": "LLM 오류로 인해 기본 결합 로직을 사용했습니다.",
                    "match_explanation": "균형 잡힌 선택을 원하는 사용자에게 적합합니다.",
                })

            fallback_sellers.sort(key=lambda x: x["final_score"], reverse=True)

            return {
                "final_recommendations": {
                    "recommended_sellers": fallback_sellers,
                    "reasoning": "LLM 오류로 인해 기본 결합 로직을 사용했습니다.",
                },
                "current_step": "completed",
                "completed_steps": ["orchestration"],
            }
        except Exception as fallback_error:
            logger.exception("Fallback 로직도 실패")
            return {
                "final_recommendations": {
                    "recommended_sellers": [],
                    "reasoning": f"최종 통합 에이전트 오류: {str(e)}",
                },
                "current_step": "error",
                "completed_steps": ["orchestration"],
            }
