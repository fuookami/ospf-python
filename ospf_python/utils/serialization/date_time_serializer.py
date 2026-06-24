"""日期时间序列化 / DateTime serialization.

提供 datetime 对象的 ISO 格式序列化和反序列化。
Provides ISO format serialization and deserialization for
datetime objects.
"""

from __future__ import annotations

from datetime import UTC, datetime


def serialize_datetime(dt: datetime) -> str:
    """将 datetime 序列化为 ISO 格式字符串 / Serialize a datetime
    to an ISO format string.

    Args:
        dt: 待序列化的 datetime 对象 / The datetime to serialize.

    Returns:
        ISO 格式的字符串 / The ISO format string.
    """
    return dt.isoformat()


def deserialize_datetime(s: str) -> datetime:
    """从 ISO 格式字符串反序列化为 datetime / Deserialize an ISO
    format string to a datetime.

    Args:
        s: ISO 格式的字符串 / The ISO format string.

    Returns:
        反序列化的 datetime 对象 / The deserialized datetime.
    """
    return datetime.fromisoformat(s)


def serialize_timestamp(dt: datetime) -> float:
    """将 datetime 序列化为 Unix 时间戳 / Serialize a datetime to a
    Unix timestamp.

    Args:
        dt: 待序列化的 datetime 对象 / The datetime to serialize.

    Returns:
        Unix 时间戳（秒） / The Unix timestamp in seconds.
    """
    return dt.timestamp()


def deserialize_timestamp(ts: float) -> datetime:
    """从 Unix 时间戳反序列化为 datetime / Deserialize a Unix
    timestamp to a datetime.

    Args:
        ts: Unix 时间戳（秒） / The Unix timestamp in seconds.

    Returns:
        UTC 时区的 datetime 对象 / The datetime in UTC timezone.
    """
    return datetime.fromtimestamp(ts, tz=UTC)
