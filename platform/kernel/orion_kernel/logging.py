"""
Platform Kernel: structured logging.

Identical behavior for every ORION Platform product: JSON or plain-text
output (product chooses via its own Settings.LOG_JSON), request ID /
path / method / status / duration attached when present on the log
record. Products call `configure_logging(settings)` once at startup.
"""
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("request_id", "path", "method", "status_code", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


def configure_logging(settings) -> None:
    """
    settings must expose: LOG_LEVEL (str), LOG_JSON (bool), DB_ECHO (bool).
    Any OrionBaseSettings subclass satisfies this.
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if getattr(settings, "DB_ECHO", False) else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
