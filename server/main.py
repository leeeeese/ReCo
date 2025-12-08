"""
FastAPI 메인 애플리케이션
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers import workflow_router, history_router
from server.db.database import database
from server.utils.logger import setup_logging, get_logger
from server.middleware.rate_limit import RateLimitMiddleware
from server.utils.config import PORT, HOST
import os

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="ReCo - 중고거래 추천 시스템",
    description="LangGraph 기반 중고거래 상품 추천 시스템",
    version="0.1.0"
)

# CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://localhost:5173"],  # Vite 기본 포트
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting 미들웨어 추가
app.add_middleware(
    RateLimitMiddleware,
    requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "100")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600")),
    enable_user_limit=os.getenv(
        "RATE_LIMIT_ENABLE_USER", "true").lower() == "true",
    enable_ip_limit=os.getenv("RATE_LIMIT_ENABLE_IP",
                              "true").lower() == "true",
)

# 라우터 등록
app.include_router(workflow_router)
app.include_router(history_router)

# 데이터베이스 초기화


async def warmup_workflow():
    """워크플로우 및 LLM 클라이언트 warmup"""
    try:
        logger.info("워크플로우 warmup 시작...")

        # 워크플로우 앱 초기화 (싱글톤)
        from server.routers.workflow import get_workflow_app
        workflow_app = get_workflow_app()
        logger.info("워크플로우 앱 초기화 완료")

        # LLM 클라이언트 warmup (각 Agent의 LLM 클라이언트 초기화)
        from server.utils.llm_agent import create_agent

        # 각 에이전트 타입별로 LLM 클라이언트 생성 (초기화만, 실제 호출은 안 함)
        agent_types = ["product_agent", "reliability_agent", "final_matcher"]
        for agent_type in agent_types:
            try:
                agent = create_agent(agent_type)
                # LLM 클라이언트가 정상적으로 생성되었는지 확인
                if agent.client is None:
                    logger.warning(f"{agent_type} LLM 클라이언트 생성 실패 (API 키 없음)")
                else:
                    logger.info(f"{agent_type} LLM 클라이언트 초기화 완료")
            except Exception as e:
                logger.warning(f"{agent_type} 초기화 중 오류: {e}")

        logger.info("워크플로우 warmup 완료")
    except Exception as e:
        logger.error(f"워크플로우 warmup 실패: {e}", exc_info=True)


@app.on_event("startup")
async def startup():
    # 환경 변수 검증은 이미 config.py에서 수행됨
    logger.info("환경 변수 검증 완료")

    database.create_tables()
    logger.info("데이터베이스 초기화 완료")

    # 캐시 시스템 초기화 확인
    from server.utils.cache import cache_manager
    if cache_manager.use_redis:
        logger.info("Redis 캐시 시스템 활성화")
    else:
        logger.info("In-memory 캐시 시스템 사용")

    # Cold start 대비: 워크플로우 warmup
    await warmup_workflow()


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "ReCo - 중고거래 추천 시스템",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host=HOST,
        port=PORT,
        reload=True
    )
