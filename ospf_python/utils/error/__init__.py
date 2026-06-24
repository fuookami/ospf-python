"""错误处理模块 / Error handling module.

提供错误码枚举和错误类型层次结构。
Provides error code enums and error type hierarchies.
"""

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import (
    ApplicationException,
    Err,
    Error,
    ExErr,
    LazyErr,
    LazyExErr,
)

__all__ = [
    "ErrorCode",
    "Error",
    "Err",
    "LazyErr",
    "ExErr",
    "LazyExErr",
    "ApplicationException",
]
