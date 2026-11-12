"""普通视图元数据的首错和释放顺序 / First-error and release ordering of plain-view metadata."""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pytest

from ospf_python.multiarray import MultiArray, MultiArrayView, StorageOrder
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


class _Integer:
    def __init__(
        self, *, value: int | BaseException, tag: str, events: list[str]
    ) -> None:
        self.value, self.tag, self.events = value, tag, events

    def __index__(self) -> int:
        self.events.append("index:" + self.tag)
        if isinstance(self.value, BaseException):
            raise self.value
        return self.value


class _Iterator:
    def __init__(self, *, values: list[Any], events: list[str]) -> None:
        self.values, self.events = values, events
        self.position = 0

    def __iter__(self) -> _Iterator:
        return self

    def __next__(self) -> Any:
        if self.position == len(self.values):
            self.events.append("end")
            raise StopIteration
        index = self.position
        self.position += 1
        self.events.append(f"next:{index}")
        return self.values[index]

    def __del__(self) -> None:
        self.events.append("iterator.release")


class _Dimensions:
    def __init__(self, *, values: list[Any], events: list[str]) -> None:
        self.values, self.events = values, events

    def __iter__(self) -> _Iterator:
        self.events.append("iter")
        return _Iterator(values=self.values, events=self.events)

    def __del__(self) -> None:
        self.events.append("sequence.release")


class _Shape:
    def __init__(
        self, *, values: list[Any], events: list[str], order: StorageOrder
    ) -> None:
        self.values, self.events, self.order = values, events, order

    @property
    def dims(self) -> _Dimensions:
        self.events.append("dims")
        return _Dimensions(values=self.values, events=self.events)

    @property
    def storage_order(self) -> StorageOrder:
        self.events.append("order")
        return self.order

    def flat_index(self, *indices: int) -> int:
        pytest.fail(
            "恒等区域不得调用索引协议 / Identity regions must not call indexing"
        )


class _View(MultiArrayView):
    events: list[str]

    def __getattribute__(self, name: str) -> Any:
        if name == "_offsets":
            object.__getattribute__(self, "events").append("offsets")
        return object.__getattribute__(self, name)


def _view(
    *,
    values: list[Any],
    events: list[str],
    order: StorageOrder,
    offsets: tuple[Any, ...] = (0, 0),
) -> _View:
    shape = _Shape(values=values, events=events, order=order)
    source: MultiArray[Any, Any] = MultiArray(shape, np.arange(6))
    view = object.__new__(_View)
    vars(view).update(_source=source, _offsets=offsets, events=events)
    return view


def _consumed_prefix(*, count: int, boolean: bool = False) -> list[str]:
    events = ["dims", "iter"]
    for index in range(count):
        events.append(f"next:{index}")
        if not boolean:
            events.append(f"index:{index}")
    return events + ["iterator.release", "sequence.release"]


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    ("values", "code"),
    [
        ((0,), ErrorCode.ILLEGAL_ARGUMENT),
        ((-1,), ErrorCode.ILLEGAL_ARGUMENT),
        ((True,), ErrorCode.ILLEGAL_ARGUMENT),
        ((sys.maxsize + 1,), ErrorCode.OVERFLOW),
        ((1 << 128,), ErrorCode.OVERFLOW),
        ((sys.maxsize, 2), ErrorCode.OVERFLOW),
    ],
)
def test_first_dimension_failure_stops_later_protocols_and_releases_iterator(
    *, order: StorageOrder, values: tuple[int, ...], code: ErrorCode
) -> None:
    events: list[str] = []
    dimensions = [
        value
        if isinstance(value, bool)
        else _Integer(value=value, tag=str(index), events=events)
        for index, value in enumerate(values)
    ]
    dimensions.append(
        _Integer(
            value=AssertionError("Later dimension consumed"), tag="later", events=events
        )
    )
    result = _view(values=dimensions, events=events, order=order).materialize()
    assert isinstance(result, Failed) and result.error.code is code
    assert events == _consumed_prefix(count=len(values), boolean=values == (True,))


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        RuntimeError,
        StopIteration,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_dimension_integer_exception_is_not_replaced_by_later_validation(
    *, order: StorageOrder, error_type: type[BaseException]
) -> None:
    error = error_type("External dimension protocol")
    events: list[str] = []
    dimensions = [
        _Integer(value=error, tag="0", events=events),
        _Integer(
            value=AssertionError("Later dimension consumed"), tag="later", events=events
        ),
    ]
    view = _view(values=dimensions, events=events, order=order)
    if isinstance(error, Exception):
        result = view.materialize()
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.APPLICATION_ERROR
        assert result.error.value.callback_exception is error
    else:
        with pytest.raises(error_type) as caught:
            view.materialize()
        assert caught.value is error
    assert events == _consumed_prefix(count=1)


@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("offset_protocol", [False, True])
def test_complete_dimensions_release_before_order_and_offset_protocols(
    *, order: StorageOrder, offset_protocol: bool
) -> None:
    events: list[str] = []
    dimensions = [
        _Integer(value=dim, tag=str(axis), events=events)
        for axis, dim in enumerate((2, 3))
    ]
    offsets = (
        tuple(
            _Integer(value=0, tag=f"offset:{axis}", events=events) for axis in range(2)
        )
        if offset_protocol
        else (0, 0)
    )
    view = _view(values=dimensions, events=events, order=order, offsets=offsets)
    result = view.materialize().unwrap()
    expected = _consumed_prefix(count=2)
    expected.insert(-2, "end")
    expected += ["order", "offsets"]
    if offset_protocol:
        expected += ["index:offset:0", "index:offset:1"]
    assert events == expected
    assert result.shape is view._source.shape
    np.testing.assert_array_equal(result._data, view._source._data)
    assert not np.shares_memory(result._data, view._source._data)
