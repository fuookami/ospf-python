"""固定 Rust 初等运算符的 Result 与异常来源适配。 / Result and exception provenance for pinned Rust elementary operators."""

from __future__ import annotations

from numbers import Real
from typing import SupportsFloat, SupportsIndex

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invalid, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed


def _evaluate(
    operation: str,
    value: SupportsFloat | SupportsIndex,
) -> BindingResult[float]:
    """执行一次原生初等运算并保留输入异常来源。 / Perform one native elementary operation and retain input-exception provenance."""
    if operation == "exp10" and not isinstance(value, Real):
        return invalid(
            "exp10 只接受真实数值协议 / exp10 accepts only the real numeric protocol"
        )
    try:
        # B330（2026-11-11）：扩展已按当前源码重建（`logs/p3/_post-soak-runbook.sh` 前 5 步全过），
        # 边界签名是「位置或关键字」，所以这里翻转成位置参数。实测位置参数比关键字约快 100 ns
        # （302 → 203 ns，B263）。原 `ponytail:` 注释已按它的升级路径执行。
        # B330: the extension has been rebuilt from current source, so the boundary is now
        # positional-or-keyword. Flipping to positional (measured ~100 ns faster, 302 -> 203 ns).
        payload = _native._elementary_operator(operation, value)
    except Exception as error:
        if isinstance(error, MemoryError):
            code = ErrorCode.RESOURCE_EXHAUSTED
        elif isinstance(error, TypeError):
            code = ErrorCode.ILLEGAL_ARGUMENT
        elif isinstance(error, OverflowError):
            code = ErrorCode.OVERFLOW
        else:
            code = ErrorCode.APPLICATION_ERROR
        return Failed(
            ExErr(
                _code=code,
                _message="初等运算输入或传输失败 / Elementary operation input or transport failed",
                value=FailureContext(
                    source="ospf-python",
                    category=code.name,
                    rust_code=None,
                    error_class="EXTERNAL_ELEMENTARY_OPERATOR",
                    callback_exception=error,
                ),
            )
        )
    return invoke(lambda: payload)


def exp(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算自然指数。 / Compute natural exponential through pinned Rust."""
    return _evaluate("exp", value)


def exp2(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 上游幂函数计算以2为底的指数。 / Compute base-2 exponential through the pinned upstream power operator."""
    return _evaluate("exp2", value)


def exp10(value: Real) -> BindingResult[float]:
    """通过固定 Rust 上游幂函数计算以10为底的指数。 / Compute base-10 exponential through the pinned upstream power operator."""
    return _evaluate("exp10", value)


def ln(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算自然对数。 / Compute natural logarithm through pinned Rust."""
    return _evaluate("ln", value)


def log2(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算以2为底的对数。 / Compute base-2 logarithm through pinned Rust."""
    return _evaluate("log2", value)


def log10(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算以10为底的对数。 / Compute base-10 logarithm through pinned Rust."""
    return _evaluate("log10", value)


def sin(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算正弦。 / Compute sine through pinned Rust."""
    return _evaluate("sin", value)


def cos(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算余弦。 / Compute cosine through pinned Rust."""
    return _evaluate("cos", value)


def tan(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算正切。 / Compute tangent through pinned Rust."""
    return _evaluate("tan", value)


def asin(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算反正弦。 / Compute arcsine through pinned Rust."""
    return _evaluate("asin", value)


def acos(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算反余弦。 / Compute arccosine through pinned Rust."""
    return _evaluate("acos", value)


def atan(value: SupportsFloat | SupportsIndex) -> BindingResult[float]:
    """通过固定 Rust 计算反正切。 / Compute arctangent through pinned Rust."""
    return _evaluate("atan", value)
