"""
SQLAlchemy 모델 정의
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from server.db.database import Base


class History(Base):
    """추천 이력"""

    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_input = Column(JSON)  # 사용자 입력
    search_query = Column(Text)  # 검색 쿼리
    persona_type = Column(String)  # 페르소나 타입
    results = Column(JSON)  # 추천 결과
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Product(Base):
    """상품 정보"""

    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, index=True)
    title = Column(String)
    price = Column(Float)
    category = Column(String)
    condition = Column(String)
    location = Column(String)
    description = Column(Text)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Seller(Base):
    """판매자 정보"""

    __tablename__ = "sellers"

    seller_id = Column(Integer, primary_key=True, index=True)
    seller_name = Column(String)
    avg_rating = Column(Float, default=0.0)
    total_sales = Column(Integer, default=0)
    response_time_hours = Column(Float, default=24.0)
    persona_vector = Column(JSON)  # 판매자 페르소나 벡터
