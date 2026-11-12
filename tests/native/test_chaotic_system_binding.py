"""混沌系统单步候选的逐位随机差分回归。

Randomized bit-exact differential regression for the pinned Rust chaotic step candidates.
"""

from __future__ import annotations

import importlib
import math
import random
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.chaotic_system import SUPPORTED_SYSTEMS, chaotic_system_step

# (系统名, 公共类模块, 参数个数, 状态维度, 出厂调用方法, 调用形状)
# (system, public module, parameter count, state dimension, step method, call shape)
SYSTEMS = [
    (
        "BurkeShawAttractor",
        "ospf_python.math.chaotic.burke_shaw_attractor",
        3,
        3,
        "__call__",
        "ndarray",
    ),
    (
        "ChenCelikovskyAttractor",
        "ospf_python.math.chaotic.chen_celikovsky_attractor",
        4,
        3,
        "__call__",
        "ndarray",
    ),
    (
        "ChenLeeAttractor",
        "ospf_python.math.chaotic.chen_lee_attractor",
        4,
        3,
        "__call__",
        "ndarray",
    ),
    ("ChenSystem", "ospf_python.math.chaotic.chen_system", 4, 3, "__call__", "ndarray"),
    (
        "ChuaCircuit",
        "ospf_python.math.chaotic.chua_circuit",
        5,
        3,
        "__call__",
        "ndarray",
    ),
    (
        "DequanLiAttractor",
        "ospf_python.math.chaotic.dequan_li_attractor",
        7,
        3,
        "__call__",
        "scalars",
    ),
    (
        "DuffingEquation",
        "ospf_python.math.chaotic.duffing_equation",
        6,
        3,
        "__call__",
        "scalars",
    ),
    ("DuffingMap", "ospf_python.math.chaotic.duffing_map", 2, 2, "__call__", "scalars"),
    (
        "FinanceAttractor",
        "ospf_python.math.chaotic.finance_attractor",
        4,
        3,
        "__call__",
        "scalars",
    ),
    (
        "HalvorsenAttractor",
        "ospf_python.math.chaotic.halvorsen_attractor",
        2,
        3,
        "__call__",
        "scalars",
    ),
    ("HenonMap", "ospf_python.math.chaotic.henon_map", 2, 2, "__call__", "scalars"),
    (
        "Lorenz84Model",
        "ospf_python.math.chaotic.lorenz84_model",
        5,
        3,
        "__call__",
        "ndarray",
    ),
    (
        "LorenzStenfloAttractor",
        "ospf_python.math.chaotic.lorenz_stenflo_attractor",
        5,
        4,
        "__call__",
        "ndarray",
    ),
    (
        "LotkaVolterraSystem",
        "ospf_python.math.chaotic.lotka_volterra_system",
        5,
        2,
        "__call__",
        "ndarray",
    ),
    (
        "NewtonLeipnikAttractor",
        "ospf_python.math.chaotic.newton_leipnik_attractor",
        3,
        3,
        "__call__",
        "ndarray",
    ),
    (
        "RabinovichFabrikantEquation",
        "ospf_python.math.chaotic.rabinovich_fabrikant_equation",
        3,
        3,
        "__call__",
        "scalars",
    ),
    (
        "RosslerAttractor",
        "ospf_python.math.chaotic.rossler_attractor",
        4,
        3,
        "__call__",
        "scalars",
    ),
    (
        "RucklidgeAttractor",
        "ospf_python.math.chaotic.rucklidge_attractor",
        3,
        3,
        "__call__",
        "scalars",
    ),
    (
        "SakaryaAttractor",
        "ospf_python.math.chaotic.sakarya_attractor",
        3,
        3,
        "__call__",
        "scalars",
    ),
    (
        "TinkerbellMap",
        "ospf_python.math.chaotic.tinkerbell_map",
        4,
        2,
        "__call__",
        "scalars",
    ),
]
SAMPLES = 1000
SEED = 20261030


def _oracle(
    *,
    module: str,
    class_name: str,
    params: list[float],
    state: list[float],
    attempt: str,
    kind: str,
) -> list[float]:
    """用出厂 Python 类执行同一次单步。 / Take the same step with the shipped Python class."""
    target = getattr(importlib.import_module(module), class_name)(*params)
    payload: tuple[Any, ...]
    if kind == "ndarray":
        payload = (np.asarray(state, dtype=np.float64),)
    elif kind == "tuple":
        payload = (tuple(state),)
    else:
        payload = tuple(state)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        values = np.asarray(getattr(target, attempt)(*payload)).reshape(-1)
    return [float(item) for item in values]


@pytest.mark.parametrize(
    ("system", "module", "arity", "dimension", "attempt", "kind"),
    SYSTEMS,
    ids=[row[0] for row in SYSTEMS],
)
def test_candidate_matches_shipped_kernel_over_random_vectors(
    *,
    system: str,
    module: str,
    arity: int,
    dimension: int,
    attempt: str,
    kind: str,
) -> None:
    """在固定 seed 的随机参数与状态上逐位比对固定上游与出厂内核。"""
    rng = random.Random(SEED)
    compared = 0
    for _ in range(SAMPLES):
        params = [rng.uniform(-4.0, 4.0) for _ in range(arity)]
        state = [rng.uniform(-4.0, 4.0) for _ in range(dimension)]
        outcome = chaotic_system_step(system=system, params=params, state=state)
        assert outcome.is_ok(), (params, state, outcome)
        actual = outcome.unwrap()
        expected = _oracle(
            module=module,
            class_name=system,
            params=params,
            state=state,
            attempt=attempt,
            kind=kind,
        )
        for got, want in zip(actual, expected, strict=True):
            if not (math.isfinite(got) and math.isfinite(want)):
                continue
            assert got.hex() == want.hex(), (params, state, got.hex(), want.hex())
            compared += 1
    assert compared >= SAMPLES // 4


def test_supported_systems_are_exactly_the_covered_rows() -> None:
    assert {row[0] for row in SYSTEMS} == set(SUPPORTED_SYSTEMS)


#: 已经把单步演化委托给固定上游的公开类；其余 15 个仍留在 Python 内核。
#: Public classes that delegate one step to the pinned upstream; the other 15 do not.
DISPATCHED = (
    "BurkeShawAttractor",
    "ChenCelikovskyAttractor",
    "ChenLeeAttractor",
    "ChenSystem",
    "ChuaCircuit",
)
DISPATCHED_ROWS = [row for row in SYSTEMS if row[0] in DISPATCHED]
OTHER_ROWS = [row for row in SYSTEMS if row[0] not in DISPATCHED]


def _public_step(row: tuple[str, str, int, int, str, str], container: Any) -> Any:
    """按出厂调用形状用公开类对容器执行一次单步。

    Take one step through the public class for a container using the shipped call shape.

    Args:
        row: `SYSTEMS` 中的一行描述。 / One row of `SYSTEMS`.
        container: 状态容器，由调用方决定其 dtype 与元素类型。 / State container.

    Returns:
        公开类的原始返回。 / Whatever the public class returns.
    """
    system, module, arity, _, attempt, kind = row
    params = [0.2 + 0.1 * index for index in range(arity)]
    target = getattr(importlib.import_module(module), system)(*params)
    payload: tuple[Any, ...]
    if kind == "ndarray":
        payload = (container,)
    elif kind == "tuple":
        payload = (tuple(container),)
    else:
        payload = tuple(container)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return getattr(target, attempt)(*payload)


def _unreachable(**_: object) -> Any:
    """原生入口被触碰时立刻暴露。 / Fail loudly when the native entry is touched."""
    raise AssertionError("the native entry was reached")


@pytest.mark.parametrize(
    "row", DISPATCHED_ROWS, ids=[row[0] for row in DISPATCHED_ROWS]
)
def test_dispatched_classes_reach_the_native_entry(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: tuple[str, str, int, int, str, str],
) -> None:
    """窄域公开类的单步必须真的经过原生入口，不能只在文档里声称已接管。"""
    monkeypatch.setattr(_native, "_chaotic_system_step", _unreachable)
    state = np.asarray([0.7 + 0.1 * index for index in range(row[3])], dtype=np.float64)
    with pytest.raises(AssertionError, match="reached"):
        _public_step(row, state)


@pytest.mark.parametrize(
    "row", DISPATCHED_ROWS, ids=[row[0] for row in DISPATCHED_ROWS]
)
def test_dispatched_classes_fall_back_outside_the_narrow_domain(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: tuple[str, str, int, int, str, str],
) -> None:
    """`float32`、整数、object、列向量与非有限状态必须原样留在 Python 内核。"""
    dimension = row[3]
    monkeypatch.setattr(_native, "_chaotic_system_step", _unreachable)
    for container in (
        np.zeros(dimension, dtype=np.float32),
        np.ones(dimension, dtype=np.int64),
        np.array([0.7 + 0.1 * index for index in range(dimension)], dtype=object),
        np.zeros((dimension, 1), dtype=np.float64),
        np.full(dimension, math.nan),
        np.full(dimension, math.inf),
    ):
        _public_step(row, container)


@pytest.mark.parametrize("row", OTHER_ROWS, ids=[row[0] for row in OTHER_ROWS])
def test_other_public_classes_never_reach_the_native_entry(
    *,
    monkeypatch: pytest.MonkeyPatch,
    row: tuple[str, str, int, int, str, str],
) -> None:
    """其余 15 个类因完整调用预算回归仍不接管，输出必须逐位不变。"""
    state = np.asarray([0.7 + 0.1 * index for index in range(row[3])], dtype=np.float64)
    before = _public_step(row, state)
    monkeypatch.setattr(_native, "_chaotic_system_step", _unreachable)
    assert (
        np.asarray(_public_step(row, state)).tobytes() == np.asarray(before).tobytes()
    )


@pytest.mark.parametrize("position", ["params", "state"])
@pytest.mark.parametrize(
    "value",
    [1, True, np.float64(0.2), 0.2 + 0j, object()],
    ids=["integer", "bool", "numpy", "complex", "object"],
)
def test_candidate_rejects_other_domains_without_coercion(
    *, position: str, value: object
) -> None:
    params: list[Any] = [0.2, 0.2, 5.7, 0.005]
    state: list[Any] = [0.7, 1.3, 2.1]
    if position == "params":
        params[0] = value
    else:
        state[0] = value
    assert chaotic_system_step(
        system="RosslerAttractor", params=params, state=state
    ).is_failed()


def test_candidate_rejects_unknown_names_and_wrong_arities() -> None:
    assert chaotic_system_step(
        system="NotASystem", params=[0.2], state=[0.7, 1.3]
    ).is_failed()
    assert chaotic_system_step(
        system="RosslerAttractor", params=[0.2, 0.2], state=[0.7, 1.3, 2.1]
    ).is_failed()
    assert chaotic_system_step(
        system="RosslerAttractor", params=[0.2, 0.2, 5.7, 0.005], state=[0.7, 1.3]
    ).is_failed()


def test_candidate_rejects_disqualified_systems_by_name() -> None:
    """随机扫描证伪的 5 个类不在名单里，必须明确失败而不是近似通过。"""
    for name in (
        "BoualiAttractor",
        "GenesioTesiAttractor",
        "HindmarshRoseModel",
        "LorenzSystem",
        "ShimizuMoriokaAttractor",
    ):
        assert chaotic_system_step(
            system=name, params=[0.1], state=[0.7, 1.3]
        ).is_failed()
