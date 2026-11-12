"""公开 clamp 的原生排序、数值协议与 Result 合同。 / Native ordering, numeric protocols, and Result contracts for public clamp."""

from __future__ import annotations

import gc
import importlib
import math
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.ordinary.clamp import clamp
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.parametrize(
    ("value", "lower", "upper"),
    [
        (5, 0, 10),
        (-(1 << 4096), -(1 << 1024), 1 << 1024),
        (1 << 4096, -(1 << 1024), 1 << 1024),
        (Fraction(1, 3), Fraction(-1), Fraction(1, 2)),
        (Decimal("0.2"), Decimal("0.1"), Decimal("0.3")),
        (np.int64(3), np.int64(2), np.int64(4)),
        (0.0, -0.0, 0.0),
        (-0.0, 0.0, -0.0),
        (math.nan, 0.0, 1.0),
        (0.5, math.nan, 1.0),
        (0.5, 0.0, math.nan),
        (math.inf, -math.inf, 1.0),
        (5, 8, 2),
    ],
)
def test_python_ordering_and_selected_identity(
    *, value: Any, lower: Any, upper: Any
) -> None:
    expected = max(lower, min(value, upper))
    result = clamp(value, min_val=lower, max_val=upper)
    assert isinstance(result, Ok)
    assert result.unwrap() is expected


def test_comparison_order_and_truth_conversion_match_python() -> None:
    events: list[tuple[str, str, str]] = []

    class Truth:
        def __init__(self, name: str, value: bool) -> None:
            self.name, self.value = name, value

        def __bool__(self) -> bool:
            events.append((self.name, "bool", str(self.value)))
            return self.value

    class Operand:
        def __init__(self, name: str, number: int) -> None:
            self.name, self.number = name, number

        def __lt__(self, other: Any) -> Truth:
            events.append((self.name, "lt", other.name))
            return Truth(self.name, self.number < other.number)

        def __gt__(self, other: Any) -> Truth:
            events.append((self.name, "gt", other.name))
            return Truth(self.name, self.number > other.number)

    value, lower, upper = Operand("value", 5), Operand("lower", 0), Operand("upper", 4)
    expected = max(lower, min(value, upper))
    expected_events = events[:]
    events.clear()
    assert clamp(value, min_val=lower, max_val=upper).unwrap() is expected
    assert (
        events
        == expected_events
        == [
            ("upper", "lt", "value"),
            ("upper", "bool", "True"),
            ("upper", "gt", "lower"),
            ("upper", "bool", "True"),
        ]
    )


def test_reflected_comparisons_and_not_implemented_match_python() -> None:
    events: list[str] = []

    class Value:
        def __gt__(self, other: object) -> Any:
            events.append("value gt")
            return False if other is upper else NotImplemented

    class Bound:
        def __lt__(self, other: object) -> Any:
            events.append("bound lt")
            return NotImplemented

        def __gt__(self, other: object) -> Any:
            events.append("bound gt")
            return NotImplemented

    class Lower:
        def __lt__(self, other: object) -> bool:
            events.append("lower reflected lt")
            return True

    value, lower, upper = Value(), Lower(), Bound()
    expected = max(lower, min(value, upper))
    expected_events = events[:]
    events.clear()
    assert clamp(value, min_val=lower, max_val=upper).unwrap() is expected
    assert (
        events
        == expected_events
        == ["bound lt", "value gt", "value gt", "lower reflected lt"]
    )


@pytest.mark.parametrize("stage", ["min", "max"])
@pytest.mark.parametrize(
    "error_type", [TypeError, ValueError, OverflowError, MemoryError, RuntimeError]
)
def test_comparison_errors_are_result_data_without_losing_identity(
    *, stage: str, error_type: type[Exception]
) -> None:
    failure = error_type("original")
    events: list[str] = []

    class Operand:
        def __init__(self, name: str) -> None:
            self.name = name

        def __lt__(self, other: object) -> bool:
            events.append("min")
            if stage == "min":
                raise failure
            return False

        def __gt__(self, other: object) -> bool:
            events.append("max")
            if stage == "max":
                raise failure
            return True

    result = clamp(Operand("value"), min_val=Operand("lower"), max_val=Operand("upper"))
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is failure
    assert failure.__traceback__ is not None
    assert events == (["min"] if stage == "min" else ["min", "max"])
    expected = (
        ErrorCode.RESOURCE_EXHAUSTED
        if error_type is MemoryError
        else ErrorCode.OVERFLOW
        if error_type is OverflowError
        else ErrorCode.ILLEGAL_ARGUMENT
        if error_type in (TypeError, ValueError)
        else ErrorCode.APPLICATION_ERROR
    )
    assert result.error.code is expected


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_base_exceptions_propagate_by_identity(error_type: type[BaseException]) -> None:
    failure = error_type("original")

    class Upper:
        def __lt__(self, other: object) -> bool:
            raise failure

    with pytest.raises(error_type) as caught:
        clamp(object(), min_val=object(), max_val=Upper())
    assert caught.value is failure


def test_result_from_custom_comparison_is_truth_tested() -> None:
    failure = ValueError("comparison truth")

    class Truth:
        def __bool__(self) -> bool:
            raise failure

    class Upper:
        def __lt__(self, other: object) -> Truth:
            return Truth()

    result = clamp(object(), min_val=object(), max_val=Upper())
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is failure


def test_dynamic_min_max_hooks_are_called_in_original_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("ospf_python.math.ordinary.clamp")
    events: list[tuple[str, object, object]] = []
    value, lower, upper, inner, output = [object() for _ in range(5)]

    def maximum(left: object, right: object) -> object:
        events.append(("max", left, right))
        return output

    def replacement(left: object, right: object) -> object:
        pytest.fail("max must be captured before the min callback")

    def minimum(left: object, right: object) -> object:
        events.append(("min", left, right))
        monkeypatch.setattr(module, "max", replacement)
        return inner

    monkeypatch.setattr(module, "max", maximum, raising=False)
    monkeypatch.setattr(module, "min", minimum, raising=False)
    assert clamp(value, min_val=lower, max_val=upper).unwrap() is output
    assert events == [("min", value, upper), ("max", lower, inner)]


@pytest.mark.parametrize("failed", [False, True])
def test_result_returned_by_hook_remains_a_success_value(
    *, failed: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("ospf_python.math.ordinary.clamp")
    data: Any = (
        Failed(Err(_code=ErrorCode.APPLICATION_ERROR, _message="data"))
        if failed
        else Ok("inner result")
    )
    monkeypatch.setattr(module, "min", lambda left, right: data, raising=False)
    monkeypatch.setattr(module, "max", lambda left, right: right, raising=False)
    result = clamp(object(), min_val=object(), max_val=object())
    assert isinstance(result, Ok)
    assert result.unwrap() is data


def test_none_returned_by_hook_is_a_success_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("ospf_python.math.ordinary.clamp")
    monkeypatch.setattr(module, "min", lambda left, right: None, raising=False)
    monkeypatch.setattr(module, "max", lambda left, right: right, raising=False)
    result = clamp(object(), min_val=object(), max_val=object())
    assert isinstance(result, Ok)
    assert result.unwrap() is None


@pytest.mark.parametrize("stage", ["min", "max"])
def test_hook_exception_is_preserved_and_short_circuits(
    *, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("ospf_python.math.ordinary.clamp")
    failure = RuntimeError("original hook exception")
    events: list[str] = []

    def hook(name: str) -> Any:
        def invoke(left: object, right: object) -> None:
            events.append(name)
            if name == stage:
                raise failure

        return invoke

    monkeypatch.setattr(module, "min", hook("min"), raising=False)
    monkeypatch.setattr(module, "max", hook("max"), raising=False)
    result = clamp(object(), min_val=object(), max_val=object())
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is failure
    assert failure.__traceback__ is not None
    assert events == (["min"] if stage == "min" else ["min", "max"])


def test_builtins_replaced_before_import_and_then_restored() -> None:
    code = """
import builtins
import os
import sys
directories = []
if os.name == "nt":
    directories = [os.add_dll_directory(path) for path in
                   os.environ.get("OSPF_NATIVE_DLL_DIRS", "").split(os.pathsep) if path]
sys.path.insert(0, sys.argv[1])
original_min, original_max = builtins.min, builtins.max
events = []
active = False
def custom_min(*args, **kwargs):
    if active:
        events.append("min")
    return original_min(*args, **kwargs)
def custom_max(*args, **kwargs):
    if active:
        events.append("max")
    return original_max(*args, **kwargs)
builtins.min, builtins.max = custom_min, custom_max
from ospf_python.math.ordinary.clamp import clamp
active = True
assert clamp(5, min_val=0, max_val=3).unwrap() == 3
assert events == ["min", "max"]
builtins.min, builtins.max = original_min, original_max
assert clamp(5, min_val=0, max_val=3).unwrap() == 3
assert events == ["min", "max"]
"""
    package_root = str(Path(_native.__file__).resolve().parent.parent)
    process = subprocess.run(
        [sys.executable, "-I", "-c", code, package_root],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr


def test_reentrant_comparison_and_concurrent_calls() -> None:
    class Upper:
        def __lt__(self, other: object) -> bool:
            assert clamp(9, min_val=0, max_val=5).unwrap() == 5
            return False

    value: Any = 3
    assert clamp(value, min_val=0, max_val=Upper()).unwrap() == 3
    values = list(range(-20, 21))
    with ThreadPoolExecutor(max_workers=4) as pool:
        actual = list(pool.map(lambda item: clamp(item, min_val=0, max_val=10), values))
    assert [item.unwrap() for item in actual] == [
        max(0, min(item, 10)) for item in values
    ]


def test_success_does_not_retain_unselected_values() -> None:
    class Item:
        def __init__(self, number: int) -> None:
            self.number = number

        def __lt__(self, other: Item) -> bool:
            return self.number < other.number

        def __gt__(self, other: Item) -> bool:
            return self.number > other.number

    value, lower, upper = Item(5), Item(0), Item(10)
    references = weakref.ref(lower), weakref.ref(upper)
    result = clamp(value, min_val=lower, max_val=upper)
    del lower, upper
    gc.collect()
    assert result.unwrap() is value
    assert all(reference() is None for reference in references)


def test_public_entry_uses_both_native_pair_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[object, object, bool]] = []
    value, lower, upper, inner, output = [object() for _ in range(5)]

    def replacement(
        *, left: object, right: object, callable: object, minimum: bool, ops: object
    ) -> object:
        events.append((left, right, minimum))
        return inner if minimum else output

    monkeypatch.setattr(_native, "_minmax_pair", replacement, raising=False)
    assert clamp(value, min_val=lower, max_val=upper).unwrap() is output
    assert events == [(value, upper, True), (lower, inner, False)]
