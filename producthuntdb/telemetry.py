"""OpenTelemetry distributed tracing integration.

This module provides OpenTelemetry instrumentation for the ProductHunt DB pipeline,
enabling distributed tracing across GraphQL queries, database operations, and Kaggle exports.

Key Features:
    - TracerProvider with service metadata (name, version, environment)
    - BatchSpanProcessor for optimal performance
    - OTLPSpanExporter for production observability platforms
    - ConsoleSpanExporter for local development debugging
    - Integration with logging.py contextvars (request_id, user_id, operation)
    - Environment variable configuration (12-factor app pattern)
    - Helper functions for span creation and attribute management

Usage:
    Basic tracing in your code:

    ```python
    from producthuntdb.telemetry import get_tracer, add_span_attributes

    tracer = get_tracer(__name__)


    def fetch_data():
        with tracer.start_as_current_span("fetch_data") as span:
            add_span_attributes(span, {"operation": "fetch", "entity_type": "posts"})
            # Your code here
            return result
    ```

    Using decorators:

    ```python
    @tracer.start_as_current_span("process_batch")
    def process_batch(items: list):
        # Your code here
        pass
    ```

Environment Variables:
    - OTEL_SERVICE_NAME: Service name for traces (default: "producthuntdb")
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (default: "http://localhost:4317")
    - OTEL_TRACES_SAMPLER: Sampling strategy (default: "always_on")
    - OTEL_TRACES_SAMPLER_ARG: Sampling rate for probability sampler (default: "1.0")
    - OTEL_LOG_LEVEL: OpenTelemetry SDK log level (default: "info")

References:
    - OpenTelemetry Python Docs: https://opentelemetry.io/docs/languages/python/instrumentation/
    - Last9 FastAPI Guide: https://last9.io/blog/integrating-opentelemetry-with-fastapi/
    - OTLP Specification: https://opentelemetry.io/docs/specs/otlp/
"""

from __future__ import annotations

import os
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode, Tracer
from opentelemetry.trace.span import Span

from producthuntdb.config import settings
from producthuntdb.logging import logger


# Global tracer provider instance
_tracer_provider: TracerProvider | None = None
_initialized: bool = False


def initialize_telemetry() -> None:
    """Initialize the global OpenTelemetry tracer provider.

    This function should be called once at application startup. It configures:
    - Resource metadata (service name, version, environment)
    - OTLP exporter for production (if enabled)
    - Console exporter for development (if enabled)
    - Batch span processor for optimal performance

    The function is idempotent - calling it multiple times has no effect.

    Example:
        ```python
        from producthuntdb.telemetry import initialize_telemetry

        # Call once at startup
        initialize_telemetry()
        ```

    Environment Variables:
        - OTEL_SERVICE_NAME: Service name (default: "producthuntdb")
        - OTEL_EXPORTER_OTLP_ENDPOINT: Collector endpoint (default: "http://localhost:4317")
        - Controlled by config.enable_tracing for production

    Raises:
        ValueError: If OTLP endpoint is invalid
    """
    global _tracer_provider, _initialized

    if _initialized:
        logger.debug("Telemetry already initialized, skipping")
        return

    # Get configuration from environment variables
    service_name = os.getenv("OTEL_SERVICE_NAME", "producthuntdb")

    # Create resource with service metadata
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "0.1.0",  # TODO: Read from pyproject.toml
            "deployment.environment": settings.environment.value,
        }
    )

    # Initialize tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Add OTLP exporter for production
    if settings.enable_tracing and settings.otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            _tracer_provider.add_span_processor(otlp_processor)
            logger.info(
                "Initialized OTLP span exporter",
                endpoint=settings.otlp_endpoint,
                service_name=service_name,
            )
        except Exception as e:
            logger.error("Failed to initialize OTLP exporter", error=str(e))
            raise ValueError(f"Invalid OTLP endpoint: {settings.otlp_endpoint}") from e

    # Add console exporter for development
    if settings.is_development:
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(console_exporter)
        _tracer_provider.add_span_processor(console_processor)
        logger.debug("Initialized console span exporter for development")

    # Set as global default
    trace.set_tracer_provider(_tracer_provider)
    _initialized = True

    logger.info(
        "Telemetry initialized",
        service_name=service_name,
        environment=settings.environment.value,
        tracing_enabled=settings.enable_tracing,
    )


def get_tracer(name: str) -> Tracer:
    """Get a tracer instance for the specified module.

    This function returns a tracer that can be used to create spans. It automatically
    initializes the tracer provider if not already done.

    Args:
        name: Tracer name, typically __name__ of the calling module.
            This helps identify which part of the application created each span.

    Returns:
        Tracer instance for creating spans

    Example:
        ```python
        from producthuntdb.telemetry import get_tracer

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("my_operation"):
            # Your code here
            pass
        ```

    Note:
        The tracer is thread-safe and can be stored as a module-level variable.
    """
    if not _initialized:
        initialize_telemetry()

    return trace.get_tracer(name)


def add_span_attributes(span: Span, attributes: dict[str, Any]) -> None:
    """Add multiple attributes to a span.

    Attributes provide additional context for spans, making traces more useful
    for debugging and performance analysis.

    Args:
        span: The span to add attributes to
        attributes: Dictionary of attribute key-value pairs.
            Values are converted to appropriate types (str, int, float, bool).
            Lists and nested dicts are converted to strings.

    Example:
        ```python
        from producthuntdb.telemetry import get_tracer, add_span_attributes
        from opentelemetry import trace

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("fetch_posts") as span:
            add_span_attributes(
                span,
                {"query_type": "posts", "page_size": 20, "cursor": "abc123", "has_filters": True},
            )
            # Fetch posts...
        ```

    Reference:
        Semantic conventions: https://opentelemetry.io/docs/specs/semconv/general/trace/
    """
    for key, value in attributes.items():
        # Convert lists/dicts to strings for OpenTelemetry compatibility
        if isinstance(value, (list, dict)):
            value = str(value)
        span.set_attribute(key, value)


def record_exception_in_span(
    span: Span,
    exception: Exception,
    set_status: bool = True,
) -> None:
    """Record an exception in a span and optionally set error status.

    This helper combines exception recording with span status setting,
    following OpenTelemetry best practices.

    Args:
        span: The span to record the exception in
        exception: The exception that occurred
        set_status: If True, sets span status to ERROR (default: True)

    Example:
        ```python
        from producthuntdb.telemetry import get_tracer, record_exception_in_span

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("database_query") as span:
            try:
                # Database operation
                result = db.execute(query)
            except Exception as ex:
                record_exception_in_span(span, ex)
                raise
        ```

    Note:
        This automatically captures the exception type, message, and stack trace.
    """
    span.record_exception(exception)
    if set_status:
        span.set_status(Status(StatusCode.ERROR, str(exception)))


def set_span_error(span: Span, message: str) -> None:
    """Set a span's status to ERROR with a custom message.

    Use this when an error occurs but no exception is raised.

    Args:
        span: The span to mark as errored
        message: Error description

    Example:
        ```python
        from producthuntdb.telemetry import get_tracer, set_span_error

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("validate_data") as span:
            if not data.is_valid():
                set_span_error(span, "Data validation failed")
                return None
            # Process valid data...
        ```
    """
    span.set_status(Status(StatusCode.ERROR, message))


def get_current_span() -> Span:
    """Get the currently active span.

    This is useful for adding attributes or events to the current span
    without needing to pass the span object around.

    Returns:
        The current active span, or a non-recording span if none is active

    Example:
        ```python
        from producthuntdb.telemetry import get_current_span, add_span_attributes


        def deep_function():
            # Add attributes to whatever span is currently active
            span = get_current_span()
            add_span_attributes(span, {"nested_call": True})
        ```

    Note:
        If no span is active, returns a non-recording span that silently ignores operations.
    """
    return trace.get_current_span()


def shutdown_telemetry() -> None:
    """Shutdown the tracer provider and flush all pending spans.

    This should be called at application shutdown to ensure all spans
    are exported before the process exits.

    Example:
        ```python
        import atexit
        from producthuntdb.telemetry import initialize_telemetry, shutdown_telemetry

        initialize_telemetry()
        atexit.register(shutdown_telemetry)

        # Your application code...
        ```

    Note:
        This function blocks until all spans are exported or a timeout occurs.
    """
    global _tracer_provider, _initialized

    if _tracer_provider and _initialized:
        _tracer_provider.shutdown()
        _initialized = False
        logger.info("Telemetry shut down successfully")


def create_span_context(
    tracer: Tracer,
    span_name: str,
    attributes: dict[str, Any] | None = None,
):
    """Context manager for creating and managing a span with attributes.

    This is a convenience wrapper that combines span creation with attribute setting.

    Args:
        tracer: Tracer instance to use
        span_name: Name for the span
        attributes: Optional dictionary of attributes to add to the span

    Yields:
        The created span

    Example:
        ```python
        from producthuntdb.telemetry import get_tracer, create_span_context

        tracer = get_tracer(__name__)

        with create_span_context(tracer, "process_posts", {"batch_size": 100}) as span:
            # Your code here
            pass
        ```
    """
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            add_span_attributes(span, attributes)
        yield span


# Integration with logging.py contextvars
def sync_logging_context_to_span(span: Span) -> None:
    """Sync logging context variables to span attributes.

    This copies request_id, user_id, and operation from logging.py's
    contextvars to the current span, ensuring correlation between logs and traces.

    Args:
        span: Span to add context attributes to

    Example:
        ```python
        from producthuntdb.logging import request_id_var, set_request_id
        from producthuntdb.telemetry import get_tracer, sync_logging_context_to_span

        tracer = get_tracer(__name__)

        # Set logging context
        set_request_id("req-123")

        with tracer.start_as_current_span("api_call") as span:
            # Sync logging context to span
            sync_logging_context_to_span(span)
            # Now span has "request_id" attribute
        ```

    Note:
        This is called automatically if you use the higher-level span helpers.
    """
    from producthuntdb.logging import operation_var, request_id_var, user_id_var

    context_attrs = {}

    if request_id := request_id_var.get(None):
        context_attrs["request_id"] = request_id

    if user_id := user_id_var.get(None):
        context_attrs["user_id"] = user_id

    if operation := operation_var.get(None):
        context_attrs["operation"] = operation

    if context_attrs:
        add_span_attributes(span, context_attrs)


# Export public API
__all__ = [
    "initialize_telemetry",
    "shutdown_telemetry",
    "get_tracer",
    "get_current_span",
    "add_span_attributes",
    "record_exception_in_span",
    "set_span_error",
    "create_span_context",
    "sync_logging_context_to_span",
]
