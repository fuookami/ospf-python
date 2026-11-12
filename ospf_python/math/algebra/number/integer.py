"""有符号整数类型。

Signed integer type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ospf_python import _native
from ospf_python.utils.functional.ord import Order


@dataclass(frozen=True)
class Integer:
    """有符号整数，基于 Python int 的不可变封装。

    Immutable wrapper around Python int for signed integers.

    Attributes:
        value: 底层整数值。/ Underlying integer value.
    """

    value: int

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
        return self.__class__(self.value)

    def __add__(self, other: Self) -> Self:
        """加法。/ Addition."""
        return _integer.add(owner=self, other=other)

    def __mul__(self, other: Self) -> Self:
        """乘法。/ Multiplication."""
        return _integer.multiply(owner=self, other=other)

    def __neg__(self) -> Self:
        """取反。/ Negation."""
        return _integer.negate(self)

    def __sub__(self, other: Self) -> Self:
        """减法。/ Subtraction."""
        return _integer.subtract(owner=self, other=other)

    def __truediv__(self, other: Self) -> Self:
        """整数除法（向下取整）。/ Integer division (flooring)."""
        return _integer.divide(owner=self, other=other)

    def __eq__(self, other: object) -> bool:
        """相等比较。/ Equality comparison."""
        if not isinstance(other, Integer):
            return NotImplemented
        return _integer.equal(left=self.value, right=other.value)

    def __ne__(self, other: object) -> bool:
        """不等比较。/ Inequality comparison."""
        if not isinstance(other, Integer):
            return NotImplemented
        return _integer.not_equal(left=self.value, right=other.value)

    def __lt__(self, other: Self) -> bool:
        """小于比较。/ Less-than comparison."""
        return _integer.less(left=self.value, right=other.value)

    def __le__(self, other: Self) -> bool:
        """小于等于比较。/ Less-or-equal comparison."""
        return _integer.less_equal(left=self.value, right=other.value)

    def __gt__(self, other: Self) -> bool:
        """大于比较。/ Greater-than comparison."""
        return _integer.greater(left=self.value, right=other.value)

    def __ge__(self, other: Self) -> bool:
        """大于等于比较。/ Greater-or-equal comparison."""
        return _integer.greater_equal(left=self.value, right=other.value)

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash(self.value)

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Integer({self.value})"

    def cmp(self, other: Self) -> Order:
        """全序比较。/ Total comparison."""
        if _integer.less(left=self.value, right=other.value):
            return Order.LT
        if _integer.greater(left=self.value, right=other.value):
            return Order.GT
        return Order.EQ

    def partial_cmp(self, other: Self) -> Order | None:
        """部分比较。/ Partial comparison."""
        return self.cmp(other)


_integer = _native._public_integer.facade(reference=Integer.__add__, domain="integer")
