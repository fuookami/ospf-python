"""公共转置的 NumPy 存储与外部协议边界 / NumPy storage and external protocols for public transpose."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import numpy as np

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.multiarray.shape import DynShape, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok


def transpose_shared_array[R](
    *,
    owner: Any,
    precopy: bool,
    finish: Callable[[Any, np.ndarray[Any, Any]], R],
) -> BindingResult[R]:
    """由固定 Rust 遍历坐标，保留 live/预复制差异 / Traverse pinned Rust coordinates, preserving live/precopy differences.

    Args:
        owner: 共享存储所有者 / Shared-storage owner.
        precopy: 可变源先创建不可变副本 / Copy mutable input into an immutable owner first.
        finish: 不可变数组构造器 / Immutable array constructor.

    Returns:
        转置数组或保留外部异常的失败 / Transposed array or failure retaining external exceptions.
    """
    try:
        if precopy:
            owner = finish(owner._shape, owner._data.copy())
        new_dims = tuple(reversed(owner._shape.dims))
        strides = tuple(reversed(owner._shape.strides()))
        data = np.empty(owner.size, dtype=owner._data.dtype)
        payload = _native._create_coordinate_plan(list(owner._shape.dims))
        plan = invoke(lambda: payload)
        if not isinstance(plan, Ok):
            return cast("BindingResult[R]", plan)
        tail_payload = plan.value.transpose_into(
            owner=owner, strides=strides, destination=data
        )
        tail = invoke(lambda: tail_payload)
        if not isinstance(tail, Ok):
            return cast("BindingResult[R]", tail)
        storage = (
            StorageOrder.COLUMN_MAJOR
            if owner._shape.storage_order == StorageOrder.ROW_MAJOR
            else StorageOrder.ROW_MAJOR
        )
        shape = DynShape(dims=new_dims, storage_order=storage)
        return Ok(finish(shape, data))
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="共享数组转置外部协议失败 / Shared array transpose external protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="EXTERNAL_TRANSPOSE",
                    callback_exception=error,
                ),
            )
        )
