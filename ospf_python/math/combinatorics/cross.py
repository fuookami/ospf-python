"""组合数学：笛卡尔积。

Combinatorics: Cartesian product.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def cross(*iterables: Iterable[T]) -> list[tuple[T, ...]]:
    """计算多个可迭代对象的笛卡尔积。

    Compute the Cartesian product of multiple iterables.

    Args:
        *iterables: 可迭代对象序列。/ Iterable sequence.

    Returns:
        笛卡尔积元组列表。/ List of Cartesian product tuples.
    """
    pools = [list(pool) for pool in iterables]
    if not pools:
        return [()]

    result: list[tuple[T, ...]] = [()]

    for pool in pools:
        result = [prefix + (item,) for prefix in result for item in pool]

    return result
