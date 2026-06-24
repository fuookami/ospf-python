"""多维数组快速求和。

Optimized summation for multi-arrays using numpy.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape


def fast_sum(
    arr: MultiArray[Any, Any],
    *,
    axis: int | None = None,
) -> Any:
    """对多维数组进行快速求和。

    Fast summation over a multi-array using numpy backend.

    当 axis 为 None 时，对所有元素求和返回标量。
    当 axis 指定维度时，沿该轴求和返回新的 MultiArray。
    When axis is None, sums all elements and returns a scalar.
    When axis is given, sums along that axis and returns a
    new MultiArray.

    Args:
        arr: 输入多维数组。/ Input multi-array.
        axis: 求和轴，None 表示全部。/ Summation axis, None for all.

    Returns:
        求和结果（标量或新数组）。/ Sum result (scalar or new array).
    """
    reshaped = arr._data.reshape(arr.shape.dims)

    if axis is None:
        return float(np.sum(reshaped))

    result = np.sum(reshaped, axis=axis)
    new_dims = result.shape
    new_shape = DynShape(dims=new_dims)
    flat_data = result.flatten()
    return MultiArray(new_shape, flat_data)
