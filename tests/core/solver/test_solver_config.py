"""SolverConfig 测试。

测试求解器配置基类和具体配置的创建。
Tests SolverConfig ABC and concrete config creation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.config.copt_solver_config import (
    CoptSolverConfig,
)
from ospf_python.core.solver.config.gurobi_solver_config import (
    GurobiSolverConfig,
)
from ospf_python.core.solver.config.scip_solver_config import (
    SCIPSolverConfig,
)
from ospf_python.core.solver.config.solver_config import (
    SolverConfig,
)


class TestSolverConfigABC:
    """抽象基类测试 / ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化。/ Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            SolverConfig()  # type: ignore[abstract]

    def test_subclass(self) -> None:
        """子类可以实例化。/ Subclass can instantiate."""

        class DummyConfig(SolverConfig):
            @property
            def name(self) -> str:
                return "dummy"

            @property
            def time_limit(self) -> float:
                return 60.0

        cfg = DummyConfig()
        assert cfg.name == "dummy"
        assert cfg.time_limit == 60.0


class TestGurobiSolverConfig:
    """Gurobi 配置测试 / Gurobi config tests."""

    def test_default_name(self) -> None:
        """默认名称为 gurobi。/ Default name is gurobi."""
        cfg = GurobiSolverConfig()
        assert cfg.name == "gurobi"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        cfg = GurobiSolverConfig()
        with pytest.raises(AttributeError):
            cfg.name = "new"  # type: ignore[misc]

    def test_custom_values(self) -> None:
        """可自定义值。/ Can customise values."""
        cfg = GurobiSolverConfig(
            time_limit=120.0,
            threads=4,
            mip_gap=1e-6,
        )
        assert cfg.time_limit == 120.0
        assert cfg.threads == 4
        assert cfg.mip_gap == 1e-6


class TestSCIPSolverConfig:
    """SCIP 配置测试 / SCIP config tests."""

    def test_default_name(self) -> None:
        """默认名称为 scip。/ Default name is scip."""
        cfg = SCIPSolverConfig()
        assert cfg.name == "scip"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        cfg = SCIPSolverConfig()
        with pytest.raises(AttributeError):
            cfg.verbose = True  # type: ignore[misc]


class TestCoptSolverConfig:
    """COPT 配置测试 / COPT config tests."""

    def test_default_name(self) -> None:
        """默认名称为 copt。/ Default name is copt."""
        cfg = CoptSolverConfig()
        assert cfg.name == "copt"

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        cfg = CoptSolverConfig()
        with pytest.raises(AttributeError):
            cfg.focus = 1  # type: ignore[misc]

    def test_default_focus(self) -> None:
        """默认 focus 为 0。/ Default focus is 0."""
        cfg = CoptSolverConfig()
        assert cfg.focus == 0
