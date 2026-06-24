"""字典操作扩展工具。

Map / dict utility extensions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

K = TypeVar("K")
K2 = TypeVar("K2")
V = TypeVar("V")
V2 = TypeVar("V2")


def map_values(d: dict[K, V], *, f: Callable[[V], V2]) -> dict[K, V2]:
    """对字典的每个值应用转换函数。

    Transforms every value in a dict using the given function.

    Args:
        d: 原始字典。/ Source dict.
        f: 值转换函数。/ Value transform function.

    Returns:
        转换后的新字典。/ New dict with transformed values.
    """
    return {k: f(v) for k, v in d.items()}


def map_keys(d: dict[K, V], *, f: Callable[[K], K2]) -> dict[K2, V]:
    """对字典的每个键应用转换函数。

    Transforms every key in a dict using the given function.

    Args:
        d: 原始字典。/ Source dict.
        f: 键转换函数。/ Key transform function.

    Returns:
        转换后的新字典。/ New dict with transformed keys.
    """
    return {f(k): v for k, v in d.items()}


def filter_keys(
    d: dict[K, V],
    *,
    predicate: Callable[[K], bool],
) -> dict[K, V]:
    """按键过滤字典。

    Filters a dict by its keys.

    Args:
        d: 原始字典。/ Source dict.
        predicate: 键的过滤条件。/ Key filter predicate.

    Returns:
        过滤后的新字典。/ New filtered dict.
    """
    return {k: v for k, v in d.items() if predicate(k)}


def filter_values(
    d: dict[K, V],
    *,
    predicate: Callable[[V], bool],
) -> dict[K, V]:
    """按值过滤字典。

    Filters a dict by its values.

    Args:
        d: 原始字典。/ Source dict.
        predicate: 值的过滤条件。/ Value filter predicate.

    Returns:
        过滤后的新字典。/ New filtered dict.
    """
    return {k: v for k, v in d.items() if predicate(v)}


def merge(*dicts: dict[K, V]) -> dict[K, V]:
    """合并多个字典，后者覆盖前者的同名键。

    Merges multiple dicts; later dicts override earlier ones on
    key collision.

    Args:
        *dicts: 待合并的字典序列。/ Dicts to merge.

    Returns:
        合并后的新字典。/ Merged dict.
    """
    result: dict[K, V] = {}
    for d in dicts:
        result.update(d)
    return result
