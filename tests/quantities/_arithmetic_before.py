"""仅测试的四则迁移前冻结参考，禁止生产导入。 / Test-only frozen arithmetic before migration; never imported by production."""

from __future__ import annotations

import operator
from types import FunctionType
from typing import Any

from ospf_python.quantities.quantity import quantity as quantity_module
from ospf_python.quantities.quantity.quantity import Quantity


def _legacy_add(self: Any, other: Any) -> Any:
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
        value=self.value + other.value,
        unit=self.unit,
    )


def _legacy_subtract(self: Any, other: Any) -> Any:
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
        value=self.value - other.value,
        unit=self.unit,
    )


def _legacy_multiply(self: Any, scalar: float) -> Any:
    """标量乘法。/ Scalar multiplication.

    Args:
        scalar: 标量因子。/ Scalar factor.

    Returns:
        缩放后的物理量。/ Scaled quantity.
    """
    return Quantity(
        value=self.value * scalar,
        unit=self.unit,
    )


def _legacy_divide(self: Any, scalar: float) -> Any:
    """标量除法。/ Scalar division.

    Args:
        scalar: 标量除数。/ Scalar divisor.

    Returns:
        缩放后的物理量。/ Scaled quantity.
    """
    return Quantity(
        value=self.value / scalar,
        unit=self.unit,
    )


_OPERATIONS = {
    operation: FunctionType(function.__code__, quantity_module.__dict__)
    for operation, function in (
        (operator.add, _legacy_add),
        (operator.sub, _legacy_subtract),
        (operator.mul, _legacy_multiply),
        (operator.truediv, _legacy_divide),
    )
}


def legacy_operation(*, operation: Any, owner: Any, other: Any) -> Any:
    """保留原断言的旧语义观测，不是默认路径。 / Preserve old assertions as before-observations, not default execution."""
    return _OPERATIONS[operation](owner, other)
