"""Utility functions for ProductHuntDB.

This module provides common helper functions for datetime handling,
GraphQL query construction, and data transformation.
"""

from datetime import UTC, datetime
from typing import Any

from dateutil import parser as dateutil_parser  # type: ignore[import-untyped]


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse ISO8601 timestamp string into timezone-aware UTC datetime.

    Args:
        value: ISO8601 timestamp string, datetime object, or None

    Returns:
        Parsed timezone-aware datetime in UTC, or None if input is None

    Raises:
        ValueError: If timestamp format is invalid

    Example:
        >>> dt = parse_datetime("2024-01-15T10:30:00Z")
        >>> dt.tzinfo
        datetime.timezone.utc
    """
    if value is None:
        return None

    # If already a datetime object, just ensure it's in UTC
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    dt = dateutil_parser.isoparse(value)

    # Ensure timezone-aware in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    return dt.astimezone(UTC)


def utc_now() -> datetime:
    """Get current UTC timestamp as timezone-aware datetime.

    Returns:
        Current datetime in UTC with timezone information

    Example:
        >>> now = utc_now()
        >>> now.tzinfo == datetime.UTC
        True
    """
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """Get current UTC timestamp as ISO8601 string with 'Z' suffix.

    Returns:
        ISO8601 formatted timestamp string ending with 'Z'

    Example:
        >>> timestamp = utc_now_iso()
        >>> timestamp.endswith('Z')
        True
    """
    return utc_now().isoformat().replace("+00:00", "Z")


def format_iso(dt: datetime | None) -> str | None:
    """Format datetime as ISO8601 string with 'Z' suffix.

    Args:
        dt: Datetime object or None

    Returns:
        ISO8601 formatted string or None if input is None

    Example:
        >>> from datetime import UTC
        >>> dt = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        >>> format_iso(dt)
        '2024-01-15T10:30:00Z'
    """
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def redact_token(token: str | None) -> str:
    """Redact sensitive tokens for safe logging.

    Args:
        token: Token string to redact

    Returns:
        Redacted token showing only first 8 and last 4 characters

    Example:
        >>> redact_token("abcdefghijklmnop")
        'abcdefgh...mnop'
        >>> redact_token("short")
        '***'
        >>> redact_token(None)
        'None'
    """
    if not token:
        return "None"
    return f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***"


def build_graphql_query(
    operation: str,
    fields: list[str],
    variables: dict[str, str] | None = None,
) -> str:
    """Build GraphQL query string from components.

    Args:
        operation: GraphQL operation (e.g., "query", "mutation")
        fields: List of field strings to include in query
        variables: Optional variable definitions

    Returns:
        Formatted GraphQL query string

    Example:
        >>> query = build_graphql_query("query", ["id", "name", "description"], {"$id": "ID!"})
    """
    var_def = ""
    if variables:
        vars_str = ", ".join(f"{k}: {v}" for k, v in variables.items())
        var_def = f"({vars_str})"

    fields_str = "\n  ".join(fields)
    return f"{operation}{var_def} {{\n  {fields_str}\n}}"


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split list into chunks of specified size.

    Args:
        items: List to split
        chunk_size: Maximum size of each chunk

    Returns:
        List of lists, each containing at most chunk_size items

    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_get(data: Any, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dictionary structure.

    Args:
        data: Dictionary to navigate
        *keys: Sequence of keys to traverse
        default: Default value if key path doesn't exist

    Returns:
        Value at key path or default if not found

    Example:
        >>> data = {"a": {"b": {"c": 123}}}
        >>> safe_get(data, "a", "b", "c")
        123
        >>> safe_get(data, "a", "x", "y", default=0)
        0
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return default
        else:
            return default
    return data


def normalize_id(id_value: str | int | None) -> str | None:
    """Normalize ID value to string format.

    Args:
        id_value: ID as string, integer, or None

    Returns:
        Normalized ID string or None

    Example:
        >>> normalize_id(123)
        '123'
        >>> normalize_id("abc")
        'abc'
        >>> normalize_id(None)
        None
    """
    if id_value is None:
        return None
    return str(id_value)


def ensure_list(value: Any) -> list[Any]:
    """Ensure value is a list, wrapping if necessary.

    Args:
        value: Value to ensure as list

    Returns:
        List containing value(s)

    Example:
        >>> ensure_list([1, 2, 3])
        [1, 2, 3]
        >>> ensure_list(42)
        [42]
        >>> ensure_list(None)
        []
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
