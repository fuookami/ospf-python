"""值域限制工具。

Clamp utility for constraining values to a range.
"""

from __future__ import annotations

from typing import TypeVar

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

T = TypeVar("T")


def clamp(
    value: T,
    *,
    min_val: T,
    max_val: T,
) -> BindingResult[T]:
    """将值限制在指定范围内。

    Constrain a value to the given range.

    Args:
        value: 输入值。/ Input value.
        min_val: 下界。/ Lower bound.
        max_val: 上界。/ Upper bound.

    Returns:
        限制后的原对象或保留原异常的失败。/ Selected original object or failure retaining the exception.
    """
    try:
        maximum = max
        inner = _native._minmax_pair(
            left=value,
            right=max_val,
            callable=min,
            minimum=True,
            ops=_native._public_integer,
        )
        result = _native._minmax_pair(
            left=min_val,
            right=inner,
            callable=maximum,
            minimum=False,
            ops=_native._public_integer,
        )
        del maximum, inner
    except Exception as error:
        if isinstance(error, MemoryError):
            code = ErrorCode.RESOURCE_EXHAUSTED
        elif isinstance(error, OverflowError):
            code = ErrorCode.OVERFLOW
        elif isinstance(error, (TypeError, ValueError)):
            code = ErrorCode.ILLEGAL_ARGUMENT
        else:
            code = ErrorCode.APPLICATION_ERROR
        return Failed(
            ExErr(
                _code=code,
                _message="值域限制比较失败 / Clamp comparison failed",
                value=FailureContext(
                    source="ospf-python",
                    category=code.name,
                    rust_code=None,
                    error_class="EXTERNAL_CLAMP",
                    callback_exception=error,
                ),
            )
        )
    return Ok(result)
