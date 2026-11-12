"""完整自然对数域和协议迁移合同。 / Complete natural logarithm domain and protocol migration contracts."""

from __future__ import annotations

import gc
import itertools
import math
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding import logarithm as adapter
from ospf_python.math.ordinary.log import log_base
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

VALUES = (
    ("negative", -1.0),
    ("negative-zero", -0.0),
    ("zero", 0),
    ("one", 1),
    ("two", 2),
    ("subnormal", math.ulp(0.0)),
    ("below-one", math.nextafter(1.0, 0.0)),
    ("above-one", math.nextafter(1.0, 2.0)),
    ("finite-max", sys.float_info.max),
    ("wide-integer", (1 << 4096) + 123),
    ("decimal", Decimal("1.25")),
    ("fraction", Fraction(7, 3)),
    ("positive-infinity", math.inf),
    ("negative-infinity", -math.inf),
    ("nan", math.nan),
    ("true", True),
    ("false", False),
)


@pytest.mark.parametrize(
    ("x", "base"),
    [(x, base) for (_, x), (_, base) in itertools.product(VALUES, repeat=2)],
    ids=[f"{x}-{base}" for (x, _), (base, _) in itertools.product(VALUES, repeat=2)],
)
def test_complete_legacy_numeric_domain(*, x: Any, base: Any) -> None:
    try:
        expected = math.log(x) / math.log(base)
    except (ValueError, ZeroDivisionError):
        result = log_base(x, base)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert result.error.value.source == "ospf-python-native"
        return
    result = log_base(x, base)
    assert result.is_ok()
    actual = result.unwrap()
    assert type(actual) is float
    if math.isnan(expected):
        assert math.isnan(actual)
    elif math.isinf(expected) or expected == 0.0:
        assert actual.hex() == expected.hex()
    else:
        assert math.isclose(actual, expected, rel_tol=4e-15, abs_tol=0.0)


@pytest.mark.parametrize("bits", (53, 128, 1023, 1024, 2048, 8192))
def test_arbitrary_width_integers_are_not_truncated(bits: int) -> None:
    value = (1 << bits) + 123
    assert log_base(value, 2).unwrap() == pytest.approx(math.log(value) / math.log(2))
    assert log_base(2, value).unwrap() == pytest.approx(math.log(2) / math.log(value))


def test_integer_subclasses_bypass_overridden_numeric_hooks() -> None:
    class Integer(int):
        def __float__(self) -> float:
            pytest.fail(
                "真实整数不调用覆盖转换 / Actual integers bypass overridden conversion"
            )

        def __index__(self) -> int:
            pytest.fail(
                "真实整数不调用覆盖索引 / Actual integers bypass overridden index"
            )

    assert log_base(Integer(1 << 2048), Integer(2)).unwrap() == pytest.approx(2048)


@pytest.mark.parametrize("x_valid", (True, False))
@pytest.mark.parametrize("protocol", ("float", "index"))
def test_protocol_order_and_invalid_x_short_circuit(
    *, x_valid: bool, protocol: str
) -> None:
    events: list[str] = []

    class Number:
        def __init__(self, name: str) -> None:
            self.name = name

    def convert(value: Number) -> Any:
        events.append(value.name)
        return (8 if x_valid else -1) if value.name == "x" else 2

    if protocol == "float":
        kind = type(
            "Float", (Number,), {"__float__": lambda value: float(convert(value))}
        )
    else:
        kind = type("Index", (Number,), {"__index__": convert})
    result = log_base(kind("x"), kind("base"))
    assert events == (["x", "base"] if x_valid else ["x"])
    assert result.is_ok() is x_valid
    if x_valid:
        assert result.unwrap() == 3.0


@pytest.mark.parametrize("position", ("x", "base"))
@pytest.mark.parametrize(
    ("error_type", "code"),
    (
        (TypeError, ErrorCode.ILLEGAL_ARGUMENT),
        (ValueError, ErrorCode.APPLICATION_ERROR),
        (OverflowError, ErrorCode.APPLICATION_ERROR),
        (RuntimeError, ErrorCode.APPLICATION_ERROR),
        (MemoryError, ErrorCode.RESOURCE_EXHAUSTED),
    ),
)
def test_external_errors_preserve_instance_without_formatting(
    *, position: str, error_type: type[Exception], code: ErrorCode
) -> None:
    def forbid_format(owner: object) -> str:
        pytest.fail("不可格式化原异常 / Original exceptions must not be formatted")

    error: Exception = type("Error", (error_type,), {"__str__": forbid_format})()

    class Number:
        def __float__(self) -> float:
            raise error

    result = log_base(Number(), 2) if position == "x" else log_base(8, Number())
    assert isinstance(result, Failed) and result.error.code is code
    assert result.error.value.callback_exception is error
    assert error.__traceback__ is not None
    frames = []
    traceback = error.__traceback__
    while traceback is not None:
        frames.append(traceback.tb_frame.f_code.co_name)
        traceback = traceback.tb_next
    assert "__float__" in frames


@pytest.mark.parametrize("error", (KeyboardInterrupt(), SystemExit(), GeneratorExit()))
@pytest.mark.parametrize("position", ("x", "base"))
def test_base_exceptions_propagate_unchanged(
    *, error: BaseException, position: str
) -> None:
    class Number:
        def __float__(self) -> float:
            raise error

    with pytest.raises(type(error)) as caught:
        if position == "x":
            log_base(Number(), 2)
        else:
            log_base(8, Number())
    assert caught.value is error


@pytest.mark.parametrize("value", ("8", b"8", None, complex(8), object()))
@pytest.mark.parametrize("position", ("x", "base"))
def test_nonnumeric_objects_are_not_accepted_by_float_coercion(
    *, value: Any, position: str
) -> None:
    result = log_base(value, 2) if position == "x" else log_base(8, value)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    assert isinstance(result.error.value.callback_exception, TypeError)


@pytest.mark.parametrize("kind", (np.int64, np.uint64, np.float32, np.float64))
def test_numpy_numeric_protocols_remain_supported(kind: Any) -> None:
    assert log_base(kind(8), kind(2)).unwrap() == pytest.approx(3)


def test_each_natural_call_reaches_pinned_native_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _native._log_base
    calls: list[tuple[object, object]] = []

    def record(*, x: object, base: object) -> Any:
        calls.append((x, base))
        return original(x=x, base=base)

    monkeypatch.setattr(_native, "_log_base", record)
    for _ in range(4):
        assert log_base(8, 2).unwrap() == 3
    assert calls == [(8, 2)] * 4
    assert vars(adapter)["_native"] is _native


def test_success_releases_input_objects_and_allows_reentry() -> None:
    class Number:
        def __float__(self) -> float:
            assert log_base(8, 2).unwrap() == 3
            return 8.0

    value = Number()
    reference = weakref.ref(value)
    assert log_base(value, 2).unwrap() == 3
    del value
    gc.collect()
    assert reference() is None


def test_detached_numeric_calls_can_share_threads() -> None:
    def compute(bits: int) -> float:
        return log_base(1 << bits, 2).unwrap()

    widths = [128, 1024, 2048] * 4
    with ThreadPoolExecutor(max_workers=4) as executor:
        outputs = list(executor.map(compute, widths))
    assert outputs == pytest.approx(widths)
