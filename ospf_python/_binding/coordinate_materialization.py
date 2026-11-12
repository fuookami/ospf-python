"""公共惰性映射的 live 采样与 NumPy 发布边界 / Live sampling and NumPy publication for public lazy mapping."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import numpy as np

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invalid, invoke
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


def materialize_coordinates[R](
    *, owner: Any, finish: Callable[[Any, np.ndarray[Any, Any]], R]
) -> BindingResult[R]:
    """采样全部逻辑坐标后按输出布局发布 / Sample all logical coordinates then publish in output layout.

    Args:
        owner: 拥有 live get 协议的视图 / View exposing live get protocols.
        finish: 保留捕获 shape 身份的结果构造器 / Result constructor retaining captured shape identity.

    Returns:
        独立数组或完整失败 / Detached array or complete failure.
    """
    try:
        shape = owner._source.shape
        plan_payload = _native._create_coordinate_plan(list(shape.dims))
        plan_result = invoke(lambda: plan_payload)
        if not isinstance(plan_result, Ok):
            return cast("BindingResult[R]", plan_result)
        plan = plan_result.value
        values = plan.sample(owner)
        # 先按原 C-order 执行全部 NumPy 输出协议，再重排第一轴；不能先换序探测叶。 / Execute all NumPy output protocols in original C order before gathering axis zero; never reorder leaf probing.
        data = np.array(values)
        order = shape.storage_order
        if not isinstance(order, StorageOrder):
            return invalid("输出存储顺序无效 / Invalid output storage order")
        permutation_payload = plan.permutation(
            column_major=order is StorageOrder.COLUMN_MAJOR,
            indexer=None
            if type(shape) in (DynShape, Shape1, Shape2, Shape3, Shape4)
            else shape.flat_index,
        )
        permutation = invoke(lambda: permutation_payload)
        if not isinstance(permutation, Ok):
            return cast("BindingResult[R]", permutation)
        if permutation.value is not None:
            data = np.take(data, permutation.value, axis=0)
        return Ok(finish(shape, data))
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="视图物化外部协议失败 / View materialization external protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="EXTERNAL_MATERIALIZATION",
                    callback_exception=error,
                ),
            )
        )
