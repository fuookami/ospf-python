"""公共共享数组的逻辑嵌套导出 / Logical nested export for public shared arrays."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

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

_SHAPE_TYPES = (Shape1, Shape2, Shape3, Shape4, DynShape)


def _native_failure(error: _native.Failure) -> BindingResult[Any]:
    return invoke(lambda: (None, error))


_protocol = _native._SharedNested(
    shape_types=_SHAPE_TYPES,
    row_major=StorageOrder.ROW_MAJOR,
    column_major=StorageOrder.COLUMN_MAJOR,
    success=Ok,
    failure=_native_failure,
)
_DEFAULT_PROTOCOL = _protocol
_DEFAULT_TO_LIST: Callable[[object], BindingResult[Any]] = _protocol.to_list


def external_failure(error: Exception) -> BindingResult[Any]:
    """发布嵌套导出的外部异常 / Publish a nested-export external exception.

    Args:
        error: 原始外部异常 / Original external exception.

    Returns:
        保留原异常身份的失败 / Failure retaining the original exception identity.
    """
    return Failed(
        ExErr(
            _code=ErrorCode.APPLICATION_ERROR,
            _message="嵌套导出外部协议失败 / Nested export external protocol failed",
            value=FailureContext(
                source="ospf-python",
                category="APPLICATION_ERROR",
                rust_code=None,
                error_class="EXTERNAL_NESTED_CONVERSION",
                callback_exception=error,
            ),
        )
    )


def nested_shared_array(owner: object) -> BindingResult[Any]:
    """按捕获的形状和缓冲导出逻辑嵌套值 / Export logical nested values from captured shape and buffer.

    Args:
        owner: 持有公开 shape/data 字段的数组 / Array holding public shape/data fields.

    Returns:
        嵌套列表、rank-zero 叶或保留原异常的失败 / Nested lists, a rank-zero leaf, or failure retaining the original exception.
    """
    try:
        value, error = _native._nested_shared_array(
            owner=owner,
            shape_types=_SHAPE_TYPES,
            row_major=StorageOrder.ROW_MAJOR,
            column_major=StorageOrder.COLUMN_MAJOR,
        )
    except Exception as error:
        return external_failure(error)
    if error is None:
        return Ok(cast("Any", value))
    code = ErrorCode.__members__.get(error.category, ErrorCode.APPLICATION_ERROR)
    return Failed(
        ExErr(
            _code=code,
            _message=error.message,
            value=FailureContext(
                source=error.source,
                category=error.category,
                rust_code=error.rust_code,
                error_class=error.error_class,
            ),
        )
    )
