"""
워크플로우 라우터
"""

import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, AsyncGenerator
from server.db.schemas import UserInput, RecommendationResult
from server.workflow.state import RecommendationState
from server.workflow.graph import recommendation_workflow
from server.utils.logger import get_logger
from server.utils import config
from server.db.conversation_service import (
    get_or_create_conversation,
    add_message,
    get_conversation_context
)
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
        # 대화 세션 관리
        session_id = user_input.session_id
        conversation = get_or_create_conversation(session_id=session_id)
        session_id = conversation.session_id
        
        # 사용자 메시지 저장
        add_message(
            session_id=session_id,
            role="user",
            content=user_input.search_query,
            metadata={"user_input": user_input.dict()}
        )
        
        # 이전 대화 컨텍스트 조회
        conversation_context = get_conversation_context(session_id, limit=10)
        
        # user_input에 대화 컨텍스트 추가
        user_input_dict = user_input.dict()
        user_input_dict["conversation_context"] = conversation_context
        
        # 초기 상태 생성
        initial_state: RecommendationState = {
            "user_input": user_input_dict,
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
            "session_id": session_id,  # 세션 ID 반환
        })
        
        # Assistant 메시지 저장
        if not final_state.get("error_message"):
            add_message(
                session_id=session_id,
                role="assistant",
                content=f"추천 완료: {len(final_state.get('final_item_scores', []))}개 상품",
                metadata={
                    "recommendation_result": {
                        "persona_classification": final_state.get("persona_classification"),
                        "final_item_scores": final_state.get("final_item_scores", []),
                        "ranking_explanation": final_state.get("ranking_explanation", ""),
                    }
                }
            )

        return response

    except Exception as e:
        logger.exception("추천 워크플로우 실행 중 예외 발생")
        raise HTTPException(status_code=500, detail=str(e))


async def stream_workflow_progress(
    user_input: UserInput
) -> AsyncGenerator[str, None]:
    """
    워크플로우 진행 상황을 SSE로 스트리밍
    """
    try:
        # 대화 세션 관리
        session_id = user_input.session_id
        conversation = get_or_create_conversation(session_id=session_id)
        session_id = conversation.session_id
        
        # 사용자 메시지 저장
        add_message(
            session_id=session_id,
            role="user",
            content=user_input.search_query,
            metadata={"user_input": user_input.dict()}
        )
        
        # 이전 대화 컨텍스트 조회
        conversation_context = get_conversation_context(session_id, limit=10)
        
        # user_input에 대화 컨텍스트 추가
        user_input_dict = user_input.dict()
        user_input_dict["conversation_context"] = conversation_context
        
        # 초기 상태 생성
        initial_state: RecommendationState = {
            "user_input": user_input_dict,
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

        # 진행률 계산을 위한 단계 정의
        step_weights = {
            "start": 0,
            "initialized": 20,
            "price_analyzed": 50,
            "safety_analyzed": 50,
            "recommendation_completed": 100,
            "error": 0,
        }

        # 초기 진행률 전송
        yield f"data: {json.dumps({'type': 'progress', 'step': 'start', 'progress': 0, 'message': '워크플로우 시작'}, ensure_ascii=False)}\n\n"

        workflow_app = get_workflow_app()
        loop = asyncio.get_running_loop()

        # LangGraph 스트리밍 실행 (동기 stream을 async로 래핑)
        try:
            # 동기 stream을 executor에서 실행
            def run_stream():
                """동기 스트림 실행"""
                states = []
                for state in workflow_app.stream(initial_state):
                    states.append(state)
                return states

            # 백그라운드에서 스트림 실행
            states = await loop.run_in_executor(None, run_stream)
            
            # 각 상태를 순차적으로 전송
            for state in states:
                # state는 딕셔너리 형태로 각 노드의 이름을 키로 가짐
                for node_name, node_state in state.items():
                    current_step = node_state.get("current_step", "processing")
                    completed_steps = node_state.get("completed_steps", [])
                    
                    # 진행률 계산
                    progress = 0
                    if current_step in step_weights:
                        progress = step_weights[current_step]
                    elif len(completed_steps) > 0:
                        # 완료된 단계 수에 따라 진행률 계산
                        total_steps = 4  # init, price, safety, orchestrator
                        progress = min(int((len(completed_steps) / total_steps) * 100), 90)

                    # 단계별 메시지 생성
                    messages = {
                        "start": "워크플로우 시작",
                        "initialized": "페르소나 분류 및 검색 쿼리 생성 완료",
                        "price_analyzed": "가격 분석 완료",
                        "safety_analyzed": "안전성 분석 완료",
                        "recommendation_completed": "추천 완료",
                        "error": "오류 발생",
                    }
                    message = messages.get(current_step, f"{current_step} 처리 중...")

                    # 진행 상황 전송
                    progress_data = {
                        "type": "progress",
                        "step": current_step,
                        "node": node_name,
                        "progress": progress,
                        "message": message,
                        "completed_steps": completed_steps,
                    }
                    yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)  # 비동기 컨텍스트 유지

                    # 에러 발생 시
                    if node_state.get("error_message"):
                        error_data = {
                            "type": "error",
                            "error_message": node_state.get("error_message"),
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                        return

                    # 완료 시 최종 결과 전송
                    if current_step == "recommendation_completed":
                        # 실행 시간 계산
                        if node_state.get("execution_start_time"):
                            node_state["execution_time"] = time.time() - node_state.get("execution_start_time", time.time())
                        
                        final_data = {
                            "type": "complete",
                            "persona_classification": node_state.get("persona_classification"),
                            "final_item_scores": node_state.get("final_item_scores", []),
                            "final_seller_recommendations": node_state.get("final_seller_recommendations", []),
                            "ranking_explanation": node_state.get("ranking_explanation", ""),
                            "execution_time": node_state.get("execution_time"),
                            "session_id": session_id,  # 세션 ID 반환
                        }
                        yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
                        
                        # Assistant 메시지 저장
                        add_message(
                            session_id=session_id,
                            role="assistant",
                            content=f"추천 완료: {len(node_state.get('final_item_scores', []))}개 상품",
                            metadata={
                                "recommendation_result": {
                                    "persona_classification": node_state.get("persona_classification"),
                                    "final_item_scores": node_state.get("final_item_scores", []),
                                    "ranking_explanation": node_state.get("ranking_explanation", ""),
                                }
                            }
                        )
                        return

        except asyncio.TimeoutError:
            logger.error(
                "워크플로우 실행 타임아웃",
                extra={"timeout_seconds": config.WORKFLOW_TIMEOUT_SECONDS},
            )
            error_data = {
                "type": "error",
                "error_message": "추천 시스템 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.",
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.exception("SSE 스트리밍 중 예외 발생")
        error_data = {
            "type": "error",
            "error_message": str(e),
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


@router.post("/recommend/stream")
async def recommend_products_stream(user_input: UserInput):
    """
    상품 추천 API (SSE 스트리밍)
    실시간으로 워크플로우 진행 상황을 전송합니다.
    """
    return StreamingResponse(
        stream_workflow_progress(user_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """헬스 체크"""
    return {"status": "healthy", "service": "ReCo"}
