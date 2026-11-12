"""公共 view 的复制和区域发布边界 / Public view copy and region publication boundary."""

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

__all__ = ["DynShape"]

_SHAPE_TYPES = (Shape1, Shape2, Shape3, Shape4, DynShape)


def _native_failure(error: _native.Failure) -> BindingResult[Any]:
    return invoke(lambda: (None, error))


_protocol = _native._SharedView(
    shape_types=_SHAPE_TYPES,
    row_major=StorageOrder.ROW_MAJOR,
    column_major=StorageOrder.COLUMN_MAJOR,
    success=Ok,
    failure=_native_failure,
)
_DEFAULT_PROTOCOL = _protocol
_DEFAULT_MATERIALIZE: Callable[..., BindingResult[Any]] = _protocol.materialize


def external_failure(error: Exception) -> BindingResult[Any]:
    """发布普通视图物化的外部异常 / Publish a plain-view materialization exception.

    Args:
        error: 原始外部异常 / Original external exception.

    Returns:
        保留原异常身份的失败 / Failure retaining the original exception identity.
    """
    return Failed(
        ExErr(
            _code=ErrorCode.APPLICATION_ERROR,
            _message="普通视图物化外部协议失败 / Plain view materialization external protocol failed",
            value=FailureContext(
                source="ospf-python",
                category="APPLICATION_ERROR",
                rust_code=None,
                error_class="EXTERNAL_VIEW_MATERIALIZATION",
                callback_exception=error,
            ),
        )
    )


def materialize_shared_view(
    owner: object, resolve: Callable[[], Callable[[Any, Any], Any]]
) -> BindingResult[Any]:
    """通过原生受检区域物化普通 view / Materialize a plain view through a native checked region.

    Args:
        owner: 持有旧 source/offset 字段的 view / View holding legacy source/offset fields.
        resolve: 在复制后捕获当前结果构造器 / Capture the current result constructor after copying.

    Returns:
        独立数组或保留外部异常的失败 / Detached array or failure retaining external exceptions.
    """
    try:
        return cast(
            "BindingResult[Any]",
            _protocol.materialize(owner=owner, make_shape=DynShape, resolve=resolve),
        )
    except Exception as error:
        return external_failure(error)
