"""Comprehensive tests for telemetry.py OpenTelemetry integration.

Tests cover:
- TracerProvider initialization and configuration
- Tracer creation and span operations
- Span attributes and exception recording
- Context synchronization with logging
- Development vs production modes
- Shutdown and cleanup
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

try:
    from opentelemetry.trace import StatusCode
    from opentelemetry.trace.span import Span
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    StatusCode = None
    Span = None

# Skip all tests if opentelemetry not installed
pytestmark = pytest.mark.skipif(
    not OPENTELEMETRY_AVAILABLE,
    reason="opentelemetry package not installed"
)

from producthuntdb.telemetry import (
    add_span_attributes,
    create_span_context,
    get_current_span,
    get_tracer,
    initialize_telemetry,
    record_exception_in_span,
    set_span_error,
    shutdown_telemetry,
    sync_logging_context_to_span,
)


@pytest.fixture(autouse=True)
def reset_telemetry():
    """Reset telemetry state between tests."""
    import producthuntdb.telemetry as telemetry_module

    # Store original values
    original_provider = telemetry_module._tracer_provider
    original_initialized = telemetry_module._initialized

    # Reset state
    telemetry_module._tracer_provider = None
    telemetry_module._initialized = False

    yield

    # Restore original state
    telemetry_module._tracer_provider = original_provider
    telemetry_module._initialized = original_initialized


class TestInitializeTelemetry:
    """Test telemetry initialization."""

    def test_initialize_creates_tracer_provider(self, monkeypatch):
        """Test that initialization creates a tracer provider."""
        monkeypatch.setenv("OTEL_SERVICE_NAME", "test-service")
        monkeypatch.setenv("ENVIRONMENT", "testing")

        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"
            
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            initialize_telemetry()

            # Verify provider was created
            mock_provider_class.assert_called_once()
            assert mock_provider.add_span_processor.call_count == 0  # No processors without tracing

    def test_initialize_with_otlp_exporter_production(self, monkeypatch):
        """Test OTLP exporter is added when tracing enabled."""
        monkeypatch.setenv("OTEL_SERVICE_NAME", "prod-service")

        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.OTLPSpanExporter") as mock_otlp, \
             patch("producthuntdb.telemetry.BatchSpanProcessor") as mock_processor, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = True
            mock_settings.otlp_endpoint = "http://localhost:4317"
            mock_settings.is_development = False
            mock_settings.environment.value = "production"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            mock_exporter = MagicMock()
            mock_otlp.return_value = mock_exporter
            mock_proc = MagicMock()
            mock_processor.return_value = mock_proc

            initialize_telemetry()

            # Verify OTLP exporter created
            mock_otlp.assert_called_once_with(endpoint="http://localhost:4317")
            mock_processor.assert_called_once_with(mock_exporter)
            mock_provider.add_span_processor.assert_called_once_with(mock_proc)

    def test_initialize_with_console_exporter_development(self, monkeypatch):
        """Test console exporter is added in development mode."""
        monkeypatch.setenv("OTEL_SERVICE_NAME", "dev-service")

        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.ConsoleSpanExporter") as mock_console, \
             patch("producthuntdb.telemetry.BatchSpanProcessor") as mock_processor, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = True
            mock_settings.environment.value = "development"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            mock_exporter = MagicMock()
            mock_console.return_value = mock_exporter
            mock_proc = MagicMock()
            mock_processor.return_value = mock_proc

            initialize_telemetry()

            # Verify console exporter created
            mock_console.assert_called_once()
            assert mock_provider.add_span_processor.call_count == 1

    def test_initialize_idempotent(self, monkeypatch):
        """Test that multiple calls to initialize have no effect."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"
            
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            initialize_telemetry()
            call_count_first = mock_provider_class.call_count

            initialize_telemetry()
            call_count_second = mock_provider_class.call_count

            # Should only be called once
            assert call_count_first == call_count_second == 1

    def test_initialize_sets_global_tracer_provider(self, monkeypatch):
        """Test that initialization sets global tracer provider."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.trace.set_tracer_provider") as mock_set_global, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            initialize_telemetry()

            mock_set_global.assert_called_once_with(mock_provider)

    def test_initialize_handles_otlp_error(self, monkeypatch):
        """Test that OTLP exporter errors are handled gracefully."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.OTLPSpanExporter") as mock_otlp, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = True
            mock_settings.otlp_endpoint = "invalid://endpoint"
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            mock_otlp.side_effect = Exception("Connection failed")

            # Should raise ValueError with invalid endpoint
            with pytest.raises(ValueError, match="Invalid OTLP endpoint"):
                initialize_telemetry()


class TestGetTracer:
    """Test tracer retrieval."""

    def test_get_tracer_returns_tracer(self, monkeypatch):
        """Test that get_tracer returns a tracer instance."""
        with patch("producthuntdb.telemetry.trace.get_tracer") as mock_get, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"
            
            mock_tracer = MagicMock()
            mock_get.return_value = mock_tracer

            tracer = get_tracer("test_module")

            mock_get.assert_called_once_with("test_module")
            assert tracer == mock_tracer

    def test_get_tracer_initializes_if_needed(self, monkeypatch):
        """Test that get_tracer initializes telemetry if not already done."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.trace.get_tracer") as mock_get, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            mock_tracer = MagicMock()
            mock_get.return_value = mock_tracer

            tracer = get_tracer("test_module")

            # Should have initialized
            mock_provider_class.assert_called_once()
            assert tracer == mock_tracer


class TestSpanAttributes:
    """Test span attribute operations."""

    def test_add_span_attributes_basic_types(self):
        """Test adding basic type attributes to span."""
        mock_span = MagicMock(spec=Span)

        attributes = {
            "string_attr": "value",
            "int_attr": 42,
            "float_attr": 3.14,
            "bool_attr": True,
        }

        add_span_attributes(mock_span, attributes)

        # Verify all attributes set
        assert mock_span.set_attribute.call_count == 4
        mock_span.set_attribute.assert_any_call("string_attr", "value")
        mock_span.set_attribute.assert_any_call("int_attr", 42)
        mock_span.set_attribute.assert_any_call("float_attr", 3.14)
        mock_span.set_attribute.assert_any_call("bool_attr", True)

    def test_add_span_attributes_list_conversion(self):
        """Test that list attributes are converted to strings."""
        mock_span = MagicMock(spec=Span)

        attributes = {"list_attr": [1, 2, 3]}

        add_span_attributes(mock_span, attributes)

        mock_span.set_attribute.assert_called_once_with("list_attr", "[1, 2, 3]")

    def test_add_span_attributes_dict_conversion(self):
        """Test that dict attributes are converted to strings."""
        mock_span = MagicMock(spec=Span)

        attributes = {"dict_attr": {"key": "value"}}

        add_span_attributes(mock_span, attributes)

        mock_span.set_attribute.assert_called_once_with("dict_attr", "{'key': 'value'}")

    def test_add_span_attributes_empty_dict(self):
        """Test adding empty attributes dict."""
        mock_span = MagicMock(spec=Span)

        add_span_attributes(mock_span, {})

        mock_span.set_attribute.assert_not_called()


class TestExceptionRecording:
    """Test exception recording in spans."""

    def test_record_exception_in_span_with_status(self):
        """Test recording exception and setting error status."""
        mock_span = MagicMock(spec=Span)
        test_exception = ValueError("Test error")

        record_exception_in_span(mock_span, test_exception, set_status=True)

        mock_span.record_exception.assert_called_once_with(test_exception)
        mock_span.set_status.assert_called_once()
        # Verify status is ERROR
        status_call = mock_span.set_status.call_args[0][0]
        assert status_call.status_code == StatusCode.ERROR
        assert "Test error" in str(status_call.description)

    def test_record_exception_in_span_without_status(self):
        """Test recording exception without setting status."""
        mock_span = MagicMock(spec=Span)
        test_exception = RuntimeError("Another error")

        record_exception_in_span(mock_span, test_exception, set_status=False)

        mock_span.record_exception.assert_called_once_with(test_exception)
        mock_span.set_status.assert_not_called()

    def test_set_span_error(self):
        """Test setting span error status with message."""
        mock_span = MagicMock(spec=Span)

        set_span_error(mock_span, "Custom error message")

        mock_span.set_status.assert_called_once()
        status_call = mock_span.set_status.call_args[0][0]
        assert status_call.status_code == StatusCode.ERROR
        assert status_call.description == "Custom error message"


class TestCurrentSpan:
    """Test current span retrieval."""

    def test_get_current_span(self):
        """Test getting currently active span."""
        with patch("producthuntdb.telemetry.trace.get_current_span") as mock_get:
            mock_span = MagicMock()
            mock_get.return_value = mock_span

            span = get_current_span()

            mock_get.assert_called_once()
            assert span == mock_span


class TestShutdown:
    """Test telemetry shutdown."""

    def test_shutdown_telemetry(self, monkeypatch):
        """Test that shutdown properly closes tracer provider."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"
            
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            # Initialize first
            initialize_telemetry()

            # Then shutdown
            shutdown_telemetry()

            mock_provider.shutdown.assert_called_once()

    def test_shutdown_when_not_initialized(self):
        """Test that shutdown handles uninitialized state."""
        # Should not raise
        shutdown_telemetry()


class TestSpanContext:
    """Test span context manager."""

    def test_create_span_context_without_attributes(self, monkeypatch):
        """Test creating span context without attributes."""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)

        with create_span_context(mock_tracer, "test_span") as span:
            assert span == mock_span

        mock_tracer.start_as_current_span.assert_called_once_with("test_span")

    def test_create_span_context_with_attributes(self, monkeypatch):
        """Test creating span context with attributes."""
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)

        attributes = {"key": "value", "count": 42}

        with create_span_context(mock_tracer, "test_span", attributes) as span:
            assert span == mock_span

        # Verify attributes were set
        assert mock_span.set_attribute.call_count == 2


class TestLoggingContextSync:
    """Test synchronization with logging context."""

    def test_sync_logging_context_to_span_all_vars(self):
        """Test syncing all logging context variables to span."""
        from producthuntdb.logging import operation_var, request_id_var, user_id_var

        mock_span = MagicMock(spec=Span)

        # Set context variables
        request_id_token = request_id_var.set("req-123")
        user_id_token = user_id_var.set("user-456")
        operation_token = operation_var.set("test_operation")

        try:
            sync_logging_context_to_span(mock_span)

            # Verify all attributes set
            assert mock_span.set_attribute.call_count == 3
            mock_span.set_attribute.assert_any_call("request_id", "req-123")
            mock_span.set_attribute.assert_any_call("user_id", "user-456")
            mock_span.set_attribute.assert_any_call("operation", "test_operation")
        finally:
            # Clean up context
            request_id_var.reset(request_id_token)
            user_id_var.reset(user_id_token)
            operation_var.reset(operation_token)

    def test_sync_logging_context_to_span_partial_vars(self):
        """Test syncing with only some context variables set."""
        from producthuntdb.logging import request_id_var

        mock_span = MagicMock(spec=Span)

        # Set only request_id
        request_id_token = request_id_var.set("req-789")

        try:
            sync_logging_context_to_span(mock_span)

            # Only request_id should be set
            assert mock_span.set_attribute.call_count == 1
            mock_span.set_attribute.assert_called_once_with("request_id", "req-789")
        finally:
            request_id_var.reset(request_id_token)

    def test_sync_logging_context_to_span_no_vars(self):
        """Test syncing with no context variables set."""
        mock_span = MagicMock(spec=Span)

        sync_logging_context_to_span(mock_span)

        # No attributes should be set
        mock_span.set_attribute.assert_not_called()


class TestIntegrationScenarios:
    """Test complete telemetry workflows."""

    def test_full_workflow_with_span(self, monkeypatch):
        """Test complete workflow: initialize, create tracer, create span, add attributes."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.trace.set_tracer_provider"), \
             patch("producthuntdb.telemetry.trace.get_tracer") as mock_get_tracer, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            
            mock_tracer = MagicMock()
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
            mock_get_tracer.return_value = mock_tracer

            # Initialize
            initialize_telemetry()

            # Get tracer
            tracer = get_tracer("test_module")

            # Create span
            with tracer.start_as_current_span("test_operation") as span:
                add_span_attributes(span, {"operation": "test", "success": True})

            # Verify workflow
            mock_provider_class.assert_called_once()
            mock_get_tracer.assert_called_once_with("test_module")
            assert mock_span.set_attribute.call_count == 2

    def test_error_handling_workflow(self, monkeypatch):
        """Test workflow with error recording."""
        with patch("producthuntdb.telemetry.TracerProvider") as mock_provider_class, \
             patch("producthuntdb.telemetry.trace.set_tracer_provider"), \
             patch("producthuntdb.telemetry.trace.get_tracer") as mock_get_tracer, \
             patch("producthuntdb.telemetry.settings") as mock_settings:
            
            mock_settings.enable_tracing = False
            mock_settings.is_development = False
            mock_settings.environment.value = "testing"

            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            
            mock_tracer = MagicMock()
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
            mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=False)
            mock_get_tracer.return_value = mock_tracer

            tracer = get_tracer("test_module")

            try:
                with tracer.start_as_current_span("failing_operation") as span:
                    raise ValueError("Test error")
            except ValueError as e:
                record_exception_in_span(mock_span, e)

            # Verify error recorded
            mock_span.record_exception.assert_called_once()
            mock_span.set_status.assert_called_once()
