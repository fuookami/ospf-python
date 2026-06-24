"""范围创建运算符。

Range creation operator.
"""

from __future__ import annotations


def range_to(start: int, end: int) -> range:
    """创建从 start 到 end（不含）的整数范围。

    Create an integer range from start to end (exclusive).

    Args:
        start: 起始值（含）。/ Start value (inclusive).
        end: 结束值（不含）。/ End value (exclusive).

    Returns:
        整数范围。/ Integer range.
    """
    return range(start, end)
