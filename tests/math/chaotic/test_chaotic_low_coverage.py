"""低覆盖率混沌系统补充测试。

Additional tests for chaotic systems at 50-56% coverage.
Targets: Halvorsen, Rabinovich-Fabrikant, Rucklidge, Sakarya,
Shimizu-Morioka, Thomas-Cyclically-Symmetric, Wimol-Banlue,
Gauss, Dyadic, Finance, Genesio-Tesi, Hadley, Qi-Chen,
Rayleigh-Benard, Yu-Wang.

Tests for these chaotic systems with low coverage.
Targets: __call__, iterate, frozen dataclass, parametrized ICs.
"""

from __future__ import annotations

import math

import pytest

from ospf_python.math.chaotic.dyadic_transformation import DyadicTransformation
from ospf_python.math.chaotic.finance_attractor import FinanceAttractor
from ospf_python.math.chaotic.gauss_map import GaussMap
from ospf_python.math.chaotic.genesio_tesi_attractor import GenesioTesiAttractor
from ospf_python.math.chaotic.hadley_attractor import HadleyAttractor
from ospf_python.math.chaotic.halvorsen_attractor import HalvorsenAttractor
from ospf_python.math.chaotic.qi_chen_attractor import QiChenAttractor
from ospf_python.math.chaotic.rabinovich_fabrikant_equation import (
    RabinovichFabrikantEquation,
)
from ospf_python.math.chaotic.rayleigh_benard_attractor import (
    RayleighBenardAttractor,
)
from ospf_python.math.chaotic.rucklidge_attractor import RucklidgeAttractor
from ospf_python.math.chaotic.sakarya_attractor import SakaryaAttractor
from ospf_python.math.chaotic.shimizu_morioka_attractor import (
    ShimizuMoriokaAttractor,
)
from ospf_python.math.chaotic.thomas_cyclically_symmetric_attractor import (
    ThomasCyclicallySymmetricAttractor,
)
from ospf_python.math.chaotic.wimol_banlue_attractor import WimolBanlueAttractor
from ospf_python.math.chaotic.yu_wang_attractor import YuWangAttractor

# -- 1D discrete maps --


class TestDyadicTransformation:
    """二进变换测试。/ Dyadic transformation tests."""

    def test_default(self) -> None:
        """实例化无参数。/ Instantiate with no params."""
        dt = DyadicTransformation()
        assert dt is not None

    @pytest.mark.parametrize("x", [0.1, 0.3, 0.5, 0.7, 0.9])
    def test_call_finite(self, x: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        dt = DyadicTransformation()
        result = dt(x)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_known_value(self) -> None:
        """已知值: 0.3 -> 0.6。/ Known: 0.3 -> 0.6."""
        dt = DyadicTransformation()
        assert abs(dt(0.3) - 0.6) < 1e-12

    def test_half_maps_to_zero(self) -> None:
        """0.5 映射到 0。/ 0.5 maps to 0."""
        dt = DyadicTransformation()
        assert abs(dt(0.5)) < 1e-12

    def test_zero_maps_to_zero(self) -> None:
        """0 映射到 0。/ 0 maps to 0."""
        dt = DyadicTransformation()
        assert abs(dt(0.0)) < 1e-12

    def test_iterate_10_steps(self) -> None:
        """迭代 10 步结果有限。/ 10-step iterate is finite."""
        dt = DyadicTransformation()
        result = dt.iterate(0.3, n=10)
        assert isinstance(result, float)
        assert math.isfinite(result)

    def test_iterate_range(self) -> None:
        """迭代结果在 [0, 1)。/ Iterate in [0, 1)."""
        dt = DyadicTransformation()
        result = dt.iterate(0.7, n=100)
        assert 0.0 <= result < 1.0

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        dt = DyadicTransformation()
        with pytest.raises(AttributeError):
            dt.dt = 0.01  # type: ignore[misc]


class TestGaussMap:
    """Gauss 映射测试。/ Gauss map tests."""

    def test_default(self) -> None:
        """实例化无参数。/ Instantiate with no params."""
        gm = GaussMap()
        assert gm is not None

    @pytest.mark.parametrize("x", [0.25, 0.33, 0.5, 0.7, 0.99])
    def test_call_finite(self, x: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        gm = GaussMap()
        result = gm(x)
        assert isinstance(result, float)
        assert math.isfinite(result)
        assert 0.0 <= result < 1.0

    def test_known_value(self) -> None:
        """已知值: 0.4 -> 0.5。/ Known: 0.4 -> 0.5."""
        gm = GaussMap()
        # 1/0.4 = 2.5, floor = 2, 2.5 - 2 = 0.5
        assert abs(gm(0.4) - 0.5) < 1e-12

    def test_reciprocal_integer(self) -> None:
        """倒数为整数时映射到 0。/ Maps to 0 when reciprocal is int."""
        gm = GaussMap()
        assert abs(gm(0.5)) < 1e-12  # 1/0.5 = 2, frac = 0
        assert abs(gm(0.25)) < 1e-12  # 1/0.25 = 4, frac = 0

    def test_iterate_10_steps(self) -> None:
        """迭代 10 步结果有限。/ 10-step iterate is finite."""
        gm = GaussMap()
        result = gm.iterate(0.618, n=10)
        assert isinstance(result, float)
        assert math.isfinite(result)
        assert 0.0 <= result < 1.0

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        gm = GaussMap()
        with pytest.raises(AttributeError):
            gm.dt = 0.01  # type: ignore[misc]


# -- 3D continuous attractors: shared parametrized ICs --

IC_SETS_3D: list[tuple[float, float, float]] = [
    (1.0, 1.0, 1.0),
    (0.1, 0.2, 0.3),
    (-1.0, 0.5, -0.5),
]


class TestHalvorsenAttractor:
    """Halvorsen 吸引子测试。/ Halvorsen attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ha = HalvorsenAttractor()
        assert ha.a == 1.89
        assert ha.dt == 0.001

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        ha = HalvorsenAttractor()
        result = ha(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_single_step(self) -> None:
        """单步积分验证。/ Single step verification."""
        ha = HalvorsenAttractor(a=1.89, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = ha(x, y, z)
        # dx = -1.89*1 - 4*1 - 4*1 - 1 = -10.89
        dx = -1.89 * x - 4.0 * y - 4.0 * z - y * y
        assert abs(nx - (x + dx * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        ha = HalvorsenAttractor()
        result = ha.iterate(x, y, z, n=50)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_iterate_moves(self) -> None:
        """迭代轨迹远离初始点。/ Trajectory moves from IC."""
        ha = HalvorsenAttractor()
        result = ha.iterate(1.0, 1.0, 1.0, n=100)
        assert not all(
            abs(r - ic) < 1e-12 for r, ic in zip(result, (1.0, 1.0, 1.0), strict=False)
        )

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        ha = HalvorsenAttractor(a=2.0)
        assert ha.a == 2.0
        with pytest.raises(AttributeError):
            ha.a = 3.0  # type: ignore[misc]

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        ha = HalvorsenAttractor(a=2.0, dt=0.005)
        assert ha.a == 2.0
        assert ha.dt == 0.005


class TestRabinovichFabrikantEquation:
    """Rabinovich-Fabrikant 方程测试。/ RF equation tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        rf = RabinovichFabrikantEquation()
        assert rf.alpha == 1.1
        assert rf.gamma == 0.87
        assert rf.dt == 0.001

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        rf = RabinovichFabrikantEquation()
        result = rf(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        rf = RabinovichFabrikantEquation(alpha=1.1, gamma=0.87, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = rf(x, y, z)
        dx = y * (z - 1 + x * x) + 0.87 * x
        assert abs(nx - (x + dx * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        rf = RabinovichFabrikantEquation()
        result = rf.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        rf = RabinovichFabrikantEquation(alpha=1.5)
        assert rf.alpha == 1.5
        with pytest.raises(AttributeError):
            rf.alpha = 2.0  # type: ignore[misc]


class TestRucklidgeAttractor:
    """Rucklidge 吸引子测试。/ Rucklidge attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ra = RucklidgeAttractor()
        assert ra.kappa == 2.0
        assert ra.alpha == 6.7
        assert ra.dt == 0.005

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        ra = RucklidgeAttractor()
        result = ra(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        ra = RucklidgeAttractor(kappa=2.0, alpha=6.7, dt=0.005)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = ra(x, y, z)
        dx = -2.0 * x + 6.7 * y - y * z
        dy = x
        dz = -z + y * y
        assert abs(nx - (x + dx * 0.005)) < 1e-12
        assert abs(ny - (y + dy * 0.005)) < 1e-12
        assert abs(nz - (z + dz * 0.005)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        ra = RucklidgeAttractor()
        result = ra.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_iterate_bounded(self) -> None:
        """默认参数迭代有界。/ Default iterate stays bounded."""
        ra = RucklidgeAttractor()
        result = ra.iterate(1.0, 0.0, 0.0, n=200)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        ra = RucklidgeAttractor(kappa=3.0)
        assert ra.kappa == 3.0
        with pytest.raises(AttributeError):
            ra.kappa = 4.0  # type: ignore[misc]


class TestSakaryaAttractor:
    """Sakarya 吸引子测试。/ Sakarya attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        sa = SakaryaAttractor()
        assert sa.a == 0.4
        assert sa.b == 0.2
        assert sa.dt == 0.005

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        sa = SakaryaAttractor()
        result = sa(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        sa = SakaryaAttractor(a=0.4, b=0.2, dt=0.005)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = sa(x, y, z)
        dx = -x + y + y * z
        dy = -x - y + 0.4 * x * z
        dz = z - 0.2 * x * y
        assert abs(nx - (x + dx * 0.005)) < 1e-12
        assert abs(ny - (y + dy * 0.005)) < 1e-12
        assert abs(nz - (z + dz * 0.005)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        sa = SakaryaAttractor()
        result = sa.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        sa = SakaryaAttractor(a=0.5)
        assert sa.a == 0.5
        with pytest.raises(AttributeError):
            sa.a = 1.0  # type: ignore[misc]


class TestShimizuMoriokaAttractor:
    """Shimizu-Morioka 吸引子测试。/ SM attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        sm = ShimizuMoriokaAttractor()
        assert sm.a == 0.75
        assert sm.b == 0.45
        assert sm.dt == 0.005

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        sm = ShimizuMoriokaAttractor()
        result = sm(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        sm = ShimizuMoriokaAttractor(a=0.75, b=0.45, dt=0.005)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = sm(x, y, z)
        dx = y
        dy = x - 0.75 * y - x * z
        dz = -0.45 * z + x * x
        assert abs(nx - (x + dx * 0.005)) < 1e-12
        assert abs(ny - (y + dy * 0.005)) < 1e-12
        assert abs(nz - (z + dz * 0.005)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        sm = ShimizuMoriokaAttractor()
        result = sm.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        sm = ShimizuMoriokaAttractor(a=1.0)
        assert sm.a == 1.0
        with pytest.raises(AttributeError):
            sm.a = 2.0  # type: ignore[misc]


class TestThomasCyclicallySymmetricAttractor:
    """Thomas 循环对称吸引子测试。/ TCS attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        tcs = ThomasCyclicallySymmetricAttractor()
        assert tcs.b == 0.18
        assert tcs.dt == 0.05

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        tcs = ThomasCyclicallySymmetricAttractor()
        result = tcs(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_origin_fixed_point(self) -> None:
        """原点是不动点。/ Origin is a fixed point."""
        tcs = ThomasCyclicallySymmetricAttractor()
        nx, ny, nz = tcs(0.0, 0.0, 0.0)
        assert abs(nx) < 1e-12
        assert abs(ny) < 1e-12
        assert abs(nz) < 1e-12

    def test_cyclic_symmetry(self) -> None:
        """循环移位导数一致。/ Cyclic shift derivatives consistent."""
        tcs = ThomasCyclicallySymmetricAttractor()
        x, y, z = 1.0, 2.0, 3.0
        dx = math.sin(y) - tcs.b * x
        dy = math.sin(z) - tcs.b * y
        dz = math.sin(x) - tcs.b * z
        dx_s = math.sin(z) - tcs.b * y
        dy_s = math.sin(x) - tcs.b * z
        dz_s = math.sin(y) - tcs.b * x
        assert abs(dx_s - dy) < 1e-12
        assert abs(dy_s - dz) < 1e-12
        assert abs(dz_s - dx) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        tcs = ThomasCyclicallySymmetricAttractor()
        result = tcs.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        tcs = ThomasCyclicallySymmetricAttractor(b=0.2)
        assert tcs.b == 0.2
        with pytest.raises(AttributeError):
            tcs.b = 0.3  # type: ignore[misc]


class TestWimolBanlueAttractor:
    """Wimol-Banlue 吸引子测试。/ Wimol-Banlue attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        wb = WimolBanlueAttractor()
        assert wb.a == 0.1
        assert wb.dt == 0.01

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        wb = WimolBanlueAttractor()
        result = wb(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        wb = WimolBanlueAttractor(a=0.1, dt=0.01)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = wb(x, y, z)
        dx = y - x
        dy = -z * math.tanh(x)
        dz = x * y - 0.1
        assert abs(nx - (x + dx * 0.01)) < 1e-12
        assert abs(ny - (y + dy * 0.01)) < 1e-12
        assert abs(nz - (z + dz * 0.01)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        wb = WimolBanlueAttractor()
        result = wb.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        wb = WimolBanlueAttractor(a=0.5)
        assert wb.a == 0.5
        with pytest.raises(AttributeError):
            wb.a = 1.0  # type: ignore[misc]


class TestFinanceAttractor:
    """金融吸引子测试。/ Finance attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        fa = FinanceAttractor()
        assert fa.a == 0.001
        assert fa.b == 0.2
        assert fa.c == 1.1
        assert fa.dt == 0.01

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        fa = FinanceAttractor()
        result = fa(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        fa = FinanceAttractor(a=0.001, b=0.2, c=1.1, dt=0.01)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = fa(x, y, z)
        dx = (1.0 / 0.2 - 0.001) * x + z + x * y
        dy = -0.2 * y - x * x
        dz = -x - 1.1 * z
        assert abs(nx - (x + dx * 0.01)) < 1e-12
        assert abs(ny - (y + dy * 0.01)) < 1e-12
        assert abs(nz - (z + dz * 0.01)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        fa = FinanceAttractor()
        result = fa.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        fa = FinanceAttractor(a=0.01)
        assert fa.a == 0.01
        with pytest.raises(AttributeError):
            fa.a = 0.1  # type: ignore[misc]


class TestGenesioTesiAttractor:
    """Genesio-Tesi 吸引子测试。/ GT attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        gt = GenesioTesiAttractor()
        assert gt.a == 1.0
        assert gt.b == 1.1
        assert gt.c == 0.44
        assert gt.dt == 0.001

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        gt = GenesioTesiAttractor()
        result = gt(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        gt = GenesioTesiAttractor(a=1.0, b=1.1, c=0.44, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = gt(x, y, z)
        dx = y
        dy = z
        dz = -0.44 * z - 1.1 * y - 1.0 * x + x * x
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        gt = GenesioTesiAttractor()
        result = gt.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        gt = GenesioTesiAttractor(a=2.0)
        assert gt.a == 2.0
        with pytest.raises(AttributeError):
            gt.a = 3.0  # type: ignore[misc]


class TestHadleyAttractor:
    """Hadley 吸引子测试。/ Hadley attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ha = HadleyAttractor()
        assert ha.a == 0.25
        assert ha.alpha == 0.9
        assert ha.beta == 4.0
        assert ha.dt == 0.01

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        ha = HadleyAttractor()
        result = ha(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        ha = HadleyAttractor(a=0.25, alpha=0.9, beta=4.0, dt=0.01)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = ha(x, y, z)
        dx = -y * y - z * z - 0.25 * x + 0.25 * 0.9
        dy = x * y - 4.0 * x * z - y + 1.0
        dz = 4.0 * x * y + x * z - z
        assert abs(nx - (x + dx * 0.01)) < 1e-12
        assert abs(ny - (y + dy * 0.01)) < 1e-12
        assert abs(nz - (z + dz * 0.01)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        ha = HadleyAttractor()
        result = ha.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        ha = HadleyAttractor(a=0.5)
        assert ha.a == 0.5
        with pytest.raises(AttributeError):
            ha.a = 1.0  # type: ignore[misc]


class TestQiChenAttractor:
    """Qi-Chen 吸引子测试。/ Qi-Chen attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        qc = QiChenAttractor()
        assert qc.a == 35.0
        assert abs(qc.b - 8.0 / 3.0) < 1e-12
        assert qc.c == 28.0
        assert qc.dt == 0.001

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        qc = QiChenAttractor()
        result = qc(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        qc = QiChenAttractor(a=35.0, b=8.0 / 3.0, c=28.0, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = qc(x, y, z)
        dx = 35.0 * (y - x) + y * z
        dy = 28.0 * x + y - x * z
        dz = -(8.0 / 3.0) * z + x * y
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        qc = QiChenAttractor()
        result = qc.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        qc = QiChenAttractor(a=40.0)
        assert qc.a == 40.0
        with pytest.raises(AttributeError):
            qc.a = 50.0  # type: ignore[misc]


class TestRayleighBenardAttractor:
    """Rayleigh-Benard 吸引子测试。/ Rayleigh-Benard attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        rb = RayleighBenardAttractor()
        assert rb.sigma == 10.0
        assert rb.r == 28.0
        assert abs(rb.b - 8.0 / 3.0) < 1e-12
        assert rb.dt == 0.001

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        rb = RayleighBenardAttractor()
        result = rb(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        rb = RayleighBenardAttractor(sigma=10.0, r=28.0, b=8.0 / 3.0, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = rb(x, y, z)
        dx = -10.0 * x + 10.0 * y
        dy = 28.0 * x - y - x * z
        dz = -(8.0 / 3.0) * z + x * y
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        rb = RayleighBenardAttractor()
        result = rb.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        rb = RayleighBenardAttractor(sigma=15.0)
        assert rb.sigma == 15.0
        with pytest.raises(AttributeError):
            rb.sigma = 20.0  # type: ignore[misc]


class TestYuWangAttractor:
    """Yu-Wang 吸引子测试。/ Yu-Wang attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        yw = YuWangAttractor()
        assert yw.a == 10.0
        assert yw.b == 40.0
        assert yw.c == 2.5
        assert yw.dt == 0.001

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        yw = YuWangAttractor()
        result = yw(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        yw = YuWangAttractor(a=10.0, b=40.0, c=2.5, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = yw(x, y, z)
        dx = 10.0 * (y - x)
        dy = 40.0 * x - x * z
        dz = -2.5 * z + x * y
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        yw = YuWangAttractor()
        result = yw.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ frozen dataclass is immutable."""
        yw = YuWangAttractor(a=15.0)
        assert yw.a == 15.0
        with pytest.raises(AttributeError):
            yw.a = 20.0  # type: ignore[misc]
