"""原生失败到既有 Result 的结构化映射合同 / Structured native-failure mapping to existing Result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ospf_python._binding.result import FailureContext, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok


@dataclass(frozen=True)
class _Failure:
    """模拟 PyO3 Failure 的只读字段 / Read-only fields mimicking a PyO3 Failure."""

    category: str
    source: str
    rust_code: int | None
    error_class: str
    message: str


@pytest.mark.parametrize(
    ("category", "code"),
    [
        ("ILLEGAL_ARGUMENT", ErrorCode.ILLEGAL_ARGUMENT),
        ("OUT_OF_RANGE", ErrorCode.OUT_OF_RANGE),
        ("MODEL_BUILD_FAILED", ErrorCode.MODEL_BUILD_FAILED),
        ("SOLVER_NOT_AVAILABLE", ErrorCode.SOLVER_NOT_AVAILABLE),
        ("DATA_LOSS", ErrorCode.DATA_LOSS),
    ],
)
def test_known_native_categories_map_by_name_and_retain_provenance(
    category: str,
    code: ErrorCode,
) -> None:
    failure = _Failure(
        category=category,
        source="ospf-rust-core",
        rust_code=0x34,
        error_class="INPUT",
        message="原始失败 / Original failure",
    )

    result = invoke(lambda: (None, failure))

    assert isinstance(result, Failed)
    assert isinstance(result.error, ExErr)
    assert result.error.code is code
    assert result.error.message == failure.message
    assert result.error.value == FailureContext(
        source=failure.source,
        category=failure.category,
        rust_code=failure.rust_code,
        error_class=failure.error_class,
    )
    assert code.value != failure.rust_code


def test_unknown_native_category_falls_back_without_losing_original_data() -> None:
    failure = _Failure(
        category="FUTURE_CATEGORY",
        source="future-native",
        rust_code=0xFE,
        error_class="FUTURE_CLASS",
        message="未来失败 / Future failure",
    )

    result = invoke(lambda: (None, failure))

    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    assert result.error.value.category == "FUTURE_CATEGORY"
    assert result.error.value.source == "future-native"
    assert result.error.value.rust_code == 0xFE
    assert result.error.value.error_class == "FUTURE_CLASS"


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (TypeError("type"), ErrorCode.ILLEGAL_ARGUMENT),
        (ValueError("value"), ErrorCode.ILLEGAL_ARGUMENT),
        (OverflowError("overflow"), ErrorCode.ILLEGAL_ARGUMENT),
    ],
)
def test_ffi_exceptions_become_results_with_original_identity(
    error: Exception,
    code: ErrorCode,
) -> None:
    def operation() -> tuple[None, Any]:
        raise error

    result = invoke(operation)

    assert isinstance(result, Failed)
    assert result.error.code is code
    assert result.error.value.source == "ospf-python-native"
    assert result.error.value.category == code.name
    assert result.error.value.rust_code is None
    assert result.error.value.error_class == "FFI_TRANSPORT"
    assert result.error.value.callback_exception is error
    assert "Binding transport failed" in result.error.message


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit()])
def test_base_exceptions_are_not_swallowed(
    error: BaseException,
) -> None:
    def operation() -> tuple[None, Any]:
        raise error

    with pytest.raises(type(error)) as caught:
        invoke(operation)

    assert caught.value is error


def test_unrelated_runtime_exceptions_are_not_reclassified() -> None:
    error = RuntimeError("callback")

    def operation() -> tuple[None, Any]:
        raise error

    with pytest.raises(RuntimeError) as caught:
        invoke(operation)

    assert caught.value is error


def test_memory_errors_are_not_reclassified_by_the_generic_adapter() -> None:
    error = MemoryError("memory")

    def operation() -> tuple[None, Any]:
        raise error

    with pytest.raises(MemoryError) as caught:
        invoke(operation)

    assert caught.value is error


def test_conversion_failure_never_formats_the_original_exception() -> None:
    class Unformattable(ValueError):
        def __str__(self) -> str:
            pytest.fail("must not format the original exception")

    error = Unformattable("original")

    def operation() -> tuple[None, Any]:
        raise error

    result = invoke(operation)

    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert result.error.value.callback_exception is error


def test_none_is_a_successful_unit_value_not_a_failure_sentinel() -> None:
    result = invoke(lambda: (None, None))

    assert isinstance(result, Ok)
    assert result.value is None
