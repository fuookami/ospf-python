"""Csp1dAssignment tests.

Test assignment creation and immutability.
测试分配创建和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
    Csp1dAssignment,
)


class TestCsp1dAssignment:
    """Csp1dAssignment frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        assert a.material == "Steel"
        assert a.cutting_plan == "plan-1"
        assert a.quantity == 5
        assert a.waste == 10.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        with pytest.raises(AttributeError):
            a.quantity = 10  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        b = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        assert a == b

    def test_inequality(self) -> None:
        """Different quantity yields inequality. / 不同数量不等。"""
        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        b = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=10,
            waste=10.0,
        )
        assert a != b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        assert hash(a) is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        a = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=5,
            waste=10.0,
        )
        assert dataclasses.is_dataclass(a)
