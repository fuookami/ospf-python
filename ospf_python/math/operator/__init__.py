"""Mathematical operators module.

Provides operator abstractions for mathematical operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ospf_python.math.algebra.number import RealNumber

V = TypeVar("V", bound=RealNumber)


class BinaryOperator(ABC, Generic[V]):
    """Binary operator interface.

    二元运算符接口。
    """

    @abstractmethod
    def apply(self, left: V, right: V) -> V:
        """Apply the operator.

        Args:
            left: Left operand.
            right: Right operand.

        Returns:
            Result of operation.
        """
        ...


class UnaryOperator(ABC, Generic[V]):
    """Unary operator interface.

    一元运算符接口。
    """

    @abstractmethod
    def apply(self, operand: V) -> V:
        """Apply the operator.

        Args:
            operand: Operand.

        Returns:
            Result of operation.
        """
        ...


class AddOperator(BinaryOperator[V]):
    """Addition operator.

    加法运算符。
    """

    def apply(self, left: V, right: V) -> V:
        """Add two values."""
        return left + right  # type: ignore[return-value]


class SubtractOperator(BinaryOperator[V]):
    """Subtraction operator.

    减法运算符。
    """

    def apply(self, left: V, right: V) -> V:
        """Subtract two values."""
        return left - right  # type: ignore[return-value]


class MultiplyOperator(BinaryOperator[V]):
    """Multiplication operator.

    乘法运算符。
    """

    def apply(self, left: V, right: V) -> V:
        """Multiply two values."""
        return left * right  # type: ignore[return-value]


class DivideOperator(BinaryOperator[V]):
    """Division operator.

    除法运算符。
    """

    def apply(self, left: V, right: V) -> V:
        """Divide two values."""
        return left / right  # type: ignore[return-value]


class NegateOperator(UnaryOperator[V]):
    """Negation operator.

    取反运算符。
    """

    def apply(self, operand: V) -> V:
        """Negate value."""
        return -operand  # type: ignore[return-value]


class AbsOperator(UnaryOperator[V]):
    """Absolute value operator.

    绝对值运算符。
    """

    def apply(self, operand: V) -> V:
        """Absolute value."""
        return abs(operand)  # type: ignore[return-value]
