"""固定 Rust 整数幂的输入协议与 Result 适配。 / Input protocol and Result adaptation for pinned Rust integer power."""

from __future__ import annotations

import operator
from typing import SupportsIndex

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed


def pow_int(base: SupportsIndex, exp: SupportsIndex) -> BindingResult[int]:
    """按底数/指数顺序采集一次整数并调用上游。 / Collect base/exponent integers once in order and invoke upstream.

    Args:
        base: 任意精度整数底数。 / Arbitrary-precision integer base.
        exp: 非负整数指数。 / Nonnegative integer exponent.

    Returns:
        精确整数或保留原异常的失败。 / Exact integer or failure retaining the original exception.
    """
    try:
        integer = operator.index(base)
        exponent = operator.index(exp)
        payload = _native._pow_int(base=integer, exponent=exponent)
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
                _message="整数幂输入或传输失败 / Integer power input or transport failed",
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
