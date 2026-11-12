"""窄派发公开混沌类的差分回归：派发路径与出厂内核逐位且同形。

Differential regression for the narrow public dispatch: inside the covered domain the delegated
path must be bit- and shape-identical to the shipped Python kernel, and every input outside that
domain must keep running the shipped kernel unchanged.
"""

from __future__ import annotations

import dataclasses
import importlib
import math
import random
from typing import Any

import numpy as np
import pytest

from ospf_python import _native

# (系统名, 公共类模块, 参数个数, 状态维度)
# (system, public module, parameter count, state dimension)
Row = tuple[str, str, int, int]
DISPATCHED: list[Row] = [
    ("BurkeShawAttractor", "ospf_python.math.chaotic.burke_shaw_attractor", 3, 3),
    (
        "ChenCelikovskyAttractor",
        "ospf_python.math.chaotic.chen_celikovsky_attractor",
        4,
        3,
    ),
    ("ChenLeeAttractor", "ospf_python.math.chaotic.chen_lee_attractor", 4, 3),
    ("ChenSystem", "ospf_python.math.chaotic.chen_system", 4, 3),
    ("ChuaCircuit", "ospf_python.math.chaotic.chua_circuit", 5, 3),
]
IDS = [row[0] for row in DISPATCHED]
SAMPLES = 300
SEED = 20261030

#: 已证明可逐位委托的三种输入风味：float64 数组、内置 float 的 list、内置 float 的 tuple。
#: The three input flavours proven delegable: float64 arrays, lists and tuples of builtin floats.
FLAVORS: dict[str, Any] = {
    "ndarray": lambda values: np.asarray(values, dtype=np.float64),
    "list": lambda values: list(values),
    "tuple": lambda values: tuple(values),
}


def _unreachable(**_: object) -> Any:
    """原生入口被触碰时立刻暴露。 / Fail loudly when the native entry is touched."""
    raise AssertionError("the native entry was reached")


def _forced(**_: object) -> tuple[None, str]:
    """让原生入口永远报告失败，从而强制回落到出厂内核。"""
    return None, "forced fallback to the shipped kernel"


def _bits(value: Any) -> tuple[str, tuple[int, ...], bytes]:
    """返回形态的可比身份：dtype、形状与逐位内容。 / Comparable identity of a return."""
    array = np.asarray(value)
    return array.dtype.str, array.shape, array.tobytes()


def _instance(*, row: Row) -> Any:
    """按显式参数构造公开类实例。 / Build the public instance from explicit parameters."""
    system, module, arity, _ = row
    params = [0.25 + 0.125 * index for index in range(arity)]
    return getattr(importlib.import_module(module), system)(*params)


def _step(*, row: Row, container: Any, target: Any = None) -> Any:
    """用公开类对容器执行一次单步。 / Take one public step for a container."""
    target = _instance(row=row) if target is None else target
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return target(container)


def _state(*, row: Row, rng: random.Random, scale: float = 4.0) -> list[float]:
    """生成一组随机状态。 / Draw one random state vector."""
    return [rng.uniform(-scale, scale) for _ in range(row[3])]


def _iterate(*, target: Any, start: np.ndarray, steps: int) -> list[Any]:
    """迭代若干步并抑制溢出告警。 / Iterate several steps, silencing overflow warnings."""
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return target.iterate(start, n=steps)


@pytest.mark.parametrize("row", DISPATCHED, ids=IDS)
@pytest.mark.parametrize("flavor", sorted(FLAVORS))
def test_dispatch_matches_shipped_kernel_bit_for_bit(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: Row,
    flavor: str,
) -> None:
    """窄域内的三种输入风味都必须与出厂内核逐位、同 dtype、同形状、同容器类型。"""
    rng = random.Random(SEED)
    build = FLAVORS[flavor]
    target = _instance(row=row)
    containers = [build(_state(row=row, rng=rng)) for _ in range(SAMPLES)]
    monkeypatch.setattr(_native, "_chaotic_system_step", _forced)
    expected = [_step(row=row, container=item, target=target) for item in containers]
    monkeypatch.undo()
    actual = [_step(row=row, container=item, target=target) for item in containers]
    for got, want in zip(actual, expected, strict=True):
        assert type(got) is type(want)
        assert _bits(got) == _bits(want)


@pytest.mark.parametrize("row", DISPATCHED, ids=IDS)
def test_wide_domain_inputs_stay_on_the_shipped_kernel(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: Row,
) -> None:
    """`float32`、整数、object、非有限值与列向量一律不得触碰原生入口。"""
    dimension = row[3]
    finite = [0.7 + 0.1 * index for index in range(dimension)]
    monkeypatch.setattr(_native, "_chaotic_system_step", _unreachable)
    for container in (
        np.asarray(finite, dtype=np.float32),
        np.asarray([index + 1 for index in range(dimension)], dtype=np.int64),
        [index + 1 for index in range(dimension)],
        [np.float64(item) for item in finite],
        np.asarray(finite, dtype=object),
        np.asarray([math.nan] * dimension),
        np.asarray([math.inf] * dimension),
        np.asarray(finite).reshape((dimension, 1)),
    ):
        _step(row=row, container=container)
    monkeypatch.undo()
    # 委托会把结果统一成 float64 的 (dimension,) 向量，保持原样即证明走的是出厂内核。
    # Delegation always yields float64 `(dimension,)`, so a preserved dtype or shape proves
    # the shipped kernel ran.
    narrow = _step(row=row, container=np.asarray(finite, dtype=np.float64))
    assert narrow.dtype == np.dtype(np.float64)
    assert narrow.shape == (dimension,)
    wide = _step(row=row, container=np.asarray(finite, dtype=np.float32))
    assert wide.dtype == np.dtype(np.float32)
    column = _step(row=row, container=np.asarray(finite).reshape((dimension, 1)))
    assert column.shape == (dimension, 1)


@pytest.mark.parametrize("row", DISPATCHED, ids=IDS)
def test_oversized_state_falls_back_to_the_shipped_kernel(*, row: Row) -> None:
    """多一分量的状态不会被委托成少一分量的结果，必须保持出厂的报错行为。"""
    state = np.asarray([0.7, 0.8, 0.9, 1.0], dtype=np.float64)
    with pytest.raises(ValueError, match="broadcast"):
        _step(row=row, container=state)


@pytest.mark.parametrize("row", DISPATCHED, ids=IDS)
@pytest.mark.parametrize("replacement", [1, math.nan], ids=["integer", "nonfinite"])
def test_out_of_domain_parameters_stay_on_the_shipped_kernel(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: Row,
    replacement: float,
) -> None:
    """参数字段一旦超出窄域，整个单步必须回落到出厂内核。"""
    target = _instance(row=row)
    field = dataclasses.fields(target)[0].name
    target = dataclasses.replace(target, **{field: replacement})
    state = np.asarray([0.7 + 0.1 * index for index in range(row[3])], dtype=np.float64)
    monkeypatch.setattr(_native, "_chaotic_system_step", _unreachable)
    result = _step(row=row, container=state, target=target)
    assert result.shape == (row[3],)


@pytest.mark.parametrize("row", DISPATCHED, ids=IDS)
def test_iterate_matches_shipped_kernel(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: Row,
) -> None:
    """多步迭代必须与出厂内核逐步逐位一致，中途溢出后结果也不得改变。"""
    rng = random.Random(SEED)
    for scale in (4.0, 1e150):
        target = _instance(row=row)
        start = np.asarray(_state(row=row, rng=rng, scale=scale), dtype=np.float64)
        monkeypatch.setattr(_native, "_chaotic_system_step", _forced)
        expected = _iterate(target=target, start=start.copy(), steps=60)
        monkeypatch.undo()
        actual = _iterate(target=target, start=start.copy(), steps=60)
        assert len(actual) == len(expected)
        for got, want in zip(actual, expected, strict=True):
            assert _bits(got) == _bits(want)


@pytest.mark.parametrize("row", DISPATCHED, ids=IDS)
def test_dispatch_does_not_mutate_the_caller_state(*, row: Row) -> None:
    """委托路径不得就地改写调用方持有的数组。"""
    state = np.asarray(_state(row=row, rng=random.Random(SEED)), dtype=np.float64)
    snapshot = state.copy()
    result = _step(row=row, container=state)
    assert state.tobytes() == snapshot.tobytes()
    assert result is not state
    assert result.shape == (row[3],)
    assert result.dtype == np.dtype(np.float64)
