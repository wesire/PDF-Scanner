"""Logging configuration for PDF Context Narrator with structured logging support."""

import json
import logging
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from contextvars import ContextVar

from pdf_context_narrator.config import get_settings

# Context variable for tracking operation IDs across async boundaries
_operation_id: ContextVar[Optional[str]] = ContextVar("operation_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON with structured fields.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add operation ID if present
        operation_id = _operation_id.get()
        if operation_id:
            log_data["operation_id"] = operation_id

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    structured: bool = False,
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        structured: If True, use JSON structured logging
    """
    settings = get_settings()

    # Use provided level or fall back to settings
    log_level = level or settings.log_level

    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(settings.log_format)

    # Configure root logger
    root_logger = logging.getLogger("pdf_context_narrator")
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    file_path = log_file or settings.log_file
    if file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    root_logger.info(f"Logging configured at {log_level} level")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    # Ensure logging is set up
    if not logging.getLogger("pdf_context_narrator").handlers:
        setup_logging()

    return logging.getLogger(f"pdf_context_narrator.{name}")


@contextmanager
def log_operation(operation_name: str, **extra_fields: Any):
    """
    Context manager for tracking operations with structured logging.

    Automatically generates an operation ID and logs operation start/end.

    Args:
        operation_name: Name of the operation being tracked
        **extra_fields: Additional fields to include in logs

    Yields:
        Dictionary containing operation context (operation_id, start_time)

    Example:
        >>> with log_operation("ingest_pdf", file_path="doc.pdf") as op:
        ...     # Your operation code here
        ...     logger.info("Processing file", extra={"progress": 50})
    """
    operation_id = str(uuid.uuid4())
    token = _operation_id.set(operation_id)

    logger = get_logger("operations")
    start_time = datetime.now(timezone.utc)

    context = {
        "operation_id": operation_id,
        "operation_name": operation_name,
        "start_time": start_time,
        **extra_fields,
    }

    logger.info(f"Operation started: {operation_name}", extra={"extra_fields": context})

    try:
        yield context
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            f"Operation completed: {operation_name}",
            extra={"extra_fields": {**context, "duration_seconds": duration, "status": "success"}},
        )
    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.error(
            f"Operation failed: {operation_name}",
            exc_info=True,
            extra={
                "extra_fields": {
                    **context,
                    "duration_seconds": duration,
                    "status": "failed",
                    "error": str(e),
                }
            },
        )
        raise
    finally:
        _operation_id.reset(token)
