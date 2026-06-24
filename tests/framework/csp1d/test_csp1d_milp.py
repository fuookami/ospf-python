"""Csp1dMilp tests.

Test MILP model construction and management.
测试 MILP 模型构建和管理。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.service.csp1d_final_milp_status import (
    Csp1dFinalMilpStatus,
)
from ospf_python.framework.csp1d.application.service.csp1d_milp import (
    Csp1dMilp,
    MilpConstraint,
    MilpVariable,
)


class TestMilpVariable:
    """MilpVariable frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        v = MilpVariable(name="x1", lower=0.0, upper=10.0, is_integer=True)
        assert v.name == "x1"
        assert v.lower == 0.0
        assert v.upper == 10.0
        assert v.is_integer is True

    def test_defaults(self) -> None:
        """Default bounds. / 默认边界。"""
        v = MilpVariable(name="x1")
        assert v.lower == 0.0
        assert v.upper == float("inf")
        assert v.is_integer is False

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        v = MilpVariable(name="x1")
        with pytest.raises(AttributeError):
            v.name = "x2"  # type: ignore[misc]


class TestMilpConstraint:
    """MilpConstraint frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        c = MilpConstraint(
            name="c1",
            coefficients=(("x1", 1.0), ("x2", 2.0)),
            sense="<=",
            rhs=10.0,
        )
        assert c.name == "c1"
        assert len(c.coefficients) == 2
        assert c.sense == "<="
        assert c.rhs == 10.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        c = MilpConstraint(
            name="c1",
            coefficients=(),
            sense="<=",
            rhs=10.0,
        )
        with pytest.raises(AttributeError):
            c.name = "c2"  # type: ignore[misc]


class TestCsp1dMilp:
    """Csp1dMilp tests."""

    def test_creation(self) -> None:
        """Create empty model. / 创建空模型。"""
        m = Csp1dMilp()
        assert len(m.variables) == 0
        assert len(m.constraints) == 0
        assert m.status == Csp1dFinalMilpStatus.INFEASIBLE

    def test_add_variable(self) -> None:
        """Add a variable. / 添加变量。"""
        m = Csp1dMilp()
        result = m.add_variable(name="x1", lower=0.0, upper=10.0)
        assert result.is_ok()
        assert len(m.variables) == 1
        assert m.variables[0].name == "x1"

    def test_add_constraint(self) -> None:
        """Add a constraint. / 添加约束。"""
        m = Csp1dMilp()
        result = m.add_constraint(
            name="c1",
            coefficients=(("x1", 1.0),),
            sense="<=",
            rhs=10.0,
        )
        assert result.is_ok()
        assert len(m.constraints) == 1

    def test_set_objective(self) -> None:
        """Set objective function. / 设置目标函数。"""
        m = Csp1dMilp()
        result = m.set_objective({"x1": 1.0, "x2": 2.0})
        assert result.is_ok()
        assert m.objective["x1"] == 1.0
        assert m.objective["x2"] == 2.0

    def test_set_status(self) -> None:
        """Set solving status. / 设置求解状态。"""
        m = Csp1dMilp()
        m.set_status(Csp1dFinalMilpStatus.OPTIMAL)
        assert m.status == Csp1dFinalMilpStatus.OPTIMAL

    def test_multiple_variables(self) -> None:
        """Add multiple variables. / 添加多个变量。"""
        m = Csp1dMilp()
        m.add_variable(name="x1")
        m.add_variable(name="x2")
        m.add_variable(name="x3", is_integer=True)
        assert len(m.variables) == 3
        assert m.variables[2].is_integer is True
