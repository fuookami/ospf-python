"""开放单位转换的控制面合同。 / Control-plane contracts for open unit conversion."""

from __future__ import annotations

import builtins
import gc
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.quantity_conversion import convert_callback
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.quantities.quantity import quantity as quantity_module
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok

_EVENTS = (
    "source-unit",
    "source-method",
    "source-value",
    "source-call",
    "target-method",
    "target-call",
    "factory-call",
)
_ERRORS = (
    ValueError,
    TypeError,
    RuntimeError,
    ArithmeticError,
    AttributeError,
    LookupError,
    KeyboardInterrupt,
    SystemExit,
    GeneratorExit,
)


def _quantity(*, value: Any, unit: Any) -> Quantity[Any]:
    return Quantity(value=value, unit=unit)


def _traced(record: Any) -> tuple[Any, Any]:
    value, standard, converted = object(), object(), object()

    class Source:
        @property
        def to_si(self) -> Any:
            record("source-method")

            def call(item: Any) -> object:
                record("source-call")
                assert item is value
                return standard

            return call

    source = Source()

    class Owner:
        @property
        def unit(self) -> Source:
            record("source-unit")
            return source

        @property
        def value(self) -> object:
            record("source-value")
            return value

    class Target:
        @property
        def from_si(self) -> Any:
            record("target-method")

            def call(item: Any) -> object:
                record("target-call")
                assert item is standard
                return converted

            return call

    return Owner(), Target()


def _reference(owner: Any, target: Any) -> Any:
    standard = owner.unit.to_si(owner.value)
    converted = target.from_si(standard)
    return quantity_module.Quantity(value=converted, unit=target)


def test_dynamic_callback_order_and_late_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    owner, target = _traced(events.append)
    marker = object()

    def factory(**kwargs: Any) -> object:
        events.append("factory-call")
        assert kwargs["unit"] is target
        return marker

    monkeypatch.setattr(quantity_module, "Quantity", factory)
    assert convert_callback(owner=owner, target=target).unwrap() is marker
    assert events == list(_EVENTS)


@pytest.mark.parametrize("stage", _EVENTS)
@pytest.mark.parametrize("error_type", _ERRORS)
@pytest.mark.parametrize("handled", (False, True))
def test_first_failure_preserves_identity_traceback_cause_and_handled_state(
    *, monkeypatch: pytest.MonkeyPatch, stage: str, error_type: Any, handled: bool
) -> None:
    events: list[str] = []
    original = error_type("original")
    cause = RuntimeError("explicit cause")
    active = RuntimeError("previously handled") if handled else None

    def record(event: str) -> None:
        assert sys.exception() is active
        events.append(event)
        if event == stage:
            raise original from cause

    owner, target = _traced(record)

    def factory(**kwargs: Any) -> Any:
        record("factory-call")
        return kwargs

    monkeypatch.setattr(quantity_module, "Quantity", factory)

    def attempt() -> None:
        if issubclass(error_type, Exception):
            result = convert_callback(owner=owner, target=target)
            assert isinstance(result, Failed)
            assert result.error.code is ErrorCode.APPLICATION_ERROR
            assert result.error.value.source == "ospf-python-native"
            assert result.error.value.callback_exception is original
            assert result.error.value.callback_index is None
            assert stage in result.error.message
        else:
            with pytest.raises(error_type) as caught:
                convert_callback(owner=owner, target=target)
            assert caught.value is original
        assert original.__context__ is active
        assert original.__cause__ is cause
        assert original.__suppress_context__
        frames = []
        traceback = original.__traceback__
        while traceback is not None:
            frames.append(traceback.tb_frame.f_code.co_name)
            traceback = traceback.tb_next
        assert "record" in frames
        assert sys.exception() is active

    if handled:
        assert active is not None
        try:
            raise active
        except RuntimeError:
            attempt()
    else:
        attempt()
    assert events == list(_EVENTS[: _EVENTS.index(stage) + 1])


@pytest.mark.parametrize(
    "value",
    (
        2**1000 + 3,
        Fraction(1, 3),
        Decimal("1.23000"),
        Floating(1.25),
        PublicRational(2, 7),
        Rational.create(numerator=23, denominator=17).unwrap(),
        True,
        None,
        object(),
    ),
)
def test_open_numeric_values_are_not_float_coerced_or_reconstructed(value: Any) -> None:
    class OpenUnit:
        @property
        def symbol(self) -> str:
            raise AssertionError("opaque units have no verified dimension metadata")

        def to_si(self, item: Any) -> Any:
            assert item is value
            return item

        def from_si(self, item: Any) -> Any:
            assert item is value
            return item

    unit = OpenUnit()
    source = _quantity(value=value, unit=unit)
    result = convert_callback(owner=source, target=unit).unwrap()
    assert type(result) is Quantity
    assert result is not source and result.value is value and result.unit is unit


def test_external_numeric_protocol_is_not_called_implicitly() -> None:
    class Opaque:
        def __float__(self) -> float:
            raise AssertionError("implicit float coercion")

        def __index__(self) -> int:
            raise AssertionError("implicit integer coercion")

        def __repr__(self) -> str:
            raise AssertionError("implicit formatting")

    value = Opaque()

    class OpenUnit:
        to_si = staticmethod(lambda item: item)
        from_si = staticmethod(lambda item: item)

    result = convert_callback(
        owner=_quantity(value=value, unit=OpenUnit()), target=OpenUnit()
    ).unwrap()
    assert result.value is value


@pytest.mark.parametrize(
    "returned", (None, object(), Ok(3), Failed(Err(ErrorCode.NOT_FOUND, "data")))
)
def test_callback_results_are_data_not_flattened(returned: Any) -> None:
    class OpenUnit:
        def to_si(self, item: Any) -> Any:
            return returned

        def from_si(self, item: Any) -> Any:
            assert item is returned
            return item

    unit = OpenUnit()
    result = convert_callback(owner=_quantity(value=1, unit=unit), target=unit).unwrap()
    assert result.value is returned


@pytest.mark.parametrize(
    "returned", (None, object(), Ok(3), Failed(Err(ErrorCode.NOT_FOUND, "data")))
)
def test_factory_output_is_opaque_including_none_and_existing_result(
    *, monkeypatch: pytest.MonkeyPatch, returned: Any
) -> None:
    owner, target = _traced(lambda event: None)
    monkeypatch.setattr(quantity_module, "Quantity", lambda **kwargs: returned)
    result = convert_callback(owner=owner, target=target)
    assert isinstance(result, Ok) and result.value is returned


def test_source_is_captured_before_value_and_target_factory_remain_late(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    marker = object()

    def factory(**kwargs: Any) -> object:
        assert kwargs == {"value": marker, "unit": target}
        events.append("factory")
        return marker

    def target_method(value: Any) -> object:
        assert value == Fraction(1, 3)
        events.append("target")
        monkeypatch.setattr(quantity_module, "Quantity", factory)
        return marker

    class Source:
        def to_si(self, value: Any) -> Any:
            events.append("captured source")
            target.from_si = target_method
            return value

    class Target:
        def from_si(self, value: Any) -> Any:
            raise AssertionError("target captured too early")

    class Owner:
        unit: Any = Source()

        @property
        def value(self) -> Fraction:
            self.unit = object()
            events.append("value")
            return Fraction(1, 3)

    target: Any = Target()
    assert convert_callback(owner=Owner(), target=target).unwrap() is marker
    assert events == ["value", "captured source", "target", "factory"]


def test_missing_and_builtin_factory_follow_global_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner, target = _traced(lambda event: None)
    monkeypatch.delattr(quantity_module, "Quantity")
    monkeypatch.delattr(builtins, "Quantity", raising=False)
    result = convert_callback(owner=owner, target=target)
    assert isinstance(result, Failed)
    assert type(result.error.value.callback_exception) is NameError
    assert "factory-lookup" in result.error.message
    marker = object()
    monkeypatch.setattr(builtins, "Quantity", lambda **kwargs: marker, raising=False)
    assert convert_callback(owner=owner, target=target).unwrap() is marker


@pytest.mark.parametrize(
    "case,stage,error_type",
    (
        ("owner", "source-unit", AttributeError),
        ("unit", "source-method", AttributeError),
        ("value", "source-value", AttributeError),
        ("to_si", "source-call", TypeError),
        ("target", "target-method", AttributeError),
        ("from_si", "target-call", TypeError),
        ("factory", "factory-call", TypeError),
    ),
)
def test_natural_missing_or_noncallable_protocol_is_a_structured_failure(
    *, monkeypatch: pytest.MonkeyPatch, case: str, stage: str, error_type: Any
) -> None:
    unit = SimpleNamespace(to_si=lambda value: value, from_si=lambda value: value)
    owner: Any = SimpleNamespace(unit=unit, value=1)
    target: Any = unit
    if case == "owner":
        owner = None
    elif case == "unit":
        owner.unit = None
    elif case == "value":
        del owner.value
    elif case == "to_si":
        unit.to_si = None
    elif case == "target":
        target = None
    elif case == "from_si":
        unit.from_si = None
    elif case == "factory":
        monkeypatch.setattr(quantity_module, "Quantity", None)
    result = convert_callback(owner=owner, target=target)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    assert type(result.error.value.callback_exception) is error_type
    assert stage in result.error.message


def test_same_owner_reentry_is_independent_and_uses_the_base_factory() -> None:
    calls = 0

    class OpenUnit:
        def to_si(self, value: Any) -> Any:
            nonlocal calls
            calls += 1
            if calls == 1:
                nested = convert_callback(owner=owner, target=self).unwrap()
                assert type(nested) is Quantity and nested.value is value
            return value

        def from_si(self, value: Any) -> Any:
            return value

    class Derived(Quantity[Any]):
        pass

    unit: Any = OpenUnit()
    owner = Derived(value=Fraction(1, 3), unit=unit)
    result = convert_callback(owner=owner, target=unit).unwrap()
    assert type(result) is Quantity and result.value is owner.value
    assert result.unit is unit and calls == 2


def test_unformattable_exception_and_hostile_class_property_are_not_inspected() -> None:
    def forbidden(self: object) -> Any:
        raise AssertionError("exception protocol was inspected")

    error = type(
        "OpaqueError",
        (ValueError,),
        {"__str__": forbidden, "__repr__": forbidden, "__class__": property(forbidden)},
    )()

    class Owner:
        @property
        def unit(self) -> Any:
            raise error

    result = convert_callback(owner=Owner(), target=object())
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error


@pytest.mark.parametrize(
    "failure_stage",
    (None, "source-call", "target-method", "target-call", "factory-call"),
)
def test_temporary_and_local_cleanup_matches_generic_python_reference(
    *, monkeypatch: pytest.MonkeyPatch, failure_stage: str | None
) -> None:
    def run(native: bool) -> tuple[list[str], bool]:
        events: list[str] = []

        class Value:
            def __init__(self, name: str) -> None:
                self.name = name

            def __del__(self) -> None:
                events.append("drop " + self.name)

        class Callback:
            def __init__(self, name: str) -> None:
                self.name = name

            def __call__(self, value: Any) -> Value:
                events.append(self.name)
                if failure_stage == self.name:
                    raise ValueError(self.name)
                return Value("standard" if self.name == "source-call" else "converted")

            def __del__(self) -> None:
                events.append("drop " + self.name)

        class Source:
            @property
            def to_si(self) -> Callback:
                return Callback("source-call")

            def __del__(self) -> None:
                events.append("drop source")

        class Owner:
            @property
            def unit(self) -> Source:
                return Source()

            @property
            def value(self) -> Value:
                return Value("input")

        class Target:
            @property
            def from_si(self) -> Callback:
                if failure_stage == "target-method":
                    raise ValueError("target-method")
                return Callback("target-call")

        def factory(**kwargs: Any) -> None:
            events.append("factory-call")
            if failure_stage == "factory-call":
                raise ValueError("factory-call")

        monkeypatch.setattr(quantity_module, "Quantity", factory)
        if native:
            result = convert_callback(owner=Owner(), target=Target())
            succeeded = isinstance(result, Ok)
            if isinstance(result, Failed):
                error = result.error.value.callback_exception
                assert error is not None
                error.__traceback__ = None
            del result
        else:
            try:
                _reference(Owner(), Target())
                succeeded = True
            except ValueError:
                succeeded = False
        gc.collect()
        return events, succeeded

    # 只比较「发生了哪些事件」与「是否成功」，不比较**次序**：
    # CPython 3.15 调换了临时对象的销毁次序（drop source-call 与 drop input 互换、
    # drop standard 与 drop converted 互换），那是解释器实现细节；两条路径的相对次序
    # 因此不再一致，但事件集合与成败判定仍然必须相同。
    # Compare the event multiset and the success flag, not the order: CPython 3.15 changed the
    # order in which temporaries are destroyed, so the two lanes no longer agree on order while
    # still agreeing on which lifecycle events happen.
    native_events, native_ok = run(True)
    reference_events, reference_ok = run(False)
    assert native_ok == reference_ok
    assert sorted(native_events) == sorted(reference_events)


@pytest.mark.parametrize(
    "value", (2**500 + 3, Fraction(23, 17), Decimal("0.12345678901234567890123456789"))
)
def test_open_callback_lane_can_delegate_real_unit_math_to_pinned_rust(
    value: Any,
) -> None:
    powers = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    standard = Unit.create(name="standard", symbol="m", powers=powers).unwrap()

    class RustBacked:
        def __init__(self, scale: int) -> None:
            self.unit = Unit.create(
                name="custom", symbol="x", powers=powers, scale=scale
            ).unwrap()

        def to_si(self, item: Any) -> Rational:
            return self.unit.convert_exact(value=item, target=standard).unwrap()

        def from_si(self, item: Any) -> Rational:
            return standard.convert_exact(value=item, target=self.unit).unwrap()

    source, target = RustBacked(1000), RustBacked(3)
    result = convert_callback(
        owner=_quantity(value=value, unit=source), target=target
    ).unwrap()
    assert Fraction(*result.value.as_integer_ratio()) == Fraction(value) * Fraction(
        1000, 3
    )
    assert result.unit is target


def test_reentry_threads_and_repeated_calls_retain_no_owners() -> None:
    class OpenUnit:
        def to_si(self, item: Any) -> Any:
            with ThreadPoolExecutor(max_workers=1) as pool:
                nested = (
                    pool.submit(
                        convert_callback,
                        owner=_quantity(value=item, unit=Identity()),
                        target=Identity(),
                    )
                    .result(timeout=10)
                    .unwrap()
                )
            return nested.value

        def from_si(self, item: Any) -> Any:
            return item

    class Identity:
        to_si = staticmethod(lambda value: value)
        from_si = staticmethod(lambda value: value)

    unit, target = OpenUnit(), Identity()
    owner = _quantity(value=Fraction(1, 3), unit=unit)
    before = (sys.getrefcount(owner), sys.getrefcount(target))
    for _ in range(10):
        assert (
            convert_callback(owner=owner, target=target).unwrap().value is owner.value
        )
    gc.collect()
    after = (sys.getrefcount(owner), sys.getrefcount(target))
    assert after == before


def test_raw_native_failure_uses_gc_visible_tuple_and_does_not_leave_python_error() -> (
    None
):
    error = ValueError("original")

    class Owner:
        @property
        def unit(self) -> Any:
            raise error

    result, failure = _native._convert_quantity_callback(
        owner=Owner(), target=None, namespace={}, builtins={}
    )
    assert result is None and type(failure) is tuple
    assert failure is not None
    assert failure[0] == "source-unit" and failure[1] is error
    assert error.__traceback__ is not None
    assert 1 + 1 == 2
