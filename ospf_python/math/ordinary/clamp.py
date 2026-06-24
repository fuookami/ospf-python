"""值域限制工具。

Clamp utility for constraining values to a range.
"""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T", int, float)


def clamp(
    value: T,
    *,
    min_val: T,
    max_val: T,
) -> T:
    """将值限制在指定范围内。

    Constrain a value to the given range.

    Args:
        value: 输入值。/ Input value.
        min_val: 下界。/ Lower bound.
        max_val: 上界。/ Upper bound.

    Returns:
        限制后的值。/ Clamped value.
    """
    return max(min_val, min(value, max_val))
