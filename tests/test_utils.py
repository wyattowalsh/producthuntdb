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


class TestUtilsAdditionalCoverage:
    """Additional comprehensive tests for 90%+ coverage."""

    def test_utc_now_returns_datetime(self):
        """Test utc_now returns a datetime object."""
        result = utc_now()
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc

    def test_utc_now_iso_ends_with_z(self):
        """Test utc_now_iso returns ISO string with Z suffix."""
        result = utc_now_iso()
        assert isinstance(result, str)
        assert result.endswith('Z')
        assert 'T' in result

    def test_format_iso_with_none_input(self):
        """Test format_iso returns None for None input."""
        assert format_iso(None) is None

    def test_format_iso_with_datetime_object(self):
        """Test format_iso with datetime object."""
        dt = datetime(2024, 6, 15, 14, 30, 45, tzinfo=timezone.utc)
        result = format_iso(dt)
        assert result == "2024-06-15T14:30:45Z"

    def test_redact_token_very_short(self):
        """Test redact_token with very short token."""
        assert redact_token("abc") == "***"

    def test_redact_token_exact_12_chars(self):
        """Test redact_token with exactly 12 characters."""
        token = "123456789012"
        result = redact_token(token)
        assert result == "***"

    def test_redact_token_13_chars(self):
        """Test redact_token with 13 characters."""
        token = "1234567890123"
        result = redact_token(token)
        assert result.startswith("12345678")
        assert result.endswith("0123")

    def test_redact_token_long_token(self):
        """Test redact_token with long token."""
        token = "a" * 50
        result = redact_token(token)
        assert len(result) == 12 + 3  # 8 + ... + 4

    def test_redact_token_with_empty_string(self):
        """Test redact_token with empty string."""
        assert redact_token("") == "None"

    def test_ensure_list_preserves_list(self):
        """Test ensure_list preserves existing list."""
        original = [1, 2, 3]
        result = ensure_list(original)
        assert result == original
        assert result is original  # Same object

    def test_ensure_list_wraps_int(self):
        """Test ensure_list wraps integer."""
        assert ensure_list(42) == [42]

    def test_ensure_list_wraps_string(self):
        """Test ensure_list wraps string."""
        assert ensure_list("test") == ["test"]

    def test_ensure_list_wraps_dict(self):
        """Test ensure_list wraps dictionary."""
        data = {"key": "value"}
        result = ensure_list(data)
        assert result == [data]

    def test_chunk_list_single_item(self):
        """Test chunking single item."""
        result = chunk_list([1], 5)
        assert result == [[1]]

    def test_chunk_list_large_chunk_size(self):
        """Test chunk_list with chunk size larger than list."""
        result = chunk_list([1, 2], 100)
        assert len(result) == 1
        assert result[0] == [1, 2]

    def test_safe_get_first_level(self):
        """Test safe_get with single level."""
        data = {"key": "value"}
        assert safe_get(data, "key") == "value"

    def test_safe_get_deep_nesting(self):
        """Test safe_get with deep nesting."""
        data = {"a": {"b": {"c": {"d": 123}}}}
        assert safe_get(data, "a", "b", "c", "d") == 123

    def test_safe_get_with_none_value(self):
        """Test safe_get when intermediate value is None."""
        data = {"a": None}
        assert safe_get(data, "a", "b", default=999) == 999

    def test_safe_get_no_keys(self):
        """Test safe_get with no keys."""
        data = {"key": "value"}
        result = safe_get(data)
        assert result == data

    def test_normalize_id_zero(self):
        """Test normalize_id with zero."""
        assert normalize_id(0) == "0"

    def test_normalize_id_negative(self):
        """Test normalize_id with negative number."""
        assert normalize_id(-123) == "-123"

    def test_parse_datetime_with_different_timezone(self):
        """Test parse_datetime converts different timezone to UTC."""
        # EST is UTC-5
        result = parse_datetime("2024-01-15T10:00:00-05:00")
        assert result is not None
        assert result.tzinfo == timezone.utc
        # 10:00 EST = 15:00 UTC
        assert result.hour == 15

    def test_parse_datetime_with_positive_offset(self):
        """Test parse_datetime with positive timezone offset."""
        # Tokyo is UTC+9
        result = parse_datetime("2024-01-15T10:00:00+09:00")
        assert result is not None
        assert result.tzinfo == timezone.utc
        # 10:00 JST = 01:00 UTC
        assert result.hour == 1

    def test_build_graphql_query_empty_fields(self):
        """Test build_graphql_query with empty fields list."""
        from producthuntdb.utils import build_graphql_query

        query = build_graphql_query("posts", [])
        assert "posts" in query

    def test_build_graphql_query_single_variable(self):
        """Test build_graphql_query with single variable."""
        from producthuntdb.utils import build_graphql_query

        query = build_graphql_query("posts", ["id"], {"$id": "ID!"})
        assert "$id: ID!" in query

    def test_chunk_list_uneven_split(self):
        """Test chunk_list with uneven split."""
        result = chunk_list([1, 2, 3, 4, 5], 2)
        assert len(result) == 3
        assert result[0] == [1, 2]
        assert result[1] == [3, 4]
        assert result[2] == [5]

    def test_safe_get_with_int_value(self):
        """Test safe_get when intermediate value is not a dict."""
        data = {"a": 123}
        assert safe_get(data, "a", "b", default=999) == 999

    def test_safe_get_list_access(self):
        """Test safe_get handles list incorrectly (not supported)."""
        data = {"items": [1, 2, 3]}
        # This will fail because lists don't have .get() method
        # safe_get only works with dicts, not lists
        assert safe_get(data, "items", default=999) == [1, 2, 3]

    def test_normalize_id_large_number(self):
        """Test normalize_id with large number."""
        assert normalize_id(999999999) == "999999999"

    def test_parse_datetime_microseconds(self):
        """Test parse_datetime preserves microseconds."""
        result = parse_datetime("2024-01-15T10:30:45.123456Z")
        assert result is not None
        assert result.microsecond == 123456

    def test_parse_datetime_milliseconds(self):
        """Test parse_datetime handles milliseconds."""
        result = parse_datetime("2024-01-15T10:30:45.123Z")
        assert result is not None
        # .123 seconds = 123000 microseconds
        assert result.microsecond == 123000

    def test_redact_token_unicode(self):
        """Test redact_token with unicode characters."""
        token = "abc123你好世界xyz"
        result = redact_token(token)
        assert "***" in result or result.endswith("xyz")

    def test_ensure_list_none_input(self):
        """Test ensure_list with None input."""
        assert ensure_list(None) == []

    def test_ensure_list_tuple(self):
        """Test ensure_list with tuple input."""
        result = ensure_list((1, 2, 3))
        assert result == [(1, 2, 3)]

    def test_build_graphql_query_mutation(self):
        """Test build_graphql_query for mutation."""
        from producthuntdb.utils import build_graphql_query

        query = build_graphql_query("createPost", ["id", "status"])
        assert "createPost" in query
        assert "id" in query
        assert "status" in query
