"""Rust 形状规划与 NumPy 存储发布边界 / Rust shape planning and NumPy storage publication."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok


def _native_failure(error: _native.Failure) -> BindingResult[Any]:
    return invoke(lambda: (None, error))


# `types[0]` 是存储类型；`types[1..]` 是**全部内置形状类**——Rust 侧的快速路径只做指针比较，
# 所以把 Shape1..Shape4 一并传入，用户直接用 `Shape2` 作 reshape 目标时也能走快路径
# （此前只有 `DynShape` 算，`Shape2` 会退化 1.38 倍）。
# `types[0]` is the storage type; `types[1..]` lists every builtin shape class so the Rust fast
# path (pointer comparisons only) also covers `Shape1`..`Shape4`, not just `DynShape`.
_protocol = _native._StorageTransform(
    types=(np.ndarray, DynShape, Shape1, Shape2, Shape3, Shape4),
    success=Ok,
    failure=_native_failure,
)
_flatten_counted = _protocol.flatten_counted
_flatten_value_result = _protocol.flatten_value_result
_flatten_value_result_checked = _protocol.flatten_value_result_checked
_reshape = _protocol.reshape
_DYN_SHAPE_CLASS = DynShape
_DYN_SHAPE_INIT = DynShape.__init__
_DYN_SHAPE_NEW = DynShape.__new__


def _shape_constructor() -> Any:
    return DynShape


def _flat_shape(count: int) -> DynShape:
    """创建标准一维形状，保留可观察的构造器 hook / Create a standard 1-D shape while retaining observable constructor hooks."""
    if (
        DynShape is _DYN_SHAPE_CLASS
        and DynShape.__init__ is _DYN_SHAPE_INIT
        and DynShape.__new__ is _DYN_SHAPE_NEW
    ):
        shape = object.__new__(DynShape)
        namespace = shape.__dict__
        namespace["dims"] = (count,)
        namespace["storage_order"] = StorageOrder.ROW_MAJOR
        return shape
    return DynShape(dims=(count,))


def _external_failure(error: Exception) -> BindingResult[Any]:
    return Failed(
        ExErr(
            _code=ErrorCode.APPLICATION_ERROR,
            _message="存储变换外部协议失败 / Storage transform external protocol failed",
            value=FailureContext(
                source="ospf-python",
                category="APPLICATION_ERROR",
                rust_code=None,
                error_class="EXTERNAL_STORAGE_TRANSFORM",
                callback_exception=error,
            ),
        )
    )


def reshape_storage[R](
    *,
    owner: Any,
    target: Any,
    precopy: bool,
    resolve: Callable[[], Callable[[Any, np.ndarray[Any, Any]], R]],
) -> BindingResult[R]:
    """规划真实存储重塑，保留扩展 hook / Plan actual-storage reshape, preserving extension hooks.

    Args:
        owner: 当前存储所有者 / Current storage owner.
        target: 重塑目标 / Reshape target.
        precopy: 可变 reshape 先构造不可变副本 / Precopy mutable reshape into an immutable owner.
        resolve: 在参数求值前捕获当前不可变构造器 / Capture the current immutable constructor before argument evaluation.

    Returns:
        独立数组或保留外部异常的失败 / Detached array or failure retaining external exceptions.
    """
    try:
        result: BindingResult[R] = _reshape(
            owner=owner, target=target, precopy=precopy, resolve=resolve
        )
        return result
    except Exception as error:
        return _external_failure(error)


def flatten_storage[R](
    owner: Any,
    resolve: Callable[[], Callable[[Any, np.ndarray[Any, Any]], R]],
    *,
    standard: bool = False,
) -> BindingResult[R]:
    """发布一维逻辑元数据，保留真实缓冲 rank / Publish one-dimensional metadata, preserving actual buffer rank.

    Args:
        owner: 当前存储所有者 / Current storage owner.
        resolve: 在复制前捕获当前构造器 / Capture the current constructor before copying.
        standard: 精确内置数组与二维形状可读取字段计数 / Exact built-in storage with a 2-D shape may read field counts.

    Returns:
        独立数组或保留外部异常的失败 / Detached array or failure retaining external exceptions.
    """
    try:
        shape = owner._shape
        if (
            standard
            and type(shape) is Shape2
            and type(shape.d0) is int
            and type(shape.d1) is int
        ):
            count = shape.d0 * shape.d1
            if count > 0:
                fast_result: BindingResult[R] = _flatten_value_result_checked(
                    owner, count, _flat_shape(count), resolve
                )
                return fast_result
        count = owner.size
        result: BindingResult[R] = _flatten_counted(
            owner, count, resolve, shape_resolve=_shape_constructor
        )
        return result
    except Exception as error:
        return _external_failure(error)
