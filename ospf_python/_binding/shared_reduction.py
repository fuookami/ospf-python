"""公共共享数组归约的薄错误边界 / Thin error boundary for public shared-array reduction."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

import numpy as np

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed

T = TypeVar("T")


def reduce_shared_array(
    owner: object, callback: Callable[[T, T], T]
) -> BindingResult[T]:
    """保留逐槽 live 读取与用户结果身份 / Preserve per-slot live reads and user result identity.

    Args:
        owner: 保持权威外部存储的公共数组 / Public array owning authoritative external storage.
        callback: 按物理次序执行的二元函数 / Binary function in physical order.

    Returns:
        最终原始叶或带原始异常的失败 / Original final leaf or failure retaining the original exception.
    """
    try:
        payload = _native._reduce_shared_array(
            owner=owner, scalar_type=np.generic, callback=callback
        )
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="共享数组归约外部协议失败 / Shared array reduction external protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="EXTERNAL_REDUCTION",
                    callback_exception=error,
                ),
            )
        )
    return cast("BindingResult[T]", invoke(lambda: payload))
