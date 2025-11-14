"""
페르소나 매칭 에이전트
LLM 기반으로 사용자와 판매자의 페르소나를 비교하여
가장 잘 어울리는 판매자를 추천
"""

from typing import Dict, Any, List
from server.workflow.state import RecommendationState, PersonaVector
from server.utils.llm_agent import create_agent
from server.db.persona_service import get_sellers_with_persona


class PersonaMatchingAgent:
    """페르소나 매칭 에이전트 - LLM 기반 자율 판단"""

    def __init__(self):
        self.llm_agent = create_agent("persona_matching_agent")

    def recommend_sellers_by_persona(self,
                                     user_persona: Dict[str, Any],
                                     sellers_with_persona: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        페르소나 관점에서 판매자 추천

        Args:
            user_persona: 사용자 페르소나 정보
            sellers_with_persona: 판매자 페르소나 정보

        Returns:
            페르소나 매칭 점수와 함께 판매자 리스트
        """
        # 페르소나 비교 데이터 구성
        persona_comparison_data = []
        for seller in sellers_with_persona:
            persona_comparison_data.append({
                "seller_id": seller.get("seller_id"),
                "seller_name": seller.get("seller_name"),
                "seller_persona_vector": seller.get("persona_vector", {}),
                "seller_persona_type": seller.get("persona_type"),
                "seller_characteristics": seller.get("characteristics", [])
            })

        # LLM에게 판단 요청
        context = {
            "user_persona_type": user_persona.get("persona_type"),
            "user_persona_vector": user_persona.get("vector", {}),
            "user_preferences": user_persona.get("matched_prototype", {}),
            "sellers": persona_comparison_data[:20]
        }

        decision = self.llm_agent.decide(
            context=context,
            decision_task="사용자 페르소나와 판매자 페르소나를 비교하여 가장 잘 어울리는 판매자를 추천해주세요. "
            "선호도, 거래 스타일, 활동성 등 복합적인 요소를 종합 고려하세요.",
            format="json"
        )

        # LLM 결과를 기반으로 판매자 점수 계산
        recommended_sellers = []
        for seller in sellers_with_persona:
            seller_id = seller.get("seller_id")
            seller_score = decision.get(
                "recommended_sellers", {}).get(str(seller_id), {})

            recommended_sellers.append({
                "seller_id": seller_id,
                "seller_name": seller.get("seller_name"),
                "persona_match_score": seller_score.get("score", 0.5),
                "persona_reasoning": seller_score.get("reasoning", ""),
                "matched_characteristics": seller_score.get("matched_characteristics", []),
                "compatibility_level": seller_score.get("compatibility", "medium"),
                "products": seller.get("products", [])
            })

        # 페르소나 매칭 점수 기준 정렬
        recommended_sellers.sort(
            key=lambda x: x["persona_match_score"], reverse=True)

        return recommended_sellers


def persona_matching_agent_node(state: RecommendationState) -> RecommendationState:
    """페르소나 매칭 에이전트 노드"""
    try:
        persona_classification = state.get("persona_classification")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        # 페르소나 매칭 에이전트 실행
        agent = PersonaMatchingAgent()

        # DB에서 조회
        try:
            sellers_with_persona = get_sellers_with_persona(
                limit=50, min_reviews=1)

            if not sellers_with_persona:
                raise ValueError("DB에서 판매자 데이터를 찾을 수 없습니다.")

            print(f"DB에서 {len(sellers_with_persona)}개 판매자 조회 완료 (페르소나 계산됨)")
        except Exception as e:
            raise ValueError(f"페르소나 매칭 에이전트 데이터 조회 실패: {e}")

        # 페르소나 관점에서 판매자 추천
        persona_recommendations = agent.recommend_sellers_by_persona(
            persona_classification,
            sellers_with_persona
        )

        # 결과를 상태에 저장
        state["persona_matching_recommendations"] = {
            "recommended_sellers": persona_recommendations,
            "reasoning": "페르소나 관점에서 가장 잘 어울리는 판매자 추천 완료"
        }
        state["current_step"] = "persona_matched"
        state["completed_steps"].append("persona_matching")

        print(f"페르소나 매칭 에이전트 분석 완료: {len(persona_recommendations)}개 판매자 추천")

    except Exception as e:
        state["error_message"] = f"페르소나 매칭 에이전트 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"페르소나 매칭 에이전트 오류: {e}")

    return state
