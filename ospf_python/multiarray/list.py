"""列表扩展工具函数，用于多维数组操作。

List extension functions for multi-array operations.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def flatten_list(nested: list[Any]) -> list[Any]:
    """递归展平嵌套列表。

    Recursively flatten nested lists.

    Args:
        nested: 嵌套列表。/ Nested list.

    Returns:
        展平后的列表。/ Flattened list.
    """
    result: list[Any] = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def transpose_list(
    matrix: list[list[T]],
) -> list[list[T]]:
    """转置二维列表（行列互换）。

    Transpose a 2-D list (swap rows and columns).

    Args:
        matrix: 二维列表。/ 2-D list.

    Returns:
        转置后的二维列表。/ Transposed 2-D list.
    """
    if not matrix:
        return []
    return [list(row) for row in zip(*matrix, strict=False)]


def chunk_list(
    items: Sequence[T],
    *,
    size: int,
) -> list[Sequence[T]]:
    """将列表按指定大小分块。

    Split a list into chunks of the given size.

    Args:
        items: 待分块的序列。/ Sequence to split.
        size: 每块大小，必须大于 0。
            Chunk size, must be > 0.

    Returns:
        分块后的列表。/ List of chunks.
    """
    if size <= 0:
        return []
    return [items[i : i + size] for i in range(0, len(items), size)]
