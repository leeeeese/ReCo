"""
워크플로우 라우터
"""

import asyncio
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from server.db.schemas import UserInput, RecommendationResult
from server.workflow.state import RecommendationState
from server.workflow.graph import recommendation_workflow
from server.utils.logger import get_logger
from server.utils import config
import time

router = APIRouter(prefix="/api/v1", tags=["workflow"])
logger = get_logger(__name__)

# 워크플로우 인스턴스 생성 (싱글톤)
_workflow_app = None

def get_workflow_app():
    """워크플로우 앱 싱글톤"""
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = recommendation_workflow()
    return _workflow_app


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
            "price_agent_recommendations": None,
            "safety_agent_recommendations": None,
            "final_seller_recommendations": None,
            "final_item_scores": None,
            "ranking_explanation": "",
            "current_step": "start",
            "completed_steps": [],
            "error_message": None,
            "execution_start_time": time.time(),
            "execution_time": None,
        }

        # LangGraph 워크플로우 실행 (타임아웃 포함)
        workflow_app = get_workflow_app()

        loop = asyncio.get_running_loop()

        try:
            final_state = await asyncio.wait_for(
                loop.run_in_executor(None, workflow_app.invoke, initial_state),
                timeout=config.WORKFLOW_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error(
                "워크플로우 실행 타임아웃",
                extra={"timeout_seconds": config.WORKFLOW_TIMEOUT_SECONDS},
            )
            return {
                "status": "error",
                "error_message": "추천 시스템 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.",
            }

        # 실행 시간 계산
        if final_state.get("execution_start_time"):
            final_state["execution_time"] = time.time() - final_state["execution_start_time"]

        # 응답 생성
        response: Dict[str, Any] = {
            "status": "success" if not final_state.get("error_message") else "error",
        }

        # 에러가 있으면 반환
        if final_state.get("error_message"):
            response["error_message"] = final_state["error_message"]
            logger.error(
                "워크플로우 실행 오류",
                extra={"error": final_state["error_message"]},
            )
            return response

        # 성공 응답 구성
        response.update({
            "persona_classification": final_state.get("persona_classification"),
            "final_item_scores": final_state.get("final_item_scores", []),
            "ranked_products": final_state.get("final_item_scores", []),  # 호환성을 위해
            "final_seller_recommendations": final_state.get("final_seller_recommendations", []),
            "ranking_explanation": final_state.get("ranking_explanation", ""),
            "current_step": final_state.get("current_step", "completed"),
            "completed_steps": final_state.get("completed_steps", []),
            "execution_time": final_state.get("execution_time"),
        })

        return response

    except Exception as e:
        logger.exception("추천 워크플로우 실행 중 예외 발생")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """헬스 체크"""
    return {"status": "healthy", "service": "ReCo"}
