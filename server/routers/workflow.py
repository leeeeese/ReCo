"""
워크플로우 라우터
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from server.db.schemas import UserInput, RecommendationResult
from server.workflow.state import RecommendationState

router = APIRouter(prefix="/api/v1", tags=["workflow"])


@router.post("/recommend")
async def recommend_products(user_input: UserInput) -> Dict[str, Any]:
    """
    상품 추천 API
    """
    try:
        # 초기 상태 생성
        initial_state: RecommendationState = {
            "user_input": user_input.dict(),
            "search_query": {},
            "persona_classification": None,
            "seller_item_scores": [],
            "final_item_scores": [],
            "sql_query": None,
            "ranking_explanation": "",
            "current_step": "start",
            "completed_steps": [],
            "error_message": None,
        }

        # TODO: LangGraph 워크플로우 실행
        # workflow.run(initial_state)

        # 임시 응답
        return {
            "status": "success",
            "message": "추천 시스템 준비 중",
            "persona": user_input.dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """헬스 체크"""
    return {"status": "healthy", "service": "ReCo"}
