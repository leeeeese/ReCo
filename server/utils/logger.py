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

        # 추가 필드
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)


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

