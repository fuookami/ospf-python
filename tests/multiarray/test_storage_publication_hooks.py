"""存储发布不绕过动态构造器。 / Storage publication must honor dynamic constructors."""

from __future__ import annotations

import subprocess
import sys
from typing import Any

import numpy as np
import pytest

from ospf_python._binding import storage_transform
from ospf_python.multiarray import DynShape, MultiArray, MutableMultiArray, Shape2
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.parametrize("owner", ["shape", "result"])
@pytest.mark.parametrize("hook", ["__new__", "__init__"])
@pytest.mark.parametrize("before_binding", [False, True])
@pytest.mark.parametrize("mutable", [False, True])
def test_flatten_honors_current_constructors_in_fresh_interpreter(
    *, owner: str, hook: str, before_binding: bool, mutable: bool
) -> None:
    script = f"""
import os
directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p] if os.name == 'nt' else []
import numpy as np
from ospf_python.multiarray.shape import DynShape, Shape1
from ospf_python.utils.functional.result import Ok
if not {before_binding!r}:
    import ospf_python._binding.storage_transform
owner = DynShape if {owner!r} == 'shape' else Ok
calls = []
original = getattr(owner, {hook!r})
if {hook!r} == '__new__':
    def construct(cls, *args, **kwargs):
        calls.append('new')
        return original(cls)
    owner.__new__ = staticmethod(construct)
else:
    def construct(self, *args, **kwargs):
        calls.append('init')
        original(self, *args, **kwargs)
    owner.__init__ = construct
from ospf_python.multiarray import MultiArray, MutableMultiArray
storage = MutableMultiArray if {mutable!r} else MultiArray
source = storage(Shape1(6), np.arange(6))
result = source.flatten()
assert result.unwrap()._data.tolist() == list(range(6))
assert calls == [{"new" if hook == "__new__" else "init"!r}], calls
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("count", [10_000, sys.maxsize, sys.maxsize + 1, 1 << 200])
def test_flatten_plans_once_and_preserves_count_and_shape_factory(
    *, storage: type[Any], count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[Any] = []
    counted = storage_transform._flatten_counted

    class Metadata:
        @property
        def size(self) -> int:
            events.append("size")
            return count

    def shape_factory(*, dims: tuple[int, ...]) -> DynShape:
        events.append("shape")
        assert dims[0] is count
        return DynShape(dims=dims)

    def track_counted(*args: Any, **kwargs: Any) -> Any:
        events.append("native")
        assert args[1] is count
        return counted(*args, **kwargs)

    monkeypatch.setattr(storage_transform, "DynShape", shape_factory)
    monkeypatch.setattr(storage_transform, "_flatten_counted", track_counted)
    source = storage(Metadata(), np.arange(3))
    result = source.flatten().unwrap()
    assert result.shape.dims[0] is count
    assert result._data.tolist() == [0, 1, 2]
    assert events == ["size", "native", "shape"]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
def test_standard_shape2_flatten_uses_exact_integer_fields(
    storage: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    source = storage(Shape2(2, 3), np.arange(6))
    checked = storage_transform._flatten_value_result_checked
    events: list[tuple[str, int]] = []

    def track_checked(*args: Any, **kwargs: Any) -> Any:
        events.append(("native", args[1]))
        return checked(*args, **kwargs)

    def forbidden(self: Shape2) -> int:
        pytest.fail(
            "标准二维展平不得读取 size 属性 / Standard 2-D flatten must not read size"
        )

    monkeypatch.setattr(Shape2, "size", property(forbidden))
    monkeypatch.setattr(
        storage_transform, "_flatten_value_result_checked", track_checked
    )
    assert source.flatten().unwrap()._data.tolist() == list(range(6))
    assert events == [("native", 6)]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("implementation", ["legacy-expression", "native"])
def test_flatten_releases_replaced_shape_factory_before_copy(
    *, storage: type[Any], implementation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    bridge: Any = storage_transform

    class ShapeFactory:
        def __call__(self, *, dims: tuple[int, ...]) -> DynShape:
            events.append("shape")
            bridge.DynShape = DynShape
            return DynShape(dims=dims)

        def __del__(self) -> None:
            events.append("release-shape-factory")

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            return np.arange(3)

    source = storage(DynShape((3,)), Data())
    monkeypatch.setattr(storage_transform, "DynShape", ShapeFactory())
    if implementation == "native":
        value = source.flatten().unwrap()
    else:
        shape = bridge.DynShape(dims=(source.size,))
        value = MultiArray(shape, source._data.copy())
    assert value._data.tolist() == [0, 1, 2]
    assert events == ["shape", "release-shape-factory", "copy"]


def test_counted_protocol_keeps_the_original_three_argument_form() -> None:
    source: Any = MultiArray(DynShape((3,)), np.arange(3))
    result = storage_transform._protocol.flatten_counted(
        source, source.size, lambda: MultiArray
    )
    assert result.unwrap()._data.tolist() == [0, 1, 2]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
def test_flatten_observes_result_init_hook_installed_during_copy(
    storage: type[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    original = Ok.__init__

    def construct(self: Any, value: Any) -> None:
        events.append("result")
        original(self, value)

    class Data:
        def copy(self) -> Any:
            events.append("copy")
            monkeypatch.setattr(Ok, "__init__", construct)
            return np.arange(3)

    source = storage(DynShape((3,)), Data())
    assert source.flatten().unwrap()._data.tolist() == [0, 1, 2]
    assert events == ["copy", "result"]


@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("error_type", [ValueError, KeyboardInterrupt])
def test_shape_factory_failure_keeps_exception_identity(
    *,
    storage: type[Any],
    error_type: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = error_type("shape factory")

    def fail(*, dims: tuple[int, ...]) -> DynShape:
        raise error

    source = storage(DynShape((3,)), np.arange(3))
    monkeypatch.setattr(storage_transform, "DynShape", fail)
    if isinstance(error, Exception):
        result = source.flatten()
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
    else:
        with pytest.raises(error_type) as caught:
            source.flatten()
        assert caught.value is error
