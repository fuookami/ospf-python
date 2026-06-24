"""列表查询扩展工具。

List utility extensions for querying elements.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")


def first_or_none(
    items: Iterable[T],
    *,
    predicate: Callable[[T], bool],
) -> T | None:
    """返回第一个满足谓词的元素，若无则返回 None。

    Returns the first element matching the predicate, or None.

    Args:
        items: 待搜索的可迭代对象。/ Items to search.
        predicate: 匹配条件。/ Match condition.

    Returns:
        匹配的元素或 None。/ Matching element or None.
    """
    return next((item for item in items if predicate(item)), None)


def last_or_none(
    items: Iterable[T],
    *,
    predicate: Callable[[T], bool],
) -> T | None:
    """返回最后一个满足谓词的元素，若无则返回 None。

    Returns the last element matching the predicate, or None.

    Args:
        items: 待搜索的可迭代对象。/ Items to search.
        predicate: 匹配条件。/ Match condition.

    Returns:
        匹配的元素或 None。/ Matching element or None.
    """
    result: T | None = None
    for item in items:
        if predicate(item):
            result = item
    return result


def single_or_none(
    items: Iterable[T],
    *,
    predicate: Callable[[T], bool],
) -> T | None:
    """返回唯一满足谓词的元素；若有多个匹配则返回 None。

    Returns the single element matching the predicate; returns None if
    there are zero or more than one matches.

    Args:
        items: 待搜索的可迭代对象。/ Items to search.
        predicate: 匹配条件。/ Match condition.

    Returns:
        唯一匹配的元素或 None。/ Single match or None.
    """
    found: T | None = None
    count = 0
    for item in items:
        if predicate(item):
            if count >= 1:
                return None
            found = item
            count += 1
    return found


def min_by_or_none(
    items: Iterable[T],
    *,
    selector: Callable[[T], K],
) -> T | None:
    """按选择器返回最小元素，若为空则返回 None。

    Returns the minimum element by selector, or None for empty input.

    Args:
        items: 待搜索的可迭代对象。/ Items to search.
        selector: 用于比较的键提取函数。/ Key extraction function.

    Returns:
        最小元素或 None。/ Minimum element or None.
    """
    best: T | None = None
    best_key: K | None = None
    for item in items:
        key = selector(item)
        if best_key is None or key < best_key:  # type: ignore[operator]
            best = item
            best_key = key
    return best


def max_by_or_none(
    items: Iterable[T],
    *,
    selector: Callable[[T], K],
) -> T | None:
    """按选择器返回最大元素，若为空则返回 None。

    Returns the maximum element by selector, or None for empty input.

    Args:
        items: 待搜索的可迭代对象。/ Items to search.
        selector: 用于比较的键提取函数。/ Key extraction function.

    Returns:
        最大元素或 None。/ Maximum element or None.
    """
    best: T | None = None
    best_key: K | None = None
    for item in items:
        key = selector(item)
        if best_key is None or key > best_key:  # type: ignore[operator]
            best = item
            best_key = key
    return best
