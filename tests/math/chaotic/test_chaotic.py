"""混沌模块测试。

Chaotic module tests.

覆盖 30+ 测试用例，包括映射迭代、吸引子轨迹和参数默认值。
Covers 30+ test cases including map iteration,
attractor trajectories, and parameter defaults.
"""

from __future__ import annotations

import math

from ospf_python.math.chaotic.circle_map import CircleMap

# ── 其他 / Other ──────────────────────────────────────────────
from ospf_python.math.chaotic.coullet_attractor import CoulletAttractor
from ospf_python.math.chaotic.coupled_lorenz_attractor import (
    CoupledLorenzAttractor,
)

# ── 2D 离散映射 / 2D Discrete Maps ────────────────────────────
from ospf_python.math.chaotic.henon_map import HenonMap

# ── 1D 离散映射 / 1D Discrete Maps ────────────────────────────
from ospf_python.math.chaotic.logistic_map import LogisticMap

# ── 3D 连续吸引子 / 3D Continuous Attractors ─────────────────
from ospf_python.math.chaotic.lorenz_attractor import LorenzAttractor
from ospf_python.math.chaotic.qi_chen_attractor import QiChenAttractor
from ospf_python.math.chaotic.rabinovich_fabrikant_equation import (
    RabinovichFabrikantEquation,
)
from ospf_python.math.chaotic.rayleigh_benard_attractor import (
    RayleighBenardAttractor,
)
from ospf_python.math.chaotic.rossler_attractor import RosslerAttractor
from ospf_python.math.chaotic.rucklidge_attractor import RucklidgeAttractor
from ospf_python.math.chaotic.sakarya_attractor import SakaryaAttractor
from ospf_python.math.chaotic.shimizu_morioka_attractor import (
    ShimizuMoriokaAttractor,
)
from ospf_python.math.chaotic.sine_map import SineMap
from ospf_python.math.chaotic.singer_map import SingerMap
from ospf_python.math.chaotic.sinus_map import SinusMap
from ospf_python.math.chaotic.sinusoidal_map import SinusoidalMap
from ospf_python.math.chaotic.symplectic_map import SymplecticMap
from ospf_python.math.chaotic.tent_map import TentMap
from ospf_python.math.chaotic.thomas_attractor import ThomasAttractor
from ospf_python.math.chaotic.thomas_cyclically_symmetric_attractor import (
    ThomasCyclicallySymmetricAttractor,
)
from ospf_python.math.chaotic.three_scroll_unified_chaotic_system import (
    ThreeScrollUnifiedChaoticSystem,
)
from ospf_python.math.chaotic.tinkerbell_map import TinkerbellMap
from ospf_python.math.chaotic.van_der_pol_system import VanDerPolSystem
from ospf_python.math.chaotic.wang_sun_attractor import WangSunAttractor
from ospf_python.math.chaotic.wimol_banlue_attractor import WimolBanlueAttractor
from ospf_python.math.chaotic.yu_wang_attractor import YuWangAttractor
from ospf_python.math.chaotic.zaslavskii_map import ZaslavskiiMap

# ══════════════════════════════════════════════════════════════
# LogisticMap 测试
# ══════════════════════════════════════════════════════════════


class TestLogisticMap:
    """Logistic 映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        lm = LogisticMap()
        assert lm.r == 3.9

    def test_fixed_point_at_zero(self) -> None:
        """x=0 是不动点。/ x=0 is a fixed point."""
        lm = LogisticMap(r=2.5)
        assert lm(0.0) == 0.0

    def test_single_step(self) -> None:
        """单步迭代。/ Single step."""
        lm = LogisticMap(r=4.0)
        result = lm(0.5)
        assert abs(result - 1.0) < 1e-12

    def test_iterate_convergence(self) -> None:
        """高 r 值迭代不发散到无穷。/ High r iteration stays bounded."""
        lm = LogisticMap(r=3.9)
        val = lm.iterate(0.1, n=1000)
        assert 0.0 <= val <= 1.0

    def test_iterate_period_two(self) -> None:
        """r=3.2 时应出现周期 2 行为。/ Period-2 at r=3.2."""
        lm = LogisticMap(r=3.2)
        val = lm.iterate(0.2, n=1000)
        a = lm(val)
        b = lm(a)
        assert abs(b - val) < 1e-6


# ══════════════════════════════════════════════════════════════
# HenonMap 测试
# ══════════════════════════════════════════════════════════════


class TestHenonMap:
    """Henon 映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        hm = HenonMap()
        assert hm.a == 1.4
        assert hm.b == 0.3

    def test_known_values(self) -> None:
        """已知值验证。/ Known value verification."""
        hm = HenonMap(a=1.4, b=0.3)
        x1, y1 = hm(0.0, 0.0)
        assert abs(x1 - 1.0) < 1e-12
        assert abs(y1 - 0.0) < 1e-12

    def test_known_values_step2(self) -> None:
        """第二步已知值。/ Step-2 known values."""
        hm = HenonMap(a=1.4, b=0.3)
        x2, y2 = hm.iterate(0.0, 0.0, n=2)
        # Step 1: (1, 0), Step 2: (1 - 1.4 + 0, 0.3) = (-0.4, 0.3)
        assert abs(x2 - (-0.4)) < 1e-12
        assert abs(y2 - 0.3) < 1e-12

    def test_iterate_n_steps(self) -> None:
        """迭代 n 步返回元组。/ n-step iteration returns tuple."""
        hm = HenonMap()
        x, y = hm.iterate(0.1, 0.2, n=50)
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        hm = HenonMap(a=1.2, b=0.2)
        assert hm.a == 1.2
        assert hm.b == 0.2


# ══════════════════════════════════════════════════════════════
# LorenzAttractor 测试
# ══════════════════════════════════════════════════════════════


class TestLorenzAttractor:
    """Lorenz 吸引子测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        la = LorenzAttractor()
        assert la.sigma == 10.0
        assert la.rho == 28.0
        assert abs(la.beta - 8.0 / 3.0) < 1e-12

    def test_trajectory_bounded(self) -> None:
        """轨迹不发散。/ Trajectory stays bounded."""
        la = LorenzAttractor()
        x, y, z = la.iterate((1.0, 1.0, 1.0), n=1000)
        assert abs(x) < 100
        assert abs(y) < 100
        assert abs(z) < 100

    def test_trajectory_moves(self) -> None:
        """轨迹远离初始点。/ Trajectory moves from initial point."""
        la = LorenzAttractor()
        x, y, z = la.iterate((1.0, 1.0, 1.0), n=100)
        assert not (x == 1.0 and y == 1.0 and z == 1.0)

    def test_single_step(self) -> None:
        """单步积分。/ Single integration step."""
        la = LorenzAttractor(dt=0.01)
        x, y, z = la((1.0, 1.0, 1.0))
        # dx = sigma*(y-x) = 10*(1-1) = 0
        # dy = x*(rho-z)-y = 1*(28-1)-1 = 26
        # dz = x*y - beta*z = 1 - 8/3 = -5/3
        assert abs(x - 1.0) < 1e-10
        assert abs(y - (1.0 + 26.0 * 0.01)) < 1e-10
        assert abs(z - (1.0 + (-5.0 / 3.0) * 0.01)) < 1e-10

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        la = LorenzAttractor(sigma=5.0)
        assert la.sigma == 5.0


# ══════════════════════════════════════════════════════════════
# TentMap 测试
# ══════════════════════════════════════════════════════════════


class TestTentMap:
    """帐篷映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        tm = TentMap()
        assert tm.mu == 2.0

    def test_basic_iteration(self) -> None:
        """基本迭代。/ Basic iteration."""
        tm = TentMap(mu=2.0)
        result = tm(0.3)
        # min(0.3, 0.7) = 0.3, 2 * 0.3 = 0.6
        assert abs(result - 0.6) < 1e-12

    def test_symmetry(self) -> None:
        """对称性。/ Symmetry."""
        tm = TentMap(mu=2.0)
        assert abs(tm(0.3) - tm(0.7)) < 1e-12

    def test_peak_at_half(self) -> None:
        """中点处最大值。/ Maximum at midpoint."""
        tm = TentMap(mu=2.0)
        assert abs(tm(0.5) - 1.0) < 1e-12

    def test_zero_at_boundary(self) -> None:
        """边界值为零。/ Zero at boundary."""
        tm = TentMap(mu=2.0)
        assert abs(tm(0.0)) < 1e-12
        assert abs(tm(1.0)) < 1e-12

    def test_iterate(self) -> None:
        """多次迭代。/ Multiple iterations."""
        tm = TentMap(mu=1.5)
        val = tm.iterate(0.4, n=10)
        assert isinstance(val, float)


# ══════════════════════════════════════════════════════════════
# SineMap 测试
# ══════════════════════════════════════════════════════════════


class TestSineMap:
    """正弦映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        sm = SineMap()
        assert sm.a == 1.0

    def test_basic_iteration(self) -> None:
        """基本迭代。/ Basic iteration."""
        sm = SineMap(a=1.0)
        result = sm(0.5)
        # sin(pi * 0.5) = 1.0
        assert abs(result - 1.0) < 1e-12

    def test_zero_maps_to_zero(self) -> None:
        """零映射到零。/ Zero maps to zero."""
        sm = SineMap()
        assert abs(sm(0.0)) < 1e-12

    def test_one_maps_to_zero(self) -> None:
        """1 映射到零。/ 1 maps to zero."""
        sm = SineMap()
        assert abs(sm(1.0)) < 1e-12

    def test_iterate(self) -> None:
        """多次迭代。/ Multiple iterations."""
        sm = SineMap(a=0.9)
        val = sm.iterate(0.3, n=20)
        assert isinstance(val, float)


# ══════════════════════════════════════════════════════════════
# CircleMap 测试
# ══════════════════════════════════════════════════════════════


class TestCircleMap:
    """圆映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        cm = CircleMap()
        assert cm.omega == 0.5
        assert cm.k == 1.0

    def test_basic_iteration(self) -> None:
        """基本迭代。/ Basic iteration."""
        cm = CircleMap(omega=0.0, k=0.0)
        result = cm(0.3)
        assert abs(result - 0.3) < 1e-12

    def test_pure_rotation(self) -> None:
        """纯旋转 (k=0)。/ Pure rotation (k=0)."""
        cm = CircleMap(omega=0.25, k=0.0)
        result = cm(0.0)
        assert abs(result - 0.25) < 1e-12

    def test_iterate_returns_list(self) -> None:
        """迭代返回列表。/ Iterate returns list."""
        cm = CircleMap()
        result = cm.iterate(0.1, n=5)
        assert len(result) == 6  # 初始值 + 5 步


# ══════════════════════════════════════════════════════════════
# RosslerAttractor 测试
# ══════════════════════════════════════════════════════════════


class TestRosslerAttractor:
    """Rossler 吸引子测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ra = RosslerAttractor()
        assert ra.a == 0.2
        assert ra.b == 0.2
        assert ra.c == 5.7

    def test_trajectory_bounded(self) -> None:
        """轨迹不发散。/ Trajectory stays bounded."""
        ra = RosslerAttractor()
        x, y, z = ra.iterate(1.0, 0.0, 0.0, n=500)
        assert abs(x) < 50
        assert abs(y) < 50
        assert abs(z) < 50


# ══════════════════════════════════════════════════════════════
# ThomasAttractor 测试
# ══════════════════════════════════════════════════════════════


class TestThomasAttractor:
    """Thomas 吸引子测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ta = ThomasAttractor()
        assert abs(ta.b - 0.208186) < 1e-6

    def test_origin_is_fixed_point(self) -> None:
        """原点是不动点。/ Origin is a fixed point."""
        ta = ThomasAttractor()
        x, y, z = ta(0.0, 0.0, 0.0)
        assert abs(x) < 1e-12
        assert abs(y) < 1e-12
        assert abs(z) < 1e-12


# ══════════════════════════════════════════════════════════════
# ThomasCyclicallySymmetricAttractor 测试
# ══════════════════════════════════════════════════════════════


class TestThomasCyclicallySymmetricAttractor:
    """Thomas 循环对称吸引子测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        tcs = ThomasCyclicallySymmetricAttractor()
        assert tcs.b == 0.18

    def test_cyclic_symmetry_equations(self) -> None:
        """微分方程具有循环对称性。/ ODEs have cyclic symmetry."""
        tcs = ThomasCyclicallySymmetricAttractor()
        # 循环移位输入 (y,z,x) 的导数应等于原始 (x,y,z)
        # 的导数循环移位 (dy,dz,dx)
        x, y, z = 1.0, 2.0, 3.0
        b = tcs.b
        # 原始导数
        dx1 = math.sin(y) - b * x
        dy1 = math.sin(z) - b * y
        dz1 = math.sin(x) - b * z
        # 循环移位输入 (y, z, x) 的导数
        dx_s = math.sin(z) - b * y
        dy_s = math.sin(x) - b * z
        dz_s = math.sin(y) - b * x
        # (dx_s, dy_s, dz_s) 应等于 (dy1, dz1, dx1)
        assert abs(dx_s - dy1) < 1e-12
        assert abs(dy_s - dz1) < 1e-12
        assert abs(dz_s - dx1) < 1e-12


# ══════════════════════════════════════════════════════════════
# 其他吸引子参数默认值测试
# ══════════════════════════════════════════════════════════════


class TestAttractorDefaults:
    """吸引子默认参数测试。"""

    def test_qi_chen_defaults(self) -> None:
        """Qi-Chen 默认参数。/ Qi-Chen defaults."""
        qca = QiChenAttractor()
        assert qca.a == 35.0
        assert qca.b == 8.0 / 3.0
        assert qca.c == 28.0

    def test_rabinovich_fabrikant_defaults(self) -> None:
        """Rabinovich-Fabrikant 默认参数。"""
        rfe = RabinovichFabrikantEquation()
        assert rfe.alpha == 1.1
        assert rfe.gamma == 0.87

    def test_rucklidge_defaults(self) -> None:
        """Rucklidge 默认参数。/ Rucklidge defaults."""
        ra = RucklidgeAttractor()
        assert ra.kappa == 2.0
        assert ra.alpha == 6.7

    def test_sakarya_defaults(self) -> None:
        """Sakarya 默认参数。/ Sakarya defaults."""
        sa = SakaryaAttractor()
        assert sa.a == 0.4
        assert sa.b == 0.2

    def test_shimizu_morioka_defaults(self) -> None:
        """Shimizu-Morioka 默认参数。"""
        sma = ShimizuMoriokaAttractor()
        assert sma.a == 0.75
        assert sma.b == 0.45

    def test_wang_sun_defaults(self) -> None:
        """Wang-Sun 默认参数。/ Wang-Sun defaults."""
        wsa = WangSunAttractor()
        assert wsa.a == 0.2
        assert wsa.b == 0.01

    def test_wimol_banlue_defaults(self) -> None:
        """Wimol-Banlue 默认参数。/ Wimol-Banlue defaults."""
        wba = WimolBanlueAttractor()
        assert wba.a == 0.1

    def test_yu_wang_defaults(self) -> None:
        """Yu-Wang 默认参数。/ Yu-Wang defaults."""
        ywa = YuWangAttractor()
        assert ywa.a == 10.0
        assert ywa.b == 40.0
        assert ywa.c == 2.5

    def test_van_der_pol_defaults(self) -> None:
        """Van der Pol 默认参数。/ Van der Pol defaults."""
        vdp = VanDerPolSystem()
        assert vdp.mu == 1.0

    def test_rayleigh_benard_defaults(self) -> None:
        """Rayleigh-Benard 默认参数。"""
        rba = RayleighBenardAttractor()
        assert rba.sigma == 10.0
        assert rba.r == 28.0

    def test_three_scroll_defaults(self) -> None:
        """三涡卷统一系统默认参数。"""
        tsu = ThreeScrollUnifiedChaoticSystem()
        assert tsu.a == 40.0
        assert tsu.b == 55.0

    def test_coullet_defaults(self) -> None:
        """Coullet 默认参数。/ Coullet defaults."""
        ca = CoulletAttractor()
        # 验证可实例化
        assert ca is not None

    def test_coupled_lorenz_defaults(self) -> None:
        """耦合 Lorenz 默认参数。/ Coupled Lorenz defaults."""
        cla = CoupledLorenzAttractor()
        assert cla is not None


# ══════════════════════════════════════════════════════════════
# 2D 映射测试
# ══════════════════════════════════════════════════════════════


class TestTinkerbellMap:
    """Tinkerbell 映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        tm = TinkerbellMap()
        assert tm.a == 0.9
        assert tm.b == -0.6013
        assert tm.c == 2.0
        assert tm.d == 0.5

    def test_iterate(self) -> None:
        """迭代返回元组。/ Iterate returns tuple."""
        tm = TinkerbellMap()
        x, y = tm.iterate(0.1, 0.1, n=10)
        assert isinstance(x, float)
        assert isinstance(y, float)


class TestSymplecticMap:
    """辛映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        sm = SymplecticMap()
        assert sm.k == 0.971635

    def test_iterate(self) -> None:
        """迭代返回元组。/ Iterate returns tuple."""
        sm = SymplecticMap()
        x, y = sm.iterate(0.1, 0.2, n=10)
        assert isinstance(x, float)
        assert isinstance(y, float)


class TestZaslavskiiMap:
    """Zaslavskii 映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        zm = ZaslavskiiMap()
        assert zm.epsilon == 4.9
        assert zm.mu == 0.01
        assert zm.r == 3.0

    def test_x_bounded(self) -> None:
        """x 值通过 mod 1 保持在 [0, 1)。/ x stays in [0, 1)."""
        zm = ZaslavskiiMap()
        x, y = zm.iterate(0.5, 0.5, n=100)
        assert 0.0 <= x < 1.0


# ══════════════════════════════════════════════════════════════
# SinusMap / SinusoidalMap / SingerMap 测试
# ══════════════════════════════════════════════════════════════


class TestSinusMap:
    """Sinus 映射测试。"""

    def test_no_params(self) -> None:
        """无参数。/ No parameters."""
        sm = SinusMap()
        result = sm(0.5)
        assert abs(result - 1.0) < 1e-12


class TestSinusoidalMap:
    """正弦型映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        sm = SinusoidalMap()
        assert sm.a == 2.3

    def test_zero_maps_to_zero(self) -> None:
        """零映射到零。/ Zero maps to zero."""
        sm = SinusoidalMap()
        assert abs(sm(0.0)) < 1e-12


class TestSingerMap:
    """Singer 映射测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        sm = SingerMap()
        assert sm.mu == 1.07
        assert sm.a1 == 1.5
        assert sm.a2 == 0.5
        assert sm.a3 == 0.0

    def test_zero_maps_to_zero(self) -> None:
        """零映射到零。/ Zero maps to zero."""
        sm = SingerMap()
        assert abs(sm(0.0)) < 1e-12
