"""组合数学：排列。

Combinatorics: Permutations.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def permutations(items: Sequence[T], k: int) -> list[list[T]]:
    """生成所有 k-排列（有序、不重复选取 k 个元素）。

    Generate all k-permutations (ordered, without replacement).

    Args:
        items: 候选元素序列。/ Candidate item sequence.
        k: 选取个数。/ Number of items to select.

    Returns:
        所有 k-排列列表。/ List of all k-permutations.
    """
    if k < 0 or k > len(items):
        return []

    result: list[list[T]] = []
    used = [False] * len(items)

    def _backtrack(current: list[T]) -> None:
        if len(current) == k:
            result.append(current[:])
            return
        for i in range(len(items)):
            if not used[i]:
                used[i] = True
                current.append(items[i])
                _backtrack(current)
                current.pop()
                used[i] = False

    _backtrack([])
    return result
