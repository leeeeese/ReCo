"""
히스토리 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from server.db.database import Database
from server.db.schemas import HistoryResponse, HistoryRequest
from server.db.models import History

router = APIRouter(prefix="/api/v1/history", tags=["history"])

database = Database()


def get_db():
    """DB 세션 의존성"""
    db = next(database.get_session())
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[HistoryResponse])
async def get_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """히스토리 조회"""
    history = db.query(History).offset(skip).limit(limit).all()
    return history


@router.post("/")
async def create_history(
    history_data: HistoryRequest,
    db: Session = Depends(get_db)
):
    """히스토리 저장"""
    history = History(
        user_input=history_data.user_input.dict(),
        search_query=history_data.search_query,
        persona_type=None,  # 페르소나 사용 안 함
        results=[r.dict() for r in history_data.results]
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
