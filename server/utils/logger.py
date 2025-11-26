"""
로깅 설정 모듈
"""

import logging
import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import json
from typing import Any, Dict

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE_PATH = LOG_DIR / "app.log"

_logging_configured = False


def _json_serialize(obj: Any) -> Any:
    """JSON 직렬화 가능한 형태로 변환"""
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {k: _json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_json_serialize(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # 객체인 경우 dict로 변환
        return _json_serialize(obj.__dict__)
    else:
        # 그 외의 경우 문자열로 변환
        return str(obj)


class JsonFormatter(logging.Formatter):
    """JSON 형태의 로그 포맷터"""

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        # 추가 필드 (extra 파라미터 등)
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__:
                try:
                    # JSON 직렬화 가능한 형태로 변환
                    log_record[key] = _json_serialize(value)
                except Exception:
                    # 직렬화 실패 시 문자열로 변환
                    log_record[key] = str(value)

        try:
            return json.dumps(log_record, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            # 최종 직렬화 실패 시 안전하게 처리
            log_record["_serialization_error"] = "Failed to serialize log record"
            return json.dumps(log_record, ensure_ascii=False, default=str)


def setup_logging() -> None:
    """로깅 설정"""
    global _logging_configured
    if _logging_configured:
        return

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": DEFAULT_LOG_LEVEL,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "level": DEFAULT_LOG_LEVEL,
                "filename": str(LOG_FILE_PATH),
                "maxBytes": 5 * 1024 * 1024,  # 5MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": DEFAULT_LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(logging_config)
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """로거 생성"""
    if not _logging_configured:
        setup_logging()
    return logging.getLogger(name)

