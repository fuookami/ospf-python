"""乘法结构协议 / Multiplicative structure protocols.

MulSemiGroup / MulGroup，乘法半群与乘法群的简化版本。
MulSemiGroup / MulGroup, simplified multiplicative semigroup
and group.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class MulSemiGroup(Protocol):
    """乘法半群协议 / Multiplicative semigroup protocol.

    仅包含乘法运算的半群。
    A semigroup with only multiplication.
    """

    def __mul__(self: Self, other: Self) -> Self:
        """乘法 / Multiplication."""

    def __rmul__(self: Self, other: Self) -> Self:
        """右乘法 / Right multiplication."""


@runtime_checkable
class MulGroup(MulSemiGroup, Protocol):
    """乘法群协议 / Multiplicative group protocol.

    在乘法半群基础上增加除法和倒数。
    Extends multiplicative semigroup with division
    and reciprocal.
    """

    def __truediv__(self: Self, other: Self) -> Self:
        """除法 / Division."""

    def __rtruediv__(self: Self, other: Self) -> Self:
        """右除法 / Right division."""

    @property
    def reciprocal(self: Self) -> Self:
        """乘法逆元 / Multiplicative inverse."""
