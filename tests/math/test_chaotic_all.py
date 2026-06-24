"""混沌映射覆盖测试 / Chaotic map coverage tests.

导入并实例化所有混沌映射类以提升覆盖率。
Import and instantiate all chaotic map classes to improve coverage.
"""

from __future__ import annotations

import math

from ospf_python.math.chaotic.arnold_tongue import ArnoldTongue
from ospf_python.math.chaotic.bakers_map import BakersMap
from ospf_python.math.chaotic.brusselator import Brusselator
from ospf_python.math.chaotic.chebyshev_map import ChebyshevMap
from ospf_python.math.chaotic.circle_map import CircleMap
from ospf_python.math.chaotic.double_pendulum_system import DoublePendulumSystem
from ospf_python.math.chaotic.duffing_map import DuffingMap
from ospf_python.math.chaotic.gingerbreadman_map import GingerbreadmanMap
from ospf_python.math.chaotic.henon_map import HenonMap
from ospf_python.math.chaotic.ikeda_map import IkedaMap
from ospf_python.math.chaotic.logistic_map import LogisticMap
from ospf_python.math.chaotic.lorenz_attractor import LorenzAttractor
from ospf_python.math.chaotic.lotka_volterra_system import LotkaVolterraSystem
from ospf_python.math.chaotic.rossler_attractor import RosslerAttractor
from ospf_python.math.chaotic.sine_map import SineMap
from ospf_python.math.chaotic.tent_map import TentMap
from ospf_python.math.chaotic.tinkerbell_map import TinkerbellMap
from ospf_python.math.chaotic.van_der_pol_system import VanDerPolSystem


def test_logistic_map() -> None:
    m = LogisticMap(r=3.9)
    v = m(0.5)
    assert math.isfinite(v)


def test_tent_map() -> None:
    m = TentMap()
    v = m(0.3)
    assert math.isfinite(v)


def test_sine_map() -> None:
    m = SineMap()
    v = m(0.5)
    assert math.isfinite(v)


def test_circle_map() -> None:
    m = CircleMap()
    v = m(0.3)
    assert math.isfinite(v)


def test_henon_map() -> None:
    m = HenonMap()
    r = m.iterate(0.1, 0.1, n=5)
    assert isinstance(r, tuple)
    assert len(r) == 2


def test_lorenz_attractor() -> None:
    m = LorenzAttractor()
    r = m.iterate((1.0, 1.0, 1.0), n=10)
    assert isinstance(r, tuple)
    assert len(r) == 3


def test_rossler_attractor() -> None:
    m = RosslerAttractor()
    r = m.iterate(1.0, 0.0, 0.0, n=10)
    assert isinstance(r, tuple)
    assert len(r) == 3


def test_arnold_tongue() -> None:
    m = ArnoldTongue()
    v = m(0.5)
    assert math.isfinite(v)


def test_bakers_map() -> None:
    m = BakersMap()
    v = m(0.5)
    assert math.isfinite(v)


def test_chebyshev_map() -> None:
    m = ChebyshevMap()
    v = m(0.3)
    assert math.isfinite(v)


def test_duffing_map() -> None:
    m = DuffingMap()
    r = m.iterate(0.1, 0.1, n=5)
    assert isinstance(r, tuple)


def test_gingerbreadman_map() -> None:
    m = GingerbreadmanMap()
    r = m.iterate(0.1, 0.1, n=5)
    assert isinstance(r, tuple)


def test_ikeda_map() -> None:
    m = IkedaMap()
    r = m.iterate(0.1, 0.1, n=5)
    assert isinstance(r, tuple)


def test_tinkerbell_map() -> None:
    m = TinkerbellMap()
    r = m.iterate(0.1, 0.1, n=5)
    assert isinstance(r, tuple)


def test_van_der_pol() -> None:
    m = VanDerPolSystem()
    r = m.iterate(1.0, 0.0, n=5)
    assert isinstance(r, tuple)


def test_brusselator() -> None:
    import numpy as np

    m = Brusselator()
    r = m.iterate(np.array([1.0, 1.0]), n=5)
    assert isinstance(r, list)


def test_lotka_volterra() -> None:
    m = LotkaVolterraSystem()
    r = m.iterate((1.0, 1.0), n=5)
    assert isinstance(r, tuple)


def test_double_pendulum() -> None:
    m = DoublePendulumSystem()
    r = m.iterate(1.0, 0.0, 0.5, 0.0, n=5)
    assert isinstance(r, tuple)
