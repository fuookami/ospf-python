"""求和特殊协议解析合同。 / Summation special-protocol resolution contracts.

保护自然入口的既有扩展行为，不代表候选默认切换。
Protect existing natural-entry extensions, not acceptance of a candidate cutover.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pytest

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.multiarray import MultiArray, Shape2


class _Poison(ValueError):
    def __str__(self) -> str:
        raise AssertionError("不格式化原异常 / Never format the original exception")


@pytest.mark.parametrize("dtype", ["int16", "float16", "float64", "complex128"])
@pytest.mark.parametrize("axis", [0, 1, ()])
@pytest.mark.parametrize("style", ["inherited", "reassigned"])
def test_inherited_and_explicitly_reassigned_ndarray_defaults_preserve_values(
    *, dtype: str, axis: Any, style: str
) -> None:
    class Inherited(np.ndarray[Any, Any]):
        pass

    cls = (
        Inherited
        if style == "inherited"
        else type(
            "Reassigned",
            (Inherited,),
            {
                "sum": np.ndarray.sum,
                "__array_function__": np.ndarray.__array_function__,
                "__array_ufunc__": np.ndarray.__array_ufunc__,
            },
        )
    )
    data = np.arange(6).astype(dtype)
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), data.view(cls))
    result = fast_sum(source, axis=axis)
    expected = np.asarray(np.sum(data.reshape(2, 3), axis=axis))
    assert result.shape.dims == expected.shape
    assert result._data.dtype == expected.dtype
    np.testing.assert_array_equal(result._data, expected.reshape(-1))
    assert not np.shares_memory(result._data, data)


@pytest.mark.parametrize("kind", ["function", "ufunc"])
@pytest.mark.parametrize("mode", ["all", "axis", "oversized"])
def test_special_descriptors_bind_on_the_type_and_receive_explicit_self(
    *, kind: str, mode: str
) -> None:
    events: list[str] = []
    flat = np.array([13, 17])

    class Axis:
        def __index__(self) -> int:
            pytest.fail("扩展先于轴解析 / Extension precedes axis parsing")

    axis: Any = (
        None
        if mode == "all"
        else Axis()
        if mode == "axis"
        else tuple(Axis() for _ in range(65))
    )

    class Output:
        @property
        def shape(self) -> tuple[int, ...]:
            events.append("shape")
            return (2,)

        def flatten(self) -> Any:
            events.append("flatten")
            return flat

        def __float__(self) -> float:
            events.append("float")
            return 31.0

    class Descriptor:
        def __get__(self, *arguments: Any) -> Any:
            instance, owner = arguments
            assert instance is None
            events.append("descriptor")

            def implementation(*args: Any, **kwargs: Any) -> Any:
                assert type(args[0]) is owner
                if kind == "function":
                    assert len(args) == 5 and args[1] is np.sum
                    assert args[2] == (owner,) and args[3][0] is args[0]
                    assert args[4] == ({} if axis is None else {"axis": axis})
                    assert kwargs == {}
                else:
                    assert len(args) == 4 and args[1] is np.add
                    assert args[2] == "reduce" and args[3] is args[0]
                    assert kwargs == {
                        "axis": axis,
                        "dtype": None,
                        "keepdims": False,
                        "where": True,
                    }
                events.append("call")
                return Output()

            return implementation

    attribute = "__array_function__" if kind == "function" else "__array_ufunc__"
    cls = type("Special", (np.ndarray,), {attribute: Descriptor()})
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(cls))
    result = fast_sum(source, axis=axis)
    if axis is None:
        assert result == 31.0 and events == ["descriptor", "call", "float"]
    else:
        assert result._data is flat
        assert events == ["descriptor", "call", "shape", "flatten"]


@pytest.mark.parametrize("axis", [None, 1])
def test_instance_special_shadows_are_ignored_but_normal_sum_is_observed(
    axis: Any,
) -> None:
    flat = np.array([13, 17])

    class Inherited(np.ndarray[Any, Any]):
        pass

    data: Any = np.arange(6).view(Inherited)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("忽略实例特殊属性 / Ignore instance special attributes")

    data.__array_function__ = forbidden
    data.__array_ufunc__ = forbidden
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), data)
    result = fast_sum(source, axis=axis)
    if axis is None:
        assert result == 15.0
    else:
        np.testing.assert_array_equal(result._data, [3, 12])
    calls: list[Any] = []

    class Output:
        shape = (2,)

        def flatten(self) -> Any:
            return flat

        def __float__(self) -> float:
            return 37.0

    class Method(Inherited):
        def reshape(self, *args: Any, **kwargs: Any) -> Any:
            result = super().reshape(*args, **kwargs)

            def custom(**kwargs: Any) -> Any:
                calls.append(kwargs)
                return Output()

            result.sum = custom
            return result

    source = MultiArray(Shape2(2, 3), np.arange(6).view(Method))
    result = fast_sum(source, axis=axis)
    assert calls == [{"axis": axis, "out": None}]
    if axis is None:
        assert result == 37.0
    else:
        assert result._data is flat


@pytest.mark.parametrize("kind", ["function", "ufunc"])
@pytest.mark.parametrize(
    "error_type",
    [
        ValueError,
        TypeError,
        AttributeError,
        RuntimeError,
        StopIteration,
        _Poison,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ],
)
def test_descriptor_failures_keep_original_exception_and_handled_state(
    *, kind: str, error_type: type[BaseException]
) -> None:
    error = error_type()
    try:
        raise error
    except BaseException:
        original = error.__traceback__
    outer = RuntimeError("外层处理中异常 / Outer handled exception")
    calls: list[str] = []

    class Descriptor:
        def __get__(self, *args: Any) -> Any:
            assert args[0] is None and sys.exception() is outer
            calls.append("descriptor")
            raise error

    class Axis:
        def __index__(self) -> int:
            pytest.fail("失败分派后不解析轴 / No axis parsing after failed dispatch")

    attribute = "__array_function__" if kind == "function" else "__array_ufunc__"
    cls = type("Special", (np.ndarray,), {attribute: Descriptor()})
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(cls))
    axis: Any = Axis()
    try:
        raise outer
    except RuntimeError:
        with pytest.raises(error_type) as caught:
            fast_sum(source, axis=axis)
        assert caught.value is error and error.__context__ is outer
        assert sys.exception() is outer
    assert calls == ["descriptor"]
    nodes = []
    node = error.__traceback__
    while node is not None:
        nodes.append(node)
        node = node.tb_next
    assert any(node is original for node in nodes)
    assert any(node.tb_frame.f_code is Descriptor.__get__.__code__ for node in nodes)


@pytest.mark.parametrize(
    "case", ["function_refused", "function_none", "ufunc_refused", "ufunc_none"]
)
@pytest.mark.parametrize("mode", ["all", "oversized"])
def test_declined_or_disabled_protocol_never_parses_axes(
    *, case: str, mode: str
) -> None:
    class Axis:
        def __index__(self) -> int:
            pytest.fail(
                "协议拒绝后不能解析轴 / Never parse axes after protocol refusal"
            )

    axis: Any = None if mode == "all" else tuple(Axis() for _ in range(65))
    attribute = (
        "__array_function__" if case.startswith("function") else "__array_ufunc__"
    )
    implementation = None if case.endswith("none") else lambda *a, **k: NotImplemented
    cls = type("Declined", (np.ndarray,), {attribute: implementation})
    source: MultiArray[Any, Shape2] = MultiArray(Shape2(2, 3), np.arange(6).view(cls))
    with pytest.raises(TypeError):
        fast_sum(source, axis=axis)


def test_protocol_rebinding_is_observed_on_each_call() -> None:
    calls: list[int] = []

    class Function(np.ndarray[Any, Any]):
        def __array_function__(self, *args: Any, **kwargs: Any) -> Any:
            calls.append(1)
            return 13

    source: MultiArray[Any, Shape2] = MultiArray(
        Shape2(2, 3), np.arange(6).view(Function)
    )
    assert fast_sum(source) == 13.0

    def replacement(*args: Any, **kwargs: Any) -> Any:
        calls.append(2)
        return 17

    dynamic_type: Any = Function
    dynamic_type.__array_function__ = replacement
    assert fast_sum(source) == 17.0 and calls == [1, 2]
