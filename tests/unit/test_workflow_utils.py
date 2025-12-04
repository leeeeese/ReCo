"""
워크플로우 유틸리티 함수 단위 테스트
"""

import pytest
from server.utils.workflow_utils import classify_persona, generate_search_query
from server.workflow.state import PersonaType


@pytest.mark.unit
class TestClassifyPersona:
    """페르소나 분류 함수 테스트"""
    
    def test_classify_persona_basic(self):
        """기본 페르소나 분류 테스트"""
        user_input = {
            "search_query": "아이폰",
            "trust_safety": 80.0,
            "quality_condition": 70.0,
            "remote_transaction": 60.0,
            "activity_responsiveness": 75.0,
            "price_flexibility": 65.0,
        }
        
        result = classify_persona(user_input)
        
        assert "persona_type" in result
        assert "vector" in result
        assert "confidence" in result
        assert result["persona_type"] in [pt.value for pt in PersonaType]
    
    def test_classify_persona_with_conversation_context(self, mock_conversation_context):
        """대화 컨텍스트를 포함한 페르소나 분류 테스트"""
        user_input = {
            "search_query": "아이폰",
            "trust_safety": 70.0,
            "quality_condition": 80.0,
            "remote_transaction": 60.0,
            "activity_responsiveness": 75.0,
            "price_flexibility": 65.0,
            "conversation_context": mock_conversation_context,
        }
        
        result = classify_persona(user_input)
        
        assert result["persona_type"] is not None
        assert "이전" in result["reason"] or len(mock_conversation_context["previous_messages"]) == 0
    
    def test_classify_persona_trust_safety_pro(self):
        """신뢰도 중심 페르소나 분류 테스트"""
        user_input = {
            "search_query": "아이폰",
            "trust_safety": 85.0,
            "quality_condition": 50.0,
            "remote_transaction": 50.0,
            "activity_responsiveness": 50.0,
            "price_flexibility": 50.0,
        }
        
        result = classify_persona(user_input)
        
        assert result["persona_type"] == PersonaType.TRUST_SAFETY_PRO.value


@pytest.mark.unit
class TestGenerateSearchQuery:
    """검색 쿼리 생성 함수 테스트"""
    
    def test_generate_search_query_basic(self):
        """기본 검색 쿼리 생성 테스트"""
        user_input = {
            "search_query": "아이폰 14 프로",
            "category": None,
            "location": None,
            "price_min": None,
            "price_max": None,
        }
        persona_classification = {
            "persona_type": PersonaType.BALANCED.value,
            "vector": {},
        }
        
        result = generate_search_query(user_input, persona_classification)
        
        assert "original_query" in result
        assert "enhanced_query" in result
        assert "keywords" in result
        assert "filters" in result
        assert result["original_query"] == "아이폰 14 프로"
        assert len(result["keywords"]) > 0
    
    def test_generate_search_query_with_filters(self):
        """필터가 포함된 검색 쿼리 생성 테스트"""
        user_input = {
            "search_query": "아이폰",
            "category": "전자기기",
            "location": "서울",
            "price_min": 500000.0,
            "price_max": 1000000.0,
        }
        persona_classification = {
            "persona_type": PersonaType.BALANCED.value,
            "vector": {},
        }
        
        result = generate_search_query(user_input, persona_classification)
        
        assert result["filters"]["category"] == "전자기기"
        assert result["filters"]["location"] == "서울"
        assert result["filters"]["price_min"] == 500000.0
        assert result["filters"]["price_max"] == 1000000.0
    
    def test_generate_search_query_with_conversation_context(self, mock_conversation_context):
        """대화 컨텍스트를 포함한 검색 쿼리 생성 테스트"""
        user_input = {
            "search_query": "아이폰 14",
            "conversation_context": mock_conversation_context,
        }
        persona_classification = {
            "persona_type": PersonaType.BALANCED.value,
            "vector": {},
        }
        
        result = generate_search_query(user_input, persona_classification)
        
        assert "context_queries" in result
        assert len(result["keywords"]) > 0

