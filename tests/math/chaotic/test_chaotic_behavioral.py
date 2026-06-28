"""Behavioral tests for low-coverage chaotic attractor modules.

Targets: ComplexSquaringMap, CoulletAttractor, FourWingAttractor,
ThreeScrollUnifiedChaoticSystem, WangSunAttractor,
FourScrollHyperChaoticAttractor.
"""

from __future__ import annotations

import math

import pytest

from ospf_python.math.chaotic.complex_squaring_map import ComplexSquaringMap
from ospf_python.math.chaotic.coullet_attractor import CoulletAttractor
from ospf_python.math.chaotic.four_scroll_hyper_chaotic_attractor import (
    FourScrollHyperChaoticAttractor,
)
from ospf_python.math.chaotic.four_wing_attractor import FourWingAttractor
from ospf_python.math.chaotic.three_scroll_unified_chaotic_system import (
    ThreeScrollUnifiedChaoticSystem,
)
from ospf_python.math.chaotic.wang_sun_attractor import WangSunAttractor

IC_SETS_3D: list[tuple[float, float, float]] = [
    (1.0, 1.0, 1.0),
    (0.1, 0.2, 0.3),
    (-1.0, 0.5, -0.5),
]


# ============================================================
# ComplexSquaringMap
# ============================================================


class TestComplexSquaringMap:
    """复数平方映射测试。/ Complex squaring map tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        csm = ComplexSquaringMap()
        assert csm.c == complex(-0.7, 0.27015)

    def test_call_basic(self) -> None:
        """__call__ 基本测试。/ Basic __call__ test."""
        csm = ComplexSquaringMap(c=0j)
        result = csm(1j)
        # z^2 + 0 = (1j)^2 = -1
        assert abs(result - (-1 + 0j)) < 1e-12

    def test_call_known_value(self) -> None:
        """已知值: z=1, c=1 -> 1^2+1=2。/ Known: z=1, c=1 -> 2."""
        csm = ComplexSquaringMap(c=1 + 0j)
        result = csm(1 + 0j)
        assert abs(result - (2 + 0j)) < 1e-12

    def test_call_with_complex_c(self) -> None:
        """复数 c 的调用。/ Call with complex c."""
        csm = ComplexSquaringMap(c=1j)
        # z=1, c=1j: 1 + 1j
        result = csm(1 + 0j)
        assert abs(result - (1 + 1j)) < 1e-12

    def test_iterate_zero_steps(self) -> None:
        """0 步迭代返回原值。/ 0-step iterate returns original."""
        csm = ComplexSquaringMap()
        z0 = 0.5 + 0.5j
        result = csm.iterate(z0, n=0)
        assert result == z0

    def test_iterate_multiple_steps(self) -> None:
        """多步迭代结果有限。/ Multi-step iterate is finite."""
        csm = ComplexSquaringMap()
        z0 = 0.1 + 0.1j
        result = csm.iterate(z0, n=10)
        assert math.isfinite(result.real)
        assert math.isfinite(result.imag)

    def test_custom_c(self) -> None:
        """自定义 c 参数。/ Custom c parameter."""
        csm = ComplexSquaringMap(c=0.5 + 0.5j)
        assert csm.c == complex(0.5, 0.5)

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        csm = ComplexSquaringMap()
        with pytest.raises(AttributeError):
            csm.c = 0j  # type: ignore[misc]


# ============================================================
# CoulletAttractor
# ============================================================


class TestCoulletAttractor:
    """Coullet 吸引子测试。/ Coullet attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ca = CoulletAttractor()
        assert ca.a == 0.8
        assert ca.b == -1.1
        assert ca.c == 0.44
        assert ca.d == -1.0
        assert ca.dt == 0.001

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        ca = CoulletAttractor(a=0.8, b=-1.1, c=0.44, d=-1.0, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = ca(x, y, z)
        dx = y
        dy = z
        dz = -0.8 * x - (-1.1) * y - 0.44 * z + (-1.0) * x * x * x
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        ca = CoulletAttractor()
        result = ca(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        ca = CoulletAttractor()
        result = ca.iterate(x, y, z, n=50)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        ca = CoulletAttractor(a=1.0, b=-2.0, c=0.5, d=-0.5, dt=0.005)
        assert ca.a == 1.0
        assert ca.b == -2.0
        assert ca.dt == 0.005

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        ca = CoulletAttractor()
        with pytest.raises(AttributeError):
            ca.a = 2.0  # type: ignore[misc]


# ============================================================
# FourWingAttractor
# ============================================================


class TestFourWingAttractor:
    """四翼吸引子测试。/ Four-wing attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        fw = FourWingAttractor()
        assert fw.a == 0.2
        assert fw.b == -0.01
        assert fw.c == -0.4
        assert fw.d == -1.0
        assert fw.dt == 0.001

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        fw = FourWingAttractor(a=0.2, b=-0.01, c=-0.4, d=-1.0, dt=0.001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = fw(x, y, z)
        dx = 0.2 * x + y * z
        dy = -0.01 * y + x * z
        dz = -0.4 * z + (-1.0) * x * y
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        fw = FourWingAttractor()
        result = fw(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        fw = FourWingAttractor()
        result = fw.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        fw = FourWingAttractor(a=0.3, b=0.01, c=-0.5, d=-2.0, dt=0.005)
        assert fw.a == 0.3
        assert fw.b == 0.01

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        fw = FourWingAttractor()
        with pytest.raises(AttributeError):
            fw.a = 0.5  # type: ignore[misc]


# ============================================================
# ThreeScrollUnifiedChaoticSystem
# ============================================================


class TestThreeScrollUnifiedChaoticSystem:
    """三涡卷统一混沌系统测试。/ Three-scroll unified chaotic system tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ts = ThreeScrollUnifiedChaoticSystem()
        assert ts.a == 40.0
        assert ts.b == 55.0
        assert abs(ts.c - 11.0 / 6.0) < 1e-12
        assert ts.d == 0.16
        assert ts.dt == 0.0001

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        ts = ThreeScrollUnifiedChaoticSystem(a=40.0, b=55.0, c=11.0 / 6.0, d=0.16, dt=0.0001)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = ts(x, y, z)
        dx = 40.0 * (y - x) - 0.16 * x * z
        dy = 55.0 * x - x * z + (11.0 / 6.0) * y
        dz = x * y - z
        assert abs(nx - (x + dx * 0.0001)) < 1e-12
        assert abs(ny - (y + dy * 0.0001)) < 1e-12
        assert abs(nz - (z + dz * 0.0001)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        ts = ThreeScrollUnifiedChaoticSystem()
        result = ts(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        ts = ThreeScrollUnifiedChaoticSystem()
        result = ts.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        ts = ThreeScrollUnifiedChaoticSystem(a=50.0, dt=0.001)
        assert ts.a == 50.0
        assert ts.dt == 0.001

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        ts = ThreeScrollUnifiedChaoticSystem()
        with pytest.raises(AttributeError):
            ts.a = 60.0  # type: ignore[misc]


# ============================================================
# WangSunAttractor
# ============================================================


class TestWangSunAttractor:
    """Wang-Sun 吸引子测试。/ Wang-Sun attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        ws = WangSunAttractor()
        assert ws.a == 0.2
        assert ws.b == 0.01
        assert ws.c == -0.4
        assert ws.d == -1.0
        assert ws.dt == 0.005

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        ws = WangSunAttractor(a=0.2, b=0.01, c=-0.4, d=-1.0, dt=0.005)
        x, y, z = 1.0, 1.0, 1.0
        nx, ny, nz = ws(x, y, z)
        dx = 0.2 * x + (-0.4) * y * z
        dy = 0.01 * x + (-1.0) * y - x * z
        dz = -z - x * y
        assert abs(nx - (x + dx * 0.005)) < 1e-12
        assert abs(ny - (y + dy * 0.005)) < 1e-12
        assert abs(nz - (z + dz * 0.005)) < 1e-12

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_call_finite(self, x: float, y: float, z: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        ws = WangSunAttractor()
        result = ws(x, y, z)
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(math.isfinite(v) for v in result)

    @pytest.mark.parametrize("x,y,z", IC_SETS_3D)
    def test_iterate_finite(self, x: float, y: float, z: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        ws = WangSunAttractor()
        result = ws.iterate(x, y, z, n=50)
        assert all(math.isfinite(v) for v in result)

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        ws = WangSunAttractor(a=0.3, b=0.02, c=-0.5, d=-2.0, dt=0.01)
        assert ws.a == 0.3
        assert ws.b == 0.02

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        ws = WangSunAttractor()
        with pytest.raises(AttributeError):
            ws.a = 0.5  # type: ignore[misc]


# ============================================================
# FourScrollHyperChaoticAttractor
# ============================================================


class TestFourScrollHyperChaoticAttractor:
    """四涡卷超混沌吸引子测试。/ Four-scroll hyperchaotic attractor tests."""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        fs = FourScrollHyperChaoticAttractor()
        assert fs.a == 10.0
        assert fs.b == 4.0
        assert fs.c == 1.0
        assert fs.d == 16.0
        assert fs.e == 1.0
        assert fs.f == 0.5
        assert fs.dt == 0.001

    def test_call_known(self) -> None:
        """单步已知值。/ Known single-step value."""
        fs = FourScrollHyperChaoticAttractor(
            a=10.0, b=4.0, c=1.0, d=16.0, e=1.0, f=0.5, dt=0.001
        )
        x, y, z, w = 1.0, 1.0, 1.0, 1.0
        nx, ny, nz, nw = fs(x, y, z, w)
        dx = 10.0 * (y - x) + w
        dy = 16.0 * x - x * z + 1.0 * y
        dz = x * y - 4.0 * z
        dw = -1.0 * y - 0.5 * w
        assert abs(nx - (x + dx * 0.001)) < 1e-12
        assert abs(ny - (y + dy * 0.001)) < 1e-12
        assert abs(nz - (z + dz * 0.001)) < 1e-12
        assert abs(nw - (w + dw * 0.001)) < 1e-12

    @pytest.mark.parametrize(
        "x,y,z,w",
        [(1.0, 1.0, 1.0, 1.0), (0.1, 0.2, 0.3, 0.4), (-1.0, 0.5, -0.5, 0.1)],
    )
    def test_call_finite(self, x: float, y: float, z: float, w: float) -> None:
        """__call__ 结果有限。/ __call__ result is finite."""
        fs = FourScrollHyperChaoticAttractor()
        result = fs(x, y, z, w)
        assert isinstance(result, tuple)
        assert len(result) == 4
        assert all(math.isfinite(v) for v in result)

    @pytest.mark.parametrize(
        "x,y,z,w",
        [(1.0, 1.0, 1.0, 1.0), (0.1, 0.2, 0.3, 0.4)],
    )
    def test_iterate_finite(self, x: float, y: float, z: float, w: float) -> None:
        """迭代 50 步结果有限。/ 50-step iterate is finite."""
        fs = FourScrollHyperChaoticAttractor()
        result = fs.iterate(x, y, z, w, n=50)
        assert len(result) == 4
        assert all(math.isfinite(v) for v in result)

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        fs = FourScrollHyperChaoticAttractor(a=15.0, b=5.0, dt=0.005)
        assert fs.a == 15.0
        assert fs.b == 5.0
        assert fs.dt == 0.005

    def test_frozen(self) -> None:
        """frozen dataclass 不可变。/ Frozen dataclass is immutable."""
        fs = FourScrollHyperChaoticAttractor()
        with pytest.raises(AttributeError):
            fs.a = 20.0  # type: ignore[misc]
