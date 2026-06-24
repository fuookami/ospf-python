"""数学层集合操作扩展。

Math-layer collection utility extensions.

委托 utils.functional.collection 中的基础实现，
提供数学领域特定的便捷函数。
Delegates to base implementations in
utils.functional.collection, providing math-domain
convenience functions.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import reduce
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")


def sum_by(
    items: Iterable[T],
    *,
    selector: Callable[[T], float],
) -> float:
    """对可迭代对象按选择器函数求和。

    Sums items projected by a selector function.

    Args:
        items: 待求和的可迭代对象。/ Items to sum.
        selector: 提取数值的函数。/ Numeric extractor.

    Returns:
        求和结果。/ Sum result.
    """
    return sum(selector(item) for item in items)


def product(
    items: Iterable[float],
) -> float:
    """计算可迭代对象中所有数值的乘积。

    Compute the product of all numeric items.

    Args:
        items: 数值可迭代对象。/ Numeric iterable.

    Returns:
        乘积结果。/ Product result.
    """
    return reduce(lambda a, b: a * b, items, 1.0)
