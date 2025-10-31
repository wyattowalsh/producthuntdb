"""Tests for API retry logic and rate limiting.

This module specifically tests:
- Exponential backoff retry logic with tenacity
- Rate limiting awareness and adaptive delays
- Transient vs permanent error handling
- HTTP error code classification

Coverage Target: api.py 34% → 70% (+59 lines)
Priority: High - Critical path for data ingestion
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from producthuntdb.api import AsyncGraphQLClient, TransientGraphQLError


# =============================================================================
# Retry Logic Tests
# =============================================================================


@pytest.mark.asyncio
async def test_retry_on_network_timeout():
    """Test retry logic triggers on network timeout."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock client that times out first 2 times, then succeeds
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"data": {"test": "success"}}

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.TimeoutException("Connection timeout")
        return mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        result = await client._post_with_retry("query", {})

        assert result == {"test": "success"}
        assert call_count == 3  # 2 failures + 1 success


@pytest.mark.asyncio
async def test_retry_on_network_error():
    """Test retry logic handles network connection errors."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock network error then success
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"data": {"test": "data"}}

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.NetworkError("Connection refused")
        return mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        result = await client._post_with_retry("query", {})

        assert result == {"test": "data"}
        assert call_count == 2


@pytest.mark.asyncio
async def test_retry_on_http_429_rate_limit():
    """Test retry logic handles HTTP 429 rate limit errors."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock 429 response then success
    rate_limit_response = MagicMock()
    rate_limit_response.status_code = 429
    rate_limit_response.headers = {
        "X-RateLimit-Reset": "2024-01-15T12:00:00Z",
    }

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.headers = {}
    success_response.json.return_value = {"data": {"test": "recovered"}}

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return rate_limit_response
        return success_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        result = await client._post_with_retry("query", {})

        assert result == {"test": "recovered"}
        assert call_count == 2


@pytest.mark.asyncio
async def test_retry_on_http_500_server_error():
    """Test retry logic handles HTTP 5xx server errors."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock 500 response then success
    server_error = MagicMock()
    server_error.status_code = 503
    server_error.headers = {}

    success_response = MagicMock()
    success_response.status_code = 200
    success_response.headers = {}
    success_response.json.return_value = {"data": {"test": "recovered"}}

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return server_error
        return success_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        result = await client._post_with_retry("query", {})

        assert result == {"test": "recovered"}
        assert call_count == 2


@pytest.mark.asyncio
async def test_retry_gives_up_after_max_attempts():
    """Test retry logic gives up after maximum attempts."""
    client = AsyncGraphQLClient(token="test_token")

    # Always timeout
    async def mock_post(*args, **kwargs):
        raise httpx.TimeoutException("Persistent timeout")

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with pytest.raises(httpx.TimeoutException):
            # This should eventually give up and raise the exception
            await client._post_with_retry("query", {})


@pytest.mark.asyncio
async def test_no_retry_on_permanent_errors():
    """Test permanent errors (HTTP 4xx except 429) don't trigger retry."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock 400 Bad Request (permanent error)
    error_response = MagicMock()
    error_response.status_code = 400
    error_response.headers = {}
    error_response.text = "Bad request"

    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return error_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            await client._do_http_post("query", {})

        assert "HTTP 400" in str(exc_info.value)
        # Should fail immediately without retry
        assert call_count == 1


# =============================================================================
# Rate Limiting Tests
# =============================================================================


@pytest.mark.asyncio
async def test_rate_limit_tracking():
    """Test rate limit headers are tracked correctly."""
    client = AsyncGraphQLClient(token="test_token")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "50",
        "X-RateLimit-Reset": "2024-01-15T12:00:00Z",
    }
    mock_response.json.return_value = {"data": {"test": "data"}}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        await client._do_http_post("query", {})

        assert client._rate_limit_limit == "100"
        assert client._rate_limit_remaining == "50"
        assert client._rate_limit_reset == "2024-01-15T12:00:00Z"


@pytest.mark.asyncio
async def test_rate_limit_remaining_property():
    """Test rate_limit_remaining property conversion."""
    client = AsyncGraphQLClient(token="test_token")

    # Initially None
    assert client.rate_limit_remaining is None

    # Set valid value
    client._rate_limit_remaining = "42"
    assert client.rate_limit_remaining == 42

    # Handle invalid value
    client._rate_limit_remaining = "invalid"
    assert client.rate_limit_remaining is None


@pytest.mark.asyncio
async def test_get_rate_limit_status():
    """Test get_rate_limit_status returns all tracking info."""
    client = AsyncGraphQLClient(token="test_token")

    client._rate_limit_limit = "100"
    client._rate_limit_remaining = "25"
    client._rate_limit_reset = "2024-01-15T12:00:00Z"

    status = client.get_rate_limit_status()

    assert status["limit"] == "100"
    assert status["remaining"] == "25"
    assert status["reset"] == "2024-01-15T12:00:00Z"


@pytest.mark.asyncio
async def test_adaptive_delay_when_rate_limit_low():
    """Test adaptive delay increases when rate limit is low."""
    client = AsyncGraphQLClient(token="test_token")

    # Set low rate limit
    client._rate_limit_remaining = "3"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"data": {"test": "data"}}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with patch("asyncio.sleep") as mock_sleep:
            await client._post_with_retry("query", {})

            # Should use 5 second delay for remaining < 5
            mock_sleep.assert_called()
            # The actual call might be 5.0 or similar
            sleep_call = mock_sleep.call_args[0][0]
            assert sleep_call >= 4.5  # Allow some variation


@pytest.mark.asyncio
async def test_adaptive_delay_when_rate_limit_moderate():
    """Test adaptive delay is moderate when rate limit is medium."""
    client = AsyncGraphQLClient(token="test_token")

    # Set moderate rate limit
    client._rate_limit_remaining = "15"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"data": {"test": "data"}}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with patch("asyncio.sleep") as mock_sleep:
            await client._post_with_retry("query", {})

            # Should use 3 second delay for 5 <= remaining < 20
            mock_sleep.assert_called()
            sleep_call = mock_sleep.call_args[0][0]
            assert 2.5 <= sleep_call <= 3.5


@pytest.mark.asyncio
async def test_adaptive_delay_when_rate_limit_high():
    """Test adaptive delay is minimal when rate limit is high."""
    client = AsyncGraphQLClient(token="test_token")

    # Set high rate limit
    client._rate_limit_remaining = "80"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"data": {"test": "data"}}

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with patch("asyncio.sleep") as mock_sleep:
            await client._post_with_retry("query", {})

            # Should use 2 second delay for remaining >= 20
            mock_sleep.assert_called()
            sleep_call = mock_sleep.call_args[0][0]
            assert 1.5 <= sleep_call <= 2.5


# =============================================================================
# Error Classification Tests
# =============================================================================


@pytest.mark.asyncio
async def test_transient_error_classification():
    """Test TransientGraphQLError is raised for retryable errors."""
    client = AsyncGraphQLClient(token="test_token")

    # Test timeout
    async def mock_timeout(*args, **kwargs):
        raise httpx.TimeoutException("timeout")

    mock_client = MagicMock()
    mock_client.post = mock_timeout

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with pytest.raises(TransientGraphQLError) as exc_info:
            await client._do_http_post("query", {})

        assert "timeout" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_permanent_error_classification():
    """Test RuntimeError is raised for non-retryable errors."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock 401 Unauthorized (permanent auth error)
    error_response = MagicMock()
    error_response.status_code = 401
    error_response.headers = {}
    error_response.text = "Unauthorized"

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=error_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            await client._do_http_post("query", {})

        assert "HTTP 401" in str(exc_info.value)


@pytest.mark.asyncio
async def test_graphql_errors_raise_runtime_error():
    """Test GraphQL errors in response raise RuntimeError."""
    client = AsyncGraphQLClient(token="test_token")

    error_response = MagicMock()
    error_response.status_code = 200
    error_response.headers = {}
    error_response.json.return_value = {
        "errors": [{"message": "Field 'invalid' doesn't exist"}]
    }

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=error_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            await client._do_http_post("query", {})

        assert "GraphQL errors" in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_json_raises_transient_error():
    """Test invalid JSON response raises TransientGraphQLError."""
    client = AsyncGraphQLClient(token="test_token")

    error_response = MagicMock()
    error_response.status_code = 200
    error_response.headers = {}
    error_response.json.side_effect = ValueError("Invalid JSON")

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=error_response)

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with pytest.raises(TransientGraphQLError) as exc_info:
            await client._do_http_post("query", {})

        assert "Invalid JSON" in str(exc_info.value)


# =============================================================================
# Concurrency Tests
# =============================================================================


@pytest.mark.asyncio
async def test_semaphore_limits_concurrency():
    """Test semaphore correctly limits concurrent requests."""
    client = AsyncGraphQLClient(token="test_token", max_concurrency=2)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"data": {"test": "data"}}

    active_requests = 0
    max_active = 0

    async def mock_post(*args, **kwargs):
        nonlocal active_requests, max_active
        active_requests += 1
        max_active = max(max_active, active_requests)
        await asyncio.sleep(0.1)  # Simulate work
        active_requests -= 1
        return mock_response

    mock_client = MagicMock()
    mock_client.post = mock_post

    with patch.object(client, "_ensure_client", return_value=mock_client):
        with patch("asyncio.sleep", new_callable=AsyncMock):  # Skip adaptive delay
            # Start 5 concurrent requests
            tasks = [client._post_with_retry("query", {}) for _ in range(5)]
            await asyncio.gather(*tasks)

            # Should never exceed max_concurrency=2
            assert max_active <= 2


# =============================================================================
# Context Manager Tests
# =============================================================================


@pytest.mark.asyncio
async def test_context_manager_ensures_cleanup():
    """Test async context manager properly initializes and cleans up."""
    client = AsyncGraphQLClient(token="test_token")

    assert client._client is None

    async with client:
        # Client should be initialized
        await client._ensure_client()
        assert client._client is not None

    # Client should be closed after context exit
    assert client._client is None


@pytest.mark.asyncio
async def test_context_manager_with_exception():
    """Test context manager cleans up even when exception occurs."""
    client = AsyncGraphQLClient(token="test_token")

    try:
        async with client:
            await client._ensure_client()
            assert client._client is not None
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Should still cleanup
    assert client._client is None


# =============================================================================
# HTTP/2 Configuration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_http2_enabled():
    """Test HTTP/2 is enabled in client configuration."""
    client = AsyncGraphQLClient(token="test_token")

    # This is tricky to test directly, but we can verify the intent
    # by checking that http2 parameter would be passed to httpx.AsyncClient
    with patch("httpx.AsyncClient") as mock_async_client:
        await client._ensure_client()

        # Check that AsyncClient was called with http2=True
        call_kwargs = mock_async_client.call_args[1]
        assert call_kwargs.get("http2") is True


@pytest.mark.asyncio
async def test_connection_pool_limits():
    """Test connection pool is configured correctly."""
    client = AsyncGraphQLClient(token="test_token")

    with patch("httpx.AsyncClient") as mock_async_client:
        await client._ensure_client()

        call_kwargs = mock_async_client.call_args[1]
        limits = call_kwargs.get("limits")

        # Verify default limits are set
        assert limits is not None
        assert limits.max_connections == 100
        assert limits.max_keepalive_connections == 20


@pytest.mark.asyncio
async def test_custom_timeout_configuration():
    """Test custom timeout can be provided."""
    custom_timeout = httpx.Timeout(timeout=60.0)
    client = AsyncGraphQLClient(token="test_token", timeout=custom_timeout)

    with patch("httpx.AsyncClient") as mock_async_client:
        await client._ensure_client()

        call_kwargs = mock_async_client.call_args[1]
        assert call_kwargs.get("timeout") == custom_timeout
