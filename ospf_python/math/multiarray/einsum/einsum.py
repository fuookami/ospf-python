"""爱因斯坦求和核心实现。

Core Einstein summation implementation with validation.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ospf_python.math.multiarray.einsum.einsum_error import (
    EinsumError,
)
from ospf_python.math.multiarray.einsum.einsum_parser import (
    parse_einsum,
)
from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape


def _as_np(arr: MultiArray[Any, Any]) -> np.ndarray:
    """将 MultiArray 转换为 numpy 数组。

    Convert a MultiArray to a numpy ndarray.
    """
    return arr._data.reshape(arr.shape.dims)


def einsum(
    subscripts: str,
    *operands: MultiArray[Any, Any],
) -> MultiArray[Any, DynShape] | float | EinsumError:
    """爱因斯坦求和，带输入校验。

    Einstein summation with input validation.

    支持标准 einsum 下标表示法，如 "ij,jk->ik"。
    委托 numpy 执行实际计算。
    Supports standard einsum subscript notation, e.g.
    "ij,jk->ik". Delegates actual computation to numpy.

    Args:
        subscripts: 下标字符串。/ Subscript string.
        *operands: 输入多维数组。/ Input multi-arrays.

    Returns:
        计算结果或错误。/ Computation result or error.
    """
    parsed = parse_einsum(subscripts)
    if isinstance(parsed, EinsumError):
        return parsed

    input_labels, output_label = parsed

    # 校验操作数数量 / Validate operand count
    if len(operands) != len(input_labels):
        return EinsumError(
            message=(
                f"操作数数量不匹配: 期望 {len(input_labels)}, "
                f"实际 {len(operands)}"
                f" / Operand count mismatch: expected "
                f"{len(input_labels)}, got {len(operands)}"
            )
        )

    # 校验维度匹配 / Validate dimension match
    for i, (label, op) in enumerate(zip(input_labels, operands, strict=False)):
        if label.ndim != op.ndim:
            return EinsumError(
                message=(
                    f"操作数 {i} 维度不匹配: "
                    f"下标期望 {label.ndim} 维, "
                    f"实际 {op.ndim} 维"
                    f" / Operand {i} dimension mismatch: "
                    f"subscript expects {label.ndim}-d, "
                    f"got {op.ndim}-d"
                )
            )

    # 委托 numpy 执行 / Delegate to numpy
    np_operands = [_as_np(op) for op in operands]
    result = np.einsum(subscripts, *np_operands)

    if result.ndim == 0:
        return float(result)

    new_shape = DynShape(dims=result.shape)
    return MultiArray(new_shape, result.flatten().copy())
