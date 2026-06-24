"""爱因斯坦求和常用操作封装。

Common einsum operation wrappers: trace, diagonal, tensordot.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape


def _as_np(arr: MultiArray[Any, Any]) -> np.ndarray:
    """将 MultiArray 转换为 numpy 数组。

    Convert a MultiArray to a numpy ndarray.

    Args:
        arr: 输入多维数组。/ Input multi-array.

    Returns:
        重塑后的 numpy 数组。/ Reshaped numpy array.
    """
    return arr._data.reshape(arr.shape.dims)


def _from_np(
    data: np.ndarray,
    shape: DynShape,
) -> MultiArray[Any, DynShape]:
    """从 numpy 数组构造 MultiArray。

    Construct a MultiArray from a numpy ndarray.

    Args:
        data: numpy 数据。/ Numpy data.
        shape: 目标形状。/ Target shape.

    Returns:
        新的 MultiArray。/ New MultiArray.
    """
    return MultiArray(shape, data.flatten().copy())


def trace(
    a: MultiArray[Any, Any],
) -> float:
    """计算方阵的迹（对角线元素之和）。

    Compute the trace of a square matrix
    (sum of diagonal elements).

    Args:
        a: 输入方阵。/ Input square matrix.

    Returns:
        迹值。/ Trace value.
    """
    a_np = _as_np(a)
    return float(np.trace(a_np))


def diagonal(
    a: MultiArray[Any, Any],
) -> MultiArray[Any, DynShape]:
    """提取方阵的对角线元素。

    Extract the diagonal elements of a square matrix.

    Args:
        a: 输入方阵。/ Input square matrix.

    Returns:
        对角线元素组成的一维数组。
        1-D array of diagonal elements.
    """
    a_np = _as_np(a)
    diag = np.diagonal(a_np)
    new_shape = DynShape(dims=diag.shape)
    return _from_np(diag, new_shape)


def tensordot(
    a: MultiArray[Any, Any],
    b: MultiArray[Any, Any],
    *,
    axes: int = 1,
) -> MultiArray[Any, DynShape]:
    """沿指定轴计算张量收缩。

    Compute tensor contraction along specified axes.

    Args:
        a: 左侧张量。/ Left tensor.
        b: 右侧张量。/ Right tensor.
        axes: 收缩的轴数。/ Number of axes to contract.

    Returns:
        收缩结果张量。/ Contracted result tensor.
    """
    a_np = _as_np(a)
    b_np = _as_np(b)
    result = np.tensordot(a_np, b_np, axes=axes)
    new_shape = DynShape(dims=result.shape)
    return _from_np(result, new_shape)
