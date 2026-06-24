"""数学层并行折叠操作。

Math-layer parallel fold operation.

委托 utils.parallel.fold 中的基础实现。
Delegates to the base implementation in utils.parallel.fold.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from ospf_python.utils.parallel.fold import (
    fold_parallel as _base_fold_parallel,
)

# T: 元素类型 / Element type
T = TypeVar("T")

# U: 累积值类型 / Accumulator type
U = TypeVar("U")


async def fold_parallel(
    items: Sequence[T],
    initial: U,
    operation: Callable[[U, T], U],
    *,
    concurrency: int = 8,
) -> U:
    """并行折叠（数学层入口）。

    Parallel fold (math-layer entry point).

    委托 utils.parallel.fold.fold_parallel。
    Delegates to utils.parallel.fold.fold_parallel.

    Args:
        items: 待折叠的元素序列。/ Elements to fold.
        initial: 初始累积值。/ Initial accumulator.
        operation: 合并操作。/ Merge operation.
        concurrency: 最大并发数。/ Max concurrency.

    Returns:
        折叠后的最终值。/ Final folded value.
    """
    return await _base_fold_parallel(
        items,
        initial,
        operation,
        concurrency=concurrency,
    )
