"""字典扩展工具函数，用于多维数组操作。

Map extension functions for multi-array operations.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

import numpy as np

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")


def map_to_matrix(
    d: dict[K, V],
    *,
    rows: Sequence[K],
    cols: Sequence[K],
    default: V = 0,  # type: ignore[assignment]
) -> np.ndarray:
    """将字典转换为二维 numpy 数组。

    Convert a dict to a 2-D numpy array.

    字典的键应为 (行键, 列键) 形式的元组。
    The dict keys should be tuples of (row_key, col_key).

    Args:
        d: 源字典，键为 (行键, 列键) 元组。
            Source dict with (row_key, col_key) tuple keys.
        rows: 行键序列。/ Row key sequence.
        cols: 列键序列。/ Column key sequence.
        default: 缺失键的默认值。
            Default value for missing keys.

    Returns:
        二维 numpy 数组。/ 2-D numpy array.
    """
    matrix = np.full((len(rows), len(cols)), default)
    row_index = {r: i for i, r in enumerate(rows)}
    col_index = {c: j for j, c in enumerate(cols)}

    for key, value in d.items():
        if (
            isinstance(key, tuple)
            and len(key) == 2
            and key[0] in row_index
            and key[1] in col_index
        ):
            r = row_index[key[0]]
            c = col_index[key[1]]
            matrix[r, c] = value

    return matrix


def group_by_to_array(
    items: Iterable[T],
    *,
    key_func: Callable[[T], K],
) -> dict[K, np.ndarray]:
    """按键函数分组并转换为 numpy 数组。

    Group items by a key function and convert to numpy arrays.

    Args:
        items: 待分组的可迭代对象。/ Items to group.
        key_func: 提取分组键的函数。
            Function to extract the grouping key.

    Returns:
        键到 numpy 数组的映射。
        Mapping from key to numpy array.
    """
    groups: dict[K, list[T]] = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return {key: np.array(values) for key, values in groups.items()}
