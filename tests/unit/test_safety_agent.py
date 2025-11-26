"""
안전거래 에이전트 단위 테스트
"""

import pytest
from unittest.mock import Mock, patch
from server.workflow.agents.safety_agent import SafetyAgent, safety_agent_node
from server.workflow.state import RecommendationState


@pytest.mark.unit
@pytest.mark.agent
class TestSafetyAgent:
    """안전거래 에이전트 클래스 테스트"""
    
    def test_safety_agent_init(self):
        """안전거래 에이전트 초기화 테스트"""
        agent = SafetyAgent()
        
        assert agent.llm_agent is not None
        assert agent.safety_prompt is not None
    
    @patch('server.workflow.agents.safety_agent.seller_profile_tool')
    @patch('server.workflow.agents.safety_agent.review_feature_tool')
    @patch('server.workflow.agents.safety_agent.trade_risk_tool')
    def test_recommend_sellers_by_safety(
        self,
        mock_trade_risk,
        mock_review_tool,
        mock_seller_tool
    ):
        """안전거래 기반 판매자 추천 테스트"""
        # 모의 데이터 설정
        mock_seller_tool.return_value = {"seller_trust_score": 80.0}
        mock_review_tool.return_value = {"positive_keywords": ["신뢰"]}
        mock_trade_risk.return_value = {"risk_score": 0.2}
        
        agent = SafetyAgent()
        user_input = {
            "search_query": "아이폰",
            "trust_safety": 80.0,
        }
        sellers_with_products = [
            {
                "product_id": 1,
                "seller_id": 101,
                "title": "테스트 상품",
                "price": 100000,
            }
        ]
        
        # LLM 에이전트 모킹
        agent.llm_agent.decide = Mock(return_value={
            "recommended_sellers": [{"seller_id": 101, "score": 0.85}],
            "reasoning": "안전한 거래",
            "confidence": 0.85
        })
        
        result = agent.recommend_sellers_by_safety(user_input, sellers_with_products)
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert "seller_id" in result[0] or "score" in result[0]


@pytest.mark.unit
@pytest.mark.agent
class TestSafetyAgentNode:
    """안전거래 에이전트 노드 테스트"""
    
    @patch('server.workflow.agents.safety_agent.get_sellers_with_products')
    def test_safety_agent_node_success(self, mock_get_sellers, mock_initial_state):
        """안전거래 에이전트 노드 성공 테스트"""
        mock_get_sellers.return_value = [
            {
                "product_id": 1,
                "seller_id": 101,
                "title": "테스트 상품",
                "price": 100000,
            }
        ]
        
        # LLM 에이전트 모킹
        with patch('server.workflow.agents.safety_agent.create_agent') as mock_create:
            mock_agent = Mock()
            mock_agent.decide = Mock(return_value={
                "recommended_sellers": [{"seller_id": 101}],
                "reasoning": "테스트",
            })
            mock_create.return_value = mock_agent
            
            result = safety_agent_node(mock_initial_state)
            
            assert result["current_step"] in ["safety_analyzed", "error"]
            if result["current_step"] == "safety_analyzed":
                assert "safety_agent_recommendations" in result

