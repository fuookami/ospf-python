"""保留现有 Result 身份及原始错误上下文 / Preserve Result identity and error provenance."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python import _native


@dataclass(frozen=True, kw_only=True)
class FailureContext:
    """不可变的错误来源 / Immutable failure provenance.

    Attributes:
        source: 来源组件 / Source component.
        category: 语义分类，不是整数错误码 / Semantic category, not an integer code.
        rust_code: Rust 明确提供的原始码 / Original code when supplied by Rust.
        error_class: Rust 结构化分类 / Structured Rust classification.
        callback_result: 原样保留的回调失败或不支持结果 / Original callback failure or unsupported result.
        callback_exception: 原始外部异常，不转换成业务异常抛出 / Original external exception, not raised as a business exception.
        callback_index: 数组或候选回调的从零开始位置 / Zero-based array or candidate callback position.
    """

    source: str
    category: str
    rust_code: int | None
    error_class: str
    callback_result: Result[Any, Any, Any] | None = None
    callback_exception: Exception | None = None
    callback_index: int | None = None


# 复用三参数 sealed Result，不建立平行结果体系。 / Reuse the three-parameter sealed Result.
type BindingResult[T] = Result[T, str, ExErr[str, FailureContext]]


def invalid[T](message: str) -> BindingResult[T]:
    """创建边界输入失败 / Create an input-boundary failure.

    Args:
        message: 双语原因 / Bilingual reason.

    Returns:
        保留来源的 Failed / Failed with provenance.
    """
    return Failed(
        ExErr(
            _code=ErrorCode.ILLEGAL_ARGUMENT,
            _message=message,
            value=FailureContext(
                source="ospf-python",
                category="ILLEGAL_ARGUMENT",
                rust_code=None,
                error_class="BOUNDARY",
            ),
        )
    )


def _transport_failure[T](error: Exception) -> BindingResult[T]:
    """把 FFI 边界异常转换为现有结果 / Convert an FFI-boundary exception to the existing result.

    Args:
        error: PyO3 或输入适配产生的普通异常 / Ordinary exception from PyO3 or input adaptation.

    Returns:
        保留原始异常身份的失败 / Failure retaining the original exception identity.
    """
    # 保持既有转换失败类别，只补充原始异常来源。 / Preserve conversion-failure categories and add provenance only.
    code = ErrorCode.ILLEGAL_ARGUMENT
    return Failed(
        ExErr(
            _code=code,
            _message="绑定传输失败 / Binding transport failed",
            value=FailureContext(
                source="ospf-python-native",
                category=code.name,
                rust_code=None,
                error_class="FFI_TRANSPORT",
                callback_exception=error,
            ),
        )
    )


def invoke[T](
    operation: Callable[[], tuple[T | None, _native.Failure | None]],
) -> BindingResult[T]:
    """将 PyO3 传输映射为现有 Result / Map PyO3 transport to the existing Result.

    Args:
        operation: 单次 FFI 调用 / One FFI call.

    Returns:
        成功值或带原始来源的失败 / Value or failure with original provenance.
    """
    try:
        value, error = operation()
    except (OverflowError, TypeError, ValueError) as error:
        return _transport_failure(error)
    if error is None:
        # None 是成功的 unit 值，不是失败哨兵。 / None is a successful unit value, not a failure sentinel.
        return Ok(cast("T", value))
    code = ErrorCode.__members__.get(error.category, ErrorCode.APPLICATION_ERROR)
    return Failed(
        ExErr(
            _code=code,
            _message=error.message,
            value=FailureContext(
                source=error.source,
                category=error.category,
                rust_code=error.rust_code,
                error_class=error.error_class,
            ),
        )
    )


def unsupported[T](message: str) -> BindingResult[T]:
    """返回明确的不支持能力失败 / Return an explicit unsupported-capability failure.

    Args:
        message: 双语原因 / Bilingual reason.

    Returns:
        保留边界来源的 Failed / Failed retaining boundary provenance.
    """
    return Failed(
        ExErr(
            _code=ErrorCode.NOT_SUPPORTED,
            _message=message,
            value=FailureContext(
                source="ospf-python",
                category="NOT_SUPPORTED",
                rust_code=None,
                error_class="BOUNDARY",
            ),
        )
    )
