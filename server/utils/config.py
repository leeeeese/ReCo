"""
설정 관리 모듈
환경 변수 로드 및 설정 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # 선택사항

# 데이터베이스 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./history.db")
PRICER_DATABASE_URL = os.getenv(
    "PRICER_DATABASE_URL", "sqlite:///./used_pricer.db")

# 서버 설정
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Playbook 경로
PLAYBOOK_DIR = os.getenv("PLAYBOOK_DIR", "./server/retrieval/playbook")

# 기타 설정
UPDATE_BATCH_LIMIT = int(os.getenv("UPDATE_BATCH_LIMIT", "100"))
USER_AGENT = os.getenv(
    "USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")


def validate_config() -> Dict[str, Any]:
    """설정 검증 및 상태 반환"""
    status = {
        "openai_api_key": "✅ 설정됨" if OPENAI_API_KEY else "❌ 미설정 (필수)",
        "serpapi_key": "✅ 설정됨" if SERPAPI_KEY else "⚠️ 미설정 (선택)",
        "database_url": DATABASE_URL,
        "playbook_dir": PLAYBOOK_DIR,
        "playbook_exists": Path(PLAYBOOK_DIR).exists(),
    }
    return status


if __name__ == "__main__":
    from typing import Dict, Any
    print("=== ReCo 설정 검증 ===")
    status = validate_config()
    for key, value in status.items():
        print(f"{key}: {value}")
