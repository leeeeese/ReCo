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
    category = Column(String)  # category_mid
    category_top = Column(String)  # 대분류
    condition = Column(String)  # item_status (중고/새상품)
    location = Column(String)
    description = Column(Text)  # item_caption
    view_count = Column(Integer, default=0)  # item_view
    like_count = Column(Integer, default=0)  # item_like
    chat_count = Column(Integer, default=0)  # item_chat
    sell_method = Column(String)  # 직거래/택배
    delivery_fee = Column(String)  # 배송비 (있음/없음)
    is_safe = Column(String)  # 안전거래 여부 (사용/미사용)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Seller(Base):
    """판매자 정보"""

    __tablename__ = "sellers"

    seller_id = Column(Integer, primary_key=True, index=True)
    seller_name = Column(String)
    seller_trust = Column(Float, default=0.0)  # 신뢰도 점수
    seller_safe_sales = Column(Integer, default=0)  # 안전거래 판매 건수
    seller_customs = Column(Integer, default=0)  # 거래 건수
    seller_items = Column(Integer, default=0)  # 판매 상품 수
    category_top = Column(String)  # 주 카테고리
    sell_method = Column(String)  # 선호 거래 방식
    seller_view = Column(Integer, default=0)  # 조회수
    seller_like = Column(Integer, default=0)  # 좋아요 수
    seller_chat = Column(Integer, default=0)  # 채팅 수
    avg_rating = Column(Float, default=0.0)  # 평균 평점 (리뷰에서 계산)
    total_sales = Column(Integer, default=0)  # 총 판매 건수
    response_time_hours = Column(Float, default=24.0)  # 응답 시간
    persona_vector = Column(JSON)  # 판매자 페르소나 벡터


class Review(Base):
    """판매자 리뷰 정보"""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reviewer_id = Column(String, index=True)  # 리뷰어 ID
    review_role = Column(String)  # 리뷰 역할 (구매자 등)
    review_content = Column(Text)  # 리뷰 내용
    seller_id = Column(Integer, index=True)  # 판매자 ID
    seller_name = Column(String)  # 판매자 이름 (참조용)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
