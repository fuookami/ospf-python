"""Csp1dSolution tests.

Test solution creation, assignments, waste, and utilization.
测试解决方案创建、分配、余料和利用率。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
    Csp1dAssignment,
)
from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)


class TestCsp1dSolution:
    """Csp1dSolution frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        s = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
        assert len(s.assignments) == 0
        assert s.total_waste == 0.0
        assert s.utilization == 1.0

    def test_with_assignments(self) -> None:
        """Create with assignments. / 带分配创建。"""
        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        s = Csp1dSolution(
            assignments=(a,),
            total_waste=10.0,
            utilization=0.95,
        )
        assert len(s.assignments) == 1
        assert s.assignments[0].material == "Steel"
        assert s.utilization == 0.95

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        s = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
        with pytest.raises(AttributeError):
            s.total_waste = 5.0  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
        b = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
        assert a == b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        s = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
        assert hash(s) is not None
