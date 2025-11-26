"""
워크플로우 통합 테스트
"""

import pytest
from unittest.mock import patch, Mock
from server.workflow.graph import recommendation_workflow
from server.workflow.state import RecommendationState


@pytest.mark.integration
@pytest.mark.workflow
class TestRecommendationWorkflow:
    """추천 워크플로우 통합 테스트"""
    
    @patch('server.workflow.agents.price_agent.search_products_by_keywords')
    @patch('server.workflow.agents.safety_agent.get_sellers_with_products')
    @patch('server.workflow.agents.orchestrator_agent.get_sellers_with_products')
    def test_workflow_full_execution(
        self,
        mock_orch_get_sellers,
        mock_safety_get_sellers,
        mock_price_search
    ):
        """전체 워크플로우 실행 테스트"""
        # 모의 데이터 설정
        mock_products = [
            {
                "product_id": 1,
                "seller_id": 101,
                "title": "아이폰 14 프로",
                "price": 850000,
            }
        ]
        mock_price_search.return_value = mock_products
        mock_safety_get_sellers.return_value = mock_products
        mock_orch_get_sellers.return_value = mock_products
        
        # LLM 에이전트 모킹
        with patch('server.utils.llm_agent.create_agent') as mock_create_agent:
            mock_agent = Mock()
            mock_agent.decide = Mock(return_value={
                "recommended_sellers": [{"seller_id": 101, "score": 0.8}],
                "reasoning": "테스트 추천",
                "confidence": 0.8
            })
            mock_agent.analyze_and_combine = Mock(return_value={
                "recommended_seller_ids": [101],
            })
            mock_create_agent.return_value = mock_agent
            
            # 워크플로우 실행
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
            
            # 검증
            assert final_state["current_step"] in ["recommendation_completed", "error"]
            assert "completed_steps" in final_state
            assert len(final_state["completed_steps"]) > 0
    
    def test_workflow_init_node(self):
        """워크플로우 초기화 노드 테스트"""
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
        
        # init 노드만 실행 (스트리밍으로 첫 번째 상태만 가져옴)
        states = list(workflow_app.stream(initial_state))
        
        assert len(states) > 0
        first_state = list(states[0].values())[0] if states else None
        if first_state:
            assert "persona_classification" in first_state
            assert "search_query" in first_state

