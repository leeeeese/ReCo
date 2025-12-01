"""
설정 관리 모듈
환경 변수 로드 및 설정 관리
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# ==================== 환경 변수 검증 ====================

class ConfigValidationError(Exception):
    """설정 검증 오류"""

    pass


def validate_required_env(env_name: str, env_value: Any, error_message: str = None):
    """필수 환경 변수 검증"""
    if env_value is None or env_value == "":
        msg = error_message or f"필수 환경 변수 {env_name}가 설정되지 않았습니다."
        raise ConfigValidationError(msg)
    return env_value


def validate_type(env_name: str, env_value: Any, expected_type: type, default_value: Any = None):
    """환경 변수 타입 검증"""
    if env_value is None:
        if default_value is not None:
            return default_value
        raise ConfigValidationError(f"환경 변수 {env_name}가 설정되지 않았습니다.")

    try:
        if expected_type == int:
            return int(env_value)
        elif expected_type == float:
            return float(env_value)
        elif expected_type == bool:
            if isinstance(env_value, str):
                return env_value.lower() in ("true", "1", "yes", "on")
            return bool(env_value)
        else:
            return expected_type(env_value)
    except (ValueError, TypeError) as e:
        raise ConfigValidationError(
            f"환경 변수 {env_name}의 타입이 올바르지 않습니다. 예상: {expected_type.__name__}, 값: {env_value}"
        ) from e


def validate_range(
    env_name: str, env_value: Any, min_value: Any = None, max_value: Any = None
):
    """환경 변수 범위 검증"""
    if min_value is not None and env_value < min_value:
        raise ConfigValidationError(
            f"환경 변수 {env_name}의 값이 최소값({min_value})보다 작습니다. 현재 값: {env_value}"
        )

    if max_value is not None and env_value > max_value:
        raise ConfigValidationError(
            f"환경 변수 {env_name}의 값이 최대값({max_value})보다 큽니다. 현재 값: {env_value}"
        )

    return env_value


def validate_choice(env_name: str, env_value: Any, choices: List[Any]):
    """환경 변수 선택값 검증"""
    if env_value not in choices:
        raise ConfigValidationError(
            f"환경 변수 {env_name}의 값이 허용된 선택지에 없습니다. "
            f"허용된 값: {choices}, 현재 값: {env_value}"
        )
    return env_value


# ==================== 환경 변수 로드 및 검증 ====================

def load_and_validate_config() -> Dict[str, Any]:
    """환경 변수 로드 및 검증"""
    errors: List[str] = []

    try:
        # 필수 환경 변수
        OPENAI_API_KEY = validate_required_env(
            "OPENAI_API_KEY",
            os.getenv("OPENAI_API_KEY"),
            "OPENAI_API_KEY는 필수입니다. .env 파일에 설정해주세요.",
        )

        # 선택적 환경 변수 (기본값 있음)
        OPENAI_MODEL = validate_type(
            "OPENAI_MODEL", os.getenv("OPENAI_MODEL"), str, "gpt-4o-mini"
        )
        SERPAPI_KEY = os.getenv("SERPAPI_KEY")  # 선택사항

        LLM_TIMEOUT_SECONDS = validate_type(
            "LLM_TIMEOUT_SECONDS", os.getenv("LLM_TIMEOUT_SECONDS"), float, 30.0
        )
        LLM_TIMEOUT_SECONDS = validate_range(
            "LLM_TIMEOUT_SECONDS", LLM_TIMEOUT_SECONDS, min_value=1.0, max_value=300.0
        )

        LLM_MAX_RETRIES = validate_type(
            "LLM_MAX_RETRIES", os.getenv("LLM_MAX_RETRIES"), int, 2
        )
        LLM_MAX_RETRIES = validate_range(
            "LLM_MAX_RETRIES", LLM_MAX_RETRIES, min_value=0, max_value=10
        )

        # 데이터베이스 설정
        DATABASE_URL = validate_type(
            "DATABASE_URL",
            os.getenv("DATABASE_URL"),
            str,
            "sqlite:///./history.db",
        )

        PRICER_DATABASE_URL = validate_type(
            "PRICER_DATABASE_URL",
            os.getenv("PRICER_DATABASE_URL"),
            str,
            "sqlite:///./used_pricer.db",
        )

        DB_POOL_SIZE = validate_type(
            "DB_POOL_SIZE", os.getenv("DB_POOL_SIZE"), int, 5
        )
        DB_POOL_SIZE = validate_range("DB_POOL_SIZE", DB_POOL_SIZE, min_value=1, max_value=100)

        DB_MAX_OVERFLOW = validate_type(
            "DB_MAX_OVERFLOW", os.getenv("DB_MAX_OVERFLOW"), int, 10
        )
        DB_MAX_OVERFLOW = validate_range(
            "DB_MAX_OVERFLOW", DB_MAX_OVERFLOW, min_value=0, max_value=200
        )

        DB_POOL_TIMEOUT = validate_type(
            "DB_POOL_TIMEOUT", os.getenv("DB_POOL_TIMEOUT"), int, 30
        )
        DB_POOL_TIMEOUT = validate_range(
            "DB_POOL_TIMEOUT", DB_POOL_TIMEOUT, min_value=1, max_value=300
        )

        DB_CONN_TIMEOUT = validate_type(
            "DB_CONN_TIMEOUT", os.getenv("DB_CONN_TIMEOUT"), int, 30
        )
        DB_CONN_TIMEOUT = validate_range(
            "DB_CONN_TIMEOUT", DB_CONN_TIMEOUT, min_value=1, max_value=300
        )

        # 서버 설정
        HOST = validate_type("HOST", os.getenv("HOST"), str, "0.0.0.0")
        PORT = validate_type("PORT", os.getenv("PORT"), int, 8000)
        PORT = validate_range("PORT", PORT, min_value=1, max_value=65535)

        WORKFLOW_TIMEOUT_SECONDS = validate_type(
            "WORKFLOW_TIMEOUT_SECONDS", os.getenv("WORKFLOW_TIMEOUT_SECONDS"), int, 60
        )
        WORKFLOW_TIMEOUT_SECONDS = validate_range(
            "WORKFLOW_TIMEOUT_SECONDS",
            WORKFLOW_TIMEOUT_SECONDS,
            min_value=10,
            max_value=600,
        )

        # 기타 설정
        UPDATE_BATCH_LIMIT = validate_type(
            "UPDATE_BATCH_LIMIT", os.getenv("UPDATE_BATCH_LIMIT"), int, 100
        )
        UPDATE_BATCH_LIMIT = validate_range(
            "UPDATE_BATCH_LIMIT", UPDATE_BATCH_LIMIT, min_value=1, max_value=10000
        )

        USER_AGENT = validate_type(
            "USER_AGENT",
            os.getenv("USER_AGENT"),
            str,
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )

        # Redis 설정 (선택사항)
        REDIS_URL = validate_type(
            "REDIS_URL", os.getenv("REDIS_URL"), str, "redis://localhost:6379/0"
        )
        REDIS_ENABLED = validate_type(
            "REDIS_ENABLED", os.getenv("REDIS_ENABLED"), bool, False
        )

        return {
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "OPENAI_MODEL": OPENAI_MODEL,
            "SERPAPI_KEY": SERPAPI_KEY,
            "LLM_TIMEOUT_SECONDS": LLM_TIMEOUT_SECONDS,
            "LLM_MAX_RETRIES": LLM_MAX_RETRIES,
            "DATABASE_URL": DATABASE_URL,
            "PRICER_DATABASE_URL": PRICER_DATABASE_URL,
            "DB_POOL_SIZE": DB_POOL_SIZE,
            "DB_MAX_OVERFLOW": DB_MAX_OVERFLOW,
            "DB_POOL_TIMEOUT": DB_POOL_TIMEOUT,
            "DB_CONN_TIMEOUT": DB_CONN_TIMEOUT,
            "HOST": HOST,
            "PORT": PORT,
            "WORKFLOW_TIMEOUT_SECONDS": WORKFLOW_TIMEOUT_SECONDS,
            "UPDATE_BATCH_LIMIT": UPDATE_BATCH_LIMIT,
            "USER_AGENT": USER_AGENT,
            "REDIS_URL": REDIS_URL,
            "REDIS_ENABLED": REDIS_ENABLED,
        }

    except ConfigValidationError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"설정 검증 중 예상치 못한 오류: {str(e)}")

    if errors:
        error_message = "\n".join([f"❌ {error}" for error in errors])
        print("\n" + "=" * 60)
        print("환경 변수 검증 실패")
        print("=" * 60)
        print(error_message)
        print("\n.env 파일을 확인하고 필요한 환경 변수를 설정해주세요.")
        print("=" * 60 + "\n")
        sys.exit(1)

    return {}


# ==================== 환경 변수 로드 (검증 포함) ====================

# 설정 검증 및 로드
_config = load_and_validate_config()

# 전역 변수로 설정값 할당
OPENAI_API_KEY = _config.get("OPENAI_API_KEY")
OPENAI_MODEL = _config.get("OPENAI_MODEL", "gpt-4o-mini")
SERPAPI_KEY = _config.get("SERPAPI_KEY")
LLM_TIMEOUT_SECONDS = _config.get("LLM_TIMEOUT_SECONDS", 30.0)
LLM_MAX_RETRIES = _config.get("LLM_MAX_RETRIES", 2)

DATABASE_URL = _config.get("DATABASE_URL", "sqlite:///./history.db")
PRICER_DATABASE_URL = _config.get("PRICER_DATABASE_URL", "sqlite:///./used_pricer.db")
DB_POOL_SIZE = _config.get("DB_POOL_SIZE", 5)
DB_MAX_OVERFLOW = _config.get("DB_MAX_OVERFLOW", 10)
DB_POOL_TIMEOUT = _config.get("DB_POOL_TIMEOUT", 30)
DB_CONN_TIMEOUT = _config.get("DB_CONN_TIMEOUT", 30)

HOST = _config.get("HOST", "0.0.0.0")
PORT = _config.get("PORT", 8000)
WORKFLOW_TIMEOUT_SECONDS = _config.get("WORKFLOW_TIMEOUT_SECONDS", 60)

UPDATE_BATCH_LIMIT = _config.get("UPDATE_BATCH_LIMIT", 100)
USER_AGENT = _config.get(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
)

REDIS_URL = _config.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_ENABLED = _config.get("REDIS_ENABLED", False)


# ==================== 기존 호환성 함수 ====================

def validate_config() -> Dict[str, Any]:
    """설정 검증 및 상태 반환 (기존 호환성)"""
    status = {
        "openai_api_key": "✅ 설정됨" if OPENAI_API_KEY else "❌ 미설정 (필수)",
        "serpapi_key": "✅ 설정됨" if SERPAPI_KEY else "⚠️ 미설정 (선택)",
        "database_url": DATABASE_URL,
        "redis_enabled": "✅ 활성화" if REDIS_ENABLED else "❌ 비활성화",
    }
    return status


if __name__ == "__main__":
    print("=== ReCo 설정 검증 ===")
    status = validate_config()
    for key, value in status.items():
        print(f"{key}: {value}")
