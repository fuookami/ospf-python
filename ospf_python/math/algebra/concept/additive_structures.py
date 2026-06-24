"""加法结构协议 / Additive structure protocols.

PlusSemiGroup / PlusGroup，加法半群与加法群的简化版本。
PlusSemiGroup / PlusGroup, simplified additive semigroup and group.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class PlusSemiGroup(Protocol):
    """加法半群协议 / Additive semigroup protocol.

    仅包含加法运算的半群。
    A semigroup with only addition.
    """

    def __add__(self: Self, other: Self) -> Self:
        """加法 / Addition."""

    def __radd__(self: Self, other: Self) -> Self:
        """右加法 / Right addition."""


@runtime_checkable
class PlusGroup(PlusSemiGroup, Protocol):
    """加法群协议 / Additive group protocol.

    在加法半群基础上增加取反和减法。
    Extends additive semigroup with negation and subtraction.
    """

    def __neg__(self: Self) -> Self:
        """取反 / Negation."""

    def __sub__(self: Self, other: Self) -> Self:
        """减法 / Subtraction."""

    def __rsub__(self: Self, other: Self) -> Self:
        """右减法 / Right subtraction."""
