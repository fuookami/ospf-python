"""普通视图外部异常的解释器状态 / Interpreter exception state at the plain-view boundary."""

from __future__ import annotations

import sys
from typing import Any, cast

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding import shared_view
from ospf_python.multiarray import MultiArray, MultiArrayView, Shape2, StorageOrder
from ospf_python.multiarray import multi_array_view as view_module
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.parametrize(
    "stage", ["copy", "resolve", "construct", "success", "failure"]
)
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
def test_external_failure_retains_handled_exception_and_user_frames(
    *, stage: str, error_type: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    class Unprintable:
        def __str__(self) -> str:
            pytest.fail("不得格式化外部异常 / Do not format external exceptions")

        def __repr__(self) -> str:
            pytest.fail("不得格式化外部异常 / Do not format external exceptions")

    error = type("External", (Unprintable, error_type), {})()
    observed: list[BaseException | None] = []

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    def publish(value: Any) -> Any:
        observed.append(sys.exception())
        assert sys.exception() is error
        return Failed(value)

    class Data:
        def copy(self) -> Any:
            return fail() if stage == "copy" else np.arange(12)

    shape = Shape2(3, 4)
    source: MultiArray[Any, Shape2] = MultiArray(shape, cast("Any", Data()))
    view = MultiArrayView(source, offsets=(1, 1))
    monkeypatch.setattr(shared_view, "Failed", publish)
    if stage == "resolve":
        monkeypatch.setattr(view_module, "_materialized_constructor", fail)
    elif stage == "construct":
        monkeypatch.setattr(view_module, "MultiArray", fail)
    elif stage in ("success", "failure"):
        protocol = _native._SharedView(
            shape_types=shared_view._SHAPE_TYPES,
            row_major=StorageOrder.ROW_MAJOR,
            column_major=StorageOrder.COLUMN_MAJOR,
            success=fail if stage == "success" else Ok,
            failure=fail if stage == "failure" else shared_view._native_failure,
        )
        monkeypatch.setattr(shared_view, "_protocol", protocol)
        if stage == "failure":
            object.__setattr__(shape, "d0", 0)

    previous = LookupError("原有处理状态 / Previous handled exception")
    outer = sys.exception()
    try:
        raise previous
    except LookupError:
        if issubclass(error_type, Exception):
            result = view.materialize()
            assert isinstance(result, Failed)
            assert result.error.value.callback_exception is error
            assert observed == [error]
        else:
            with pytest.raises(error_type) as caught:
                view.materialize()
            assert caught.value is error and observed == []
        assert sys.exception() is previous
    assert sys.exception() is outer and error.__context__ is previous
    frames = []
    traceback = error.__traceback__
    while traceback is not None:
        frames.append(traceback.tb_frame.f_code.co_name)
        traceback = traceback.tb_next
    assert "fail" in frames


def test_external_error_publisher_failure_is_not_recaught(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original, secondary = ValueError("external"), RuntimeError("publisher")

    class Data:
        def copy(self) -> Any:
            raise original

    def fail_publication(value: Any) -> Any:
        assert sys.exception() is original
        raise secondary

    monkeypatch.setattr(shared_view, "Failed", fail_publication)
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(3, 4), cast("Any", Data()))
    with pytest.raises(RuntimeError) as caught:
        MultiArrayView(source).materialize()
    assert caught.value is secondary and secondary.__context__ is original


def test_protocol_method_is_captured_before_the_shape_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second, token = object(), object(), object()
    events: list[str] = []
    view = MultiArrayView(MultiArray(Shape2(3, 4), np.arange(12)))

    class Delegate:
        @property
        def materialize(self) -> Any:
            events.append("method")
            monkeypatch.setattr(shared_view, "DynShape", first)

            def operation(**kwargs: Any) -> Any:
                events.append("call")
                assert kwargs["owner"] is view
                assert kwargs["make_shape"] is first
                assert kwargs["resolve"] is view_module._materialized_constructor
                monkeypatch.setattr(shared_view, "DynShape", second)
                return token

            return operation

    monkeypatch.setattr(shared_view, "_protocol", Delegate())
    assert view.materialize() is token
    assert events == ["method", "call"] and vars(shared_view)["DynShape"] is second
