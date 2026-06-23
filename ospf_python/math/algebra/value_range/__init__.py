"""Value range types for algebraic operations.

Provides TypedValueRange and ClosedTypedValueRange for range constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.algebra.number import RealNumber

V = TypeVar("V", bound=RealNumber)


@dataclass(frozen=True, slots=True)
class TypedValueRange(Generic[V]):
    """Typed value range with lower and upper bounds.

    类型化值范围，包含上下界。
    """

    lower: V | None
    upper: V | None

    def contains(self, value: V) -> bool:
        """Check if value is in range.

        Args:
            value: Value to check.

        Returns:
            True if value is in range.
        """
        return not (
            (self.lower is not None and value < self.lower)
            or (self.upper is not None and value > self.upper)
        )

    def is_bounded(self) -> bool:
        """Check if range is bounded on both sides."""
        return self.lower is not None and self.upper is not None

    def is_lower_bounded(self) -> bool:
        """Check if range has lower bound."""
        return self.lower is not None

    def is_upper_bounded(self) -> bool:
        """Check if range has upper bound."""
        return self.upper is not None

    def __repr__(self) -> str:
        """String representation."""
        lower_str = str(self.lower) if self.lower is not None else "-inf"
        upper_str = str(self.upper) if self.upper is not None else "+inf"
        return f"TypedValueRange({lower_str}, {upper_str})"


@dataclass(frozen=True, slots=True)
class ClosedTypedValueRange(TypedValueRange[V]):
    """Closed typed value range (inclusive bounds).

    闭合类型化值范围（包含边界）。
    """

    def contains(self, value: V) -> bool:
        """Check if value is in closed range.

        Args:
            value: Value to check.

        Returns:
            True if value is in range (inclusive).
        """
        return not (
            (self.lower is not None and value < self.lower)
            or (self.upper is not None and value > self.upper)
        )

    def __repr__(self) -> str:
        """String representation."""
        lower_str = str(self.lower) if self.lower is not None else "-inf"
        upper_str = str(self.upper) if self.upper is not None else "+inf"
        return f"ClosedTypedValueRange[{lower_str}, {upper_str}]"


def create_range(
    lower: V | None = None,
    upper: V | None = None,
) -> TypedValueRange[V]:
    """Create a typed value range.

    Args:
        lower: Lower bound (None for unbounded).
        upper: Upper bound (None for unbounded).

    Returns:
        TypedValueRange instance.
    """
    return TypedValueRange(lower=lower, upper=upper)


def create_closed_range(
    lower: V | None = None,
    upper: V | None = None,
) -> ClosedTypedValueRange[V]:
    """Create a closed typed value range.

    Args:
        lower: Lower bound (None for unbounded).
        upper: Upper bound (None for unbounded).

    Returns:
        ClosedTypedValueRange instance.
    """
    return ClosedTypedValueRange(lower=lower, upper=upper)
