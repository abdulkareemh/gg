"""Structured logging for Noor AI.

Provides consistent, structured log output across the application.
In production, logs are JSON-formatted for easy parsing by log aggregators.
"""

import logging
import sys
import json
from datetime import datetime

from src.utils.config import settings


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for production."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key in ("merchant_id", "phone", "platform", "order_id", "action"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """Simple colored log format for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        return (
            f"{color}[{record.levelname:>7}]{self.RESET} "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging():
    """Configure logging for the application."""
    root_logger = logging.getLogger("noor")
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.app_env == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(SimpleFormatter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the noor prefix."""
    return logging.getLogger(f"noor.{name}")


# Initialize logging on import
logger = setup_logging()
