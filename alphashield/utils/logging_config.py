from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any


LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading.log")


def _ensure_log_dir() -> None:
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Allow passing a dict via extra={"event":..., ...}
        for key in [
            "event",
            "date",
            "loan_id",
            "step",
            "coverage_ratio",
            "template",
            "weights",
            "costs",
            "metrics",
            "duration_ms",
        ]:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, default=str)


_def_level = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger(name: str) -> logging.Logger:
    _ensure_log_dir()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(_def_level)

    formatter = JsonFormatter()

    # File handler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=2)
    fh.setLevel(_def_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(_def_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
