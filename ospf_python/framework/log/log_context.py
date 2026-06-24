"""日志上下文 / Log context.

封装日志记录的上下文信息。
Encapsulates context information for log records.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LogContext:
    """日志上下文 / Log context.

    携带日志记录的附加上下文，如模块名、请求标识等。
    Carries附加 context for log records, such as module
    name, request identifier, etc.

    Attributes:
        module: 模块名称 / The module name.
        request_id: 请求标识 / The request identifier.
        user_id: 用户标识 / The user identifier.
    """

    module: str
    request_id: str = ""
    user_id: str = ""
