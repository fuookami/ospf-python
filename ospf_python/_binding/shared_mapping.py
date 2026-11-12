"""公共共享映射的薄 NumPy/错误边界 / Thin NumPy/error boundary for public shared mapping."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import numpy as np

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok


def map_shared_array[T, R](
    *,
    owner: object,
    callback: Callable[[T], object],
    flat: bool,
    finish: Callable[[np.ndarray[Any, Any]], R],
) -> BindingResult[R]:
    """保留 live 读取及 NumPy 输出协议 / Preserve live reads and NumPy output protocols.

    Args:
        owner: 权威共享存储所有者 / Authoritative shared-storage owner.
        callback: 任意单叶转换 / Arbitrary single-leaf transform.
        flat: 是否使用 list.extend / Whether to use list.extend.
        finish: 转换完成后读取当前形状并构造结果 / Read current shape and construct after conversion.

    Returns:
        新数组或保留原异常的失败 / New array or failure retaining the original exception.
    """
    try:
        # map 提前解析 callable，flat_map 完整扩展后才解析。 / map resolves the callable early; flat_map only after complete extension.
        array = None if flat else np.array
        values, failure = _native._map_shared_array(
            owner=owner, scalar_type=np.generic, callback=callback, flat=flat
        )
        if failure is not None:
            return cast("BindingResult[R]", invoke(lambda: (None, failure)))
        new_data = (np.array if flat else cast("Any", array))(values)
        del array
        if not flat:
            # 列表推导临时值在构造器之前释放；flat_map 局部列表保持存活。 / Release the comprehension temporary before construction; keep flat_map's local list alive.
            del values
        return Ok(finish(new_data))
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="共享数组映射外部协议失败 / Shared array mapping external protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="EXTERNAL_MAPPING",
                    callback_exception=error,
                ),
            )
        )
