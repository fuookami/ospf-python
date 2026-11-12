"""完整初等运算符域、协议和固定 Rust 边界合同。 / Complete elementary-operator domain, protocol, and pinned-Rust boundary contracts."""

from __future__ import annotations

import gc
import math
import sys
import weakref
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from numbers import Real
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.operator.exp import exp2_op, exp10_op, exp_op
from ospf_python.math.operator.log import log2_op, log10_op, log_op
from ospf_python.math.operator.trigonometry import (
    acos_op,
    asin_op,
    atan_op,
    cos_op,
    sin_op,
    tan_op,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

Operation = Callable[[Any], Any]

OPERATIONS: tuple[tuple[str, Operation, Operation], ...] = (
    ("exp", exp_op, math.exp),
    ("exp2", exp2_op, math.exp2),
    ("exp10", exp10_op, lambda value: float(10.0**value)),
    ("ln", log_op, math.log),
    ("log2", log2_op, math.log2),
    ("log10", log10_op, math.log10),
    ("sin", sin_op, math.sin),
    ("cos", cos_op, math.cos),
    ("tan", tan_op, math.tan),
    ("asin", asin_op, math.asin),
    ("acos", acos_op, math.acos),
    ("atan", atan_op, math.atan),
)

VALUES = (
    ("negative-large", -(2**2000)),
    ("negative-one", -1),
    ("negative-zero", -0.0),
    ("zero", 0),
    ("subnormal", math.ulp(0.0)),
    ("quarter", 0.25),
    ("half", 0.5),
    ("one", 1),
    ("two", 2),
    ("eight", 8),
    ("pi", math.pi),
    ("huge-int", 1 << 4096),
    ("finite-max", sys.float_info.max),
    ("positive-inf", math.inf),
    ("negative-inf", -math.inf),
    ("nan", math.nan),
    ("decimal", Decimal("1.25")),
    ("fraction", Fraction(7, 3)),
    ("true", True),
    ("false", False),
)


@pytest.mark.parametrize(
    ("name", "operation", "reference"),
    OPERATIONS,
    ids=[name for name, _, _ in OPERATIONS],
)
@pytest.mark.parametrize(
    ("input_name", "value"), VALUES, ids=[name for name, _ in VALUES]
)
def test_complete_legacy_numeric_domain(
    *,
    name: str,
    operation: Operation,
    reference: Operation,
    input_name: str,
    value: Any,
) -> None:
    try:
        expected = reference(value)
    except TypeError:
        result = operation(value)
        assert isinstance(result, Failed), (name, input_name)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        return
    except OverflowError:
        result = operation(value)
        assert isinstance(result, Failed), (name, input_name)
        assert result.error.code is ErrorCode.OVERFLOW
        return
    except ValueError:
        result = operation(value)
        assert isinstance(result, Failed), (name, input_name)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        return

    result = operation(value)
    assert result.is_ok(), (name, input_name, result)
    actual = result.unwrap()
    assert type(actual) is float
    if math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert actual.hex() == expected.hex(), (name, input_name)


@pytest.mark.parametrize("bits", (53, 128, 1023, 1024, 2048, 4096, 8192))
@pytest.mark.parametrize(
    ("name", "operation"),
    tuple(
        (name, operation)
        for name, operation, _ in OPERATIONS
        if name in ("ln", "log2", "log10")
    ),
)
def test_arbitrary_width_integer_logarithms_are_not_truncated(
    *, name: str, operation: Operation, bits: int
) -> None:
    value = (1 << bits) + 123
    expected = math.log(value) if name == "ln" else getattr(math, name)(value)
    assert operation(value).unwrap() == pytest.approx(expected, rel=4e-15)


@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_integer_subclasses_follow_the_legacy_float_hook_split(
    *, name: str, operation: Operation
) -> None:
    class Integer(int):
        def __float__(self) -> float:
            raise RuntimeError("integer hook called")

        def __index__(self) -> int:
            pytest.fail(
                "真实整数不调用覆盖索引 / Actual integers bypass overridden index"
            )

    result = operation(Integer(8))
    if name in ("exp10", "ln", "log2", "log10"):
        assert result.is_ok()
        expected = (
            float(10.0**8)
            if name == "exp10"
            else math.log(8)
            if name == "ln"
            else getattr(math, name)(8)
        )
        assert result.unwrap() == expected
    else:
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.APPLICATION_ERROR
        assert isinstance(result.error.value.callback_exception, RuntimeError)


@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_each_call_collects_the_numeric_protocol_once(
    *, name: str, operation: Operation
) -> None:
    events: list[float] = []

    class Number:
        def __float__(self) -> float:
            events.append(0.5)
            return 0.5

    if name == "exp10":
        Real.register(Number)
    result = operation(Number())
    assert result.is_ok()
    assert events == [0.5]


@pytest.mark.parametrize(
    ("error_type", "code"),
    (
        (TypeError, ErrorCode.ILLEGAL_ARGUMENT),
        (ValueError, ErrorCode.APPLICATION_ERROR),
        (OverflowError, ErrorCode.OVERFLOW),
        (RuntimeError, ErrorCode.APPLICATION_ERROR),
        (MemoryError, ErrorCode.RESOURCE_EXHAUSTED),
    ),
)
@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_external_errors_preserve_instance_without_formatting(
    *,
    name: str,
    operation: Operation,
    error_type: type[Exception],
    code: ErrorCode,
) -> None:
    def forbid_format(owner: object) -> str:
        pytest.fail("不可格式化原异常 / Original exceptions must not be formatted")

    error: Exception = type("Error", (error_type,), {"__str__": forbid_format})()

    class Number:
        def __float__(self) -> float:
            raise error

    if name == "exp10":
        Real.register(Number)
    result = operation(Number())
    assert isinstance(result, Failed)
    assert result.error.code is code
    assert result.error.value.callback_exception is error
    assert error.__traceback__ is not None
    frames = []
    traceback = error.__traceback__
    while traceback is not None:
        frames.append(traceback.tb_frame.f_code.co_name)
        traceback = traceback.tb_next
    assert "__float__" in frames


@pytest.mark.parametrize("error", (KeyboardInterrupt(), SystemExit(), GeneratorExit()))
@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_base_exceptions_propagate_unchanged(
    *, name: str, operation: Operation, error: BaseException
) -> None:
    class Number:
        def __float__(self) -> float:
            raise error

    if name == "exp10":
        Real.register(Number)
    with pytest.raises(type(error)) as caught:
        operation(Number())
    assert caught.value is error


@pytest.mark.parametrize("value", ("0.5", b"0.5", None, complex(0.5), object()))
@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_nonnumeric_objects_are_rejected(
    *, name: str, operation: Operation, value: Any
) -> None:
    result = operation(value)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


def test_exp10_rejects_non_real_protocols_before_native(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def record(*, operation: str, value: object) -> Any:
        calls.append(value)
        pytest.fail("非Real输入不应进入原生边界 / Non-Real input must not reach native")

    monkeypatch.setattr(_native, "_elementary_operator", record)
    for value in (
        Decimal("0.5"),
        type("FloatOnly", (), {"__float__": lambda self: 0.5})(),
    ):
        result = exp10_op(value)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert calls == []


@pytest.mark.parametrize("kind", (np.int64, np.uint64, np.float32, np.float64))
@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_numpy_numeric_protocols_remain_supported(
    *, name: str, operation: Operation, kind: Any
) -> None:
    value = kind(2)
    result = operation(value)
    if name in ("asin", "acos"):
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    else:
        assert result.is_ok()


@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_each_natural_call_reaches_pinned_native_boundary(
    *, name: str, operation: Operation, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _native._elementary_operator
    calls: list[tuple[str, object]] = []

    # 边界签名是「位置或关键字」（B263），所以这里两种传法都要接住；
    # 转发时仍用关键字，因为仓库里装着的扩展是 11-09 的构建，只接受 `(*, ...)`。
    # The boundary is positional-or-keyword (B263), so accept both; forward by keyword because the
    # extension installed in the repo is the 11-09 build, which only accepts `(*, ...)`.
    def record(operation: str, value: object) -> Any:
        calls.append((operation, value))
        return original(operation=operation, value=value)

    monkeypatch.setattr(_native, "_elementary_operator", record)
    for _ in range(3):
        assert operation(0.5).is_ok()
    assert calls == [(name, 0.5)] * 3


def test_unknown_native_operation_is_structured_failure() -> None:
    value, failure = _native._elementary_operator(operation="unknown", value=1)
    assert value is None
    assert failure is not None
    assert failure.category == "ILLEGAL_ARGUMENT"


@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_success_releases_input_objects_and_allows_reentry(
    *, name: str, operation: Operation
) -> None:
    class Number:
        def __float__(self) -> float:
            assert operation(0.5).is_ok()
            return 0.5

    if name == "exp10":
        Real.register(Number)
    value = Number()
    reference = weakref.ref(value)
    assert operation(value).is_ok()
    del value
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize(
    ("name", "operation"),
    tuple((name, operation) for name, operation, _ in OPERATIONS),
)
def test_detached_calls_can_share_threads(*, name: str, operation: Operation) -> None:
    values = (
        [0.25, 0.5, 0.75, 1.0] * 4
        if name in ("asin", "acos")
        else [0.25, 0.5, 1.0, 2.0] * 4
    )
    with ThreadPoolExecutor(max_workers=4) as executor:
        outputs = list(executor.map(lambda value: operation(value).unwrap(), values))
    assert len(outputs) == len(values)
    assert all(type(output) is float for output in outputs)
