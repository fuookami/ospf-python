"""最小值/最大值工具。

Minimum / maximum utilities.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def min_of(items: Iterable[T]) -> T:
    """返回可迭代对象中的最小值。

    Return the minimum value from an iterable.

    Args:
        items: 可迭代对象。/ Iterable of items.

    Returns:
        最小值。/ Minimum value.
    """
    return min(items)  # type: ignore[type-var]


def max_of(items: Iterable[T]) -> T:
    """返回可迭代对象中的最大值。

    Return the maximum value from an iterable.

    Args:
        items: 可迭代对象。/ Iterable of items.

    Returns:
        最大值。/ Maximum value.
    """
    return max(items)  # type: ignore[type-var]


def min_max_of(
    items: Iterable[T],
) -> tuple[T, T]:
    """返回可迭代对象中的最小值和最大值。

    Return the minimum and maximum from an iterable.

    Args:
        items: 可迭代对象。/ Iterable of items.

    Returns:
        (最小值, 最大值) 元组。/
        (minimum, maximum) tuple.
    """
    collected = list(items)
    return (min(collected), max(collected))  # type: ignore[type-var]
