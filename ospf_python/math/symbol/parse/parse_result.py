"""解析结果。

Parse result wrapper for parser outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ParseResult(Generic[T]):
    """解析结果，包含解析值和剩余输入。

    Parse result containing the parsed value and
    remaining unparsed input.

    Attributes:
        value: 解析得到的值。/ Parsed value.
        remaining: 剩余未解析的输入。/ Remaining input.
    """

    value: T
    remaining: str

    @staticmethod
    def of(value: T, remaining: str) -> ParseResult[T]:
        """创建解析结果。

        Create a parse result.

        Args:
            value: 解析得到的值。/ Parsed value.
            remaining: 剩余输入。/ Remaining input.

        Returns:
            解析结果。/ Parse result.
        """
        return ParseResult(value=value, remaining=remaining)

    @property
    def is_fully_consumed(self) -> bool:
        """输入是否已完全消费。/
        Whether input is fully consumed.
        """
        return self.remaining.strip() == ""
