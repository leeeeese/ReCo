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

        # 초기 상태 생성 (total=False이므로 필수 필드만)
        initial_state: RecommendationState = {
            "user_input": user_input_dict,
            "current_step": "start",
            "completed_steps": [],
            "execution_start_time": time.time(),
        }

        # LangGraph 워크플로우 실행 (타임아웃 포함)
        workflow_app = get_workflow_app()

        loop = asyncio.get_running_loop()

        logger.info(
            "워크플로우 실행 시작",
            extra={
                "search_query": user_input.search_query,
                "timeout_seconds": config.WORKFLOW_TIMEOUT_SECONDS,
            }
        )

        try:
            final_state = await asyncio.wait_for(
                loop.run_in_executor(None, workflow_app.invoke, initial_state),
                timeout=config.WORKFLOW_TIMEOUT_SECONDS,
            )

            logger.info(
                "워크플로우 실행 완료",
                extra={
                    "execution_time": final_state.get("execution_time"),
                    "completed_steps": final_state.get("completed_steps", []),
                    "has_error": bool(final_state.get("error_message")),
                }
            )
        except asyncio.TimeoutError:
            logger.error(
                "워크플로우 실행 타임아웃",
                extra={
                    "timeout_seconds": config.WORKFLOW_TIMEOUT_SECONDS,
                    "search_query": user_input.search_query,
                },
            )
            return {
                "status": "error",
                "error_message": f"추천 시스템 응답이 지연되고 있습니다. (타임아웃: {config.WORKFLOW_TIMEOUT_SECONDS}초) 잠시 후 다시 시도해주세요.",
            }

        # 실행 시간 계산 (final_state는 불변이므로 변수에 저장)
        execution_time = None
        if final_state.get("execution_start_time"):
            execution_time = time.time() - final_state["execution_start_time"]

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

        # final_item_scores 생성 (final_seller_recommendations에서 추출)
        recommended_sellers = final_state.get(
            "final_seller_recommendations") or []

        # None 체크 및 타입 보장
        if not isinstance(recommended_sellers, list):
            logger.warning(
                f"final_seller_recommendations가 리스트가 아닙니다: {type(recommended_sellers)}"
            )
            recommended_sellers = []

        # final_item_scores 형식으로 변환
        final_item_scores = []
        for seller in recommended_sellers:
            products = seller.get("products", [])
            if products:
                for product in products:
                    final_item_scores.append({
                        "product_id": product.get("product_id"),
                        "seller_id": seller.get("seller_id"),
                        "title": product.get("title", ""),
                        "price": product.get("price", 0),
                        "final_score": seller.get("final_score", 0.5),
                        "ranking_factors": {
                            "reasoning": seller.get("final_reasoning", ""),
                            "product_score": seller.get("product_score", 0.5),
                            "reliability_score": seller.get("reliability_score", 0.5),
                        },
                        "final_reasoning": seller.get("final_reasoning", ""),
                        "seller_name": seller.get("seller_name", ""),
                        "category": product.get("category", ""),
                        "condition": product.get("condition", ""),
                        "location": product.get("location", ""),
                    })
            else:
                # 상품 정보가 없으면 판매자 정보만으로 생성
                final_item_scores.append({
                    "product_id": seller.get("seller_id", 0),
                    "seller_id": seller.get("seller_id", 0),
                    "title": seller.get("seller_name", ""),
                    "price": 0,
                    "final_score": seller.get("final_score", 0.5),
                    "ranking_factors": {
                        "reasoning": seller.get("final_reasoning", ""),
                        "product_score": seller.get("product_score", 0.5),
                        "reliability_score": seller.get("reliability_score", 0.5),
                    },
                    "final_reasoning": seller.get("final_reasoning", ""),
                    "seller_name": seller.get("seller_name", ""),
                    "category": "",
                    "condition": "",
                    "location": "",
                })

        # 점수 기준 정렬
        final_item_scores.sort(key=lambda x: x.get(
            "final_score", 0), reverse=True)

        # 성공 응답 구성
        response.update({
            "final_item_scores": final_item_scores,
            # 호환성을 위해
            "ranked_products": final_item_scores,
            "final_seller_recommendations": recommended_sellers,
            "ranking_explanation": final_state.get("ranking_explanation", ""),
            "current_step": final_state.get("current_step", "completed"),
            "completed_steps": final_state.get("completed_steps", []),
            "execution_time": execution_time,  # 계산된 실행 시간 사용
            "session_id": session_id,  # 세션 ID 반환
        })

        # Assistant 메시지 저장
        if not final_state.get("error_message"):
            add_message(
                session_id=session_id,
                role="assistant",
                content=f"추천 완료: {len(final_item_scores)}개 상품",
                metadata={
                    "recommendation_result": {
                        "final_item_scores": final_item_scores,
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
            "product_agent_recommendations": None,
            "reliability_agent_recommendations": None,
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
                        progress = min(
                            int((len(completed_steps) / total_steps) * 100), 90)

                    # 단계별 메시지 생성
                    messages = {
                        "start": "워크플로우 시작",
                        "initialized": "검색 쿼리 생성 완료",
                        "price_analyzed": "상품 특성 분석 완료",
                        "safety_analyzed": "신뢰도 분석 완료",
                        "recommendation_completed": "추천 완료",
                        "error": "오류 발생",
                    }
                    message = messages.get(
                        current_step, f"{current_step} 처리 중...")

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
                            node_state["execution_time"] = time.time(
                            ) - node_state.get("execution_start_time", time.time())

                        final_data = {
                            "type": "complete",
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


@router.post("/chat")
async def chat(message: Dict[str, str]) -> Dict[str, str]:
    """
    일반 대화 API (LLM 기반)
    """
    user_message = message.get("message", "").strip()

    if not user_message:
        return {
            "response": "안녕하세요! 중고거래 상품 추천을 도와드릴 수 있습니다. 무엇을 찾고 계신가요?"
        }

    try:
        # LLM을 사용한 자연스러운 대화
        from server.utils.llm_agent import LLMAgent

        chat_agent = LLMAgent(
            system_prompt="""당신은 중고거래 상품 추천 서비스 ReCo의 친절한 AI 어시스턴트입니다.
사용자와 자연스럽고 친근하게 대화하며, 중고거래 상품 추천 서비스를 소개하고 도와드립니다.
- 인사말에는 친근하게 응답하세요
- 감사 표현에는 겸손하게 응답하세요
- 질문에는 간단명료하게 답변하세요
- 상품 추천이 필요하면 상품명을 입력하라고 안내하세요
- 항상 한국어로 응답하세요
- 응답은 1-2문장으로 간결하게 작성하세요"""
        )

        # LLM 호출 (텍스트 형식)
        result = chat_agent.decide(
            context={"user_message": user_message},
            decision_task=f"사용자가 '{user_message}'라고 말했습니다. 자연스럽고 친근하게 응답해주세요.",
            format="text"
        )

        if result.get("error") or result.get("fallback"):
            # LLM 호출 실패 시 기본 응답
            logger.warning("일반 대화 LLM 호출 실패, 기본 응답 사용", extra={
                           "error": result.get("error")})
            return {
                "response": "안녕하세요! 중고거래 상품 추천을 도와드릴 수 있습니다. 찾고 계신 상품을 알려주시면 추천해드릴 수 있습니다."
            }

        # LLM 응답 추출
        llm_response = result.get("result", "").strip()
        if llm_response:
            return {"response": llm_response}
        else:
            return {
                "response": "안녕하세요! 중고거래 상품 추천을 도와드릴 수 있습니다. 무엇을 찾고 계신가요?"
            }

    except Exception as e:
        logger.exception("일반 대화 처리 중 오류 발생")
        # 에러 발생 시 기본 응답
        return {
            "response": "안녕하세요! 중고거래 상품 추천을 도와드릴 수 있습니다. 찾고 계신 상품을 알려주시면 추천해드릴 수 있습니다."
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """헬스 체크"""
    return {"status": "healthy", "service": "ReCo"}
