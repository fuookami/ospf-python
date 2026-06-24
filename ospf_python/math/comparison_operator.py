"""比较运算符。

Comparison operators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Equal(Generic[T, U]):
    """相等比较。

    Equality comparison.

    Attributes:
        left: 左操作数。/ Left operand.
        right: 右操作数。/ Right operand.
    """

    left: T
    right: U


@dataclass(frozen=True)
class Unequal(Generic[T, U]):
    """不等比较。

    Inequality comparison.

    Attributes:
        left: 左操作数。/ Left operand.
        right: 右操作数。/ Right operand.
    """

    left: T
    right: U


@dataclass(frozen=True)
class Less(Generic[T, U]):
    """小于比较。

    Less-than comparison.

    Attributes:
        left: 左操作数。/ Left operand.
        right: 右操作数。/ Right operand.
    """

    left: T
    right: U


@dataclass(frozen=True)
class LessEqual(Generic[T, U]):
    """小于等于比较。

    Less-than-or-equal comparison.

    Attributes:
        left: 左操作数。/ Left operand.
        right: 右操作数。/ Right operand.
    """

    left: T
    right: U


@dataclass(frozen=True)
class Greater(Generic[T, U]):
    """大于比较。

    Greater-than comparison.

    Attributes:
        left: 左操作数。/ Left operand.
        right: 右操作数。/ Right operand.
    """

    left: T
    right: U


@dataclass(frozen=True)
class GreaterEqual(Generic[T, U]):
    """大于等于比较。

    Greater-than-or-equal comparison.

    Attributes:
        left: 左操作数。/ Left operand.
        right: 右操作数。/ Right operand.
    """

    left: T
    right: U


ComparisonOperator = Union[
    Equal[T, U],
    Unequal[T, U],
    Less[T, U],
    LessEqual[T, U],
    Greater[T, U],
    GreaterEqual[T, U],
]
"""比较运算符联合类型。

Comparison operator union type.
"""
