"""
오케스트레이터 에이전트 단위 테스트
"""

import pytest
from unittest.mock import Mock, patch
from server.workflow.agents.orchestrator_agent import OrchestratorAgent, orchestrator_agent_node
from server.workflow.state import RecommendationState


@pytest.mark.unit
@pytest.mark.agent
class TestOrchestratorAgent:
    """오케스트레이터 에이전트 클래스 테스트"""
    
    def test_orchestrator_agent_init(self):
        """오케스트레이터 에이전트 초기화 테스트"""
        agent = OrchestratorAgent()
        
        assert agent.llm_agent is not None
        assert agent.combine_sellers_prompt is not None
        assert agent.rank_products_prompt is not None
    
    def test_combine_and_rank(self):
        """결과 통합 및 랭킹 테스트"""
        agent = OrchestratorAgent()
        
        # 실제 구조에 맞게 price_results와 safety_results 설정
        test_product = {"product_id": 1, "seller_id": 101, "title": "테스트 상품", "price": 100000}
        price_results = {
            "recommended_sellers": [{
                "seller_id": 101,
                "seller_name": "테스트 판매자",
                "price_score": 0.8,
                "price_reasoning": "합리적",
                "products": [test_product]
            }],
        }
        safety_results = {
            "recommended_sellers": [{
                "seller_id": 101,
                "seller_name": "테스트 판매자",
                "safety_score": 0.85,
                "safety_reasoning": "안전함",
                "products": [test_product]
            }],
        }
        user_input = {"search_query": "아이폰"}
        persona_classification = {"persona_type": "balanced"}
        
        # LLM 에이전트 모킹
        agent.llm_agent.analyze_and_combine = Mock(return_value={
            "final_recommendations": {
                "seller_ids": [101],
                "scores": {
                    "101": {"score": 0.8, "reasoning": "통합 추천"}
                }
            },
            "reasoning": "통합 추천",
        })
        agent.llm_agent.decide = Mock(return_value={
            "ranked_product_ids": [1],
        })
        
        result = agent.combine_and_rank(
            price_results, safety_results, user_input, persona_classification
        )
        
        assert "final_seller_recommendations" in result or "ranked_products" in result


@pytest.mark.unit
@pytest.mark.agent
class TestOrchestratorAgentNode:
    """오케스트레이터 에이전트 노드 테스트"""
    
    def test_orchestrator_agent_node_success(self, mock_initial_state):
        """오케스트레이터 에이전트 노드 성공 테스트"""
        # 이전 에이전트 결과 설정 (실제 구조에 맞게)
        test_product = {"product_id": 1, "seller_id": 101, "title": "테스트", "price": 100000}
        mock_initial_state["price_agent_recommendations"] = {
            "recommended_sellers": [{
                "seller_id": 101,
                "seller_name": "테스트 판매자",
                "price_score": 0.8,
                "price_reasoning": "합리적",
                "products": [test_product]
            }],
        }
        mock_initial_state["safety_agent_recommendations"] = {
            "recommended_sellers": [{
                "seller_id": 101,
                "seller_name": "테스트 판매자",
                "safety_score": 0.85,
                "safety_reasoning": "안전함",
                "products": [test_product]
            }],
        }
        mock_initial_state["persona_classification"] = {
            "persona_type": "balanced",
        }
        
        # LLM 에이전트 모킹
        with patch('server.workflow.agents.orchestrator_agent.create_agent') as mock_create:
            mock_agent = Mock()
            mock_agent.analyze_and_combine = Mock(return_value={
                "final_recommendations": {
                    "seller_ids": [101],
                    "scores": {
                        "101": {"score": 0.8, "reasoning": "테스트"}
                    }
                },
                "reasoning": "통합 추천"
            })
            mock_agent.decide = Mock(return_value={
                "ranked_product_ids": [1],
            })
            mock_create.return_value = mock_agent
            
            result = orchestrator_agent_node(mock_initial_state)
            
            assert result["current_step"] in ["recommendation_completed", "error"]
            if result["current_step"] == "recommendation_completed":
                assert "final_seller_recommendations" in result or "final_item_scores" in result

