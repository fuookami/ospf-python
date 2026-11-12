"""公开混沌单步完整调用合同，不冒充预算验收。 / Complete public chaotic step calls, not budget acceptance."""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pytest

from ospf_python.math.chaotic.burke_shaw_attractor import BurkeShawAttractor
from ospf_python.math.chaotic.chen_celikovsky_attractor import ChenCelikovskyAttractor
from ospf_python.math.chaotic.chen_lee_attractor import ChenLeeAttractor
from ospf_python.math.chaotic.chen_system import ChenSystem
from ospf_python.math.chaotic.chua_circuit import ChuaCircuit

#: (公开实例, 其所在模块) —— 模块名用于关掉快路后取出厂内核的对照值。
#: (public instance, its module) — the module turns the fast path off for the reference run.
TARGETS: list[tuple[Any, str]] = [
    (BurkeShawAttractor(), "ospf_python.math.chaotic.burke_shaw_attractor"),
    (ChenCelikovskyAttractor(), "ospf_python.math.chaotic.chen_celikovsky_attractor"),
    (ChenLeeAttractor(), "ospf_python.math.chaotic.chen_lee_attractor"),
    (ChenSystem(), "ospf_python.math.chaotic.chen_system"),
    (ChuaCircuit(), "ospf_python.math.chaotic.chua_circuit"),
]
IDS = ("burke-shaw", "chen-celikovsky", "chen-lee", "chen-system", "chua-circuit")


@pytest.mark.parametrize(("target", "module"), TARGETS, ids=IDS)
def test_public_chaotic_complete_call(
    *,
    benchmark: Any,
    monkeypatch: pytest.MonkeyPatch,
    target: Any,
    module: str,
) -> None:
    """公开单步默认走原生快路，且与出厂内核逐位一致。"""
    state = np.asarray([0.7, 1.3, 2.1], dtype=np.float64)
    dispatched = benchmark(lambda: target(state))
    monkeypatch.setattr(
        importlib.import_module(module), "array_step_or_none", lambda **_: None
    )
    reference = target(state)
    assert dispatched.dtype == np.dtype(np.float64)
    assert dispatched.tobytes() == reference.tobytes()
