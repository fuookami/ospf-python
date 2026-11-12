"""浮点数类型。

Floating-point number type.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Self

from ospf_python import _native
from ospf_python.utils.functional.ord import Order


@dataclass(frozen=True)
class Floating:
    """浮点数，基于 Python float 的不可变封装。

    Immutable wrapper around Python float.

    Attributes:
        value: 底层浮点值。/ Underlying float value.
    """

    value: float

    @property
    def zero(self) -> Self:
        """零值。/ Zero value."""
        return self.__class__(0.0)

    @property
    def one(self) -> Self:
        """单位值。/ One value."""
        return self.__class__(1.0)

    @property
    def two(self) -> Self:
        """二值。/ Two value."""
        return self.__class__(2.0)

    @property
    def three(self) -> Self:
        """三值。/ Three value."""
        return self.__class__(3.0)

    @property
    def five(self) -> Self:
        """五值。/ Five value."""
        return self.__class__(5.0)

    @property
    def ten(self) -> Self:
        """十值。/ Ten value."""
        return self.__class__(10.0)

    @property
    def half(self) -> Self:
        """半值 (0.5)。/ Half value (0.5)."""
        return self.__class__(0.5)

    @property
    def min_value(self) -> Self:
        """最小值。/ Minimum value."""
        return self.__class__(-math.inf)

    @property
    def max_value(self) -> Self:
        """最大值。/ Maximum value."""
        return self.__class__(math.inf)

    @property
    def positive_inf(self) -> Self:
        """正无穷。/ Positive infinity."""
        return self.__class__(math.inf)

    @property
    def negative_inf(self) -> Self:
        """负无穷。/ Negative infinity."""
        return self.__class__(-math.inf)

    @property
    def nan(self) -> Self:
        """非数值。/ Not a Number."""
        return self.__class__(math.nan)

    def copy(self) -> Self:
        """浅复制。/ Shallow copy."""
        return self.__class__(self.value)

    def __add__(self, other: Self) -> Self:
        """加法。/ Addition."""
        return _floating.binary(owner=self, other=other, operation="add")

    def __mul__(self, other: Self) -> Self:
        """乘法。/ Multiplication."""
        return _floating.binary(owner=self, other=other, operation="multiply")

    def __neg__(self) -> Self:
        """取反。/ Negation."""
        return _floating.negated(self)

    def __sub__(self, other: Self) -> Self:
        """减法。/ Subtraction."""
        return _floating.binary(owner=self, other=other, operation="subtract")

    def __truediv__(self, other: Self) -> Self:
        """除法。/ Division."""
        if _floating.relation(left=other.value, right=0.0, operation="eq"):
            return self.__class__(0.0)
        return _floating.binary(owner=self, other=other, operation="divide")

    def __eq__(self, other: object) -> bool:
        """相等比较。/ Equality comparison."""
        if not isinstance(other, Floating):
            return NotImplemented
        return _floating.relation(left=self.value, right=other.value, operation="eq")

    def __ne__(self, other: object) -> bool:
        """不等比较。/ Inequality comparison."""
        if not isinstance(other, Floating):
            return NotImplemented
        return _floating.relation(left=self.value, right=other.value, operation="ne")

    def __lt__(self, other: Self) -> bool:
        """小于比较。/ Less-than comparison."""
        return _floating.relation(left=self.value, right=other.value, operation="lt")

    def __le__(self, other: Self) -> bool:
        """小于等于。/ Less-or-equal."""
        return _floating.relation(left=self.value, right=other.value, operation="le")

    def __gt__(self, other: Self) -> bool:
        """大于比较。/ Greater-than comparison."""
        return _floating.relation(left=self.value, right=other.value, operation="gt")

    def __ge__(self, other: Self) -> bool:
        """大于等于。/ Greater-or-equal."""
        return _floating.relation(left=self.value, right=other.value, operation="ge")

    def __hash__(self) -> int:
        """哈希值。/ Hash value."""
        return hash(self.value)

    def __repr__(self) -> str:
        """字符串表示。/ String representation."""
        return f"Floating({self.value})"

    def cmp(self, other: Self) -> Order:
        """全序比较。/ Total comparison."""
        if _floating.relation(left=self.value, right=other.value, operation="lt"):
            return Order.LT
        if _floating.relation(left=self.value, right=other.value, operation="gt"):
            return Order.GT
        return Order.EQ

    def partial_cmp(self, other: Self) -> Order | None:
        """部分比较。/ Partial comparison."""
        return self.cmp(other)


_floating = _native._public_floating
