"""
데이터베이스 연결 및 세션 관리
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from server.utils import config

# 환경 변수에서 DB URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./history.db")


def _create_engine():
    engine_kwargs = {"echo": False}

    if DATABASE_URL.startswith("sqlite"):
        engine_kwargs["connect_args"] = {
            "check_same_thread": False,
            "timeout": config.DB_CONN_TIMEOUT,
        }
    else:
        engine_kwargs.update(
            {
                "pool_pre_ping": True,
                "pool_size": config.DB_POOL_SIZE,
                "max_overflow": config.DB_MAX_OVERFLOW,
                "pool_timeout": config.DB_POOL_TIMEOUT,
                "pool_recycle": 1800,
            }
        )

    return create_engine(DATABASE_URL, **engine_kwargs)


# Engine 생성
engine = _create_engine()

# SessionLocal 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


class Database:
    """데이터베이스 연결 관리"""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Generator:
        """세션 생성"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_tables(self):
        """테이블 생성"""
        Base.metadata.create_all(bind=self.engine)


# 전역 데이터베이스 인스턴스
database = Database()
"""
데이터베이스 연결 및 세션 관리
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# 환경 변수에서 DB URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./history.db")

# Engine 생성
engine = create_engine(DATABASE_URL, echo=False)

# SessionLocal 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


class Database:
    """데이터베이스 연결 관리"""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Generator:
        """세션 생성"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def create_tables(self):
        """테이블 생성"""
        Base.metadata.create_all(bind=self.engine)


# 전역 데이터베이스 인스턴스
database = Database()
