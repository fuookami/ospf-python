"""解析结果。

Parse result wrapper for parser outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParseResult:
    """解析结果，封装成功/失败状态、解析值和错误信息。

    Parse result wrapping success/failure state,
    parsed value, and error message.

    Attributes:
        success: 是否解析成功。/ Whether parsing succeeded.
        value: 解析得到的值。/ Parsed value.
        error: 错误信息（成功时为空字符串）。/
            Error message (empty on success).
    """

    success: bool
    value: Any
    error: str

    @staticmethod
    def ok(value: Any) -> ParseResult:
        """创建成功的解析结果。

        Create a successful parse result.

        Args:
            value: 解析得到的值。/ Parsed value.

        Returns:
            成功的解析结果。/ Successful parse result.
        """
        return ParseResult(success=True, value=value, error="")

    @staticmethod
    def fail(error: str) -> ParseResult:
        """创建失败的解析结果。

        Create a failed parse result.

        Args:
            error: 错误信息。/ Error message.

        Returns:
            失败的解析结果。/ Failed parse result.
        """
        return ParseResult(success=False, value=None, error=error)
