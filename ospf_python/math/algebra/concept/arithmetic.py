"""算术协议 / Arithmetic protocol.

Arithmetic 组合了可复制、可比较与基本算术运算。
Arithmetic combines copyable, equality, and basic
arithmetic operations.
"""

from __future__ import annotations

from typing import Protocol, Self, runtime_checkable

from ospf_python.utils.concept.clone import Copyable
from ospf_python.utils.functional.eq import PartialEq


@runtime_checkable
class Arithmetic(Copyable, PartialEq, Protocol):
    """算术协议 / Arithmetic protocol.

    包含加法、乘法、取反、减法、除法运算。
    Includes addition, multiplication, negation,
    subtraction, and division.
    """

    def __add__(self: Self, other: Self) -> Self:
        """加法 / Addition."""

    def __mul__(self: Self, other: Self) -> Self:
        """乘法 / Multiplication."""

    def __neg__(self: Self) -> Self:
        """取反 / Negation."""

    def __sub__(self: Self, other: Self) -> Self:
        """减法 / Subtraction."""

    def __truediv__(self: Self, other: Self) -> Self:
        """除法 / Division."""
