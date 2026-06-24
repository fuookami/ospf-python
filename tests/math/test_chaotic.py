"""混沌映射模块测试。

Chaotic maps module tests.

覆盖 18 种混沌映射的迭代行为、输出类型和 frozen 属性，
共 32 个测试用例。
Covers 18 chaotic maps for iteration behavior,
output types, and frozen dataclass properties (32 tests).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ospf_python.math.chaotic.arnold_tongue import ArnoldTongue
from ospf_python.math.chaotic.bakers_map import BakersMap
from ospf_python.math.chaotic.brusselator import Brusselator
from ospf_python.math.chaotic.chebyshev_map import ChebyshevMap
from ospf_python.math.chaotic.circle_map import CircleMap
from ospf_python.math.chaotic.double_pendulum_system import (
    DoublePendulumSystem,
)
from ospf_python.math.chaotic.duffing_map import DuffingMap
from ospf_python.math.chaotic.gingerbreadman_map import GingerbreadmanMap

# ── 2D 离散映射 / 2D Discrete Maps ────────────────────────────
from ospf_python.math.chaotic.henon_map import HenonMap
from ospf_python.math.chaotic.ikeda_map import IkedaMap

# ── 1D 离散映射 / 1D Discrete Maps ────────────────────────────
from ospf_python.math.chaotic.logistic_map import LogisticMap

# ── 连续系统 / Continuous Systems ─────────────────────────────
from ospf_python.math.chaotic.lorenz_attractor import LorenzAttractor
from ospf_python.math.chaotic.lotka_volterra_system import (
    LotkaVolterraSystem,
)
from ospf_python.math.chaotic.rossler_attractor import RosslerAttractor
from ospf_python.math.chaotic.sine_map import SineMap
from ospf_python.math.chaotic.tent_map import TentMap
from ospf_python.math.chaotic.tinkerbell_map import TinkerbellMap
from ospf_python.math.chaotic.van_der_pol_system import VanDerPolSystem


def _all_finite(values: list[float]) -> bool:
    """检查列表中所有值是否有限。

    Check that every value in the list is finite.
    """
    return all(math.isfinite(v) for v in values)


# ══════════════════════════════════════════════════════════════
# 1. LogisticMap
# ══════════════════════════════════════════════════════════════


class TestLogisticMapIteration:
    """Logistic 映射迭代测试。/ Logistic map iteration tests."""

    def test_iterate_finite_values(self) -> None:
        """r=3.9 从 x0=0.5 迭代 5 步产生有限值。

        Iterate 5 steps from x0=0.5 at r=3.9
        produces finite values.
        """
        lm = LogisticMap(r=3.9)
        val = lm.iterate(0.5, n=5)
        assert isinstance(val, float)
        assert math.isfinite(val)

    def test_iterate_output_length(self) -> None:
        """iterate 返回单个浮点数。/ iterate returns a float."""
        lm = LogisticMap()
        val = lm.iterate(0.5, n=10)
        assert isinstance(val, float)

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float 类型。/ __call__ returns float."""
        lm = LogisticMap()
        result = lm(0.5)
        assert isinstance(result, float)

    def test_frozen_dataclass(self) -> None:
        """LogisticMap 是 frozen dataclass。

        LogisticMap is a frozen dataclass.
        """
        lm = LogisticMap(r=3.9)
        assert lm.r == 3.9
        with pytest.raises(AttributeError):
            lm.r = 4.0  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# 2. TentMap
# ══════════════════════════════════════════════════════════════


class TestTentMapIteration:
    """帐篷映射迭代测试。/ Tent map iteration tests."""

    def test_values_stay_in_unit_interval(self) -> None:
        """从 x0=0.3 迭代 10 步，值保持在 [0, 1]。

        Iterate 10 steps from x0=0.3,
        values stay in [0, 1].
        """
        tm = TentMap()
        val = tm.iterate(0.3, n=10)
        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float 类型。/ __call__ returns float."""
        tm = TentMap()
        result = tm(0.3)
        assert isinstance(result, float)

    def test_frozen_dataclass(self) -> None:
        """TentMap 是 frozen dataclass。/ TentMap is frozen."""
        tm = TentMap(mu=1.5)
        assert tm.mu == 1.5
        with pytest.raises(AttributeError):
            tm.mu = 2.0  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# 3. SineMap
# ══════════════════════════════════════════════════════════════


class TestSineMapIteration:
    """正弦映射迭代测试。/ Sine map iteration tests."""

    def test_iterate_finite(self) -> None:
        """从 x0=0.5 迭代 10 步产生有限值。

        Iterate 10 steps from x0=0.5 produces
        finite values.
        """
        sm = SineMap()
        val = sm.iterate(0.5, n=10)
        assert isinstance(val, float)
        assert math.isfinite(val)

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float。/ __call__ returns float."""
        sm = SineMap()
        result = sm(0.5)
        assert isinstance(result, float)

    def test_frozen_dataclass(self) -> None:
        """SineMap 是 frozen dataclass。/ SineMap is frozen."""
        sm = SineMap(a=0.9)
        assert sm.a == 0.9
        with pytest.raises(AttributeError):
            sm.a = 1.0  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# 4. CircleMap
# ══════════════════════════════════════════════════════════════


class TestCircleMapIteration:
    """圆映射迭代测试。/ Circle map iteration tests."""

    def test_iterate_returns_list(self) -> None:
        """omega=0.5, k=0.5 迭代 10 步返回列表。

        Iterate 10 steps with omega=0.5, k=0.5
        returns a list.
        """
        cm = CircleMap(omega=0.5, k=0.5)
        result = cm.iterate(0.3, n=10)
        assert isinstance(result, list)
        assert len(result) == 11  # 初始值 + 10 步 / init + 10 steps

    def test_all_finite(self) -> None:
        """所有迭代值有限。/ All iteration values are finite."""
        cm = CircleMap(omega=0.5, k=0.5)
        result = cm.iterate(0.3, n=10)
        assert _all_finite(result)

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float。/ __call__ returns float."""
        cm = CircleMap()
        result = cm(0.3)
        assert isinstance(result, float)


# ══════════════════════════════════════════════════════════════
# 5. HenonMap
# ══════════════════════════════════════════════════════════════


class TestHenonMapIteration:
    """Henon 映射迭代测试。/ Henon map iteration tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (0.1, 0.1) 迭代 10 步返回二维元组。

        Iterate 10 steps from (0.1, 0.1)
        returns a 2-tuple.
        """
        hm = HenonMap()
        result = hm.iterate(0.1, 0.1, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple[float, float]。

        __call__ returns tuple[float, float].
        """
        hm = HenonMap()
        result = hm(0.1, 0.1)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_frozen_dataclass(self) -> None:
        """HenonMap 是 frozen dataclass。/ HenonMap is frozen."""
        hm = HenonMap(a=1.2, b=0.2)
        assert hm.a == 1.2
        with pytest.raises(AttributeError):
            hm.a = 1.4  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# 6. LorenzAttractor
# ══════════════════════════════════════════════════════════════


class TestLorenzAttractorIteration:
    """Lorenz 吸引子迭代测试。/ Lorenz attractor iteration tests."""

    def test_trajectory_not_nan(self) -> None:
        """从 (1,1,1) 迭代 100 步，轨迹无 NaN。

        Iterate 100 steps from (1,1,1),
        trajectory has no NaN.
        """
        la = LorenzAttractor()
        result = la.iterate((1.0, 1.0, 1.0), n=100)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 3 元组。/ __call__ returns 3-tuple."""
        la = LorenzAttractor()
        result = la((1.0, 1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 3


# ══════════════════════════════════════════════════════════════
# 7. RosslerAttractor
# ══════════════════════════════════════════════════════════════


class TestRosslerAttractorIteration:
    """Rossler 吸引子迭代测试。/ Rossler attractor iteration tests."""

    def test_iterate_finite(self) -> None:
        """从 (1,0,0) 迭代 50 步，结果有限。

        Iterate 50 steps from (1,0,0),
        results are finite.
        """
        ra = RosslerAttractor()
        x, y, z = ra.iterate(1.0, 0.0, 0.0, n=50)
        assert all(math.isfinite(v) for v in (x, y, z))

    def test_call_returns_3tuple(self) -> None:
        """__call__ 返回 3 元组。/ __call__ returns 3-tuple."""
        ra = RosslerAttractor()
        result = ra(1.0, 0.0, 0.0)
        assert isinstance(result, tuple)
        assert len(result) == 3


# ══════════════════════════════════════════════════════════════
# 8. ArnoldTongue
# ══════════════════════════════════════════════════════════════


class TestArnoldTongueIteration:
    """Arnold 舌迭代测试。/ Arnold tongue iteration tests."""

    def test_basic_iteration(self) -> None:
        """基本迭代返回列表。/ Basic iteration returns list."""
        at = ArnoldTongue()
        result = at.iterate(0.3, n=10)
        assert isinstance(result, list)
        assert len(result) == 11

    def test_all_finite(self) -> None:
        """所有值有限。/ All values are finite."""
        at = ArnoldTongue()
        result = at.iterate(0.3, n=10)
        assert _all_finite(result)

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float。/ __call__ returns float."""
        at = ArnoldTongue()
        result = at(0.3)
        assert isinstance(result, float)


# ══════════════════════════════════════════════════════════════
# 9. BakersMap
# ══════════════════════════════════════════════════════════════


class TestBakersMapIteration:
    """Baker 映射迭代测试。/ Baker's map iteration tests."""

    def test_iterate_returns_list(self) -> None:
        """从 0.5 迭代 10 步返回列表。

        Iterate 10 steps from 0.5 returns a list.
        """
        bm = BakersMap()
        result = bm.iterate(0.5, n=10)
        assert isinstance(result, list)
        assert len(result) == 11

    def test_all_finite(self) -> None:
        """所有值有限。/ All values are finite."""
        bm = BakersMap()
        result = bm.iterate(0.25, n=10)
        assert _all_finite(result)

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float。/ __call__ returns float."""
        bm = BakersMap()
        result = bm(0.25)
        assert isinstance(result, float)


# ══════════════════════════════════════════════════════════════
# 10. ChebyshevMap
# ══════════════════════════════════════════════════════════════


class TestChebyshevMapIteration:
    """Chebyshev 映射迭代测试。/ Chebyshev map iteration tests."""

    def test_iterate_returns_list(self) -> None:
        """从 0.3 迭代 10 步返回列表。

        Iterate 10 steps from 0.3 returns a list.
        """
        cm = ChebyshevMap()
        result = cm.iterate(0.3, n=10)
        assert isinstance(result, list)
        assert len(result) == 11

    def test_all_finite(self) -> None:
        """所有值有限。/ All values are finite."""
        cm = ChebyshevMap()
        result = cm.iterate(0.3, n=10)
        assert _all_finite(result)

    def test_call_returns_float(self) -> None:
        """__call__ 返回 float。/ __call__ returns float."""
        cm = ChebyshevMap()
        result = cm(0.3)
        assert isinstance(result, float)


# ══════════════════════════════════════════════════════════════
# 11. DuffingMap
# ══════════════════════════════════════════════════════════════


class TestDuffingMapIteration:
    """Duffing 映射迭代测试。/ Duffing map iteration tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (0.1, 0.1) 迭代 10 步返回二维元组。

        Iterate 10 steps from (0.1, 0.1)
        returns a 2-tuple.
        """
        dm = DuffingMap()
        result = dm.iterate(0.1, 0.1, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple。/ __call__ returns tuple."""
        dm = DuffingMap()
        result = dm(0.1, 0.1)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ══════════════════════════════════════════════════════════════
# 12. GingerbreadmanMap
# ══════════════════════════════════════════════════════════════


class TestGingerbreadmanMapIteration:
    """姜饼人映射迭代测试。/ Gingerbreadman map tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (0.1, 0.1) 迭代 10 步返回二维元组。

        Iterate 10 steps from (0.1, 0.1)
        returns a 2-tuple.
        """
        gm = GingerbreadmanMap()
        result = gm.iterate(0.1, 0.1, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple。/ __call__ returns tuple."""
        gm = GingerbreadmanMap()
        result = gm(0.1, 0.1)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ══════════════════════════════════════════════════════════════
# 13. IkedaMap
# ══════════════════════════════════════════════════════════════


class TestIkedaMapIteration:
    """Ikeda 映射迭代测试。/ Ikeda map iteration tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (0.1, 0.1) 迭代 10 步返回二维元组。

        Iterate 10 steps from (0.1, 0.1)
        returns a 2-tuple.
        """
        im = IkedaMap()
        result = im.iterate(0.1, 0.1, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple。/ __call__ returns tuple."""
        im = IkedaMap()
        result = im(0.1, 0.1)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ══════════════════════════════════════════════════════════════
# 14. TinkerbellMap
# ══════════════════════════════════════════════════════════════


class TestTinkerbellMapIteration:
    """Tinkerbell 映射迭代测试。/ Tinkerbell map tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (0.1, 0.1) 迭代 10 步返回二维元组。

        Iterate 10 steps from (0.1, 0.1)
        returns a 2-tuple.
        """
        tm = TinkerbellMap()
        result = tm.iterate(0.1, 0.1, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple。/ __call__ returns tuple."""
        tm = TinkerbellMap()
        result = tm(0.1, 0.1)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_frozen_dataclass(self) -> None:
        """TinkerbellMap 是 frozen dataclass。

        TinkerbellMap is frozen.
        """
        tm = TinkerbellMap(a=0.9, b=-0.6013, c=2.0, d=0.5)
        assert tm.a == 0.9
        with pytest.raises(AttributeError):
            tm.a = 1.0  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════
# 15. VanDerPolSystem
# ══════════════════════════════════════════════════════════════


class TestVanDerPolSystemIteration:
    """Van der Pol 系统迭代测试。/ Van der Pol tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (1, 0) 迭代 10 步返回二维元组。

        Iterate 10 steps from (1, 0)
        returns a 2-tuple.
        """
        vdp = VanDerPolSystem()
        result = vdp.iterate(1.0, 0.0, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple。/ __call__ returns tuple."""
        vdp = VanDerPolSystem()
        result = vdp(1.0, 0.0)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ══════════════════════════════════════════════════════════════
# 16. DoublePendulumSystem
# ══════════════════════════════════════════════════════════════


class TestDoublePendulumIteration:
    """双摆系统迭代测试。/ Double pendulum tests."""

    def test_iterate_4d_output(self) -> None:
        """从 (1,0,0.5,0) 迭代 10 步返回四维元组。

        Iterate 10 steps from (1,0,0.5,0)
        returns a 4-tuple.
        """
        dp = DoublePendulumSystem()
        result = dp.iterate(1.0, 0.0, 0.5, 0.0, n=10)
        assert isinstance(result, tuple)
        assert len(result) == 4
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_4tuple(self) -> None:
        """__call__ 返回 4 元组。/ __call__ returns 4-tuple."""
        dp = DoublePendulumSystem()
        result = dp(1.0, 0.0, 0.5, 0.0)
        assert isinstance(result, tuple)
        assert len(result) == 4


# ══════════════════════════════════════════════════════════════
# 17. Brusselator
# ══════════════════════════════════════════════════════════════


class TestBrusselatorIteration:
    """Brusselator 迭代测试。/ Brusselator iteration tests."""

    def test_iterate_returns_list(self) -> None:
        """从 [1,1] 迭代 10 步返回列表。

        Iterate 10 steps from [1,1] returns a list.
        """
        br = Brusselator()
        x0 = np.array([1.0, 1.0])
        result = br.iterate(x0, n=10)
        assert isinstance(result, list)
        assert len(result) == 11  # 初始值 + 10 步 / init + 10 steps

    def test_all_finite(self) -> None:
        """所有状态值有限。/ All state values are finite."""
        br = Brusselator()
        x0 = np.array([1.0, 1.0])
        result = br.iterate(x0, n=10)
        for state in result:
            assert np.all(np.isfinite(state))

    def test_call_returns_ndarray(self) -> None:
        """__call__ 返回 NDArray。/ __call__ returns NDArray."""
        br = Brusselator()
        x0 = np.array([1.0, 1.0])
        result = br(x0)
        assert isinstance(result, np.ndarray)
        assert result.shape == (2,)


# ══════════════════════════════════════════════════════════════
# 18. LotkaVolterraSystem
# ══════════════════════════════════════════════════════════════


class TestLotkaVolterraIteration:
    """Lotka-Volterra 系统迭代测试。/ Lotka-Volterra tests."""

    def test_iterate_2d_output(self) -> None:
        """从 (1,1) 迭代 10 步返回二维元组。

        Iterate 10 steps from (1,1)
        returns a 2-tuple.
        """
        lv = LotkaVolterraSystem()
        result = lv.iterate((1.0, 1.0), n=10)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert all(math.isfinite(v) for v in result)

    def test_call_returns_tuple(self) -> None:
        """__call__ 返回 tuple。/ __call__ returns tuple."""
        lv = LotkaVolterraSystem()
        result = lv((1.0, 1.0))
        assert isinstance(result, tuple)
        assert len(result) == 2
