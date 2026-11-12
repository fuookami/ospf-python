"""普通极值的原生比较与公开协议。 / Native extrema and public protocols."""

from __future__ import annotations

import importlib
import math
import sys
import weakref
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.ordinary.min_max import max_of, min_max_of, min_of
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.parametrize(
    "values",
    [
        [4, 2, 9, 2],
        [-(1 << 1024), 1 << 2048, 0],
        [Fraction(1, 3), Fraction(-2, 7), Fraction(4, 5)],
        [Decimal("0.3"), Decimal("-0.1"), Decimal("0.1")],
        [np.int64(2), np.int64(1), np.int64(3)],
        [0.0, -0.0, 0.0],
        [math.nan, 2.0, -1.0],
        [2.0, math.nan, -1.0],
        [None],
    ],
)
def test_extrema_return_original_objects(values: list[Any]) -> None:
    expected_min = min(values)
    expected_max = max(values)
    assert min_of(iter(values)).unwrap() is expected_min
    assert max_of(iter(values)).unwrap() is expected_max
    low, high = min_max_of(iter(values)).unwrap()
    assert low is expected_min
    assert high is expected_max


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_exact_small_int_list_handles_i64_boundaries_and_ties(operation: Any) -> None:
    values = [2**63 - 1, -(2**63), *range(62)]
    expected = (min(values), max(values))
    actual = operation(values).unwrap()
    if operation is min_max_of:
        assert actual[0] is values[1] and actual[1] is values[0]
        assert actual == expected
    else:
        assert actual is (values[1] if operation is min_of else values[0])


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_small_integer_prefix_falls_back_for_a_wide_value(operation: Any) -> None:
    values = [3, 1, *range(2, 63), 1 << 80]
    expected = (min(values), max(values))
    actual = operation(values).unwrap()
    if operation is min_max_of:
        assert actual == expected
    else:
        assert actual is (values[1] if operation is min_of else values[-1])


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_exact_list_retains_int_subclass_comparison_hooks(operation: Any) -> None:
    events: list[str] = []

    class Hooked(int):
        def __lt__(self, other: object) -> bool:
            events.append("lt")
            return int.__lt__(self, other)

        def __gt__(self, other: object) -> bool:
            events.append("gt")
            return int.__gt__(self, other)

    values = [*range(2, 65), Hooked(1)]
    actual = operation(values).unwrap()
    if operation is min_max_of:
        assert actual == (values[-1], values[-2])
        assert events == ["lt", "gt"]
    else:
        assert actual is (values[-1] if operation is min_of else values[-2])
        assert events == (["lt"] if operation is min_of else ["gt"])


def test_exact_list_retains_bool_identity() -> None:
    values = [100, True, *range(2, 64)]
    assert min_of(values).unwrap() is values[1]
    assert max_of(values).unwrap() is values[0]
    assert min_max_of(values).unwrap() == (values[1], values[0])


def test_result_item_is_data() -> None:
    item: Any = Ok(None)
    assert min_of([item]).unwrap() is item
    assert max_of([item]).unwrap() is item
    low, high = min_max_of([item]).unwrap()
    assert low is high is item


def test_combined_materializes_and_compares_in_two_passes() -> None:
    events: list[tuple[str, int]] = []

    class Item:
        def __init__(self, value: int) -> None:
            self.value = value

        def __lt__(self, other: Item) -> bool:
            events.append(("lt", self.value))
            return self.value < other.value

        def __gt__(self, other: Item) -> bool:
            events.append(("gt", self.value))
            return self.value > other.value

    values = [Item(3), Item(1), Item(2)]

    def source() -> Any:
        for item in values:
            events.append(("yield", item.value))
            yield item

    low, high = min_max_of(source()).unwrap()
    assert low is values[1] and high is values[0]
    assert events == [
        ("yield", 3),
        ("yield", 1),
        ("yield", 2),
        ("lt", 1),
        ("lt", 2),
        ("gt", 1),
        ("gt", 2),
    ]


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_reflection_and_comparison_truth_follow_python(operation: Any) -> None:
    events: list[str] = []

    class Truth:
        def __bool__(self) -> bool:
            events.append("bool")
            return True

    class First:
        def __gt__(self, other: object) -> Truth:
            events.append("reflected gt")
            return Truth()

        def __lt__(self, other: object) -> Truth:
            events.append("reflected lt")
            return Truth()

    class Second:
        def __lt__(self, other: object) -> Any:
            events.append("lt")
            return NotImplemented

        def __gt__(self, other: object) -> Any:
            events.append("gt")
            return NotImplemented

    values: list[Any] = [First(), Second()]
    expected: Any
    if operation is min_max_of:
        expected = (min(values), max(values))
    else:
        expected = (min if operation is min_of else max)(values)
    expected_events = events[:]
    events.clear()
    actual = operation(values).unwrap()
    if operation is min_max_of:
        assert actual[0] is expected[0] and actual[1] is expected[1]
    else:
        assert actual is expected
    assert events == expected_events


def test_single_extrema_are_streaming_without_length_hint() -> None:
    events: list[str] = []

    class Item:
        def __lt__(self, other: object) -> bool:
            events.append("compare")
            return False

    class Items:
        def __iter__(self) -> Any:
            events.append("first")
            yield Item()
            events.append("second")
            yield Item()
            events.append("end")

        def __len__(self) -> int:
            raise AssertionError("unexpected length hint")

    min_of(Items()).unwrap()
    assert events == ["first", "second", "compare", "end"]


def test_comparison_can_reenter_extrema() -> None:
    class Item:
        def __lt__(self, other: object) -> bool:
            assert max_of([1, 3, 2]).unwrap() == 3
            return True

    candidate = Item()
    assert min_of([object(), candidate]).unwrap() is candidate


@pytest.mark.parametrize("operation", [min_of, max_of])
def test_streamed_temporary_lifetimes_follow_builtin(operation: Any) -> None:
    def run(*, current: bool) -> tuple[str, list[str]]:
        events: list[str] = []

        class Item:
            def __init__(self, value: int) -> None:
                self.value = value

            def __lt__(self, other: Item) -> bool:
                events.append(f"lt {self.value} {other.value}")
                return self.value < other.value

            def __gt__(self, other: Item) -> bool:
                events.append(f"gt {self.value} {other.value}")
                return self.value > other.value

            def __del__(self) -> None:
                events.append(f"del {self.value}")

        def source() -> Any:
            for value in (3, 1, 2):
                yield Item(value)

        if current:
            selected = operation(source()).unwrap()
        else:
            selected = (min if operation is min_of else max)(source())
        result = str(selected.value)
        del selected
        return result, events

    assert run(current=True) == run(current=False)


@pytest.mark.skipif(
    not hasattr(sys, "getrefcount"), reason="requires CPython refcounts"
)
@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
@pytest.mark.parametrize("truth_object", [False, True])
def test_reference_sensitive_comparison_matches_builtin(
    *, operation: Any, truth_object: bool
) -> None:
    def run(*, current: bool) -> tuple[Any, list[tuple[str, int, int]]]:
        events: list[tuple[str, int, int]] = []

        class Item:
            def __init__(self, value: int) -> None:
                self.value = value

            def compare(self, other: Item, *, name: str) -> Any:
                if truth_object:
                    return Truth(self, other, name=name)
                references = sys.getrefcount(self)
                events.append((name, references, sys.getrefcount(other)))
                return references % 2 == 0

            def __lt__(self, other: Item) -> Any:
                return self.compare(other, name="lt")

            def __gt__(self, other: Item) -> Any:
                return self.compare(other, name="gt")

        class Truth:
            def __init__(self, left: Item, right: Item, *, name: str) -> None:
                self.left = left
                self.right = right
                self.name = name

            def __bool__(self) -> bool:
                references = sys.getrefcount(self.left)
                events.append((self.name, references, sys.getrefcount(self.right)))
                return references % 2 == 0

        def source() -> Any:
            for value in (3, 1, 2):
                yield Item(value)

        if current:
            selected = operation(source()).unwrap()
        elif operation is min_max_of:
            collected = list(source())
            selected = (min(collected), max(collected))
        else:
            selected = (min if operation is min_of else max)(source())
        values = (
            tuple(item.value for item in selected)
            if isinstance(selected, tuple)
            else selected.value
        )
        return values, events

    assert run(current=True) == run(current=False)


@pytest.mark.skipif(
    not hasattr(sys, "getrefcount"), reason="requires CPython refcounts"
)
@pytest.mark.parametrize("operation", [min_of, max_of])
def test_streamed_reference_lifetime_matches_builtin(operation: Any) -> None:
    def run(*, current: bool) -> tuple[int, list[int]]:
        references: list[int] = []

        class Item:
            def __init__(self, value: int) -> None:
                self.value = value

            def __lt__(self, other: Item) -> bool:
                return self.value < other.value

            def __gt__(self, other: Item) -> bool:
                return self.value > other.value

        def source() -> Any:
            first = Item(3)
            yield first
            references.append(sys.getrefcount(first))
            yield Item(1)
            references.append(sys.getrefcount(first))
            yield first

        if current:
            selected = operation(source()).unwrap()
        else:
            selected = (min if operation is min_of else max)(source())
        return selected.value, references

    assert run(current=True) == run(current=False)


@pytest.mark.skipif(
    not hasattr(sys, "getrefcount"), reason="requires CPython refcounts"
)
@pytest.mark.parametrize("operation", [min_of, max_of])
def test_destruction_observes_the_same_candidate_references(operation: Any) -> None:
    def run(*, current: bool) -> list[tuple[Any, ...]]:
        events: list[tuple[Any, ...]] = []
        candidate_reference: list[Any] = [None]

        class Item:
            def __init__(self, value: int) -> None:
                self.value = value

            def __lt__(self, other: Item) -> bool:
                candidate_reference[0] = weakref.ref(self)
                return self.value < other.value

            def __gt__(self, other: Item) -> bool:
                candidate_reference[0] = weakref.ref(self)
                return self.value > other.value

            def __del__(self) -> None:
                reference = candidate_reference[0]
                candidate = reference() if reference is not None else None
                events.append(
                    (
                        self.value,
                        None if candidate is None else candidate.value,
                        None if candidate is None else sys.getrefcount(candidate),
                    )
                )

        def source() -> Any:
            for value in (3, 1, 2, 4, 4):
                yield Item(value)

        if current:
            selected = operation(source()).unwrap()
        else:
            selected = (min if operation is min_of else max)(source())
        del selected
        return events

    assert run(current=True) == run(current=False)


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
@pytest.mark.parametrize("failure", ["comparison", "iteration"])
def test_temporary_lifetimes_on_failure_match_builtin(
    *, operation: Any, failure: str
) -> None:
    def run(*, current: bool) -> list[str]:
        events: list[str] = []
        error = RuntimeError("original")

        class Item:
            def __init__(self, value: int) -> None:
                self.value = value

            def __lt__(self, other: Item) -> bool:
                events.append("compare")
                if failure == "comparison":
                    raise error
                return self.value < other.value

            def __gt__(self, other: Item) -> bool:
                events.append("compare")
                if failure == "comparison":
                    raise error
                return self.value > other.value

            def __del__(self) -> None:
                events.append(f"del {self.value}")

        def source() -> Any:
            yield Item(3)
            yield Item(1)
            if failure == "iteration":
                raise error

        if current:
            result = operation(source())
            assert isinstance(result, Failed)
            assert result.error.value.callback_exception is error
        else:
            try:
                if operation is min_max_of:
                    collected = list(source())
                    min(collected), max(collected)
                else:
                    (min if operation is min_of else max)(source())
            except RuntimeError as caught:
                assert caught is error
        assert error.__traceback__ is not None
        error.__traceback__ = None
        return events

    assert run(current=True) == run(current=False)


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_comparison_can_mutate_source_with_original_iteration_policy(
    operation: Any,
) -> None:
    def run(*, current: bool) -> tuple[Any, list[str]]:
        events: list[str] = []
        source: list[Any] = []

        class Item:
            def __init__(self, value: int) -> None:
                self.value = value

            def compare(self, other: Item, *, minimum: bool) -> bool:
                events.append(f"{'lt' if minimum else 'gt'} {self.value} {other.value}")
                if len(source) == 2:
                    source.append(Item(2))
                return self.value < other.value if minimum else self.value > other.value

            def __lt__(self, other: Item) -> bool:
                return self.compare(other, minimum=True)

            def __gt__(self, other: Item) -> bool:
                return self.compare(other, minimum=False)

        source.extend([Item(3), Item(1)])
        if current:
            result = operation(source).unwrap()
        elif operation is min_of:
            result = min(source)
        elif operation is max_of:
            result = max(source)
        else:
            collected = list(source)
            result = (min(collected), max(collected))
        values = (
            tuple(item.value for item in result)
            if isinstance(result, tuple)
            else result.value
        )
        return values, events

    assert run(current=True) == run(current=False)


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_empty_failure_preserves_interpreter_exception(operation: Any) -> None:
    expected_function = max if operation is max_of else min
    with pytest.raises(ValueError) as original:
        expected_function([])
    result = operation([])
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    failure = result.error.value.callback_exception
    assert type(failure) is ValueError
    assert str(failure) == str(original.value)


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
@pytest.mark.parametrize(
    ("error_type", "code"),
    [
        (TypeError, ErrorCode.ILLEGAL_ARGUMENT),
        (ValueError, ErrorCode.ILLEGAL_ARGUMENT),
        (OverflowError, ErrorCode.OVERFLOW),
        (MemoryError, ErrorCode.RESOURCE_EXHAUSTED),
        (RuntimeError, ErrorCode.APPLICATION_ERROR),
    ],
)
def test_iteration_failure_preserves_exception(
    *, operation: Any, error_type: type[Exception], code: ErrorCode
) -> None:
    error = error_type("original")

    def source() -> Any:
        yield 1
        raise error

    result = operation(source())
    assert isinstance(result, Failed)
    assert result.error.code is code
    assert result.error.value.callback_exception is error
    assert error.__traceback__ is not None


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_base_exceptions_are_not_wrapped(
    *, operation: Any, error_type: type[BaseException]
) -> None:
    error = error_type("original")

    def source() -> Any:
        raise error
        yield

    with pytest.raises(error_type) as captured:
        operation(source())
    assert captured.value is error


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_comparison_failure_short_circuits(operation: Any) -> None:
    error = RuntimeError("comparison")
    seen: list[str] = []

    class Broken:
        def __lt__(self, other: Any) -> Any:
            seen.append("lt")
            raise error

        def __gt__(self, other: Any) -> Any:
            seen.append("gt")
            raise error

    result = operation([object(), Broken(), object()])
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error
    assert seen == (["gt"] if operation is max_of else ["lt"])


def test_comparison_truth_failure_is_not_formatted() -> None:
    class SensitiveError(RuntimeError):
        def __str__(self) -> str:
            raise AssertionError("unexpected formatting")

    error = SensitiveError()

    class Truth:
        def __bool__(self) -> bool:
            raise error

    class Item:
        def __lt__(self, other: object) -> Truth:
            return Truth()

    result = min_of([object(), Item()])
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is error


def test_exception_class_spoof_does_not_escape_result() -> None:
    class Hostile(RuntimeError):
        def __getattribute__(self, name: str) -> Any:
            if name == "__class__":
                raise AssertionError("unexpected class protocol")
            return super().__getattribute__(name)

    error = Hostile("original")

    class Item:
        def __lt__(self, other: object) -> bool:
            raise error

    escaped = None
    result = None
    try:
        result = min_of([object(), Item()])
    except Exception as caught:
        escaped = type(caught).__name__
    assert escaped is None
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    assert result.error.value.callback_exception is error


def test_dynamic_hooks_and_late_max_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("ospf_python.math.ordinary.min_max")
    first, second = object(), object()
    events: list[str] = []

    def later(items: object) -> object:
        events.append("max")
        return second

    def earlier(items: object) -> object:
        events.append("min")
        monkeypatch.setattr(module, "max", later, raising=False)
        return first

    monkeypatch.setattr(module, "min", earlier, raising=False)
    low, high = min_max_of([1]).unwrap()
    assert low is first and high is second
    assert events == ["min", "max"]


def test_min_comparison_can_change_the_later_max_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("ospf_python.math.ordinary.min_max")
    sentinel = object()

    class Item:
        def __lt__(self, other: object) -> bool:
            monkeypatch.setattr(module, "max", lambda items: sentinel, raising=False)
            return True

    low, high = min_max_of([object(), Item()]).unwrap()
    assert isinstance(low, Item)
    assert high is sentinel


@pytest.mark.parametrize("operation", [min_of, max_of, min_max_of])
def test_natural_entry_uses_native_dispatch(
    *, operation: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _native._ordinary_extreme
    calls: list[bool] = []

    def spy(**kwargs: Any) -> Any:
        calls.append(kwargs["minimum"])
        return original(**kwargs)

    monkeypatch.setattr(_native, "_ordinary_extreme", spy)
    operation([3, 1, 2]).unwrap()
    assert calls == (
        [True, False] if operation is min_max_of else [operation is min_of]
    )
