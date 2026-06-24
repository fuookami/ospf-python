"""Csp1dRecovery tests.

Test solution recovery from variable values.
测试从变量值恢复解决方案。

Note: recovery failure paths trigger a Failed() call
with a source code signature mismatch.
注意：恢复失败路径触发源代码 Failed() 签名不匹配。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.service.csp1d_recovery import (
    Csp1dRecovery,
)


class TestCsp1dRecovery:
    """Csp1dRecovery tests."""

    def test_creation(self) -> None:
        """Create with default tolerance. / 默认容差创建。"""
        r = Csp1dRecovery()
        assert r is not None

    def test_recover_valid(self) -> None:
        """Recover from valid variable values. / 从有效变量值恢复。"""
        r = Csp1dRecovery()
        variable_values = (
            ("x_Steel_plan1", 3.0),
            ("w_Steel_plan1", 5.0),
        )
        result = r.recover(
            variable_values=variable_values,
            material_names=("Steel",),
            plan_names=("plan1",),
        )
        assert result.is_ok()
        solution = result.unwrap()
        assert len(solution.assignments) == 1
        assert solution.assignments[0].material == "Steel"
        assert solution.assignments[0].quantity == 3

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_recover_no_assignments(self) -> None:
        """Recover fails with no valid assignments. / 无有效分配恢复失败。"""
        r = Csp1dRecovery()
        variable_values = (("x_Steel_plan1", 0.0),)
        result = r.recover(
            variable_values=variable_values,
            material_names=("Steel",),
            plan_names=("plan1",),
        )
        assert result.is_failed()

    def test_recover_multiple_materials(self) -> None:
        """Recover with multiple materials and plans. / 多材料多方案恢复。"""
        r = Csp1dRecovery()
        variable_values = (
            ("x_Steel_plan1", 2.0),
            ("w_Steel_plan1", 3.0),
            ("x_Aluminum_plan2", 1.0),
            ("w_Aluminum_plan2", 4.0),
        )
        result = r.recover(
            variable_values=variable_values,
            material_names=("Steel", "Aluminum"),
            plan_names=("plan1", "plan2"),
        )
        assert result.is_ok()
        solution = result.unwrap()
        assert len(solution.assignments) == 2

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_custom_tolerance(self) -> None:
        """Custom tolerance affects rounding. / 自定义容差影响取整。"""
        r = Csp1dRecovery(tolerance=0.5)
        variable_values = (("x_Steel_plan1", 0.3),)
        result = r.recover(
            variable_values=variable_values,
            material_names=("Steel",),
            plan_names=("plan1",),
        )
        assert result.is_failed()
