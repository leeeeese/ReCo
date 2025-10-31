"""
ProductMatching Agent
사용자 persona ↔ 판매자 persona ↔ 상품 피처 매칭
입력: persona, seller_features → 출력: seller_item_scores
"""

from typing import List, Dict, Any, Optional, Tuple
from server.workflow.state import RecommendationState, PersonaVector
from server.utils.tools import (
    calculate_persona_match_score,
    calculate_seller_quality_score,
    calculate_product_feature_score
)


class ProductMatching:
    """상품 매칭기"""

    def __init__(self):
        # TODO: DB 서비스 구현 필요
        self.db_service = None

    def match_user_seller_persona(self, user_persona: PersonaVector, sellers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """1단계: 사용자 페르소나 ↔ 판매자 페르소나 매칭"""
        seller_scores = []

        for seller in sellers:
            seller_vector = seller["persona_vector"]

            # 페르소나 매칭 점수 계산
            persona_score = calculate_persona_match_score(
                user_persona, seller_vector)

            # 추가 판매자 특성 점수
            seller_quality_score = calculate_seller_quality_score(seller)

            # 최종 판매자 점수 (가중 평균)
            final_score = 0.7 * persona_score + 0.3 * seller_quality_score

            seller_scores.append({
                "seller_id": seller["seller_id"],
                "seller_name": seller["seller_name"],
                "persona_score": persona_score,
                "quality_score": seller_quality_score,
                "final_score": final_score,
                "persona_vector": seller_vector,
                "total_sales": seller["total_sales"],
                "avg_rating": seller["avg_rating"],
                "response_time_hours": seller["response_time_hours"]
            })

        # 점수 순으로 정렬
        seller_scores.sort(key=lambda x: x["final_score"], reverse=True)

        return seller_scores

    def match_seller_product_features(self, seller_scores: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """2단계: 판매자 ↔ 상품 피처 매칭"""
        seller_item_scores = []

        for seller_score in seller_scores:
            seller_id = seller_score["seller_id"]
            seller_products = [
                p for p in products if p["seller_id"] == seller_id]

            for product in seller_products:
                # 상품 피처 점수 계산
                product_feature_score = calculate_product_feature_score(
                    product)

                # 판매자 점수와 상품 점수 결합
                final_item_score = 0.6 * \
                    seller_score["final_score"] + 0.4 * product_feature_score

                seller_item_scores.append({
                    "product_id": product["product_id"],
                    "seller_id": seller_id,
                    "seller_name": seller_score["seller_name"],
                    "title": product["title"],
                    "price": product["price"],
                    "category": product["category"],
                    "condition": product["condition"],
                    "location": product["location"],
                    "description": product["description"],
                    "seller_persona_score": seller_score["persona_score"],
                    "seller_quality_score": seller_score["quality_score"],
                    "product_feature_score": product_feature_score,
                    "final_item_score": final_item_score,
                    "seller_rating": seller_score["avg_rating"],
                    "view_count": product["view_count"],
                    "like_count": product["like_count"]
                })

        # 최종 점수 순으로 정렬
        seller_item_scores.sort(
            key=lambda x: x["final_item_score"], reverse=True)

        return seller_item_scores

    def get_products_for_matching(self, filters: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """매칭을 위한 판매자와 상품 데이터 조회"""
        # TODO: 실제 DB 조회 구현
        # 현재는 목업 데이터 반환
        sellers = [
            {
                "seller_id": 1,
                "seller_name": "목업 판매자",
                "persona_vector": PersonaVector(
                    trust_safety=50, quality_condition=50, remote_transaction=50,
                    activity_responsiveness=50, price_flexibility=50
                ),
                "avg_rating": 4.5,
                "total_sales": 100,
                "response_time_hours": 12.0
            }
        ]
        products = [
            {
                "product_id": 1,
                "seller_id": 1,
                "title": "목업 상품",
                "price": 100000,
                "category": "전자제품",
                "condition": "중고",
                "location": "서울",
                "description": "목업 상품 설명",
                "view_count": 100,
                "like_count": 10
            }
        ]
        return sellers, products


def product_matching_node(state: RecommendationState) -> RecommendationState:
    """상품 매칭 노드"""
    try:
        persona_classification = state.get("persona_classification")
        search_query = state.get("search_query")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        # 필터 추출
        filters = search_query.get("filters", {}) if search_query else {}

        # ProductMatching 인스턴스 생성
        matcher = ProductMatching()

        # 1. 판매자와 상품 데이터 조회
        sellers, products = matcher.get_products_for_matching(filters)

        if not sellers or not products:
            raise ValueError("매칭할 판매자나 상품이 없습니다.")

        # 2. 사용자 페르소나 ↔ 판매자 페르소나 매칭
        user_persona = persona_classification["vector"]
        seller_scores = matcher.match_user_seller_persona(
            user_persona, sellers)

        # 3. 판매자 ↔ 상품 피처 매칭
        seller_item_scores = matcher.match_seller_product_features(
            seller_scores, products)

        # 결과를 상태에 저장
        state["seller_item_scores"] = seller_item_scores
        state["current_step"] = "products_matched"
        state["completed_steps"].append("product_matching")

        print(f"상품 매칭 완료: {len(seller_item_scores)}개 상품")
        print(f"판매자 매칭: {len(seller_scores)}개 판매자")

        # 상위 5개 결과 출력
        for i, item in enumerate(seller_item_scores[:5], 1):
            print(
                f"  {i}. {item['title']} (점수: {item['final_item_score']:.3f})")
            print(
                f"     판매자: {item['seller_name']} (페르소나: {item['seller_persona_score']:.3f})")

    except Exception as e:
        state["error_message"] = f"상품 매칭 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"상품 매칭 오류: {e}")

    return state
