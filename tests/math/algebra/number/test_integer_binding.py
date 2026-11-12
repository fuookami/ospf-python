"""公开整数默认绑定与扩展协议。 / Public default integer bindings and extension protocols."""

from __future__ import annotations

import gc
import importlib
import operator
import sys
import weakref
from typing import Any

import pytest

from ospf_python import _native
from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger

_TYPES = (Integer, UInteger, NumericInteger, NumericUInteger)


@pytest.mark.parametrize("cls", _TYPES)
def test_public_default_arithmetic_and_comparison_delegate_to_native(
    *, cls: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(cls.__module__)
    engine = module._integer
    calls: list[str] = []
    clamps: list[str] = []

    class Proxy:
        def __getattr__(self, name: str) -> Any:
            original = getattr(engine, name)

            def invoke(*args: Any, **kwargs: Any) -> Any:
                calls.append(name)
                return original(*args, **kwargs)

            return invoke

    left, right = cls(7), cls(3)
    monkeypatch.setattr(module, "_integer", Proxy())
    if cls is NumericInteger:

        def minimum(left: Any, right: Any) -> Any:
            clamps.append("min")
            return min(left, right)

        def maximum(left: Any, right: Any) -> Any:
            clamps.append("max")
            return max(left, right)

        monkeypatch.setattr(module, "min", minimum, raising=False)
        monkeypatch.setattr(module, "max", maximum, raising=False)
    result = left.safe_add(right) if cls is NumericInteger else left + right
    assert (
        result.value == 10
        and ("bounded_add" if cls is NumericInteger else "add") in calls
    )
    assert operator.eq(left, right) is False and "equal" in calls
    if cls is NumericInteger:
        assert (
            calls.count("bounded_add")
            == calls.count("clamp_result")
            == calls.count("clamp_owner")
            == 1
        )
        assert clamps == ["min", "max", "min", "max"]
    assert list(left.__dict__) == (
        ["_value"] if cls in (NumericInteger, NumericUInteger) else ["value"]
    )


@pytest.mark.parametrize("cls", _TYPES)
def test_no_silent_python_arithmetic_fallback_after_native_failure(
    *, cls: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    error = RuntimeError("原生边界诊断 / Native boundary diagnostic")
    left, right = cls(7), cls(3)
    module = importlib.import_module(cls.__module__)

    class Broken:
        def add(self, **kwargs: Any) -> Any:
            raise error

        bounded_add = add

    monkeypatch.setattr(module, "_integer", Broken())
    with pytest.raises(RuntimeError) as caught:
        left.safe_add(right) if cls is NumericInteger else left + right
    assert caught.value is error


@pytest.mark.parametrize("cls", (Integer, UInteger, NumericUInteger))
@pytest.mark.parametrize("operation", (operator.add, operator.mul))
def test_native_public_arbitrary_precision_bridge_avoids_decimal_conversion(
    *, cls: Any, operation: Any
) -> None:
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        value = 1 << 100000
        assert operation(cls(value), cls(3)).value == operation(value, 3)
    finally:
        sys.set_int_max_str_digits(previous)


@pytest.mark.parametrize("cls", _TYPES)
def test_reflected_int_subclass_arithmetic_keeps_priority_over_builtin_left(
    cls: Any,
) -> None:
    calls: list[int] = []

    class Reflected(int):
        def __radd__(self, left: int) -> int:
            calls.append(left)
            return 29

        def __index__(self) -> int:
            pytest.fail("不能抽取外部整数 / External integers must not be extracted")

    left, right = cls(7), cls(Reflected(3))
    result = left.safe_add(right) if cls is NumericInteger else left + right
    assert result.value == 29 and calls == [7]


@pytest.mark.parametrize(
    "operation", ("__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__")
)
def test_external_rich_comparison_result_is_not_forced_to_bool(operation: str) -> None:
    marker = object()
    calls: list[Any] = []

    def compare(self: Any, right: Any) -> Any:
        calls.append(right)
        return marker

    value_type = type("ExternalComparison", (), {operation: compare})
    left, right = Integer(7), Integer(3)
    object.__setattr__(left, "value", value_type())
    assert getattr(Integer, operation)(left, right) is marker and calls == [3]


@pytest.mark.parametrize("stage", ("min", "max"))
@pytest.mark.parametrize(
    "error_type",
    (ValueError, RuntimeError, KeyboardInterrupt, SystemExit, GeneratorExit),
)
def test_external_clamp_failure_keeps_exception_traceback_and_handled_state(
    *, stage: str, error_type: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(NumericInteger.__module__)
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = RuntimeError()
    calls: list[str] = []

    def failing(left: Any, right: Any) -> Any:
        assert sys.exception() is outer
        calls.append(stage)
        raise error

    monkeypatch.setattr(module, stage, failing, raising=False)
    try:
        raise outer
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            NumericInteger(7)
        assert caught.value is error and sys.exception() is outer
    assert calls == [stage]
    nodes = []
    node = error.__traceback__
    while node is not None:
        nodes.append(node)
        node = node.tb_next
    assert any(node is original for node in nodes)


def test_clamp_external_callables_and_owners_are_not_retained_by_native_engine() -> (
    None
):
    class Owner:
        pass

    owner = Owner()
    reference = weakref.ref(owner)

    def minimum(*, held: Any) -> Any:
        def invoke(left: Any, right: Any) -> Any:
            assert held is not None
            return min(left, right)

        return invoke

    callback = minimum(held=owner)
    assert (
        _native._public_integer.clamp(
            maximum=max, lower=0, minimum=callback, upper=9, value=7
        )
        == 7
    )
    del owner, callback
    gc.collect()
    assert reference() is None and gc.is_tracked(_native._public_integer)


def test_native_clamp_keeps_tie_object_identity_and_legacy_reversed_bounds() -> None:
    # 用 10000 而非 1000：CPython 3.15 把小整数缓存上界从 256 扩到至少 1000，
    # 两次 int("1000") 会返回同一对象，前置条件「upper 与 value 是不同对象」无法成立。
    # 10000 在两个版本上都不被缓存，前置条件与断言意图均不变。
    # Use 10000: CPython 3.15 caches small ints up to at least 1000, so int("1000") twice
    # yields the same object; 10000 is uncached on both versions, keeping the precondition.
    lower = int("-1000")
    upper = int("10000")
    value = int("10000")
    assert upper is not value
    assert (
        _native._public_integer.clamp(
            maximum=max, lower=lower, minimum=min, upper=upper, value=value
        )
        is upper
    )
    assert (
        _native._public_integer.maximum(callable=max, left=value, right=upper) is value
    )
    assert (
        _native._public_integer.clamp(
            maximum=max, lower=9, minimum=min, upper=2, value=7
        )
        == 9
    )
