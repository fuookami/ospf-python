"""常量提供者协议 / Constant provider protocols.

提供常用数值常量的协议集合。
A collection of protocols providing common numeric constants.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class HasZero(Protocol):
    """提供零值 / Provides zero value."""

    @property
    def zero(self: Self) -> Self:
        """零 / Zero."""


@runtime_checkable
class HasOne(Protocol):
    """提供单位值 / Provides one value."""

    @property
    def one(self: Self) -> Self:
        """一 / One."""


@runtime_checkable
class HasTwo(Protocol):
    """提供二值 / Provides two value."""

    @property
    def two(self: Self) -> Self:
        """二 / Two."""


@runtime_checkable
class HasThree(Protocol):
    """提供三值 / Provides three value."""

    @property
    def three(self: Self) -> Self:
        """三 / Three."""


@runtime_checkable
class HasFive(Protocol):
    """提供五值 / Provides five value."""

    @property
    def five(self: Self) -> Self:
        """五 / Five."""


@runtime_checkable
class HasTen(Protocol):
    """提供十值 / Provides ten value."""

    @property
    def ten(self: Self) -> Self:
        """十 / Ten."""


@runtime_checkable
class HasHalf(Protocol):
    """提供半值 / Provides half value."""

    @property
    def half(self: Self) -> Self:
        """半 / Half (0.5)."""


@runtime_checkable
class HasBounds(Protocol):
    """提供边界值 / Provides boundary values."""

    @property
    def min_value(self: Self) -> Self:
        """最小值 / Minimum value."""

    @property
    def max_value(self: Self) -> Self:
        """最大值 / Maximum value."""


@runtime_checkable
class HasInfinity(Protocol):
    """提供无穷值 / Provides infinity values."""

    @property
    def positive_inf(self: Self) -> Self:
        """正无穷 / Positive infinity."""

    @property
    def negative_inf(self: Self) -> Self:
        """负无穷 / Negative infinity."""


@runtime_checkable
class HasNaN(Protocol):
    """提供非数值 / Provides NaN value."""

    @property
    def nan(self: Self) -> Self:
        """非数值 / Not a Number."""
