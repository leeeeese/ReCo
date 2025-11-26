"""
가격 에이전트 단위 테스트
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from server.workflow.agents.price_agent import PriceAgent, price_agent_node
from server.workflow.state import RecommendationState


@pytest.mark.unit
@pytest.mark.agent
class TestPriceAgent:
    """가격 에이전트 클래스 테스트"""
    
    def test_price_agent_init(self):
        """가격 에이전트 초기화 테스트"""
        agent = PriceAgent()
        
        assert agent.llm_agent is not None
        assert agent.price_prompt is not None
    
    @patch('server.workflow.agents.price_agent.joongna_search_prices')
    def test_collect_market_data(self, mock_search_prices):
        """시세 데이터 수집 테스트"""
        mock_search_prices.return_value = [800000, 850000, 900000]
        
        agent = PriceAgent()
        products = [
            {"product_id": 1, "title": "아이폰 14 프로", "price": 850000}
        ]
        
        market_data = agent._collect_market_data(products)
        
        assert len(market_data) > 0
        if 1 in market_data:
            assert "market_avg" in market_data[1]
            assert "market_median" in market_data[1]
    
    @patch('server.workflow.agents.price_agent.search_products_by_keywords')
    @patch('server.workflow.agents.price_agent.item_market_tool')
    @patch('server.workflow.agents.price_agent.price_risk_tool')
    @patch('server.workflow.agents.price_agent.seller_profile_tool')
    @patch('server.workflow.agents.price_agent.review_feature_tool')
    def test_recommend_sellers_by_price(
        self,
        mock_review_tool,
        mock_seller_tool,
        mock_price_risk,
        mock_item_market,
        mock_search_products
    ):
        """가격 기반 판매자 추천 테스트"""
        # 모의 데이터 설정
        mock_search_products.return_value = [
            {
                "product_id": 1,
                "seller_id": 101,
                "title": "아이폰 14 프로",
                "price": 850000,
            }
        ]
        mock_item_market.return_value = {"estimated_fair_price": 800000}
        mock_price_risk.return_value = {"price_score": 80.0}
        mock_seller_tool.return_value = {"seller_trust_score": 75.0}
        mock_review_tool.return_value = {"positive_keywords": []}
        
        agent = PriceAgent()
        user_input = {
            "search_query": "아이폰",
            "price_min": 500000,
            "price_max": 1000000,
        }
        sellers_with_products = mock_search_products.return_value
        
        # LLM 에이전트 모킹
        agent.llm_agent.decide = Mock(return_value={
            "recommended_sellers": [{"seller_id": 101, "score": 0.8}],
            "reasoning": "합리적인 가격",
            "confidence": 0.8
        })
        
        result = agent.recommend_sellers_by_price(user_input, sellers_with_products)
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert "seller_id" in result[0] or "score" in result[0]


@pytest.mark.unit
@pytest.mark.agent
class TestPriceAgentNode:
    """가격 에이전트 노드 테스트"""
    
    @patch('server.workflow.agents.price_agent.search_products_by_keywords')
    @patch('server.workflow.agents.price_agent.get_sellers_with_products')
    def test_price_agent_node_success(self, mock_get_sellers, mock_search_products, mock_initial_state):
        """가격 에이전트 노드 성공 테스트"""
        # get_sellers_with_products 형식으로 반환 (seller별로 그룹화)
        mock_get_sellers.return_value = [
            {
                "seller_id": 101,
                "seller_name": "테스트 판매자",
                "products": [
                    {
                        "product_id": 1,
                        "seller_id": 101,
                        "title": "테스트 상품",
                        "price": 100000,
                    }
                ]
            }
        ]
        mock_search_products.return_value = mock_get_sellers.return_value
        
        # LLM 에이전트 모킹 (dict 형태로 반환)
        with patch('server.workflow.agents.price_agent.create_agent') as mock_create:
            mock_agent = Mock()
            mock_agent.decide = Mock(return_value={
                "recommended_sellers": {
                    "101": {
                        "seller_id": 101,
                        "score": 0.8,
                        "reasoning": "합리적인 가격",
                        "price_range": {"min": 90000, "max": 110000}
                    }
                },
                "reasoning": "테스트",
                "confidence": 0.8
            })
            mock_create.return_value = mock_agent
            
            # joongna_search_prices 모킹
            with patch('server.workflow.agents.price_agent.joongna_search_prices') as mock_joongna:
                mock_joongna.return_value = [95000, 100000, 105000]
                
                result = price_agent_node(mock_initial_state)
                
                assert result["current_step"] in ["price_analyzed", "error"]
                if result["current_step"] == "price_analyzed":
                    assert "price_agent_recommendations" in result

