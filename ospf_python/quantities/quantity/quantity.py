"""物理量。/ Physical quantity.

值 + 单位，不同单位物理量不得直接加减。
Value + unit; different-unit quantities cannot
be directly added or subtracted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ospf_python.quantities.unit.physical_unit import (
        PhysicalUnit,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class Quantity(Generic[T]):
    """物理量，包含数值和单位。

    Physical quantity with numeric value and unit.

    不同单位的物理量不能直接加减，
    必须先转换单位。
    Quantities with different units cannot be
    directly added or subtracted; conversion
    is required first.

    Attributes:
        value: 数值。/ Numeric value.
        unit: 物理单位。/ Physical unit.
    """

    value: T
    unit: PhysicalUnit

    def to(self, target_unit: PhysicalUnit) -> Quantity[T]:
        """转换单位。/ Convert to target unit.

        通过 SI 中间单位进行转换。
        Converts via SI intermediate unit.

        Args:
            target_unit: 目标单位。/ Target unit.

        Returns:
            转换后的物理量。/ Converted quantity.
        """
        si_val = self.unit.to_si(float(self.value))  # type: ignore[arg-type]
        new_val = target_unit.from_si(si_val)
        return Quantity(
            value=new_val,  # type: ignore[arg-type]
            unit=target_unit,
        )

    def __add__(self, other: Quantity[T]) -> Quantity[T]:
        """同单位相加。/ Add same-unit quantities.

        Args:
            other: 另一个物理量。/ Another quantity.

        Returns:
            相加结果。/ Addition result.

        Raises:
            TypeError: 单位不匹配时。
                When units mismatch.
        """
        if self.unit.symbol != other.unit.symbol:
            raise TypeError(
                f"Cannot add quantities with different "
                f"units: {self.unit.symbol} and "
                f"{other.unit.symbol}"
            )
        return Quantity(
            value=self.value + other.value,  # type: ignore[operator]
            unit=self.unit,
        )

    def __sub__(self, other: Quantity[T]) -> Quantity[T]:
        """同单位相减。/ Subtract same-unit quantities.

        Args:
            other: 另一个物理量。/ Another quantity.

        Returns:
            相减结果。/ Subtraction result.

        Raises:
            TypeError: 单位不匹配时。
                When units mismatch.
        """
        if self.unit.symbol != other.unit.symbol:
            raise TypeError(
                f"Cannot subtract quantities with "
                f"different units: {self.unit.symbol} "
                f"and {other.unit.symbol}"
            )
        return Quantity(
            value=self.value - other.value,  # type: ignore[operator]
            unit=self.unit,
        )

    def __mul__(self, scalar: float) -> Quantity[T]:
        """标量乘法。/ Scalar multiplication.

        Args:
            scalar: 标量因子。/ Scalar factor.

        Returns:
            缩放后的物理量。/ Scaled quantity.
        """
        return Quantity(
            value=self.value * scalar,  # type: ignore[operator, arg-type]
            unit=self.unit,
        )

    def __truediv__(self, scalar: float) -> Quantity[T]:
        """标量除法。/ Scalar division.

        Args:
            scalar: 标量除数。/ Scalar divisor.

        Returns:
            缩放后的物理量。/ Scaled quantity.
        """
        return Quantity(
            value=self.value / scalar,  # type: ignore[operator, arg-type]
            unit=self.unit,
        )

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        return f"{self.value} {self.unit.symbol}"
