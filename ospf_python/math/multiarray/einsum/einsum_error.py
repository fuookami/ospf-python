"""爱因斯坦求和错误类型。

Einstein summation error types.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EinsumError:
    """爱因斯坦求和操作错误。

    Error for invalid einsum operations.

    Attributes:
        message: 错误信息。/ Error message.
    """

    message: str

    def __str__(self) -> str:
        """返回错误描述。/ Return error description."""
        return f"EinsumError: {self.message}"
