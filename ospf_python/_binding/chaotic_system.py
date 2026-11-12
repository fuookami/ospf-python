"""固定 Rust 混沌系统单步的私有门面，不改写公共类语义。

Private facade for one pinned Rust chaotic step; the public classes keep their own semantics.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ospf_python import _native
from ospf_python._binding.result import BindingResult, invalid, invoke

# 已按“互不相同的参数向量”逐位确认可委托固定上游的系统名；参数顺序就是公共类的字段顺序。
# Systems confirmed bit-exact on distinct parameter vectors; params follow the class fields.
SUPPORTED_SYSTEMS = (
    "BurkeShawAttractor",
    "ChenCelikovskyAttractor",
    "ChenLeeAttractor",
    "ChenSystem",
    "ChuaCircuit",
    "DequanLiAttractor",
    "DuffingEquation",
    "DuffingMap",
    "FinanceAttractor",
    "HalvorsenAttractor",
    "HenonMap",
    "Lorenz84Model",
    "LorenzStenfloAttractor",
    "LotkaVolterraSystem",
    "NewtonLeipnikAttractor",
    "RabinovichFabrikantEquation",
    "RosslerAttractor",
    "RucklidgeAttractor",
    "SakaryaAttractor",
    "TinkerbellMap",
)


def chaotic_system_step(
    *,
    system: str,
    params: list[float] | tuple[float, ...],
    state: list[float] | tuple[float, ...],
) -> BindingResult[tuple[float, ...]]:
    """用固定上游执行一次单步。

    Take exactly one step with the pinned upstream system.

    Args:
        system: `SUPPORTED_SYSTEMS` 中的系统名。 / A name from `SUPPORTED_SYSTEMS`.
        params: 按公共类字段顺序排列的内置 float。 / Builtin floats in field order.
        state: 与状态维度等长的内置 float。 / Builtin floats matching the dimension.

    Returns:
        下一步各分量的元组，或保留来源的失败。
        A tuple of the next components, or a failure retaining its provenance.
    """
    if system not in SUPPORTED_SYSTEMS:
        return invalid(f"未知的混沌系统 / Unknown chaotic system: {system}")
    return invoke(
        lambda: _native._chaotic_system_step(system=system, params=params, state=state)
    ).map(tuple)


def _finite_floats(values: Any) -> list[float] | None:
    """把 float64 容器下沉成内置 float 列表，超出窄域时返回 None。

    Sink a float64 container into builtin floats, or reject anything outside that narrow domain.

    Args:
        values: ndarray、list 或 tuple 状态/参数容器。 / An ndarray, list or tuple container.

    Returns:
        全部有限且逐项为内置 `float` 的列表，否则 `None`。
        A list of finite builtin floats, or `None` when the domain is not covered.
    """
    dtype = getattr(values, "dtype", None)
    if dtype is not None and dtype != np.float64:
        return None
    tolist = getattr(values, "tolist", None)
    try:
        items = tolist() if tolist is not None else list(values)
    except TypeError:
        return None
    if not isinstance(items, list):
        items = [items]
    for item in items:
        if type(item) is not float or not math.isfinite(item):
            return None
    return items


def array_step_or_none(
    *,
    system: str,
    params: Any,
    state: Any,
) -> np.ndarray | None:
    """在有限 float64 窄域上把一步演化委托给固定上游。

    Delegate one evolution step to the pinned upstream inside the narrow finite float64 domain.

    只覆盖能被证明与出厂实现逐位且同形的输入：`float64` 数组、或全部为内置 `float` 的
    list/tuple，且逐项有限。任何超出该域（`float32`、整数、布尔、`Decimal`、非有限值、
    二维容器）都返回 `None`，由调用方原样保留既有实现。

    Only inputs proven bit-identical and shape-identical are delegated: a `float64` array, or a
    list/tuple of builtin floats, all finite. Anything else (float32, ints, bools, `Decimal`,
    non-finite values, nested containers) returns `None` so the caller keeps its own behaviour.

    Args:
        system: `SUPPORTED_SYSTEMS` 中的系统名。 / A name from `SUPPORTED_SYSTEMS`.
        params: 按公共类字段顺序排列的参数容器。 / Parameters in public field order.
        state: 当前状态容器。 / The current state container.

    Returns:
        dtype 为 `float64`、形状为 `(dimension,)` 的下一步状态，或 `None`。
        The next state as a `float64` array of shape `(dimension,)`, or `None`.
    """
    sunk_params = _finite_floats(params)
    sunk_state = _finite_floats(state)
    if sunk_params is None or sunk_state is None:
        return None
    values, failure = _native._chaotic_system_step(
        system=system, params=sunk_params, state=sunk_state
    )
    if failure is not None:
        return None
    return np.asarray(values, dtype=np.float64)
