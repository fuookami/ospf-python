"""持久化日志记录 / Persistence log record.

定义持久化层的日志记录结构。
Defines the log record structure for the persistence layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PersistenceLogRecord:
    """持久化日志记录 / Persistence log record.

    记录持久化操作的日志信息，包括操作类型、
    目标实体和执行时间。
    Records persistence operation log information,
    including operation type, target entity, and
    execution time.

    Attributes:
        operation: 操作类型 / The operation type.
        entity_name: 实体名称 / The entity name.
        timestamp: 记录时间戳 / The record timestamp.
        success: 是否成功 / Whether the operation succeeded.
    """

    operation: str
    entity_name: str
    timestamp: datetime
    success: bool = True
