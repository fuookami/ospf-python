"""日志模块 / Logging module.

提供日志上下文和日志记录功能。
Provides log context and log record functionality.
"""

from ospf_python.framework.log.log_context import LogContext
from ospf_python.framework.log.log_record import LogRecord

__all__ = [
    "LogContext",
    "LogRecord",
]
