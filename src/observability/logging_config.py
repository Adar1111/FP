"""Configure JSON event logs for measurement ingestion."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock


DEFAULT_LOG_PATH = Path(__file__).resolve().parents[2] / "results" / "logs" / "ingestion.jsonl"
_LOGGER_NAME = "ofdr.ingestion"
_CONFIG_LOCK = RLock()


class JsonFormatter(logging.Formatter):
    """Write only the event fields, without measurement contents."""

    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "event": record.getMessage(),
            "level": record.levelname,
            "stage": record.stage,
            "measurement_id": record.measurement_id,
        }
        for field in ("error", "error_type", "stored_path", "run_id", "elapsed_seconds"):
            value = getattr(record, field, None)
            if value is not None:
                event[field] = value
        return json.dumps(event, ensure_ascii=False)


class EventFileHandler(logging.FileHandler):
    """Raise write errors instead of letting logging hide them."""

    def handleError(self, record: logging.LogRecord) -> None:
        # Logging calls this inside the write error's exception handler.
        raise


def configure_logging(log_path: str | Path = DEFAULT_LOG_PATH) -> logging.Logger:
    """Append UTF-8 JSON lines to one log file. Reuse repeated configuration."""
    path = Path(log_path).resolve()
    with _CONFIG_LOCK:
        logger = logging.getLogger(_LOGGER_NAME)
        for handler in logger.handlers:
            if isinstance(handler, EventFileHandler) and handler.baseFilename == str(path):
                return logger

        path.parent.mkdir(parents=True, exist_ok=True)
        handler = EventFileHandler(path, mode="a", encoding="utf-8")
        handler.setFormatter(JsonFormatter())
        for previous in logger.handlers[:]:
            logger.removeHandler(previous)
            previous.close()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger


def log_event(event: str, level: str, stage: str, measurement_id: str | None = None, **details: str | float | None) -> None:
    """Record an event. Configure the default log on first use; raise errors."""
    if level not in ("INFO", "WARNING", "ERROR"):
        raise ValueError("level must be INFO, WARNING, or ERROR")
    with _CONFIG_LOCK:
        logger = logging.getLogger(_LOGGER_NAME)
        if not logger.handlers:
            logger = configure_logging()
        logger.log(getattr(logging, level), event, extra={"stage": stage, "measurement_id": measurement_id, **details})
