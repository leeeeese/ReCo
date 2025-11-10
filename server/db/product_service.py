"""
상품 및 판매자 데이터 조회 서비스
Price Agent에서 사용할 상품 조회 로직
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from server.db.database import SessionLocal
from server.db.models import Product, Seller


def get_sellers_with_products(
    search_query: Optional[str] = None,
    category: Optional[str] = None,
    category_top: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    condition: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    판매자와 상품 정보를 함께 조회 (Price Agent용)

    Args:
        search_query: 검색어 (제목, 설명에서 검색)
        category: 카테고리 (category_mid)
        category_top: 대분류 카테고리
        price_min: 최소 가격
        price_max: 최대 가격
        condition: 상품 상태 (중고/새상품)
        limit: 최대 조회 개수

    Returns:
        판매자별로 그룹화된 상품 리스트
    """
    db: Session = SessionLocal()

    try:
        # 기본 쿼리: Product와 Seller 조인
        query = db.query(Product, Seller).join(
            Seller, Product.seller_id == Seller.seller_id
        )

        # 필터 적용
        filters = []

        if search_query:
            search_term = f"%{search_query}%"
            filters.append(
                or_(
                    Product.title.contains(search_query),
                    Product.description.contains(search_query)
                )
            )

        if category:
            filters.append(Product.category == category)

        if category_top:
            filters.append(Product.category_top == category_top)

        if price_min is not None:
            filters.append(Product.price >= price_min)

        if price_max is not None:
            filters.append(Product.price <= price_max)

        if condition:
            filters.append(Product.condition == condition)

        if filters:
            query = query.filter(and_(*filters))

        # 정렬: 조회수 높은 순
        results = query.order_by(Product.view_count.desc()).limit(limit).all()

        # 판매자별로 그룹화
        sellers_dict = {}

        for product, seller in results:
            seller_id = seller.seller_id

            if seller_id not in sellers_dict:
                sellers_dict[seller_id] = {
                    "seller_id": seller.seller_id,
                    "seller_name": seller.seller_name,
                    "seller_trust": seller.seller_trust,
                    "seller_safe_sales": seller.seller_safe_sales,
                    "seller_customs": seller.seller_customs,
                    "products": []
                }

            sellers_dict[seller_id]["products"].append({
                "product_id": product.product_id,
                "title": product.title,
                "price": product.price,
                "category": product.category,
                "category_top": product.category_top,
                "condition": product.condition,
                "description": product.description,
                "view_count": product.view_count,
                "like_count": product.like_count,
                "chat_count": product.chat_count,
                "sell_method": product.sell_method,
                "delivery_fee": product.delivery_fee,
                "is_safe": product.is_safe
            })

        return list(sellers_dict.values())

    finally:
        db.close()


def get_products_by_seller_ids(seller_ids: List[int], limit: int = 100) -> List[Dict[str, Any]]:
    """
    특정 판매자들의 상품 조회

    Args:
        seller_ids: 판매자 ID 리스트
        limit: 판매자당 최대 상품 수

    Returns:
        판매자별로 그룹화된 상품 리스트
    """
    db: Session = SessionLocal()

    try:
        results = db.query(Product, Seller).join(
            Seller, Product.seller_id == Seller.seller_id
        ).filter(
            Product.seller_id.in_(seller_ids)
        ).order_by(Product.view_count.desc()).all()

        sellers_dict = {}

        for product, seller in results:
            seller_id = seller.seller_id

            # 판매자당 상품 수 제한
            if seller_id in sellers_dict:
                if len(sellers_dict[seller_id]["products"]) >= limit:
                    continue

            if seller_id not in sellers_dict:
                sellers_dict[seller_id] = {
                    "seller_id": seller.seller_id,
                    "seller_name": seller.seller_name,
                    "seller_trust": seller.seller_trust,
                    "seller_safe_sales": seller.seller_safe_sales,
                    "seller_customs": seller.seller_customs,
                    "products": []
                }

            sellers_dict[seller_id]["products"].append({
                "product_id": product.product_id,
                "title": product.title,
                "price": product.price,
                "category": product.category,
                "category_top": product.category_top,
                "condition": product.condition,
                "description": product.description,
                "view_count": product.view_count,
                "like_count": product.like_count,
                "chat_count": product.chat_count,
                "sell_method": product.sell_method,
                "delivery_fee": product.delivery_fee,
                "is_safe": product.is_safe
            })

        return list(sellers_dict.values())

    finally:
        db.close()


def search_products_by_keywords(
    keywords: List[str],
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    키워드로 상품 검색 (검색 쿼리 파싱 후 사용)

    Args:
        keywords: 검색 키워드 리스트
        category: 카테고리 필터
        price_min: 최소 가격
        price_max: 최대 가격
        limit: 최대 조회 개수

    Returns:
        판매자별로 그룹화된 상품 리스트
    """
    # 키워드를 공백으로 연결하여 검색
    search_query = " ".join(keywords) if keywords else None

    return get_sellers_with_products(
        search_query=search_query,
        category=category,
        price_min=price_min,
        price_max=price_max,
        limit=limit
    )
