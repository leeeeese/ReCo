"""
FastAPI 메인 애플리케이션
"""

import uvicorn
from fastapi import FastAPI
from server.routers import workflow_router, history_router
from server.db.database import database

app = FastAPI(
    title="ReCo - 중고거래 추천 시스템",
    description="LangGraph 기반 중고거래 상품 추천 시스템",
    version="0.1.0"
)

# 라우터 등록
app.include_router(workflow_router)
app.include_router(history_router)

# 데이터베이스 초기화


@app.on_event("startup")
async def startup():
    database.create_tables()
    print("데이터베이스 초기화 완료")


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
        host="0.0.0.0",
        port=8000,
        reload=True
    )
