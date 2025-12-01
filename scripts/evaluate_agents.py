"""
에이전트 평가 스크립트
정답 데이터와 추천 결과를 비교하여 정확도 계산
"""

import sys
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.db.database import SessionLocal
from server.db.models import RecommendationLog, Review
from server.workflow.graph import recommendation_workflow
from server.workflow.state import RecommendationState
from server.utils.logger import get_logger

logger = get_logger(__name__)


def load_answer_data(csv_path: str = "answer_data.csv") -> pd.DataFrame:
    """정답 데이터 로드"""
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding="cp949")
        except:
            df = pd.read_csv(csv_path, encoding="euc-kr")

    logger.info(f"정답 데이터 로드 완료: {len(df)}개")
    return df


def get_buyer_info_from_reviews(db: Session, buyer_id: str) -> Optional[Dict[str, Any]]:
    """Review 테이블에서 구매자 정보 조회"""
    # reviewer_id로 리뷰 조회 (구매자 역할)
    reviews = (
        db.query(Review)
        .filter(Review.reviewer_id == str(buyer_id))
        .filter(Review.review_role == "구매자")
        .limit(10)
        .all()
    )

    if not reviews:
        return None

    # 구매자가 거래한 판매자들 수집
    seller_ids = list(set([review.seller_id for review in reviews]))

    return {
        "buyer_id": buyer_id,
        "review_count": len(reviews),
        "traded_seller_ids": seller_ids,
        "sample_review": reviews[0].review_content if reviews else None,
    }


def create_user_input_from_buyer(buyer_info: Dict[str, Any]) -> Dict[str, Any]:
    """구매자 정보로부터 사용자 입력 생성 (간단한 예시)"""
    # 실제로는 buyer_info의 리뷰 내용을 분석하여 선호도를 추출해야 함
    # 여기서는 기본값 사용
    return {
        "search_query": "중고거래",
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


def run_recommendation(
    user_input: Dict[str, Any], workflow_app
) -> Optional[List[Dict[str, Any]]]:
    """워크플로우 실행하여 추천 결과 얻기"""
    try:
        initial_state: RecommendationState = {
            "user_input": user_input,
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

        final_state = workflow_app.invoke(initial_state)

        if final_state.get("error_message"):
            logger.warning(f"워크플로우 오류: {final_state['error_message']}")
            return None

        recommended_sellers = final_state.get("final_seller_recommendations", [])
        if not recommended_sellers:
            return None

        return recommended_sellers

    except Exception as e:
        logger.error(f"추천 실행 오류: {e}", exc_info=True)
        return None


def evaluate_recommendation(
    recommended_sellers: List[Dict[str, Any]], ground_truth_seller_id: int
) -> Dict[str, Any]:
    """추천 결과와 정답 비교"""
    recommended_seller_ids = [
        seller.get("seller_id") for seller in recommended_sellers if seller.get("seller_id")
    ]

    # 정답 판매자가 추천 리스트에 있는지 확인
    is_correct = ground_truth_seller_id in recommended_seller_ids

    # 정답 판매자의 순위 (1-based)
    rank = None
    if is_correct:
        rank = recommended_seller_ids.index(ground_truth_seller_id) + 1

    return {
        "is_correct": 1 if is_correct else 0,
        "rank": rank,
        "recommended_seller_ids": recommended_seller_ids,
    }


def save_recommendation_log(
    db: Session,
    buyer_id: str,
    user_input: Dict[str, Any],
    recommended_sellers: List[Dict[str, Any]],
    ground_truth_seller_id: int,
    evaluation_result: Dict[str, Any],
):
    """추천 결과를 DB에 저장"""
    recommended_seller_ids = evaluation_result["recommended_seller_ids"]

    log = RecommendationLog(
        buyer_id=buyer_id,
        user_input=user_input,
        recommended_seller_ids=recommended_seller_ids,
        recommended_sellers=recommended_sellers,
        ground_truth_seller_id=ground_truth_seller_id,
        is_correct=evaluation_result["is_correct"],
        rank=evaluation_result["rank"],
    )

    db.add(log)
    db.commit()


def evaluate_all(
    answer_data_path: str = "answer_data.csv",
    limit: Optional[int] = None,
    save_logs: bool = True,
) -> Dict[str, Any]:
    """전체 평가 실행"""
    # 정답 데이터 로드
    answer_df = load_answer_data(answer_data_path)

    if limit:
        answer_df = answer_df.head(limit)
        logger.info(f"평가 제한: {limit}개만 평가")

    # 워크플로우 초기화
    workflow_app = recommendation_workflow()

    # DB 연결
    db: Session = SessionLocal()

    # 평가 결과
    total_count = 0
    correct_count = 0
    rank_sum = 0
    rank_counts = {}  # {rank: count}

    try:
        for idx, row in answer_df.iterrows():
            buyer_id = str(row["buyer"])
            ground_truth_seller_id = int(row["seller"])

            logger.info(f"[{idx + 1}/{len(answer_df)}] 구매자 {buyer_id} 평가 중...")

            # 구매자 정보 조회
            buyer_info = get_buyer_info_from_reviews(db, buyer_id)
            if not buyer_info:
                logger.warning(f"구매자 {buyer_id}의 리뷰 정보를 찾을 수 없습니다.")
                continue

            # 사용자 입력 생성
            user_input = create_user_input_from_buyer(buyer_info)

            # 추천 실행
            recommended_sellers = run_recommendation(user_input, workflow_app)
            if not recommended_sellers:
                logger.warning(f"구매자 {buyer_id}에 대한 추천 실패")
                continue

            # 평가
            evaluation_result = evaluate_recommendation(
                recommended_sellers, ground_truth_seller_id
            )

            # 결과 저장
            if save_logs:
                save_recommendation_log(
                    db,
                    buyer_id,
                    user_input,
                    recommended_sellers,
                    ground_truth_seller_id,
                    evaluation_result,
                )

            # 통계 업데이트
            total_count += 1
            if evaluation_result["is_correct"]:
                correct_count += 1
                rank = evaluation_result["rank"]
                rank_sum += rank
                rank_counts[rank] = rank_counts.get(rank, 0) + 1

            logger.info(
                f"구매자 {buyer_id}: {'✅ 정답' if evaluation_result['is_correct'] else '❌ 오답'} "
                f"(순위: {evaluation_result['rank'] if evaluation_result['rank'] else 'N/A'})"
            )

    finally:
        db.close()

    # 최종 결과 계산
    accuracy = correct_count / total_count if total_count > 0 else 0.0
    mean_rank = rank_sum / correct_count if correct_count > 0 else None

    results = {
        "total_count": total_count,
        "correct_count": correct_count,
        "accuracy": accuracy,
        "mean_rank": mean_rank,
        "rank_distribution": rank_counts,
    }

    return results


def print_evaluation_results(results: Dict[str, Any]):
    """평가 결과 출력"""
    print("\n" + "=" * 60)
    print("에이전트 평가 결과")
    print("=" * 60)
    print(f"총 평가 수: {results['total_count']}")
    print(f"정답 수: {results['correct_count']}")
    print(f"정확도: {results['accuracy']:.2%}")
    if results["mean_rank"]:
        print(f"평균 순위: {results['mean_rank']:.2f}")
    print("\n순위 분포:")
    for rank in sorted(results["rank_distribution"].keys()):
        count = results["rank_distribution"][rank]
        print(f"  {rank}위: {count}개")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="에이전트 평가 스크립트")
    parser.add_argument(
        "--answer-data",
        type=str,
        default="answer_data.csv",
        help="정답 데이터 CSV 파일 경로",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="평가할 데이터 수 제한 (테스트용)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="추천 로그를 DB에 저장하지 않음",
    )

    args = parser.parse_args()

    # 평가 실행
    results = evaluate_all(
        answer_data_path=args.answer_data,
        limit=args.limit,
        save_logs=not args.no_save,
    )

    # 결과 출력
    print_evaluation_results(results)

