"""
공통 테스트 설정 (DB + 백엔드용)
- agent / integration 테스트에서 실제 DB + 서비스 레이어를 쓰기 위한 기본 세팅
"""

import os
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.db.database import Base  # Base: declarative_base()
# get_db 스타일의 DI를 쓰고 있으면 같이 import 해서 override 할 수도 있음
# from server.db.database import get_db

from server.db import models  # Product, Seller 등이 여기 들어있다고 가정


# -------------------------------------------------------------------
# 1) 테스트용 DB 엔진/세션 정의
#    - 실제 개발 DB 안 건드리도록 별도 URL 사용 권장
#    - .env / pytest.ini 에 TEST_DATABASE_URL 설정해두면 제일 깔끔
# -------------------------------------------------------------------
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_reco.db")

# sqlite라면 check_same_thread 옵션 많이 씀 (FastAPI 예제 스타일)
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# -------------------------------------------------------------------
# 2) 세션 하나를 테스트마다 제공하는 픽스처
#    - 필요하면 테스트 함수 시그니처에 db_session 넣어서 사용 가능
# -------------------------------------------------------------------
@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# 3) 세션 스코프에서 테이블 생성 + 더미 데이터 시딩
#    - agent / workflow 쪽에서 실제 데이터를 잘 활용하는지 확인용
# -------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    세션 시작 시:
      - 기존 테이블 드랍 후 재생성
      - 간단한 seller / product 더미 데이터 삽입
    세션 종료 시:
      - 필요하면 테이블 드랍
    """
    # 깨끗한 스키마 생성
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # --- 여기서 기본 더미 데이터 넣기 ---
    from server.db.models import Seller, Product  # 실제 모델명에 맞게 바꿔줘야 함

    session = TestingSessionLocal()
    try:
        # 판매자 하나
        seller = Seller(
            seller_id=101,
            seller_name="테스트판매자",
            seller_trust=80,
            seller_safe_sales=10,
            seller_customs=0,
            seller_items=5,
            category_top="디지털기기",
            sell_method="직거래,택배",
            seller_view=100,
            seller_like=5,
            seller_chat=3,
            avg_rating=4.5,
            total_sales=20,
            response_time_hours=2,
            persona_vector="balanced",
        )
        session.add(seller)

        # 상품 하나 (아이폰)
        product = Product(
            product_id=1,
            seller_id=101,
            title="아이폰 14 프로",
            price=850000,
            category="스마트폰",
            category_top="디지털기기",
            condition="상",
            location="서울",
            description="테스트용 아이폰 14 프로",
            view_count=123,
            like_count=4,
            chat_count=2,
            sell_method="직거래",
            delivery_fee=0,
            is_safe=True,
        )
        session.add(product)

        session.commit()
    finally:
        session.close()

    # 이 아래 yield 이후에는 세션 종료 시점
    yield

    # 테스트 끝나고 테이블 정리하고 싶으면 주석 해제
    # Base.metadata.drop_all(bind=engine)


# -------------------------------------------------------------------
# 4) FastAPI 의존성(get_db)을 쓰는 경우: 자동 오버라이드 (선택)
#    - API 테스트에서 실제 DB 대신 TestingSessionLocal을 쓰도록 강제
#    - 이미 별도의 test용 conftest가 있으면 이 부분은 상황 보면서 조정
# -------------------------------------------------------------------
@pytest.fixture(autouse=True)
def override_db_dependency(monkeypatch, db_session):
    """
    server.db.database.get_db 같은 의존성 주입 함수를 override 해서
    항상 TestingSessionLocal 세션을 쓰게 만든다.
    """
    try:
        from server.db import database as db_module

        def _get_test_db():
            try:
                yield db_session
            finally:
                # 여기서는 db_session 픽스처가 정리해주므로 별도 close 안함
                pass

        if hasattr(db_module, "get_db"):
            monkeypatch.setattr(db_module, "get_db", _get_test_db)
    except ImportError:
        # get_db 패턴을 안 쓰고 있으면 무시
        pass
