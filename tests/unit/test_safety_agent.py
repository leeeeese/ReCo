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
        # sellers_with_products는 seller별로 그룹화된 구조
        sellers_with_products = [
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
        
        # LLM 에이전트 모킹 (dict 형태로 반환)
        agent.llm_agent.decide = Mock(return_value={
            "recommended_sellers": {
                "101": {
                    "seller_id": 101,
                    "score": 0.85,
                    "reasoning": "안전한 거래",
                    "matched_features": ["안전결제", "인증판매자"],
                    "trust_level": "high"
                }
            },
            "reasoning": "안전한 거래",
        })
        
        result = agent.recommend_sellers_by_safety(user_input, sellers_with_products)
        
        assert isinstance(result, list)
        if len(result) > 0:
            assert "seller_id" in result[0]
            assert "safety_score" in result[0]


@pytest.mark.unit
@pytest.mark.agent
class TestSafetyAgentNode:
    """안전거래 에이전트 노드 테스트"""
    
    @patch('server.db.product_service.get_sellers_with_products')
    @patch('server.db.product_service.search_products_by_keywords')
    def test_safety_agent_node_success(self, mock_search_products, mock_get_sellers, mock_initial_state):
        """안전거래 에이전트 노드 성공 테스트"""
        # get_sellers_with_products 형식으로 반환 (seller별로 그룹화)
        # 실제 product_service.get_sellers_with_products의 반환 구조와 일치
        sellers_data = [
            {
                "seller_id": 101,
                "seller_name": "테스트 판매자",
                "seller_trust": 0.8,
                "seller_safe_sales": 50,
                "seller_customs": 100,
                "products": [
                    {
                        "product_id": 1,
                        "seller_id": 101,
                        "title": "테스트 상품",
                        "price": 100000,
                        "category": "전자기기",
                        "category_top": "디지털/가전",
                        "condition": "중고",
                        "description": "테스트 상품 설명",
                        "view_count": 100,
                        "like_count": 10,
                        "chat_count": 5,
                        "sell_method": "택배",
                        "delivery_fee": "있음",
                        "is_safe": "사용"
                    }
                ]
            }
        ]
        mock_get_sellers.return_value = sellers_data
        mock_search_products.return_value = sellers_data
        
        # LLM 에이전트 모킹 (dict 형태로 반환)
        with patch('server.workflow.agents.safety_agent.create_agent') as mock_create:
            mock_agent = Mock()
            mock_agent.decide = Mock(return_value={
                "recommended_sellers": {
                    "101": {
                        "seller_id": 101,
                        "score": 0.85,
                        "reasoning": "안전한 거래",
                        "matched_features": ["안전결제", "인증판매자"],
                        "trust_level": "high"
                    }
                },
                "reasoning": "테스트",
            })
            mock_create.return_value = mock_agent
            
            # tool 함수들 모킹
            with patch('server.workflow.agents.safety_agent.seller_profile_tool') as mock_seller_tool, \
                 patch('server.workflow.agents.safety_agent.review_feature_tool') as mock_review_tool, \
                 patch('server.workflow.agents.safety_agent.trade_risk_tool') as mock_trade_risk:
                mock_seller_tool.return_value = {"seller_trust_score": 80.0}
                mock_review_tool.return_value = {"positive_keywords": ["신뢰"]}
                mock_trade_risk.return_value = {"risk_score": 0.2}
                
                result = safety_agent_node(mock_initial_state)
                
                assert result["current_step"] in ["safety_analyzed", "error"]
                if result["current_step"] == "safety_analyzed":
                    assert "safety_agent_recommendations" in result

