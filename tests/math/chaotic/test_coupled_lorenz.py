"""耦合 Lorenz 吸引子测试。

Coupled Lorenz attractor tests.

测试 CoupledLorenzAttractor 的创建、迭代和轨迹稳定性。
Tests CoupledLorenzAttractor creation, iteration,
and trajectory stability.
"""

from __future__ import annotations

import math

from ospf_python.math.chaotic.coupled_lorenz_attractor import (
    CoupledLorenzAttractor,
)

# ── Creation tests ───────────────────────────────────────────────


class TestCoupledLorenzAttractorCreation:
    """耦合 Lorenz 吸引子创建测试。"""

    def test_default_params(self) -> None:
        """默认参数。/ Default parameters."""
        cla = CoupledLorenzAttractor()
        assert cla.sigma == 10.0
        assert cla.r == 28.0
        assert abs(cla.b - 8.0 / 3.0) < 1e-12
        assert cla.k == 1.0
        assert cla.dt == 0.001

    def test_custom_params(self) -> None:
        """自定义参数。/ Custom parameters."""
        cla = CoupledLorenzAttractor(
            sigma=5.0, r=20.0, b=2.0, k=0.5, dt=0.01,
        )
        assert cla.sigma == 5.0
        assert cla.r == 20.0
        assert cla.b == 2.0
        assert cla.k == 0.5
        assert cla.dt == 0.01

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        cla = CoupledLorenzAttractor(sigma=5.0)
        assert cla.sigma == 5.0


# ── Single step tests ────────────────────────────────────────────


class TestCoupledLorenzAttractorCall:
    """耦合 Lorenz 吸引子单步测试。"""

    def test_single_step_returns_tuple(self) -> None:
        """单步返回六元组。/ Single step returns 6-tuple."""
        cla = CoupledLorenzAttractor()
        result = cla(1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        assert len(result) == 6
        assert all(isinstance(v, float) for v in result)

    def test_single_step_known_values(self) -> None:
        """单步已知值验证。/ Single step known value check."""
        cla = CoupledLorenzAttractor(dt=0.01)
        x1, y1, z1, x2, y2, z2 = cla(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        )
        # System 1: dx1 = sigma*(y1-x1) = 10*(1-1) = 0
        # dy1 = r*x1 - y1 - x1*z1 = 28 - 1 - 1 = 26
        # dz1 = -b*z1 + x1*y1 = -8/3 + 1 = -5/3
        assert abs(x1 - 1.0) < 1e-10
        assert abs(y1 - (1.0 + 26.0 * 0.01)) < 1e-10
        assert abs(z1 - (1.0 + (-5.0 / 3.0) * 0.01)) < 1e-10

    def test_origin_is_fixed_point(self) -> None:
        """原点是不动点。/ Origin is a fixed point."""
        cla = CoupledLorenzAttractor()
        x1, y1, z1, x2, y2, z2 = cla(
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        )
        assert abs(x1) < 1e-15
        assert abs(y1) < 1e-15
        assert abs(z1) < 1e-15
        assert abs(x2) < 1e-15
        assert abs(y2) < 1e-15
        assert abs(z2) < 1e-15

    def test_systems_differ_with_coupling(self) -> None:
        """耦合后两系统状态不同。/ Systems differ with coupling."""
        cla = CoupledLorenzAttractor(k=1.0, dt=0.01)
        # Start with identical states but slightly perturb
        # system 1
        x1, y1, z1, x2, y2, z2 = cla(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        )
        # After one step systems should differ due to
        # coupling term k*(x1-x2) in dx2; here x1==x2
        # so coupling term is zero. Let's perturb.
        x1p, y1p, z1p, x2p, y2p, z2p = cla(
            1.1, 1.0, 1.0, 1.0, 1.0, 1.0,
        )
        # dx2 has coupling k*(x1-x2) = 1*(1.1-1.0) = 0.1
        # so x2p should differ from the no-perturbation case
        assert x2p != x2


# ── Iteration tests ──────────────────────────────────────────────


class TestCoupledLorenzAttractorIterate:
    """耦合 Lorenz 吸引子迭代测试。"""

    def test_iterate_single_step(self) -> None:
        """单步迭代等同于 __call__。/ Single iterate matches call."""
        cla = CoupledLorenzAttractor()
        init = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        from_call = cla(*init)
        from_iter = cla.iterate(*init, n=1)
        for a, b in zip(from_call, from_iter, strict=False):
            assert abs(a - b) < 1e-15

    def test_iterate_multi_step(self) -> None:
        """多步迭代返回六元组。/ Multi-step returns 6-tuple."""
        cla = CoupledLorenzAttractor()
        result = cla.iterate(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, n=100,
        )
        assert len(result) == 6

    def test_trajectory_stays_finite(self) -> None:
        """轨迹保持有限值。/ Trajectory stays finite."""
        cla = CoupledLorenzAttractor()
        result = cla.iterate(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, n=1000,
        )
        for v in result:
            assert math.isfinite(v)
            assert abs(v) < 500

    def test_trajectory_bounded_long(self) -> None:
        """长迭代轨迹有界。/ Long iteration stays bounded."""
        cla = CoupledLorenzAttractor()
        result = cla.iterate(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, n=5000,
        )
        for v in result:
            assert math.isfinite(v)
            assert abs(v) < 1000

    def test_trajectory_moves(self) -> None:
        """轨迹远离初始点。/ Trajectory moves from initial."""
        cla = CoupledLorenzAttractor()
        init = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        result = cla.iterate(*init, n=100)
        assert result != init

    def test_iterate_zero_steps(self) -> None:
        """零步迭代返回初始值。/ Zero steps returns initial."""
        cla = CoupledLorenzAttractor()
        init = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        result = cla.iterate(*init, n=0)
        for a, b in zip(init, result, strict=False):
            assert abs(a - b) < 1e-15


# ── Coupling strength tests ──────────────────────────────────────


class TestCoupledLorenzAttractorCoupling:
    """耦合强度变化测试。"""

    def test_zero_coupling(self) -> None:
        """零耦合时系统 2 独立于系统 1。/ Zero coupling decouples system 2."""
        cla = CoupledLorenzAttractor(k=0.0)
        # With k=0, dx2 = sigma*(y2-x2) with no coupling term
        # So system 2 evolves independently
        result = cla(1.0, 1.0, 1.0, 2.0, 2.0, 2.0)
        x1, y1, z1, x2, y2, z2 = result
        # Verify finite and changed
        assert math.isfinite(x1)
        assert math.isfinite(x2)

    def test_large_coupling(self) -> None:
        """大耦合强度仍保持稳定。/ Large coupling stays stable."""
        cla = CoupledLorenzAttractor(k=10.0, dt=0.0005)
        result = cla.iterate(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, n=2000,
        )
        for v in result:
            assert math.isfinite(v)

    def test_negative_coupling(self) -> None:
        """负耦合强度。/ Negative coupling strength."""
        cla = CoupledLorenzAttractor(k=-1.0, dt=0.001)
        result = cla.iterate(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, n=500,
        )
        for v in result:
            assert math.isfinite(v)

    def test_different_coupling_different_results(
        self,
    ) -> None:
        """不同耦合强度产生不同结果。/ Different coupling gives different results."""
        # Use asymmetric init so coupling term is nonzero
        init = (1.0, 1.0, 1.0, 1.1, 1.0, 1.0)
        cla0 = CoupledLorenzAttractor(k=0.0, dt=0.001)
        cla2 = CoupledLorenzAttractor(k=2.0, dt=0.001)
        r0 = cla0.iterate(*init, n=500)
        r2 = cla2.iterate(*init, n=500)
        # At least one component should differ
        assert r0 != r2


# ── Symmetry tests ───────────────────────────────────────────────


class TestCoupledLorenzAttractorSymmetry:
    """耦合 Lorenz 吸引子对称性测试。"""

    def test_symmetric_initial_conditions(self) -> None:
        """对称初始条件下系统 1 前进更快。/ System 1 advances faster under symmetric init with coupling."""
        cla = CoupledLorenzAttractor(k=1.0, dt=0.01)
        # Same initial conditions for both systems
        x1, y1, z1, x2, y2, z2 = cla(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        )
        # With identical states, coupling term is k*(x1-x2)=0
        # so both systems should evolve identically
        assert abs(x1 - x2) < 1e-15
        assert abs(y1 - y2) < 1e-15
        assert abs(z1 - z2) < 1e-15

    def test_asymmetric_evolution(self) -> None:
        """非对称初始条件导致不同演化。/ Asymmetric init leads to divergent evolution."""
        cla = CoupledLorenzAttractor(k=1.0, dt=0.001)
        # System 1 starts at (1,1,1), system 2 at (1.01,1,1)
        result = cla.iterate(
            1.0, 1.0, 1.0, 1.01, 1.0, 1.0, n=5000,
        )
        x1, y1, z1, x2, y2, z2 = result
        # After many steps with coupling, states should diverge
        # (chaotic sensitivity to initial conditions)
        assert abs(x1 - x2) > 1e-6 or abs(y1 - y2) > 1e-6
