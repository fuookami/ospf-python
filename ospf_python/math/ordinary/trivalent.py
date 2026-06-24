"""三值逻辑类型。

Trivalent (three-valued) logic type.
"""

from __future__ import annotations

import enum


class Trivalent(enum.Enum):
    """三值逻辑：真、假、未知。

    Three-valued logic: True, False, Unknown.

    Attributes:
        TRUE: 真。/ True.
        FALSE: 假。/ False.
        UNKNOWN: 未知。/ Unknown.
    """

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"

    def __and__(self, other: Trivalent) -> Trivalent:
        """逻辑与。/ Logical AND.

        Args:
            other: 另一个三值。/ Other trivalent.

        Returns:
            与运算结果。/ AND result.
        """
        if self == Trivalent.FALSE or other == Trivalent.FALSE:
            return Trivalent.FALSE
        if self == Trivalent.TRUE and other == Trivalent.TRUE:
            return Trivalent.TRUE
        return Trivalent.UNKNOWN

    def __or__(self, other: Trivalent) -> Trivalent:
        """逻辑或。/ Logical OR.

        Args:
            other: 另一个三值。/ Other trivalent.

        Returns:
            或运算结果。/ OR result.
        """
        if self == Trivalent.TRUE or other == Trivalent.TRUE:
            return Trivalent.TRUE
        if self == Trivalent.FALSE and other == Trivalent.FALSE:
            return Trivalent.FALSE
        return Trivalent.UNKNOWN

    def __invert__(self) -> Trivalent:
        """逻辑非。/ Logical NOT.

        Returns:
            非运算结果。/ NOT result.
        """
        if self == Trivalent.TRUE:
            return Trivalent.FALSE
        if self == Trivalent.FALSE:
            return Trivalent.TRUE
        return Trivalent.UNKNOWN

    @property
    def is_true(self) -> bool:
        """是否为真。/ Whether true."""
        return self == Trivalent.TRUE

    @property
    def is_false(self) -> bool:
        """是否为假。/ Whether false."""
        return self == Trivalent.FALSE

    @property
    def is_unknown(self) -> bool:
        """是否未知。/ Whether unknown."""
        return self == Trivalent.UNKNOWN

    def to_bool(self) -> bool | None:
        """转换为 Python bool 或 None。

        Convert to Python bool or None.

        Returns:
            True/False/None。
        """
        if self == Trivalent.TRUE:
            return True
        if self == Trivalent.FALSE:
            return False
        return None
