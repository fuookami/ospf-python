"""组合数学：组合。

Combinatorics: Combinations.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def combinations(items: Sequence[T], k: int) -> list[list[T]]:
    """生成所有 k-组合（无序、不重复选取 k 个元素）。

    Generate all k-combinations (unordered, without replacement).

    Args:
        items: 候选元素序列。/ Candidate item sequence.
        k: 选取个数。/ Number of items to select.

    Returns:
        所有 k-组合列表。/ List of all k-combinations.
    """
    if k < 0 or k > len(items):
        return []

    result: list[list[T]] = []

    def _backtrack(
        start: int,
        current: list[T],
    ) -> None:
        if len(current) == k:
            result.append(current[:])
            return
        for i in range(start, len(items)):
            current.append(items[i])
            _backtrack(i + 1, current)
            current.pop()

    _backtrack(0, [])
    return result
