"""
pytest 공통 픽스처 및 설정
"""

import os
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.main import app
from server.db import database as db_module
from server.workflow.state import RecommendationState


@pytest.fixture(scope="session")
def test_db():
    """
    테스트용 SQLite 데이터베이스 설정

    - 실제 개발 DB와 분리된 test_history.db 사용
    - server.db.database 모듈의 engine / SessionLocal 을 테스트용으로 교체
    """
    test_db_url = "sqlite:///./test_history.db"

    # 1) 테스트용 엔진/세션팩토리 생성
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    # 2) 기존 모듈의 엔진/세션을 테스트용으로 교체
    db_module.engine = test_engine
    db_module.SessionLocal = TestingSessionLocal
    Base = db_module.Base

    # 3) 스키마 생성
    Base.metadata.create_all(bind=test_engine)

    yield

    # 4) 정리: 테이블 드랍 + 파일 삭제
    # Windows에서 SQLite 파일 삭제 전에 모든 연결을 닫아야 함
    test_engine.dispose()
    Base.metadata.drop_all(bind=test_engine)
    
    # 파일 삭제 시도 (다른 프로세스가 사용 중이면 무시)
    try:
        if os.path.exists("test_history.db"):
            os.remove("test_history.db")
    except PermissionError:
        # Windows에서 파일이 잠겨있을 수 있음 - 무시
        pass


@pytest.fixture
def client(test_db):
    """
    FastAPI 테스트 클라이언트

    - test_db 픽스처를 선행 실행하여 테스트용 DB를 준비
    - FastAPI의 get_db 의존성을 테스트용 세션으로 override
    """
    # get_db는 history.py에 정의되어 있음
    from server.routers.history import get_db

    def override_get_db():
        db = db_module.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


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
                },
            }
        ],
        "total_messages": 1,
        "session_id": "test-session-123",
    }
