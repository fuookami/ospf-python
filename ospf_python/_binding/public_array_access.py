"""公共共享数组的受检访问边界 / Checked access boundary for public shared arrays."""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from ospf_python import _native
from ospf_python._binding.multiarray import Shape as RustShape
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
    invoke,
)
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

_SHAPE_TYPES = (Shape1, Shape2, Shape3, Shape4, DynShape)


def _native_failure(error: _native.Failure) -> BindingResult[Any]:
    return invoke(lambda: (None, error))


_protocol = _native._SharedAccess(
    shape_types=_SHAPE_TYPES,
    row_major=StorageOrder.ROW_MAJOR,
    column_major=StorageOrder.COLUMN_MAJOR,
    ndarray_type=np.ndarray,
    scalar_type=np.generic,
    success=Ok,
    failure=_native_failure,
)
_read_shared_slot = _protocol.read
_write_shared_slot = _protocol.write


def _external_failure[T](error: Exception) -> BindingResult[T]:
    return Failed(
        ExErr(
            _code=ErrorCode.APPLICATION_ERROR,
            _message="共享数组外部协议失败 / Shared array external protocol failed",
            value=FailureContext(
                source="ospf-python",
                category="APPLICATION_ERROR",
                rust_code=None,
                error_class="EXTERNAL_ARRAY",
                callback_exception=error,
            ),
        )
    )


def _checked_shape(owner: Any, standard_layout: bool) -> BindingResult[RustShape]:
    if type(standard_layout) is not bool:
        return invalid("standard_layout 必须为 bool / standard_layout must be bool")
    # 不调用旧 flat_index/strides，不推断任意用户映射。 / Do not call legacy flat_index/strides or infer arbitrary user mappings.
    shape = owner._shape
    if (
        type(shape) not in (Shape1, Shape2, Shape3, Shape4, DynShape)
        and not standard_layout
    ):
        return invalid(
            "自定义形状必须显式确认标准布局 / Custom shapes require explicit standard-layout confirmation"
        )
    return RustShape.create(dims=shape.dims, storage_order=shape.storage_order)


def read_many[T](
    *, owner: Any, indices: list[tuple[int, ...]], standard_layout: bool
) -> BindingResult[list[T]]:
    """一次定位整批坐标后收集共享槽位 / Collect shared slots after checking a whole coordinate batch.

    Args:
        owner: 持有公开字段的数组 / Array holding public fields.
        indices: 内置坐标 list，保持次序和重复 / Built-in coordinate list, preserving order and duplicates.
        standard_layout: 自定义形状的显式标准布局确认 / Explicit standard-layout confirmation for custom shapes.

    Returns:
        完整独立列表或保留原始异常的失败，不发布部分输出 / Complete detached list or failure retaining the original exception, never partial output.
    """
    try:
        if type(indices) is not list:
            return invalid(
                "需要坐标的内置 list / A built-in coordinate list is required"
            )
        shape_result = _checked_shape(owner, standard_layout)
        if not isinstance(shape_result, Ok):
            return cast("BindingResult[list[T]]", shape_result)
        offsets = shape_result.value.indices_of(indices)
        if not isinstance(offsets, Ok):
            return cast("BindingResult[list[T]]", offsets)
        data = owner._data
        if not issubclass(type(data), np.ndarray):
            return invalid("共享存储必须为 ndarray / Shared storage must be an ndarray")
        if data.ndim != 1 or data.size != shape_result.value.size:
            return invalid(
                "共享存储必须是一维且与形状大小一致 / Shared storage must be one-dimensional and match the shape size"
            )
        return Ok(
            _native._read_shared_array(
                data=data,
                count=len(offsets.value),
                offsets=offsets.value,
                scalar_type=np.generic,
            )
        )
    except Exception as error:
        return _external_failure(error)


def raw_snapshot(*, data: np.ndarray, count: int) -> BindingResult[list[Any]]:
    """按物理次序取得原始叶，不执行 scalar 转换 / Collect raw leaves in physical order without scalar conversion.

    Args:
        data: 已检查的一维 ndarray / Validated one-dimensional ndarray.
        count: 已检查的形状大小 / Validated shape size.

    Returns:
        完整物理引用列表或外部协议失败 / Complete physical reference list or external-protocol failure.
    """
    try:
        return Ok(_native._read_shared_array(data=data, count=count))
    except Exception as error:
        return _external_failure(error)


def read[T](
    *, owner: object, indices: tuple[int, ...], standard_layout: bool
) -> BindingResult[T]:
    """在 Rust 受检定位后读取原共享槽位 / Read the original shared slot after Rust checked indexing.

    Args:
        owner: 持有公开字段的数组 / Array holding the public fields.
        indices: 完整非负坐标 / Complete nonnegative coordinates.
        standard_layout: 自定义形状的显式标准布局确认 / Explicit standard-layout confirmation for custom shapes.

    Returns:
        叶值或保留原始外部异常的失败 / Leaf or failure retaining the original external exception.
    """
    try:
        return cast(
            "BindingResult[T]",
            _read_shared_slot(
                owner=owner,
                indices=indices,
                standard_layout=standard_layout,
            ),
        )
    except Exception as error:
        # ndarray/自定义形状/scalar 为外部协议；不吞进程控制异常、不格式化用户异常。 / ndarray/custom shape/scalar are external protocols; preserve process-control exceptions and never format user exceptions.
        return _external_failure(error)


def write[T](
    *, owner: object, indices: tuple[int, ...], value: T, standard_layout: bool
) -> BindingResult[None]:
    """在 Rust 受检定位后写入原共享槽位 / Write the original shared slot after Rust checked indexing.

    Args:
        owner: 可变公开数组 / Mutable public array.
        indices: 完整非负坐标 / Complete nonnegative coordinates.
        value: 遵守原 ndarray dtype 赋值协议的值 / Value following the original ndarray dtype assignment protocol.
        standard_layout: 自定义形状的显式标准布局确认 / Explicit standard-layout confirmation for custom shapes.

    Returns:
        成功或保留原始外部异常的失败 / Success or failure retaining the original external exception.
    """
    try:
        return cast(
            "BindingResult[None]",
            _write_shared_slot(
                owner=owner,
                indices=indices,
                value=value,
                standard_layout=standard_layout,
            ),
        )
    except Exception as error:
        return _external_failure(error)
