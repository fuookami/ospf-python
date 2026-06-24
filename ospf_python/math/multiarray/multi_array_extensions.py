"""多维数组运算扩展。

Multi-array operation extensions: dot, matmul, elementwise ops.
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


def dot(
    a: MultiArray[Any, Any],
    b: MultiArray[Any, Any],
) -> Any:
    """计算两个数组的点积。

    Compute the dot product of two arrays.

    对于一维数组，计算内积并返回标量。
    对于二维数组，执行矩阵乘法。
    For 1-D arrays, computes the inner product (scalar).
    For 2-D arrays, performs matrix multiplication.

    Args:
        a: 左侧数组。/ Left array.
        b: 右侧数组。/ Right array.

    Returns:
        点积结果。/ Dot product result.
    """
    a_np = _as_np(a)
    b_np = _as_np(b)
    result = np.dot(a_np, b_np)

    if result.ndim == 0:
        return float(result)

    new_shape = DynShape(dims=result.shape)
    return _from_np(result, new_shape)


def matmul(
    a: MultiArray[Any, Any],
    b: MultiArray[Any, Any],
) -> MultiArray[Any, DynShape]:
    """矩阵乘法。

    Matrix multiplication.

    Args:
        a: 左侧矩阵。/ Left matrix.
        b: 右侧矩阵。/ Right matrix.

    Returns:
        乘积结果矩阵。/ Product result matrix.
    """
    a_np = _as_np(a)
    b_np = _as_np(b)
    result = np.matmul(a_np, b_np)
    new_shape = DynShape(dims=result.shape)
    return _from_np(result, new_shape)


def elementwise_add(
    a: MultiArray[Any, Any],
    b: MultiArray[Any, Any],
) -> MultiArray[Any, Any]:
    """逐元素加法。

    Element-wise addition.

    Args:
        a: 左侧数组。/ Left array.
        b: 右侧数组。/ Right array.

    Returns:
        逐元素求和的新数组。/ New array with element-wise sum.
    """
    a_np = _as_np(a)
    b_np = _as_np(b)
    result = a_np + b_np
    new_shape = DynShape(dims=result.shape)
    return _from_np(result, new_shape)


def elementwise_mul(
    a: MultiArray[Any, Any],
    b: MultiArray[Any, Any],
) -> MultiArray[Any, Any]:
    """逐元素乘法。

    Element-wise multiplication.

    Args:
        a: 左侧数组。/ Left array.
        b: 右侧数组。/ Right array.

    Returns:
        逐元素乘积的新数组。/ New array with element-wise product.
    """
    a_np = _as_np(a)
    b_np = _as_np(b)
    result = a_np * b_np
    new_shape = DynShape(dims=result.shape)
    return _from_np(result, new_shape)
