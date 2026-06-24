"""集合操作扩展工具。

Collection utility extensions.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")


def flatten(list_of_lists: Iterable[Iterable[T]]) -> list[T]:
    """将嵌套列表展平为单层列表。

    Flattens a nested iterable into a single flat list.

    Args:
        list_of_lists: 嵌套可迭代对象。/ Nested iterables.

    Returns:
        展平后的列表。/ Flattened list.
    """
    return [item for sublist in list_of_lists for item in sublist]


def distinct_by(
    items: Iterable[T],
    *,
    key_func: Callable[[T], K],
) -> list[T]:
    """按指定键函数去重，保留首次出现的元素。

    Deduplicates items by a key function, keeping the first occurrence.

    Args:
        items: 待去重的可迭代对象。/ Items to deduplicate.
        key_func: 提取去重键的函数。/ Function to extract the dedup key.

    Returns:
        去重后的列表。/ Deduplicated list.
    """
    seen: set[K] = set()
    result: list[T] = []
    for item in items:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def chunked(items: Sequence[T], *, size: int) -> list[Sequence[T]]:
    """将序列按指定大小分块。

    Splits a sequence into chunks of the given size.

    Args:
        items: 待分块的序列。/ Sequence to split.
        size: 每块的大小，必须大于 0。/ Chunk size, must be > 0.

    Returns:
        分块后的列表。/ List of chunks.
    """
    return [items[i : i + size] for i in range(0, len(items), size)]


def zip_with_next(items: Sequence[T]) -> list[tuple[T, T]]:
    """将序列中相邻元素配对。

    Pairs each element with its next neighbour.

    Args:
        items: 待配对的序列。/ Sequence to pair.

    Returns:
        相邻元素对列表。/ List of consecutive pairs.
    """
    return [(items[i], items[i + 1]) for i in range(len(items) - 1)]


def sum_of(
    items: Iterable[T],
    *,
    selector: Callable[[T], float],
) -> float:
    """对可迭代对象按选择器函数求和。

    Sums items using a selector function.

    Args:
        items: 待求和的可迭代对象。/ Items to sum.
        selector: 提取数值的函数。/ Function to extract a numeric value.

    Returns:
        求和结果。/ Sum of selected values.
    """
    return sum(selector(item) for item in items)
