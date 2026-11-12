"""固定 Rust 素数筛的整数协议和 Result 适配。 / Integer protocol and Result adapter for the pinned Rust sieve."""

from __future__ import annotations

import operator
from typing import SupportsIndex

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed


def primes_up_to(n: SupportsIndex) -> BindingResult[list[int]]:
    """采集一次整数并调用唯一的上游筛法。 / Collect an integer once and call the sole upstream sieve.

    Args:
        n: 包含式整数上界。 / Inclusive integer bound.

    Returns:
        素数列表或保留原异常的失败。 / Prime list or failure retaining the original exception.
    """
    try:
        limit = operator.index(n)
        payload = _native._primes_up_to(limit=limit)
    except Exception as error:
        if isinstance(error, MemoryError):
            code = ErrorCode.RESOURCE_EXHAUSTED
        elif isinstance(error, TypeError):
            code = ErrorCode.ILLEGAL_ARGUMENT
        else:
            code = ErrorCode.APPLICATION_ERROR
        return Failed(
            ExErr(
                _code=code,
                _message="素数筛输入或传输失败 / Prime sieve input or transport failed",
                value=FailureContext(
                    source="ospf-python",
                    category=code.name,
                    rust_code=None,
                    error_class="EXTERNAL_INTEGER",
                    callback_exception=error,
                ),
            )
        )
    return invoke(lambda: payload)
