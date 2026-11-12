"""公共选择的原生候选及外部协议。 / Native selection candidate and external protocols."""

from __future__ import annotations

import gc
import itertools
import json
import subprocess
import sys
import threading
import weakref
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from fractions import Fraction
from typing import Any, get_type_hints

import pytest

from ospf_python import _native
from ospf_python._binding.result import BindingResult
from ospf_python.math.algebra.number.rational import Rational
from ospf_python.math.combinatorics.combinations import combinations
from ospf_python.math.combinatorics.combinatorics_async import (
    combinations_async,
    permutations_async,
)
from ospf_python.math.combinatorics.permutations import permutations
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok

Selection = Callable[[Any, Any], BindingResult[list[list[Any]]]]
"""自然选择 Result 入口。 / Natural selection Result entry point."""

FUNCTIONS = (combinations, permutations)


class Indexed:
    """不允许迭代的 live 索引源。 / Live indexed source that cannot be iterated."""

    def __init__(self, values: list[Any]) -> None:
        self.values = values

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, index: int) -> Any:
        return self.values[index]

    def __iter__(self) -> Any:
        raise AssertionError("must not snapshot through iteration")


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize(
    ("n", "k"), [(n, k) for n in range(6) for k in range(-1, n + 2)]
)
def test_indexed_protocol_complete_position_order(
    *, function: Selection, n: int, k: int
) -> None:
    oracle = (
        itertools.combinations if function is combinations else itertools.permutations
    )
    expected = [] if k < 0 else [list(row) for row in oracle(range(n), k)]
    assert function(Indexed(list(range(n))), k).unwrap() == expected


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize(
    "kind", ["fraction", "decimal", "rational", "quantity", "result"]
)
def test_exact_numeric_unit_and_result_leaves_are_not_converted(
    function: Selection, kind: str
) -> None:
    a: Any
    b: Any
    if kind == "fraction":
        a, b = Fraction(1, 3), Fraction(2, 7)
    elif kind == "decimal":
        a, b = Decimal("0.1"), Decimal("0.2")
    elif kind == "rational":
        a, b = Rational(1, 3), Rational(2, 7)
    elif kind == "quantity":
        a, b = Quantity(Fraction(1, 3), METER), Quantity(Fraction(2, 7), METER)
    else:
        a, b = Ok(object()), Ok(None)
    source = [a, a, b]
    oracle = (
        itertools.combinations if function is combinations else itertools.permutations
    )
    for source_kind in (source, tuple(source), Indexed(source)):
        actual = function(source_kind, 2).unwrap()
        for row, positions in zip(actual, oracle(range(3), 2), strict=True):
            assert all(
                value is source[index]
                for value, index in zip(row, positions, strict=True)
            )


@pytest.mark.parametrize("function", FUNCTIONS)
def test_list_subclass_keeps_index_hooks_and_prefix_identity(
    function: Selection,
) -> None:
    references: list[object] = []

    class Source(list[int]):
        def __getitem__(self, index: Any) -> Any:
            super().__getitem__(index)
            value = object()
            references.append(value)
            return value

        def __iter__(self) -> Any:
            raise AssertionError("must not iterate subclass")

    rows = function(Source([0, 1, 2]), 2).unwrap()
    assert rows[0][0] is rows[1][0] is references[0]
    assert rows[0][1] is references[1] and rows[1][1] is references[2]
    assert len(references) == (6 if function is combinations else 9)


@pytest.mark.parametrize("function", FUNCTIONS)
def test_count_subclass_equality_remains_live(function: Selection) -> None:
    equalities: list[int] = []

    class Count(int):
        def __eq__(self, other: object) -> bool:
            assert isinstance(other, int)
            equalities.append(other)
            return other == 2

    assert (
        function(Indexed([0, 1, 2]), Count(2)).unwrap()
        == function([0, 1, 2], 2).unwrap()
    )
    expected = (
        [0, 1, 2, 2, 1, 2, 1]
        if function is combinations
        else [0, 1, 2, 2, 1, 2, 2, 1, 2, 2]
    )
    assert equalities == expected


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("stage", ["less", "greater", "equal", "len", "get"])
@pytest.mark.parametrize("exception_type", [TypeError, RuntimeError, KeyboardInterrupt])
def test_external_failure_identity_traceback_and_baseexception(
    *, function: Selection, stage: str, exception_type: type[BaseException]
) -> None:
    error = exception_type("selection hook")

    class Count:
        def __lt__(self, other: object) -> bool:
            if stage == "less":
                raise error
            return False

        def __gt__(self, other: object) -> bool:
            if stage == "greater":
                raise error
            return False

        def __eq__(self, other: object) -> bool:
            if stage == "equal":
                raise error
            return other == 1

    class Source(Indexed):
        def __len__(self) -> int:
            if stage == "len":
                raise error
            return super().__len__()

        def __getitem__(self, index: int) -> Any:
            if stage == "get":
                raise error
            return super().__getitem__(index)

    if isinstance(error, Exception):
        result = function(Source([0, 1]), Count())
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.APPLICATION_ERROR
        assert result.error.value.callback_exception is error
        assert error.__traceback__ is not None
        frames = []
        traceback = error.__traceback__
        while traceback is not None:
            frames.append(traceback.tb_frame.f_code.co_name)
            traceback = traceback.tb_next
        assert (
            frames[-1]
            == {
                "less": "__lt__",
                "greater": "__gt__",
                "equal": "__eq__",
                "len": "__len__",
                "get": "__getitem__",
            }[stage]
        )
    else:
        with pytest.raises(KeyboardInterrupt) as caught:
            function(Source([0, 1]), Count())
        assert caught.value is error


@pytest.mark.parametrize("function", FUNCTIONS)
def test_capacity_fails_before_reading_a_leaf(function: Selection) -> None:
    class Huge:
        def __len__(self) -> int:
            return sys.maxsize

        def __getitem__(self, index: int) -> Any:
            raise AssertionError("capacity must be checked first")

    result = function(Huge(), 1)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OVERFLOW
    assert result.error.value.callback_exception is None


def test_growing_permutation_fails_without_exposing_partial_rows() -> None:
    class Growing(Indexed):
        def __getitem__(self, index: int) -> Any:
            if len(self.values) == 3:
                self.values.append(3)
            return super().__getitem__(index)

    operation: Selection = permutations
    result = operation(Growing([0, 1, 2]), 2)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_one_native_call_annotations_and_no_owner_retention(
    function: Selection, monkeypatch: pytest.MonkeyPatch
) -> None:
    native = _native._selection
    sources: list[int] = []

    def delegated(**kwargs: Any) -> Any:
        sources.append(id(kwargs["items"]))
        return native(**kwargs)

    monkeypatch.setattr(_native, "_selection", delegated)
    source = Indexed([object(), object()])
    reference = weakref.ref(source)
    result = function(source, 1)
    assert isinstance(result, Ok) and sources == [id(source)]
    assert get_type_hints(function)["return"] is not list
    del source
    gc.collect()
    assert reference() is None


@pytest.mark.parametrize("function", FUNCTIONS)
def test_external_getter_can_wait_for_a_nested_call_on_another_thread(
    function: Selection,
) -> None:
    class Source(Indexed):
        def __getitem__(self, index: int) -> Any:
            with ThreadPoolExecutor(max_workers=1) as executor:
                assert executor.submit(function, [7], 1).result(timeout=5).unwrap() == [
                    [7]
                ]
            return super().__getitem__(index)

    assert function(Source([0, 1]), 1).unwrap() == [[0], [1]]


@pytest.mark.asyncio
@pytest.mark.parametrize("ordered", [False, True])
@pytest.mark.parametrize("external", [False, True])
async def test_real_async_native_call_preserves_protocol_and_result(
    *, ordered: bool, external: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """真实异步入口运行同一原生内核，不用 mock 代替工作。

    The real async entry point runs the same native kernel, not mocked work.
    """
    leaves = [object(), object(), object()]
    source: Any = Indexed(leaves) if external else leaves
    operation = permutations_async if ordered else combinations_async
    original = _native._selection
    calls: list[tuple[int, int]] = []

    def delegated(**kwargs: Any) -> Any:
        calls.append((id(kwargs["items"]), threading.get_ident()))
        return original(**kwargs)

    monkeypatch.setattr(_native, "_selection", delegated)
    main_thread = threading.get_ident()
    result = await operation(source, 2)
    assert isinstance(result, Ok)
    assert len(calls) == 1 and calls[0][0] == id(source)
    assert calls[0][1] != main_thread
    oracle = itertools.permutations if ordered else itertools.combinations
    for row, indices in zip(result.unwrap(), oracle(range(3), 2), strict=True):
        assert all(
            value is leaves[index] for value, index in zip(row, indices, strict=True)
        )


@pytest.mark.parametrize("depth", [129, 512, 4096])
def test_deep_pinned_recursion_has_a_separate_checked_worker_stack(depth: int) -> None:
    program = """
import json
import os
handles = []
if os.name == 'nt':
    handles = [os.add_dll_directory(path) for path in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python import _native
from ospf_python.math.combinatorics.combinations import combinations
n = DEPTH
rows = combinations(list(range(n)), n).unwrap()
assert rows == [list(range(n))]
print(json.dumps({'depth': n, 'extension': _native.__file__}))
""".replace("DEPTH", str(depth))
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["depth"] == depth
    assert report["extension"] == _native.__file__


@pytest.mark.parametrize("function", FUNCTIONS)
def test_prefix_release_hooks_change_later_reads_in_original_depth_first_order(
    function: Selection,
) -> None:
    """前缀析构会改变后续 getter 观察到的状态。 / Prefix destruction changes later reads."""
    events: list[tuple[str, int, int]] = []
    state = {"epoch": 0}

    class Leaf:
        def __init__(self, index: int) -> None:
            self.index = index
            self.epoch = state["epoch"]

        def __del__(self) -> None:
            events.append(("drop", self.index, self.epoch))
            state["epoch"] += 1

    class Source:
        def __len__(self) -> int:
            events.append(("len", 2, -1))
            return 2

        def __getitem__(self, index: int) -> Leaf:
            assert 0 <= index < 2
            events.append(("get", index, state["epoch"]))
            return Leaf(index)

        def __iter__(self) -> Any:
            raise AssertionError("must not snapshot the live source")

    result = function(Source(), 1.5)
    assert result.unwrap() == []
    length = ("len", 2, -1)
    if function is combinations:
        assert events == [
            length,
            length,
            ("get", 0, 0),
            length,
            ("get", 1, 0),
            length,
            ("drop", 1, 0),
            ("drop", 0, 0),
            ("get", 1, 2),
            length,
            ("drop", 1, 2),
        ]
    else:
        assert events == [
            length,
            length,
            length,
            ("get", 0, 0),
            length,
            ("get", 1, 0),
            length,
            ("drop", 1, 0),
            ("drop", 0, 0),
            ("get", 1, 2),
            length,
            ("get", 0, 2),
            length,
            ("drop", 0, 2),
            ("drop", 1, 2),
        ]
