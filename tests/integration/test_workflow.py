"""
워크플로우 통합 테스트
"""

import pytest
from unittest.mock import patch
from server.workflow.graph import recommendation_workflow
from server.workflow.state import RecommendationState


@pytest.mark.integration
@pytest.mark.workflow
class TestRecommendationWorkflow:
    """추천 워크플로우 통합 테스트"""

    # graph.py 안에서 사용 중인 노드 함수들을 직접 patch 해야 함
    @patch("server.workflow.graph.orchestrator_agent_node")
    @patch("server.workflow.graph.safety_agent_node")
    @patch("server.workflow.graph.price_agent_node")
    def test_workflow_full_execution(
        self,
        mock_price_node,
        mock_safety_node,
        mock_orch_node,
    ):
        """전체 워크플로우 실행 테스트"""

        test_product = {
            "product_id": 1,
            "seller_id": 101,
            "title": "아이폰 14 프로",
            "price": 850000,
        }

        # price_agent_node 가 DB 안 타고 이 결과만 state 에 반영하도록 함
        # user_input은 변경하지 않으므로 반환하지 않음 (LastValue 채널 중복 write 방지)
        def price_node_side_effect(state: RecommendationState):
            return {
                "price_agent_recommendations": {
                    "recommended_sellers": [
                        {
                            "seller_id": 101,
                            "seller_name": "테스트 판매자",
                            "price_score": 0.8,
                            "price_reasoning": "합리적인 가격",
                            "products": [test_product],
                        }
                    ],
                    "market_analysis": {},
                    "reasoning": "가격 관점 분석 완료",
                },
                "current_step": "price_analyzed",
                "completed_steps": ["price_analysis"],  # add reducer 사용
            }

        # safety_agent_node 도 마찬가지로 mock
        # user_input은 변경하지 않으므로 반환하지 않음
        def safety_node_side_effect(state: RecommendationState):
            return {
                "safety_agent_recommendations": {
                    "recommended_sellers": [
                        {
                            "seller_id": 101,
                            "seller_name": "테스트 판매자",
                            "safety_score": 0.85,
                            "safety_reasoning": "신뢰할 수 있는 판매자",
                            "products": [test_product],
                        }
                    ],
                    "reasoning": "안전거래 관점에서 신뢰할 수 있는 판매자 추천 완료",
                },
                "current_step": "safety_analyzed",
                "completed_steps": ["safety_analysis"],  # add reducer 사용
            }

        # orchestrator_agent_node 도 LLM 안 타고 최종 결과만 합성하도록 mock
        # user_input은 변경하지 않으므로 반환하지 않음
        # 이제는 상품 매칭도 룰베이스로 처리되므로 products 포함된 판매자 리스트 반환
        def orchestrator_side_effect(state: RecommendationState):
            return {
                "final_seller_recommendations": [
                    {
                        "seller_id": 101,
                        "seller_name": "테스트 판매자",
                        "price_score": 0.8,
                        "safety_score": 0.85,
                        "final_score": 0.82,
                        "final_reasoning": "통합 테스트",
                        "products": [test_product]  # 룰베이스로 매칭된 상품
                    }
                ],
                "final_item_scores": [
                    {
                        **test_product,
                        "match_score": 0.82,
                        "seller_name": "테스트 판매자",
                        "seller_price_score": 0.8,
                        "seller_safety_score": 0.85,
                        "seller_final_score": 0.82,
                    }
                ],
                "ranking_explanation": "LLM 기반 판매자 추천 완료, 상품 매칭은 룰베이스로 처리",
                "current_step": "recommendation_completed",
                "completed_steps": ["recommendation"],  # add reducer 사용
            }

        mock_price_node.side_effect = price_node_side_effect
        mock_safety_node.side_effect = safety_node_side_effect
        mock_orch_node.side_effect = orchestrator_side_effect

        workflow_app = recommendation_workflow()
        initial_state: RecommendationState = {
            "user_input": {
                "search_query": "아이폰 14 프로",
                "trust_safety": 70.0,
                "quality_condition": 80.0,
                "remote_transaction": 60.0,
                "activity_responsiveness": 75.0,
                "price_flexibility": 65.0,
            },
            "search_query": {},
            "persona_classification": None,
            "price_agent_recommendations": None,
            "safety_agent_recommendations": None,
            "final_seller_recommendations": None,
            "final_item_scores": None,
            "ranking_explanation": "",
            "current_step": "start",
            "completed_steps": [],
            "error_message": None,
            "execution_start_time": None,
            "execution_time": None,
        }

        final_state = workflow_app.invoke(initial_state)

        # --- 검증 ---
        assert final_state["current_step"] == "recommendation_completed"
        assert "completed_steps" in final_state
        assert "price_analysis" in final_state["completed_steps"]
        assert "safety_analysis" in final_state["completed_steps"]
        assert "recommendation" in final_state["completed_steps"]

        assert final_state["final_seller_recommendations"] is not None
        assert final_state["final_seller_recommendations"][0]["seller_id"] == 101
        assert final_state["final_item_scores"] is not None
        assert len(final_state["final_item_scores"]) > 0
        assert final_state["final_item_scores"][0]["product_id"] == 1

    # init 테스트도 동일하게 graph 노드를 patch 해서 DB 호출 막기
    @patch("server.workflow.graph.orchestrator_agent_node")
    @patch("server.workflow.graph.safety_agent_node")
    @patch("server.workflow.graph.price_agent_node")
    def test_workflow_init_node(
        self,
        mock_price_node,
        mock_safety_node,
        mock_orch_node,
    ):
        """워크플로우 초기 상태에서 기본 플로우 동작 테스트"""

        test_product = {
            "product_id": 1,
            "seller_id": 101,
            "title": "아이폰",
            "price": 800000,
        }

        def price_node_side_effect(state: RecommendationState):
            # user_input은 변경하지 않으므로 반환하지 않음
            return {
                "price_agent_recommendations": {
                    "recommended_sellers": [
                        {
                            "seller_id": 101,
                            "seller_name": "테스트 판매자",
                            "price_score": 0.75,
                            "price_reasoning": "테스트용 가격 점수",
                            "products": [test_product],
                        }
                    ],
                    "market_analysis": {},
                    "reasoning": "가격 관점 분석 완료",
                },
                "current_step": "price_analyzed",
                "completed_steps": ["price_analysis"],  # add reducer 사용
            }

        def safety_node_side_effect(state: RecommendationState):
            # user_input은 변경하지 않으므로 반환하지 않음
            return {
                "safety_agent_recommendations": {
                    "recommended_sellers": [
                        {
                            "seller_id": 101,
                            "seller_name": "테스트 판매자",
                            "safety_score": 0.9,
                            "safety_reasoning": "테스트용 안전 점수",
                            "products": [test_product],
                        }
                    ],
                    "reasoning": "안전거래 관점에서 신뢰할 수 있는 판매자 추천 완료",
                },
                "current_step": "safety_analyzed",
                "completed_steps": ["safety_analysis"],  # add reducer 사용
            }

        def orchestrator_side_effect(state: RecommendationState):
            # init 테스트에서는 너무 세게 검증 안 하고, 기본 결과만 채워줌
            # user_input은 변경하지 않으므로 반환하지 않음
            # 이제는 상품 매칭도 룰베이스로 처리되므로 products 포함된 판매자 리스트 반환
            return {
                "final_seller_recommendations": [
                    {
                        "seller_id": 101,
                        "seller_name": "테스트 판매자",
                        "price_score": 0.75,
                        "safety_score": 0.9,
                        "final_score": 0.8,
                        "final_reasoning": "init 테스트",
                        "products": [test_product]  # 룰베이스로 매칭된 상품
                    }
                ],
                "final_item_scores": [
                    {
                        **test_product,
                        "match_score": 0.8,
                        "seller_name": "테스트 판매자",
                        "seller_price_score": 0.75,
                        "seller_safety_score": 0.9,
                        "seller_final_score": 0.8,
                    }
                ],
                "ranking_explanation": "LLM 기반 판매자 추천 완료, 상품 매칭은 룰베이스로 처리",
                "current_step": "recommendation_completed",
                "completed_steps": ["recommendation"],  # add reducer 사용
            }

        mock_price_node.side_effect = price_node_side_effect
        mock_safety_node.side_effect = safety_node_side_effect
        mock_orch_node.side_effect = orchestrator_side_effect

        workflow_app = recommendation_workflow()
        initial_state: RecommendationState = {
            "user_input": {
                "search_query": "아이폰",
                "trust_safety": 70.0,
                "quality_condition": 80.0,
                "remote_transaction": 60.0,
                "activity_responsiveness": 75.0,
                "price_flexibility": 65.0,
            },
            "search_query": {},
            "persona_classification": None,
            "price_agent_recommendations": None,
            "safety_agent_recommendations": None,
            "final_seller_recommendations": None,
            "final_item_scores": None,
            "ranking_explanation": "",
            "current_step": "start",
            "completed_steps": [],
            "error_message": None,
            "execution_start_time": None,
            "execution_time": None,
        }

        final_state = workflow_app.invoke(initial_state)

        # --- 검증 ---
        assert "user_input" in final_state
        assert final_state["user_input"]["search_query"] == "아이폰"

        # 초기 플로우에서 persona / search_query 등 기본 필드가 세팅되어 있는지만 확인
        assert "persona_classification" in final_state
        assert "search_query" in final_state

        # 에이전트/오케스트레이터가 한 번은 돌았는지
        assert "completed_steps" in final_state
        assert "price_analysis" in final_state["completed_steps"]
        assert "safety_analysis" in final_state["completed_steps"]
        assert "recommendation" in final_state["completed_steps"]
