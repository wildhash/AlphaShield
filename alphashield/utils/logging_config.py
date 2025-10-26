from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any


LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading.log")


def _ensure_log_dir() -> None:
    """
    Ensure the configured log directory exists, creating it if necessary.
    
    Attempts to create LOG_DIR and suppresses any exception raised during creation so callers will not receive an error if the directory cannot be created.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        """
        Format a LogRecord into a JSON string containing core fields and selected extras.
        
        Produces a JSON object with keys "level", "logger", and "message", and includes any of the optional extra attributes found on the record: "event", "date", "loan_id", "step", "coverage_ratio", "template", "weights", "costs", "metrics", and "duration_ms". Non-JSON-serializable values are converted to strings during serialization.
        
        Parameters:
            record (logging.LogRecord): The log record to format.
        
        Returns:
            str: A JSON-formatted string representing the payload.
        """
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
    """
    Create or retrieve a logger configured to emit JSON-formatted records to a rotating file and to the console.
    
    This returns an existing logger if it is already configured; otherwise it sets the logger's level from the module's default, attaches a rotating file handler (writing to LOG_FILE with rotation) and a console stream handler, both using JsonFormatter.
    
    Parameters:
        name (str): Name of the logger to retrieve or create.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
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