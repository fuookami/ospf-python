"""固定Rust对数的Result与异常来源适配。 / Result and exception provenance for pinned Rust logarithms."""

from __future__ import annotations

from typing import SupportsFloat, SupportsIndex

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed


def log_base(
    x: SupportsFloat | SupportsIndex, base: SupportsFloat | SupportsIndex
) -> BindingResult[float]:
    """按原顺序调用输入协议，并保留原始异常。 / Invoke input protocols in original order and retain original exceptions.

    Args:
        x: 正数或非有限数值输入。 / Positive or nonfinite numeric input.
        base: 正数且不为1的底数或非有限值。 / Positive nonunit base or nonfinite value.

    Returns:
        Float64结果或带原始来源的失败。 / Float64 result or failure with original provenance.
    """
    try:
        payload = _native._log_base(x=x, base=base)
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
                _message="对数输入或传输失败 / Logarithm input or transport failed",
                value=FailureContext(
                    source="ospf-python",
                    category=code.name,
                    rust_code=None,
                    error_class="EXTERNAL_LOGARITHM",
                    callback_exception=error,
                ),
            )
        )
    return invoke(lambda: payload)
