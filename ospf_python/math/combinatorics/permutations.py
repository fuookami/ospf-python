"""组合数学：排列。

Combinatorics: Permutations.
"""

from collections.abc import Sequence
from typing import TypeVar

from ospf_python._binding.result import BindingResult
from ospf_python._binding.selection import select

T = TypeVar("T")


def permutations(items: Sequence[T], k: int) -> BindingResult[list[list[T]]]:
    """生成所有 k-排列（有序、不重复选取 k 个元素）。

    Generate all k-permutations (ordered, without replacement).

    Args:
        items: 候选元素序列。/ Candidate item sequence.
        k: 选取个数。/ Number of items to select.

    Returns:
        现有 Result，成功包含所有 k-排列。 / Existing Result containing all k-permutations.
    """
    return select(items=items, k=k, permutations=True)
