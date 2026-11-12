"""公共求和切换前 object 协议基线 / Pre-cutover public object summation protocols.

当前仍为 NumPy 默认入口；不授权数值域缩窄或将本基线计为原生切换验收。
The default remains NumPy; these baselines certify neither narrowing nor a native cutover.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pytest

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.multiarray import MultiArray, Shape2
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Warn


class _UnformattableError(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不得格式化外部异常 / Must not format external exceptions")


def _objects(values: list[Any]) -> np.ndarray[Any, Any]:
    data = np.empty(len(values), dtype=object)
    for position, value in enumerate(values):
        data[position] = value
    return data


@pytest.mark.parametrize("axis", [0, 1])
def test_nonempty_groups_need_neither_zero_truth_equality_nor_inplace_addition(
    axis: int,
) -> None:
    class Leaf:
        def __init__(self, trace: str) -> None:
            self.trace = trace

        def __add__(self, other: Leaf) -> Leaf:
            assert type(other) is Leaf
            return Leaf(f"({self.trace}+{other.trace})")

        def __radd__(self, other: Any) -> Any:
            pytest.fail("不应加入 Python 零 / Must not add Python zero")

        def __iadd__(self, other: Leaf) -> Leaf:
            pytest.fail("不应原地修改叶 / Must not mutate leaves in place")

        def __bool__(self) -> bool:
            pytest.fail("不应读取叶真值 / Must not read leaf truth")

        def __eq__(self, other: object) -> bool:
            pytest.fail("不应比较叶 / Must not compare leaves")

    values = [Leaf(label) for label in "abcdef"]
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), _objects(values))
    result = fast_sum(source, axis=axis)
    expected = ["(a+d)", "(b+e)", "(c+f)"] if axis == 0 else ["((a+b)+c)", "((d+e)+f)"]
    assert [value.trace for value in result._data] == expected
    assert [value.trace for value in values] == list("abcdef")
    assert all(source._data[position] is value for position, value in enumerate(values))


@pytest.mark.parametrize("axis", [0, 1])
def test_singleton_groups_retain_leaf_identity_without_arithmetic(axis: int) -> None:
    class Leaf:
        def __add__(self, other: Any) -> Any:
            pytest.fail("单元素组不应加法 / Singleton groups must not add")

        def __radd__(self, other: Any) -> Any:
            pytest.fail("单元素组不应加零 / Singleton groups must not add zero")

    values = [Leaf(), Leaf()]
    shape = Shape2(1, 2) if axis == 0 else Shape2(2, 1)
    source: MultiArray[Any, Shape2] = MultiArray(shape, _objects(values))
    result = fast_sum(source, axis=axis)
    assert result.shape.dims == (2,)
    assert all(result._data[position] is value for position, value in enumerate(values))


@pytest.mark.parametrize("axis", [0, 1])
def test_captured_buffer_reads_later_mutations_but_not_owner_rebinding(
    axis: int,
) -> None:
    calls: list[tuple[str, str]] = []

    class Leaf:
        def __init__(self, trace: str) -> None:
            self.trace = trace

        def __add__(self, other: Leaf) -> Leaf:
            calls.append((self.trace, other.trace))
            if len(calls) == 1:
                data[4 if axis == 0 else 2] = Leaf("x")
                source._data = _objects([Leaf("z") for _ in range(6)])
            return Leaf(f"({self.trace}+{other.trace})")

    data = _objects([Leaf(label) for label in "abcdef"])
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), data)
    result = fast_sum(source, axis=axis)
    expected = ["(a+d)", "(b+x)", "(c+f)"] if axis == 0 else ["((a+b)+x)", "((d+e)+f)"]
    assert [value.trace for value in result._data] == expected
    assert source._data is not data
    assert all(value.trace == "z" for value in source._data)


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("kind", ["none", "object", "ok", "failed", "fatal", "warn"])
def test_final_external_addition_result_is_an_opaque_leaf(axis: int, kind: str) -> None:
    error: Err[Any] = Err(ErrorCode.NOT_FOUND, "数据而非传输 / Data, not transport")
    leaves: dict[str, Any] = {
        "none": None,
        "object": object(),
        "ok": Ok(object()),
        "failed": Failed(error),
        "fatal": Fatal((error,)),
        "warn": Warn(object(), error),
    }
    leaf = leaves[kind]
    calls: list[Any] = []

    class Input:
        def __add__(self, other: Input) -> Any:
            calls.append(other)
            return leaf

    values = [Input() for _ in range(4)]
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 2), _objects(values))
    result = fast_sum(source, axis=axis)
    assert result.shape.dims == (2,) and len(calls) == 2
    assert result._data[0] is leaf and result._data[1] is leaf
    assert all(source._data[position] is value for position, value in enumerate(values))


@pytest.mark.parametrize("fail_at", [0, 1, 2])
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        _UnformattableError,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_external_addition_stops_at_first_failure_and_keeps_exception_state(
    *, fail_at: int, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    calls: list[tuple[int, int]] = []
    outer: BaseException | None = None

    class Leaf:
        def __init__(self, position: int) -> None:
            self.position = position

        def __add__(self, other: Leaf) -> Leaf:
            assert sys.exception() is outer
            calls.append((self.position, other.position))
            if len(calls) == fail_at + 1:
                raise error
            return Leaf(self.position)

    values = [Leaf(position) for position in range(6)]
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), _objects(values))
    try:
        raise RuntimeError("先前处理中的异常 / Previously handled exception")
    except RuntimeError as handled:
        outer = handled
        with pytest.raises(error_type) as caught:
            fast_sum(source, axis=0)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    assert calls == [(0, 3), (1, 4), (2, 5)][: fail_at + 1]
    assert all(source._data[position] is value for position, value in enumerate(values))
    chain = []
    traceback = error.__traceback__
    while traceback is not None:
        chain.append(traceback)
        traceback = traceback.tb_next
    assert any(node is original for node in chain)
    assert any(node.tb_frame.f_code is Leaf.__add__.__code__ for node in chain)
