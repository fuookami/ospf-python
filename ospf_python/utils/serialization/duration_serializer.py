"""时长序列化 / Duration serialization.

提供 timedelta 对象的序列化和反序列化。
Provides serialization and deserialization for timedelta
objects.
"""

from __future__ import annotations

from datetime import timedelta


def serialize_duration(td: timedelta) -> str:
    """将 timedelta 序列化为字符串 / Serialize a timedelta to a
    string.

    格式为 "DdHhMmS.sss"，省略零值部分。
    Format is "DdHhMmS.sss", omitting zero-valued parts.

    Args:
        td: 待序列化的 timedelta / The timedelta to serialize.

    Returns:
        时长的字符串表示 / The string representation of the duration.
    """
    total_seconds = td.total_seconds()
    if total_seconds == 0:
        return "0s"

    # 处理负值 / Handle negative values
    sign = "-" if total_seconds < 0 else ""
    remaining = abs(total_seconds)

    days = int(remaining // 86400)
    remaining %= 86400
    hours = int(remaining // 3600)
    remaining %= 3600
    minutes = int(remaining // 60)
    seconds = remaining % 60

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        # 整数时无小数点 / No decimal point for whole seconds
        if seconds == int(seconds):
            parts.append(f"{int(seconds)}s")
        else:
            parts.append(f"{seconds:.3f}s")

    return sign + "".join(parts) if parts else "0s"


def deserialize_duration(s: str) -> timedelta:
    """从字符串反序列化为 timedelta / Deserialize a string to a
    timedelta.

    支持 "DdHhMmS.sss" 格式，各部分可选。
    Supports "DdHhMmS.sss" format, all parts optional.

    Args:
        s: 时长的字符串表示 / The string representation.

    Returns:
        反序列化的 timedelta / The deserialized timedelta.
    """
    if not s or s == "0s":
        return timedelta(0)

    # 处理负值 / Handle negative values
    negative = s.startswith("-")
    if negative:
        s = s[1:]

    import re

    pattern = (
        r"(?:(\d+)d)?"
        r"(?:(\d+)h)?"
        r"(?:(\d+)m)?"
        r"(?:(\d+(?:\.\d+)?)s)?"
    )
    match = re.fullmatch(pattern, s)
    if not match or not match.group(0):
        return timedelta(0)

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = float(match.group(4) or 0)

    td = timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )
    return -td if negative else td
