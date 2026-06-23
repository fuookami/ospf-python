"""Number types for algebraic operations.

Provides RealNumber abstraction and concrete numeric types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar


class RealNumber(ABC):
    """Abstract base for real numbers.

    抽象实数基类，供 framework 泛型约束使用。
    """

    @abstractmethod
    def __add__(self, other: RealNumber) -> RealNumber:
        """Add two numbers."""
        ...

    @abstractmethod
    def __sub__(self, other: RealNumber) -> RealNumber:
        """Subtract two numbers."""
        ...

    @abstractmethod
    def __mul__(self, other: RealNumber) -> RealNumber:
        """Multiply two numbers."""
        ...

    @abstractmethod
    def __truediv__(self, other: RealNumber) -> RealNumber:
        """Divide two numbers."""
        ...

    @abstractmethod
    def __neg__(self) -> RealNumber:
        """Negate number."""
        ...

    @abstractmethod
    def __abs__(self) -> RealNumber:
        """Absolute value."""
        ...

    @abstractmethod
    def __lt__(self, other: RealNumber) -> bool:
        """Less than comparison."""
        ...

    @abstractmethod
    def __le__(self, other: RealNumber) -> bool:
        """Less than or equal comparison."""
        ...

    @abstractmethod
    def __gt__(self, other: RealNumber) -> bool:
        """Greater than comparison."""
        ...

    @abstractmethod
    def __ge__(self, other: RealNumber) -> bool:
        """Greater than or equal comparison."""
        ...

    @abstractmethod
    def to_float(self) -> float:
        """Convert to float."""
        ...


# TypeVar bound to RealNumber for generic constraints
V = TypeVar("V", bound=RealNumber)


class Float64(RealNumber):
    """Float64 implementation of RealNumber.

    Float64 实数实现。
    """

    __slots__ = ("_value",)

    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def value(self) -> float:
        """Get the float value."""
        return self._value

    def __add__(self, other: RealNumber) -> Float64:
        """Add two numbers."""
        return Float64(self._value + other.to_float())

    def __sub__(self, other: RealNumber) -> Float64:
        """Subtract two numbers."""
        return Float64(self._value - other.to_float())

    def __mul__(self, other: RealNumber) -> Float64:
        """Multiply two numbers."""
        return Float64(self._value * other.to_float())

    def __truediv__(self, other: RealNumber) -> Float64:
        """Divide two numbers."""
        return Float64(self._value / other.to_float())

    def __neg__(self) -> Float64:
        """Negate number."""
        return Float64(-self._value)

    def __abs__(self) -> Float64:
        """Absolute value."""
        return Float64(abs(self._value))

    def __lt__(self, other: RealNumber) -> bool:
        """Less than comparison."""
        return self._value < other.to_float()

    def __le__(self, other: RealNumber) -> bool:
        """Less than or equal comparison."""
        return self._value <= other.to_float()

    def __gt__(self, other: RealNumber) -> bool:
        """Greater than comparison."""
        return self._value > other.to_float()

    def __ge__(self, other: RealNumber) -> bool:
        """Greater than or equal comparison."""
        return self._value >= other.to_float()

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if isinstance(other, RealNumber):
            return self._value == other.to_float()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash."""
        return hash(self._value)

    def __repr__(self) -> str:
        """Repr."""
        return f"Float64({self._value})"

    def to_float(self) -> float:
        """Convert to float."""
        return self._value


class Int64(RealNumber):
    """Int64 implementation of RealNumber.

    Int64 实数实现。
    """

    __slots__ = ("_value",)

    def __init__(self, value: int) -> None:
        self._value = value

    @property
    def value(self) -> int:
        """Get the int value."""
        return self._value

    def __add__(self, other: RealNumber) -> RealNumber:
        """Add two numbers."""
        if isinstance(other, Int64):
            return Int64(self._value + other._value)
        return Float64(self._value + other.to_float())

    def __sub__(self, other: RealNumber) -> RealNumber:
        """Subtract two numbers."""
        if isinstance(other, Int64):
            return Int64(self._value - other._value)
        return Float64(self._value - other.to_float())

    def __mul__(self, other: RealNumber) -> RealNumber:
        """Multiply two numbers."""
        if isinstance(other, Int64):
            return Int64(self._value * other._value)
        return Float64(self._value * other.to_float())

    def __truediv__(self, other: RealNumber) -> Float64:
        """Divide two numbers."""
        return Float64(self._value / other.to_float())

    def __neg__(self) -> Int64:
        """Negate number."""
        return Int64(-self._value)

    def __abs__(self) -> Int64:
        """Absolute value."""
        return Int64(abs(self._value))

    def __lt__(self, other: RealNumber) -> bool:
        """Less than comparison."""
        return self._value < other.to_float()

    def __le__(self, other: RealNumber) -> bool:
        """Less than or equal comparison."""
        return self._value <= other.to_float()

    def __gt__(self, other: RealNumber) -> bool:
        """Greater than comparison."""
        return self._value > other.to_float()

    def __ge__(self, other: RealNumber) -> bool:
        """Greater than or equal comparison."""
        return self._value >= other.to_float()

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if isinstance(other, Int64):
            return self._value == other._value
        if isinstance(other, RealNumber):
            return self._value == other.to_float()
        return NotImplemented

    def __hash__(self) -> int:
        """Hash."""
        return hash(self._value)

    def __repr__(self) -> str:
        """Repr."""
        return f"Int64({self._value})"

    def to_float(self) -> float:
        """Convert to float."""
        return float(self._value)
