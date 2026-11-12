"""公开浮点原生默认路径与失败边界。 / Public floating native defaults and failure boundaries."""

from __future__ import annotations

import builtins
import gc
import importlib
import operator
import weakref
from typing import Any

import pytest

from ospf_python import _native
from ospf_python.math.algebra.number.floating import Floating


def test_public_float_arithmetic_and_comparison_use_native_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module(Floating.__module__)
    original = module._floating
    calls: list[str] = []

    class Proxy:
        def __getattr__(self, name: str) -> Any:
            def invoke(*args: Any, **kwargs: Any) -> Any:
                calls.append(kwargs.get("operation", name))
                return getattr(original, name)(*args, **kwargs)

            return invoke

    monkeypatch.setattr(module, "_floating", Proxy())
    assert (Floating(7.0) + Floating(3.0)).value == 10.0
    assert (Floating(7.0) - Floating(3.0)).value == 4.0
    assert (Floating(7.0) * Floating(3.0)).value == 21.0
    assert (Floating(7.0) / Floating(2.0)).value == 3.5
    assert (-Floating(7.0)).value == -7.0
    assert Floating(7.0) > Floating(3.0)
    assert calls == ["add", "subtract", "multiply", "eq", "divide", "negated", "gt"]


@pytest.mark.parametrize(
    "operation", (operator.add, operator.sub, operator.mul, operator.truediv)
)
def test_native_failure_is_not_retried_with_the_old_python_operation(
    *, operation: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(Floating.__module__)
    original = module._floating
    error = RuntimeError()

    class Broken:
        relation = original.relation

        def binary(self, **kwargs: Any) -> Any:
            raise error

    monkeypatch.setattr(module, "_floating", Broken())
    with pytest.raises(RuntimeError) as caught:
        operation(Floating(7.0), Floating(3.0))
    assert caught.value is error


def test_native_helper_does_not_retain_dtos_or_external_payloads() -> None:
    class Payload:
        def __add__(self, other: Any) -> float:
            return 10.0

    payload: Any = Payload()
    owner, other = Floating(payload), Floating(3.0)
    references = [weakref.ref(value) for value in (payload, owner, other)]
    assert (owner + other).value == 10.0
    assert gc.is_tracked(_native._public_floating)
    assert {id(value) for value in gc.get_referents(_native._public_floating)} == {
        id(type(_native._public_floating)),
        id(builtins.min),
        id(builtins.max),
    }
    assert len(gc.get_referents(_native._public_floating)) == 3
    del payload, owner, other
    gc.collect()
    assert all(reference() is None for reference in references)
