"""有理数类型。

Rational number type.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Self

from ospf_python.utils.functional.ord import Order


@dataclass(frozen=True)
class Rational:
    """有理数，以分子/分母的不可变分数表示。

    Immutable rational number as numerator/denominator fraction.

    Attributes:
        numerator: 分子。/ Numerator.
        denominator: 分母。/ Denominator.
    """

    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        """约分并确保分母为正。/ Reduce and ensure positive denominator."""
        if self.denominator == 0:
            object.__setattr__(self, "denominator", 1)
            object.__setattr__(self, "numerator", 0)
            return
        gcd = math.gcd(self.numerator, self.denominator)
        num = self.numerator // gcd
        den = self.denominator // gcd
        if den < 0:
            num = -num
            den = -den
        object.__setattr__(self, "numerator", num)
        object.__setattr__(self, "denominator", den)

    @property
    def zero(self) -> Self:
        """零值。/ Zero value."""
        return self.__class__(0)

    @property
    def one(self) -> Self:
        """单位值。/ One value."""
        return self.__class__(1)

    def copy(self) -> Self:
        """浅复制。/ Shallow copy."""
        return self.__class__(self.numerator, self.denominator)

    def __add__(self, other: Self) -> Self:
        """加法。/ Addition."""
        num = self.numerator * other.denominator + other.numerator * self.denominator
        den = self.denominator * other.denominator
        return self.__class__(num, den)

    def __mul__(self, other: Self) -> Self:
        """乘法。/ Multiplication."""
        return self.__class__(
            self.numerator * other.numerator,
            self.denominator * other.denominator,
        )

    def __neg__(self) -> Self:
        """取反。/ Negation."""
        return self.__class__(-self.numerator, self.denominator)

    def __sub__(self, other: Self) -> Self:
        """减法。/ Subtraction."""
        return self + (-other)

    def __truediv__(self, other: Self) -> Self:
        """除法。/ Division."""
        if other.numerator == 0:
            return self.__class__(0)
        return self.__class__(
            self.numerator * other.denominator,
            self.denominator * other.numerator,
        )

    def __eq__(self, other: object) -> bool:
        """相等比较。/ Equality comparison."""
        if not isinstance(other, Rational):
            return NotImplemented
        return (
            self.numerator == other.numerator and self.denominator == other.denominator
        )

    def __ne__(self, other: object) -> bool:
        """不等比较。/ Inequality comparison."""
        if not isinstance(other, Rational):
            return NotImplemented
        return not self.__eq__(other)

    def __lt__(self, other: Self) -> bool:
        """小于比较。/ Less-than comparison."""
        return self.numerator * other.denominator < other.numerator * self.denominator

    def __le__(self, other: Self) -> bool:
        """小于等于。/ Less-or-equal."""
        return not other.__lt__(self)

    def __gt__(self, other: Self) -> bool:
        """大于比较。/ Greater-than comparison."""
        return other.__lt__(self)

    def __ge__(self, other: Self) -> bool:
        """大于等于。/ Greater-or-equal."""
        return not self.__lt__(other)

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash((self.numerator, self.denominator))

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        if self.denominator == 1:
            return f"Rational({self.numerator})"
        return f"Rational({self.numerator}/{self.denominator})"

    def cmp(self, other: Self) -> Order:
        """全序比较。/ Total comparison."""
        if self < other:
            return Order.LT
        if self > other:
            return Order.GT
        return Order.EQ

    def partial_cmp(self, other: Self) -> Order | None:
        """部分比较。/ Partial comparison."""
        return self.cmp(other)

    @property
    def float_value(self) -> float:
        """转换为浮点值。/ Convert to float value."""
        return self.numerator / self.denominator
