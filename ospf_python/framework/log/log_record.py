"""日志记录 / Log record.

定义框架层的日志记录结构。
Defines the log record structure for the framework layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LogRecord:
    """日志记录 / Log record.

    包含日志级别、消息和时间戳的不可变记录。
    An immutable record containing log level, message,
    and timestamp.

    Attributes:
        level: 日志级别 / The log level (e.g. INFO, WARNING).
        message: 日志消息 / The log message.
        timestamp: 记录时间戳 / The record timestamp.
    """

    level: str
    message: str
    timestamp: datetime
