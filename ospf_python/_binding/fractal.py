"""固定 Rust 分形迭代的 Result 与输入异常适配。 / Result and input-exception adaptation for pinned Rust fractal iteration."""

from __future__ import annotations

from operator import index
from typing import SupportsComplex, SupportsFloat, SupportsIndex

from ospf_python import _native
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
    invoke,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

# 公共边界共享的原生计数上限。 / Shared native count limit for public boundaries.
_U64_MAX = (1 << 64) - 1


def _external_failure[T](error: Exception) -> BindingResult[T]:
    """保留 Python 输入协议异常。 / Preserve a Python input-protocol exception."""
    if isinstance(error, MemoryError):
        code = ErrorCode.RESOURCE_EXHAUSTED
    elif isinstance(error, (TypeError, ValueError)):
        code = ErrorCode.ILLEGAL_ARGUMENT
    elif isinstance(error, OverflowError):
        code = ErrorCode.OVERFLOW
    else:
        code = ErrorCode.APPLICATION_ERROR
    return Failed(
        ExErr(
            _code=code,
            _message="分形输入协议失败 / Fractal input protocol failed",
            value=FailureContext(
                source="ospf-python",
                category=code.name,
                rust_code=None,
                error_class="EXTERNAL_FRACTAL_INPUT",
                callback_exception=error,
            ),
        )
    )


def _resource_failure[T]() -> BindingResult[T]:
    """拒绝超出原生计数的正迭代上限。 / Reject positive iteration limits outside the native count."""
    return Failed(
        ExErr(
            _code=ErrorCode.RESOURCE_EXHAUSTED,
            _message=(
                "分形迭代次数超过u64原生边界 / "
                "Fractal iteration count exceeds the native u64 boundary"
            ),
            value=FailureContext(
                source="ospf-python",
                category="RESOURCE_EXHAUSTED",
                rust_code=None,
                error_class="BOUNDARY",
            ),
        )
    )


def _transport_failure[T](error: _native.Failure) -> BindingResult[T]:
    """发布原生结构化失败。 / Publish a structured native failure."""
    return invoke(lambda: (None, error))


def mandelbrot_iterate(
    c: SupportsComplex,
    max_iterations: SupportsIndex,
) -> BindingResult[int]:
    """执行 Mandelbrot 逃逸迭代。 / Evaluate Mandelbrot escape iteration."""
    try:
        count = (
            max_iterations
            if type(max_iterations) is int or type(max_iterations) is bool
            else index(max_iterations)
        )
    except Exception as error:
        return _external_failure(error)
    if count > _U64_MAX:
        return _resource_failure()
    if count <= 0:
        return Ok(count)
    try:
        value = c if type(c) is complex else complex(c)
    except Exception as error:
        return _external_failure(error)
    try:
        result, transport_error = _native._fractal_escape_time(0j, value, count)
    except (TypeError, ValueError, OverflowError) as error:
        return invalid(f"绑定参数无效 / Invalid binding argument: {error}")
    if transport_error is None:
        if result is None:
            return invalid("原生分形结果缺失 / Native fractal result is missing")
        return Ok(result)
    return invoke(lambda: (None, transport_error))


def julia_iterate(
    z: SupportsComplex,
    c: SupportsComplex,
    max_iterations: SupportsIndex,
) -> BindingResult[int]:
    """执行 Julia 逃逸迭代。 / Evaluate Julia escape iteration."""
    try:
        count = (
            max_iterations
            if type(max_iterations) is int or type(max_iterations) is bool
            else index(max_iterations)
        )
    except Exception as error:
        return _external_failure(error)
    if count > _U64_MAX:
        return _resource_failure()
    if count <= 0:
        return Ok(count)
    try:
        current = z if type(z) is complex else complex(z)
    except Exception as error:
        return _external_failure(error)
    try:
        parameter = c if type(c) is complex else complex(c)
    except Exception as error:
        return _external_failure(error)
    try:
        result, transport_error = _native._fractal_escape_time(
            current, parameter, count
        )
    except (TypeError, ValueError, OverflowError) as error:
        return invalid(f"绑定参数无效 / Invalid binding argument: {error}")
    if transport_error is None:
        if result is None:
            return invalid("原生分形结果缺失 / Native fractal result is missing")
        return Ok(result)
    return invoke(lambda: (None, transport_error))


def julia_contains_pair(
    *,
    x: SupportsComplex | SupportsFloat | SupportsIndex,
    y: SupportsFloat | SupportsIndex,
    c_real: SupportsComplex | SupportsFloat | SupportsIndex,
    c_imag: SupportsFloat | SupportsIndex,
    max_iterations: SupportsIndex,
) -> BindingResult[tuple[complex, complex]]:
    """按历史顺序构造 Julia 的 z 与 c。 / Build Julia z and c in historical order."""
    try:
        parameter = complex(c_real, c_imag)
    except Exception as error:
        return _external_failure(error)
    try:
        current = complex(x, y)
    except Exception as error:
        return _external_failure(error)
    return Ok((current, parameter))
