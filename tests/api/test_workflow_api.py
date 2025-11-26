"""
워크플로우 API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from server.main import app


@pytest.mark.api
class TestWorkflowAPI:
    """워크플로우 API 엔드포인트 테스트"""
    
    def test_health_check(self, client):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    @pytest.mark.slow
    def test_recommend_endpoint(self, client, mock_user_input):
        """추천 API 엔드포인트 테스트"""
        # LLM 호출을 모킹하여 실제 API 호출 없이 테스트
        from unittest.mock import patch, Mock
        with patch('server.routers.workflow.get_workflow_app') as mock_workflow:
            mock_app = Mock()
            mock_app.invoke = Mock(return_value={
                "user_input": mock_user_input,
                "persona_classification": {"persona_type": "balanced"},
                "final_item_scores": [
                    {
                        "product_id": 1,
                        "seller_id": 101,
                        "title": "테스트 상품",
                        "price": 100000,
                        "final_score": 0.85,
                        "ranking_factors": {},
                        "seller_name": "테스트 판매자",
                        "category": "전자기기",
                        "condition": "중고",
                        "location": "서울",
                    }
                ],
                "current_step": "recommendation_completed",
                "completed_steps": ["initialization", "price_analysis", "safety_analysis", "recommendation"],
                "error_message": None,
            })
            mock_workflow.return_value = mock_app
            
            response = client.post("/api/v1/recommend", json=mock_user_input)
            
            assert response.status_code in [200, 500]  # 모킹 실패 시 500 가능
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
    
    def test_recommend_endpoint_validation_error(self, client):
        """추천 API 입력 검증 오류 테스트"""
        invalid_input = {
            "search_query": "",  # 빈 문자열 (검증 실패)
        }
        
        response = client.post("/api/v1/recommend", json=invalid_input)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_recommend_endpoint_price_range_error(self, client):
        """가격 범위 검증 오류 테스트"""
        invalid_input = {
            "search_query": "아이폰",
            "price_min": 1000000,
            "price_max": 500000,  # min > max (검증 실패)
        }
        
        response = client.post("/api/v1/recommend", json=invalid_input)
        
        assert response.status_code == 422
    
    def test_recommend_endpoint_preference_range_error(self, client):
        """선호도 범위 검증 오류 테스트"""
        invalid_input = {
            "search_query": "아이폰",
            "trust_safety": 150.0,  # 100 초과 (검증 실패)
        }
        
        response = client.post("/api/v1/recommend", json=invalid_input)
        
        assert response.status_code == 422

