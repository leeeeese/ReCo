"""
pytest 공통 픽스처 및 설정
"""

import pytest
import os
from typing import Dict, Any
from fastapi.testclient import TestClient
from server.main import app
from server.db.database import Base, engine
from server.workflow.state import RecommendationState


@pytest.fixture(scope="session")
def test_db():
    """테스트용 데이터베이스 설정"""
    # 테스트용 SQLite DB 사용
    test_db_url = "sqlite:///./test_history.db"
    os.environ["DATABASE_URL"] = test_db_url
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # 테스트 후 정리
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_history.db"):
        os.remove("test_history.db")


@pytest.fixture
def client(test_db):
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_user_input() -> Dict[str, Any]:
    """모의 사용자 입력"""
    return {
        "search_query": "아이폰 14 프로",
        "trust_safety": 70.0,
        "quality_condition": 80.0,
        "remote_transaction": 60.0,
        "activity_responsiveness": 75.0,
        "price_flexibility": 65.0,
        "category": None,
        "location": None,
        "price_min": None,
        "price_max": None,
    }


@pytest.fixture
def mock_initial_state(mock_user_input) -> RecommendationState:
    """모의 초기 워크플로우 상태"""
    return {
        "user_input": mock_user_input,
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


@pytest.fixture
def mock_conversation_context() -> Dict[str, Any]:
    """모의 대화 컨텍스트"""
    return {
        "previous_messages": [
            {
                "role": "user",
                "content": "아이폰 찾고 있어요",
                "metadata": {
                    "user_input": {
                        "search_query": "아이폰 찾고 있어요",
                        "trust_safety": 70.0,
                        "quality_condition": 80.0,
                    }
                }
            }
        ],
        "total_messages": 1,
        "session_id": "test-session-123",
    }

