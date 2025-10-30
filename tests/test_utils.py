"""Unit tests for utility functions."""

from datetime import datetime, timezone

import pytest

from producthuntdb.utils import (
    chunk_list,
    ensure_list,
    format_iso,
    normalize_id,
    parse_datetime,
    redact_token,
    safe_get,
    utc_now,
    utc_now_iso,
)


class TestDatetimeFunctions:
    """Tests for datetime utility functions."""

    def test_parse_datetime_valid_iso(self):
        """Test parsing valid ISO8601 timestamp."""
        result = parse_datetime("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo == timezone.utc

    def test_parse_datetime_with_offset(self):
        """Test parsing ISO8601 with timezone offset."""
        result = parse_datetime("2024-01-15T10:30:00+05:00")
        assert result is not None
        assert result.tzinfo is not None
        # Should be converted to UTC
        assert result.tzinfo == timezone.utc

    def test_parse_datetime_none(self):
        """Test parsing None returns None."""
        assert parse_datetime(None) is None

    def test_parse_datetime_invalid(self):
        """Test parsing invalid timestamp raises error."""
        with pytest.raises(ValueError):
            parse_datetime("not-a-date")

    def test_utc_now(self):
        """Test getting current UTC time."""
        now = utc_now()
        assert now.tzinfo == timezone.utc
        assert isinstance(now, datetime)

    def test_utc_now_iso(self):
        """Test getting current UTC time as ISO string."""
        iso_str = utc_now_iso()
        assert isinstance(iso_str, str)
        assert iso_str.endswith("Z")
        assert "T" in iso_str

    def test_format_iso_valid(self):
        """Test formatting datetime to ISO string."""
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result = format_iso(dt)
        assert result == "2024-01-15T10:30:00Z"

    def test_format_iso_none(self):
        """Test formatting None returns None."""
        assert format_iso(None) is None


class TestTokenRedaction:
    """Tests for token redaction."""

    def test_redact_long_token(self):
        """Test redacting long token."""
        token = "abcdefghijklmnopqrstuvwxyz"
        result = redact_token(token)
        assert result == "abcdefgh...wxyz"
        assert len(result) < len(token)

    def test_redact_short_token(self):
        """Test redacting short token."""
        token = "short"
        result = redact_token(token)
        assert result == "***"

    def test_redact_none(self):
        """Test redacting None."""
        assert redact_token(None) == "None"

    def test_redact_empty_string(self):
        """Test redacting empty string."""
        assert redact_token("") == "None"


class TestListUtilities:
    """Tests for list manipulation utilities."""

    def test_chunk_list_even(self):
        """Test chunking list evenly."""
        items = [1, 2, 3, 4, 5, 6]
        result = chunk_list(items, 2)
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_chunk_list_uneven(self):
        """Test chunking list unevenly."""
        items = [1, 2, 3, 4, 5]
        result = chunk_list(items, 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunk_list_single_chunk(self):
        """Test chunking into single chunk."""
        items = [1, 2, 3]
        result = chunk_list(items, 10)
        assert result == [[1, 2, 3]]

    def test_chunk_list_empty(self):
        """Test chunking empty list."""
        result = chunk_list([], 2)
        assert result == []

    def test_ensure_list_already_list(self):
        """Test ensure_list with existing list."""
        result = ensure_list([1, 2, 3])
        assert result == [1, 2, 3]

    def test_ensure_list_single_value(self):
        """Test ensure_list with single value."""
        result = ensure_list(42)
        assert result == [42]

    def test_ensure_list_none(self):
        """Test ensure_list with None."""
        result = ensure_list(None)
        assert result == []


class TestDictionaryUtilities:
    """Tests for dictionary manipulation utilities."""

    def test_safe_get_valid_path(self):
        """Test safe_get with valid path."""
        data = {"a": {"b": {"c": 123}}}
        result = safe_get(data, "a", "b", "c")
        assert result == 123

    def test_safe_get_missing_key(self):
        """Test safe_get with missing key."""
        data = {"a": {"b": 123}}
        result = safe_get(data, "a", "x", "y", default=0)
        assert result == 0

    def test_safe_get_none_value(self):
        """Test safe_get with None value in path."""
        data = {"a": None}
        result = safe_get(data, "a", "b", default="default")
        assert result == "default"

    def test_safe_get_non_dict(self):
        """Test safe_get with non-dict value."""
        data = {"a": "string"}
        result = safe_get(data, "a", "b", default=None)
        assert result is None

    def test_safe_get_empty_dict(self):
        """Test safe_get with empty dict."""
        result = safe_get({}, "a", default="empty")
        assert result == "empty"


class TestIdNormalization:
    """Tests for ID normalization."""

    def test_normalize_id_string(self):
        """Test normalizing string ID."""
        assert normalize_id("abc123") == "abc123"

    def test_normalize_id_integer(self):
        """Test normalizing integer ID."""
        assert normalize_id(123) == "123"

    def test_normalize_id_none(self):
        """Test normalizing None."""
        assert normalize_id(None) is None


# =============================================================================
# Property-based tests with Hypothesis
# =============================================================================


@pytest.mark.parametrize(
    "timestamp",
    [
        "2024-01-01T00:00:00Z",
        "2024-12-31T23:59:59Z",
        "2024-06-15T12:30:45.123456Z",
        "2024-01-15T10:30:00+00:00",
        "2024-01-15T10:30:00-05:00",
    ],
)
def test_parse_datetime_various_formats(timestamp):
    """Test parsing various ISO8601 formats."""
    result = parse_datetime(timestamp)
    assert result is not None
    assert result.tzinfo == timezone.utc


@pytest.mark.parametrize(
    "token,expected_length",
    [
        ("a" * 20, 15),  # abcdefgh...mnop (8 + 3 + 4 = 15)
        ("b" * 50, 15),
        ("c" * 100, 15),
    ],
)
def test_redact_token_length(token, expected_length):
    """Test redacted token length is consistent."""
    result = redact_token(token)
    assert len(result) == expected_length


@pytest.mark.parametrize(
    "items,chunk_size",
    [
        ([1, 2, 3, 4], 1),
        ([1, 2, 3, 4], 2),
        ([1, 2, 3, 4], 3),
        ([1, 2, 3, 4], 4),
        ([1, 2, 3, 4], 5),
    ],
)
def test_chunk_list_parametrized(items, chunk_size):
    """Test chunking with various sizes."""
    result = chunk_list(items, chunk_size)
    # Flatten and check all items are preserved
    flattened = [item for chunk in result for item in chunk]
    assert flattened == items
    # Check chunk sizes
    for chunk in result[:-1]:  # All but last
        assert len(chunk) == chunk_size
    # Last chunk should be <= chunk_size
    if result:
        assert len(result[-1]) <= chunk_size


class TestUtilsCoverage:
    """Additional tests for full coverage."""

    def test_normalize_id(self):
        """Test normalize_id function."""
        from producthuntdb.utils import normalize_id

        assert normalize_id(123) == "123"
        assert normalize_id("abc") == "abc"
        assert normalize_id(None) is None

    def test_build_graphql_query_basic(self):
        """Test building a basic GraphQL query."""
        from producthuntdb.utils import build_graphql_query

        query = build_graphql_query("posts", ["id", "name"])
        assert "posts" in query
        assert "id" in query
        assert "name" in query

    def test_build_graphql_query_simple(self):
        """Test build_graphql_query with simple fields."""
        from producthuntdb.utils import build_graphql_query

        query = build_graphql_query("users", ["username"])
        assert "users" in query
        assert "username" in query

    def test_parse_datetime_with_naive_datetime_object(self):
        """Test parse_datetime with a naive datetime object."""
        from datetime import datetime
        from producthuntdb.utils import parse_datetime, UTC

        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        result = parse_datetime(naive_dt)
        
        assert result is not None
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_with_aware_datetime_object(self):
        """Test parse_datetime with an aware datetime object."""
        from datetime import datetime, timezone
        from producthuntdb.utils import parse_datetime, UTC

        aware_dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = parse_datetime(aware_dt)
        
        assert result is not None
        assert result.tzinfo == UTC
        assert result.year == 2024

    def test_parse_datetime_string_without_timezone(self):
        """Test parse_datetime with ISO string without timezone info."""
        from producthuntdb.utils import parse_datetime, UTC

        # ISO string without timezone - should be treated as UTC
        result = parse_datetime("2024-01-15T10:30:00")
        
        assert result is not None
        assert result.tzinfo == UTC
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_build_graphql_query_with_variables(self):
        """Test build_graphql_query with variables."""
        from producthuntdb.utils import build_graphql_query

        query = build_graphql_query(
            "posts",
            ["id", "name"],
            {"$first": "Int!", "$after": "String"}
        )
        assert "posts" in query
        assert "$first: Int!" in query
        assert "$after: String" in query
        assert "id" in query
        assert "name" in query
