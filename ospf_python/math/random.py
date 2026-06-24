"""随机数工具。

Random utilities.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def random_int(
    min_val: int,
    max_val: int,
) -> int:
    """生成随机整数。

    Generate a random integer in [min_val, max_val].

    Args:
        min_val: 最小值（含）。/ Minimum (inclusive).
        max_val: 最大值（含）。/ Maximum (inclusive).

    Returns:
        随机整数。/ Random integer.
    """
    return random.randint(min_val, max_val)


def random_float(
    min_val: float,
    max_val: float,
) -> float:
    """生成随机浮点数。

    Generate a random float in [min_val, max_val).

    Args:
        min_val: 最小值（含）。/ Minimum (inclusive).
        max_val: 最大值（不含）。/ Maximum (exclusive).

    Returns:
        随机浮点数。/ Random float.
    """
    return random.uniform(min_val, max_val)


def random_choice(items: Sequence[T]) -> T:
    """从序列中随机选择一个元素。

    Choose a random element from a sequence.

    Args:
        items: 待选择的序列。/ Sequence to choose from.

    Returns:
        随机选中的元素。/ Randomly chosen element.
    """
    return random.choice(items)
