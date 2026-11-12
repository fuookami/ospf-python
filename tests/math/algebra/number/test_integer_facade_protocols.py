"""整数门面的动态命名空间与临时值生命周期。 / Dynamic namespaces and temporary lifetimes in integer facades."""

from __future__ import annotations

import builtins
import gc
import importlib
import weakref
from types import SimpleNamespace
from typing import Any

import pytest

from ospf_python import _native
from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger


@pytest.mark.parametrize("operation", ("safe_add", "safe_mul"))
def test_arithmetic_temporary_survives_clamp_failure_traceback(
    *, operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(NumericInteger.__module__)
    references: list[weakref.ReferenceType[Any]] = []
    error = RuntimeError()

    class Temporary:
        pass

    class Input:
        def __add__(self, right: Any) -> Any:
            result = Temporary()
            references.append(weakref.ref(result))
            return result

        __mul__ = __add__

    class Unvalidated(NumericInteger):
        def __post_init__(self) -> None:
            pass

    def failing(left: Any, right: Any) -> Any:
        del left, right
        raise error

    source = Unvalidated(7)
    object.__setattr__(source, "_value", Input())
    monkeypatch.setattr(module, "min", failing, raising=False)
    with pytest.raises(RuntimeError) as caught:
        getattr(source, operation)(3)
    assert caught.value is error
    gc.collect()
    assert len(references) == 1 and references[0]() is not None
    del caught
    error.__traceback__ = None
    gc.collect()
    assert references[0]() is None


@pytest.mark.parametrize("stage", ("second-read", "comparison", "assignment"))
def test_constructor_temporary_survives_late_failure_traceback(
    *, stage: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(NumericInteger.__module__)
    references: list[weakref.ReferenceType[Any]] = []
    error = RuntimeError()
    reads = 0

    class Temporary:
        def __ne__(self, other: Any) -> bool:
            if stage == "comparison":
                del self, other
                raise error
            return True

    class Traced(NumericInteger):
        def __getattribute__(self, name: str) -> Any:
            nonlocal reads
            if name == "_value":
                reads += 1
                if reads == 2 and stage == "second-read":
                    raise error
            return super().__getattribute__(name)

    class Setter:
        @staticmethod
        def __setattr__(*args: Any) -> None:
            del args
            raise error

    def minimum(left: Any, right: Any) -> Any:
        result = Temporary()
        references.append(weakref.ref(result))
        return result

    def maximum(left: Any, right: Any) -> Any:
        return right

    monkeypatch.setattr(module, "min", minimum, raising=False)
    monkeypatch.setattr(module, "max", maximum, raising=False)
    if stage == "assignment":
        monkeypatch.setattr(module, "object", Setter, raising=False)
    with pytest.raises(RuntimeError) as caught:
        Traced(7)
    assert caught.value is error
    gc.collect()
    assert len(references) == 1 and references[0]() is not None
    del caught
    error.__traceback__ = None
    gc.collect()
    assert references[0]() is None


@pytest.mark.parametrize("operation", ("safe_add", "safe_mul"))
def test_success_releases_named_temporaries_after_constructor(
    *, operation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(NumericInteger.__module__)
    events: list[str] = []
    published = object()

    class Temporary:
        def __init__(self, label: str) -> None:
            self.label = label

        def __del__(self) -> None:
            events.append(self.label)

    def constructor(value: Any) -> Any:
        assert value.label == "clamped"
        events.append("constructor")
        return published

    class Input:
        def __add__(self, right: Any) -> Any:
            monkeypatch.setattr(module, "NumericInteger", constructor)
            return Temporary("result")

        __mul__ = __add__

    class RHS:
        def __del__(self) -> None:
            events.append("rhs")

    def minimum(left: Any, right: Any) -> Any:
        return Temporary("clamped")

    def maximum(left: Any, right: Any) -> Any:
        return right

    source = NumericInteger(7)
    object.__setattr__(source, "_value", Input())
    monkeypatch.setattr(module, "min", minimum, raising=False)
    monkeypatch.setattr(module, "max", maximum, raising=False)
    assert getattr(source, operation)(RHS()) is published
    # result 与 clamped 的相对次序随解释器版本变化（CPython 3.15 先释放 clamped），
    # 那是临时对象销毁的实现细节，不在此断言；保留「构造最前、rhs 最后、四者都发生」。
    # The relative order of result/clamped varies by interpreter version and is a temporary-
    # destruction detail; keep construction first, rhs last, and all four occurring.
    assert events[0] == "constructor"
    assert events[-1] == "rhs"
    assert sorted(events) == ["clamped", "constructor", "result", "rhs"]


def test_facade_namespace_and_cycles_are_visible_to_gc() -> None:
    class Owner:
        pass

    owner = Owner()
    reference = weakref.ref(owner)
    namespace: dict[str, Any] = {"__builtins__": builtins.__dict__, "owner": owner}
    exec("def anchor(): pass", namespace)
    context = _native._public_integer.facade(
        reference=namespace["anchor"], domain="numeric_integer"
    )
    namespace["context"] = context
    assert gc.is_tracked(context)
    assert any(value is namespace for value in gc.get_referents(context))
    assert any(value is builtins.__dict__ for value in gc.get_referents(context))
    del owner, context, namespace
    gc.collect()
    assert reference() is None


def test_facade_uses_function_builtins_identity_and_live_global_overrides() -> None:
    class Original(ValueError):
        pass

    class Rebound(ValueError):
        pass

    class Global(ValueError):
        pass

    table: dict[str, Any] = {"ValueError": Original}
    namespace: dict[str, Any] = {"__builtins__": table}
    exec("def anchor(): pass", namespace)
    context = _native._public_integer.facade(
        reference=namespace["anchor"], domain="numeric_u_integer"
    )
    namespace["__builtins__"] = {"ValueError": Rebound}
    owner = SimpleNamespace(_value=-1)
    with pytest.raises(Original):
        context.initialize(owner)
    table["ValueError"] = Rebound
    with pytest.raises(Rebound):
        context.initialize(owner)
    namespace["ValueError"] = Global
    with pytest.raises(Global):
        context.initialize(owner)


def test_facade_missing_global_keeps_name_error_metadata() -> None:
    namespace: dict[str, Any] = {"__builtins__": {}}
    exec("def anchor(): pass", namespace)
    context = _native._public_integer.facade(
        reference=namespace["anchor"], domain="numeric_integer"
    )
    with pytest.raises(NameError) as caught:
        context.clamp_owner(SimpleNamespace(MIN_VALUE=0, MAX_VALUE=9, _value=7))
    assert caught.value.name == "max"
    assert caught.value.args == ("name 'max' is not defined",)


def test_clamp_callbacks_can_reenter_the_same_read_only_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(NumericInteger.__module__)
    entered = False
    calls: list[int] = []

    def minimum(left: Any, right: Any) -> Any:
        nonlocal entered
        calls.append(right)
        if not entered:
            entered = True
            assert NumericInteger(3).safe_add(4).value == 7
        return min(left, right)

    monkeypatch.setattr(module, "min", minimum, raising=False)
    assert NumericInteger(7).safe_add(2).value == 9
    assert calls == [7, 3, 7, 7, 9, 9]
    assert (Integer(7) + Integer(3)).value == 10
