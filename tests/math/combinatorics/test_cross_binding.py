"""公共笛卡尔积的默认 Rust 路径 / Default Rust path for public Cartesian products."""

from __future__ import annotations

import copy
import gc
import itertools
import pickle
import weakref
from decimal import Decimal
from fractions import Fraction
from typing import Any, get_type_hints

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.combinatorics import cross as exported_cross
from ospf_python.math.combinatorics.cross import cross
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.parametrize(
    "lengths",
    [
        (),
        (0,),
        (3,),
        (2, 3),
        (2, 0, 3),
        (2, 3, 4),
        (2, 3, 2, 3),
        (2, 1, 2, 3, 2),
        (2,) * 6,
        (2,) * 7,
        (2,) * 13,
        (1,) * 2048,
    ],
)
def test_order_rank_and_nullary_identity(lengths: tuple[int, ...]) -> None:
    pools = [list(range(length)) for length in lengths]
    result = cross(*pools)
    assert isinstance(result, Ok)
    assert result.value == list(itertools.product(*pools))
    assert all(type(row) is tuple for row in result.value)


def test_natural_export_annotation_and_exactly_one_native_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _native._cross
    calls = []

    def invoke(inputs: Any) -> Any:
        calls.append(inputs)
        return original(inputs)

    monkeypatch.setattr(_native, "_cross", invoke)
    assert exported_cross is cross
    assert get_type_hints(cross)["return"] is not list
    left, right = [1, 2], ["a", "b"]
    assert cross(left, right).unwrap() == [(1, "a"), (1, "b"), (2, "a"), (2, "b")]
    assert len(calls) == 1 and calls[0][0] is left and calls[0][1] is right


def test_arbitrary_iterables_are_consumed_once_in_input_order() -> None:
    events = []

    def pool(label: str) -> Any:
        events.append(label)
        yield label
        events.append(f"{label}-done")

    result = cross(pool("first"), pool("second"), {"a": 1}, "xy", range(1)).unwrap()
    assert result == [
        ("first", "second", "a", "x", 0),
        ("first", "second", "a", "y", 0),
    ]
    assert events == ["first", "first-done", "second", "second-done"]


def test_empty_pool_does_not_skip_later_input_protocols() -> None:
    events = []

    def tail() -> Any:
        events.append("tail-consumed")
        yield 7

    assert cross([], tail()).unwrap() == []
    assert events == ["tail-consumed"]


def test_list_constructor_protocol_order_matches_builtin_list() -> None:
    events = []

    class Pool:
        def __iter__(self) -> Any:
            events.append("iter")
            return iter([1, 2])

        def __len__(self) -> int:
            events.append("len")
            return 2

    baseline = list(Pool())
    expected_events = events[:]
    events.clear()
    assert cross(Pool()).unwrap() == [(value,) for value in baseline]
    assert events == expected_events


def test_snapshots_preserve_live_leaf_identity_but_not_later_pool_mutations() -> None:
    leaf: list[str] = []
    left: list[Any] = [leaf]

    def right() -> Any:
        left.append("not-in-snapshot")
        leaf.append("visible-leaf-change")
        yield 1

    output = cross(left, right()).unwrap()
    assert len(output) == 1 and output[0][0] is leaf
    assert output[0][0] == ["visible-leaf-change"]
    left.clear()
    assert output[0][0] is leaf


def test_reentrant_input_protocol_runs_without_a_native_lock() -> None:
    def pool() -> Any:
        yield cross([1, 2], [3]).unwrap()

    assert cross(pool()).unwrap() == [([(1, 3), (2, 3)],)]


def test_opaque_domains_duplicates_and_result_leaves_keep_identity() -> None:
    quantity: Quantity[Fraction] = Quantity(Fraction(3, 2), METER)
    leaves: list[Any] = [
        None,
        Fraction(1, 3),
        Decimal("0.1"),
        2**300,
        1 + 2j,
        quantity,
        np.int64(9),
        np.array([1, 2]),
        Ok(7),
        Failed(Err(ErrorCode.ILLEGAL_ARGUMENT, "leaf")),
    ]
    result = cross(leaves, [leaves[0], leaves[0]]).unwrap()
    for index, leaf in enumerate(leaves):
        assert result[index * 2][0] is leaf and result[index * 2 + 1][0] is leaf
        assert result[index * 2][1] is None


def test_enumeration_does_not_execute_leaf_protocols() -> None:
    class Leaf:
        def __getattribute__(self, name: str) -> Any:
            raise AssertionError("不得解释叶 / Do not interpret leaves")

        def __eq__(self, other: Any) -> bool:
            raise AssertionError("不得比较叶 / Do not compare leaves")

        def __hash__(self) -> int:
            raise AssertionError("不得哈希叶 / Do not hash leaves")

    leaf = Leaf()
    output = cross([leaf, leaf], [leaf]).unwrap()
    assert len(output) == 2 and all(value is leaf for row in output for value in row)


@pytest.mark.parametrize(
    "kind", [RuntimeError, TypeError, ValueError, OverflowError, MemoryError]
)
@pytest.mark.parametrize("phase", ["iter", "len", "next"])
def test_original_external_exception_is_returned_without_formatting(
    kind: type[Exception], phase: str
) -> None:
    def invalid_string(self: object) -> str:
        raise AssertionError("不得格式化异常 / Do not format exceptions")

    external = type("External", (kind,), {"__str__": invalid_string})
    failure = external()

    class Pool:
        def __iter__(self) -> Any:
            if phase == "iter":
                raise failure
            return self

        def __len__(self) -> int:
            if phase == "len":
                raise failure
            return 1

        def __next__(self) -> Any:
            raise failure

    result = cross([], Pool())
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    assert result.error.value.callback_exception is failure
    assert result.error.value.error_class == "EXTERNAL_ITERABLE"
    assert failure.__traceback__ is not None


@pytest.mark.parametrize("kind", [KeyboardInterrupt, SystemExit, GeneratorExit])
def test_process_control_exceptions_propagate(kind: type[BaseException]) -> None:
    failure = kind()

    def pool() -> Any:
        raise failure
        yield 1

    with pytest.raises(kind) as caught:
        cross(pool())
    assert caught.value is failure


def test_capacity_overflow_is_structured_and_empty_annihilator_is_not_overflow() -> (
    None
):
    pools = [[0, 1] for _ in range(64)]
    result = cross(*pools)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OVERFLOW
    assert result.error.value.callback_exception is None
    assert result.error.value.source == "ospf-python-native"
    assert cross(*pools, []).unwrap() == []


def test_temporary_snapshots_release_on_later_input_failure() -> None:
    class Leaf:
        pass

    references = []

    def first() -> Any:
        for _ in range(8):
            leaf = Leaf()
            references.append(weakref.ref(leaf))
            yield leaf

    def second() -> Any:
        raise RuntimeError("外部失败 / External failure")
        yield 1

    result = cross(first(), second())
    assert isinstance(result, Failed)
    gc.collect()
    assert all(reference() is None for reference in references)


def test_plain_result_container_roundtrips_and_preserves_graph_aliases() -> None:
    leaf: list[Any] = []
    leaf.append(leaf)
    output = cross([leaf, leaf], [None]).unwrap()
    for restored in [copy.deepcopy(output)] + [
        pickle.loads(pickle.dumps(output, protocol=p))
        for p in range(pickle.HIGHEST_PROTOCOL + 1)
    ]:
        assert restored[0][0] is restored[1][0]
        assert restored[0][0][0] is restored[0][0]
    assert copy.copy(output)[0] is output[0]


@pytest.mark.parametrize("arity", [1, 2, 3, 4, 5, 6, 7, 13])
def test_output_has_no_persistent_native_owner_or_leaked_leaf_references(
    arity: int,
) -> None:
    class Leaf:
        pass

    for _ in range(8):
        leaf = Leaf()
        reference = weakref.ref(leaf)
        output = cross(*[[leaf] * 2 for _ in range(arity)]).unwrap()
        del leaf
        assert reference() is not None
        del output
        gc.collect()
        assert reference() is None


@pytest.mark.parametrize("arity", [1, 2, 3, 4, 5, 6, 7, 13])
def test_static_packing_never_flattens_a_python_tuple_leaf(arity: int) -> None:
    leaf = ("opaque", [1, 2])
    rows = cross(*[[leaf] for _ in range(arity)]).unwrap()
    assert len(rows) == 1 and len(rows[0]) == arity
    assert all(value is leaf for value in rows[0])
