"""公开 raw 扩展分派合同 / Public raw-extension dispatch contracts.

不授权默认 get/set 的 Result 切换或新的方括号异常政策。
These tests authorize neither the default Result cutover nor a new indexing policy.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest

from ospf_python.multiarray import (
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape1,
    Shape2,
    StorageOrder,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Warn


class _UnformattableError(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不得格式化外部异常 / Must not format external exceptions")


def _leaf(kind: str) -> Any:
    error: Err[Any] = Err(ErrorCode.NOT_FOUND, "数据而非传输 / Data, not transport")
    match kind:
        case "ok":
            return Ok(object())
        case "failed":
            return Failed(error)
        case "fatal":
            return Fatal((error,))
        case "warn":
            return Warn(object(), error)
        case "none":
            return None
        case _:
            return object()


@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("kind", ["ok", "failed", "fatal", "warn", "none", "object"])
@pytest.mark.parametrize("override", ["instance", "subclass"])
def test_explicit_raw_override_is_data_through_brackets_and_native_sampling(
    *, cls: type[Any], kind: str, override: str
) -> None:
    leaf = _leaf(kind)
    calls: list[tuple[int, ...]] = []
    inputs: list[Any] = []

    def raw_get(*indices: int) -> Any:
        calls.append(indices)
        return leaf

    def callback(value: Any) -> Any:
        inputs.append(value)
        return value

    def subclass_get(self: Any, *indices: int) -> Any:
        return raw_get(*indices)

    source_cls = (
        cls
        if override == "instance"
        else type("RawSubclass", (cls,), {"get": subclass_get})
    )
    source = source_cls(Shape1(1), np.array([7]))
    if override == "instance":
        source.get = raw_get
    assert source[0] is leaf and source[(0,)] is leaf
    mapped = MultiArrayView(source).map(callback)
    result = mapped.materialize()
    assert isinstance(result, Ok) and result.value._data[0] is leaf
    assert len(inputs) == 1 and inputs[0] is leaf
    assert calls == [(0,)] * 3
    replacement = object()
    source.get = lambda *indices: replacement
    assert source[0] is replacement
    assert mapped.materialize().unwrap()._data[0] is replacement


@pytest.mark.parametrize("key", [0, (0,)])
def test_bracket_write_does_not_call_a_named_set_override(key: Any) -> None:
    data = np.array([7], dtype=np.int16)
    source: Any = MutableMultiArray(Shape1(1), data)

    def forbidden(*args: Any) -> None:
        pytest.fail(
            "方括号写入不分派到命名 set / Bracket writes do not dispatch to named set"
        )

    source.set = forbidden
    source[key] = 9
    assert data.tolist() == [9]


@pytest.mark.parametrize("order", list(StorageOrder))
def test_raw_get_descriptor_is_resolved_per_coordinate_before_callback(
    order: StorageOrder,
) -> None:
    leaves = [object() for _ in range(4)]
    events: list[Any] = []
    lookups = 0

    class RawSource:
        shape = Shape2(2, 2, order)
        ndim = 2

        @property
        def get(self) -> Callable[..., Any]:
            nonlocal lookups
            ordinal = lookups
            lookups += 1
            events.append(("lookup", ordinal))

            def read(*indices: int) -> Any:
                events.append(("read", ordinal, indices))
                return leaves[ordinal]

            return read

    def callback(value: Any) -> Any:
        events.append(("callback", value))
        return value

    source: Any = RawSource()
    result = MultiArrayView(source).map(callback).materialize().unwrap()
    expected: list[Any] = []
    for ordinal, coordinates in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
        expected.extend(
            [
                ("lookup", ordinal),
                ("read", ordinal, coordinates),
                ("callback", leaves[ordinal]),
            ]
        )
    assert events == expected and lookups == 4
    permutation = [0, 1, 2, 3] if order is StorageOrder.ROW_MAJOR else [0, 2, 1, 3]
    assert all(
        result._data[index] is leaves[position]
        for index, position in enumerate(permutation)
    )
    assert result.shape is source.shape


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
def test_raw_get_descriptor_failure_stops_sampling_and_retains_external_error(
    *, fail_at: int, error_type: type[BaseException]
) -> None:
    error = error_type()
    events: list[Any] = []
    lookups = 0
    leaf = object()

    class RawSource:
        shape = Shape1(3)
        ndim = 1

        @property
        def get(self) -> Callable[..., Any]:
            nonlocal lookups
            ordinal = lookups
            lookups += 1
            events.append(("lookup", ordinal))
            if ordinal == fail_at:
                raise error

            def read(*indices: int) -> Any:
                events.append(("read", ordinal, indices))
                return leaf

            return read

    def callback(value: Any) -> Any:
        assert value is leaf
        events.append(("callback",))
        return value

    source: Any = RawSource()
    mapped = MultiArrayView(source).map(callback)
    if isinstance(error, Exception):
        result = mapped.materialize()
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.APPLICATION_ERROR
        assert result.error.value.error_class == "EXTERNAL_MATERIALIZATION"
        assert result.error.value.callback_exception is error
    else:
        with pytest.raises(error_type) as caught:
            mapped.materialize()
        assert caught.value is error
    expected: list[Any] = []
    for ordinal in range(fail_at):
        expected.extend(
            [("lookup", ordinal), ("read", ordinal, (ordinal,)), ("callback",)]
        )
    assert events == [*expected, ("lookup", fail_at)] and lookups == fail_at + 1
    traceback = error.__traceback__
    assert traceback is not None
    while traceback.tb_next is not None:
        traceback = traceback.tb_next
    descriptor = vars(RawSource)["get"]
    assert isinstance(descriptor, property) and descriptor.fget is not None
    assert traceback.tb_frame.f_code is descriptor.fget.__code__
