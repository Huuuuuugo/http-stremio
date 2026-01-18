import logging
import os

from asgi_correlation_id import correlation_id
from pydantic import BaseModel

os.makedirs("logs", exist_ok=True)


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        cid = correlation_id.get()
        record.correlation_id = cid[:8] if cid else "-"
        return True


class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOG_FORMAT: str = "%(asctime)s | %(levelprefix)s | [%(correlation_id)s] | %(name)s - %(message)s"
    FILELOG_FORMAT: str = "%(asctime)s | %(levelname)s | [%(correlation_id)s] | %(name)s - %(message)s"
    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "file": {
            "()": "logging.Formatter",
            "fmt": FILELOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "filters": ["request_id_filter"],
        },
        "file_error": {
            "formatter": "file",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/errors.log",
            "mode": "a",
            "maxBytes": 5 * 1024 * 1024,  # 5 MB
            "backupCount": 3,
            "level": "ERROR",
            "encoding": "utf-8",
            "filters": ["request_id_filter"],
        },
    }
    filters: dict = {
        "request_id_filter": {
            "()": CorrelationIdFilter,
        }
    }
    loggers: dict = {
        # Root logger (captura tudo que não for específico)
        "": {"handlers": ["default", "file_error"], "level": "INFO"},
        "src": {
            "handlers": ["default", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["default", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
    }
