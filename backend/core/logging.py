"""Centralized logging configuration with optional JSON output.

Usage:

    from core.logging import configure_logging
    configure_logging()          # reads LOG_FORMAT from settings
"""

from __future__ import annotations

import json
import logging

from core.config import settings


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line (machine-parseable)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("request_"):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    """Configure root logging according to settings (text or JSON format)."""
    fmt = "text"
    try:
        fmt = settings.LOG_FORMAT.lower()
    except Exception:  # pragma: no cover - settings may be uninitialized
        fmt = "text"

    handler = logging.StreamHandler()
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(level=level, handlers=[handler], force=True)


__all__ = ["configure_logging", "JsonFormatter"]
