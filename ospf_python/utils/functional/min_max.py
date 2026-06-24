"""数值边界裁剪工具。

Min / max clamping helpers.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def clamp(value: T, *, min_val: T, max_val: T) -> T:
    """将值裁剪到 [min_val, max_val] 区间。

    Clamps a value into the [min_val, max_val] range.

    Args:
        value: 待裁剪的值。/ Value to clamp.
        min_val: 下界。/ Lower bound.
        max_val: 上界。/ Upper bound.

    Returns:
        裁剪后的值。/ Clamped value.
    """
    return max(min_val, min(value, max_val))  # type: ignore[call-overload,no-any-return]


def ensure_min(value: T, *, min_val: T) -> T:
    """确保值不小于下界。

    Ensures a value is not less than the minimum.

    Args:
        value: 待检查的值。/ Value to check.
        min_val: 下界。/ Minimum bound.

    Returns:
        不小于 min_val 的值。/ Value clamped to min_val.
    """
    return max(value, min_val)  # type: ignore[call-overload,no-any-return]


def ensure_max(value: T, *, max_val: T) -> T:
    """确保值不大于上界。

    Ensures a value is not greater than the maximum.

    Args:
        value: 待检查的值。/ Value to check.
        max_val: 上界。/ Maximum bound.

    Returns:
        不大于 max_val 的值。/ Value clamped to max_val.
    """
    return min(value, max_val)  # type: ignore[call-overload,no-any-return]
