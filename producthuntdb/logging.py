"""Production-grade logging setup using Loguru.

This module configures structured logging with:
- JSON output for production environments
- Context variables for request tracking (request_id, user_id)
- Custom serialization without Loguru's verbose defaults
- File rotation and compression
- Async logging for performance

Reference:
    - Dash0 Loguru Guide: https://www.dash0.com/guides/python-logging-with-loguru
    - DataCamp Tutorial: https://www.datacamp.com/tutorial/loguru-python-logging-tutorial
    - docs/source/refactoring-enhancements.md lines 420-570

Example:
    >>> from producthuntdb.logging import logger, request_id_var
    >>> import uuid
    >>> request_id_var.set(str(uuid.uuid4()))
    >>> logger.info("Processing request", user_id=123, action="sync")
    >>> # JSON output includes request_id automatically
"""

import json
import sys
import traceback
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from loguru import logger as loguru_logger

from producthuntdb.config import settings

# =============================================================================
# Context Variables for Request Tracking
# =============================================================================

# Context variables maintain values across async calls
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
operation_var: ContextVar[str | None] = ContextVar("operation", default=None)


# =============================================================================
# Custom JSON Serialization
# =============================================================================


def serialize(record: dict[str, Any]) -> str:
    """Custom JSON serializer for production logs.

    Produces clean, structured JSON without Loguru's verbose defaults.
    Includes context variables (request_id, user_id, operation) when set.

    Args:
        record: Loguru log record dictionary

    Returns:
        JSON string with selected fields and context

    Example:
        >>> # Output: {"time": "2024-01-01T12:00:00", "level": "INFO", ...}
    """
    subset = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add custom context from contextvars
    if request_id := request_id_var.get():
        subset["request_id"] = request_id
    if user_id := user_id_var.get():
        subset["user_id"] = user_id
    if operation := operation_var.get():
        subset["operation"] = operation

    # Add extra fields from logger.bind() or keyword arguments
    subset.update(record["extra"])

    # Add exception info if present
    if exc := record["exception"]:
        subset["exception"] = {
            "type": exc.type.__name__ if exc.type else None,
            "value": str(exc.value),
            "traceback": traceback.format_exception(
                exc.type, exc.value, exc.traceback
            ),
        }

    return json.dumps(subset, default=str)


def patching(record: dict[str, Any]) -> None:
    """Patch log records with serialized JSON.

    Args:
        record: Loguru log record to patch (modified in-place)
    """
    record["serialized"] = serialize(record)


def custom_formatter(record: dict[str, Any]) -> str:
    """Custom formatter using pre-serialized JSON.

    Args:
        record: Loguru log record with 'serialized' key

    Returns:
        Formatted log line (JSON + newline)
    """
    return "{serialized}\n"


# =============================================================================
# Logger Configuration
# =============================================================================


def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_file: Path | None = None,
    colorize: bool = True,
) -> Any:
    """Configure Loguru for production use.

    This function:
    1. Removes default Loguru handler
    2. Patches logger with custom JSON serialization
    3. Adds stdout handler (JSON or human-readable)
    4. Optionally adds file handler with rotation/compression

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Output JSON format (True for production)
        log_file: Optional file path for log output
        colorize: Enable colored output for human-readable logs

    Returns:
        Configured Loguru logger instance

    Example:
        >>> logger = setup_logging(level="DEBUG", json_logs=False)
        >>> logger.info("Application started")
    """
    # Remove default handler
    loguru_logger.remove()

    # Patch logger with custom serialization
    patched_logger = loguru_logger.patch(patching)

    if json_logs:
        # Production: JSON logs to stdout
        patched_logger.add(
            sys.stdout,
            level=level,
            format=custom_formatter,
            serialize=False,  # We handle serialization manually
        )
    else:
        # Development: Human-readable colored logs
        format_str = (
            "<green>{time:HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        patched_logger.add(
            sys.stdout,
            level=level,
            format=format_str,
            colorize=colorize,
        )

    # Optional file output with rotation and compression
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        patched_logger.add(
            log_file,
            level=level,
            format=custom_formatter if json_logs else "{time} | {level} | {message}",
            rotation="100 MB",  # Rotate when file reaches 100MB
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress rotated logs
            enqueue=True,  # Async logging for performance
        )

    return patched_logger


# =============================================================================
# Initialize Global Logger
# =============================================================================

# Configure logger based on settings
logger = setup_logging(
    level=settings.log_level,
    json_logs=settings.log_json,
    log_file=settings.data_dir / "producthuntdb.log" if settings.log_to_file else None,
    colorize=not settings.log_json,  # Disable colors for JSON logs
)


# =============================================================================
# Utility Functions
# =============================================================================


def set_request_context(
    request_id: str | None = None,
    user_id: str | None = None,
    operation: str | None = None,
) -> None:
    """Set context variables for the current async context.

    These values will be automatically included in all log messages
    within the current async context.

    Args:
        request_id: Unique identifier for the request/operation
        user_id: User identifier (if applicable)
        operation: Operation name (e.g., "sync_posts", "export_csv")

    Example:
        >>> import uuid
        >>> set_request_context(
        ...     request_id=str(uuid.uuid4()),
        ...     operation="sync_posts"
        ... )
        >>> logger.info("Starting sync")
        # Log includes request_id and operation automatically
    """
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if operation is not None:
        operation_var.set(operation)


def clear_request_context() -> None:
    """Clear all context variables for the current async context.

    Call this at the end of request processing to avoid leaking
    context into subsequent operations.

    Example:
        >>> set_request_context(request_id="123", operation="sync")
        >>> logger.info("Processing")
        >>> clear_request_context()
        >>> logger.info("Next operation")  # No context included
    """
    request_id_var.set(None)
    user_id_var.set(None)
    operation_var.set(None)


def get_request_context() -> dict[str, str | None]:
    """Get current context variable values.

    Returns:
        Dictionary with current context values (may contain None)

    Example:
        >>> set_request_context(request_id="abc123")
        >>> ctx = get_request_context()
        >>> print(ctx["request_id"])
        abc123
    """
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
        "operation": operation_var.get(),
    }


# =============================================================================
# Export Public API
# =============================================================================

__all__ = [
    "logger",
    "request_id_var",
    "user_id_var",
    "operation_var",
    "set_request_context",
    "clear_request_context",
    "get_request_context",
    "setup_logging",
]
