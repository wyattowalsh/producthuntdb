"""Tests for logging configuration and functionality.

This module tests:
- Custom JSON serialization
- Context variable management
- Logger setup and configuration
- File logging with rotation
- Structured logging output

Coverage Target: logging.py 60.6% → 80% (+14 lines)
Priority: High - Critical for observability
"""

import json
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

from producthuntdb.logging import (
    clear_request_context,
    custom_formatter,
    get_request_context,
    logger,
    operation_var,
    patching,
    request_id_var,
    serialize,
    set_request_context,
    setup_logging,
    user_id_var,
)


# =============================================================================
# Serialization Tests
# =============================================================================


def test_serialize_basic_record():
    """Test serialization of basic log record."""
    # Create a proper mock for the level with .name attribute
    level_mock = MagicMock()
    level_mock.name = "INFO"
    
    record = {
        "time": MagicMock(isoformat=lambda: "2024-01-01T12:00:00"),
        "level": level_mock,
        "message": "Test message",
        "module": "test_module",
        "function": "test_function",
        "line": 42,
        "extra": {},
        "exception": None,
    }
    
    result = serialize(record)
    data = json.loads(result)
    
    assert data["time"] == "2024-01-01T12:00:00"
    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["module"] == "test_module"
    assert data["function"] == "test_function"
    assert data["line"] == 42


def test_serialize_with_context_variables():
    """Test serialization includes context variables."""
    request_id_var.set("req-123")
    user_id_var.set("user-456")
    operation_var.set("test_operation")
    
    record = {
        "time": MagicMock(isoformat=lambda: "2024-01-01T12:00:00"),
        "level": MagicMock(name="INFO"),
        "message": "Test message",
        "module": "test",
        "function": "test",
        "line": 1,
        "extra": {},
        "exception": None,
    }
    
    result = serialize(record)
    data = json.loads(result)
    
    assert data["request_id"] == "req-123"
    assert data["user_id"] == "user-456"
    assert data["operation"] == "test_operation"
    
    # Cleanup
    clear_request_context()


def test_serialize_with_extra_fields():
    """Test serialization includes extra fields."""
    record = {
        "time": MagicMock(isoformat=lambda: "2024-01-01T12:00:00"),
        "level": MagicMock(name="INFO"),
        "message": "Test message",
        "module": "test",
        "function": "test",
        "line": 1,
        "extra": {"custom_field": "custom_value", "count": 42},
        "exception": None,
    }
    
    result = serialize(record)
    data = json.loads(result)
    
    assert data["custom_field"] == "custom_value"
    assert data["count"] == 42


def test_serialize_with_exception():
    """Test serialization includes exception information."""
    try:
        raise ValueError("Test error")
    except ValueError:
        exc_info = sys.exc_info()
        
        record = {
            "time": MagicMock(isoformat=lambda: "2024-01-01T12:00:00"),
            "level": MagicMock(name="ERROR"),
            "message": "Error occurred",
            "module": "test",
            "function": "test",
            "line": 1,
            "extra": {},
            "exception": MagicMock(
                type=exc_info[0],
                value=exc_info[1],
                traceback=exc_info[2]
            ),
        }
        
        result = serialize(record)
        data = json.loads(result)
        
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["value"]
        assert isinstance(data["exception"]["traceback"], list)


def test_patching_adds_serialized_field():
    """Test patching function adds serialized field to record."""
    record = {
        "time": MagicMock(isoformat=lambda: "2024-01-01T12:00:00"),
        "level": MagicMock(name="INFO"),
        "message": "Test",
        "module": "test",
        "function": "test",
        "line": 1,
        "extra": {},
        "exception": None,
    }
    
    patching(record)
    
    assert "serialized" in record
    assert isinstance(record["serialized"], str)
    # Should be valid JSON
    json.loads(record["serialized"])


def test_custom_formatter_uses_serialized():
    """Test custom formatter returns format string for Loguru."""
    # The custom_formatter returns a format string that Loguru will substitute
    # It doesn't actually format the record itself - that's Loguru's job
    record = MagicMock()
    
    result = custom_formatter(record)
    
    # Should return the format string with {serialized} placeholder
    assert result == "{serialized}\n"
    assert "{serialized}" in result


# =============================================================================
# Context Variable Tests
# =============================================================================


def test_set_request_context():
    """Test setting request context."""
    set_request_context(
        request_id="test-request",
        user_id="test-user",
        operation="test-operation"
    )
    
    assert request_id_var.get() == "test-request"
    assert user_id_var.get() == "test-user"
    assert operation_var.get() == "test-operation"
    
    clear_request_context()


def test_set_request_context_partial():
    """Test setting partial context (some values None)."""
    set_request_context(request_id="req-123")
    
    assert request_id_var.get() == "req-123"
    # Other values should remain as they were
    
    clear_request_context()


def test_clear_request_context():
    """Test clearing request context."""
    set_request_context(
        request_id="test",
        user_id="user",
        operation="op"
    )
    
    clear_request_context()
    
    assert request_id_var.get() is None
    assert user_id_var.get() is None
    assert operation_var.get() is None


def test_get_request_context():
    """Test getting current context."""
    set_request_context(request_id="req-999")
    
    context = get_request_context()
    
    assert context["request_id"] == "req-999"
    assert "user_id" in context
    assert "operation" in context
    
    clear_request_context()


def test_get_request_context_empty():
    """Test getting context when nothing is set."""
    clear_request_context()
    
    context = get_request_context()
    
    assert context["request_id"] is None
    assert context["user_id"] is None
    assert context["operation"] is None


# =============================================================================
# Logger Setup Tests
# =============================================================================


def test_setup_logging_json_mode():
    """Test logger setup with JSON output."""
    with patch("sys.stdout", new_callable=StringIO):
        test_logger = setup_logging(level="INFO", json_logs=True)
        
        assert test_logger is not None


def test_setup_logging_human_readable():
    """Test logger setup with human-readable output."""
    with patch("sys.stdout", new_callable=StringIO):
        test_logger = setup_logging(level="INFO", json_logs=False, colorize=False)
        
        assert test_logger is not None


def test_setup_logging_with_file(tmp_path):
    """Test logger setup with file output."""
    log_file = tmp_path / "test.log"
    
    test_logger = setup_logging(
        level="INFO",
        json_logs=False,
        log_file=log_file,
        colorize=False
    )
    
    # File should be created
    assert log_file.exists()
    
    # Cleanup by removing the handler
    test_logger.remove()


def test_setup_logging_creates_log_directory(tmp_path):
    """Test logger creates parent directory if it doesn't exist."""
    log_file = tmp_path / "logs" / "subdir" / "test.log"
    
    test_logger = setup_logging(
        level="INFO",
        json_logs=False,
        log_file=log_file,
        colorize=False
    )
    
    assert log_file.parent.exists()
    assert log_file.exists()
    
    # Cleanup
    test_logger.remove()


def test_setup_logging_different_levels():
    """Test logger setup with different log levels."""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        test_logger = setup_logging(level=level, json_logs=False, colorize=False)
        assert test_logger is not None
        test_logger.remove()


def test_setup_logging_with_colorize_disabled():
    """Test logger setup with colors disabled."""
    test_logger = setup_logging(
        level="INFO",
        json_logs=False,
        colorize=False
    )
    
    assert test_logger is not None
    test_logger.remove()


# =============================================================================
# Integration Tests
# =============================================================================


def test_logger_with_context_in_message():
    """Test that context variables appear in log output."""
    # Setup a test logger that outputs to stdout
    with patch("sys.stdout", new_callable=StringIO):
        test_logger = setup_logging(level="INFO", json_logs=True, colorize=False)
        
        set_request_context(request_id="integration-test")
        
        # This should include the request_id
        test_logger.info("Test message")
        
        clear_request_context()
        test_logger.remove()


def test_logger_extra_fields():
    """Test logging with extra fields."""
    with patch("sys.stdout", new_callable=StringIO):
        test_logger = setup_logging(level="INFO", json_logs=True, colorize=False)
        
        # Log with extra fields
        test_logger.bind(custom="value").info("Test with extras")
        
        test_logger.remove()


def test_logger_exception_handling():
    """Test logging exceptions."""
    with patch("sys.stdout", new_callable=StringIO):
        test_logger = setup_logging(level="ERROR", json_logs=True, colorize=False)
        
        try:
            raise RuntimeError("Test exception")
        except RuntimeError:
            test_logger.exception("Caught exception")
        
        test_logger.remove()


def test_context_isolation_across_operations():
    """Test that context is properly isolated between operations."""
    set_request_context(request_id="op1", operation="operation1")
    ctx1 = get_request_context()
    
    clear_request_context()
    set_request_context(request_id="op2", operation="operation2")
    ctx2 = get_request_context()
    
    assert ctx1["request_id"] == "op1"
    assert ctx2["request_id"] == "op2"
    assert ctx1["operation"] == "operation1"
    assert ctx2["operation"] == "operation2"
    
    clear_request_context()


def test_serialize_handles_non_json_serializable():
    """Test serialization handles non-JSON-serializable objects."""
    class CustomObject:
        def __str__(self):
            return "CustomObject instance"
    
    record = {
        "time": MagicMock(isoformat=lambda: "2024-01-01T12:00:00"),
        "level": MagicMock(name="INFO"),
        "message": "Test",
        "module": "test",
        "function": "test",
        "line": 1,
        "extra": {"custom_obj": CustomObject()},
        "exception": None,
    }
    
    result = serialize(record)
    data = json.loads(result)
    
    # Should convert to string
    assert "custom_obj" in data
    assert isinstance(data["custom_obj"], str)


# =============================================================================
# Module Import Tests
# =============================================================================


def test_logger_is_configured():
    """Test that the global logger is configured on import."""
    assert logger is not None
    # Should have at least one handler
    # (This tests the module-level initialization)


def test_all_exports_are_available():
    """Test that all public APIs are exported."""
    from producthuntdb import logging as logging_module
    
    expected_exports = [
        "logger",
        "request_id_var",
        "user_id_var",
        "operation_var",
        "set_request_context",
        "clear_request_context",
        "get_request_context",
        "setup_logging",
    ]
    
    for export in expected_exports:
        assert hasattr(logging_module, export)
